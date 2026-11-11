# Journal for Nature Conservation：本次费用核验

访问日期：2026年11月9日15:24（Asia/Shanghai）。本次重新调用官方公开接口，未仅复用旧值。

- 精确刊名：Journal for Nature Conservation；ISSN 1617-1381；出版社Elsevier，和MDPI的Conservation是两本期刊。
- 官方Elsevier Journal Finder返回 `openAccessType: "HYBRID"`。
- `goldOpenAccessFee: {"value":3160,"currency":"USD","discountedValue":null,"discountExpiryDate":null}`。
- 因而，选择开放获取（OA）的标准APC为 **3160美元**。官网一般费用说明写明APC价格不含税；机构协议、折扣和最终报价需另核。
- 官方数据的 `hasAgreements:false` 只是本次未带机构身份查询的结果，不能据此断定埼玉大学无协议或作者不能获得资助。

官方入口：[Journal Finder结果页](https://journalfinder.elsevier.com/results?query=Journal%20for%20Nature%20Conservation&mode=search)。公开请求接口：`POST https://journalfinder.elsevier.com/api/journals/search`，payload和响应摘录见elsevier_jnc_fee_evidence.json，完整原始响应见elsevier_jnc_fee_api_raw.json。

传统订阅发表与OA须区分。Elsevier官方[Journal pricing](https://www.elsevier.com/about/policies-and-standards/pricing)说明：

> Subscription articles funded by payments for reading made by subscribing individuals or institutions

> Open access articles funded by payments for publishing made by authors, their institution or funding bodies, commonly known as Article Publishing Charges (APCs)

其当前[Open access说明](https://www.elsevier.com/open-access)还说明：

> Where articles are not supported by the pay-to-publish model, they are typically supported by subscription fees paid for by readers.

> Finally, we provide high quality subscription publishing options, so authors should never face a cost barrier to publishing in their journal of choice.

这些支持“3160美元是选择OA的APC，不应说不选OA也必须付此款”。本次该刊特定[Guide for Authors](https://www.sciencedirect.com/journal/journal-for-nature-conservation/publish/guide-for-authors)和[Open access options](https://www.sciencedirect.com/journal/journal-for-nature-conservation/publish/open-access-options)均403，未直接读取该刊关于订阅模式无出版费、彩印费等额外费用的完整条款，故不将“所有可能费用均为0”作为已核事实。

可直接答用户：“如果你指的是刚才的Journal for Nature Conservation，它属于Elsevier，不是MDPI；它是混合开放获取期刊，选择OA时标准APC为3160美元，传统订阅路线不需支付这笔OA APC。如果刊名只有Conservation，那是另一本MDPI期刊。”
