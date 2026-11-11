"""Independent NDVI scenario standardization QC, not SEM estimation.

No imagery is selected by agreement with old SEM outcomes. Original inputs
and derived GIS review files are read-only. Reported associations with old
NDVI columns are descriptive checks, not a source-selection criterion.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.paper15_work'))
from read_numeric_sav import decode_numeric_matrix


def stdev_sample(values):
    mean = math.fsum(values) / len(values)
    return math.sqrt(math.fsum((v - mean) ** 2 for v in values) / (len(values) - 1))


def correlation(left, right):
    lm, rm = math.fsum(left) / len(left), math.fsum(right) / len(right)
    numerator = math.fsum((x - lm) * (y - rm) for x, y in zip(left, right))
    denominator = math.sqrt(math.fsum((x - lm) ** 2 for x in left)
                            * math.fsum((y - rm) ** 2 for y in right))
    return numerator / denominator


def build_qc():
    sav_path = ROOT / '最终用于sem的匿名39✖16输入矩阵.sav'
    source_hash_before = hashlib.sha256(sav_path.read_bytes()).hexdigest()
    saved = decode_numeric_matrix(sav_path)
    decoded = json.loads((ROOT / '.paper15_work/sem_input_decoded.json').read_text(encoding='utf-8'))
    assert saved['rows'] == decoded['rows']
    assert saved['variables'] == decoded['variables']
    assert saved['case_count'] == 39 and saved['variable_count'] == 17
    names = [variable['name'] for variable in saved['variables']]
    columns = {name: i for i, name in enumerate(names)}
    inside_name, outside_name = 'Z内部NDVI平均値', 'Z外部NDVI平均値'
    assert saved['variables'][columns[inside_name]]['label'] == '公園内部緑化度'
    assert saved['variables'][columns[outside_name]]['label'] == '公園外部緑化度'
    assert [int(row[columns['ParkID']]) for row in saved['rows']] == list(range(1, 40))
    assert all(all(value is not None and math.isfinite(value) for value in row) for row in saved['rows'])
    old = {
        'inside': [row[columns[inside_name]] for row in saved['rows']],
        'outside': [row[columns[outside_name]] for row in saved['rows']],
    }
    package = ROOT / 'NDVI_区域平均值_20261111_核对版'
    with (package / 'NDVI_area_means_39_review.csv').open(encoding='utf-8-sig', newline='') as stream:
        main = {int(row['ParkID']): row for row in csv.DictReader(stream)}
    with (package / 'overlap_sources_4parks.csv').open(encoding='utf-8-sig', newline='') as stream:
        alternatives = {(int(row['ParkID']), row['source_raster']): row for row in csv.DictReader(stream)}
    extraction = json.loads((package / 'GIS/pixel_extractions.json').read_text(encoding='utf-8'))
    by_source = {(entry['ParkID'], entry['source_raster']): entry for entry in extraction}
    selected = {entry['ParkID']: entry for entry in extraction if entry['status'] == 'CONFIRMED'}
    assert sorted(pid for pid, row in main.items() if row['status'] == 'CHOOSE_SOURCE') == [9, 18, 28, 32]
    assert len(alternatives) == 8 and len(selected) == 35 and len(extraction) == 43
    for (pid, source), row in alternatives.items():
        detail = by_source[(pid, source)]
        assert float(row['inside_mean']) == detail['inside']['mean']
        assert float(row['outside_mean']) == detail['outside']['mean']
        assert int(row['inside_valid_pixels']) == detail['inside']['valid_n']
        assert int(row['outside_valid_pixels']) == detail['outside']['valid_n']
    for pid, row in main.items():
        if row['status'] == 'CONFIRMED':
            assert float(row['ndvi_inside_area_mean']) == selected[pid]['inside']['mean']
            assert float(row['ndvi_outside_100m_ring_area_mean']) == selected[pid]['outside']['mean']
        else:
            assert row['ndvi_inside_area_mean'] == row['ndvi_outside_100m_ring_area_mean'] == ''
    scenarios = [
        (1, 'NDVI_nagoya.tif', 'NDVI_fukushima.tif'),
        (2, 'NDVI_nagoya.tif', 'NDVI_fukushima_up.tif'),
        (3, 'NDVI_nara.tif', 'NDVI_fukushima.tif'),
        (4, 'NDVI_nara.tif', 'NDVI_fukushima_up.tif'),
    ]
    all_rows, scenario_report = [], []
    for number, central_source, north_source in scenarios:
        raw, used = {'inside': [], 'outside': []}, []
        for pid in range(1, 40):
            if pid in (9, 18, 28):
                entry = by_source[(pid, central_source)]
            elif pid == 32:
                entry = by_source[(pid, north_source)]
            else:
                entry = selected[pid]
            used.append(entry)
            for side in ('inside', 'outside'):
                assert entry[side]['valid_n'] > 0
                raw[side].append(entry[side]['mean'])
        z, side_report = {}, {}
        for side in ('inside', 'outside'):
            mean = math.fsum(raw[side]) / 39
            sd = stdev_sample(raw[side])
            assert sd > 0
            z[side] = [(value - mean) / sd for value in raw[side]]
            z_mean, z_sd = math.fsum(z[side]) / 39, stdev_sample(z[side])
            assert abs(z_mean) < 1e-14 and abs(z_sd - 1) < 1e-14
            side_report[side] = {
                'raw_min': min(raw[side]), 'raw_max': max(raw[side]),
                'raw_mean_across_39': mean, 'raw_sample_sd_across_39': sd,
                'z_mean': z_mean, 'z_sample_sd': z_sd,
                'z_min': min(z[side]), 'z_max': max(z[side]),
                'old_input_correlation_descriptive_only': correlation(z[side], old[side]),
            }
        for i, entry in enumerate(used):
            all_rows.append({
                'scenario': number, 'ParkID': i + 1, 'source_raster': entry['source_raster'],
                'ndvi_inside_area_mean': raw['inside'][i], 'ndvi_outside_area_mean': raw['outside'][i],
                'z_inside_area_mean': z['inside'][i], 'z_outside_area_mean': z['outside'][i],
                'inside_valid_pixels': entry['inside']['valid_n'],
                'outside_valid_pixels': entry['outside']['valid_n'],
            })
        scenario_report.append({
            'scenario': number, 'ParkID_9_18_28_source': central_source,
            'ParkID_32_source': north_source, 'region_statistics': side_report,
            'inside_outside_correlation': correlation(z['inside'], z['outside']),
            'all_39_in_each_side': True, 'no_missing_values_or_zero_imputation': True,
        })
    source_hash_after = hashlib.sha256(sav_path.read_bytes()).hexdigest()
    assert source_hash_before == source_hash_after
    report = {
        'scope': 'Independent four-scenario NDVI data and sample-SD Z-standardization QC; no SEM estimated',
        'source_file': sav_path.name, 'source_sha256': source_hash_after,
        'original_sav_matches_prior_decoded_json': True,
        'original_rows': 39, 'original_columns_with_ParkID': 17,
        'original_observed_variable_count_excluding_ParkID': 16,
        'ndvi_column_mapping': {
            'inside': {'name': inside_name, 'zero_based_column': columns[inside_name], 'one_based_excel_column': columns[inside_name] + 1},
            'outside': {'name': outside_name, 'zero_based_column': columns[outside_name], 'one_based_excel_column': columns[outside_name] + 1},
        },
        'standardization_rule': 'For every scenario and each region separately, z=(park area mean - mean of 39 park area means)/sample SD using denominator 38',
        'all_39_z_values_recomputed_per_scenario': True,
        'unchanged_14_non_NDVI_observed_variables': True,
        'missing_value_rule': 'No missing means in scenario tables; pending sources are filled only from their exact identified candidate, not by 0 or by mixing imagery',
        'source_selection_by_old_SEM_agreement': False,
        'old_input_statistics': {side: {'mean': math.fsum(old[side])/39, 'sample_sd': stdev_sample(old[side]), 'min': min(old[side]), 'max': max(old[side])} for side in ('inside', 'outside')},
        'scenarios': scenario_report,
    }
    out = Path(__file__).resolve().parent
    with (out / 'qc_four_ndvi_values.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    (out / 'qc_four_ndvi_scenarios.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=True))


if __name__ == '__main__':
    build_qc()
