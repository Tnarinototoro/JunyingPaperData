from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json,sys,importlib.util
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).parent
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','r':'http://schemas.openxmlformats.org/package/2006/relationships'}
with ZipFile(ROOT/'Guidelines for authors.docx') as z:
 parts=[n for n in z.namelist() if n=='word/document.xml' or (n.startswith('word/') and any(t in n for t in ['header','footer','footnotes','endnotes','comments']) and n.endswith('.xml'))]
 text=[];counts={}
 for name in parts:
  tree=ET.fromstring(z.read(name));paras=[]
  for p in tree.findall('.//w:p',NS):
   chunks=[]
   for e in p.iter():
    local=e.tag.rsplit('}',1)[-1]
    if local in ['t','delText','instrText'] and e.text:chunks.append(e.text)
    elif local=='tab':chunks.append('\t')
    elif local in ['br','cr']:chunks.append('\n')
   line=''.join(chunks)
   if line.strip():paras.append(line)
  counts[name]={'paragraphs':len(paras),'characters':sum(map(len,paras))}
  text.append('PART '+name)
  text.extend(f'{i:04d}\t{s}' for i,s in enumerate(paras,1))
 links=[]
 for name in z.namelist():
  if name.endswith('.rels') and name.startswith('word/'):
   for e in ET.fromstring(z.read(name)):
    if e.attrib.get('TargetMode')=='External':links.append({'part':name,**e.attrib})
(OUT/'guidelines_fulltext.txt').write_text('\n'.join(text)+'\n',encoding='utf-8')
(OUT/'guidelines_external_links.json').write_text(json.dumps(links,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'parts':counts,'external_links':len(links),'python_docx_available':bool(importlib.util.find_spec('docx')),'markdown_available':bool(importlib.util.find_spec('markdown'))},ensure_ascii=False))
