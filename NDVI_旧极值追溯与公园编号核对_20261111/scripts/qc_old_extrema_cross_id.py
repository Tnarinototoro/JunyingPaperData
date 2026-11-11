"""Read-only independent fixed-geometry extrema and cross-ID source audit.

Every candidate in the existing source scan is reaggregated with the audited
independent sixth-order UTM / winding-mask implementation. No source selection,
distance tuning, row remapping, raster resampling, or SEM runs are performed.
Only anonymous IDs, scalar statistics and source basenames are output.
"""
import csv
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
from audit_vectors_std import read_shp
from qc_regional_means_stdlib import independent_case
from qc_crop_raw_bits import IndependentRows

FIELDS = ("ndvi_inside_min", "ndvi_inside_max", "ndvi_outside_min", "ndvi_outside_max")
TARGET_IDS = (9, 18, 28, 32)
PACKAGE = ROOT / "NDVI_区域平均值_20261111_核对版"


def places(text):
    return max(0, -Decimal(text).as_tuple().exponent)


def compare(actual, old):
    comparisons = []
    for field, value in zip(FIELDS, actual):
        original = old[field]
        digits = places(original)
        unit = Decimal(1).scaleb(-digits)
        expected = Decimal(original)
        rounded = Decimal.from_float(value).quantize(unit, rounding=ROUND_HALF_UP)
        delta = Decimal.from_float(value) - expected
        comparisons.append({
            "field": field, "old_text": original, "decimal_places": digits,
            "rounding_half_step": float(unit / 2), "actual": value,
            "actual_rounded_to_old_precision": str(rounded),
            "actual_minus_old": float(delta),
            "absolute_difference_in_rounding_half_steps": float(abs(delta) / (unit / 2)),
            "matches_original_display_precision": rounded == expected,
        })
    return comparisons


def all_match(comparisons):
    return all(item["matches_original_display_precision"] for item in comparisons)


def extrema_vectors(stats):
    inner, outer = stats["inside"], stats["outside"]
    if not inner["valid_n"] or not outer["valid_n"]:
        return {}
    return {
        "park_plus_exterior_ring": [inner["minimum"], inner["maximum"], outer["minimum"], outer["maximum"]],
        "park_plus_full_expanded_buffer": [inner["minimum"], inner["maximum"],
            min(inner["minimum"], outer["minimum"]), max(inner["maximum"], outer["maximum"])],
    }


def summarize_cross(old, candidates):
    matches, inside_only = [], []
    for candidate in candidates:
        vectors = extrema_vectors(candidate["stats"])
        if not vectors:
            continue
        original_comparison = compare(vectors["park_plus_exterior_ring"], old)
        if all_match(original_comparison[:2]):
            inside_only.append({"current_geometry_park_id": candidate["current_geometry_park_id"],
                "source_raster": candidate["source_raster"], "candidate_label": candidate["candidate_label"],
                "inside_extrema": vectors["park_plus_exterior_ring"][:2]})
        for definition, vector in vectors.items():
            comparisons = compare(vector, old)
            if all_match(comparisons):
                matches.append({"current_geometry_park_id": candidate["current_geometry_park_id"],
                    "source_raster": candidate["source_raster"], "candidate_label": candidate["candidate_label"],
                    "definition": definition, "actual_extrema": vector,
                    "actual_minus_old": [item["actual_minus_old"] for item in comparisons]})
    geometry_ids = sorted({item["current_geometry_park_id"] for item in matches})
    source_pairs = sorted({(item["current_geometry_park_id"], item["source_raster"]) for item in matches})
    old_id = int(old["park_code"][1:])
    return {
        "old_s1_park_code": old["park_code"], "old_s1_id": old_id,
        "old_extrema_text": [old[field] for field in FIELDS],
        "decimal_places_by_field": [places(old[field]) for field in FIELDS],
        "classification": "no_match" if not matches else "unique_geometry" if len(geometry_ids) == 1 else "multiple_geometry_matches",
        "matched_geometry_ids": geometry_ids, "matched_source_pair_count": len(source_pairs),
        "multiple_sources_match": len(source_pairs) > 1,
        "same_number_geometry_among_matches": old_id in geometry_ids,
        "unique_numeric_geometry_has_different_id": len(geometry_ids) == 1 and geometry_ids[0] != old_id,
        "four_extrema_matches": matches, "inside_extrema_only_matches": inside_only,
    }


