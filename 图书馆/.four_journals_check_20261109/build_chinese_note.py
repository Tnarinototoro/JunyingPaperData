from pathlib import Path
import json
from datetime import date
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
rows=json.loads((OUT/'root_taylor_history_audit.json').read_text(encoding='utf-8'))
text='''# 四刊投稿至接收时间与Conservation出版社、费用核验

核验日期：2026年11月9日。投稿至接收按Received → Accepted的自然日差计算，含作者修稿时间；首次决定、外审后首次决定、接收后出版均不代替这一指标。

## 四刊实际能确认的接收时间

**本次没有取得四刊可用的最新全刊官方Submission to acceptance统计。** ScienceDirect和Taylor & Francis的期刊指标页受访问限制；经其他公开读取途径访问，返回的仍是安全验证页。下表报告逐篇论文的实际履历，不能写成全刊平均或承诺。

|期刊（官网）|本次核到的论文实际历时|样本口径|
|---|---|---|
|[Journal for Nature Conservation](https://www.sciencedirect.com/journal/journal-for-nature-conservation/about/insights)|159天|1篇原刊全文存档；非全刊统计|
|[Journal of Environmental Management](https://www.sciencedirect.com/journal/journal-of-environmental-management/about/insights)|89天|1篇原刊PDF；非全刊统计|
|[Journal of Environmental Planning and Management](https://www.tandfonline.com/journals/cjep20/about-this-journal?show=journalMetrics)|156–449天，6篇样本中位数333天|出版社提交至Crossref的publication_history日期；未直接读到期刊网页正文|
|[Landscape Research](https://www.tandfonline.com/journals/clar20/about-this-journal?show=journalMetrics)|68–793天，4篇样本中位数320天|近期6条Crossref记录中，排除特刊导言及类型未核实的短稿后4条；未直接读到期刊网页正文|

**各组数量、题材及取得方式不同，不能据此认定哪本期刊全刊接收最快。** 接收/发表样本不包括被拒稿者，亦非随机样本。就速度优先的决策而言，这些履历不足以支持将后两刊视为稳定在1—2个月内接收的投稿选择；JEM的89天也仅为一个实例。

Landscape Research所属学术团体[Landscape Research Group期刊页](https://landscaperesearch.org/journal/)写的是“10 days average from submission to first decision”，且未说明统计窗口或更新日。这是首次决定，**不是10天接收**。官方[T&F指标释义](https://authorservices.taylorandfrancis.com/publishing-your-research/choosing-a-journal/journal-metrics/)亦区分首次决定、外审后首次决定和接收后出版，不能把这些数字相加代替投稿至接收。

## 单篇日期与可核来源

|期刊|论文与来源|Received|Accepted|日数|
|---|---|---|---|---:|
|Journal for Nature Conservation|[Rewilding reshapes gut microbiomes and parasite exposure in European bison: a 17-month release from Wilder Blean](https://pmc.ncbi.nlm.nih.gov/articles/PMC13276717/)；DOI 10.1016/j.jnc.2026.127304；PMC原刊全文存档|2025-11-07|2026-04-15|159|
|Journal of Environmental Management|[Understanding public preferences for urban wildflower meadows](https://spiral.imperial.ac.uk/server/api/core/bitstreams/8ebd20d6-e37f-442d-bdbc-a35427f92681/content)；DOI 10.1016/j.jenvman.2026.131156；Imperial机构库原刊PDF，与Kent原刊副本交叉核对，仍只算1篇|2026-07-13|2026-10-10|89|
'''
for x in rows:
    if not x['included']:continue
    text+=f"|{x['journal']}|[{x['title']}]({x['article_url']})；[出版社提交的Crossref日期]({x['crossref_url']})|{x['received']}|{x['accepted']}|{x['days']}|\n"
