import pathlib,requests,concurrent.futures,json,datetime,re,sys
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
jobs=[
('article_100458_api','https://api.elsevier.com/content/article/PII:S2590252026001650?httpAccept=text/xml'),
('article_100458_oa','https://api.openalex.org/works/https://doi.org/10.1016/j.cacint.2026.100458'),
('repository_list','https://api.openalex.org/works?filter=primary_location.source.issn:2590-2520,open_access.any_repository_has_fulltext:true,from_publication_date:2025-01-01,to_publication_date:2026-11-09&sort=publication_date:desc&per-page=40'),
('article_100458_full','https://api.elsevier.com/content/article/PII:S2590252026001650?view=FULL&httpAccept=text/xml'),
('article_100458_home','https://www.sciencedirect.com/science/article/pii/S2590252026001650')]
def get(item):
 k,u=item;z={'key':k,'url':u,'checked_at':datetime.datetime.now().isoformat(timespec='seconds')}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(u,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0'});(ROOT/f'city_{k}_raw.txt').write_text(r.text,encoding='utf8');z.update(status=r.status_code,final_url=r.url,length=len(r.content))
  if r.status_code==200 and 'openalex' in u:
   data=r.json();items=data.get('results',[data]);z['results']=[{'doi':a.get('doi'),'title':a.get('title'),'date':a.get('publication_date'),'locations':a.get('locations')}for a in items]
  elif r.status_code==200:z['history_contexts']=[r.text[max(0,m.start()-100):m.start()+350]for m in re.finditer(r'received|accepted|date-accept|date-rec|history',r.text,re.I)][:25]
 except Exception as e:z['error']=str(e)
 print(json.dumps(z,ensure_ascii=False),flush=True);return z
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as ex:results=list(ex.map(get,jobs))
(ROOT/'city_article_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
