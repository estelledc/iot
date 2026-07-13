---
schema_version: '1.0'
id: infrared-communication-irda-iot
title: 红外通信IrDA在IoT遥控中的应用与局限
layer: 2
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - ble-5-features-coded-phy
tags:
- 红外
- IrDA
- NEC协议
- 智能家居
- 红外桥接
- 遥控
- 视线通信
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 红外通信IrDA在IoT遥控中的应用与局限

> **难度**：🟢 初级 | **领域**：红外通信 | **阅读时间**：约 18 分钟

## 日常类比

红外遥控像用看不见的手电筒打摩斯密码：必须对准、挡住就断。载波（常约 38 kHz）像约定「只听这种闪法」，用来抵抗日光灯与阳光里的红外噪声。IoT 里它很少当主力无线，却常当「翻译」：Wi-Fi/语音指令 → 红外码 → 老空调/电视。

## 摘要

介绍红外物理与 NEC/RC5/SIRC 编码、IrDA 速率演进与衰落，以及智能家居红外桥接与学习码库。对比 BLE/Wi-Fi/Zigbee 的适用边界。距离与速率为消费遥控典型量级[3][5]。

## 1 物理与调制

通信常用约 850–950 nm LED + 硅光电二极管。数据调制到数十 kHz 载波（常见 36–40 kHz），一体化接收头（如 TSOP 系列）完成滤波解调[5]。

| 协议 | 编码思路 | 备注 |
|------|----------|------|
| NEC | 脉冲距离 | 家电遥控极常见 |
| RC5 | 曼彻斯特 | 飞利浦系 |
| Sony SIRC | 脉冲宽度 | 12/15/20 位等变体 |

## 2 IrDA 标准

IrDA（Infrared Data Association）面向短距双向数据（非单向遥控）[1]：

| 标准 | 速率量级 | 时期 |
|------|----------|------|
| SIR | 115.2 kbps | 1994 |
| MIR | 1.152 Mbps | 1995 |
| FIR | 4 Mbps | 1996 |
| VFIR | 16 Mbps | 1999 |
| UFIR | 96 Mbps | 2005 |

栈含 IrPHY、IrLAP、IrLMP、TinyTP 及 IrOBEX 等。典型：点对点、半双工、约 0–1 m、需对准。蓝牙/Wi-Fi 普及后消费电子 IrDA 口基本消失；残留多是手机红外发射器模拟遥控[1][2]。

## 3 IoT 角色：桥接

Wi-Fi/BLE 网关收云指令 → 查码库或学习时序 → 多方向红外 LED 发射。产品如 Broadlink、米家万能遥控、涂鸦方案等。码库格式含 LIRC、Pronto Hex 及厂商私有；无码则学习原始遥控器[3][4]。

MCU 示例路径：ESP32 + IRremote 类库发 NEC；MQTT 订阅 `home/ac/#` 驱动格力等空调协议库[4]。

## 4 优劣与射频对比

**优势**：无 RF 干扰、不受无线电许可约束、元器件极便宜、不穿墙带来房间级物理隔离、按键级占空比极低。

**局限**：需视线、距离短（遥控常约 1–10 m）、多为单向无确认、强阳光恶化 SNR、速率仅 kbps 级。

| 特性 | 红外 | BLE | Wi-Fi | Zigbee |
|------|------|-----|-------|--------|
| 视线 | 需要 | 不需要 | 不需要 | 不需要 |
| 穿墙 | 无 | 弱 | 中 | 弱 |
| 双向 | 少 | 是 | 是 | 是 |
| 速率 | kbps | Mbps 量级 | 更高 | 250 kbps |
| 成本 | 极低 | 低 | 中 | 低 |

## 5 实践建议

新设备优先 BLE/Wi-Fi；改造存量家电用红外桥。酒店等同室隔离场景可刻意利用「不穿墙」。自由空间光（FSO）等高速红外激光属另一技术线，与家电遥控不是同一产品形态。

## 6 局限、挑战与可改进方向

### 1. 视线与布置

**局限**：家具遮挡导致偶发失灵。
**改进**：多 LED 广角/天花反射布置；关键指令加状态反馈（电表/温湿度回读）。

### 2. 单向无 ACK

**局限**：不知空调是否收到。
**改进**：配对可上报状态的智能设备；或传感器闭环确认。

### 3. 码库碎片

**局限**：冷门型号学习失败或时序漂移。
**改进**：存原始时序重放；社区码库 + 本机学习备份。

### 4. 被射频替代

**局限**：新家电原生联网后红外需求下降。
**改进**：网关同时保留红外与 Matter/Wi-Fi，生命周期内兼容混场。

## 参考文献

[1] Infrared Data Association, "IrDA Specifications," https://www.irda.org/
[2] Altium, "Understanding Infrared Communication," technical resources, 2022.
[3] K. Shirriff, "Understanding IR Remote Control Protocols," blog, 2013.
[4] Espressif / community, "IRremoteESP8266 Documentation," GitHub, 2023.
[5] SB-Projects, "IR Remote Control Theory and Protocols," https://www.sbprojects.net/knowledge/ir/
[6] Vishay / TSOP receiver application notes.
[7] Philips, "RC5 IR protocol documentation."
[8] NEC Corporation, "NEC Infrared Transmission Protocol" (industry descriptions).
[9] LIRC project, "Linux Infrared Remote Control."
[10] Bluetooth SIG, "Bluetooth Core Specification" (replacement context for IrDA data).
[11] IEEE 802.11 / Wi-Fi Alliance materials (short-range data alternative).
[12] Free-space optical communications surveys (FSO, distinct from consumer IR).
