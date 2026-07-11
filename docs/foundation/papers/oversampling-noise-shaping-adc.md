---
schema_version: '1.0'
id: oversampling-noise-shaping-adc
title: 过采样与噪声整形提升ADC有效位数
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - adc-sar-vs-sigma-delta
  - adc-resolution-snr-enob
  - anti-aliasing-filter-design
tags:
  - 过采样
  - Sigma-Delta
  - 噪声整形
  - ENOB
  - CIC滤波器
  - ADC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 过采样与噪声整形提升ADC有效位数

> **难度**：🟡 中级 | **领域**：数据转换 | **关键词**：OSR, Σ-Δ, ENOB, CIC | **阅读时间**：约 18 分钟

## 日常类比

嘈杂菜市场用手机录音：只录一瞬，人声与噪声糊在一起；若长时间录同一句话再平均，噪声趋于抵消、人声更清晰。过采样（oversampling）把量化噪声摊到更宽频带，再用数字滤波砍掉带外噪声；Σ-Δ（Sigma-Delta）进一步把噪声“推”向高频——即噪声整形（noise shaping）[1][3]。

## 摘要

推导过采样率（Oversampling Ratio, OSR）对信噪比（Signal-to-Noise Ratio, SNR）的增益，说明一阶/高阶整形与抽取滤波，并给出微控制器（MCU）实现边界。公式基于常用白噪声量化模型，直流小信号时模型可能失效[2][3]。

## 1. 量化噪声与过采样

带限 \(f_b\) 信号奈奎斯特速率约 \(2f_b\)。\(N\) 位模数转换器（ADC）量化步长与满幅相关；均匀量化误差模型下，噪声功率谱密度随 \(f_s\) 摊薄。OSR \(= f_s/(2f_b)\)。纯过采样（无整形）理想情况下每 4× OSR 约得 +1 bit 有效位数量级（约 +6 dB SNR/倍频程的一半关系），实际受热噪声、抖动、电源限制[1][2]。

| 手段 | SNR/分辨率倾向 | 代价 |
|------|----------------|------|
| 提高标称位数 | 直接 | 芯片成本/速度 |
| 纯过采样+平均 | 每 4× OSR ~+1 bit 量级 | 吞吐下降、CPU/DMA |
| Σ-Δ 整形 | 同 OSR 收益更大 | 模拟环路/延迟 |

## 2. 噪声整形与抽取

Σ-Δ 用过采样比较器/量化器加反馈环，把量化噪声高通化。阶数越高带内抑制越强，但稳定性与系数敏感度上升；多级（MASH）可缓解单环稳定问题却对失配敏感[3][5]。

数字端常用级联积分梳状（Cascaded Integrator-Comb, CIC）或 FIR 抽取，把高速率 1-bit/低位数流变成奈奎斯特速率高位数。通带平坦度与混叠抑制决定最终有效位数（Effective Number of Bits, ENOB）[1]。

| 阶数（示意） | 带内噪声抑制倾向 | 设计难度 |
|--------------|------------------|----------|
| 0（纯过采样） | 最弱 | 低 |
| 1 阶整形 | 中 | 中 |
| 2+ 阶 / MASH | 强 | 高 |

## 3. MCU 工程路径

| 路径 | 做法 | 适合 |
|------|------|------|
| 片上过采样 | SAR ADC 硬件累加/平均 | 多要 1–3 bit、低频 |
| 外置 Σ-Δ | 调制器 + SPI + 软件 CIC | 隔离/高精度前端 |
| 集成 Σ-Δ ADC | 成品转换器 | 计量/工业 |

收益递减：时钟抖动、参考噪声、前端运放会先于“理论 bit”封顶。kHz 以下、多要数 bit 时过采样最划算；精密计量仍优先专用 Σ-Δ[4]。

## 4. 局限、挑战与可改进方向

### 1. 白噪声模型在近直流失效

**局限**：缓慢信号不充分穿越码阶时，平均无法降量化误差。
**改进**：加抖动（dither）；保证前端有足够交流激励[2]。

### 2. OSR 换带宽

**局限**：分辨率升则输出速率降，不适合快控制环。
**改进**：降目标 bit；或换更快高位数 ADC[4]。

### 3. 高阶环路不稳定

**局限**：过载或系数漂移导致限幅振荡。
**改进**：限制输入幅度；用成熟 MASH/商用芯片[3]。

### 4. 数字滤波延迟与资源

**局限**：深抽取增加群时延与 RAM/CPU。
**改进**：硬件 CIC；缩短级数并接受旁瓣折中[4]。

## 总结

过采样摊薄噪声，Σ-Δ 再整形；工程上先算噪声预算再堆 OSR。MCU 片上过采样适合小幅提精度，高精度走专用转换器。

## 参考文献

[1] Maxim, Demystifying Delta-Sigma ADCs (AN1870).
[2] Kester, Data Conversion Handbook（过采样章节）.
[3] Schreier & Temes, Understanding Delta-Sigma Data Converters.
[4] ST, AN5137 Oversampling on STM32 ADC.
[5] Candy & Temes, Oversampling Delta-Sigma Data Converters.
[6] Analog Devices, Σ-Δ ADC 基础教程.
[7] CIC 滤波器 Hogenauer 经典论文/应用笔记.
[8] ADC 时钟抖动与 SNR 关系应用笔记.
[9] MASH 结构综述文献.
[10] ENOB/SINAD 测试方法（IEEE ADC 标准相关）.
[11] 抗混叠滤波与过采样系统联合设计笔记.
[12] 参考电压噪声对过采样增益的限制分析.
