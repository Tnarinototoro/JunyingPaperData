import requests,concurrent.futures,sys,re,json,html
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
JOBS=[
 ('wiley_home','https://onlinelibrary.wiley.com/journal/1526100x'),
 ('wiley_scope','https://onlinelibrary.wiley.com/page/journal/1526100x/homepage/productinformation.html'),
 ('wiley_author','https://onlinelibrary.wiley.com/page/journal/1526100x/homepage/forauthors.html'),
 ('wiley_metrics','https://onlinelibrary.wiley.com/page/journal/1526100x/homepage/journalmetrics.html'),
 ('wiley_oa','https://onlinelibrary.wiley.com/page/journal/1526100x/homepage/openaccess.html'),
 ('ser_journal','https://www.ser.org/page/RestorationEcology'),
 ('ser_journal_alt','https://www.ser.org/page/REJournal'),
 ('crossref','https://api.crossref.org/journals/1526-100X/works?sort=published&order=desc&rows=15&filter=until-pub-date:2026-11-09'),
 ('wiley_product','https://www.wiley.com/en-us/Restoration+Ecology-p-1526100X'),
 ('wiley_finder','https://journalfinder.wiley.com/journal/1526100x'),
]
def fetch(job):
 key,url=job;o={'key':key,'url':url,'checked_date':'2026-11-09'}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(12,30),headers={'User-Agent':'Mozilla/5.0'});o.update(status=r.status_code,final_url=r.url,bytes=len(r.content))
  ext='.json' if key=='crossref' else '.html';(ROOT/('restoration_'+key+ext)).write_text(r.text,encoding='utf-8')
  if key!='crossref':
   t=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',r.text,flags=re.I);t=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip();(ROOT/('restoration_'+key+'.txt')).write_text(t,encoding='utf-8')
   o.update(title=re.findall('<title>(.*?)</title>',r.text,re.S|re.I),contexts=[t[max(0,m.start()-140):m.end()+500] for m in re.finditer(r'aims|scope|fee|charge|subscription|decision|acceptance|social|policy|journal',t,re.I)][:15])
  else:
   o['items']=[{'DOI':x['DOI'],'title':x.get('title'),'published':x.get('published'),'assertion':x.get('assertion'),'link':x.get('link')} for x in r.json().get('message',{}).get('items',[])]
 except Exception as e:o['error']=str(e)
 return o
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:out=list(ex.map(fetch,JOBS))
 (ROOT/'restoration_online_evidence_20261109.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 for o in out:print(json.dumps({k:v for k,v in o.items() if k not in ['items','contexts']},ensure_ascii=False))
