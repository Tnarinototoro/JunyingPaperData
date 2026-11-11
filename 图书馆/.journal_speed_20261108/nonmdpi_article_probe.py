import sys,json,re,pathlib,concurrent.futures,requests
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
def get(item):
 key,url=item
 try:
  s=requests.Session();s.trust_env=False
  r=s.get(url,timeout=(10,25),headers={'User-Agent':'Mozilla/5.0'})
  (ROOT/f'nonmdpi_art_{key}.txt').write_text(r.text,encoding='utf8')
  text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',r.text))
  snippets=[text[max(0,m.start()-80):m.start()+350] for m in re.finditer(r'Received|Accepted|date-received|date-accepted|submission-to-acceptance|Submission to acceptance',text,re.I)]
  return {'key':key,'url':url,'status':r.status_code,'final_url':r.url,'length':len(r.content),'snippets':snippets[:20]}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
jobs=[
 ('jnc_crossref','https://api.crossref.org/journals/1617-1381/works?sort=published&order=desc&rows=8&filter=until-pub-date:2026-11-08'),
 ('jort_xml','https://api.elsevier.com/content/article/PII:S2213078026000630?httpAccept=text/xml'),
 ('cres_xml','https://api.elsevier.com/content/article/PII:S266604902600037X?httpAccept=text/xml'),
 ('jort_html','https://www.sciencedirect.com/science/article/pii/S2213078026000630'),
 ('cres_html','https://www.sciencedirect.com/science/article/pii/S266604902600037X'),
 ('jort_api_full','https://api.elsevier.com/content/article/pii/S2213078026000630?view=FULL'),
 ('jort_api_meta','https://api.elsevier.com/content/article/pii/S2213078026000630?view=META'),
 ('jort_linkinghub','https://linkinghub.elsevier.com/retrieve/pii/S2213078026000630'),
 ('jem_xml','https://api.elsevier.com/content/article/PII:S0301479726026563?httpAccept=text/xml')]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_article_probe_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
