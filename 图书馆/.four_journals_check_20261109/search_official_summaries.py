from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests, re, html, json

OUT=Path(__file__).resolve().parent
QUERIES={
  'jnc': 'site:sciencedirect.com/journal/journal-for-nature-conservation "Submission to acceptance"',
  'jem': 'site:sciencedirect.com/journal/journal-of-environmental-management "Submission to acceptance"',
  'jnc_name': '"Journal for Nature Conservation" "Submission to acceptance" days',
  'jem_name': '"Journal of Environmental Management" "Submission to acceptance" days',
}
def fetch(item):
    key, engine, query=item
    sess=requests.Session();sess.trust_env=False
    sess.headers['User-Agent']='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36'
    if engine=='bingrss':
        url='https://www.bing.com/search';params={'q':query,'format':'rss'}
    else:
        url='https://www.google.com/search';params={'q':query,'gbv':'1'}
    try:
        r=sess.get(url,params=params,timeout=25)
        (OUT/f'root_search_{engine}_{key}.html').write_text(r.text,encoding='utf-8')
        text=re.sub(r'<(script|style)\b[^>]*>[\s\S]*?</\1>', ' ',r.text,flags=re.I)
        text=html.unescape(re.sub('<[^>]+>',' ',text))
        text=re.sub(r'\s+',' ',text).strip()
        (OUT/f'root_search_{engine}_{key}.txt').write_text(text,encoding='utf-8')
        return {'key':key,'engine':engine,'query':query,'url':r.url,'status':r.status_code,'length':len(r.content),'checked':datetime.now().isoformat(),'text':text[:13000]}
    except Exception as e:
        return {'key':key,'engine':engine,'error':str(e)}

jobs=[(key,engine,q) for key,q in QUERIES.items() for engine in ['bingrss','google']]
results=[]
with ThreadPoolExecutor(max_workers=8) as pool:
    for fut in as_completed([pool.submit(fetch,x) for x in jobs]):
        r=fut.result();results.append(r)
        print(json.dumps({k:v for k,v in r.items() if k!='text'},ensure_ascii=True))
(OUT/'root_official_search_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
