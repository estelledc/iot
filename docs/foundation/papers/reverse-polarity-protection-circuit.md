---
schema_version: '1.0'
id: reverse-polarity-protection-circuit
title: 反接保护与过压保护电路设计
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 14
prerequisites:
  - esd-protection-circuit-design
tags:
  - 反接保护
  - MOSFET
  - TVS
  - 过压保护
  - ESD
  - 理想二极管
  - 电源保护
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 反接保护与过压保护电路设计

> **难度**：🟢 入门 | **领域**：电源保护 | **关键词**：反接, MOSFET, TVS, 过压, ESD | **阅读时间**：约 14 分钟

## 日常类比

电池装反时，好的遥控器不亮也不坏——里面有“门卫”挡住反方向电流。野外物联网节点还要防浪涌、静电与过压。保护电路就是保险丝 + 门卫，避免几十元传感器被一次接错永久报废[1][2]。

## 摘要

对比二极管/金属氧化物半导体场效应管（MOSFET）反接保护、瞬态电压抑制器（TVS）与过压关断、与静电放电（ESD）配合。压降与钳位电压以器件手册为准[3]。

## 1. 反接保护

| 方案 | 优点 | 代价 |
|------|------|------|
| 串联二极管 | 简单 | 压降与发热，低电压电池吃亏 |
| P-MOS / N-MOS 理想二极管 | 压降小 | 驱动与成本稍高 |
| 专用理想二极管控制器 | 性能好 | 元件更多 |

MOSFET 方案注意阈值、体二极管方向、启动浪涌与热；汽车/工业输入常叠加反向与过压复合保护[1][4]。

## 2. 过压与浪涌

TVS 吸收短时尖峰；持续过压需输入开关关断或串联调节。选 TVS：工作电压、钳位、功率波形（如 8/20 µs）、封装热[2][5]。极性保护与 TVS 布局应靠近连接器。

| 威胁 | 典型手段 |
|------|----------|
| 反接 | 二极管/MOSFET |
| 浪涌/抛负载 | TVS、滤波、抑制器 |
| ESD | TVS/ESD 阵列、结构泄放 |
| 过流 | 保险丝、限流开关 |

## 3. 系统注意

保护后的电压仍须满足后级欠压锁定；测量时确认保护本身漏电流不毁掉年续航。多电源输入防反灌（理想二极管或负载开关）[6]。

## 4. 局限、挑战与可改进方向

### 1. 二极管压降导致欠压

**局限**：电池末期设备提前关机。
**改进**：改 MOSFET 理想二极管；允许的压降预算进设计[4]。

### 2. TVS 钳位过高

**局限**：尖峰仍超过后级绝对最大额定。
**改进**：选更低钳位或二级保护；验证浪涌标准等级[5]。

### 3. 保护器件自身失效短路

**局限**：TVS 短路导致冒烟。
**改进**：上游保险丝协调；热与能量计算[2]。

### 4. 忽略返修与误接场景

**局限**：现场接线工反接无指示。
**改进**：反接指示、防呆连接器、印刷极性[6]。

## 总结

反接用低损耗 MOSFET 方案更适合电池 IoT；过压/ESD 用靠近接口的分级保护，并与保险丝能量配合，形成可验证的防护链。

## 参考文献

[1] Reverse-polarity protection with P-channel MOSFETs (vendor ANs).
[2] TVS diode selection guides for DC power ports.
[3] IEC 61000-4-2 ESD and surge standards context.
[4] Ideal diode controllers and OR-ing controllers datasheets.
[5] Clamping voltage vs working peak reverse voltage trade-offs.
[6] Hot-plug reverse current blocking practices.
[7] Fuse and TVS coordination application notes.
[8] Automotive load-dump protection overview (ISO 7637 context).
[9] Battery-powered IoT quiescent current impact of protection parts.
[10] Connector keying and polarity marking for field installs.
[11] ESD protection for signal lines vs power lines.
[12] Thermal design of series protection MOSFETs.
