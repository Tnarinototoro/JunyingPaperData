"""Read-only same-number workbook/CSV QC; no source choice or package edits."""

import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "NDVI_同号公园复核与区域均值_20261111"
NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
RNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FIELDS = ["ndvi_inside_min", "ndvi_inside_max", "ndvi_outside_min", "ndvi_outside_max"]


def jread(path):
    return json.loads(path.read_text(encoding="utf-8"))


def cread(path, delimiter=","):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file, delimiter=delimiter))


def col_index(address):
    number = 0
    for letter in re.sub(r"\d", "", address):
        number = number * 26 + ord(letter) - 64
    return number - 1


def workbook_tables(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Workbook ZIP failed CRC validation")
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(node.text or "" for node in item.iter("{" + NS + "}t"))
                      for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        book = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = {node.get("Id"): node.get("Target") for node in
                ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        for sheet in book.find("{" + NS + "}sheets"):
            target = rels[sheet.get("{" + RNS + "}id")]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            xml = ET.fromstring(archive.read(part))
            rows = []
            formula_count = 0
            for row in xml.iter("{" + NS + "}row"):
                values = {}
                for cell in row.findall("{" + NS + "}c"):
                    formula_count += cell.find("{" + NS + "}f") is not None
                    value = cell.find("{" + NS + "}v")
                    if cell.get("t") == "inlineStr":
                        decoded = "".join(node.text or "" for node in cell.iter("{" + NS + "}t"))
                    elif cell.get("t") == "s":
                        decoded = shared[int(value.text)]
                    elif value is not None and value.text is not None:
                        decoded = float(value.text)
                    else:
                        decoded = None
                    values[col_index(cell.get("r"))] = decoded
                rows.append(values)
            width = max(rows[0]) + 1
            header = [rows[0].get(index) for index in range(width)]
            data = [{name: row.get(index) for index, name in enumerate(header)} for row in rows[1:]]
            result[sheet.get("name")] = {"header": header, "rows": data, "formula_count": formula_count}
    return result


def display_interval_match(value, text):
    if value is None:
        return False
    original = Decimal(text)
    half = Decimal(1).scaleb(original.as_tuple().exponent) / 2
    actual = Decimal.from_float(float(value))
    # HALF_UP display interval, independent of production quantize implementation.
    if original > 0:
        return original - half <= actual < original + half
    if original < 0:
        return original - half < actual <= original + half
    return -half < actual < half


def old_match(values, original):
    return all(display_interval_match(value, original[field]) for field, value in zip(FIELDS, values))


def equal_cell(cell, csv_text):
    if csv_text == "":
        return cell in (None, "")
    if isinstance(cell, (int, float)):
        try:
            return float(csv_text) == cell
        except ValueError:
            return False
    return str(cell) == csv_text


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def main():
    book = workbook_tables(OUT / "39公园NDVI区域均值与同号核对.xlsx")
    original = {int(row["park_code"][1:]): row for row in cread(ROOT / "17 NDVI補足資料S1.tsv", "\t")}
    scan = {row["ParkID"]: row for row in jread(ROOT / "NDVI_mean_work" / "regional_mean_source_scan.json")["parks"]}
    main_table = book["公園別地域平均"]["rows"]
    options = book["4公園候補"]["rows"]
    comparison = book["同号旧極値照合"]["rows"]
    identity = book["番号確認"]["rows"]
    state = jread(OUT / "同号核对与数据状态.json")
    checks = {"main_exact_ID_order_1_to_39": [int(row["ParkID"]) for row in main_table] == list(range(1, 40)),
              "final_78_Z_cells_blank": len(main_table) == 39 and all(row.get(key) in (None, "")
                                           for row in main_table for key in ["z_inside_area_mean", "z_outside_area_mean"]),
              "no_workbook_formulas": all(table["formula_count"] == 0 for table in book.values()),
              "same_number_identity_rows": len(identity) == 39 and all(
                  int(row["SEM_ParkID"]) == int(row["address_Excel_NO"]) == int(row["GIS_SHP_record"])
                  == int(row["GIS_DBF_row"]) == int(row["old_S1_park_code"][1:])
                  and row["author_identity_confirmed"] == "YES" and row["cross_ID_remap_used"] == "NO"
                  for row in identity),
              "history_not_used_to_reassign_ID": all(int(row["old_S1_ParkID"]) == int(row["same_number_identity_for_new_data"])
                      and row["numeric_status_not_identity_decision"] in ("NUMERIC_CLUE_ONLY", "NO_NUMERIC_MATCH")
                      for row in book["旧数値診断_不作改号"]["rows"]),
              "historical_original_source_not_claimed_confirmed": all(not row["historical_original_source_confirmed"]
                                                                        for row in state["per_park"])}
    mean_max_diff, numeric_mismatches, pending, available = 0.0, [], [], []
    for row in main_table:
        pid = int(row["ParkID"])
        chosen = scan[pid]["selected"]
        if chosen is None:
            pending.append(pid)
            if row["source_status"] != "SOURCE_NOT_SELECTED" or any(row.get(key) not in (None, "")
               for key in ["source_raster", "ndvi_inside_area_mean", "ndvi_outside_100m_ring_area_mean"]):
                numeric_mismatches.append({"ParkID": pid, "kind": "unselected_source_not_blank"})
            continue
        available.append(pid)
        expected = {"source_raster": chosen["source_raster"], "source_status": "ONE_AVAILABLE_SOURCE"}
        for side, mean_name, count_name in [("inside", "ndvi_inside_area_mean", "inside_valid_pixels"),
                                          ("outside", "ndvi_outside_100m_ring_area_mean", "outside_valid_pixels")]:
            expected.update({mean_name: chosen[side]["mean"], count_name: chosen[side]["valid_n"],
                             side + "_min": chosen[side]["minimum"], side + "_max": chosen[side]["maximum"]})
            mean_max_diff = max(mean_max_diff, abs(row[mean_name] - chosen[side]["mean"]))
        if any(row.get(key) != value for key, value in expected.items()):
            numeric_mismatches.append({"ParkID": pid, "kind": "chosen_source_or_value_difference"})
    checks["35_values_and_sources_exactly_match_reliable_scan"] = len(available) == 35 and not numeric_mismatches and mean_max_diff == 0
    checks["four_pending_IDs_are_9_18_28_32"] = pending == [9, 18, 28, 32]
    usable_pairs = {}
    for pid in pending:
        for candidate in scan[pid]["candidates"]:
            if candidate["full_extent"] and all(candidate[side]["valid_n"] > 0 and candidate[side]["out_of_range_n"] == 0
                                                for side in ("inside", "outside")):
                usable_pairs[(pid, candidate["source_raster"])] = candidate
    candidate_mismatches = []
    for row in options:
        key = (int(row["ParkID"]), row["source_raster"])
        expected = usable_pairs.get(key)
        if not expected:
            candidate_mismatches.append({"ParkID": key[0], "kind": "unexpected_candidate"})
            continue
        values = [expected["inside"]["minimum"], expected["inside"]["maximum"],
                  expected["outside"]["minimum"], expected["outside"]["maximum"]]
        wanted = {"inside_area_mean": expected["inside"]["mean"], "outside_ring_area_mean": expected["outside"]["mean"],
                  "inside_valid_pixels": expected["inside"]["valid_n"], "outside_valid_pixels": expected["outside"]["valid_n"],
                  "inside_min": values[0], "inside_max": values[1], "outside_min": values[2], "outside_max": values[3]}
        if any(row[field] != value for field, value in wanted.items()):
            candidate_mismatches.append({"ParkID": key[0], "kind": "candidate_value_difference"})
    checks["four_parks_eight_candidates_exact"] = (len(options) == len(usable_pairs) == 8 and not candidate_mismatches
                and {(int(row["ParkID"]), row["source_raster"]) for row in options} == set(usable_pairs))
    ring_ids, full_ids, precision_errors = set(), set(), []
    for row in comparison:
        pid = int(row["ParkID"])
        values = [row.get(field) for field in ["current_inside_min", "current_inside_max", "current_outside_min", "current_outside_max"]]
        full = [values[0], values[1], min(values[0], values[2]), max(values[1], values[3])] if all(value is not None for value in values) else [None] * 4
        ring, full_match = old_match(values, original[pid]), old_match(full, original[pid])
        if ring:
            ring_ids.add(pid)
        if full_match:
            full_ids.add(pid)
        if (row["same_ID_old_ring_match"] == "YES") != ring or (row["same_ID_old_full_buffer_match"] == "YES") != full_match:
            precision_errors.append({"ParkID": pid, "source_raster": row["source_raster"]})
        if any(row["old_" + field] != float(original[pid][field]) for field in FIELDS):
            precision_errors.append({"ParkID": pid, "kind": "old_extrema_transcription_difference"})
    checks["same_ID_precision_flags_correct"] = not precision_errors
    checks["ring_matches_only_11"] = sorted(ring_ids) == [11]
    checks["full_buffer_matches_11_26_30_31"] = sorted(full_ids) == [11, 26, 30, 31]
    csv_checks = []
    for sheet, filename, delimiter in [("公園別地域平均", "39公园NDVI区域均值_同号.csv", ","),
                                       ("4公園候補", "4园候选来源_区域均值.csv", ","),
                                       ("同号旧極値照合", "同号旧极值逐来源核对.tsv", "\t"),
                                       ("番号確認", "39公园编号确认.tsv", "\t")]:
        rows = cread(OUT / filename, delimiter)
        cells = book[sheet]["rows"]
        csv_checks.append(len(rows) == len(cells) and all(equal_cell(cell.get(field), text)
                         for cell, csv_row in zip(cells, rows) for field, text in csv_row.items()))
    checks["all_four_workbook_tables_match_CSV_TSV"] = all(csv_checks)
    original_qc = jread(ROOT / "NDVI_sem_sensitivity_work" / "qa_new_bilingual_excel_original.json")
    protected = [(ROOT / "最终用于sem的匿名39✖16输入矩阵.sav", original_qc["original_sav_sha256"]),
                 (ROOT / original_qc["xlsx_file"], original_qc["xlsx_sha256"]),
                 (ROOT / "amos模型.amw", "19410f39905c9ea51909b5bb2fad3e6cad35f32dde2c3bd859c968de014371a1")]
    hash_checks = [{"input_kind": kind, "matches_original_hash": sha256(path) == expected}
                   for kind, (path, expected) in zip(["original_SAV", "original_bilingual_XLSX", "original_AMW"], protected)]
    checks["protected_original_SAV_XLSX_AMW_hashes_unchanged"] = all(row["matches_original_hash"] for row in hash_checks)
    report = {"scope": "Independent read-only XLSX XML/CSV and precision interval QA; no raster scan, source selection, SEM or output package edits.",
              "checks": checks, "all_checks_pass": all(checks.values()),
              "available_current_sources_n": len(available), "pending_ParkID": pending,
              "final_Z_cells_confirmed_blank_n": 78, "maximum_main_mean_difference": mean_max_diff,
              "same_ID_ring_match_ParkID": sorted(ring_ids), "same_ID_full_buffer_match_ParkID": sorted(full_ids),
              "numeric_mismatches": numeric_mismatches, "candidate_mismatches": candidate_mismatches,
              "precision_errors": precision_errors, "protected_original_hash_checks": hash_checks,
              "code_review": "Production build uses scan ParkID order and same-ID lookups; cross-row fingerprints are history clues only. No code path writes original GIS/SAV/XLSX/AMW; derived notices/archives are separate.",
              "privacy": "No park names, addresses or coordinates included."}
    target = ROOT / "NDVI_same_number_work" / "qc_same_number_handoff_independent.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
