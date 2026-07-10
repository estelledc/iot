---
schema_version: '1.0'
id: ble-power-consumption-profiling
title: BLE功耗分析：广播/连接/休眠各阶段
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - ble-connection-parameter-optimization
tags:
  - BLE
  - 功耗
  - 广播间隔
  - 连接间隔
  - Slave Latency
  - PPK2
  - DCDC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# BLE功耗分析：广播/连接/休眠各阶段

> **难度**：🟡 中级 | **领域**：BLE功耗工程 | **阅读时间**：约 20 分钟

## 日常类比

水龙头：洗手时大开（射频发射/接收毫安级），关紧后仍可能微漏（休眠微安级）。蓝牙低功耗（Bluetooth Low Energy, BLE）优化核心是缩短开阀时间、拉长关阀时间。同一颗纽扣电池在不同占空比下，续航可差几个数量级——**必须以实测平均电流核算**[2][5]。

## 摘要

本文按链路层状态拆解广播、扫描、连接与休眠电流，给出连接间隔（Connection Interval, CI）、从属延迟（Slave Latency）与发射功率等旋钮，并概述功耗分析仪测量要点。文中微安/毫安数字多取自 Nordic 等数据手册量级，**换芯片需重测**[3]。

## 1. 状态与占空比

| 状态 | 射频 | 电流量级（常见 SoC） |
|------|------|----------------------|
| Sleep/Standby | 关 | µA |
| Advertising | 周期 TX | 活跃时 mA |
| Scanning | RX | 活跃时 mA |
| Connection | 周期 RX/TX | 活跃时 mA |

\[
I_\mathrm{avg}\approx (I_\mathrm{active}T_\mathrm{active}+I_\mathrm{sleep}T_\mathrm{sleep})/T
\]

## 2. 广播与扫描

单次广播事件通常在 37/38/39 各发一包，活跃约数毫秒。间隔从约 20 ms 到约 10.24 s：间隔越大越省电，发现越慢[1]。

| 广播间隔倾向 | 平均电流倾向 | 发现时延倾向 |
|--------------|--------------|--------------|
| 很快（数十 ms） | 高 | 低 |
| 中（百 ms～1 s） | 中 | 中 |
| 很慢（数秒） | 接近休眠 | 高 |

扫描平均电流 ≈ RX 电流 ×（Scan Window / Scan Interval）。持续扫描可达数毫安，仅适短时发现[5]。

发射功率从 +8 dBm 降到负值可明显降 TX 电流，但缩短距离；室内近场常可低于 0 dBm——**以链路预算实测为准**[3]。

## 3. 连接阶段

Peripheral 每事件先 RX 再 TX；无应用数据仍可能交换空包保活。CI 越大，空闲越省电、时延越大。Slave Latency 允许跳过若干事件，有数据时可提前响应[1]。

| CI 倾向 | 功耗 | 时延 | 场景叙事 |
|---------|------|------|----------|
| 极短 | 高 | 低 | 高吞吐 |
| 中 | 中 | 中 | 交互 |
| 长 + Latency | 低 | 首包可能变长 | 慢传感器 |

## 4. 休眠与系统漏电

休眠含 RTC、RAM retention、漏电；启用直流-直流（DCDC）相对低压差线性稳压器（LDO）常可降射频阶段电流（需外部电感）[3]。系统总电流 = 射频平均 + MCU + 传感器 + 外设；传感器待机与 GPIO 浮空常是“隐形杀手”。

| 优化 | 效果倾向 | 代价 |
|------|----------|------|
| 增大广播/连接间隔 | 近似线性降射频均值 | 时延↑ |
| Slave Latency | 空闲大降 | 下行首包延迟 |
| 降 TX 功率 | 降 TX 电流 | 距离↓ |
| 开 DCDC | 降活跃电流 | PCB 电感 |
| 关调试 UART/日志 | 常可降数百 µA 量级 | 少日志 |

## 5. 测量

推荐电源分析仪（如 Nordic PPK2）覆盖 nA～A；或分流电阻+示波器看事件波形。须断开调试器、关 LED/日志，平均至少多个完整事件，并计入晶振启动尖峰[2][5]。

## 6. 局限、挑战与可改进方向

### 1. 数据手册 ≠ 整机

**局限**：手册 TX 电流不含传感器与电源效率[3]。
**改进**：整机电池路径测 \(I_\mathrm{avg}\)；按任务剖面（广播/连接/休眠占比）加权。

### 2. 调试态污染

**局限**：SWD、日志、USB 供电掩盖真实睡眠电流。
**改进**：量产配置复测；夹具供电与电池内阻一并考虑。

### 3. 参数与体验冲突

**局限**：为续航把 CI 拉满导致 App 卡顿或超时断连。
**改进**：空闲用长 CI+Latency，突发数据临时请求参数更新[6]。

### 4. 外设与 GPIO

**局限**：ADC/传感器常开或浮空脚可吞掉射频优化收益。
**改进**：用完断电；未用脚固定电平；批量上报减唤醒次数。

## 7. 实践要点

1. 先定续航目标反推允许 \(I_\mathrm{avg}\)，再选 CI/间隔。
2. 用波形确认“事件尖峰 + 平坦睡眠”，而不是只看万用表瞬时值。
3. OTA/高速传输阶段单独做功耗预算，勿与慢采样剖面混用。

## 参考文献

[1] Bluetooth SIG, "Bluetooth Core Specification," Vol 6 Link Layer (states, CI, latency).
[2] Nordic Semiconductor, Measuring current with Power Profiler Kit II.
[3] Nordic Semiconductor, nRF52/nRF53 Product Specifications (TX/RX/sleep currents).
[4] Gomez, C. et al., "Overview and Evaluation of Bluetooth Low Energy," Sensors, 2012.
[5] Texas Instruments, "Measuring Bluetooth Low Energy Power Consumption," SWRA478.
[6] Bluetooth SIG / vendor docs on connection parameter update.
[7] Nordic, DCDC enable and external component guidelines.
[8] ST / Silicon Labs BLE power optimization application notes.
[9] Bluetooth SIG, Advertising interval ranges and scan window definitions.
[10] Zephyr Project, power management + Bluetooth integration notes.
[11] Battery capacity derating guidance for CR2032-class cells in IoT designs.
