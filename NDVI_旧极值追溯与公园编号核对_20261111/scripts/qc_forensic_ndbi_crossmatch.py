"""Read-only forensic test of supplied NDBI-labelled files, never NDVI inputs.

Scope: the 13 geometry records not occupied by prior exact numeric NDVI
matches, and only NDBI filenames corresponding to their existing candidates.
Exact old textual precision; two fixed geometries; no nearest-error search.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
from audit_rasters_stdlib import first, geo_keys, metadata_items, read_ifd
from audit_vectors_std import read_shp
from qc_regional_means_stdlib import independent_case
from qc_old_extrema_cross_id import summarize_cross


def main():
    work = Path(__file__).resolve().parent
    previous = json.loads((work / "independent_old_extrema_cross_id.json").read_text(encoding="utf-8"))
    scan = json.loads((ROOT / "NDVI_mean_work/regional_mean_source_scan.json").read_text(encoding="utf-8"))
    pairing = json.loads((ROOT / "NDVI_mean_work/audit_vector_topology.json").read_text(encoding="utf-8"))
    occupied = {park_id for row in previous["all_old_rows_cross_id"] for park_id in row["matched_geometry_ids"]}
    target_geometry_ids = sorted(set(range(1, 40)) - occupied)
    target_old_ids = set(previous["old_ids_with_no_four_extrema_match"])
    old_path = ROOT / "17 NDVI補足資料S1.tsv"
    with old_path.open("r", encoding="utf-8-sig", newline="") as stream:
        olds = [row for row in csv.DictReader(stream, delimiter="\t") if int(row["park_code"][1:]) in target_old_ids]
    parks = read_shp(ROOT / "NDVI/parks_metric.shp", include_points=True)["feature_details"]
    buffers = read_shp(ROOT / "NDVI/100m_buffer.shp", include_points=True)["feature_details"][0]["private_parts"]
    pairings = {item["park_id"]: item["covering_buffer_parts"][0] - 1 for item in pairing["matches"]}
    candidates, missing_files, failures = [], [], []
    for park in scan["parks"]:
        park_id = park["ParkID"]
        if park_id not in target_geometry_ids:
            continue
        shape, buffer = parks[park_id - 1]["private_parts"][0], buffers[pairings[park_id]]
        for ordinal, ndvi_candidate in enumerate(park["candidates"], 1):
            original_name = ndvi_candidate["source_raster"]
            if not original_name.startswith("NDVI_"):
                raise ValueError("Unexpected existing NDVI candidate basename")
            labelled_name = "NDBI_" + original_name[len("NDVI_"):]
            path = ROOT / "NDVI" / labelled_name
            if not path.is_file():
                missing_files.append({"current_geometry_park_id": park_id, "expected_labelled_basename": labelled_name})
                continue
            try:
                tags, container = read_ifd(path)
                keys = geo_keys(tags)
                items = metadata_items(tags.get(42112))
                scale = float(next((item["value"] for item in items if item.get("role") == "scale"), 1))
                offset = float(next((item["value"] for item in items if item.get("role") == "offset"), 0))
                source = dict(ndvi_candidate, source_raster=labelled_name)
                result = independent_case(shape, buffer, source)
                candidates.append({"current_geometry_park_id": park_id,
                    "candidate_label": f"P{park_id:02d}_NDBIlabel_candidate{ordinal}",
                    "source_raster": labelled_name, "corresponding_ndvi_basename": original_name,
                    "stats": result["independent_stats"],
                    "has_valid_pixels_in_both_zones": bool(result["independent_stats"]["inside"]["valid_n"] and result["independent_stats"]["outside"]["valid_n"]),
                    "tiff_metadata": {"epsg": keys["3072"]["value"], "bits_per_sample": first(tags, 258),
                        "sample_format": first(tags, 339, 1), "raster_pixel_is_area": keys.get("1025", {}).get("value", 1) == 1,
                        "compression": first(tags, 259), "value_scale": scale, "value_offset": offset,
                        "byte_order": container["byte_order"]},
                    "maximum_inverse_transform_difference_m": result["maximum_inverse_transform_difference_m"]})
            except Exception as exc:
                failures.append({"current_geometry_park_id": park_id, "labelled_basename": labelled_name,
                    "error_type": type(exc).__name__, "error": str(exc)})
    cross = [summarize_cross(old, candidates) for old in olds]
    report = {
        "purpose": "Forensic exact-value comparison against NDBI-labelled supplied rasters; not a calculation of NDVI, not a source selection and not proof of the labelled index formula",
        "method": "Independent sixth-order Krueger UTM, bisection Albers inverse, nonzero winding masks, original Float32 reads; only audited TIFF header and SHP decoding shared. Fixed park interior plus exterior ring / full expanded buffer. Per-field Decimal rounding at old S1 textual precision.",
        "input_gis_files_modified": False, "ndvi_or_sem_inputs_modified": False,
        "source_selection_or_id_remapping_performed": False, "sem_run_performed": False,
        "coordinates_or_park_attributes_output": False,
        "old_s1_sha256": hashlib.sha256(old_path.read_bytes()).hexdigest(),
        "target_unoccupied_geometry_ids": target_geometry_ids,
        "target_old_s1_ids": sorted(target_old_ids),
        "existing_labelled_file_geometry_candidates_checked": len(candidates),
        "candidates_with_valid_pixels_in_both_zones": sum(row["has_valid_pixels_in_both_zones"] for row in candidates),
        "missing_corresponding_labelled_files": missing_files, "failures": failures,
        "old_s1_ids_with_four_extrema_matches": [row["old_s1_id"] for row in cross if row["four_extrema_matches"]],
        "old_s1_ids_with_no_four_extrema_match": [row["old_s1_id"] for row in cross if not row["four_extrema_matches"]],
        "old_s1_ids_with_multiple_geometry_matches": [row["old_s1_id"] for row in cross if row["classification"] == "multiple_geometry_matches"],
        "cross_id_results": cross, "independently_recomputed_labelled_candidates": candidates,
        "interpretation_limits": [
            "A match means the supplied NDBI-labelled file has matching scalar values under the audited fixed geometry at the old display precision. It is not proof of the actual spectral-index formula or of historical layer use.",
            "NDBI-labelled values must never be substituted as NDVI into the new data or SEM.",
            "No-match excludes only reproduction by these supplied labelled files and two fixed definitions, not every possible past layer, geometry or processing operation.",
            "No closest-error candidate, tuned distance, invented mask, row assignment, final source selection or SEM re-estimation is performed.",
            "Park identity alignment remains an author-confirmation requirement even if a numeric fingerprint matches."
        ],
    }
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
