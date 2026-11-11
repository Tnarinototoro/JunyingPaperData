import sys,json,re,pathlib,concurrent.futures,subprocess
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent;sys.path.insert(0,str(ROOT/'python_pdf_deps'))
from pypdf import PdfReader
jobs=[
('jort','10.1016/j.jort.2026.101078','The skin of sorrow: Protected areas and tourism','https://hal.science/hal-05724989/document'),
('jort','10.1016/j.jort.2026.101052','Outdoor recreation in a changing climate','https://www.research.ed.ac.uk/ws/files/661625484/SmithEtalJORT2026OutdoorRecreationInAChangingClimate.pdf'),
('jnc','10.1016/j.jnc.2026.127399','Human-wildlife conflicts in Polish cities','https://ruj.uj.edu.pl/handle/item/581230'),
('jnc','10.1016/j.jnc.2026.127389','Naturalized range expansion','https://repozitorij.upr.si/Dokument.php?id=35542&dn='),
('jem','10.1016/j.jenvman.2026.131156','Understanding public preferences for urban wildflower meadows','https://kar.kent.ac.uk/117287/1/1-s2.0-S0301479726026162-main.pdf'),
('cres','10.1016/j.crsust.2026.100340','Code ecologies','https://researchonline.rca.ac.uk/6667/8/1-s2.0-S2666049026000083-main.pdf'),
('cres','10.1016/j.crsust.2026.100379','Future reef island habitability under climate change and the role of governance','https://www.repository.cam.ac.uk/server/api/core/bitstreams/f96e3139-894e-4bf8-8bf9-84f49d830084/content')]
def get(item):
 journal,doi,title,url=item;key=re.sub('[^a-zA-Z0-9]+','_',doi);fn=ROOT/f'nonmdpi_last_{key}.dat';res={'journal':journal,'doi':doi,'title':title,'url':url,'filename':fn.name}
 try:
  script="import requests,sys,pathlib;s=requests.Session();s.trust_env=False;r=s.get(sys.argv[1],timeout=(6,20));pathlib.Path(sys.argv[2]).write_bytes(r.content);print(r.status_code)"
  p=subprocess.run([sys.executable,'-c',script,url,str(fn)],capture_output=True,timeout=27);res.update(status=p.stdout.decode(errors='replace').strip(),error=p.stderr.decode(errors='replace')[:100])
  if fn.exists():
   res['length']=fn.stat().st_size
   if fn.read_bytes().startswith(b'%PDF'):
    r=PdfReader(fn);text='\n'.join(p.extract_text() for p in r.pages[:4]);(ROOT/f'nonmdpi_last_{key}_first4.txt').write_text(text,encoding='utf8');text=re.sub(r'\s+',' ',text)
    res['snippets']=[text[max(0,m.start()-50):m.start()+400] for m in re.finditer(r'Received|Accepted|Article history',text,re.I)];res['start']=text[:900]
   else:
    t=fn.read_text(encoding='utf8',errors='replace');res['bitstream_ids']=list(dict.fromkeys(re.findall(r'/bitstreams/([0-9a-f-]{36})',t)))[:5]
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=7) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_last_batch_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
