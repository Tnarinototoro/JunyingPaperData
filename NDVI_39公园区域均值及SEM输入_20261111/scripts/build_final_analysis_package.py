"""Package selected 39-park GIS pixels, data inputs and honest SEM diagnostics.

Original regional images are not duplicated here; a separate original-source
ZIP contains them. The included crops keep original grid and Float32 values.
"""

import csv
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(__file__).resolve().parent
OUT = ROOT / "NDVI_39公园区域均值及SEM输入_20261111"
PRIOR = ROOT / "NDVI_同号公园复核与区域均值_20261111"
SEM = ROOT / "NDVI_sem_completion_work"
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
sys.path.insert(0, str(PRIOR / "scripts"))
sys.path.insert(0, str(ROOT / "NDVI_same_number_work"))
from build_review_package import xlsx, write_shapefile
from compute_regional_means import load_geometry
from audit_vectors_std import ring_stats, read_shp
from verify_pack import verify
from build_same_number_handoff import archive_directory


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                               allow_nan=False), encoding="utf-8")


def selected_qgs(source, destination, old_to_new):
    project = ET.parse(source)
    layers = project.find("./projectlayers")
    kept, changed_names, changed_sources = set(), {}, {}
    for layer in list(layers):
        old_source = layer.findtext("datasource")
        if "/rasters/" in old_source:
            if old_source not in old_to_new:
                layers.remove(layer)
                continue
            new_source = old_to_new[old_source]
            layer.find("datasource").text = new_source
            label = Path(new_source).stem.replace("_", " ")
            layer.find("layername").text = label
            changed_names[layer.findtext("id")] = label
            changed_sources[layer.findtext("id")] = new_source
        kept.add(layer.findtext("id"))
    def prune(parent):
        for child in list(parent):
            if child.tag == "layer-tree-layer":
                identity = child.get("id")
                if identity not in kept:
                    parent.remove(child)
                    continue
                if identity in changed_names:
                    child.set("name", changed_names[identity])
                    child.set("source", changed_sources[identity])
            else:
                prune(child)
                if child.tag == "layer-tree-group" and not child.findall(".//layer-tree-layer"):
                    parent.remove(child)
    tree = project.find("./layer-tree-group")
    if tree is not None:
        prune(tree)
    for layer in layers:
        resolved = (OUT / layer.findtext("datasource")).resolve()
        assert resolved.is_relative_to(OUT.resolve()) and resolved.is_file()
    assert len(layers) == 80  # Two vector layers plus 39 NDVI and 39 masks.
    project.write(destination, encoding="utf-8", xml_declaration=True)
    return 80


