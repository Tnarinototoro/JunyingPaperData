import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT/'python_pdf_deps'))
from pypdf import PdfReader
jobs=[
 ('jort_101052','https://www.research.ed.ac.uk/files/661625484/SmithEtalJORT2026OutdoorRecreationInAChangingClimate.pdf'),
 ('jort_101046','https://idus.us.es/server/api/core/bitstreams/4cb89072-e717-4b77-af8b-da0c68b90feb/content'),
 ('cres_100337','https://pure.uva.nl/ws/files/344461153/Evaluating_socioeconomic_and_equity_outcomes_in_livelihood_interventions.pdf'),
 ('cres_100344','https://ruj.uj.edu.pl/server/api/core/bitstreams/d98e64cd-b2d8-4082-bc84-97c30f0586a0/content'),
 ('jort_101070','https://vtechworks.lib.vt.edu/server/api/core/bitstreams/44c9f36e-18f7-47fb-8bcd-ee20d516e8b1/content')]
def get(item):
 key,url=item;res={'key':key,'url':url}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(8,22),headers={'User-Agent':'Mozilla/5.0'})
  suffix='.pdf' if r.content.startswith(b'%PDF') else '.html';fn=ROOT/f'nonmdpi_finalpdf_{key}{suffix}';fn.write_bytes(r.content)
  res.update(status=r.status_code,final_url=r.url,length=len(r.content),filename=fn.name)
  if suffix=='.pdf':
   reader=PdfReader(fn);text='\n'.join(p.extract_text() for p in reader.pages[:3]);(ROOT/f'nonmdpi_finalpdf_{key}_first3.txt').write_text(text,encoding='utf8')
   text=re.sub(r'\s+',' ',text);res['snippets']=[text[max(0,m.start()-50):m.start()+400] for m in re.finditer(r'Received|Accepted|Article history',text,re.I)];res['start']=text[:1600]
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_finalpdf_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
