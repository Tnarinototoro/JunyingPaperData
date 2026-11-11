# 第14版文献核查：Labib et al. (2020), Scale effects

## 完整阅读记录与文件

- 核查原文：`Scale effects in remotely sensed greenspace metrics and how to mitigate them for environmental health exposure assessment.pdf`。
- 已逐页完整阅读全部15页，包括方法、全部图表、讨论、限制、结论、声明与参考文献。每页均读取OCR并核对页面图像；不是摘要式或关键词式审读。
- 以下页码均为PDF页码，也与页脚1–15相同。
- 全文提取：`C:\Users\happyelements\Desktop\Paper\.paper14_work\scale_review\ocr.txt`。
- 逐页文本及图像：同目录的 `page_1.txt`–`page_15.txt`、`page_1.png`–`page_15.png`。
- OCR由现有Windows语言包提取，Latin基本可读，但数字、公式、标点、两栏顺序有误；直接引文和不等号均以页面图像为准。
- 本次未编辑稿件正文，未阅读无关文件，未将参考文献列表中的其他文章计为已经完整阅读。

## 结论

**本文不能支持生态与人类两个领域“统一最优100m”。** 它研究遥感绿量指标的尺度敏感性与多尺度暴露地图，不是生态响应最优距离、人类视觉感知最优距离或某一实际健康结局最优距离的验证研究。作者明确认为暴露尺度随作用路径而变，统一的绝对标准可能无法成立。

100m可以被准确描述为本文使用的多个分析距离之一，或作为局地绿地收益路径讨论中的例子；不能写成已验证的普适最优值。全文未提出25m、29m或43m的人类尺度／最优距离结论。

## 精确证据与解释边界

### 1. p2左栏：明确没有统一buffer共识

> “However, there is no consensus among scholars as to what buffer distance should be used to define the exposure area (e.g., neighbourhood). Indeed, it is highly unlikely that such a universal figure could ever be justified (Huck et al., 2018a; Labib et al., 2020).”

此句直接排除把本文当作统一最优距离的依据。这里的Labib et al. (2020)指作者同年的另一篇系统综述，不是本文自我验证“100m最佳”。

### 2. p2右栏§2.1：只研究availability，而非visibility／实际使用

> “The present study only focuses on the exemplar of availability exposure due to its dominance in previous studies.”

此前区分availability、accessibility和visibility。本文的卫星NDVI／LAI／LULC代表周边绿地可用量或潜在暴露，并不直接等于利用者所见、偏好、接触时长或活动。

### 3. p3左栏§2.2：≤100m是条件性的局地路径示例，不是恰好100m最优

> “Markevych et al. (2017) argued that the selection of buffer size and areal unit of analysis might depend on the pathways of benefits being considered in a given study; for example, for air and noise pollution mitigation, a smaller buffer (≤ 100 m) may be more appropriate, whereas for physical activity based benefits a larger buffer (e.g., 500 m) size might be relevant (Labib et al., 2020).”

> “Therefore, it appears that selection of an absolute standard in terms of buffer size or spatial unit of greenspace exposure measurement may not be possible due to how the different potential benefit pathways from greenspace may vary over different spatial extents.”

核查要点：

- 原文为 **≤100m**，不是“≥100m”，也不是“100m是最大效应点”。
- 对象是空气／噪声污染缓解，措辞为“may be more appropriate”。
- 身体活动路径给出的例子为500m。
- 本文在此综合转述既有研究，不是本文对100m与其他距离的健康效应最优性检验。
- p3同栏另提到Su et al. (2019)的500m／250m比较；“250m”不能误读或缩写为25m。

### 4. p5右栏§3.4与表1：多尺度暴露用mean，不是midrange

> “For each specific scale, mean values of NDVI, LAI, and green percentage (for LULC) were estimated.”

表1列出100、200、300、400、500m五个尺度。各尺度的平均NDVI／LAI／绿色比例进一步以lacunarity权重合成多尺度地图，再组合不同指标。

本稿若采用 `(max + min) / 2`，那是midrange／极值中点，不是本文使用的均值方法。不能用本文证明该midrange指数已获得暴露测度验证。lacunarity阶段对连续NDVI／LAI使用的“range”是box mass计算中的极差处理（p4–5、Fig. 1与p8 Fig. 3），与暴露图的平均值是不同步骤。

