# -*- coding: utf-8 -*-
"""
図1 本研究の分析枠組み  —  1スライド（16:9, 13.333 x 7.5 in）
ネイティブ図形（矩形＋細実線矢印）で作図。後から PowerPoint で編集可能。
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
from lxml import etree
import copy

# ---------------- palette ----------------
INK      = RGBColor(0x1F, 0x29, 0x33)
GRAY     = RGBColor(0x5B, 0x67, 0x70)
GRAY_L   = RGBColor(0x8D, 0x99, 0xA6)
RULE     = RGBColor(0xC9, 0xD1, 0xD9)
BORDER   = RGBColor(0xB9, 0xC4, 0xCE)
BLUE     = RGBColor(0x2F, 0x5D, 0x9E)
BLUE_T   = RGBColor(0xED, 0xF1, 0xF8)
TEAL     = RGBColor(0x1F, 0x7A, 0x74)
TEAL_T   = RGBColor(0xEE, 0xF4, 0xF3)
NAVY     = RGBColor(0x1B, 0x3A, 0x57)
PALE     = RGBColor(0xF4, 0xF6, 0xF8)
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
ARROW    = RGBColor(0x5B, 0x67, 0x70)

FONT = "Yu Gothic"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])
shapes = slide.shapes


# ---------------- helpers ----------------
def _set_font(run, name=FONT):
    run.font.name = name
    rPr = run.font._rPr
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = etree.SubElement(rPr, qn(tag))
        el.set("typeface", name)


def rect(x, y, w, h, fill=None, line=None, line_w=0.9, shape=MSO_SHAPE.RECTANGLE):
    shp = shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.shadow.inherit = False
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line
        shp.line.width = Pt(line_w)
    return shp


def text(x, y, w, h, paras, anchor=MSO_ANCHOR.MIDDLE, margins=(0.10, 0.04, 0.10, 0.04)):
    tb = shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = [Inches(m) for m in margins]
    first = True
    for p in paras:
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        para.alignment = p.get("align", PP_ALIGN.CENTER)
        if p.get("line_spacing"):
            para.line_spacing = p["line_spacing"]
        if p.get("space_before") is not None:
            para.space_before = Pt(p["space_before"])
        if p.get("space_after") is not None:
            para.space_after = Pt(p["space_after"])
        run = para.add_run()
        run.text = p["t"]
        run.font.size = Pt(p.get("size", 9.5))
        run.font.bold = p.get("bold", False)
        run.font.color.rgb = p.get("color", INK)
        _set_font(run)
    return tb


def arrow(x1, y1, x2, y2, head=True, width=1.0, color=ARROW):
    conn = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(width)
    if head:
        ln = conn.line._get_or_add_ln()
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "sm")
        tail.set("len", "sm")
    return conn


def card(x, y, w, h, band, band_h, band_text, body, body_paras,
         body_fill=WHITE, border=None, band_size=10.5, inset=0.22, top_pad=0.06,
         body_anchor=MSO_ANCHOR.MIDDLE):
    """見出し帯つきの矩形（見出し＝白抜き文字）"""
    border = border or band
    rect(x, y, w, h, fill=body_fill, line=None)                      # 本体地
    rect(x, y, w, band_h, fill=band, line=None)                       # 見出し帯
    text(x, y, w, band_h, [dict(t=band_text, size=band_size, bold=True,
                                color=WHITE, align=PP_ALIGN.LEFT)],
         margins=(inset, 0.01, inset, 0.01))
    outline = rect(x, y, w, h, fill=None, line=border, line_w=1.0)    # 枠線（最前面）
    outline.line.width = Pt(1.0)
    if body_paras:
        text(x, y + band_h + top_pad, w, h - band_h - top_pad - 0.04, body_paras,
             anchor=body_anchor, margins=(inset, 0.0, inset - 0.06, 0.02))


# ---------------- header ----------------
rect(0, 0, 0.16, 7.5, fill=BLUE)                                      # 左の帯
text(0.60, 0.22, 12.13, 0.62,
     [dict(t="図1　本研究の分析枠組み", size=22, bold=True, color=INK, align=PP_ALIGN.LEFT)])
rect(0.60, 1.00, 12.13, 0.02, fill=RULE)
rect(0.60, 0.975, 1.60, 0.05, fill=BLUE)

# ---------------- 1. 研究目的 ----------------
AX, AY, AW, AH = 3.30, 1.12, 6.72, 0.74
rect(AX, AY, AW, AH, fill=WHITE, line=BORDER, line_w=0.9)
text(AX, AY, AW, AH, [
    dict(t="【研究目的】", size=10.2, bold=True, color=BLUE, space_after=2),
    dict(t="自然再生と公園利用の調整に関わる", size=9.8, color=INK),
    dict(t="管理の実態・課題と関連条件を把握する", size=9.8, color=INK),
])

# ---------------- 2. 質問紙調査 ----------------
BX, BY, BW, BH = 3.06, 2.02, 7.20, 0.92
rect(BX, BY, BW, BH, fill=WHITE, line=BORDER, line_w=0.9)
text(BX, BY, BW, BH, [
    dict(t="【質問紙調査：日本の39公園の管理者】", size=10.6, bold=True, color=BLUE, space_after=6),
    dict(t="・保全・利用・調整の取組と課題（問2・4・5・9）", size=9.0, color=INK),
    dict(t="・主体の関与・経費（問3・6）", size=9.0, color=INK),
    dict(t="・要望・苦情と対応（問7・8）", size=9.0, color=INK),
])

# ---------------- 3. 研究課題Ⅰ（左） ----------------
CX, CY, CW, CH = 0.60, 3.18, 5.70, 1.90
card(CX, CY, CW, CH, TEAL, 0.38, "【研究課題Ⅰ】管理の実態・課題の把握",
     None, [], body_fill=TEAL_T)

text(CX, 3.78, CW, 0.26,
     [dict(t="記述集計（問2～5）", size=9.2, bold=True, color=TEAL)], anchor=MSO_ANCHOR.MIDDLE)

for _col, _x in ((0, 2.03), (1, 3.85)):
    for _row, _y in ((0, 4.18), (1, 4.60)):
        text(_x, _y, 1.70, 0.28,
             [dict(t=[["・取組の実施状況", "・未実施の内訳"],
                      ["・課題認識", "・主体の関与"]][_row][_col],
                   size=10.4, color=INK, align=PP_ALIGN.LEFT)],
             anchor=MSO_ANCHOR.MIDDLE, margins=(0.0, 0.0, 0.0, 0.0))

# ---------------- 4. 指標の構成（右）＋資料小枠 ----------------
DX, DY, DW, DH = 9.58, 3.18, 3.17, 0.98
rect(DX, DY, DW, DH, fill=BLUE_T, line=BLUE, line_w=1.0)
text(DX, DY, DW, DH, [
    dict(t="【指標の構成】", size=10, bold=True, color=BLUE, space_after=2),
    dict(t="表1・表2の指標", size=9, color=INK),
])

EX, EW = 6.75, 2.45
rect(EX, 3.18, EW, 0.42, fill=PALE, line=GRAY_L, line_w=0.75)
text(EX, 3.18, EW, 0.42, [dict(t="公園内外の緑化状況（NDVI）", size=8.8, color=INK)],
     margins=(0.06, 0.01, 0.06, 0.01))

rect(EX, 3.64, EW, 0.50, fill=PALE, line=GRAY_L, line_w=0.75)
text(EX, 3.64, EW, 0.50, [
    dict(t="問5の項目構成：", size=8.8, color=INK),
    dict(t="EFAによる補助的検討", size=8.8, color=INK),
], margins=(0.06, 0.01, 0.06, 0.01))

# ---------------- 5. 研究課題Ⅱ（右下） ----------------
GX, GY, GW, GH = 6.75, 4.40, 6.00, 1.28
card(GX, GY, GW, GH, BLUE, 0.36, "【研究課題Ⅱ】管理行動の関連条件の検討",
     None, [
         dict(t="探索的SEM（図2）", size=9.6, bold=True, color=BLUE,
              align=PP_ALIGN.LEFT, space_after=5),
         dict(t="説明側：社会的規範／利用者態度／環境的質", size=9.2, color=INK, align=PP_ALIGN.LEFT),
         dict(t="行動側：環境重視的行動／両立的行動／利用者重視的行動", size=9.2, color=INK,
              align=PP_ALIGN.LEFT, space_before=3),
     ], body_fill=BLUE_T)

# ---------------- 6. 結果の統合・考察 ----------------
HX, HY, HW, HH = 2.36, 5.92, 8.60, 0.62
rect(HX, HY, HW, HH, fill=NAVY, line=None)
text(HX, HY, HW, HH, [
    dict(t="【結果の統合・考察】両立に向けた管理課題と関連条件の整理", size=10.5, bold=True, color=WHITE),
    dict(t="―実施移行・適用判断・継続管理―", size=9.5, color=RULE, space_before=2),
])

# ---------------- arrows ----------------
arrow(6.66, 1.86, 6.66, 2.02)                       # 研究目的 → 質問紙調査
arrow(6.66, 2.94, 6.66, 3.02, head=False)           # 幹
arrow(3.45, 3.02, 11.165, 3.02, head=False)         # 分岐バス
arrow(3.45, 3.02, 3.45, 3.18)                       # → 研究課題Ⅰ
arrow(11.165, 3.02, 11.165, 3.18)                   # → 指標の構成
arrow(9.20, 3.39, 9.58, 3.39)                       # NDVI → 指標の構成
arrow(9.20, 3.89, 9.58, 3.89)                       # EFA → 指標の構成
arrow(11.165, 4.16, 11.165, 4.26, head=False)       # 指標 → 課題Ⅱ（折れ）
arrow(11.165, 4.26, 9.75, 4.26, head=False)
arrow(9.75, 4.26, 9.75, 4.40)                       # → 研究課題Ⅱ
arrow(3.45, 5.08, 3.45, 5.80, head=False)           # 課題Ⅰ → 統合バス
arrow(9.75, 5.68, 9.75, 5.80, head=False)           # 課題Ⅱ → 統合バス
arrow(3.45, 5.80, 9.75, 5.80, head=False)           # 統合バス
arrow(6.66, 5.80, 6.66, 5.92)                       # → 結果の統合

# ---------------- 図注 ----------------
text(0.60, 6.62, 12.13, 0.62, [
    dict(t="図注：矢印は資料と分析の対応を示し、因果関係や管理の時間的な移行を表さない。"
           "探索的因子分析は問5の指標構成の補助的検討に用いた。",
         size=8.2, color=GRAY, align=PP_ALIGN.LEFT, line_spacing=1.28, space_after=3),
    dict(t="各指標の定義及び算出方法は表1・表2に、SEMの個別のパス及び推定結果は図2に示す。",
         size=8.2, color=GRAY, align=PP_ALIGN.LEFT, line_spacing=1.28),
], anchor=MSO_ANCHOR.TOP, margins=(0.0, 0.0, 0.0, 0.0))

# ---------------- 発表用ノート ----------------
slide.notes_slide.notes_text_frame.text = (
    "図1は、質問紙調査から二つの分析課題へ進み、最後に統合する構成を示す。"
    "左の支路は記述集計（問2～5）による実態把握、右の支路は表1・表2の指標構成を経て、"
    "探索的SEM（図2）による関連条件の検討である。"
    "NDVIと問5のEFAは指標構成を補助する資料であり、矢印は資料と分析の対応を示すもので、"
    "因果関係や管理の時間的な移行を表すものではない。"
)

out = r"C:\Users\happyelements\Desktop\Paper\図1_本研究の分析枠組み.pptx"
prs.save(out)
print("saved:", out, "shapes:", len(shapes))
