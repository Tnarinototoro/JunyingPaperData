# Elsevier 官方在线核验与费用表核读：2026-11-08

25本用户指定Elsevier期刊及5本补充期刊的官方scope全部获取并核读。使用Elsevier正常公开Journal Finder搜索接口，所有30本返回HTTP200，原始JSON已保存。ScienceDirect各刊insights正文受HTTP403阻挡。

## 时间口径

官方搜索入口：https://journalfinder.elsevier.com/ 。页面正常调用POST https://journalfinder.elsevier.com/api/journals/search。
- `timeToFirstDecision`在官方卡片标为 **Submission to first decision**，单位day；筛选提示为“Time from manuscript submission to the initial decision on the article, in days.”。可能包含编辑拒稿，不能解释为首轮外审意见。接口未说明统计周期或均值/中位数。
- **不能将此接口的`timeToAcceptance`当成投稿至接收。** 当前官方结果卡片将同一值标为 **Acceptance to publication**；筛选tooltip却写“Time from 1st decision to acceptance of manuscript, in days.”，存在内部标签冲突。已保存`jf_0qn8gwwr_-4q_.js`与`jf_09k3slfwkioev.js`为证。所有这些值都不进入投稿到接收栏，也不据此排序。
- 例如JORT first decision=15，原始timeToAcceptance=12；后者官方卡片标为Acceptance to publication，绝非投稿12天接收。JEM为4及6，SCS为2及2，同理。
- 全部30本的外审后决定时间、投稿到接收总体时长均未成功核实；不能据此认定任何一本同时主题一致且接收最快。

## 逐刊结果

