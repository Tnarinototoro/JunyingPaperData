"""Read-only SHP/DBF audit. Never emits attribute values or point coordinates."""
import collections
import json
import math
import statistics
import struct
import sys
from pathlib import Path


def ring_stats(points):
    closed = len(points) > 1 and points[0] == points[-1]
    vertices = points[:-1] if closed else points
    if not vertices:
        return {"vertices": 0, "closed": closed, "area": 0.0}
    ox, oy = vertices[0]
    shifted = [(x - ox, y - oy) for x, y in vertices]
    edges = list(zip(shifted, shifted[1:] + shifted[:1]))
    cross = [a[0] * b[1] - b[0] * a[1] for a, b in edges]
    twice_area = sum(cross)
    area = abs(twice_area) / 2
    perimeter = sum(math.dist(a, b) for a, b in edges)
    if abs(twice_area) > 1e-12:
        cx = sum((a[0] + b[0]) * c for (a, b), c in zip(edges, cross)) / (3 * twice_area)
        cy = sum((a[1] + b[1]) * c for (a, b), c in zip(edges, cross)) / (3 * twice_area)
    else:
        cx = statistics.mean(p[0] for p in shifted)
        cy = statistics.mean(p[1] for p in shifted)
    radii = [math.hypot(x - cx, y - cy) for x, y in shifted]
    radial_mean = statistics.mean(radii)
    radial_cv = statistics.pstdev(radii) / radial_mean if radial_mean else None
    lengths = [math.dist(a, b) for a, b in edges]
    edge_mean = statistics.mean(lengths)
    edge_cv = statistics.pstdev(lengths) / edge_mean if edge_mean else None
    width = max(x for x, y in vertices) - min(x for x, y in vertices)
    height = max(y for x, y in vertices) - min(y for x, y in vertices)
    compactness = 4 * math.pi * area / perimeter**2 if perimeter else None
    return {
        "vertices": len(vertices), "closed": closed, "area": area,
        "signed_area": twice_area / 2, "perimeter": perimeter,
        "width": width, "height": height, "mean_vertex_radius": radial_mean,
        "radial_cv": radial_cv, "edge_cv": edge_cv, "compactness": compactness,
        "circle_like": bool(len(vertices) >= 16 and radial_cv is not None and
                            radial_cv < 0.03 and compactness is not None and compactness > 0.9),
        "regular_circle_like": bool(len(vertices) >= 16 and radial_cv is not None and
                                    radial_cv < 1e-5 and edge_cv is not None and edge_cv < 1e-5),
        "nonfinite_points": sum(not (math.isfinite(x) and math.isfinite(y)) for x, y in vertices),
        "zero_length_edges": sum(length == 0 for length in lengths),
    }


def read_shp(path, include_points=False):
    data = path.read_bytes()
    code = struct.unpack_from(">i", data, 0)[0]
    expected_size = struct.unpack_from(">i", data, 24)[0] * 2
    version, shape_type = struct.unpack_from("<2i", data, 28)
    bbox = struct.unpack_from("<4d", data, 36)
    records = []
    pos = 100
    while pos < len(data):
        number, words = struct.unpack_from(">2i", data, pos)
        content = data[pos + 8:pos + 8 + words * 2]
        st = struct.unpack_from("<i", content, 0)[0]
        row = {"record": number, "shape_type": st, "bytes": words * 2}
        if st in (3, 5, 13, 15, 23, 25):
            nparts, npoints = struct.unpack_from("<2i", content, 36)
            offsets = list(struct.unpack_from("<" + "i" * nparts, content, 44))
            flat = struct.unpack_from("<" + "d" * (2 * npoints), content, 44 + 4 * nparts)
            points = list(zip(flat[::2], flat[1::2]))
            ends = offsets[1:] + [npoints]
            parts = [points[start:end] for start, end in zip(offsets, ends)]
            stats = [ring_stats(part) for part in parts]
            row.update(parts=nparts, points=npoints, rings=stats,
                       area=abs(sum(s.get("signed_area", 0) for s in stats)))
            if include_points:
                row["private_parts"] = parts
        elif st == 0:
            row.update(parts=0, points=0, area=0, rings=[])
        elif st in (1, 11, 21):
            row.update(parts=0, points=1, area=0, rings=[])
        records.append(row)
        pos += 8 + words * 2
    shx = path.with_suffix(".shx")
    index_data = shx.read_bytes() if shx.exists() else b""
    index_rows = (len(index_data) - 100) // 8 if index_data else None
    index_ok = None
    if index_data:
        entries = [struct.unpack_from(">2i", index_data, p) for p in range(100, len(index_data), 8)]
        expected_entries = []
        offset = 100
        for row in records:
            expected_entries.append((offset // 2, row["bytes"] // 2))
            offset += row["bytes"] + 8
        index_ok = entries == expected_entries
    areas = [r.get("area", 0) for r in records]
    return {
        "filename": path.name, "file_code": code, "version": version,
        "shape_type": shape_type, "header_size_matches": expected_size == len(data),
        "parsed_to_end": pos == len(data), "records": len(records),
        "index_records": index_rows, "index_matches_shp": index_ok,
        "record_types": dict(collections.Counter(r["shape_type"] for r in records)),
        "bbox_width": bbox[2] - bbox[0], "bbox_height": bbox[3] - bbox[1],
        "coordinate_order_of_magnitude": max(abs(v) for v in bbox),
        "area_min": min(areas) if areas else None, "area_max": max(areas) if areas else None,
        "area_sum": sum(areas), "feature_details": records,
        "dbf_exists": path.with_suffix(".dbf").exists(),
    }


def read_dbf(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 4)[0]
    header, length = struct.unpack_from("<2H", data, 8)
    fields = []
    p = 32
    while p < header and data[p] != 13:
        d = data[p:p + 32]
        name = d[:11].split(b"\0", 1)[0].decode("utf-8", errors="replace")
        fields.append({"name": name, "type": chr(d[11]), "width": d[16], "decimals": d[17]})
        p += 32
    statuses = [data[header + i * length:header + i * length + 1] for i in range(count)]
    return {"filename": path.name, "records": count, "header_bytes": header,
            "record_bytes": length, "complete_records": (len(data) - header) // length,
            "deleted_records": sum(s == b"*" for s in statuses), "fields": fields,
            "field_widths_match_record": 1 + sum(f["width"] for f in fields) == length}


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def point_segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    denominator = dx * dx + dy * dy
    if denominator == 0:
        return math.dist(p, a)
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / denominator))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def segments_intersect(a, b, c, d):
    if (max(a[0], b[0]) < min(c[0], d[0]) - 1e-7 or
            max(c[0], d[0]) < min(a[0], b[0]) - 1e-7 or
            max(a[1], b[1]) < min(c[1], d[1]) - 1e-7 or
            max(c[1], d[1]) < min(a[1], b[1]) - 1e-7):
        return False
    c1, c2, c3, c4 = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
    if ((c1 > 0 and c2 < 0) or (c1 < 0 and c2 > 0)) and ((c3 > 0 and c4 < 0) or (c3 < 0 and c4 > 0)):
        return True
    return (point_segment_distance(a, c, d) < 1e-7 or point_segment_distance(b, c, d) < 1e-7 or
            point_segment_distance(c, a, b) < 1e-7 or point_segment_distance(d, a, b) < 1e-7)


