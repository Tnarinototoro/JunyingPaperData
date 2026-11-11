import pathlib,requests,concurrent.futures,json,datetime,re,sys,io
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT.parent/'.journal_speed_20261108/python_pdf_deps'))
from pypdf import PdfReader
jobs=[
('100505','https://uwe-repository.worktribe.com/preview/16652091/1-s2.0-S2590252026002126-main.pdf'),
('100444','https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13576388/fullTextXML'),
('100456','https://escholarship.org/content/qt90h8c013/qt90h8c013.pdf'),
('100503','https://repository.rothamsted.ac.uk/id/eprint/34242/1/Nosrati%20et%20al%20City%20and%20Environment%202026.pdf')]
def get(item):
 k,u=item;z={'article':k,'url':u,'checked_at':datetime.datetime.now().isoformat(timespec='seconds')}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(u,timeout=(6,18),headers={'User-Agent':'Mozilla/5.0'});z.update(status=r.status_code,final_url=r.url,length=len(r.content))
  if r.content.startswith(b'%PDF'):
   (ROOT/f'city_sample_{k}.pdf').write_bytes(r.content);reader=PdfReader(io.BytesIO(r.content));t='\n'.join(p.extract_text() or ''for p in reader.pages[:3]);(ROOT/f'city_sample_{k}.txt').write_text(t,encoding='utf8');z['history_contexts']=[t[max(0,m.start()-100):m.start()+250]for m in re.finditer(r'received|accepted|revised',t,re.I)][:15]
  else:
   (ROOT/f'city_sample_{k}_response.txt').write_text(r.text,encoding='utf8');z['history_contexts']=[r.text[max(0,m.start()-120):m.start()+450]for m in re.finditer(r'<history|date-type="received"|date-type="accepted"|is-manuscript|article-type=',r.text,re.I)][:10]
 except Exception as e:z['error']=str(e)
 print(json.dumps(z,ensure_ascii=False),flush=True);return z
with concurrent.futures.ThreadPoolExecutor(max_workers=4)as ex:res=list(ex.map(get,jobs))
(ROOT/'city_sample_access.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