def crop_bbox_summary(item):
    crop = IndependentRows(PACKAGE / item["ndvi_crop"])
    mask = IndependentRows(PACKAGE / item["zone_mask"])
    values = []
    pixel_digest, mask_digest = hashlib.sha256(), hashlib.sha256()
    try:
        assert crop.bits == 32 and mask.bits == 8
        assert (crop.width, crop.height) == (mask.width, mask.height)
        scale, offset = crop.scale_offset()
        for row in range(crop.height):
            rowbytes, maskbytes = crop.row_bytes(row), mask.row_bytes(row)
            pixel_digest.update(rowbytes)
            mask_digest.update(maskbytes)
            for value in struct.unpack(crop.order + "f" * crop.width, rowbytes):
                if math.isfinite(value) and value != crop.nodata:
                    values.append(value * scale + offset)
        return {"valid_n": len(values), "minimum": min(values), "maximum": max(values),
                "native_crop_pixel_bytes_sha256": pixel_digest.hexdigest(),
                "zone_mask_bytes_sha256": mask_digest.hexdigest(),
                "definition": "All valid pixels of the existing packaged native crop rectangle, including pixels outside the buffer; this is the recorded extraction window, not a newly chosen buffer or proof of the old QGIS extent"}
    finally:
        crop.close()
        mask.close()


