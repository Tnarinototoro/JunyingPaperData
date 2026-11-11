# Ecological Management & Restoration 核验

核验日期：2026-11-09。结论：**Wiley／澳大利亚生态学会期刊，仍在出版；当前日本公园问卷稿仅部分匹配，不建议作为速度优先选项。**

## 存续、出版社与范围

Ecological Society of Australia（ESA）现行官网 Journals 页仍将本刊列为其管理导向期刊并链接 Wiley，官方关联 EMR Project Summaries 网站也显示 2026 年 10 月当期论文链接。Wiley 提交的 Crossref 记录包括 2026-10-21、2026-10-11 等新发表论文，原标题和 `10.1111/emr.*` DOI 持续使用；未查到停刊、并刊或更名证据。Crossref 中还出现 2027 卷期记录，但它不是已发表研究论文，未用于审稿样本。

- ESA：https://www.ecolsoc.org.au/publications/journals/ （HTTP 200；`emr_esa_journals_retry.html/.txt`）
- Wiley 本刊：https://onlinelibrary.wiley.com/journal/14428903 （本环境 HTTP 403）
- 当前记录：https://api.crossref.org/journals/1442-8903/works?sort=published&order=desc&rows=10 （HTTP 200；`emr_crossref_recent.html`）
- ESA 当前页直接链接的期刊项目站：https://emrprojects.wordpress.com/ （HTTP 200；`emr_projects_home.html/.txt`）

ESA 对本刊的原句：

> EMR combines a highly readable style with scientifically credible material. It answers the growing need among land managers for reliable, relevant information and acknowledges the need for two-way communication in devising new hypotheses, sound experimentation, effective treatments and reliable monitoring.

项目站首页包含全刊范围说明：

> Ecological Management & Restoration is a peer-reviewed journal dedicated to promoting improved ecosystem management and restoration within the context of ecologically sustainable utilisation.

> The Editorial Board seeks original contributions from both scientists and practitioners that focus on the management and restoration of plant and animal communities. Cross-disciplinary contributions that are highly relevant to improved management of ecosystems will also be considered. **While the Journal focuses on Australasia, contributions from elsewhere will be considered if distinctly relevant to Australasia.**

因此，日本研究并非绝对禁止，但需要证明对澳新生态管理／恢复的明确相关性，不能仅以一般全球意义替代。当前稿为日本 39 公园、34 管理团体问卷，分析保护—游憩协调、实施条件与协作，探索性 SEM 辅以 NDVI，未测量实际生态恢复／保护效果。其治理与管理主题有交集，但“澳新明确相关性”和生态管理实践贡献是主要适配门槛；若不补足，不宜列入最合适且最快的首选。

注意：ESA 所说 Australia 项目、800–1100 词、已有良好／有希望结果且**不同行评议**，特指 **EMR Summaries**，不是整本期刊的通用稿型或审稿快速通道。不能用该类短摘要支持用户原创论文接收快。

## 投稿至接收：五篇可辨识研究样本

没有取得全刊官方“投稿至接收”总体统计。Wiley 原站、文章全文／XML 和 reader 路由返回安全验证页；下表的准确日期来自 **Wiley 向 Crossref 提交的 `publication_history` assertion**，并非成功读取原刊全文，不是首次决定数据。

选取方法：从按发表日期倒序的最近 10 条 Crossref 记录，排除卷期、Issue Information；按原有顺序，取出版商摘要明确描述实证生态研究的前五篇。70072 没有出版商摘要，精确类型未能确认，故跳过；70062 的完整摘要明确报告两项空洞树干迁移案例及繁殖观测，应计入；第六篇明确研究 70068 及无摘要条目仍保留在完整七条双日期文件中。选择依据是固定发表顺序及研究内容可辨识性，不按快慢筛选。原刊具体 article subtype 未经全文独立确认。

