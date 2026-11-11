import sys,json,re,pathlib,concurrent.futures,requests
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
def get(item):
 key,url=item
 try:
  s=requests.Session();s.trust_env=False
  r=s.get(url,timeout=(10,25),headers={'User-Agent':'Mozilla/5.0'})
  suffix='.pdf' if r.content.startswith(b'%PDF') else '.txt'
  (ROOT/f'nonmdpi_pdf_{key}{suffix}').write_bytes(r.content)
  text=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',r.text)) if suffix!='.pdf' else ''
  snippets=[text[max(0,m.start()-80):m.start()+400] for m in re.finditer(r'Received|Accepted|date-received|date-accepted|submission-to-acceptance|Submission to acceptance',text,re.I)]
  return {'key':key,'url':url,'status':r.status_code,'final_url':r.url,'length':len(r.content),'content_type':r.headers.get('content-type'),'filetype':suffix,'snippets':snippets[:20]}
 except Exception as e:return {'key':key,'url':url,'error':str(e)}
jobs=[
 ('jort_pdf','https://www.sciencedirect.com/science/article/pii/S2213078026000630/pdf'),
 ('jort_pdfft','https://www.sciencedirect.com/science/article/pii/S2213078026000630/pdfft?isDTMRedir=true&download=true'),
 ('jort_abs','https://www.sciencedirect.com/science/article/abs/pii/S2213078026000630'),
 ('jort_api_pdf','https://api.elsevier.com/content/article/PII:S2213078026000630?httpAccept=application/pdf'),
 ('cres_api_pdf','https://api.elsevier.com/content/article/PII:S266604902600037X?httpAccept=application/pdf'),
 ('jort_reader','https://reader.elsevier.com/reader/sd/pii/S2213078026000630'),
 ('jnc_xml','https://api.elsevier.com/content/article/PII:S1617138126002864?httpAccept=text/xml'),
 ('jnc_html','https://www.sciencedirect.com/science/article/pii/S1617138126002864'),
 ('jort_elsevierscope','https://www.elsevier.com/journals/journal-of-outdoor-recreation-and-tourism/2213-0780/guide-for-authors'),
 ('jort_sd_json','https://www.sciencedirect.com/science/article/pii/S2213078026000630?via=ihub')]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_pdf_probe_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
