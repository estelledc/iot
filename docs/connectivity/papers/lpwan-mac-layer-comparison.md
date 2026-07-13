---
schema_version: '1.0'
id: lpwan-mac-layer-comparison
title: LPWAN MAC层协议对比：LoRaWAN/Sigfox/NB-IoT
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 20
prerequisites:
  - lpwan-comparison
  - low-power-wide-area-network-survey
tags:
  - MAC
  - LoRaWAN
  - Sigfox
  - NB-IoT
  - ALOHA
  - 调度
  - Class-A
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LPWAN MAC层协议对比：LoRaWAN/Sigfox/NB-IoT

> **难度**：🟡 中级 | **领域**：LPWAN协议 | **阅读时间**：约 20 分钟

## 日常类比

三条乡间单车道：LoRaWAN 像谁有货谁就上（Pure ALOHA）；Sigfox 像用极窄车身乱穿加连开三趟碰运气；NB-IoT 像红绿灯调度——上车前先要通行证。媒体访问控制（Medium Access Control, MAC）决定时延、容量、电池与能不能远程下令[1][5]。

## 摘要

对比三种主流 LPWAN 的信道接入、下行窗口、占空比/消息配额、容量与可靠性机制。设备数、丢包率区间为文献与部署**经验量级**，随负载与确认比变化[2][3]。

## 1. LoRaWAN MAC

上行 Pure ALOHA：有数据就选信道/速率发送，无先听后发、无基站时隙调度。换来终端简单、易深睡。

| Class | 下行机会 | 功耗倾向 | 适用 |
|-------|----------|----------|------|
| A | 上行后 RX1/RX2 | 最低 | 传感上报默认 |
| B | 信标同步 + ping slot | 中 | 需周期下行 |
| C | 几乎常接收 | 高 | 常需外供电 |

本质是上行密集型设计；遥控阀门若只靠 Class A，下行要等下次上行[1]。

## 2. Sigfox MAC

超窄带（UNB）ALOHA：~100 Hz 级占用，在可用谱内随机选频；消息常重复 3 次。无连接、无 ADR、无复杂状态机。下行每日条数与载荷严格受限，且多由终端请求触发——适合“上报为主、几乎不遥控”[4]。

## 3. NB-IoT MAC

继承蜂窝调度：随机接入信道（RACH）要资源 → 基站授上行授权 → 数据段确定性发送；混合自动重传请求（HARQ）等提高可靠。设备需同步、处理寻呼与跟踪区更新，复杂度最高，但信道利用率与 QoS 最好讲[3]。

## 4. 接入与下行对比

| 维度 | LoRaWAN | Sigfox | NB-IoT |
|------|---------|--------|--------|
| 接入 | 非协调 ALOHA | UNB-ALOHA + 重复 | 调度为主 |
| 冲突 | 数据段可撞；SF 正交缓解 | 靠稀疏+重复 | 主要在 RACH |
| 下行 | Class 决定 | 极受限 | 连接/寻呼可达 |
| 同步 | A 基本不需 | 不需 | 必须 |

## 5. 监管与空口时间

| 技术 | 关键约束 |
|------|----------|
| LoRaWAN（欧） | 子带占空比；高 SF ToA 可到秒级 |
| Sigfox | 日上行条数上限；单消息空口含重复 |
| NB-IoT | 授权谱无 ISM 占空比；受小区资源与运营商策略限制 |

## 6. 容量、时延、功耗、可靠性

| 维度 | LoRaWAN | Sigfox | NB-IoT |
|------|---------|--------|--------|
| 容量逻辑 | ALOHA 上界低，靠多网关/ADR | UNB 并行 + 运营配额 | 调度，重复次数吃资源 |
| 上行首发 | 可立即发 | 可立即发 | 可能先建链 |
| 强下行/OTA | Class B/C 或痛苦 | 基本不适合 | 相对合适 |
| 确认 | 可选 Confirmed | 上行无经典 ACK | HARQ/RLC |

极低频次：Sigfox/LoRa 连接开销小。高频次：NB-IoT 建链成本被摊薄。只有蜂窝侧常能谈“电信级”丢包目标；免许可侧要在应用层做幂等与补传[2][5]。

## 7. 场景与案例要点

| 需求 | 更贴 |
|------|------|
| 私有网 + 中等上报 | LoRaWAN |
| 极小包、极低频、最低运维 | Sigfox |
| 可靠双向、OTA、计费 | NB-IoT |

垃圾桶水位：日更 1–2 次时三者都能讲故事；若未来要固件 OTA 与告警必达，NB-IoT 溢价才划算。选型看演进路线，不看单日演示[5]。

## 8. 局限、挑战与可改进方向

### 1. 用 PHY 对比代替 MAC 对比

**局限**：只比灵敏度，忽略下行窗口与碰撞[2]。
**改进**：用例写清上下行比与确认需求再选型。

### 2. Class A 误当实时可控

**局限**：下行时延绑定上行业务。
**改进**：控制类终端用 Class C/蜂窝，或上行心跳拉下行。

### 3. 容量口号

**局限**：“单站百万”未绑定消息模型与 PDR[4]。
**改进**：用包/小时与目标 PDR 重算；见容量专文。

### 4. 应用层补救不足

**局限**：Unconfirmed + 无去重导致误控或丢告警。
**改进**：关键事件 Confirmed/应用 ACK；幂等命令设计。

## 9. 实践要点

1. 先画流量：上行周期、下行命令、是否 OTA。
2. MAC 哲学匹配业务：随机接入换简单，调度换确定。
3. 验收包含碰撞负载与下行可达性，不只测单设备。

## 参考文献

[1] LoRa Alliance, LoRaWAN 1.0.4 Specification.
[2] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[3] 3GPP TS 36.321, E-UTRA MAC protocol specification (NB-IoT).
[4] Sigfox/UnaBiz, Sigfox Technical Overview materials.
[5] H. Mroue et al., "MAC layer-based evaluation of IoT technologies," related LPWAN MAC surveys, 2018.
[6] ETSI EN 300 220, SRD regulations affecting MAC timing.
[7] 3GPP TR 45.820, CIoT.
[8] O. Georgiou, U. Raza, "Can LoRa Scale?" IEEE Wireless Commun. Lett., 2017.
[9] GSMA, Mobile IoT best practice / power saving (PSM, eDRX).
[10] Semtech, LoRaWAN Class A/B/C application notes.
[11] U. Raza et al., IEEE COMST LPWAN overview, 2017.
[12] K. Mekki et al., LPWAN comparative study, ICT Express, 2019.
