---
schema_version: '1.0'
id: spi-protocol-modes-timing
title: SPI协议四种模式与时序参数详解
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - i2c-vs-spi-selection-guide
  - nor-flash-spi-qspi-xip
tags:
  - SPI
  - CPOL
  - CPHA
  - 时序
  - DMA
  - QSPI
  - 嵌入式总线
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# SPI协议四种模式与时序参数详解

> **难度**：🟡 中级 | **领域**：板级总线 | **关键词**：SPI, CPOL, CPHA, Mode 0–3 | **阅读时间**：约 16 分钟

## 日常类比

分拣中心传送带按节拍转（时钟 SCLK），包裹上下（MOSI/MISO），被点名的分拣员才动手（片选 CS）。串行外设接口（Serial Peripheral Interface, SPI）用这组线做高速同步传输[1][2]。

## 摘要

讲清时钟极性（CPOL）与相位（CPHA）定义的四种模式、片选与多从机、时序裕量与 DMA。器件“Mode 0/3”标注以数据手册时序图为准，名称偶有混用[2]。

## 1. 信号与模式

| 信号 | 角色 |
|------|------|
| SCLK | 主机产生时钟 |
| MOSI | 主机→从机 |
| MISO | 从机→主机 |
| CS/SS | 从机选择，通常低有效 |

| 模式 | CPOL | CPHA | 常见用途倾向 |
|------|------|------|----------------|
| 0 | 0 | 0 | 很多传感器默认 |
| 1 | 0 | 1 | 部分器件 |
| 2 | 1 | 0 | 较少 |
| 3 | 1 | 1 | Flash 等常见 |

CPOL=空闲电平；CPHA=采样边沿相对（第一/第二边沿）——务必对照波形，不要只背数字[1]。

## 2. 时序与系统

关注 t_SU/t_H、CS 建立/保持、最大频率与布线电容。多从机独立 CS；避免从机 MISO 冲突。长线降频或加串阻[3]。

| 技术 | 作用 |
|------|------|
| DMA | 卸载 CPU，维持吞吐 |
| 双缓冲 | 连续传输 |
| QSPI/OSPI | 多数据线加速 Flash |
| 模式故障检测 | 主机配置错误保护（视 MCU） |

## 3. 与 I²C 快对照

| 维度 | SPI | I²C |
|------|-----|-----|
| 速率 | 常更高 | 较低 |
| 线数 | 4+CS | 2 |
| 地址 | CS 硬件选 | 地址字节 |
| 上拉 | 非必须 | 必须 |

## 4. 局限、挑战与可改进方向

### 1. 模式配错静默失败

**局限**：通信“通”但数据移位错。
**改进**：逻辑分析仪对手册波形；从低速验证[2][4]。

### 2. CS 软件抖动

**局限**：位 bang CS 破坏建立时间。
**改进**：用硬件 NSS 或 GPIO+精确时序，DMA 期间保持 CS[3]。

### 3. 多从机电容负载

**局限**：时钟边沿变缓致采样失败。
**改进**：降频、缓冲、短星型布线[3]。

### 4. 与低功耗冲突

**局限**：高速时钟增加动态功耗。
**改进**：按需提频；传完门控 SPI 时钟[5]。

## 总结

SPI 的坑多半在模式与时序而非“会不会发字节”。先对齐 Mode 与 CS 时序，再用 DMA/QSPI 要吞吐。

## 参考文献

[1] Motorola/Freescale SPI 经典规范描述与后续 MCU 手册.
[2] 各传感器/Flash 数据手册 SPI 时序图.
[3] 高速 SPI 布线与信号完整性应用笔记.
[4] 逻辑分析仪解码 SPI 实践.
[5] MCU 低功耗下外设时钟门控文档.
[6] STM32 SPI HAL/LL 应用笔记.
[7] Quad-SPI / XIP 设计指南.
[8] I2C vs SPI 选型文章.
[9] DMA 与 SPI 连续传输示例.
[10] 多从机总线拓扑建议.
[11] 建立保持时间裕量计算方法.
[12] 工业环境 SPI 隔离与电平转换注意.
