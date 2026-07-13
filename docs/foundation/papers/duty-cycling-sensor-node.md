---
schema_version: '1.0'
id: duty-cycling-sensor-node
title: 传感器节点占空比策略与寿命估算
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - sleep-mode-hierarchy-mcu
  - power-profiler-current-measurement
tags:
  - 占空比
  - 低功耗
  - 电池寿命
  - LoRa
  - RTC唤醒
  - 睡眠电流
  - 能耗估算
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 传感器节点占空比策略与寿命估算

> **难度**：🟡 中级 | **领域**：IoT功耗优化 | **阅读时间**：约 14 分钟

## 日常类比

守仓库不必整夜盯屏：每半小时巡两分钟，其余打盹。占空比（duty cycle）= 活跃时间/周期。纽扣电池温湿度节点往往绝大多数时间在 μA 级睡眠，只在采集与发射的短窗口醒来——间隔与各段电流决定寿命是年计还是月计[1][2]。

## 摘要

```
I_avg ≈ Σ(I_i × T_i) / T_cycle
DC ≪ 1 时 ≈ I_sleep + I_active × DC
```

睡眠是地板，发射常是活跃电量大头。寿命用有效容量而非标称 mAh。文中电流/寿命为演算示意，**必须以 PPK 类仪器实测与电池脉冲能力校验**[3][4]。

## 1. 周期拆解

| 阶段 | 优化杠杆 |
|------|----------|
| Sleep | 最深可行模式、GPIO 漏电、LDO Iq |
| Wake/Setup | 保 RAM 的 Stop 优于冷启动 Standby |
| Sense | 低功耗传感器、低精度快测、批量读 |
| Process | 短路径打包 |
| TX/RX | 功率、空中时间、是否听 ACK |
| Shutdown | 快速进睡 |

LoRa 高功率短脉冲可占活跃电量绝大部分；BLE 短包事件驱动则睡眠电流更常成主导[4][5]。

## 2. 电池与寿命

```
寿命 ≈ C_eff / (I_avg × 小时/年)
C_eff = C_nom × 温度 × 自放电 × 截止电压等因子
```

| 常见坑 | 后果 |
|--------|------|
| 用标称容量 | 高估寿命 |
| 忽略 LDO Iq | 睡眠电流被抬高数 μA |
| 忽略峰值与内阻 | 发射时电压塌陷复位 |
| 忽略 PCB 漏电 | 潮湿现场“算不准” |

CR2032 类高内阻电池难直接扛百 mA 级脉冲，常需并联电容或换低内阻锂亚等化学体系——以电池手册脉冲曲线为准[6][7]。

## 3. 策略：周期 / 事件 / 自适应

| 策略 | 可预测性 | 注意 |
|------|----------|------|
| 固定周期 | 高 | 易算寿命 |
| 事件驱动 | 依赖事件率 | 要设上限 |
| 自适应间隔 | 稳态长才省电 | 变化频繁可能更费 |

RTC（LSE 等）定时唤醒是主流；精度与休眠电流权衡[8]。

## 4. 测量

PPK2/Joulescope 等：看睡眠均值、发射峰值、分段积分电量、异常尖峰。手册典型值只能做初值[3]。

## 5. 局限、挑战与可改进方向

### 1. 只优化活跃电流不拉长间隔

**局限**：DC 仍高时收益有限。
**改进**：业务允许下延长周期或批量上报[2]。

### 2. 寿命表不算 LDO/PCB

**局限**：纸面十年、现场一年。
**改进**：整机睡眠电流验收；选 nA 级 Iq 或负载开关[7]。

### 3. 自适应当万能

**局限**：事件密时比固定更耗。
**改进**：仿真事件分布；设最快间隔与日电量上限[1]。

### 4. 平均电流合格但脉冲不合格

**局限**：电池压降复位。
**改进**：脉冲测试；储能电容或换电池化学[6]。

## 6. 实践要点

1. 先测 I_sleep 与单次 Q_active，再反推间隔。
2. 发射路径做功率/重传/Rx 窗敏感度分析。
3. 设计留约三成容量裕量应对温度与老化。

## 参考文献

[1] A. Bachir et al., MAC protocols for WSN survey, IEEE ComST.
[2] R. Piyare et al., Ultra low power wake-up radios survey, IEEE ComST.
[3] Nordic Power Profiler / PPK application guidance.
[4] Semtech SX127x power consumption profiles.
[5] Nordic nRF52 product spec — power consumption.
[6] Coin cell pulsed load and internal resistance application notes.
[7] Ultra-low Iq LDO datasheets (e.g. TPS7A02 class) vs legacy LDOs.
[8] STM32L4 Stop/Standby and RTC wakeup reference manual sections.
[9] J. Polastre et al., Telos ultra-low power wireless research, IPSN.
[10] Battery self-discharge and effective capacity derating notes.
[11] LoRaWAN Class A receive window energy accounting notes.
