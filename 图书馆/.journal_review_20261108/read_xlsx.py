import argparse
from collections import Counter
import json
from pathlib import Path
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

sys.stdout.reconfigure(encoding='utf-8')

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
PKG = {'p': 'http://schemas.openxmlformats.org/package/2006/relationships'}

def all_text(element):
    return ''.join(element.itertext()) if element is not None else ''

def load_workbook(path):
    with ZipFile(path) as z:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared = [''.join(si.itertext()) for si in root.findall('s:si', NS)]
        relationships = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        targets = {e.get('Id'): e.get('Target') for e in relationships}
        workbook = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = []
        for sheet in workbook.findall('s:sheets/s:sheet', NS):
            target = targets[sheet.get('{'+NS['r']+'}id')]
            sheetpath = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            root = ET.fromstring(z.read(sheetpath))
            rows = []
            for row in root.findall('s:sheetData/s:row', NS):
                values = []
                for cell in row.findall('s:c', NS):
                    v = cell.find('s:v', NS)
                    value = v.text or '' if v is not None else ''
                    kind = cell.get('t', '')
                    if kind == 's':
                        value = shared[int(value)] if value else ''
                    elif kind == 'inlineStr':
                        value = ''.join(cell.find('s:is', NS).itertext())
                    formula = cell.find('s:f', NS)
                    if formula is not None:
                        value += ' [formula='+all_text(formula)+']'
                    if value:
                        values.append((cell.get('r'), value))
                if values:
                    rows.append({'row': int(row.get('r')), 'cells': values})
            hyperlink_targets = {}
            relpath = posixpath.dirname(sheetpath)+'/_rels/'+posixpath.basename(sheetpath)+'.rels'
            if relpath in z.namelist():
                hyperlink_targets = {e.get('Id'): e.get('Target') for e in ET.fromstring(z.read(relpath))}
            hyperlinks = []
            for h in root.findall('s:hyperlinks/s:hyperlink', NS):
                link = h.get('location') or hyperlink_targets.get(h.get('{'+NS['r']+'}id'), '')
                hyperlinks.append({'ref':h.get('ref'),'target':link})
            sheets.append({'name':sheet.get('name'), 'path':sheetpath,
                'dimension':root.find('s:dimension', NS).get('ref') if root.find('s:dimension', NS) is not None else '',
                'rows':rows, 'hyperlinks':hyperlinks})
        return sheets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--sheet', type=int)
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=0)
    parser.add_argument('--find')
    parser.add_argument('--compact', action='store_true')
    parser.add_argument('--dictionary', action='store_true')
    args = parser.parse_args()
    sheets = load_workbook(Path(args.file))
    if args.sheet is None and not args.find:
        for i, s in enumerate(sheets):
            print(json.dumps({'sheet':i, 'name':s['name'], 'dimension':s['dimension'],
                'nonempty_rows':len(s['rows']), 'last_row':s['rows'][-1]['row'] if s['rows'] else 0,
                'first_rows':s['rows'][:5], 'hyperlinks':s['hyperlinks'][:5]},ensure_ascii=False))
        return
    for i, s in enumerate(sheets):
        if args.sheet is not None and i != args.sheet:
            continue
        print('SHEET '+str(i)+' '+s['name'])
        frequencies = Counter(value for row in s['rows'] for ref,value in row['cells'])
        compact_values = sorted(value for value,count in frequencies.items() if count >= 20 and len(value) > 4)
        dictionary = {value:'@'+str(n+1) for n,value in enumerate(compact_values)}
        if args.compact and (args.start == 1 or args.dictionary):
            print('Compact format: row number followed by columns A..G in order; empty fields preserved. @codes below expand to EXACT original strings.')
            print('SD(B) expands to http://www.sciencedirect.com/science/journal/ followed by column B ISSN with hyphens removed.')
            for value,code in dictionary.items():
                print(code+'='+value)
        if args.dictionary:
            continue
        for row in s['rows']:
            if row['row'] < args.start or (args.end and row['row'] > args.end):
                continue
            if args.find and not any(re.search(args.find,value,re.I) for ref,value in row['cells']):
                continue
            if args.compact:
                by_col = {re.sub(r'\d+$','',ref):value for ref,value in row['cells']}
                last_col = max(ord(col)-ord('A') for col in by_col if len(col)==1)
                values = []
                for n in range(last_col+1):
                    col = chr(ord('A')+n)
                    value = by_col.get(col,'')
                    if col == 'G' and value == 'http://www.sciencedirect.com/science/journal/'+by_col.get('B','').replace('-',''):
                        value = 'SD(B)'
                    else:
                        value = dictionary.get(value,value)
                    values.append(value.replace('\n',' / ').replace('\r',''))
                print(str(row['row'])+': '+'|'.join(values))
            else:
                print(str(row['row'])+': '+' | '.join(ref+'='+value.replace('\n',' / ').replace('\r','') for ref,value in row['cells']))
        if args.start == 1 and not args.end and not args.find:
            for h in s['hyperlinks']:
                print('HYPERLINK '+h['ref']+' '+h['target'])

if __name__ == '__main__':
    main()
