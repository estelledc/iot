---
schema_version: '1.0'
id: low-power-design-patterns
title: IoT 低功耗设计模式
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - duty-cycling-sensor-node
  - battery-life-estimation-model
tags:
  - 低功耗
  - 休眠
  - 占空比
  - DVFS
  - 电源门控
  - IoT
  - 电池寿命
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT 低功耗设计模式

> **难度**：🟡 中级 | **领域**：嵌入式电源管理 | **关键词**：Sleep、Duty Cycle、门控、DVFS | **阅读时间**：约 16 分钟

## 日常类比

偏远小屋靠太阳能蓄电池：灯按需开（事件驱动），睡觉关电器只留烟雾报警（深度睡眠），某些房间拉电闸（电源门控）。纽扣电池 IoT 节点往往绝大部分时间在“睡”，只在采样/发送的短窗口工作——平均电流由休眠电流与唤醒占空比共同决定[1][2]。

## 摘要

梳理 MCU 睡眠层级、外设与射频占空比、电压调节与电源门控、测量方法。文中寿命与电流为**量级示意，必须以目标板万用表/电源分析仪实测为准**[3][4]。

## 1. 睡眠与唤醒

| 深度倾向 | 省电 | 唤醒代价 | 典型保留 |
|----------|------|----------|----------|
| 浅睡 | 较少 | 快 | 时钟/RAM 较多 |
| 深睡 | 多 | 慢，可能丢 RAM | RTC/唤醒引脚 |
| 关断级 | 最多 | 需冷启动 | 极少逻辑 |

选择原则：在截止期限内选“够用最深”。错误的高频定时唤醒会吃掉深睡收益[1]。

## 2. 模式工具箱

| 模式 | 要点 |
|------|------|
| 占空比传感 | 传感器上电→稳定→采样→断电 |
| 射频短窗 | 发完即睡；RX 窗口最小化 |
| 时钟门控 | 关掉不用总线/外设时钟 |
| 电源门控 | 负载开关切断整块模拟/射频 |
| DVFS | 忙时提频/压，闲时降（视 MCU 支持） |
| 批量上报 | 本地聚合，减少空中次数 |

| 能耗粗账 | 说明 |
|----------|------|
| E ≈ I_sleep·T_sleep + Σ I_active·T_active | 平均电流决定电池寿命 |
| 无线突发 | 往往占能量大头，优化协议与重传 |

## 3. 局限、挑战与可改进方向

### 1. 休眠电流被外设偷走

**局限**：上拉、漏电 IO、LDO 静态电流让“深睡”仍数百 μA。
**改进**：断电域、高阻 IO 表、选低 Iq 稳压；逐项断电实验。

### 2. 唤醒过于频繁

**局限**：RTC 1 Hz 无脑醒，平均电流下不来。
**改进**：事件驱动、自适应周期、传感器硬件中断。

### 3. 只优化 MCU 忽略射频/传感器

**局限**：MCU 睡了，模组仍在听。
**改进**：模组级 sleep API；天线开关与电源开关。

### 4. 实验室数据难复现外场

**局限**：温度、电池内阻、网络重传改变寿命。
**改进**：高低温测电流；寿命模型加余量；见电池估算文。

## 4. 实践要点

1. 先画状态机与各态电流预算，再写代码。
2. 用分流电阻+示波器看尖峰，不只看万用表平均值。
3. 节点占空比细节见 `duty-cycling-sensor-node`。

## 参考文献

[1] MCU vendor low-power modes application notes (STM32/nRF/ESP 等).
[2] Semtech / BLE vendor sleep current guidance.
[3] Battery life estimation methodologies for IoT.
[4] Power analyzer measurement best practices.
[5] DVFS in embedded systems surveys.
[6] Power gating and isolation cell basics.
[7] Sensor duty-cycling design patterns.
[8] LoRaWAN/NB-IoT energy consumption studies.
[9] LDO Iq and load-switch selection guides.
[10] IEC / 工业现场低功耗设备设计综述.
[11] Energy harvesting vs battery tradeoff notes.
