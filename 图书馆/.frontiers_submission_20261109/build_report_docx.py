"""Create a Japanese Word report from the reviewed Markdown, using only stdlib."""

from datetime import datetime, timezone
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
STEM = "Frontiers_in_Sustainable_Cities_投稿検討報告書_2026-11-09"
SOURCE = ROOT / (STEM + ".md")
TARGET = ROOT / (STEM + ".docx")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
XML = "http://www.w3.org/XML/1998/namespace"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
ET.register_namespace("w", W)
ET.register_namespace("r", R)


def wtag(name):
    return "{" + W + "}" + name


def elem(parent, name, attrs=None, text=None):
    node = ET.SubElement(parent, wtag(name))
    for key, value in (attrs or {}).items():
        node.set(wtag(key), str(value))
    if text is not None:
        node.text = text
    return node


def xmlbytes(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


relationships = ET.Element("Relationships", xmlns=PKG)
for rid, kind, target in [
    ("rIdStyles", "styles", "styles.xml"),
    ("rIdSettings", "settings", "settings.xml"),
    ("rIdFooter", "footer", "footer1.xml"),
]:
    ET.SubElement(relationships, "Relationship", {
        "Id": rid, "Type": R + "/" + kind, "Target": target
    })
link_ids = {}


def link_id(url):
    if url not in link_ids:
        rid = "rIdLink" + str(len(link_ids) + 1)
        link_ids[url] = rid
        ET.SubElement(relationships, "Relationship", {
            "Id": rid, "Type": R + "/hyperlink", "Target": url,
            "TargetMode": "External"
        })
    return link_ids[url]


def run(parent, value, bold=False, link=False, size=None):
    node = elem(parent, "r")
    if bold or link or size:
        props = elem(node, "rPr")
        if bold:
            elem(props, "b")
        if link:
            elem(props, "rStyle", {"val": "Hyperlink"})
        if size:
            elem(props, "sz", {"val": size})
    txt = elem(node, "t", text=value)
    txt.set("{" + XML + "}space", "preserve")
    return node


LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def inline(parent, value, bold=False, size=None):
    at = 0
    for match in LINK.finditer(value):
        if match.start() > at:
            run(parent, value[at:match.start()], bold=bold, size=size)
        node = elem(parent, "hyperlink", {"history": "1"})
        node.set("{" + R + "}id", link_id(match.group(2)))
        run(node, match.group(1), bold=bold, link=True, size=size)
        at = match.end()
    if at < len(value):
        run(parent, value[at:], bold=bold, size=size)


def paragraph(parent, value, style="Normal", bold=False):
    p = elem(parent, "p")
    props = elem(p, "pPr")
    elem(props, "pStyle", {"val": style})
    if style in ("Title", "Heading1"):
        elem(props, "keepNext")
    inline(p, value, bold=bold)
    return p


CONTENT_WIDTH = 9638


def table(parent, rows):
    cols = len(rows[0])
    widths = [2500, CONTENT_WIDTH - 2500] if cols == 2 else [5300, 1500, 1500, 1338]
    assert sum(widths) == CONTENT_WIDTH and len(widths) == cols
    tbl = elem(parent, "tbl")
    props = elem(tbl, "tblPr")
    elem(props, "tblW", {"w": CONTENT_WIDTH, "type": "dxa"})
    elem(props, "tblLayout", {"type": "fixed"})
    borders = elem(props, "tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        elem(borders, side, {"val": "single", "sz": "4", "color": "BCC8D1"})
    margins = elem(props, "tblCellMar")
    for side in ("top", "left", "bottom", "right"):
        elem(margins, side, {"w": "90", "type": "dxa"})
    grid = elem(tbl, "tblGrid")
    for width in widths:
        elem(grid, "gridCol", {"w": width})
    for i, row in enumerate(rows):
        assert len(row) == cols
        tr = elem(tbl, "tr")
        tr_props = elem(tr, "trPr")
        elem(tr_props, "cantSplit")
        if i == 0:
            elem(tr_props, "tblHeader")
        for j, value in enumerate(row):
            cell = elem(tr, "tc")
            cp = elem(cell, "tcPr")
            elem(cp, "tcW", {"w": widths[j], "type": "dxa"})
            elem(cp, "vAlign", {"val": "center" if i == 0 else "top"})
            if i == 0:
                elem(cp, "shd", {"fill": "E7EEF4", "val": "clear"})
            elif i % 2 == 0:
                elem(cp, "shd", {"fill": "F6F8FA", "val": "clear"})
            p = elem(cell, "p")
            pp = elem(p, "pPr")
            elem(pp, "pStyle", {"val": "TableText"})
            if cols == 4 and j:
                elem(pp, "jc", {"val": "center"})
            inline(p, value, bold=i == 0)
    paragraph(parent, "", style="TableGap")


styles = ET.Element(wtag("styles"))
defaults = elem(styles, "docDefaults")
rp = elem(elem(defaults, "rPrDefault"), "rPr")
elem(rp, "rFonts", {"ascii": "Calibri", "hAnsi": "Calibri", "eastAsia": "Yu Mincho"})
elem(rp, "sz", {"val": "21"})
elem(rp, "lang", {"val": "en-US", "eastAsia": "ja-JP"})
pp = elem(elem(defaults, "pPrDefault"), "pPr")
elem(pp, "spacing", {"after": "130", "line": "290", "lineRule": "auto"})
elem(pp, "widowControl")


def style(sid, name, size, before=0, after=130, bold=False, color="202E3A", line=290):
    st = elem(styles, "style", {"type": "paragraph", "styleId": sid})
    if sid == "Normal":
        st.set(wtag("default"), "1")
    elem(st, "name", {"val": name})
    if sid != "Normal":
        elem(st, "basedOn", {"val": "Normal"})
    pp = elem(st, "pPr")
    elem(pp, "spacing", {"before": before, "after": after, "line": line, "lineRule": "auto"})
    if sid == "Heading1":
        elem(pp, "keepNext")
        elem(pp, "outlineLvl", {"val": "0"})
    rp = elem(st, "rPr")
    elem(rp, "sz", {"val": size})
    elem(rp, "color", {"val": color})
    if bold:
        elem(rp, "b")
        elem(rp, "rFonts", {"ascii": "Calibri", "hAnsi": "Calibri", "eastAsia": "Yu Gothic"})


style("Normal", "Normal", 21)
style("Title", "Title", 32, after=200, bold=True, color="163D59")
style("Heading1", "Heading 1", 24, before=240, after=100, bold=True, color="163D59")
style("TableText", "Table Text", 19, after=30, line=265)
style("TableGap", "Table Gap", 6, after=0, line=100)
style("Footer", "Footer", 17, after=0, color="5D6872")
st = elem(styles, "style", {"type": "character", "styleId": "Hyperlink"})
elem(st, "name", {"val": "Hyperlink"})
rp = elem(st, "rPr")
elem(rp, "color", {"val": "0563A5"})
elem(rp, "u", {"val": "single"})

doc = ET.Element(wtag("document"))
body = elem(doc, "body")
lines = SOURCE.read_text(encoding="utf-8-sig").splitlines()
expected_paragraphs = []
expected_tables = 0
i = 0
while i < len(lines):
    value = lines[i].strip()
    if not value:
        i += 1
        continue
    if value.startswith("|"):
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            row = [x.strip() for x in lines[i].strip().strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", x) for x in row):
                rows.append(row)
                expected_paragraphs.extend(LINK.sub(r"\1", x) for x in row)
            i += 1
        table(body, rows)
        expected_tables += 1
        continue
    is_heading = value.startswith("**") and value.endswith("**")
    if is_heading:
        value = value[2:-2]
    expected_paragraphs.append(LINK.sub(r"\1", value))
    paragraph(body, value, style=("Title" if i == 0 else "Heading1") if is_heading else "Normal")
    i += 1

section = elem(body, "sectPr")
footer_ref = elem(section, "footerReference", {"type": "default"})
footer_ref.set("{" + R + "}id", "rIdFooter")
elem(section, "pgSz", {"w": "11906", "h": "16838"})
elem(section, "pgMar", {"top": "1134", "right": "1134", "bottom": "1134", "left": "1134", "header": "600", "footer": "600", "gutter": "0"})

footer = ET.Element(wtag("ftr"))
p = paragraph(footer, "Frontiers in Sustainable Cities｜投稿検討　　", "Footer")
elem(p.find(wtag("pPr")), "jc", {"val": "right"})
field = elem(p, "fldSimple", {"instr": " PAGE "})
run(field, "1")

settings = ET.Element(wtag("settings"))
elem(settings, "zoom", {"percent": "100"})
elem(settings, "defaultTabStop", {"val": "420"})
elem(settings, "updateFields", {"val": "true"})

types = ET.Element("Types", xmlns=CT)
for ext, content in [("rels", "application/vnd.openxmlformats-package.relationships+xml"), ("xml", "application/xml")]:
    ET.SubElement(types, "Default", {"Extension": ext, "ContentType": content})
for part, content in [
    ("/word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"),
    ("/word/styles.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"),
    ("/word/settings.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"),
    ("/word/footer1.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"),
    ("/docProps/core.xml", "application/vnd.openxmlformats-package.core-properties+xml"),
]:
    ET.SubElement(types, "Override", {"PartName": part, "ContentType": content})

package_rels = ET.Element("Relationships", xmlns=PKG)
ET.SubElement(package_rels, "Relationship", {"Id": "rId1", "Type": R + "/officeDocument", "Target": "word/document.xml"})
ET.SubElement(package_rels, "Relationship", {"Id": "rId2", "Type": PKG + "/metadata/core-properties", "Target": "docProps/core.xml"})
CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DT = "http://purl.org/dc/terms/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("cp", CP)
ET.register_namespace("dc", DC)
ET.register_namespace("dcterms", DT)
ET.register_namespace("xsi", XSI)
core = ET.Element("{" + CP + "}coreProperties")
ET.SubElement(core, "{" + DC + "}title").text = "Frontiers in Sustainable Cities 投稿検討報告書"
ET.SubElement(core, "{" + DC + "}subject").text = "投稿適合性・記事種別・出版費用・投稿から受理までの期間"
ET.SubElement(core, "{" + DC + "}language").text = "ja-JP"
created = ET.SubElement(core, "{" + DT + "}created", {"{" + XSI + "}type": "dcterms:W3CDTF"})
created.text = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

parts = {
    "[Content_Types].xml": types,
    "_rels/.rels": package_rels,
    "word/document.xml": doc,
    "word/_rels/document.xml.rels": relationships,
    "word/styles.xml": styles,
    "word/settings.xml": settings,
    "word/footer1.xml": footer,
    "docProps/core.xml": core,
}
with zipfile.ZipFile(TARGET, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for name, content in parts.items():
        archive.writestr(name, xmlbytes(content))

# Read back the final artifact and compare every body paragraph with Markdown.
with zipfile.ZipFile(TARGET) as archive:
    assert archive.testzip() is None
    for name in archive.namelist():
        ET.fromstring(archive.read(name))
    restored = ET.fromstring(archive.read("word/document.xml"))
    actual = []
    for p in restored.iter(wtag("p")):
        value = "".join(t.text or "" for t in p.iter(wtag("t")))
        if value:
            actual.append(value)
    assert actual == expected_paragraphs, "DOCX content differs from reviewed Markdown"
    assert len(list(restored.iter(wtag("tbl")))) == expected_tables
    assert all("??" not in value for value in actual)
    assert "CHF 2,195" in "".join(actual)
    assert "標本中央値59日" in "".join(actual)
    assert expected_tables == 5

print("DOCX created and verified")
print("File:", TARGET.name)
print("Bytes:", TARGET.stat().st_size)
print("Body paragraphs/cells:", len(actual))
print("Tables:", expected_tables)
print("Unique official hyperlinks:", len(link_ids))
