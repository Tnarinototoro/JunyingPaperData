import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
jobs=[]
for slug,fn in [('jort','nonmdpi_jort_crossref.html'),('jnc','nonmdpi_art_jnc_crossref.txt'),('cres','nonmdpi_cres_crossref.html')]:
 d=json.loads((ROOT/fn).read_text(encoding='utf8'))
 for item in d['message']['items'][:6]:
  if any(w in item['title'][0].lower() for w in ['corrigendum','editorial','retraction']):continue
  jobs.append((slug,item['DOI'],item['title'][0]))
def get(item):
 slug,doi,title=item
 key=re.sub('[^a-zA-Z0-9]+','_',doi)
 url='https://api.openalex.org/works/https://doi.org/'+doi
 try:
  s=requests.Session();s.trust_env=False
  r=s.get(url,timeout=(10,25))
  (ROOT/f'nonmdpi_openalex_{key}.json').write_text(r.text,encoding='utf8')
  res={'journal':slug,'doi':doi,'title':title,'status':r.status_code}
  if r.status_code==200:
   data=r.json();res['locations']=[a for a in data.get('locations',[]) if a.get('is_oa') or a.get('pdf_url')]
  return res
 except Exception as e:return {'journal':slug,'doi':doi,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_openalex_locations.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
