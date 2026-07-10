---
schema_version: '1.0'
id: flexible-pcb-rigid-flex-iot
title: 柔性PCB与刚柔结合板在IoT可穿戴中的应用
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - flexible-electronics-iot
  - connector-selection-iot-harsh-env
tags:
  - 柔性PCB
  - 刚柔结合
  - PI
  - 可穿戴
  - Coverlay
  - 弯折寿命
  - FPC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 柔性PCB与刚柔结合板在IoT可穿戴中的应用

> **难度**：🟡 中级 | **领域**：柔性电路 | **关键词**：FPC, Rigid-Flex, PI, Coverlay | **阅读时间**：约 18 分钟

## 日常类比

刚性印制电路板（Printed Circuit Board, PCB）像木板；柔性电路（Flexible Printed Circuit, FPC）像可卷的膜；刚柔结合板（Rigid-Flex）像精装书——硬页焊器件、软脊负责弯折，少用板间连接器硌皮肤[1][2]。

## 摘要

梳理聚酰亚胺（Polyimide, PI）/聚酯（PET）基材、单双多层与刚柔结构、弯折设计规则与可穿戴可靠性。厚度、弯折次数与成本倍数为行业常见量级，**以板厂叠构与 IPC 规范为准**[3][4]。

## 1. 材料与结构

| 材料 | 耐温 | 成本 | 典型用途 |
|------|------|------|----------|
| PI | 可回流焊量级 | 较高 | 可焊接可穿戴主板/排线 |
| PET | 显著更低 | 低 | 热压/银浆、一次性贴片 |

覆盖层（Coverlay）替代阻焊；无胶铜箔弯折寿命通常优于有胶结构，但更贵。单面最薄最便宜；双面可过孔与地平面，可穿戴性价比常见；多层弯折变差，可穿戴宜控制层数[1][5]。

| 结构 | 优点 | 代价 |
|------|------|------|
| 纯软板 | 薄、可贴合 | 细密器件贴装与补强要求高 |
| 刚柔一体 | 无连接器、可靠性高 | 设计/制程贵、交期长 |
| 软板+连接器 | 模块化 | 接触电阻、厚度、失效点 |

## 2. 设计规则要点

弯折区：避免过孔与器件；走线垂直弯折轴；铜厚与线宽按动态/静态弯折区分；内外角加泪滴；阻抗与叠构在软区单独核算[3][6]。刚区放 MCU/射频，软区做传感器延伸或铰链。

| 场景 | 更合适 |
|------|--------|
| 手环表带过铰链 | 动态弯折 FPC 或刚柔 |
| TWS 天线排线 | 双面软板 + 补强 |
| 医疗一次性贴片 | PET/印刷或低成本单面 |

## 3. 制造与可靠性

刚柔需多次压合与激光成型，良率与尺寸公差严于普通 FR-4。测试：动态弯折、湿热、盐雾（汗液）、微动磨损（若有连接器）[4][7]。补强片（PI/钢片）用于连接器与芯片区，避免“软到无法贴片”。

## 4. 局限、挑战与可改进方向

### 1. 成本与交期

**局限**：刚柔相对刚性板贵一个数量级量级并不罕见，改版慢。
**改进**：早期用软排线+两块硬板验证；量产再合刚柔；冻结弯折区叠构[2]。

### 2. 动态弯折疲劳

**局限**：中性层偏移、有胶层蠕变导致断线。
**改进**：无胶或薄胶、对称叠构、控制弯折半径 ≥ 板厂建议倍数[3]。

### 3. 吸湿与尺寸漂移

**局限**：PI 吸水导致对位与阻抗变化。
**改进**：烘烤、阻湿覆盖、关键射频区用覆盖膜与接地策略[5]。

### 4. 维修性差

**局限**：一体刚柔损坏常整板报废。
**改进**：高损耗区可拆软排线模块化；测试点预留在刚区[8]。

## 总结

可穿戴优先“刚区算力 + 软区过弯”，用 IPC 弯折规则与补强把寿命做实；不确定销量时先软硬组合验证，再投入刚柔量产。

## 参考文献

[1] IPC-2223, Sectional Design Standard for Flexible/Rigid-Flexible Printed Boards.
[2] IPC-6013, Qualification and Performance Specification for Flexible/Rigid-Flexible Printed Boards.
[3] DuPont / 板厂 PI 覆铜板与 Coverlay 技术手册.
[4] IPC-TM-650, 弯折与环境试验方法（柔性板相关）.
[5] Panasonic / 无胶挠性覆铜板应用笔记.
[6] Howard Johnson, High-Speed Digital Design（阻抗与叠构对照）.
[7] IEEE / 可穿戴设备汗液腐蚀与 FPC 可靠性研究.
[8] 连接器厂商 FPC 补强与插拔寿命应用指南.
[9] JEDEC / 湿热与温度循环对聚合物基板影响综述.
[10] Rigid-Flex 设计检查清单（主流 EDA 与板厂 DFM 文档）.
[11] PET 柔性电路热压键合工艺说明.
[12] 可穿戴天线与 FPC 净空设计应用笔记.
