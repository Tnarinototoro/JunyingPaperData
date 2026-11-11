from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests, html, re, json
from urllib.parse import quote
OUT=Path(__file__).resolve().parent
queries={
'cjep20':'cjep20',
'clar20':'clar20',
'jem_exact':'"Journal of Environmental Management" "acceptance"',
'jnc_exact':'"Journal for Nature Conservation" "acceptance"',
'jeplm_exact':'"Journal of Environmental Planning and Management" "acceptance"',
'lr_exact':'"Landscape Research" "submission to acceptance"',
}
def f(item):
    key,q=item;s=requests.Session();s.trust_env=False
    s.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
    url='https://www.bing.com/search?q='+quote(q,safe='')+'&setlang=en-US&cc=US'
    try:
        r=s.get(url,timeout=20)
        (OUT/f'root_bing_precise_{key}.html').write_text(r.text,encoding='utf-8')
        t=re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>',' ',r.text,flags=re.I)
        t=html.unescape(re.sub('<[^>]+>',' ',t));t=re.sub(r'\s+',' ',t).strip()
        (OUT/f'root_bing_precise_{key}.txt').write_text(t,encoding='utf-8')
        return {'key':key,'status':r.status_code,'url':r.url,'text':t[:18000]}
    except Exception as e:return {'key':key,'error':str(e)}
with ThreadPoolExecutor(max_workers=6) as p:results=list(p.map(f,queries.items()))
(OUT/'root_search_precise_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for r in results:print(json.dumps({k:v for k,v in r.items() if k!='text'}))
