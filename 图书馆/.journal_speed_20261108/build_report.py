from pathlib import Path
import json,csv,re,statistics,datetime

ROOT=Path(__file__).resolve().parent.parent
WORK=Path(__file__).parent
OUT=ROOT/'17号论文_68项期刊官网核验与速度优先建议_2026-11-08.md'
CSV=ROOT/'17号论文_68项期刊逐刊核验表_2026-11-08.csv'
HISTORY_CSV=ROOT/'17号论文_50篇近期研究论文收稿接收日期_2026-11-08.csv'

ORDER='''Sustainable Cities and Society
Forest Science
Discover Cities
Journal of Environmental Management
Land Use Policy
Journal of Environmental Planning and Management
Urban Ecosystems
Journal of Outdoor Recreation and Tourism
Land
Urban Science
Global Journal of Environmental Science and Management
Regional Sustainability
Environmental Earth Sciences
Trends in Sciences
Environmental Engineering and Management Journal
Jordan Journal of Earth and Environmental Sciences
Maejo International Journal of Science and Technology
Environmental Education Research
Environmental Management
Landscape Research
Landscape Ecology
People and Nature
Land Degradation & Development
Forestry: An International Journal
Journal of Environmental Law
Architectural Research Quarterly
Environmental Conservation
Science of The Total Environment
Environmental Technology & Innovation
Environment & Ecology
Global Ecology and Conservation
Ecological Indicators
Heliyon
Forest Ecology and Management
Discover Environment
Discover Sustainability
Frontiers in Sustainable Cities
Urban Biodiversity and Ecosystem Services
Building and Environment
Biological Conservation
Journal of Urban Ecology
Urban Design International
Diversity
Frontiers in Ecology and Evolution
PeerJ
Frontiers in Conservation Science
Frontiers in Environmental Science
Environmental and Sustainability Indicators
Cities
Habitat International
Applied Geography
Ecology & Ecosystem Services
Ecosystem Services
Ecological Engineering
Environmental Science & Policy
Environmental Impact Assessment Review
Resources, Conservation and Recycling
Journal of Cleaner Production
Urban Agriculture and Forestry
Built Environment
Urban Planning, Design and Transport
Urban Health and Well-being
Current Science
Applied Sciences-Basel
Environment, Development and Sustainability
Journal of Urban Planning and Development
Ecotoxicology and Environmental Safety
Environmental Research'''.splitlines()
assert len(ORDER)==68

E=json.loads((WORK/'elsevier_summary.json').read_text(encoding='utf-8'))
S=json.loads((WORK/'springer_summary.json').read_text(encoding='utf-8'))
M=json.loads((WORK/'mdpi_six_journals_recent5_selected.json').read_text(encoding='utf-8'))
P=json.loads((WORK/'springer_sample_selected.json').read_text(encoding='utf-8'))
SAMPLE_TITLES={'land':'Land','urbansci':'Urban Science','environments':'Environments','sustainability':'Sustainability','conservation':'Conservation','diversity':'Diversity'}
MS={}
for slug,title in SAMPLE_TITLES.items():
    articles=[a for a in M['selected'] if a['journal_slug']==slug]
    days=[a['submission_to_acceptance_days'] for a in articles]
    assert len(articles)==5
    for a in articles:
        assert a['article_type']=='research-article'
        assert (datetime.date.fromisoformat(a['history']['accepted'])-datetime.date.fromisoformat(a['history']['received'])).days==a['submission_to_acceptance_days']
    MS[title]={'articles':articles,'days':days,'median':statistics.median(days),'min':min(days),'max':max(days)}
def norm(t):return re.sub(r'[^a-z0-9]','',t.lower().replace('&','and'))
rows={}
for x in E:
    f=x['first_decision_days']; fees=x['local_fee_table']
    status='官方Finder范围/初决已核；ScienceDirect Insights 403' if f is not None else '官方Finder范围已核；初决未取得；ScienceDirect Insights 403'
    fit='总范围可考虑，具体栏目待核' if x['title']=='Heliyon' else x['fit']
    rows[norm(x['title'])]=dict(title=x['title'],url=x['official_finder_url'],fit=fit,reason=x['reason'],first=f'{f}天；官网Finder初决，统计口径未明' if f is not None else '未取得',first_days=f,total='未取得全刊统计',status=status,fee='；'.join(f"表第{p['row']}行：{p['bucket']}/{p['eligibility']}" for p in fees) or '所给名单未命中')
