---
schema_version: '1.0'
id: device-to-device-d2d-communication
title: 设备到设备D2D通信在IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - lte-cat-m1-vs-nbiot
  - grant-free-access-massive-iot
tags:
- D2D
- ProSe
- Sidelink
- 5G NR
- 设备发现
- 干扰管理
- 工业IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 设备到设备D2D通信在IoT中的应用

> **难度**：🔴 高级 | **领域**：蜂窝旁路链路、近距 IoT | **阅读时间**：约 22 分钟

## 日常类比

把照片发给隔壁邻居，却先上传千里外的云再下来——路绕远了。D2D（Device-to-Device）让近距设备直连，少经基站中转：延迟与发射能量往往更低，灾后无基站时仍可能保本地连通。工厂里传感器到旁侧控制器，不必事事绕核心网。

## 摘要

覆盖 3GPP ProSe / NR Sidelink、发现与 Mode 1/2 资源分配、带内复用干扰，以及中继与能耗逻辑。文中毫秒/微焦级算例为链路预算示意，须用目标频段与调度参数重测[1][2][3]。

## 1 概念与对比

传统路径：UE→基站→UE；D2D：UE↔UE（sidelink）。距离通常数十～数百米量级，可用授权频谱（基站协调）或非授权（自主，QoS 难保证）[2]。

| 特征 | 蜂窝 D2D | Wi-Fi Direct | 蓝牙 |
|------|----------|--------------|------|
| 频段 | 授权（典型） | 非授权 | 非授权 |
| 管理 | 基站可调度 | 自主 | 自主配对 |
| QoS | 相对可控 | 有限 | 有限 |

## 2 标准化要点

LTE ProSe（Proximity Services，自 R12）：直接发现与直接通信，公共安全是重要推手[1]。5G NR Sidelink（R16 起强化，面向 V2X 并可延伸 IoT）：OFDM、HARQ、Mode 1（gNB 调度）与 Mode 2（sensing 自主选资源）；后续发行版增强省电、中继与 RedCap 等方向，以当时 3GPP 文档为准[3][10]。

## 3 发现、模式与干扰

发现耗电：周期信标 vs 网络辅助告知邻居。主动发现利于紧急，被动利于偶发上报[2][4]。

| 模式 | 频谱关系 | 效率 | 干扰 |
|------|----------|------|------|
| 带内 underlay | 与蜂窝复用 |  theoretically 高 | 互干扰难 |
| 带内 overlay | 划出专用 D2D 资源 | 中 | 较低 |
| 带外 | ISM 等 | 视 ISM | 与蜂窝隔离 |

模式选择常看距离与 SINR；功率控制把 D2D 功率压低以保护基站上行[2][5]。短距路径损耗小，相对宏蜂窝上行可显著降功率——具体倍数随距离/频率变，勿写死「200 倍」当普遍定律[5]。

## 4 IoT 用法

本地交换与聚合、覆盖外中继（边缘设备→中继 UE→基站）、应急通信、近距测距辅助。工业侧可用 sidelink 做近距闭环；基站作管理者与备份路径而非每包中转[3][9]。

## 5 局限、挑战与可改进方向

### 1. 发现能耗 vs 时延

**局限**：常听耗电，偶发发现又增首包延迟。
**改进**：业务分级（告警主动/遥测被动）；网络辅助发现；对齐 DRX/唤醒周期[4][10]。

### 2. 密集 D2D 互干扰

**局限**：Mode 2 冲突与 underlay 对蜂窝伤害随密度上升。
**改进**：关键流 Mode 1 预留；地理复用与功率帽；准入控制[2][5]。

### 3. 安全绕过核心网

**局限**：直连易受伪造、窃听、DoS；位置隐私经发现信标泄露。
**改进**：ProSe 安全上下文、临时 ID、覆盖外预共享/证书方案；审计直连策略[1][11]。

### 4. IoT/RedCap 支持仍不均

**局限**：早期 sidelink 画像偏手机/车载，模组与协议配置复杂。
**改进**：跟踪 R17/R18 IoT 向增强；工厂场景做专用频谱规划与失败回退蜂窝[3][10][12]。

## 参考文献

[1] 3GPP TR 22.803, Proximity Services feasibility.
[2] A. Asadi et al., "A Survey on Device-to-Device Communication in Cellular Networks," IEEE ComST, 2014.
[3] 3GPP TS 38.331 / sidelink-related NR specs (Release 16+).
[4] G. Fodor et al., "Design Aspects of Network Assisted D2D," IEEE Communications Magazine, 2012.
[5] L. Wei et al., "D2D Communications in 5G Cellular Networks," IEEE Network, 2015.
[6] 3GPP ProSe security architecture documents.
[7] Resource allocation Mode 1/Mode 2 analyses for NR sidelink.
[8] V2X sidelink tutorials (mechanism reuse for IoT caution notes).
[9] Industrial wireless control latency requirements vs sidelink mini-slot discussions.
[10] 3GPP Release 17/18 sidelink / RedCap enhancement overviews.
[11] Privacy issues in proximity discovery literature.
[12] UE relay / coverage extension studies for mMTC.