def ring_edges(points):
    vertices = points[:-1] if points[0] == points[-1] else points
    return list(zip(vertices, vertices[1:] + vertices[:1]))


def self_intersections(points):
    edges = ring_edges(points)
    pairs = []
    for i, (a, b) in enumerate(edges):
        for j in range(i + 2, len(edges)):
            if i == 0 and j == len(edges) - 1:
                continue
            if segments_intersect(a, b, *edges[j]):
                pairs.append((i, j))
    return pairs


def point_in_ring(point, points):
    inside = False
    for a, b in ring_edges(points):
        if point_segment_distance(point, a, b) < 1e-7:
            return 0
        if (a[1] > point[1]) != (b[1] > point[1]):
            x = a[0] + (point[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > point[0]:
                inside = not inside
    return 1 if inside else -1


def ring_pair_relation(first, second):
    first_box = (min(x for x, y in first), min(y for x, y in first),
                 max(x for x, y in first), max(y for x, y in first))
    second_box = (min(x for x, y in second), min(y for x, y in second),
                  max(x for x, y in second), max(y for x, y in second))
    if first_box[2] < second_box[0] or second_box[2] < first_box[0] or first_box[3] < second_box[1] or second_box[3] < first_box[1]:
        return "separate"
    if any(segments_intersect(a, b, c, d) for a, b in ring_edges(first) for c, d in ring_edges(second)):
        return "boundaries_intersect_or_touch"
    if point_in_ring(first[0], second) >= 0:
        return "first_inside_second"
    if point_in_ring(second[0], first) >= 0:
        return "second_inside_first"
    return "separate"


def topology_summary(root):
    parks = read_shp(root / "parks_metric.shp", include_points=True)["feature_details"]
    buffer_parts = read_shp(root / "100m_buffer.shp", include_points=True)["feature_details"][0]["private_parts"]
    bad_parks = {row["record"]: sum(len(self_intersections(p)) for p in row["private_parts"]) for row in parks}
    bad_parts = {i + 1: len(self_intersections(p)) for i, p in enumerate(buffer_parts)}
    park_relations = []
    for i, row in enumerate(parks):
        for other in parks[i + 1:]:
            relation = ring_pair_relation(row["private_parts"][0], other["private_parts"][0])
            if relation != "separate":
                park_relations.append((row["record"], other["record"], relation))
    buffer_relations = []
    for i, part in enumerate(buffer_parts):
        for j in range(i + 1, len(buffer_parts)):
            relation = ring_pair_relation(part, buffer_parts[j])
            if relation != "separate":
                buffer_relations.append((i + 1, j + 1, relation))
    matches = []
    for row in parks:
        ring = row["private_parts"][0]
        matching = [i for i, part in enumerate(buffer_parts) if all(point_in_ring(point, part) >= 0 for point in ring)]
        entry = {"anonymous_record": row["record"], "covering_buffer_parts": [i + 1 for i in matching]}
        if len(matching) == 1:
            distances = [min(point_segment_distance(point, a, b) for a, b in ring_edges(ring))
                         for point in buffer_parts[matching[0]][:-1]]
            entry["buffer_vertex_distance_min"] = min(distances)
            entry["buffer_vertex_distance_max"] = max(distances)
            entry["buffer_vertex_distance_mean"] = statistics.mean(distances)
        matches.append(entry)
    return {"checks": "Standard-library planar segment/containment checks, not a GEOS validity certificate",
            "self_intersecting_park_rings": {k: v for k, v in bad_parks.items() if v},
            "self_intersecting_buffer_rings": {k: v for k, v in bad_parts.items() if v},
            "park_intersection_or_nesting_pairs": park_relations,
            "buffer_intersection_or_nesting_pairs": buffer_relations,
            "matches": matches}


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("NDVI")
    result = {"note": "Anonymous, read-only preliminary audit; ring checks are not full OGC validity."}
    for filename in ("parks_metric.shp", "100m_buffer.shp"):
        result[filename] = read_shp(root / filename)
    result["parks_metric.dbf"] = read_dbf(root / "parks_metric.dbf")
    print(json.dumps(result, ensure_ascii=True, indent=2))