for title,x in S.items():
    f=x['first_decision']['days']; a=x['acceptance']
    total=f"未取得全刊统计；近期5篇样本中位{a['sample_median']}天（{a['sample_min']}–{a['sample_max']}）" if a['sample_n'] else '未取得全刊统计'
    rows[norm(title)]=dict(title=title,url=x['url'],fit=x['fit'],reason=x['reason'],first=f'{f}天；官网中位数' if f is not None else '未取得',first_days=f,total=total,status='主页/范围可读，200' if x['status']==200 else '官网403，范围判断仅为学科初筛',fee='见学校协议及逐刊资格，非时效证据')

def add(title,url,fit,reason,first=None,total='未取得全刊统计',status='官网可读',fee='未核具体费用'):
    rows[norm(title)]=dict(title=title,url=url,fit=fit,reason=reason,first=f'{first}天；中国官网中位数' if isinstance(first,int) else first or '未取得',first_days=first if isinstance(first,int) else None,total=total,status=status,fee=fee)

MDPI=[('Land','land','较适合','景观/土地管理、都市绿地治理',16),('Urban Science','urbansci','较适合','城市公园与绿地管理，已有接近题材先例',20),('Diversity','diversity','有条件','需明确生物多样性保全贡献，现稿没有多样性效果测量',14),('Applied Sciences-Basel','applsci','不优先','正式刊名Applied Sciences；现稿缺应用技术/工程贡献',15),('Environments','environments','较适合','环境管理、保全与管理实践',18),('Sustainability','sustainability','较适合','可持续公园管理和多主体治理',16),('Conservation','conservation','有条件','保全实践及社会管理相关，最新英文Scope未取到',23),('Forests','forests','有条件','须以森林/林地经营为核心，不能把全部公园自动视为森林',17)]
for t,slug,fit,reason,first in MDPI:
    add(t,f'https://www.mdpi.com/journal/{slug}',fit,reason,first,status='中国官方API/前端标签已核；英文主页403，最新英文Scope未取到',fee='学校资料：MDPI APC 10%折扣，非免费')
    if t in MS:
        a=MS[t]
        rows[norm(t)]['total']=f"未取得全刊统计；近期5篇样本中位{a['median']:g}天（{a['min']}–{a['max']}）"
add('Global Journal of Environmental Science and Management','https://www.gjesm.net/','有条件','环境管理/治理相关；最新Scope未读',status='官网403')
add('Trends in Sciences','https://tis.wu.ac.th/tishome/','有条件，匹配较弱','范围列Ecology，但以自然/应用科学为主，现稿管理社会调查需确认范围','1–3天编辑初筛；外审4–6周，再1–2周编辑决定','官网列50天；未注明统计年度、均值/中位数','主页及范围/审稿流程200')
add('Environmental Engineering and Management Journal','https://eemj.eu/index.php/EEMJ/about/editorialPolicies','有条件','范围含综合环境管理、政策与可持续发展；可从实施管理切入',status='Scope200；无可用时长数字')
add('Jordan Journal of Earth and Environmental Sciences','https://jjees.hu.edu.jo/','不优先','以地球/环境自然科学为主，公园管理行为的直接匹配弱',status='官网及作者指南可读，无时效')
add('Maejo International Journal of Science and Technology','https://mijst.mju.ac.th/','不优先','综合科技期刊；公园治理社会调查的范围匹配未证实',status='SSL证书验证失败，最新范围/时效未核')
add('Environment & Ecology','https://environmentandecology.com/','不优先','现稿缺生态过程/效果数据；最新Scope未读',status='官网406')
add('Frontiers in Sustainable Cities','https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about','较适合','Urban Greening栏目明确收绿蓝空间治理、使用、管理与生物多样性',total='未取得全刊统计；相近单篇128天',status='主页及Urban Greening Scope200')
add('Frontiers in Ecology and Evolution','https://www.frontiersin.org/journals/ecology-and-evolution/about','不优先','需要生态/演化概念或城市生物过程贡献；本稿管理行为为主',status='主页/About及相关栏目可读')
add('PeerJ','https://peerj.com/journals/peerj/aims-and-scope/','有条件','环境/保全研究可考虑，须证明方法与报告质量',status='官网及公开前端可读；32天属接收后出版')
add('Frontiers in Conservation Science','https://www.frontiersin.org/journals/conservation-science/sections/conservation-social-sciences-indigenous-and-local-knowledge/about','较适合','保全社会科学栏目明确收保全管理的人类维度、协作及决策',total='未取得全刊统计；相近社会调查单篇186天',status='主页及保全社会科学Scope200')
add('Frontiers in Environmental Science','https://www.frontiersin.org/journals/environmental-science/about','有条件','环境管理/政策治理栏目相关；选栏目时突出管理实施',status='主页及About可读')
add('Built Environment','https://www.alexandrinepress.co.uk/built-environment','有条件，非首选','城市公共空间/治理相关，需核主题专刊及主动投稿规则',status='出版社官网403')
add('Current Science','https://www.currentscience.ac.in/','不优先','综合科学取向，现稿的普适科学贡献和范围尚未证实',status='官网307及JavaScript防护')
add('Journal of Urban Planning and Development','https://ascelibrary.org/journal/jupddm','有条件','需突出都市公园规划、治理和决策贡献；最新Scope未读',status='ASCE官网403')
for t in ['Urban Agriculture and Forestry','Urban Planning, Design and Transport','Urban Health and Well-being']:
    add(t,'https://link.springer.com/journal/44327/aims-and-scope','已核为主题类别','此完整名称是Discover Cities官网Topics中的类别；不能据此作为独立期刊重复计算',first='不适用',total='归入Discover Cities',status='Discover Cities Scope200')
