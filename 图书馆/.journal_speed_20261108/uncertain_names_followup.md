# 两个精确名称追加核查（2026-11-08）

针对 `Urban Biodiversity and Ecosystem Services` 与 `Ecology & Ecosystem Services`，本次仍未取得与其一一对应的官方独立期刊主页及ISSN证据。不能断言不存在，也不能断言是某刊栏目。

已实际检查的公开官方来源：

- MDPI中国官网[完整期刊列表API](https://mdpi.cn/api/journals)返回HTTP200，JSON保存为 `root_https_mdpi_cn_api_journals.html`（内容实际为JSON）。按完整name字段检索，不含上述两个精确名称；含Urban Science。该API提供的是期刊列表，**不能用其查无名称来排除栏目或其他出版社的期刊**。
- MDPI英文[Urban Science sections](https://www.mdpi.com/journal/urbansci/sections)、[Land sections](https://www.mdpi.com/journal/land/sections)及按第一名称构造的Urban Science栏目候选路径均403；未读到栏目内容，因此无从确认是否栏目。
- Frontiers按两名称构造的公开栏目路径：[Sustainable Cities候选栏目](https://www.frontiersin.org/journals/sustainable-cities/sections/urban-biodiversity-and-ecosystem-services/about)、[Environmental Science候选栏目](https://www.frontiersin.org/journals/environmental-science/sections/ecology-and-ecosystem-services/about)、[Ecology and Evolution候选栏目](https://www.frontiersin.org/journals/ecology-and-evolution/sections/ecology-and-ecosystem-services/about)均404。**猜测路径404不能证明名称不存在**，仅说明这些路径没有确认到页面。
- Springer Nature Link官方全文检索两名称，结果为相关文章、书章或其他期刊，没有获得与精确名称对应的独立期刊。Elsevier官方Finder由另一子任务查无精确独立刊名。
- Discover Cities的[官方scope](https://link.springer.com/journal/44327/aims-and-scope)已完整读取，不含以上两个完整名称。其确实包含另外三个用户名称Urban Planning, Design and Transport、Urban Agriculture and Forestry、Urban Health and Well-being，作为Topics类别；不能把这项发现类推到尚未确认的两名称。

外部Bing仅作线索但返回重定向空壳或不相关结果，Google返回脚本中转页，没有被当成事实证据。追加请求日志见 `name_followup_b.json`。

总表建议措辞：**“精确刊名与ISSN未确认，暂不作为独立期刊排序；可能为领域、专题或栏目，但本次未核实。”**

对最终速度排序的复核意见：目前材料不能识别“与现稿契合且投稿到接收最快”的唯一最优刊或完整最终名单。首决数字可以带口径列出；不能将Elsevier数字、Springer首次决定中位数、MDPI首次决定中位数和文章历史样本混为同一全刊速度排名。Trends in Sciences官网50天投稿到接收未标统计窗口和统计量，且题材较弱；它是有条件候选，不足以认定最佳首投。Discover各刊及Environmental Management的5篇已接收文章样本可展示接收实际历时跨度，但不能据样本中位数细小差异推出全刊谁更快。
