# 第14版：两篇新NDVI文献完整阅读核查

已完整逐页阅读Fairbairn等14页、Cabello等8页，含结果、考察、结论、声明和参考文献；对书目及关键方法/缓冲尺度原句、图表进行视觉核对。不编辑正文、不改原PDF、不重新估计。本笔记只根据这两篇用户提供的PDF，不把其所引其他论文当作已读原始证据。

## 全文工件：主代理可直接完整复读

- Fairbairn全文：C:\Users\happyelements\Desktop\Paper\.paper14_work\fairbairn_review\ocr.txt 。14页标记齐全。
- Sierra全文：C:\Users\happyelements\Desktop\Paper\.paper14_work\sierra_review\ocr.txt 。8页标记齐全。
- 每个folder另有page_1.txt等单页文本、page_1.png等原页图像及pages.json。中文OCR识别器对少量英文字母、符号、下标/公式有误，引用以下核对后的原句；遇疑优先看对应png。

## 1. 真实书目

### Fairbairn

Fairbairn, A. J., Katholnigg, S., Leichtle, T., Merkens, L., Schroll, L., Weisser, W. W., & Meyer, S. T. (2025). NDVI and vegetation volume as predictors of urban bird diversity. Scientific Reports, 15, 12863. https://doi.org/10.1038/s41598-025-96098-0

页1核实完整署名：Andrew J. Fairbairn; Sophia Katholnigg; Tobias Leichtle; Lisa Merkens; Louis Schroll; Wolfgang W. Weisser; Sebastian T. Meyer。页11：Received 23 November 2024; Accepted 26 March 2025; Published online 15 April 2025。

### Sierra

完整文件名：A dataset on potentially groundwater-dependent vegetation in the Sierra Nevada Protected Area (Southern Spain) and its underlying NDVI-derived ecohydrological attributes.pdf

Cabello, J., Escudero-Clares, M., Martos-Rosillo, S., Casas, J. J., Cintas, J., Zakaluk, T., & Salinas-Bonillo, M. J. (2025). A dataset on potentially groundwater-dependent vegetation in the Sierra Nevada Protected Area (Southern Spain) and its underlying NDVI-derived ecohydrological attributes. Data in Brief, 61, 111760. https://doi.org/10.1016/j.dib.2025.111760

页1完整署名：Javier Cabello; Montserrat Escudero-Clares; Sergio Martos-Rosillo; J. Jesús Casas; Juanma Cintas; Thomas Zakaluk; María J. Salinas-Bonillo。Received 9 May 2025; Revised 28 May 2025; Accepted 2 June 2025; Available online 9 June 2025。论文DOI与其数据集DOI 10.5281/zenodo.15315192不同。论文参考文献[11]将数据集年份写2024，不能据此把本论文改为2024。

## 2. 100m能支持什么：结论最重要

Fairbairn不是验证“所有生物多样性或公园研究的100m最佳”。它在德国慕尼黑86个声学调查点，比较六种点周围半径（25、50、100、200、400、800m），用线性模型的部分R²等评价鸟类群落的种丰富度、鸣声活动率VAR及Shannon指数。它不是某一个物种的100m最优，而是特定城市、特定调查方式、三个群落指标、六个候选尺度中的总体选择。

尤其，植被体积预测VAR时50m表现略好，作者为变量比较的一致性采用100m。因此“100m在所有模型中都唯一最优”也不准确。

这与本研究公园polygon边界为基准的外环/内外抽取范围，在几何形状、分析单元、响应变量和采样方式上不同。点圆缓冲半径100m不能直接验证公园外环宽100m。更不能用该文替代本研究真实GIS操作或宣布已做多尺度敏感性检验。

Sierra论文没有100m距离比较或选择论证。它是10m像元上的NDVI时间序列/地下水依赖植被分类。Fig.2的100/200/300等是类别数码，不是米；“groundwater buffering”指水文缓冲作用，不是空间缓冲区。

## 3. Fairbairn精确原句与页码

### 产品/时间：p4，Mapping NDVI and vegetation volume

> While site selection was done on an NDVI map from 2017, we obtained newer remote sensing data from 2019 for all further analyses.

> Optical satellite imagery with very high spatial resolution of 30 × 30 cm² was acquired by WorldView-3 on 04.07.2019.

> Based on these data, the NDVI was calculated (range −1 to 1, Fig. 2) for the single date.

注意：原文所报告的NDVI地图解像度为30cm；不擅自把这一报告扩展成WorldView-3所有原生多光谱波段均为30cm。原文此处没有给出产品处理级别、云掩膜阈值或完整波段比值算式。

### 点周围多尺度/真正的空间平均：p4，Site characteristics at differing Spatial scales

