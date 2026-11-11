import sys,json,re,pathlib,concurrent.futures,requests,urllib.parse
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
jobs=[]
for j in json.loads((ROOT/'nonmdpi_repository_locations.json').read_text(encoding='utf8')):
 for w in j.get('works',[]):
  if any(x in w['title'].lower() for x in ['review','meta-analysis','editorial','progress and prospects']):continue
  for a in w['locations']:
   url=a.get('pdf_url') or a.get('landing_page_url')
   if not url or any(x in url for x in ['sciencedirect','doi.org','biorxiv','osf.io','ssrn','zenodo','doaj']):continue
   jobs.append({'journal':j['journal'],'doi':w['doi'],'title':w['title'],'url':url})
def get(item):
 ritem=item.copy();url=item['url'];key=re.sub('[^a-zA-Z0-9]+','_',item['doi'].replace('https://doi.org/',''))
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(10,30),headers={'User-Agent':'Mozilla/5.0'})
  suffix='.pdf' if r.content.startswith(b'%PDF') else '.html'
  filename=f'nonmdpi_repo_{key}{suffix}';(ROOT/filename).write_bytes(r.content)
  ritem.update(status=r.status_code,final_url=r.url,filename=filename,length=len(r.content))
  if suffix!='.pdf':
   ritem['pdf_links']=list(dict.fromkeys(urllib.parse.urljoin(r.url,x) for x in re.findall(r'(?:href|content)=[\"\x27]([^\"\x27]*(?:\.pdf|/bitstream|/bitstreams|/Download/|/files/)[^\"\x27]*)',r.text,re.I)))[:15]
  return ritem
 except Exception as e:ritem['error']=str(e);return ritem
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
(ROOT/'nonmdpi_repo_download_log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
for r in results:print(json.dumps(r,ensure_ascii=False),flush=True)
