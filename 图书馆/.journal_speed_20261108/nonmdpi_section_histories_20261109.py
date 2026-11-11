import sys,json,re,concurrent.futures,statistics
from pathlib import Path
from nonmdpi_frontiers_peerj_20261109 import get,fetch_article
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).parent
SECTIONS=[('Frontiers in Sustainable Cities','sustainable-cities','urban-greening'),('Frontiers in Conservation Science','conservation-science','conservation-social-sciences-indigenous-and-local-knowledge'),('Frontiers in Environmental Science','environmental-science','environmental-economics-and-management')]
def listing(item):
 name,slug,section=item;url=f'https://www.frontiersin.org/journals/{slug}/sections/{section}/articles'
 try:
  r=get(url);(ROOT/f'nonmdpi_section_list_{section}_20261109.html').write_text(r.text,encoding='utf-8')
  links=list(dict.fromkeys(re.findall(r'https://www.frontiersin.org/journals/'+slug+r'/articles/(10\.[^"<>? ]+)/full',r.text)))
  return {'journal':name,'slug':slug,'section':section,'url':url,'status':r.status_code,'doi_order':links[:20]}
 except Exception as e:return {'journal':name,'section':section,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:lists=list(ex.map(listing,SECTIONS))
(ROOT/'nonmdpi_section_lists_20261109.json').write_text(json.dumps(lists,ensure_ascii=False,indent=2),encoding='utf-8')
items=[]
for data in lists:
 for i,doi in enumerate(data.get('doi_order',[]),1):items.append((data,(data['journal'],data['slug'],{'DOI':doi,'title':['title from article below']}),i))
def fetch(pair):
 data,item,i=pair;x=fetch_article(item);x['section']=data['section'];x['section_source_order']=i;x['section_list_url']=data['url']
 if x.get('status')==200:
  t=(ROOT/('nonmdpi_'+re.sub(r'[^a-z0-9]+','_',x['doi'].lower())+'.txt')).read_text(encoding='utf-8')
  m=re.search(r'Volume\s+\d+\s*-\s*\d{4}\s*\|\s*https://doi.org/[^ ]+\s+(.{5,500}?)\s+(?:Download article|View article|[A-Z][a-z]+ [A-Z])',t)
  x['article_text_title_candidate']=m.group(1) if m else ''
 return x
print('section_candidates',len(items),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(fetch,items))
(ROOT/'nonmdpi_section_histories_all_20261109.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
selected=[]
for name,slug,section in SECTIONS:
 group=[x for x in results if x['section']==section and x.get('valid_dates') and x.get('original_research')][:5]
 selected+=group;days=[x['days'] for x in group]
 print(name,section,len(group),days,'median',statistics.median(days) if days else None,flush=True)
 for x in group:print(json.dumps({k:v for k,v in x.items() if k not in ['header'] and not k.endswith('_context')},ensure_ascii=False),flush=True)
(ROOT/'nonmdpi_section_histories_selected_20261109.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
