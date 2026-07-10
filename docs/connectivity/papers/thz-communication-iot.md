---
schema_version: '1.0'
id: thz-communication-iot
title: 太赫兹通信在 IoT 中的前景
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - terahertz-communication-future-iot
tags:
  - 太赫兹
  - 纳米物联网
  - WNoC
  - 石墨烯
  - 数据中心
  - 分子吸收
  - Sub-THz
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 太赫兹通信在 IoT 中的前景

> **难度**：🟡 中级 | **领域**：无线通信、纳米技术 | **阅读时间**：约 18 分钟

## 日常类比

频谱像公路：2.4 GHz 像拥堵普通道；毫米波像快速道；太赫兹（0.1–10 THz）像超宽但未铺好的路，水分子沿途设卡（分子吸收）。多数传感器不需要 Tbps；价值更在**纳米物联网**（天线做进微米器件）与**米级超高速互连**（机架/芯片间）[1][3]。

## 摘要

聚焦传输窗口、器件路线、纳米网络、无线片上网络（Wireless Network-on-Chip, WNoC）与数据中心链路，并给出商用阶段判断。功率、Gbps 与衰减表为文献/试验**量级**，湿度与工艺差会改变数量级[2][5]。与姊妹文《太赫兹通信在未来IoT中的潜力与挑战》互补：本文偏器件与垂直场景，彼文偏 6G/ISAC 总览。

## 1. 频段与大气窗

| 频段 | 频率量级 | 带宽叙事 | 大气衰减叙事 |
|------|----------|----------|--------------|
| Sub-6 | GHz 级 | 百 MHz | 很低 |
| mmWave | 24–71 GHz | GHz 级 | 低到中 |
| Sub-THz | 100–300 GHz | 数十 GHz | 中到高 |
| THz | 0.3–10 THz | 窗口内仍宽 | 高到极高 |

吸收线之间存在窗口（如约 140/220/340 GHz 等叙事）：数米内或可用，更高频常缩到米内甚至厘米——反而贴合纳米与片上距离[2][3]。精确系数应查 ITU-R / HITRAN，而非口算拟合[10]。

## 2. 器件路线

- **电子学**：基频倍频；频率升则功率常降至 μW 级。
- **光子学**：双激光差频驱动光电导天线；功率可观但体积与成本高。
- **QCL**：1–5 THz 可较高功率，常需低温；室温仍是难题[5]。

石墨烯：高迁移率、栅压可调、天线可缩至 μm 量级——多为实验室演示（噪声等效功率、调制带宽等指标随论文变化）[4][6]。

## 3. 纳米物联网

1 THz 波长约 300 μm，半波偶极约 150 μm；等离子体天线可更短。协议须极简帧、洪泛/短跳，TCP/IP 不适用。体内、土壤、结构健康监测是常见场景叙事，功耗常要求 nW–μW 预算[1][3][7]。

## 4. WNoC 与数据中心

片上金属线延迟、功耗与布线拥塞推动 WNoC：集群内有线、集群间 THz 无线。芯片内无大气吸收，距离毫米级；速率/功耗数字以流片论文为准[4]。

机架顶互连：1–2 m 级、100 Gbps 叙事的 Sub-THz/THz 试验见诸报道；对准与成本是门槛[5][8]。

| 指标 | ~60 GHz | ~140 GHz | ~300 GHz |
|------|---------|----------|----------|
| 带宽 | 约 9 GHz 级 | 约 20 GHz 级 | 更宽 |
| 距离 | 更远 | 中 | 更短 |
| 器件成本 | 相对低 | 中 | 高 |
| 产品化 | WiGig 等 | 原型 | 实验室为主 |

## 5. 局限、挑战与可改进方向

### 1. 发射功率与噪声系数不够

**局限**：链路预算撑不起目标距离×带宽。
**改进**：InP/SiGe 混合；降阶调制；先做固定对准链路[5][9]。

### 2. 窄波束 MAC 失效

**局限**：经典载波侦听“听不到”其他方向。
**改进**：调度式接入、波束训练协议、位置辅助预约[9]。

### 3. 纳米能量与安全

**局限**：nJ 级能量与广播洪泛并存。
**改进**：脉冲极低占空比；能量收集；物理层认证研究[3][7]。

### 4. 时间线过度承诺

**局限**：把实验室 Gbps 写成明年 IoT 标配。
**改进**：分阶段：Sub-THz 回程 → 机架/热点 → 纳米试验床[8][10]。

## 6. 入门路径（压缩）

读清窗口与法规频段 → 用公开吸收数据做链路预算 → ns-3/TeraSim 类仿真纳米场景 → 再读 Schottky/InP 器件综述。研究方向：信道近场效应、THz MAC、与能量收集联合设计[1][9]。

## 参考文献

[1] I. F. Akyildiz et al., TeraNets, IEEE Wireless Communications, 2014.
[2] T. Kürner and S. Priebe, Towards THz communications, J. Infrared Milli Terahz Waves, 2014.
[3] J. M. Jornet and I. F. Akyildiz, Channel modeling for THz nanonetworks, IEEE TWC, 2011.
[4] S. Abadal et al., Graphene-enabled wireless for multicore, IEEE Comm. Mag., 2013.
[5] H.-J. Song and T. Nagatsuma, Present and future of terahertz communications, IEEE T-TST, 2011.
[6] A. Llatser et al., Graphene-based nano-patch antenna for THz, Photonics and Nanostructures, 2012.
[7] C. Han et al., Multi-wideband THz for body-centric nano-communications, IEEE JSAC, 2021.
[8] V. Petrov et al., IEEE 802.15.3d standardization toward 6G, IEEE Comm. Mag., 2020.
[9] Z. Hossain et al., Stochastic interference for pulse-based THz, IEEE TWC, 2019.
[10] ITU-R / WRC materials on frequencies above 100 GHz; HITRAN for absorption lines.
[11] WNoC and data-center wireless interconnect experimental reports (treat link rates as demo-specific).
