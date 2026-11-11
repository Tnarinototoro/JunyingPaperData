from pathlib import Path
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import json, re, statistics
from datetime import datetime
from check_lee import fetch
OUT=Path(__file__).resolve().parent
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a' and re.match(r'/article/10\.1007/s11355-',a.get('href','')):
   if a['href'] not in self.links:self.links.append(a['href'])
parser=Links();parser.feed((OUT/'lee_articles.html').read_text(encoding='utf-8'))
jobs=[('article_'+p.split('/')[-1],'https://link.springer.com'+p) for p in parser.links[:9]]
results=[]
with ThreadPoolExecutor(max_workers=9) as pool:results=list(pool.map(fetch,jobs))
for r in results:
 p=OUT/('lee_'+r['key']+'.txt')
 t=p.read_text(encoding='utf-8') if p.exists() else ''
 r['article_type']='Original Paper' if '\nOriginal Paper\n' in t[:5000] else 'other'
 r['title']=t.splitlines()[0] if t else ''
 history={}
 for label in ['Received','Revised','Accepted','Published']:
  m=re.search(r'(?:^|\n)'+label+r'(?:\s*:\s*|\s+)(\d{1,2} [A-Za-z]+ \d{4})(?:\n|$)',t)
  if m:history[label]=m.group(1)
 r['history']=history
 if all(k in history for k in ['Received','Accepted']):
  r['days']=(datetime.strptime(history['Accepted'],'%d %B %Y')-datetime.strptime(history['Received'],'%d %B %Y')).days
 print(json.dumps({k:r[k] for k in ['key','status','article_type','title','history'] if k in r},ensure_ascii=True))
(OUT/'lee_article_histories_all.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
selected=[r for r in results if r.get('article_type')=='Original Paper' and 'days' in r][:5]
values=[r['days'] for r in selected]
summary={'selection':'First five Original Paper entries with received/accepted in current newest-to-oldest official list; first 9 list items fetched','n':len(selected),'days':values,'median':statistics.median(values) if values else None,'range':[min(values),max(values)] if values else None,'articles':selected}
(OUT/'lee_selected_histories.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='articles'},ensure_ascii=True))