几何也不可直接等同：作者采用gliding-box／focal-statistics框架（Fig. 1的box shape为Rectangle），并在行文中称buffer distance或box size；本文未测试沿公园边界向内／向外各100m的边界带，也未证明此类带状比较与该方法相同。

### 5. p6右栏§4.3：100／200m与300／400／500m各有不同用途

> “These scales were set by buffer distances of 100, 200, 300, 400, and 500 m.”

> “Buffer distances such as 100 and 200 m, for example, allow consideration of relatively localised exposure benefits, e.g. some forms of air pollution removal and cooling (Labib et al., 2020; Markevych et al., 2017); whereas distances such as 300, 400, and 500 m allow the consideration of neighbourhood exposure benefits in terms of the capacity-building benefits of greenspace exposure such as encouraging physical activities, improving social cohesion, and stress recovery (Hartig et al., 2014; Markevych et al., 2017; Nieuwenhuijsen et al., 2017).”

“such as”“for example”均为例示，不是统一最优判定。100与200共同作为局地暴露例子，邻里收益则使用300–500m。

### 6. p6§4.2、p8 Fig. 3、p10§5.1：640／480m是案例内聚合上限，不是健康或生态最优

本文在Greater Manchester的影像与景观条件下发现，NDVI／LAI的lacunarity曲线在300–600m逐渐趋平；Sentinel-2约640m、Landsat-8约480m是作者描述的尺度变异可接受范围上限。

p10原句：

> “The lacunarity analysis results in the present study show the upper limit for scale or buffer distance values (~640 m for Sentinel-2, ~480 m for Landsat-8) above which real-world landscape characteristics and image textures might no longer exhibit variability because of a reduction in variance caused by aggregation of the landscape patterns (see Fig. 3b, c, d).”

> “Therefore, selecting the appropriate buffer distances below the upper limit of the acceptable range of scales should be a key consideration.”

这些值涉及遥感指标方差与影像纹理随聚合变化，并未寻找某个生态种群／人类结局的最强作用距离。不能推广为跨地点通用阈值，也不意味着“低于640m的每个距离均同样有效”或“100m最好”。p10–11还建议在统计分析前检查不同buffer距离的方差，警惕过度聚合改变统计关联。

### 7. p11§5.2：作者主张按路径选一个或多个尺度

> “They provide opportunities to select one or more scales based on the pathways of health benefits under consideration (Labib et al., 2020; Markevych et al., 2017; Su et al., 2019).”

该段再次说明使用100–500m五个等间距尺度并综合，不是选出单一100m胜者。其输出表示各像元的潜在暴露，可结合居住、工作、路线等位置资料使用；不是已经观察到每个人的真实暴露。

### 8. p12§5.3：人类视觉指标没有研究，实际健康指标没有验证

> “Thirdly, we only investigated scale effects in satellite image based exposure metrics as a measure of greenspace abundance.”

> “Recent work has utilised street view images to measure how people actually observe greenspace (Helbich et al., 2019; Li & Ghosh, 2018; Lu, 2019; Wang et al., 2019). Scaling effects in observational metrics (e.g., derived from street view images) should therefore also be explored in future studies.”

> “Fourth, we have only presented an analysis from a single case study region.”

> “Finally, we did not test our new exposure index with explicit health indicators to test its robustness. Instead we compared with IMD, and health deprivation, which are pseudo indicators for health and wellbeing (Cebrecos et al., 2018).”

作者在限制部分明确承认：

- 只研究卫星绿量，而人类实际观察绿地的street-view类指标需要未来研究。
- 仅有一个案例地区，跨城市／跨地理环境的尺度敏感性需检验。
- 只测试Sentinel-2及Landsat-8的moderate–coarse resolution，尚未检验更高分辨率影像。
- 未用实际健康指标验证新指数；IMD与health deprivation是代理指标。
- 未考虑蓝空间。

p6§3.5也先行说明，以LSOA的IMD与health deprivation deciles代表社会经济剥夺及“pseudo health conditions”，通过均值比较、Spearman相关评价指数。p7与p12 Fig. 7的相关结果不能升级成个体健康因果证据。

### 9. p12–13§6：结论仍是多尺度减轻不确定性

