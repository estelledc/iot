---
schema_version: '1.0'
id: photodiode-phototransistor-comparison
title: 光电二极管与光电晶体管对比选型
layer: 1
content_type: comparison
difficulty: beginner
reading_time: 16
prerequisites:
  - optical-sensors-iot
  - op-amp-selection-iot-sensor
  - ambient-light-sensor-als
tags:
  - 光电二极管
  - 光电晶体管
  - 跨阻放大器
  - 光谱响应
  - 光传感
  - 线性度
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 光电二极管与光电晶体管对比选型

> **难度**：🟢 初级 | **领域**：光电器件 | **关键词**：PD, PT, TIA, 响应度 | **阅读时间**：约 16 分钟

## 日常类比

雨中接水：敞口杯水位与雨强近似成正比——像光电二极管（Photodiode, PD），一光子对应量级确定的光电流。若杯下接水泵放大水流，灵敏度高了却难反推真实雨量——像光电晶体管（Phototransistor, PT）。判断亮/暗用 PT 方便；要准测勒克斯，回到 PD + 跨阻放大器（Transimpedance Amplifier, TIA）[1][4]。

## 摘要

对比 PD/PT 的增益、线性、速度与电路，并给出光谱与 TIA 要点。参数以具体型号数据手册为准[5][6]。

## 1. 原理要点

内光电效应：光子能量大于带隙则产生电子-空穴对。PD 可光伏或光导（反偏）模式；反偏更快、暗电流更大。PT 本质是光控双极晶体管，光电流经 β 放大[1][2]。

| 维度 | 光电二极管 | 光电晶体管 |
|------|------------|------------|
| 增益 | ≈1（外加电路放大） | 约 10²–10³ 量级 |
| 线性 | 优 | 一般，饱和易出现 |
| 速度 | 可到很高（PIN） | 常慢（结电容+β） |
| 电路 | 需 TIA/运放 | 可简单电阻上拉 |
| 温度稳定 | 相对更好控 | β 温漂明显 |

## 2. 光谱与电路

硅响应峰常在近红外；可见光传感需滤光或专用芯片。TIA：\(V_o=-I_{ph}R_f\)，并联 Cf 防振荡；Rf 大则噪声与稳定性更敏感[3][7]。

| 应用 | 更合适 |
|------|--------|
| 精密光度/分析 | PD + TIA |
| 开关、编码器、有无检测 | PT |
| 高速光通信 | PIN PD（非 PT） |

## 3. 局限、挑战与可改进方向

### 1. PT 当精密光度计

**局限**：非线性与温漂毁掉校准。
**改进**：改 PD；或只用阈值检测[4]。

### 2. TIA 振荡与噪声

**局限**：大 Rf + 输入电容自激。
**改进**：补偿电容、选合适 GBW 运放[3]。

### 3. 环境光淹没信号

**局限**：直流光背景淹调制信号。
**改进**：光学滤波、调制光源+同步解调[2]。

### 4. 近红外泄漏

**局限**：硅 PD“看见”IR，可见光读数偏。
**改进**：IR 截止滤光；用专用 ALS 芯片[4][5]。

## 总结

要线性与速度选 PD；要简单开关灵敏度选 PT。IoT 计量类光传感默认 PD+TIA，开关类才用 PT。

## 参考文献

[1] Sze & Ng, Physics of Semiconductor Devices.
[2] Wilson & Hawkes, Optoelectronics: An Introduction.
[3] Texas Instruments, Transimpedance Amplifier Design (SBOA122 等).
[4] Vishay, Photodiode and Phototransistor Application Notes.
[5] OSRAM 等, PIN 光电二极管数据手册（代表型号）.
[6] Everlight 等, 光电晶体管数据手册（代表型号）.
[7] Coughlin & Driscoll, Operational Amplifiers and Linear Integrated Circuits.
[8] Hamamatsu, Photodiode Technical Guide.
[9] 光伏 vs 光导模式应用笔记.
[10] 光电编码器传感器选型指南.
[11] ALS 滤光与人眼匹配文献.
[12] TIA 噪声分析应用笔记.
