import requests, re, html, json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
OUT=Path(__file__).resolve().parent
q='Journal for Nature Conservation submission acceptance days'
jobs=[
('bing','https://www.bing.com/search',{'q':q,'setlang':'en-US','cc':'US'}),
('google','https://www.google.com/search',{'q':q,'udm':'14','num':'10','hl':'en'}),
('ddg','https://html.duckduckgo.com/html/',{'q':q}),
('yahoo','https://search.yahoo.com/search',{'p':q}),
('brave','https://search.brave.com/search',{'q':q,'source':'web'}),
('baidu','https://www.baidu.com/s',{'wd':'Journal for Nature Conservation 接收 时间'}),
]
def f(job):
    key,url,params=job
    s=requests.Session();s.trust_env=False
    s.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
    try:
        r=s.get(url,params=params,timeout=20)
        (OUT/f'root_search_extra_{key}.html').write_text(r.text,encoding='utf-8')
        t=re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>',' ',r.text,flags=re.I)
        t=html.unescape(re.sub('<[^>]+>',' ',t));t=re.sub(r'\s+',' ',t).strip()
        (OUT/f'root_search_extra_{key}.txt').write_text(t,encoding='utf-8')
        return {'key':key,'status':r.status_code,'len':len(r.content),'url':r.url,'text':t[:18000]}
    except Exception as e:return {'key':key,'error':str(e)}
with ThreadPoolExecutor(max_workers=6) as p:results=list(p.map(f,jobs))
(OUT/'root_search_extra_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for r in results:print(json.dumps({k:v for k,v in r.items() if k!='text'}))
