"""Build an anonymous ID-confirmation handoff, not a new SEM input."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
AUDIT = WORK / 'old_extrema_source_audit'
OUT = ROOT / 'NDVI_旧极值追溯与公园编号核对_20261111'
sys.path.insert(0, str(ROOT / 'NDVI_mean_work'))
from build_review_package import xlsx


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    OUT.mkdir(exist_ok=True)
    evidence = OUT / '匿名核对记录'
    evidence.mkdir(exist_ok=True)
    scripts = OUT / 'scripts'
    scripts.mkdir(exist_ok=True)
    with (AUDIT / 'independent_cross_id_mapping.tsv').open(encoding='utf-8', newline='') as stream:
        mapping = list(csv.DictReader(stream, delimiter='\t'))
    assert [int(row['old_s1_code'][1:]) for row in mapping] == list(range(1, 40))
    scan = json.loads((ROOT / 'NDVI_mean_work/regional_mean_source_scan.json').read_text(encoding='utf-8'))
    candidates = {(row['ParkID'], candidate['source_raster']): candidate
                  for row in scan['parks'] for candidate in row['candidates']}
    header = ['原SEM_ParkID', '旧S1代码', '极值指纹候选GIS记录号（地址表NO）',
              '候选图层标签', '旧外部极值匹配定义', '作者确认GIS记录号（地址表NO）', '作者备注', '状态']
    confirmation = [header]
    draft_means = [['原SEM_ParkID（身份待确认）', '候选GIS记录号', 'NDVI源标签',
                    '公园内部全域像元均值', '公园外100m环带像元均值',
                    '内部有效像元数', '环带有效像元数', '身份确认状态']]
    target_summary = [['旧S1公园编号', '数字指纹候选GIS记录号', '候选NDVI标签', '结果/解释']]
    unique_count = 0
    for row in mapping:
        old_id = int(row['old_s1_code'][1:])
        if row['classification'] == 'unique_geometry':
            unique_count += 1
            geometry_id = int(row['matched_current_geometry_ids'])
            tokens = row['candidate_sources_and_definitions'].split('|')
            sources = sorted({token.split(':')[1] for token in tokens})
            definitions = {token.split(':')[2] for token in tokens}
            assert len(sources) == 1
            source = sources[0]
            description = ('仅完整外扩面（含园内）'
                           if definitions == {'park_plus_full_expanded_buffer'}
                           else '环带与完整外扩面均吻合')
            status = '唯一数值指纹；真实公园身份待作者核对'
            candidate = candidates[(geometry_id, source)]
            draft_means.append([old_id, geometry_id, source, candidate['inside']['mean'], candidate['outside']['mean'],
                                candidate['inside']['valid_n'], candidate['outside']['valid_n'], '待作者核对；非最终SEM数据'])
        else:
            assert row['classification'] == 'no_match'
            geometry_id, source, description = None, '', '全部候选四极值及内部二极值均无显示精度匹配'
            status = '需原公园编号对应记录；不得猜测'
        confirmation.append([old_id, row['old_s1_code'], geometry_id, source, description, None, None, status])
        if old_id in (9, 18, 28, 32):
            target_summary.append([old_id, geometry_id, source, description])
    assert unique_count == 26 and len(draft_means) == 27
    assert [int(row['old_s1_code'][1:]) for row in mapping if row['classification'] == 'no_match'] == [
        5, 6, 8, 18, 20, 21, 24, 25, 28, 29, 33, 34, 39]
    notes = [
        ['项目', '说明'],
        ['用途', '身份对应核对模板；非39园最终NDVI或SEM输入。'],
        ['原SEM编号', '原SAV/旧17 S1的ParkID，1至39。'],
        ['GIS记录号', '等于39个公园地址.xlsx的NO1至39；不等于已确认原SEM编号，不用0起fid。'],
        ['候选', '26条唯一四极值指纹匹配；另13条空白。数字吻合仍需作者核对真实园身份。'],
        ['填写', 'F列填写作者确认的GIS记录号，核实26条候选并补齐13条；只需两个编号，不需公开名称地址。'],
        ['原外部范围', '18旧编号只有完整外扩面（含园内）复现外部极值。新均值仍使用扣园内后的100m环带。'],
        ['均值表', '第三张仅是26条身份候选的有效像元均值，不是旧中间值，不填缺失为0，不可当最终SEM。'],
        ['原数据保护', '原SAV、原双语Excel、原模型及原GIS文件未改。此前4套同号拼接的候选输入暂停使用。'],
    ]
    workbook_path = OUT / '39公园编号对应_作者核对表.xlsx'
    xlsx(workbook_path, [('39公園対応確認', confirmation), ('4公園数値照合', target_summary),
                          ('26候補の区域平均_非最終', draft_means), ('填写说明', notes)])
    with (OUT / '39公园编号对应_作者核对表.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        csv.writer(stream).writerows(confirmation)
    for name in ('independent_old_extrema_cross_id.json', 'independent_cross_id_mapping.tsv',
                 'forensic_ndbi_crossmatch.json', 'identity_columns_audit.json', 'metadata_only_audit.txt'):
        shutil.copy2(AUDIT / name, evidence / name)
    for name in ('qc_old_extrema_cross_id.py', 'qc_forensic_ndbi_crossmatch.py', 'audit_identity_columns.py'):
        shutil.copy2(AUDIT / name, scripts / name)
    shutil.copy2(WORK / 'build_old_extrema_handoff.py', scripts / 'build_old_extrema_handoff.py')
    shutil.copy2(ROOT / 'NDVI_重要更正_编号对应与数据使用状态_20261111.txt', OUT / '0_重要更正_之前四套SEM输入暂停使用.txt')
    report = {'old_SEM_rows': 39, 'unique_numeric_fingerprint_candidates': 26,
              'nonmatching_old_ids': [5, 6, 8, 18, 20, 21, 24, 25, 28, 29, 33, 34, 39],
              'different_number_unique_matches': 22, 'author_confirmation_column_all_39_blank': True,
              'primary_imagery_or_final_id_alignment_selected': False,
              'new_SEM_input_generated': False, 'source_data_overwritten': False,
              'target_9_numeric_match': {'GIS_record': 20, 'source': 'NDVI_tokyo_down.tif'},
              'target_32_numeric_match': {'GIS_record': 22, 'source': 'NDVI_fukushima.tif'}}
    (OUT / '交付状态.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    files = sorted(path for path in OUT.rglob('*') if path.is_file() and '__pycache__' not in path.parts)
    manifest = [{'file': path.relative_to(OUT).as_posix(), 'bytes': path.stat().st_size,
                 'sha256': sha256(path)} for path in files]
    (OUT / '文件校验.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    files.append(OUT / '文件校验.json')
    archive_path = ROOT / (OUT.name + '.zip')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, (Path(OUT.name) / path.relative_to(OUT)).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
    print(json.dumps({**report, 'workbook': str(workbook_path), 'zip': str(archive_path),
                      'archive_integrity_pass': True}, ensure_ascii=True))


if __name__ == '__main__':
    build()
