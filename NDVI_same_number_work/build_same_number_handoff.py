"""Publish the author-confirmed same-number GIS/NDVI verification.

Uses already independently audited pixel statistics; no raster resampling,
new extrema search, identity remapping, source guessing, or SEM estimation.
Original GIS, SAV, XLSX and AMW inputs are never edited.
"""

import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "NDVI_同号公园复核与区域均值_20261111"
PREVIOUS = ROOT / "NDVI_区域平均值_20261111_核对版"
AUDIT = ROOT / "NDVI_sem_sensitivity_work" / "old_extrema_source_audit"
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
sys.path.insert(0, str(PREVIOUS / "scripts"))
from build_review_package import xlsx, write_shapefile
from compute_regional_means import load_geometry
from audit_vectors_std import read_shp, ring_stats
from verify_pack import verify

FIELDS = ("ndvi_inside_min", "ndvi_inside_max", "ndvi_outside_min", "ndvi_outside_max")


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def precision_match(values, old):
    if any(value is None for value in values):
        return False
    return all(Decimal.from_float(value).quantize(
        Decimal(1).scaleb(Decimal(old[field]).as_tuple().exponent),
        rounding=ROUND_HALF_UP) == Decimal(old[field])
        for field, value in zip(FIELDS, values))


def write_rows(path, rows, delimiter=","):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, delimiter=delimiter)
        writer.writerows(rows)


def json_file(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                               allow_nan=False), encoding="utf-8")


def archive_directory(folder, archive_path, manifest_name="文件校验清单.json"):
    assert folder.resolve().is_relative_to(ROOT.resolve())
    assert archive_path.resolve().parent == ROOT.resolve()
    files = sorted(path for path in folder.rglob("*") if path.is_file()
                   and "__pycache__" not in path.parts and path.name != manifest_name)
    manifest = [{"path": p.relative_to(folder).as_posix(),
                 "bytes": p.stat().st_size, "sha256": digest(p)} for p in files]
    json_file(folder / manifest_name, manifest)
    files.append(folder / manifest_name)
    with zipfile.ZipFile(archive_path, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, (Path(folder.name) / path.relative_to(folder)).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files)
        for entry in manifest:
            payload = archive.read((Path(folder.name) / entry["path"]).as_posix())
            assert len(payload) == entry["bytes"]
            assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    return {"archive": archive_path.name, "files": len(files),
            "bytes": archive_path.stat().st_size, "sha256": digest(archive_path)}


def update_previous_notices():
    notice = ROOT / "NDVI_重要更正_编号对应与数据使用状态_20261111.txt"
    specifications = [
        ("NDVI_区域平均值_20261111_核对版", "package_file_manifest.json"),
        ("NDVI_四组合SEM敏感性分析_20261111", "文件校验清单.json"),
        ("NDVI_旧极值追溯与公园编号核对_20261111", "文件校验.json"),
    ]
    updates = []
    for name, manifest_name in specifications:
        folder = ROOT / name
        # Existing historical filenames are retained, but their contents now
        # explicitly withdraw the unsupported cross-ID identity interpretation.
        for old_notice in folder.glob("0_重要更正_*.txt"):
            shutil.copy2(notice, old_notice)
        archive = ROOT / (name + ".zip")
        if not archive.exists():
            continue
        backup = ROOT / (name + "_跨号判读历史存档.zip")
        temporary = ROOT / (name + "_同号说明更新临时.zip")
        assert all(p.resolve().is_relative_to(ROOT.resolve())
                   for p in (folder, archive, backup, temporary))
        if backup.exists() or temporary.exists():
            raise FileExistsError("Refusing to overwrite a prior audit backup/temp file")
        before = digest(archive)
        shutil.copy2(archive, backup)
        assert digest(backup) == before
        result = archive_directory(folder, temporary, manifest_name)
        temporary.replace(archive)  # Our generated ZIP, exact backup verified.
        updates.append({"archive": archive.name, "previous_zip_backup": backup.name,
                        "previous_sha256": before, "updated_sha256": result["sha256"]})
    return updates


