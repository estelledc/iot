---
schema_version: '1.0'
id: can-lin-bus-iot
title: CAN/LIN 总线在 IoT 中的应用
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 16
prerequisites: UNKNOWN
tags:
  - CAN
  - LIN
  - 工业总线
  - CAN FD
  - 车联网
  - 差分信号
  - 仲裁
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# CAN/LIN 总线在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：工业通信、车联网 | **阅读时间**：约 16 分钟

## 日常类比

会议室只有一支麦克风（共享总线）。控制器局域网（Controller Area Network, CAN）像大家同时喊出优先级编号：编号最小者发言，其他人退让且不破坏已发出的位——非破坏性仲裁。本地互联网络（Local Interconnect Network, LIN）像主持人按名单点名：被点到才能说。工厂里 CAN 更像抗干扰的“车间神经”；LIN 更像车窗、座椅这类低优先级舒适件的“经济型支线”[1][5]。

## 摘要

对比 CAN 2.0 / CAN FD / CAN XL 与 LIN 的物理层、仲裁、错误处理与 IoT 选型线索。表中速率、长度与节点数为标准/厂商标称量级，**实际受线缆、终端电阻与负载率约束**[1][2][4]。

## 1. CAN 物理层与帧

CAN 用差分对（CAN_H / CAN_L）：显性位（逻辑 0）压差约数伏量级，隐性位（逻辑 1）压差近零；显性覆盖隐性，仲裁才成立[1][7]。

| 参数 | CAN 2.0 | CAN FD | CAN XL |
|------|---------|--------|--------|
| 数据段速率叙事 | 至约 1 Mbps | 数据段可更高（常见至数 Mbps 级） | 更高（标准叙事至约 20 Mbps 级） |
| 仲裁段 | 与数据同速叙事 | 常保持较低仲裁速率 | 类似双速率思路 |
| 数据长度 | 0–8 B | 0–64 B | 至约 2048 B 级 |
| CRC | 15-bit | 17/21-bit | 更长 CRC 叙事 |
| 典型定位 | 成熟车身/工业 | 中等载荷实时 | 过渡期大载荷 |

标准帧含 SOF、仲裁 ID、控制、数据、CRC、ACK、EOF。CAN FD 用位速率切换（Bit Rate Switch, BRS）在数据段提速；CAN XL 面向更大载荷与以太网过渡场景[2][3][4]。

## 2. 仲裁与错误处理

多节点同时发送时，逐位比较：发隐性却读到显性则退出，ID 最小者获胜，失败帧未被破坏[1][7]。

错误检测含位监控、位填充、CRC、帧格式与 ACK 等；节点用发送/接收错误计数在 Error Active / Passive / Bus-Off 间迁移。残余错误率极低是协议设计目标，**现场仍须看负载率与物理层质量**[1][2][9]。

## 3. LIN 与 CAN 对比

LIN 单主多从、单线+地、速率约 20 kbps 量级，从节点可用 RC 振荡器靠 Sync 字节校准——成本与布线简单，实时性与抗扰弱于差分 CAN[5]。

| 维度 | CAN | LIN |
|------|-----|-----|
| 拓扑 | 多主 | 单主多从 |
| 物理层 | 差分双线 | 单线 |
| 速率叙事 | Mbps 级（视代际） | 约 20 kbps |
| 成本/节点 | 较高 | 较低 |
| 同步 | 通常需晶振级精度 | 从节点可 RC |
| 典型用途 | 动力/安全/工业传感 | 舒适件、低速执行器 |

IoT 中 LIN 偶见于楼宇窗帘、农业低速传感等“能点名即可”的场景；关键路径、高可靠仍优先 CAN/CAN FD[5][10]。

## 4. 硬件接入与选型

无内置 CAN 的微控制器（Microcontroller Unit, MCU）常用串行外设接口（Serial Peripheral Interface, SPI）外挂控制器（如 MCP2515）+ 收发器（如 TJA1050），总线两端各约 120 Ω 终端，测 CAN_H–CAN_L 应约 60 Ω 量级[6][7]。

| 场景 | 更常见选择 | 原因 |
|------|------------|------|
| 产线传感、中等载荷 | CAN FD | 单帧更大、实时 |
| 车身/成熟工业 | CAN 2.0 | 生态与工具成熟 |
| 舒适/低成本支线 | LIN | 单线、主从简单 |
| 大载荷过渡 | CAN XL / 以太网 | 载荷与带宽 |

经验上总线长度与波特率负相关；负载率建议留裕量（常见叙事不超过约 70%），否则低优先级易饿死——**以示波器/总线分析仪实测为准**[7][8]。

## 5. 局限、挑战与可改进方向

### 1. 把标称 Mbps 当有效吞吐

**局限**：忽略填充位、仲裁等待与重传。
**改进**：按目标消息周期与最坏仲裁延迟做负载预算，并用 can-utils / 逻辑分析仪验收。

### 2. 终端与拓扑被忽视

**局限**：缺终端、星型乱接导致反射与间歇错误。
**改进**：坚持两端终端；分支尽量短；量产前做眼图/错误帧统计。

### 3. ID 分配无优先级策略

**局限**：紧急帧 ID 过大，被周期数据挤掉。
**改进**：预留低 ID 给安全/告警；周期传感与诊断分区。

### 4. LIN 当“便宜 CAN”滥用

**局限**：单线抗扰与带宽不足，现场误码高。
**改进**：关键闭环仍用 CAN；LIN 仅限低优先级、短距离支线。

## 6. 实践要点

1. 先定载荷与实时性，再选 CAN 2.0 / FD / XL 或 LIN。
2. 物理层：差分走线、终端、共地与浪涌防护一起做。
3. 软件：超时看门狗 + Bus-Off 恢复策略，勿只依赖“发成功就返回”。

## 参考文献

[1] Bosch, "CAN Specification Version 2.0," Robert Bosch GmbH, 1991.
[2] ISO 11898-1, "Road vehicles — Controller area network (CAN)," ISO.
[3] CAN in Automation (CiA), CAN FD specification / CiA documents.
[4] CiA 610-1, "CAN XL Data Link Layer," 2024.
[5] LIN Consortium, "LIN Specification Package Revision 2.2A," 2010.
[6] Microchip, "MCP2515 Stand-Alone CAN Controller Datasheet."
[7] S. Corrigan, "Introduction to the Controller Area Network (CAN)," TI SLOA101.
[8] F. Hartwich, "CAN with Flexible Data-Rate," Bosch.
[9] M. Di Natale et al., "Understanding and Using the Controller Area Network Communication Protocol," Springer.
[10] W. Voss, "A Comprehensible Guide to Controller Area Network," Copperhill.
[11] ISO 17987, LIN related road vehicles standards (family).
