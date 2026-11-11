import pathlib,json,re,statistics,datetime
root=pathlib.Path(__file__).parent
data=json.loads((root/'springer_article_histories_all.json').read_text(encoding='utf8'))
for r in data:
 p=root/(re.sub('[^a-z0-9]+','_',('/article/'+r.get('doi','')).lower())+'.txt')
 if not p.exists():continue
 t=p.read_text(encoding='utf8')
 h=t[t.rfind('About this article'):]
 r['history_context']=h[:2000]
 for key in ['Received','Revised','Accepted','Published','Version of record']:
  found=re.search(re.escape(key)+r'\s*:?\s*(\d{1,2} [A-Za-z]+ \d{4})',h)
  if found:r[key]=found.group(1)
 if 'Received'in r and 'Accepted'in r:
  r['days']=(datetime.datetime.strptime(r['Accepted'],'%d %B %Y')-datetime.datetime.strptime(r['Received'],'%d %B %Y')).days
 (root/'springer_article_histories_all.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
for name in dict.fromkeys(r['journal']for r in data):
 selected=[r for r in data if r['journal']==name and any(x in ['Research','Article']for x in r.get('type',[]))][:5]
 vals=[r['days']for r in selected if 'days'in r]
 print(json.dumps({'journal':name,'n':len(vals),'median':statistics.median(vals)if vals else None,'min':min(vals)if vals else None,'max':max(vals)if vals else None,'records':[{k:v for k,v in r.items()if k not in ['history_context','header']}for r in selected]},ensure_ascii=True))
(root/'springer_sample_selected.json').write_text(json.dumps([r for name in dict.fromkeys(r['journal']for r in data) for r in [r for r in data if r['journal']==name and any(x in ['Research','Article']for x in r.get('type',[]))][:5]],ensure_ascii=False,indent=2),encoding='utf8')
