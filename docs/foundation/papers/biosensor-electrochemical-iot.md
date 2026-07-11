---
schema_version: '1.0'
id: biosensor-electrochemical-iot
title: 电化学生物传感器在IoT健康监测中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 14
prerequisites: UNKNOWN
tags:
  - 生物传感器
  - 电化学
  - AFE
  - CGM
  - 可穿戴
  - SPE
  - 恒电位仪
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 电化学生物传感器在IoT健康监测中的应用

> **难度**：🔴 高级 | **领域**：生物传感 | **阅读时间**：约 14 分钟

## 日常类比

医院抽血查血糖像“去加油站量油”；皮肤贴片每隔数分钟测组织液/汗液指标，则像车上的油量灯——靠生物识别层（酶/抗体）这把“钥匙”开锁，换能电极把结合事件变成电流或阻抗[1][2]。

## 摘要

梳理电流法/电位法/阻抗法/伏安法、三电极与丝网印刷电极（SPE）、恒电位仪与 AFE（Analog Front End）选型，以及 CGM（连续血糖监测）等 IoT 链路。灵敏度与寿命数字为量级，**随酶活性、污染与校准策略变化**[3][4]。

## 1. 测量方法

| 方法 | 观测量 | IoT 常见用途 |
|------|--------|--------------|
| 电流法（Amperometry） | 固定电位下电流 | 葡萄糖/H₂O₂ 等 |
| 电位法（Potentiometry） | 电极电位（Nernst） | pH、ISE 离子 |
| 阻抗法（Impedimetry） | 界面阻抗 | 免疫结合 |
| 伏安法（Voltammetry） | 扫电位下的 I–V | 机理与高灵敏定量 |

葡萄糖氧化酶路径：底物反应产生 H₂O₂，再在工作电极氧化产生电流，浓度与电流相关（理想扩散模型）[1]。

## 2. 电极与 AFE

| 电极材料 | 倾向优势 | 备注 |
|----------|----------|------|
| 金 | 易修饰、稳定 | 免疫/DNA |
| 碳 | 宽电位窗、低成本 | SPE 主流 |
| 铂 | 催化 H₂O₂ | 气体/过氧化物 |

三电极：工作电极（WE）、参比（RE，常 Ag/AgCl）、对电极（CE）。恒电位仪稳住 WE–RE 电位，跨阻放大器（TIA）把 nA–µA 电流转为电压[2][5]。

| AFE | 方法覆盖 | 功耗倾向 | 场景 |
|-----|----------|----------|------|
| AD5940 类 | 电流/伏安/阻抗 | 中 | 通用电化学 |
| LMP91000 类 | 电流法为主 | 低 | 电池供电气体/生物 |
| 生物电位 SoC | 阻抗/ECG 等 | 低 | 非纯电流法 |

## 3. IoT 应用与集成

链路：SPE → AFE → ADC → MCU → BLE → App/云。CGM 等产品以分钟级采样、日计佩戴为目标；汗液乳酸/电解质/皮质醇等多仍受选择性、校准与稳定性约束[3][6]。

| 挑战 | 要点 |
|------|------|
| 生物相容 | ISO 10993 等；水凝胶界面 |
| 漂移/污染 | 酶衰减、蛋白 fouling、钝化 |
| 校准 | 工厂/指血/自校准（成熟度不同） |
| 法规 | “健康参考”与医疗诊断门槛差巨大 |

## 4. 局限、挑战与可改进方向

### 1. 传感器寿命短于电子寿命

**局限**：酶电极常仅数日–数周量级有效。
**改进**：防污膜、可替换 SPE、算法漂移补偿；规格写清更换周期[4][7]。

### 2. 汗液/间质液与血液不等价

**局限**：相关关系因人、因运动状态变化。
**改进**：明确用例（趋势 vs 诊断）；多传感器融合与临床标定[3][6]。

### 3. AFE 噪声与微电流

**局限**：大 Rf TIA 带宽与噪声恶化，易被运动伪迹淹没。
**改进**：可编程增益、屏蔽与机械固定；按电流量程分段校准[2][5]。

### 4. 法规定位不清

**局限**：按消费电子宣称医疗效果风险高。
**改进**：早期划分 IVD/可穿戴健康路径；软件按 IEC 62304 分级管理[8][9]。

## 5. 实践要点

1. 先定分析物与方法（电流 vs 阻抗），再选 AFE。
2. 功耗按“测量窗 + 长睡眠”预算，验证整机而非仅芯片 Iq。
3. 产品文案与认证路径同步设计，避免后期推倒重来。

## 参考文献

[1] Wang, J., "Electrochemical Glucose Biosensors," Chem. Rev., 2008.
[2] Analog Devices, AD5940 datasheet / electrochemical AFE user guide.
[3] Gao, W. et al., wearable perspiration sensor arrays, Nature, 2016.
[4] Bandodkar, A. J. et al., wearable chemical sensors challenges, ACS Sensors, 2016.
[5] Texas Instruments, LMP91000 Sensor AFE datasheet.
[6] CGM accuracy literature (MARD reporting practices).
[7] Biosensor fouling and anti-fouling coating reviews.
[8] ISO 10993 biocompatibility; IEC 60601 / IEC 62304 context.
[9] FDA/CE-MDR IVD vs wellness product guidance overviews.
[10] SPE fabrication and disposable electrode application notes.
[11] Nernstian ISE theory and wearable electrolyte sensing papers.
[12] BLE wearable power budgeting for intermittent AFE sampling.
