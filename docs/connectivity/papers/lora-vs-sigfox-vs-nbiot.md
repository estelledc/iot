---
schema_version: '1.0'
id: lora-vs-sigfox-vs-nbiot
title: LoRa/Sigfox/NB-IoT LPWAN技术全面对比
layer: 2
content_type: comparison
difficulty: beginner
reading_time: 16
prerequisites:
  - lpwan-comparison
tags:
  - LPWAN
  - LoRaWAN
  - Sigfox
  - NB-IoT
  - 技术选型
  - 总拥有成本
  - 双向通信
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LoRa/Sigfox/NB-IoT LPWAN技术全面对比

> **难度**：🟢 初级 | **领域**：LPWAN选型 | **阅读时间**：约 16 分钟

## 日常类比

给偏远朋友寄信：自建邮局（LoRa/LoRaWAN）前期贵、之后可控；超低价快递（Sigfox）便宜但每日限额、几乎难回信；运营商短信/蜂窝物联网（NB-IoT）用现成基站、按月付费、双向更顺[1][2]。

## 摘要

三者同属低功耗广域网（Low Power Wide Area Network, LPWAN），在频谱、建网权、速率与下行能力上取舍不同。覆盖公里数、模组价与电池年数随地区法规、运营商套餐与业务剖面变化，**下文量级仅供选型对照，不作报价或 SLA**[1][3]。

## 1. 定位对照

| 维度 | LoRa/LoRaWAN | Sigfox | NB-IoT |
|------|--------------|--------|--------|
| 频谱 | 免许可 ISM 等 | 免许可超窄带 | 运营商许可频段 |
| 建网 | 可私有/公共 | 依赖运营网络 | 依赖蜂窝运营商 |
| 物理层 | CSS | 约百 Hz 超窄带 | OFDM/SC-FDMA 类蜂窝 |
| 标准 | LoRa Alliance | 厂商生态 | 3GPP |
| 下行 | Class A/B/C 可选 | 极受限 | 完整双向（受 PSM/eDRX 影响） |

## 2. 机制要点

**LoRaWAN**：MAC 在 LoRa 之上；可自建网关与网络服务器，数据主权强；ADR 调节 SF/功率[4]。

**Sigfox**：极窄带宽换高灵敏度与低协议开销；上行载荷与日消息数严格受限；下行能力弱。商业主体历经重组，**覆盖与长期供给需按地区核实**[5][6]。

**NB-IoT**：可独立/保护带/带内部署；覆盖增强相对 LTE 有约数十 dB 量级叙事；支持 PSM、eDRX 省电；速率高于典型 LoRa/Sigfox 小包场景，但射频与协议栈更重[3][7]。

## 3. 能力对比（量级）

| 能力 | LoRaWAN | Sigfox | NB-IoT |
|------|---------|--------|--------|
| 城市覆盖叙事 | 数 km 量级 | 数–十余 km 叙事 | 依赖基站密度与 CE 等级 |
| 峰值速率 | SF 相关，kbps 量级 | 约百 bps 量级 | 可达数十–百余 kbps 量级 |
| 双向/控制 | 中–强（视 Class） | 弱 | 强 |
| 私有网络 | 是 | 否 | 否（专网另议） |
| 典型电池叙事 | 数年 | 数年（极简业务） | 数年（依赖休眠策略） |

| 成本结构 | LoRaWAN 私网 | Sigfox | NB-IoT |
|----------|--------------|--------|--------|
| 终端模组 | 中 | 偏低叙事 | 中–高 |
| 基础设施 | 网关+服务器 CAPEX | 订阅为主 | SIM/套餐 OPEX |
| 通信费 | 私网可近零 | 年费叙事 | 月费，地区差异大 |

## 4. 选型逻辑

```
必须私有/数据主权？ → 倾向 LoRaWAN
需要可靠双向/OTA/秒级可达？ → 倾向 NB-IoT（或 LoRa Class C+市电）
极简上行、当地有覆盖且成本极敏感？ → 再评估 Sigfox
中国市场常见主选项：NB-IoT 与 LoRa 私网[8]
```

总拥有成本（Total Cost of Ownership, TCO）需按设备数、上报频率、网关密度与五年运维重算；公开美元示例易过时[9]。

## 5. 局限、挑战与可改进方向

### 1. 参数表被当成承诺

**局限**：白皮书覆盖/寿命在理想剖面下测得。
**改进**：用本地区路测与真实上报周期做容量与电池仿真。

### 2. Sigfox 供给不确定性

**局限**：网络与商务连续性因地区而异。
**改进**：合同写清覆盖与退出迁移路径（LoRa/NB-IoT）。

### 3. NB-IoT 休眠与可达性冲突

**局限**：PSM/eDRX 省电会拉长下行可达时间。
**改进**：按控制时延选休眠参数；区分“可上报”与“可被叫”。

### 4. LoRa 免许可干扰

**局限**：ISM 共存导致实地性能波动。
**改进**：信道规划、网关密度与 ADR；关键业务保留确认策略。

## 6. 实践要点

1. 先写清：数据主权、日字节量、下行时延、供电。
2. 再查当地覆盖与法规，最后算五年 TCO。
3. 混合部署常见：园区 LoRa 私网 + 广域 NB-IoT。

## 参考文献

[1] Mekki, K. et al., "A comparative study of LPWAN technologies," ICT Express, 2019.
[2] Raza, U. et al., "Low Power Wide Area Networks: An Overview," IEEE COMST, 2017.
[3] 3GPP TR 45.820 / NB-IoT related specifications (Release 13+).
[4] LoRa Alliance, "LoRa and LoRaWAN: A technical overview."
[5] Sigfox technical overview documentation (historical/operator materials).
[6] Industry reports on Sigfox restructuring / UnaBiz (treat as time-sensitive).
[7] 3GPP materials on PSM and eDRX for CIoT.
[8] China operator / MIIT oriented NB-IoT and CN470 LoRa deployment notes (region-specific).
[9] TCO case studies comparing private LoRaWAN vs cellular IoT subscriptions.
[10] Adelantado, F. et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[11] GSMA / operator NB-IoT deployment guidelines.
