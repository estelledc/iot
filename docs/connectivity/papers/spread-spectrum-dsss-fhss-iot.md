---
schema_version: '1.0'
id: spread-spectrum-dsss-fhss-iot
title: 扩频技术DSSS/FHSS在IoT抗干扰中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - spread-spectrum-dsss-fhss
tags:
  - DSSS
  - FHSS
  - 扩频
  - 抗干扰
  - Zigbee
  - Bluetooth
  - 处理增益
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 扩频技术DSSS/FHSS在IoT抗干扰中的应用

> **难度**：🟡 中级 | **领域**：扩频通信 | **阅读时间**：约 14 分钟

## 日常类比

火车站用“暗语节奏”说话：旁人听不懂，熟人能抠出内容——直接序列扩频（Direct Sequence Spread Spectrum, DSSS）像把每个字换成固定节奏码片；跳频扩频（Frequency Hopping Spread Spectrum, FHSS）像约定换柱子说话，躲开固定噪声源。物联网（IoT）在拥挤 ISM 频段靠它们换抗干扰与共存能力[1][2]。

## 摘要

处理增益（Processing Gain）≈ 扩频带宽/数据带宽。Zigbee/802.15.4、经典 802.11b 偏 DSSS；蓝牙偏 FHSS/自适应跳频（Adaptive Frequency Hopping, AFH）；LoRa 用啁啾扩频（Chirp Spread Spectrum, CSS）属另一家族。增益与占空比、法规、灵敏度叙事绑定，**不可把理论 dB 直接当现场余量**[3][4]。

## 1. 协议侧地图

| 协议/技术 | 扩频类型 | 频段叙事 | IoT 用途 |
|-----------|----------|----------|----------|
| Zigbee / 802.15.4 | DSSS | 2.4 GHz 等 | Mesh 传感/灯控 |
| Bluetooth LE/BR | FHSS/AFH | 2.4 GHz | 穿戴、外设 |
| 802.11b（历史） | DSSS | 2.4 GHz | 对照 |
| WirelessHART | FHSS+TDMA | 2.4 GHz | 工业 |
| LoRa | CSS | Sub-GHz 等 | LPWAN |

## 2. DSSS 应用要点

每位数据乘高速伪随机码片；接收端相关解扩：期望信号收拢，窄带干扰被摊薄。Zigbee 2.4 GHz 使用规定码片映射与 O-QPSK 等，处理增益约数 dB 到十余 dB 量级（视码片长度与速率）[3][5]。

| 机制 | 作用 |
|------|------|
| 码片相关 | 抑制非匹配干扰 |
| 多码/信道 | 区分网络与共存 |
| 重传/CSMA | MAC 层再扛残余冲突 |

## 3. FHSS 应用要点

按跳频序列在多信道间切换；窄带干扰只打中部分驻留。蓝牙 AFH 可剔除被 Wi-Fi 占满的信道。工业 FHSS 常叠加时隙，换确定性[2][6]。

| 对比 | DSSS | FHSS |
|------|------|------|
| 抗窄带干扰 | 靠处理增益稀释 | 靠躲避信道 |
| 同步要求 | 码相位同步 | 跳频图样同步 |
| 瞬时带宽 | 常较宽 | 单跳可较窄 |
| 典型 IoT | 802.15.4 | 蓝牙/部分工业 |

## 4. 局限、挑战与可改进方向

### 1. 增益被宽带干扰吃掉

**局限**：Wi-Fi 类宽带干扰覆盖多信道时，DSSS/FHSS 收益下降。
**改进**：信道规划、降占空比、空间隔离；必要时跳 Sub-GHz。

### 2. 同步失败即整链失效

**局限**：时钟漂移、漏跳导致长时间失锁。
**改进**：定期重同步；看门狗与降级信道；工业用有线时间基准。

### 3. 把理论 PG 当链路余量

**局限**：忽略实现损失、邻道与功放非线性。
**改进**：用 PER/RSSI 实地标定；链路预算留实现余量。

### 4. 多技术同箱互扰

**局限**：一板多射频时，跳频与 DSSS 仍可能自干扰。
**改进**：天线隔离、时分发射、AFH 黑名单共享。

## 5. 实践要点

1. 先分清干扰是窄带还是宽带，再选 DSSS/FHSS/CSS。
2. 蓝牙与 Wi-Fi 共存优先开 AFH 并固定 Wi-Fi 信道。
3. 原理细节见同目录 `spread-spectrum-dsss-fhss` 文。

## 参考文献

[1] Peterson, R. L. et al., Introduction to Spread-Spectrum Communications.
[2] Bluetooth SIG, Core Specification (AFH / hopping).
[3] IEEE 802.15.4 standard (DSSS PHY).
[4] Semtech LoRa modulation resources (CSS contrast).
[5] Zigbee Alliance / CSA PHY-MAC overview materials.
[6] IEC 62591 WirelessHART related materials.
[7] Torrieri, D., Principles of Spread-Spectrum Communication Systems.
[8] IEEE 802.11b DSSS historical PHY clauses.
[9] FCC Part 15.247 hopping / digital modulation rules (US context).
[10] Rappaport, T. S., Wireless Communications (spread spectrum chapters).
[11] Coexistence studies: Wi-Fi / Zigbee / Bluetooth in 2.4 GHz (survey papers).