text+='''
T&F样本从本次在线取得的两刊最近各6条Crossref记录中核对`assertion → publication_history → received/accepted`。这些字段是出版商提交的发表履历，不是Crossref的created、deposited或published日期。JEPM六条全部具双日期；LR排除了“Landscapes of abandonment”（3天，文章类型未核实）及“Introduction to special issue…”（16天，特刊导言），未将其作为研究论文快接收证据。文章标题及研究题材仍有差异，因此保留样本限制。

## MDPI与Conservation刊名区分

以下四本**全部由MDPI出版**：[Land](https://www.mdpi.com/journal/land)、[Urban Science](https://www.mdpi.com/journal/urbansci)、[Environments](https://www.mdpi.com/journal/environments)、[Sustainability](https://www.mdpi.com/journal/sustainability)。本次经MDPI官方目录API核对，未在此重复核价四刊。

“Conservation”与“Journal for Nature Conservation”是两本不同的期刊：

|准确刊名|出版社与识别信息|本次费用核验|
|---|---|---|
|[Conservation](https://www.mdpi.com/journal/conservation)|MDPI；eISSN 2673-7159|[官方费用页](https://www.mdpi.com/journal/conservation/apc)显示基础APC **CHF 1,200**，适用VAT或Sales Tax另加；接受后不久邮件开具发票|
|[Journal for Nature Conservation](https://www.sciencedirect.com/journal/journal-for-nature-conservation)|Elsevier；ISSN 1617-1381；混合出版模式|[官方Journal Finder](https://journalfinder.elsevier.com/results?query=Journal%20for%20Nature%20Conservation&mode=search)本次刷新显示，选择OA时标准APC **USD 3,160**；订阅路线不需支付这笔OA APC|

Conservation费用页本环境原站直连403，通过公开文本读取服务获得官方页完整正文转写，其原句是：“An article processing charge (APC) of CHF 1200 (Swiss francs) applies to papers accepted after peer review.”另明确“Invoices are emailed shortly after acceptance”及“Local VAT or Sales Tax will be added if applicable”。正文未标明报价生效日，最终以投稿/开票时适用条件为准。DOAJ及OpenAlex的CHF1,000与官网正文不一致，本报告不采用旧目录数字。

用户提供的埼玉大学图书馆资料确认参加MDPI IOAP、MDPI全刊APC九折；如果本稿作者确实符合资格，且投稿时用大学邮箱正确识别并应用协议，Conservation基础预算为 **1,200 × 90% = CHF 1,080＋适用税**。这不是无条件最终发票金额，也不预设与其他优惠叠加。

Journal for Nature Conservation的USD3,160来自本次HTTP200的官方Finder接口准确刊名记录，`openAccessType=HYBRID`、`goldOpenAccessFee.value=3160`、`currency=USD`。Elsevier[官方出版定价说明](https://www.elsevier.com/about/policies-and-standards/pricing)区分订阅与OA融资模式；本刊GFA和OA options页面仍受访问限制，不能扩大为“任何路线的所有潜在费用均为零”。机构协议资格和适用税另按实际确认。

## 复核记录

原官网快照、访问状态、出版社元数据、原刊PDF与日期差计算结果保存在同目录的`.four_journals_check_20261109`。主要文件：`elsevier_verified_evidence.md`、`elsevier_jnc_fee_findings.md`、`taylor_crossref_je_pm.json`、`taylor_crossref_lr.json`、`root_taylor_history_audit.json/.csv`、`mdpi_publisher_conservation_apc_evidence.md`和`root_reader_conservation.txt`。本次未联系编辑部、未投稿、未改动论文。
'''
target=ROOT/'四刊投稿至接收时间与Conservation费用核验_2026-11-09.md'
target.write_text(text,encoding='utf-8')
assert (date(2026,4,15)-date(2025,11,7)).days==159
assert (date(2026,10,10)-date(2026,7,13)).days==89
assert len([x for x in rows if x['included']])==10
print('Report created; 12 article histories included, with 2 additional Crossref records excluded.')
