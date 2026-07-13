---
schema_version: '1.0'
id: rf-energy-harvesting-rectenna
title: 射频能量采集整流天线设计与效率分析
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - energy-harvesting-iot
  - boost-converter-energy-harvesting
tags:
  - 整流天线
  - RF能量采集
  - 整流
  - 阻抗匹配
  - 环境能量
  - 肖特基
  - 微功率
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 射频能量采集整流天线设计与效率分析

> **难度**：🔴 高级 | **领域**：RF 能量采集 | **关键词**：Rectenna, 整流, 匹配, 功率密度 | **阅读时间**：约 16 分钟

## 日常类比

手机没电时，空气里仍有广播、蜂窝、Wi-Fi 电波。射频（Radio Frequency, RF）能量采集像在沙漠里“挤空气里的水”：**整流天线**（rectenna = antenna + rectifier）把高频交流变成直流，供微功率物联网节点——可用功率通常很小，须精打细算[1][2]。

## 摘要

从环境功率密度、天线与整流拓扑、匹配与效率瓶颈，到升压存储与系统占空比。功率密度与效率数字为场景量级，随距离与法规限值剧变[3]。

## 1. 可用能量

自由空间路径损耗使远场密度迅速下降；室内多径可能局部增强或抵消。须区分“环境机会采集”与“专用无线供电”[1][4]。

| 来源倾向 | 特点 |
|----------|------|
| 广播/蜂窝环境 | 覆盖广，密度常很低 |
| Wi-Fi 近距 | 中等，不稳定 |
| 专用发射机 | 可控，需合规 |

## 2. 整流天线链路

天线 → 匹配网络 → 肖特基等非线性整流 → 滤波储能 → 可选升压变换器 → 负载。低输入功率下二极管阈值电压是效率杀手；多倍压可抬电压但可能损效率[2][5]。

| 环节 | 关键 |
|------|------|
| 天线 | 增益、极化、带宽、尺寸 |
| 匹配 | 随功率电平变化的大信号阻抗 |
| 整流 | 器件选择、谐波、效率曲线 |
| 电源管理 | 冷启动、最大功率点、存储 |

## 3. 系统可行性

微瓦级平均功率只支撑极低占空比传感；需超级电容/薄膜电池缓冲，并严格睡眠电流。商用能量采集电源芯片可简化冷启动，仍不能违背链路预算[6]。

## 4. 局限、挑战与可改进方向

### 1. 功率密度被高估

**局限**：实验室近场结果无法搬到百米室外。
**改进**：现场测密度；按法规等效全向辐射功率做预算[3][4]。

### 2. 匹配随功率漂移

**局限**：小信号匹配在真实输入下失配。
**改进**：大信号表征；可调/宽带匹配；多频整流[5]。

### 3. 冷启动失败

**局限**：电压低于芯片启动阈值。
**改进**：专用冷启动电路；降低负载；间歇工作[6]。

### 4. 与通信天线共存

**局限**：收能与通信互相干扰或占净空。
**改进**：频分/时分；双天线隔离；优先专用供能链路[7]。

## 总结

整流天线能让极低功耗节点“喝电波”，但必须用诚实的链路预算与占空比设计；它是能量架构选项，不是无限电池替代品。

## 参考文献

[1] Friis transmission and RF power density fundamentals.
[2] Rectenna design surveys (antenna + Schottky rectifier).
[3] Regulatory EIRP limits impacting wireless power / harvesting.
[4] Ambient RF energy measurement studies in urban environments.
[5] Large-signal matching and diode model for low-power rectifiers.
[6] Cold-start boost converters for energy harvesting PMICs.
[7] Coexistence of harvesting and communication antennas.
[8] Multiband and broadband rectenna techniques.
[9] Storage element selection: supercap vs thin-film battery.
[10] Harmonic termination and rectifier efficiency optimization.
[11] Wireless power transfer vs ambient harvesting taxonomy.
[12] IoT duty-cycle design under microwatt average budgets.
