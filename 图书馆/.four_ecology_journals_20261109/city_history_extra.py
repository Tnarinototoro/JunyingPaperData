import pathlib,requests,concurrent.futures,json,datetime,re,sys,io
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
sys.path.insert(0,str(ROOT.parent/'.journal_speed_20261108/python_pdf_deps'))
from pypdf import PdfReader
jobs=[
('100415','https://www.utupub.fi/bitstreams/b2936758-3e08-464d-963f-c9cf66183230/download'),
('100488','https://infoscience.epfl.ch/bitstreams/5b4b086f-940f-41f9-8304-2655589537e5/download'),
('100434','https://repository.naturalis.nl/pub/802279/Dorst-2026-Urban-airborne-allergenic-pollen-A.pdf')]

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
(ROOT/'city_sample_access_extra.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf8')
