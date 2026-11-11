from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'taylor_crossref_publication_histories_20261109.json').read_text(encoding='utf-8'))
text='''# T&F 两刊审稿及接收时间：2026-11-09 在线核验

**结论：两刊官网全刊“投稿至接收”统计本次均未核得；但已从出版社提交至Crossref的publication_history断言核得各6篇文章的Received/Accepted。单篇历史不能改称全刊最新接收时长，也不能预测本稿需要几天。**

|期刊|投稿→首次决定|投稿→外审后首次决定|投稿→接收全刊统计|本次单篇接收证据|
|---|---|---|---|---|
|[Journal of Environmental Planning and Management](https://www.tandfonline.com/journals/cjep20)|未核得|未核得|未核得|Crossref出版社历史6篇：434、200、418、156、449、248天|
|[Landscape Research](https://www.tandfonline.com/journals/clar20)|[Landscape Research Group官方期刊页](https://landscaperesearch.org/journal/)写“10 days average from submission to first decision”|未核得|未核得|Crossref中4篇非明显导言个例：793、554、68、86天；另有3天类型未核条目和16天专辑导言，不列作快速原始研究证据|

LRG的10天是**首决平均值**，不是外审决定或接收。该网页未给此速度的统计窗口/更新日，邻近的2024年影响因子、下载量年份不能移作速度年份。不能改写为最新全刊中位数或接收10天。

**更正记录：初次只检查Crossref顶层accepted/received，误报未含日期；复查发现assertion数组的group.name=publication_history含明确日期，现已抽出全部12条。以下日期来自出版社提交到Crossref的记录，不能标成“本次直接从期刊全文官网核得”。**

## 出版社提交至Crossref的Received→Accepted

本日在线查询均HTTP200：[JEPM最近6条](https://api.crossref.org/journals/0964-0568/works?sort=published&order=desc&rows=6&filter=until-pub-date:2026-11-09)，[LR最近6条](https://api.crossref.org/journals/0142-6397/works?sort=published&order=desc&rows=6&filter=until-pub-date:2026-11-09)。顺序按上述API本次返回顺序保留，不按快慢选择。日差用datetime按自然日相减；全部Received≤Accepted≤2026-11-09。包括作者修回时间。Crossref的journal-article标记本身不能独立证明稿型为Original Research。

|期刊/顺序|文章与官方链接|Received|Accepted|自然日差|使用限制|
|---|---|---|---|---:|---|
'''
for row in rows:
    note='单篇历史；非全刊统计'
    if row['journal_code']=='clar20' and row['source_order']==1:
        note='稿型未从原刊核实；不作为快速原著证据'
    if row['journal_code']=='clar20' and row['source_order']==3:
        note='专辑导言；排除作为原始研究速度证据'
    title=re.sub(r'\s+',' ',re.sub('<[^>]+>','',row['title'])).strip()
    text+=f"|{row['journal_code']} / {row['source_order']}|[{title}]({row['publisher_article_url']})<br>[Crossref记录]({row['crossref_work_url']})|{row['received']}|{row['accepted']}|{row['days']}|{note}|\n"
text+='''
## 官网各阶段指标的定义

T&F官方[Understanding journal metrics](https://authorservices.taylorandfrancis.com/publishing-your-research/choosing-a-journal/journal-metrics/)本次HTTP200：

1. **Speed from submission to first-decision**：过去6个月收到首次决定的全部稿件，自投稿至首次决定的天数中位数。含未经外审即拒稿。桌拒多时可能非常短，不能代表送外审稿件的等待。
2. **Speed from submission to first post-review decision**：仅考虑已送专家外审的文章，过去6个月收到首次决定的稿件，自投稿至该决定的天数中位数。包含寻找审稿人的时间，仍不是最终接收。
3. **Speed from acceptance to online publication**：接受至正式Version of Record在线出版的天数中位数，是制作出版阶段，不能作投稿至接收。

该通用页说明T&F Online速度指标基于过去6个月、2月和7月更新，且只是指引而非保证。但未成功取得两刊实际指标页，不能由通用更新规则推断具体数值或保证目前数据窗口，也不能把该中位数定义强加给LRG另外写出的average。通用页未取得“投稿至接收”独立指标定义，不能把外审首决与制作出版日数相加拼成接收全流程。

## 直接官网访问结果及机构库补查

两刊home、about-this-journal、about-this-journal/journal-metrics、旧action/journalInformation?show=journalMetrics、toc/{code}/0/0最新列表，共10路径全为HTTP403“Just a moment...”挑战页。T&F企业站、Think和Journal Suggester替代页也403。LRG实际期刊页200，含上述首决10天。

Crossref返回前3篇各查原刊/doi/full/、/doi/full-xml/、/doi/pdf/，17条403、1条超时；因此没有直接从原刊网页读取日期。所有准确URL和原响应保存，不能把挑战页HTTP403当成期刊没有数据。

按Crossref DOI→OpenAlex locations定位大学机构库后取得以下公开PDF；OpenAlex只用于发现地址，不取其索引日作接收日：

- KU Leuven：`taylor_je_kuleuven.pdf`（HTTP200，32页），为JEPM正式版，DOI `10.1080/09640568.2026.2714013`。PDF第2页清晰写 **Received 27 August 2025; final version received 13 July 2026**。后者是收到最终版本，不能不经其他接收证据直接改写Accepted。已逐图核对，图片`taylor_je_kuleuven_ocr/page_2.png`。
- White Rose：`taylor_je_whiterose.pdf`（HTTP200，33页），机构库封面明确Published Version，DOI `10.1080/09640568.2026.2680123`。已渲染前2页，未据封面推算接收日。
- UCL：`taylor_lr_ucl.pdf`（HTTP200，9页），Landscapes of Care；正文说明为专辑introduction，前2页无双日期，不用于原始研究速度样本。
- Brookes公共API显示论文附件restricted、metadataOnlyAccess，未下载受限附件；Auckland虽然HTTP200，实际返回防护脚本，不算全文获取成功。其他库有403，原始记录均保留。

## 证据索引

- `taylor_verified_summary_20261109.json`：最终结构化摘要，区分全刊指标与Crossref单篇历史。
- `taylor_crossref_publication_histories_20261109.json`：12条出版历史及逐篇API/原刊链接、日期和自然日差。
- `taylor_crossref_je_pm.json`、`taylor_crossref_lr.json`：原始Crossref响应，日期在assertion的publication_history组中。
- `taylor_online_access_20261109.json`：两刊10个直接期刊路径与状态，原文taylor_cjep20_*.html/.txt和taylor_clar20_*.html/.txt。
- `taylor_official_articles_alternatives_20261109.json`：18个直接文章路径及官方替代访问记录。
- `taylor_lrg_journal_actual.html/.txt`、`taylor_lrg_actual_evidence.json`：首决10天原文。
- `taylor_tf_metrics_explainer.html/.txt`：T&F各阶段口径与更新规则原文。
- `taylor_openalex_locations_20261109.json`、`taylor_repository_access_20261109.json`、`taylor_direct_repository_pdfs_20261109.json`：机构库地址、访问/版本及PDF获取记录。

未登录、未联系编辑、未投稿、未改已有主报告。现有个例可说明两刊有较长的接收周期，但不足以确定全刊典型速度，更不能证明某刊对本稿最快。
'''
(ROOT/'taylor_review_times_20261109.md').write_text(text,encoding='utf-8')
print('Final report rewritten in UTF-8 with all12 histories and provenance.')