def main():
    old_path = ROOT / "17 NDVI補足資料S1.tsv"
    with old_path.open("r", encoding="utf-8-sig", newline="") as stream:
        olds = list(csv.DictReader(stream, delimiter="\t"))
    scan = json.loads((ROOT / "NDVI_mean_work/regional_mean_source_scan.json").read_text(encoding="utf-8"))
    pairing_audit = json.loads((ROOT / "NDVI_mean_work/audit_vector_topology.json").read_text(encoding="utf-8"))
    parks = read_shp(ROOT / "NDVI/parks_metric.shp", include_points=True)["feature_details"]
    buffers = read_shp(ROOT / "NDVI/100m_buffer.shp", include_points=True)["feature_details"][0]["private_parts"]
    pairings = {item["park_id"]: item["covering_buffer_parts"][0] - 1 for item in pairing_audit["matches"]}
    packaged = json.loads((PACKAGE / "GIS/pixel_extractions.json").read_text(encoding="utf-8"))
    package_labels = {(item["ParkID"], item["source_raster"]): item["label"] for item in packaged}
    candidates = []
    for park in scan["parks"]:
        park_id = park["ParkID"]
        shape = parks[park_id - 1]["private_parts"][0]
        buffer = buffers[pairings[park_id]]
        for ordinal, original in enumerate(park["candidates"], 1):
            result = independent_case(shape, buffer, original)
            candidates.append({"current_geometry_park_id": park_id,
                "candidate_label": package_labels.get((park_id, original["source_raster"]), f"P{park_id:02d}_extra_source{ordinal}"),
                "source_raster": original["source_raster"], "stats": result["independent_stats"],
                "has_valid_pixels_in_both_zones": bool(result["independent_stats"]["inside"]["valid_n"] and result["independent_stats"]["outside"]["valid_n"]),
                "minus_primary_stats": result["minus_primary"],
                "all_count_and_stat_differences_zero": result["all_count_and_stat_differences_zero"],
                "maximum_inverse_transform_difference_m": result["maximum_inverse_transform_difference_m"],
                "reported_pixel_signature_sha256": original["pixel_signature_sha256"]})
    cross = [summarize_cross(old, candidates) for old in olds]
    old_by_id = {int(item["park_code"][1:]): item for item in olds}
    targeted = []
    for item in packaged:
        if item["ParkID"] not in TARGET_IDS:
            continue
        current = next(row for row in candidates if row["current_geometry_park_id"] == item["ParkID"] and row["source_raster"] == item["source_raster"])
        old = old_by_id[item["ParkID"]]
        rectangle = crop_bbox_summary(item)
        vectors = extrema_vectors(current["stats"])
        inner = vectors["park_plus_exterior_ring"][:2]
        vectors["park_plus_existing_native_crop_rectangle"] = inner + [rectangle["minimum"], rectangle["maximum"]]
        vectors["same_existing_native_crop_rectangle_for_both"] = [rectangle["minimum"], rectangle["maximum"]] * 2
        targeted.append({"old_s1_id": item["ParkID"], "current_geometry_park_id": item["ParkID"],
            "candidate_label": item["label"], "source_raster": item["source_raster"],
            "native_crop_rectangle": rectangle,
            "fixed_definition_comparisons": {definition: {"all_four_match_display_precision": all_match(compare(vector, old)),
                "fields": compare(vector, old)} for definition, vector in vectors.items()}})
    matches = [row for row in cross if row["four_extrema_matches"]]
    report = {
        "method": "Independently reaggregate every existing source candidate with sixth-order Krueger UTM, bisection Albers inverse, nonzero winding masks, direct Float32 reads; only audited TIFF header and SHP decoding shared. Per-field Decimal rounding uses the exact textual precision of old S1.",
        "input_source_files_modified": False, "sem_inputs_modified": False,
        "source_selection_or_id_remapping_performed": False, "coordinates_or_park_attributes_output": False,
        "old_s1_sha256": hashlib.sha256(old_path.read_bytes()).hexdigest(),
        "old_park_row_count": len(olds), "existing_candidate_count": len(candidates),
        "candidates_with_valid_pixels_in_both_zones": sum(row["has_valid_pixels_in_both_zones"] for row in candidates),
        "candidate_labels_without_valid_pixels_in_both_zones": [row["candidate_label"] for row in candidates if not row["has_valid_pixels_in_both_zones"]],
        "fixed_cross_id_definitions": ["park_plus_exterior_ring", "park_plus_full_expanded_buffer"],
        "all_independent_candidate_stats_match_primary": all(row["all_count_and_stat_differences_zero"] for row in candidates),
        "maximum_inverse_transform_difference_m": max(row["maximum_inverse_transform_difference_m"] for row in candidates),
        "old_ids_with_four_extrema_matches": [row["old_s1_id"] for row in matches],
        "old_ids_with_no_four_extrema_match": [row["old_s1_id"] for row in cross if not row["four_extrema_matches"]],
        "old_ids_with_multiple_geometry_matches": [row["old_s1_id"] for row in cross if row["classification"] == "multiple_geometry_matches"],
        "unique_geometry_numeric_matches_with_different_id_count": sum(row["unique_numeric_geometry_has_different_id"] for row in cross),
        "target_old_rows_cross_id": [row for row in cross if row["old_s1_id"] in TARGET_IDS],
        "all_old_rows_cross_id": cross,
        "independently_recomputed_candidates": [{
            "current_geometry_park_id": row["current_geometry_park_id"],
            "candidate_label": row["candidate_label"], "source_raster": row["source_raster"],
            "has_valid_pixels_in_both_zones": row["has_valid_pixels_in_both_zones"],
            "stats": {side: {key: row["stats"][side][key] for key in
                ("eligible_n", "valid_n", "nodata_n", "outside_extent_n", "minimum", "maximum")}
                for side in ("inside", "outside")},
            "all_count_and_stat_differences_zero": row["all_count_and_stat_differences_zero"],
            "maximum_inverse_transform_difference_m": row["maximum_inverse_transform_difference_m"],
            "reported_pixel_signature_sha256": row["reported_pixel_signature_sha256"],
        } for row in candidates],
        "eight_same_id_candidate_comparisons": targeted,
        "interpretation_limits": [
            "A precise cross-ID extrema match is a numeric fingerprint clue, not an author-confirmed park identity mapping, and cannot authorize automatic SEM row reassignment.",
            "Multiple rasters with identical pixels may all match; extrema cannot distinguish file identity within such an equivalence class.",
            "A no-match result excludes only reproducing that old row with the audited existing fixed park/ring/full-buffer definitions and supplied candidate rasters at old display precision. It does not exclude different historical geometry, ROI, imagery, processing, or transcription.",
            "Four-decimal extrema are weaker fingerprints than eight- or nine-decimal extrema; precision is not a freely adjustable tolerance.",
            "The native-crop-rectangle tests use the existing recorded extraction windows only. No distance, bbox or mask was varied to chase an old value.",
            "No original GIS, NDVI, anonymous identity, SEM input or model was changed, and no SEM was run."
        ],
    }
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
