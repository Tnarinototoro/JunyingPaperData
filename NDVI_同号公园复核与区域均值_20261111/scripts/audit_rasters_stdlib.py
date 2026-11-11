"""Read GeoTIFF headers/tags only; never load pixels or modify source data."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
from pathlib import Path
import re
import struct
import xml.etree.ElementTree as ET


TAG_NAMES = {
    254: "NewSubfileType", 256: "ImageWidth", 257: "ImageLength",
    258: "BitsPerSample", 259: "Compression", 262: "PhotometricInterpretation",
    269: "DocumentName", 270: "ImageDescription", 273: "StripOffsets", 277: "SamplesPerPixel",
    278: "RowsPerStrip", 279: "StripByteCounts", 284: "PlanarConfiguration", 305: "Software",
    306: "DateTime", 315: "Artist", 322: "TileWidth", 323: "TileLength",
    324: "TileOffsets", 325: "TileByteCounts",
    338: "ExtraSamples", 339: "SampleFormat", 700: "XMP",
    33550: "ModelPixelScaleTag", 33922: "ModelTiepointTag",
    34264: "ModelTransformationTag", 34735: "GeoKeyDirectoryTag",
    34736: "GeoDoubleParamsTag", 34737: "GeoAsciiParamsTag",
    42112: "GDAL_METADATA", 42113: "GDAL_NODATA",
}
TYPE_FORMATS = {
    1: ("B", 1), 2: (None, 1), 3: ("H", 2), 4: ("I", 4),
    5: ("II", 8), 6: ("b", 1), 7: (None, 1), 8: ("h", 2),
    9: ("i", 4), 10: ("ii", 8), 11: ("f", 4), 12: ("d", 8),
    13: ("I", 4), 16: ("Q", 8), 17: ("q", 8), 18: ("Q", 8),
}
GEO_KEY_NAMES = {
    1024: "GTModelTypeGeoKey", 1025: "GTRasterTypeGeoKey",
    1026: "GTCitationGeoKey", 2048: "GeographicTypeGeoKey",
    2049: "GeogCitationGeoKey", 2050: "GeogGeodeticDatumGeoKey",
    2054: "GeogAngularUnitsGeoKey", 3072: "ProjectedCSTypeGeoKey",
    3073: "PCSCitationGeoKey", 3074: "ProjectionGeoKey",
    3075: "ProjCoordTransGeoKey", 3076: "ProjLinearUnitsGeoKey",
}


def read_exact(stream, offset, length, total_length):
    if offset < 0 or length < 0 or offset + length > total_length:
        raise ValueError("TIFF metadata offset is outside the source file")
    stream.seek(offset)
    value = stream.read(length)
    if len(value) != length:
        raise ValueError("Truncated TIFF metadata")
    return value


def read_ifd(path):
    stat = path.stat()
    tags, skipped = {}, []
    with path.open("rb") as stream:
        header = read_exact(stream, 0, 16, stat.st_size)
        order = {b"II": "<", b"MM": ">"}.get(header[:2])
        if not order:
            raise ValueError("Not a TIFF byte-order signature")
        version = struct.unpack(order + "H", header[2:4])[0]
        if version == 42:
            big, inline_size, entry_size, count_size = False, 4, 12, 2
            ifd_offset = struct.unpack(order + "I", header[4:8])[0]
        elif version == 43:
            if struct.unpack(order + "HH", header[4:8]) != (8, 0):
                raise ValueError("Unsupported BigTIFF offset size")
            big, inline_size, entry_size, count_size = True, 8, 20, 8
            ifd_offset = struct.unpack(order + "Q", header[8:16])[0]
        else:
            raise ValueError(f"Unsupported TIFF version {version}")
        count_fmt = "Q" if big else "H"
        entry_count = struct.unpack(order + count_fmt, read_exact(
            stream, ifd_offset, count_size, stat.st_size))[0]
        if entry_count > 4096:
            raise ValueError("Unexpectedly large TIFF IFD")
        entries = read_exact(stream, ifd_offset + count_size,
                             entry_count * entry_size, stat.st_size)
        for entry_index in range(entry_count):
            entry = entries[entry_index * entry_size:(entry_index + 1) * entry_size]
            tag, value_type = struct.unpack(order + "HH", entry[:4])
            if tag not in TAG_NAMES:
                continue
            if value_type not in TYPE_FORMATS:
                skipped.append({"tag": tag, "reason": "unknown TIFF value type"})
                continue
            value_count = struct.unpack(order + ("Q" if big else "I"),
                                        entry[4:12] if big else entry[4:8])[0]
            fmt, size = TYPE_FORMATS[value_type]
            byte_count = value_count * size
            if byte_count > 1048576:
                skipped.append({"tag": tag, "reason": "metadata larger than 1 MiB"})
                continue
            inline = entry[12:20] if big else entry[8:12]
            if byte_count <= inline_size:
                raw = inline[:byte_count]
            else:
                value_offset = struct.unpack(order + ("Q" if big else "I"), inline)[0]
                raw = read_exact(stream, value_offset, byte_count, stat.st_size)
            if value_type in (2, 7):
                value = raw.rstrip(b"\0").decode("utf-8", errors="replace")
            elif value_type in (5, 10):
                value = [list(struct.unpack(order + fmt, raw[i * size:(i + 1) * size]))
                         for i in range(value_count)]
            else:
                value = list(struct.unpack(order + fmt * value_count, raw))
            tags[tag] = value
        pointer_pos = ifd_offset + count_size + entry_count * entry_size
        next_ifd = struct.unpack(order + ("Q" if big else "I"),
                                read_exact(stream, pointer_pos, inline_size, stat.st_size))[0]
    return tags, {"big_tiff": big, "byte_order": order,
                  "first_ifd_entries": entry_count, "next_ifd_offset": next_ifd,
                  "skipped_tags": skipped}


def first(tags, key, default=None):
    value = tags.get(key, [default])
    return value[0] if isinstance(value, list) and value else default


def geo_keys(tags):
    directory = tags.get(34735, [])
    if not isinstance(directory, list) or len(directory) < 4:
        return {}
    result = {}
    for start in range(4, min(len(directory), 4 + directory[3] * 4), 4):
        key, location, count, offset = directory[start:start + 4]
        if location == 0:
            value = offset
        else:
            values = tags.get(location, [])
            value = values[offset:offset + count]
            if isinstance(value, str):
                value = value.rstrip("|\0")
            elif len(value) == 1:
                value = value[0]
        result[str(key)] = {"name": GEO_KEY_NAMES.get(key, "GeoKey"), "value": value}
    return result


def metadata_items(raw):
    if not raw:
        return []
    try:
        return [{"name": node.get("name"), "sample": node.get("sample"),
                 "role": node.get("role"), "domain": node.get("domain"),
                 "value": node.text}
                for node in ET.fromstring(raw).iter("Item")]
    except ET.ParseError:
        return [{"name": "UNPARSED_GDAL_METADATA", "value": raw}]


def sidecar_metadata(path):
    aux = path.with_name(path.name + ".aux.xml")
    if not aux.exists():
        return None
    root = ET.parse(aux).getroot()
    bands = []
    for band in root.iter("PAMRasterBand"):
        bands.append({"band": band.get("band"),
                      "metadata": {node.get("key"): node.text for node in band.iter("MDI")}})
    return {"filename": aux.name, "bands": bands}


def storage_layout(tags):
    strip_offsets, strip_bytes = tags.get(273, []), tags.get(279, [])
    tile_offsets, tile_bytes = tags.get(324, []), tags.get(325, [])
    offsets, byte_counts = (tile_offsets, tile_bytes) if tile_offsets else (strip_offsets, strip_bytes)
    differences = [right - left for left, right in zip(offsets, offsets[1:])]
    return {
        "organization": "tiles" if tile_offsets else "strips",
        "rows_per_strip": first(tags, 278), "tile_width": first(tags, 322),
        "tile_height": first(tags, 323), "planar_configuration": first(tags, 284, 1),
        "block_count": len(offsets), "first_16_block_offsets": offsets[:16],
        "last_block_offset": offsets[-1] if offsets else None,
        "first_16_block_byte_counts": byte_counts[:16],
        "last_block_byte_count": byte_counts[-1] if byte_counts else None,
        "total_stored_pixel_bytes": sum(byte_counts),
        "minimum_block_bytes": min(byte_counts) if byte_counts else None,
        "maximum_block_bytes": max(byte_counts) if byte_counts else None,
        "block_offset_step_constant": len(set(differences)) <= 1,
        "block_offset_step": differences[0] if differences and len(set(differences)) == 1 else None,
        "blocks_are_contiguous": all(left + count == right for left, count, right
                                     in zip(offsets, byte_counts, offsets[1:])),
        "reader_note": "Import read_ifd from this script to retrieve exact tag 273/279 or 324/325 arrays without reading pixels.",
    }


def audit(path):
    tags, container = read_ifd(path)
    keys = geo_keys(tags)
    width, height = first(tags, 256), first(tags, 257)
    scale, ties, matrix = tags.get(33550), tags.get(33922), tags.get(34264)
    transform = None
    if matrix and len(matrix) == 16:
        transform = [matrix[3], matrix[0], matrix[1], matrix[7], matrix[4], matrix[5]]
    elif scale and ties and len(scale) >= 2 and len(ties) >= 6:
        transform = [ties[3] - ties[0] * scale[0], scale[0], 0,
                     ties[4] + ties[1] * scale[1], 0, -scale[1]]
    extent = None
    raster_type = keys.get("1025", {}).get("value")
    if transform is not None and width is not None and height is not None:
        shift = -0.5 if raster_type == 2 else 0
        corners = []
        for col, row in [(shift, shift), (width + shift, shift),
                         (shift, height + shift), (width + shift, height + shift)]:
            corners.append((transform[0] + col * transform[1] + row * transform[2],
                            transform[3] + col * transform[4] + row * transform[5]))
        extent = [min(x for x, _ in corners), min(y for _, y in corners),
                  max(x for x, _ in corners), max(y for _, y in corners)]
    items = metadata_items(tags.get(42112))
    scale_items = [item for item in items if item.get("role") == "scale"]
    offset_items = [item for item in items if item.get("role") == "offset"]
    sample_format = first(tags, 339, 1)
    bits = first(tags, 258)
    kind = {1: "UInt", 2: "Int", 3: "Float"}.get(sample_format, f"SampleFormat{sample_format}")
    stem = path.stem.lower()
    category = "NDVI-labelled" if stem.startswith("ndvi_") else (
        "NDBI-labelled; NOT a substitute for NDVI" if stem.startswith("ndbi_")
        else "Hokka auxiliary/candidate; index identity not established")
    source_time_items = [item for item in items if re.search(
        r"source|product|sensor|satellite|acqui|date|time|landsat|sentinel|system:",
        " ".join(str(item.get(key) or "") for key in ["name", "value"]), re.I)]
    sidecar = sidecar_metadata(path)
    stored_statistics = {item["name"]: item.get("value") for item in items
                         if (item.get("name") or "").startswith("STATISTICS_")}
    if sidecar:
        for band in sidecar["bands"]:
            if band.get("band") == "1":
                stored_statistics.update({key: value for key, value in band["metadata"].items()
                                          if key.startswith("STATISTICS_")})
    issues = []
    model_type = keys.get("1024", {}).get("value")
    if model_type == 2 and extent and (max(abs(extent[0]), abs(extent[2])) > 180
                                     or max(abs(extent[1]), abs(extent[3])) > 90):
        issues.append("Geographic CRS declaration conflicts with projected-looking coordinate magnitudes; do not silently relabel/reproject.")
    if any(not value for value in tags.get(279, [])):
        issues.append("Zero-byte strips exist; do not read offset zero as image pixels.")
    if any(re.search(r"inf|nan", str(value), re.I) for value in stored_statistics.values()):
        issues.append("Stored statistics contain nonfinite values; not evidence of usable NDVI.")
    if keys.get("3072", {}).get("value") == 32767:
        issues.append("ProjectedCSType=32767 means a user-defined CRS, not an EPSG authority code.")
    stat = path.stat()
    return {
        "filename": path.name, "category": category, "file_bytes": stat.st_size,
        "filesystem_modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat(),
        "filesystem_date_caveat": "File modification is not imagery acquisition/compositing time.",
        "width": width, "height": height, "bands_samples_per_pixel": first(tags, 277, 1),
        "bits_per_sample": tags.get(258), "sample_format": sample_format,
        "data_type": kind + str(bits), "compression_code": first(tags, 259),
        "photometric_interpretation": first(tags, 262),
        "storage_layout": storage_layout(tags),
        "crs_epsg_projected": keys.get("3072", {}).get("value"),
        "crs_epsg_geographic": keys.get("2048", {}).get("value"),
        "linear_units_geokey": keys.get("3076", {}).get("value"),
        "geo_keys": keys, "pixel_scale_tag": scale,
        "pixel_resolution_in_crs_units": [math.hypot(transform[1], transform[4]),
                                          math.hypot(transform[2], transform[5])] if transform else None,
        "geotransform": transform, "extent_crs_units": extent,
        "extent_caveat": "Whole-raster bounding extent, not park coordinates or valid-pixel footprint.",
        "nodata_text": tags.get(42113),
        "band_scale": scale_items or "No explicit scale metadata: GDAL semantic default is 1.",
        "band_offset": offset_items or "No explicit offset metadata: GDAL semantic default is 0.",
        "tiff_datetime_tag": tags.get(306), "software_tag": tags.get(305),
        "image_description_tag": tags.get(270), "document_name_tag": tags.get(269),
        "gdal_metadata_items": items, "source_time_candidate_metadata": source_time_items,
        "sidecar": sidecar, "stored_statistics": stored_statistics,
        "stored_statistics_caveat": "Copied header/PAM statistics only; approximate where marked; not recalculated and not park-specific.",
        "metadata_issues": issues, "tiff_container": container,
        "pixel_statistics_computed": False,
        "provenance_caveat": "Filename/index label and container metadata alone do not verify sensor provenance, acquisition date, NDVI formula, or valid pixels.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for path in sorted(args.input_dir.glob("*.tif"), key=lambda p: p.name.lower()):
        try:
            records.append(audit(path))
        except Exception as exc:
            records.append({"filename": path.name, "error": str(exc)})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {"method": "Python standard-library TIFF/GeoTIFF first-IFD tag audit; source files read-only; no image pixel arrays loaded.",
              "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "input_tiff_count": len(records), "rasters": records}
    json_path = args.output_dir / "audit_rasters_stdlib.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    columns = ["filename", "category", "file_bytes", "width", "height", "bands_samples_per_pixel",
               "data_type", "crs_epsg_projected", "crs_epsg_geographic", "pixel_resolution_in_crs_units",
               "extent_crs_units", "nodata_text", "tiff_datetime_tag", "filesystem_modified_utc"]
    with (args.output_dir / "audit_rasters_stdlib.tsv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: json.dumps(record.get(key), ensure_ascii=False) if isinstance(record.get(key), (list, dict))
                             else record.get(key) for key in columns})
    print(json.dumps({"tiffs_audited": len(records), "errors": [record for record in records if "error" in record],
                      "json_report": str(json_path),
                      "image_pixels_read": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
