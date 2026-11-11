from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests, json
OUT=Path(__file__).resolve().parent
jobs={
'jnc':'https://www.sciencedirect.com/journal/journal-for-nature-conservation/about/insights',
'jem':'https://www.sciencedirect.com/journal/journal-of-environmental-management/about/insights',
'jeplm':'https://www.tandfonline.com/journals/cjep20/about-this-journal?show=journalMetrics',
'landscape':'https://www.tandfonline.com/journals/clar20/about-this-journal?show=journalMetrics',
'conservation':'https://www.mdpi.com/journal/conservation/apc',
}
def f(item):
    key,url=item
    s=requests.Session();s.trust_env=False
    try:
        r=s.get('https://r.jina.ai/'+url,timeout=45)
        (OUT/f'root_reader_{key}.txt').write_text(r.text,encoding='utf-8')
        return {'key':key,'primary_url':url,'reader_url':r.url,'status':r.status_code,'length':len(r.content),'checked':datetime.now().isoformat()}
    except Exception as e:return {'key':key,'error':str(e)}
results=[]
with ThreadPoolExecutor(max_workers=5) as p:
    for future in as_completed([p.submit(f,x) for x in jobs.items()]):
        r=future.result();results.append(r);print(json.dumps(r))
(OUT/'root_reader_log.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
