from pathlib import Path
import json,csv,re,statistics,datetime,html
ROOT=Path(__file__).resolve().parent.parent
WORK=Path(__file__).parent
OUT=ROOT/'17号论文_四刊费用与非MDPI速度优先选刊_2026-11-09.md'
CSV=ROOT/'17号论文_非MDPI近期收稿接收日期_2026-11-09.csv'
ORIGINAL=json.loads((WORK/'all_68_summary.json').read_text(encoding='utf-8'))
BYTITLE={x['用户刊名']:x for x in ORIGINAL}
SECTIONS=json.loads((WORK/'nonmdpi_section_histories_selected_20261109.json').read_text(encoding='utf-8'))
OTHER=json.loads((WORK/'non_mdpi_urban_ecosystems_enc_20261109.json').read_text(encoding='utf-8'))
PRIOR=json.loads((WORK/'springer_sample_selected.json').read_text(encoding='utf-8'))
S=json.loads((WORK/'springer_summary.json').read_text(encoding='utf-8'))
NAMES={'urban-greening':'Urban Greening','conservation-social-sciences-indigenous-and-local-knowledge':'Conservation Social Sciences & Indigenous and Local Knowledge','environmental-economics-and-management':'Environmental Economics and Management'}
FEES=[('Land','land','2073-445X'),('Urban Science','urbansci','2413-8851'),('Environments','environments','2076-3298'),('Sustainability','sustainability','2071-1050')]
def iso(date):return datetime.datetime.strptime(date,'%d %B %Y').date().isoformat()
def safe(t):return html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',str(t)))).strip().replace('|','\\|')
history=[]
for a in SECTIONS:
 history.append(dict(journal=a['journal'],section=NAMES[a['section']],title=a['title'],doi=a['doi'],received=iso(a['Received']),accepted=iso(a['Accepted']),days=a['days'],url=a['url'],sample='栏目官网固定前5篇已接收Original Research（含接受稿）',date='2026-11-09'))
for a in OTHER['urban_ecosystems']['articles']:
 history.append(dict(journal='Urban Ecosystems',section='全刊',title=a['title'].split(' | ')[0],doi=a['doi'],received=a['received_iso'],accepted=a['accepted_iso'],days=a['days'],url=a['url'],sample='官网列表前5篇Research',date='2026-11-09'))
for a in OTHER['environmental_conservation']['articles']:
 if not a.get('days'):continue
 history.append(dict(journal='Environmental Conservation',section='全刊',title=a['title'],doi=a.get('doi',''),received=a['received_iso'],accepted=a['accepted_iso'],days=a['days'],url=a.get('pdf_url',a.get('url','')),sample='FirstView前5篇原始研究/Report中3篇日期可核，2篇缺失',date='2026-11-09'))
for a in PRIOR:
 history.append(dict(journal=a['journal'],section='全刊',title=a['title'].split(' | ')[0],doi=a['doi'],received=iso(a['Received']),accepted=iso(a['Accepted']),days=a['days'],url=a['url'],sample='官网列表每刊5篇Research，复用前一日核查',date='2026-11-08'))
EXTRAS=json.loads((WORK/'nonmdpi_elsevier_verified_histories.json').read_text(encoding='utf-8'))
for a in EXTRAS:
 conceptual=a['kind'].startswith('Conceptual')
 history.append(dict(journal=a['journal'],section='单篇概念框架（单列）' if conceptual else '全刊便利样本',title=a['title'],doi=a['doi'],received=a['received'],accepted=a['accepted'],days=a['days'],url=a['url'],sample='公开机构库保存的原刊排版PDF，概念框架，单列' if conceptual else '公开机构库保存的原刊排版PDF，可下载便利样本，每刊2篇',date='2026-11-09'))
def stat(title,section=None):
 group=[a for a in history if a['journal']==title and (section is None or a['section']==section)]
 days=[a['days'] for a in group]
 return len(days),statistics.median(days),min(days),max(days)
