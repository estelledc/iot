---
schema_version: '1.0'
id: satellite-direct-to-device-nbiot
title: 卫星直连设备NTN NB-IoT技术分析
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - nbiot-coverage-enhancement-repetition
  - satellite-iot
tags:
  - NTN
  - NB-IoT
  - 卫星直连
  - 多普勒预补偿
  - 定时提前
  - LEO
  - 3GPP Rel-17
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 卫星直连设备NTN NB-IoT技术分析

> **难度**：🔴 高级 | **领域**：卫星直连IoT | **阅读时间**：约 18 分钟

## 日常类比

包裹在城市用窄带物联网（NB-IoT）基站报位置，出海后基站消失。若同一模组固件升级后就能连天上卫星继续上报，则无需换芯片换天线。第三代合作伙伴计划（3GPP）非地面网络（Non-Terrestrial Network, NTN）正把蜂窝物联网协议延伸到卫星[1][2]。

## 摘要

Release 17 起标准化物联网 NTN（NB-IoT/增强机器类通信）。相对地面，须处理大传播时延、低地球轨道（LEO）多普勒与大小区差分。终端用全球导航卫星系统（GNSS）位置与星历做定时/频率预补偿。链路余量与功耗倍数为示例预算，**随轨道、频段、天线与重复次数变化**[2][3]。

## 1. 挑战与适配

| 问题 | 量级直觉 | 协议影响 |
|------|----------|----------|
| 传播时延 | LEO 往返可达数十 ms 叙事；地球同步轨道更大 | 定时提前（TA）、混合自动重传请求（HARQ）窗口 |
| 多普勒 | S 波段可达数十 kHz 量级 | 须预补偿，否则偏离子载波 |
| 大小区 | 波束覆盖可达数百 km | 差分时延/多普勒、随机接入资源 |

设备根据 GNSS 与星历估算距离与径向速度，发射时预留 TA 并偏移载波；残余须落在循环前缀与接收机容忍内[1][2]。HARQ/随机接入窗口扩展；架构上透明转发（弯管，基带在地面）常见，再生载荷（星上基站功能）为演进方向。

## 2. 轨道、频段与链路

| 轨道叙事 | 高度 | RTT 直觉 | 多普勒 |
|----------|------|----------|--------|
| LEO ~600 km | 低 | 相对较低 | 高、变化快 |
| 更高 LEO | 中 | 更大 | 中 |
| GEO | ~36000 km | 很大 | 相对低 |

物联网 NTN 常用与地面接近的 S 波段叙事，便于复用射频设计。NB-IoT 窄带、重复传输与低速率有助于关闭长距链路；示例上行预算在 23 dBm 终端 + 高增益卫星天线下可出现数 dB 余量叙事——**不可当作通用保证**[3]。

## 3. 功耗、芯片与场景

相对纯地面，NTN 常需 GNSS 定位与更多重复，日均电量可高数倍量级；仍可能用大电池支撑数年，取决于上报周期[3]。芯片需更大频率/定时补偿范围与星历处理；厂商发布 NTN 能力以数据手册为准。

典型：远洋段切卫星、靠港切地面；偏远农牧；海上浮标；灾后备用。商用节奏依赖频谱协调、星地干扰管理、漫游计费与认证，进度因运营商与星座而异。

## 4. 局限、挑战与可改进方向

### 1. GNSS 依赖与室内失效

**局限**：预补偿依赖定位与星历，遮挡下难附着[2]。
**改进**：辅助 GNSS、星历缓存、过顶窗口调度；室内仍走地面。

### 2. 功耗上升

**局限**：GNSS + 重复使电池寿命短于地面叙事。
**改进**：降上报频率；热启动；深度休眠；仅无覆盖时启用 NTN。

### 3. 透明转发对馈电依赖

**局限**：弯管需馈电链路与关口站几何配合。
**改进**：选有关口站规划的服务；关注再生载荷路线图。

### 4. 监管与商业分成

**局限**：频谱与漫游协议未统一则难全球一张网。
**改进**：按航线/国家清单采购连接；合同写清 NTN 与地面切换策略。

## 5. 实践要点

1. 先确认模组宣称的 3GPP NTN 版本与频段认证。
2. 链路预算按最差仰角与最大多普勒做，不按天顶理想值。
3. 双模策略：有地面用地面，卫星作补盲与灾备。

## 参考文献

[1] 3GPP TS 36.331 / IoT NTN related specifications, Release 17+.
[2] 3GPP TR 36.763, Study on NB-IoT/eMTC support for NTN.
[3] Liberg, O. et al., "Satellite NB-IoT: Design and Analysis," IEEE Trans. Veh. Technol. (or equivalent peer-reviewed NTN IoT analyses).
[4] Lin, X. et al., "5G New Radio Evolution Meets Satellite Communications," IEEE Commun. Mag./Standards Mag.
[5] Qualcomm / MediaTek / Altair NTN IoT product briefs (vendor-specific).
[6] 3GPP TR 38.811, NR to support NTN study.
[7] ITU/3GPP materials on S-band NTN frequency arrangements.
[8] Skylo and MNO–satellite partnership public overviews (commercial, non-normative).
[9] GNSS-assisted TA and Doppler pre-compensation application notes.
[10] NB-IoT coverage enhancement / repetition specifications.
[11] Transparent vs regenerative NTN architecture discussions in 3GPP/industry.
