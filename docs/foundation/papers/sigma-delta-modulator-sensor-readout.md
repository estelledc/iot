---
schema_version: '1.0'
id: sigma-delta-modulator-sensor-readout
title: Sigma-Delta调制器在高精度传感器读出中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 20
prerequisites:
  - adc-sar-vs-sigma-delta
  - adc-resolution-snr-enob
  - oversampling-noise-shaping-adc
tags:
  - Sigma-Delta
  - ADC
  - 过采样
  - 噪声整形
  - ENOB
  - 传感器读出
  - 精密测量
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# Sigma-Delta调制器在高精度传感器读出中的应用

> **难度**：🔴 高级 | **领域**：精密数据转换 | **关键词**：Σ-Δ, OSR, 噪声整形, ENOB | **阅读时间**：约 20 分钟

## 日常类比

用厘米刻度尺量发丝不够。Sigma-Delta（Σ-Δ）模数转换器（Analog-to-Digital Converter, ADC）像“电子千分尺”：用远高于信号带宽的速率做粗比较，再靠噪声整形与数字滤波用时间换有效位数（Effective Number of Bits, ENOB）[1][2]。

## 摘要

说明过采样、噪声整形与抽取滤波三支柱，对比逐次逼近（Successive Approximation Register, SAR）适用域，并讨论传感器前端（电桥、热电偶）接口注意。分辨率与信噪比（Signal-to-Noise Ratio, SNR）公式为理想量级，实际受基准与 1/f 噪声限制[2][3]。

## 1. 三支柱

输入 → 过采样 → 噪声整形 → 数字低通/抽取 → 高精度码字。

| 机制 | 作用 |
|------|------|
| 过采样 | 量化噪声摊到更宽频带 |
| 噪声整形 | 把噪声推向高频 |
| 抽取滤波 | 去掉带外噪声并降速率 |

| 特性 | SAR | Σ-Δ |
|------|-----|-----|
| 分辨率倾向 | 约 8–18 bit | 约 16–24+ bit |
| 速率倾向 | 可至 MSPS | Hz–kSPS 常见 |
| 抗混叠 | 需较陡模拟滤波 | 过采样放松模拟要求 |
| 延迟 | 低 | 滤波器群时延较高 |
| 典型负载 | 音频/高速 | 称重、温度、慢变传感器 |

## 2. 过采样与整形直觉

过采样率（Oversampling Ratio, OSR）提高可改善带内噪声；仅靠过采样时，约每 4× OSR 理论约 +1 bit 量级，更高阶整形更高效[1]。

| OSR 量级 | 理论 ENOB 提升倾向（仅过采样粗估） |
|----------|-------------------------------------|
| 4 | ~1 bit |
| 16 | ~2 bit |
| 64 | ~3 bit |
| 256 | ~4 bit |

一阶/高阶环路把量化噪声高通化；阶数与 OSR 共同决定带内 SNR，但高阶需关注稳定性[2]。

## 3. 传感器读出要点

| 议题 | 建议 |
|------|------|
| 基准 | 低噪声电压基准，布局远离数字回流 |
| 输入缓冲 | 高阻抗源需驱动 Σ-Δ 开关电容输入 |
| 数据速率 | 选输出字率兼顾噪声与延迟 |
| 斩波/交流激励 | 抑制失调与 1/f（电桥常见） |
| 数字滤波缺口 | 工频陷波（50/60 Hz）按地区配置 |

称重、电阻温度探测器（RTD）、热电偶冷端补偿等慢信号是 Σ-Δ 主场；振动高频细节更常看 SAR/流水线[3][4]。

## 4. 局限、挑战与可改进方向

### 1. 建立时间与延迟

**局限**：高阶数字滤波使阶跃响应变慢，不适合快速闭环。
**改进**：降低滤波器阶数/提高字率；快环用 SAR，慢环用 Σ-Δ[2]。

### 2. 空闲音与极限环

**局限**：直流输入可能出现杂散谱线。
**改进**：抖动（dither）、合理输入偏置、选带抖动的器件[1][5]。

### 3. 基准与电源限制 ENOB

**局限**：手册位数远高于系统有效位数。
**改进**：测实际噪声直方图；优化基准、去耦与接地分割[3]。

### 4. 多通道复用尖峰

**局限**：多路开关切换后滤波器未建立即读数。
**改进**：每通道等待建立；或每通道独立 ADC[4]。

## 总结

Σ-Δ 用过采样与噪声整形服务慢变、高分辨传感器读出。选型看字率、延迟、基准与前端驱动能力，并用实测 ENOB 而非标称位数做系统预算。

## 参考文献

[1] R. Schreier, G. Temes, *Understanding Delta-Sigma Data Converters*.
[2] Analog Devices, MT-022 / Σ-Δ ADC 教程应用笔记.
[3] Texas Instruments, 高精度 ADC 与电桥测量应用笔记.
[4] Microchip / ADI 称重与 RTD 参考设计.
[5] Idle tone 与 dither 技术文献.
[6] IEEE 标准与 ADC 测试方法（ENOB/SNR）.
[7] SAR vs Δ-Σ 选型指南（ADI/TI）.
[8] 开关电容输入驱动与抗混叠放松条件应用笔记.
[9] 工频陷波与数字滤波器配置手册章节.
[10] 电压基准噪声对系统分辨率影响分析.
[11] 热电偶 / RTD 信号链完整参考设计.
[12] Oversampling and noise shaping 经典教材章节.
