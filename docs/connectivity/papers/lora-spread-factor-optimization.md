---
schema_version: '1.0'
id: lora-spread-factor-optimization
title: LoRa扩频因子SF优化与链路预算计算
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - link-budget-calculation-lpwan
tags:
  - LoRa
  - 扩频因子
  - 链路预算
  - CSS
  - 空中时间
  - ADR
  - 占空比
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LoRa扩频因子SF优化与链路预算计算

> **难度**：🟡 中级 | **领域**：LoRa物理层 | **阅读时间**：约 18 分钟

## 日常类比

山谷里喊话：快说一句传得近、信息多；把字拖长则传得远、耗时长。LoRa 扩频因子（Spreading Factor, SF）就是“拖长”程度——SF 越高，灵敏度越好、速率越低、空中时间（Time on Air, ToA）越长[1][2]。

## 摘要

本文说明啁啾扩频（Chirp Spread Spectrum, CSS）、SF/带宽（Bandwidth, BW）/编码率（Coding Rate, CR）权衡、链路预算与自适应数据速率（Adaptive Data Rate, ADR）选型逻辑。灵敏度、速率与覆盖数字多来自芯片手册与区域参数，**实地路径损耗与干扰会使可用距离显著短于自由空间估算**[2][5]。

## 1. CSS 与 SF

LoRa 用线性调频啁啾编码符号；每符号含 \(2^{\mathrm{SF}}\) 个 chip，chip 速率等于 BW。SF 常用 7–12（区域参数另有约束）[1][5]。

| SF | 符号时间（BW=125 kHz） | 相对 SF7 |
|----|------------------------|----------|
| 7 | 约 1.0 ms | 1× |
| 9 | 约 4.1 ms | 4× |
| 12 | 约 32.8 ms | 32× |

不同 SF 近似准正交：同信道可并发，但隔离度有限，强信号仍可压制弱信号[4][6]。

## 2. 灵敏度、速率与 ToA

接收灵敏度随 SF 升高而改善（量级约每级数 dB，具体以芯片手册为准）[2]。比特率近似：

\[
R_b \approx \mathrm{SF}\cdot\frac{\mathrm{BW}}{2^{\mathrm{SF}}}\cdot\mathrm{CR}
\]

| SF（BW=125 kHz, CR=4/5） | 比特率量级 | 相对 SF7 |
|--------------------------|------------|----------|
| 7 | 约数 kbps | 基准 |
| 10 | 约 1 kbps | 约 1/5 |
| 12 | 约数百 bps | 约 1/20 |

同等有效载荷下，SF12 的 ToA 可比 SF7 长一个数量级以上，直接抬高功耗、占空比占用与碰撞概率[3][4]。

## 3. 链路预算

\[
P_{\mathrm{rx}} = P_{\mathrm{tx}} + G_{\mathrm{tx}} + G_{\mathrm{rx}} - L_{\mathrm{path}} - L_{\mathrm{extra}}
\]

可靠条件：\(P_{\mathrm{rx}} \ge S_{\mathrm{rx}} + M_{\mathrm{fade}}\)。路径损耗常用对数距离模型；城市指数常高于自由空间，穿墙与线缆损耗需单独计入[3][7]。

| 项 | 典型量级（需实测校准） | 说明 |
|----|------------------------|------|
| 终端 EIRP | 区域法规上限内 | 如 EU868/CN470 限制不同[5] |
| 网关天线增益 | 数 dBi 量级 | 高度往往比增益更关键 |
| 衰落余量 | 数–十余 dB | 室内外差异大 |

**规划结论应写“在给定模型与余量下的可用 SF”，而非绝对公里数。**

## 4. BW、CR 与占空比

| 参数 | 提高时 | 代价 |
|------|--------|------|
| BW↑ | 速率↑ | 噪声带宽↑、灵敏度↓ |
| CR 冗余↑ | 纠错↑ | 有效吞吐↓、ToA↑ |
| SF↑ | 灵敏度↑ | ToA↑、容量↓ |

欧盟等区域对子频段有占空比限制；高 SF 会显著压缩每小时可发次数。载荷宜用紧凑二进制，避免冗长文本[5][8]。

## 5. 优化策略与 ADR

原则：**在可靠前提下用最低 SF**。静止/慢变链路可由网络侧 ADR 据信噪比（Signal-to-Noise Ratio, SNR）历史下调 SF 或功率；快速移动、室内外突变场景应固定保守参数或缩短历史窗[8][9]。

容量规划需同时计入多信道、SF 准正交与碰撞重传；公开“单网关数千设备”叙事高度依赖上报周期与 SF 分布，**不可直接当 SLA**[4][10]。

## 6. 局限、挑战与可改进方向

### 1. 模型与实地偏差

**局限**：自由空间/单一路径指数低估城市与室内衰减。
**改进**：用路测 RSSI/SNR 校准 \(n\) 与余量；关键点做双向连通验证。

### 2. ADR 滞后与移动性

**局限**：基于历史 SNR 的 ADR 跟不上快速位移。
**改进**：移动终端禁用 ADR；或缩短窗并加大 margin。

### 3. 准正交不完美

**局限**：同 SF 碰撞与近远效应仍会丢包。
**改进**：加密网关、优化 ADR 使 SF 分布左移；控制确认帧比例。

### 4. 占空比与下行不对称

**局限**：高 SF 吃满占空比后几乎无法再发；下行更稀缺。
**改进**：减载荷、降上报频率；FUOTA 等大下行另做专项设计。

## 7. 实践要点

1. 先定区域参数与法规功率，再算链路与 ToA。
2. 规划用保守余量；上线后靠 ADR/路测收敛。
3. 监控 SF 分布与丢包，而非只看覆盖半径宣传值。

## 参考文献

[1] Semtech, "LoRa Modulation Basics," AN1200.22.
[2] Semtech, SX1276/77/78/79 Datasheet.
[3] Augustin, A. et al., "A Study of LoRa," Sensors, 2016.
[4] Bor, M. et al., "Do LoRa Low-Power Wide-Area Networks Scale?," ACM MSWiM, 2016.
[5] LoRa Alliance, LoRaWAN Regional Parameters (RP002 series).
[6] Mahmood, A. et al., "Scalability Analysis under Imperfect Orthogonality," IEEE TII, 2019.
[7] ITU-R / common log-distance path-loss models for outdoor IoT planning.
[8] LoRa Alliance, LoRaWAN Specification v1.0.4 / v1.1 (ADR related).
[9] ChirpStack / TTN documentation on Adaptive Data Rate.
[10] Adelantado, F. et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[11] Semtech application notes on time-on-air calculation.
