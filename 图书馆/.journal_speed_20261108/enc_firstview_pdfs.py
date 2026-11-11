from sample_enc_followup import ROOT,P,get,run
import pathlib,concurrent.futures,re,html,json
text=(ROOT/'root_https_www_cambridge_org_core_journals_environmental_conservation_firstview.html').read_text(encoding='utf8')
p=P();p.feed(text);links=list(dict.fromkeys(x for x in p.links if '/environmental-conservation/article/'in x))
def each(item):
 i,path=item;u='https://www.cambridge.org'+path;r,p,t=run(u,f'enc_firstview_{i}')
 meta={m[0]:html.unescape(m[1])for m in re.findall(r'<meta\s+name="([^"]+)"\s+content="([^"]+)',r.text)}
 out={'list_order':i,'url':u,'status':r.status_code,'title':meta.get('citation_title'),'doi':meta.get('citation_doi'),'online':meta.get('citation_online_date'),'pdf_url':meta.get('citation_pdf_url')}
 if i in [1,2,3,4,8] and out['pdf_url']:
  try:
   pr=get(out['pdf_url']);out.update(pdf_status=pr.status_code,pdf_bytes=len(pr.content),pdf_type=pr.headers.get('Content-Type'))
   if pr.content.startswith(b'%PDF'):(ROOT/f'enc_firstview_{i}.pdf').write_bytes(pr.content)
  except Exception as e:out['pdf_error']=str(e)
 print(json.dumps(out,ensure_ascii=True),flush=True);return out
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as ex:out=list(ex.map(each,enumerate(links[:8],1)))
(ROOT/'enc_firstview_sample_access.json').write_text(json.dumps({'list_url':'https://www.cambridge.org/core/journals/environmental-conservation/firstview','checked_date':'2026-11-09','results':out},ensure_ascii=False,indent=2),encoding='utf8')
