import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
def get(item):
 key,url=item
 try:
  s=requests.Session();s.trust_env=False
  r=s.get(url,timeout=(10,22),headers={'User-Agent':'Mozilla/5.0'})
  (ROOT/f'nonmdpi_alt_{key}.txt').write_text(r.text,encoding='utf8')
  text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',r.text))
  snippets=[text[max(0,m.start()-100):m.start()+450] for m in re.finditer(r'Received|Accepted|submission|review speed|decision',text,re.I)]
  return {'key':key,'url':url,'status':r.status_code,'final_url':r.url,'length':len(r.content),'snippets':snippets[:12]}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
jobs=[
 ('jort_insight','https://journalinsights.elsevier.com/journals/2213-0780/review_speed'),
 ('jnc_insight','https://journalinsights.elsevier.com/journals/1617-1381/review_speed'),
 ('jort_cdn','https://ars.els-cdn.com/content/image/1-s2.0-S2213078026000630-main.pdf'),
 ('jort_raw','https://api.elsevier.com/content/article/pii/S2213078026000630?httpAccept=text%2Fxml&view=FULL'),
 ('jort_raw2','https://api.elsevier.com/content/article/pii/S2213078026000630?httpAccept=text%2Fplain'),
 ('jort_search','https://www.bing.com/search?q='+urllib.parse.quote('"Sustainable outdoor recreation in rapidly urbanising landscapes" pdf')),
 ('jnc_search','https://www.bing.com/search?q='+urllib.parse.quote('"Journal for Nature Conservation" "2026" "Received" "Accepted" pdf')),
 ('cres_search','https://www.bing.com/search?q='+urllib.parse.quote('"Current Research in Environmental Sustainability" "2026" "Received" "Accepted" pdf'))]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_alt_probe_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
