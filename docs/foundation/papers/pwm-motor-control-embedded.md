---
schema_version: '1.0'
id: pwm-motor-control-embedded
title: PWM电机控制在嵌入式IoT执行器中的应用
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 15
prerequisites: UNKNOWN
tags:
  - PWM
  - 电机控制
  - 占空比
  - H桥
  - 死区时间
  - 嵌入式
  - 执行器
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# PWM电机控制在嵌入式IoT执行器中的应用

> **难度**：🟢 入门 | **领域**：电机控制基础 | **关键词**：PWM, 占空比, H桥, 死区 | **阅读时间**：约 15 分钟

## 日常类比

花洒水龙头近似只有开/关，但快速点动可调出水量：开得久水量大。**脉宽调制**（Pulse Width Modulation, PWM）用开关管的导通时间占比（占空比）控制电机平均电压，从而调速——管脚仍是数字电平[1][2]。

## 摘要

覆盖 PWM 基本量、直流有刷/简易无刷驱动、H 桥与死区、微控制器定时器配置、开环与比例积分（PI）闭环，以及续流与保护。频率与电流数字为量级，随电机与负载变化[3]。

## 1. PWM 基础

周期 \(T\)、高电平时间 \(t_{\mathrm{on}}\)，占空比 \(D=t_{\mathrm{on}}/T\)。平均电压约 \(D\cdot V_{\mathrm{bus}}\)（忽略管压降）。频率过低可闻噪声与转矩脉动；过高则开关损耗与电磁干扰（EMI）上升[1]。

| 参数 | 选型倾向 |
|------|----------|
| 频率 | 常数十 kHz 量级避开可闻区，视驱动与电机 |
| 分辨率 | 定时器计数决定占空比步进 |
| 极性 | 高有效/低有效与驱动芯片匹配 |

## 2. 功率级

小风扇可用单管+续流二极管；正反转需 H 桥。上下管必须插入**死区**，防止直通短路。逻辑与功率地、自举电容、电流采样电阻布局影响可靠性与测量[2][4]。

| 拓扑 | 用途 |
|------|------|
| 低边开关 | 单向调速 |
| H 桥 | 正反转、制动 |
| 半桥×3 | 三相无刷（需换相） |

## 3. 控制与 MCU

开环：占空比映射转速，带载后掉速明显。闭环：测转速（编码器/测速发电机/反电动势）做 PI。物联网场景常“慢速阀门/风扇”，优先可靠保护而非极致带宽[3][5]。

保护：过流关断、欠压锁定、堵转超时、温度降额；软件看门狗与硬件刹车输入并用。

## 4. 局限、挑战与可改进方向

### 1. 开环带载精度差

**局限**：同一占空比转速随负载大变。
**改进**：加反馈做速度/电流环；或限位开关定位[5]。

### 2. 直通与死区不当

**局限**：死区过小炸管；过大导致非线性。
**改进**：按驱动手册设死区；示波查桥臂中点[4]。

### 3. EMI 与地弹

**局限**：大 di/dt 干扰射频与传感器。
**改进**：慢化开关、吸收电路、短功率环、分区地[6]。

### 4. 续流与感性尖峰

**局限**：缺续流路径击穿开关管。
**改进**：正确续流二极管/同步整流；钳位[2]。

## 总结

IoT 执行器 PWM 的关键是安全功率级 + 合适频率/死区 + 按需闭环与保护；先保证不炸机，再谈调速手感。

## 参考文献

[1] PWM fundamentals in motor drive application notes.
[2] H-bridge driver datasheets (dead time, bootstrap).
[3] DC motor speed control: open-loop vs closed-loop.
[4] Shoot-through prevention and dead-time measurement.
[5] MCU timer PWM configuration guides (STM32/nRF/ESP class).
[6] EMI reduction for switched motor loads.
[7] Current sensing shunts for motor protection.
[8] Freewheeling paths for inductive loads.
[9] PI tuning basics for speed loops.
[10] Thermal design of small motor drivers.
[11] Brushed vs BLDC drive complexity for IoT actuators.
[12] Stall detection and overcurrent fault handling.
