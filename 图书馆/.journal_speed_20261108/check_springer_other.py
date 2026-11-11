import concurrent.futures, requests, re, json, pathlib, html, datetime
ROOT=pathlib.Path(__file__).parent
ROOT.mkdir(exist_ok=True)
JOURNALS={
'Forest Science':'https://academic.oup.com/forestscience',
'Discover Cities':'https://link.springer.com/journal/44327',
'Journal of Environmental Planning and Management':'https://www.tandfonline.com/journals/cjep20/about-this-journal',
'Urban Ecosystems':'https://link.springer.com/journal/11252',
'Environmental Earth Sciences':'https://link.springer.com/journal/12665',
'Environmental Education Research':'https://www.tandfonline.com/journals/ceer20/about-this-journal',
'Environmental Management':'https://link.springer.com/journal/267',
'Landscape Research':'https://www.tandfonline.com/journals/clar20/about-this-journal',
'Landscape Ecology':'https://link.springer.com/journal/10980',
'People and Nature':'https://besjournals.onlinelibrary.wiley.com/journal/25758314',
'Land Degradation & Development':'https://onlinelibrary.wiley.com/journal/1099145x',
'Forestry: An International Journal':'https://academic.oup.com/forestry',
'Journal of Environmental Law':'https://academic.oup.com/jel',
'Architectural Research Quarterly':'https://www.cambridge.org/core/journals/arq-architectural-research-quarterly',
'Environmental Conservation':'https://www.cambridge.org/core/journals/environmental-conservation',
'Discover Environment':'https://link.springer.com/journal/44274',
'Discover Sustainability':'https://link.springer.com/journal/43621',
'Journal of Urban Ecology':'https://academic.oup.com/jue',
'Urban Design International':'https://link.springer.com/journal/41289',
'Environment, Development and Sustainability':'https://link.springer.com/journal/10668'}
def fetch(item):
    name,url=item
    s=requests.Session();s.trust_env=False
    try:
        r=s.get(url,timeout=(15,35))
        slug=re.sub('[^a-z0-9]+','_',name.lower()).strip('_')
        (ROOT/(slug+'.html')).write_text(r.text,encoding='utf-8')
        text=re.sub(r'<script\b[^>]*>[\s\S]*?</script>|<style\b[^>]*>[\s\S]*?</style>', ' ',r.text,flags=re.I)
        text=html.unescape(re.sub('<[^>]+>',' ',text))
        text=re.sub(r'\s+',' ',text).strip()
        (ROOT/(slug+'.txt')).write_text(text,encoding='utf-8')
        snippets=[]
        for m in re.finditer('first decision|submission to|peer review|turnaround|acceptance rate|time to|scope|processing time',text,re.I):
            snippets.append(text[max(0,m.start()-130):m.end()+250])
        result={'journal':name,'url':url,'final_url':r.url,'status':r.status_code,'size':len(r.content),'title':re.findall('<title>(.*?)</title>',r.text,re.S),'snippets':snippets}
    except Exception as e: result={'journal':name,'url':url,'error':str(e)}
    print(json.dumps(result,ensure_ascii=True),flush=True)
    return result
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results=list(ex.map(fetch,JOURNALS.items()))
    (ROOT/'springer_other_evidence.json').write_text(json.dumps({'date':str(datetime.datetime.now()),'results':results},ensure_ascii=False,indent=2),encoding='utf-8')
