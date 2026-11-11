import pathlib,json,re,statistics,datetime,sys
sys.stdout.reconfigure(encoding='utf8')
ROOT=pathlib.Path(__file__).parent
path=ROOT/'speed_scope_evidence.json';d=json.loads(path.read_text(encoding='utf8'));sources={x['key']:x for x in d['sources']}
rows=[]
for x in d['prior_selection']:
 key='article_'+x['doi'].rsplit('.',1)[-1];r=sources[key];h=(ROOT/r['snapshot']).read_text(encoding='utf8')
 raw=re.search(r'<script[^>]+id="__NUXT_DATA__"[^>]*>([\s\S]*?)</script>',h)
 meta={}
 if raw:
  a=json.loads(raw.group(1));o=next((o for o in a if isinstance(o,dict)and 'receptionDate'in o and 'acceptanceDate'in o),{})
  for k in ['doi','acceptanceDate','receptionDate','publicationDate','isPublished','isPublishedV2']:
   if k in o and isinstance(o[k],int)and 0<=o[k]<len(a):meta[k]=a[o[k]]
 r['article_internal_metadata']=meta
 text=(ROOT/f'speed_{key}.txt').read_text(encoding='utf8');m=re.search('The final, formatted version of the article will be published soon',text)
 r['accepted_not_finally_formatted']=bool(m)
 assert r['days']==x['days']
 assert r['metadata']['citation_article_type']==['Original Research']
 rows.append({'doi':x['doi'],'title':r['title'].removeprefix('Frontiers | '),'url':r['final_url'],'received':datetime.datetime.strptime(r['Received'],'%d %B %Y').date().isoformat(),'accepted':datetime.datetime.strptime(r['Accepted'],'%d %B %Y').date().isoformat(),'published':datetime.datetime.strptime(r['Published'],'%d %B %Y').date().isoformat()if r.get('Published')else None,'days':r['days'],'status':'受理済み・最終組版版は未公刊'if r['accepted_not_finally_formatted']else'正式公刊済み'})
days=[r['days']for r in rows]
d['verified_sample']={'n':len(rows),'days':days,'median':statistics.median(days),'minimum':min(days),'maximum':max(days),'mean':statistics.mean(days),'rows':rows,'interpretation':'已接收Original Research便利样本；含一篇未最终出版接受稿；不是全刊总体统计，也不是本稿时长保证。'}
d['overall_submission_to_acceptance']={'found':False,'claim_limit':'在已核主页/about、Urban Greening scope、Why submit、peer-review及peer-review-guidelines页面未取得本刊全刊同口径总体统计；不据此断言官网所有入口绝无此统计。'}
d['scope_assessment']={'fit':'都市公园保全与游憩协调、管理者行为及协作治理与Urban Greening范围吻合；须具体围绕都市绿地管理，不能仅泛化为社会问卷/TPB。','quotes':['governance of urban green and blue spaces for sustainable and resilient development of human settlements','human perception and use of urban green and blue spaces','innovative design and management of urban green and blue spaces, including novel technologies and green-grey hybrid solutions','power structures and mechanisms between governments, companies, and civil society in transformative processes'],'exclusion':'Studies that primarily address general environmental issues or unrelated social sciences are outside the scope of this section.'}
d['timing_interpretation']={'reviewer_endorsement':'The editor can then either accept the final version of the manuscript or request further changes as necessary, typically within a few days.','correction_deadlines':'authors requested to revise within 7/10/14 days; not journal receipt-to-acceptance','not_total':['arbitration updates every 2–4 weeks','APC payable within 30 days of acceptance','unresponsive authors for 30 days']}
path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
lines=['# Frontiers in Sustainable Cities：審査期間と投稿範囲の検証記録','','確認日：2026年11月9日。既存の5件を再抽出した後、公式ページを再取得して日付・記事種別・Urban Greening所属を確認した。12ページすべてHTTP 200。通常のブラウザー用User-Agentによるアクセスであり、認証情報は使用していない。','','## 期間に関する確認結果','','Urban Greeningに掲載・受理されたOriginal Research 5件のReceived→Acceptedは、41、44、59、61、182日で、標本中央値は59日である。これは5件の便宜的標本から計算した値であり、本誌全体またはセクション全体の公式中央値・平均値ではない。著者の修正期間を含み、採択された論文に限定される。5件は同一研究テーマ・同一研究方法ではない。','','|論文（公式リンク）|Received|Accepted|Received→Accepted|Published／状態|','|---|---|---|---:|---|']
for r in rows:lines.append(f"|[{r['title']}]({r['url']})|{r['received']}|{r['accepted']}|{r['days']}日|{r['published']or'日付なし'}；{r['status']}|")
lines += ['','182日の論文は、公式ページに「The final, formatted version of the article will be published soon.」と表示され、Published日がなく、2026年10月16日のAcceptedだけが示されている。したがって「正式公刊済み5編」ではなく、「受理済みOriginal Research 5件（最終組版版の公刊前1件を含む）」と記す。5件ともReceived→Acceptedが確認できるため、受理までを扱う標本に含めること自体は可能である。','','公式のjournal main、About、Urban Greening scope、Why submit、Peer review、Peer review guidelinesを確認した範囲では、本誌のSubmission→Acceptanceの全誌統計は取得できなかった。「全誌の審査期間は59日」「59日以内に受理される」「世界で最も速い」とは記載できない。初回の実質的な査読回答日も、上記5件のPublished/Received/Revised/Acceptedだけからは算出できない。','','## 範囲の適合性','','[Urban Greening公式Scope](https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about)には、都市・都市周辺の緑地・水辺の開発、改善、評価、ガバナンス、人々による利用、革新的な設計・管理、行政・企業・市民社会の関係などが明記されている。原稿の都市公園における保全と利用の調整、管理者の行動、多主体の関与はこの範囲と対応する。','','- “governance of urban green and blue spaces for sustainable and resilient development of human settlements”','- “human perception and use of urban green and blue spaces”','- “innovative design and management of urban green and blue spaces”','- “power structures and mechanisms between governments, companies, and civil society in transformative processes”','','一方、都市緑化との明確な関連を欠く一般的な環境問題・無関係な社会科学は対象外とされる。したがって「都市公園の保全・利用調整に役立つ管理上の知見」を前面に出し、SEMの実施自体を貢献としないことが適切である。','','## Word投稿規程の全文確認','','guidelines_fulltext.txtの全246段落（番号付き全文）を読了した。査読期間・受理期間の保証条項は確認できなかった。第28段落は英文校閲を受けても採択は保証されないこと、第156・176段落は図表の形式不備が出版工程を遅らせること、第246段落は不適切な投稿先の選択が遅延・不採択の可能性を高めることを述べる。','','公式Peer review guidelinesにある修正期限7／10／14日、異議申立ての更新2–4週間、受理後APC支払い30日は、投稿から受理までの保証期間ではない。また、査読者のendorsement後に編集者が通常数日で採択または追加修正を判断する記述も、その最終段階のみを指す。','','## 教授への説明で使用できる表現','','「本稿はUrban Greeningの対象範囲と整合している。公式ページで確認した受理済みOriginal Research 5件では、投稿から受理まで41–182日、標本中央値59日であった。ただし、全誌の公式統計ではなく、本稿の受理可否や期間を保証するものではない。」','','主報告書は変更していない。出典・本文の関連箇所・内部日付情報はspeed_scope_evidence.jsonに、取得ページはspeed_*.html/txtに保存した。']
(ROOT/'speed_scope_evidence.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'rows':rows,'median':statistics.median(days),'statuses':{k:sources[k]['status']for k in sources}},ensure_ascii=False,indent=2))
