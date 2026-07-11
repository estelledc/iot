---
schema_version: '1.0'
id: z-wave-long-range-800-series
title: Z-Wave Long Range 800系列芯片新特性
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - z-wave-protocol-smart-home
tags:
  - Z-Wave
  - Long Range
  - ZWLR
  - 800系列
  - DSSS
  - Silicon Labs
  - TrustZone
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Z-Wave Long Range 800系列芯片新特性

> **难度**：🟡 中级 | **领域**：Z-Wave 演进 | **阅读时间**：约 18 分钟

## 日常类比

小区内靠邻居接力送快递（经典 Mesh）；对面别墅区则骑车直达驿站（Z-Wave Long Range, ZWLR 星型直连控制器）。800 系列让同一控制器可同时管“接力”与“直达”两种配送[1][2]。

## 摘要

概述 EFR32ZG23 一代相对 700 系列的安全/射频/存储提升，以及 ZWLR 的 DSSS（Direct Sequence Spread Spectrum）、更高链路预算与星型拓扑。距离公里级与节点四千级为规格叙事，**视距、法规功率与天线强相关**[2][4]。

## 1. 800 系列硬件要点

| 项 | 700 系列量级 | 800 系列量级 |
|----|--------------|--------------|
| CPU | Cortex-M4 | Cortex-M33（可含 TrustZone） |
| 加密 | 更多靠软件 | 硬件加速更常见 |
| Flash/RAM | 较低 | 更高（利于安全与应用） |
| 灵敏度叙事 | 较弱 | 经典/ZWLR 分列更优数字 |

TrustZone 等把密钥与安全启动与应用隔离，配合 Z-Wave S2；具体分区以实现为准[3][5]。

## 2. ZWLR vs 经典 Z-Wave

| 特性 | 经典 Z-Wave | ZWLR |
|------|-------------|------|
| 拓扑 | Mesh，多跳中继 | 星型，直连 Hub |
| 调制叙事 | FSK 族 | DSSS |
| 距离叙事 | 每跳室内数十米级 | 视距可至公里量级 |
| 节点容量叙事 | 232 量级 | 更高（规格称数千） |
| 适用 | 室内家居密集 | 院落、车库、大户型远点 |

经典 Mesh 与 ZWLR 可共存于同一网络叙事下；远点用 LR，近点仍可 Mesh——规划时避免假设“LR 节点还能当中继”[1][2]。

## 3. 功耗与安全

800 系列厂商材料常称发射能量与睡眠电流优于上代；ZWLR 更高功率档会抬发射能耗，需按上报周期重算电池[3][4]。S2 入网与硬件 AES/ECC 加速缩短安全握手时间，仍须正确配置密钥与控制器策略[5]。

## 4. 局限、挑战与可改进方向

### 1. 视距规格当户内承诺

**局限**：1.6 km 级数字不适用于多层混凝土。
**改进**：按实际墙体做链路测试；远点优先室外/窗边天线。

### 2. 星型单点 Hub

**局限**：无 Mesh 中继时 Hub 故障或遮挡即失联。
**改进**：Hub 冗余与位置优化；关键设备保留经典 Mesh 路径。

### 3. 区域频段与认证

**局限**：Sub-GHz 功率/频点因地区而异。
**改进**：SKU 分区认证；勿混用未认证功率档。

### 4. 生态双模复杂度

**局限**：安装商需理解何种设备是 LR-only。
**改进**：包装与 App 标明模式；控制器 UI 分拓扑视图。

## 5. 实践要点

1. 大户型/院落先画“直连 LR”与“室内 Mesh”分区图。
2. 电池设备按 ZWLR 功率档重做续航预算。
3. 升级 800 时验证 S2、OTA 与旧设备混网兼容矩阵。

## 参考文献

[1] Z-Wave Alliance, Z-Wave Long Range technical overview.
[2] Silicon Labs, EFR32ZG23 / Z-Wave 800 series product documentation.
[3] Silicon Labs, Z-Wave 700 vs 800 migration and power notes.
[4] Z-Wave Alliance, Z-Wave protocol and RF specifications (regional).
[5] Z-Wave Alliance, Security 2 (S2) documentation.
[6] ARM, TrustZone for Cortex-M technical overview.
[7] DSSS fundamentals in wireless textbooks / IEEE tutorials.
[8] Vendor application notes on mixed classic + LR networks.
[9] Indoor vs outdoor Sub-GHz propagation references (treat km claims carefully).
[10] Z-Wave certification and interoperability program materials.
[11] Comparative smart-home LR options (ZWLR vs other Sub-GHz) — market notes.
