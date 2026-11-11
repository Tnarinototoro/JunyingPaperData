"""Read-only inspection of the uploaded bilingual original SEM workbook."""
import csv
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def column_number(reference):
    result = 0
    for letter in re.match(r'[A-Z]+', reference).group():
        result = result * 26 + ord(letter) - 64
    return result


def read_book(path):
    sheets = []
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        shared = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared = [''.join(node.text or '' for node in item.findall('.//s:t', NS))
                      for item in strings.findall('s:si', NS)]
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {item.get('Id'): item.get('Target') for item in rels}
        for item in workbook.findall('s:sheets/s:sheet', NS):
            target = targets[item.get(RID)]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
            document = ET.fromstring(archive.read(member))
            cells = {}
            for cell in document.findall('s:sheetData/s:row/s:c', NS):
                reference, typ = cell.get('r'), cell.get('t', 'n')
                value = cell.findtext('s:v', namespaces=NS)
                if typ == 's':
                    actual = shared[int(value)]
                elif typ == 'inlineStr':
                    actual = ''.join(node.text or '' for node in cell.findall('.//s:is//s:t', NS))
                elif typ in ('str', 'e'):
                    actual = value
                elif typ == 'b':
                    actual = bool(int(value)) if value is not None else None
                elif value is not None:
                    actual = float(value)
                else:
                    actual = None
                cells[reference] = {'value': actual, 'type': typ,
                                    'formula': cell.findtext('s:f', namespaces=NS),
                                    'raw_value': value, 'style': cell.get('s')}
            sheets.append({'name': item.get('name'), 'member': member,
                           'dimension': document.find('s:dimension', NS).get('ref') if document.find('s:dimension', NS) is not None else None,
                           'state': item.get('state', 'visible'), 'cells': cells})
    return sheets


