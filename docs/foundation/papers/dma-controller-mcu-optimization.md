---
schema_version: '1.0'
id: dma-controller-mcu-optimization
title: DMA控制器在MCU数据搬运中的优化策略
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - adc-dma-continuous-sampling
  - mcu-memory-map-flash-ram
tags:
  - DMA
  - 零拷贝
  - Circular
  - Cache一致性
  - ADC
  - UART
  - STM32
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# DMA控制器在MCU数据搬运中的优化策略

> **难度**：🟡 中级 | **领域**：嵌入式数据传输 | **阅读时间**：约 14 分钟

## 日常类比

厨师（CPU）若亲自端菜，炒菜时间被占光。DMA（Direct Memory Access）像专职传菜员：配置好源/目的/长度后自动搬数，搬完再打断厨师。ADC、UART、SPI 连续流最吃这个分工[1][2]。

## 摘要

大块连续数据优先 DMA；小而稀的用中断/轮询即可。模式选 Normal / Circular / 双缓冲；注意通道映射、优先级与 Cortex-M7 上 D-Cache 一致性。占用与耗时表为示意，**随主频、总线矩阵与编译选项变化**[1][3]。

## 1. 何时用

| 对比 | CPU 搬 | DMA |
|------|--------|-----|
| 执行者 | 指令循环 | 独立控制器 |
| CPU 占用 | 高 | 配置后通常极低 |
| 确定性 | 受中断抖动 | 硬件节奏更稳 |
| 适合 | 少量/不规则 | 大块/连续流 |

经验阈值：连续且明显大于十余字节的流优先 DMA；变长帧用 DMA + IDLE 等辅助[2]。

## 2. 模式与通道

| 模式 | 行为 | 场景 |
|------|------|------|
| Normal | 满 N 停止 | 单次发送 |
| Circular | 回绕持续 | ADC 连续采样 |
| Double-buffer | 硬件切缓冲 | 需边收边算 |

方向：P2M / M2P / M2M。STM32 类器件 Stream/Channel 映射固定，冲突要查手册。仲裁：软件优先级 + 同级硬件编号；实时采样高于低速日志[1][4]。

FIFO 合并窄外设访问为宽总线事务；Burst（INCR4/8/16）提吞吐但拉长不可抢占窗口，硬实时宜保守[4]。

## 3. 典型场景

- **ADC**：Circular + 半传输/全传输中断，缓冲 ≥ 处理时间×速率×2。
- **UART 变长帧**：Circular 收 + IDLE 算长度。
- **SPI 全双工**：TX/RX 各一通道；只收也要发 dummy 产时钟。

H7 等 MDMA 链表适合多段不连续搬移[5]。

## 4. Cache 一致性（Cortex-M7 等）

DMA 走总线看的是存储，CPU 可能看 D-Cache 副本：TX 前 Clean，RX 后 Invalidate；或把缓冲放 Non-Cacheable（MPU）；或关 D-Cache（简单但伤性能）。地址宜按 cache line 对齐[3][6]。

| 方案 | 性能 | 复杂度 |
|------|------|--------|
| 关 D-Cache | 低 | 低 |
| Non-Cacheable 区 | 中 | 中（常用） |
| 手动维护 | 高 | 高 |

## 5. 局限、挑战与可改进方向

### 1. 全外设开 DMA 却撞通道

**局限**：静默失败或错误外设被服务。
**改进**：启动前核对 request mapping 表[1]。

### 2. Circular 消费慢于生产

**局限**：未处理数据被覆盖。
**改进**：加大缓冲、HT/TC 双阶段处理、监控过载标志[2]。

### 3. M7 上忽略 Cache

**局限**：偶发错数，难复现。
**改进**：MPU 非缓存区或成对 Clean/Invalidate[3][6]。

### 4. Burst 过大拖死实时通道

**局限**：高优先级也要等长 burst。
**改进**：限制 burst；关键通道更高优先级与分 bank SRAM[4][5]。

## 6. 实践要点

1. 先画数据路径与通道分配表再写代码。
2. ADC/音频默认 Circular + 双半区。
3. 凡带 D-Cache 的核，DMA 缓冲策略写进编码规范。

## 参考文献

[1] ST, RM0090 — DMA controller chapters.
[2] ST, AN4839 DMA controller guidelines.
[3] Armv7-M Architecture Reference Manual — memory/cache model.
[4] ST DMA FIFO/burst application notes.
[5] ST, RM0433 — MDMA linked-list.
[6] Joseph Yiu, Cortex-M7 memory system guidance.
[7] STM32 HAL ADC/UART/SPI DMA examples.
[8] AHB bus matrix contention / SRAM bank notes (H7 class).
[9] UART IDLE + DMA reception application notes.
[10] Cache maintenance API alignment requirements.
[11] Vendor DMA request mapping tables (F4/F7/H7).