for t in ['Urban Biodiversity and Ecosystem Services','Ecology & Ecosystem Services']:
    add(t,'','独立刊名未证实','未取得该精确刊名对应的期刊官方主页/ISSN；不能与已证实的刊混排',first='不适用/未证实',total='不适用/未证实',status='身份待确认')

for filename in ['elsevier_api_all.json','elsevier_extra_api_all.json']:
    for record in json.loads((WORK/filename).read_text(encoding='utf-8')):
        title=record['requested_title']; x=rows.get(norm(title))
        if x is None: continue
        for item in record.get('response',{}).get('results',[]):
            if norm(item['title'])!=norm(title): continue
            guide=item.get('links',{}).get('guideForAuthors') or ''
            match=re.match(r'https://www\.sciencedirect\.com/journal/[^/]+',guide)
            if match:
                x['source_url']=x['url']
                x['url']=match.group()
            break
for t,slug,*_ in MDPI:
    rows[norm(t)]['source_url']='https://mdpi.cn/api/journals'

out=[]
for i,t in enumerate(ORDER,1):
    x=rows.get(norm(t))
    assert x is not None,t
    out.append({'序号':i,'用户刊名':t,'判断':x['fit'],'理由':x['reason'],'首次决定天数':x['first_days'],'首次决定说明':x['first'],'投稿至接收':x['total'],'核验状态':x['status'],'官网':x['url'],'官方时效来源':x.get('source_url',x['url']),'学校资料费用资格':x['fee']})

def mdrow(x):
    link=f"[{x['用户刊名']}]({x['官网']})" if x['官网'] else x['用户刊名']
    if x['官方时效来源'] and x['官方时效来源']!=x['官网']:
        link+=f"；[时效来源]({x['官方时效来源']})"
    return f"|{x['序号']}|{link}|{x['判断']}：{x['理由']}|{x['首次决定说明']}|{x['投稿至接收']}|{x['核验状态']}|"

def sample_table():
    lines=['|期刊及官网|官网首次决定中位数|近期5篇投稿至接收：样本中位数|5篇范围|本稿适配判断|','|---|---:|---:|---:|---|']
    for t in ['Land','Urban Science','Environments','Sustainability','Conservation','Diversity']:
        a=MS[t]; x=rows[norm(t)]
        lines.append(f"|[{t}]({x['url']})|{x['first_days']}天|{a['median']:g}天|{a['min']}–{a['max']}天|{x['fit']}：{x['reason']}|")
    for t in ['Discover Cities','Discover Environment','Discover Sustainability','Environmental Management']:
        a=S[t]['acceptance']; x=rows[norm(t)]
        lines.append(f"|[{t}]({x['url']})|{x['first_days']}天|{a['sample_median']}天|{a['sample_min']}–{a['sample_max']}天|{x['fit']}：{x['reason']}|")
    return '\n'.join(lines)