|官方结果页|首次决定（天）|外审后决定|投稿至接收|现稿判断|所给Elsevier表资格|
|---|---:|---|---|---|---|
|[Sustainable Cities and Society](https://journalfinder.elsevier.com/results?query=Sustainable%20Cities%20and%20Society&mode=search)|2|未核|未核|**有条件；非速度优先首选**。范围包括green infrastructure、urban forestry、行为与城市治理；需城市可持续性机制、国际意义和更充分方法证据。|第1675行：Core Hybrid / QUOTA|
|[Journal of Environmental Management](https://journalfinder.elsevier.com/results?query=Journal%20of%20Environmental%20Management&mode=search)|4|未核|未核|**适合，主题主候选**。包括生态系统、自然资源管理和环境管理社会科学；官网警惕高度局地化且使用常规方法的案例，须证明国际管理意义。|第952行：Core Hybrid / QUOTA|
|[Land Use Policy](https://journalfinder.elsevier.com/results?query=Land%20Use%20Policy&mode=search)|10|未核|未核|**有条件；需重定位**。核心是土地利用的制度、规划与政策；须形成土地/绿地管理权责、制度或政策工具的贡献。|第1180行：Core Hybrid / QUOTA|
|[Journal of Outdoor Recreation and Tourism](https://journalfinder.elsevier.com/results?query=Journal%20of%20Outdoor%20Recreation%20and%20Tourism&mode=search)|15|未核|未核|**适合，主题主候选**。官网明确从荒野到都市户外游憩，欢迎自然资源社会科学与公园管理案例；突出保全—游憩协调、利用规则及管理实践。|第1067行：Core Hybrid / QUOTA|
|[Regional Sustainability](https://journalfinder.elsevier.com/results?query=Regional%20Sustainability&mode=search)|16|未核|未核|**有条件**。包括保全、人与土地关系及公共管理，但须对区域可持续性理论/方法及环境—经济—社会联系作贡献。|该表未找到精确刊名|
|[Science of the Total Environment](https://journalfinder.elsevier.com/results?query=Science%20of%20the%20Total%20Environment&mode=search)|3|未核|未核|**现稿不适合**。官方明确排除以经济、社会、心理、政策、规划或管理为本质的社会科学稿件；辅助NDVI不能改变本稿管理问卷研究的本质。|第1591行：Core Hybrid / QUOTA|
|[Environmental Technology & Innovation](https://journalfinder.elsevier.com/results?query=Environmental%20Technology%20%26%20Innovation&mode=search)|6|未核|未核|**现稿不适合**。核心是自然科学支撑的环境技术、创新产品/方法及环境效益；本稿没有对应技术或效果验证。|第2144行：Gold / DISCOUNT|
|[Global Ecology and Conservation](https://journalfinder.elsevier.com/results?query=Global%20Ecology%20and%20Conservation&mode=search)|4|未核|未核|**现稿不优先，匹配弱**。官网一般不考虑无significant biological component稿件；管理者问卷与辅助NDVI尚未形成生态效果或保全科学新证据。|第2208行：Gold / DISCOUNT|
|[Ecological Indicators](https://journalfinder.elsevier.com/results?query=Ecological%20Indicators&mode=search)|1|未核|未核|**现稿不适合直接投**。要求指标开发、方法或指示理论创新；不能把SEM因子或NDVI附件自动当作生态指标创新。|第2110行：Gold / DISCOUNT|
|[Heliyon](https://journalfinder.elsevier.com/results?query=Heliyon&mode=search)|未提供|未核|未核|**范围可投；速度证据不足**。官网Finder覆盖自然、应用、生命与社会科学，强调科学准确性；须核对具体section和方法可靠性；无first decision数值。|第2227行：Gold / DISCOUNT|
|[Forest Ecology and Management](https://journalfinder.elsevier.com/results?query=Forest%20Ecology%20and%20Management&mode=search)|4|未核|未核|**现稿不适合直接投**。要求森林生态与管理明确联系；跨类型都市公园管理者问卷未形成森林生态知识和管理效果证据。|第641行：Core Hybrid / QUOTA|
|[Building and Environment](https://journalfinder.elsevier.com/results?query=Building%20and%20Environment&mode=search)|3|未核|未核|**现稿不适合**。核心是建筑科学、城市物理及热舒适/空气质量/建成环境性能，本稿无相关过程与性能测量。|第247行：Core Hybrid / QUOTA|
|[Biological Conservation](https://journalfinder.elsevier.com/results?query=Biological%20Conservation&mode=search)|6|未核|未核|**有条件；不作速度赌注**。官网明确欢迎保全政治、政策、社会结构等社会科学；需超越局地案例的保全科学贡献，39样本SEM可靠性将是重点。|第212行：Core Hybrid / QUOTA|
|[Environmental and Sustainability Indicators](https://journalfinder.elsevier.com/results?query=Environmental%20and%20Sustainability%20Indicators&mode=search)|3|未核|未核|**现稿不优先，需重构**。要求指标开发或方法推进；本稿主要研究管理行为关联，并非指标体系开发/验证。|第2136行：Gold / DISCOUNT|
|[Cities](https://journalfinder.elsevier.com/results?query=Cities&mode=search)|12|未核|未核|**有条件，需重构**。包括城市治理、合作、管理和greening；需形成城市政策/规划理论贡献。|第301行：Core Hybrid / QUOTA|
|[Habitat International](https://journalfinder.elsevier.com/results?query=Habitat%20International&mode=search)|6|未核|未核|**有条件但非首选**。关注人类住区规划、设计、生产与管理，偏城市化与发展；日本公园案例须有更广住区治理意义。|第690行：Core Hybrid / QUOTA|
|[Applied Geography](https://journalfinder.elsevier.com/results?query=Applied%20Geography&mode=search)|5|未核|未核|**现稿不优先**。要求地理理论/方法解决有空间维度的问题；辅助NDVI和公园位置本身不构成空间解释贡献。|第129行：Core Hybrid / QUOTA|
|[Ecosystem Services](https://journalfinder.elsevier.com/results?query=Ecosystem%20Services&mode=search)|16|未核|未核|**现稿不优先，需重构**。可以研究治理和参与，但须扎根生态系统服务/自然对人的贡献框架并提供管理、价值或权衡证据。|第505行：Core Hybrid / QUOTA|
|[Ecological Engineering](https://journalfinder.elsevier.com/results?query=Ecological%20Engineering&mode=search)|8|未核|未核|**现稿不适合直接投**。核心是生态系统设计、监测、恢复与生态工程；现稿未测恢复效果，主要是管理者问卷。|第493行：Core Hybrid / QUOTA|
|[Environmental Science & Policy](https://journalfinder.elsevier.com/results?query=Environmental%20Science%20%26%20Policy&mode=search)|5|未核|未核|**有条件，需大幅加强定位**。要求环境知识、政策与社会关系，不能只声称有政策意义；须具体分析知识如何进入决策。|第550行：Core Hybrid / QUOTA|
|[Environmental Impact Assessment Review](https://journalfinder.elsevier.com/results?query=Environmental%20Impact%20Assessment%20Review&mode=search)|2|未核|未核|**现稿不适合直接投**。核心是影响评价理论、程序、制度和创新方法；本稿没有EIA/SEA/SIA等影响评价设计。|第544行：Core Hybrid / QUOTA|
|[Resources, Conservation & Recycling](https://journalfinder.elsevier.com/results?query=Resources%2C%20Conservation%20%26%20Recycling&mode=search)|7|未核|未核|**现稿不适合**。主要是物质流、资源效率、循环利用、生产消费转型；生物多样性保全不能等同于资源循环。|第1547行：Core Hybrid / QUOTA|
|[Journal of Cleaner Production](https://journalfinder.elsevier.com/results?query=Journal%20of%20Cleaner%20Production&mode=search)|6|未核|未核|**现稿不优先**。虽含可持续治理，核心仍为清洁生产、资源效率、生产消费系统；本稿公园保全管理距离较远。|第889行：Core Hybrid / QUOTA|
|[Ecotoxicology and Environmental Safety](https://journalfinder.elsevier.com/results?query=Ecotoxicology%20and%20Environmental%20Safety&mode=search)|5|未核|未核|**现稿不适合**。污染物暴露、毒理/生态毒理机制与安全；现稿没有污染、暴露或毒理数据。|第2112行：Gold / DISCOUNT|
|[Environmental Research](https://journalfinder.elsevier.com/results?query=Environmental%20Research&mode=search)|2|未核|未核|**现稿不适合**。主要污染、化学、毒理、环境材料、过程与健康；绿地稿需健康/福祉结局，现稿无此结局。|第549行：Core Hybrid / QUOTA|
|[Journal for Nature Conservation](https://journalfinder.elsevier.com/results?query=Journal%20for%20Nature%20Conservation&mode=search)|14|未核|未核|**适合，新增主题主候选**。鼓励保全科学与实践结合及生物多样性和社会经济概念整合；须连到可立即使用的保全决策。|第830行：Core Hybrid / QUOTA|
|[City and Environment Interactions](https://journalfinder.elsevier.com/results?query=City%20and%20Environment%20Interactions&mode=search)|5|未核|未核|**有条件，新增候选**。欢迎都市环境自然与社会科学、政策和利益主体界面；重点仍为城市气候/环境压力，需交代对应决策问题。|第2014行：Gold / DISCOUNT|
|[Environmental Challenges](https://journalfinder.elsevier.com/results?query=Environmental%20Challenges&mode=search)|5|未核|未核|**现稿不优先，谨慎**。最新scope强调经过测试/评估/实施的响应及环境结果指标，明确可能不收surveys without environmental outcome metrics；本稿缺环境效果测量。|第2137行：Gold / DISCOUNT|
|[Current Research in Environmental Sustainability](https://journalfinder.elsevier.com/results?query=Current%20Research%20in%20Environmental%20Sustainability&mode=search)|4|未核|未核|**适合，新增候选**。包括维持生态系统的社会条件/关系与自然资源可持续管理；需严谨方法、新知识与可迁移意义。|第2076行：Gold / DISCOUNT|
|[Trees, Forests and People](https://journalfinder.elsevier.com/results?query=Trees%2C%20Forests%20and%20People&mode=search)|2|未核|未核|**有条件，新增候选**。包括都市树木/森林及社会政治治理，但须以树木/森林及其管理为核心对象，不能仅把公园自动当森林。|第2660行：Gold / DISCOUNT|

## 关键官网证据

- Regional Sustainability另访问KeAi主页及Guide成功HTTP200：https://www.keaipublishing.com/en/journals/regional-sustainability/ 。主页未展示审稿总时长；Guide要求two days返回校样，不是审稿时间。
- STOTEN排除原句：“Papers of social science in nature on economics, sociology, psychology, political science, policy, planning and/or management”。
- GECCO：“The journal will generally not consider manuscripts without a significant biological component”。
- Biological Conservation：“We also welcome papers coming from social sciences including those reporting on advances in conservation politics, ethics, policy, human social structure and biodiversity, and political culture among other subjects.”
- Environmental Challenges可能不收：“General SDG/ESG discourse, awareness studies, or surveys without environmental outcome metrics.”
- 用户给的Urban Agriculture and Forestry、Ecology & Ecosystem Services官方Finder搜索200，但无精确刊名结果；不能据此确认为独立期刊。也不应擅自改成已排除的UFUG。

## Excel完整核读记录

`Q1 2026 埼玉大学.xlsx`全部2个工作表的非空内容已按可逆compact格式分8批核读：Q1 TA共2681条非空行（物理行至2685）；Changes Journal Categories共115条非空行（物理行至117）。核读包括定义、表头、日期、ISSN、刊名、FC状态、费用资格、类别变化及URL。Q1是第1季度版本；没有审稿时间，也不是分区。
- QUOTA是转换协议OA额度资格；DISCOUNT是折扣资格，均不证明审稿快。
- 表中JORT、JEM、LUP、SCS等为Core Hybrid+QUOTA；GECCO、Heliyon、EI、ESI、ETI、Ecotoxicology and Environmental Safety为Gold+DISCOUNT。
- Regional Sustainability未在所给表中发现精确刊名；KeAi Guide写2025-09-10起投稿接收后APC USD900，不能假定有学校额度。
- 表日期数值46100对应2026-03-19。资格仍须结合学校协议、通讯作者与剩余额度。

原始文件未修改；官方证据保存在本目录。
