"""Read-only independent physical SHP/SHX/DBF linking QC, private labels.

No park names, addresses, coordinate values, automatic row remapping or SEM
operations are output or performed. Geometry XY values are compared in memory
only to check the existing reader, not to establish real-world park identity.
"""
import collections
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "NDVI_mean_work"))
from audit_vectors_std import read_shp as prior_read_shp


def independently_read_shp(path):
    data = path.read_bytes()
    if len(data) < 100:
        raise ValueError("Invalid SHP header length")
    header = {"code": struct.unpack_from(">i", data, 0)[0],
              "declared_bytes": struct.unpack_from(">i", data, 24)[0] * 2,
              "version": struct.unpack_from("<i", data, 28)[0],
              "shape_type": struct.unpack_from("<i", data, 32)[0]}
    rows, offset = [], 100
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("Truncated SHP record header")
        number, words = struct.unpack_from(">ii", data, offset)
        end = offset + 8 + words * 2
        if words < 2 or end > len(data):
            raise ValueError("Invalid SHP content length")
        content = memoryview(data)[offset + 8:end]
        shape_type = struct.unpack_from("<i", content, 0)[0]
        points, parts = [], []
        npoints = nparts = 0
        if shape_type == 15:
            nparts, npoints = struct.unpack_from("<ii", content, 36)
            if nparts < 1 or npoints < 1 or 44 + 4 * nparts + 16 * npoints > len(content):
                raise ValueError("Invalid PolygonZ array lengths")
            starts = list(struct.unpack_from("<" + "i" * nparts, content, 44))
            if starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= npoints:
                raise ValueError("Invalid PolygonZ part indices")
            points = [struct.unpack_from("<dd", content, 44 + 4 * nparts + 16 * i) for i in range(npoints)]
            parts = [points[a:b] for a, b in zip(starts, starts[1:] + [npoints])]
        rows.append({"physical_position": len(rows) + 1, "record_number": number,
                     "byte_offset": offset, "content_words": words, "shape_type": shape_type,
                     "nparts": nparts, "npoints": npoints, "private_parts": parts,
                     "content_sha256": hashlib.sha256(content).hexdigest()})
        offset = end
    return data, header, rows, offset == len(data)


def independently_read_dbf(path, encoding):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 4)[0]
    header_length, record_length = struct.unpack_from("<HH", data, 8)
    fields, cursor, value_offset = [], 32, 1
    while cursor < header_length and data[cursor] != 13:
        descriptor = data[cursor:cursor + 32]
        if len(descriptor) != 32:
            raise ValueError("Truncated DBF descriptor")
        field_name = bytes(descriptor[:11]).split(b"\0", 1)[0].decode("ascii")
        width = descriptor[16]
        fields.append({"name": field_name, "type": chr(descriptor[11]), "width": width, "offset": value_offset})
        value_offset += width
        cursor += 32
    name_field = next(field for field in fields if field["name"] == "Name")
    rows = []
    for ordinal in range(count):
        record = data[header_length + ordinal * record_length:header_length + (ordinal + 1) * record_length]
        if len(record) != record_length:
            raise ValueError("Truncated DBF record")
        raw = record[name_field["offset"]:name_field["offset"] + name_field["width"]].rstrip(b" \0")
        try:
            private_name = raw.decode(encoding, errors="strict")
        except UnicodeError:
            raise ValueError("Private DBF label cannot be decoded with CPG encoding") from None
        rows.append({"physical_position": ordinal + 1, "active": record[0] == 32,
                     "deleted": record[0] == 42, "private_name": private_name})
    return data, {"header_record_count": count, "header_length": header_length,
                  "record_length": record_length, "fields_sum_matches_record_length": value_offset == record_length,
                  "descriptor_terminator_present": data[cursor] == 13,
                  "record_payload_complete": header_length + count * record_length <= len(data),
                  "trailing_bytes": len(data) - header_length - count * record_length}, rows


def private_workbook_rows(path):
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns):
                shared.append("".join(node.text or "" for node in item.findall(".//s:t", ns)))
        worksheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows = []
        for row in worksheet.findall(".//s:sheetData/s:row", ns):
            cells = {}
            for cell in row.findall("s:c", ns):
                column = re.match(r"[A-Z]+", cell.attrib["r"]).group(0)
                value_node = cell.find("s:v", ns)
                value = value_node.text if value_node is not None else ""
                if cell.attrib.get("t") == "s":
                    value = shared[int(value)]
                elif cell.attrib.get("t") == "inlineStr":
                    value = "".join(node.text or "" for node in cell.findall(".//s:t", ns))
                cells[column] = value or ""
            if cells.get("B", "").strip() and cells.get("C", "").strip() and cells.get("A", "").isdigit():
                rows.append({"NO": int(cells["A"]), "private_name": cells["B"], "worksheet_row": int(row.attrib["r"])})
        return rows


