"""Independent, read-only QC of final 39-park NDVI inputs against backups.

Does not import the production SAV/XLSX exporter or its decoder. Independently
decodes SPSS bytecode and XML, recomputes sample-SD Z values, and byte-compares
the unchanged spreadsheet content/model text. Writes only its own QC JSON.
"""

from __future__ import annotations

import codecs
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import struct
import xml.etree.ElementTree as ET
import zipfile


WORK = Path(__file__).resolve().parent
ROOT = WORK.parent
PACKAGE = ROOT / "NDVI_39公园区域均值及SEM输入_20261111"
BACKUP = PACKAGE / "00_原始数据备份"
NEW = PACKAGE / "SEM输入"
SAV_NAME = "最终用于sem的匿名39✖16输入矩阵.sav"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
EXPECTED_SAV_HASH = "54cca5a9e38faf59635ebcd9d645d7d77083ac30c7f2d8f46751d809c47d2737"
EXPECTED_BOOK_HASH = "681c5807e4caae6e470d1646946ee9858af46cc65e804540b2aac6479a80e288"
EXPECTED_MODEL_HASH = "19410f39905c9ea51909b5bb2fad3e6cad35f32dde2c3bd859c968de014371a1"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def independently_read_sav(path):
    data = path.read_bytes()
    if data[:4] != b"$FL2":
        raise ValueError("Only classic SPSS SAV files are accepted")
    if struct.unpack_from("<i", data, 64)[0] in (2, 3):
        order = "<"
    elif struct.unpack_from(">i", data, 64)[0] in (2, 3):
        order = ">"
    else:
        raise ValueError("Unknown SAV byte order/layout")
    width, compression, weight, count = struct.unpack_from(order + "4i", data, 68)
    bias = struct.unpack_from(order + "d", data, 84)[0]
    if compression not in (0, 1) or count != 39 or width != 17:
        raise ValueError("Expected 39 numeric cases and 17 SAV variables")
    pos = 176
    variables, extensions = [], []
    while True:
        tag = struct.unpack_from(order + "i", data, pos)[0]
        pos += 4
        if tag == 2:
            kind, label_flag, missing, pformat, wformat = struct.unpack_from(order + "5i", data, pos)
            pos += 20
            short = data[pos:pos + 8].rstrip(b" ")
            pos += 8
            label = b""
            if label_flag:
                label_len = struct.unpack_from(order + "i", data, pos)[0]
                pos += 4
                label = data[pos:pos + label_len]
                pos += (label_len + 3) // 4 * 4
            missing_values = list(struct.unpack_from(order + "d" * abs(missing), data, pos)) if missing else []
            pos += abs(missing) * 8
            variables.append({"short_bytes": short, "label_bytes": label, "type": kind,
                              "missing_specification": missing, "missing_values": missing_values,
                              "print_format": pformat, "write_format": wformat})
        elif tag == 3:
            number = struct.unpack_from(order + "i", data, pos)[0]
            pos += 4
            for _ in range(number):
                pos += 8
                length = data[pos]
                pos += ((length + 1 + 7) // 8) * 8
        elif tag == 4:
            number = struct.unpack_from(order + "i", data, pos)[0]
            pos += 4 + number * 4
        elif tag == 6:
            number = struct.unpack_from(order + "i", data, pos)[0]
            pos += 4 + number * 80
        elif tag == 7:
            subtype, size, number = struct.unpack_from(order + "3i", data, pos)
            pos += 12
            payload = data[pos:pos + size * number]
            pos += size * number
            extensions.append((subtype, size, number, payload))
        elif tag == 999:
            if struct.unpack_from(order + "i", data, pos)[0] != 0:
                raise ValueError("Invalid SAV dictionary terminator")
            pos += 4
            break
        else:
            raise ValueError(f"Unknown SAV dictionary record {tag}")
        if pos > len(data):
            raise ValueError("Truncated SAV dictionary")
    dictionary = data[176:pos]
    if len(variables) != width or any(variable["type"] != 0 for variable in variables):
        raise ValueError("SAV is not the expected numeric matrix")
    encoding = next((payload.rstrip(b"\0").decode("ascii") for subtype, _, _, payload in extensions if subtype == 20), "utf-8")
    codecs.lookup(encoding)
    long_names = {}
    for subtype, _, _, payload in extensions:
        if subtype == 13:
            for pair in payload.decode(encoding).rstrip("\0").split("\t"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    long_names[key] = value
    for variable in variables:
        short = variable.pop("short_bytes").decode(encoding)
        variable["short_name"] = short
        variable["name"] = long_names.get(short, short)
        variable["label"] = variable.pop("label_bytes").decode(encoding)
    total = count * width
    cells = []
    if compression == 0:
        expected_end = pos + total * 8
        if expected_end != len(data):
            raise ValueError("Uncompressed SAV length disagrees with case count")
        cells = list(struct.unpack_from(order + "d" * total, data, pos))
        pos = expected_end
    else:
        while len(cells) < total:
            controls = data[pos:pos + 8]
            if len(controls) != 8:
                raise ValueError("Truncated SAV compressed controls")
            pos += 8
            for code in controls:
                if code == 0:
                    continue
                if code in (252, 254, 255):
                    raise ValueError("Unexpected end/missing/string code in the numeric SAV matrix")
                if code == 253:
                    value = struct.unpack_from(order + "d", data, pos)[0]
                    pos += 8
                else:
                    value = float(code - bias)
                cells.append(value)
                if len(cells) == total:
                    break
    if len(cells) != total or not all(math.isfinite(value) and value > -1e307 for value in cells):
        raise ValueError("SAV matrix has incorrect size or missing/nonfinite values")
    return {"rows": [cells[i:i + width] for i in range(0, total, width)],
            "variables": variables, "dictionary_bytes": dictionary,
            "compression": compression, "weight_index": weight,
            "encoding": encoding, "case_count": count, "variable_count": width}


def parse_sheet_cells(archive, name="xl/worksheets/sheet1.xml"):
    shared = []
    if "xl/sharedStrings.xml" in archive.namelist():
        shared = ["".join(node.text or "" for node in entry.iter(NS + "t"))
                  for entry in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
    result = {}
    for cell in ET.fromstring(archive.read(name)).iter(NS + "c"):
        address = cell.get("r")
        value = cell.find(NS + "v")
        text = value.text if value is not None else None
        if cell.get("t") == "s":
            decoded = shared[int(text)]
        elif cell.get("t") == "inlineStr":
            decoded = "".join(node.text or "" for node in cell.iter(NS + "t"))
        elif text is None:
            decoded = None
        else:
            decoded = float(text)
        result[address] = {"value": decoded, "value_text": text, "type": cell.get("t"),
                           "formula": cell.find(NS + "f") is not None}
    return result


def mask_only_allowed_v_text(xml, addresses):
    seen = set()
    def replace_cell(match):
        cell = match.group(0)
        reference = re.search(rb'\br="([^"]+)"', cell)
        if reference is None or reference.group(1).decode("ascii") not in addresses:
            return cell
        address = reference.group(1).decode("ascii")
        if address in seen:
            raise ValueError("Duplicate spreadsheet cell")
        seen.add(address)
        values = list(re.finditer(rb"<v(?:\s[^>]*)?>([^<]*)</v>", cell))
        if len(values) != 1:
            raise ValueError("Expected one numeric value per permitted NDVI cell")
        a, b = values[0].span(1)
        return cell[:a] + b"__QC_NDVI_VALUE__" + cell[b:]
    masked = re.sub(rb"<c(?=[\s>])[^>]*>.*?</c>", replace_cell, xml, flags=re.S)
    if seen != addresses:
        raise ValueError("Some permitted NDVI spreadsheet cells are absent")
    return masked


def compressed_zip_payload(path, info):
    with path.open("rb") as stream:
        stream.seek(info.header_offset)
        head = stream.read(30)
        if head[:4] != b"PK\x03\x04":
            raise ValueError("Bad local ZIP header")
        name_len, extra_len = struct.unpack_from("<HH", head, 26)
        stream.seek(name_len + extra_len, 1)
        return stream.read(info.compress_size)


def audit_excel(old_path, new_path, expected_matrix):
    allowed = {f"{column}{row}" for column in ("Q", "R") for row in range(4, 43)}
    with zipfile.ZipFile(old_path) as old, zipfile.ZipFile(new_path) as new:
        old_names, new_names = old.namelist(), new.namelist()
        if old_names != new_names:
            raise ValueError("Workbook member inventory/order changed")
        if old.testzip() is not None or new.testzip() is not None:
            raise ValueError("Workbook ZIP CRC check failed")
        changed = [name for name in old_names if old.read(name) != new.read(name)]
        old_xml = old.read("xl/worksheets/sheet1.xml")
        new_xml = new.read("xl/worksheets/sheet1.xml")
        outside_values_identical = mask_only_allowed_v_text(old_xml, allowed) == mask_only_allowed_v_text(new_xml, allowed)
        old_cells, new_cells = parse_sheet_cells(old), parse_sheet_cells(new)
        numeric_changed = [address for address in allowed if old_cells[address]["value"] != new_cells[address]["value"]]
        changed_values_numeric_no_formula = all(
            new_cells[address]["type"] in (None, "n") and not new_cells[address]["formula"]
            and isinstance(new_cells[address]["value"], float)
            for address in allowed)
        matrix = [[new_cells[f"{col}{row}"]["value"] for col in "BCDEFGHIJKLMNOPQR"]
                  for row in range(4, 43)]
        unchanged = [name for name in old_names if name != "xl/worksheets/sheet1.xml"]
        fields = ("date_time", "compress_type", "comment", "extra", "create_system", "create_version",
                  "extract_version", "flag_bits", "volume", "internal_attr", "external_attr", "CRC", "file_size")
        metadata_unchanged = all(all(getattr(old.getinfo(name), field) == getattr(new.getinfo(name), field)
                                   for field in fields) for name in unchanged)
        compressed_bytes_unchanged = all(compressed_zip_payload(old_path, old.getinfo(name)) == compressed_zip_payload(new_path, new.getinfo(name))
                                        for name in unchanged)
        return {
            "zip_CRC_checks_pass": True, "ZIP_member_inventory_and_order_unchanged": old_names == new_names,
            "ZIP_archive_comment_unchanged": old.comment == new.comment,
            "changed_ZIP_members": changed,
            "only_sheet1_payload_changed": changed == ["xl/worksheets/sheet1.xml"],
            "unchanged_member_count": len(unchanged),
            "all_other_member_payload_bytes_unchanged": all(old.read(name) == new.read(name) for name in unchanged),
            "all_other_member_compressed_bytes_unchanged": compressed_bytes_unchanged,
            "all_other_member_metadata_unchanged": metadata_unchanged,
            "sheet1_bytes_outside_Q4_Q42_R4_R42_v_text_unchanged": outside_values_identical,
            "permitted_numeric_cells": len(allowed), "actually_changed_numeric_cells": len(numeric_changed),
            "changed_cells_are_numeric_without_formulas": changed_values_numeric_no_formula,
            "new_39x17_Excel_matrix_exactly_matches_new_SAV": matrix == expected_matrix,
            "changed_cell_range": "Q4:Q42 and R4:R42",
        }


def audit_amw(old_path, new_path, root_path, new_sav_path):
    before = old_path.read_bytes().decode("utf-16").splitlines(keepends=True)
    after = new_path.read_bytes().decode("utf-16").splitlines(keepends=True)
    if len(before) != len(after):
        raise ValueError("AMW line inventory changed")
    permitted = []
    bindings = {}
    expected = {"!@!dbname": str(new_sav_path.resolve()), "!@!dbtable": new_sav_path.stem}
    for marker in expected:
        old_pos = [i for i, line in enumerate(before) if line.rstrip("\r\n") == marker]
        new_pos = [i for i, line in enumerate(after) if line.rstrip("\r\n") == marker]
        if len(old_pos) != 1 or old_pos != new_pos:
            raise ValueError("AMW binding marker missing/moved")
        pos = old_pos[0] + 1
        permitted.append(pos)
        bindings[marker[3:]] = after[pos].rstrip("\r\n")
    differences = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    masked_old, masked_new = before[:], after[:]
    for pos in permitted:
        masked_old[pos] = masked_new[pos] = "__QC_PERMITTED_DATA_BINDING__"
    return {
        "original_root_AMW_SHA256": sha256(root_path),
        "original_AMW_remains_original_hash": sha256(root_path) == EXPECTED_MODEL_HASH,
        "original_root_AMW_exactly_matches_backup": root_path.read_bytes() == old_path.read_bytes(),
        "new_AMW_only_dbname_dbtable_value_lines_can_differ": all(i in permitted for i in differences),
        "new_AMW_actual_changed_binding_line_count": len(differences),
        "new_AMW_entire_remaining_serialized_text_identical": masked_old == masked_new,
        "new_AMW_BOM_unchanged": old_path.read_bytes()[:2] == new_path.read_bytes()[:2],
        "new_AMW_binding_names_checked": ["dbname", "dbtable"],
        "new_AMW_dbname_binds_final_package_SAV": bindings["dbname"] == expected["!@!dbname"],
        "new_AMW_dbtable_matches_SAV_stem": bindings["dbtable"] == expected["!@!dbtable"],
        "native_Amos_run_not_performed_by_QC": True,
    }


def main():
    old_sav, new_sav = BACKUP / SAV_NAME, NEW / SAV_NAME
    books = [path for path in BACKUP.glob("*.xlsx") if path.name.startswith("公園番号ParkIDと16のSEM観測変数")]
    if len(books) != 1:
        raise ValueError("Expected a unique bilingual workbook backup")
    old_book, new_book = books[0], NEW / books[0].name
    old_amw, new_amw, root_amw = BACKUP / "amos模型.amw", PACKAGE / "amos模型_NDVI区域均值更新.amw", ROOT / "amos模型.amw"
    checks = {
        "old_SAV_backup_matches_original_SHA256": sha256(old_sav) == EXPECTED_SAV_HASH,
        "old_Excel_backup_matches_original_SHA256": sha256(old_book) == EXPECTED_BOOK_HASH,
        "old_AMW_backup_matches_original_SHA256": sha256(old_amw) == EXPECTED_MODEL_HASH,
        "root_updated_SAV_byte_identical_to_final_package_copy": (ROOT / SAV_NAME).read_bytes() == new_sav.read_bytes(),
        "root_updated_Excel_byte_identical_to_final_package_copy": (ROOT / old_book.name).read_bytes() == new_book.read_bytes(),
    }
    baseline, final = independently_read_sav(old_sav), independently_read_sav(new_sav)
    checks.update({
        "SAV_case_count_39_and_variable_count_17": final["case_count"] == 39 and final["variable_count"] == 17,
        "SAV_entire_dictionary_bytes_identical_to_backup": final["dictionary_bytes"] == baseline["dictionary_bytes"],
        "SAV_names_labels_formats_missing_specs_preserved": final["variables"] == baseline["variables"],
        "SAV_first_variable_ParkID_and_final_two_names_preserved": [item["name"] for item in final["variables"]][0] == "ParkID"
            and [item["name"] for item in final["variables"]][-2:] == ["Z内部NDVI平均値", "Z外部NDVI平均値"],
        "SAV_ParkID_order_exactly_1_to_39": [row[0] for row in final["rows"]] == list(range(1, 40)),
        "SAV_585_ParkID_and_nonNDVI_cells_exactly_unchanged": all(struct.pack("<15d", *old[:15]) == struct.pack("<15d", *new[:15]) for old, new in zip(baseline["rows"], final["rows"])),
        "SAV_all_values_finite_and_no_system_missing": all(math.isfinite(value) and value > -1e307 for row in final["rows"] for value in row),
        "SAV_weight_index_preserved": final["weight_index"] == baseline["weight_index"],
    })
    selection = json.loads((WORK / "frame_margin_selection.json").read_text(encoding="utf-8"))["parks"]
    package_ndvi = read_csv(PACKAGE / "39公园NDVI区域均值及Z值.csv")
    agent_ndvi = read_csv(ROOT / "NDVI_sem_completion_work" / "selected_frame_margin_ndvi_means_and_z.csv")
    checks["all_three_NDVI_tables_39_rows_in_same_ParkID_order"] = (
        len(selection) == len(package_ndvi) == len(agent_ndvi) == 39
        and [p["ParkID"] for p in selection] == [int(p["ParkID"]) for p in package_ndvi] == [int(p["ParkID"]) for p in agent_ndvi] == list(range(1, 40)))
    checks["package_sources_rawmeans_counts_frame_margin_exactly_match_selection"] = all(
        row["source_raster"] == sel["selected_source_raster"]
        and float(row["ndvi_inside_area_mean"]) == sel["inside_mean"]
        and float(row["ndvi_outside_100m_ring_area_mean"]) == sel["outside_mean"]
        and float(row["source_frame_margin_m"]) == sel["selected_frame_margin_m"]
        and all(int(row[side + "_" + key + "_pixels"]) == sel[side + "_" + key + "_n"]
                for side in ("inside", "outside") for key in ("valid", "eligible", "nodata"))
        for row, sel in zip(package_ndvi, selection))
    checks["package_sources_rawmeans_Z_validcounts_exactly_match_SEMagent_csv"] = all(
        row["source_raster"] == agent["source_raster"]
        and float(row["ndvi_inside_area_mean"]) == float(agent["inside_mean"])
        and float(row["ndvi_outside_100m_ring_area_mean"]) == float(agent["outside_mean"])
        and float(row["z_inside_area_mean"]) == float(agent["z_inside"])
        and float(row["z_outside_area_mean"]) == float(agent["z_outside"])
        and int(row["inside_valid_pixels"]) == int(agent["inside_valid_n"])
        and int(row["outside_valid_pixels"]) == int(agent["outside_valid_n"])
        for row, agent in zip(package_ndvi, agent_ndvi))
    standardization = {}
    for side, sav_col in (("inside", 15), ("outside", 16)):
        raw = [park[side + "_mean"] for park in selection]
        mean = statistics.fmean(raw)
        sample_sd = statistics.stdev(raw)
        recomputed_z = [(value - mean) / sample_sd for value in raw]
        actual_z = [float(row["z_" + side + "_area_mean"]) for row in package_ndvi]
        max_difference = max(abs(a - b) for a, b in zip(recomputed_z, actual_z))
        actual_mean = statistics.fmean(actual_z)
        actual_sd = statistics.stdev(actual_z)
        standardization[side] = {"n": 39, "sample_SD_divisor": 38,
                                 "independently_recomputed_raw_mean": mean,
                                 "independently_recomputed_raw_sample_SD": sample_sd,
                                 "actual_Z_mean": actual_mean, "actual_Z_sample_SD": actual_sd,
                                 "maximum_independent_Z_difference": max_difference}
        checks[side + "_39_Z_recomputed_from_frame_selected_rawmeans"] = max_difference < 5e-14
        checks[side + "_39_Z_mean_zero_sample_SD_one"] = abs(actual_mean) < 1e-12 and abs(actual_sd - 1) < 1e-12
        checks[side + "_39_saved_SAV_Z_exactly_match_package_csv"] = actual_z == [row[sav_col] for row in final["rows"]]
    sem_csv = read_csv(NEW / "39公园16观测变量_更新NDVI.csv")
    names = [item["name"] for item in final["variables"]]
    checks["saved_full_SEM_csv_exactly_matches_SAV_names_and_all_values"] = (
        len(sem_csv) == 39 and list(sem_csv[0]) == names
        and [[float(row[name]) for name in names] for row in sem_csv] == final["rows"])
    excel = audit_excel(old_book, new_book, final["rows"])
    container_only_fields = {"all_other_member_compressed_bytes_unchanged", "all_other_member_metadata_unchanged"}
    for key, value in excel.items():
        if isinstance(value, bool) and key not in container_only_fields:
            checks["Excel_" + key] = value
    checks["Excel_all_78_allowed_NDVI_numeric_values_actually_changed"] = excel["actually_changed_numeric_cells"] == 78
    amw = audit_amw(old_amw, new_amw, root_amw, new_sav)
    for key, value in amw.items():
        if isinstance(value, bool):
            checks["AMW_" + key] = value
    report = {
        "QC_scope": "Independent read-only check using package/00_原始数据备份 as the BEFORE baseline; root SAV/Excel are already updated and were used only for equality-to-new-copy checks.",
        "production_exporter_and_production_decoders_not_imported": True,
        "QC_writes_only_own_JSON": True, "original_data_and_package_not_modified_by_QC": True,
        "checks": checks, "all_checks_pass": all(checks.values()),
        "failed_checks": [key for key, value in checks.items() if not value],
        "standardization": standardization,
        "SAV_compression_before_after": [baseline["compression"], final["compression"]],
        "SAV_changed_NDVI_numeric_cells": sum(a != b for old, new in zip(baseline["rows"], final["rows"]) for a, b in zip(old[-2:], new[-2:])),
        "SAV_dictionary_preservation_note": "Dictionary is byte-identical, including Japanese NDVI variable names, labels/formats and extension records. Export header compression/product/date/file label changed; whole-file equality to the old SAV is therefore neither expected nor claimed.",
        "Excel_container_note": "The XLSX ZIP container was repacked: unchanged members have identical decompressed payload bytes, but their compressed streams and ZIP flag/external-attribute metadata can differ. This is not spreadsheet content change or a data error; compressed bytes/ZIP metadata equality is outside the requested content-integrity requirements. Only Q4:Q42 and R4:R42 numeric value text changed in sheet1 XML.",
        "Excel_container_metadata_observation": "For the nine unchanged members, flag_bits changed from 6 to 0 and external_attr from 0 to 25165824; compression remains DEFLATE and payloads are byte-identical.",
        "Excel": excel, "AMW": amw,
        "SHA256": {"old_backup_SAV": sha256(old_sav), "new_package_SAV": sha256(new_sav),
                   "old_backup_Excel": sha256(old_book), "new_package_Excel": sha256(new_book),
                   "old_backup_AMW": sha256(old_amw), "original_root_AMW": sha256(root_amw), "new_bound_AMW": sha256(new_amw)},
    }
    report["checks"]["SAV_all_78_NDVI_numeric_values_actually_changed"] = report["SAV_changed_NDVI_numeric_cells"] == 78
    report["all_checks_pass"] = all(report["checks"].values())
    report["failed_checks"] = [key for key, value in report["checks"].items() if not value]
    target = WORK / "qc_final_selected_inputs_independent.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"all_checks_pass": report["all_checks_pass"], "failed_checks": report["failed_checks"],
                      "check_count": len(checks), "SAV_changed_NDVI_numeric_cells": report["SAV_changed_NDVI_numeric_cells"],
                      "Excel_actually_changed_numeric_cells": excel["actually_changed_numeric_cells"],
                      "standardization": standardization, "QC_output": str(target.relative_to(ROOT))}, ensure_ascii=False))
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
