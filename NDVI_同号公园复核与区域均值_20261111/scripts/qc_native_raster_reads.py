"""Independent seek/read Float32 QC; source files are opened read-only."""

import json
import math
from pathlib import Path
import struct

from audit_rasters_stdlib import read_ifd, first, geo_keys, metadata_items
from compute_regional_means import Raster, load_geometry, mapped_bounds
from geo_math_stdlib import utm_to_albers


def inside_polygon(x, y, points):
    """Independent even/odd ray test; audit does not change source polygons."""
    pts = points[:-1] if points[0] == points[-1] else points
    inside = False
    previous = pts[-1]
    for current in pts:
        if (current[1] > y) != (previous[1] > y):
            crossing = (previous[0] - current[0]) * (y - current[1]) / (previous[1] - current[1]) + current[0]
            if x < crossing:
                inside = not inside
        previous = current
    return inside


def main():
    work = Path(__file__).resolve().parent
    source_dir = work.parent / "NDVI"
    scan = json.loads((work / "regional_mean_source_scan.json").read_text(encoding="utf-8"))
    pairs, _ = load_geometry(source_dir)
    paired = {row["ParkID"]: row for row in pairs}
    selected_ids = [1, 5, 7, 10, 11, 21, 22, 29, 30, 34, 39]
    records = []
    for report in scan["parks"]:
        if report["ParkID"] not in selected_ids or report["selected"] is None:
            continue
        candidate = report["selected"]
        pair = paired[report["ParkID"]]
        path = source_dir / candidate["source_raster"]
        tags, container = read_ifd(path)
        epsg = geo_keys(tags)["3072"]["value"]
        width, height = first(tags, 256), first(tags, 257)
        dx, dy = tags[33550][:2]
        tie = tags[33922]
        x0, y0 = tie[3] - tie[0] * dx, tie[4] + tie[1] * dy
        raw_nodata = struct.unpack("<f", struct.pack("<f", float(tags[42113])))[0]
        items = metadata_items(tags.get(42112))
        value_scale = float(next((item["value"] for item in items if item.get("role") == "scale"), 1))
        value_offset = float(next((item["value"] for item in items if item.get("role") == "offset"), 0))
        bx0, by0, bx1, by1 = mapped_bounds(pair["buffer"], epsg)
        c0, c1 = math.floor((bx0 - x0) / dx) - 1, math.ceil((bx1 - x0) / dx) + 1
        r0, r1 = math.floor((y0 - by1) / dy) - 1, math.ceil((y0 - by0) / dy) + 1
        values = {"inside": [], "outside": []}
        eligible = {"inside": 0, "outside": 0}
        nodata = {"inside": 0, "outside": 0}
        out_extent = {"inside": 0, "outside": 0}
        samples = []
        main_reader = Raster(path)
        try:
            with path.open("rb") as source:
                for row in range(r0, r1 + 1):
                    lo, hi = max(c0, 0), min(c1, width - 1)
                    source_row = None
                    if 0 <= row < height and lo <= hi:
                        offset, count = tags[273][row], tags[279][row]
                        if offset and count:
                            source.seek(offset + lo * 4)
                            rowbytes = source.read((hi - lo + 1) * 4)
                            source_row = struct.unpack("<" + "f" * (hi - lo + 1), rowbytes)
                    for col in range(c0, c1 + 1):
                        x, y = x0 + (col + 0.5) * dx, y0 - (row + 0.5) * dy
                        ax, ay = utm_to_albers(x, y, epsg)
                        if not inside_polygon(ax, ay, pair["buffer"]):
                            continue
                        side = "inside" if inside_polygon(ax, ay, pair["park"]) else "outside"
                        eligible[side] += 1
                        if not (0 <= row < height and 0 <= col < width):
                            out_extent[side] += 1
                            continue
                        raw = source_row[col - lo] if source_row is not None else raw_nodata
                        if not math.isfinite(raw) or raw == raw_nodata:
                            nodata[side] += 1
                            continue
                        values[side].append(raw * value_scale + value_offset)
                for row, col in [(0, 0), (height // 2, width // 2), (height - 1, width - 1)]:
                    offset, count = tags[273][row], tags[279][row]
                    if not offset or not count:
                        samples.append({"row": row, "col": col, "sparse_strip": True})
                        continue
                    source.seek(offset + col * 4)
                    rawbytes = source.read(4)
                    direct = struct.unpack("<f", rawbytes)[0]
                    _, result = main_reader.get_row(row, col, col)
                    reencoded = struct.pack("<f", result[0])
                    same_bits = rawbytes == reencoded
                    samples.append({"row": row, "col": col, "source_float32_bytes_hex": rawbytes.hex(),
                                    "value": direct if math.isfinite(direct) else str(direct),
                                    "main_reader_matches_source_bits": same_bits,
                                    "is_nodata": direct == raw_nodata,
                                    "main_is_valid": main_reader.is_valid(result[0])})
        finally:
            main_reader.close()
        checked = {"ParkID": report["ParkID"], "source_raster": candidate["source_raster"],
                   "epsg": epsg, "byte_order": container["byte_order"],
                   "samples": samples, "zones": {}}
        for side in ("inside", "outside"):
            mean = math.fsum(values[side]) / len(values[side]) if values[side] else None
            expected = candidate[side]
            got = {"eligible_n": eligible[side], "valid_n": len(values[side]),
                   "nodata_n": nodata[side], "outside_extent_n": out_extent[side], "mean": mean}
            got["reported_mean"] = expected["mean"]
            got["absolute_mean_difference"] = abs(mean - expected["mean"]) if mean is not None else None
            got["counts_match"] = all(got[key] == expected[key] for key in
                                       ["eligible_n", "valid_n", "nodata_n", "outside_extent_n"])
            checked["zones"][side] = got
        records.append(checked)
    report = {"method": "Independent original-strip seek/read Float32 decode and even/odd ROI count; existing transform routines shared; no source selection or resampling.",
              "source_files_read_only": True, "whole_raster_arrays_loaded": False,
              "park_count": len(records), "raw_word_sample_count": sum(len(row["samples"]) for row in records),
              "all_samples_match_bits": all(sample.get("main_reader_matches_source_bits", True)
                                            for row in records for sample in row["samples"]),
              "all_zone_counts_match": all(zone["counts_match"] for row in records for zone in row["zones"].values()),
              "maximum_zone_mean_difference": max(zone["absolute_mean_difference"] or 0
                                                   for row in records for zone in row["zones"].values()),
              "parks": records}
    target = work / "qc_native_raster_reads.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "parks"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
