import pathlib,sys,json,re,requests,concurrent.futures,datetime,html,statistics
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
BASE=ROOT.parent/'.journal_speed_20261108'
old=json.loads((BASE/'nonmdpi_section_histories_selected_20261109.json').read_text(encoding='utf8'))
old=[x for x in old if x['journal']=='Frontiers in Sustainable Cities']
jobs=[('article_'+x['doi'].rsplit('.',1)[-1],x['url']) for x in old]
jobs += [('journal_about','https://www.frontiersin.org/journals/sustainable-cities/about'),('section_scope','https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about'),('journal_main','https://www.frontiersin.org/journals/sustainable-cities'),('review_process','https://www.frontiersin.org/about/peer-review'),('section_articles','https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/articles'),('journal_why_submit','https://www.frontiersin.org/journals/sustainable-cities/for-authors/why-submit'),('peer_review_guidelines','https://www.frontiersin.org/guidelines/peer-review-guidelines')]
def clean(t):
 t=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>',' ',t,flags=re.I)
 return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',t))).strip()
def get(item):
 key,url=item;res={'key':key,'url':url}
 try:
  s=requests.Session();s.trust_env=False;r=s.get(url,timeout=(10,25),headers={'User-Agent':'Mozilla/5.0'});text=clean(r.text)
  (ROOT/f'speed_{key}.html').write_text(r.text,encoding='utf8');(ROOT/f'speed_{key}.txt').write_text(text,encoding='utf8')
  res.update(status=r.status_code,final_url=r.url,length=len(r.content),snapshot=f'speed_{key}.html')
  if key.startswith('article_'):
   res['title']=clean(re.search(r'<title>([\s\S]*?)</title>',r.text).group(1))
   for term in ['Received','Revised','Accepted','Published']:
    m=re.search(r'\b'+term+r'\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})',text)
    if m:res[term]=m.group(1);res[term+'_context']=text[max(0,m.start()-90):m.end()+200]
   if res.get('Received') and res.get('Accepted'):res['days']=(datetime.datetime.strptime(res['Accepted'],'%d %B %Y')-datetime.datetime.strptime(res['Received'],'%d %B %Y')).days
   res['type_status_contexts']=[text[max(0,m.start()-80):m.start()+250] for m in re.finditer(r'Original Research|Provisionally accepted|Provisional|accepted manuscript|final version',text,re.I)][:12]
   res['metadata']={k:re.findall(r'<meta[^>]+name=["\x27]'+k+r'["\x27][^>]+content=["\x27]([^"\x27]+)',r.text,re.I) for k in ['citation_title','citation_date','citation_publication_date','citation_online_date','citation_article_type']}
   res['urban_greening_contexts']=[text[max(0,m.start()-50):m.start()+180] for m in re.finditer('Urban Greening',text)][-6:]
  else:
   res['time_contexts']=[text[max(0,m.start()-100):m.start()+350] for m in re.finditer(r'\b\d+\s*(?:days?|weeks?)|acceptance|first decision|review time|review speed|submission to|guarantee',text,re.I)][:35]
   if key=='section_scope':
    start=text.find('Mission & scope');res['scope_text']=text[start:start+12000] if start>=0 else text[3000:16000]
  print(json.dumps(res,ensure_ascii=False),flush=True)
 except Exception as e:res['error']=str(e);print(json.dumps(res,ensure_ascii=False),flush=True)
 return res
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:results=list(ex.map(get,jobs))
evidence={'checked_date':'2026-11-09','retrieved_at_local':datetime.datetime.now().isoformat(timespec='seconds'),'sources':results,'prior_selection':[{'doi':x['doi'],'days':x['days'],'section_source_order':x.get('section_source_order'),'original_research':x.get('original_research')}for x in old]}
guidelines=(ROOT/'guidelines_fulltext.txt').read_text(encoding='utf8')
evidence['guidelines_read']={'filename':'guidelines_fulltext.txt','characters':len(guidelines),'lines':len(guidelines.splitlines()),'review_time_guarantee_found':False,'relevant_lines':[x for x in guidelines.splitlines() if re.search('guarantee|delay|review|accept',x,re.I)]}
(ROOT/'speed_scope_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
