---
schema_version: '1.0'
id: mems-accelerometer-adxl345
title: MEMS加速度计ADXL345原理与运动检测
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 15
prerequisites:
  - mems-fabrication-process-survey
tags:
  - ADXL345
  - MEMS
  - 加速度计
  - 运动检测
  - SPI
  - I2C
  - 倾斜检测
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MEMS加速度计ADXL345原理与运动检测

> **难度**：🟢 初级 | **领域**：惯性传感 | **关键词**：ADXL345, MEMS, Activity, Free-Fall | **阅读时间**：约 15 分钟

## 日常类比

电梯里：静止时脚底主要是重力（静态加速度）；启动上升时多一股推力（动态加速度）。MEMS（Micro-Electro-Mechanical Systems）加速度计像指甲盖上的微型弹簧秤：质量块位移改变梳齿电容，芯片把它变成数字 g 值[1][5]。

## 摘要

介绍电容式 MEMS 结构、ADXL345 量程/接口/片上活动检测，以及倾斜与简易计步思路。噪声、功耗与灵敏度**以 ADI 数据手册为准**[1]。

## 1. 原理与器件

| 概念 | 说明 |
|------|------|
| 静态 g | 重力投影，可测倾角 |
| 动态 g | 运动加速度 |
| 结构 | 质量块 + 弹性梁 + 差分电容 |

| ADXL345 要点 | 典型印象（查手册确认） |
|--------------|------------------------|
| 分辨率 | 最高约 13 位档 |
| 量程 | ±2/±4/±8/±16 g 可选 |
| 接口 | SPI 或 I2C |
| 特色 | Activity / Inactivity / Free-Fall / Tap 等片上检测 |

片上检测可让 MCU 睡，中断醒来——低功耗运动节点常用[1]。

## 2. 配置与应用

| 寄存器组 | 作用 |
|----------|------|
| DATA_FORMAT | 量程、分辨率、自测 |
| BW_RATE | 输出速率与功耗折中 |
| POWER_CTL | 测量模式 |
| INT 相关 | 映射活动/自由落体等到 INT1/2 |

| 应用 | 做法倾向 |
|------|----------|
| 倾角 | 低通重力分量 + atan2 |
| 计步 | 阈值带通 + 阈值 |
| 资产震动 | 活动阈值中断 |
| 跌落 | Free-Fall 阈值 |

对比选型时常看 LIS3DH、BMA400 等：更低功耗或不同封装——按指标表评，不唯品牌[2][4]。

## 3. 局限、挑战与可改进方向

### 1. 噪声与振动混淆

**局限**：车辆/风扇振动触发误活动中断。
**改进**：调阈值与持续时间；机械减振；融合陀螺。

### 2. 偏移与温度

**局限**：零偏随温度变，倾角慢漂。
**改进**：上电校准；温度补偿；选更低漂移器件。

### 3. 带宽不足测冲击

**局限**：采样/内部滤波限制高冲击保真。
**改进**：提高速率；冲击场景选专用高 g 传感器。

### 4. 老型号供货与功耗

**局限**：ADXL345 非最低功耗首选。
**改进**：新设计评估 BMA400 等超低功耗方案。

## 4. 实践要点

1. 先读 WHO_AM_I/器件 ID，再配量程。
2. 安装方向与坐标定义写进固件文档。
3. 工艺背景见 `mems-fabrication-process-survey`。

## 参考文献

[1] Analog Devices, ADXL345 datasheet.
[2] ST, LIS3DH datasheet.
[3] NXP, MMA8452Q datasheet.
[4] Bosch, BMA400 datasheet.
[5] MEMS capacitive accelerometer review papers.
[6] SparkFun ADXL345 hookup guide.
[7] Pedometer algorithm surveys for wearables.
[8] Tilt sensing using accelerometers application notes.
[9] I2C/SPI best practices for IMU modules.
[10] Free-fall detection application notes.
[11] Sensor fusion intro (accel + gyro) overviews.
