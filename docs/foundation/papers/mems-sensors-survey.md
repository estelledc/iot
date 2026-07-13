---
schema_version: '1.0'
id: mems-sensors-survey
title: MEMS 传感器技术综述
layer: 1
content_type: survey
difficulty: intermediate
reading_time: 18
prerequisites:
  - mems-accelerometer-adxl345
  - mems-gyroscope-drift-compensation
tags:
  - MEMS
  - IMU
  - 加速度计
  - 陀螺仪
  - 气压计
  - 麦克风
  - 传感器选型
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MEMS 传感器技术综述

> **难度**：🟡 中级 | **领域**：微机电系统、传感器 | **关键词**：MEMS, IMU, 气压计, 麦克风 | **阅读时间**：约 18 分钟

## 日常类比

手机自动旋转、计步、气压估楼层，靠的是把机械结构缩到微米级、刻在硅片上的 **MEMS**（Micro-Electro-Mechanical Systems，微机电系统）。像沙粒大小的“跷跷板”质量块因惯性偏移，电容变化变成电信号——这就是加速度计的直觉[1][2]。

## 摘要

综述 MEMS 惯性、压力、气体与麦克风路线，对比消费/车规差异与选型要点。份额、灵敏度与功耗数字为公开资料常见量级，以现行数据手册与认证状态为准[3][4]。

## 1. 基础与分类

MEMS：微米级机械结构 + 半导体工艺批量制造，常与 ASIC（Application-Specific Integrated Circuit）同封装。

| 类型 | 典型物理量 | IoT 常见用途 |
|------|------------|--------------|
| 惯性 | a、ω | 姿态、振动、计步 |
| 压力 | 气压/差压 | 高度、暖通、液位辅助 |
| 声学 | 声压 | 语音、异常声检测 |
| 气体/环境 | 气体、温湿 | IAQ（Indoor Air Quality） |
| 光学 MEMS | 镜面/光路 | 投影、激光雷达扫描 |

## 2. IMU 与融合

加速度计多电容式质量块；陀螺仪多科氏力驱动结构。六轴 IMU（Inertial Measurement Unit）= 三轴加速度 + 三轴陀螺；九轴再加磁力计。

| 维度 | 消费级量级 | 车规/工业倾向 |
|------|------------|----------------|
| 噪声/零偏 | 可接受日常姿态 | 更严、温漂与寿命要求高 |
| 接口 | I²C/SPI | 常带诊断与冗余 |
| 认证 | 无/消费 | AEC-Q100 等路径 |

短时姿态可用互补滤波；长时导航需与磁力计/GNSS（Global Navigation Satellite System）等融合，抑制陀螺漂移[5][6]。

## 3. 气压、气体与麦克风

MEMS 气压计：膜片形变 → 电容/压阻；室内楼层分辨依赖噪声、温补与安装密封，宣称“厘米级”须场景实测[4]。

| 气体路线 | 特点 | 注意 |
|----------|------|------|
| MOX | 便宜、加热功耗 | 交叉敏感 |
| 电化学 | 选择性较好 | 寿命/温湿 |
| NDIR 等光学 | CO₂ 等更稳 | 体积与成本 |

MEMS 麦克风：振膜 + 背板电容；阵列做波束形成。SNR（Signal-to-Noise Ratio）、AOP（Acoustic Overload Point）与封装声孔决定可用性[7]。

## 4. 车规、可穿戴与趋势

车规强调温度、振动、功能安全与长期漂移；可穿戴强调 μA 级平均电流与小封装。趋势：片上预处理/AI 特征、柔性衬底、能量收集 MEMS——成熟度参差，量产仍看供应链与标定成本[8][9]。

| 选型检查 | 要点 |
|----------|------|
| 量程/带宽 | 覆盖冲击与振动谱 |
| 功耗占空比 | 采样率 × 工作电流 |
| 封装与应力 | PCB 弯曲致零偏 |
| 标定与温补 | 出厂 vs 现场 |

## 5. 局限、挑战与可改进方向

### 1. 漂移与温湿耦合

**局限**：陀螺零偏、气压温漂使开环积分快速发散。
**改进**：周期用磁力计/GNSS/静止检测校正；查数据手册温漂曲线并做现场标定[5][6]。

### 2. 封装应力与安装

**局限**：回流焊与壳体应力改变零点。
**改进**：遵循厂商布局；软件存偏移；关键件做应力隔离[3]。

### 3. 气体选择性不足

**局限**：低成本 MOX 交叉敏感，难当“单一气体真值”。
**改进**：阵列 + 模式识别，或换电化学/NDIR 针对目标气体[10]。

### 4. 车规与消费混用

**局限**：消费料在车载温振下寿命与诊断不足。
**改进**：按环境选 AEC 器件；加看门狗与冗余通道[8]。

## 总结

MEMS 把机械感知做成可批量的硅器件，是 IoT 姿态、环境与声学的底座。选型看量程、噪声、功耗与封装应力；融合与标定决定“能用多久”，而非仅看标称灵敏度。

## 参考文献

[1] Senturia, *Microsystem Design*, Springer.
[2] Kaajakari, *Practical MEMS*, Small Gear Publishing.
[3] Bosch / ST / InvenSense 惯性传感器数据手册（现行版本）.
[4] Bosch BMP/BME 系列气压与环境传感器文档.
[5] Titterton & Weston, *Strapdown Inertial Navigation Technology*.
[6] Madgwick 等姿态滤波开源说明与相关论文.
[7] Knowles / Infineon MEMS 麦克风应用笔记.
[8] AEC-Q100 车规应力测试标准概述.
[9] Yole / 市场机构 MEMS 产业公开摘要（份额口径随年变）.
[10] MOX/电化学气体传感综述（Sensors 期刊相关文）.
[11] IEEE MEMS 会议与传感器综述专刊.
[12] MEMS 封装可靠性与应力影响应用笔记.