| 完整论文标题 | 收稿 | 接收 | 天数 | 日期来源 |
|---|---|---|---:|---|
| Landscape Context Influences the Use of Nest Boxes by a Black-Cockatoo | 2025-12-19 | 2026-09-20 | 275 | https://api.crossref.org/works/10.1111/emr.70071 |
| Spatial and Temporal Vegetation and Peat Depth Patterns in Alpine, Subalpine and Montane Peatlands of South-Eastern Australia | 2025-12-29 | 2026-09-20 | 265 | https://api.crossref.org/works/10.1111/emr.70070 |
| Relocating Large Hollow-Bearing Tree Trunk Sections to Restore Forest Owl Breeding Habitat: When Is It Warranted? | 2025-07-18 | 2026-07-17 | 364 | https://api.crossref.org/works/10.1111/emr.70062 |
| Food for the Future: Identifying and Prioritising Feeding Habitat for South-Eastern Glossy Black-Cockatoos to Guide Strategic Ecological Restoration in North-Eastern NSW | 2026-02-05 | 2026-09-18 | 225 | https://api.crossref.org/works/10.1111/emr.70069 |
| Developing Habitat Descriptors for a Threatened Cryptic Worm-Lizard to Determine Potential Habitat Under the NSW Biodiversity Offset Scheme in Australia | 2025-04-16 | 2026-09-06 | 508 | https://api.crossref.org/works/10.1111/emr.70067 |

**五篇样本中位数 275 天，范围 225–508 天。** 这是小样本历史差值，含作者修回时间，不是本刊官方总体中位数或接收承诺。`emr_selected_five_history.json` 保存完整标题、摘要、原始 assertion、日期和链接；`emr_crossref_history_samples.json` 保留全部七篇。

## 费用与订阅路径

本次团队于 **2026-11-09 从 Wiley 官网在线重新下载报价表成功（HTTP 200）**：https://authors.wiley.com/asset/Wiley-Journal-APCs-OnlineOpen.xlsx ，存档 `restoration_authors_retry.xlsx`、访问记录 `restoration_online_apc_fetch.json`，与用户所给 `Wiley-Journal-APCs-OnlineOpen.xlsx` 哈希相同。表内首表名为 **Hybrid OA Journals**、更新日期 **12 October 2026**。第 346 行本刊 eISSN **1442-8903**，完整 OA APC 列值为：**USD 2,760／GBP 1,840／EUR 2,300**。币种根据第 7 行表头确认，不能把数额写成 CHF。Wiley 通用 APC 条款按付款方账单地址决定币种：英国 GBP、欧元区 EUR、其他国家 USD，因此日本账单地址对应 **USD 2,760**，另加依法适用税。

该表将其列为 hybrid；Wiley 当前通用 APC 原句：`For hybrid open access journals, the responsible corresponding author can select open access or subscription for their article after it enters the production cycle.` 因此可选择传统订阅发表路径，不支付可选 OA APC。**本次未取得本刊现行完整收费条款，不能保证没有页费、彩图等其他费用，也不将“无 OA APC”写成“所有费用为零”。** ESA 页上“no page charges”只说 Austral Ecology，不能移用于 EMR。

表格证据与超链接已摘录：`emr_local_wiley_price_row.json`。Wiley 通用 APC 条款正文存档 `restoration_apc_final.txt`（https://authors.wiley.com/author-resources/Journal-Authors/open-access/article-publication-charges.html）：`The prices listed above do not include any value-added tax (VAT), goods and services tax (GST), or other sales taxes, which may be charged where required by law.`；付款／许可／机构确认在接收后进行。没有推断本刊发票具体期限。

## 埼玉大学协议的条件

用户学校资料 `.journal_review_20261108/pdf01_saitama/ocr.txt` 第 138–155 行明确：Wiley 协议 **2023-01-01 至 2026-12-31，按接收日，以后未定**；需埼玉大学所属通讯作者，出版社指定 hybrid 期刊，原创论文／综述，录用后申请。校内还设作者负担制度，具体依校内指南。不能把 OA 全额永久免费写为已保证，更不能对 2027 年接收承诺覆盖。

本刊在当前用户提供 hybrid APC 表中，不足以单独证明它必然进入学校协议的指定期刊及剩余额度。需要符合接收年度、对应作者身份、合格类型、指定刊表、学校审批及额度后才可确认；当前速度样本提示接收到 2027 年的可能性，应按尚未确认后续协议处理。

## 核查局限

Wiley 本刊 scope、GFA、metrics、全文与 XML 直接访问受阻，reader 也未成功；范围采用 ESA 当前官方站直接链接的 EMR 项目站原文，费用采用本次官网成功下载的官方表及通用 APC 条款，日期采用出版商提交的 Crossref assertion。没有引用 search snippet、首次决定、非同行评议摘要或 2027 预排卷期计算接收速度。
