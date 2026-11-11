import concurrent.futures,json,re,pathlib,urllib.parse,requests,html
from check_springer_other import fetch,ROOT
items={
'bing urban biodiversity mdpi':'https://www.bing.com/search?q='+urllib.parse.quote('"Urban Biodiversity and Ecosystem Services" site:mdpi.com'),
'bing ecology ecosystem mdpi':'https://www.bing.com/search?q='+urllib.parse.quote('"Ecology & Ecosystem Services" site:mdpi.com'),
'frontiers sustainable cities section index':'https://www.frontiersin.org/journals/sustainable-cities/sections',
'frontiers sustainable cities urban biodiversity section':'https://www.frontiersin.org/journals/sustainable-cities/sections/urban-biodiversity-and-ecosystem-services/about',
'frontiers environmental ecology ecosystem section':'https://www.frontiersin.org/journals/environmental-science/sections/ecology-and-ecosystem-services/about',
'frontiers ecology ecosystem section':'https://www.frontiersin.org/journals/ecology-and-evolution/sections/ecology-and-ecosystem-services/about',
'urban science mdpi cfp':'https://www.mdpi.com/journal/urbansci/sections/urban_biodiversity_ecosystem_services',
'mdpi search ecology ecosystem':'https://www.mdpi.com/search?q='+urllib.parse.quote('Ecology & Ecosystem Services'),
'mdpi china journal list':'https://mdpi.cn/journal'}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:rs=list(ex.map(fetch,items.items()))
(ROOT/'name_followup_b.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2),encoding='utf8')
for r in rs:
 if r.get('status')==200:
  n=re.sub('[^a-z0-9]+','_',r['journal'].lower()).strip('_')
  t=(ROOT/(n+'.txt')).read_text(encoding='utf8')
  print(json.dumps({'name':r['journal'],'text':t[:16000]},ensure_ascii=True),flush=True)
