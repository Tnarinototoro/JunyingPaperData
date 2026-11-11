# Conservation 与四刊出版社／费用核验

核验日期：2026-11-09。仅核验准确刊名，不把不同刊名合并。

**Conservation 确实由 MDPI 出版，eISSN 为 2673-7159。当前取得的官方 APC 正文转写报价是 CHF 1,200，加适用 VAT／Sales Tax。** 前面 DOAJ 和 OpenAlex 所载的 CHF 1,000 与这次取得的官方正文不一致，应优先使用官方正文的 CHF 1,200，不再将 1,000 当作当前预算。

## 官网正文：价格、税、付款时点

来源：https://www.mdpi.com/journal/conservation/apc

本环境直连原站 HTTP 403；主代理通过公开文本读取服务取得该官方页面的完整正文转写，文件为 `root_reader_conservation.txt`。**这属于经读取服务取得的官网正文，不能表述为原站直连成功。** 文本没有标出报价生效日期，因此这里只报告本次获取正文所显示的价格，不推断未来变更时间。

官网原句：

> All articles published in _Conservation_ (ISSN 2673-7159) are published in full open access. An article processing charge (APC) of **CHF 1200 (Swiss francs)** applies to papers accepted after peer review.

> In addition to Swiss francs (CHF), we also accept payment in euros (EUR), US dollars (USD), British pound sterling (GBP), Japanese yen (JPY) or Canadian dollars (CAD).

> Invoices are emailed shortly after acceptance to the payment contact provided by the authors.

> Local VAT or Sales Tax will be added if applicable.

因此，基础 APC 是 **1,200 瑞士法郎**；接受后不久向作者所指定的付款联系人发送发票；可使用官网列明的其他币种支付，但本次没有核实该币种发票的具体汇率或金额。本文没有把收费阶段误写为投稿时收费，也没有预设日本一定加税或免税。

## 出版社与准确刊名

| 准确刊名 | 出版社 | 官网 |
|---|---|---|
| Conservation | MDPI | https://www.mdpi.com/journal/conservation |
| Land | MDPI | https://www.mdpi.com/journal/land |
| Urban Science | MDPI | https://www.mdpi.com/journal/urbansci |
| Environments | MDPI | https://www.mdpi.com/journal/environments |
| Sustainability | MDPI | https://www.mdpi.com/journal/sustainability |
| Journal for Nature Conservation | Elsevier；不同期刊，ISSN 1617-1381 | https://www.sciencedirect.com/journal/journal-for-nature-conservation |

前五刊全部出现在 MDPI 中国官网当前期刊目录 API：
https://mdpi.cn/api/journals （HTTP 200；原始数据 `mdpi_api_journals.html`，精选五刊 `mdpi_official_journals_selected.json`）。

Conservation 另有今日从 MDPI 官方资源域名重新下载的文章 XML 作为直接证据：
https://mdpi-res.com/d_attachment/conservation/conservation-06-00134/article_deploy/conservation-06-00134.xml

其 `journal-meta` 原文为：

```xml
<journal-title>Conservation</journal-title>
<issn pub-type="epub">2673-7159</issn>
<publisher><publisher-name>MDPI</publisher-name></publisher>
```

`Journal for Nature Conservation` 的 Crossref 期刊记录返回 `publisher: Elsevier`、`ISSN: 1617-1381`：https://api.crossref.org/journals/1617-1381 。这是对两种准确刊名的区分，不能推断用户实际上指的是哪一本。

## 埼玉大学折扣：有资格时的预算

用户提供的埼玉大学资料 `.journal_review_20261108/pdf02_saitama/ocr.txt` 第 38–45 行写明：本校参加 MDPI IOAP，**MDPI 全期刊 APC 10% 折扣，通讯作者和共同作者均可使用，须用埼玉大学邮箱确保识别**。本次 MDPI 中国官网 IOAP 页也明确“合作机构作者享有：文章处理费（APC）10% 折扣”：https://mdpi.cn/ioap ，HTTP 200。

所以，如果作者确属该校且投稿时识别并应用了该协议，Conservation 的基础预算可按 **1,200 × 90% = CHF 1,080，再加适用税**估算。不能把 1,080 写成无条件最终发票金额，也不预设与其他优惠叠加。

## 旧元数据冲突记录

- DOAJ：https://doaj.org/api/search/journals/issn:2673-7159 ，`publisher=MDPI AG`，`apc.max=1000 CHF`，记录 `last_updated=2026-09-17T10:40:26Z`。
- OpenAlex：https://api.openalex.org/sources/issn:2673-7159 ，`apc_prices=1000 CHF`，记录 `updated_date=2026-11-08T13:48:25`。
- 两处是目录元数据；更新时间不是收费生效日期。因已取得官方正文的 **CHF 1,200**，费用结论采用后者。

本报告没有重新核实 Land、Urban Science、Environments、Sustainability 的当前官方 APC，前五刊的出版社结论与 Conservation 的当前收费结论应分别理解。
