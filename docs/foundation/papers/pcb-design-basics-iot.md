---
schema_version: '1.0'
id: pcb-design-basics-iot
title: IoT设备PCB设计基础：布局布线规则
layer: 1
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - decoupling-capacitor-placement
  - pcb-ground-plane-partitioning
  - emc-fundamentals-iot-device
tags:
  - PCB布局
  - 布线规则
  - 地平面
  - 去耦
  - 天线净空
  - DRC
  - IoT硬件
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# IoT设备PCB设计基础：布局布线规则

> **难度**：🟢 初级 | **领域**：PCB设计 | **关键词**：布局, 地平面, 去耦, 净空 | **阅读时间**：约 18 分钟

## 日常类比

装修房子：冰箱不跟电视挤同一角，水管不与电线乱缠。印刷电路板（Printed Circuit Board, PCB）上元件是家具、走线是管线、地平面是地基、设计规则检查（Design Rule Check, DRC）是竣工验收。物联网（Internet of Things, IoT）还多了天线：附近铜皮与板形会让无线变聋——衰减数 dB、距离数量级下降的案例并不罕见，须以实测为准[2][4]。

## 摘要

覆盖从原理图到 Gerber 的流程、分区布局、电源与去耦、布线与地、天线禁区及 2/4 层选择。规则引用 IPC 与 EMC 实践，具体数值跟工厂能力走[1][2]。

## 1. 流程与布局

| 阶段 | 输出 |
|------|------|
| 原理图 | 网表 |
| 布局 | 坐标与分区 |
| 布线 | 铜几何 |
| DRC | 违规报告 |
| Gerber/钻孔 | 制造文件 |

布局优先：按电源/模拟/数字/射频分区；晶振靠近芯片；去耦紧贴电源脚；连接器与机械孔先定。好布局让布线顺，坏布局怎么布都别扭[1]。

## 2. 电源、布线与地

| 规则 | 做法 |
|------|------|
| 去耦 | 小电容最近，回路面积最小[3] |
| 电源 | 足够宽或平面，避免细长瓶颈 |
| 走线 | 优先 45°/弧角；关键信号控长与阻抗 |
| 地 | 连续回流；射频设备慎乱分割[2] |

IoT 无线：天线 keep-out 无铜无高大元件；馈线按 50 Ω 设计；有 Wi-Fi/BLE 强烈建议 ≥4 层以获得完整参考地[4]。

| 层数 | 倾向 |
|------|------|
| 2 层 | 低速、无射频或模组已含天线认证 |
| 4 层 | 射频/高速/EMC 更友好 |

## 3. 常见错误与审查

| 错误 | 风险 |
|------|------|
| 去耦过远 | 复位/数字噪声 |
| 地缺口切回流 | EMC 失败 |
| 侵占天线净空 | 距离骤降 |
| 未跑 DRC | 制造报废 |

交付前用检查清单：间距、孔环、丝印、测试点、阻抗与净空逐项勾选[1]。

## 4. 局限、挑战与可改进方向

### 1. 2 层板硬上高速射频

**局限**：回流与屏蔽不足，认证难。
**改进**：升 4 层或认证模组+保留布局约束[4]。

### 2. 过早布线忽视机械

**局限**：外壳/电池迫使改天线与接口。
**改进**：ID 与结构并行，先锁板框与 keep-out[1]。

### 3. 分割地引入天线效应

**局限**：地缝成缝隙天线，辐射超标。
**改进**：单点桥接策略要有回流分析；默认完整地[2]。

### 4. 工具默认规则≠工厂能力

**局限**：DRC 通过仍无法生产。
**改进**：导入厂商叠层/间距约束再布线[1]。

## 总结

IoT PCB：分区布局、就近去耦、完整地、天线净空、有射频上 4 层。DRC 与清单是量产门槛，不是可选步骤。

## 参考文献

[1] IPC-2221, Generic Standard on Printed Board Design.
[2] Ott, Electromagnetic Compatibility Engineering.
[3] Bogatin, Signal and Power Integrity - Simplified.
[4] ST, AN4509 STM32WB 硬件设计指南（无线布局代表）.
[5] TI/Espressif 模组天线 keep-out 应用笔记.
[6] IPC-7351 焊盘图形标准.
[7] 去耦电容选型与放置应用笔记.
[8] Gerber / ODB++ 制造输出检查清单（厂商）.
[9] 2 层 vs 4 层 EMC 对比案例研究.
[10] 晶振布局与负载电容实践笔记.
[11] USB/高速差分入门布线指南.
[12] DFM 与 DRC 协同检查实践.
