import requests, concurrent.futures, pathlib, json, re, sys, html
sys.stdout.reconfigure(encoding='utf-8')
ROOT=pathlib.Path(__file__).parent
JOURNALS={
 'jort':('Journal of Outdoor Recreation and Tourism','2213-0780','journal-of-outdoor-recreation-and-tourism'),
 'jnc':('Journal for Nature Conservation','1617-1381','journal-for-nature-conservation'),
 'jem':('Journal of Environmental Management','0301-4797','journal-of-environmental-management'),
 'cres':('Current Research in Environmental Sustainability','2666-0490','current-research-in-environmental-sustainability')}
def get(item):
 key,url=item
 try:
  s=requests.Session();s.trust_env=False
  r=s.get(url,timeout=(10,25),headers={'User-Agent':'Mozilla/5.0'})
  (ROOT/f'nonmdpi_{key}.html').write_text(r.text,encoding='utf8')
  return {'key':key,'url':url,'status':r.status_code,'final_url':r.url,'length':len(r.content),'text':r.text}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
jobs=[]
for key,(title,issn,slug) in JOURNALS.items():
 jobs.extend([(key+'_crossref',f'https://api.crossref.org/journals/{issn}/works?sort=published&order=desc&rows=8&filter=until-pub-date:2026-11-08'),
  (key+'_elsevier',f'https://www.elsevier.com/journals/{slug}/{issn}'),
  (key+'_sdinsights',f'https://www.sciencedirect.com/journal/{slug}/about/insights')])
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 results=list(ex.map(get,jobs))
for r in results:
 print(json.dumps({k:v for k,v in r.items() if k!='text'},ensure_ascii=False),flush=True)
(ROOT/'nonmdpi_elsevier_probe_log.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='text'} for r in results],ensure_ascii=False,indent=2),encoding='utf8')
for r in results:
 if r['key'].endswith('_crossref') and r.get('status')==200:
  try:
   items=json.loads(r['text'])['message']['items']
   for a in items:print(json.dumps({'journal':r['key'],'doi':a['DOI'],'title':a.get('title'),'dates':{k:v for k,v in a.items() if k in ['accepted','created','published','published-online']},'link':a.get('link')},ensure_ascii=False),flush=True)
  except Exception as e:print(str(e))
