"""Audit a NEW frame-margin source-selection rule; preserve all source files.

Only source headers, the existing 39 geometry pairs and the eight already
extracted crop/mask pairs are read. No original-image rescanning, resampling,
historical-source reconstruction, Z-score calculation or SEM fitting occurs.
Output is anonymous: ParkID, source filenames, distances and statistics only.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import sys


WORK = Path(__file__).resolve().parent
ROOT = WORK.parent
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))

from audit_rasters_stdlib import first, geo_keys, read_ifd
from compute_regional_means import load_geometry, mapped_bounds
from qc_crop_raw_bits import IndependentRows


PAIR_IDS = (9, 18, 28, 32)
PACKAGE = ROOT / "NDVI_同号公园复核与区域均值_20261111"


def source_frame(source_name, frames):
    if source_name not in frames:
        tags, container = read_ifd(ROOT / "NDVI" / source_name)
        keys = geo_keys(tags)
        if 34264 in tags:
            raise ValueError("Rotated source rasters are not permitted")
        dx, dy = tags[33550][:2]
        tie = tags[33922]
        x0, y0 = tie[3] - tie[0] * dx, tie[4] + tie[1] * dy
        width, height = first(tags, 256), first(tags, 257)
        frames[source_name] = {
            "epsg": keys.get("3072", {}).get("value"),
            "pixel_is_area": keys.get("1025", {}).get("value") == 1,
            "x0": x0, "y0": y0, "dx": dx, "dy": dy,
            "width": width, "height": height,
            "right": x0 + width * dx, "bottom": y0 - height * dy,
            "byte_order": container["byte_order"],
        }
    return frames[source_name]


def inspect_candidate(park_id, candidate, geometry, frames):
    frame = source_frame(candidate["source_raster"], frames)
    if frame["epsg"] != candidate["epsg"] or not frame["pixel_is_area"]:
        raise ValueError("Candidate source metadata disagrees with scan")
    bx0, by0, bx1, by1 = mapped_bounds(geometry["buffer"], frame["epsg"])
    distances = {
        "left_margin_m": bx0 - frame["x0"],
        "right_margin_m": frame["right"] - bx1,
        "bottom_margin_m": by0 - frame["bottom"],
        "top_margin_m": frame["y0"] - by1,
    }
    margin = min(distances.values())
    reasons = []
    if not candidate["full_extent"] or margin < 0:
        reasons.append("buffer_not_wholly_inside_source_rectangle")
    for side in ("inside", "outside"):
        zone = candidate[side]
        if zone["valid_n"] <= 0 or zone["mean"] is None:
            reasons.append(side + "_has_no_valid_pixels")
        if zone["outside_extent_n"]:
            reasons.append(side + "_contains_outside_extent_pixels")
        if zone["out_of_range_n"]:
            reasons.append(side + "_has_values_outside_NDVI_range")
    row = {
        "ParkID": park_id,
        "source_raster": candidate["source_raster"],
        "source_epsg": candidate["epsg"],
        "source_resolution_x_m": frame["dx"],
        "source_resolution_y_m": frame["dy"],
        "scan_full_extent": candidate["full_extent"],
        **distances,
        "frame_margin_m": margin,
        "limiting_frame_side": min(distances, key=distances.get).replace("_margin_m", ""),
        "eligible_for_frame_margin_selection": not reasons,
        "ineligibility_reasons": reasons,
    }
    for side in ("inside", "outside"):
        for field in ("eligible_n", "valid_n", "nodata_n", "outside_extent_n", "out_of_range_n", "mean"):
            row[side + "_" + field] = candidate[side][field]
    return row


def audit_selection():
    scan = json.loads((ROOT / "NDVI_mean_work" / "regional_mean_source_scan.json").read_text(encoding="utf-8"))
    pairs, _prj = load_geometry(ROOT / "NDVI")
    geometry = {item["ParkID"]: item for item in pairs}
    if sorted(geometry) != list(range(1, 40)):
        raise ValueError("Geometry IDs must remain exactly 1 through 39")
    frames, parks, candidate_rows = {}, [], []
    for old in scan["parks"]:
        park_id = old["ParkID"]
        rows = [inspect_candidate(park_id, item, geometry[park_id], frames) for item in old["candidates"]]
        usable = [row for row in rows if row["eligible_for_frame_margin_selection"]]
        if not usable:
            raise ValueError(f"P{park_id:02d} has no eligible full-extent source")
        best_margin = max(row["frame_margin_m"] for row in usable)
        best = [row for row in usable if abs(row["frame_margin_m"] - best_margin) < 1e-8]
        if len(best) != 1:
            raise ValueError(f"P{park_id:02d} has tied frame margins; no silent tie-breaker")
        chosen = best[0]
        old_source = old["selected"]["source_raster"] if old["selected"] else None
        previous_statistics_preserved = None
        if old_source is not None:
            previous_statistics_preserved = all(
                chosen[side + "_" + field] == old["selected"][side][field]
                for side in ("inside", "outside")
                for field in ("eligible_n", "valid_n", "nodata_n", "outside_extent_n", "out_of_range_n", "mean")
            )
        for row in rows:
            row["selected_by_new_frame_margin_rule"] = row["source_raster"] == chosen["source_raster"]
        candidate_rows.extend(rows)
        parks.append({
            "ParkID": park_id,
            "old_selected_source": old_source,
            "selected_source_raster": chosen["source_raster"],
            "selected_frame_margin_m": chosen["frame_margin_m"],
            "eligible_candidate_count": len(usable),
            "selection_reason": "only_eligible_full_extent_source" if len(usable) == 1 else "largest_minimum_buffer_to_TIFF_rectangle_margin",
            "old_available_source_preserved": old_source == chosen["source_raster"] if old_source else None,
            "old_available_region_statistics_preserved": previous_statistics_preserved,
            "inside_mean": chosen["inside_mean"],
            "outside_mean": chosen["outside_mean"],
            "inside_valid_n": chosen["inside_valid_n"],
            "outside_valid_n": chosen["outside_valid_n"],
            "inside_eligible_n": chosen["inside_eligible_n"],
            "outside_eligible_n": chosen["outside_eligible_n"],
            "inside_nodata_n": chosen["inside_nodata_n"],
            "outside_nodata_n": chosen["outside_nodata_n"],
            "candidates": rows,
        })
    old_available = [row for row in parks if row["old_selected_source"] is not None]
    summary = {
        "method": "NEW single-source rule applied identically to all 39 parks: among full-rectangle-coverage candidates with positive valid pixel counts in both zones and no out-of-range values, choose the greatest minimum net distance from the transformed full-buffer bounding box to the source TIFF rectangle's four sides; distances use each source's native UTM metres.",
        "not_historical_source_identification": True,
        "not_cloud_time_or_scene_footprint_quality_validation": True,
        "old_extrema_and_SEM_fit_not_used": True,
        "no_cross_park_imputation": True,
        "no_original_file_edits": True,
        "no_resampling": True,
        "NoData_policy": "Exclude invalid pixels when computing the existing regional means; nonzero NoData counts do not make an otherwise usable source ineligible. P27 exterior remains 598 valid of 600 eligible pixels, with two NoData pixels excluded.",
        "bbox_transform_rule": "Use existing mapped_bounds routine, densifying the supplied Albers buffer edges at at most 100 m steps and mapping them into source UTM. This is a numerical bounding-box proxy for the source rectangle, not distance to the actual valid-scene footprint.",
        "park_count": len(parks),
        "scan_candidate_count": len(candidate_rows),
        "eligible_candidate_count": sum(row["eligible_for_frame_margin_selection"] for row in candidate_rows),
        "all_same_number_ParkIDs_preserved": [row["ParkID"] for row in parks] == list(range(1, 40)),
        "previous_available_source_count": len(old_available),
        "previous_available_sources_all_preserved": all(row["old_available_source_preserved"] for row in old_available),
        "previous_available_region_statistics_all_preserved": all(row["old_available_region_statistics_preserved"] for row in old_available),
        "newly_selected_ParkIDs": [row["ParkID"] for row in parks if row["old_selected_source"] is None],
        "selected_four": {str(row["ParkID"]): row["selected_source_raster"] for row in parks if row["ParkID"] in PAIR_IDS},
    }
    if len(old_available) != 35 or not summary["previous_available_sources_all_preserved"] or not summary["previous_available_region_statistics_all_preserved"]:
        raise ValueError("New rule unexpectedly changes one of the previous 35 available sources")
    if summary["newly_selected_ParkIDs"] != list(PAIR_IDS):
        raise ValueError("Unresolved source IDs differ from expected four")
    (WORK / "frame_margin_selection.json").write_text(json.dumps(summary | {"parks": parks}, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    fields = list(candidate_rows[0])
    with (WORK / "frame_margin_candidates.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in candidate_rows:
            writer.writerow(row | {"ineligibility_reasons": ";".join(row["ineligibility_reasons"])})
    selected_fields = [key for key in parks[0] if key != "candidates"]
    with (WORK / "frame_margin_selected_39.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=selected_fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in selected_fields} for row in parks)
    print(json.dumps(summary, ensure_ascii=False))
    return frames


def is_valid(raw, nodata, scale, offset):
    return math.isfinite(raw) and (nodata is None or raw != nodata) and -1.000001 <= raw * scale + offset <= 1.000001


def audit_pair(park_id, items, frames):
    options = sorted([item for item in items if item["ParkID"] == park_id], key=lambda item: item["label"])
    if len(options) != 2:
        raise ValueError("Each audited park must have exactly two existing source options")
    readers = [IndependentRows(PACKAGE / item["ndvi_crop"]) for item in options]
    masks = [IndependentRows(PACKAGE / item["zone_mask"]) for item in options]
    try:
        a, b = readers
        ma, mb = masks
        metadata_checks = {
            "native_EPSG_identical": a.keys.get("3072", {}).get("value") == b.keys.get("3072", {}).get("value"),
            "crop_dimensions_identical": (a.width, a.height) == (b.width, b.height),
            "crop_origin_and_resolution_identical": a.georeference() == b.georeference(),
            "mask_dimensions_match_crops": (ma.width, ma.height) == (mb.width, mb.height) == (a.width, a.height),
            "mask_georeferences_match_crops": ma.georeference() == mb.georeference() == a.georeference(),
            "mask_EPSG_matches_crops": ma.keys.get("3072", {}).get("value") == mb.keys.get("3072", {}).get("value") == a.keys.get("3072", {}).get("value"),
            "pixel_is_area_all": all(reader.keys.get("1025", {}).get("value") == 1 for reader in readers + masks),
            "float32_crops_uint8_masks": a.bits == b.bits == 32 and ma.bits == mb.bits == 8,
            "scale_offset_identical": a.scale_offset() == b.scale_offset(),
        }
        source_a = source_frame(options[0]["source_raster"], frames)
        source_b = source_frame(options[1]["source_raster"], frames)
        dcol = (source_a["x0"] - source_b["x0"]) / source_a["dx"]
        drow = (source_a["y0"] - source_b["y0"]) / source_a["dy"]
        metadata_checks["source_native_grid_origins_differ_by_integer_pixels"] = (
            source_a["dx"] == source_b["dx"] and source_a["dy"] == source_b["dy"]
            and abs(dcol - round(dcol)) < 1e-10 and abs(drow - round(drow)) < 1e-10)
        if not all(metadata_checks.values()):
            raise ValueError("Source option grids cannot be combined without resampling")
        zone_hashes = [hashlib.sha256(), hashlib.sha256()]
        valid_hashes = [hashlib.sha256(), hashlib.sha256()]
        values = {1: [[], [], []], 2: [[], [], []]}
        zone_mismatch = valid_mismatch = roi_valid_mismatch = 0
        eligible = {1: 0, 2: 0}
        scale_a, offset_a = a.scale_offset()
        scale_b, offset_b = b.scale_offset()
        for row in range(a.height):
            zone_rows = [mask.row_bytes(row) for mask in masks]
            raw_rows = [struct.unpack(reader.order + "f" * reader.width, reader.row_bytes(row)) for reader in readers]
            valid_rows = [bytearray(), bytearray()]
            for col, (za, zb) in enumerate(zip(*zone_rows)):
                va, vb = raw_rows[0][col], raw_rows[1][col]
                good_a, good_b = is_valid(va, a.nodata, scale_a, offset_a), is_valid(vb, b.nodata, scale_b, offset_b)
                valid_rows[0].append(int(good_a))
                valid_rows[1].append(int(good_b))
                zone_mismatch += za != zb
                valid_mismatch += good_a != good_b
                if za in (1, 2):
                    eligible[za] += 1
                    roi_valid_mismatch += good_a != good_b
                    if good_a:
                        values[za][0].append(va * scale_a + offset_a)
                    if good_b:
                        values[za][1].append(vb * scale_b + offset_b)
                    if good_a and good_b:
                        values[za][2].append(((va * scale_a + offset_a) + (vb * scale_b + offset_b)) / 2)
            for i in (0, 1):
                zone_hashes[i].update(zone_rows[i])
                valid_hashes[i].update(valid_rows[i])
        zones = {}
        for zone, side in ((1, "inside"), (2, "outside")):
            arrays = values[zone]
            means = [math.fsum(array) / len(array) if array else None for array in arrays]
            counts = [len(array) for array in arrays]
            reference_means = [option[side]["mean"] for option in options]
            midpoint = (means[0] + means[1]) / 2
            zones[side] = {
                "eligible_n": eligible[zone],
                "source_A_valid_n": counts[0], "source_B_valid_n": counts[1], "both_valid_n": counts[2],
                "source_A_mean": means[0], "source_B_mean": means[1],
                "source_A_mean_abs_difference_from_index": abs(means[0] - reference_means[0]),
                "source_B_mean_abs_difference_from_index": abs(means[1] - reference_means[1]),
                "optional_equal_pixelwise_two_source_mean": means[2],
                "source_region_means_midpoint": midpoint,
                "pixelwise_composite_minus_region_midpoint": means[2] - midpoint,
                "both_valid_count_equals_eligible": counts[0] == counts[1] == counts[2] == eligible[zone],
            }
        return {
            "ParkID": park_id,
            "source_A": options[0]["source_raster"], "source_B": options[1]["source_raster"],
            "metadata_checks": metadata_checks,
            "source_A_minus_source_B_native_grid_origin_offset_columns": dcol,
            "source_A_minus_source_B_native_grid_origin_offset_rows_upward": drow,
            "bounding_box_pixels_checked": a.width * a.height,
            "zone_mask_pixel_mismatch_count": zone_mismatch,
            "valid_mask_pixel_mismatch_count_including_bbox": valid_mismatch,
            "valid_mask_pixel_mismatch_count_inside_ROI": roi_valid_mismatch,
            "zone_mask_SHA256_A": zone_hashes[0].hexdigest(), "zone_mask_SHA256_B": zone_hashes[1].hexdigest(),
            "valid_mask_SHA256_A": valid_hashes[0].hexdigest(), "valid_mask_SHA256_B": valid_hashes[1].hexdigest(),
            "zones": zones,
        }
    finally:
        for reader in readers + masks:
            reader.close()


def main():
    frames = audit_selection()
    items = json.loads((PACKAGE / "GIS" / "pixel_extractions.json").read_text(encoding="utf-8"))
    audits = [audit_pair(park_id, items, frames) for park_id in PAIR_IDS]
    summary = {
        "method": "Read existing native-grid crop TIFFs and UInt8 zone masks; compare every paired mask and validity flag at corresponding pixels. Optional composite is (source A pixel + source B pixel)/2 only at jointly valid pixels, then the within-zone arithmetic mean; never resample.",
        "optional_composite_not_applied_to_final_selection": True,
        "not_historical_source_or_temporal_average": True,
        "source_dates_unconfirmed": True,
        "original_files_and_delivery_package_unmodified": True,
        "four_pair_count": len(audits),
        "source_options_count": 2 * len(audits),
        "source_region_mean_checks_count": 4 * len(audits),
        "all_grid_metadata_checks_pass": all(all(item["metadata_checks"].values()) for item in audits),
        "all_zone_masks_identical": all(item["zone_mask_pixel_mismatch_count"] == 0 for item in audits),
        "all_valid_masks_identical": all(item["valid_mask_pixel_mismatch_count_including_bbox"] == 0 for item in audits),
        "all_16_source_region_mean_checks_exact": all(zone["source_A_mean_abs_difference_from_index"] == 0 and zone["source_B_mean_abs_difference_from_index"] == 0 for item in audits for zone in item["zones"].values()),
        "all_pair_ROI_pixels_valid_in_both_sources": all(zone["both_valid_count_equals_eligible"] for item in audits for zone in item["zones"].values()),
        "max_optional_composite_difference_from_source_region_mean_midpoint": max(abs(zone["pixelwise_composite_minus_region_midpoint"]) for item in audits for zone in item["zones"].values()),
    }
    (WORK / "dual_source_grid_mask_audit.json").write_text(json.dumps(summary | {"pairs": audits}, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
