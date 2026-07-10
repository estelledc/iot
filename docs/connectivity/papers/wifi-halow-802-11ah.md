---
schema_version: '1.0'
id: wifi-halow-802-11ah
title: WiFi HaLow (802.11ah)：专为物联网设计的长距离 WiFi
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - wifi-6-ofdma-mu-mimo-iot
tags:
  - WiFiHaLow
  - 802.11ah
  - Sub-1GHz
  - OFDM
  - MCS
  - 信道带宽
  - 标准化
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# WiFi HaLow (802.11ah)：专为物联网设计的长距离 WiFi

> **难度**：🟡 中级 | **领域**：低功耗广域网、Sub-GHz 通信 | **阅读时间**：约 14 分钟

## 日常类比

低音能穿墙、高音出屋就散——波长更长更好绕障。HaLow 把 Wi‑Fi“音调”从 2.4 GHz（波长约 12.5 cm）降到约 900 MHz（波长约 33 cm），用窄信道换距离与省电，仍尽量走同一套 IP“交通规则”，少一次协议换乘[1][2]。

## 摘要

本文侧重 **802.11ah/HaLow 标准与 PHY/MAC 取舍**：地区频段、1–16 MHz 带宽、OFDM/MCS 速率量级、与传统 Wi‑Fi 的定位。应用选型与 LPWAN 对照见 `wifi-halow-802-11ah-iot`。文中速率与公里数为标准/厂商量级，**非保证链路预算**[1][4]。

## 1. 起源与时间线

传统 Wi‑Fi 快但耗电、覆盖短；Zigbee/BLE 省电但覆盖有限；LoRa 等极远但速率低且常非 IP 原生。802.11ah 工作组约 2010 启动，2016 年标准发布；Wi‑Fi 联盟品牌名 HaLow，其后推进认证与 R2 等增强[1][2]。

| 年份线索 | 事件 |
|----------|------|
| 2010 | 802.11ah 工作组成立 |
| 2016 | IEEE 802.11ah 正式发布 |
| 2021+ | HaLow 认证与商用芯片推进 |
| 2024 线索 | HaLow R2 等互操作/安全增强叙事 |

## 2. 地区频段

| 地区 | 频段线索 | 备注 |
|------|----------|------|
| 美国 | 约 902–928 MHz | FCC Part 15 等 |
| 欧洲 | 约 863–868 MHz 等 | ETSI SRD，可用带宽更紧 |
| 中国 | Sub‑1 GHz 划分以主管部门为准 | 需型号核准等合规 |
| 日/韩/澳等 | 各自 900 MHz 附近片段 | 全球产品要分区 |

这些频段常与其他免授权技术共享，部署需共存意识[5]。

## 3. 带宽与速率量级

| 信道带宽 | 速率量级（视 MCS/空间流） | 覆盖叙事 | 场景 |
|----------|---------------------------|----------|------|
| 1 MHz | 约百 kbps～数 Mbps | 最远倾向 | 远距传感 |
| 2 MHz | 更高 | 远 | 表计/追踪 |
| 4–8 MHz | 可达十余～数十 Mbps 量级 | 中 | 较高数据率 IoT |
| 16 MHz | 更高峰值 | 相对近 | 高带宽 IoT |

PHY 为 OFDM，符号时间等参数相对 2.4 GHz Wi‑Fi 按窄带缩放；MCS（Modulation and Coding Scheme）与带宽共同决定吞吐。1 MHz 是“距离优先”常用点[1][6]。

## 4. MAC 侧 IoT 友好机制（提要）

- **大规模关联**：标准支持很大 AID 空间；信标/TIM 分层减轻听 Beacon 负担。
- **RAW**：Restricted Access Window，限制竞争集。
- **TWT**：约定唤醒，降空闲听射频时间。
- **安全**：认证与产品叙事强调 WPA3 基线[2][7]。

相对 802.11n/ac：HaLow 不追求室内峰值影音体验，而追求 Sub‑1 GHz 下的可达性与规模。

## 5. 局限、挑战与可改进方向

### 1. 峰值速率天花板

**局限**：再开 16 MHz 也难与 5/6 GHz Wi‑Fi 宽信道比峰值。
**改进**：视频等高吞吐留在 5/6 GHz；HaLow 承载控制与中低码率。

### 2. 法规占空比与功率帽

**局限**：欧等地区 SRD 规则可能显著限制空口时间与 EIRP。
**改进**：按市场做链路与上报周期设计；勿用美国实测推全球。

### 3. 互操作与工具链成熟度

**局限**：相对 2.4 GHz Wi‑Fi，抓包/芯片SDK/人才池仍薄。
**改进**：选认证模组；保留串口/BLE 调试面；参与联盟插拔测试。

### 4. 与经典 Wi‑Fi 运维假设不一致

**局限**：工程师易按 20 MHz BSS 经验设期望。
**改进**：培训以 1–2 MHz 与 Sub‑1 GHz 传播为主；建立独立 RF 规划。

## 6. 实践要点

1. 先定目标市场频段表，再选模组。
2. 默认从 1–2 MHz 做覆盖设计，需要再升带宽。
3. 把 HaLow AP 当“园区 LPWAN 网关”运维，而不是家用路由替代品。

## 参考文献

[1] IEEE Std 802.11ah-2016.
[2] Wi-Fi Alliance, Wi-Fi HaLow technology overview and certification.
[3] Wi-Fi Alliance HaLow R2 related announcements (verify current text).
[4] Vendor datasheets (e.g. Morse Micro MM61xx family) — rates/ranges as claims.
[5] ETSI EN 300 220 / FCC Part 15 Sub-1 GHz SRD rules.
[6] IEEE 802.11ah PHY MCS and bandwidth tables in the standard.
[7] IEEE 802.11ah RAW, TWT, and hierarchical TIM related clauses.
[8] Academic surveys on 802.11ah for IoT (capacity and range analyses).
[9] Comparison literature: 802.11ah vs 802.11n/ac design goals.
[10] Regional spectrum allocation summaries for 868/915 MHz ISM.
[11] Wi-Fi Alliance security requirements applicable to HaLow products.
