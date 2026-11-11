"""Build confidential GIS review files; never fills unresolved imagery choices."""

from __future__ import annotations
import csv
import datetime
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile

from compute_regional_means import Raster, calculate, load_geometry, write_csv
from audit_vectors_std import ring_stats


def write_tiff(path, rows, raster, window, is_mask=False):
    height, width = len(rows), len(rows[0])
    c0, r0 = window[:2]
    bpp = 1 if is_mask else 4
    sample_type = 1 if is_mask else 3
    nodata = '0' if is_mask else raster.tags.get(42113, '-3.4028234663852886e+38')
    descriptions = 'ROI codes: 0=outside ROI, 1=park interior, 2=exterior ring' if is_mask else 'Unresampled source NDVI pixel crop for confidential regional-mean verification'
    # TIFF values: (tag, TIFF type, count, packed bytes).
    entries = []
    def add(tag, typ, vals):
        if typ == 2:
            raw = vals.encode('ascii') + b'\0'
            count = len(raw)
        else:
            fmt = {3: 'H', 4: 'I', 12: 'd'}[typ]
            count, raw = len(vals), struct.pack('<' + fmt * len(vals), *vals)
        entries.append((tag, typ, count, raw))
    for tag, val in [(256, width), (257, height), (278, 1)]:
        add(tag, 4, [val])
    for tag, val in [(258, bpp * 8), (259, 1), (262, 1), (277, 1), (284, 1), (339, sample_type)]:
        add(tag, 3, [val])
    add(270, 2, descriptions)
    add(305, 2, 'Python standard-library review export; not acquisition metadata')
    add(273, 4, [0] * height)
    add(279, 4, [width * bpp] * height)
    add(33550, 12, [raster.dx, raster.dy, 0.0])
    add(33922, 12, [0.0, 0.0, 0.0, raster.x0 + c0 * raster.dx, raster.y0 - r0 * raster.dy, 0.0])
    add(34735, 3, [1, 1, 0, 4, 1024, 0, 1, 1, 1025, 0, 1, 1,
                   3072, 0, 1, raster.epsg, 3076, 0, 1, 9001])
    add(42113, 2, nodata)
    entries.sort()
    extra_start = 8 + 2 + len(entries) * 12 + 4
    positions = {}
    cursor = extra_start
    for tag, typ, count, raw in entries:
        if len(raw) > 4:
            cursor = (cursor + 7) // 8 * 8
            positions[tag] = cursor
            cursor += len(raw)
    data_start = (cursor + 7) // 8 * 8
    entries = [(tag, typ, count, struct.pack('<' + 'I' * height,
               *(data_start + i * width * bpp for i in range(height))) if tag == 273 else raw)
               for tag, typ, count, raw in entries]
    header = bytearray(data_start)
    header[:8] = b'II' + struct.pack('<HI', 42, 8)
    struct.pack_into('<H', header, 8, len(entries))
    for i, (tag, typ, count, raw) in enumerate(entries):
        pos = 10 + 12 * i
        struct.pack_into('<HHI', header, pos, tag, typ, count)
        if len(raw) <= 4:
            header[pos + 8:pos + 12] = raw.ljust(4, b'\0')
        else:
            struct.pack_into('<I', header, pos + 8, positions[tag])
            header[positions[tag]:positions[tag] + len(raw)] = raw
    with path.open('wb') as stream:
        stream.write(header)
        for row in rows:
            stream.write(bytes(row) if is_mask else struct.pack('<' + 'f' * width, *row))


