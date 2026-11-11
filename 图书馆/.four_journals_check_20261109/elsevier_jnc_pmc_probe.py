import pathlib,requests,concurrent.futures,json,sys,re,html
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent
jobs=[('jnc_pmc_html','https://pmc.ncbi.nlm.nih.gov/articles/PMC13276717/'),('jnc_epmc_xml','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13276717/fullTextXML'),('jnc_oa_api','https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC13276717'),('jnc_pmc_bio','https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13276717/?report=xml'),('jnc_efetch','https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC13276717/unicode')]
def get(item):
 key,url=item;res={'key':key,'url':url}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,20),headers={'User-Agent':'Mozilla/5.0'});(ROOT/f'elsevier_{key}.txt').write_text(r.text,encoding='utf8');t=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',r.text)))
  res.update(status=r.status_code,final_url=r.url,length=len(r.content),snippets=[t[max(0,m.start()-100):m.start()+400]for m in re.finditer(r'Received|Accepted|history|date-type',t,re.I)][:20],title=re.findall(r'<title>(.*?)</title>',r.text,re.S)[:1])
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as ex:results=list(ex.map(get,jobs))
(ROOT/'elsevier_jnc_pmc_access.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
