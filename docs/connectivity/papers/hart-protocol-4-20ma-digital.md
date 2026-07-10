---
schema_version: '1.0'
id: hart-protocol-4-20ma-digital
title: HART协议4-20mA叠加数字通信
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - io-link-sensor-actuator-interface
tags:
- HART
- 4-20mA
- FSK
- WirelessHART
- HART-IP
- 过程自动化
- 预测维护
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# HART协议4-20mA叠加数字通信

> **难度**：🟡 中级 | **领域**：过程自动化 | **阅读时间**：约 20 分钟

## 日常类比

HART（Highway Addressable Remote Transducer）像「打电话还能听到背景音乐」：同一对线上，4–20 mA 直流传主测量值（控制用），FSK 交流传诊断与配置（数字旁路）。模拟仪表继续工作，数字通道被「听见」后才变成 IoT 数据金矿。

## 摘要

说明 4–20 mA 与 Bell 202 FSK 共存机理、命令体系、HART 7 / WirelessHART / HART-IP，以及多路复用器与适配器采集路径。安装量与 ROI 数字来自行业公开材料量级，项目须本厂基线[1][2][4]。

## 1 4–20 mA 基础

| 电流 | 含义 |
|------|------|
| 4 mA | 量程 0% |
| 20 mA | 量程 100% |
| 0 mA | 常表示断线（相对「真 0%」） |

电流环对线阻不敏感，可较长距离传输。局限：单变量、无诊断、现场调参、精度受环路与 ADC 约束。

## 2 FSK 叠加

逻辑「1/0」对应约 1200/2200 Hz 正弦，幅度约 ±0.5 mA；交流均值为 0，不改变直流分量。DCS 低通看 4–20 mA，HART 调制解调器带通看 FSK[1]。

| 参数 | 典型值 |
|------|--------|
| 物理层 | Bell 202 FSK |
| 比特率 | 1200 bps |
| 事务时间 | 约数百 ms 量级/次 |
| 主测量实时性 | 仍由模拟环保证 |

过程变量变化慢时，数字通道够用；主控仍走模拟。

## 3 通信模式与命令

| 模式 | 行为 |
|------|------|
| 请求/响应 | 主站轮询；可支持主主站 + 手操器副主站 |
| 突发 | 从站主动连发，更新更快 |
| 多点 | 多设备共线，模拟常固定 4 mA，数据走数字（少用） |

命令分层：通用（0–30，如 Cmd 0/1/3）、常规实践（32–126，如 33/35/48）、设备特定（128–253，需 DD）[1]。

## 4 多变量与诊断

PV 走 4–20 mA；SV/TV/QV、状态、健康度等走数字。远程可读写量程、阻尼、单位、标签、校准与故障模式。阀门定位器可提供摩擦、泄漏、响应时间等趋势，支撑计划检修而非紧急停车[2][4]。

## 5 HART 7、WirelessHART、HART-IP

| 路径 | 特点 |
|------|------|
| 有线 HART | 既有两线环，1200 bps |
| WirelessHART（IEC 62591） | 无线网状，适配器并联读取[3] |
| HART-IP | 以太网封装命令，便于上位与云[5] |

演进：HART 5/6 → 7（WirelessHART、时间戳、增强突发）→ HART-IP 与安全增强。

## 6 与 IoT 集成

行业常见说法是大量已装 HART 设备数字功能未用（比例因厂而异）。采集方案：

| 方案 | 做法 |
|------|------|
| HART 多路复用器 | 并联监听，一台管多回路，不影响控制 |
| WirelessHART 适配器 | 不改布线，无线回传数字数据 |
| HART-IP 网关 | 向 MQTT/OPC UA/云桥接 |

示意：周期发 Cmd 3/48，经 MQTT 发布过程量与诊断。

## 7 与 IO-Link / SPE 对比

| 特性 | HART | IO-Link | SPE/APL（方向） |
|------|------|---------|-----------------|
| 主战场 | 过程工业 | 离散制造 | 以太网统一现场 |
| 速率 | 1.2 kbps | 最高 230.4 kbps | 10 Mbps 量级 |
| 供电/线 | 两线 4–20 mA | 三线 24 V | 两线 PoDL 等 |
| 距离 | km 量级环路 | 约 20 m | 百米–km 级视规格 |
| 安装基数 | 极大（过程） | 离散侧增长快 | 早期 |

既有 SIL 认证与长寿命仪表使 HART 长期共存；绿场或许可时再评估 APL[1][3]。

## 8 局限、挑战与可改进方向

### 1. 数字通道慢

**局限**：1200 bps 不适合高频采样闭环。
**改进**：控制仍用 4–20 mA；数字只承载诊断/辅助量；需高速则上现场总线/以太网。

### 2. 「有 HART 未采集」

**局限**：I/O 卡不通数字、无 Mux/网关则数据沉睡。
**改进**：优先加 Mux/适配器，避免整厂换表；先阀门与关键变送器试点。

### 3. 设备特定命令碎片

**局限**：无 DD/IODD 类工具难解厂商命令。
**改进**：维护 DD 库；采集先用通用/常规命令覆盖 80% 需求。

### 4. 无线与网络安全

**局限**：WirelessHART/HART-IP 扩大攻击面。
**改进**：分区、密钥轮换、只读采集账户、变更走变更管理。

## 参考文献

[1] FieldComm Group, "HART Communication Protocol Specification," Revision 7.6, 2020.
[2] Emerson, "HART Communication: The Complete Guide," Fisher-Rosemount materials, 2019.
[3] IEC 62591:2016, "WirelessHART."
[4] J. Pinto, "HART and the Industrial Internet of Things," ISA InTech, 2021.
[5] FieldComm Group, "HART-IP Developer Guide," FCG-TS20200, 2020.
[6] IEC 61158 / related fieldbus context for process automation.
[7] NAMUR recommendations on device diagnostics and NE 107 status signals.
[8] WirelessHART device/adapter vendor application notes (Emerson, Pepperl+Fuchs, et al.).
[9] OPC Foundation, "OPC UA companion / gateway patterns for field protocols."
[10] ISA, "The Automation Book / InTech articles on HART multiplexing."
[11] FieldComm Group, "FDI / DD technology overview."
[12] IEC 61784 / CPF profiles referencing HART integration.
