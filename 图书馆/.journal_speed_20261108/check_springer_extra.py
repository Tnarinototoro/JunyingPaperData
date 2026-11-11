from check_springer_other import fetch,ROOT
import concurrent.futures,json,re
ITEMS={
'Discover Cities scope':'https://link.springer.com/journal/44327/aims-and-scope',
'Urban Ecosystems scope':'https://link.springer.com/journal/11252/aims-and-scope',
'Environmental Earth Sciences scope':'https://link.springer.com/journal/12665/aims-and-scope',
'Environmental Management scope':'https://link.springer.com/journal/267/aims-and-scope',
'Landscape Ecology scope':'https://link.springer.com/journal/10980/aims-and-scope',
'Discover Environment scope':'https://link.springer.com/journal/44274/aims-and-scope',
'Discover Sustainability scope':'https://link.springer.com/journal/43621/aims-and-scope',
'Urban Design International scope':'https://link.springer.com/journal/41289/aims-and-scope',
'Environment Development Sustainability scope':'https://link.springer.com/journal/10668/aims-and-scope',
'Environmental Management metrics':'https://link.springer.com/journal/267/metrics',
'Environmental Conservation information':'https://www.cambridge.org/core/journals/environmental-conservation/information/about-this-journal',
'Environmental Conservation author instructions':'https://www.cambridge.org/core/journals/environmental-conservation/information/author-instructions',
'ARQ information':'https://www.cambridge.org/core/journals/arq-architectural-research-quarterly/information/about-this-journal',
'JEPM metrics alternative':'https://www.tandfonline.com/action/journalInformation?show=journalMetrics&journalCode=cjep20',
'Landscape Research metrics alternative':'https://www.tandfonline.com/action/journalInformation?show=journalMetrics&journalCode=clar20',
'EER metrics alternative':'https://www.tandfonline.com/action/journalInformation?show=journalMetrics&journalCode=ceer20',
'People Nature metrics':'https://besjournals.onlinelibrary.wiley.com/journal/25758314/journal-metrics',
'Land Degradation metrics':'https://onlinelibrary.wiley.com/journal/1099145x/journal-metrics',
'Journal Urban Ecology about':'https://academic.oup.com/jue/pages/About',
'Forest Science about':'https://academic.oup.com/forestscience/pages/About',
'Forestry about':'https://academic.oup.com/forestry/pages/About',
'Journal Environmental Law about':'https://academic.oup.com/jel/pages/About'}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: results=list(ex.map(fetch,ITEMS.items()))
(ROOT/'springer_extra_evidence.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
for r in results:
 if 'status' in r and r['status']==200 and 'scope' in r['journal']:
  text=(ROOT/(re.sub('[^a-z0-9]+','_',r['journal'].lower()).strip('_')+'.txt')).read_text(encoding='utf-8')
  p=text.find('Aims and scope',text.find('Journal menu'))
  print(r['journal'],text[p:p+6000],flush=True)
