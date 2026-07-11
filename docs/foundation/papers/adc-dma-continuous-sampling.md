---
schema_version: '1.0'
id: adc-dma-continuous-sampling
title: ADC+DMA连续采样实时数据采集系统设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - dma-controller-mcu-optimization
  - adc-sar-vs-sigma-delta
tags:
  - ADC
  - DMA
  - 连续采样
  - 双缓冲
  - 定时器触发
  - 过采样
  - STM32
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# ADC+DMA连续采样实时数据采集系统设计

> **难度**：🟡 中级 | **领域**：数据采集系统 | **阅读时间**：约 16 分钟

## 日常类比

流水线：原料（模拟量）进机器（ADC）成半成品，传送带（直接存储器访问，Direct Memory Access, DMA）自动入库，质检员（CPU）只在半仓/满仓时处理一批。硬件完成“转换+搬运”，CPU 专注算法[1][2]。

## 摘要

说明为何单次轮询不够、循环 DMA + 双缓冲（乒乓）、定时器触发稳采样率、多通道扫描解交织、过采样与 Cache 一致性。采样率与精度数字为**器件量级**，以时钟树与手册为准[1][3]。

## 1. 需求与 DMA 角色

| 应用线索 | 采样率量级 | 要点 |
|----------|------------|------|
| 振动 | kSPS–十 kSPS | 持续频谱 |
| 音频 | 八–四十八 kSPS | 流式 |
| 电能质量 | 十–百 kSPS | 同步 |
| 心电等 | 数百 SPS | 低速不断 |

轮询单次转换：间隔抖动大、高速率时 CPU 打满。DMA 在外设与内存间搬数；**Circular** 模式写到末尾绕回，是连续采样关键[1]。

## 2. 双缓冲与触发

半传输/全传输中断：CPU 处理刚写完的半区，DMA 写另一半，避免覆盖[2]。

```
缓冲区: [====A====|====B====]
中断:    半满处理A   满处理B
```

缓冲长度 ≥ 最长处理时间内产生的样本数。回调内只置标志，重活放主循环/任务。

| 触发 | 速率稳定性 | 用途 |
|------|------------|------|
| ADC 连续 | 一般 | 粗采 |
| 定时器 TRGO | 高（晶振限制） | 频谱/计量 |
| 软件 | 差 | 单次 |

多通道扫描时 DMA 缓冲交错存放，处理前解交织。过采样（如 4×/16×）可换约 1–2 bit 量级噪声改善，代价是有效吞吐下降——且不修复失真[3][5]。

## 3. 常见坑

| 问题 | 处理线索 |
|------|----------|
| DMA 优先级低 | 抬高 ADC DMA 优先级 |
| 对齐/位宽错 | 右对齐 + half-word |
| Cortex-M7 D-Cache | 处理前 Invalidate 缓冲 |
| 采样时间不够 | 高源阻加长采样周期 |

模拟供电（VDDA）滤波、ADC 时钟不超手册上限，写入检查清单[3]。

## 4. 局限、挑战与可改进方向

### 1. 半满标志丢失

**局限**：处理过慢导致连续半满，数据间隙。
**改进**：加大缓冲；处理下移 DMA/轻量 ISR；测最坏执行时间。

### 2. 用连续模式做精密频谱

**局限**：采样时钟不稳，谱线泄漏。
**改进**：定时器触发；必要时外部低抖动时钟。

### 3. 忽略 Cache

**局限**：M7 上读到陈旧样本，难复现。
**改进**：缓冲放非 Cache 区或显式维护一致性[4]。

### 4. 过采样当“免费位数”

**局限**：对 THD/1/f 无效，还拖垮实时性。
**改进**：先看 ENOB 瓶颈；过采样只作噪声预算一项。

## 5. 实践要点

1. 标准骨架：定时器触发 + ADC 扫描 + DMA Circular + 乒乓。
2. 用逻辑分析仪/GPIO 翻转测处理时限。
3. 打包上传前做通道校验和与时间戳。

## 参考文献

[1] STMicroelectronics, STM32 reference manuals — ADC and DMA chapters.
[2] ST, AN3116, STM32 ADC modes and their applications.
[3] ST, AN4235, How to improve ADC accuracy.
[4] ARM, Cortex-M7 Technical Reference Manual — cache coherency.
[5] W. Kester, Data Conversion Handbook — sampling and averaging.
[6] STM32 HAL ADC Start_DMA and circular mode application notes.
[7] Nyquist sampling and anti-aliasing companion guidance.
[8] Multi-channel ADC scan timing diagrams (vendor training).
[9] FreeRTOS/ISR best practices for DMA half-complete flags.
[10] Oversampling and decimation app notes (TI/ST).
[11] Power integrity for VDDA in mixed-signal MCU designs.
