import pathlib,requests,json,re,html,datetime,concurrent.futures,sys
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
payload={'query':'Journal for Nature Conservation','mode':'search','goldOpenAccess':True,'subscription':True,'sortBy':'default','sortOrder':'asc','ecrId':'','agreementsFilter':'all-journals'}
api='https://journalfinder.elsevier.com/api/journals/search'
s=requests.Session();s.trust_env=False
r=s.post(api,json=payload,timeout=(8,25),headers={'User-Agent':'Mozilla/5.0'})
(ROOT/'elsevier_jnc_fee_api_raw.json').write_text(r.text,encoding='utf8')
res={'checked_at':datetime.datetime.now().isoformat(timespec='seconds'),'api_url':api,'request':payload,'status':r.status_code,'result_page':'https://journalfinder.elsevier.com/results?query=Journal%20for%20Nature%20Conservation&mode=search'}
if r.status_code==200:
 exact=[x for x in r.json().get('results',[])if x['title']=='Journal for Nature Conservation']
 res['exact_journal']=[{k:x.get(k)for k in ['title','issn','openAccessType','goldOpenAccessFee','editorInChief','links','hasAgreements']}for x in exact]
print(json.dumps(res,ensure_ascii=False),flush=True)
jobs=[('gfa','https://www.sciencedirect.com/journal/journal-for-nature-conservation/publish/guide-for-authors'),('open_access','https://www.sciencedirect.com/journal/journal-for-nature-conservation/publish/open-access-options'),('publishing_options','https://www.elsevier.com/researcher/author/open-access'),('finder_result',res['result_page'])]
def get(item):
 key,url=item;z={'key':key,'url':url}
 try:
  st=requests.Session();st.trust_env=False;rr=st.get(url,timeout=(8,20),headers={'User-Agent':'Mozilla/5.0'})
  (ROOT/f'elsevier_jnc_fee_{key}.html').write_text(rr.text,encoding='utf8');t=html.unescape(re.sub('<[^>]+>',' ',re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',rr.text,flags=re.I)));t=re.sub(r'\s+',' ',t)
  (ROOT/f'elsevier_jnc_fee_{key}.txt').write_text(t,encoding='utf8');z.update(status=rr.status_code,final_url=rr.url,length=len(rr.content),contexts=[t[max(0,m.start()-90):m.start()+250]for m in re.finditer(r'No open access publication fee|subscription|article publishing charge|APC|hybrid|USD|tax',t,re.I)][:30])
 except Exception as e:z['error']=str(e)
 print(json.dumps(z,ensure_ascii=False),flush=True);return z
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:res['official_pages']=list(ex.map(get,jobs))
(ROOT/'elsevier_jnc_fee_evidence.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
