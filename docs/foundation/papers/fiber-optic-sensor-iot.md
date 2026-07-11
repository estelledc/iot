---
schema_version: '1.0'
id: fiber-optic-sensor-iot
title: 光纤传感器在工业IoT温度/应变测量中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 20
prerequisites:
  - optical-sensors-iot
  - corrosion-sensor-structural-health
tags:
  - 光纤传感
  - FBG
  - DTS
  - 布里渊
  - 结构健康监测
  - 工业IoT
  - OTDR
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 光纤传感器在工业IoT温度/应变测量中的应用

> **难度**：🔴 高级 | **领域**：光纤传感 | **关键词**：FBG, DTS, OTDR, 应变/温度 | **阅读时间**：约 20 分钟

## 日常类比

高速公路不只运车，还能靠路面微振感知车流。光纤传感器（Fiber-Optic Sensor）类似：同一根纤既传光，又沿途感知温度与应变；石英不导电，适合强电磁与易燃易爆区[1][2]。

## 摘要

对比点式光纤布拉格光栅（Fiber Bragg Grating, FBG）与分布式拉曼/布里渊/瑞利方案，说明解调、交叉敏感与工业物联网（IoT）集成要点。灵敏度、距离与价格为公开资料常见量级，**以解调仪与光纤规格书为准**[3][4]。

## 1. 分类与 FBG

光强、相位、波长、偏振或散射可被外部量调制。点式以 FBG、法布里–珀罗为主；分布式依托光时域反射（Optical Time-Domain Reflectometer, OTDR）类技术[1]。

布拉格条件：`λ_B = 2 n_eff Λ`。应变与温度使 `λ_B` 漂移；1550 nm 附近应变与温度灵敏度常分别约 pm/με 与约 10 pm/℃ 量级[2][4]。一根纤可波分复用多个不同中心波长的 FBG。

| 解调思路 | 精度倾向 | 成本倾向 |
|----------|----------|----------|
| 宽谱源 + 光谱仪 | 约 pm 级 | 中 |
| 可调谐激光扫描 | 更高 | 高 |
| 边缘滤波 | 较低 | 较低 |

## 2. 分布式传感

| 技术 | 主要测量量 | 空间分辨倾向 | 距离倾向 |
|------|------------|--------------|----------|
| 拉曼 DTS | 温度 | 米级 | 数十 km 量级 |
| 布里渊 | 温度+应变 | 米级 | 更长可达 |
| 瑞利 OFDR | 高分辨应变/温度 | mm 级 | 通常更短 |

拉曼用反斯托克斯/斯托克斯比测温，应变耦合弱。布里渊频移同时含温度与应变，需松套管参考纤或双参数解耦[3][5]。

## 3. 工业价值与集成

抗电磁干扰、本质安全（无电火花）、长距离多点是相对电传感器的核心优势。典型场景：桥梁/大坝应变、油井分布式温度传感（Distributed Temperature Sensing, DTS）、变压器与电缆热点、复合材料埋入监测[1][6]。

| 传感器规模 | 数据量倾向 | 上云链路 |
|------------|------------|----------|
| 少量 FBG | 很低 | 蜂窝/LoRa 等均可评估 |
| 百点 FBG / 动态 | 中 | 常需以太网 |
| DTS 剖面 | 单次较大 | 以太网/4G |

链路一般为：传感纤 → 解调/OTDR → 边缘预处理 → 网关 → 云端趋势与告警。

## 4. 局限、挑战与可改进方向

### 1. 解调仪成本高

**局限**：入门 FBG/分布式仪价格常远高于电测节点，阻碍规模部署。
**改进**：边缘滤波或硅光集成解调；按精度降配；多点摊薄单点成本[7]。

### 2. 温度–应变交叉敏感

**局限**：单 FBG/`ν_B` 无法唯一分解两物理量。
**改进**：温度参考光栅/松套管；封装补偿；算法联合估计[2][5]。

### 3. 机械脆弱与连接损耗

**局限**：裸纤易断；多连接器累积损耗降低信噪比。
**改进**：铠装/套管；优先熔接；户外密封连接器[6]。

### 4. IoT 采样与带宽错配

**局限**：高速动态 FBG 数据量超出低功耗广域网能力。
**改进**：边缘特征提取后稀疏上报；监测类用分钟级采样[8]。

## 总结

FBG 适合多点离散监测，分布式适合长距离连续剖面；强 EMI 与本安场景优先考虑光纤。落地关键是解调成本、交叉敏感解耦与机械保护，而不是“有纤就能测准”。

## 参考文献

[1] R. Measures, Structural Health Monitoring with Fiber Optic Systems, Academic Press.
[2] A. Kersey et al., Fiber grating sensors, J. Lightwave Technol.
[3] A. Hartog, Distributed Fiber-Optic Sensing, CRC Press.
[4] A. Othonos, K. Kalli, Fiber Bragg Gratings, Artech House.
[5] X. Bao, L. Chen, Brillouin scattering based fiber sensors, Sensors.
[6] IEC / 工业光纤传感与本安相关应用指南（油气电力语境）.
[7] 硅光子解调与低成本interrogator 研究进展综述.
[8] IEEE IoT Journal, 光纤传感边缘网关与数据缩减案例.
[9] ITU-T / 光纤衰减与连接器损耗工程建议（链路预算）.
[10] SPIE, FBG 风电叶片与复合材料埋入监测论文集选篇.
[11] IEEE Sensors Journal, 拉曼 DTS 电缆沟测温应用.
[12] OSA / Optica, OFDR 高分辨分布式应变综述.
