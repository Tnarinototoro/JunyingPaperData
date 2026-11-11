"""Verify every crop Float32 word against source bytes; input files read-only."""

import hashlib
import json
import math
from pathlib import Path
import struct

from audit_rasters_stdlib import first, geo_keys, metadata_items, read_ifd


class IndependentRows:
    """Uncompressed single-band strip reader, independent of production Raster."""

    def __init__(self, path):
        self.path = path
        self.tags, self.container = read_ifd(path)
        self.keys = geo_keys(self.tags)
        self.width, self.height = first(self.tags, 256), first(self.tags, 257)
        self.bits = first(self.tags, 258)
        self.word_bytes = self.bits // 8
        self.order = self.container["byte_order"]
        self.rows_per_strip = first(self.tags, 278, self.height)
        self.offsets, self.byte_counts = self.tags[273], self.tags[279]
        if first(self.tags, 259) != 1 or first(self.tags, 277, 1) != 1:
            raise ValueError("Unsupported compression or band count")
        if self.bits not in (8, 32):
            raise ValueError("Unsupported sample size")
        self.nodata_text = self.tags.get(42113)
        self.nodata = float(self.nodata_text) if self.nodata_text is not None else None
        if self.bits == 32 and self.nodata is not None:
            self.nodata = struct.unpack(self.order + "f", struct.pack(self.order + "f", self.nodata))[0]
        self.file = path.open("rb")

    def close(self):
        self.file.close()

    def row_bytes(self, row):
        if not 0 <= row < self.height:
            raise ValueError("Row outside image")
        block, within = divmod(row, self.rows_per_strip)
        offset, count = self.offsets[block], self.byte_counts[block]
        row_size = self.width * self.word_bytes
        if offset == 0 and count == 0:
            if self.bits == 32 and self.nodata is not None:
                return struct.pack(self.order + "f", self.nodata) * self.width
            if self.bits == 8 and self.nodata is not None:
                return bytes([int(self.nodata)]) * self.width
            raise ValueError("Sparse strip without a defined fill value")
        if within * row_size + row_size > count:
            raise ValueError("Row bytes exceed strip byte count")
        self.file.seek(offset + within * row_size)
        raw = self.file.read(row_size)
        if len(raw) != row_size:
            raise ValueError("Truncated raster row")
        return raw

    def georeference(self):
        pixel_scale, tie = self.tags.get(33550), self.tags.get(33922)
        if not pixel_scale or not tie or 34264 in self.tags:
            raise ValueError("Unsupported crop georeferencing")
        dx, dy = pixel_scale[:2]
        return (tie[3] - tie[0] * dx, tie[4] + tie[1] * dy, dx, dy)

    def scale_offset(self):
        items = metadata_items(self.tags.get(42112))
        return tuple(float(next((item["value"] for item in items if item.get("role") == role), default))
                     for role, default in [("scale", 1), ("offset", 0)])


