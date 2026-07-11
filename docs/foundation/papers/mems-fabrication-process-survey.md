---
schema_version: '1.0'
id: mems-fabrication-process-survey
title: MEMS传感器制造工艺：体硅与表面微加工
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - mems-packaging-reliability
tags:
  - MEMS
  - 体硅微加工
  - 表面微加工
  - DRIE
  - SOI
  - 牺牲层
  - 晶圆键合
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# MEMS传感器制造工艺：体硅与表面微加工

> **难度**：🔴 高级 | **领域**：MEMS 制造 | **关键词**：Bulk, Surface, DRIE, SOI | **阅读时间**：约 16 分钟

## 日常类比

木雕两种做法：厚木料往下凿（减法）≈ 体硅微加工（Bulk Micromachining）；平板上叠薄片再抽掉中间层让上层悬空（加法再拆）≈ 表面微加工（Surface Micromachining）。工艺路线决定结构厚度、纵横比、良率与成本量级[1][2]。

## 摘要

对比湿法/干法刻蚀、DRIE（Deep Reactive Ion Etching，深反应离子刻蚀）Bosch 工艺、SOI（Silicon-on-Insulator）、牺牲层、键合与 LIGA 等。能力数字因产线而异，**以代工厂 PDK/文献区间理解，勿当承诺规格**[3][4]。

## 1. 体硅 vs 表面

| 维度 | 体硅 | 表面微加工 |
|------|------|------------|
| 材料去除 | 从衬底挖 | 薄膜堆叠+释放 |
| 结构厚度 | 可较厚 | 通常更薄 |
| 典型器件 | 压力传感器膜、喷墨等 | 加速度计梳齿、RF 开关等 |
| 兼容 CMOS | 视流程 | 常更易后道兼容 |

| 刻蚀 | 特点 |
|------|------|
| KOH 等湿法 | 各向异性晶体依赖，成本低，角补偿需设计 |
| RIE/DRIE | 高纵横比，Bosch 循环钝化/刻蚀，侧壁波纹 |

SOI 提供精确器件层厚度与埋氧释放停止层，常用于高精度惯性结构[5]。

## 2. 关键辅助工艺

| 工艺 | 用途 |
|------|------|
| 牺牲层释放 | 形成可动结构；防粘连关键 |
| 晶圆键合 | 密封腔、多层结构（阳极/熔融/玻璃浆料等） |
| LIGA | 高深宽比金属结构（非硅主流） |
| 金属/压电沉积 | 电极与换能材料 |

| 传感器例子 | 工艺倾向 |
|-------------|----------|
| 压阻压力 | 体硅膜 + 腔 |
| 电容加速度计 | 表面或 SOI 梳齿 |
| 麦克风 | 复合膜 + 背板孔 |

## 3. 局限、挑战与可改进方向

### 1. 粘连与释放良率

**局限**：干燥释放时结构贴死。
**改进**：超临界干燥、抗粘连凸点、气相 HF 等。

### 2. 残余应力

**局限**：薄膜应力导致弯曲、频偏。
**改进**：应力工程、退火、对称叠层。

### 3. 成本与产能

**局限**：特殊 MEMS 步骤使晶圆价高。
**改进**：与 CMOS 共线策略；设计规则保守换良率。

### 4. 设计–工艺鸿沟

**局限**：仿真未含刻蚀偏差导致量产漂移。
**改进**：PCM 监控；统计设计；与代工厂早期共设计。

## 4. 实践要点

1. 选型传感器时问清工艺世代与空腔密封方式。
2. 可靠性与封装强相关，见 `mems-packaging-reliability`。
3. 读懂剖面图再评估是否能改版定制。

## 参考文献

[1] Madou, Fundamentals of Microfabrication.
[2] Senturia, Microsystem Design.
[3] Bosch DRIE process reviews.
[4] SOI MEMS technology papers.
[5] Wafer bonding techniques for MEMS surveys.
[6] Stiction and release methods literature.
[7] LIGA process overviews.
[8] CMOS-MEMS integration reviews.
[9] Residual stress in thin films MEMS.
[10] Foundry MEMS PDK example documentation.
[11] Surface vs bulk micromachining comparison chapters.
