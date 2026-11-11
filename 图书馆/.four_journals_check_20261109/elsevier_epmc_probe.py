import pathlib,requests,concurrent.futures,json,sys,urllib.parse,re,datetime
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
jobs=[('jnc','ISSN:1617-1381 AND FIRST_PDATE:[2025-01-01 TO 2026-11-09] AND OPEN_ACCESS:Y'),('jem','ISSN:0301-4797 AND FIRST_PDATE:[2026-01-01 TO 2026-11-09] AND OPEN_ACCESS:Y')]
def get(item):
 key,query=item;url='https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&pageSize=10&sort_date:y&query='+urllib.parse.quote(query);res={'journal':key,'url':url,'checked_date':'2026-11-09'}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,20));(ROOT/f'elsevier_epmc_{key}.json').write_text(r.text,encoding='utf8');res['status']=r.status_code
  if r.status_code==200:res['hitCount']=r.json()['hitCount'];res['results']=r.json()['resultList']['result']
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=2)as ex:results=list(ex.map(get,jobs))
(ROOT/'elsevier_epmc_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
