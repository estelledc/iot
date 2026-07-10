---
schema_version: '1.0'
id: 5g-redcap-iot
title: 5G RedCap：为物联网量身定制的 5G 技术
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 22
prerequisites:
  - cellular-iot-evolution-2g-5g
  - lte-cat-m1-vs-nbiot
  - 5g-nr-redcap-iot-device
tags:
- RedCap
- eRedCap
- NB-IoT
- LTE-M
- 5G-IoT
- 模组选型
- 网络切片
- 运营商部署
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 5G RedCap：为物联网量身定制的 5G 技术

> **难度**：🟡 中级 | **领域**：蜂窝物联网 | **阅读时间**：约 22 分钟

## 日常类比

完整 5G NR 像满配 SUV：动力强、油耗与车位都贵。NB-IoT 像电动自行车：极省电但载不动视频。RedCap（Reduced Capability）是紧凑型轿车——中等速率、成本与功耗，专门填 LPWAN 与旗舰 5G 之间的缺口[1][2]。

## 摘要

以对比为主：整理 Rel-17 RedCap / Rel-18 eRedCap 相对完整 NR、NB-IoT、LTE-M 的能力与选型建议，并概述运营商部署节奏、覆盖代价与迁移路线。速率、价格、连接数预测为规格或市场量级，随时间变化[3][4][12]。

## 1 规格对比

| 参数 | 完整 NR | RedCap (R17) | eRedCap (R18) | NB-IoT | LTE-M |
|------|---------|--------------|---------------|--------|-------|
| 带宽量级 | 100 MHz 级 | 20 MHz | 5 MHz | ~180 kHz | 1.4 MHz |
| 下行峰值倾向 | Gbps | 约百 Mbps 量级 | ~10 Mbps 量级 | kbps | ~Mbps |
| 天线 | 多 RX MIMO | 1–2 RX | 常 1 RX | 1 | 1–2 |
| 双工 | 全双工为主 | 可 HD-FDD | 更简化 | HD-FDD | HD-FDD/FDD |
| 核心网 | 5GC | 5GC | 5GC | 常 EPC | 常 EPC |
| 切片 | 支持 | 可支持 | 可支持 | 基本无 | 基本无 |

削减带宽与天线是降本降耗主因；HD-FDD 省双工器。RRC Inactive 小数据传输（SDT）等可降信令，视网络支持而定[1][2][7]。

## 2 怎么选

| 需求 | 更合适 |
|------|--------|
| 极小包、超长电池、深覆盖 | NB-IoT |
| 移动性/语音、中等数据（当前） | LTE-M；中期看 eRedCap |
| 图片/视频、要 5G 切片/定位 | RedCap |
| Gbps 或硬 URLLC | 完整 NR |

## 3 场景要点

- **可穿戴**：尺寸与待机；语音/定位看运营商策略。
- **工业传感/网关**：中等数据 + QoS；常有稳定供电。
- **视频**：中低码率上行；模组价差是相对完整 5G 的主因。
- **车内非安全类**：诊断/OTA/娱乐；安全直连仍要完整 NR 或 PC5 等[4][8]。

芯片如 Snapdragon X35、各家 IoT 平台已商用或量产，具体功耗降幅以厂商测试条件为准[5][6]。

## 4 部署与共存

中国运营商公开材料显示 2024 年起 RedCap 商用推进较快；欧美多为试商用/计划节奏，以各运营商公告为准[9][11]。共存上：NB-IoT/LTE-M 多留在 4G 频谱，RedCap 用 NR 频段；需 UE 能力上报与接入控制，避免错误调度[1][10]。

覆盖：少天线/窄带可能损失数 dB 量级链路预算，可用重复传输、低频段与上行增强缓解[2][7]。

## 5 迁移时间线（示意）

NB-IoT 存量大、生命周期长；LTE-M 新增或逐步转向 eRedCap；RedCap 承接中端 5G IoT。市场预测中的「十亿连接」为分析师情景，不作规划唯一依据[4][12]。

## 6 局限、挑战与可改进方向

### 1. 选型表被当成绝对性能排名

**局限**：实网吞吐、覆盖与资费使「RedCap 一定快于 LTE-M」不成立[3][10]。
**改进**：用业务模型做外场对比；把资费与退网时间写入决策。

### 2. 覆盖与容量被低估

**局限**：宣传峰值忽略边缘与共享小区[2][8]。
**改进**：规划含边缘 MCS/重复；视频业务单独算上行容量。

### 3. 多技术并行增加运维成本

**局限**：NB-IoT + LTE-M + RedCap 三套终端与套餐并存[4][9]。
**改进**：分行业收敛 SKU；明确何年停售何类模组。

### 4. 生态绑定与版本碎片

**局限**：早期网络软件未开齐 SDT/定位/切片[5][11]。
**改进**：采购列必选特性清单；认证矩阵锁定版本。

## 7 总结

RedCap/eRedCap 是 5G 中端 IoT 档位，与 NB-IoT/LTE-M 长期并存。选型看数据量、移动性、是否要 5GC 特性，而不是「凡 IoT 都上 RedCap」。

## 参考文献

[1] 3GPP, "Study on support of reduced capability NR devices," TR 38.875, Release 17.

[2] 3GPP, "NR; UE radio transmission and reception," TS 38.101-1, Release 17（含 RedCap 相关）。

[3] 3GPP, "Study on further NR RedCap UE complexity reduction," TR 38.865, Release 18.

[4] GSMA, "5G IoT: transition from LPWA to RedCap related outlook," 相关白皮书.

[5] Qualcomm, "Snapdragon X35 5G Modem-RF System," Product Brief, 2024.

[6] MediaTek, "T300 5G RedCap Platform," Product Brief, 相关年份.

[7] S. Parkvall et al., "5G NR RedCap: Scalable 5G for IoT," IEEE Communications Magazine, 2024.

[8] Ericsson, "5G RedCap: Opening New 5G Opportunities," Technology Review, 2024.

[9] 中国移动研究院, "5G RedCap 技术白皮书," 2024.

[10] R. Ratasuk et al., "NR RedCap: Reducing 5G Device Complexity for IoT Applications," IEEE IoT Magazine, 2024.

[11] Nokia, "5G RedCap for Industrial IoT," White Paper, 2024.

[12] ABI Research 等, "5G RedCap chipset and module market analysis," 相关季度报告.
