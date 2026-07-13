---
schema_version: '1.0'
id: isa100-11a-industrial-wireless
title: ISA100.11a工业无线标准与应用
layer: 2
content_type: comparison
difficulty: advanced
reading_time: 22
prerequisites:
  - hart-protocol-4-20ma-digital
  - ethernet-industrial-iot-tsn
tags:
  - ISA100.11a
  - IEC 62734
  - 工业无线
  - TDMA
  - WirelessHART
  - 6LoWPAN
  - 过程自动化
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# ISA100.11a工业无线标准与应用

> **难度**：🔴 高级 | **领域**：工业无线标准 | **阅读时间**：约 22 分钟

## 日常类比

炼油厂若给每只传感器拉线，造价高且防爆施工难。ISA100.11a 像工业“公交时刻表”：数据在固定时间槽上车，信道按跳频路线跑，用时分多址（TDMA）+ 跳频在 2.4 GHz 上求可靠[1][2]。

## 摘要

ISA100.11a（IEC 62734）面向过程自动化，PHY 基于 IEEE 802.15.4；强调传输与应用分离、骨干与现场分离。与 WirelessHART 同属工业无线，但网络层与生态不同。电池寿命与延迟承诺依赖报告周期与现场射频，**须按项目测算**[4]。

## 1. 定位与分级

| 分级 | 应用 | 延迟观感 |
|------|------|----------|
| Class 0 | 紧急安全 | 毫秒级，无线慎用 |
| Class 1–2 | 闭环/监督 | 百毫秒～秒 |
| Class 3–5 | 监测/报警/记录 | 秒～更长 |

标准主要覆盖 Class 1–5；紧急安全仍常建议有线或专用安全系统[1]。

## 2. 设计哲学

- **传输与应用分离**：可隧道承载 HART、Modbus、Foundation Fieldbus 等，不绑死单一应用协议。
- **骨干 + 现场**：市电骨干路由器组网，电池现场设备偏采集、少转发。
- **关注点分离**：PHY / DLL（同步与调度）/ 网络（IPv6+6LoWPAN）/ 传输 / 应用对象清晰[1][2]。

## 3. 角色与拓扑

| 角色 | 职责 |
|------|------|
| 现场设备 | 低占空比传感/执行 |
| 路由器 | 始终在线转发、同步 |
| 网关 | 对接 DCS/SCADA |
| 系统管理器 | 入网、时隙、路由 |
| 安全管理器 | 密钥与认证 |

拓扑：星形、网状、星-网混合（常见）。可多子网经骨干扩展。

## 4. TDMA 与跳频

时间槽长度常为十余毫秒量级；2.4 GHz 上使用一组信道伪随机跳频，获频率分集与抗窄带干扰。超帧可多长度并存；调度通信保带宽，非调度槽用竞争服务突发报警[1]。

| DLL 能力 | 说明 |
|----------|------|
| TDMA | 时隙分配 |
| 跳频 | 多信道序列 |
| ACK/重传 | 逐跳可靠 |
| 黑名单 | 避开持续差信道 |

## 5. 与 WirelessHART

| 特性 | ISA100.11a | WirelessHART |
|------|------------|--------------|
| 标准 | ISA / IEC 62734 | HART / IEC 62591 |
| 应用 | 多协议隧道 | 偏 HART |
| 网络层 | IPv6 / 6LoWPAN | 专有 |
| 路由 | 骨干为主 | 设备可广泛参与 |
| 生态部署 | 相对较少 | 更广 |

选型：棕地 HART 多选 WirelessHART；多协议/IPv6/大规模骨干偏 ISA100.11a（及既有供应商生态）[4]。

## 6. 共存与部署

与 Wi-Fi、另一套工业无线分区信道；黑名单动态跳过差频。部署前做 2.4 GHz 勘查。电池寿命随报告间隔从约年到近十年量级变化——**表值为经验区间**。北向常见 OPC UA/Modbus TCP，诊断（RSSI、电池）一并进 DCS。

## 7. 局限、挑战与可改进方向

### 1. 生态与份额

**局限**：全球装机与工具链常不及 WirelessHART[4]。
**改进**：双模网关；按工厂已有协议与供应商锁定选型。

### 2. Class 0 能力边界

**局限**：紧急安全不宜单靠本无线。
**改进**：安全回路独立；无线作监测与非安全控制。

### 3. 2.4 GHz 干扰

**局限**：Wi-Fi 等宽干扰占多信道。
**改进**：信道规划、黑名单、必要时 5 GHz Wi-Fi 分流办公流量。

### 4. 与 5G 边界模糊

**局限**：URLLC 叙事冲击，但成本功耗不同。
**改进**：低功耗自组网保留 ISA100；厂区骨干/移动用蜂窝/TSN，互补而非单替。

## 8. 实践要点

1. 先定应用 Class 与是否必须多协议隧道。
2. 骨干市电、现场电池；路由冗余按故障恢复秒级目标设计。
3. 验收含干扰下丢包、时隙延迟与电池电流剖面。

## 参考文献

[1] ISA-100.11a, Wireless systems for industrial automation: Process control and related applications.
[2] IEC 62734, Industrial communication networks — Wireless systems for industrial automation.
[3] IEEE 802.15.4, Low-Rate Wireless Networks (PHY/MAC baseline).
[4] Petersen, S. and Carlsen, S., "WirelessHART Versus ISA100.11a," IEEE Industrial Electronics Magazine, 2011.
[5] Song, J. et al., "WirelessHART: Applying Wireless Technology in Real-Time Industrial Process Control," IEEE RTAS, 2008.
[6] IEC 62591, WirelessHART related standard.
[7] IETF 6LoWPAN compression RFCs applicable to ISA100 networking.
[8] Vendor ISA100 deployment guides (e.g. Yokogawa, Honeywell) — treat as vendor-specific.
[9] Coexistence studies of IEEE 802.15.4 and Wi-Fi in plants.
[10] Industrial automation application class definitions in ISA materials.
[11] OPC UA gateway integration notes for wireless field networks.
[12] AES-128 security architecture overviews in ISA100/WirelessHART literature.
