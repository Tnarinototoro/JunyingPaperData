import requests,pathlib,re,html,json,concurrent.futures,datetime,statistics,sys
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
class P(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.text=[];self.hide=0
 def handle_starttag(self,t,a):
  d=dict(a)
  if t=='a' and d.get('href'):self.links.append(d['href'])
  if t in ['script','style']:self.hide+=1
 def handle_endtag(self,t):
  if t in ['script','style']:self.hide=max(0,self.hide-1)
 def handle_data(self,d):
  if not self.hide:self.text.append(d)
def get(u):
 s=requests.Session();s.trust_env=False
 return s.get(u,timeout=(15,35))
def run(u,slug):
 r=get(u);(ROOT/(slug+'.html')).write_text(r.text,encoding='utf8');p=P();p.feed(r.text);t=re.sub(r'\s+',' ', ' '.join(p.text)).strip();(ROOT/(slug+'.txt')).write_text(t,encoding='utf8')
 return r,p,t
if __name__=='__main__':
 u='https://www.cambridge.org/core/journals/environmental-conservation/latest-issue'
 r,p,t=run(u,'enc_latest_issue')
 links=list(dict.fromkeys(x for x in p.links if '/environmental-conservation/article/' in x))
 print(json.dumps({'url':u,'status':r.status_code,'links':links[:20],'tail':t[-5000:]},ensure_ascii=True),flush=True)
 if not links:
  u='https://www.cambridge.org/core/journals/environmental-conservation/firstview'
  r,p,t=run(u,'enc_firstview')
  links=list(dict.fromkeys(x for x in p.links if '/environmental-conservation/article/' in x))
  print(json.dumps({'url':u,'status':r.status_code,'links':links[:20],'tail':t[-5000:]},ensure_ascii=True),flush=True)
 out=[]
 def art(item):
  i,path=item;url=path if path.startswith('http')else 'https://www.cambridge.org'+path
  res={'journal':'Environmental Conservation','url':url,'list_order':i}
  try:
   r,p,t=run(url,f'enc_sample_{i}');res['status']=r.status_code
   m=re.search(r'<title>(.*?)</title>',r.text,re.S);res['title']=html.unescape(m.group(1)).strip()if m else ''
   res['matches']=[t[max(0,m.start()-150):m.end()+250]for m in re.finditer(r'received|accepted|revised|article type|research article|report',t,re.I)]
   res['meta']=[x for x in re.findall(r'<meta[^>]+>',r.text)if any(z in x.lower()for z in ['citation','dc.type','dc.date'])]
  except Exception as e:res['error']=str(e)
  print(json.dumps(res,ensure_ascii=True),flush=True)
  return res
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:out=list(ex.map(art,list(enumerate(links[:8],1))))
 (ROOT/'enc_article_histories_followup.json').write_text(json.dumps({'list_url':u,'list_status':r.status_code,'results':out},ensure_ascii=False,indent=2),encoding='utf8')
