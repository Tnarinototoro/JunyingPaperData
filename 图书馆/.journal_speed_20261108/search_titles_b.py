from check_springer_other import fetch,ROOT
import concurrent.futures,urllib.parse,json
items={
'google urban biodiversity':'https://www.google.com/search?q='+urllib.parse.quote('"Urban Biodiversity and Ecosystem Services" journal'),
'google ecology ecosystem':'https://www.google.com/search?q='+urllib.parse.quote('"Ecology & Ecosystem Services" journal'),
'bing urban biodiversity':'https://www.bing.com/search?q='+urllib.parse.quote('"Urban Biodiversity and Ecosystem Services" journal'),
'bing ecology ecosystem':'https://www.bing.com/search?q='+urllib.parse.quote('"Ecology & Ecosystem Services" journal')}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:r=list(ex.map(fetch,items.items()))
for name in ['google_urban_biodiversity','google_ecology_ecosystem','bing_urban_biodiversity','bing_ecology_ecosystem']:
 p=ROOT/(name+'.txt')
 if p.exists():print(json.dumps({'file':name,'text':p.read_text(encoding='utf8')[:18000]},ensure_ascii=True),flush=True)
