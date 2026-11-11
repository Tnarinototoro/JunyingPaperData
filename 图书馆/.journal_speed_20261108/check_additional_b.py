from check_springer_other import fetch,ROOT
import concurrent.futures,json,re,urllib.parse
ITEMS={
'ENC metrics':'https://www.cambridge.org/core/journals/environmental-conservation/information/about-this-journal/journal-metrics',
'ENC review process':'https://www.cambridge.org/core/journals/environmental-conservation/information/peer-review-information/review-process',
'ARQ metrics':'https://www.cambridge.org/core/journals/arq-architectural-research-quarterly/information/about-this-journal/journal-metrics',
'JEPM metrics new':'https://www.tandfonline.com/journals/cjep20/about-this-journal#journal-metrics',
'Landscape Research metrics new':'https://www.tandfonline.com/journals/clar20/about-this-journal#journal-metrics',
'EER metrics new':'https://www.tandfonline.com/journals/ceer20/about-this-journal#journal-metrics',
'springer Urban Biodiversity search':'https://link.springer.com/search?query='+urllib.parse.quote('"Urban Biodiversity and Ecosystem Services"'),
'springer Ecology Ecosystem search':'https://link.springer.com/search?query='+urllib.parse.quote('"Ecology & Ecosystem Services"'),
}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(fetch,ITEMS.items()))
(ROOT/'springer_more_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for name in ['enc_metrics','enc_review_process','arq_metrics']:
 p=ROOT/(name+'.txt')
 if p.exists():
  t=p.read_text(encoding='utf8')
  print(json.dumps({'filename':name,'tail':t[-13000:]},ensure_ascii=True),flush=True)
