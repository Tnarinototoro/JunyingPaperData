# Restoration Ecology 核验（2026-11-09）

结论：非 MDPI；Wiley / Society for Ecological Restoration（SER）期刊。官网明确包含生态修复的政策、治理和实践研究，因此不能因稿件缺少生态实测就直接排除。但目前稿件的核心是日本公园的保全—利用协调及管理实施条件，只有把研究问题、变量和结论具体联系到生态修复的实施过程、治理障碍或修复决策时，才有较清楚的投稿理由。不能仅将“公园保全”改称“生态修复”，也不宜把管理者评价或 NDVI 当作已经测量到的生态修复效果。按当前稿件，属于有条件适配，速度优先时不宜直接列为首选。

## 官方范围与出版方

Wiley 官方产品页（200，可读）：
https://www.wiley.com/en-us/Restoration+Ecology-p-1526100X

原文：“publishing original papers on the full range of experimental, theoretical, technical, practical, policy, governance, and strategic research and applications across all terrestrial and aquatic ecosystems and taxa.”

并写：“an internationally recognized journal of the Society for Ecological Restoration, publishing research contributing to restoring damaged ecosystems.”

以上明确支持政策、治理与管理实践研究；核心约束是对恢复受损生态系统有贡献。资料存档 `restoration_wiley_product.html/.txt`。

Wiley Online Library 的主页、范围、作者须知、OA 和 metrics 页面以及 SER 页面均遇到 403。不能声称已读到这些页面中的全部条款，也未核得全刊官网“投稿→最终接收”统计。

## 收稿至最终接收：近期论文小样本

来源为 Wiley 向 Crossref 提交的 `assertion.group.name=publication_history` 中 `received` 与 `accepted` 字段，非编辑部公布的全刊中位数。按截至 2026-11-09 Crossref 最新发表顺序，先排除最新一篇以全球示例和制度改革论证为主、确切 Wiley 文章栏目无法核实的 rec.70598，然后连续取下列 5 篇。其摘要包含现场观测、实验或经验案例数据；属于经验研究内容，但 Wiley 页面被 403 拦截，正式细分栏目名称尚未核实。

| DOI / 官网论文入口 | 收稿 | 接收 | 日数 |
|---|---|---|---:|
| [10.1111/rec.70589](https://onlinelibrary.wiley.com/doi/10.1111/rec.70589) | 2026-04-05 | 2026-10-13 | 191 |
| [10.1111/rec.70599](https://onlinelibrary.wiley.com/doi/10.1111/rec.70599) | 2026-07-10 | 2026-10-26 | 108 |
| [10.1111/rec.70595](https://onlinelibrary.wiley.com/doi/10.1111/rec.70595) | 2026-07-02 | 2026-10-22 | 112 |
| [10.1111/rec.70596](https://onlinelibrary.wiley.com/doi/10.1111/rec.70596) | 2026-01-22 | 2026-10-23 | 274 |
| [10.1111/rec.70590](https://onlinelibrary.wiley.com/doi/10.1111/rec.70590) | 2026-08-05 | 2026-10-15 | 71 |

样本中位数 **112 天**，范围 **71–274 天**，n=5，包含作者返修时间，仅为已接收论文的小样本，不能预测本稿接收时长。未删除 274 天的较慢样本。最新排除文 rec.70598 是 168 天；排除基于研究类型而非速度。最新 15 篇原始元数据和完整摘要在 `restoration_crossref.json`；选样与日期计算在 `restoration_publication_histories_20261109.json`。

Crossref API：
https://api.crossref.org/journals/1526-100X/works?sort=published&order=desc&rows=15&filter=until-pub-date:2026-11-09

## APC 与订阅选项

官网当日重新下载的 Wiley Hybrid OA 价格表（200）：
https://authors.wiley.com/asset/Wiley-Journal-APCs-OnlineOpen.xlsx

表内更新日期 **2026-10-12**。Hybrid OA Journals 表，第 1059 行列明 Restoration Ecology（ISSN 1526100X）：**USD 3,460 / GBP 2,310 / EUR 2,880**。表头 E=USD、F=GBP、G=EUR；这些是可选开放获取的全额 APC，不是三种费用相加。币种随付款人账单地址确定，官网说明价格不含适用税费。日本付款通常对应美元，但最终以生产系统报价为准。

下载存档：`restoration_authors_retry.xlsx`；SHA256 `5a17b1c6c0b2a1373d3044e98410518f031d391841960b8f82062588a383aa99`，与用户提供的同名表一致。HTTP 证据在 `restoration_online_apc_fetch.json`。因此这次价格已完成官网在线核验，不能只写“本地旧表价格”。

Wiley 当前官方 APC 页面（200）：
https://authors.wiley.com/author-resources/Journal-Authors/open-access/article-publication-charges/index.html

原文：“For hybrid open access journals, the responsible corresponding author can select open access or subscription for their article after it enters the production cycle.”

Hybrid 页面（200）：
https://authors.wiley.com/author-resources/Journal-Authors/open-access/hybrid-open-access/index.html

明确 APC 是选择开放获取时支付的费用。**可选择订阅发表以免 OA APC**。但本次作者须知 403，未能核实该刊是否另有强制页费、彩图费、超长费或 SER 会员与非会员差别，故不承诺“发表所有费用为 0”。

## 埼玉大学协议

用户提供的大学资料 `pdf01_saitama/ocr.txt` Wiley 段：2023-01-01 至 **2026-12-31（以后未定）**，按**接收日期**；埼玉大学所属通讯作者；出版社指定 hybrid OA 期刊；原著及综述。具体作者负担须见校内限定的“転換契約による OA 出版枠利用案内”。官方在线价格表证实本刊是 hybrid，但这不等于已获学校支付批准或尚有可用名额。

现为 2026-11-09；若接收跨至 2027，现有资料不能保证协议延续。不能用 2023 年新闻稿或“出现在全年名单”推定本稿免费。用户提供 Wiley 作者指南第 35–36 页支持机构不支付时可改用非 OA / CTA 路线以免 OA APC；仍不等于该刊全部杂费已核为零。

## 推荐表可用简写

“Restoration Ecology：有条件可投，需围绕实际生态修复治理/实施贡献；Wiley/SER，非 MDPI。官网全刊接收指标未核得；出版商 Crossref 近期 5 篇经验研究样本中位 112 天，71–274 天。Hybrid 可订阅发表免 OA APC；可选 OA 标价 US$3,460（2026-10-12 表，当日官网下载）。其他页费/会员费差别未核实。埼玉协议按接收日仅证实至 2026-12-31，是否支付及名额不保证。”
