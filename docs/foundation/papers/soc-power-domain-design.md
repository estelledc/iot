---
schema_version: '1.0'
id: soc-power-domain-design
title: SoC电源域划分与低功耗架构
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - power-gating-clock-gating-techniques
  - power-sequencing-multi-rail
  - sleep-mode-hierarchy-mcu
tags:
  - 电源域
  - Power Gating
  - SoC
  - 低功耗
  - 隔离单元
  - 电压域
  - IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# SoC电源域划分与低功耗架构

> **难度**：🔴 高级 | **领域**：SoC 电源架构 | **关键词**：Power Domain, 电源门控, 隔离 | **阅读时间**：约 18 分钟

## 日常类比

酒店分区供电：走廊常亮，客房走人断电。片上系统（System on Chip, SoC）把电路划成电源域（Power Domain），不用的域切断电源（Power Gating），用隔离单元防止“断电输出”污染仍上电逻辑[1][2]。

## 摘要

讲解电源域/电压域、时钟门控与电源门控差异、上电顺序与状态保持（retention），以及物联网（IoT）应用处理器常见域划分。漏电与唤醒延迟为工艺与实现相关量级[2][3]。

## 1. 域的概念

| 概念 | 含义 |
|------|------|
| 电源域 | 可独立开关的供电区域 |
| 电压域 | 可不同标称电压（DVFS） |
| Always-on | 常开：RTC、唤醒逻辑、少量 SRAM |
| Retention | 掉主电仍保持的寄存器/内存 |

时钟门控降动态功耗；电源门控降漏电，但引入隔离、缓冲与唤醒代价[1]。

## 2. 关键单元

| 单元 | 作用 |
|------|------|
| Isolation cell | 钳位断电域输出 |
| Level shifter | 跨电压域电平转换 |
| Power switch | 头/脚开关切电源 |
| Retention latch | 保存关键状态 |

上电顺序：先常开与隔离有效 → 目标域上电稳定 → 解除隔离 → 释放复位。顺序反了会总线卡死或闩锁风险（视工艺）[3]。

## 3. IoT SoC 典型划分

| 域 | 内容 |
|----|------|
| AON | 唤醒、RTC、电源管理状态机 |
| CPU | 应用核，可深睡断电 |
| 外设 | UART/SPI 等分组 |
| 无线 | Modem 独立供电 |
| 存储器 | 银行级 retention 策略 |

| 策略 | 动态功耗 | 漏电 | 唤醒 |
|------|----------|------|------|
| 仅时钟门控 | ↓ | 仍在 | 快 |
| 电源门控 | ↓↓ | ↓↓ | 较慢 |
| DVFS | ↓ | 视电压 | 中 |

## 4. 局限、挑战与可改进方向

### 1. 域过多增加验证成本

**局限**：隔离/时序边角爆炸。
**改进**：域数量克制；形式化检查隔离与复位[2][4]。

### 2. 唤醒延迟影响体验

**局限**：频繁短唤醒不适合深断电。
**改进**：按事件统计选层级；热路径保留浅睡[3]。

### 3. 软件不知电源状态

**局限**：驱动访问已断电外设导致挂死。
**改进**：运行时电源管理框架与引用计数[5]。

### 4. 电源完整性

**局限**：大开关同时上电冲击。
**改进**：分步上电、软启动开关、足够去耦[6]。

## 总结

电源域是 SoC 低功耗的骨架：常开最小化、隔离正确、软硬件契约清晰。IoT 产品用事件画像选择门控深度，而不是默认“能断尽断”。

## 参考文献

[1] ARM, Power Management 与 UPF 相关白皮书概述.
[2] IEEE 1801 (UPF) 低功耗设计意图标准.
[3] 商业 IoT SoC 技术参考手册电源章节（ESP/nRF/STM32U5 等）.
[4] 低功耗实现与签核实践（隔离/电平转换检查）.
[5] Linux Runtime PM / Zephyr 电源管理文档.
[6] 片上电源开关与 PDN 完整性应用笔记.
[7] Retention SRAM 与状态保存策略文献.
[8] DVFS 与功耗模型基础.
[9] 时钟门控 vs 电源门控对比教程.
[10] 唤醒延迟测量方法.
[11] 多轨上电时序与电源好（Power Good）设计.
[12] IoT 漏电随温度变化的数据手册阅读注意.
