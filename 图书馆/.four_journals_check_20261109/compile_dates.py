from pathlib import Path
from datetime import date
import json,csv,statistics,html,re
OUT=Path(__file__).resolve().parent
EXCLUDE={
 '10.1080/01426397.2026.2737849': 'Landscapes of abandonment: article category not verified; short contribution excluded from research-paper comparison',
 '10.1080/01426397.2026.2730202': 'Introduction to special issue; excluded',
}
allrows=[]
for name in ['taylor_crossref_je_pm.json','taylor_crossref_lr.json']:
    data=json.loads((OUT/name).read_text(encoding='utf-8'))
    for item in data['message']['items']:
        history={a['name']:a['value'] for a in item.get('assertion',[]) if a.get('group',{}).get('name')=='publication_history'}
        if not all(k in history for k in ['received','accepted']):continue
        d=(date.fromisoformat(history['accepted'])-date.fromisoformat(history['received'])).days
        title=html.unescape(re.sub('<[^>]+>','',item['title'][0]))
        title=re.sub(r'\s+',' ',title).strip()
        allrows.append({'journal':item['container-title'][0],'title':title,'doi':item['DOI'],'received':history['received'],'accepted':history['accepted'],'days':d,'included':item['DOI'] not in EXCLUDE,'exclusion':EXCLUDE.get(item['DOI'],''),'evidence':'Publisher-submitted Crossref publication_history assertion; publisher webpage inaccessible','crossref_url':'https://api.crossref.org/works/'+item['DOI'],'article_url':'https://www.tandfonline.com/doi/full/'+item['DOI']})
(OUT/'root_taylor_history_audit.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'root_taylor_history_audit.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
for j in sorted(set(x['journal'] for x in allrows)):
    values=[x['days'] for x in allrows if x['journal']==j and x['included']]
    print(json.dumps({'journal':j,'days':values,'n':len(values),'median':statistics.median(values),'min':min(values),'max':max(values)},ensure_ascii=True))
