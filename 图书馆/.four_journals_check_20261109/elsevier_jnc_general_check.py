import pathlib,requests,re,html,concurrent.futures,sys,json
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
jobs=[('pricing','https://www.elsevier.com/about/policies-and-standards/pricing'),('hybrid','https://www.elsevier.com/researcher/author/open-access/hybrid-open-access'),('subscription','https://www.elsevier.com/researcher/author/submit-your-paper')]
def get(item):
 key,url=item;res={'key':key,'url':url}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,20),headers={'User-Agent':'Mozilla/5.0'});(ROOT/f'elsevier_jnc_general_{key}.html').write_text(r.text,encoding='utf8')
  t=html.unescape(re.sub('<[^>]+>',' ',re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',r.text,flags=re.I)));t=re.sub(r'\s+',' ',t);(ROOT/f'elsevier_jnc_general_{key}.txt').write_text(t,encoding='utf8')
  res.update(status=r.status_code,final_url=r.url,length=len(r.content),contexts=[t[max(0,m.start()-100):m.start()+350]for m in re.finditer(r'no.*(?:fee|charge)|not.*(?:fee|charge)|subscription|hybrid',t,re.I)][:20])
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as ex:results=list(ex.map(get,jobs))
(ROOT/'elsevier_jnc_general_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
