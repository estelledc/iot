---
schema_version: '1.0'
id: mems-gyroscope-drift-compensation
title: MEMS 陀螺仪零偏漂移补偿算法
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - mems-accelerometer-adxl345
tags:
  - 陀螺仪
  - 零偏
  - 漂移补偿
  - 卡尔曼滤波
  - Allan方差
  - MEMS
  - 传感器融合
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MEMS 陀螺仪零偏漂移补偿算法

> **难度**：🔴 高级 | **领域**：惯性导航 | **关键词**：Bias, Allan, ZUPT, 融合 | **阅读时间**：约 16 分钟

## 日常类比

秒表每次慢一点点，一圈误差就攒出来；天冷天热走速还变。陀螺仪零偏（bias）积分成角度误差——消费级 MEMS 静置一段时间，角度漂移可达数度量级（**视型号与温度，以实测为准**）。不补偿，航向会“走进墙里”[1][2]。

## 摘要

从科里奥利 MEMS 陀螺原理到 Allan 方差噪声项、零偏建模、静止检测/ZUPT、温度补偿与互补/卡尔曼融合。算法参数必须用日志标定，**禁止照抄网络默认值当真理**[3][4]。

## 1. 误差从哪来

| 项 | 含义 |
|----|------|
| 角随机游走 | 白噪声积分 |
| 零偏不稳定性 | 慢漂，Allan 曲线谷区 |
| 速率随机游走 | 更长时漂 |
| 温漂/应力 | 环境与焊接 |

| 工具 | 用途 |
|------|------|
| Allan 方差 | 分解噪声类型、选平均时间 |
| 温度扫 | 建 bias(T) 表 |
| 静止标定 | 估计当前零偏 |

## 2. 补偿策略（IoT 可落地）

| 策略 | 条件 | 说明 |
|------|------|------|
| 上电静止估偏 | 可保证静止 | 简单有效 |
| 温度查找表 | 有温感 | 减慢漂 |
| ZUPT | 步态/车辆可检测静止 | 伪测量刹住积分 |
| 互补滤波 | 有加速度计/磁力计 | 低频姿态靠 accel/mag |
| 卡尔曼/EKF | 资源允许 | 状态含 bias |

资源极紧时：一阶互补 + 间歇静止校准往往优于“空转积分”[5]。

## 3. 局限、挑战与可改进方向

### 1. 静止检测误判

**局限**：缓动被当成静止，把真角速度学进 bias。
**改进**：多阈值（方差+幅值）；仅在确认窗口更新。

### 2. 磁场干扰破坏融合

**局限**：磁力计修正航向时被电机带偏。
**改进**：磁异常检测；室内少依赖 mag；视觉/轮速辅助。

### 3. 温度快速变化

**局限**：查找表滞后。
**改进**：片上温度靠近陀螺；动态估偏；选更稳器件。

### 4. 过度滤波延迟

**局限**：控制环变钝。
**改进**：双路径（控制用宽带，导航用融合）。

## 4. 实践要点

1. 先画 Allan 曲线再谈算法。
2. 记录原始 ω 与温度，离线重放调参。
3. 加速度基础见 `mems-accelerometer-adxl345`。

## 参考文献

[1] IEEE inertial sensor error modeling standards / literature.
[2] Allan variance analysis for gyros (IEEE Std related papers).
[3] TDK/Bosch/ST gyro datasheets — bias and noise specs.
[4] ZUPT aided pedestrian navigation papers.
[5] Complementary filter attitude estimation classics.
[6] Kalman filtering for IMU bias estimation tutorials.
[7] Temperature compensation of MEMS gyros.
[8] Coriolis vibratory gyroscope principle reviews.
[9] Magnetic disturbance detection in AHRS.
[10] Consumer vs tactical grade IMU comparisons.
[11] On-device sensor calibration practices.
