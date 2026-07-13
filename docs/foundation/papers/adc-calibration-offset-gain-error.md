---
schema_version: '1.0'
id: adc-calibration-offset-gain-error
title: ADC校准：失调误差与增益误差补偿
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 15
prerequisites:
  - adc-resolution-snr-enob
  - adc-reference-voltage-design
tags:
  - ADC校准
  - 失调误差
  - 增益误差
  - 两点校准
  - 温漂补偿
  - 端到端校准
  - STM32
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# ADC校准：失调误差与增益误差补偿

> **难度**：🟡 中级 | **领域**：ADC 精度优化 | **阅读时间**：约 15 分钟

## 日常类比

尺子零点没对齐 → 读数整体偏一截，即失调（Offset）；尺子被拉长/缩短 → 读数按比例偏，即增益（Gain）误差。模数转换器（Analog-to-Digital Converter, ADC）校准就是用已知电压把“零点”和“刻度”扳正[1][3]。

## 摘要

梳理失调/增益/积分非线性（Integral Nonlinearity, INL）/微分非线性（Differential Nonlinearity, DNL），两点与多点校准、片内自校准局限、工厂与现场流程、温度插值与端到端校准。手册中的 ppm、µV/°C 为**典型量级**，以具体硅片与板级实测为准[1][2]。

## 1. 误差类型

| 类型 | 特征 | 线性校准能否消 |
|------|------|----------------|
| 失调 | 整体平移 | 能（两点中的偏置） |
| 增益 | 斜率偏 | 能 |
| INL | 曲线弯曲 | 需多点/分段 |
| DNL | 码宽不均 | 有限改善 |

根因线索：比较器失调与电荷注入 → 失调；基准与电阻匹配 → 增益；电容失配 → INL/DNL[1]。基准 1% 级误差可直接变成约 1% 增益误差，往往大于 1–2 LSB 的宣传噪声[3][4]。

## 2. 两点与多点

```
D_cal = G · D_raw + B
G = (D_ideal_h − D_ideal_l) / (D_meas_h − D_meas_l)
```

| 校准点 | 优点 | 注意 |
|--------|------|------|
| 近 0 + 近满度 | 覆盖全量程 | 端部可能更非线性 |
| 约 25% + 75% | 避开端部 | 两端外推略差 |

12 位及以下多数场景两点够用；更高位数或大 INL 用分段线性或低阶多项式（阶数不宜过高，防 Runge）[1][5]。

片内自校准：短路测失调、内部参考估增益——**只覆盖 ADC 核**，不含运放/传感器；不能替代系统校准[2]。

## 3. 存储、温度与端到端

| 介质 | 线索 |
|------|------|
| OTP | 工厂一次性 |
| EEPROM/Flash | 现场更新；注意擦写寿命 |
| 结构 | magic + 系数 + 温度 + CRC |

温漂：失调与基准温度系数叠加。策略：单点+手册 TC 粗补，或多温度表插值；MCU 内温传感器仅粗用[3][4]。

端到端：在传感器侧施加已知物理量，直接映射到工程量，一次吃掉链路误差；每通道、接近使用条件校准[4]。

| 场景精度线索 | 校准频率线索 |
|--------------|--------------|
| 消费级数 % | 出厂一次量级 |
| 工业约 1% 级 | 维护周期 |
| 精密 <0.1% 级 | 更频或开机/测前 |

## 4. 局限、挑战与可改进方向

### 1. 只做片内自校准就宣称精度

**局限**：前端运放与传感器漂移未进模型。
**改进**：产线端到端两点；现场用板载基准或冰点等可复现点抽检。

### 2. 忽略温度

**局限**：25 °C 校准，野外数十 °C 漂移吃掉 LSB。
**改进**：多温度表或选低温漂基准；记录校准温度。

### 3. 校准数据无完整性保护

**局限**：Flash 损坏或写穿导致荒谬读数。
**改进**：CRC、双备份、非法则回退默认并告警。

### 4. 高阶多项式过拟合

**局限**：边界振荡，现场更差。
**改进**：优先分段线性；多项式阶数压到 2–3 并做交叉验证。

## 5. 实践要点

1. STM32 等：上电按手册 ADCAL 流程，校准前禁用转换[2]。
2. 先噪声/ENOB 达标，再谈亚 LSB 校准收益。
3. 校准间隔与温度阈值写入产品需求，而非临时拍脑袋。

## 参考文献

[1] W. Kester, Data Conversion Handbook, Analog Devices — ADC error chapters.
[2] STMicroelectronics, STM32 reference manuals — ADC calibration (e.g. RM0090 lineage).
[3] Texas Instruments, understanding ADC errors and calibration (SLAA013 lineage).
[4] Maxim/ADI application notes on ADC calibration for precision measurement.
[5] J. G. Jespers, Integrated Converters — error correction chapters.
[6] Voltage reference temperature coefficient and gain error coupling notes.
[7] EEPROM/FRAM endurance guidance for calibration storage.
[8] System-level sensor calibration best practices (ISA/NIST metrology intros).
[9] INL/DNL definition — IEEE ADC terminology standards lineage.
[10] Factory ATE two-point calibration throughput case notes (vendor).
[11] On-chip VREFINT accuracy limitations in MCU datasheets.
