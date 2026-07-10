---
schema_version: '1.0'
id: dect-2020-nr-plus-iot
title: DECT-2020 NR+非蜂窝5G IoT标准
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - dect-2020-nr
  - frequency-band-regulation-iot
tags:
- DECT-2020
- NR+
- IMT-2020
- Mesh
- 1.9GHz
- 非蜂窝5G
- Nordic
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# DECT-2020 NR+非蜂窝5G IoT标准

> **难度**：🔴 高级 | **领域**：非蜂窝 5G、工业/园区 IoT | **阅读时间**：约 22 分钟

## 日常类比

小区对讲若事事经运营商专线，审批与月费都重。若无绳电话能直连并互相中继，就更像「自建对讲网」。DECT-2020 NR+（New Radio Plus）把传统 DECT（Digital Enhanced Cordless Telecommunications）专用频段思路升级为现代 OFDM Mesh：无 SIM、无蜂窝核心网，却在 ITU IMT-2020 框架下获得非蜂窝 5G 技术族身份[1][3]。

## 摘要

对比专用 1.9 GHz 相对 ISM/授权频谱的利弊，概述 PHY/MAC/Mesh 与 Nordic 双模芯片路径。峰值速率、单跳距离与「亚毫秒」须对照 ETSI TS 103 636 与实测，避免把目标值当保证 SLA[1][2][5]。

## 1 频谱为何特殊

传统 DECT 语音设备体量巨大；多数地区为 DECT 预留约 1880–1900 MHz（北美等略有偏移）。相对 2.4 GHz ISM：干扰源更少；相对 Sub-GHz ISM：常无严格占空比天花板，但传播不如更低频段「穿得远」[4][7]。

| 维 | DECT 约 1.9 GHz | Sub-GHz ISM | 2.4 GHz ISM | 授权蜂窝 |
|----|-----------------|-------------|-------------|----------|
| 干扰 | 专用倾向，相对干净 | 视当地占用 | WiFi/BLE 拥挤 | 运营商隔离 |
| 许可费 | 通常免许可使用 | 免许可 | 免许可 | 高 |
| 占空比 | 通常无 ISM 式严限 | 欧洲等常有 | 一般无 | 无 |
| 运维模式 | 企业自运营 Mesh | 自运营 | 自运营 | 订阅 |

## 2 技术要点

PHY：OFDM，信道带宽约 1.728 MHz 量级；子载波间隔可配置（覆盖优先 / 速率优先 numerology）；MCS 从稳健到更高阶 QAM，单载波峰值约 Mbps 量级（多载波绑定更高，以规范与芯片为准）[1][5]。

MAC：TDMA/FDMA 混合本地调度。网络：去中心 Mesh，节点可中继、自愈；跳数增加延迟与失败率，工业控制应限制跳数[1][5]。汇聚层适配传感、音频、控制等不同流量轮廓。

| 场景 | 为何考虑 NR+ | 留意点 |
|------|--------------|--------|
| 工厂传感 | 无月费、专用频段 | 芯片生态仍窄 |
| 智能建筑 | Mesh 覆盖楼层 | 与 WiFi/KNX 运维叠加 |
| 专业音频 | 低时延传统优势域 | 需厂商互操作验证 |
| 仓内 AGV/传感 | 少布 AP | 金属货架信道实测 |

## 3 芯片与部署经济

Nordic nRF9161 等将 DECT NR+ 与 LTE-M/NB-IoT 放同 SiP，便于「局域 Mesh + 蜂窝回传」[2][10]。相对私有 5G：免频谱租赁与核心网，但峰值与生态不同；相对公网蜂窝：无每设备订阅，但无广域运营商覆盖[4][8]。

成本对比中的「每设备每月 × N」仅为示意账，合同价差异大，应用 TCO 模型单列[8]。

## 4 局限、挑战与可改进方向

### 1. 供应链与互操作早期

**局限**：可选硅片少，栈与认证仍在成熟中。
**改进**：PoC 绑定单一芯片商 SDK；要求 DECT Forum 互操作测试记录；关键项目保留蜂窝/有线回退[2][4]。

### 2. 与 LoRa / Thread / 私有 5G 定位重叠叙事

**局限**：市场教育成本高，「DECT=无绳电话」刻板印象。
**改进**：用速率–距离–运维三角图选型；只在「中速 + 免运营商 + Mesh」交集立项[5][8]。

### 3. Mesh 跳数与确定性

**局限**：多跳后延迟/抖动上升，URLLC 式指标不能默认端到端成立。
**改进**：控制平面限制跳数；时延敏感流固定骨干节点；实验室按跳数测 P99[1][5][9]。

### 4. 区域频段差异

**局限**：北美等载波规划与欧亚不完全相同，全球 SKU 复杂。
**改进**：分区认证与载波表；硬件预留频偏校准[1][7]。

## 参考文献

[1] ETSI TS 103 636 (Parts 1–4+), "DECT-2020 New Radio," ETSI.
[2] Nordic Semiconductor, "nRF9161 Product Specification," and nRF Connect SDK DECT NR+ docs.
[3] ITU-R M.2150, "Detailed specifications of the radio interfaces of IMT-2020."
[4] DECT Forum, DECT-2020 NR+ technology introductions / white papers.
[5] S. Betz et al. (and related), IEEE Communications Magazine treatments of DECT-2020 NR.
[6] ETSI TR 103 636-1, DECT-2020 NR overview.
[7] National frequency allocation tables for DECT bands (EU/US/Asia differences).
[8] Private 5G vs unlicensed/lightly licensed IoT TCO comparisons.
[9] Industrial wireless latency/reliability measurement methodologies.
[10] Nordic dual-mode (cellular + DECT NR+) application notes.
[11] OFDM numerology design notes analogous to 5G NR (educational contrast).
[12] Wirepas / audio vendor ecosystem notes around DECT Forum membership.
