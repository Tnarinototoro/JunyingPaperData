from pathlib import Path
import json
from datetime import datetime, date
from statistics import median

base = Path(__file__).resolve().parent
ue_raw = json.loads((base / 'urban_ecosystems_histories_all.json').read_text(encoding='utf-8'))
ue = ue_raw['results'][:5]
for row in ue:
    assert row['type'] == ['Research']
    row['received_iso'] = datetime.strptime(row['Received'], '%d %B %Y').date().isoformat()
    row['accepted_iso'] = datetime.strptime(row['Accepted'], '%d %B %Y').date().isoformat()
    assert (date.fromisoformat(row['accepted_iso']) - date.fromisoformat(row['received_iso'])).days == row['days']

access = json.loads((base / 'enc_firstview_sample_access.json').read_text(encoding='utf-8'))
histories = {
    2: ('2026-03-17', '2026-08-29', 'Research Paper'),
    3: ('2026-04-02', '2026-10-05', 'Research Paper'),
    4: ('2025-10-07', '2026-09-10', 'Report'),
}
enc = []
for row in access['results']:
    if row['list_order'] not in (1, 2, 3, 4, 8):
        continue
    item = dict(row)
    if row['list_order'] in histories:
        received, accepted, article_type = histories[row['list_order']]
        item.update(received_iso=received, accepted_iso=accepted, article_type=article_type,
                    days=(date.fromisoformat(accepted)-date.fromisoformat(received)).days,
                    history_source='Official PDF first page; OCR dates verified visually against rendered page',
                    local_pdf=f"enc_firstview_{row['list_order']}.pdf")
    else:
        item.update(history_unavailable='PDF URL returned text/html; no Received/Accepted history obtained; not replaced')
    enc.append(item)

def stats(rows):
    values = [r['days'] for r in rows if 'days' in r]
    return {'n': len(values), 'median_days': median(values), 'min_days': min(values), 'max_days': max(values), 'days_in_list_order': values}

result = {'verified_date': '2026-11-09', 'metric_definition': 'Accepted minus Received in calendar days; includes author revision time; samples of already accepted articles, not whole-journal statistics',
          'urban_ecosystems': {'list_url': ue_raw['list_url'], 'selection': 'First five Research articles in official latest articles list, unchanged list order', 'stats': stats(ue), 'articles': ue},
          'environmental_conservation': {'list_url': access['list_url'], 'selection': 'First five original Research Papers/Reports in FirstView list (positions 1,2,3,4,8); three histories obtained, two unavailable; comments and corrigendum excluded', 'stats': stats(enc), 'articles': enc}}
