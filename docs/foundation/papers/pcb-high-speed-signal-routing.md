---
schema_version: '1.0'
id: pcb-high-speed-signal-routing
title: PCB高速信号布线与阻抗控制
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - pcb-stackup-layer-design
  - pcb-ground-plane-partitioning
  - emc-fundamentals-iot-device
tags:
  - 高速布线
  - 差分对
  - 阻抗控制
  - 端接
  - 等长
  - 信号完整性
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# PCB高速信号布线与阻抗控制

> **难度**：🟡 中级 | **领域**：信号完整性 | **关键词**：传输线, 差分, 端接, 过孔 | **阅读时间**：约 18 分钟

## 日常类比

城市道路限速 30 时路面小坑无妨；高速公路上同坑可能翻车。印刷电路板（PCB）走线亦然：边沿够慢时铜线只是导线；上升时间到纳秒级，走线变成有阻抗与反射的传输线[1][2]。

## 摘要

给出何时按传输线设计、差分/单端阻抗、端接、等长与过孔残桩要点，并映射 USB/QSPI/MIPI 等物联网常见接口。临界长度与阻抗公差为经验量级，以叠层与板厂阻抗报告为准[3]。

## 1. 何时是传输线

经验：走线长度相对上升时间对应的传播距离不可忽略时（常有 1/6 波长量级判据），需控阻抗并考虑端接。FR-4 上延时约数 ps/mm 量级[1]。

| 主题 | 要点 |
|------|------|
| 单端 | 常 50 Ω 目标，参考平面连续 |
| 差分 | USB 常 90 Ω 等，按接口规范 |
| 端接 | 串阻/并阻/戴维南等，匹配源或载 |

## 2. 差分、等长与过孔

| 规则 | 做法 |
|------|------|
| 差分对 | 等长、等距、同层；少换层 |
| 内间距 | 按计算叠层，勿任意拉远 |
| 等长 | DDR 等按字节组/时钟预算；USB 容差相对宽 |
| 过孔 | 短残桩或背钻；换层补回流过孔 |

眼图用于看余量：抖动、噪声、码间干扰使眼闭合。IoT 入门可先做 USB 2.0 差分（容差相对友好），再上更严接口[5]。

## 3. 局限、挑战与可改进方向

### 1. 只控线宽忽略参考面

**局限**：地缺口使阻抗突变、辐射上升。
**改进**：完整参考；跨分割必桥接回流[1][4]。

### 2. 过孔残桩谐振

**局限**：多 Gb/s 眼图塌陷。
**改进**：盲埋孔、背钻或优化层切换[2]。

### 3. 等长只齐线不齐延迟

**局限**：介质/过孔延迟未计入。
**改进**：用工具延迟规则而非纯几何长度[1]。

### 4. 未端接却超临界长度

**局限**：振铃误触发、EMI 差。
**改进**：算临界长度；加串阻或改驱动强度[2]。

## 总结

高速布线三件套：阻抗连续、回流完整、时序/等长按接口预算。超临界长度后规则是必须项不是加分项。

## 参考文献

[1] Bogatin, Signal and Power Integrity - Simplified.
[2] Johnson & Graham, High-Speed Digital Design.
[3] IPC-2141A, Controlled Impedance Design Guide.
[4] Montrose, EMC and the Printed Circuit Board.
[5] USB-IF, USB 2.0 规范及相关 ECN.
[6] MIPI Alliance 布线指南（代表高速屏/摄像接口）.
[7] DDR 等长与飞行时间应用笔记.
[8] 过孔模型与残桩效应文献.
[9] 端接策略比较应用笔记.
[10] 眼图测量与模板测试基础.
[11] 板厂阻抗 coupon 测试说明.
[12] QSPI/OSPI 布线实践（Flash 接口）.
