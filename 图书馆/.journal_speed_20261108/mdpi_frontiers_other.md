# MDPI、Frontiers及其他期刊核验（2026-11-08）

本表针对日本39个公园、34个管理团体的管理者问卷，EFA及探索性SEM，研究自然恢复、生物多样性保全与游憩协调、管理实施条件和多主体参与。适投评价是论文与范围的专业判断，不是编辑接收承诺。原始官网页面及全文已保存同目录，抓取程序为check_c.py，初批访问日志为access_c.json。

## 可取得的官方速度证据

- **Trends in Sciences**：[官网首页](https://tis.wu.ac.th/tishome/)明确标示“1 - 3 days / Time to First Decision”“30 days / Review Time”“50 days / Submission to Acceptance”。页面未说明统计年度、窗口、均值或中位数。[审稿流程](https://tis.wu.ac.th/tishome/about/about.php)明确1–3天是Editorial Check（可能初筛拒稿），Peer Review为4–6周，其后Editorial Decision再1–2周。这是官方刊载时效，不能承诺任何一稿50天接收，1–3天也不是外审意见时间。
- **MDPI**：英文官网本次返回403；中国官网公开API https://mdpi.cn/api/journals 可读。父任务已核对前端 `/_nuxt/DFZrzpts.js` 标题为 **Median Time to First Decision**。API对应数值Land16天、Urban Science20天、Diversity14天、Applied Sciences15天、Environments18天、Sustainability16天；**未提供投稿至接收时间，也未给统计窗口**。这组数字只能支持首次决定比较，不能支持最终接收速度排序。父任务保存原始API与前端证据。
- **Frontiers四刊**：主页、About、栏目Scope、出版社Peer Review与How We Publish页均可读取；本次所读取页面没有发现逐刊投稿至接收或首次决定的总体统计。不得套用出版社记忆数值。
- **PeerJ**：页面为Javascript应用；读取其官方加载脚本 `https://cdn.peerj.com/96897eb/webpack/246.98d6423f.js`，其中明确“32 days / Acceptance to publication”。**这32天是接收后出版，完全不是投稿至接收**。未获首次决定和投稿至接收总体数值。

## 用户清单逐刊判断

“未核实”指不能给出可靠数字，不代表审稿慢或快；范围未能读取时，不将人工判断伪装成最新官网核验结果。

|期刊|官网/在线状态与范围证据|对现稿判断|首次决定|投稿至接收|
|---|---|---|---|---|
|Land|[官网](https://www.mdpi.com/journal/land)403；中国官方API可读|**较适合**：土地与景观管理、都市绿地治理；范围匹配为专业判断，英文最新Scope未读取|官方API中位16天，窗口未明|未核实|
|Urban Science|[官网](https://www.mdpi.com/journal/urbansci)403；中国官方API可读|**较适合**：都市公园、城市绿地管理；英文最新Scope未读取|官方API中位20天，窗口未明|未核实|
|Global Journal of Environmental Science and Management|[官网](https://www.gjesm.net/)403|**有条件**：须突出环境管理与保全治理贡献；最新Scope未读取|未核实|未核实|
|Trends in Sciences|[Scope](https://tis.wu.ac.th/tishome/AimsandScope.php)200，涵盖自然、物理与应用科学，列Ecology、Environmental chemistry等|**有条件、匹配较弱**：论文主要是管理者/社会调查，不宜仅因有Ecology就认定最契合|官网1–3天初筛；外审4–6周，之后决定1–2周|官网刊载50天，未交代统计口径|
|Environmental Engineering and Management Journal|[Scope](https://eemj.eu/index.php/EEMJ/about/editorialPolicies)200，明确integrated management、strategies/policies、environmental education/sustainable development，亦大量工程主题|**有条件**：可从环境综合管理与政策实践切入；不能因刊名含engineering一概排除|未核实；官网只有rapid editorial decisions的描述|未核实|
|Jordan Journal of Earth and Environmental Sciences|[官网](https://jjees.hu.edu.jo/)200；官方Scope为earth/environmental sciences，含geology、land、water、air、plant；作者指南8页也读取|**不优先**：现稿为公园管理行为，地球/环境自然科学实测弱|未核实|未核实；作者指南two days仅校样返还|
|Maejo International Journal of Science and Technology|[官网](https://mijst.mju.ac.th/)SSL证书验证失败，HTTP入口亦转HTTPS失败|**不优先**：综合科技主题，公园管理问卷的直接匹配未证实|未核实|未核实|
|Environment & Ecology|[官网入口](https://environmentandecology.com/)406|**不优先**：生态方向相关，但现稿没有生态过程/生态结果数据；最新Scope未读|未核实|未核实|
|Frontiers in Sustainable Cities|[Urban Greening栏目Scope](https://www.frontiersin.org/journals/sustainable-cities/sections/urban-greening/about)200；明确urban green/blue space governance、human perception/use、management、biodiversity|**较适合，Frontiers中优先**；Urban Greening栏目直接匹配|未核实总体统计|未核实总体统计；下方相近单篇128天|
|Urban Biodiversity and Ecosystem Services|未能证实该精确名称为独立期刊，未找到可靠官方刊名/ISSN对应|**先核对刊名和ISSN**；不能把领域/栏目名当独立刊推荐|不适用/未证实|不适用/未证实|
|Diversity|[官网](https://www.mdpi.com/journal/diversity)403；中国官方API可读|**有条件、低于Land/Urban Science**：需明确生物多样性保全贡献；管理行为不是直接的多样性结果|官方API中位14天，窗口未明|未核实|
|Frontiers in Ecology and Evolution|[About](https://www.frontiersin.org/journals/ecology-and-evolution/about)200；要求contemporary ecological/evolutionary concepts，[Urban Ecology](https://www.frontiersin.org/journals/ecology-and-evolution/sections/urban-ecology/about)强调生物组分与过程|**不优先/需增强生态学贡献**：现稿主要管理行为，没有直接生态结果|未核实|未核实|
|PeerJ|[Scope](https://peerj.com/journals/peerj/aims-and-scope/)200，JS内容读取；涵盖Environmental Science，强调有效研究与报告质量|**有条件**：需清楚呈现保全科学问题与方法有效性；小样本SEM是风险|未核实|未核实；32天是接收后出版|
|Frontiers in Conservation Science|[保全社会科学栏目Scope](https://www.frontiersin.org/journals/conservation-science/sections/conservation-social-sciences-indigenous-and-local-knowledge/about)200；human dimensions of conservation management/policy，含behavior change、cooperative conservation、decision making|**较适合**：保全管理的人类维度直接匹配；Original Research需novel/hypothesis/data-driven，须如实解释探索性设计|未核实|未核实总体统计；相近社会调查单篇186天，另一遗传研究42天|
|Frontiers in Environmental Science|[About](https://www.frontiersin.org/journals/environmental-science/about)200；含Environmental Economics and Management、Environmental Policy and Governance、Social-Ecological Urban Systems|**有条件、较相关**：建议环境管理/治理栏目；Social-Ecological Urban Systems目前强调气候适应/减缓，现稿未必最贴该栏目|未核实|未核实|
|Ecology & Ecosystem Services|未能证实该精确名称为独立期刊；Crossref这次精确查询未返回项，不能据此断言不存在|**先核对刊名/ISSN**；不能与Ecosystem Services混同|不适用/未证实|不适用/未证实|
|Urban Agriculture and Forestry|未能证实该精确名称为独立期刊|**先核对刊名/ISSN**；可能与Urban Forestry & Urban Greening等混淆，而后者用户已排除|不适用/未证实|不适用/未证实|
|Built Environment|[出版社官方入口](https://www.alexandrinepress.co.uk/built-environment)403|**有条件但不优先**：城市空间规划、治理相关；须核是否主题专刊及接受主动投稿，当前未核实|未核实|未核实|
|Urban Planning, Design and Transport|未能证实精确名称为独立期刊|**先核对刊名/ISSN**；不可自动替换为Urban Planning等其它刊|不适用/未证实|不适用/未证实|
|Urban Health and Well-being|未能证实精确名称为独立期刊|**先核对刊名/ISSN**；论文没有健康结果，若为健康主题栏目也不优先|不适用/未证实|不适用/未证实|
|Current Science|[官网](https://www.currentscience.ac.in/)307+Javascript防护页，未读取正常内容|**不优先**：综合科学取向，现稿的普适自然科学贡献有限，最新Scope未读|未核实|未核实|
|Applied Sciences-Basel（正式刊名Applied Sciences）|[官网](https://www.mdpi.com/journal/applsci)403；中国API可读|**不优先**：现稿非应用技术/工程创新，仅有NDVI不足以改变主体|官方API中位15天，窗口未明|未核实|
|Journal of Urban Planning and Development|[ASCE官网](https://ascelibrary.org/journal/jupddm)403|**有条件**：需突出都市公园规划、治理和可操作决策贡献；最新Scope未读取|未核实|未核实|

## 补充候选（不表示已证明接收快）

|期刊|官网与判断|首次决定|投稿至接收|
|---|---|---|---|
|Environments|[官网](https://www.mdpi.com/journal/environments)403，中国API可读；环境管理/保全实践较相关|API中位18天，窗口未明|未核实|
|Sustainability|[官网](https://www.mdpi.com/journal/sustainability)403，中国API可读；可持续公园治理较相关|API中位16天，窗口未明|未核实|
|Journal for Nature Conservation|[官网Insights](https://www.sciencedirect.com/journal/journal-for-nature-conservation/about/insights)403；保全管理实施很相关|未核实|未核实|
|City and Environment Interactions|[官网Insights](https://www.sciencedirect.com/journal/city-and-environment-interactions/about/insights)403；城市社会与环境管理交互较相关|未核实|未核实|
|Conservation Science and Practice|[Wiley官网](https://conbio.onlinelibrary.wiley.com/journal/25784854)403；保全实践实施/治理较相关|未核实|未核实|
|Ecological Solutions and Evidence|[Wiley官网](https://besjournals.onlinelibrary.wiley.com/journal/26888319)403；应用管理证据相关，需要决策贡献|未核实|未核实|

## Frontiers单篇官方日期案例（不能替代全刊中位数）

|期刊/文章|Received|Accepted|自然日|官方原文|
|---|---|---|---:|---|
|Frontiers in Sustainable Cities, “Green for whom? Sociospatial inequalities in public green space accessibility in the context of a Latin American City”（Original Research，GIS+社会调查）|2026-07-01|2026-11-06|128|[DOI10.3389/frsc.2026.1925722](https://www.frontiersin.org/journals/sustainable-cities/articles/10.3389/frsc.2026.1925722/abstract)|
|Frontiers in Conservation Science, “Towards Effective and Inclusive Protected Areas: Characterising Perceptions of Benefit Flows and Support for Conservation in Protected Area adjacent Communities”（Original Research，保全社会调查）|2026-05-04|2026-11-06|186|[DOI10.3389/fcosc.2026.1872441](https://www.frontiersin.org/journals/conservation-science/articles/10.3389/fcosc.2026.1872441/abstract)|
|Frontiers in Conservation Science, “Characterization of a SNP panel for individual discrimination in the critically endangered Apennine brown bear ...”（Original Research，分子遗传，题材不近）|2026-09-24|2026-11-05|42|[DOI10.3389/fcosc.2026.2009037](https://www.frontiersin.org/journals/conservation-science/articles/10.3389/fcosc.2026.2009037/abstract)|

有意排除：DOI10.3389/frsc.2026.1964710虽列Received11Aug→Accepted23Oct=73天，但页面同时列Revised16Nov2026，晚于接收/上线和查询日，日期矛盾；不能用于速度证据。DOI10.3389/fcosc.2026.2033635虽19天，但为Perspective，不能与研究论文同类比较。其他首页最新Original Research链接多403，未凑足每刊3篇。

## 专业建议

在本批中，主题优先顺序可用：Land / Urban Science / Frontiers in Sustainable Cities–Urban Greening / Frontiers in Conservation Science–Conservation Social Sciences，再到Frontiers in Environmental Science、Environments、Sustainability。**目前无证据可把这组按投稿至接收速度可靠排序。** Trends in Sciences的官方50天是当前本批唯一直接的全刊投稿至接收刊载值，但主题贴合明显弱于上述候选，统计口径也未公布，因此只能列作条件性备选，不能直接宣布为用户最佳首投。
