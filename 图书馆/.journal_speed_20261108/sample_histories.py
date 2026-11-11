import requests,pathlib,re,html,json,concurrent.futures,datetime,statistics,sys
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
JOURNALS={'Discover Cities':44327,'Discover Environment':44274,'Discover Sustainability':43621,'Environmental Management':267}
def get(url):
 s=requests.Session();s.trust_env=False
 return s.get(url,timeout=(15,30))
def clean(t):return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
def list_articles(item):
 name,jid=item;url=f'https://link.springer.com/journal/{jid}/articles'
 r=get(url);(ROOT/(f'sample_list_{jid}.html')).write_text(r.text,encoding='utf8')
 links=list(dict.fromkeys(re.findall(r'href="(/article/[^"#?]+)',r.text)))
 return name,links
def article(item):
 name,path=item;url='https://link.springer.com'+path;res={'journal':name,'url':url}
 try:
  r=get(url);slug=re.sub('[^a-z0-9]+','_',path.lower());(ROOT/(slug+'.html')).write_text(r.text,encoding='utf8')
  t=clean(re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',r.text,flags=re.I))
  (ROOT/(slug+'.txt')).write_text(t,encoding='utf8')
  res.update(status=r.status_code,doi=path.replace('/article/',''),title=clean(re.search('<title>(.*?)</title>',r.text,re.S).group(1)))
  types=re.findall(r'<meta\s+name="citation_article_type"\s+content="([^"]+)',r.text)
  res['type']=types
  p=t.find('About this article');res['history_context']=t[p:p+6500]
  for key in ['Received','Revised','Accepted','Published','Version of record']:
   found=re.search(re.escape(key)+r'\s+(\d{1,2} [A-Za-z]+ \d{4})',t)
   if found:res[key]=found.group(1)
  if 'Received'in res and 'Accepted'in res:
   res['days']=(datetime.datetime.strptime(res['Accepted'],'%d %B %Y')-datetime.datetime.strptime(res['Received'],'%d %B %Y')).days
  res['header']=t[:3500]
 except Exception as e:res['error']=str(e)
 return res
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:lists=list(ex.map(list_articles,JOURNALS.items()))
print(json.dumps(lists,ensure_ascii=False),flush=True)
items=[(name,path)for name,links in lists for path in links[:10]]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(article,items))
(ROOT/'springer_article_histories_all.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps({k:v for k,v in r.items() if k not in ['history_context','header']},ensure_ascii=False),flush=True)