> To characterise the area surrounding each sampling point, we calculated mean NDVI and mean vegetation volume (henceforth NDVI and vegetation volume) within several buffers around each sampling point (25 m, 50 m, 100 m, 200 m, 400 m, 800 m).

> Mean NDVI was calculated using the extract function in the terra package using a summary function of mean.

p5 Fig.3图题明确叫“six different radius buffers”。p4所报告的最小/最大值是不同缓冲范围的分布描述，不是用(max+min)/2算均值。文中没有把极值中间值作为区域平均NDVI的依据。

### 选择尺度：p5 Analysis，p6 Results及p7 Fig.4

作者比较各buffer和指标的线性模型部分R²，加入记录周与距市中心距离为协变量；以跨指标表现选择buffer。图4纵轴是Partial R squared。不是随机化干预的因果结果。

关键例外原句（p6，Optimal buffer for vegetation metrics）：

> Although the 50 m buffer initially appeared preferable for VAR and vegetation volume, we ultimately selected the 100 m buffer for consistency.

p7 Fig.4的植被体积VAR曲线最高在50m，另两条最高在100m；与p6一致。

### 采样方法决定尺度、物种差异：p8，Optimal buffer for vegetation metrics

> However, their surveys were based on a 50 m point count at each observation point.

> It is worth noting that while we used the same buffer for all species, there is likely an effect of scale when investigating species individually, as others have found.

> Thus, our findings suggest that using passive acoustic monitoring, a 100 m buffer effectively describes the spatial relationship between vegetation characteristics and overall bird diversity.

p8解释声学记录探测范围受环境、鸣声属性、设备影响；小缓冲可能遗漏相关资源，大缓冲可能混入无关变异。本文比较另一研究50m时，说明该研究采用50m point counts，不能转引成自己已读那篇研究或普遍规则。

### 地域与解释边界：p10—11

p10，NDVI as a planning and conservation tool：

> It's worth noting that our study represents a Western European city, and results may vary in other regions.

p11续段：

> Additionally, as our community composition shows, species react differently to increasing green, and for conservation efforts targeting a specific species, just increasing NDVI will likely not have the desired outcomes.

作者把提高模型/物种特异分析列作未来方向。不能从NDVI较高的相关性直接提出“提高NDVI即可提高目标物种”“本研究环境的質已经代表生物多样性”或“100m对日本公园也最优”。

## 4. Fairbairn可借鉴的报告项目（仅借格式，不填进本研究）

| 项目 | 原文实际报告及位置 |
|---|---|
| 地点/样本 | Munich, Germany；86监测点，街灯位置；p2—3 |
| 选点底图 | 2017 NDVI、20×20cm原地图；聚合为100m栅格、负值归0用于分层选点；p2、p4 |
| 分析产品 | 2019-07-04 WorldView-3单景；NDVI图30cm；p4 |
| 另一个遥感量 | 50cm nDSM与植被分类、体积m³；p4 |
| 生物调查时点 | 2023年四个记录周，每点录一次约一周；p3；2019影像与2023调查非同期 |
| 空间汇总 | 点周围六个半径范围；terra extract的mean作NDVI；p4 |
| NA/体积汇总 | 植被体积sum/整个buffer面积，处理非植被NA；p4；这不是NDVI掩膜方案 |
| 区分100m用途 | 选点栅格p2—3；点圆缓冲p4—8；预测图100m网格p6；三个概念不可混写 |
| 指标/拟合 | 丰富度、VAR、基于VAR的Shannon；记录周/市中心距协变量、多尺度部分R²；p4—7 |
| 验证 | 69训练点、17测试点、误差评估；p6—7；这是其研究的验证，不是本研究已有验证 |

另：p10讨论NDVI对非植被表面、水面、建筑/道路等也有取值，可能帮助描述城市矩阵；因此不要把其“选点时负值归0”误写为正式分析时也删掉/清零所有非植被像元。

## 5. Sierra方法实际内容及精确原句

### p5，Experimental Design, Materials and Methods

> Sentinel-2 Level 2A imagery from January 2019 to December 2023 was obtained from the Copernicus Open Access Hub.

紧随其后给出2,537景、QA波段及两个概率阈值；云雪掩膜原句：

> Cloud and snow masking were applied using Sentinel-2 QA bands (MSK_CLDPRB, MSK_SNWPRB), excluding pixels with >10% cloud probability and >1% snow probability.

> A minimum NDVI threshold of 0.1 was used to mask non-vegetated areas, validated using high-resolution orthophotos (PNOA).

> Monthly NDVI was calculated using Sentinel-2 bands B4 (red) and B8 (NIR).