def sample_details():
    lines=['\n\n**MDPI六刊：30篇近期研究论文的官网日期明细**','',
           '取Crossref按发表日期降序返回的近期候选，逐篇读取官方XML，依次取每刊前5篇日期有效的research-article；未按速度筛选。已排除综述、社论、撤稿记录。该抽样不是随机抽样，也未限制为与本稿相同题材。以下链接直接打开含收稿及接收日期的官方XML。','',
           '|期刊|文章题名及官方XML|DOI|Received|Accepted|投稿至接收|','|---|---|---|---|---|---:|']
    for a in M['selected']:
        title=a['title'].replace('|','\\|')
        lines.append(f"|{SAMPLE_TITLES[a['journal_slug']]}|[{title}]({a['url']})|{a['doi']}|{a['history']['received']}|{a['history']['accepted']}|{a['submission_to_acceptance_days']}天|")
    lines+=['','**Springer四刊：20篇近期研究论文的官网日期明细**','',
            '取各刊官网列表中的近期Research文章，每刊5篇；以下为文章页面About this article的Received、Accepted日期。样本选择、文章类型及原网页上下文保留在证据目录。','',
            '|期刊|文章题名及官网|Received|Accepted|投稿至接收|','|---|---|---|---|---:|']
    for a in P:
        title=a['title'].split(' | ')[0].replace('|','\\|')
        received=datetime.datetime.strptime(a['Received'],'%d %B %Y').date()
        accepted=datetime.datetime.strptime(a['Accepted'],'%d %B %Y').date()
        assert (accepted-received).days==a['days']
        lines.append(f"|{a['journal']}|[{title}]({a['url']})|{received.isoformat()}|{accepted.isoformat()}|{a['days']}天|")
    return '\n'.join(lines)+'\n'

def build():
    text=(WORK/'report_intro.md').read_text(encoding='utf-8').replace('{{SAMPLE_TABLE}}',sample_table())
    text+='\n\n**您所列68项，按原顺序逐一核查**\n\n'
    text+='“未取得”不等于官网从未公布，也不等于慢；表示本次没有取得足以引用的最新数字。适投判断针对现稿，不等于编辑保证送审。全部时长为天/自然日，周另标。涉及403等访问失败的条目，范围判断仅是学科初筛。\n\n'
    text+='|序号|期刊及官网入口|现稿是否适合|首次决定|投稿至接收|核验状态|\n|---:|---|---|---|---|---|\n'
    text+='\n'.join(map(mdrow,out))+'\n'
    text+='\n\n**补充主题候选**\n\n这些补充刊也不能全部认定为接收快。\n\n|期刊及官网|适配理由|首次决定|投稿至接收|\n|---|---|---|---|\n'
    for t in ['Environments','Sustainability','Conservation','Journal for Nature Conservation','Current Research in Environmental Sustainability','City and Environment Interactions','Trees, Forests and People','Forests']:
        x=rows[norm(t)]
        text+=f"|[{t}]({x['url']})|{x['fit']}：{x['reason']}|{x['first']}|{x['total']}|\n"
    text+='\nConservation Science and Practice、Ecological Solutions and Evidence也与保全实践相关；本次Wiley官网403，未取得时效，故不列作已证实快刊。Environmental Challenges最新官方Scope提示可能不考虑“surveys without environmental outcome metrics”，现稿缺环境结果测量，不沿用旧报告中对它的宽泛推荐。\n'
    text+=(WORK/'report_end.md').read_text(encoding='utf-8')
    text+=sample_details()
    assert '{{' not in text
    OUT.write_text(text,encoding='utf-8')
    with CSV.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
    history=[]
    for a in M['selected']:
        history.append({'期刊':SAMPLE_TITLES[a['journal_slug']],'题名':a['title'],'类型':a['article_type'],'DOI':a['doi'],'Received':a['history']['received'],'Accepted':a['history']['accepted'],'投稿至接收天数':a['submission_to_acceptance_days'],'官网日期来源':a['url']})
    for a in P:
        history.append({'期刊':a['journal'],'题名':a['title'].split(' | ')[0],'类型':'Research','DOI':a['doi'],'Received':datetime.datetime.strptime(a['Received'],'%d %B %Y').date().isoformat(),'Accepted':datetime.datetime.strptime(a['Accepted'],'%d %B %Y').date().isoformat(),'投稿至接收天数':a['days'],'官网日期来源':a['url']})
    with HISTORY_CSV.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=history[0].keys());w.writeheader();w.writerows(history)
    (WORK/'all_68_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(OUT),'csv':str(CSV),'rows':len(out),'history_csv':str(HISTORY_CSV),'history_rows':len(history),'unmapped':[]},ensure_ascii=False))

if __name__=='__main__':build()