(base / 'non_mdpi_urban_ecosystems_enc_20261109.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

lines = [
    '# Urban Ecosystems 与 Environmental Conservation：非 MDPI 补充时长核验',
    '',
    '复核日期：2026-11-09。此补充只列两刊近期文章的官方 Received→Accepted 历史，不把首决、审稿人期限或出版制作时间当作接收时长。用户排除 MDPI 后，这两刊均可保留为主题候选，但本证据不能证明其中任何一本是全球最快或承诺本稿的接收期限。',
    '',
    '对象稿件按城市自然恢复公园中生物多样性保全与游憩协调、管理者问卷、组织实施与协作、探索性 SEM 判断。Urban Ecosystems 应突出城市社会—生态管理贡献；Environmental Conservation 应突出明确保全目标和可迁移的管理启示。',
    '',
    '## 结果与边界',
    '',
    '|期刊|官网全刊指标|本次已接收文章样本|样本中位数|样本范围|',
    '|---|---|---|---:|---:|',
    '|[Urban Ecosystems](https://link.springer.com/journal/11252)|Submission to first decision (median) 7 天；未取得全刊投稿至接收统计|官方最新列表前 5 篇 Research，209、97、75、901、105 天|105 天|75–901 天|',
    '|[Environmental Conservation](https://www.cambridge.org/core/journals/environmental-conservation)|作者指南的 30 天是审稿人审稿期限；未取得全刊投稿至接收统计|FirstView 前 5 篇原始研究/Report 中 3 篇成功核得历史，165、186、338 天，另 2 篇缺失|186 天，n=3|165–338 天|',
    '',
    '**样本数很小，且仅包含已接收、已发表的文章。文章题材、稿件质量、修回轮次与作者修回时间各异；样本中位数不是全刊统计，也不是现稿等待时间预测。不能把 Urban Ecosystems 的 7 天首决解释成 7 天外审或接收。**',
    '',
    '## Urban Ecosystems 的固定顺序样本',
    '',
    f"官方最新文章入口：{ue_raw['list_url']}。原始抓取文件记载日期为 {ue_raw['checked_date']}；本次重新核算日差。前 5 条均标记 Research，全部纳入，没有按速度挑选。",
    '',
    '|列表顺序|文章 / 官网|Received|Accepted|自然日差|',
    '|---:|---|---|---|---:|',
]
for i, r in enumerate(ue, 1):
    title = r['title'].split(' | Urban Ecosystems')[0]
    lines.append(f"|{i}|[{title}]({r['url']})<br>DOI: {r['doi']}|{r['received_iso']}|{r['accepted_iso']}|{r['days']}|")
lines += [
    '',
    '第 4 篇官网确实显示 Received: 04 April 2024、Accepted: 22 September 2026，计算为 901 天。不得将其当作输入错误擅自删除，也不能用样本中位数掩盖该长尾。',
    '',
    '## Environmental Conservation 的固定顺序样本和缺失',
    '',
    f"官方 FirstView 最新文章入口：{access['list_url']}。取列表前 5 篇原始研究/Report，即原列表第 1、2、3、4、8 条；第 5、6 条 Comment 和第 7 条 Corrigendum 排除。Research Paper 与原始实证 Report 均纳入。未因时长或主题换样。",
    '',
    '|原列表位置|文章 / 官网|类型|Received|Accepted|自然日差 / 状态|',
    '|---:|---|---|---|---|---|',
]
for r in enc:
    lines.append(f"|{r['list_order']}|[{r['title']}]({r['url']})<br>DOI: {r['doi']}|{r.get('article_type', 'Report' if r['list_order']==1 else 'Research Paper')}|{r.get('received_iso', '未取得')}|{r.get('accepted_iso', '未取得')}|{str(r['days'])+' 天' if 'days' in r else 'PDF 地址返回 HTML；保留缺失，不换样'}|")
lines += [
    '',
    '3 篇日期来自官方 PDF 首页，先 OCR 后逐图人工核对。第 1、8 条文章 HTML 可访问，但 PDF 链接虽然 HTTP 200，实际 content-type 为 text/html；没有获取到 Received/Accepted。缺失可能使 n=3 的结果受选择影响，应比 5 篇完整样本更加谨慎。',
    '',
    'Environmental Conservation 作者说明：https://www.cambridge.org/core/journals/environmental-conservation/information/author-instructions 。原句为 “Selected manuscripts are sent out to external reviewers, who agree to undertake the review within 30 days.” 仅说明审稿人同意在 30 天内完成审稿。',
    '',
    '## 可复核证据',
    '',
    '- 结构化补充：`non_mdpi_urban_ecosystems_enc_20261109.json`。所有日期均用 Python datetime 独立按自然日相减。',
    '- Urban Ecosystems：`ue_latest_articles_list.html/.txt`、`urban_ecosystems_histories_all.json`、`ue_article_*.html/.txt`。',
    '- Environmental Conservation：`root_https_www_cambridge_org_core_journals_environmental_conservation_firstview.html/.txt`、`enc_firstview_sample_access.json`、`enc_firstview_2.pdf`、`enc_firstview_3.pdf`、`enc_firstview_4.pdf`。',
    '- PDF 日期截图：`enc_pdf2_ocr/history_lower.png`、`enc_pdf3_ocr/history_lower.png`、`enc_pdf4_ocr/history_lower.png`；原始整页和 OCR 位于相同目录。',
]
(base / 'non_mdpi_urban_ecosystems_enc_20261109.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print(json.dumps({k: v['stats'] for k, v in result.items() if isinstance(v, dict)}, ensure_ascii=False, indent=2))
