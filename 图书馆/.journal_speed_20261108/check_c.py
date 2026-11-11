import requests, concurrent.futures, json, pathlib, re
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).parent
class Text(HTMLParser):
 def __init__(self): super().__init__(); self.chunks=[]; self.ignore=0
 def handle_starttag(self,t,a):
  if t in ['script','style']: self.ignore+=1
  elif t in ['p','div','li','h1','h2','h3','br','tr']: self.chunks.append('\n')
 def handle_endtag(self,t):
  if t in ['script','style']: self.ignore=max(0,self.ignore-1)
  elif t in ['p','div','li','h1','h2','h3','tr']: self.chunks.append('\n')
 def handle_data(self,d):
  if not self.ignore:self.chunks.append(d)
def fetch(pair):
 name,url=pair;s=requests.Session();s.trust_env=False
 try:
  r=s.get(url,timeout=25); p=Text();p.feed(r.text)
  txt=re.sub(r'\n[ \t]*\n+', '\n', ''.join(p.chunks))
  (ROOT/(name+'.html')).write_text(r.text,encoding='utf8'); (ROOT/(name+'.txt')).write_text(txt,encoding='utf8')
  result={'name':name,'url':url,'final_url':r.url,'status':r.status_code,'chars':len(txt)}
  print(json.dumps(result,ensure_ascii=False),flush=True);return result
 except Exception as e:
  result={'name':name,'url':url,'error':str(e)}; print(json.dumps(result,ensure_ascii=False),flush=True); return result
if __name__=='__main__':
 pairs=json.loads((ROOT/'urls_c.json').read_text(encoding='utf8'))
 results=list(concurrent.futures.ThreadPoolExecutor(max_workers=10).map(fetch,pairs))
 (ROOT/'access_c.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
