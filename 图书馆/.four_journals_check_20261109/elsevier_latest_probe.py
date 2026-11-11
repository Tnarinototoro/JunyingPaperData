import pathlib,requests,concurrent.futures,re,html,json,sys,datetime
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
def clean(t):
 t=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',t,flags=re.I)
 return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
jobs=[]
for key,slug,issn in [('jnc','journal-for-nature-conservation','1617-1381'),('jem','journal-of-environmental-management','0301-4797')]:
 jobs += [(key+'_insights',f'https://www.sciencedirect.com/journal/{slug}/about/insights'),(key+'_publish_insights',f'https://www.sciencedirect.com/journal/{slug}/publish/insights'),(key+'_home',f'https://www.sciencedirect.com/journal/{slug}'),(key+'_elsevier_insights',f'https://www.elsevier.com/journals/{slug}/{issn}/insights'),(key+'_legacy_insights',f'https://journalinsights.elsevier.com/journals/{issn}/review_speed')]
def get(item):
 key,url=item;res={'key':key,'url':url,'checked_at':datetime.datetime.now().isoformat(timespec='seconds')}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,20),headers={'User-Agent':'Mozilla/5.0','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
  t=clean(r.text);(ROOT/f'elsevier_{key}.html').write_text(r.text,encoding='utf8');(ROOT/f'elsevier_{key}.txt').write_text(t,encoding='utf8')
  res.update(status=r.status_code,final_url=r.url,bytes=len(r.content),title=clean(re.search('<title>([\s\S]*?)</title>',r.text,re.I).group(1))if re.search('<title>([\s\S]*?)</title>',r.text,re.I)else'',contexts=[t[max(0,m.start()-120):m.start()+350]for m in re.finditer(r'Submission to acceptance|Submission to first decision|Decision after review|Acceptance to.*publication',t,re.I)])
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as ex:results=list(ex.map(get,jobs))
(ROOT/'elsevier_latest_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
