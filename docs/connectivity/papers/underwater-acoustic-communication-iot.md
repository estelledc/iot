---
schema_version: '1.0'
id: underwater-acoustic-communication-iot
title: 水下声学通信在海洋IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites: UNKNOWN
tags:
  - 水下声学
  - 海洋物联网
  - UWSN
  - 调制解调
  - 多径
  - AUV
  - 链路预算
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 水下声学通信在海洋IoT中的应用

> **难度**：🔴 高级 | **领域**：水下通信 | **阅读时间**：约 18 分钟

## 日常类比

泳池里喊话，几米外还能听见模糊声；手机 Wi-Fi 隔一厘米水就断。海水中电磁波趋肤深度在微波段可到毫米级，而声波能传百米到数十公里——水下声学通信（Underwater Acoustic Communication, UAC）因此成为中远距海洋物联网几乎唯一实用无线手段[1][2]。

## 摘要

对比射频/光学，梳理声速剖面、吸收、多径与多普勒，以及调制、介质访问控制（MAC）、能量与商用调制解调器量级。速率 kbps、距离 km 为产品/海试**量级**，浅海与深海差一个数量级都常见[1][4]。

## 1. 为何是声学

| 参数 | 射频（海水） | 声学 |
|------|--------------|------|
| 速度 | ~3×10⁸ m/s | ~1500 m/s |
| 1 km 时延 | μs 级 | ~0.67 s |
| 带宽 | 理论高但不可用 | 常 kHz–数十 kHz |
| 多径扩展 | 小 | ms–数十 ms |
| 多普勒 | 常可忽略 | v/c 不可忽略 |

光学可在清水短距高速，需对准；极低频电磁可远但速率极低。声学是折衷主力[2][5]。

## 2. 信道要点

声速随温度、盐度、深度变；最小值附近可形成声道，能量可沿轴传很远。传播损耗含扩散项与频率相关吸收：低频走得远但窄带，高频带宽大但衰减快[1]。

多径来自海面/海底反射与折射；浅海延迟扩展可达数十 ms，使高速单载波符号间干扰极重，需均衡或 OFDM 等[1][4]。噪声随航运与海况变化大。

## 3. 调制与设备

| 方式 | 速率量级 | 距离叙事 | 特点 |
|------|----------|----------|------|
| FSK | 百–千 bps | 更远 | 稳健、对多普勒较不敏感 |
| PSK/QAM | kbps–数十 kbps | 中距 | 需均衡 |
| OFDM | kbps–更高 | 较短 | 抗多径，怕多普勒 |
| DSSS | 低速率 | 视设计 | 抗干扰/多址 |

换能器多为压电陶瓷；发射功耗可达瓦–数十瓦，往往主导能耗。商用例如 EvoLogics、Teledyne、WHOI Micromodem、Blueprint 等，规格以数据手册为准[4][8]。

## 4. 网络与能量

长传播时延使载波侦听冲突避免效率极低；TDMA、握手类、短探测脉冲协议更常见。路由须处理三维、节点漂移与“靠近浮标能量空洞”[2][3]。

| 状态 | 功耗量级（示意） |
|------|------------------|
| 待机 | mW 以下–mW |
| 接收/传感 | mW–数十 mW |
| 发射 | 常 W 级 |

故策略是：深睡眠、本地压缩、短距多跳、自主水下航行器（AUV）数据骡近距卸载[3][5]。

## 5. 局限、挑战与可改进方向

### 1. 时延使交互协议失效

**局限**：TCP 式端到端确认吞吐崩溃。
**改进**：大窗口/否定确认、束协议、应用层聚合[2][4]。

### 2. 发射能耗占比过高

**局限**：电池月～年寿命高度依赖上报频率。
**改进**：事件触发；中继缩短单跳；波浪/温差收集作补充[3]。

### 3. 海况非平稳

**局限**：同调制白天可用、风暴失效。
**改进**：自适应调制编码；海况传感器联动降速[1]。

### 4. 单浮标单点

**局限**：网关丢失则整片离线。
**改进**：多浮标；声学+卫星冗余；定期 AUV 巡游[5]。

## 6. 实践要点

1. 先定距离–带宽–功耗三角形，再选频段与调制。
2. 浅海必须按多径扩展设计均衡/保护间隔。
3. 验收在目标海况做海试，不轻信水池数据。
4. 定位（LBL/USBL 等）与通信常共享声学资源，调度要统一[4]。

## 参考文献

[1] M. Stojanovic and J. Preisig, Underwater acoustic communication channels, IEEE Comm. Mag., 2009.
[2] I. F. Akyildiz, D. Pompili, T. Melodia, Underwater acoustic sensor networks: research challenges, Ad Hoc Networks, 2005.
[3] J. Heidemann et al., Underwater sensor networks: applications, advances and challenges, Phil. Trans. R. Soc. A, 2012.
[4] M. Chitre, S. Shahabudeen, M. Stojanovic, Underwater acoustic communications and networking, MTS Journal, 2008.
[5] M. C. Domingo, An overview of the Internet of Underwater Things, JNCA, 2012.
[6] Urick, Principles of Underwater Sound (classic reference on propagation/noise).
[7] WHOI Micromodem and related acoustic modem technical documentation.
[8] EvoLogics / Teledyne / Blueprint acoustic modem datasheets (vendor specs).
[9] VBF / DBR underwater routing protocol literature.
[10] OFDM underwater acoustic communication survey papers.
[11] AUV data muling and multimodal acoustic–optical transfer studies.
