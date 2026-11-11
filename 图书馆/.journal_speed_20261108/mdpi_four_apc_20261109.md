# MDPI四刊费用核验（2026-11-09）

四刊英文官网APC正文均返回HTTP403，**尚不能声称已经确认2026-11-09当日官方标价**。父任务另取得四刊OpenAlex来源记录，已逐一检查`apc_prices`内金额和币种；前两刊亦有DOAJ记录交叉支持。以下可作有来源的费用预算，不能伪称当日官网价格。

|期刊|当日官方APC正文|备用记录金额|记录最后更新|按埼玉大学10%条件折扣估算|
|---|---|---:|---|---:|
|Land|[官方收费页](https://www.mdpi.com/journal/land/apc)，403|2600 CHF，OpenAlex+DOAJ|OpenAlex2026-11-08；DOAJ2026-09-17|2340 CHF|
|Urban Science|[官方收费页](https://www.mdpi.com/journal/urbansci/apc)，403|1600 CHF，OpenAlex+DOAJ|OpenAlex2026-11-08；DOAJ2026-09-17|1440 CHF|
|Environments|[官方收费页](https://www.mdpi.com/journal/environments/apc)，403|1800 CHF，OpenAlex|2026-11-08|1620 CHF|
|Sustainability|[官方收费页](https://www.mdpi.com/journal/sustainability/apc)，403|2400 CHF，OpenAlex|2026-11-08|2160 CHF|

OpenAlex备用来源（第三方元数据，不是出版社官网正文）：

- [Land来源API](https://api.openalex.org/sources/S2738397068)：`apc_prices=[{"price":2600,"currency":"CHF"}]`。
- [Urban Science来源API](https://api.openalex.org/sources/S4210174142)：`apc_prices=[{"price":1600,"currency":"CHF"}]`。
- [Environments来源API](https://api.openalex.org/sources/S4210187256)：`apc_prices=[{"price":1800,"currency":"CHF"}]`。
- [Sustainability来源API](https://api.openalex.org/sources/S10134376)：`apc_prices=[{"price":2400,"currency":"CHF"}]`。
- 四记录均`updated_date=2026-11-08T13:48:25`。这只是元数据整体更新日，**不是价格生效日，也不证明APC值在该日经出版社复核**。原始文件由父任务保存为`root_apc_openalex_<slug>_20261109.json`；本任务已只读核对。

DOAJ来源（目录记录，非出版社当日正文）：

- [Land DOAJ API记录](https://doaj.org/api/search/journals/issn:2073-445X)：`bibjson.apc.max=[{"price":2600,"currency":"CHF"}]`；`last_updated=2026-09-17T10:42:05Z`；出版社字段MDPI AG，收费链接指向Land官方APC页。原始保存`apc_doaj_land.html`。
- [Urban Science DOAJ API记录](https://doaj.org/api/search/journals/issn:2413-8851)：`bibjson.apc.max=[{"price":1600,"currency":"CHF"}]`；`last_updated=2026-09-17T10:42:07Z`；出版社字段MDPI AG，收费链接指向Urban Science官方APC页。原始保存`apc_doaj_urbansci.html`。
- 两条记录提供的是APC的`max`字段，币种明确为CHF。记录更新日不是APC生效日；数据没有单独标注APC最后更新日期、价格有效期或2027年调整。
- 两条记录均`other_charges.has_other_charges=false`，但未直接核实出版社当日费用政策，不以此替代实际发票。

10%折扣的依据与条件：

- 本地《埼玉大学図書館2.pdf》明确MDPI全部期刊APC可享10%折扣，通讯作者和共作者均可利用；应使用埼玉大学邮箱（`.saitama-u.ac.jp`）以确保识别。本地OCR位置为`.journal_review_20261108/pdf02_saitama/ocr.txt`，原PDF未修改。
- [MDPI中国官网IOAP页面](https://mdpi.cn/ioap)当日HTTP200，明确“合作机构作者享有：文章处理费（APC）10%折扣”。原始保存`apc_ioap_cn.html`及`.txt`。该中文页展示的是中国机构列表，**本任务没有据此证明埼玉大学当前仍在名录**；埼玉资格依所给大学资料。
- 因此2340 CHF、1440 CHF、1620 CHF、2160 CHF只是用有来源的元数据标价乘0.9的条件性预算值，未核汇率、付款手续费、额外服务，也没有将优惠假设为可任意叠加。

币种与促销：

- [MDPI官方2023-02-03支付说明](https://mdpi.cn/announcements/747)HTTP200，明确“Online Payment by Credit Card in Swiss Francs (CHF)”以及支付宝目前只支持CHF；它说明付款币种，不是四刊当日标价来源。原始保存`apc_mdpi_news747.html`、`.txt`。
- [MDPI官方2026-08-18 Land/IFLA合作新闻](https://mdpi.cn/announcements/3520)HTTP200，说明IFLA会员可享APC折扣，但未公布比例。本任务没有用户为IFLA会员的证据，故未计入或叠加。原始保存`apc_mdpi_IFLA.html`、`.txt`。
- 中国官网`https://mdpi.cn/api/journals`只有名称、指标、首次决定等字段，**没有APC金额或币种字段**；不能用它计算费用。
- 搜索引擎查询未取得可用官方收费摘要：Google返回启用Javascript提示；Bing的精确收费页、金额关键词、URL查询返回与请求不相干的普通结果，不能据其填金额；DuckDuckGo、Baidu、Yandex显示验证码；Google翻译两个公开APC页均连接超时。MDPI Japan FAQ及publishing页可读取，但没有四刊收费数字；试查公开价目表路径未成功，不能凭记忆填充。

未解决项：四刊当前官方价格与生效日期，以及最新是否有适用于本稿的特刊/其他优惠。未发送邮件或联系编辑。