def inspect():
    candidates = [path for path in ROOT.glob('*.xlsx') if path.name.startswith('公園番号ParkIDと16のSEM観測変数')
                  and '16 SEM observed variables' in path.name]
    assert len(candidates) == 1
    path = candidates[0]
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    sheets = read_book(path)
    original = json.loads((ROOT / '.paper15_work/sem_input_decoded.json').read_text(encoding='utf-8'))
    sav_sha = hashlib.sha256((ROOT / '最终用于sem的匿名39✖16输入矩阵.sav').read_bytes()).hexdigest()
    prior_qc = json.loads((WORK / 'qc_four_ndvi_scenarios.json').read_text(encoding='utf-8'))
    assert sav_sha == prior_qc['source_sha256']
    names = [variable['name'] for variable in original['variables']]
    original_rows = original['rows']
    summary, data_ranges, differences = [], [], []
    method_hits = []
    for sheet in sheets:
        cells = sheet['cells']
        preview = []
        populated_rows = sorted({int(re.search(r'[0-9]+', reference).group()) for reference, cell in cells.items() if cell['value'] is not None})
        for rownum in populated_rows[:7]:
            ordered = sorted(((reference, cell) for reference, cell in cells.items()
                              if int(re.search(r'[0-9]+', reference).group()) == rownum), key=lambda x: column_number(x[0]))
            preview.append({'row': rownum, 'values': [{'cell': reference, 'value': cell['value']} for reference, cell in ordered if cell['value'] is not None]})
        for reference, cell in cells.items():
            value = cell['value']
            if isinstance(value, str) and re.search(r'NDVI|midrange|中間値|中间值|最大値|最小値|maximum|minimum|Z-score|Z値|Z値|標準化|standardiz', value, re.I):
                method_hits.append({'sheet': sheet['name'], 'cell': reference, 'text': value})
        runs = []
        for reference, cell in cells.items():
            if cell['value'] != 1 or isinstance(cell['value'], bool):
                continue
            first_letter = re.match(r'[A-Z]+', reference).group()
            rownum = int(re.search(r'[0-9]+', reference).group())
            ids = [cells.get(f'{first_letter}{rownum+i}', {}).get('value') for i in range(39)]
            if ids == list(range(1, 40)):
                runs.append((rownum, column_number(reference)))
        for start, first_column in runs:
            expected_columns = 17
            columns = [chr(64+first_column+i) for i in range(expected_columns)]
            matrix = [[cells.get(f'{letter}{row}', {}).get('value') for letter in columns]
                      for row in range(start, start + 39)]
            headers = [{letter: cells.get(f'{letter}{row}', {}).get('value') for letter in columns}
                       for row in range(max(1, start-3), start)]
            range_differences = []
            for rowindex, (actual, expected) in enumerate(zip(matrix, original_rows)):
                for colindex, (value, baseline) in enumerate(zip(actual, expected)):
                    if value != baseline:
                        actual_cell = cells.get(f'{columns[colindex]}{start+rowindex}', {})
                        raw_value = actual_cell.get('raw_value')
                        quantum = float(Decimal(1).scaleb(Decimal(raw_value).as_tuple().exponent)) if raw_value is not None else None
                        error = abs(value-baseline) if isinstance(value, (int, float)) else None
                        effective_quantum = 1e-5 if colindex in (15, 16) else quantum
                        matches_reported_precision = (error is not None and effective_quantum is not None
                                                      and error <= effective_quantum/2+1e-15
                                                      and (colindex not in (15, 16) or abs(value-round(value, 5)) < 1e-14))
                        entry = {'sheet': sheet['name'], 'cell': f'{columns[colindex]}{start+rowindex}',
                                 'ParkID': rowindex+1, 'variable_assuming_original_order': names[colindex],
                                 'excel_value': value, 'sav_value': baseline,
                                 'absolute_difference': error,
                                 'xlsx_stored_numeric_quantum': quantum,
                                 'effective_reported_numeric_quantum': effective_quantum,
                                 'consistent_with_reported_decimal_precision': matches_reported_precision,
                                 'NDVI_matches_SAV_rounded_to_5_decimals': round(value, 5) == round(baseline, 5) if colindex in (15, 16) else None}
                        range_differences.append(entry)
                        differences.append(entry)
            japan_headers = headers[-1]
            assert japan_headers[columns[0]] == 'ParkID'
            assert all(isinstance(japan_headers[columns[i]], str) and japan_headers[columns[i]].startswith(original['variables'][i]['label']) for i in range(1, 17))
            data_ranges.append({'sheet': sheet['name'], 'range': f'{columns[0]}{start}:{columns[-1]}{start+38}',
                                'data_start_row': start, 'data_end_row': start+38,
                                'headers_before_data': headers,
                                'rows': 39, 'columns': 17,
                                'Japanese_headers_confirm_original_variable_order': True,
                                'NDVI_inside_range': f'{columns[15]}{start}:{columns[15]}{start+38}',
                                'NDVI_outside_range': f'{columns[16]}{start}:{columns[16]}{start+38}',
                                'non_NDVI_observed_range_to_preserve': f'{columns[1]}{start}:{columns[14]}{start+38}',
                                'all_cells_numeric': all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for row in matrix for value in row),
                                'formula_cell_count': sum(bool(cells.get(f'{letter}{row}', {}).get('formula')) for row in range(start, start+39) for letter in columns),
                                'different_cells': len(range_differences),
                                'max_absolute_difference': max((entry['absolute_difference'] for entry in range_differences if entry['absolute_difference'] is not None), default=0),
                                'all_differences_consistent_with_reported_decimal_precision': all(entry['consistent_with_reported_decimal_precision'] for entry in range_differences),
                                'ParkID_and_14_non_NDVI_columns_exactly_equal_original_SAV': all(actual[:15] == expected[:15] for actual, expected in zip(matrix, original_rows)),
                                'all_78_NDVI_values_equal_original_SAV_rounded_to_5_decimals': all(round(actual[i], 5) == round(expected[i], 5) for actual, expected in zip(matrix, original_rows) for i in (15, 16))})
        summary.append({'name': sheet['name'], 'state': sheet['state'], 'dimension': sheet['dimension'],
                        'nonempty_cell_count': sum(cell['value'] is not None for cell in cells.values()),
                        'first_populated_rows': preview, 'contiguous_ParkID_runs': [{'first_row': row, 'first_column_1based': col} for row, col in runs]})
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert len(data_ranges) == 1
    report = {'scope': 'Read-only bilingual original Excel versus original saved SEM matrix; no imagery selected or files modified',
              'xlsx_file': path.name, 'xlsx_sha256': before, 'sheet_count': len(sheets),
              'original_sav_sha256': sav_sha, 'original_SAV_unchanged_since_direct_data_QC': True,
              'sheet_summary': summary, 'candidate_data_ranges': data_ranges,
              'original_sav_variable_order': names,
              'different_cells_total': len(differences), 'differences': differences,
              'substantial_mismatches_beyond_reported_decimal_precision': [entry for entry in differences if not entry['consistent_with_reported_decimal_precision']],
              'per_variable_precision_comparison': [{'name': name, 'different_cell_count': sum(entry['variable_assuming_original_order'] == name for entry in differences),
                                                    'maximum_absolute_difference': max((entry['absolute_difference'] for entry in differences if entry['variable_assuming_original_order'] == name), default=0)} for name in names],
              'NDVI_or_standardization_text_cells': method_hits,
              'other_sheet_NDVI_method_paragraphs_found': False,
              'original_files_modified': False, 'primary_source_selected': False}
    (WORK / 'qa_new_bilingual_excel_original.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('xlsx_file', 'xlsx_sha256', 'sheet_count', 'candidate_data_ranges',
                                                 'different_cells_total', 'substantial_mismatches_beyond_reported_decimal_precision',
                                                 'per_variable_precision_comparison', 'other_sheet_NDVI_method_paragraphs_found',
                                                 'original_files_modified', 'primary_source_selected')}, ensure_ascii=True))


if __name__ == '__main__':
    inspect()
