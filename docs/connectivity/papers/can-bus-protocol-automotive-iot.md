---
schema_version: '1.0'
id: can-bus-protocol-automotive-iot
title: CAN总线协议在车联网IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags:
  - CAN
  - 车联网
  - OBD-II
  - 仲裁
  - SecOC
  - CANopen
  - J1939
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# CAN总线协议在车联网IoT中的应用

> **难度**：🟡 中级 | **领域**：车载通信 | **阅读时间**：约 20 分钟

## 日常类比

走廊传纸条：两人同时扔会撞车。控制器局域网（Controller Area Network, CAN）给纸条写优先级——编号更小的非破坏性胜出，另一张自动重试，纸条本身不损坏。这就是基于标识符的仲裁。车联网里，CAN 仍是车内数据源头，经网关/车载终端上云[1][2]。

## 摘要

本文覆盖物理层差分信号、帧与仲裁、域划分与网关、车联网采集与车载诊断（On-Board Diagnostics, OBD-II），以及安全缺陷与工业应用层（CANopen、J1939）。波特率–总线长度与 ECU 数量为工程经验区间，**以整车网络设计为准**[1][5]。

## 1. 概述与物理层

多主、消息导向（ID 非节点地址）、差分双线、广播过滤、非破坏性仲裁。总线两端各约 120 Ω 终端电阻防反射[1]。

| 逻辑 | 总线倾向 | 含义 |
|------|----------|------|
| 显性 0 | CAN_H/CAN_L 有压差 | 覆盖隐性 |
| 隐性 1 | 近似同电位 | 可被显性覆盖 |

| 波特率倾向 | 长度倾向 | 场景 |
|------------|----------|------|
| 高（至约 1 Mbps） | 短 | 动力等 |
| 中 | 更长 | 车身/诊断 |
| 低 | 很长 | 部分工业/农机 |

高速时位时间短，传播延迟占比大，故长度受限[1]。

## 2. 帧与仲裁

标准帧 11 位 ID，扩展帧 29 位；数据场最多 8 字节。CRC、ACK、EOF 等保证检错与确认。多节点同时发送时按 ID 逐位仲裁，小 ID 优先[2]。

| ID 区段叙事 | 优先级 | 消息类 |
|-------------|--------|--------|
| 较低数值 | 高 | 安全/底盘关键 |
| 中 | 中 | 动力/车身 |
| 较高数值 | 低 | 娱乐/诊断 |

大块传输常走 ISO-TP（ISO 15765-2）多帧，效率有限，推动了 CAN FD[1]。

## 3. 车载架构与 IoT 数据路径

现代车辆按域划分多条 CAN，经中央网关路由、过滤与协议转换。ECU 数量随车型从数十到近百量级不等——**以具体架构为准**[5]。

```
车内 CAN → 网关 → T-Box/OBD 设备 → 蜂窝网络 → 云平台
```

OBD-II 提供法规诊断访问（如 PIN6/14 上的 CAN）；标准 PID 可读转速、车速等，支撑车队与远程诊断，同时扩大攻击面[4]。

## 4. 安全

经典 CAN 无认证、无加密、无源地址。威胁含注入、重放、高优先级拒绝服务、诊断滥用。缓解：AUTOSAR 安全车载通信（SecOC）消息认证码、网关防火墙、入侵检测、硬件安全模块与安全启动。8 字节载荷使 MAC 与数据争空间，CAN FD 更大载荷对此更友好[3]。

| 措施 | 作用 | 代价 |
|------|------|------|
| SecOC | 完整性/新鲜性 | 载荷与密钥管理 |
| 网关过滤 | 域隔离 | 策略维护 |
| IDS | 异常检测 | 误报/算力 |

## 5. 工业侧与以太网关系

| 方案 | 要点 |
|------|------|
| CANopen | 对象字典、PDO/SDO、NMT |
| J1939 | 重型车 PGN/SPN，常用扩展帧 |
| DeviceNet | 工控主从、可总线供电 |

| 特性 | CAN 2.0 | 车载以太网倾向 |
|------|---------|-----------------|
| 速率 | ≤1 Mbps 级 | 百兆+ |
| 载荷 | 8 B | 大帧 |
| 确定性 | 原生仲裁 | 常需时间敏感网络 |
| 成本/复杂度 | 低 | 更高 |

演进叙事：以太网作骨干，CAN 留在传感器/执行器边缘[5]。

## 6. 局限、挑战与可改进方向

### 1. 先天无安全

**局限**：总线任一节点可伪造高优先级帧[3]。
**改进**：SecOC+密钥分级；诊断接口强鉴权；分段网络。

### 2. 8 字节与总线负载

**局限**：ECU 增多导致负载与延迟抖动上升。
**改进**：域拆分；迁移 CAN FD；合并信号矩阵。

### 3. OBD/售后物联网风险

**局限**：第三方 Dongle 成为入口。
**改进**：网关策略区分诊断与控制；监控异常 PID/UDS 序列。

### 4. 与云侧语义断裂

**局限**：原始 CAN 信号无统一字典，车队平台难复用。
**改进**：采用 DBC/标准化信号层；边缘做单位与质量戳。

## 7. 实践要点

1. 硬件先查终端电阻与双绞线极性。
2. ID 分配先保安全相关消息。
3. 上云只采集最小必要信号，并做新鲜性校验。

## 参考文献

[1] ISO 11898-1, Road vehicles — CAN — Data link layer and physical signalling.
[2] Robert Bosch GmbH, CAN Specification 2.0.
[3] AUTOSAR, Secure Onboard Communication (SecOC).
[4] SAE J1939 (heavy-duty) and OBD-II related SAE/ISO diagnostic standards.
[5] Industry surveys on automotive E/E architecture (CAN domains + Ethernet backbone).
[6] CiA 301, CANopen application layer and communication profile.
[7] ISO 15765-2 (ISO-TP) for multi-frame transport over CAN.
[8] Academic/industry papers on CAN bus attacks and mitigations.
[9] SAE / OEM guidance on gateway firewalling between domains.
[10] Rockwell/ODVA DeviceNet overview materials (industrial CAN).
[11] ISO 11898-2 high-speed medium access unit (physical layer companion).
