import sys,json,re,pathlib,concurrent.futures,subprocess,datetime
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent;BASE=ROOT.parent/'.journal_speed_20261108';sys.path.insert(0,str(BASE/'python_pdf_deps'))
from pypdf import PdfReader
jobs=[
('jnc','10.1016/j.jnc.2026.127389','Naturalized range expansion: Assessing the invasion risk of aoudad into Balkan chamois habitat','https://repozitorij.uni-lj.si/Dokument.php?id=243491&dn='),
('jnc','10.1016/j.jnc.2026.127384','Using wild bees as indicators of landscape composition and bee diversity','https://repository.naturalis.nl/pub/802219/Visser-2026-Using-wild-bees-as-indicators-A.pdf'),
('jem','10.1016/j.jenvman.2026.131156','Understanding public preferences for urban wildflower meadows','https://spiral.imperial.ac.uk/server/api/core/bitstreams/8ebd20d6-e37f-442d-bdbc-a35427f92681/content'),
('jem','10.1016/j.jenvman.2026.131156','Understanding public preferences for urban wildflower meadows','https://kar.kent.ac.uk/117287/1/1-s2.0-S0301479726026162-main.pdf'),
('jem','10.1016/j.jenvman.2026.131165','Redeposited particles mitigate dredging effect on internal phosphorus loading','https://ray.yorksj.ac.uk/id/eprint/16242/1/Manuscript_R2%20%28unmarked%29.pdf')]
def get(item):
 journal,doi,title,url=item;key=re.sub('[^a-zA-Z0-9]+','_',doi)+'_'+str(jobs.index(item));fn=ROOT/f'elsevier_article_{key}.dat';res={'journal':journal,'doi':doi,'title':title,'url':url,'checked_date':'2026-11-09','filename':fn.name}
 try:
  script="import requests,sys,pathlib;s=requests.Session();s.trust_env=False;r=s.get(sys.argv[1],timeout=(6,18),headers={'User-Agent':'Mozilla/5.0'});pathlib.Path(sys.argv[2]).write_bytes(r.content);print(r.status_code)"
  p=subprocess.run([sys.executable,'-c',script,url,str(fn)],capture_output=True,timeout=28);res.update(status=p.stdout.decode(errors='replace').strip(),error=p.stderr.decode(errors='replace')[:120])
  if fn.exists():
   res['length']=fn.stat().st_size
   if fn.read_bytes().startswith(b'%PDF'):
    r=PdfReader(fn);text='\n'.join(p.extract_text() for p in r.pages[:3]);(ROOT/f'elsevier_article_{key}_first3.txt').write_text(text,encoding='utf8');text=re.sub(r'\s+',' ',text)
    res['snippets']=[text[max(0,m.start()-50):m.start()+350]for m in re.finditer(r'Received|Accepted|Article history',text,re.I)]
    for term in ['Received','Accepted']:
     m=re.search(r'\b'+term+r'\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',text)
     if m:res[term]=m.group(1)
    if res.get('Received')and res.get('Accepted'):res['days']=(datetime.datetime.strptime(res['Accepted'],'%d %B %Y')-datetime.datetime.strptime(res['Received'],'%d %B %Y')).days
    res['header']=text[:1300]
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as ex:results=list(ex.map(get,jobs))
(ROOT/'elsevier_article_date_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
