---
schema_version: '1.0'
id: mbus-metering-protocol-iot
title: M-Bus抄表协议在IoT智能计量中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - dlms-cosem-smart-meter-protocol
tags:
  - M-Bus
  - EN-13757
  - 智能计量
  - wM-Bus
  - 抄表
  - 总线供电
  - 物联网网关
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# M-Bus抄表协议在IoT智能计量中的应用

> **难度**：🟡 中级 | **领域**：智能计量 | **阅读时间**：约 18 分钟

## 日常类比

物业手抄地下室水表、热表像逐个收风筝线；M-Bus（Meter-Bus）用两芯总线把表串起来，主机一拉（轮询）就能收回读数，且总线常给从站通信电路供电，表侧不必再为通信单独换电池[1][3]。

## 摘要

概述有线 M-Bus（EN 13757-2/3）物理层电压/电流调制、主从帧与 DIF/VIF 自描述应用层，以及 IoT 网关上行与有线/无线选型。电气上限与距离为标准/工程量级，**布线与负载须按段核算**[1][2]。

## 1. 标准定位

M-Bus 面向公用事业远程抄表（水/热/气/电等），属 EN 13757 体系；本文聚焦有线，无线 wM-Bus 见 EN 13757-4[1][2][4]。

| 部分 | 内容 |
|------|------|
| EN 13757-2 | 有线物理层与数据链路 |
| EN 13757-3 | 应用层数据格式 |
| EN 13757-4 | 无线 M-Bus |
| EN 13757-7 | 安全与密钥管理 |

## 2. 物理层与主从通信

两线总线：主站电压调制发令，从站电流调制应答；半双工、主站发起，从站间不直通[1][3]。

| 参数（量级） | 说明 |
|--------------|------|
| 空闲/Mark 电压 | 约 36 V DC 量级（以标准与器件为准） |
| Space 电压 | 相对 Mark 降低（常见叙述约 24 V） |
| 从站电流 | Mark 约 1.5 mA；Space 抬升至十余 mA 量级 |
| 地址与容量 | 常用地址空间支持约数百从站/段量级 |
| 速率 | 常见 300–9600 bit/s，工程多用 2400 |
| 距离 | 数百米量级；中继可扩展，依赖线径与负载 |

## 3. 链路与应用层

长帧含长度、控制（C）、地址（A）、控制信息（CI）、数据与校验等字段[1]。应用层记录常用 DIF（长度/类型）+ VIF（物理量/单位）+ Data，接收方可自描述解析体积、能量、温度等[2]。

| VIF 类别（例） | 物理量 |
|----------------|--------|
| 能量相关编码 | Wh / J 等倍率 |
| 体积相关编码 | L / m³ 等 |
| 功率/流量/温度 | W、m³/h、℃ 等 |

## 4. IoT 网关融合

传统集中器本地轮询与存数；IoT 网关增加蜂窝/以太网上行、边缘告警与远程配置，并把 M-Bus 转为 MQTT、HTTP、BACnet、Modbus TCP、DLMS/COSEM 等[5][8]。

| 上行 | 场景 |
|------|------|
| MQTT | 云平台遥测 |
| HTTP/REST | 业务 API |
| BACnet | 楼宇自控 |
| Modbus TCP | 工控集成 |
| DLMS/COSEM | 电力计量对接 |

漏水/异常用能常需小时级甚至更高频采样；完整轮询时延随表计数量与帧长增长，**须做容量与告警时效设计**[5]。

## 5. 有线 vs 无线

| 特性 | 有线 M-Bus | 无线 M-Bus |
|------|------------|------------|
| 介质 | 双芯电缆 | Sub-GHz 等 |
| 供电 | 总线供电常见 | 电池，寿命依赖占空比 |
| 安装 | 需布线 | 改造友好 |
| 可靠性 | 不受墙体射频衰减 | 受干扰与遮挡 |
| 典型选型 | 新建可布线 | 既有建筑改造 |

## 6. 局限、挑战与可改进方向

### 1. 主从轮询扩展性

**局限**：表多或读频高时总线占用与时延上升，难支撑“类实时”全表高频。
**改进**：分段多主/多网关；关键表提高频、其余降频；边缘先聚合再上传。

### 2. 布线与电气裕量

**局限**：超长线、细线径、从站过多导致电压/电流裕量不足。
**改进**：分段与中继；按标准核算负载；验收测末端电压与误码。

### 3. 安全基线参差

**局限**：老部署明文或弱安全；EN 13757-7 落地不一。
**改进**：新项目启用标准安全选项；网关到云强制 TLS；密钥轮换纳入运维。

### 4. 与 BMS 语义对齐

**局限**：DIF/VIF 到 BACnet/MQTT 点表映射易错单位与倍率。
**改进**：网关侧维护映射表与校准用例；账单字段双人复核。

## 7. 实践要点

1. 新建可布线优先有线；改造与分散户优先评估 wM-Bus。
2. 先定抄读周期与告警 SLA，再定段数与网关数。
3. 联调用已知体积/能量样例帧验证解析，再接计费。

## 参考文献

[1] EN 13757-2, Communication systems for meters — Wired M-Bus.
[2] EN 13757-3, Communication systems for meters — Application protocols.
[3] M-Bus technical introductions / m-bus.com style references (Ziegler et al.).
[4] EN 13757-4, Wireless M-Bus.
[5] OMS Group, Open Metering System specifications.
[6] EN 13757-7, Security and key management related parts.
[7] Popa, M., Smart Metering Communication Systems (survey-style references).
[8] Vendor M-Bus IoT gateway manuals (MQTT/BACnet mapping; treat as product-specific).
[9] CEN metering communications overview materials.
[10] Practical wiring and repeater application notes from M-Bus transceiver vendors.
[11] Integration notes: M-Bus to DLMS/COSEM or BMS (project-dependent).
