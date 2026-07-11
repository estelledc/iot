---
schema_version: '1.0'
id: sigfox-0g-network-architecture
title: Sigfox 0G网络架构与超窄带技术
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - lora-vs-sigfox-vs-nbiot
tags:
  - Sigfox
  - UNB
  - LPWAN
  - 0G
  - 超窄带
  - UnaBiz
  - 随机接入
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Sigfox 0G网络架构与超窄带技术

> **难度**：🟡 中级 | **领域**：LPWAN | **阅读时间**：约 14 分钟

## 日常类比

嘈杂体育场里不喊整段话，只用极尖、极短的一声暗号——对面仍可能听出“是你”。Sigfox 超窄带（Ultra-Narrowband, UNB）把能量挤进约百赫兹量级带宽，用“尖”换灵敏度与穿透叙事；设备侧几乎不做蜂窝那套附着流程，故称“0G”极简网络[1][2]。

## 摘要

设备随机选频发射短包，基站侧宽带接收与云端解调；上行载荷与日消息数严格受限，下行更弱。商业主体历经重组（UnaBiz 等），**覆盖与长期供给须按地区核实，不作全球可用性承诺**[3][4]。

## 1. 0G 设备侧极简

| 对比项 | 典型蜂窝 IoT | Sigfox 设备叙事 |
|--------|--------------|-----------------|
| 连接建立 | 搜索/同步/附着/承载 | 基本无 |
| 信道协商 | 有 | 无（随机接入） |
| 网络管理信令 | 重 | 趋近于零 |
| 复杂度落点 | 终端+网络 | 网络/云侧更重 |

代价：日上行消息上限叙事（如约 140）、载荷约 12 字节量级、日下行极少、无端到端送达保证给应用——适合“偶尔上报状态”，不适合实时控制[1][5]。

## 2. UNB 物理层要点

| 参数 | Sigfox UNB 叙事 | LoRa 对照 | NB-IoT 对照 |
|------|-----------------|-----------|-------------|
| 信号带宽 | ~100 Hz 量级 | ~125 kHz 等 | ~180 kHz 量级 |
| 调制 | DBPSK（上行）/GFSK（下行）等 | CSS | OFDM/SC-FDMA 类 |
| 速率 | 百 bps 量级 | 数百 bps–数十 kbps | 可达更高 kbps |
| 灵敏度/链路预算 | 很高（窄带降噪底） | 高 | 高（许可频段） |

热噪声功率随带宽下降：带宽越窄，噪底叙事越低，有利于检测微弱信号；同时符号更长，对晶振与多普勒更敏感，故用差分调制等工程折中[2][6]。

## 3. 接入与网络架构

```
设备 → 随机频点短包（可重复发送）→ 多基站接收
     → 回传运营商云 → 客户回调/API
```

| 环节 | 作用 |
|------|------|
| 随机 ALOHA 式发射 | 去掉终端信道分配 |
| 空间分集（多站收） | 提高送达概率叙事 |
| 重复发送 | 对冲碰撞与衰落 |
| 云端解调/鉴权 | 终端不做复杂会话 |

合作运营商建站，客户买连接而非自建 MAC；与可私有部署的 LoRaWAN 权属模型不同[1][7]。

## 4. 局限、挑战与可改进方向

### 1. 业务剖面过窄

**局限**：字节与日次数墙死，固件升级/频繁遥测不适合。
**改进**：选型阶段用真实日字节核算；溢出业务改 LoRa/NB-IoT。

### 2. 下行与可控性弱

**局限**：难做可靠远程控制与低时延配置。
**改进**：控制面走其他链路；Sigfox 仅作上行遥测。

### 3. 无送达 ACK 给应用

**局限**：设备不知是否入库，易误判“已上报”。
**改进**：云侧去重+业务超时告警；关键事件多连或多技术备份。

### 4. 网络与商务连续性

**局限**：重组后地区覆盖与套餐变化快。
**改进**：合同写清覆盖地图、SLA 与退出迁移（LoRa/蜂窝）。

## 5. 实践要点

1. 先确认目标国是否有可用网络与模组供货。
2. 载荷设计按 12 字节级比特编排（状态位图优于文本）。
3. 与 LoRa/NB-IoT 对比时分开“技术指标”与“运营风险”。

## 参考文献

[1] Sigfox / UnaBiz, Technical Overview / 0G network documentation.
[2] Mekki, K. et al., "A comparative study of LPWAN technologies," ICT Express, 2019.
[3] Industry reports on Sigfox restructuring / UnaBiz (time-sensitive).
[4] Raza, U. et al., "Low Power Wide Area Networks: An Overview," IEEE COMST, 2017.
[5] Sigfox device protocol / message size and daily quota materials.
[6] Proakis & Salehi, Digital Communications (narrowband noise / DBPSK background).
[7] Adelantado, F. et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017 (contrast).
[8] ETSI EN 300 220 (SRD / sub-GHz regulatory context in EU).
[9] GSMA / LPWAN market landscape materials (cellular vs non-cellular).
[10] Centenaro, M. et al., "Long-range communications in unlicensed bands," IEEE Wireless Commun., 2016.
[11] UnaBiz partner / coverage map notes (region-specific, verify locally).