def main():
    archive = ROOT / (OUT.name + ".zip")
    workbook = OUT / "39公园NDVI区域均值及Z值.xlsx"
    if archive.exists() or workbook.exists():
        raise FileExistsError("Refusing to overwrite an existing final package")
    selection = load(WORK / "frame_margin_selection.json")
    input_qc = load(OUT / "QC" / "39园NDVI与两份SEM输入保存核对.json")
    independent = load(WORK / "qc_final_selected_inputs_independent.json")
    assert independent["all_checks_pass"]
    with (OUT / "39公园NDVI区域均值及Z值.csv").open(encoding="utf-8-sig", newline="") as stream:
        raw_rows = list(csv.DictReader(stream))
    assert [int(r["ParkID"]) for r in raw_rows] == list(range(1, 40))
    with (SEM / "selected_frame_margin_ndvi_means_and_z.csv").open(encoding="utf-8-sig", newline="") as stream:
        sem_rows = list(csv.DictReader(stream))
    for actual, used in zip(raw_rows, sem_rows):
        assert int(actual["ParkID"]) == int(used["ParkID"])
        assert actual["source_raster"] == used["source_raster"]
        for a, b in (("ndvi_inside_area_mean", "inside_mean"),
                     ("ndvi_outside_100m_ring_area_mean", "outside_mean"),
                     ("z_inside_area_mean", "z_inside"), ("z_outside_area_mean", "z_outside")):
            assert abs(float(actual[a]) - float(used[b])) < 1e-14
    fields = list(raw_rows[0])
    numeric = [fields] + [[r[f] if f == "source_raster" else float(r[f]) for f in fields] for r in raw_rows]
    stats = [["範囲 / Region", "n", "39園平均 / Across-park mean", "標本SD / Sample SD", "標本分散の分母"],
             ["公園内部 / Interior", 39, input_qc["inside_standardization"]["mean"],
              input_qc["inside_standardization"]["sample_sd"], 38],
             ["公園外100m環帯 / Exterior ring", 39, input_qc["outside_standardization"]["mean"],
              input_qc["outside_standardization"]["sample_sd"], 38]]
    four = [["ParkID", "selected_source", "selected_min_frame_margin_m", "other_source", "other_min_frame_margin_m"]]
    for park in selection["parks"]:
        if park["ParkID"] in (9, 18, 28, 32):
            alternative = next(c for c in park["candidates"]
                               if c["source_raster"] != park["selected_source_raster"]
                               and c["eligible_for_frame_margin_selection"])
            four.append([park["ParkID"], park["selected_source_raster"], park["selected_frame_margin_m"],
                         alternative["source_raster"], alternative["frame_margin_m"]])
    notes = [["項目 / Item", "説明 / Explanation"],
             ["内部", "作者提供的公园边界全域。18/28以现有外环整体统计，未按行政地区数新造边界。"],
             ["外部", "原约100m外扩面扣除对应公园内部，得到外部环带。"],
             ["平均", "选区内全部有限、非NoData的原30m像元值之和除以有效像元数；像元中心纳入，不重采样。"],
             ["NoData", "有效0和负值保留；NoData不补0。P27外部600纳入像元中598有效、2 NoData。"],
             ["选片", "本轮新的可复现空间规则：在满足覆盖及有效值条件的候选中，选择选区距TIFF矩形边界最小净距较大者。不是原影像来源复原或云量/日期质量证明，也不按SEM选优。"],
             ["Z公式", "Z=(该园区域均值−39园区域均值的平均)/39园样本标准差；内部、外部分别计算，样本方差分母38。"],
             ["数据更新", "原SAV和双语Excel的NDVI末两列已更新；其他14列和ParkID精确不变；原件在00_原始数据备份。"],
             ["影像", "使用作者现有NDVI层，未新下载影像；NDBI未使用，未用其他公园均值或中位数填补。"],
             ["SEM", "独立计算不是Amos原生输出。原固定模型本轮出现负EQ方差，所附系数是诊断记录，不作论文标准化结果图。"],
             ["位置", "数值表不含名称地址；GIS可识别位置，只供作者及教授内部使用。"]]
    xlsx(workbook, [("NDVI平均値とZ_39公園", numeric), ("Z標準化の統計", stats),
                    ("4公園の空間選片", four), ("方法とデータ状態", notes)])
    gis = OUT / "GIS"
    crops = gis / "rasters"
    crops.mkdir(parents=True, exist_ok=True)
    previous = load(PRIOR / "GIS" / "pixel_extractions.json")
    by_pair = {(e["ParkID"], e["source_raster"]): e for e in previous}
    selected, selected_labels, old_to_new = [], {}, {}
    for park in selection["parks"]:
        pid = park["ParkID"]
        entry = dict(by_pair[(pid, park["selected_source_raster"])])
        assert entry["inside"]["mean"] == park["inside_mean"]
        assert entry["outside"]["mean"] == park["outside_mean"]
        selected_labels[pid] = entry["label"]
        label = f"P{pid:02d}"
        for field, suffix in (("ndvi_crop", "NDVI"), ("zone_mask", "zones")):
            old = entry[field]
            new = f"GIS/rasters/{label}_{suffix}.tif"
            shutil.copy2(PRIOR / old, OUT / new)
            old_to_new["./" + old] = "./" + new
            entry[field] = new
        entry["label"], entry["status"] = label, "SELECTED_SPATIAL_RULE"
        selected.append(entry)
    save(gis / "pixel_extractions.json", selected)
    pixel_count = 0
    with (PRIOR / "GIS" / "valid_pixels.csv").open(encoding="utf-8-sig", newline="") as src, \
         (gis / "valid_pixels.csv").open("w", encoding="utf-8-sig", newline="") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            pid = int(row["ParkID"])
            if row["source_option_label"] == selected_labels[pid]:
                row["source_option_label"] = f"P{pid:02d}"
                writer.writerow(row)
                pixel_count += 1
    assert pixel_count == sum(e[s]["valid_n"] for e in selected for s in ("inside", "outside"))
    pairs, prj = load_geometry(ROOT / "NDVI")
    attrs = [{"ParkID": e["ParkID"], "MeanIn": e["inside"]["mean"], "MeanOut": e["outside"]["mean"],
              "NIn": e["inside"]["valid_n"], "NOut": e["outside"]["valid_n"], "Status": "SELECTED"} for e in selected]
    def orient(ring, clockwise):
        return list(reversed(ring)) if (ring_stats(ring)["signed_area"] > 0) == clockwise else ring
    for name, geometries in (("park_boundaries", [[orient(p["park"], True)] for p in pairs]),
                             ("outer_100m_rings", [[orient(p["buffer"], True), orient(p["park"], False)] for p in pairs]),
                             ("full_100m_buffers", [[orient(p["buffer"], True)] for p in pairs])):
        write_shapefile(gis / (name + ".shp"), geometries, attrs, prj)
        audit = read_shp(gis / (name + ".shp"))
        assert audit["records"] == 39 and audit["index_matches_shp"]
    layers = selected_qgs(PRIOR / "NDVI区域均值复核.qgs", OUT / "39公园NDVI区域均值复核.qgs", old_to_new)
    scripts = OUT / "scripts"
    scripts.mkdir(exist_ok=True)
    for path in (PRIOR / "scripts").glob("*.py"):
        shutil.copy2(path, scripts / path.name)
    for path in WORK.glob("*.py"):
        shutil.copy2(path, scripts / path.name)
    shutil.copy2(ROOT / ".paper15_work" / "read_numeric_sav.py", scripts / "read_numeric_sav.py")
    shutil.copy2(ROOT / "NDVI_sem_sensitivity_work" / "sem_covariance_ml.py", scripts / "sem_covariance_ml.py")
    for filename in ("check_composite_ml.py", "selected_frame_margin_same_model.py"):
        shutil.copy2(SEM / filename, scripts / filename)
    qc = OUT / "QC"
    for filename in ("frame_margin_selection.json", "frame_margin_candidates.csv",
                     "frame_margin_selected_39.csv", "dual_source_grid_mask_audit.json",
                     "qc_final_selected_inputs_independent.json"):
        shutil.copy2(WORK / filename, qc / filename)
    audit_root = ROOT / "NDVI_sem_sensitivity_work" / "old_extrema_source_audit"
    for filename in ("four_supplied_geometry_extent_qc.json", "shp_shx_dbf_link_qc_independent.json"):
        shutil.copy2(audit_root / filename, qc / filename)
    shutil.copytree(audit_root / "private_four_outlines", qc / "private_four_outlines", dirs_exist_ok=True)
    shutil.copy2(PRIOR / "原地区影像与边界校验.json", OUT / "原地区影像与边界校验.json")
    sem_out = OUT / "SEM复算记录_非Amos原生结果"
    sem_out.mkdir(exist_ok=True)
    for path in SEM.glob("selected_frame_margin_*"):
        if path.is_file():
            shutil.copy2(path, sem_out / path.name)
    pixel_qc = verify(OUT)
    assert pixel_qc["options_verified"] == 39 and pixel_qc["regions_verified"] == 78
    assert pixel_qc["maximum_mean_difference"] == 0
    save(qc / "最终39园78选区像元均值复算.json", pixel_qc)
    summary = {"final_current_spatial_source_selection_complete": True,
               "historical_source_identification_claimed": False, "parks": 39,
               "mean_values": 78, "Z_values": 78, "missing_park_NDVI_values": 0,
               "cross_park_mean_median_imputation": False,
               "selected_native_valid_pixel_rows": pixel_count, "QGIS_layers": layers,
               "QGIS_XML_paths_checked": True, "QGIS_GUI_opened": False,
               "all_pixel_means_reproduced_exactly": True,
               "root_SAV_XLSX_updated_with_verified_original_backups": True,
               "ParkID_and_14_other_columns_preserved_exactly": True,
               "source_selection_excluded_SEM_fit": True,
               "new_AMW_structure_and_constraints_unchanged": True,
               "native_Amos_run": False, "independent_same_model_ML_run": True,
               "valid_final_standardized_SEM_figure_generated": False,
               "reason_no_final_SEM_figure": "Inadmissible negative EQ latent variance in the independent original-model refit"}
    save(OUT / "本轮交付状态.json", summary)
    result = archive_directory(OUT, archive)
    print(json.dumps({**summary, **result, "workbook": str(workbook)}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
