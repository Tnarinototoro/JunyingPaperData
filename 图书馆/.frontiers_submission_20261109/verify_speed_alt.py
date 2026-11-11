import pathlib,requests,sys,json,concurrent.futures
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
jobs=[('abstract1858698','https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1858698/abstract'),('abs1883980','https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1883980/abstract'),('scope','https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about'),('review','https://www.frontiersin.org/about/peer-review')]
def get(item):
 key,url=item
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(10,20),headers={'User-Agent':'Mozilla/5.0'})
  (ROOT/f'speed_alt_{key}.html').write_text(r.text,encoding='utf8');res={'key':key,'url':url,'status':r.status_code,'length':len(r.content)}
 except Exception as e:res={'key':key,'url':url,'error':str(e)}
 print(json.dumps(res),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(get,jobs))
(ROOT/'speed_alt_refresh.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
