"""Read-only SPSS $FL2 numeric-matrix reader using the standard library.

Handles uncompressed or SPSS bytecode-compressed numeric cases and exposes
dictionary metadata. It does not estimate a model, impute data, or modify files.
Output goes to stdout; any persisted derived artifact is made with apply_patch.
"""

import argparse
import codecs
import csv
import io
import json
import math
import struct
import sys
from pathlib import Path


class SavReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.endian = "<"

    def take(self, count):
        if count < 0 or self.pos + count > len(self.data):
            raise ValueError(f"Unexpected end of SAV at byte {self.pos}")
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result

    def integer(self):
        return struct.unpack(self.endian + "i", self.take(4))[0]

    def double(self):
        return struct.unpack(self.endian + "d", self.take(8))[0]


def decode_numeric_matrix(path):
    reader = SavReader(Path(path).read_bytes())
    signature = reader.take(4)
    if signature != b"$FL2":
        raise ValueError("Only classic SPSS $FL2 system files are supported")
    reader.take(60)  # Product string is not needed for the anonymous matrix.
    layout_bytes = reader.take(4)
    if struct.unpack("<i", layout_bytes)[0] in (2, 3):
        reader.endian = "<"
    elif struct.unpack(">i", layout_bytes)[0] in (2, 3):
        reader.endian = ">"
    else:
        raise ValueError("Unrecognized system-file layout")
    width = reader.integer()
    compression = reader.integer()
    weight_index = reader.integer()
    case_count = reader.integer()
    bias = reader.double()
    reader.take(9 + 8 + 64 + 3)  # Dates/file label are not disclosed.
    if compression not in (0, 1):
        raise ValueError("Unsupported ZSAV compression")

    variables = []
    information = []
    while True:
        record_type = reader.integer()
        if record_type == 2:
            variable_type = reader.integer()
            has_label = reader.integer()
            missing_count = reader.integer()
            print_format = reader.integer()
            write_format = reader.integer()
            short_name = reader.take(8).rstrip(b" ")
            label = b""
            if has_label:
                label_length = reader.integer()
                label = reader.take(label_length)
                reader.take((-label_length) % 4)
            missing_values = [reader.double() for _ in range(abs(missing_count))]
            variables.append({
                "short_name_bytes": short_name,
                "label_bytes": label,
                "type": variable_type,
                "missing_specification": missing_count,
                "user_missing_values": missing_values,
                "print_format": print_format,
                "write_format": write_format,
            })
        elif record_type == 3:
            label_count = reader.integer()
            for _ in range(label_count):
                reader.take(8)
                label_length = reader.take(1)[0]
                reader.take(label_length)
                reader.take((-(label_length + 1)) % 8)
        elif record_type == 4:
            associated_count = reader.integer()
            reader.take(4 * associated_count)
        elif record_type == 6:
            document_lines = reader.integer()
            reader.take(80 * document_lines)
        elif record_type == 7:
            subtype = reader.integer()
            size = reader.integer()
            count = reader.integer()
            information.append((subtype, size, count, reader.take(size * count)))
        elif record_type == 999:
            if reader.integer() != 0:
                raise ValueError("Nonzero system-file dictionary terminator")
            break
        else:
            raise ValueError(f"Unsupported dictionary record {record_type}")

    encoding = "utf-8"
    for subtype, size, count, payload in information:
        if subtype == 20:
            encoding = payload.rstrip(b"\0").decode("ascii")
    try:
        codecs.lookup(encoding)
    except LookupError:
        encoding = "utf-8"
    decode = lambda item: item.decode(encoding, errors="replace")
    long_names = {}
    for subtype, size, count, payload in information:
        if subtype == 13:
            for entry in decode(payload).rstrip("\0").split("\t"):
                if "=" in entry:
                    key, value = entry.split("=", 1)
                    long_names[key] = value
        if subtype == 16 and size == 8 and count >= 2 and case_count < 0:
            extended_counts = struct.unpack(reader.endian + "q" * count, payload)
            case_count = extended_counts[-1]

    for variable in variables:
        short_name = decode(variable.pop("short_name_bytes"))
        variable["name"] = long_names.get(short_name, short_name)
        variable["short_name"] = short_name
        variable["label"] = decode(variable.pop("label_bytes"))
    if len(variables) != width or any(v["type"] != 0 for v in variables):
        raise ValueError("The supplied input is not a purely numeric fixed-width matrix")

    target = case_count * width if case_count >= 0 else None
    cells = []
    if compression == 0:
        available = (len(reader.data) - reader.pos) // 8
        for _ in range(min(available, target) if target is not None else available):
            cells.append(reader.double())
    else:
        ended = False
        while not ended and (target is None or len(cells) < target):
            control = reader.take(8)
            for code in control:
                if code == 0:
                    continue
                if code == 252:
                    ended = True
                    break
                if code == 253:
                    value = reader.double()
                elif code == 254:
                    raise ValueError("String-blank instruction found in numeric cases")
                elif code == 255:
                    value = -sys.float_info.max
                else:
                    value = code - bias
                cells.append(value)
                if target is not None and len(cells) == target:
                    ended = True
                    break
    if target is not None and len(cells) != target:
        raise ValueError(f"Decoded {len(cells)} numeric cells; expected {target}")
    if len(cells) % width:
        raise ValueError("Case data do not form a rectangular matrix")

    rows = [cells[i:i + width] for i in range(0, len(cells), width)]
    rows = [[None if not math.isfinite(v) or v <= -1e307 else v for v in row]
            for row in rows]
    column_checks = []
    for index, variable in enumerate(variables):
        values = [row[index] for row in rows if row[index] is not None]
        column_checks.append({
            "name": variable["name"],
            "valid_numeric_count": len(values),
            "system_missing_count": len(rows) - len(values),
            "zero_count": sum(v == 0 for v in values),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
        })
    return {
        "format": "$FL2",
        "compression": compression,
        "encoding": encoding,
        "weight_index": weight_index,
        "header_case_count": case_count,
        "case_count": len(rows),
        "variable_count": width,
        "variables": variables,
        "column_checks": column_checks,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sav")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--csv", action="store_true")
    args = parser.parse_args()
    matrix = decode_numeric_matrix(args.sav)
    if args.csv:
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow([v["name"] for v in matrix["variables"]])
        writer.writerows(matrix["rows"])
    else:
        if args.summary:
            matrix.pop("rows")
        print(json.dumps(matrix, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