def main():
    archive = ROOT / (OUT.name + ".zip")
    workbook = OUT / "39公园NDVI区域均值与同号核对.xlsx"
    if workbook.exists() or archive.exists():
        raise FileExistsError("Refusing to overwrite an existing same-number handoff")
    OUT.mkdir(exist_ok=True)
    scan = read_json(ROOT / "NDVI_mean_work" / "regional_mean_source_scan.json")
    cross = read_json(AUDIT / "independent_old_extrema_cross_id.json")
    links = read_json(AUDIT / "shp_shx_dbf_link_qc_independent.json")
    assert links["all_structural_checks_pass"]
    with (ROOT / "17 NDVI補足資料S1.tsv").open(encoding="utf-8-sig", newline="") as stream:
        old_rows = list(csv.DictReader(stream, delimiter="\t"))
    old_by_id = {int(row["park_code"][1:]): row for row in old_rows}
    assert sorted(old_by_id) == list(range(1, 40))
    assert [row["ParkID"] for row in scan["parks"]] == list(range(1, 40))
    indep = {(row["current_geometry_park_id"], row["source_raster"]): row
             for row in cross["independently_recomputed_candidates"]}

    numeric = [["ParkID", "source_raster", "ndvi_inside_area_mean",
                "ndvi_outside_100m_ring_area_mean", "inside_valid_pixels",
                "outside_valid_pixels", "inside_min", "inside_max",
                "outside_min", "outside_max", "source_status",
                "z_inside_area_mean", "z_outside_area_mean"]]
    options = [["ParkID", "source_raster", "inside_area_mean", "outside_ring_area_mean",
                "inside_valid_pixels", "outside_valid_pixels",
                "inside_min", "inside_max", "outside_min", "outside_max",
                "same_ID_old_extrema_ring_match", "same_ID_old_extrema_full_buffer_match"]]
    comparison = [["ParkID", "source_raster", *["old_" + f for f in FIELDS],
                   "current_inside_min", "current_inside_max", "current_outside_min",
                   "current_outside_max", "inside_valid_pixels", "outside_valid_pixels",
                   "same_ID_old_ring_match", "same_ID_old_full_buffer_match", "usable_source"]]
    identity = [["SEM_ParkID", "address_Excel_NO", "old_S1_park_code",
                 "GIS_SHP_record", "GIS_DBF_row", "author_identity_confirmed",
                 "same_number_GIS_label_check", "cross_ID_remap_used"]]
    history = [["old_S1_ParkID", "same_number_identity_for_new_data",
                "numerical_fingerprint_matching_GIS_records",
                "matching_source_files", "numeric_status_not_identity_decision"]]
    summaries, pending = [], []
    all_same_ring, all_same_full = set(), set()
    for row in scan["parks"]:
        pid, chosen = row["ParkID"], row["selected"]
        old = old_by_id[pid]
        identity.append([pid, pid, old["park_code"], pid, pid, "YES", "PASS", "NO"])
        status = "ONE_AVAILABLE_SOURCE" if chosen else "SOURCE_NOT_SELECTED"
        if chosen:
            ins, ext = chosen["inside"], chosen["outside"]
            numeric.append([pid, chosen["source_raster"], ins["mean"], ext["mean"],
                            ins["valid_n"], ext["valid_n"], ins["minimum"], ins["maximum"],
                            ext["minimum"], ext["maximum"], status, None, None])
        else:
            pending.append(pid)
            numeric.append([pid, None, None, None, None, None,
                            None, None, None, None, status, None, None])
        matches_this_id = []
        usable_sources = []
        for candidate in row["candidates"]:
            ins, ext = candidate["inside"], candidate["outside"]
            independent = indep[(pid, candidate["source_raster"])]
            assert independent["all_count_and_stat_differences_zero"]
            values = [ins["minimum"], ins["maximum"], ext["minimum"], ext["maximum"]]
            full = ([values[0], values[1], min(values[0], values[2]), max(values[1], values[3])]
                    if all(value is not None for value in values) else [None] * 4)
            ring_match, full_match = precision_match(values, old), precision_match(full, old)
            if ring_match:
                all_same_ring.add(pid)
            if full_match:
                all_same_full.add(pid)
            if ring_match or full_match:
                matches_this_id.append(candidate["source_raster"])
            usable = candidate["full_extent"] and all(
                candidate[s]["valid_n"] > 0 and candidate[s]["out_of_range_n"] == 0
                for s in ("inside", "outside"))
            comparison.append([pid, candidate["source_raster"], *[float(old[f]) for f in FIELDS],
                               *values, ins["valid_n"], ext["valid_n"],
                               "YES" if ring_match else "NO", "YES" if full_match else "NO",
                               "YES" if usable else "NO"])
            if usable:
                usable_sources.append(candidate["source_raster"])
                if chosen is None:
                    options.append([pid, candidate["source_raster"], ins["mean"], ext["mean"],
                                    ins["valid_n"], ext["valid_n"], *values,
                                    "YES" if ring_match else "NO", "YES" if full_match else "NO"])
        summaries.append({"ParkID": pid, "same_number_identity": True,
                          "source_status": status,
                          "chosen_current_source": chosen["source_raster"] if chosen else None,
                          "usable_sources": usable_sources,
                          "same_number_old_extrema_matching_sources": sorted(set(matches_this_id)),
                          "historical_original_source_confirmed": False})
    assert pending == [9, 18, 28, 32]
    assert len(numeric) == len(identity) == 40
    assert len(options) == 9 and len(comparison) == 53
    for row in cross["all_old_rows_cross_id"]:
        history.append([row["old_s1_id"], row["old_s1_id"],
                        ",".join(map(str, row["matched_geometry_ids"])),
                        ";".join(sorted({m["source_raster"] for m in row["four_extrema_matches"]})),
                        "NUMERIC_CLUE_ONLY" if row["four_extrema_matches"] else "NO_NUMERIC_MATCH"])
    notes = [["項目 / Item", "説明 / Explanation"],
             ["编号", "作者确认所有ParkID、地址NO、S1 Pxx为同号1—39；P及前导0仅为格式。本版不重排。"],
             ["此前跨号表", "填写要求已撤销。跨行极值吻合保留为旧数值线索，不作为身份对应。"],
             ["本版状态", "35园有唯一当前可用来源；4园各两套候选。不是39园来源全部选定后的最终SEM输入。"],
             ["园内", "提供的公园边界全域。"],
             ["园外", "提供的约100m外扩面扣除对应公园内部后的环带。"],
             ["区域均值", "每个区域全部有效NDVI像元之和除以有效像元数，不再使用最大/最小值中间值。"],
             ["像元规则", "原30m格网像元中心位于选区；不重采样。NoData及非有限值排除，有效负值和0保留。"],
             ["Z标准化", "待39园来源选定后，园内/园外分别以39个均值计算Z=(该园均值−39园均值平均)/样本标准差；样本方差分母38。本主表Z留空，未对35园先标准化。"],
             ["旧极值复现", "逐字段按旧S1保留的小数位核对；同时检查真正外环带及包含园内的完整缓冲面。"],
             ["来源判定", "ONE_AVAILABLE_SOURCE只表示现有文件中一个来源满足覆盖及有效值条件，不表示历史原操作或影像产品/时段已全部认证。"],
             ["SEM文件", "原SAV、双语Excel、AMW及另外14变量均未修改；未产生新的正式Amos输出。"],
             ["GIS源包", "含43组选区的原始像元裁切、mask、39园边界和外环带及逐像元数据。裁切保持原格网和像元值，不是新下载影像。"],
             ["位置保密", "表不含名称/地址；GIS仍可识别地点，仅供作者及教授内部核对。"],
             ["复算", "python scripts/verify_pack.py 可从所附裁切及mask重新求均值，无需第三方Python库。"],
             ["QGIS工程", "为本轮生成的相对路径复核工程，不是原操作工程；XML/路径已验证，本机未实际打开QGIS GUI。"]]
    xlsx(workbook, [("公園別地域平均", numeric), ("4公園候補", options),
                    ("同号旧極値照合", comparison), ("番号確認", identity),
                    ("旧数値診断_不作改号", history), ("方法と状態", notes)])
    write_rows(OUT / "39公园NDVI区域均值_同号.csv", numeric)
    write_rows(OUT / "4园候选来源_区域均值.csv", options)
    write_rows(OUT / "同号旧极值逐来源核对.tsv", comparison, "\t")
    write_rows(OUT / "39公园编号确认.tsv", identity, "\t")

    shutil.copytree(PREVIOUS / "GIS", OUT / "GIS", dirs_exist_ok=True)
    shutil.copy2(PREVIOUS / "NDVI区域均值复核.qgs", OUT / "NDVI区域均值复核.qgs")
    shutil.copy2(PREVIOUS / "source_manifest.json", OUT / "原地区影像与边界校验.json")
    shutil.copytree(PREVIOUS / "scripts", OUT / "scripts", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copy2(Path(__file__), OUT / "scripts" / Path(__file__).name)
    extraction = read_json(OUT / "GIS" / "pixel_extractions.json")
    for entry in extraction:
        entry["status"] = "ONE_AVAILABLE_SOURCE" if entry["ParkID"] not in pending else "SOURCE_NOT_SELECTED"
    json_file(OUT / "GIS" / "pixel_extractions.json", extraction)
    pairs, prj = load_geometry(ROOT / "NDVI")
    attributes = []
    for row in numeric[1:]:
        attributes.append({"ParkID": row[0], "MeanIn": row[2], "MeanOut": row[3],
                           "NIn": row[4], "NOut": row[5],
                           "Status": "ONE_SOURCE" if row[0] not in pending else "CHOOSE_SOURCE"})
    def orient(ring, clockwise):
        return list(reversed(ring)) if (ring_stats(ring)["signed_area"] > 0) == clockwise else ring
    write_shapefile(OUT / "GIS" / "park_boundaries.shp",
                    [[orient(p["park"], True)] for p in pairs], attributes, prj)
    write_shapefile(OUT / "GIS" / "outer_100m_rings.shp",
                    [[orient(p["buffer"], True), orient(p["park"], False)] for p in pairs], attributes, prj)
    write_shapefile(OUT / "GIS" / "full_100m_buffers.shp",
                    [[orient(p["buffer"], True)] for p in pairs], attributes, prj)
    qc = OUT / "QC"
    qc.mkdir(exist_ok=True)
    for filename in ("shp_shx_dbf_link_qc_independent.json", "native_crs_footprints.json"):
        shutil.copy2(AUDIT / filename, qc / filename)
    geography = AUDIT / "address_region_geometry_screen.json"
    if geography.exists():
        shutil.copy2(geography, qc / geography.name)
    independent_qc = Path(__file__).with_name("qc_same_number_handoff_independent.json")
    if independent_qc.exists():
        shutil.copy2(independent_qc, qc / independent_qc.name)
    pixel_qc = verify(OUT)
    assert pixel_qc["options_verified"] == 43
    assert pixel_qc["regions_verified"] == 86
    assert pixel_qc["maximum_mean_difference"] == 0
    json_file(qc / "所附像元重新求均值核对.json", pixel_qc)
    for name in ("park_boundaries", "outer_100m_rings", "full_100m_buffers"):
        shp = read_shp(OUT / "GIS" / (name + ".shp"))
        assert shp["records"] == 39 and shp["index_matches_shp"] and shp["parsed_to_end"]
    for layer in ET.parse(OUT / "NDVI区域均值复核.qgs").findall("./projectlayers/maplayer"):
        path = (OUT / layer.findtext("datasource")).resolve()
        assert path.is_relative_to(OUT.resolve()) and path.is_file()
    with zipfile.ZipFile(workbook) as book:
        assert book.testzip() is None
        for name in book.namelist():
            if name.endswith((".xml", ".rels")):
                ET.fromstring(book.read(name))
    protected = {
        ROOT / "最终用于sem的匿名39✖16输入矩阵.sav": "54cca5a9e38faf59635ebcd9d645d7d77083ac30c7f2d8f46751d809c47d2737",
        ROOT / "amos模型.amw": "19410f39905c9ea51909b5bb2fad3e6cad35f32dde2c3bd859c968de014371a1",
    }
    bilingual_qc = read_json(ROOT / "NDVI_sem_sensitivity_work" / "qa_new_bilingual_excel_original.json")
    protected[ROOT / bilingual_qc["xlsx_file"]] = bilingual_qc["xlsx_sha256"]
    for path, expected in protected.items():
        assert digest(path) == expected
    report = {"identity_policy": "Author-confirmed same park identities 1–39; no renumbering",
              "all_39_structural_ID_checks_pass": True,
              "old_cross_ID_form_no_longer_required": True,
              "unique_current_source_parks": 35, "source_pending_ParkID": pending,
              "same_ID_old_four_extrema_ring_match_ParkID": sorted(all_same_ring),
              "same_ID_old_four_extrema_full_buffer_match_ParkID": sorted(all_same_full),
              "cross_row_numeric_matches_are_not_identity_crosswalks": True,
              "final_39_park_Z_values_generated": False,
              "original_SEM_SAV_XLSX_AMW_unchanged_sha256_verified": True,
              "mean_definition": "Arithmetic mean of all finite non-NoData pixel-centre values in each region",
              "exterior": "Supplied approx100m expanded buffer minus same-number park interior",
              "all_43_extraction_options_pixel_mean_verified": True,
              "maximum_pixel_mean_recalculation_difference": pixel_qc["maximum_mean_difference"],
              "per_park": summaries}
    json_file(OUT / "同号核对与数据状态.json", report)
    update_results = update_previous_notices()
    json_file(OUT / "历史说明更正及ZIP存档.json", update_results)
    result = archive_directory(OUT, archive)
    print(json.dumps({"workbook": str(workbook), **result,
                      "confirmed_same_number_parks": 39, "one_available_source_parks": 35,
                      "unselected_source_ParkID": pending,
                      "same_ID_old_ring_matches": sorted(all_same_ring),
                      "same_ID_old_full_buffer_matches": sorted(all_same_full),
                      "old_identity_claim_corrected": True,
                      "original_SEM_files_unchanged": True}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
