---
schema_version: '1.0'
id: adc-resolution-snr-enob
title: ADC分辨率/SNR/ENOB有效位数深度解析
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - adc-sar-vs-sigma-delta
  - oversampling-noise-shaping-adc
tags:
  - ADC
  - SNR
  - ENOB
  - SINAD
  - 量化噪声
  - 过采样
  - 噪声预算
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# ADC分辨率/SNR/ENOB有效位数深度解析

> **难度**：🟡 中级 | **领域**：数据转换器性能 | **阅读时间**：约 16 分钟

## 日常类比

尺子刻度很密叫分辨率；尺子本身胀缩、刻歪叫精度问题。标称 24 位不等于 24 位可信——有效位数（Effective Number of Bits, ENOB）才回答“相当于几位理想 ADC”[1][4]。

## 摘要

区分分辨率与精度，推导理想信噪比（Signal-to-Noise Ratio, SNR）`6.02N+1.76 dB`，由信号与噪声失真比（SINAD）算 ENOB，并讨论谐波失真（Total Harmonic Distortion, THD）、无噪声分辨率、过采样与系统噪声预算。手册 SINAD 为**特定测试条件**下数值[1][2]。

## 1. 分辨率 vs 精度与理想 SNR

| | 分辨率 | 精度 |
|--|--------|------|
| 问 | 能分多少层 | 离真值多远 |
| 决定 | 位数 N | INL/DNL/失调/增益/噪声 |

`LSB = FSR/2^N`。理想量化噪声均匀分布时：

```
SNR_ideal ≈ 6.02N + 1.76 dB   （满量程正弦）
```

每增 1 位约 +6 dB SNR——工程直觉[1][2]。

## 2. 噪声、SINAD 与 ENOB

| 来源 | 线索 |
|------|------|
| 量化 | LSB²/12，满带 |
| 热噪声 | kT/C 等 |
| 基准噪声 | 按比例进输出 |
| 抖动 | 高频大信号更伤 |
| 电源/数字馈通 | 布局与 PSRR |

```
ENOB = (SINAD − 1.76) / 6.02
SINAD ≤ SNR（因含失真）
```

例：标称 16 位、SINAD 约 86 dB → ENOB 约 14 位量级。THD 接近或差于 SNR 时，失真会主导 SINAD，ENOB 明显掉[1][4]。

| 指标 | 含义 | 更相关场景 |
|------|------|------------|
| ENOB | rms 等效位 | 动态/交流 |
| 无噪声分辨率 | 码基本不跳的位 | 直流/称重 |

经验关系量级：无噪声位 ≈ ENOB − 约 2.7（按峰峰值≈6.6·rms 概率覆盖）[1]。

## 3. 读手册、测量与过采样

陷阱：首页位数营销；SINAD 只在低频测；只给 SNR 不给 SINAD；输入远小于满量程时有效 SNR 再降[4]。

测量：相干正弦 + FFT 得 SINAD；直流直方图得 σ 再换算有效/无噪声位。过采样：OSR 每约 ×4，简单平均约 +1 bit；不修复 THD，对 1/f 有限[3][5]。

按 `log2(量程/所需精度)` 估所需 ENOB，再选型——避免盲目上 24 位[3]。

## 4. 局限、挑战与可改进方向

### 1. 把标称位当合同指标

**局限**：系统验收对不上。
**改进**：合同写清 SINAD/ENOB/无噪声位与测试条件。

### 2. 忽略前端与基准

**局限**：ADC 芯片 ENOB 高，板级一塌糊涂。
**改进**：输入短路噪声预算；基准与 PGA 单列。

### 3. 小信号仍按满量程 SNR 宣传

**局限**：实际输入 10% FS 时 SNR 大降。
**改进**：按实际幅度重算；或 PGA 抬满量程。

### 4. 过采样迷信

**局限**：延迟、功耗上升，失真仍在。
**改进**：先降非线性与干扰；过采样作补充。

## 5. 实践要点

1. 打开数据手册找目标 fs、fin 下的 SINAD，当场算 ENOB。
2. 直流应用同时要 input noise 峰峰值。
3. 优化最大噪声源，而不是先换更多位的芯片。

## 参考文献

[1] W. Kester, Data Conversion Handbook, Analog Devices.
[2] B. Razavi, Principles of Data Conversion System Design, IEEE Press.
[3] Texas Instruments, delta-sigma / precision ADC intro (SLAA511 lineage).
[4] Analog Devices, understanding ENOB (AN-1271 lineage).
[5] Maxim/ADI, demystifying delta-sigma ADC performance vs resolution.
[6] IEEE standard terminology for ADC static/dynamic specs.
[7] Aperture jitter SNR formulas — converter handbooks.
[8] Coherent sampling and FFT windowing app notes.
[9] Noise-free resolution in weighing applications (load-cell ADC notes).
[10] Oversampling gain derivations — signal processing texts.
[11] System noise budget worksheets (vendor precision designs).
