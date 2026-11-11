"""Generate a relative-path QGIS 3.x review project from packaged GIS files.

This is a generated review project, not the user's original QGIS project.
It does not calculate or replace NDVI values.
"""
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET


def child(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, tag, attrs)
    if text is not None:
        node.text = str(text)
    return node


def crs(parent, prj):
    srs = child(parent, 'spatialrefsys', nativeFormat='Wkt')
    child(srs, 'wkt', prj)
    child(srs, 'proj4', '+proj=aea +lat_1=15 +lat_2=65 +lat_0=30 +lon_0=95 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs')
    child(srs, 'authid', 'ESRI:102025')
    child(srs, 'description', 'Asia North Albers Equal Area Conic')
    child(srs, 'projectionacronym', 'aea')
    child(srs, 'ellipsoidacronym', 'EPSG:7030')
    child(srs, 'geographicflag', 'false')


def build(root):
    prj = (root / 'GIS/park_boundaries.prj').read_text(encoding='ascii')
    source = (root / 'GIS/park_boundaries.shp').read_bytes()
    bbox = struct.unpack_from('<4d', source, 36)
    entries = json.loads((root / 'GIS/pixel_extractions.json').read_text(encoding='utf-8'))
    project = ET.Element('qgis', version='3.28.13', projectname='NDVI Regional Mean Review')
    child(project, 'homePath', path='')
    child(project, 'title', 'NDVI Regional Mean Review: 35 sources selected, 4 parks awaiting source selection')
    crs(child(project, 'projectCrs'), prj)
    tree = child(project, 'layer-tree-group', name='', expanded='1', checked='Qt::Checked')
    layers = child(project, 'projectlayers')
    for identifier, name, datasource in [
        ('park_boundaries', '39 park boundaries (ParkID)', 'GIS/park_boundaries.shp'),
        ('outer_100m_rings', '39 exterior rings (park interiors excluded)', 'GIS/outer_100m_rings.shp')]:
        child(tree, 'layer-tree-layer', id=identifier, name=name, source='./' + datasource,
              providerKey='ogr', expanded='1', checked='Qt::Checked')
        layer = child(layers, 'maplayer', type='vector', geometry='Polygon', autoRefreshEnabled='0')
        child(layer, 'id', identifier)
        child(layer, 'datasource', './' + datasource)
        child(layer, 'layername', name)
        child(layer, 'provider', 'ogr', encoding='UTF-8')
        crs(child(layer, 'srs'), prj)
    group = child(tree, 'layer-tree-group', name='Original-pixel ROI crops and region masks (internal review)',
                  expanded='0', checked='Qt::Unchecked')
    for entry in entries:
        subgroup = child(group, 'layer-tree-group', name=entry['label'] + ' ' + entry['status'],
                         expanded='0', checked='Qt::Unchecked')
        for key, suffix in [('ndvi_crop', 'NDVI'), ('zone_mask', 'zones: 1=inside, 2=outside')]:
            identifier = entry['label'] + '_' + key
            name = entry['label'] + ' ' + suffix
            datasource = './' + entry[key]
            assert (root / entry[key]).is_file()
            child(subgroup, 'layer-tree-layer', id=identifier, name=name, source=datasource,
                  providerKey='gdal', expanded='0', checked='Qt::Unchecked')
            layer = child(layers, 'maplayer', type='raster', autoRefreshEnabled='0')
            child(layer, 'id', identifier)
            child(layer, 'datasource', datasource)
            child(layer, 'layername', name)
            child(layer, 'provider', 'gdal')
            # GDAL reads the crop's native CRS from its GeoTIFF EPSG keys.
            pipe = child(layer, 'pipe')
            renderer = child(pipe, 'rasterrenderer', type='singlebandgray', grayBand='1', opacity='1', alphaBand='-1')
            enhancement = child(renderer, 'contrastEnhancement')
            child(enhancement, 'minValue', -1 if key == 'ndvi_crop' else 0)
            child(enhancement, 'maxValue', 1 if key == 'ndvi_crop' else 2)
            child(enhancement, 'algorithm', 1)
    canvas = child(project, 'mapcanvas')
    child(canvas, 'units', 'meters')
    extent = child(canvas, 'extent')
    for name, value in zip(('xmin', 'ymin', 'xmax', 'ymax'), bbox):
        child(extent, name, repr(value))
    child(canvas, 'rotation', 0)
    crs(child(canvas, 'destinationsrs'), prj)
    properties = child(project, 'properties')
    child(child(properties, 'Paths'), 'Absolute', 'false', type='bool')
    path = root / 'NDVI区域均值复核.qgs'
    ET.indent(project, space='  ')
    path.write_bytes(ET.tostring(project, encoding='utf-8', xml_declaration=True))
    ET.parse(path)
    return {'project': str(path), 'layers': len(layers), 'relative_datasources_verified': True,
            'gui_opened': False, 'note': 'Generated XML checked; no local QGIS GUI runtime was available.'}


if __name__ == '__main__':
    print(json.dumps(build(Path(__file__).resolve().parent.parent), ensure_ascii=True))
