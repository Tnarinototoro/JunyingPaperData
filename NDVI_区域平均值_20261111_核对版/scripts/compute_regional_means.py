"""Calculate pixel-centre zonal means from supplied uncompressed GeoTIFFs.

Raw inputs are never written. Uses the supplied park polygons and supplied
100 m buffer geometry, paired by containment. The exterior excludes its park.
No resampling, NDBI substitution, raster-wide approximate statistics, or
midrange calculation is used to obtain a regional mean.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import mmap
from pathlib import Path
import statistics
import struct
import time

from audit_rasters_stdlib import read_ifd, first, geo_keys, metadata_items
from audit_vectors_std import read_shp, point_in_ring, ring_stats
from geo_math_stdlib import albers_to_utm, utm_to_albers, self_test


class Ring:
    def __init__(self, vertices):
        self.vertices = vertices[:-1] if vertices[0] == vertices[-1] else vertices
        self.edges = list(zip(self.vertices, self.vertices[1:] + self.vertices[:1]))
        self.box = (min(x for x, y in self.vertices), min(y for x, y in self.vertices),
                    max(x for x, y in self.vertices), max(y for x, y in self.vertices))

    def contains(self, x, y):
        if x < self.box[0] or x > self.box[2] or y < self.box[1] or y > self.box[3]:
            return False
        inside = False
        for (ax, ay), (bx, by) in self.edges:
            if (ay > y) != (by > y):
                crossing = ax + (y - ay) * (bx - ax) / (by - ay)
                if crossing > x:
                    inside = not inside
        return inside


class Raster:
    def __init__(self, path):
        self.path = path
        self.tags, self.container = read_ifd(path)
        self.keys = geo_keys(self.tags)
        self.epsg = self.keys.get('3072', {}).get('value')
        if self.epsg not in (32652, 32653, 32654):
            raise ValueError('This calculation accepts only the supplied WGS84 UTM NDVI rasters')
        checks = [(first(self.tags, 259), 1), (first(self.tags, 277, 1), 1),
                  (first(self.tags, 258), 32), (first(self.tags, 339), 3),
                  (first(self.tags, 278), 1), (self.container['byte_order'], '<')]
        if any(actual != expected for actual, expected in checks):
            raise ValueError('Unsupported TIFF pixel storage; no silent fallback')
        if self.keys.get('1025', {}).get('value', 1) != 1:
            raise ValueError('RasterPixelIsPoint not supported by this pixel-centre convention')
        self.width, self.height = first(self.tags, 256), first(self.tags, 257)
        scale, tie = self.tags[33550], self.tags[33922]
        if 34264 in self.tags:
            raise ValueError('Rotated rasters are not supported')
        self.dx, self.dy = scale[:2]
        self.x0, self.y0 = tie[3] - tie[0] * self.dx, tie[4] + tie[1] * self.dy
        self.offsets, self.bytecounts = self.tags[273], self.tags[279]
        if len(self.offsets) != self.height or len(self.bytecounts) != self.height:
            raise ValueError('Strip count is not equal to raster height')
        if any(n not in (0, self.width * 4) for n in self.bytecounts):
            raise ValueError('Unexpected byte count in uncompressed row strip')
        raw_nodata = self.tags.get(42113)
        self.nodata = struct.unpack('<f', struct.pack('<f', float(raw_nodata)))[0] if raw_nodata else None
        items = metadata_items(self.tags.get(42112))
        self.scale = float(next((x['value'] for x in items if x.get('role') == 'scale'), 1))
        self.value_offset = float(next((x['value'] for x in items if x.get('role') == 'offset'), 0))
        self.file = path.open('rb')
        self.map = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)

    def close(self):
        self.map.close()
        self.file.close()

    def get_row(self, row, c0, c1):
        if not (0 <= row < self.height) or c1 < 0 or c0 >= self.width:
            return None, None
        lo, hi = max(0, c0), min(self.width - 1, c1)
        offset, bytecount = self.offsets[row], self.bytecounts[row]
        if offset == 0 and bytecount == 0:
            return lo, [self.nodata] * (hi - lo + 1)
        if offset < 8 or offset + bytecount > len(self.map):
            raise ValueError('Row strip lies outside source file')
        values = struct.unpack_from('<' + 'f' * (hi - lo + 1), self.map, offset + lo * 4)
        return lo, values

    def is_valid(self, value):
        return math.isfinite(value) and (self.nodata is None or value != self.nodata)


def mapped_bounds(vertices, epsg):
    points = []
    for a, b in zip(vertices, vertices[1:]):
        n = max(1, math.ceil(math.dist(a, b) / 100.0))
        for j in range(n):
            t = j / n
            points.append(albers_to_utm(a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), epsg))
    points.append(albers_to_utm(*vertices[-1], epsg))
    return min(x for x, y in points), min(y for x, y in points), max(x for x, y in points), max(y for x, y in points)


def stats(values, counts):
    n = len(values)
    mean = math.fsum(values) / n if n else None
    return dict(counts, valid_n=n, mean=mean,
                minimum=min(values) if n else None, maximum=max(values) if n else None,
                sd_population=math.sqrt(math.fsum((v - mean) ** 2 for v in values) / n) if n else None,
                valid_fraction=n / counts['eligible_n'] if counts['eligible_n'] else None)


def calculate(park_id, park_vertices, buffer_vertices, raster, keep_pixels=False):
    try:
        bx0, by0, bx1, by1 = mapped_bounds(buffer_vertices, raster.epsg)
    except ValueError:
        return None
    rx1, ry0 = raster.x0 + raster.width * raster.dx, raster.y0 - raster.height * raster.dy
    if bx1 < raster.x0 or bx0 > rx1 or by1 < ry0 or by0 > raster.y0:
        return None
    c0 = math.floor((bx0 - raster.x0) / raster.dx) - 1
    c1 = math.ceil((bx1 - raster.x0) / raster.dx) + 1
    r0 = math.floor((raster.y0 - by1) / raster.dy) - 1
    r1 = math.ceil((raster.y0 - by0) / raster.dy) + 1
    if (c1 - c0 + 1) * (r1 - r0 + 1) > 2_000_000:
        raise ValueError('Unexpectedly large per-park ROI')
    park, buffer = Ring(park_vertices), Ring(buffer_vertices)
    values = {1: [], 2: []}
    counts = {z: dict(eligible_n=0, nodata_n=0, outside_extent_n=0, out_of_range_n=0) for z in (1, 2)}
    signature = hashlib.sha256(struct.pack('<I', raster.epsg))
    pixels = []
    crop, mask = [], []
    for row in range(r0, r1 + 1):
        lo, rawrow = raster.get_row(row, c0, c1)
        y = raster.y0 - (row + 0.5) * raster.dy
        crow, mrow = [], []
        for col in range(c0, c1 + 1):
            x = raster.x0 + (col + 0.5) * raster.dx
            ax, ay = utm_to_albers(x, y, raster.epsg)
            zone = (1 if park.contains(ax, ay) else 2) if buffer.contains(ax, ay) else 0
            in_extent = 0 <= row < raster.height and 0 <= col < raster.width
            raw = rawrow[col - lo] if in_extent and rawrow is not None else raster.nodata
            valid = raw is not None and raster.is_valid(raw)
            value = raw * raster.scale + raster.value_offset if valid else None
            if keep_pixels:
                crow.append(raw if raw is not None else -3.4028234663852886e38)
                mrow.append(zone)
            if not zone:
                continue
            counts[zone]['eligible_n'] += 1
            if not in_extent:
                counts[zone]['outside_extent_n'] += 1
                signature.update(struct.pack('<ddBB', round(x, 6), round(y, 6), zone, 0))
            elif not valid:
                counts[zone]['nodata_n'] += 1
                signature.update(struct.pack('<ddBB', round(x, 6), round(y, 6), zone, 1))
            else:
                if not (-1.000001 <= value <= 1.000001):
                    counts[zone]['out_of_range_n'] += 1
                values[zone].append(value)
                signature.update(struct.pack('<ddBBf', round(x, 6), round(y, 6), zone, 2, value))
                if keep_pixels:
                    pixels.append((park_id, 'inside' if zone == 1 else 'outside', raster.path.name, row, col, value))
        if keep_pixels:
            crop.append(crow)
            mask.append(mrow)
    result = {'ParkID': park_id, 'source_raster': raster.path.name, 'epsg': raster.epsg,
              'inside': stats(values[1], counts[1]), 'outside': stats(values[2], counts[2]),
              'pixel_signature_sha256': signature.hexdigest(),
              # This flag concerns all eligible pixel centres, not coverage of
              # every point of the continuous polygon or absence of NoData.
              'full_extent': all(counts[z]['outside_extent_n'] == 0 for z in (1, 2)),
              'pixel_rule': 'Native raster pixel centre; exterior = supplied buffer part minus supplied park polygon'}
    if keep_pixels:
        result.update(private_pixels=pixels, private_crop=crop, private_mask=mask,
                      private_window=[c0, r0, c1, r1])
    return result


def load_geometry(input_dir):
    prj = (input_dir / 'parks_metric.prj').read_text(encoding='utf-8').strip()
    other_prj = (input_dir / '100m_buffer.prj').read_text(encoding='utf-8').strip()
    if prj != other_prj or 'Asia_North_Albers_Equal_Area_Conic' not in prj:
        raise ValueError('Source vector CRS differs from the audited Albers definition')
    required = ['Central_Meridian",95', 'Standard_Parallel_1",15', 'Standard_Parallel_2",65',
                'Latitude_Of_Origin",30', '6378137', 'UNIT["Meter",1']
    if any(x not in prj for x in required):
        raise ValueError('Vector CRS parameters are not the expected Albers parameters')
    parks = read_shp(input_dir / 'parks_metric.shp', include_points=True)['feature_details']
    buffer_rows = read_shp(input_dir / '100m_buffer.shp', include_points=True)['feature_details']
    if len(parks) != 39 or len(buffer_rows) != 1:
        raise ValueError('Unexpected park or buffer feature count')
    parts = buffer_rows[0]['private_parts']
    paired = []
    used = set()
    for park in parks:
        if len(park['private_parts']) != 1:
            raise ValueError('Unexpected park multipart geometry')
        vertices = park['private_parts'][0]
        matches = [i for i, ring in enumerate(parts) if all(point_in_ring(p, ring) >= 0 for p in vertices)]
        if len(matches) != 1 or matches[0] in used:
            raise ValueError('Park/buffer containment is not unique')
        used.add(matches[0])
        paired.append({'ParkID': park['record'], 'park': vertices, 'buffer': parts[matches[0]],
                       'buffer_part': matches[0] + 1,
                       'area_inside_projected_m2': ring_stats(vertices)['area'],
                       'area_outside_projected_m2': ring_stats(parts[matches[0]])['area'] - ring_stats(vertices)['area']})
    return paired, prj


def original_extrema(root):
    path = root / '17 NDVI補足資料S1.tsv'
    if not path.exists():
        return {}
    with path.open(encoding='utf-8', newline='') as stream:
        return {int(row['park_code'][1:]): row for row in csv.DictReader(stream, delimiter='\t')}


def matches_original_extrema(candidate, original):
    if not original:
        return False
    for side in ('inside', 'outside'):
        for name, field in [('minimum', 'min'), ('maximum', 'max')]:
            actual = candidate[side][name]
            if actual is None or abs(actual - float(original[f'ndvi_{side}_{field}'])) > 2e-9:
                return False
    return True


def select_candidate(candidates):
    usable = [c for c in candidates if c['full_extent'] and all(
        c[s]['valid_n'] > 0 and c[s]['out_of_range_n'] == 0 for s in ('inside', 'outside'))]
    if not usable:
        return None, 'no_usable_full_extent_source'
    prior = [c for c in usable if c.get('original_four_extrema_match')]
    if len(prior) == 1:
        return prior[0], 'unique_match_to_previous_four_extrema'
    if len(usable) == 1:
        return usable[0], 'unique_usable_full_extent_source'
    if len({c['pixel_signature_sha256'] for c in usable}) == 1:
        return sorted(usable, key=lambda c: c['source_raster'])[0], 'overlap_pixels_identical'
    return None, 'multiple_nonidentical_full_extent_sources_need_confirmation'


def write_csv(path, rows, columns):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def scan(input_dir, work_dir):
    started = time.perf_counter()
    transform_tests = self_test()
    pairs, prj = load_geometry(input_dir)
    previous = original_extrema(input_dir.parent)
    rasters = [Raster(path) for path in sorted(input_dir.glob('NDVI_*.tif'))]
    result, flat = [], []
    try:
        for pair in pairs:
            candidates = []
            for raster in rasters:
                candidate = calculate(pair['ParkID'], pair['park'], pair['buffer'], raster)
                if candidate:
                    candidate['original_four_extrema_match'] = matches_original_extrema(candidate, previous.get(pair['ParkID']))
                    candidates.append(candidate)
                    item = {'ParkID': pair['ParkID'], 'source_raster': candidate['source_raster'],
                            'epsg': candidate['epsg'], 'full_extent': candidate['full_extent'],
                            'original_four_extrema_match': candidate['original_four_extrema_match']}
                    for side in ('inside', 'outside'):
                        item.update({side + '_' + key: val for key, val in candidate[side].items()})
                    flat.append(item)
            selected, decision = select_candidate(candidates)
            result.append({k: v for k, v in pair.items() if k not in ('park', 'buffer')} | {
                'decision': decision, 'selected_source': selected['source_raster'] if selected else None,
                'selected': selected, 'candidates': candidates})
            print(json.dumps({'ParkID': pair['ParkID'], 'candidate_sources': len(candidates),
                              'decision': decision, 'selected_source': selected['source_raster'] if selected else None}), flush=True)
    finally:
        for raster in rasters:
            raster.close()
    all_complete = all(row['selected'] is not None for row in result)
    report = {'status': 'complete_source_selection' if all_complete else 'source_confirmation_required',
              'transform_self_tests': transform_tests, 'parks': result,
              'input_park_count': len(pairs), 'ndvi_raster_count': len(rasters),
              'excluded': 'NDBI rasters and ambiguous Hokka auxiliary copies are not used',
              'roi': 'Supplied park polygon; supplied approximately 100m Albers-plane buffer part minus park',
              'mean': 'Arithmetic mean of all finite, non-NoData, native-grid pixel-centre values in each ROI',
              'nodata': 'NoData excluded, not zero-imputed; valid zero and negative NDVI retained',
              'resampling': False, 'imagery_time': 'Not established by the supplied TIFF tags',
              'elapsed_seconds': time.perf_counter() - started}
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / 'regional_mean_source_scan.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    columns = ['ParkID', 'source_raster', 'epsg', 'full_extent', 'original_four_extrema_match']
    for side in ('inside', 'outside'):
        columns.extend(side + '_' + key for key in ('mean', 'valid_n', 'eligible_n', 'nodata_n',
                                                   'outside_extent_n', 'out_of_range_n', 'valid_fraction',
                                                   'minimum', 'maximum', 'sd_population'))
    write_csv(work_dir / 'regional_mean_candidates.csv', flat, columns)
    print(json.dumps({'status': report['status'], 'selected_park_count': sum(r['selected'] is not None for r in result),
                      'unresolved_ParkID': [r['ParkID'] for r in result if r['selected'] is None],
                      'elapsed_seconds': report['elapsed_seconds']}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=Path, default=Path('NDVI'))
    parser.add_argument('--work-dir', type=Path, default=Path('NDVI_mean_work'))
    args = parser.parse_args()
    scan(args.input_dir.resolve(), args.work_dir.resolve())
