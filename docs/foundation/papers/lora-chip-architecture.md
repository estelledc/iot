---
schema_version: '1.0'
id: lora-chip-architecture
title: LoRa 芯片架构深度解析
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - lora-module-sx1276-register
tags:
  - LoRa
  - CSS
  - SX1262
  - SX1276
  - LPWAN
  - 链路预算
  - Semtech
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# LoRa 芯片架构深度解析

> **难度**：🟡 中级 | **领域**：低功耗广域无线 | **关键词**：LoRa, CSS, SF, SX1262, 链路预算 | **阅读时间**：约 16 分钟

## 日常类比

嘈杂体育场里喊话：短促大喊像高速窄覆盖；LoRa（Long Range）的啁啾扩频（Chirp Spread Spectrum, CSS）像约定好的“滑音口哨”——频率慢慢扫过，接收端按同一模式相关，弱信号也能从噪声里捞出来。芯片就是这套发声/听声硬件[1][3]。

## 摘要

概述 CSS 与扩频因子（Spreading Factor, SF）、SX1276→SX1262 架构演进、链路预算与选型。灵敏度、电流与距离**强烈依赖天线、环境与法规占空比，以手册与实测为准**[1][2][5]。

## 1. CSS 与 SF

信息编码在啁啾起始频率偏移上；SF 越高，符号更长、速率更低、处理增益通常更高，接收更“敏”但空中时间更长[3][8]。

| SF（BW≈125 kHz 语境） | 速率倾向 | 灵敏度倾向 |
|----------------------|----------|------------|
| 7–8 | 较高 | 较弱 |
| 9–10 | 中 | 中 |
| 11–12 | 低 | 较强 |

具体 bps / dBm 数字以 Semtech 数据手册曲线为准，勿把单一表格当全球真理[1][2]。

## 2. 芯片代际

| 项 | SX1276 代 | SX1262 代（典型） |
|----|-----------|-------------------|
| 发射功率上限 | 约 +20 dBm 档 | 可达约 +22 dBm 档 |
| 接收电流 | 约十余 mA 量级 | 常明显更低 |
| 睡眠电流 | μA 量级 | 可到亚 μA / 百 nA 量级 |
| 封装 | 较大 | 更紧凑 |
| 特色 | 生态成熟 | 占空比 RX、集成 DC-DC 等 |

中国频段常见 SX1268 等变体；成本敏感可评估 LLCC68（SF 范围可能受限）；多频/卫星向有 LR11xx 系列——**以当期选型表为准**[1][10]。

## 3. 链路预算与 PA

链路预算粗看：`EIRP + 天线增益 − 路径损耗 − 余量 ≟ 灵敏度需求`。城区、室内穿墙损耗远大于视距农田；水面/视距报告的超长距离不可直接外推[4][5]。

功率放大器（Power Amplifier, PA）与匹配网络决定谐波与效率；认证（ETSI/FCC 等）限制占空比与杂散[6]。

| 芯片族 | 备注 |
|--------|------|
| SX1262/61/68 | Semtech 主流 Sub-GHz |
| LLCC68 | 成本优化变体 |
| 集成 MCU SoC | 如部分 ASR 方案，软硬件一体 |

## 4. 局限、挑战与可改进方向

### 1. 空中时间与占空比

**局限**：高 SF 包很长，法规占空比与网络容量受限。
**改进**：能低 SF 就低；自适应数据速率（ADR）；控制上报频率。

### 2. 同频干扰与碰撞

**局限**：CSS 非正交多用户，网关密集时吞吐下降。
**改进**：信道规划、跳频、合理 SF 分布；容量模型参考研究[4]。

### 3. 手册灵敏度 ≠ 外场距离

**局限**：天线失配、噪声底抬高、人体遮挡导致“差很远”。
**改进**：暗室/外场实测；固定天线与匹配；留链路余量。

### 4. 一代芯片功耗偏高

**局限**：SX1276 接收电流对纽扣电池不友好。
**改进**：新设计优先 SX126x；严格 RX 窗口与休眠策略。

## 5. 实践要点

1. 新项目默认评估 SX1262/1268；维护老模组再深挖 SX1276 寄存器（见姊妹文）。
2. 先跑通点对点再上 LoRaWAN。
3. 距离承诺必须带环境与 SF/BW 条件。

## 参考文献

[1] Semtech, SX1261/62 datasheet.
[2] Semtech, SX1276/77/78/79 datasheet.
[3] Augustin et al., A Study of LoRa, Sensors, 2016.
[4] Bor et al., Do LoRa LPWANs Scale?, MSWiM 2016.
[5] Cattani et al., Experimental evaluation of LoRa reliability, JSAN 2017.
[6] Semtech, LoRa and LoRaWAN technical overview.
[7] Liando et al., Large-scale LoRa measurement study, ACM ToSN.
[8] Seller & Sornin, Low Power Long Range Transmitter patent / CSS 基础.
[9] Mekki et al., LPWAN technologies comparison, ICT Express.
[10] Semtech, LR1121 datasheet.
[11] ETSI / FCC Sub-GHz duty cycle and emission guidance summaries.