def build():
 text='''**17号论文：四刊费用与非MDPI速度优先选刊**

补充核查日期：2026年11月9日；复用的Springer四刊样本于11月8日核查。以已全文核读的日本39公园/34管理团体、自然恢复与保全—游憩协调的管理者问卷及探索性SEM论文为依据。继续排除Urban Forestry & Urban Greening、Landscape and Urban Planning；本次速度建议同时排除全部MDPI。

**先回答四刊费用：以下是可追溯公开数据库的APC预算参考，现行官网价格尚未最终确认。** 四刊官方APC正文均遇403，不能把二手目录金额写成2026年11月9日官网现价。Land、Urban Science有DOAJ及OpenAlex相同金额；Environments、Sustainability取得OpenAlex价格记录。

|期刊及官方收费入口|公开记录APC预算|符合埼玉大学10%折扣时|价格证据|
|---|---:|---:|---|
'''
 for name,slug,issn in FEES:
  d=json.loads((WORK/f'root_apc_openalex_{slug}_20261109.json').read_text(encoding='utf-8'))
  price=next(x['price'] for x in d['apc_prices'] if x['currency']=='CHF')
  source=f'[OpenAlex记录](https://api.openalex.org/sources/issn:{issn})'
  if slug in ['land','urbansci']:source+=f'；[DOAJ记录](https://doaj.org/api/search/journals/issn:{issn})'
  text+=f'|[{name}](https://www.mdpi.com/journal/{slug}/apc)|{price:,} CHF|{price*0.9:,.0f} CHF|{source}|\n'
 text+='''
CHF为瑞士法郎，每篇论文计费。OpenAlex四条记录整体更新时间均为2026-11-08；Land、Urban Science的DOAJ记录整体更新于2026-09-17。**元数据更新日不等于APC价格生效日**，尤其不能由数据库的最近更新推断价格已逐项更新。此表适合初步预算，最终金额仍须以实际适用的官网标价/发票确认；未计可能适用的税费、汇率与额外服务，也未假设其他优惠可叠加。

埼玉大学所给《埼玉大学図書館2.pdf》明确：MDPI全部期刊APC享10%折扣，符合所属条件的通讯作者或共作者均可利用；应使用埼玉大学邮箱确保识别。[MDPI官方IOAP说明](https://mdpi.cn/ioap)亦载一般10%优惠。本次没有重新在线确认学校当前参与资格或本稿最终折扣。所给资料对MDPI支持的是九折条件，不能套用其他出版社每篇5万日元的额度制度。

**排除MDPI后，我建议优先考察Frontiers in Sustainable Cities的Urban Greening栏目。** 其城市绿地治理、使用、管理与生物多样性范围与本稿最直接。其次为Frontiers in Conservation Science的保全社会科学栏目；Frontiers in Environmental Science的环境经济与管理栏目是条件候选，需要清楚呈现环境管理机制、可迁移贡献及方法可靠性。

这份建议依据主题与实际已接收文章历史。没有取得覆盖全部候选、同一统计窗口的全刊投稿至接收数字，故无法证明其中任何一本是所有非MDPI期刊中绝对最快。下面按样本历时列出已取得日期证据的候选；小样本之间几天、几周的差异不能当成全刊真实差异。

|期刊/已核栏目及官网|本稿匹配判断|已核样本数|投稿至接收样本中位数|样本范围|
|---|---|---:|---:|---:|
'''
 entries=[
 ('Frontiers in Sustainable Cities','Urban Greening','https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about','较贴合：都市公园及绿地治理、保全—利用协调；优先考察'),
 ('Frontiers in Conservation Science',NAMES['conservation-social-sciences-indigenous-and-local-knowledge'],'https://www.frontiersin.org/journals/conservation-science/sections/conservation-social-sciences-indigenous-and-local-knowledge/about','较贴合：保全的人类维度、协作、管理与决策'),
 ('Frontiers in Environmental Science','Environmental Economics and Management','https://www.frontiersin.org/journals/environmental-science/sections/environmental-economics-and-management/about','有条件：自然资源可持续管理，需管理机制/方法贡献'),
 ('Urban Ecosystems',None,'https://link.springer.com/journal/11252/aims-and-scope','社会—生态与管理相关，需清楚交代生态学贡献'),
 ('Discover Cities',None,'https://link.springer.com/journal/44327/aims-and-scope','较贴合都市公园治理，样本历时较长'),
 ('Discover Environment',None,'https://link.springer.com/journal/44274/aims-and-scope','环境、保全恢复及政策相关'),
 ('Discover Sustainability',None,'https://link.springer.com/journal/43621/aims-and-scope','可持续管理、环境行为及治理相关'),
 ('Environmental Management',None,'https://link.springer.com/journal/267/aims-and-scope','自然资源保全管理及社会科学较贴合'),
 ('Environmental Conservation',None,'https://www.cambridge.org/core/journals/environmental-conservation/information/author-instructions','保全实践与管理较贴合；5篇中仅3篇日期可核')]
 for name,section,url,fit in entries:
  n,med,lo,hi=stat(name,section)
  label=name+(f' — {section}' if section else '')
  text+=f'|[{label}]({url})|{fit}|{n}|{med:g}天|{lo}–{hi}天|\n'
 text+='''
前三刊为**相应栏目的近期已接收Original Research**，依官网文章列表原顺序取前5篇，包含正式版尚未出版的接受稿；没有按速度挑选。其余为全刊近期研究样本，Environmental Conservation有2篇历史缺失。各组题材和抽样框仍有差别，不能精确统一排名。Received→Accepted按自然日计算，包含作者修稿时间；所有样本均存在接受稿/发表选择及小样本限制。

Urban Ecosystems的901天案例（2024-04-04→2026-09-22）真实保留，未为了缩短范围而删除。其官网首次决定7天不能代替接收历时。Frontiers in Environmental Science全刊另取5篇的中位数为51天，但相应环境经济与管理栏目为84天；本报告优先展示更相关栏目，不能拿其他栏目较快的技术论文预测本稿。Urban Greening中研究Green Care的182天案例也保留在样本中。

**与你题材更接近的单篇先例**

'''
 examples=['10.3389/frsc.2026.1883980','10.3389/fcosc.2026.1943380','10.3389/fcosc.2026.1977380']
 for doi in examples:
  a=next(a for a in history if a['doi']==doi)
  text+=f"- [{safe(a['title'])}]({a['url']})（{a['journal']}）：{a['received']}投稿，{a['accepted']}接收，{a['days']}天。\n"
 text+='''
以上分别涉及公共公园参与、游憩公园周边保全感知、环境认同与亲环境行为，可作社会调查题材先例。它们与本稿的对象、样本数和模型不同，不能由题材先例推断39公园的探索性SEM必然获接收。

**其他题材候选及接收速度证据的边界**

Journal of Outdoor Recreation and Tourism、Journal for Nature Conservation、Journal of Environmental Management、Current Research in Environmental Sustainability均与本稿有较明确主题联系，仍应保留为题材候选。四刊本次官网Insights受访问限制；官方Finder的timeToAcceptance显示标签存在冲突，不能当总接收时间。机构库保存原刊PDF中找到的少量历史另列于证据报告；不能按个别可下载论文为四刊作全刊速度排名。

|候选及官网|适配理由|目前能否据证据称为接收快|
|---|---|---|
'''
 E=json.loads((WORK/'elsevier_summary.json').read_text(encoding='utf-8'))
 by={a['title']:a for a in E}
 for title in ['Journal of Outdoor Recreation and Tourism','Journal for Nature Conservation','Journal of Environmental Management','Current Research in Environmental Sustainability']:
  a=by[title]
  extra_home={'Journal for Nature Conservation':'https://www.sciencedirect.com/journal/journal-for-nature-conservation','Current Research in Environmental Sustainability':'https://www.sciencedirect.com/journal/current-research-in-environmental-sustainability'}
  url=BYTITLE.get(title,{}).get('官网',extra_home.get(title,a['official_finder_url']))
  text+=f"|[{title}]({url})|{a['reason']}|未取得可靠全刊统计，不能认定为最快|\n"
 text+='''
补取得的机构库原刊PDF显示：JORT两篇实证研究为299、298天；Current Research in Environmental Sustainability两篇实证/资料分析为246、270天，另有概念框架文章124天单列。它们是可下载PDF的便利样本，不能当全刊中位数；但目前没有证据支持将这两刊作为1—2个月接收的首选。Journal for Nature Conservation和Journal of Environmental Management仍未核得同时含Received、Accepted的有效样本。[原刊PDF与日期明细](.journal_speed_20261108/nonmdpi_elsevier_findings.md)保留了全部来源。
'''
 text+='''
Journal of Environmental Planning and Management、Landscape Research、People and Nature、Journal of Urban Ecology、Environment, Development and Sustainability、Global Journal of Environmental Science and Management、Environmental Engineering and Management Journal、PeerJ、Journal of Urban Planning and Development也有主题交集，详见下表。最新范围/时效未完整核实的，不列入“已证实快速接收”名单。

Trends in Sciences官网再次核得“Submission to Acceptance 50 days”，但未给统计年度、样本、均值或中位数。[范围](https://tis.wu.ac.th/tishome/AimsandScope.php)以生物/医学、物理、应用科学为主，虽列Ecology，本稿公园管理者社会问卷的直接匹配弱。因此不将其放在“主题一致且速度优先”的主推名单。其1–3天是编辑初筛，外审流程写4–6周，之后再1–2周编辑决定。

**其余有主题交集的非MDPI候选：可投条件及时间状态**

下表保留需要重新定位或进一步核范围的候选，方便查看；“有条件”不等于现稿直接适投或接收快。

|期刊及官网|针对现稿的判断|首次决定（供参考）|投稿至接收|
|---|---|---|---|
'''
 titles=['Journal of Environmental Planning and Management','Landscape Research','People and Nature','Journal of Urban Ecology','Environment, Development and Sustainability','Global Journal of Environmental Science and Management','Environmental Engineering and Management Journal','PeerJ','Journal of Urban Planning and Development','Sustainable Cities and Society','Regional Sustainability','Land Use Policy','Biological Conservation','Cities','Habitat International','Ecosystem Services','Environmental Science & Policy','Urban Design International','Built Environment']
 for title in titles:
  a=BYTITLE[title]
  text+=f"|[{title}]({a['官网']})|{a['判断']}：{a['理由']}|{a['首次决定说明']}|{a['投稿至接收']}|\n"
 for title in ['City and Environment Interactions','Trees, Forests and People']:
  a=by[title];text+=f"|[{title}]({a['official_finder_url']})|{a['reason']}|{a['first_decision_days']}天，Finder口径/窗口未明|未取得全刊统计|\n"
 text+='''
Conservation Science and Practice、Ecological Solutions and Evidence也有保全实践交集，但Wiley官方时效未取得，本次不将它们列为快刊。Forest Science、Forestry、Forest Ecology and Management等森林专业刊要求以森林为核心，不能把跨类型公园自动视为森林；Ecological Indicators等要求指标贡献，现稿不直接满足。本稿没有生态结果、工程性能、污染/健康结局的实测，其他自然/工程/健康方向刊不因初决短而升级推荐。

**本次新增及复用的实际日期明细**

|期刊/栏目|文章及原始日期来源（官网或原刊PDF）|Received|Accepted|自然日|取样说明|
|---|---|---|---|---:|---|
'''
 for a in history:
  text+=f"|{a['journal']} / {a['section']}|[{safe(a['title'])}]({a['url']})|{a['received']}|{a['accepted']}|{a['days']}|{a['sample']}，核查{a['date']}|\n"
 text+='''
全部原始网页、官方日期记录和计算保留在`.journal_speed_20261108`。本次较前一次答复补充了Frontiers相应栏目、Urban Ecosystems及Environmental Conservation的日期证据；前一次只用Frontiers单篇128/186天的记录，不足以代表这些栏目。

- [Frontiers三个栏目15篇接受稿历史](.journal_speed_20261108/nonmdpi_section_histories_selected_20261109.json)
- [Urban Ecosystems、Environmental Conservation补充核查](.journal_speed_20261108/non_mdpi_urban_ecosystems_enc_20261109.md)
- [四刊费用来源与核查限制](.journal_speed_20261108/mdpi_four_apc_20261109.md)
- [Elsevier四刊追加核查及原刊PDF](.journal_speed_20261108/nonmdpi_elsevier_findings.md)
- [原68项逐刊报告](17号论文_68项期刊官网核验与速度优先建议_2026-11-08.md)
'''
 assert '{{' not in text and 'title from article' not in text
 OUT.write_text(text,encoding='utf-8')
 for a in history:assert (datetime.date.fromisoformat(a['accepted'])-datetime.date.fromisoformat(a['received'])).days==a['days']
 with CSV.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(history[0]));w.writeheader();w.writerows(history)
 print(json.dumps({'report':str(OUT),'csv':str(CSV),'histories':len(history)},ensure_ascii=False))
if __name__=='__main__':build()
