import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
jobs=[('jort','S2764702529'),('jnc','S77407326'),('jem','S17743007'),('cres','S4210178349')]
def get(item):
 key,sid=item
 url='https://api.openalex.org/works?filter='+urllib.parse.quote('primary_location.source.id:'+sid+',open_access.any_repository_has_fulltext:true,from_publication_date:2026-01-01,to_publication_date:2026-11-08')+'&sort=publication_date:desc&per-page=8'
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(10,25))
  (ROOT/f'nonmdpi_rep_{key}.json').write_text(r.text,encoding='utf8')
  res={'journal':key,'url':url,'status':r.status_code}
  if r.status_code==200:
   res['count']=r.json()['meta']['count'];res['works']=[]
   for x in r.json()['results']:
    res['works'].append({'doi':x.get('doi'),'title':x['display_name'],'date':x['publication_date'],'locations':[a for a in x.get('locations',[]) if a.get('pdf_url') or (a.get('source') or {}).get('type')=='repository']})
  return res
 except Exception as e:return {'journal':key,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_repository_locations.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
