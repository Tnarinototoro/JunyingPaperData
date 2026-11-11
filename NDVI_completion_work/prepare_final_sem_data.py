"""Prepare selected 39-park NDVI means/Z and replace only two SEM columns.

The spatial source rule was fixed independently of SEM results. Original data
are backed up before the user-authorized two-column update. Model structure is
never changed; a separate AMW copy only receives new data-file bindings.
"""

import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(__file__).resolve().parent
OUT = ROOT / "NDVI_39公园区域均值及SEM输入_20261111"
sys.path.insert(0, str(ROOT / ".paper15_work"))
sys.path.insert(0, str(ROOT / "NDVI_sem_sensitivity_work"))
from read_numeric_sav import decode_numeric_matrix
from qa_new_bilingual_excel_original import read_book
from audit_amw_structure import parse as parse_amw


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                               allow_nan=False), encoding="utf-8")


def save_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream).writerows(rows)


def standardize(values):
    assert len(values) == 39 and all(math.isfinite(v) for v in values)
    mean = math.fsum(values) / 39
    sd = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / 38)
    assert sd > 0
    result = [(v - mean) / sd for v in values]
    assert abs(math.fsum(result) / 39) < 1e-14
    assert abs(math.sqrt(math.fsum(v * v for v in result) / 38) - 1) < 1e-14
    return result, {"n": 39, "mean": mean, "sample_sd": sd,
                    "sample_variance_divisor": 38, "minimum": min(values),
                    "maximum": max(values)}


def export_sav(path, source, rows):
    marker = struct.pack("<ii", 999, 0)
    assert source[:4] == b"$FL2" and source.count(marker) == 1
    offset = source.index(marker) + len(marker)
    header = bytearray(source[:offset])
    assert struct.unpack_from("<i", header, 68)[0] == 17
    struct.pack_into("<i", header, 72, 0)
    struct.pack_into("<i", header, 80, 39)
    header[4:64] = b"Python SPSS-compatible NDVI regional mean export".ljust(60, b" ")
    generated = datetime.now()
    header[92:101] = generated.strftime("%d %b %y").encode("ascii")
    header[101:109] = generated.strftime("%H:%M:%S").encode("ascii")
    header[109:173] = b"n=39; true regional NDVI mean Z; spatial-frame source rule".ljust(64, b" ")
    cases = b"".join(struct.pack("<17d", *row) for row in rows)
    path.write_bytes(header + cases)
    decoded = decode_numeric_matrix(path)
    assert decoded["rows"] == rows and decoded["case_count"] == 39
    assert decoded["compression"] == 0
    return decoded


def update_xlsx(source, destination, zin, zout):
    replacement = {f"{column}{i + 4}": value
                   for column, values in (("Q", zin), ("R", zout))
                   for i, value in enumerate(values)}
    changed = set()
    pattern = re.compile(rb'(<c\b[^>]*\br="([QR][0-9]+)"[^>]*>)(.*?)(</c>)', re.S)
    def replace(match):
        reference = match.group(2).decode("ascii")
        if reference not in replacement:
            return match.group(0)
        assert reference not in changed and b"<f" not in match.group(3)
        body, count = re.subn(rb"(<v\b[^>]*>)[^<]*(</v>)",
                             lambda v: v.group(1) + repr(replacement[reference]).encode("ascii") + v.group(2),
                             match.group(3))
        assert count == 1
        changed.add(reference)
        return match.group(1) + body + match.group(4)
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination, "x") as new:
        new.comment = old.comment
        for entry in old.infolist():
            payload = old.read(entry.filename)
            if entry.filename == "xl/worksheets/sheet1.xml":
                payload = pattern.sub(replace, payload)
            new.writestr(entry, payload)
    assert changed == set(replacement)
    with zipfile.ZipFile(source) as old, zipfile.ZipFile(destination) as new:
        assert new.testzip() is None and old.namelist() == new.namelist()
        for name in old.namelist():
            if name != "xl/worksheets/sheet1.xml":
                assert old.read(name) == new.read(name)
    return 78


def update_model_binding(source, destination, sav):
    text = source.read_bytes().decode("utf-16")
    lines = text.splitlines(keepends=True)
    before = lines[:]
    modified = []
    for marker, value in (("!@!dbname", str(sav.resolve())), ("!@!dbtable", sav.stem)):
        positions = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == marker]
        assert len(positions) == 1
        pos = positions[0] + 1
        ending = "\r\n" if lines[pos].endswith("\r\n") else "\n" if lines[pos].endswith("\n") else ""
        lines[pos] = value + ending
        modified.append(pos)
    assert all(a == b for i, (a, b) in enumerate(zip(before, lines)) if i not in modified)
    destination.write_bytes("".join(lines).encode("utf-16"))
    old, new = parse_amw(source), parse_amw(destination)
    for key in ("attribute_count", "object_count", "object_types", "settings", "nodes", "arrows"):
        assert old[key] == new[key]
    return {"data_binding_fields_updated": ["dbname", "dbtable"],
            "model_paths_loadings_variance_constraints_and_settings_preserved": True,
            "native_Amos_open_or_run_performed": False}


