# -*- coding: utf-8 -*-
"""Build one-slide PPTX: 図1 本研究の分析枠組み (Japanese, 16:9)."""
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE
from pptx.oxml.ns import qn
from PIL import ImageFont

FONT = "Yu Gothic"

_FR = ImageFont.truetype("C:/Windows/Fonts/YuGothR.ttc", 100)
_FB = ImageFont.truetype("C:/Windows/Fonts/YuGothB.ttc", 100)


def text_width(text, size_pt, bold=False):
    """Approximate rendered width in points."""
    return (_FB if bold else _FR).getlength(text) / 100.0 * size_pt

NAVY = RGBColor(0x1E, 0x35, 0x50)
INK = RGBColor(0x23, 0x30, 0x3C)
ACCENT = RGBColor(0x2C, 0x5F, 0x8A)
MUTED = RGBColor(0x5F, 0x6B, 0x78)
BORDER = RGBColor(0x5A, 0x76, 0x91)
BORDER_SOFT = RGBColor(0x8F, 0xA7, 0xBE)
AUX_LINE = RGBColor(0xB0, 0x8A, 0x52)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FILL_PURPOSE = RGBColor(0xE3, 0xED, 0xF7)
FILL_DATA = RGBColor(0xF1, 0xF5, 0xF9)
FILL_BRANCH = RGBColor(0xFF, 0xFF, 0xFF)
FILL_AUX = RGBColor(0xFC, 0xF5, 0xE8)
FILL_RESULT = RGBColor(0xE1, 0xEA, 0xF3)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])


def style_run(run, size, bold=False, color=INK):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", FONT)
    rPr.set("lang", "ja-JP")


def add_para(tf, first, text, size, bold=False, color=INK,
             align=PP_ALIGN.CENTER, line=None, before=0, indent=0.0):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    if line:
        p.line_spacing = Pt(line)
    if before:
        p.space_before = Pt(before)
    p.space_after = Pt(0)
    if indent:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(Inches(indent))))
        pPr.set("indent", "0")
    r = p.add_run()
    r.text = text
    style_run(r, size, bold, color)
    return p


def box(x, y, w, h, fill, line_color, paras, radius=0.05,
        line_w=1.25, dash=None):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line_color
    shp.line.width = Pt(line_w)
    if dash is not None:
        shp.line.dash_style = dash
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.10)
    tf.margin_right = Inches(0.10)
    tf.margin_top = Inches(0.06)
    tf.margin_bottom = Inches(0.06)
    built = []
    for i, (text, kw) in enumerate(paras):
        kw = dict(kw)
        kw.pop("grp", None)
        built.append((text, paras[i][1], add_para(tf, i == 0, text, **kw)))
    # paragraphs sharing a group name are left-aligned and centred as one block
    groups = {}
    for i, (text, kw, p) in enumerate(built):
        g = kw.get("grp")
        if g:
            groups.setdefault(g, []).append((text, kw, p))
    for items in groups.values():
        max_w = max(text_width(t, kw["size"], kw.get("bold", False))
                    for t, kw, _ in items) / 72.0
        marL = max(0.02, (w - 0.20 - max_w) / 2)
        for _, _, p in items:
            p.alignment = PP_ALIGN.LEFT
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Inches(marL))))
            pPr.set("indent", "0")
    return shp


def textbox(x, y, w, h, text, size, bold=False, color=INK,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line=None):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0)
    tf.margin_right = Inches(0)
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    add_para(tf, True, text, size, bold, color, align, line)
    return tb


def arrow(x1, y1, x2, y2, head=True, width=1.1, color=BORDER):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,
                                   Inches(x1), Inches(y1),
                                   Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    c.shadow.inherit = False
    ln = c.line._get_or_add_ln()
    ln.set("cap", "rnd")
    if head:
        te = etree.SubElement(ln, qn("a:tailEnd"))
        te.set("type", "triangle")
        te.set("w", "med")
        te.set("len", "med")
    return c


# ---------------------------------------------------------------- title
textbox(0.55, 0.16, 9.6, 0.46, "図1\u3000本研究の分析枠組み", 21, True, NAVY,
        align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.MIDDLE)
rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.55),
                                  Inches(0.70), Inches(12.95), Inches(0.70))
rule.line.color.rgb = RGBColor(0xC9, 0xD4, 0xDE)
rule.line.width = Pt(0.75)

# ---------------------------------------------------------------- 1 研究目的
box(2.35, 0.86, 5.70, 0.84, FILL_PURPOSE, BORDER_SOFT, [
    ("研究目的", dict(size=9.5, bold=True, color=ACCENT, line=12)),
    ("自然再生と公園利用の調整に関わる", dict(size=11.5, color=NAVY, line=16)),
    ("管理の実態・課題と関連条件を把握する", dict(size=11.5, bold=True, color=NAVY, line=16)),
], radius=0.10)

arrow(5.20, 1.70, 5.20, 1.83)

