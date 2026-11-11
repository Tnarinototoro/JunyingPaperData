"""Read-only checks of the four packaged SAV inputs; no SEM is estimated."""
import csv
import json
import math
from pathlib import Path

from read_numeric_sav import decode_numeric_matrix


def verify(root):
    original = decode_numeric_matrix(root / 'SEM输入/原输入_仅用于基线复现.sav')
    columns = {v['name']: i for i, v in enumerate(original['variables'])}
    inside = columns['Z内部NDVI平均値']
    outside = columns['Z外部NDVI平均値']
    with (root / '四组合NDVI均值与Z值.csv').open(encoding='utf-8-sig', newline='') as stream:
        ndvi = {(int(row['scenario']), int(row['ParkID'])): row for row in csv.DictReader(stream)}
    result = []
    for number in range(1, 5):
        data = decode_numeric_matrix(root / f'SEM输入/组合{number}_SEM输入.sav')
        assert data['case_count'] == 39 and data['variable_count'] == 17
        assert data['variables'] == original['variables']
        assert [int(row[columns['ParkID']]) for row in data['rows']] == list(range(1, 40))
        for i, (row, old) in enumerate(zip(data['rows'], original['rows']), 1):
            assert all(row[col] == old[col] for col in range(17) if col not in (inside, outside))
            expected = ndvi[(number, i)]
            assert row[inside] == float(expected['z_inside_area_mean'])
            assert row[outside] == float(expected['z_outside_area_mean'])
        for col in (inside, outside):
            values = [row[col] for row in data['rows']]
            mean = math.fsum(values) / 39
            sd = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / 38)
            assert abs(mean) < 1e-14 and abs(sd - 1) < 1e-14
        result.append({'scenario': number, 'cases': 39,
                       'observed_variables_excluding_ParkID': 16,
                       'original_14_other_variables_and_ParkID_unchanged': True,
                       'all_78_NDVI_Z_values_match_scenario_table': True,
                       'z_mean_zero_and_sample_SD_one': True})
    return {'all_four_inputs_pass': True, 'details': result,
            'SEM_estimated': False, 'primary_source_selected': False}


if __name__ == '__main__':
    print(json.dumps(verify(Path(__file__).resolve().parent.parent), ensure_ascii=True, indent=2))
