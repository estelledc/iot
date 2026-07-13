---
schema_version: '1.0'
id: ble-5-features-coded-phy
title: BLE 5.0新特性：Coded PHY与远距离通信
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - ble-connection-parameter-optimization
  - link-budget-calculation-lpwan
tags:
  - BLE
  - Coded PHY
  - LE 2M
  - 扩展广播
  - FEC
  - 远距离
  - Bluetooth 5
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# BLE 5.0新特性：Coded PHY与远距离通信

> **难度**：🟡 中级 | **领域**：BLE协议演进 | **阅读时间**：约 20 分钟

## 日常类比

足球场一端喊话：正常说（1M 物理层）近处才清；大声（编码物理层 S=2）更远但费劲；扩音器反复同一句（S=8）全场可懂，但一句说完更久。蓝牙低功耗（Bluetooth Low Energy, BLE）5.0 的编码物理层（Coded PHY）用前向纠错（Forward Error Correction, FEC）换距离[1][3]。

## 摘要

解析 BLE 5 多物理层（PHY）、Coded PHY 卷积编码与模式映射、链路预算、2M PHY 与扩展广播，并给出选型权衡。距离与灵敏度表为芯片/外场量级示意，**依赖天线、功率与环境**[2][4]。

## 1 PHY 一览

蓝牙技术联盟（Bluetooth SIG）Core 5.0（2016）相对 4.2 在速度、距离、广播容量上扩展[1]。

| PHY | 符号速率 | 有效吞吐量级 | 优势 |
|-----|----------|--------------|------|
| LE 1M | 1 Msym/s | 约数百 kbps | 兼容 4.x |
| LE 2M | 2 Msym/s | 约 Mbps 量级 | 更快、空中时间更短 |
| Coded S=2 | 1 Msym/s | 500 kbps | 约 +6 dB 链路预算 |
| Coded S=8 | 1 Msym/s | 125 kbps | 约 +12 dB 链路预算 |

宣传语“2× speed / 4× range / 8× advertising”指理想条件相对基线，非任意场景保证[3]。

## 2 Coded PHY 机制

流程：比特 → rate-1/2 卷积编码（约束长度 K=4）→ 模式映射（S=2/S=8）→ 空中符号。前导、编码指示（Coding Indicator, CI）、TERM1 固定 S=8，便于可靠检包；CI 指示后续协议数据单元（PDU）用 S=2 或 S=8[1]。

| 参数 | S=2 | S=8 |
|------|-----|-----|
| 有效数据率 | 500 kbps | 125 kbps |
| 链路预算增益（相对 1M，规范/典型） | 约 +6 dB | 约 +12 dB |
| 理论距离（自由空间直觉） | 约 2× | 约 4× |
| 纠错能力 | 中 | 强 |

接收端维特比（Viterbi）最大似然解码；弱信号下少重传，有时反而更省电[1][4]。

## 3 链路预算与实测量级

| PHY | 典型灵敏度量级 | 相对 1M |
|-----|----------------|---------|
| 1M | 约 −96 dBm | 基准 |
| 2M | 约 −93 dBm | 约 −3 dB |
| Coded S=2 | 约 −102 dBm | 约 +6 dB |
| Coded S=8 | 约 −108 dBm | 约 +12 dB |

nRF52840 等 +8 dBm 外场：室外视距 1M 约百米量级、S=8 可达数百米量级；室内穿墙显著缩短——以 PER/RSSI 实测为准[2][4]。

## 4 2M 与扩展广播

2M 缩短空中时间 → 吞吐↑、碰撞窗↓、射频开启时间↓；适合音频、固件升级、高频传感。代价：灵敏度略差、无 Coded FEC、4.x 不兼容[1]。

扩展广播：主信道 ADV_EXT_IND 指向数据信道辅助 PDU（单包最多 255 字节，可链式）；支持多广播集与周期广播同步省电[1]。

## 5 硬件与选型

| 芯片 | 1M/2M | Coded | Ext Adv |
|------|-------|-------|---------|
| nRF52840/5340 | Y | Y | Y |
| CC2652R / EFR32BG22 / STM32WB55 | Y | Y | Y |
| ESP32-C3 | Y | 常不支持 Coded | Y |

双方都需支持 Coded；手机端 API 支持参差（Android 部分版本、iOS 不公开 Coded API）[2][5]。决策：最远 → S=8；高吞吐 → 2M；穿墙平衡 → S=2；兼容优先 → 1M。可按 RSSI 自适应切换，但须验证协商与功耗。

## 6 局限、挑战与可改进方向

### 1. 空中时间与共存

**局限**：S=8 单包可长达十余 ms 量级，密集部署碰撞上升[1]。
**改进**：缩短 PDU、提高跳频质量、非必要不用 S=8。

### 2. 手机生态缺口

**局限**：手机作中心时 Coded 不可用或不可控[5]。
**改进**：网关/自研中心跑 Coded；手机链路回退 1M/2M。

### 3. “4 倍距离”被当承诺

**局限**：忽略天线效率、人体遮挡与 Wi-Fi 干扰[2][4]。
**改进**：链路预算 + 现场 PER 热力；预留约 6–10 dB 裕度。

### 4. 芯片特性名不副实

**局限**：标 BLE 5 但不含 Coded[2]。
**改进**：数据手册核对 PHY 矩阵；采购写明强制特性。

## 参考文献

[1] Bluetooth SIG, Bluetooth Core Specification v5.0（及后续维护版本）.
[2] Nordic Semiconductor, nRF52840 Product Specification.
[3] Bluetooth SIG, Bluetooth 5 feature overview.
[4] Nordic, Developing Bluetooth 5 Long Range Applications with nRF Connect SDK.
[5] Android / iOS BLE API 文档（PHY 能力差异）.
[6] M. Afaneh, BLE 5 Long Range — Coded PHY, Novel Bits, 2020.
[7] Bluetooth SIG, Core Specification Supplement（扩展广播 AD 结构）.
[8] TI / Silicon Labs BLE 5 应用笔记（PHY 切换）.
[9] Bluetooth Core v5.4, Vol 6（链路层 PHY 更新）.
[10] Zephyr Bluetooth API：`bt_conn_le_phy_update` 文档.
[11] Gomez et al., Overview and Evaluation of BLE, Sensors, 2012（基线对比）.
