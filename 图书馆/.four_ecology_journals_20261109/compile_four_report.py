from pathlib import Path
from datetime import datetime
import statistics,json,re,html,csv
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent

def tidy(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',t))).strip()
lee=json.loads((OUT/'lee_selected_histories.json').read_text(encoding='utf-8'))
rest=json.loads((OUT/'restoration_publication_histories_20261109.json').read_text(encoding='utf-8'))
emr_all=json.loads((OUT/'emr_crossref_history_samples.json').read_text(encoding='utf-8'))
# Keep original recent-list order. Exclude only the cultural contribution with
# unconfirmed research type, then take the first five entries with research content.
emr=[x for x in emr_all if x['doi']!='10.1111/emr.70072'][:5]
allrows=[]
for x in lee['articles']:
 h=x['history'];allrows.append({'journal':'Landscape and Ecological Engineering','title':x['title'].split(' | ')[0],'doi':x['url'].split('/article/')[-1],'received':datetime.strptime(h['Received'],'%d %B %Y').date().isoformat(),'accepted':datetime.strptime(h['Accepted'],'%d %B %Y').date().isoformat(),'days':x['days'],'source':'Springer official article history','url':x['url']})
for x in rest['items']:
 allrows.append({'journal':'Restoration Ecology','title':tidy(x['title']),'doi':x['doi'],'received':x['received'],'accepted':x['accepted'],'days':x['days'],'source':'Publisher-supplied Crossref publication_history assertion','url':x['metadata_url']})
for x in emr:
 allrows.append({'journal':'Ecological Management & Restoration','title':tidy(x['title']),'doi':x['doi'],'received':x['received'],'accepted':x['accepted'],'days':x['days'],'source':'Publisher-supplied Crossref publication_history assertion; exact journal subtype not checked in full text','url':x['crossref_url']})
city=[
 {'journal':'City and Environment Interactions','title':'Urban airborne allergenic pollen shows highly local patterns correlated with public green spaces','doi':'10.1016/j.cacint.2026.100434','received':'2026-03-30','accepted':'2026-07-20','days':112,'source':'Publisher PDF in Naturalis repository','url':'https://repository.naturalis.nl/pub/802279/Dorst-2026-Urban-airborne-allergenic-pollen-A.pdf'},
 {'journal':'City and Environment Interactions','title':'Urban green space engagement patterns and mental health in a Mediterranean City','doi':'10.1016/j.cacint.2026.100444','received':'2026-03-31','accepted':'2026-08-10','days':132,'source':'Elsevier-published full text deposited in PMC','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC13576388/'},
 {'journal':'City and Environment Interactions','title':'Predicting environmental health-related search patterns using freely available digital and reanalysis data: A critical evaluation of Google Trends and global datasets for Morocco','doi':'10.1016/j.cacint.2026.100488','received':'2026-01-15','accepted':'2026-09-25','days':253,'source':'Publisher Journal Pre-proof in EPFL repository; accepted, not final VOR','url':'https://infoscience.epfl.ch/bitstreams/5b4b086f-940f-41f9-8304-2655589537e5/download'},
]
allrows.extend(city)
for x in allrows:
 assert (datetime.fromisoformat(x['accepted'])-datetime.fromisoformat(x['received'])).days==x['days']
summary={}
for j in dict.fromkeys(x['journal'] for x in allrows):
 values=[x['days'] for x in allrows if x['journal']==j]
 summary[j]={'n':len(values),'days':values,'median':statistics.median(values),'min':min(values),'max':max(values)}
(OUT/'four_selected_histories.json').write_text(json.dumps({'checked_date':'2026-11-09','summary':summary,'articles':allrows},ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'四本生态与城市期刊_收稿接收日期明细_2026-11-09.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)

text='''# 39公园研究：四本生态与城市环境期刊投稿核验

核验日期：2026年11月9日。针对原稿《自然再生に取り組む都市公園の管理行動と関連要因―日本の39公園を対象とした質問紙調査と構造方程式モデリングによる探索的分析―》（17 10.31 txt.txt）。

## 判断依据与结论

本稿核心是日本39公园、34管理团体的管理者问卷，研究自然保护／恢复与游憩利用的协调、管理行为、参与主体和实施条件，以探索性EFA／SEM整理关联，辅以NDVI。它没有直接测量生物多样性提升、恢复前后成效或生态工程性能。期刊是否适合应按这些实际证据判断，不能仅因题名中有“restoration”或“ecological”而认定符合。

**四刊均不是MDPI。现稿可优先保留Landscape and Ecological Engineering和City and Environment Interactions作为主题候选；Restoration Ecology也可投，但应更集中地呈现生态修复治理与实施障碍的贡献；Ecological Management & Restoration需要对澳新地区明确相关性，现稿不宜优先。** 这是主題与研究设计适合性的判断，英文化、格式、伦理和数据说明仍须按选定期刊整备，不能解释为保证接收。

|期刊（官方范围入口）|出版社／模式|本稿主题判断|投稿至接收：本次已核样本|
|---|---|---|---|
|[Landscape and Ecological Engineering](https://link.springer.com/journal/11355/aims-and-scope)|Springer Nature／ICLEE；Hybrid|**可以考虑，中高匹配**：生态系统保护、恢复、管理及景观规划的实践应用均在范围内|5篇，89–367天，样本中位数171天|
|[Restoration Ecology](https://www.wiley.com/en-us/restoration-ecology-p-1526100X)|Wiley／Society for Ecological Restoration；Hybrid|**有条件适合**：范围明确包括policy、governance与实践研究；应以修复实施条件和障碍为核心|5篇，71–274天，样本中位数112天|
|[Ecological Management & Restoration](https://www.ecolsoc.org.au/publications/journals/)|Wiley／Ecological Society of Australia；Hybrid|**有交集，但现稿不优先**：重实践和澳新相关性；日本案例须证明对澳新有明确意义|5篇，225–508天，样本中位数275天|
|[City and Environment Interactions](https://journalfinder.elsevier.com/results?query=City%20and%20Environment%20Interactions&mode=search)|Elsevier；全OA|**可以考虑，有条件适合**：城市环境社会科学、利益相关者与政策界面；需突出城市公园治理的环境及政策意义|3篇，112–253天，样本中位数132天|

**上表全部为已接收／发表论文的小样本，不是全刊官方平均值或中位数，也不是本稿预计接收时间。** 日数是Received到Accepted的自然日差，包含作者修稿时间。各刊样本量、研究题材和取得方式不同，不能据中位数直接宣布“Restoration Ecology最快”。本次未取得四刊可用的最新全刊投稿至接收统计；官网首次决定或接收后制作时间不能代替。

## 各刊的主題适合性

### Landscape and Ecological Engineering

[官网范围](https://link.springer.com/journal/11355/aims-and-scope)包括“all aspects of conservation, restoration, and management of ecosystems”，并明确重视面向景观规划和管理决策者的实际应用。因此，研究公园保护、利用协调与实施条件属于可考虑的范围，不要求所有投稿都是工程实验。建议以城市生态管理的实践问题为主线，解释哪些组织条件关联于管理行动，以及其他地区可采用或检验哪些发现。

[作者指南](https://link.springer.com/journal/11355/submission-guidelines)中Original Paper上限9,000词，适合本稿独立调查与分析；应按完成英文稿核字数。[相关刊内先例](https://link.springer.com/article/10.1007/s11355-026-00760-2)结合城市绿地植被指标与问卷，但它还含现场验证，不能当作本稿已有同等生态实测。

### Restoration Ecology

[Wiley官方产品页](https://www.wiley.com/en-us/restoration-ecology-p-1526100X)原文明确欢迎“experimental, theoretical, technical, practical, policy, governance, and strategic research and applications”，目标为恢复受损生态系统。因此不能仅因管理问卷或缺少生态实验就排除本稿。

适配条件是把保护—游憩协调具体联系到生态修复目标、实施过程、参与和决策障碍，而非只做一般公园满意度或管理类型描述。原稿“自然再生”定义同时包括恢复与既有自然的维护，应清楚区分两者，说明样本公园实际开展哪些恢复行动，并在现有数据允许范围内阐明对修复实践的贡献；不能将问卷管理行动解释成已证实生态恢复有效。

### Ecological Management & Restoration

ESA当前[期刊页面](https://www.ecolsoc.org.au/publications/journals/)仍列有本刊，2026年新文章与后续卷期元数据存在；没有依据称其停刊。ESA链接的[本刊关联项目站](https://emrprojects.wordpress.com/)有全刊范围原句：

> While the Journal focuses on Australasia, contributions from elsewhere will be considered if distinctly relevant to Australasia.

因此日本案例并非绝对禁止，但必须说明对澳大利亚／新西兰生态管理与修复的明确相关性。本稿目前以日本公园为核心、没有恢复监测结果，需较大幅度强化实践启示与地域可迁移性；不建议为了速度优先投入这本。项目站的800–1100词澳大利亚项目摘要是**非同行评议的Project Summaries栏目**，不能误当作本稿应选的研究文章类型，或套为全刊字数上限。

### City and Environment Interactions

通过[Elsevier官方Journal Finder](https://journalfinder.elsevier.com/results?query=City%20and%20Environment%20Interactions&mode=search)成功取得的范围，明确欢迎城市环境“both the natural and social sciences”，尤其重视与城市政策及利益相关者的联系。你的公园保护—游憩协调、管理主体与参与条件可据此组织投稿，需强调其城市环境治理和可持续性意义。

已发表直接相关题目为“Participatory environmentalism in practice: a mixed-methods analysis of stakeholder perceptions, participation and governance of urban green stewardship in a secondary city in Ghana”，[DOI 10.1016/j.cacint.2026.100458](https://doi.org/10.1016/j.cacint.2026.100458)。题名和出版商元数据已核，全文日期未取得，因此不把它纳入时长样本。“rapid open access forum”只是范围介绍，不是固定天数接收保证。

## 费用：普通发表与开放获取分开

|期刊|传统订阅发表|选择开放获取的标准APC（税另计）|当前价格来源|
|---|---|---|---|
|Landscape and Ecological Engineering|**无APC**，官网明确|**USD3,590／GBP2,390／EUR2,790**|[本刊出版费用页](https://link.springer.com/journal/11355/how-to-publish-with-us)，按接收日适用价格确定|
|Restoration Ecology|可选择订阅，**免这笔OA APC**；其他可能收费未完整核实|**USD3,460／GBP2,310／EUR2,880**|[Wiley官方Hybrid APC表](https://authors.wiley.com/asset/Wiley-Journal-APCs-OnlineOpen.xlsx)，本次在线重新下载，表内更新日2026-10-12，第1059行|
|Ecological Management & Restoration|可选择订阅，**免这笔OA APC**；其他可能收费未完整核实|**USD2,760／GBP1,840／EUR2,300**|同一[官方Hybrid APC表](https://authors.wiley.com/asset/Wiley-Journal-APCs-OnlineOpen.xlsx)，第346行|
|City and Environment Interactions|全OA，无传统订阅替代路线|**USD2,700**|本次[官方Journal Finder](https://journalfinder.elsevier.com/results?query=City%20and%20Environment%20Interactions&mode=search)准确刊名记录|

APC是论文处理／开放获取出版费，不应一概称为投稿时需支付的费用。Wiley[官方APC说明](https://authors.wiley.com/author-resources/Journal-Authors/open-access/article-publication-charges/index.html)按付款人账单地址决定币种；日本通常属“All other countries”，用USD报价，适用税另计。Wiley两刊作者页受访问限制，强制页费、会员费或彩图等条款未完整核实，因此“免OA APC”不扩大为“所有可能费用都保证为零”。Landscape and Ecological Engineering作者指南另明确彩图免费；可选纸质抽印不属于必需APC。

## 埼玉大学可能适用的支持

下列为用户提供资料和本次价格的条件性预算，**资格、接收日、额度和图书馆批准均须满足**：

|期刊／出版社|所给资料显示的可能支持|重要限制|
|---|---|---|
|Landscape and Ecological Engineering／Springer|合格混合刊原著若获转化协议额度，可按校内规则作者负担**5万日元／篇**|协议按接收日2025-01-01至2028-12-31；需埼玉所属通讯作者、大学邮箱、刊名资格、额度及批准。普通订阅发表不需要为OA名额付这5万日元|
|Restoration Ecology、Ecological Management & Restoration／Wiley|两刊均列入所给Hybrid OA表；合格原著若获校内额度，可按规则作者负担**5万日元／篇**|现有协议文件仅到**2026-12-31，按接收日，以后未定**。现在投稿若2027年接收，不能预先保证延续或名额|
|City and Environment Interactions／Elsevier|若符合埼玉通讯作者等资格和协议，**15%优惠后按当前价USD2,295＋税预算**|本地Q1表第2014行标Gold／DISCOUNT；它不属于Hybrid额度路线，不能套5万日元。Elsevier所给协议接收日区间至2027-03-31|

所依据原件：埼玉大学図書館.pdf、(2026.1～)Introduction_TransformativeAgreement(Japanese).pdf、Q1 2026 埼玉大学.xlsx及Wiley Hybrid表。没有把“学校有协议”当作本篇已获得资助，亦没有查询未公开的当前名额。

## 投稿至接收：逐篇日期

Landscape and Ecological Engineering按官网最新文章固定顺序，排短通讯和致谢后最先5篇Original Paper；Restoration Ecology按Crossref近期顺序排观点式贡献后，取最先5篇有经验研究摘要的条目。两本Wiley期刊具体文章子类型页面未能直接读取，其Received／Accepted来自出版社提交的Crossref publication_history；没有将created、deposited或published当作接收日。City为可公开取得原文的3篇便利样本，其中1篇为接收后Journal Pre-proof。

EMR保留最近7条完整历史；主表按顺序排除文化贡献（研究子类型未核）的70072后，取最先5条有研究内容的论文，包括70062，**没有为缩短天数跳过364天的文章**。这5篇虽可从题名／摘要判断研究内容，确切Wiley文章子类型仍未逐篇由原文确认，因此不能把它们写成严格核实的同一稿型统计。70068的161天例子为第6条研究内容记录，不进入固定前5样本；全部7条另存。

|期刊|论文／原始日期证据|Received|Accepted|自然日差|
|---|---|---|---|---:|
'''
for x in allrows:
 text+=f"|{x['journal']}|[{x['title']}]({x['url']})；DOI {x['doi']}|{x['received']}|{x['accepted']}|{x['days']}|\n"
text+='''
**首次决定的补充说明：** Landscape and Ecological Engineering官网首页当前显示“Submission to first decision (median) 19 days”，不能称19天接收；City官方Finder内的timeToAcceptance字段存在标签含义冲突，数值5没有作为接收时间使用。Wiley两刊全刊总接收指标本次未核实。上述样本均含修稿时间且仅包含已接收条目，有发表选择和小样本限制。

## 对现稿的共同准备要求

四刊的主题符合都不等于现行日文TXT可直接提交。完成英文投稿稿、按选定期刊整理作者信息、伦理承认／免除依据、数据利用声明和补充材料。原稿已有同意、非同定化、资金、利益冲突、作者贡献及AI简述，不应误写成这些全部缺失。

方法上，39公园且部分同属34管理团体、复杂探索SEM、同样本模型调整和指标编码，是可能影响审稿及修稿轮次的实质问题；不能宣称单凭39例就违反这些期刊最低样本门槛。本稿应坚持探索性关联解释，不能把SEM路径当因果证明，把NDVI当恢复成效验证。若速度是第一目标，应同时权衡主题适配和方法准备，不能仅根据小样本时长排序。

证据目录：`.four_ecology_journals_20261109`。各刊官方页面快照、访问记录、价格表、原文日期、样本选择及计算均保留；原始论文和学校资料未改动。本次未投稿或联系编辑部。
'''
target=ROOT/'39公园论文_四本生态与城市期刊投稿适配费用及接收时间_2026-11-09.md'
target.write_text(text,encoding='utf-8')
assert summary['Ecological Management & Restoration']['days']==[275,265,364,225,508]
assert summary['Ecological Management & Restoration']['median']==275
print(json.dumps(summary,ensure_ascii=True,indent=2))
print('Report bytes:',target.stat().st_size,'article histories:',len(allrows))