# ---------------------------------------------------------------- 2 調査資料
box(1.10, 1.86, 8.15, 1.50, FILL_DATA, BORDER_SOFT, [
    ("調査資料", dict(size=9.5, bold=True, color=ACCENT, line=12)),
    ("自然再生に取り組む39公園の管理者への質問紙調査", dict(size=11, bold=True, color=NAVY, line=16)),
    ("分析単位：公園", dict(size=9, color=MUTED, line=13)),
    ("保全・利用・調整の取組と課題（問2・4・5・9）", dict(size=9.5, color=INK, line=13.5, before=5, grp="dom")),
    ("主体の関与・経費（問3・6）", dict(size=9.5, color=INK, line=13.5, grp="dom")),
    ("要望・苦情と対応（問7・8）", dict(size=9.5, color=INK, line=13.5, grp="dom")),
], radius=0.06)

arrow(2.95, 3.36, 2.62, 3.58)
arrow(7.45, 3.36, 7.72, 3.58)

# ---------------------------------------------------------------- 3 研究課題Ⅰ
box(0.55, 3.60, 4.10, 2.32, FILL_BRANCH, BORDER, [
    ("研究課題Ⅰ", dict(size=9.5, bold=True, color=ACCENT, line=12)),
    ("管理の実態・課題の把握", dict(size=16, bold=True, color=NAVY, line=22)),
    ("記述集計（問2～5）", dict(size=11.5, bold=True, color=NAVY, line=16, before=16)),
    ("・取組の実施状況／未実施の内訳", dict(size=11, color=INK, line=17, before=6, grp="items")),
    ("・課題認識／主体の関与", dict(size=11, color=INK, line=17, before=2, grp="items")),
], radius=0.05)

# ---------------------------------------------------------------- 4 研究課題Ⅱ
box(5.55, 3.60, 4.35, 2.32, FILL_BRANCH, BORDER, [
    ("研究課題Ⅱ", dict(size=9.5, bold=True, color=ACCENT, line=12)),
    ("管理行動の関連条件の検討", dict(size=14, bold=True, color=NAVY, line=19)),
    ("指標の構成（表1・表2）", dict(size=11, color=INK, line=15, before=8)),
    ("↓", dict(size=10, color=MUTED, line=13)),
    ("探索的SEM（図2）", dict(size=11.5, bold=True, color=NAVY, line=15)),
    ("説明側：社会的規範・利用者態度・環境的質", dict(size=10, color=INK, line=14.5, before=9)),
    ("行動側：環境重視的行動・両立的行動・利用者重視的行動", dict(size=10, color=INK, line=14.5, before=2)),
], radius=0.05)

# ---------------------------------------------------------------- 5 aux boxes
box(10.30, 3.86, 2.10, 0.92, FILL_AUX, AUX_LINE, [
    ("公園内外の緑化状況", dict(size=9.5, bold=True, color=NAVY, line=13)),
    ("（NDVI）", dict(size=9, color=MUTED, line=12)),
], radius=0.09, line_w=0.9, dash=MSO_LINE.DASH)

box(10.30, 4.94, 2.65, 0.96, FILL_AUX, AUX_LINE, [
    ("問5の項目構成の補助的検討", dict(size=9.5, color=NAVY, line=13)),
    ("（探索的因子分析）", dict(size=8.5, color=MUTED, line=12)),
], radius=0.09, line_w=0.9, dash=MSO_LINE.DASH)

# NDVI -> 指標の構成
arrow(10.30, 4.50, 9.92, 4.50)
# EFA -> 指標の構成 (elbow through the gap)
arrow(10.30, 5.40, 10.08, 5.40, head=False)
arrow(10.08, 5.40, 10.08, 4.64, head=False)
arrow(10.08, 4.64, 9.92, 4.64)
# 調査資料(問5) -> EFA, routed along the right margin
arrow(9.25, 2.58, 12.66, 2.58, head=False)
arrow(12.66, 2.58, 12.66, 4.92)
textbox(9.42, 2.28, 0.60, 0.24, "問5", 8, False, MUTED, align=PP_ALIGN.CENTER)

# ---------------------------------------------------------------- 6 結果の統合
box(1.10, 6.10, 11.30, 0.88, FILL_RESULT, BORDER, [
    ("結果の統合・考察", dict(size=12.5, bold=True, color=NAVY, line=17)),
    ("両立に向けた管理課題と関連条件の整理", dict(size=11, color=INK, line=15, before=2)),
    ("―実施移行・適用判断・継続管理―", dict(size=9.5, color=MUTED, line=13)),
], radius=0.10)

arrow(3.40, 5.92, 3.40, 6.08)
arrow(9.00, 5.92, 9.00, 6.08)

# ---------------------------------------------------------------- caption
textbox(0.55, 7.06, 12.25, 0.38,
        "図注：矢印は資料と分析の対応を示し、因果関係や管理の時間的な移行を表さない。"
        "探索的因子分析は問5の指標構成の補助的検討に用いた。"
        "各指標の定義及び算出方法は表1・表2に、SEMの個別のパス及び推定結果は図2に示す。",
        8.5, False, MUTED, align=PP_ALIGN.LEFT, line=11.5)

prs.save("2 図1_本研究の分析枠組み.pptx")
print("saved")
