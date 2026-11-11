import requests,pathlib,re,html,json,concurrent.futures,datetime,statistics,sys
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
def get(url):
 s=requests.Session();s.trust_env=False
 return s.get(url,timeout=(15,35))
def clean(t):
 t=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>', ' ',t,flags=re.I)
 return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
def article(path):
 url='https://link.springer.com'+path;res={'journal':'Urban Ecosystems','url':url}
 try:
  r=get(url);slug='ue'+re.sub('[^a-z0-9]+','_',path.lower());(ROOT/(slug+'.html')).write_text(r.text,encoding='utf8')
  t=clean(r.text);(ROOT/(slug+'.txt')).write_text(t,encoding='utf8')
  title=re.search('<title>(.*?)</title>',r.text,re.S)
  res.update(status=r.status_code,doi=path.replace('/article/',''),title=clean(title.group(1))if title else '')
  res['type']=re.findall(r'<meta\s+name="citation_article_type"\s+content="([^"]+)',r.text)
  h=t[t.rfind('About this article'):];res['history_context']=h[:2500]
  res['header']=t[:5000]
  for key in ['Received','Revised','Accepted','Published','Version of record']:
   found=re.search(re.escape(key)+r'\s*:?\s*(\d{1,2} [A-Za-z]+ \d{4})',h)
   if found:res[key]=found.group(1)
  if 'Received'in res and 'Accepted'in res:
   res['days']=(datetime.datetime.strptime(res['Accepted'],'%d %B %Y')-datetime.datetime.strptime(res['Received'],'%d %B %Y')).days
 except Exception as e:res['error']=str(e)
 print(json.dumps({k:v for k,v in res.items()if k not in ['history_context','header']},ensure_ascii=False),flush=True)
 return res
if __name__=='__main__':
 url='https://link.springer.com/journal/11252/articles'
 r=get(url);(ROOT/'ue_latest_articles_list.html').write_text(r.text,encoding='utf8');(ROOT/'ue_latest_articles_list.txt').write_text(clean(r.text),encoding='utf8')
 links=list(dict.fromkeys(re.findall(r'href="(/article/[^"#?]+)',r.text)))
 print(json.dumps({'list_url':url,'status':r.status_code,'links':links[:12]},ensure_ascii=False),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(article,links[:10]))
 out={'checked_date':'2026-11-08','list_url':url,'list_status':r.status_code,'selection':'官网最新articles列表顺序前10条，下一步取其中前5篇原始研究，排除综述/社论而非按速度选择','results':results}
 (ROOT/'urban_ecosystems_histories_all.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
