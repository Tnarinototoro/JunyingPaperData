"""Read-only independent binary and Excel QA for the four SEM inputs.

Scenario SAV case data are decoded directly as uncompressed IEEE doubles,
not through the same SAV reader used by the package writer. The original
numeric dictionary is compared byte-for-byte and long names are parsed.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
PACKAGE = ROOT / 'NDVI_四组合SEM敏感性分析_20261111'


def dictionary(data):
    assert data[:4] == b'$FL2'
    assert struct.unpack_from('<i', data, 64)[0] == 2
    position, variables, info = 176, [], []

    def integer():
        nonlocal position
        value = struct.unpack_from('<i', data, position)[0]
        position += 4
        return value

    while True:
        record = integer()
        if record == 2:
            vtype, haslabel, missing, print_format, write_format = [integer() for _ in range(5)]
            assert vtype == 0
            short = data[position:position + 8].rstrip(b' ')
            position += 8
            label = b''
            if haslabel:
                length = integer()
                label = data[position:position + length]
                position += length + (-length) % 4
            position += 8 * abs(missing)
            variables.append((short, label))
        elif record == 3:
            count = integer()
            for _ in range(count):
                position += 8
                length = data[position]
                position += 1 + length + (-(length + 1)) % 8
        elif record == 4:
            count = integer()
            position += 4 * count
        elif record == 6:
            count = integer()
            position += 80 * count
        elif record == 7:
            subtype, width, count = [integer() for _ in range(3)]
            payload = data[position:position + width * count]
            position += width * count
            info.append((subtype, payload))
        elif record == 999:
            assert integer() == 0
            break
        else:
            raise AssertionError(f'Unexpected dictionary record {record}')
    encoding = next((payload.rstrip(b'\0').decode('ascii')
                     for subtype, payload in info if subtype == 20), 'utf-8')
    long_names = {}
    for subtype, payload in info:
        if subtype == 13:
            for entry in payload.decode(encoding).rstrip('\0').split('\t'):
                if '=' in entry:
                    key, value = entry.split('=', 1)
                    long_names[key] = value
    names = [long_names.get(short.decode(encoding), short.decode(encoding)) for short, _ in variables]
    labels = [label.decode(encoding) for _, label in variables]
    return position, names, labels


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.reader(stream))


def xlsx_sheets(path):
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rid = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    result = {}
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if name.endswith('.xml') or name.endswith('.rels'):
                ET.fromstring(archive.read(name))
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {row.get('Id'): row.get('Target') for row in rels}
        for sheet in workbook.findall('s:sheets/s:sheet', ns):
            document = ET.fromstring(archive.read('xl/' + targets[sheet.get(rid)]))
            rows, types = [], []
            for row in document.findall('s:sheetData/s:row', ns):
                values, celltypes = [], []
                for cell in row.findall('s:c', ns):
                    letters = re.match(r'[A-Z]+', cell.get('r')).group()
                    index = 0
                    for letter in letters:
                        index = index * 26 + ord(letter) - 64
                    while len(values) < index:
                        values.append(None)
                        celltypes.append(None)
                    typ = cell.get('t', 'n')
                    if typ == 'inlineStr':
                        value = ''.join(node.text or '' for node in cell.findall('s:is/s:t', ns))
                    else:
                        assert typ == 'n'
                        value = float(cell.findtext('s:v', namespaces=ns))
                        assert math.isfinite(value)
                    values[index - 1] = value
                    celltypes[index - 1] = typ
                rows.append(values)
                types.append(celltypes)
            result[sheet.get('name')] = (rows, types)
    return result


def run():
    original_sav = (ROOT / '最终用于sem的匿名39✖16输入矩阵.sav').read_bytes()
    assert (PACKAGE / 'SEM输入/原输入_仅用于基线复现.sav').read_bytes() == original_sav
    offset, names, labels = dictionary(original_sav)
    original_matrix = json.loads((ROOT / '.paper15_work/sem_input_decoded.json').read_text(encoding='utf-8'))
    assert names == [variable['name'] for variable in original_matrix['variables']]
    assert labels == [variable['label'] for variable in original_matrix['variables']]
    assert names.index('Z内部NDVI平均値') == 15 and names.index('Z外部NDVI平均値') == 16
    qc = csv_rows(WORK / 'qc_four_ndvi_values.csv')
    qc_maps = {scenario: {} for scenario in range(1, 5)}
    for row in qc[1:]:
        fields = dict(zip(qc[0], row))
        qc_maps[int(fields['scenario'])][int(fields['ParkID'])] = fields
    ndvi_csv = csv_rows(PACKAGE / '四组合NDVI均值与Z值.csv')
    assert ndvi_csv == qc
    book = xlsx_sheets(PACKAGE / '四组合NDVI与SEM输入_待Amos复核.xlsx')
    assert len(book) == 8
    expected_names = ['説明', '四組合せ_試算状態', '四組合せ_NDVI値'] + [f'組合せ{i}_SEM入力' for i in range(1, 5)] + ['原モデル再現確認']
    assert list(book) == expected_names
    ndvi_sheet, ndvi_types = book['四組合せ_NDVI値']
    assert ndvi_sheet[0] == ndvi_csv[0] and len(ndvi_sheet) == 157
    for data, types, text in zip(ndvi_sheet[1:], ndvi_types[1:], ndvi_csv[1:]):
        for i, header in enumerate(ndvi_csv[0]):
            if header == 'source_raster':
                assert data[i] == text[i] and types[i] == 'inlineStr'
            else:
                assert data[i] == float(text[i]) and types[i] == 'n'
    scenario_reports = []
    for scenario in range(1, 5):
        path = PACKAGE / 'SEM输入' / f'组合{scenario}_SEM输入.sav'
        data = path.read_bytes()
        case_start, actual_names, actual_labels = dictionary(data)
        assert case_start == offset
        assert data[176:case_start] == original_sav[176:offset]
        assert actual_names == names and actual_labels == labels
        assert struct.unpack_from('<i', data, 68)[0] == 17
        assert struct.unpack_from('<i', data, 72)[0] == 0
        assert struct.unpack_from('<i', data, 76)[0] == 0
        assert struct.unpack_from('<i', data, 80)[0] == 39
        assert len(data) - case_start == 39 * 17 * 8
        cases = [list(struct.unpack_from('<17d', data, case_start + row * 17 * 8)) for row in range(39)]
        csv_data = csv_rows(PACKAGE / 'SEM输入' / f'组合{scenario}_SEM输入.csv')
        assert csv_data[0] == names and len(csv_data) == 40
        expected_rows = [[float(cell) for cell in row] for row in csv_data[1:]]
        assert cases == expected_rows
        excel_rows, excel_types = book[f'組合せ{scenario}_SEM入力']
        assert excel_rows[0] == names and excel_rows[1:] == cases
        assert all(types == ['n'] * 17 for types in excel_types[1:])
        for park_id, (row, original) in enumerate(zip(cases, original_matrix['rows']), 1):
            assert row[0] == park_id
            assert row[:15] == original[:15]
            fields = qc_maps[scenario][park_id]
            assert row[15] == float(fields['z_inside_area_mean'])
            assert row[16] == float(fields['z_outside_area_mean'])
        z_summary = {}
        for column in (15, 16):
            values = [row[column] for row in cases]
            mean = math.fsum(values) / 39
            sd = math.sqrt(math.fsum((value - mean) ** 2 for value in values) / 38)
            assert abs(mean) < 1e-14 and abs(sd - 1) < 1e-14
            z_summary[names[column]] = {'mean': mean, 'sample_sd': sd}
        scenario_reports.append({'scenario': scenario, 'sav': path.name, 'sha256': hashlib.sha256(data).hexdigest(),
                                 'uncompressed_case_data_directly_decoded': True, 'rows': 39, 'columns': 17,
                                 'dictionary_byte_identical_to_original': True, 'long_names_preserved': True,
                                 'exactly_matches_CSV_Excel_and_independent_NDVI_QC': True,
                                 'ParkID_and_14_non_NDVI_observed_columns_preserved': True,
                                 'all_78_Z_values_recomputed': True, 'z_statistics': z_summary})
    original_amw = (ROOT / 'amos模型.amw').read_bytes()
    assert (PACKAGE / '原模型_保持结构.amw').read_bytes() == original_amw
    states = csv_rows(PACKAGE / '四组合试算状态_非正式SEM结果.csv')
    state_sheet, state_types = book['四組合せ_試算状態']
    assert state_sheet[0] == states[0] and len(state_sheet) == len(states) == 5
    for excel, types, row in zip(state_sheet[1:], state_types[1:], states[1:]):
        assert excel[0] == float(row[0]) and types[0] == 'n'
        assert excel[1:] == row[1:]
        assert '未取得收敛且非负方差' in row[3] and 'e16' in row[4]
        assert row[5] == '0/3' and row[6].startswith('不可') and row[7] == '待复核'
    diagnostic = json.loads((PACKAGE / '复算记录与QC/四组合诊断迭代值_不能用于论文.json').read_text(encoding='utf-8'))
    assert diagnostic['valid_final_SEM_results'] is False
    assert diagnostic['coefficients_SE_p_and_fit_are_nonconverged_diagnostic_iterates'] is True
    assert diagnostic['do_not_rank_sources_using_these_values'] is True
    assert diagnostic['native_Amos_replication_pending'] is True
    assert len(diagnostic['models']) == 4
    for model in diagnostic['models']:
        assert model['termination'] == 'iteration_limit' and model['negative_variance_parameters']
    readme = (PACKAGE / '复核说明_先读.md').read_text(encoding='utf-8')
    for phrase in ('四组本次试算均未取得收敛且方差非负的解', '负估计', '不是可用于论文的SEM结果',
                   '不是Amos原生输出', '不能单独证明Amos必然失败', '没有选定主分析影像'):
        assert phrase in readme
    notes = dict(book['説明'][0][1:])
    assert '不能当正式SEM结果' in notes['新试算']
    assert '并非Amos原生输出' in notes['软件']
    baseline_rows, baseline_types = book['原モデル再現確認']
    for row, types in zip(baseline_rows[1:8], baseline_types[1:8]):
        assert types[1:3] == ['n', 'n']
    result = {'scope': 'Read-only final QA of four scenario SAV/CSV/XLSX and original AMW copy; not SEM estimation',
              'all_checks_pass': True, 'original_files_modified': False, 'package_files_modified': False,
              'xlsx_sheet_count': 8, 'scientific_numeric_cells_are_numeric': True,
              'scenario_data_checks': scenario_reports,
              'original_model_copy_byte_identical': True,
              'original_baseline_input_copy_byte_identical': True,
              'original_sav_sha256': hashlib.sha256(original_sav).hexdigest(),
              'original_amw_sha256': hashlib.sha256(original_amw).hexdigest(),
              'trial_status_and_documentation_label_nonconvergence_negative_variance_and_nonformal_results': True,
              'primary_imagery_selected': False, 'new_native_Amos_results_verified': False}
    (WORK / 'qa_delivery_four_inputs.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))


if __name__ == '__main__':
    run()
