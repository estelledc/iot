---
schema_version: '1.0'
id: switched-capacitor-circuit-sensor
title: 开关电容电路在传感器接口中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - sigma-delta-modulator-sensor-readout
  - capacitive-touch-sensor-design
tags:
  - 开关电容
  - CDC
  - 相关双采样
  - MEMS读出
  - 模拟IC
  - 传感器接口
  - 噪声
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 开关电容电路在传感器接口中的应用

> **难度**：🔴 高级 | **领域**：模拟传感器接口 | **关键词**：开关电容, CDC, CDS | **阅读时间**：约 16 分钟

## 日常类比

用水桶量水再倒进量杯——用“电荷包”代替连续电流。开关电容（Switched-Capacitor, SC）电路用时钟控制的电容传输电荷，实现滤波、增益与电容数字转换（Capacitance-to-Digital, CDC）[1][2]。

## 摘要

介绍 SC 电阻等效、积分/增益积木、在 Σ-Δ 与 MEMS/触摸 CDC 中的角色，以及相关双采样（Correlated Double Sampling, CDS）。时钟与 kT/C 噪声为设计核心约束[2][3]。

## 1. 基本思想

开关以频率 \(f_s\) 切换时，电容可等效为电阻 \(R_{eq}\approx 1/(f_s C)\)（理想化）。由此构成滤波器与放大器，且易在 CMOS 工艺集成[1]。

| 积木 | 用途 |
|------|------|
| SC 积分器 | 滤波、Σ-Δ 环路 |
| SC 增益 | 可编程增益 |
| 电荷泵/平衡 | 电容传感读出 |
| CDS | 抑制失调与低频噪声 |

## 2. 传感器接口价值

| 优势 | 说明 |
|------|------|
| 匹配好 | 电容比精度优于电阻比 |
| 可编程 | 改时钟/电容阵列调增益 |
| 与 ADC 同源 | 同芯片 Σ-Δ 前端 |
| 触摸/压力 | CDC 直接数字化微电容变化 |

| 噪声源 | 缓解 |
|--------|------|
| kT/C | 增大 C、过采样 |
| 电荷注入 | 底板采样、虚拟地开关技巧 |
| 时钟抖动 | 低抖动时钟 |
| 衬底耦合 | 布局隔离、差分 |

## 3. 局限、挑战与可改进方向

### 1. 别名与时钟馈通

**局限**：开关动作耦合到敏感节点。
**改进**：差分、时序优化、屏蔽[2]。

### 2. 驱动与建立

**局限**：片外高阻传感器难直接驱动 SC 输入。
**改进**：缓冲；或片外离散前端[3]。

### 3. 功耗随时钟升

**局限**：提高 \(f_s\) 降等效 R 也增动态功耗。
**改进**：按带宽最小时钟；功率门控[1]。

### 4. 设计门槛高

**局限**：离散运放难“手搭”高性能 SC。
**改进**：优先集成 CDC/Σ-Δ 芯片[4]。

## 总结

SC 是现代传感器读出芯片的隐形英雄：用电荷域信号处理微电容与高精度转换。系统工程师重在理解噪声与接口约束，并把细节交给成熟 CDC/ADC。

## 参考文献

[1] Gregorian, Temes, *Analog MOS Integrated Circuits for Signal Processing*.
[2] 开关电容滤波器与噪声分析教材章节.
[3] ADI/TI CDC 与电容传感应用笔记.
[4] MEMS 压力/加速度计读出 ASIC 综述.
[5] Σ-Δ 调制器中 SC 环路滤波器设计.
[6] CDS 在图像与传感器中的应用.
[7] 电荷注入与时钟馈通抑制技术文献.
[8] kT/C 噪声基本推导参考.
[9] 触摸屏 CDC 架构白皮书.
[10] 衬底噪声耦合与隔离布局指南.
[11] 可编程增益 SC PGA 数据手册示例.
[12] IoT 电容液位/压力传感前端案例.