def write_shapefile(path, geometry_rows, attr_rows, prj):
    all_points = [p for rings in geometry_rows for ring in rings for p in ring]
    bbox = (min(p[0] for p in all_points), min(p[1] for p in all_points),
            max(p[0] for p in all_points), max(p[1] for p in all_points))
    contents = []
    for rings in geometry_rows:
        flat = [p for ring in rings for p in ring]
        box = (min(p[0] for p in flat), min(p[1] for p in flat), max(p[0] for p in flat), max(p[1] for p in flat))
        offsets, current = [], 0
        for ring in rings:
            offsets.append(current)
            current += len(ring)
        content = struct.pack('<i4d2i', 5, *box, len(rings), len(flat))
        content += struct.pack('<' + 'i' * len(offsets), *offsets)
        content += struct.pack('<' + 'd' * (len(flat) * 2), *(v for p in flat for v in p))
        contents.append(content)
    def header(byte_length):
        return struct.pack('>7i', 9994, 0, 0, 0, 0, 0, byte_length // 2) + struct.pack('<2i8d', 1000, 5, *bbox, 0, 0, 0, 0)
    shp_size = 100 + sum(8 + len(c) for c in contents)
    with path.open('wb') as shp, path.with_suffix('.shx').open('wb') as shx:
        shp.write(header(shp_size))
        shx.write(header(100 + 8 * len(contents)))
        offset = 100
        for i, content in enumerate(contents, 1):
            shp.write(struct.pack('>2i', i, len(content) // 2))
            shp.write(content)
            shx.write(struct.pack('>2i', offset // 2, len(content) // 2))
            offset += 8 + len(content)
    fields = [('ParkID', 'N', 3, 0), ('MeanIn', 'N', 20, 15), ('MeanOut', 'N', 20, 15),
              ('NIn', 'N', 7, 0), ('NOut', 'N', 7, 0), ('Status', 'C', 20, 0)]
    hlen, rlen = 32 + 32 * len(fields) + 1, 1 + sum(f[2] for f in fields)
    today = datetime.date.today()
    dbf = bytearray(32)
    dbf[:4] = bytes([3, today.year - 1900, today.month, today.day])
    struct.pack_into('<IHH', dbf, 4, len(attr_rows), hlen, rlen)
    for name, typ, width, decimals in fields:
        desc = bytearray(32)
        desc[:len(name)] = name.encode('ascii')
        desc[11], desc[16], desc[17] = ord(typ), width, decimals
        dbf.extend(desc)
    dbf.append(13)
    for row in attr_rows:
        dbf.append(32)
        for name, typ, width, decimals in fields:
            value = row.get(name)
            if value is None:
                text = ''
            elif typ == 'N':
                text = f'{value:.{decimals}f}' if decimals else str(int(value))
            else:
                text = str(value)
            if len(text.encode('ascii')) > width:
                raise ValueError('DBF field overflow')
            dbf.extend((text.rjust(width) if typ == 'N' else text.ljust(width)).encode('ascii'))
    dbf.append(26)
    path.with_suffix('.dbf').write_bytes(dbf)
    path.with_suffix('.prj').write_text(prj, encoding='ascii')
    path.with_suffix('.cpg').write_text('UTF-8', encoding='ascii')


def column_name(index):
    result = ''
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def xlsx(path, sheets):
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    ET.register_namespace('', ns)
    def q(tag):
        return '{' + ns + '}' + tag
    types = ET.Element('Types', xmlns='http://schemas.openxmlformats.org/package/2006/content-types')
    ET.SubElement(types, 'Default', Extension='rels', ContentType='application/vnd.openxmlformats-package.relationships+xml')
    ET.SubElement(types, 'Default', Extension='xml', ContentType='application/xml')
    ET.SubElement(types, 'Override', PartName='/xl/workbook.xml', ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml')
    workbook = ET.Element(q('workbook'), {'xmlns:r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'})
    sheet_nodes = ET.SubElement(workbook, q('sheets'))
    relns = 'http://schemas.openxmlformats.org/package/2006/relationships'
    rootrels, wb_rels = ET.Element('Relationships', xmlns=relns), ET.Element('Relationships', xmlns=relns)
    ET.SubElement(rootrels, 'Relationship', Id='rId1', Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument', Target='xl/workbook.xml')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for i, (name, rows) in enumerate(sheets, 1):
            ET.SubElement(sheet_nodes, q('sheet'), {'name': name, 'sheetId': str(i), 'r:id': f'rId{i}'})
            ET.SubElement(wb_rels, 'Relationship', Id=f'rId{i}', Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet', Target=f'worksheets/sheet{i}.xml')
            ET.SubElement(types, 'Override', PartName=f'/xl/worksheets/sheet{i}.xml', ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml')
            worksheet = ET.Element(q('worksheet'))
            views = ET.SubElement(worksheet, q('sheetViews'))
            view = ET.SubElement(views, q('sheetView'), workbookViewId='0')
            ET.SubElement(view, q('pane'), ySplit='1', topLeftCell='A2', activePane='bottomLeft', state='frozen')
            sheet_data = ET.SubElement(worksheet, q('sheetData'))
            for ri, values in enumerate(rows, 1):
                row_node = ET.SubElement(sheet_data, q('row'), r=str(ri))
                for ci, value in enumerate(values, 1):
                    if value is None:
                        continue
                    cell = ET.SubElement(row_node, q('c'), r=column_name(ci) + str(ri))
                    if isinstance(value, (int, float)) and not isinstance(value, bool):
                        if not math.isfinite(value):
                            raise ValueError('Nonfinite value cannot be exported as an Excel numeric cell')
                        ET.SubElement(cell, q('v')).text = repr(value)
                    else:
                        cell.set('t', 'inlineStr')
                        ET.SubElement(ET.SubElement(cell, q('is')), q('t')).text = str(value)
            if rows:
                ET.SubElement(worksheet, q('autoFilter'), ref=f'A1:{column_name(len(rows[0]))}{len(rows)}')
            archive.writestr(f'xl/worksheets/sheet{i}.xml', ET.tostring(worksheet, encoding='utf-8', xml_declaration=True))
        archive.writestr('[Content_Types].xml', ET.tostring(types, encoding='utf-8', xml_declaration=True))
        archive.writestr('_rels/.rels', ET.tostring(rootrels, encoding='utf-8', xml_declaration=True))
        archive.writestr('xl/workbook.xml', ET.tostring(workbook, encoding='utf-8', xml_declaration=True))
        archive.writestr('xl/_rels/workbook.xml.rels', ET.tostring(wb_rels, encoding='utf-8', xml_declaration=True))


def build(root, out):
    work, inputs = root / 'NDVI_mean_work', root / 'NDVI'
    scan = json.loads((work / 'regional_mean_source_scan.json').read_text(encoding='utf-8'))
    pairs, prj = load_geometry(inputs)
    out.mkdir(exist_ok=True)
    gis = out / 'GIS'
    crops = gis / 'rasters'
    crops.mkdir(parents=True, exist_ok=True)
    scripts = out / 'scripts'
    scripts.mkdir(exist_ok=True)
    # Z-scores deliberately remain blank until all 39 source selections are confirmed.
    numeric, overlaps, attrs, extraction, points = [], [], [], [], []
    readers = {}
    try:
        for pair, row in zip(pairs, scan['parks']):
            assert pair['ParkID'] == row['ParkID']
            chosen = row['selected']
            status = 'CONFIRMED' if chosen else 'CHOOSE_SOURCE'
            numeric.append({'ParkID': row['ParkID'], 'ndvi_inside_area_mean': chosen['inside']['mean'] if chosen else None,
                            'ndvi_outside_100m_ring_area_mean': chosen['outside']['mean'] if chosen else None,
                            'z_inside_area_mean': None, 'z_outside_area_mean': None,
                            'inside_valid_pixels': chosen['inside']['valid_n'] if chosen else None,
                            'outside_valid_pixels': chosen['outside']['valid_n'] if chosen else None,
                            'inside_nodata_pixels': chosen['inside']['nodata_n'] if chosen else None,
                            'outside_nodata_pixels': chosen['outside']['nodata_n'] if chosen else None,
                            'status': status})
            attrs.append({'ParkID': row['ParkID'], 'MeanIn': numeric[-1]['ndvi_inside_area_mean'],
                          'MeanOut': numeric[-1]['ndvi_outside_100m_ring_area_mean'],
                          'NIn': numeric[-1]['inside_valid_pixels'], 'NOut': numeric[-1]['outside_valid_pixels'], 'Status': status})
            options = [chosen] if chosen else [c for c in row['candidates'] if c['full_extent'] and all(c[s]['valid_n'] for s in ('inside', 'outside'))]
            for option_index, option in enumerate(options, 1):
                if not chosen:
                    overlaps.append({'ParkID': row['ParkID'], 'source_option': option_index,
                                     'source_raster': option['source_raster'],
                                     'inside_mean': option['inside']['mean'], 'outside_mean': option['outside']['mean'],
                                     'inside_valid_pixels': option['inside']['valid_n'], 'outside_valid_pixels': option['outside']['valid_n']})
                name = option['source_raster']
                if name not in readers:
                    readers[name] = Raster(inputs / name)
                raster = readers[name]
                detail = calculate(row['ParkID'], pair['park'], pair['buffer'], raster, keep_pixels=True)
                for side in ('inside', 'outside'):
                    assert detail[side] == option[side], 'Crop replay changed regional statistics'
                label = f'P{row["ParkID"]:02d}' + ('' if chosen else f'_option{option_index}')
                ndvi_path, mask_path = crops / f'{label}_NDVI.tif', crops / f'{label}_zones.tif'
                write_tiff(ndvi_path, detail['private_crop'], raster, detail['private_window'])
                write_tiff(mask_path, detail['private_mask'], raster, detail['private_window'], is_mask=True)
                points.extend((pid, label, zone, source, rr, cc, value) for pid, zone, source, rr, cc, value in detail['private_pixels'])
                extraction.append({'ParkID': row['ParkID'], 'label': label, 'status': status,
                                   'source_raster': name, 'source_epsg': raster.epsg,
                                   'source_window': detail['private_window'],
                                   'ndvi_crop': str(ndvi_path.relative_to(out)).replace('\\', '/'),
                                   'zone_mask': str(mask_path.relative_to(out)).replace('\\', '/'),
                                   'inside': detail['inside'], 'outside': detail['outside'],
                                   'pixel_signature_sha256': detail['pixel_signature_sha256']})
    finally:
        for raster in readers.values():
            raster.close()
    fields = list(numeric[0])
    write_csv(out / 'NDVI_area_means_39_review.csv', numeric, fields)
    write_csv(out / 'overlap_sources_4parks.csv', overlaps, list(overlaps[0]))
    with (gis / 'valid_pixels.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['ParkID', 'source_option_label', 'zone', 'source_raster', 'source_row', 'source_col', 'ndvi'])
        writer.writerows(points)
    park_geometries, ring_geometries, buffer_geometries = [], [], []
    def orient(ring, clockwise):
        positive = ring_stats(ring)['signed_area'] > 0
        return list(reversed(ring)) if positive == clockwise else ring
    for pair in pairs:
        park_geometries.append([orient(pair['park'], True)])
        ring_geometries.append([orient(pair['buffer'], True), orient(pair['park'], False)])
        buffer_geometries.append([orient(pair['buffer'], True)])
    write_shapefile(gis / 'park_boundaries.shp', park_geometries, attrs, prj)
    write_shapefile(gis / 'outer_100m_rings.shp', ring_geometries, attrs, prj)
    write_shapefile(gis / 'full_100m_buffers.shp', buffer_geometries, attrs, prj)
    (gis / 'pixel_extractions.json').write_text(json.dumps(extraction, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    notes = [
        ['項目 / Item', '説明 / Explanation'],
        ['用途', '内部核对版：35公园已选定当前可用栅格，4公园需确认重叠影像。不是最终39公园SEM输入。'],
        ['内部', '提供的公园边界全域；不是点周围100m，也不是仅有植被的区域。'],
        ['外部', '提供的100m缓冲部分，扣除对应公园内部；按包含关系匹配，不按part顺序。'],
        ['范围单位', '原边界/缓冲的Asia North Albers投影平面米；保留原空间范围，非精确测地100m。'],
        ['平均公式', '范围内所有有效像元之和 / 有效像元数；不是最大最小值的中间值。'],
        ['像元边界规则', '原30m格网的像元中心落入多边形；无重采样。边界相交的面积权重未另作估计。'],
        ['full_extent字段', '全部纳入选区的像元中心均位于栅格范围内；不表示连续几何的每一点均被覆盖，也不表示无NoData。'],
        ['NoData', 'NoData和非有限值不计入；有效0及负NDVI保留，不作0填补。'],
        ['Z值', '本版全部留空；4园影像选择确定后，内部、外部各39个均值分别用样本标准差标准化。'],
        ['NDBI', '不是NDVI；未用于本次区域均值或替代缺值。'],
        ['来源核对', '按所提供NDVI标签文件的覆盖与有效像元条件选取；CONFIRMED不表示已完整核实旧测量来源、卫星产品或拍摄/合成时段。'],
        ['修改时间', '2026年11月文件修改/上传时间不等于影像拍摄时间。'],
        ['SEM', '本次未重跑Amos，未改原SAV、原模型或原论文。'],
        ['位置保护', 'GIS含位置及边界，仅供作者/教授内部核对，不作为匿名公开补充资料。'],
    ]
    all_candidates = []
    with (work / 'regional_mean_candidates.csv').open(encoding='utf-8-sig', newline='') as stream:
        all_candidates = list(csv.reader(stream))
    def numeric_cell(value):
        if value == '':
            return None
        try:
            result = float(value)
            return int(result) if result.is_integer() and '.' not in value and 'e' not in value.lower() else result
        except ValueError:
            return value
    all_candidates = all_candidates[:1] + [[numeric_cell(v) for v in row] for row in all_candidates[1:]]
    summary_rows = [fields] + [[row.get(f) for f in fields] for row in numeric]
    overlap_fields = list(overlaps[0])
    sheets = [('NDVI地域平均_39公園', summary_rows),
              ('重複影像4公園', [overlap_fields] + [[r.get(f) for f in overlap_fields] for r in overlaps]),
              ('全候補の統計', all_candidates), ('算出方法と確認事項', notes)]
    workbook_path = out / 'NDVI区域平均值_39公园_待4园影像确认.xlsx'
    xlsx(workbook_path, sheets)
    for name in ['audit_rasters_stdlib.py', 'audit_vectors_std.py', 'geo_math_stdlib.py',
                 'compute_regional_means.py', 'build_review_package.py']:
        shutil.copy2(work / name, scripts / name)
    for name in ['audit_rasters_stdlib.json', 'audit_rasters_stdlib.tsv', 'audit_vector_topology.json',
                 'regional_mean_source_scan.json', 'regional_mean_candidates.csv']:
        shutil.copy2(work / name, out / name)
    manifest = []
    for path in sorted(inputs.glob('*')):
        if path.name.startswith('NDVI_') and path.suffix.lower() == '.tif' or path.name.startswith('parks_metric.') or path.name.startswith('100m_buffer.'):
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(block)
            manifest.append({'source_file': path.name, 'bytes': path.stat().st_size, 'sha256': digest.hexdigest()})
    (out / 'source_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'output_folder': str(out), 'confirmed_parks': sum(r['status'] == 'CONFIRMED' for r in numeric),
                      'pending_ParkID': [r['ParkID'] for r in numeric if r['status'] != 'CONFIRMED'],
                      'z_scores_generated': False, 'pixel_extraction_options': len(extraction),
                      'valid_pixel_rows': len(points), 'xlsx': str(workbook_path)}, ensure_ascii=True))


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    build(root, root / 'NDVI_区域平均值_20261111_核对版')
