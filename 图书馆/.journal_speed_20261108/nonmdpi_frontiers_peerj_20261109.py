import requests,sys,re,json,datetime,statistics,concurrent.futures,html
from pathlib import Path
from check_c import Text
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).parent
CHECKED='2026-11-09'
JOURNALS={'Frontiers in Sustainable Cities':('2624-9634','sustainable-cities'), 'Frontiers in Conservation Science':('2673-611X','conservation-science'), 'Frontiers in Environmental Science':('2296-665X','environmental-science'), 'PeerJ':('2167-8359','peerj')}
def get(url):
 s=requests.Session();s.trust_env=False
 return s.get(url,timeout=(12,25),headers={'User-Agent':'Mozilla/5.0'})
def recent(item):
 name,(issn,slug)=item
 url=f'https://api.crossref.org/journals/{issn}/works?sort=published&order=desc&rows=12&filter=until-pub-date:{CHECKED}'
 try:
  r=get(url);(ROOT/f'nonmdpi_{slug}_crossref_20261109.json').write_text(r.text,encoding='utf-8')
  entries=r.json()['message']['items']
  return [(name,slug,x) for x in entries]
 except Exception as e:return [{'journal':name,'error':str(e)}]
def fetch_article(item):
 if isinstance(item,dict):return item
 name,slug,x=item;doi=x['DOI'];result={'journal':name,'doi':doi,'title':x.get('title',[''])[0],'crossref_url':x.get('URL')}
 if slug=='peerj':
  number=doi.split('.')[-1];url=f'https://peerj.com/articles/{number}/'
 else:url=f'https://www.frontiersin.org/journals/{slug}/articles/{doi}/full'
 result['url']=url
 try:
  r=get(url);result['status']=r.status_code
  titlematch=re.search(r'<title>(.*?)</title>',r.text,re.S|re.I)
  if titlematch:result['official_page_title']=html.unescape(titlematch.group(1)).removeprefix('Frontiers | ').strip()
  stem='nonmdpi_'+re.sub(r'[^a-z0-9]+','_',doi.lower())
  (ROOT/(stem+'.html')).write_text(r.text,encoding='utf-8')
  parser=Text();parser.feed(r.text)
  t=re.sub(r'\s+',' ',''.join(parser.chunks)).strip()
  (ROOT/(stem+'.txt')).write_text(t,encoding='utf-8')
  result['header']=t[:1600]
  result['original_research']=bool(re.search(r'ORIGINAL RESEARCH article',t,re.I)) if slug!='peerj' else bool(re.search('Research Article',t,re.I))
  for field in ['Received','Revised','Accepted','Published']:
   hits=list(re.finditer(field+r'\s*[:]?\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',t))
   if hits:
    m=hits[-1];result[field]=m.group(1);result[field+'_context']=t[max(0,m.start()-100):m.end()+180]
  if 'Received' in result and 'Accepted' in result:
   a=datetime.datetime.strptime(result['Received'],'%d %B %Y').date();b=datetime.datetime.strptime(result['Accepted'],'%d %B %Y').date()
   result['days']=(b-a).days;result['valid_dates']=a<=b<=datetime.date.fromisoformat(CHECKED)
   if 'Revised' in result:
    c=datetime.datetime.strptime(result['Revised'],'%d %B %Y').date();result['valid_dates']&=a<=c<=b
 except Exception as e:result['error']=str(e)
 return result
def main():
 subset={k:v for k,v in JOURNALS.items() if len(sys.argv)<2 or v[1] in sys.argv[1:]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:lists=list(ex.map(recent,subset.items()))
 items=[x for batch in lists for x in batch]
 print('candidate_count',len(items),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(fetch_article,items))
 path=ROOT/'nonmdpi_frontiers_peerj_histories_20261109.json'
 if path.exists() and len(subset)<len(JOURNALS):
  old=json.loads(path.read_text(encoding='utf-8'));results=[x for x in old if x['journal'] not in subset]+results
 path.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 for name in JOURNALS:
  candidates=[x for x in results if x['journal']==name]
  sel=[x for x in candidates if x.get('original_research') and x.get('valid_dates')][:5]
  print(name,'retrieved',len(candidates),'usable',len(sel),'days',[x['days'] for x in sel],flush=True)
 for x in results:
  if x['journal'] in subset:print(json.dumps({k:v for k,v in x.items() if k not in ['header'] and not k.endswith('_context')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
