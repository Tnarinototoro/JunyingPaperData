from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from html.parser import HTMLParser
import json, requests, re
OUT=Path(__file__).resolve().parent
JOBS={
 'home':'https://link.springer.com/journal/11355',
 'scope':'https://link.springer.com/journal/11355/aims-and-scope',
 'fees':'https://link.springer.com/journal/11355/how-to-publish-with-us',
 'instructions':'https://link.springer.com/journal/11355/submission-guidelines',
 'articles':'https://link.springer.com/journal/11355/articles?sort=PubDate&filterOpenAccess=false',
 'metrics':'https://link.springer.com/journal/11355/journal-metrics',
}
class Text(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.bits=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
  if not self.skip and tag in ('p','div','li','h1','h2','h3','h4','tr','br','section'):self.bits.append('\n')
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
  if not self.skip and tag in ('p','div','li','h1','h2','h3','h4','tr','section'):self.bits.append('\n')
 def handle_data(self,value):
  if not self.skip:self.bits.append(value)
 def result(self):return '\n'.join(re.sub('[ \t\r\f]+',' ',line).strip() for line in ''.join(self.bits).splitlines() if line.strip())
def fetch(item):
 key,url=item;s=requests.Session();s.trust_env=False
 s.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
 try:
  r=s.get(url,timeout=30);(OUT/f'lee_{key}.html').write_text(r.text,encoding='utf-8')
  parser=Text();parser.feed(r.text);t=parser.result();(OUT/f'lee_{key}.txt').write_text(t,encoding='utf-8')
  snippets=[t[max(0,m.start()-200):m.end()+700] for m in re.finditer(r'Submission to|acceptance|processing charge|Open Choice|Aims and scope|£|\$|€',t,re.I)][:15]
  return {'key':key,'url':r.url,'status':r.status_code,'bytes':len(r.content),'checked':datetime.now().isoformat(),'snippets':snippets}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
if __name__=='__main__':
 results=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  for fut in as_completed([pool.submit(fetch,item) for item in JOBS.items()]):
   r=fut.result();results.append(r);print(json.dumps({k:v for k,v in r.items() if k!='snippets'}))
 (OUT/'lee_page_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
