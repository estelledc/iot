---
schema_version: '1.0'
id: 4-20ma-current-loop-industrial
title: 4-20mA电流环在工业IoT中的信号传输
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 16
prerequisites:
  - current-sense-resistor-shunt
  - adc-calibration-offset-gain-error
tags:
  - 4-20mA
  - 电流环
  - 工业传感
  - HART
  - NAMUR
  - 变送器
  - 信号调理
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 4-20mA电流环在工业IoT中的信号传输

> **难度**：🟢 初级 | **领域**：工业信号传输 | **阅读时间**：约 16 分钟

## 日常类比

电压信号像长水管末端水压——管子越长、旁人越吵（电磁干扰），末端越不准。电流环像“流量”：闭合回路里电流处处相等（基尔霍夫电流定律），线阻主要吃掉电源裕量而非信号本身。4 mA 作“活零点”：0 mA 像电话断线，4 mA 才是量程零点[1][2]。

## 摘要

说明 4–20 mA 抗干扰与断线检测机制、两/三/四线制、采样电阻与环路电阻预算、HART（Highway Addressable Remote Transducer）叠加与 NAMUR NE43 故障电流，以及工业物联网（IoT）网关数字化路径。距离与功耗数字为**典型量级**，须按电源、线阻与变送器压降核算[1][3]。

## 1. 为何用电流而非电压

| 特性 | 0–10 V 类电压 | 4–20 mA 电流环 |
|------|---------------|----------------|
| 感应噪声 | 直接叠到电压 | 主要改电位分布，理想串联电流不变 |
| 线阻影响 | 分压误差 | 不改变电流值（电源够驱动时） |
| 断线检测 | 0 V 可能是真零 | 0 mA ≈ 断线；4 mA = 零点 |
| 距离 | 通常较短 | 可达公里量级（视电源与总阻） |

活零点对比：

| 电流 | 0–20 mA 含义 | 4–20 mA 含义 |
|------|--------------|--------------|
| 0 mA | 可能是零点 | 故障/断线 |
| 4 mA | 量程 20% | 量程零点 |
| 20 mA | 满度 | 满度 |

工程量换算：`PV = (I−4)/16 × (URV−LRV) + LRV`[1]。

## 2. 回路组成与电阻预算

核心：24 V 级电源、变送器、线缆、接收端采样电阻（常见 250 Ω → 1–5 V）[3][4]。

```
V_supply ≥ I_max × R_total
R_total ≈ R_tx_drop等效 + R_wire往返 + R_sense + …
```

采样电阻精度（如 0.1% 级金属箔）直接进增益误差；选 165/250/500 Ω 需同时看 MCU 量程与环路裕量[4]。

| 接线 | 线数 | 特点 |
|------|------|------|
| 两线制（环路供电） | 2 | 变送器从环路取电，静态须 <4 mA |
| 三线制 | 3 | 独立供电，共地 |
| 四线制 | 4 | 电源与信号隔离，抗扰更好、线成本高 |

两线制在现场占比高，但可用功率在 4 mA 时最紧，传感器须低功耗[3][5]。

## 3. 驱动、接收与故障信令

电压–电流转换可用 XTR111 类模拟驱动；数字侧可用环路供电数模转换器（Digital-to-Analog Converter, DAC）如 AD5420 等——以数据手册为准[3][4]。

接收：`V = I × R_sense` → 模数转换器（Analog-to-Digital Converter, ADC）。多通道注意共地与差分/仪表放大。软件侧按 NAMUR NE43 判据处理故障电流（如 <3.6 mA、>21 mA 等区间，以现行 NE43 为准）[2]。

HART：在直流 4–20 mA 上叠加约 ±0.5 mA 量级频移键控（Frequency-Shift Keying, FSK），均值近零，便于诊断与组态而不丢模拟主变量[5]。

| 能力 | 纯 4–20 mA | +HART |
|------|------------|-------|
| 过程变量 | 是 | 是 |
| 诊断/组态 | 弱 | 强 |
| 多变量 | 否 | 有限支持 |

## 4. 接地与总线对照

单点接地在接收端；屏蔽层通常单端接地；用双绞屏蔽线。两端接地易引入地环路工频纹波[1][6]。

| 方案 | 距离/拓扑线索 | 诊断 |
|------|----------------|------|
| 4–20 mA | 长距离点对点 | 断线级 |
| HART | 同电流环 | 丰富 |
| Modbus RTU 等 | 多站数字 | 有 |
| IO-Link | 短距离点对点 | 丰富 |

存量现场仍大量 4–20 mA；IoT 网关首要任务常是可靠数字化而非立刻换总线[5][6]。

## 5. 局限、挑战与可改进方向

### 1. 忽略环路压降预算

**局限**：线阻+采样电阻过大导致 20 mA 削顶。
**改进**：按 `R_max ≈ (V_supply − V_tx_min)/0.02` 留裕量；长线升压或降采样电阻。

### 2. 地环路与屏蔽接错

**局限**：读数漂、50/60 Hz 纹波。
**改进**：接收端单点地；屏蔽单端；必要时隔离接收。

### 3. 只用 ADC 位数堆精度

**局限**：采样电阻与基准误差主导。
**改进**：0.1% 级电阻 + 稳基准；端到端校准；RSS 误差预算[4][7]。

### 4. 无故障电流策略

**局限**：断线与真零混淆，安全联锁失效。
**改进**：实现 NE43 区间；联锁测 0 mA 与超量程。

## 6. 实践要点

1. 新变送器优先两线制，确认 4 mA 功率够用。
2. 网关侧统一工程量与故障码上报（MQTT/OPC UA 等）。
3. 需要诊断时评估 HART 调制解调，而非先上复杂现场总线。

## 参考文献

[1] ISA-50.00.01, Analog signals for process control systems.
[2] NAMUR NE43, Failure information signal levels for analog transmitters.
[3] Texas Instruments, XTR111 Precision Voltage-to-Current Converter datasheet.
[4] Analog Devices, AD5420 16-Bit Loop-Powered 4–20 mA DAC datasheet.
[5] FieldComm Group / HART Communication Protocol Specification (Rev. 7 lineage).
[6] Industrial grounding and shielded twisted-pair wiring practices (vendor app notes).
[7] Walt Kester, Data Conversion Handbook, Analog Devices — error budget chapters.
[8] IEC 60381-1, Analogue signals for process control systems — Direct current signals.
[9] Emerson/Siemens/ABB transmitter manuals on 2/3/4-wire hookup.
[10] TI/ADI application notes on 4–20 mA input protection and surge.
[11] OPC UA / MQTT gateway patterns for analog input digitization (industry white papers).
