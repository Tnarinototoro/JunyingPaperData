"""Validate and archive the derived review package without changing inputs.

Uses standard-library Python only. The resulting GIS ZIP is confidential:
anonymous numeric attributes do not anonymize spatial geometry.
"""

import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

from audit_vectors_std import read_shp, read_dbf


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def finalize(root):
    work = root / 'NDVI_mean_work'
    package = root / 'NDVI_区域平均值_20261111_核对版'
    archive_path = root / 'NDVI_区域平均值_20261111_核对版.zip'
    if archive_path.exists():
        raise FileExistsError('Refusing to overwrite an existing archive')
    qc = package / 'QC'
    qc.mkdir(exist_ok=True)
    for name in ('qc_native_raster_reads.json', 'qc_crop_raw_bits.json',
                 'audit_regional_means_qc.json', 'qc_workbook_consistency.json'):
        shutil.copy2(work / name, qc / name)
    for name in ('qc_native_raster_reads.py', 'qc_crop_raw_bits.py',
                 'qc_regional_means_stdlib.py', 'finalize_review_package.py'):
        shutil.copy2(work / name, package / 'scripts' / name)

    # This check uses only the actual NDVI crops and zone masks in the ZIP.
    sys.path.insert(0, str(package / 'scripts'))
    from verify_pack import verify
    pixel_check = verify(package)
    assert pixel_check['options_verified'] == 43
    assert pixel_check['regions_verified'] == 86
    assert pixel_check['maximum_mean_difference'] == 0
    (qc / 'qc_packaged_pixel_means.json').write_text(
        json.dumps(pixel_check, ensure_ascii=False, indent=2), encoding='utf-8')

    with (package / 'NDVI_area_means_39_review.csv').open(
            encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert [int(row['ParkID']) for row in rows] == list(range(1, 40))
    pending = [int(row['ParkID']) for row in rows if row['status'] == 'CHOOSE_SOURCE']
    assert pending == [9, 18, 28, 32]
    assert sum(row['status'] == 'CONFIRMED' for row in rows) == 35
    assert all(row['z_inside_area_mean'] == row['z_outside_area_mean'] == '' for row in rows)
    assert all(row['ndvi_inside_area_mean'] == row['ndvi_outside_100m_ring_area_mean'] == ''
               for row in rows if row['status'] == 'CHOOSE_SOURCE')
    with zipfile.ZipFile(package / 'NDVI区域平均值_39公园_待4园影像确认.xlsx') as book:
        assert book.testzip() is None
        for item in book.namelist():
            if item.endswith('.xml') or item.endswith('.rels'):
                ET.fromstring(book.read(item))

    shapes = {}
    for name, expected_parts in (('park_boundaries', 1), ('outer_100m_rings', 2),
                                  ('full_100m_buffers', 1)):
        shp = read_shp(package / 'GIS' / (name + '.shp'))
        dbf = read_dbf(package / 'GIS' / (name + '.dbf'))
        assert shp['records'] == dbf['records'] == 39
        assert shp['header_size_matches'] and shp['index_matches_shp'] and shp['parsed_to_end']
        assert all(row['parts'] == expected_parts for row in shp['feature_details'])
        assert [field['name'] for field in dbf['fields']] == ['ParkID', 'MeanIn', 'MeanOut', 'NIn', 'NOut', 'Status']
        assert all(row['rings'][0]['signed_area'] < 0 for row in shp['feature_details'])
        if expected_parts == 2:
            assert all(row['rings'][1]['signed_area'] > 0 for row in shp['feature_details'])
        shapes[name] = {'records': 39, 'parts_per_record': expected_parts,
                        'shx_verified': True, 'anonymous_attribute_fields': True}

    project = ET.parse(package / 'NDVI区域均值复核.qgs')
    layers = project.findall('./projectlayers/maplayer')
    assert len(layers) == 88
    ids = [layer.findtext('id') for layer in layers]
    assert len(set(ids)) == len(ids)
    for layer in layers:
        datasource = layer.findtext('datasource')
        assert datasource.startswith('./')
        path = (package / datasource).resolve()
        assert path.is_relative_to(package.resolve()) and path.is_file()

    source_manifest = json.loads((package / 'source_manifest.json').read_text(encoding='utf-8'))
    for entry in source_manifest:
        original = root / 'NDVI' / entry['source_file']
        assert original.stat().st_size == entry['bytes']
        assert digest(original) == entry['sha256']
    summary = {
        'package': package.name,
        'numeric_rows': 39,
        'usable_source_selections': 35,
        'unresolved_ParkID': pending,
        'source_selection_not_complete_provenance_verification': True,
        'all_78_final_z_scores_blank': True,
        'final_SEM_input_generated': False,
        'mean_definition': 'Unweighted mean of all finite non-NoData native NDVI pixels whose centres fall in the supplied region',
        'exterior_definition': 'Supplied approximately 100 m buffer part minus corresponding whole park polygon',
        'pixel_extraction_options': 43,
        'pixel_regions_verified': 86,
        'maximum_mean_difference': pixel_check['maximum_mean_difference'],
        'vector_checks': shapes,
        'qgis_project_layer_count': len(layers),
        'qgis_xml_and_relative_paths_verified': True,
        'qgis_gui_opened': False,
        'original_source_manifest_files_matched': len(source_manifest),
        'confidential_spatial_data': True,
    }
    (qc / 'qc_final_package.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    # A manifest of all delivery files except itself, before ZIP packaging.
    files = sorted(path for path in package.rglob('*') if path.is_file()
                   and '__pycache__' not in path.parts
                   and path.name != 'package_file_manifest.json')
    manifest = [{'path': path.relative_to(package).as_posix(),
                 'bytes': path.stat().st_size, 'sha256': digest(path)} for path in files]
    (package / 'package_file_manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    files.append(package / 'package_file_manifest.json')
    with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6) as archive:
        for path in files:
            archive.write(path, (Path(package.name) / path.relative_to(package)).as_posix())
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files)
        assert not any('__pycache__' in name for name in archive.namelist())
        for entry in manifest:
            name = (Path(package.name) / entry['path']).as_posix()
            payload = archive.read(name)
            assert len(payload) == entry['bytes']
            assert hashlib.sha256(payload).hexdigest() == entry['sha256']
    return {**summary, 'archive': str(archive_path), 'archive_files': len(files),
            'archive_bytes': archive_path.stat().st_size,
            'archive_sha256': digest(archive_path), 'archive_integrity_verified': True}


if __name__ == '__main__':
    print(json.dumps(finalize(Path(__file__).resolve().parent.parent), ensure_ascii=True))