def normalize(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def main():
    shp_path, shx_path = ROOT / "NDVI/parks_metric.shp", ROOT / "NDVI/parks_metric.shx"
    dbf_path, cpg_path = ROOT / "NDVI/parks_metric.dbf", ROOT / "NDVI/parks_metric.cpg"
    workbook_path = ROOT / "39个公园地址.xlsx"
    encoding = cpg_path.read_text(encoding="ascii").strip()
    shp_data, shp_header, shp_rows, parsed_to_end = independently_read_shp(shp_path)
    shx_data = shx_path.read_bytes()
    if len(shx_data) < 100 or (len(shx_data) - 100) % 8:
        raise ValueError("Invalid SHX payload length")
    shx_rows = [struct.unpack_from(">ii", shx_data, offset) for offset in range(100, len(shx_data), 8)]
    dbf_data, dbf_header, dbf_rows = independently_read_dbf(dbf_path, encoding)
    excel_rows = private_workbook_rows(workbook_path)
    prior = prior_read_shp(shp_path, include_points=True)["feature_details"]
    links = []
    for ordinal, row in enumerate(shp_rows):
        dbf_row = dbf_rows[ordinal]
        raw_matches = [item["NO"] for item in excel_rows if item["private_name"].strip() == dbf_row["private_name"].strip()]
        normalized_matches = [item["NO"] for item in excel_rows if normalize(item["private_name"]) == normalize(dbf_row["private_name"])]
        expected_shx = (row["byte_offset"] // 2, row["content_words"])
        links.append({"shp_physical_position": row["physical_position"], "shp_record_number": row["record_number"],
            "shx_position": ordinal + 1, "shx_offset_and_length_match_physical_shp": shx_rows[ordinal] == expected_shx,
            "dbf_physical_position": dbf_row["physical_position"], "dbf_active": dbf_row["active"],
            "dbf_name_raw_matching_excel_NO": raw_matches, "dbf_name_normalized_matching_excel_NO": normalized_matches,
            "prior_reader_record_number_matches": prior[ordinal]["record"] == row["record_number"],
            "prior_reader_geometry_xy_part_arrays_match_independent_parse": prior[ordinal].get("private_parts") == row["private_parts"],
            "geometry_content_sha256": row["content_sha256"], "geometry_part_count": row["nparts"], "geometry_point_count": row["npoints"]})
    checks = {
        "shp_file_code_9994": shp_header["code"] == 9994,
        "shp_version_1000": shp_header["version"] == 1000,
        "shp_declared_file_size_matches": shp_header["declared_bytes"] == len(shp_data),
        "shp_parsed_exactly_to_end": parsed_to_end,
        "shp_physical_record_numbers_are_1_through_39": [row["record_number"] for row in shp_rows] == list(range(1, 40)),
        "all_shp_records_polygonz": all(row["shape_type"] == 15 for row in shp_rows),
        "shx_declared_file_size_matches": struct.unpack_from(">i", shx_data, 24)[0] * 2 == len(shx_data),
        "shx_fixed_header_and_geometry_bounds_bytes_match_shp": shx_data[:24] == shp_data[:24] and shx_data[28:100] == shp_data[28:100],
        "shp_shx_dbf_and_named_excel_record_counts_all_39": len(shp_rows) == len(shx_rows) == len(dbf_rows) == len(excel_rows) == 39,
        "all_shx_rows_match_physical_shp_offset_and_length": all(row["shx_offset_and_length_match_physical_shp"] for row in links),
        "no_deleted_or_inactive_dbf_records": all(row["active"] and not row["deleted"] for row in dbf_rows),
        "all_dbf_row_labels_match_same_number_excel_NO_after_normalization": all(row["dbf_name_normalized_matching_excel_NO"] == [row["dbf_physical_position"]] for row in links),
        "all_dbf_row_labels_match_same_number_excel_NO_without_normalization": all(row["dbf_name_raw_matching_excel_NO"] == [row["dbf_physical_position"]] for row in links),
        "all_prior_reader_record_numbers_and_private_xy_arrays_match_independent_parse": all(row["prior_reader_record_number_matches"] and row["prior_reader_geometry_xy_part_arrays_match_independent_parse"] for row in links),
        "dbf_record_length_and_descriptors_valid": all(dbf_header[key] for key in ("fields_sum_matches_record_length", "descriptor_terminator_present", "record_payload_complete")),
    }
    report = {
        "scope": "Independent read-only SHP physical records, SHX index, DBF label row order and private Excel Name alignment. No actual geographic location validation in this structural subtask.",
        "author_authority": "Author confirmation accepted: Excel NO, old S1 Pxx and anonymous SAV ParkID denote the same 1-through-39 identities; no alternative cross-ID identity mapping inferred.",
        "input_files_modified": False, "automatic_row_reordering_performed": False, "sem_run_performed": False,
        "names_addresses_or_coordinate_values_output": False,
        "cpg_encoding": encoding, "checks": checks, "all_structural_checks_pass": all(checks.values()),
        "shp_record_count": len(shp_rows), "shx_record_count": len(shx_rows), "dbf_record_count": len(dbf_rows),
        "named_excel_row_count": len(excel_rows), "dbf_layout": dbf_header,
        "input_file_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (shp_path, shx_path, dbf_path, cpg_path, workbook_path)},
        "per_record_links": links,
        "reader_code_assessment": "audit_vectors_std.read_shp appends records in physical byte order and retains the SHP record number; it does not sort features. For this file record numbers equal positions 1..39, SHX positions and DBF positions, so using the header number does not alter row order. Independent XY/part parsing matches the prior reader for every record.",
        "version_and_identity_limits": [
            "Structural agreement and exact private label-to-Excel alignment exclude a detected SHX index or parser-order mismatch for the supplied files. They do not prove historical SHP and DBF came from the same export version.",
            "SHP records do not embed the DBF Name text or an immutable feature UUID. A DBF and SHP with the same 39-record layout could be internally consistent yet semantically mispaired.",
            "Actual geometry location versus labelled park/address requires private independent location or boundary evidence; this structural subtask does not certify it.",
            "No numeric extrema match is used to overturn the author's identity confirmation."
        ],
    }
    print(json.dumps(report, ensure_ascii=True, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