结论强调greenspace metrics随buffer distance变化而敏感，结合多个尺度／指标以减少尺度效应及健康路径选择的不确定性。没有提出100m是生态或人类最优尺度，也没有给25／29／43m阈值。

## 25m、29m、43m核查

逐页完整阅读后，又对全文OCR检索25、29、43及距离关键词，并回看相关图像。全文没有25m、29m、43m的人类尺度／感知距离／统一最佳距离命题。

实际可见的近似数字包括：

- p3：250m（转述Su et al. 2019关于某些健康关系随buffer变化的讨论），不是25m。
- p6及p8：`r = 129`、2560m等，是gliding-box／lacunarity图示参数，不是29m。
- p13–14参考文献：Drusch et al.的页码25–36、Kabisch et al.的页码25–34、Myint & Lam的期刊卷号29、Park & Kwan的期刊卷号43，以及其他卷页／DOI数字。

因此不能从本文为25／29／43m添加出处。若稿件需要这些距离，应另核查真正提出该数字且与研究问题匹配的原始文献。

## 准确书目与同作者同年区分

本篇：

Labib, S. M., Lindley, S., & Huck, J. J. (2020). Scale effects in remotely sensed greenspace metrics and how to mitigate them for environmental health exposure assessment. *Computers, Environment and Urban Systems, 82*, 101501. https://doi.org/10.1016/j.compenvurbsys.2020.101501

首页作者写作S.M. Labib、Sarah Lindley、Jonny J. Huck；不应自行扩展Labib名字。DOI是`compenvurbsys`，不要照抄OCR的误分隔形式。

本文p14列出的另一篇同作者2020综述：

Labib, S. M., Lindley, S., & Huck, J. J. (2020). Spatial dimensions of the influence of urban green-blue spaces on human health: A systematic review. *Environmental Research, 180*, 108869. https://doi.org/10.1016/j.envres.2019.108869

若稿件同时引用二者，作者–年份体例需按采用格式统一2020a／2020b。若按题名字母序赋号，则Scale effects为2020a，Spatial dimensions为2020b。第二篇书目在本文参考文献中核实，但本次并未读取第二篇全文；p3的相关论述在本篇中属于转引／综述式论述。

其他相关转引的身份（仅本篇书目核对，未独立完整阅读）：

- Browning, M. H., & Lee, K. (2017). Within what distance does “greenness” best predict physical health? A systematic review of articles with GIS buffer analyses across the lifespan. *International Journal of Environmental Research and Public Health, 14*(7), 675. https://doi.org/10.3390/ijerph14070675 （p13）
- Markevych et al. (2017). Exploring pathways linking greenspace to health: Theoretical and methodological guidance. *Environmental Research, 158*, 301–317. https://doi.org/10.1016/j.envres.2017.06.028 （p14；本篇列表缩略作者，未自行补全）
- Su, J. G., Dadvand, P., Nieuwenhuijsen, M. J., Bartoll, X., & Jerrett, M. (2019). Associations of green space metrics with health and behavior outcomes at different buffer sizes and remote sensing sensor resolutions. *Environment International, 126*, 162–170. https://doi.org/10.1016/j.envint.2019.02.008 （p15）

## 稿件可用的保守写法（供父代理判断，不代表已编辑）

如果100m确为本稿预设的公园边界内外比较宽度，可以将其明确归为操作性分析尺度，并用本文支持“不能解读为统一最优”的限制，而不让文献承担该几何或数值已经验证的论断。

日文示例：

> 公園境界の内外を共通の空間単位で比較するため、本研究では100m幅の帯域を操作的な分析単位として採用した。ただし、これは生態学的応答と人間の知覚に共通する最適距離を意味しない。緑地曝露の適切な空間尺度は、想定する便益の経路や分析条件によって異なる（Labib et al., 2020a）。

英文示例：

> For a consistent comparison inside and outside park boundaries, we adopted a 100 m band as an operational spatial unit. This should not be interpreted as a universal optimum for ecological responses or human perception; appropriate greenspace-exposure scales depend on the benefit pathway and analytical context (Labib et al., 2020a).

此例中的a／b须与稿件实际文献表一致。若需要把100m描述为文献中已有局地路径的候选距离，可以说明空气／噪声缓解在本文综述讨论中采用≤100m的条件性例子，但不可扩大为视觉感知、所有健康结局或生物多样性最佳距离。
