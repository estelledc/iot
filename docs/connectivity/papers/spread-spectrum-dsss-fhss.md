---
schema_version: '1.0'
id: spread-spectrum-dsss-fhss
title: 扩频技术DSSS与FHSS在IoT抗干扰中的原理
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites: UNKNOWN
tags:
  - DSSS
  - FHSS
  - 扩频原理
  - 处理增益
  - PN码
  - 抗干扰
  - ISM
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 扩频技术DSSS与FHSS在IoT抗干扰中的原理

> **难度**：🟡 中级 | **领域**：扩频通信 | **阅读时间**：约 14 分钟

## 日常类比

嘈杂火车站传话：DSSS（Direct Sequence Spread Spectrum）像把同一句话用约定节奏“拉长喊很多码片”，对方相关叠加后声音浮出；FHSS（Frequency Hopping Spread Spectrum）像按暗号换位置说话，躲开固定噪声源。二者都用多余带宽换抗干扰，是工业科学医疗（ISM）频段物联网可靠通信的基础武器[1][2]。

## 摘要

处理增益 \(G_p \approx B_{\mathrm{spread}}/B_{\mathrm{data}}\)。DSSS 靠码片相关抑制干扰；FHSS 靠跳信道躲避。码同步与跳频同步是工程关键；理论增益需扣实现损失[1][3]。

## 1. 为何扩频

| 方式 | 带宽策略 | 优点 | 代价 |
|------|----------|------|------|
| 窄带 | 刚好够传数据 | 频谱效率高 | 窄带干扰可一击致命 |
| 扩频 | 故意展宽 | 抗干扰/低截获/可共存 | 占更多频谱 |

民用化与 FCC 等对扩频设备的开放推动了 Wi-Fi/蓝牙/Zigbee 等落地（历史脉络，细节以法规原文为准）[4]。

## 2. DSSS 原理

数据比特乘伪随机（PN）码片序列，速率提升则频谱展宽。接收端用同一码相关：

| 对象 | 解扩后行为 |
|------|------------|
| 匹配信号 | 能量收拢回窄带，幅度按码长增强 |
| 不相关干扰 | 被进一步打散，落入滤波器的比例下降 |

常见码：Barker（如历史 802.11b）、Gold、Walsh（同步正交）、802.15.4 规定序列等[3][5]。

```
发送: bit → × PN chips → 调制
接收: RF → × 本地 PN → 积分判决
```

## 3. FHSS 原理

载波按跳频图样在信道集合上切换；单跳可保持较窄瞬时带宽。处理增益叙事常与跳频点数、被干扰比例相关。需收发共享图样与时间基准；蓝牙等还用自适应剔除坏信道[2][6]。

| 维度 | DSSS | FHSS |
|------|------|------|
| 干扰策略 | 稀释 | 躲避 |
| 同步 | 码相位 | 时间+图样 |
| 瞬时谱 | 宽 | 可窄 |
| 多址 | CDMA 码分 | 跳图/时隙组合 |

## 4. 与 IoT 波形关系

802.15.4/Zigbee：DSSS；蓝牙：FHSS/AFH；LoRa：CSS（啁啾），原理同属“展宽换增益”家族但实现不同。应用选型见 `spread-spectrum-dsss-fhss-iot`[5][7]。

## 5. 局限、挑战与可改进方向

### 1. 同步门限

**局限**：低信噪比下先丢同步再丢比特，增益用不上。
**改进**：加长前导、提高捕获算法；温度补偿晶振。

### 2. 近远效应与非线性

**局限**：强干扰/强邻道使相关器饱和或互调。
**改进**：AGC、滤波、功率控制；现场避开大功率源。

### 3. 理论 \(G_p\) 高估

**局限**：忽略滤波、量化、码不理想互相关。
**改进**：链路预算留 若干 dB 实现余量；用 PER 标定。

### 4. 法规约束

**局限**：跳频点数、驻留时间、带宽影响合法功率。
**改进**：按目标市场选 FHSS vs 数字调制条款设计。

## 6. 实践要点

1. 先算所需抗干扰类型（窄带音 vs Wi-Fi 宽干扰）。
2. 示波器/SDR 观察码片速率与跳频驻留是否符合设计。
3. 与 MAC 重传、信道评估一起评估，单靠 PHY 扩频不够。

## 参考文献

[1] Peterson, R. L., Ziemer, R. E., Borth, D. E., Introduction to Spread-Spectrum Communications.
[2] Bluetooth SIG, Core Specification (frequency hopping).
[3] Torrieri, D., Principles of Spread-Spectrum Communication Systems.
[4] FCC Part 15.247 historical/current materials (US).
[5] IEEE 802.15.4 standard.
[6] Simon, M. K. et al., Spread Spectrum Communications Handbook.
[7] Semtech LoRa modulation primers (CSS).
[8] IEEE 802.11b PHY clauses (DSSS Barker).
[9] Rappaport, T. S., Wireless Communications: Principles and Practice.
[10] Proakis, J. G., Digital Communications (spread spectrum chapters).
[11] Dixon, R. C., Spread Spectrum Systems with Commercial Applications.
