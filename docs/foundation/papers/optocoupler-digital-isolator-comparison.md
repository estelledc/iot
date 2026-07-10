---
schema_version: '1.0'
id: optocoupler-digital-isolator-comparison
title: 光耦与数字隔离器对比选型
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 18
prerequisites:
  - esd-protection-circuit-design
  - emc-fundamentals-iot-device
  - can-lin-bus-iot
tags:
  - 光耦
  - 数字隔离器
  - 电气隔离
  - CMTI
  - CTR
  - 工业物联网
  - 增强隔离
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 光耦与数字隔离器对比选型

> **难度**：🟡 中级 | **领域**：电气隔离 | **关键词**：光耦, 数字隔离器, CTR, CMTI | **阅读时间**：约 18 分钟

## 日常类比

隔离器件像两间控制室之间的玻璃窗：要让信号“看见”，又不能让高压/地电位差伤人伤板。传统光耦像早期单层玻璃；数字隔离器更像现代夹层钢化玻璃——更薄、带宽更高、老化机制不同。物联网（Internet of Things, IoT）里 RS-485、隔离串行外设接口（Serial Peripheral Interface, SPI）、栅极驱动都靠这扇窗[2][3]。

## 摘要

对比光耦与电容/磁耦数字隔离器的速度、功耗、寿命与安全认证要点，并给出工业现场选型与印刷电路板（Printed Circuit Board, PCB）隔离带注意。耐压与共模瞬态抗扰度（Common-Mode Transient Immunity, CMTI）以认证报告与数据手册为准[1][5]。

## 1. 为何隔离

安全（防触电）、噪声（切断地环路）、地电位差（长线/电机）是三大动机。核心指标：隔离耐压、工作电压、爬电/电气间隙、CMTI、传播延迟与功耗[2][5]。

## 2. 原理对比

光耦：LED → 光 → 光敏晶体管；电流传输比（Current Transfer Ratio, CTR）随老化与温度下降。数字隔离器：片上电容或变压器传递调制数字边沿，无 CTR 老化机制，速率与通道密度通常更高[1][3][4]。

| 维度 | 光耦 | 数字隔离器 |
|------|------|------------|
| 速率 | 常 kbit/s–数 Mbit/s（高速型更贵） | 常可达数十–百 Mbit/s 量级 |
| 功耗 | LED 静态电流明显 | 通常更低（视型号） |
| 寿命机制 | CTR 退化 | 介质/封装为主，无 CTR |
| 多通道 | 单通道成本低 | 多通道集成更优 |
| EMI | 相对简单 | 高频载波需注意布局 |
| 成本 | 低速极低 | 单通道更高，多通道摊薄 |

## 3. 安全、寿命与应用

基本隔离 vs 增强隔离、UL/IEC/VDE 认证决定能否用于电网侧。爬电距离按污染等级与材料组计算，隔离带内禁铺铜/过孔是硬规则[5]。

| 场景 | 倾向 | 理由 |
|------|------|------|
| 低速开关量 | 光耦 | 成本 |
| 高速 SPI/多通道 UART | 数字隔离 | 速率与集成 |
| ≥5 年高温现场 | 数字隔离 | 规避 CTR 退化 |
| SiC 快开关栅驱 | 高 CMTI 数字隔离 | 抗共模浪涌 |

光耦设计须留 CTR 寿命余量（高温加速更明显）；数字隔离器两侧仍需隔离电源（或集成 iso-power 方案）[4][1]。

| PCB 要点 | 做法 |
|----------|------|
| 隔离带 | 满足爬电/间隙，无铜 |
| CMTI | 选够规格，远离开关节点 |
| EMI | 短接线、就近去耦 |

## 4. 局限、挑战与可改进方向

### 1. 光耦 CTR 长期漂移

**局限**：数年高温后逻辑阈值失效。
**改进**：加大初识 CTR 余量；周期自检；改数字隔离[4]。

### 2. 数字隔离器 EMI 与认证成本

**局限**：片上射频调制可能增加辐射；认证器件单价高。
**改进**：按厂商布局指南；低速通道仍可用光耦混合[1]。

### 3. 只隔信号不隔电源

**局限**：地仍通过电源连在一起，隔离名存实亡。
**改进**：隔离 DC-DC 或集成电源隔离器，分侧预算功率[2]。

### 4. CMTI 不足导致误码

**局限**：快沿功率级共模瞬态击穿逻辑。
**改进**：提高 CMTI 规格；加强分侧地完整与滤波[1][3]。

## 总结

低速廉价选光耦并管理 CTR 寿命；高速、多通道、长寿命与高 CMTI 选数字隔离器。信号隔离与电源隔离、PCB 隔离带必须一起做。

## 参考文献

[1] Skyworks/Silicon Labs, Digital Isolator Design Guide (AN1081).
[2] Texas Instruments, Isolation in Industrial Systems (SLLA414).
[3] Analog Devices, iCoupler 数字隔离技术说明.
[4] Vishay, Optocoupler Application Design Guide.
[5] UL 1577 / IEC 60747-5 等光耦与隔离相关标准.
[6] IEC 60664 绝缘配合（爬电/间隙背景）.
[7] TI/ADI 隔离 RS-485 参考设计.
[8] 栅极驱动隔离与 CMTI 应用笔记.
[9] 光耦 CTR 老化与寿命预测应用笔记.
[10] 隔离电源模块选型指南.
[11] PCB 隔离带与安规布局检查清单（厂商白皮书）.
[12] VDE 0884-11 等数字隔离器相关认证说明.
