import concurrent.futures, html, json, re, sys
from pathlib import Path
from datetime import datetime
import requests
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent

JOURNALS={'cjep20':'Journal of Environmental Planning and Management','clar20':'Landscape Research'}
JOBS=[]
for code,name in JOURNALS.items():
    for key,url in [
        ('home',f'https://www.tandfonline.com/journals/{code}'),
        ('about',f'https://www.tandfonline.com/journals/{code}/about-this-journal'),
        ('metrics',f'https://www.tandfonline.com/journals/{code}/about-this-journal/journal-metrics'),
        ('metrics_legacy',f'https://www.tandfonline.com/action/journalInformation?show=journalMetrics&journalCode={code}'),
        ('latest',f'https://www.tandfonline.com/toc/{code}/0/0'),
    ]: JOBS.append((code,name,key,url))

def fetch(job):
    code,name,key,url=job
    result={'journal':name,'code':code,'key':key,'url':url,'checked_local':datetime.now().isoformat(timespec='seconds')}
    try:
        s=requests.Session();s.trust_env=False
        r=s.get(url,timeout=(12,25),headers={'User-Agent':'Mozilla/5.0'})
        stem=f'taylor_{code}_{key}'
        (ROOT/(stem+'.html')).write_text(r.text,encoding='utf-8')
        t=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',r.text,flags=re.I)
        t=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
        (ROOT/(stem+'.txt')).write_text(t,encoding='utf-8')
        result.update(status=r.status_code,final_url=r.url,bytes=len(r.content),title=re.findall('<title>(.*?)</title>',r.text,re.S|re.I),text_preview=t[:350])
        result['metric_contexts']=[t[max(0,m.start()-150):m.end()+350] for m in re.finditer(r'submission to|first decision|first post-review|to acceptance|days|weeks',t,re.I)][:20]
    except Exception as e: result['error']=str(e)
    return result

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: results=list(ex.map(fetch,JOBS))
    (ROOT/'taylor_online_access_20261109.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in results: print(json.dumps({k:r[k] for k in ['code','key','status','title','error'] if k in r},ensure_ascii=False))
