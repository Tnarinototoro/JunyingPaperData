# -*- coding: utf-8 -*-
"""博士汇报PPT（26页）生成脚本：正文逐字取自用户给定的【PPT正文】。"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.dml import MSO_LINE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.oxml.ns import qn
from lxml import etree
from PIL import ImageFont

sys.stdout.reconfigure(encoding="utf-8")
FONT = "Yu Gothic"
FR = ImageFont.truetype(r"C:\Windows\Fonts\YuGothR.ttc", 100)
FB = ImageFont.truetype(r"C:\Windows\Fonts\YuGothB.ttc", 100)
_cw = {}


def cw(c, b):
    k = (c, b)
    if k not in _cw:
        _cw[k] = (FB if b else FR).getlength(c) / 100.0
    return _cw[k]


W, H = 13.333, 7.5
LM = 0.6
CW = 12.13
LH = 1.32  # 行高 = size*LH（固定行距）

NAVY = "1B3A57"
TEAL = "1F7A74"   # 研究Ⅰ
BLUE = "2F5D9E"   # 研究Ⅱ
AMBER = "B8741A"  # 研究Ⅲ
GREEN = "2E7D5B"  # 環境重視
ORANGE = "C26A1B"  # 利用者重視
GREY = "5B6770"
TXT = "1F2933"
WARN = "8A4B2A"


def rgb(h):
    return RGBColor.from_string(h)


def tint(h, f=0.90):
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * f); g = int(g + (255 - g) * f); b = int(b + (255 - b) * f)
    return "%02X%02X%02X" % (r, g, b)


class P:
    def __init__(self, *runs, scale=1.0, bold=False, color=None, before=None, align=None):
        self.runs = []
        for r in runs:
            if isinstance(r, str):
                self.runs.append((r, {}))
            else:
                self.runs.append(r)
        self.scale = scale
        self.bold = bold
        self.color = color
        self.before = before
        self.align = align

    @property
    def text(self):
        return "".join(t for t, _ in self.runs)

    def hang(self):
        return self.text.startswith("・")


def para_lines(p, size, width):
    s = size * p.scale
    chars = []
    for t, o in p.runs:
        b = o.get("bold", p.bold)
        for c in t:
            chars.append((c, b))
    hang = s / 72.0 if p.hang() else 0.0
    lines, x, avail = 1, 0.0, width
    for c, b in chars:
        w = cw(c, b) * s / 72.0
        if x + w > avail + 1e-6:
            lines += 1
            x = 0.0
            avail = width - hang
        x += w
    return lines


def need_height(paras, size, width):
    total = 0.0
    for i, p in enumerate(paras):
        s = size * p.scale
        n = para_lines(p, size, width * 0.955)
        total += n * s * LH / 72.0
        if i > 0:
            bf = p.before if p.before is not None else 0.32
            total += bf * s / 72.0
    return total


def fit_size(paras, width, height, maxs=20, mins=10.5):
    s = maxs
    while s >= mins:
        if need_height(paras, s, width) <= height:
            return s
        s -= 0.5
    print("  !! 无法放下，使用最小字号", mins, paras[0].text[:20])
    return mins


def write_paras(tf, paras, size):
    tf.word_wrap = True
    first = True
    for p in paras:
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        s = size * p.scale
        para.line_spacing = Pt(s * LH)
        if not first:
            bf = p.before if p.before is not None else 0.32
            para.space_before = Pt(bf * s)
        else:
            para.space_before = Pt(0)
        para.space_after = Pt(0)
        if p.align:
            para.alignment = p.align
        if p.hang():
            pPr = para._p.get_or_add_pPr()
            pPr.set("marL", str(int(Pt(s))))
            pPr.set("indent", str(-int(Pt(s))))
        for t, o in p.runs:
            r = para.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(s)
            f.bold = o.get("bold", p.bold)
            f.color.rgb = rgb(o.get("color", p.color or TXT))
            rPr = r._r.get_or_add_rPr()
            for tag in ("a:ea", "a:cs"):
                el = rPr.find(qn(tag))
                if el is None:
                    el = etree.SubElement(rPr, qn(tag))
                el.set("typeface", FONT)
        first = False


def B(t, color=None):
    d = {"bold": True}
    if color:
        d["color"] = color
    return (t, d)


def set_shape_fill(shape, fill, line=None):
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False


def rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    set_shape_fill(s, fill, line)
    if name:
        s.name = name
    return s


def textbox(slide, x, y, w, h, paras, size=18, mins=10.5, anchor="top", mx=0.05, my=0.03):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.margin_left = tf.margin_right = Inches(mx)
    tf.margin_top = tf.margin_bottom = Inches(my)
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE}[anchor]
    s = fit_size(paras, w - 2 * mx, h - 2 * my, size, mins)
    write_paras(tf, paras, s)
    return tb


def card_spec(x, y, w, h, paras, color, heading=None, fill=None, accent=True, bold_all=False, anchor="top"):
    ps = list(paras)
    if heading:
        ps = [P(heading, bold=True, color=color)] + ps
    return dict(x=x, y=y, w=w, h=h, paras=ps, color=color, fill=fill, accent=accent, anchor=anchor)


ML, MR, MT, MB = 0.2, 0.12, 0.09, 0.07


def draw_cards(slide, specs, maxs=20, mins=10.5, uniform=True):
    sizes = []
    for sp in specs:
        tw = sp["w"] - ML - MR - (0.07 if sp["accent"] else 0)
        th = sp["h"] - MT - MB
        sizes.append(fit_size(sp["paras"], tw, th, maxs, mins))
    if uniform:
        m = min(sizes)
        sizes = [m] * len(sizes)
    for sp, s in zip(specs, sizes):
        fill = sp["fill"] or tint(sp["color"], 0.92)
        r = rect(slide, sp["x"], sp["y"], sp["w"], sp["h"], fill=fill)
        if sp["accent"]:
            rect(slide, sp["x"], sp["y"], 0.07, sp["h"], fill=sp["color"])
        tf = r.text_frame
        tf.margin_left = Inches(ML + (0.07 if sp["accent"] else 0))
        tf.margin_right = Inches(MR)
        tf.margin_top = Inches(MT)
        tf.margin_bottom = Inches(MB)
        tf.vertical_anchor = MSO_ANCHOR.TOP if sp["anchor"] == "top" else MSO_ANCHOR.MIDDLE
        write_paras(tf, sp["paras"], s)
    return sizes[0]


def card(slide, *a, maxs=20, mins=10.5, **k):
    return draw_cards(slide, [card_spec(*a, **k)], maxs, mins)


def figure_placeholder(slide, x, y, w, h, label, color):
    s = rect(slide, x, y, w, h, fill="F4F6F8", line="8D99A6", name="原図挿入位置_" + label[:12])
    s.line.dash_style = MSO_LINE.DASH
    s.line.width = Pt(1.5)
    tf = s.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    ps = [P("［原図挿入位置］", color=GREY, scale=0.8, align=PP_ALIGN.CENTER),
          P(label, color=GREY, bold=True, align=PP_ALIGN.CENTER, before=0.4)]
    sz = fit_size(ps, w - 0.6, h - 0.3, 18, 10)
    tf.margin_left = tf.margin_right = Inches(0.3)
    write_paras(tf, ps, sz)
    return s


def arrow(slide, x, y, w, h, color, kind="right"):
    sh = {"right": MSO_SHAPE.RIGHT_ARROW, "down": MSO_SHAPE.DOWN_ARROW}[kind]
    return rect(slide, x, y, w, h, fill=color, shape=sh)


# ---------------------------------------------------------------- deck
prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]
TOTAL = 26


def new_slide(no, title, color, notes):
    s = prs.slides.add_slide(BLANK)
    rect(s, 0, 0, 0.16, H, fill=color)
    # title
    for sz in (26, 24, 22, 20):
        n = para_lines(P(title, bold=True), sz, (CW - 0.1) * 0.955)
        if n == 1:
            break
    tb = textbox(s, LM, 0.26, CW, 0.7, [P(title, bold=True, color=color)], size=sz, mins=sz, anchor="middle")
    tb.name = "Title"
    rect(s, LM, 1.0, CW, 0.02, fill="C9D1D9")
    rect(s, LM, 0.985, 1.4, 0.05, fill=color)
    textbox(s, 11.6, 7.1, 1.13, 0.28, [P("%d / %d" % (no, TOTAL), color="8D99A6", align=PP_ALIGN.RIGHT)], size=10, mins=10)
    s.notes_slide.notes_text_frame.text = notes
    return s


# ================= 01 表題
s = prs.slides.add_slide(BLANK)
bg = s.background.fill
bg.solid(); bg.fore_color.rgb = rgb(NAVY)
rect(s, 0.9, 2.35, 0.09, 2.2, fill="E0B04A")
textbox(s, 1.25, 2.2, 11.2, 1.7, [P("公園緑地における自然再生と施設利用の両立に関する研究", bold=True, color="FFFFFF")], size=38, mins=30, anchor="middle")
textbox(s, 1.25, 3.95, 11.2, 0.7, [P("―管理の方向性と利用者の認識・賛成・協力―", color="D6E2EE")], size=24, mins=20, anchor="middle")
textbox(s, 1.25, 5.5, 11.2, 0.5, [P("［氏名］　　［所属］", color="9FB3C8")], size=18, mins=14)
s.notes_slide.notes_text_frame.text = "建议讲述：0:10｜累计：0:10"

# ================= 02 研究背景と目的
s = new_slide(2, "研究背景と目的：生き物を守ることと、公園利用をどう両立させるか", NAVY, "建议讲述：0:45｜累计：0:55")
draw_cards(s, [
    card_spec(LM, 1.35, 6.0, 3.5, [
        P("・生き物を守るための立入制限は、利用できる場所・時期を限定する。"),
        P("・採集や水面利用、施設整備、危険生物の駆除は、生息・生育環境の保全と競合する場合がある。"),
    ], NAVY, heading="問題となる場面"),
    card_spec(6.85, 1.35, 5.88, 3.5, [
        P("公園で実施される利用制限、保全作業、体験・教育、参加・協働を調べる。"),
        P("その実施に関わる場所・管理体制と、利用者の具体的な方針への賛成・参加意向を検討する。"),
    ], NAVY, heading="本研究の目的"),
], maxs=20)
draw_cards(s, [card_spec(LM, 5.05, CW, 1.85, [
    P("生態学的研究は、利用が生息・生育環境に及ぼす影響を考える基礎として参照する。"),
    P("本研究では、競合に対する管理と利用者の回答を調べる。"),
    P("（Monz et al., 2013；Aronson et al., 2017）", color=GREY, scale=0.85),
], GREY, fill="EEF1F4")], maxs=17)

# ================= 03 博士論文の構成
s = new_slide(3, "博士論文の構成：調べる問題・資料と方法・明らかにする内容", NAVY, "建议讲述：1:25｜累计：2:20")
cols = [
    ("研究Ⅰ｜5公園の管理者・協力団体", TEAL, [
        P(B("問題：", TEAL), "立ち入り・採集・水面利用を、保全のために制限するか、利用を認めるか。"),
        P(B("方法：", TEAL), "ヒアリングの発言を、テキストマイニング（単語の出現頻度・共起関係）と30段階の段落分類で比較する。"),
        P(B("示したこと：", TEAL), "保全・利用を優先する対応の違いと、周辺環境・土地所有・管理体制との関連。"),
    ]),
    ("研究Ⅱ｜39公園の管理者", BLUE, [
        P(B("問題：", BLUE), "保全作業、体験・教育、区域の分離をどこまで実施し、何に困っているか。"),
        P(B("方法：", BLUE), "アンケートを集計し、管理体制・苦情・緑化環境と取組の実施との関係を、共分散構造分析で検討する。"),
        P(B("示したこと：", BLUE), "体験・教育が中心で、区域の分離は限定的。保全活動と体験・教育では、緑化環境との関係が異なる。"),
    ]),
    ("研究Ⅲ｜かすかべ夢の森公園の利用者・139件", AMBER, [
        P(B("問題：", AMBER), "自然再生への賛成と、年間立入制限への賛成、自分の定期的な参加意向は同じか。"),
        P(B("方法：", AMBER), "利用者本人の回答を集計し、同じ人の回答の組合せと、認識・関心・参加経験との関係を調べる。"),
        P(B("検討すること：", AMBER), "具体的な利用制限への賛成と、活動別の参加意向の違い（分析予定）。"),
    ]),
]
specs = []
cwid = 3.95
for i, (hd, col, ps) in enumerate(cols):
    x = LM + i * (cwid + 0.14)
    hb = rect(s, x, 1.3, cwid, 0.72, fill=col)
    tf = hb.text_frame
    tf.margin_left = Inches(0.15); tf.margin_right = Inches(0.1)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    hs = fit_size([P(hd, bold=True)], cwid - 0.25, 0.66, 15, 11)
    write_paras(tf, [P(hd, bold=True, color="FFFFFF")], 13.5)
    specs.append(card_spec(x, 2.02, cwid, 3.25, ps, col, accent=False))
draw_cards(s, specs, maxs=15)
for i, (a, b, bw, aw) in enumerate([
    ("研究Ⅰの管理対応", "研究Ⅱの質問項目", 5.9, 5.48),
    ("研究Ⅰ・Ⅱの利用制限・体験・教育・共同管理", "研究Ⅲで利用者本人にたずねる", 5.9, 5.48),
]):
    y = 5.42 + i * 0.58
    r1 = rect(s, LM, y, bw, 0.48, fill=tint(NAVY, 0.9))
    tf = r1.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = Inches(0.15)
    write_paras(tf, [P(a, color=NAVY, bold=True)], 14)
    arrow(s, 6.6, y + 0.07, 0.5, 0.34, NAVY)
    r2 = rect(s, 7.25, y, aw, 0.48, fill=tint(NAVY, 0.9))
    tf = r2.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = Inches(0.15)
    write_paras(tf, [P(b, color=NAVY, bold=True)], 14)
textbox(s, LM, 6.6, CW, 0.42, [P("第6・7章：管理対応、実施を担う体制、利用者の賛成と参加意向を関連づけ、管理運営を検討する。", bold=True, color=NAVY)], size=15, mins=12, anchor="middle")

# ================= 04 研究Ⅰ 背景
s = new_slide(4, "研究Ⅰ　5公園で、立ち入り・採集・水面利用への管理対応を比較する", TEAL, "建议讲述：0:30｜累计：2:50")
draw_cards(s, [
    card_spec(LM, 1.35, 7.7, 1.85, [
        P("保全のために利用を制限すると、利用できる場所や活動が限られる。"),
        P("自由な利用を認める場合には、生息・生育環境への影響を考える必要がある。"),
    ], TEAL, heading="背景"),
    card_spec(LM, 3.35, 7.7, 1.6, [
        P("協働、規制・ゾーニング、環境教育などの対応が示されている。"),
        P("（Gobster, 2001；Ballantyne et al., 2014；Young et al., 2016）", color=GREY, scale=0.85),
    ], TEAL, heading="既存研究"),
    card_spec(LM, 5.1, 7.7, 1.8, [
        P("同じ保全と利用の問題に対して、管理者が何を優先し、なぜその対応を選ぶか。"),
    ], TEAL, heading="本研究で比較すること"),
    card_spec(8.5, 1.35, 4.23, 5.55, [
        P("鴨川みずべの里／いきものふれあいの里センター／さいたま緑の森博物館"),
        P("北本自然観察公園／上尾丸山公園"),
    ], TEAL, heading="対象", fill=tint(TEAL, 0.86)),
], maxs=19)

# ================= 05 研究Ⅰ 目的・仮説・全体図
s = new_slide(5, "研究Ⅰ　目的・仮説と調査・分析の全体像", TEAL, "建议讲述：0:40｜累计：3:30")
draw_cards(s, [
    card_spec(LM, 1.35, 4.4, 2.2, [P("5公園の管理対応を同じ保全・利用の軸で比較し、その違いと関連する公園の条件を整理する。")], TEAL, heading="目的"),
    card_spec(LM, 3.7, 4.4, 3.2, [P("立ち入り・採集・水面利用などへの管理対応の違いは、周辺環境、自然度・規模・土地所有、方針・体制・専門性と関連する。")], TEAL, heading="仮説"),
], maxs=18)
textbox(s, 5.2, 1.3, 7.53, 0.78, [P("研究Ⅰの全体像", bold=True, color=TEAL), P("原論文 Fig. 1（要旨・図1）", color=GREY, scale=0.8, before=0.1)], size=18, mins=12)
figure_placeholder(s, 5.2, 2.12, 7.53, 3.65, "Fig. 1. Overall structure of the study.", TEAL)
draw_cards(s, [card_spec(5.2, 5.9, 7.53, 1.0, [
    P("管理者・協力団体へのヒアリング", bold=True, color=TEAL),
    P("単語の出現頻度・共起関係、段落の分類、元の発言内容と公園の条件の照合"),
], TEAL, fill=tint(TEAL, 0.9))], maxs=15)

# ================= 06 研究Ⅰ 手法
s = new_slide(6, "研究Ⅰ　手法：単語を調べる分析と、段落の内容を分類する分析", TEAL, "建议讲述：0:50｜累计：4:20")
draw_cards(s, [
    card_spec(LM, 1.3, 7.3, 1.6, [
        P("2019～2020年／5公園の管理者・協力団体／各90分程度・24項目"),
        P("質問者の発言を除いた逐語記録を、段落単位で分析する。"),
    ], TEAL, heading="調査"),
    card_spec(8.05, 1.3, 4.68, 1.6, [P("何が繰り返し語られ、その発言が保全・利用の何を優先しているかを確認する。")], TEAL, heading="目的"),
], maxs=16)
arrow(s, 3.3, 2.95, 0.4, 0.28, TEAL, "down")
arrow(s, 9.6, 2.95, 0.4, 0.28, TEAL, "down")
draw_cards(s, [
    card_spec(LM, 3.28, 5.95, 2.75, [
        P("・単語の出現頻度を調べる。"),
        P("・同じ段落に現れる単語の組合せを調べる。"),
        P("・Jaccard係数で共起関係の強さを表し、0.1以上の関係を表示する。"),
        P("・元の発言を読み、管理の対象・目的・課題を確認する。"),
        P("使用：KH Coder 3", color=GREY, scale=0.85),
    ], TEAL, heading="A　テキストマイニング", fill=tint(TEAL, 0.9)),
    card_spec(6.78, 3.28, 5.95, 2.75, [
        P("・同じ逐語記録の各段落を、保全・利用の30段階に分類する。"),
        P("・環境重視・両立・利用者重視に分類した発言数を数える。"),
    ], TEAL, heading="B　段落の管理内容の分類", fill=tint(TEAL, 0.9)),
], maxs=17)
draw_cards(s, [card_spec(LM, 6.15, CW, 0.78, [
    P("AとBを並行して行い、元の発言内容と照合する。", bold=True),
    P("管理の方向性の割合は、Bの分類結果から求める。", bold=True),
], NAVY, fill="EEF1F4", anchor="middle")], maxs=16)

# ================= 07 研究Ⅰ 30段階の分類表
s = new_slide(7, "研究Ⅰ　管理対応を比較する30段階の分類", TEAL, "建议讲述：0:40｜累计：5:00")
textbox(s, LM, 1.3, 7.7, 0.78, [P("保全・利用管理フレームワーク", bold=True, color=TEAL), P("原論文 Table 5（要旨・表3）", color=GREY, scale=0.8, before=0.1)], size=18, mins=12)
figure_placeholder(s, LM, 2.12, 7.7, 4.78, "Table 5. Results of the Conservation and Utilisation Management Framework.", TEAL)
for i, (t, c) in enumerate([("利用者重視：段階1～10", ORANGE), ("両立：段階11～20", BLUE), ("環境重視：段階21～30", GREEN)]):
    r = rect(s, 8.5, 1.35 + i * 0.7, 4.23, 0.6, fill=c)
    tf = r.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.margin_left = Inches(0.2)
    write_paras(tf, [P(t, bold=True, color="FFFFFF")], 17)
draw_cards(s, [card_spec(8.5, 3.55, 4.23, 2.0, [
    P("ヒアリングの各段落を、管理対応の内容に応じて30段階に分類した。"),
    P("分類の対象とならない発言は除いた。"),
], TEAL)], maxs=16)
draw_cards(s, [card_spec(8.5, 5.7, 4.23, 1.2, [P("次に、各方向に分類した発言数から、公園ごとの割合を求める。", bold=True, color=NAVY)], NAVY, fill="EEF1F4", anchor="middle")], maxs=16)

# ================= 08 研究Ⅰ 結果図
s = new_slide(8, "研究Ⅰ　結果：分類した発言の割合から、公園の管理対応を比較する", TEAL, "建议讲述：0:55｜累计：5:55")
draw_cards(s, [
    card_spec(LM, 1.3, 5.1, 1.78, [
        P("テキストマイニングと元の発言内容の確認に並行して、同じ記録の各段落を30段階に分類した。"),
        P("図の割合は、段落の分類結果から求めた。"),
    ], TEAL, fill=tint(TEAL, 0.92)),
    card_spec(5.85, 1.3, 6.88, 1.78, [
        P("各方向の割合＝その方向に分類した段落数／分類した段落の総数×100", bold=True, color=NAVY),
        P("分類の対象外の発言は、分母に含めない。"),
        P("Jaccard係数や、保全活動の実施率を示す割合ではない。"),
    ], TEAL, heading="公園ごとに計算", fill=tint(TEAL, 0.86)),
], maxs=15)
textbox(s, LM, 3.2, 7.6, 0.58, [P("公園緑地別の環境重視・両立・利用者重視の割合", bold=True, color=TEAL), P("原論文 Fig. 2（要旨・図2）", color=GREY, scale=0.85, before=0.05)], size=15, mins=11)
figure_placeholder(s, LM, 3.82, 7.6, 3.08, "Fig. 2. Proportion of Environmental Focus, Balanced and User Focus by park.", TEAL)
draw_cards(s, [
    card_spec(8.4, 3.2, 4.33, 1.1, [P("北本自然観察公園：環境重視68％／利用者重視1％", bold=True)], GREEN, anchor="middle"),
    card_spec(8.4, 4.4, 4.33, 1.15, [P("いきものふれあいの里センター・上尾丸山公園：両立47％", bold=True)], BLUE, anchor="middle"),
    card_spec(8.4, 5.7, 4.33, 1.2, [P("同じ自然再生に取り組む公園でも、保全・利用を優先する対応の構成は異なる。", bold=True, color=NAVY)], NAVY, fill="EEF1F4", anchor="middle"),
], maxs=16)

# ================= 09 研究Ⅰ 共起ネットワーク
s = new_slide(9, "研究Ⅰ　共起ネットワークで、発言の内容を確認する", TEAL, "建议讲述：0:40｜累计：6:35")
textbox(s, LM, 1.3, 7.6, 0.78, [P("共起ネットワークの例", bold=True, color=TEAL), P("原論文 Fig. 4：Sayama（要旨・図3）", color=GREY, scale=0.8, before=0.1)], size=18, mins=12)
figure_placeholder(s, LM, 2.12, 7.6, 4.78, "Fig. 4. Co-occurrence network diagram for Sayama.", TEAL)
draw_cards(s, [
    card_spec(8.4, 1.35, 4.33, 3.1, [
        P("・同じ段落に現れる単語の組合せ"),
        P("・単語の出現頻度と共起関係の強さ"),
        P("・元の発言における管理の対象・目的・課題"),
    ], TEAL, heading="図で確認すること"),
    card_spec(8.4, 4.6, 4.33, 2.3, [
        P("係数上位の単語対を、元の発言内容と照合する。"),
        P("共起関係の強さだけで、環境重視・両立・利用者重視を決めない。", bold=True, color=NAVY),
    ], NAVY, fill="EEF1F4"),
], maxs=17)

# ================= 10 研究Ⅰ 考察
s = new_slide(10, "研究Ⅰ　考察：管理者の考え方だけでなく、場所と体制を合わせて考える", TEAL, "建议讲述：0:35｜累计：7:10")
draw_cards(s, [
    card_spec(LM + i * (3.95 + 0.14), 1.3, 3.95, 2.55, [P(t)], TEAL, heading=h)
    for i, (h, t) in enumerate([
        ("周辺環境", "北本自然観察公園：荒川流域の生態系ネットワーク・湿地と、環境重視の対応。"),
        ("土地所有", "いきものふれあいの里センター：私有地が分断された条件と、多様な主体との協働。"),
        ("管理主体", "鴨川みずべの里：市民ボランティアと、参加型の運営。"),
    ])
], maxs=18)
draw_cards(s, [card_spec(LM, 4.0, CW, 1.1, [P("利用ルールの説明、観察イベント、案内・解説などを、公園の条件に応じて組み合わせる必要がある。", bold=True, color=NAVY)], TEAL, fill=tint(TEAL, 0.84), anchor="middle")], maxs=19)
draw_cards(s, [card_spec(LM, 5.25, CW, 1.65, [
    P("5公園の発言と条件の比較であり、各要因の因果効果は確定していない。"),
    P("研究Ⅱでは、39公園で実施された取組と、実施に関わる条件を調べる。"),
    P("（Chen & Fukahori, 2026）", color=GREY, scale=0.85),
], GREY, fill="EEF1F4")], maxs=16)

# ================= 11 研究Ⅱ 背景
s = new_slide(11, "研究Ⅱ　39公園で、保全・利用調整の取組と実施上の課題を調べる", BLUE, "建议讲述：0:50｜累計：8:00".replace("累計", "累计"))
draw_cards(s, [
    card_spec(LM, 1.35, 6.0, 3.0, [
        P("5公園では、立入制限、観察イベント、情報提供などの対応がみられた。"),
        P("しかし、複数の公園で何が実施され、必要でも実施できない取組がどこにあるかは、十分にわからない。"),
    ], BLUE, heading="背景"),
    card_spec(LM, 4.5, 6.0, 2.4, [
        P("保全施策の実施には、制度・資源、関係主体、専門知識、コミュニケーションが関わる。"),
        P("（Aronson et al., 2017；Bodin, 2017；Brocki et al., 2025）", color=GREY, scale=0.85),
    ], BLUE, heading="既存研究"),
    card_spec(6.85, 1.35, 5.88, 5.55, [
        P("保全と公園利用を両立させるために、保全作業、体験・教育、区域の分離などをどこまで実施し、何に困っているかを管理者にたずねる。"),
        P("その実施の違いを、管理を担う主体、利用者からの要請・苦情、公園内外の緑化環境から検討する。", bold=True, color=NAVY, before=1.0),
    ], BLUE, heading="本研究で調べること", fill=tint(BLUE, 0.88)),
], maxs=19)

# ================= 12 研究Ⅱ 目的・仮説
s = new_slide(12, "研究Ⅱ　目的・仮説：何を実施し、その実施は何と関わるか", BLUE, "建议讲述：0:55｜累计：8:55")
draw_cards(s, [
    card_spec(LM, 1.35, 6.2, 5.55, [
        P("① 保全作業、体験・教育、場所分けがどこまで実施され、必要性と実施にどのような差があるかを把握する。"),
        P("② 公園ごとの保全活動、利用調整、利用の受入れ方を比較する。", before=0.7),
        P("③ 管理体制、要請・苦情、緑化環境と、各取組の実施との関係を検討する。", before=0.7),
    ], BLUE, heading="目的"),
    card_spec(7.0, 1.35, 5.73, 1.75, [P("公的・指定管理と市民・専門家の関与を含む体制は、保全活動と体験・教育などの実施と正に関連する。")], BLUE, heading="仮説1", fill=tint(BLUE, 0.88)),
    card_spec(7.0, 3.2, 5.73, 1.75, [P("保全作業、体験・教育、利用の受入れでは、要請・苦情や緑化環境との関係が異なる。")], BLUE, heading="仮説2", fill=tint(BLUE, 0.88)),
    card_spec(7.0, 5.05, 5.73, 1.85, [
        P("緑化環境の代理指標が高いほど、環境重視的行動も高い。"),
        P("自然再生に取り組む公園では、規制・分離が両立の中心になる。"),
    ], GREY, heading="当初の予想", fill="EEF1F4"),
], maxs=19)

# ================= 13 研究Ⅱ 手法①
s = new_slide(13, "研究Ⅱ　手法①：取組の実施と、実施できないことを公園ごとに把握する", BLUE, "建议讲述：0:45｜累计：9:40")
draw_cards(s, [card_spec(LM, 1.3, CW, 1.05, [P("保全活動、両立の工夫、必要でも実施できない取組と、その対応を担う主体を把握する。")], BLUE, heading="目的", fill=tint(BLUE, 0.88))], maxs=17)
draw_cards(s, [
    card_spec(LM, 2.5, 5.0, 2.75, [
        P("自然再生に取り組む全国39公園の管理者"),
        P("2024年10月～2025年2月／郵送・電子メール・オンライン・対面"),
    ], BLUE, heading="対象・調査"),
    card_spec(5.75, 2.5, 6.98, 2.75, [
        P("問2：自然環境の保全活動"),
        P("問3：保全活動を担う主体"),
        P("問4：利用利便性"),
        P("問5：体験・教育、区域の分離など、保全と利用を両立させる取組"),
        P("問7・問8：苦情・要望とその対応"),
    ], BLUE, heading="調べた内容"),
], maxs=17)
draw_cards(s, [card_spec(LM, 5.4, CW, 1.5, [
    P("各取組の実施状況を集計し、公園ごとの回答を比較する。", bold=True, color=NAVY),
    P("5公園のヒアリングと39公園の公式ウェブサイトを、具体的な内容を確認する補足資料として用いる。"),
], GREY, fill="EEF1F4")], maxs=16)

# ================= 14 研究Ⅱ 手法②
s = new_slide(14, "研究Ⅱ　手法②：管理体制・苦情・緑化環境と、取組の実施を比較する", BLUE, "建议讲述：0:55｜累计：10:35")
draw_cards(s, [card_spec(LM, 1.3, CW, 0.95, [P("同じ管理体制や緑化環境が、保全活動、体験・教育、利用の受入れと同じように関わるかを検討する。")], BLUE, heading="目的", fill=tint(BLUE, 0.88))], maxs=16)
# 対応表（原文ではスペースで揃えた2列）
rows = [
    ("公的・指定管理と市民・専門家の関与", "社会的規範", BLUE),
    ("管理者が回答した要請・苦情圧力", "利用者態度", BLUE),
    ("公園内外のNDVIによる緑化環境", "環境的質", BLUE),
    ("保全作業など", "環境重視的行動", GREEN),
    ("体験・教育・啓発など", "両立的行動", GREEN),
    ("安全・利便性と利用の受入れ", "利用者重視的行動", GREEN),
]
tb_shape = s.shapes.add_table(7, 2, Inches(LM), Inches(2.4), Inches(7.0), Inches(3.2))
tbl = tb_shape.table
tblPr = tbl._tbl.tblPr
sid = tblPr.find(qn("a:tableStyleId"))
if sid is None:
    sid = etree.SubElement(tblPr, qn("a:tableStyleId"))
sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
tbl.columns[0].width = Inches(4.3)
tbl.columns[1].width = Inches(2.7)


def border(cell, color="FFFFFF", w=2.0, sides=("B",)):
    tcPr = cell._tc.get_or_add_tcPr()
    for sd in sides:
        ln = etree.SubElement(tcPr, qn("a:ln" + sd), w=str(int(Pt(w))), cap="flat", cmpd="sng", algn="ctr")
        sf = etree.SubElement(ln, qn("a:solidFill"))
        etree.SubElement(sf, qn("a:srgbClr"), val=color)
        etree.SubElement(ln, qn("a:prstDash"), val="solid")


def cell_set(cell, text, size, color, fill, bold=False, align=None):
    cell.fill.solid(); cell.fill.fore_color.rgb = rgb(fill)
    cell.margin_left = Inches(0.14); cell.margin_right = Inches(0.1)
    cell.margin_top = Inches(0.04); cell.margin_bottom = Inches(0.04)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf = cell.text_frame
    write_paras(tf, [P(text, bold=bold, color=color, align=align)], size)


hdrs = ("調べた内容", "モデルの名称")
for j, h in enumerate(hdrs):
    cell_set(tbl.cell(0, j), h, 15, "FFFFFF", NAVY, bold=True)
tbl.rows[0].height = Inches(0.44)
for i, (a, b, c) in enumerate(rows, start=1):
    cell_set(tbl.cell(i, 0), a, 15.5, TXT, tint(c, 0.9))
    cell_set(tbl.cell(i, 1), b, 15.5, c, tint(c, 0.9), bold=True)
    tbl.rows[i].height = Inches(0.46)
    for j in (0, 1):
        border(tbl.cell(i, j), "FFFFFF", 3.0 if i == 3 else 1.5)
# 右：研究の枠組み
textbox(s, 7.9, 2.4, 4.83, 0.4, [P("研究の枠組み", bold=True, color=BLUE)], size=16, mins=12)
steps = [("39公園の回答＋公園内外のNDVI", 0.62), ("質問項目の構成を確認する（探索的因子分析）", 0.8), ("複数の条件と管理行動の関係を、一つのモデルで検討する（共分散構造分析）", 1.1)]
yy = 2.85
for k, (t, hh) in enumerate(steps):
    r = rect(s, 7.9, yy, 4.83, hh, fill=tint(BLUE, 0.86))
    tf = r.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.15); tf.margin_right = Inches(0.12); tf.margin_top = tf.margin_bottom = Inches(0.04)
    write_paras(tf, [P(t, color=TXT)], fit_size([P(t)], 4.5, hh - 0.08, 15, 11))
    yy += hh
    if k < 2:
        arrow(s, 10.1, yy + 0.02, 0.4, 0.2, BLUE, "down")
        yy += 0.25
draw_cards(s, [card_spec(LM, 5.85, CW, 1.08, [
    P("NDVIは、生物多様性そのものを直接測定するものではない。"),
    P("計画的行動理論は条件の整理に参照する。行動意図を測定しておらず、理論の検証ではない。"),
    P("（Ajzen, 1991）", color=GREY, scale=0.85),
], GREY, fill="EEF1F4")], maxs=14)

# ================= 15 研究Ⅱ 結果①
s = new_slide(15, "研究Ⅱ　結果①：体験・教育は多いが、区域の分離は限定的", BLUE, "建议讲述：1:05｜累计：11:40")
textbox(s, LM, 1.3, 6.6, 0.45, [P("実施率：39公園のうち、取組を実施している公園の割合", bold=True, color=BLUE)], size=15, mins=11)
textbox(s, LM, 1.8, 2.5, 0.3, [P("取組", color=GREY, bold=True)], size=12, mins=10)
textbox(s, 5.0, 1.8, 2.2, 0.3, [P("実施率", color=GREY, bold=True, align=PP_ALIGN.RIGHT)], size=12, mins=10)
cd = CategoryChartData()
cd.categories = ["啓発・マナー", "保全イベント", "レクリエーションの場所分け", "分離配置"]
cd.add_series("実施率", (82.1, 71.8, 56.4, 43.6))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(LM), Inches(2.1), Inches(6.6), Inches(3.65), cd)
ch = gf.chart
ch.has_legend = False
ch.has_title = False
ch.font.name = FONT
ch.font.size = Pt(15)
ch.font.color.rgb = rgb(TXT)
pl = ch.plots[0]
pl.gap_width = 55
pl.vary_by_categories = False
pl.has_data_labels = True
dl = pl.data_labels
dl.number_format = '0.0"％"'
dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END
dl.font.size = Pt(16); dl.font.bold = True; dl.font.name = FONT
dl.font.color.rgb = rgb(NAVY)
ser = pl.series[0]
ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(BLUE)
# 区域の分離に関わる2項目を同系の濃淡で区別
for idx, col in enumerate([BLUE, BLUE, "6F93C9", "6F93C9"]):
    pt = ser.points[idx]
    pt.format.fill.solid(); pt.format.fill.fore_color.rgb = rgb(col)
ca = ch.category_axis
ca.reverse_order = True
ca.format.line.color.rgb = rgb("8D99A6")
ca.tick_labels.font.size = Pt(15)
ca.has_major_gridlines = False
va = ch.value_axis
va.minimum_scale = 0; va.maximum_scale = 100
va.visible = False
va.has_major_gridlines = False
draw_cards(s, [
    card_spec(7.45, 1.35, 5.28, 2.1, [
        P("環境調整・外来生物の駆除：各89.7％／在来種植栽：51.3％"),
        P("危険生物の駆除・情報資料・ペット連れ：各94.9％／水面利用：23.1％"),
    ], BLUE, heading="その他の取組"),
    card_spec(7.45, 3.6, 5.28, 2.15, [
        P("保全イベント：必要性はあるが実施していない20.5％"),
        P("場所分け：方針がなく実施していない38.5％"),
    ], AMBER, heading="実施に至らない取組"),
], maxs=16)
draw_cards(s, [card_spec(LM, 5.95, CW, 0.95, [P("保全活動は、行政・指定管理者・市民団体・専門家の分業・協働で支えられていた。", bold=True, color=NAVY)], BLUE, fill=tint(BLUE, 0.84), anchor="middle")], maxs=19)

# ================= 16 研究Ⅱ 結果② SEM
s = new_slide(16, "研究Ⅱ　結果②：管理体制と緑化環境では、保全・体験教育との関係が異なる", BLUE, "建议讲述：1:30｜累计：13:10")
textbox(s, LM, 1.28, 7.4, 0.4, [P("共分散構造分析の結果（要旨・図4）", bold=True, color=BLUE)], size=16, mins=12)
figure_placeholder(s, LM, 1.72, 7.4, 4.2, "都市公園管理行動との構造的関連に関する構造方程式モデリング（SEM）の推定結果", BLUE)
draw_cards(s, [card_spec(LM, 6.02, 7.4, 0.92, [
    P("n＝39。GFI＝0.749／AGFI＝0.659／RMSEA＝0.072。"),
    P("適合度は限定的な許容水準にとどまり、因果効果ではなく探索的な関係として解釈する。"),
], GREY, fill="EEF1F4")], maxs=13)
textbox(s, 8.2, 1.28, 4.53, 0.4, [P("原図で見る四つのパス係数", bold=True, color=BLUE)], size=16, mins=12)
draw_cards(s, [
    card_spec(8.2, 1.72, 4.53, 1.3, [P("・環境重視的行動：0.84"), P("・両立的行動：0.65")], BLUE, heading="管理体制（社会的規範）"),
    card_spec(8.2, 3.1, 4.53, 1.3, [P("・環境重視的行動：−0.51"), P("・両立的行動：0.42")], BLUE, heading="緑化環境（環境的質）"),
], maxs=16)
draw_cards(s, [card_spec(8.2, 4.5, 4.53, 2.44, [
    P("管理体制は両方と正に関連したが、緑化環境との関連方向は異なった。", bold=True, color=NAVY),
    P("利用者重視的行動の説明率は0.03。", before=0.6),
    P("本モデルでは、利用の受入れの違いを十分に説明できなかった。"),
], NAVY, fill="EEF1F4")], maxs=15)

# ================= 17 研究Ⅱ 考察①
s = new_slide(17, "研究Ⅱ　考察①：体験・教育だけでなく、利用調整と担い手を検討する", BLUE, "建议讲述：0:50｜累计：14:00")
draw_cards(s, [
    card_spec(LM, 1.35, 6.2, 3.7, [
        P("・管理体制と保全活動・体験教育の正の関係は、想定と整合した。"),
        P("・緑化環境と環境重視的行動との関係は、予想に反して負であった。"),
        P("・規制・分離が中心という予想に対し、体験・教育の実施率が高かった。"),
    ], BLUE, heading="仮説・予想との対応"),
    card_spec(7.0, 1.35, 5.73, 2.4, [
        P("方針・基準の整理／場所分け・活動制限の判断／専門性・人員・予算"),
        P("在来種植栽などでは、継続的な担い手と役割分担が明確でない可能性がある。"),
    ], BLUE, heading="39公園に共通する課題"),
    card_spec(7.0, 3.85, 5.73, 1.2, [P("立地、湿地などの自然条件、土地所有、管理主体に応じた対応が必要である。")], BLUE, heading="公園ごとの課題"),
], maxs=17)
draw_cards(s, [card_spec(LM, 5.25, CW, 1.65, [P("体験・教育を実施するだけでなく、保全上必要な場所・時期・活動の制限と、その実施を担う主体を明確にすることが課題となる。", bold=True, color=NAVY)], BLUE, fill=tint(BLUE, 0.84), anchor="middle")], maxs=21)

# ================= 18 研究Ⅱ 考察②
s = new_slide(18, "研究Ⅱ　考察②：同じ「両立」でも、実施する取組は異なる", BLUE, "建议讲述：0:50｜累计：14:50")
t18 = [
    ("劣化した自然を回復する", "再生型", GREEN),
    ("残された自然を維持し、守り続ける", "保全型", GREEN),
    ("体験・教育を通じて利用者の理解と協力を得る", "体験・教育型", BLUE),
    ("保全区域と利用区域を分ける", "空間分離型", BLUE),
    ("体験・教育と区域の分離を組み合わせる", "総合型", BLUE),
    (["安全・情報などの公共性を確保し、", "高負荷の利用の受入れ範囲を調整する"], "選別型", ORANGE),
]
gs = s.shapes.add_table(7, 2, Inches(LM), Inches(1.35), Inches(7.9), Inches(4.4))
t = gs.table
tp = t._tbl.tblPr
sid = tp.find(qn("a:tableStyleId"))
if sid is None:
    sid = etree.SubElement(tp, qn("a:tableStyleId"))
sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
tp.set("firstRow", "0"); tp.set("bandRow", "0")
t.columns[0].width = Inches(5.4); t.columns[1].width = Inches(2.5)
cell_set(t.cell(0, 0), "具体的な管理内容", 15, "FFFFFF", NAVY, bold=True)
cell_set(t.cell(0, 1), "類型", 15, "FFFFFF", NAVY, bold=True)
t.rows[0].height = Inches(0.45)
for i, (a, b, c) in enumerate(t18, start=1):
    for j in (0, 1):
        cell = t.cell(i, j)
        cell.fill.solid(); cell.fill.fore_color.rgb = rgb(tint(c, 0.88))
        cell.margin_left = Inches(0.15); cell.margin_right = Inches(0.1)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if isinstance(a, list):
        write_paras(t.cell(i, 0).text_frame, [P(a[0]), P(a[1], before=0.0)], 16)
        t.rows[i].height = Inches(0.9)
    else:
        write_paras(t.cell(i, 0).text_frame, [P(a)], 16)
        t.rows[i].height = Inches(0.6)
    write_paras(t.cell(i, 1).text_frame, [P(b, bold=True, color=c)], 17)
    gap = 3.0 if i in (2, 5) else 1.5
    for j in (0, 1):
        border(t.cell(i, j), "FFFFFF", gap)
draw_cards(s, [card_spec(8.75, 1.35, 3.98, 4.4, [
    P("公園別の回答と補足資料から、管理内容をこの六つに整理した。"),
    P("両立の有無ではなく、体験・教育、空間分離、両者の組合せを比較する。", before=0.8),
], BLUE, heading="本研究の特徴")], maxs=18)
draw_cards(s, [card_spec(LM, 5.95, CW, 0.97, [P("管理者が体験・教育や利用ルールを用意しても、利用者が知り、賛成し、自ら参加しようとするかは、別に調べる必要がある。", bold=True, color=NAVY)], BLUE, fill=tint(BLUE, 0.84), anchor="middle")], maxs=17)

# ================= 19 研究Ⅲ 背景
s = new_slide(19, "研究Ⅲ　利用者は立入制限に賛成し、自分も活動に参加しようとするか", AMBER, "建议讲述：0:35｜累计：15:25")
draw_cards(s, [
    card_spec(LM, 1.35, 6.9, 1.75, [P("管理者が説明や活動の機会を用意していても、利用者が知り、賛成し、自ら参加する意向を持つとは限らない。")], AMBER, heading="背景"),
    card_spec(LM, 3.2, 6.9, 2.5, [
        P("公園利用者が期待する生態系サービスや、都市緑地への市民参加が検討されている。"),
        P("（Büchel & Frantzeskaki, 2015；Huang et al., 2021）", color=GREY, scale=0.85),
        P("自然を守りたいという考えと、自分が参加する意向を区別する考え方を参照する。"),
        P("（広瀬, 1994）", color=GREY, scale=0.85),
    ], AMBER, heading="既存研究"),
    card_spec(7.7, 1.35, 5.03, 3.05, [P("自然再生への賛成、年間の立入制限への賛成、自分の定期的な参加意向を分け、認識・関心、参加経験との関係を調べる。")], AMBER, heading="目的", fill=tint(AMBER, 0.86)),
    card_spec(7.7, 4.5, 5.03, 1.2, [P("かすかべ夢の森公園の利用者、139件の回答", bold=True)], AMBER, heading="対象"),
], maxs=17)
draw_cards(s, [card_spec(LM, 5.9, CW, 0.9, [P("分析・考察は今後行う。", bold=True, color=WARN)], AMBER, fill=tint(AMBER, 0.78), anchor="middle")], maxs=18)

# ================= 20 研究Ⅲ 仮説
s = new_slide(20, "研究Ⅲ　仮説：知っていること、賛成すること、自分が参加することを分ける", AMBER, "建议讲述：0:50｜累计：16:15")
draw_cards(s, [
    card_spec(LM + i * (3.95 + 0.14), 1.35, 3.95, 2.95, ps, AMBER, heading=h)
    for i, (h, ps) in enumerate([
        ("仮説1", [P("自然再生活動や管理体制を知り、関心が高い利用者ほど、管理方針への賛成と参加意向が高い。")]),
        ("仮説2", [P("両立への賛成に比べ、年間を通した立入制限への賛成は低い。"), P("共同管理への賛成に比べ、自らの定期的な参加意向は低い。")]),
        ("仮説3", [P("参加経験がある利用者は、参加経験がない利用者より、自然再生活動への協力と継続的な参加意向が高い。")]),
    ])
], maxs=17)
textbox(s, LM, 4.45, 6, 0.4, [P("研究の枠組み", bold=True, color=AMBER)], size=16, mins=12)
for x, w, t in [(LM, 4.8, "認識・関心／参加経験／個人特性・利用形態"), (7.93, 4.8, "具体的な管理方針への賛成／活動別の参加意向")]:
    r = rect(s, x, 4.9, w, 1.3, fill=tint(AMBER, 0.84), line=AMBER)
    tf = r.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.2)
    write_paras(tf, [P(t, bold=True, color=TXT, align=PP_ALIGN.CENTER)], fit_size([P(t, bold=True)], w - 0.4, 1.2, 18, 12))
textbox(s, 5.5, 4.9, 2.33, 1.3, [P("―― 関連を検討 ――", bold=True, color=AMBER, align=PP_ALIGN.CENTER)], size=15, mins=11, anchor="middle")
textbox(s, LM, 6.35, CW, 0.5, [P("各段階を順に進む因果関係として検証するものではない。", bold=True, color=WARN)], size=16, mins=12, anchor="middle")

# ================= 21 研究Ⅲ 手法
s = new_slide(21, "研究Ⅲ　手法：同じ利用者の賛成と参加意向を組み合わせて調べる", AMBER, "建议讲述：0:50｜累计：17:05")
draw_cards(s, [card_spec(LM, 1.3, CW, 1.0, [P("一般的な方向性への賛成が、具体的な利用制限や自分の定期参加でも同じかを確認する。")], AMBER, heading="目的", fill=tint(AMBER, 0.86))], maxs=17)
draw_cards(s, [
    card_spec(LM, 2.45, 4.4, 3.2, [
        P("認識：Q1～Q3"),
        P("管理方針への賛成：Q9～Q14"),
        P("参加経験・参加意向：Q17・Q18"),
    ], AMBER, heading="把握する内容"),
    card_spec(5.15, 2.45, 7.58, 3.2, [
        P("単純集計：知っている人数、賛成する人数、活動別の参加意向の人数・割合。"),
        P("仮説1：認識・関心と賛成・参加意向の関係を、Spearmanの順位相関係数で検討する。"),
        P("仮説2：同じ回答者の二つの回答を組み合わせるクロス集計と、肯定的回答の割合を比較する。"),
        P("仮説3：参加経験がある人とない人で、活動への協力・継続的な参加意向を比較する。"),
    ], AMBER, heading="分析予定"),
], maxs=16)
draw_cards(s, [card_spec(LM, 5.8, CW, 1.12, [
    P("139件の独立性と回収記録を確認する。"),
    P("Q14は方針への賛成であり、実施状況の認識ではない。"),
    P("Q18は参加意向であり、今後の実際の参加ではない。"),
], GREY, fill="EEF1F4")], maxs=15)

# ================= 22 研究Ⅲ 結果・考察の予定
s = new_slide(22, "研究Ⅲ　結果・考察で整理する内容（分析予定）", AMBER, "建议讲述：0:35｜累计：17:40")
draw_cards(s, [
    card_spec(LM, 1.35, 7.0, 3.35, [
        P("① 両立への賛成と、年間立入制限への賛成の組合せ"),
        P("② 共同管理への賛成と、自分の定期的な参加意向の組合せ"),
        P("③ 認識・関心、参加経験と、管理方針への賛成・活動別の参加意向との関係"),
    ], AMBER, heading="結果として整理する内容"),
    card_spec(7.8, 1.35, 4.93, 3.35, [P("具体的な利用制限への賛成と、希望する参加形態を踏まえ、利用調整、体験・教育、継続的な作業の役割分担を検討する。")], AMBER, heading="考察する内容", fill=tint(AMBER, 0.86)),
], maxs=19)
draw_cards(s, [card_spec(LM, 4.9, CW, 1.95, [
    P("現在は139件の回答を用いた分析を予定しており、結果の数値は示さない。", bold=True, color=WARN),
    P("時間・費用・責任認識を直接たずねていないため、参加しない理由までは特定できない。", before=0.6),
], AMBER, fill=tint(AMBER, 0.78), anchor="middle")], maxs=19)

# ================= 23 総合考察
s = new_slide(23, "総合考察：利用調整、体験・教育、継続的な作業をどう組み合わせるか", NAVY, "建议讲述：0:50｜累计：18:30")
t23 = [
    ("立入制限・利用ルール", "公園ごとの対応は異なり、規制・分離の取組は限定的。", "時期に応じた制限と、年間立入制限への賛成。"),
    ("体験・教育", "観察イベント・啓発・情報提供を中心に、利用者への対応が行われる。", "活動や管理体制の認識、関心と参加意向。"),
    ("参加・協働", "分業・協働で実施される一方、継続的な担い手・役割分担が課題。", "共同管理への賛成、参加経験と希望する参加形態。"),
]
gs = s.shapes.add_table(4, 3, Inches(LM), Inches(1.35), Inches(CW), Inches(3.6))
t = gs.table
tp = t._tbl.tblPr
sid = tp.find(qn("a:tableStyleId"))
if sid is None:
    sid = etree.SubElement(tp, qn("a:tableStyleId"))
sid.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
tp.set("firstRow", "0"); tp.set("bandRow", "0")
for j, wd in enumerate((2.75, 4.8, 4.58)):
    t.columns[j].width = Inches(wd)
for j, (h, c) in enumerate([("管理内容", NAVY), ("研究Ⅰ・Ⅱで得られた知見", BLUE), ("研究Ⅲで検討する内容（予定）", AMBER)]):
    cell_set(t.cell(0, j), h, 16, "FFFFFF", c, bold=True)
t.rows[0].height = Inches(0.5)
for i, row in enumerate(t23, start=1):
    for j, txt in enumerate(row):
        c = [NAVY, BLUE, AMBER][j]
        cell_set(t.cell(i, j), txt, 16.5, NAVY if j == 0 else TXT, tint(c, 0.9), bold=(j == 0))
        border(t.cell(i, j), "FFFFFF", 3.0)
    t.rows[i].height = Inches(1.0)
draw_cards(s, [card_spec(LM, 5.1, CW, 1.4, [
    P("保全上必要な場所・時期・活動の範囲を明確にする。"),
    P("学び・体験の機会と継続的な作業を分け、担う主体と参加機会を検討する。"),
], NAVY, heading="管理運営の課題", fill=tint(NAVY, 0.88))], maxs=17)
textbox(s, LM, 6.55, CW, 0.42, [P("対象公園と質問項目は異なり、管理者と利用者の回答割合を直接比較するものではない。", color=WARN, bold=True)], size=14, mins=11, anchor="middle")

# ================= 24 結論
s = new_slide(24, "結論：得られた知見と今後の課題", NAVY, "建议讲述：1:00｜累计：19:30")
draw_cards(s, [
    card_spec(LM, 1.35, 3.95, 4.45, [P("5公園の発言を30段階で比較し、立ち入り・採集・水面利用などへの対応の違いと、場所・管理体制との関連を整理した。")], TEAL, heading="研究Ⅰ"),
    card_spec(LM + 4.09, 1.35, 3.95, 4.45, [
        P("両立の取組は体験・教育が中心で、規制・分離は限定的であった。"),
        P("体験・教育、空間分離、両者の組合せを区別し、管理内容を六つに整理した。"),
        P("保全活動と両立の取組は管理体制と正に関連したが、緑化環境との関連方向は異なった。"),
    ], BLUE, heading="研究Ⅱ"),
    card_spec(LM + 8.18, 1.35, 3.95, 4.45, [
        P("139件の回答から、具体的な利用制限への賛成と活動別の参加意向を検討する。"),
        P("対象公園と環境指標を拡充し、管理方策の効果と実際の継続状況を調べる。"),
    ], AMBER, heading="研究Ⅲ・今後の課題"),
], maxs=17)
draw_cards(s, [card_spec(LM, 5.95, CW, 0.98, [
    P("研究Ⅲは分析予定である。", bold=True, color=WARN),
    P("研究Ⅰ・Ⅱも、因果効果や、すべての公園に共通する両立の成立条件を確定したものではない。", bold=True, color=WARN),
], GREY, fill="EEF1F4", anchor="middle")], maxs=16)

# ================= 25 / 26 参考文献
def refs_slide(no, title, left, right, notes):
    s = new_slide(no, title, GREY, notes)
    for x, items in ((LM, left), (6.78, right)):
        ps = []
        for k, (txt, doi) in enumerate(items):
            ps.append(P(txt, before=0.0 if k == 0 else 0.9))
            if doi:
                ps.append(P(doi, color=BLUE, scale=0.92, before=0.1))
        textbox(s, x, 1.3, 5.95, 5.65, ps, size=13, mins=9.5)
    return s


refs_slide(25, "参考文献（1）", [
    ("Ajzen, I. (1991). The theory of planned behavior. Organizational Behavior and Human Decision Processes, 50(2), 179–211.", "https://doi.org/10.1016/0749-5978(91)90020-T"),
    ("Aronson, M. F. J., Lepczyk, C. A., Evans, K. L., Goddard, M. A., Lerman, S. B., MacIvor, J. S., Nilon, C. H., & Vargo, T. (2017). Biodiversity in the city: Key challenges for urban green space management. Frontiers in Ecology and the Environment, 15(4), 189–196.", "https://doi.org/10.1002/fee.1480"),
    ("Ballantyne, M., Gudes, O., & Pickering, C. M. (2014). Recreational trails are an important cause of fragmentation in endangered urban forests: A case study from Australia. Landscape and Urban Planning, 130, 112–124.", "https://doi.org/10.1016/j.landurbplan.2014.07.004"),
], [
    ("Bodin, Ö. (2017). Collaborative environmental governance: Achieving collective action in social-ecological systems. Science, 357(6352), eaan1114.", "https://doi.org/10.1126/science.aan1114"),
    ("Brocki, M., Christoffersen, L., Randrup, T. B., Emilsson, T., Sjöman, J. D., & Jansson, M. (2025). Green space management for biodiversity: Swedish managers’ experience of implementation and influence. Urban Forestry & Urban Greening, 113, 129126.", "https://doi.org/10.1016/j.ufug.2025.129126"),
    ("Büchel, S., & Frantzeskaki, N. (2015). Citizens’ voice: A case study about perceived ecosystem services by urban park users in Rotterdam, the Netherlands. Ecosystem Services, 12, 169–177.", "https://doi.org/10.1016/j.ecoser.2014.11.014"),
], "展示预留：0:15｜累计：19:45")

refs_slide(26, "参考文献（2）", [
    ("Chen, J., & Fukahori, K. (2026). Balancing biodiversity conservation and recreational use in nature-oriented parks in Saitama Prefecture, Japan. Urban Forestry & Urban Greening, 124, 129577.", "https://doi.org/10.1016/j.ufug.2026.129577"),
    ("Gobster, P. H. (2001). Visions of nature: Conflict and compatibility in urban park restoration. Landscape and Urban Planning, 56(1–2), 35–51.", "https://doi.org/10.1016/S0169-2046(01)00164-5"),
    ("Hirose, Y. (1994). 環境配慮的行動の規定因について [On the determinants of pro-environmental behavior]. Japanese Journal of Social Psychology, 10(1), 44–55.", None),
], [
    ("Huang, Y., Aguilar, F., Yang, J., Qin, Y., & Wen, Y. (2021). Predicting citizens’ participatory behavior in urban green space governance: Application of the extended theory of planned behavior. Urban Forestry & Urban Greening, 61, 127110.", "https://doi.org/10.1016/j.ufug.2021.127110"),
    ("Monz, C. A., Pickering, C. M., & Hadwen, W. L. (2013). Recent advances in recreation ecology and the implications of different relationships between recreation use and ecological impacts. Frontiers in Ecology and the Environment, 11(8), 441–446.", "https://doi.org/10.1890/120358"),
    ("Young, J. C., Searle, K., Butler, A., Simmons, P., Watt, A. D., & Jordan, A. (2016). The role of trust in the resolution of conservation conflicts. Biological Conservation, 195, 196–202.", "https://doi.org/10.1016/j.biocon.2015.12.030"),
], "展示预留：0:15｜累计：20:00")

assert len(prs.slides) == TOTAL, len(prs.slides)
out = r"C:\Users\happyelements\Desktop\Paper\PPT\博士汇报_26页.pptx"
prs.save(out)
print("saved", out)
