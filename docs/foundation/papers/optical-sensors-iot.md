---
schema_version: '1.0'
id: optical-sensors-iot
title: 光电传感器在 IoT 中的应用
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - photodiode-phototransistor-comparison
  - ambient-light-sensor-als
  - lidar-sensor-tof-principles
tags:
  - 光电传感器
  - ToF
  - LiDAR
  - PPG
  - ALS
  - 光纤传感
  - 光谱
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 光电传感器在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：光电子与智能感知 | **关键词**：PD, ToF, PPG, ALS | **阅读时间**：约 20 分钟

## 日常类比

手机在阳光下自动调亮，靠的是环境光传感器——像“数光子的计数器”。高速公路闸机的红外对射则像看不见的绊线：挡光即触发。光电传感器都在把光变成电；接入物联网（Internet of Things, IoT）后，可做农业光照、光电容积脉搏波（Photoplethysmography, PPG）健康监测、飞行时间（Time of Flight, ToF）测距等[1][3]。

## 摘要

对比光电二极管（Photodiode, PD）、光电晶体管与雪崩光电二极管（Avalanche Photodiode, APD），并概述 ToF/激光雷达（LiDAR）、环境光传感（Ambient Light Sensor, ALS）、PPG 与光纤/光谱在 IoT 中的用法。响应度、精度与功耗为常见量级，以器件手册为准[1][2]。

## 1. 探测器基础

光电流 \(I_{ph}=R\cdot P_{opt}\)，响应度 \(R\) 与量子效率、波长相关。硅 PD 近红外响应常较强，可见光需滤光匹配人眼[1]。

| 器件 | 增益量级 | 带宽倾向 | 暗电流倾向 | 典型用途 |
|------|----------|----------|------------|----------|
| PD（PN/PIN） | 1× | 可到很高 | 较低 | 光度、通信 |
| 光电晶体管 | 约 10²–10³ | 较慢 | 较高 | 开关、编码器 |
| APD | 约 10–10³ | 高 | 偏高 | LiDAR、弱光 |

噪声等效功率（Noise Equivalent Power, NEP）与比探测率用于比较灵敏度；计算依赖暗电流、带宽与面积，设计时用手册曲线而非单点公式[1]。

## 2. ToF / LiDAR 与 ALS

| 方案 | 原理 | 距离/成本倾向 | IoT 角色 |
|------|------|---------------|----------|
| dToF | 测脉冲往返 | 更远、成本更高 | 车载/机器人雷达 |
| iToF | 测调制相位 | 近距、成本较低 | 人在检测、满溢、库位 |

多区 ToF（如 8×8 区）可当低分辨率深度图做人流/存在检测；刷新率与功耗强相关，人体检测数 Hz 往往够用[2][8]。

ALS 应尽量匹配明视觉 \(V(\lambda)\)；现代芯片常用可见+红外双通道推算 lux，并自动切换增益/积分时间。强红外环境（白炽/阳光）需算法补偿[1]。

## 3. PPG、光纤与光谱

PPG：LED 照皮肤，PD 收反射/透射，波形随血容变化。绿光偏浅表（腕部常见），红/红外更深。运动伪影是可穿戴主敌，需机械贴合、自适应 LED 电流与滤波/融合加速度计[3][6][7]。

| 应用 | 光学手段 | 注意 |
|------|----------|------|
| 可穿戴心率 | 反射 PPG | 运动伪影、肤色/灌注 |
| 结构健康 | 光纤布拉格光栅等 | 解调仪成本 |
| 农业长势 | 多光谱/NDVI 相关指数 | 标定与大气/角度 |

提高信噪比：加长积分、光调制+同步解调、窄带滤光、必要时制冷降暗电流——均以功耗与时间为代价[1][10]。

## 4. 局限、挑战与可改进方向

### 1. 环境光与多径干扰 ToF

**局限**：强光与镜面反射造成拖尾、假目标。
**改进**：窄带滤光、直方图/多脉冲统计、光学遮光罩[2][8]。

### 2. PPG 临床级精度难

**局限**：消费级 PPG 受运动、温度、接触压力影响大。
**改进**：多波长+IMU 融合；明确非医疗声明与标定协议[3][7]。

### 3. 功耗与常开矛盾

**局限**：LED/激光与高频测距使电池节点难常开。
**改进**：事件触发、降频、ALS 优先积分时间而非盲目加增益[10]。

### 4. 光谱指数易被误用

**局限**：NDVI 等受光照几何与传感器通道匹配影响。
**改进**：现场定标、固定几何、记录元数据；勿把指数当绝对生物量[9]。

## 总结

光电 IoT 选型先定物理量（照度、距离、脉搏、光谱），再选 PD/ToF/ALS/PPG 模组，并把环境光、功耗与标定写进验收。探测器灵敏不等于系统准确。

## 参考文献

[1] Hamamatsu, Photodiode Technical Guide.
[2] STMicroelectronics, VL53 系列 ToF 数据手册.
[3] Castaneda et al., Wearable PPG sensors review, Sensors, 2018.
[4] AMS-OSRAM, 多光谱传感器数据手册（如 AS7341）.
[5] Measures, Structural Monitoring with Fiber Optic Technology.
[6] Allen, Photoplethysmography in clinical measurement, Physiol. Meas., 2007.
[7] 运动伪影抑制与 PPG 深度学习相关 IEEE 文献.
[8] LiDAR 扫描机制综述（Electronics 等）.
[9] Mulla, Remote sensing in precision agriculture 综述.
[10] 超低功耗光学传感相关 Nature Electronics / 产业白皮书.
[11] VEML7700 / TSL2591 等 ALS 数据手册.
[12] 锁相放大与光学调制抗干扰应用笔记.
