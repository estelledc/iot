---
schema_version: '1.0'
id: load-cell-hx711-interface
title: 称重传感器与HX711 ADC接口设计
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 15
prerequisites:
  - bridge-circuit-sensor-excitation
  - adc-sar-vs-sigma-delta
tags:
  - 称重传感器
  - HX711
  - 应变片
  - 惠斯通电桥
  - 24位ADC
  - 校准
  - PGA
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 称重传感器与HX711 ADC接口设计

> **难度**：🟢 初级 | **领域**：力传感与嵌入式接口 | **关键词**：Load Cell, HX711, PGA, 电桥 | **阅读时间**：约 15 分钟

## 日常类比

商场电子秤：人站上去 → 金属梁微弯 → 应变片电阻微变 → 电桥输出毫伏级电压 → HX711 放大并转成数字 → 屏幕显示公斤。整条链像“翻译接力”，每一环都可能引入误差，校准就是用已知砝码给这套翻译定标尺[1][2]。

## 摘要

梳理悬臂梁/S 型等称重传感器、四/六线制、HX711 可编程增益放大器（Programmable Gain Amplifier, PGA）与两线时序，以及去皮/两点校准。灵敏度与噪声数字**以传感器与芯片手册实测为准**[1][3]。

## 1. 传感器与电桥

| 类型 | 量程倾向 | 抗偏载 | 常见场景 |
|------|----------|--------|----------|
| 悬臂梁 | 较小～中等 | 中 | 台秤、料斗 |
| S 型 | 中～大 | 较强 | 吊秤、测力 |
| 轮辐式 | 大 | 强 | 地磅等 |

应变片常组成惠斯通电桥；激励电压典型为数伏量级，满量程输出常为约 1–2 mV/V 量级（**以铭牌为准**）[2]。

| 接线 | 特点 |
|------|------|
| 四线制 | 简单；线阻影响激励 |
| 六线制 | 远端 Sense 补偿线损，远距离/高精度更稳 |

## 2. 为何用 HX711

MCU 内置 10/12 位模数转换器（Analog-to-Digital Converter, ADC）对毫伏级电桥信号通常不够；HX711 集成 PGA + 24 位 Σ-Δ ADC，通道 A 增益可选约 128/64，通道 B 约 32（**以数据手册为准**）[1]。

| 项 | MCU 低分辨率 ADC | HX711（典型） |
|----|------------------|---------------|
| 位数 | 10–12 | 24（有效位数常低于标称） |
| PGA | 常无 | 有 |
| 接口 | 片内 | 两线（SCK/DOUT）类 SPI |

数据速率常见约 10 / 80 SPS 档；更高速率噪声更大，称重多选低速档[1]。

## 3. 校准与布线要点

1. 上电稳定后多次平均读空载 → 去皮（tare）。
2. 放已知砝码 → 求 `scale = (raw - offset) / mass`。
3. 激励与模拟地短、粗；数字线远离模拟差分对；金属结构良好接地。

| 竞品倾向 | 接口 | 备注 |
|----------|------|------|
| HX711 | 两线 | 成本低、资料多 |
| NAU7802 | I2C | 速率/功能更灵活 |
| ADS1232 等 | 专用串行 | 工业向 |

## 4. 局限、挑战与可改进方向

### 1. 温度与蠕变

**局限**：应变片与结构随温度漂移；长期负载蠕变。
**改进**：恒温/温度补偿通道；定期复校；选低蠕变传感器。

### 2. 噪声与机械振动

**局限**：风扇、人碰台面导致读数跳。
**改进**：机械隔振、平均滤波、稳态判定后再上报。

### 3. 供电与参考不稳

**局限**：激励纹波直接进电桥。
**改进**：独立模拟供电/LDO；六线制；星形地。

### 4. 有效分辨率被夸大

**局限**：24 位标称不等于 24 位可用。
**改进**：用噪声自由分辨率评估；必要时换更低噪声前端。

## 5. 实践要点

1. 先确认量程与灵敏度，再选增益，避免饱和。
2. 校准砝码覆盖工作区间；量产做多点抽检。
3. 电桥激励细节见 `bridge-circuit-sensor-excitation`。

## 参考文献

[1] Avia Semiconductor, HX711 24-Bit Analog-to-Digital Converter datasheet.
[2] Load cell manufacturer application notes（应变片电桥与灵敏度）.
[3] Texas Instruments / ADI, bridge sensor and PGA design notes.
[4] Nuvoton, NAU7802 datasheet（I2C 对照）.
[5] TI, ADS1232 datasheet.
[6] OIML / 商用衡器准确度等级概述.
[7] Wheatstone bridge temperature compensation techniques.
[8] EMC grounding practices for low-level analog sensors.
[9] MCU bit-banging HX711 timing examples（社区与厂商例程）.
[10] Strain gauge creep and hysteresis white papers.
[11] IEC / 工业称重系统安装指南摘要.