三个属性：August旱季NDVI；May/June与August干湿季差（按高度调整）；2019—2023年际NDVI CV。Fig.2指AAZ用August—June，SAZ/CAZ用August—May。全文没有明确交代月内多景汇总用mean还是median，也没有写完整NDVI波段比值算式；不能替作者补称采用特定月合成方式。也没有空间均值midrange的算式。

### p6：空间/软件/验证

> Raster layers were generated at 10 m spatial resolution for both the 64 ecohydrological classes and the three-level pGDV classification.

> All layers use the ETRS89 / UTM Zone 30N coordinate system (EPSG: 25830).

GEE处理NDVI和过滤；R 4.2.3做统计/聚类，列raster、sp、terra、rgdal、cluster、factoextra、FactoMineR、NbClust、ggplot2；QGIS Desktop 3.28.4显示/导出。三变量四分位组合64类，再分海拔/含水层区域做欧氏距离、完全链接聚类，得到三类潜在地下水依赖。统计表含mean、SD、min、max，描述的是类别的属性，不是以min/max替代区域平均。

泉点与喜湿植物分布作部分验证，只用存在点，Producer’s Accuracy关注漏判；排除定位不精确记录、作χ²空间关联检验。这里没有100m圆缓冲或polygon外环的优化实验。

### p6：限制原句

> Cloud and snow filtering, although applied systematically, may lead to data gaps in high-elevation zones, especially during winter months.

> The NDVI threshold of 0.1 used to mask non-vegetated areas may exclude low-biomass ecosystems with some degree of groundwater dependence, such as sparsely vegetated wetlands or early-successional habitats.

> The classification into pGDV levels is based on remotely sensed proxies, which, although validated using spatial indicators (springs and hygrophilous species), do not directly measure groundwater use.

其他限制：10m可能漏掉窄河岸廊道/小地下水排出区；既有植被图在交错带/混合覆盖不确定；仅存在数据不能评总体分类精度。故其0.1掩膜也不是普遍“正确阈值”，尤其不能直接用于本稿自然再生公园湿地而不说明可能的丢失。

## 6. 对日本第二篇可做的最小、诚实改进

### 100m选择：可选日语句（只有需要比较时才加入）

> 都市鳥類を対象とした研究では、ミュンヘンの86調査点の周囲で25～800mの六つの半径を比較し、音響調査で把握した鳥類群落を説明する範囲として100mを選択している（Fairbairn et al., 2025）。ただし、これは調査点を中心とする範囲についての結果であり、本研究の公園ポリゴンを基準とする範囲とは、幾何形状、分析単位及び測定内容が異なる。本研究の100m設定は、この文献によって最適性が検証された距離ではなく、公園に近接する緑化条件を共通の範囲で比較するための操作的設定として扱う。

原稿方法可完全不加入长比较段，只在方法注明操作设定、在限界注明未作其他距离/形状敏感性检验；文献用于说明尺度依赖即可。别让篇幅被新遥感文献占据。

### 方法的报告清单

参考Sierra的报告组织，按本研究真实记录逐项说明：影像/NDVI产品及处理级别；获取时间/所用时段；分辨率；红光和近红外波段（若自算）；投影；公园polygon边界及内/外范围的几何构造；空间/时间汇总函数；云雪、水面、无效像元和NoData规则；软件版本；相对调查日期；必要的地图/元数据。缺失项目保留待确认，不能从这两篇论文借来当成本研究参数。

若本研究本轮已经确认采用全像元平均，应如实写其统计函数；若仍是13版的(max+min)/2，则仍明确为midrange。两篇新文献都不能证明midrange等于领域平均或验证其作为本模型环境指标的效度。

Cabello文献可用于解释“数据处理/掩膜本身会改变所代表的生态环境”，不是本研究测量效度的外部验证。除非正文确有时间序列/低植被湿地处理的具体论点，不必为已读而强行添加引用。

## 7. 逐页阅读覆盖核对

- Fairbairn p1署名/摘要/背景；p2遥感指标背景与选点；p3声学调查及Fig.1；p4产品、空间汇总及Fig.2；p5 Fig.3和分析；p6预测方法/结果/尺度例外；p7 Fig.4、预测结果及考察起始；p8 Fig.5、尺度考察、NDVI解释；p9 Fig.6群落及Fig.7预测地图；p10群落与应用/地域限制；p11未来、结论、日期和参考文献1—13；p12参考文献14—61；p13参考文献62—78、资助/作者/声明；p14许可。全部页完整读过。
- Sierra p1署名/摘要；p2摘要续及规格表；p3价值/背景/数据；p4 Fig.1与文件；p5 Fig.2和处理步骤1—3；p6步骤4—7及限制；p7伦理/贡献/可用性/资金/声明及首条引用；p8全部参考文献。全部页完整读过。
