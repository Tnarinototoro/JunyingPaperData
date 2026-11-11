"""Recompute every packaged zonal mean from NDVI crops and zone masks.

This verification uses only packaged files, not the original regional rasters.
No third-party Python packages are required. Inputs are never modified.
"""
import hashlib
import json
import math
import mmap
from pathlib import Path
import struct
import sys

from audit_rasters_stdlib import read_ifd, first, geo_keys


def verify(root):
    entries = json.loads((root / 'GIS/pixel_extractions.json').read_text(encoding='utf-8'))
    results = []
    for entry in entries:
        ndvi_path, mask_path = root / entry['ndvi_crop'], root / entry['zone_mask']
        tags, info = read_ifd(ndvi_path)
        mtags, minfo = read_ifd(mask_path)
        width, height = first(tags, 256), first(tags, 257)
        assert (width, height) == (first(mtags, 256), first(mtags, 257))
        assert first(tags, 259) == first(mtags, 259) == 1
        assert first(tags, 258) == 32 and first(tags, 339) == 3
        assert first(mtags, 258) == 8
        assert tags[33550] == mtags[33550] and tags[33922] == mtags[33922]
        assert geo_keys(tags)['3072']['value'] == geo_keys(mtags)['3072']['value'] == entry['source_epsg']
        nodata = struct.unpack('<f', struct.pack('<f', float(tags[42113])))[0]
        values = {'inside': [], 'outside': []}
        eligible, missing = dict(inside=0, outside=0), dict(inside=0, outside=0)
        with ndvi_path.open('rb') as ns, mask_path.open('rb') as ms:
            with mmap.mmap(ns.fileno(), 0, access=mmap.ACCESS_READ) as nm, mmap.mmap(ms.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                for row in range(height):
                    nv = struct.unpack_from('<' + 'f' * width, nm, tags[273][row])
                    masks = mm[mtags[273][row]:mtags[273][row] + width]
                    for value, zone in zip(nv, masks):
                        if zone not in (1, 2):
                            continue
                        side = 'inside' if zone == 1 else 'outside'
                        eligible[side] += 1
                        if not math.isfinite(value) or value == nodata:
                            missing[side] += 1
                        else:
                            values[side].append(value)
        errors = []
        for side in ('inside', 'outside'):
            actual_mean = math.fsum(values[side]) / len(values[side])
            expected = entry[side]
            assert len(values[side]) == expected['valid_n']
            assert eligible[side] == expected['eligible_n']
            assert missing[side] == expected['nodata_n'] + expected['outside_extent_n']
            error = abs(actual_mean - expected['mean'])
            assert error < 1e-15
            errors.append(error)
        results.append({'label': entry['label'], 'counts_match': True, 'max_abs_mean_difference': max(errors)})
    return {'options_verified': len(results), 'regions_verified': len(results) * 2,
            'maximum_mean_difference': max(row['max_abs_mean_difference'] for row in results),
            'all_counts_match': True, 'details': results,
            'note': 'Each option is verified separately; this does not resolve the four imagery choices.'}


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    print(json.dumps(verify(root), ensure_ascii=True, indent=2))
