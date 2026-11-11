"""Audit identifier columns only; never emit park names, addresses or coordinates."""

import json
import re
import struct
import unicodedata
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def is_id_name(name):
    text = unicodedata.normalize("NFKC", name).strip().lower()
    compact = re.sub(r"[\s_.-]", "", text)
    return (compact in {"no", "id", "parkid", "parkno", "semid", "semno", "origid", "origno", "originalid", "originalno"}
            or any(word in text for word in ["番号", "编号", "編號", "番號"])
            or bool(re.search(r"(?:original|orig|old|sem|旧|原).*(?:id|no|号)", text)))


def integer_or_none(value):
    text = str(value).strip()
    try:
        number = float(text)
        return int(number) if number.is_integer() else None
    except (ValueError, OverflowError):
        return None


def dbf_audit(path):
    raw = path.read_bytes()
    count = struct.unpack_from("<I", raw, 4)[0]
    header_size, record_size = struct.unpack_from("<HH", raw, 8)
    fields, position, byte_position = [], 32, 1
    while position < header_size and raw[position] != 13:
        descriptor = raw[position:position + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("utf-8", errors="replace")
        fields.append({"name": name, "type": chr(descriptor[11]), "width": descriptor[16],
                       "decimal_places": descriptor[17], "private_byte_offset": byte_position})
        byte_position += descriptor[16]
        position += 32
    identifiers = []
    value_profiles = []
    private_name_values = []
    for field in fields:
        values, nonblank, embedded_id_records = [], 0, []
        for index in range(count):
            start = header_size + index * record_size + field["private_byte_offset"]
            value = raw[start:start + field["width"]].decode("utf-8", errors="replace").strip()
            if field["name"] == "Name":
                private_name_values.append(value)
            values.append(integer_or_none(value))
            nonblank += bool(value)
            hits = re.findall(r"(?:Park[_ ]?ID|SEM[_ ]?ID|原番号|原编号|旧番号|旧编号|\bNO\b|\bNo\.)\s*(?:[:=：#]|</td>\s*<td[^>]*>)?\s*(\d+)", value, re.I)
            if hits:
                embedded_id_records.append({"gis_record": index + 1, "labelled_integer_ids": [int(hit) for hit in hits]})
        numeric = [value for value in values if value is not None]
        value_profiles.append({"field": field["name"], "nonblank_records": nonblank,
                               "integer_only_records": len(numeric),
                               "unique_integer_only_values": sorted(set(numeric)),
                               "labelled_embedded_identifier_records": embedded_id_records})
        if is_id_name(field["name"]) or (numeric and len(numeric) == nonblank and len(set(numeric)) > 1):
            identifiers.append({"field": field["name"], "integer_values_in_gis_record_order": values,
                                "matches_gis_record_1_to_39": values == list(range(1, 40)),
                                "all_integers": all(value is not None for value in values),
                                "unique_nonblank_n": len({value for value in values if value is not None})})
    return {"file": path.name, "record_count": count,
            "fields": [{key: value for key, value in field.items() if not key.startswith("private_")}
                       for field in fields], "identifier_fields": identifiers,
            "nonidentifying_value_profiles": value_profiles,
            "_private_name_values": private_name_values}


def cell_value(cell, shared):
    kind = cell.get("t")
    if kind == "inlineStr":
        return "".join(node.text or "" for node in cell.iter("{" + MAIN_NS + "}t"))
    value = cell.find("{" + MAIN_NS + "}v")
    text = value.text if value is not None else ""
    return shared[int(text)] if kind == "s" and text else text


def workbook_audit(path):
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared = ["".join(node.text or "" for node in si.iter("{" + MAIN_NS + "}t"))
                      for si in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = {node.get("Id"): node.get("Target") for node in
                ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        sheets = []
        private_no_name_rows = []
        for index, sheet in enumerate(workbook.find("{" + MAIN_NS + "}sheets"), 1):
            target = rels[sheet.get("{" + REL_NS + "}id")]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            xml = ET.fromstring(archive.read(part))
            data_rows = []
            formula_count, cross_sheet_formula_count = 0, 0
            for row in xml.iter("{" + MAIN_NS + "}row"):
                cells = {}
                for cell in row.findall("{" + MAIN_NS + "}c"):
                    address = cell.get("r")
                    cells[re.sub(r"\d", "", address)] = cell_value(cell, shared)
                    formula = cell.find("{" + MAIN_NS + "}f")
                    if formula is not None:
                        formula_count += 1
                        cross_sheet_formula_count += "!" in (formula.text or "")
                data_rows.append((int(row.get("r")), cells))
            id_headers = []
            for row_no, cells in data_rows[:5]:
                for col, value in cells.items():
                    if isinstance(value, str) and is_id_name(value):
                        values = [integer_or_none(other_cells[col]) for other_row, other_cells in data_rows
                                  if other_row > row_no and col in other_cells and str(other_cells[col]).strip()]
                        id_headers.append({"column": col, "header_row": row_no, "header": value,
                                           "integer_values_in_sheet_order": values,
                                           "matches_1_to_39": values == list(range(1, 40)),
                                           "all_integers": all(value is not None for value in values)})
            # Semantic column headers are safe; cell values naming parks are never emitted.
            common_headers = {"no", "no.", "id", "名称", "名前", "公園名", "公园名称", "公园名", "住所", "地址", "所在地",
                              "緯度", "経度", "latitude", "longitude", "管理者", "管理主体", "備考", "备注"}
            header_rows = [{"row": row_no, "columns": [{"column": col, "header": value}
                            for col, value in cells.items() if isinstance(value, str)
                            and (unicodedata.normalize("NFKC", value).strip().lower() in common_headers or is_id_name(value))]}
                           for row_no, cells in data_rows[:5]]
            first_row_headers = [{"column": col, "header": value} for col, value in data_rows[0][1].items()]
            all_id_labels = [{"row": row_no, "column": col, "identifier_label": value}
                             for row_no, cells in data_rows for col, value in cells.items()
                             if isinstance(value, str) and is_id_name(value)]
            columns = sorted({col for _, cells in data_rows for col in cells})
            nonblank_by_column = {col: sum(bool(str(cells.get(col, "")).strip()) for _, cells in data_rows[1:])
                                 for col in columns}
            if data_rows[0][1].get("A") == "NO" and data_rows[0][1].get("B") == "Name":
                private_no_name_rows.extend((integer_or_none(cells.get("A", "")), cells.get("B", ""))
                                            for _, cells in data_rows[1:] if integer_or_none(cells.get("A", "")) is not None)
            numeric_profiles = []
            for col in columns:
                numbers = [(row_no, integer_or_none(cells[col])) for row_no, cells in data_rows[1:]
                           if col in cells and str(cells[col]).strip()]
                if numbers and all(value is not None for _, value in numbers):
                    numeric_profiles.append({"column": col, "integer_values": [value for _, value in numbers],
                                             "worksheet_rows": [row for row, _ in numbers]})
            dimension = xml.find("{" + MAIN_NS + "}dimension")
            safe_sheet_name = sheet.get("name") if re.fullmatch(r"(?:Sheet|工作表|シート)\s*\d+", sheet.get("name", ""), re.I) else None
            sheets.append({"sheet_index": index, "safe_generic_sheet_name": safe_sheet_name,
                           "sheet_state": sheet.get("state", "visible"), "xml_part": part,
                           "dimension": dimension.get("ref") if dimension is not None else None,
                           "populated_row_count": len(data_rows), "safe_header_rows": header_rows,
                           "first_row_column_headers": first_row_headers,
                           "all_identifier_labels": all_id_labels,
                           "integer_only_data_columns": numeric_profiles,
                           "nonblank_data_cell_count_by_column": nonblank_by_column,
                           "column_visibility_metadata": [{"min": col.get("min"), "max": col.get("max"),
                                                           "hidden": col.get("hidden", "0")}
                                                          for col in xml.iter("{" + MAIN_NS + "}col")],
                           "identifier_headers": id_headers, "formula_count": formula_count,
                           "cross_sheet_formula_count": cross_sheet_formula_count})
        names = workbook.find("{" + MAIN_NS + "}definedNames")
        return {"file": path.name, "worksheet_count": len(sheets), "worksheets": sheets,
                "defined_name_count": len(names) if names is not None else 0,
                "external_link_part_count": sum(name.startswith("xl/externalLinks/") and name.endswith(".xml")
                                                for name in archive.namelist()),
                "privacy": "Only identifier/header metadata and integer ID sequences emitted; no park names, addresses or coordinate values.",
                "_private_no_name_rows": private_no_name_rows}


def main():
    out = Path(__file__).resolve().parent
    root = out.parents[1]
    dbf = dbf_audit(root / "NDVI" / "parks_metric.dbf")
    book = workbook_audit(root / "39个公园地址.xlsx")
    private_names = dbf.pop("_private_name_values")
    private_rows = book.pop("_private_no_name_rows")
    normalize = lambda value: " ".join(unicodedata.normalize("NFKC", str(value)).split())
    numeric_crosswalk = [{"gis_record": index, "matching_excel_NO": [number for number, label in private_rows
                          if normalize(name) == normalize(label)],
                          "method": "Exact private Name equality after Unicode/whitespace normalization; no name value emitted."}
                         for index, name in enumerate(private_names, 1)]
    report = {"dbf": dbf, "workbook": book,
              "gis_to_excel_name_match_numeric_only": numeric_crosswalk,
              "source_files_modified": False,
              "caution": "GIS record/Excel NO agreement does not prove equivalence to anonymous SEM ParkID or old S1 numbering."}
    target = out / "identity_columns_audit.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
