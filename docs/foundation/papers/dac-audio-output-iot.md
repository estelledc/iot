---
schema_version: '1.0'
id: dac-audio-output-iot
title: DAC在IoT音频输出与执行器控制中的应用
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 14
prerequisites:
  - dma-controller-mcu-optimization
  - signal-conditioning-amplifier-filter
tags:
  - DAC
  - I2S
  - PWM
  - 音频输出
  - 执行器控制
  - DMA
  - 数模转换
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# DAC在IoT音频输出与执行器控制中的应用

> **难度**：🟢 初级 | **领域**：数模转换应用 | **阅读时间**：约 14 分钟

## 日常类比

手机里的音乐是一串数字，扬声器却要连续电压才能震动。DAC（Digital-to-Analog Converter，数模转换器）像“旋钮替身”：把离散码字变成连续电压，才能播提示音、渐变灯光、把阀门停在半开。没有它，数字世界往往只能开/关[1][2]。

## 摘要

IoT 里 DAC 用于音频、模拟给定与调光。选型轴：**MCU 内置 DAC、I2S 音频 DAC、PWM+RC 等效**。分辨率≠精度（看 INL/DNL）；驱动弱负载必须缓冲。芯片 SNR/价格为标称量级，**以数据手册与听感/闭环实测为准**[1][3]。

## 1. 原理与架构

```
Vout ≈ Vref × (D / 2^N)
LSB = Vref / 2^N
```

| 架构 | 速度 | 精度倾向 | 面积/成本 | 典型用途 |
|------|------|----------|-----------|----------|
| R-2R | 中 | 中高 | 中 | MCU 内置 |
| 电流舵 | 高 | 中 | 大 | 高速/视频 |
| PWM+滤波 | 低 | 中 | 极小 | LED/粗给定 |

| 要素 | 含义 |
|------|------|
| 分辨率 | 位宽，决定最小步进 |
| INL/DNL | 积分/微分非线性；DNL>1 LSB 可能丢码 |
| 建立时间 | 跳变后稳定到规定误差带 |
| 毛刺能量 | 码字切换尖峰，音频里像“咔嗒” |

## 2. MCU 内置 vs I2S 音频

MCU 内置 8～12 位 DAC 适合偏置、阀门给定、呼吸灯；做语音时 SNR、去毛刺与滤波常不够。专用 I2S DAC/功放接收 PCM，更适合门铃与播报[2][3]。

| 方案倾向 | 接口 | 场景 |
|----------|------|------|
| MCU DAC | 寄存器/DMA | 执行器模拟给定 |
| PCM5102 类 | I2S 线出 | 较高品质立体声 |
| MAX98357 类 | I2S→D 类功放 | 低成本单声道扬声器 |
| Codec（ADC+DAC） | I2S | 对讲/录音回放 |

音频路径用 DMA（Direct Memory Access）搬 PCM，避免 CPU 逐样点写；定时器触发 MCU DAC 可零占用输出波形表[2][4]。

## 3. PWM 等效 DAC

占空比经 RC 低通得直流：`Vout ≈ Vcc × Duty`。截止频率需满足 `f_signal < f_c < f_pwm/10` 量级；单级纹波大时用二阶 RC。适合慢变执行器，不适合宽带音频[1][5]。

## 4. 执行器与缓冲

| 应用 | 要点 |
|------|------|
| 阀门/变频器 0～10 V | 常需运放放大与跟随 |
| 电机速度给定 | 长线加缓冲，防压降 |
| EMI 敏感调光 | 模拟调光降谐波；效率通常低于 PWM |

无缓冲时 MCU DAC 输出阻抗可到十余 kΩ 量级，带载跌落严重；轨到轨运放跟随是默认补丁[1][6]。

## 5. 局限、挑战与可改进方向

### 1. 把位数当精度

**局限**：12 位器件 INL 数 LSB 时有效步进远粗于理想。
**改进**：看 INL/DNL/偏移；闭环用反馈校准[1][7]。

### 2. 音频硬用内置 DAC

**局限**：click/pop、SNR 不足。
**改进**：I2S DAC/功放 + DMA；软件避免大步进跳变[3][4]。

### 3. PWM 当“高精度 DAC”

**局限**：纹波与带宽限制被低估。
**改进**：提高载波、二阶滤波，或换真 DAC[5]。

### 4. 忽略驱动能力

**局限**：直接驱动电缆/SSR 输入导致误差。
**改进**：跟随器/差分驱动；测满载建立时间[6]。

## 6. 实践要点

1. 音频 → I2S；慢变给定 → MCU DAC 或 PWM+RC。
2. 任何带载输出先问：要不要缓冲？
3. DNL>1 LSB 的通道慎用于闭环位置控制。

## 参考文献

[1] Texas Instruments, DAC Essentials, SLAA567.
[2] STMicroelectronics, STM32 Reference Manual — DAC chapter.
[3] Maxim, MAX98357A datasheet.
[4] Espressif / vendor I2S DMA audio application notes.
[5] Analog Devices, Data Conversion Handbook — DAC architectures (Kester).
[6] Op-amp buffer application notes for DAC drive.
[7] DAC INL/DNL and monotonicity application notes.
[8] TI PCM5102A datasheet / no-MCLK I2S notes.
[9] PWM DAC RC filter design notes.
[10] IEC / audio SNR measurement context for codecs.
[11] STM32 DAC+DMA+Timer waveform generation examples.
