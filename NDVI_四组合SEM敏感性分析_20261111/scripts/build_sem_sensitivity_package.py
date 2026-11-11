"""Build four parallel NDVI SEM inputs and an honest diagnostic handoff.

Binary/data outputs are derived artifacts; original files are read-only.
No primary imagery selection and no paper/model-structure edits are made.
"""

import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
PACKAGE = ROOT / 'NDVI_四组合SEM敏感性分析_20261111'
sys.path.insert(0, str(ROOT / '.paper15_work'))
sys.path.insert(0, str(ROOT / 'NDVI_mean_work'))
from read_numeric_sav import decode_numeric_matrix
from build_review_package import xlsx


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        csv.writer(stream).writerows(rows)


def write_uncompressed_sav(path, original_bytes, matrix, rows, scenario):
    """Reuse the verified numeric dictionary, replace only the case data."""
    marker = struct.pack('<ii', 999, 0)
    assert original_bytes[:4] == b'$FL2'
    assert original_bytes.count(marker) == 1
    offset = original_bytes.index(marker) + len(marker)
    assert offset > 176
    header_and_dictionary = bytearray(original_bytes[:offset])
    assert struct.unpack_from('<i', header_and_dictionary, 64)[0] == 2
    assert struct.unpack_from('<i', header_and_dictionary, 68)[0] == 17
    struct.pack_into('<i', header_and_dictionary, 72, 0)  # No bytecode compression.
    struct.pack_into('<i', header_and_dictionary, 80, len(rows))
    product = b'Python standard-library SPSS-compatible scenario export'
    header_and_dictionary[4:64] = product.ljust(60, b' ')
    generated = datetime.now()
    header_and_dictionary[92:101] = generated.strftime('%d %b %y').encode('ascii')
    header_and_dictionary[101:109] = generated.strftime('%H:%M:%S').encode('ascii')
    label = f'NDVI source scenario {scenario}; regional pixel-mean Z; not primary selected'.encode('ascii')[:64]
    header_and_dictionary[109:173] = label.ljust(64, b' ')
    cases = b''.join(struct.pack('<' + 'd' * 17, *row) for row in rows)
    path.write_bytes(header_and_dictionary + cases)
    decoded = decode_numeric_matrix(path)
    assert decoded['rows'] == rows
    assert decoded['variables'] == matrix['variables']
    assert decoded['compression'] == 0 and decoded['case_count'] == 39
    return {'file': path.name, 'rows': 39, 'columns': 17,
            'saved_then_read_back_exact_match': True,
            'original_numeric_dictionary_preserved': True,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def build():
    PACKAGE.mkdir(exist_ok=True)
    inputs = PACKAGE / 'SEM输入'
    inputs.mkdir(exist_ok=True)
    evidence = PACKAGE / '复算记录与QC'
    evidence.mkdir(exist_ok=True)
    scripts = PACKAGE / 'scripts'
    scripts.mkdir(exist_ok=True)
    sav_source = ROOT / '最终用于sem的匿名39✖16输入矩阵.sav'
    model_source = ROOT / 'amos模型.amw'
    original_bytes = sav_source.read_bytes()
    hashes_before = {'sav': hashlib.sha256(original_bytes).hexdigest(),
                     'amw': hashlib.sha256(model_source.read_bytes()).hexdigest()}
    matrix = decode_numeric_matrix(sav_source)
    names = [variable['name'] for variable in matrix['variables']]
    assert names[0] == 'ParkID' and len(names) == 17
    inside_index = names.index('Z内部NDVI平均値')
    outside_index = names.index('Z外部NDVI平均値')
    assert (inside_index, outside_index) == (15, 16)
    with (WORK / 'qc_four_ndvi_values.csv').open(encoding='utf-8-sig', newline='') as stream:
        scenario_ndvi = list(csv.DictReader(stream))
    trials = json.loads((WORK / 'independent_ml_four_scenarios.json').read_text(encoding='utf-8'))
    assert len(trials['models']) == 4
    assert all(model['termination'] == 'iteration_limit' and
               model['negative_variance_parameters'] for model in trials['models'])

    notes = [
        ['項目 / Item', '説明 / Explanation'],
        ['用途', '四组合并列敏感性情境；未选主分析影像，未按接近旧SEM排序。'],
        ['输入', '每组39行、ParkID加16观测变量。只替换内部/外部两列NDVI Z，其余14列不变。'],
        ['区域均值', '原始有效NDVI像元之和/有效像元数；园内全域、园外既有约100m环带。'],
        ['Z标准化', '每组内部/外部分别按全部39园均值和样本SD（分母38）重算。'],
        ['基线', '独立ML已再现原Amos的25路径、22方差、7适合指标及3个R²的三位小数。'],
        ['新试算', '四组独立ML本次均未取得收敛且非负方差的解；状态表不能当正式SEM结果。'],
        ['软件', '本机无Amos。独立ML实现并非Amos原生输出；请用所附SAV正式复核。'],
        ['模型', '附原AMW逐字节副本；只需在Amos数据设置中指定某组SAV，不改结构/约束。'],
        ['来源', '按当前提供的NDVI标签栅格提取；观测时段/产品尚未核实，不用旧结果倒选来源。'],
        ['原文件', '原SAV、AMW及论文均未修改。'],
    ]
    states = [['组合', '9/18/28来源', '32来源', '独立试算状态', '负方差指标',
               '收敛起点数/总起点数', '当前迭代值可否用于论文', 'Amos原生复核']]
    for model in trials['models']:
        converged = sum(start['termination'] == 'gradient_converged' for start in model['starts'])
        states.append([model['scenario'], model['ParkID_9_18_28_source'], model['ParkID_32_source'],
                       '本次未取得收敛且非负方差的解', 'O06/公园外部绿化度/e16',
                       f'{converged}/{len(model["starts"])}', '不可；仅诊断迭代值', '待复核'])
    ndvi_fields = list(scenario_ndvi[0])
    ndvi_rows = [ndvi_fields]
    for row in scenario_ndvi:
        ndvi_rows.append([row[name] if name == 'source_raster' else
                          int(row[name]) if name in ('scenario', 'ParkID', 'inside_valid_pixels', 'outside_valid_pixels')
                          else float(row[name]) for name in ndvi_fields])
    sheets = [('説明', notes), ('四組合せ_試算状態', states), ('四組合せ_NDVI値', ndvi_rows)]
    file_qc = []
    for scenario_number in range(1, 5):
        chosen = [row for row in scenario_ndvi if int(row['scenario']) == scenario_number]
        assert [int(row['ParkID']) for row in chosen] == list(range(1, 40))
        rows = [row[:] for row in matrix['rows']]
        for row, ndvi in zip(rows, chosen):
            row[inside_index] = float(ndvi['z_inside_area_mean'])
            row[outside_index] = float(ndvi['z_outside_area_mean'])
        for row, old in zip(rows, matrix['rows']):
            assert all(row[i] == old[i] for i in range(17) if i not in (inside_index, outside_index))
        for col in (inside_index, outside_index):
            values = [row[col] for row in rows]
            mean = math.fsum(values) / 39
            sd = math.sqrt(math.fsum((v - mean) ** 2 for v in values) / 38)
            assert abs(mean) < 1e-14 and abs(sd - 1) < 1e-14
        sheets.append((f'組合せ{scenario_number}_SEM入力', [names] + rows))
        write_csv(inputs / f'组合{scenario_number}_SEM输入.csv', [names] + rows)
        file_qc.append(write_uncompressed_sav(inputs / f'组合{scenario_number}_SEM输入.sav',
                                              original_bytes, matrix, rows, scenario_number))
    baseline = json.loads((WORK / 'independent_ml_baseline_checks.json').read_text(encoding='utf-8'))
    reproduced = next(model for model in baseline['models'] if model['covariance_divisor'] == 39)
    spec = json.loads((WORK / 'sem_model_specification.json').read_text(encoding='utf-8'))
    checks = [['指标', '原Amos显示值', '独立复算值', '三位小数一致']]
    for key, expected in [('chi_square', 119.555), ('GFI', .749), ('AGFI', .659), ('CFI', .854),
                          ('TLI', .825), ('RMR', .063), ('RMSEA', .072)]:
        value = reproduced['fit_indices'][key]
        assert round(value, 3) == expected
        checks.append([key, expected, value, '是'])
    checks += [['25路径B/β', '原PDF/S2', '独立QA逐条比较', '全匹配'],
               ['22方差', '原PDF', '独立QA逐条比较', '全匹配'],
               ['3个内生R²', '原PDF', '独立QA逐条比较', '全匹配']]
    sheets.append(('原モデル再現確認', checks))
    book = PACKAGE / '四组合NDVI与SEM输入_待Amos复核.xlsx'
    xlsx(book, sheets)
    write_csv(PACKAGE / '四组合试算状态_非正式SEM结果.csv', states)
    write_csv(PACKAGE / '四组合NDVI均值与Z值.csv', ndvi_rows)
    shutil.copy2(model_source, PACKAGE / '原模型_保持结构.amw')
    shutil.copy2(sav_source, inputs / '原输入_仅用于基线复现.sav')
    assert (inputs / '原输入_仅用于基线复现.sav').read_bytes() == original_bytes
    assert (PACKAGE / '原模型_保持结构.amw').read_bytes() == model_source.read_bytes()
    for name in ('amw_structure_audit.json', 'sem_model_specification.json',
                 'independent_ml_baseline_checks.json', 'independent_ml_baseline_information.json',
                 'qa_baseline_reproduction.json', 'qc_four_ndvi_scenarios.json'):
        shutil.copy2(WORK / name, evidence / name)
    diagnostic_record = {**trials,
        'valid_final_SEM_results': False,
        'coefficients_SE_p_and_fit_are_nonconverged_diagnostic_iterates': True,
        'do_not_rank_sources_using_these_values': True,
        'native_Amos_replication_pending': True}
    (evidence / '四组合诊断迭代值_不能用于论文.json').write_text(
        json.dumps(diagnostic_record, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    for name in ('sem_covariance_ml.py', 'audit_amw_structure.py', 'qa_baseline_reproduction.py',
                 'qc_four_ndvi_scenarios.py', 'build_sem_sensitivity_package.py'):
        shutil.copy2(WORK / name, scripts / name)
    shutil.copy2(ROOT / '.paper15_work/read_numeric_sav.py', scripts / 'read_numeric_sav.py')
    summary = {'four_parallel_scenarios': True, 'primary_source_selected': False,
               'original_14_non_NDVI_indicators_and_ParkID_preserved': True,
               'all_39_z_values_recomputed_per_region_per_scenario': True,
               'saved_SAV_read_back_checks': file_qc,
               'baseline_reproduced_to_original_reported_precision': True,
               'new_native_Amos_results_generated': False,
               'new_independent_trials_converged_admissible': False,
               'original_sav_hash': hashes_before['sav'], 'original_amw_hash': hashes_before['amw']}
    assert hashlib.sha256(sav_source.read_bytes()).hexdigest() == hashes_before['sav']
    assert hashlib.sha256(model_source.read_bytes()).hexdigest() == hashes_before['amw']
    (evidence / '输入与交付QA.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    with zipfile.ZipFile(book) as workbook:
        assert workbook.testzip() is None
    print(json.dumps({'package': str(PACKAGE), 'workbook': str(book), **summary}, ensure_ascii=True))


if __name__ == '__main__':
    build()
