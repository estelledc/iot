---
schema_version: '1.0'
id: boost-converter-energy-harvesting
title: Boost升压转换器在能量采集中的应用
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - buck-converter-design-iot
tags:
  - Boost
  - 能量采集
  - 冷启动
  - MPPT
  - 超电容
  - BQ25570
  - 微功率
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Boost升压转换器在能量采集中的应用

> **难度**：🟡 中级 | **领域**：升压电源 | **阅读时间**：约 14 分钟

## 日常类比

荒野用小镜子聚光生火：单次能量微弱，持续聚焦才能点燃。能量采集同理——室内光伏、TEG（热电发电机）电压常远低于 MCU 门槛，需 Boost 把微瓦级能量“攒”到可用轨[1][2]。

## 摘要

讲清 Boost 增益与冷启动、电荷泵辅助 vs 电感升压、BQ25570/LTC3108/SPV1050 类 IC 对比、OCV-MPPT 与储能管理。效率与冷启动电压以数据手册为准，**微瓦区效率远低于瓦级叙事**[3][4]。

## 1. 原理与为何需要升压

理想 CCM：\(V_{\mathrm{out}}/V_{\mathrm{in}}=1/(1-D)\)。输入电流经电感较连续，输出侧电流更脉动，纹波与补偿（含 RHP 零点）通常难于 Buck[5]。

| 源 | 电压量级 | 功率量级 |
|----|----------|----------|
| 室内光伏 | 约 0.3–0.6 V | µW–mW/cm² 视光照 |
| TEG | 约数十–百 mV | 常 µW 级 |
| 压电 | AC 伏级不等 | 间歇 µW–mW |
| RF 采集 | 亚伏 | 极微弱 |

冷启动：系统无电时 IC 仍需最低输入才能“醒来”；启动后工作电压往往可更低（电荷泵或变压器辅助）[1][6]。

## 2. IC 与 MPPT

| IC 倾向 | 冷启动叙事 | MPPT | 备注 |
|---------|------------|------|------|
| BQ25570 | 约数百 mV 启动 | 可编程 | 电池/超电容管理较全 |
| LTC3108 | 极低（变压器） | 基本无 | 体积换电压 |
| SPV1050 | 约 0.1 V 级 | OCV 法 | 低 Iq 叙事 |

OCV-MPPT：周期性测开路电压，工作点取 \(k\cdot V_{\mathrm{oc}}\)（\(k\) 常约 0.75–0.85）。P&O 更精细但微功率下采样开销与误差大，采集 IC 少用[3][7]。

| 储能 | 适合 |
|------|------|
| 超电容 | 频繁脉冲负载缓冲 |
| 二次电池 | 较长时储能 |
| 薄膜电池 | 微型、低自放电场景 |

## 3. 微功率效率

| 输入功率区 | 效率倾向 |
|------------|----------|
| 瓦级 | 可很高 |
| mW | Iq 开始显眼 |
| 数十–百 µW | 常明显下降 |
| 极低 µW | 可能入不敷出 |

策略：超低 Iq、间歇工作（充到阈值再唤醒）、简化 MPPT 频率、电感低 DCR；微电流下肖特基有时优于同步整流（驱动损耗）[4][8]。

## 4. 局限、挑战与可改进方向

### 1. 冷启动门槛高于源电压

**局限**：弱光/小温差永远启动不了。
**改进**：选更低冷启动 IC/变压器方案；增大换能器或改储能预充策略[1][6]。

### 2. 手册峰值效率误导

**局限**：90% 出现在毫瓦以上，室内节点跑不到。
**改进**：按实际 Pin 测端到端；能量预算含 Boost Iq 与泄漏[4][9]。

### 3. MPPT 采样打断充电

**局限**：OCV 采样窗口损失能量，快变光照跟踪差。
**改进**：拉长采样间隔或按环境自适应；关键场景评估输入电容[3][7]。

### 4. 超电容自放电

**局限**：天级自放电吃掉采集盈余。
**改进**：容量与漏电流匹配负载周期；必要时混用电池[8][10]。

## 5. 实践要点

1. 先做源 I–V 与负载能量预算，再选 IC。
2. 验收看“能否冷启动 + 目标工作周期能否能量中性”。
3. 布局按开关电源：短环路、输入输出电容就近。

## 参考文献

[1] Texas Instruments, BQ25570 datasheet / energy harvesting ANs.
[2] Analog Devices, LTC3108 ultralow voltage step-up datasheet.
[3] STMicroelectronics, SPV1050 energy harvester datasheet.
[4] Ramadass, Y. & Chandrakasan, A., minimum-energy tracking, IEEE JSSC, 2011.
[5] Erickson & Maksimović, Fundamentals of Power Electronics (boost, RHPZ).
[6] Cold-start charge-pump techniques in harvesting PMICs.
[7] MPPT methods for PV at microwatt scale (OCV vs P&O).
[8] Supercapacitor leakage and buffering in IoT nodes.
[9] Power-neutral testing of energy harvesting systems (sensors literature).
[10] TEG interface and low-voltage boost design notes.
[11] Indoor PV characterization under lux-level illumination.
[12] Schottky vs sync rectification at microamp currents.
