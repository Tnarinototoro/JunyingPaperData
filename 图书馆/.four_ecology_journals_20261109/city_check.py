import pathlib,requests,concurrent.futures,re,html,json,sys,datetime
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
payload={'query':'City and Environment Interactions','mode':'search','goldOpenAccess':True,'subscription':True,'sortBy':'default','sortOrder':'asc','ecrId':'','agreementsFilter':'all-journals'}
api='https://journalfinder.elsevier.com/api/journals/search';s=requests.Session();s.trust_env=False;r=s.post(api,json=payload,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0'});(ROOT/'city_finder_raw.json').write_text(r.text,encoding='utf8')
res={'checked_date':'2026-11-09','checked_at':datetime.datetime.now().isoformat(timespec='seconds'),'api_url':api,'status':r.status_code,'request':payload}
if r.status_code==200:res['exact_results']=[x for x in r.json()['results']if x['title']=='City and Environment Interactions']
(ROOT/'city_finder_evidence.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
for x in res.get('exact_results',[]):print(json.dumps({k:x.get(k)for k in ['title','issn','openAccessType','goldOpenAccessFee','insights','links']},ensure_ascii=False),flush=True)
slug='city-and-environment-interactions';jobs=[('home',f'https://www.sciencedirect.com/journal/{slug}'),('insights',f'https://www.sciencedirect.com/journal/{slug}/about/insights'),('gfa',f'https://www.sciencedirect.com/journal/{slug}/publish/guide-for-authors'),('oa',f'https://www.sciencedirect.com/journal/{slug}/publish/open-access-options'),('crossref','https://api.crossref.org/journals/2590-2520/works?sort=published&order=desc&rows=12&filter=until-pub-date:2026-11-09')]
def get(item):
 key,url=item;z={'key':key,'url':url}
 try:
  st=requests.Session();st.trust_env=False;rr=st.get(url,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0'});(ROOT/f'city_{key}.html').write_text(rr.text,encoding='utf8')
  t=html.unescape(re.sub('<[^>]+>',' ',re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',rr.text,flags=re.I)));t=re.sub(r'\s+',' ',t);(ROOT/f'city_{key}.txt').write_text(t,encoding='utf8')
  z.update(status=rr.status_code,final_url=rr.url,length=len(rr.content),contexts=[t[max(0,m.start()-100):m.start()+350]for m in re.finditer(r'Submission to acceptance|Article Publishing Charge|USD|No open access publication fee',t,re.I)][:15])
  if key=='crossref'and rr.status_code==200:
   z['candidates']=[{'doi':a['DOI'],'title':a.get('title'),'assertion':a.get('assertion'),'link':a.get('link')}for a in rr.json()['message']['items']]
 except Exception as e:z['error']=str(e)
 print(json.dumps(z,ensure_ascii=False),flush=True);return z
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as ex:results=list(ex.map(get,jobs))
(ROOT/'city_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