def main():
    inputs = OUT / "SEM输入"
    backup = OUT / "00_原始数据备份"
    qc = OUT / "QC"
    for path in (inputs, backup, qc):
        path.mkdir(parents=True, exist_ok=True)
    sav = ROOT / "最终用于sem的匿名39✖16输入矩阵.sav"
    xlsx_paths = [p for p in ROOT.glob("*.xlsx")
                  if p.name.startswith("公園番号ParkIDと16のSEM観測変数")
                  and "16 SEM observed variables" in p.name]
    assert len(xlsx_paths) == 1
    book, model = xlsx_paths[0], ROOT / "amos模型.amw"
    expected = {sav: "54cca5a9e38faf59635ebcd9d645d7d77083ac30c7f2d8f46751d809c47d2737",
                book: "681c5807e4caae6e470d1646946ee9858af46cc65e804540b2aac6479a80e288",
                model: "19410f39905c9ea51909b5bb2fad3e6cad35f32dde2c3bd859c968de014371a1"}
    for path, old_hash in expected.items():
        assert digest(path) == old_hash, "Original input changed; refusing silent overwrite"
        destination = backup / path.name
        if destination.exists():
            raise FileExistsError("Refusing to overwrite an existing original-data backup")
        shutil.copy2(path, destination)
        assert digest(destination) == old_hash
    matrix = decode_numeric_matrix(sav)
    names = [v["name"] for v in matrix["variables"]]
    assert names[0] == "ParkID" and names[-2:] == ["Z内部NDVI平均値", "Z外部NDVI平均値"]
    selection = json.loads((WORK / "frame_margin_selection.json").read_text(encoding="utf-8"))
    parks = selection["parks"]
    assert [p["ParkID"] for p in parks] == list(range(1, 40))
    zin, stats_inside = standardize([p["inside_mean"] for p in parks])
    zout, stats_outside = standardize([p["outside_mean"] for p in parks])
    rows = [row[:] for row in matrix["rows"]]
    for row, park, zi, zo in zip(rows, parks, zin, zout):
        assert row[0] == park["ParkID"]
        row[15], row[16] = zi, zo
    assert all(new[:15] == old[:15] for new, old in zip(rows, matrix["rows"]))
    new_sav, new_book = inputs / sav.name, inputs / book.name
    new_model = OUT / "amos模型_NDVI区域均值更新.amw"
    if any(p.exists() for p in (new_sav, new_book, new_model)):
        raise FileExistsError("Refusing to overwrite existing prepared inputs")
    decoded = export_sav(new_sav, sav.read_bytes(), rows)
    assert decoded["variables"] == matrix["variables"]
    assert update_xlsx(book, new_book, zin, zout) == 78
    actual = read_book(new_book)[0]["cells"]
    actual_rows = [[actual[f"{col}{i + 4}"]["value"] for col in "BCDEFGHIJKLMNOPQR"]
                   for i in range(39)]
    assert actual_rows == rows
    binding = update_model_binding(model, new_model, new_sav)
    save_csv(inputs / "39公园16观测变量_更新NDVI.csv", [names] + rows)
    ndvi_fields = ["ParkID", "source_raster", "ndvi_inside_area_mean", "ndvi_outside_100m_ring_area_mean",
                   "z_inside_area_mean", "z_outside_area_mean", "inside_valid_pixels",
                   "outside_valid_pixels", "inside_eligible_pixels", "outside_eligible_pixels",
                   "inside_nodata_pixels", "outside_nodata_pixels", "source_frame_margin_m"]
    ndvi_rows = [ndvi_fields] + [[p["ParkID"], p["selected_source_raster"], p["inside_mean"], p["outside_mean"],
                                 zi, zo, p["inside_valid_n"], p["outside_valid_n"], p["inside_eligible_n"],
                                 p["outside_eligible_n"], p["inside_nodata_n"], p["outside_nodata_n"],
                                 p["selected_frame_margin_m"]]
                                for p, zi, zo in zip(parks, zin, zout)]
    save_csv(OUT / "39公园NDVI区域均值及Z值.csv", ndvi_rows)
    saved_rows = []
    for original, prepared in ((sav, new_sav), (book, new_book)):
        assert original.resolve().parent == ROOT.resolve()
        assert digest(original) == expected[original]
        temporary = original.with_name(original.name + ".ndvi_update.tmp")
        assert temporary.resolve().is_relative_to(ROOT.resolve())
        if temporary.exists():
            raise FileExistsError("Refusing to overwrite an existing temporary update")
        shutil.copy2(prepared, temporary)
        assert digest(temporary) == digest(prepared)
        temporary.replace(original)  # Exact original target, verified backup already exists.
        assert digest(original) == digest(prepared)
        saved_rows.append({"root_file": original.name, "original_sha256": expected[original],
                           "updated_sha256": digest(original), "backup_relative_path": str((backup / original.name).relative_to(OUT))})
    assert decode_numeric_matrix(sav)["rows"] == rows
    assert read_book(book)[0]["cells"] == actual
    assert digest(model) == expected[model]
    summary = {"source_rule": selection["method"], "historical_source_restoration_claimed": False,
               "ParkID_order": list(range(1, 40)), "cases": 39,
               "NDVI_region_means_are_actual_pixel_means": True, "other_park_mean_or_median_imputation": False,
               "inside_standardization": stats_inside, "outside_standardization": stats_outside,
               "all_78_Z_values_recalculated": True, "ParkID_and_other_14_columns_preserved_exactly": True,
               "SAV_variable_dictionary_preserved": True, "xlsx_only_78_Q4_R42_numeric_values_changed": True,
               "SAV_and_XLSX_saved_then_read_back_identical": True, "root_originals_updated_with_backups": saved_rows,
               "original_AMW_unchanged": True, "new_AMW_data_binding": binding,
               "native_Amos_run_performed": False}
    save_json(qc / "39园NDVI与两份SEM输入保存核对.json", summary)
    print(json.dumps({"package": str(OUT), "prepared_SAV": str(new_sav), "prepared_XLSX": str(new_book),
                      "prepared_AMW": str(new_model), "root_two_input_files_updated": True,
                      "backups": str(backup), "cases": 39, "all_78_Z_updated": True,
                      "other_14_columns_unchanged": True, "inside": stats_inside,
                      "outside": stats_outside}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
