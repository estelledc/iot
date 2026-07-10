---
schema_version: '1.0'
id: adc-reference-voltage-design
title: ADC基准电压源设计与温漂控制
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - voltage-reference-precision-design
  - adc-resolution-snr-enob
tags:
  - 基准电压
  - 带隙基准
  - 温漂
  - 串联基准
  - 并联基准
  - ADC精度
  - PSRR
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# ADC基准电压源设计与温漂控制

> **难度**：🟡 中级 | **领域**：精密基准设计 | **阅读时间**：约 16 分钟

## 日常类比

尺子热胀冷缩，冬天夏天量同一张桌会“变长”——不是桌子变了，是尺子变了。ADC 的基准电压（Vref）就是这把尺子：`D ≈ (Vin/Vref)·(2^N−1)`。基准一漂，多出来的位数常是噪声[1][3]。

## 摘要

从带隙原理、串联/并联结构、温度系数（Temperature Coefficient, TC）与噪声指标，到缓冲、去耦、布局、比例测量与内/外基准选型。器件 ppm、µV 与价格为**公开手册量级**，以当期数据手册为准[2][5]。

## 1. 误差如何吃掉位数

| Vref 误差量级 | 对满量程影响 |
|---------------|--------------|
| 0.1% | 约 0.1% FS |
| 1% | 约 1% FS（12 位上可达数十 LSB 量级） |

初始误差可校准；宽温下 TC 累积往往更致命。工业温域跨约百 °C 量级时，50 ppm/°C 与 3 ppm/°C 差一个数量级的满量程漂移[1][2]。

带隙：CTAT 的 Vbe 与 PTAT 的 Vt 加权抵消，得到约 1.2 V 量级与温度弱相关电压；再放大到 2.5 V 等标称输出[3]。

## 2. 串联 vs 并联与指标

| | 串联（Series） | 并联（Shunt） |
|--|----------------|---------------|
| 像 | LDO | 稳压管 |
| 优点 | 低 Iq、好 PSRR、易用 | 宽输入、易做负基准/环路 |
| 典型 IoT | 采集板优先 | 4–20 mA/隔离侧常见 |

| 指标 | 含义 | 优先级线索 |
|------|------|------------|
| 初始精度 | 25 °C 偏差 | 可校准，次要 |
| TC | ppm/°C | 宽温最关键 |
| 噪声 | 0.1–10 Hz 等 | 高位数/直流 |
| 长期漂移 | ppm/kHr | 计量/长周期 |

选型地图（示例级）：12 位可用较便宜并联/中端串联；16 位起认真看 TC 与噪声；24 位系统常需精密串联 + 缓冲滤波[2][4][5]。

## 3. 缓冲、滤波、布局与比例法

ADC 采样在 Vref 脚拉瞬态电流，驱动不足会跌落。低噪声运放跟随 + 小隔离电阻 + 陶瓷去耦是常见做法；运放噪声不可差过基准[1][3]。

布局：基准紧邻 ADC、模拟地、远离开关电源与热源。比例测量（激励与 Vref 同源）可消电源慢漂，适合电桥/分压类；绝对输出传感器与嘈杂开关电源场景慎用[1]。

MCU 内部基准：零 BOM，但精度与 TC 通常显著差于外置精密件，只适合粗测或低位数[2]。

## 4. 局限、挑战与可改进方向

### 1. 高位数配劣基准

**局限**：24 位外壳、50 ppm/°C 内核。
**改进**：按 ENOB 目标反推 TC/噪声预算再选型。

### 2. 无缓冲直驱

**局限**：码跳变与动态误差。
**改进**：检查 Iref 峰值；16 位以上默认评估缓冲。

### 3. 热梯度

**局限**：旁边 DC-DC 加热导致昼夜间漂。
**改进**：热隔离、同温区放置 ADC 与基准；必要时软件温补。

### 4. 过度软件补偿劣器件

**局限**：标定成本高，二阶残差仍大。
**改进**：优先换低温漂基准；补偿作增强而非救命。

## 5. 实践要点

1. 宽温项目把 TC 写进必选规格，不只看初始 %。
2. Vref 脚 1 µF 级 + 0.1 µF 就近，忌劣质高介电陶瓷当唯一滤波。
3. 噪声与 TC 用短路输入与温箱实测验收。

## 参考文献

[1] Texas Instruments, Voltage Reference Selection Basics (SLYY154 lineage).
[2] Analog Devices / LTC, precision voltage reference design notes (AN-82 lineage).
[3] W. Kester, Data Conversion Handbook — voltage reference chapter.
[4] REF50xx / ADR45xx / LM4040 / MCP1501 datasheets (representative parts).
[5] Microchip MCP1501 high-precision voltage reference datasheet.
[6] Op-amp buffer driving ADC reference application notes.
[7] Capacitor dielectric (C0G vs X7R/Y5V) guidance for reference decoupling.
[8] Ratiometric measurement app notes for bridge sensors.
[9] MCU internal VREF accuracy tables (STM32/ESP/nRF datasheets).
[10] Long-term drift and burn-in practices for precision references.
[11] PSRR measurement methods for series references.
