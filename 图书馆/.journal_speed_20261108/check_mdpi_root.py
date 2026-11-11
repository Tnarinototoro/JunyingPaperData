from pathlib import Path
from html.parser import HTMLParser
import requests, re, json, concurrent.futures, sys
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).parent
class Parse(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.scripts=[]; self.txt=[]; self.hide=0
    def handle_starttag(self,t,a):
        d=dict(a)
        if t=='a' and d.get('href'): self.links.append(d['href'])
        if t=='script' and d.get('src'): self.scripts.append(d['src'])
        if t in ['script','style']: self.hide+=1
    def handle_endtag(self,t):
        if t in ['script','style']: self.hide=max(0,self.hide-1)
    def handle_data(self,d):
        if not self.hide: self.txt.append(d)
s=requests.Session(); s.trust_env=False
if len(sys.argv)==1:
    h=(OUT/'root_mdpi_https_www_mdpi_cn.html').read_text(encoding='utf-8')
    p=Parse(); p.feed(h)
    print(json.dumps({'links':sorted(set(p.links)),'scripts':p.scripts},ensure_ascii=False,indent=2))
else:
    urls=sys.argv[1:]
    def get(u):
        try:
            r=s.get(u,timeout=20); k='root_'+re.sub('[^a-zA-Z0-9]+','_',u)
            (OUT/(k+'.html')).write_text(r.text,encoding='utf-8')
            p=Parse(); p.feed(r.text)
            txt=' '.join(' '.join(p.txt).split()); (OUT/(k+'.txt')).write_text(txt,encoding='utf-8')
            return {'url':u,'status':r.status_code,'length':len(r.content),'text':txt[:3500],'links':p.links[:20]}
        except Exception as e:return {'url':u,'error':str(e)[:200]}
    print(json.dumps(list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(get,urls)),ensure_ascii=False,indent=2))
