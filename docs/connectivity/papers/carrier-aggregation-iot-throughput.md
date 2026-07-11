---
schema_version: '1.0'
id: carrier-aggregation-iot-throughput
title: 载波聚合在IoT高吞吐场景中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - cellular-iot-evolution-2g-5g
  - lte-cat-m1-vs-nbiot
tags:
  - 载波聚合
  - LTE
  - 5G NR
  - 吞吐量
  - PCell
  - SCell
  - 工业物联网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 载波聚合在IoT高吞吐场景中的应用

> **难度**：🔴 高级 | **领域**：蜂窝技术 | **阅读时间**：约 22 分钟

## 日常类比

一根水管流量受管径限制；并联多根则总流量相加。载波聚合（Carrier Aggregation, CA）把多个组件载波（Component Carrier, CC）并行给用户面，换更高吞吐。多数物联网走低功耗广域；矿卡点云、工业视觉、多路视频等才需要 CA 这类“功耗与成本换带宽”方案[1][2]。

## 摘要

本文说明主小区（PCell）/辅小区（SCell）、带内/带间 CA、跨载波调度与独立混合自动重传请求（HARQ），并对比模组等级与 Wi-Fi/毫米波替代。峰值 Mbps/Gbps 为无线电能力上限，**实地常显著低于峰值**[3][5]。

## 1. 原理与术语

运营商频谱常碎片化于多频段；长期演进（LTE）单载波常至 20 MHz，新空口（NR）单载波可更宽，仍可能不够。CA 聚合多 CC：PCell 承载关键控制与移动性；SCell 主要承载数据，可激活/去激活以省电[1][2]。

| 类型 | 形态 | 硬件复杂度 | 分集 |
|------|------|------------|------|
| 带内连续 | 同频段相邻 | 较低 | 弱 |
| 带内非连续 | 同频段有空隙 | 中 | 弱–中 |
| 带间 | 跨频段 | 高 | 强（常见） |

## 2. 建立与调度

流程概要：仅 PCell 接入 → UE 能力上报 → RRC 配置 SCell（常先不激活）→ MAC 控制元素激活 → 每 CC 独立调度/HARQ。跨载波调度可用 PCell 物理下行控制信道指示 SCell 数据，节省 SCell 控制开销但加重 PCell[1]。

| 方案 | 优点 | 代价 |
|------|------|------|
| 自载波调度 | 简单 | 每 CC 控制开销 |
| 跨载波调度 | SCell 资源偏数据 | PCell 控制负担 |

## 3. IoT 适用边界

| 适合 CA | 不适合 |
|---------|--------|
| 持续高吞吐、有线供电 | NB-IoT/小包传感器 |
| 运营商多频覆盖 | 仅单频弱覆盖 |
| 可接受模组成本 | 极低成本终端 |

LTE 类别与 NR 终端能力决定最大 CC 数与 MIMO；模组价与电流随 CC/带宽上升——具体美元与毫安随供应链变化，**需询价与热设计**[5]。

## 4. 与替代技术

| 方案 | 优点 | 限制 |
|------|------|------|
| CA | 蜂窝广域、标准成熟 | 贵、耗电、依赖运营商 |
| 高阶 MIMO | 不额外占频谱 | 天线空间 |
| 毫米波 | 单载波大带宽 | 覆盖/阻挡 |
| Wi-Fi 多链路 | 免授权灵活 | 范围与干扰 |

工业现场常见：广域用 NR CA+MIMO，车间用 Wi-Fi，固定回传用毫米波或有线。

## 5. 案例要点（矿山类高上行）

高上行持续需求（传感+多路视频压缩后达百 Mbps 量级叙事）时，需确认**上行 CA** 配置、路测边缘吞吐、切换时 SCell 行为与模组散热。双连接/冗余可降中断；多车并发要做小区容量规划。公开白皮书数字为场景绑定，**不可直接当 SLA**[5]。

## 6. 局限、挑战与可改进方向

### 1. 下行思维惯性

**局限**：消费电子 CA 偏下行，工业 IoT 常卡上行[1][5]。
**改进**：招标明确 UL CA 频段组合；路测记上行百分位。

### 2. 功耗与热

**局限**：多 RF 链路满载温升导致降速或断链。
**改进**：SCell 动态去激活；导通比与散热设计；环境高温降额。

### 3. 覆盖与移动性

**局限**：边缘退回单 CC，吞吐掉台阶。
**改进**：缓存/补传；加密地图分区；基站密度与切换参数联调。

### 4. 成本错配

**局限**：用高 Cat/NR CA 模组跑低速率业务。
**改进**：按 P95 吞吐选型；能边缘抽稀则降 CC；与 Wi-Fi 分流。

## 7. 实践要点

1. 先写清上行/下行分别目标与供电约束，再选 Cat/NR 能力。
2. 向运营商索取支持的频段组合与 UL CA 表。
3. 验收用持续流量剖面，而非瞬时 speedtest 峰值。

## 参考文献

[1] 3GPP TS 36.300, E-UTRA and E-UTRAN overall description (Carrier Aggregation).
[2] 3GPP TS 38.300, NR and NG-RAN overall description (CA).
[3] Pedersen, K. et al., "Carrier Aggregation for LTE-Advanced," IEEE Commun. Mag., 2011.
[4] Yuan, G. et al., "Carrier Aggregation for LTE-Advanced Mobile Communication Systems," IEEE Commun. Mag., 2010.
[5] Vendor industrial 5G/mining white papers (treat KPIs as case-specific).
[6] 3GPP UE capability and CA band combination specifications.
[7] 3GPP MAC CE SCell activation timing related specs.
[8] Comparisons of CA vs MIMO vs mmWave for high-throughput IoT (survey/industry).
[9] Module vendor datasheets for LTE Cat and NR CA power consumption.
[10] 3GPP RedCap / eRedCap overviews (when CA is out of scope for constrained UE).
[11] ITU/3GPP materials on uplink-centric industrial wireless requirements.
