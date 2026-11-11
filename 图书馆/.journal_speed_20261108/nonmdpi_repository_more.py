import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
jobs=[('jort','2213-0780'),('jnc','1617-1381'),('jem','0301-4797'),('cres','2666-0490')]
def get(item):
 key,issn=item;url='https://api.openalex.org/works?filter='+urllib.parse.quote('primary_location.source.issn:'+issn+',open_access.any_repository_has_fulltext:true,from_publication_date:2025-01-01,to_publication_date:2026-11-08')+'&sort=publication_date:desc&per-page=40'
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,20));(ROOT/f'nonmdpi_more_{key}.json').write_text(r.text,encoding='utf8')
  res={'journal':key,'url':url,'status':r.status_code,'works':[]}
  if r.status_code==200:
   for w in r.json()['results']:
    locs=[a for a in w['locations'] if (a.get('source') or {}).get('type')=='repository' and not any(t in str(a.get('landing_page_url')) for t in ['ssrn','doi.org/10.2139','doi.org/10.5281','doaj','biorxiv','osf.io'])]
    if locs:res['works'].append({'doi':w['doi'],'title':w['display_name'],'date':w['publication_date'],'locations':locs})
  print(json.dumps(res,ensure_ascii=False),flush=True);return res
 except Exception as e:return {'journal':key,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_more_locations.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
