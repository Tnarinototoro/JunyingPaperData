import json,pathlib,statistics
p=pathlib.Path(__file__).parent
data=json.loads((p/'springer_other_evidence.json').read_text(encoding='utf8'))['results']
meta={
'Forest Science':('弱','森林科学/森林经营不是现稿研究核心',None),
'Discover Cities':('高','城市公园治理/城市绿地管理属于城市科学及政策实践',17),
'Journal of Environmental Planning and Management':('中高','需要突出规划、管理组织及实施机制；scope未最新核验',None),
'Urban Ecosystems':('中高','scope明确收社会经济—生态关系、政策与社会/人类生态',7),
'Environmental Earth Sciences':('低','地球系统/地质过程与风险为核心，现稿未涉及',37),
'Environmental Education Research':('低','缺少环境教育/学习研究设计；scope未最新核验',None),
'Environmental Management':('高','scope明确收环境及自然资源保全管理、社会学科及国际相关案例',9),
'Landscape Research':('中高','景观管理及社会维度相关；scope未最新核验',None),
'Landscape Ecology':('低','scope要求空间显式格局—生态过程贡献，辅助NDVI不足',10),
'People and Nature':('中','人—自然/保全治理相关，需加强概念贡献；scope未最新核验',None),
'Land Degradation & Development':('低','未研究退化过程或恢复成效；scope未最新核验',None),
'Forestry: An International Journal':('弱','需要以森林经营/森林科学为核心；scope未最新核验',None),
'Journal of Environmental Law':('低','缺少环境法核心研究问题；scope未最新核验',None),
'Architectural Research Quarterly':('低','建筑研究与现稿公园保全管理受众不一致',None),
'Environmental Conservation':('高','scope明确保全科学与实践，需保全目标及国际贡献；6000词/6图表',None),
'Discover Environment':('中高','scope含生态、生物多样性、保全恢复、城市环境及政策',20),
'Discover Sustainability':('高','scope含保全、城市化、环境行为、治理、资源管理及实施',17),
'Journal of Urban Ecology':('中','城市社会生态/管理相关，需要生态学问题；scope未最新核验',None),
'Urban Design International':('中低','需要城市设计新知识，另有不收主要源于学位论文等明确规则',15),
'Environment, Development and Sustainability':('中高','需可持续管理多维度与可迁移地方实施贡献',21)}
samples=json.loads((p/'springer_sample_selected.json').read_text(encoding='utf8'))
out={}
for r in data:
 n=r['journal'];fit,reason,fd=meta[n]
 vals=[x['days'] for x in samples if x['journal']==n]
 out[n]={'url':r['url'],'fit':fit,'reason':reason,'first_decision':{'days':fd,'kind':'submission to first decision (median)' if fd is not None else '未核得','statistic_period':'官网未注明'},'acceptance':{'official_journal_statistic':None,'sample_n':len(vals),'sample_median':statistics.median(vals)if vals else None,'sample_min':min(vals)if vals else None,'sample_max':max(vals)if vals else None,'note':'近期已接收原始文章小样本，不是全刊或预测' if vals else '未核得'},'status':r.get('status',r.get('error')),'checked_at':'2026-11-08'}
(p/'springer_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print('20 journals saved')
