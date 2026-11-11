"""Read-only coarse footprint QA; never changes CRS, grid, buffer or identities."""

import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[1]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))

from audit_rasters_stdlib import read_ifd, first, geo_keys
from geo_math_stdlib import utm_to_lonlat, lonlat_to_utm


def main():
    records = []
    for source in sorted((ROOT / "NDVI").glob("NDVI_*.tif")):
        tags, container = read_ifd(source)
        keys = geo_keys(tags)
        epsg = keys["3072"]["value"]
        width, height = first(tags, 256), first(tags, 257)
        dx, dy = tags[33550][:2]
        tie = tags[33922]
        x0, y0 = tie[3] - tie[0] * dx, tie[4] + tie[1] * dy
        corners = [(x0, y0), (x0 + width * dx, y0), (x0, y0 - height * dy),
                   (x0 + width * dx, y0 - height * dy)]
        geographical = [utm_to_lonlat(x, y, epsg) for x, y in corners]
        inverse_errors = []
        for projected, geographic in zip(corners, geographical):
            check = lonlat_to_utm(*geographic, epsg)
            inverse_errors.append(max(abs(check[0] - projected[0]), abs(check[1] - projected[1])))
        corner_bounds = [min(lon for lon, _ in geographical), min(lat for _, lat in geographical),
                         max(lon for lon, _ in geographical), max(lat for _, lat in geographical)]
        centre_x, centre_y = x0 + width * dx / 2, y0 - height * dy / 2
        west = utm_to_lonlat(centre_x - dx, centre_y, epsg)
        east = utm_to_lonlat(centre_x + dx, centre_y, epsg)
        north = utm_to_lonlat(centre_x, centre_y + dy, epsg)
        south = utm_to_lonlat(centre_x, centre_y - dy, epsg)
        corner_lats = [lat for _, lat in geographical]
        records.append({
            "source_raster": source.name, "projected_epsg": epsg,
            "utm_central_meridian_degrees": (epsg - 32600) * 6 - 183,
            "projected_units_are_metres": keys.get("3076", {}).get("value") == 9001,
            "raster_pixel_is_area": keys.get("1025", {}).get("value") == 1,
            "dimensions": [width, height], "pixel_spacing_m": [dx, dy],
            "coarse_geographic_corner_bounds_lonlat": corner_bounds,
            "footprint_within_broad_japanese_region": 122 <= corner_bounds[0] <= corner_bounds[2] <= 154
                                                       and 20 <= corner_bounds[1] <= corner_bounds[3] <= 46,
            "northup_rows_move_south": north[1] > south[1] and dy > 0,
            "columns_move_east": east[0] > west[0] and dx > 0,
            "max_forward_inverse_check_difference_m": max(inverse_errors),
            "logical_row_storage": {"rows_per_strip": first(tags, 278),
                                    "strip_count": len(tags[273]),
                                    "strip_address_order_is_monotonic": all(a < b for a, b in zip(tags[273], tags[273][1:])),
                                    "byte_order": container["byte_order"]},
            "interpretation": "Coarse consistency of declared native CRS/grid only; not independent imagery geolocation or park identity proof.",
        })
    report = {"numbering_policy": "Accept the author's explicit confirmation that all park numbers 1–39 refer to the same parks; no renumbering or inferred crosswalk.",
              "source_files_modified": False, "resampling_or_crs_reassignment": False,
              "utm_inverse_routine": "Existing local standard-library WGS84 UTM implementation; no network or package installation.",
              "source_raster_count": len(records), "rasters": records,
              "scope_caveat": "Plausible Japanese footprint does not prove the correct park outline or acquisition product/date. Filenames are not reliable geographic pairing evidence."}
    target = WORK / "native_crs_footprints.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"count": len(records),
                      "all_broad_region_checks_pass": all(row["footprint_within_broad_japanese_region"] for row in records),
                      "all_northup_checks_pass": all(row["northup_rows_move_south"] and row["columns_move_east"] for row in records),
                      "max_coordinate_roundtrip_difference_m": max(row["max_forward_inverse_check_difference_m"] for row in records),
                      "raster_corner_bounds": [{"file": row["source_raster"], "epsg": row["projected_epsg"],
                                                "lonlat_bounds": [round(x, 5) for x in row["coarse_geographic_corner_bounds_lonlat"]]}
                                               for row in records]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
