"""Add an ID-alignment correction to our previous review bundles.

Preserves the exact prior ZIPs as audit backups; no original GIS/SAV/XLSX is
changed. Numeric artifacts inside the old bundles are retained but suspended.
"""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish():
    root = Path(__file__).resolve().parent.parent
    notice = root / 'NDVI_重要更正_编号对应与数据使用状态_20261111.txt'
    specifications = [
        ('NDVI_区域平均值_20261111_核对版', 'package_file_manifest.json',
         'b9741548af22bfd58326a0234fff9e0cb1ce1fef7e2c8bb61614fa21d88b525e'),
        ('NDVI_四组合SEM敏感性分析_20261111', '文件校验清单.json',
         'd323cf43bea44f0281dc504f0c31c1573ef911b9fc69a4c6c6db51420804632d'),
    ]
    reports = []
    for folder, manifest_name, expected_hash in specifications:
        package = (root / folder).resolve()
        archive = (root / (folder + '.zip')).resolve()
        backup = (root / (folder + '_编号核对前存档_勿作最终数据.zip')).resolve()
        temporary = (root / (folder + '_编号更正临时包.zip')).resolve()
        assert all(path.is_relative_to(root.resolve()) for path in (package, archive, backup, temporary))
        assert archive.is_file() and sha256(archive) == expected_hash
        if backup.exists() or temporary.exists():
            raise FileExistsError('Refusing to replace an existing correction backup/temp file')
        shutil.copy2(archive, backup)
        assert sha256(backup) == expected_hash
        shutil.copy2(notice, package / '0_重要更正_暂停按同号用于SEM.txt')
        files = sorted(path for path in package.rglob('*') if path.is_file()
                       and '__pycache__' not in path.parts and path.name != manifest_name)
        manifest = [{'path': path.relative_to(package).as_posix(), 'bytes': path.stat().st_size,
                     'sha256': sha256(path)} for path in files]
        (package / manifest_name).write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        files.append(package / manifest_name)
        with zipfile.ZipFile(temporary, 'x', compression=zipfile.ZIP_DEFLATED) as target:
            for path in files:
                target.write(path, (Path(package.name) / path.relative_to(package)).as_posix())
        with zipfile.ZipFile(temporary) as target:
            assert target.testzip() is None
        temporary.replace(archive)  # Only our verified, already-backed-up generated ZIP.
        reports.append({'archive': archive.name, 'prior_archive_backup': backup.name,
                        'prior_archive_sha256': expected_hash, 'corrected_archive_sha256': sha256(archive),
                        'correction_notice_included': True, 'original_input_files_modified': False,
                        'same_number_SEM_join_suspended': True})
    print(json.dumps(reports, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    publish()