def check_record(item, package, source_dir, source_readers):
    source_name = item["source_raster"]
    if source_name not in source_readers:
        source_readers[source_name] = IndependentRows(source_dir / source_name)
    source = source_readers[source_name]
    crop = IndependentRows(package / item["ndvi_crop"])
    mask = IndependentRows(package / item["zone_mask"])
    try:
        c0, r0, c1, r1 = item["source_window"]
        width, height = c1 - c0 + 1, r1 - r0 + 1
        sx0, sy0, dx, dy = source.georeference()
        expected_reference = (sx0 + c0 * dx, sy0 - r0 * dy, dx, dy)
        crop_epsg = crop.keys.get("3072", {}).get("value")
        source_epsg = source.keys.get("3072", {}).get("value")
        source_nodata_bits = struct.pack(source.order + "f", source.nodata)
        checks = {
            "crop_dimensions_match_source_window": (crop.width, crop.height) == (width, height),
            "mask_dimensions_match_crop": (mask.width, mask.height) == (width, height),
            "crop_float32": crop.bits == 32 and first(crop.tags, 339, 1) == 3,
            "mask_uint8": mask.bits == 8 and first(mask.tags, 339, 1) == 1,
            "crop_byte_order_matches_source": crop.order == source.order,
            "crop_origin_and_spacing_match_source_window": crop.georeference() == expected_reference,
            "mask_origin_and_spacing_match_source_window": mask.georeference() == expected_reference,
            "crop_epsg_matches_source": crop_epsg == source_epsg == item["source_epsg"],
            "mask_epsg_matches_source": mask.keys.get("3072", {}).get("value") == source_epsg,
            "crop_pixel_is_area": crop.keys.get("1025", {}).get("value") == 1,
            "mask_pixel_is_area": mask.keys.get("1025", {}).get("value") == 1,
            "crop_nodata_bits_match_source": (crop.nodata is not None and
                                               struct.pack(crop.order + "f", crop.nodata) == source_nodata_bits),
            "crop_scale_offset_match_source": crop.scale_offset() == source.scale_offset(),
        }
        if not all(checks.values()):
            raise ValueError("Crop metadata mismatch: " + ", ".join(key for key, value in checks.items() if not value))
        crop_digest, expected_digest = hashlib.sha256(), hashlib.sha256()
        mismatch_count, valid_zone_mismatches, padding_count = 0, 0, 0
        eligible, valid, nodata, outside_extent = ({1: 0, 2: 0} for _ in range(4))
        source_values, crop_values = {1: [], 2: []}, {1: [], 2: []}
        zone_codes = set()
        scale, value_offset = source.scale_offset()
        mismatch_examples = []
        for out_row in range(height):
            in_row = r0 + out_row
            expected = bytearray(source_nodata_bits * width)
            if 0 <= in_row < source.height:
                lo, hi = max(c0, 0), min(c1, source.width - 1)
                if lo <= hi:
                    source_row = source.row_bytes(in_row)
                    expected[(lo - c0) * 4:(hi - c0 + 1) * 4] = source_row[lo * 4:(hi + 1) * 4]
            crop_row, mask_row = crop.row_bytes(out_row), mask.row_bytes(out_row)
            crop_digest.update(crop_row)
            expected_digest.update(expected)
            source_floats = struct.unpack(source.order + "f" * width, expected)
            crop_floats = struct.unpack(crop.order + "f" * width, crop_row)
            for out_col, zone in enumerate(mask_row):
                zone_codes.add(zone)
                if zone not in (0, 1, 2):
                    raise ValueError("Unexpected zone-mask value")
                in_col = c0 + out_col
                in_extent = 0 <= in_row < source.height and 0 <= in_col < source.width
                if not in_extent:
                    padding_count += 1
                start = out_col * 4
                identical = crop_row[start:start + 4] == expected[start:start + 4]
                if not identical:
                    mismatch_count += 1
                    if len(mismatch_examples) < 4:
                        mismatch_examples.append({"crop_row": out_row, "crop_col": out_col,
                                                  "expected_bits": expected[start:start + 4].hex(),
                                                  "crop_bits": crop_row[start:start + 4].hex()})
                if zone == 0:
                    continue
                eligible[zone] += 1
                raw = source_floats[out_col]
                if not in_extent:
                    outside_extent[zone] += 1
                elif not math.isfinite(raw) or raw == source.nodata:
                    nodata[zone] += 1
                else:
                    valid[zone] += 1
                    source_values[zone].append(raw * scale + value_offset)
                    crop_values[zone].append(crop_floats[out_col] * scale + value_offset)
                    if not identical:
                        valid_zone_mismatches += 1
        zones = {}
        for zone, side in [(1, "inside"), (2, "outside")]:
            source_mean = math.fsum(source_values[zone]) / valid[zone] if valid[zone] else None
            crop_mean = math.fsum(crop_values[zone]) / valid[zone] if valid[zone] else None
            reported = item[side]
            got = {"eligible_n": eligible[zone], "valid_n": valid[zone], "nodata_n": nodata[zone],
                   "outside_extent_n": outside_extent[zone]}
            counts_match = all(got[key] == reported[key] for key in got)
            zones[side] = got | {"source_mean": source_mean, "crop_mean": crop_mean,
                                "reported_mean": reported["mean"], "counts_match_report": counts_match,
                                "absolute_mean_difference_from_report": abs(source_mean - reported["mean"])
                                if source_mean is not None else None}
        return {"ParkID": item["ParkID"], "label": item["label"], "status": item["status"],
                "source_raster": source_name, "source_window": item["source_window"],
                "ndvi_crop": item["ndvi_crop"], "metadata_checks": checks,
                "bounding_box_pixel_count": width * height,
                "bounding_box_pixels_outside_source_extent_nodata_filled": padding_count,
                "bounding_box_bit_mismatch_count": mismatch_count,
                "valid_zone_pixel_count": valid[1] + valid[2],
                "valid_zone_bit_mismatch_count": valid_zone_mismatches,
                "zone_mask_codes": sorted(zone_codes), "crop_pixel_bytes_sha256": crop_digest.hexdigest(),
                "expected_source_window_bytes_sha256": expected_digest.hexdigest(),
                "mismatch_examples": mismatch_examples, "zones": zones}
    finally:
        crop.close()
        mask.close()


def main():
    work = Path(__file__).resolve().parent
    root = work.parent
    package = root / "NDVI_区域平均值_20261111_核对版"
    items = json.loads((package / "GIS" / "pixel_extractions.json").read_text(encoding="utf-8"))
    source_readers, records, failures = {}, [], []
    try:
        for item in items:
            try:
                records.append(check_record(item, package, root / "NDVI", source_readers))
            except Exception as exc:
                failures.append({"label": item["label"], "error": str(exc)})
    finally:
        for source in source_readers.values():
            source.close()
    summary = {
        "method": "Independent strip decoding and raw 4-byte Float32 comparison for every crop bounding-box pixel; no resampling or source selection.",
        "input_source_files_modified": False, "package_files_modified": False,
        "expected_crop_options": len(items), "crop_options_checked": len(records), "failures": failures,
        "bounding_box_pixels_checked": sum(row["bounding_box_pixel_count"] for row in records),
        "padding_outside_source_extent_pixels": sum(row["bounding_box_pixels_outside_source_extent_nodata_filled"] for row in records),
        "bounding_box_bit_mismatch_count": sum(row["bounding_box_bit_mismatch_count"] for row in records),
        "valid_zone_pixels_checked": sum(row["valid_zone_pixel_count"] for row in records),
        "valid_zone_bit_mismatch_count": sum(row["valid_zone_bit_mismatch_count"] for row in records),
        "all_metadata_checks_pass": not failures and all(all(row["metadata_checks"].values()) for row in records),
        "all_source_window_hashes_match_crop_bytes": all(row["crop_pixel_bytes_sha256"] == row["expected_source_window_bytes_sha256"] for row in records),
        "all_86_region_counts_match": not failures and all(zone["counts_match_report"] for row in records for zone in row["zones"].values()),
        "maximum_region_mean_difference_from_report": max((zone["absolute_mean_difference_from_report"] or 0
                                                           for row in records for zone in row["zones"].values()), default=None),
        "option_count_caveat": "Totals include all 43 source options, including alternatives for four unresolved parks; not 43 unique parks or a finalized source selection.",
        "padding_caveat": "Pixels outside a source bounding extent, if present, are tested against documented NoData padding, not purported original pixels.",
    }
    target = work / "qc_crop_raw_bits.json"
    target.write_text(json.dumps(summary | {"options": records}, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
