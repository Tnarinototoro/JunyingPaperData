import sys,json,re,pathlib,concurrent.futures,subprocess
sys.stdout.reconfigure(encoding='utf8');ROOT=pathlib.Path(__file__).parent;sys.path.insert(0,str(ROOT/'python_pdf_deps'))
from pypdf import PdfReader
jobs=[]
for j in json.loads((ROOT/'nonmdpi_more_locations.json').read_text(encoding='utf8')):
 n=0
 for w in j['works']:
  if any(x in w['title'].lower() for x in ['review','meta-analysis','editorial','progress and prospects']):continue
  for a in w['locations']:
   url=a.get('pdf_url')
   if not url:continue
   if any(x in url for x in ['biorxiv','osf','researchsquare']):continue
   jobs.append({'journal':j['journal'],'doi':w['doi'],'title':w['title'],'url':url});n+=1;break
  if n>=5:break
def get(item):
 res=item.copy();key=re.sub('[^a-zA-Z0-9]+','_',item['doi'].replace('https://doi.org/',''));fn=ROOT/f'nonmdpi_curl_{key}.pdf'
 try:
  script="import requests,sys,pathlib;s=requests.Session();s.trust_env=False;r=s.get(sys.argv[1],timeout=(5,15));pathlib.Path(sys.argv[2]).write_bytes(r.content);print(r.status_code)"
  p=subprocess.run([sys.executable,'-c',script,item['url'],str(fn)],capture_output=True,timeout=21)
  res.update(code=p.returncode,status=p.stdout.decode(errors='replace'),error=p.stderr.decode(errors='replace')[:200],filename=fn.name)
  if fn.exists():
   res['length']=fn.stat().st_size
   if fn.read_bytes().startswith(b'%PDF'):
    r=PdfReader(fn);text='\n'.join(p.extract_text() for p in r.pages[:3]);(ROOT/f'nonmdpi_curl_{key}_first3.txt').write_text(text,encoding='utf8');text=re.sub(r'\s+',' ',text)
    res['snippets']=[text[max(0,m.start()-40):m.start()+400] for m in re.finditer(r'Received|Accepted|Article history',text,re.I)];res['start']=text[:1200]
 except Exception as e:res['error']=str(e)
 print(json.dumps(res,ensure_ascii=False),flush=True);return res
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_curl_pdf_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
