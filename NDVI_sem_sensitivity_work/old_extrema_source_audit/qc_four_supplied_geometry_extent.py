"""Read-only extent/topology inspection of four author-labelled park outlines.

No identities or absolute coordinates are output. Relative local-UTM vertices
are supplied only for private outline plots, not public site-location maps.
"""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
from audit_vectors_std import read_shp, ring_stats, self_intersections
from qc_regional_means_stdlib import inverse_albers, forward_utm

TARGETS = (9, 18, 28, 32)


def planar_centroid(points):
    pts = points[:-1] if points[0] == points[-1] else points
    ox, oy = pts[0]
    shifted = [(x - ox, y - oy) for x, y in pts]
    edges = list(zip(shifted, shifted[1:] + shifted[:1]))
    crosses = [a[0] * b[1] - b[0] * a[1] for a, b in edges]
    twice_area = math.fsum(crosses)
    return (ox + math.fsum((a[0] + b[0]) * c for (a, b), c in zip(edges, crosses)) / (3 * twice_area),
            oy + math.fsum((a[1] + b[1]) * c for (a, b), c in zip(edges, crosses)) / (3 * twice_area))


def principal_dimensions(points):
    pts = points[:-1] if points[0] == points[-1] else points
    mx, my = math.fsum(x for x, _ in pts) / len(pts), math.fsum(y for _, y in pts) / len(pts)
    xx = math.fsum((x - mx)**2 for x, _ in pts)
    yy = math.fsum((y - my)**2 for _, y in pts)
    xy = math.fsum((x - mx) * (y - my) for x, y in pts)
    theta = 0.5 * math.atan2(2 * xy, xx - yy)
    along = [(x - mx) * math.cos(theta) + (y - my) * math.sin(theta) for x, y in pts]
    across = [-(x - mx) * math.sin(theta) + (y - my) * math.cos(theta) for x, y in pts]
    length, width = max(along) - min(along), max(across) - min(across)
    return {"vertex_pca_major_span_m": length, "vertex_pca_minor_span_m": width,
            "vertex_pca_span_ratio": length / width if width else None,
            "method": "Vertex-PCA descriptive dimensions, not a minimum-area rectangle or river reach length"}


def main():
    path = ROOT / "NDVI/parks_metric.shp"
    all_features = read_shp(path, include_points=True)["feature_details"]
    records = []
    for feature in all_features:
        park_id = feature["record"]
        if park_id not in TARGETS:
            continue
        ring = feature["private_parts"][0]
        center_lon, center_lat = inverse_albers(*planar_centroid(ring))
        epsg = 32600 + int(math.floor((center_lon + 180) / 6) + 1)
        utm_ring = [forward_utm(*inverse_albers(x, y), epsg) for x, y in ring]
        xs, ys = [x for x, _ in utm_ring], [y for _, y in utm_ring]
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        utm_stats = ring_stats(utm_ring)
        relative = [[round(x - min(xs), 6), round(y - min(ys), 6)] for x, y in utm_ring]
        max_vertex_distance = max(math.dist(a, b) for a in utm_ring for b in utm_ring)
        records.append({"ParkID": park_id,
            "author_confirmed_numbering_accepted": True,
            "physical_record_number": feature["record"], "shape_type": feature["shape_type"],
            "ring_count": feature["parts"], "closed_exterior_ring_count": sum(part[0] == part[-1] for part in feature["private_parts"]),
            "polygon_connected_components_from_audited_single_ring": 1 if feature["parts"] == 1 else None,
            "holes_from_audited_geometry": 0 if feature["parts"] == 1 else None,
            "vertex_count_including_closure": feature["points"],
            "self_intersection_count": sum(len(self_intersections(part)) for part in feature["private_parts"]),
            "equal_area_native_projection_area_m2": feature["area"],
            "equal_area_native_projection_area_ha": feature["area"] / 10000,
            "local_utm_epsg_for_relative_outline": epsg,
            "local_utm_polygon_area_m2": utm_stats["area"],
            "utm_vs_native_equal_area_percent_difference": 100 * (utm_stats["area"] / feature["area"] - 1),
            "local_utm_east_west_extent_m": width, "local_utm_north_south_extent_m": height,
            "maximum_vertex_to_vertex_distance_m": max_vertex_distance,
            "local_utm_exterior_perimeter_m": utm_stats["perimeter"],
            "compactness_4pi_area_perimeter_squared": utm_stats["compactness"],
            "principal_dimension_description": principal_dimensions(utm_ring),
            "author_reported_multi_area_count": 3 if park_id == 18 else 5 if park_id == 28 else None,
            "separate_area_or_administrative_boundaries_available_in_supplied_shapefile": False,
            "can_certify_complete_coverage_of_all_reported_areas_from_local_outline_alone": False if park_id in (18, 28) else None,
            "relative_plot_vertices_m": relative,
            "relative_plot_origin": "Arbitrary local-UTM minimum x/y; absolute origin and geographic coordinates intentionally withheld",
        })
    report = {
        "purpose": "Inspect supplied same-number whole-park outlines for four clarified identities; accept author numbering, no identity reordering or boundary invention",
        "input_file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "records": records,
        "private_plot_caveat": "Relative outlines have no names, addresses or absolute coordinates and are for internal root inspection only; not official maps",
        "input_gis_files_modified": False, "geometry_or_id_reordering_performed": False,
        "source_selection_based_on_sem_or_extrema": False, "sem_run_performed": False,
        "interpretation": [
            "All four supplied records use one closed exterior ring. A connected whole-park outline can include several administrative or management areas; one ring does not prove an area was omitted.",
            "The shapefile contains no component boundaries or area-specific labels. Extent/shape alone cannot certify coverage of every one of the reported three or five areas.",
            "The earlier same-number address-region screen shows no obvious regional contradiction. It does not independently geocode a precise street address, park entrance or legal boundary.",
            "No raw address is converted into a supposedly exact boundary, and no existing geometry is expanded or adjusted to chase an old statistic or improve SEM.",
            "These properties describe the author's supplied boundary as it stands. A complete-area claim must follow the author's intended selection rather than the number of rings or a bibliographic assumption."
        ],
    }
    print(json.dumps(report, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
