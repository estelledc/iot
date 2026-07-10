---
schema_version: '1.0'
id: iot-connectivity-selection-framework
title: IoT连接技术选型决策框架
layer: 2
content_type: technical_analysis
difficulty: beginner
reading_time: 18
prerequisites:
  - lpwan-comparison
  - lora-vs-sigfox-vs-nbiot
tags:
  - 技术选型
  - 决策框架
  - LPWAN
  - TCO
  - 私有网络
  - 公共网络
  - 场景推荐
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT连接技术选型决策框架

> **难度**：初级 | **领域**：技术选型 | **阅读时间**：约 18 分钟

## 日常类比

选连接像选交通：楼下超市骑自行车（BLE），跨城高铁（NB-IoT），跨洲飞机（5G/卫星）。用飞机买菜或骑自行车跨省，都是典型失败模式。框架的作用是按顺序排除，而不是听厂商“都最好”[1][2]。

## 摘要

给出距离→速率→电源→成本→验证的五步流程，并覆盖私有/公共网络与常见场景。模块美元价与公里数为**量级示意**，须以目标市场报价与现场实测为准[3][5]。

## 1 为何需要框架

选项过多（Wi‑Fi、BLE、Zigbee、Thread、LoRa、Sigfox、NB-IoT、LTE-M、5G、卫星等）；选错常在部署数月后暴露为换电池、补网关、重认证。框架：逻辑排除 + 可量化维度。

## 2 关键维度

| 距离分类 | 范围（示意） | 候选 |
|----------|--------------|------|
| 超短距 | <10 cm | NFC、RFID |
| 短距 | <100 m | BLE、Zigbee、Wi‑Fi、Thread、Z-Wave |
| 中距 | 100 m–5 km | Wi‑Fi HaLow、Sub‑GHz 专有 |
| 长距 | 5–50 km | LoRa、Sigfox、NB-IoT、LTE-M |
| 超长距 | >50 km | 卫星、广域蜂窝 |

手册“最大距离”是开阔地极限；室内墙体下应大幅折减[2]。

| 速率分类 | 范围（示意） | 应用倾向 |
|----------|--------------|----------|
| 极低 | <1 kbps | 开关、温度 |
| 低 | 1–100 kbps | 周期传感 |
| 中 | 100 kbps–1 Mbps | 音频、图片 |
| 高 | >1 Mbps | 视频 |

电源：市电可放开；多年电池几乎只剩 LPWAN/低占空比短距；能量收集仅匹配极低功耗模式。成本看总拥有成本（TCO）：模组 + 基建 + 年费 + 换电池，而非只看模组标价[3][5]。

| 延迟分类 | 范围 | 候选倾向 |
|----------|------|----------|
| 实时 | <10 ms | Wi‑Fi、5G URLLC |
| 低 | <1 s | LTE、BLE |
| 中 | <10 s | NB-IoT、LoRa Class C |
| 高容忍 | 分钟级 | Sigfox、LoRa Class A |

可靠性：生命安全偏授权频谱与冗余；需确认则选带 ACK 的模式；趋势监测可接受尽力而为。另评移动性、下行、安全、生态成熟度。

## 3 私有 vs 公共

| 模型 | 优点 | 代价 | 适合 |
|------|------|------|------|
| 私有 | 可控、少月费 | 基建与运维 | 园区高密度 |
| 公共 | 快部署、广覆盖 | 订阅、第三方路径 | 分散广域 |
| 混合 | 本地+回传 | 集成复杂 | 园区+云 |

## 4 五步流程

1. 距离分桶  
2. 速率分桶  
3. 电源否决（电池/采集）  
4. TCO 与商业模型（零月费 vs 订阅）  
5. 验证：覆盖实测、≥3 家模组、案例、3–5 年路线图  

## 5 场景推荐（压缩）

| 场景 | 倾向组合 |
|------|----------|
| 智能家居 | Wi‑Fi + BLE + Zigbee/Thread；关注 Matter |
| 农业 | LoRa 优先；有覆盖可 NB-IoT |
| 抄表 | NB-IoT / Wireless M-Bus；弱覆盖用 LoRa |
| 工业控制 | WirelessHART / 5G URLLC / 有线 TSN |
| 可穿戴 | BLE |
| 车队 | 蜂窝 + GNSS |

## 6 冷链示意

需求：≥2 年电池、15 分钟/约 50 B、仓+车+装卸、模组预算约十美元量级、千到万台。距离排除纯 BLE；速率不否决 LPWAN；电源留下 LoRa/NB-IoT；运输途中无 LoRa 时 NB-IoT 公网常胜；偏远仓则 LoRa+蜂窝回传混合。数字为教学推演[3][5]。

## 7 误区与检查清单

误区：信峰值距离、忽略 TCO、为假想视频过度设计、押单一供应商、一刀切一种技术。清单：现场覆盖？多供应商？寿命按真实 profile？生命周期 TCO？同业案例？标准活跃？可升级路径？

## 8 局限、挑战与可改进方向

### 1. 静态决策树

**局限**：需求中途加视频/下行控制会推翻结论。
**改进**：把“硬否决项”单独列表；预留多模或网关升级路径[1]。

### 2. 报价过时

**局限**：模组与连接费季度波动，文中美元仅示意。
**改进**：立项当周询价；TCO 做高低两档[5]。

### 3. 实验室距离

**局限**：用手册 km 数做城市规划必翻车。
**改进**：链路预算 + 试点驱测；室内单独测穿透[2][6]。

### 4. 忽略认证与频谱

**局限**：技术合适但进不了目标国认证窗口。
**改进**：第 5 步加入认证周期与频段合规门禁。

## 9 总结

按距离、速率、电源、TCO、验证收敛到 1–2 个候选；用现场与合同约束做最终否决。合适优于“最强”。

## 参考文献

[1] A. Al-Fuqaha et al., "Internet of Things: A Survey on Enabling Technologies, Protocols, and Applications," IEEE Communications Surveys & Tutorials, 2015.

[2] U. Raza et al., "Low Power Wide Area Networks: An Overview," IEEE Communications Surveys & Tutorials, 2017.

[3] K. Mekki et al., "A Comparative Study of LPWAN Technologies," ICT Express, 2019.

[4] W. Ayoub et al., "Internet of Things security: A review," Digital Communications and Networks, 2019.

[5] GSMA, "Mobile IoT Technologies: NB-IoT and LTE-M," 2020.

[6] LoRa Alliance, "LoRaWAN Specification v1.0.4," 2020.

[7] 3GPP TR 45.820, "Cellular system support for ultra-low complexity and low throughput IoT."

[8] Connectivity Standards Alliance, "Matter Specification," 2022+.

[9] IEEE 802.15.4, "Low-Rate Wireless Personal Area Networks," 2020.

[10] Sigfox / UnaBiz, "Technical Overview," white paper.

[11] Bluetooth SIG, "Bluetooth Core Specification," LE related volumes.
