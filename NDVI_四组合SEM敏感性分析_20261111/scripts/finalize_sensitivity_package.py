"""Archive the four-input diagnostic package without overwriting originals."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finalize():
    work = Path(__file__).resolve().parent
    root = work.parent
    package = root / 'NDVI_四组合SEM敏感性分析_20261111'
    archive_path = root / (package.name + '.zip')
    if archive_path.exists():
        raise FileExistsError('Refusing to replace an existing delivery archive')
    evidence = package / '复算记录与QC'
    for name in ('qa_four_scenario_diagnostics.json', 'qa_delivery_four_inputs.json'):
        shutil.copy2(work / name, evidence / name)
    shutil.copy2(work / 'finalize_sensitivity_package.py', package / 'scripts/finalize_sensitivity_package.py')
    sys.path.insert(0, str(package / 'scripts'))
    from verify_sem_inputs import verify
    check = verify(package)
    (evidence / '包内四组输入复核.json').write_text(
        json.dumps(check, ensure_ascii=False, indent=2), encoding='utf-8')
    assert sha256(package / '原模型_保持结构.amw') == sha256(root / 'amos模型.amw')
    assert sha256(package / 'SEM输入/原输入_仅用于基线复现.sav') == sha256(root / '最终用于sem的匿名39✖16输入矩阵.sav')
    files = sorted(path for path in package.rglob('*') if path.is_file()
                   and '__pycache__' not in path.parts and path.name != '文件校验清单.json')
    manifest = [{'path': path.relative_to(package).as_posix(),
                 'bytes': path.stat().st_size, 'sha256': sha256(path)} for path in files]
    (package / '文件校验清单.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    files.append(package / '文件校验清单.json')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, (Path(package.name) / path.relative_to(package)).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files)
        for entry in manifest:
            payload = archive.read((Path(package.name) / entry['path']).as_posix())
            assert len(payload) == entry['bytes']
            assert hashlib.sha256(payload).hexdigest() == entry['sha256']
    return {'archive': str(archive_path), 'bytes': archive_path.stat().st_size,
            'sha256': sha256(archive_path), 'files': len(files),
            'archive_integrity_verified': True, 'four_inputs_pass': check['all_four_inputs_pass'],
            'new_valid_SEM_results_delivered': False, 'primary_source_selected': False}


if __name__ == '__main__':
    print(json.dumps(finalize(), ensure_ascii=True))
