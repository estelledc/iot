---
schema_version: '1.0'
id: cellular-iot-evolution-2g-5g
title: 蜂窝IoT演进：从2G到5G的技术路线
layer: 2
content_type: technical_analysis
difficulty: beginner
reading_time: 20
prerequisites: UNKNOWN
tags:
  - 蜂窝IoT
  - NB-IoT
  - LTE-M
  - RedCap
  - 5G-mMTC
  - 2G退网
  - 设备类别
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 蜂窝IoT演进：从2G到5G的技术路线

> **难度**：🟢 入门 | **领域**：蜂窝演进 | **阅读时间**：约 20 分钟

## 日常类比

经营快递时，自行车（2G）能到但慢，摩托车（3G）更快却更耗油，面包车（4G）又快又能装，无人车（5G）能力最强。寄一封信不必上无人车——蜂窝物联网（Internet of Things, IoT）同理：每一代更强，设备真正需要的往往是最合适的连接档位，而非峰值速率。

## 摘要

本文梳理蜂窝 IoT 从第二代移动通信（2G）机器对机器（Machine-to-Machine, M2M）到第五代（5G）海量机器类通信（massive Machine-Type Communications, mMTC）/超可靠低时延通信（Ultra-Reliable Low-Latency Communications, URLLC）与精简能力（Reduced Capability, RedCap）的演进。重点说明长期演进（Long Term Evolution, LTE）设备类别、窄带物联网（Narrowband IoT, NB-IoT）与 LTE-M（Cat-M1）定位，以及 2G/3G 退网后的迁移路径。速率、覆盖与成本数字以标准与行业报告量级表述，并指向参考文献[1][3][5]。

## 1. 2G：M2M 起点

全球移动通信系统（Global System for Mobile Communications, GSM）与通用分组无线服务（General Packet Radio Service, GPRS）本为话音与短信设计，却被早期 M2M 用来连“物”：车载追踪、销售点终端（Point of Sale, POS）、自动售货机等以小包、间歇上报为主[5]。

| 参数 | GSM（电路交换数据） | GPRS | EDGE（2.5G） |
|------|---------------------|------|--------------|
| 峰值速率量级 | 约 9.6 kbps | 约数十–百余 kbps | 约数百 kbps |
| 时延量级 | 数百毫秒以上 | 数百毫秒 | 约 200–300 ms |
| 典型频段 | 900/1800 MHz 等 | 同 GSM | 同 GSM |
| IoT 定位 | 极简遥测 | 早期主流 M2M | 速率略升 |

2G 存量设备仍以亿级量级存在于部分市场，但多国运营商已关停或计划关停 2G，频谱重耕为 4G/NB-IoT；北美、日澳等已基本完成，欧洲多国窗口约在 2020 年代中后期，具体以当地运营商公告为准[5][9]。

## 2. 3G：对多数 IoT 不友好的过客

通用移动通信系统（Universal Mobile Telecommunications System, UMTS）/高速分组接入（High Speed Packet Access, HSPA）把速率推到数十 Mbps 量级，但模组功耗与成本相对 GPRS 明显上升，对“小包、长寿命电池”场景往往过剩。车载信息娱乐、远程视频、企业级 POS 等带宽敏感场景曾使用 3G；大量低速率 IoT 则直接跳过 3G 留在 2G[5]。

3G 频谱对运营商价值高，退网往往快于 2G：美日等已关停，欧洲与部分亚洲市场亦在加速，迁移目标多为 LTE Cat-1/LTE-M/NB-IoT[9]。

## 3. 4G：为 IoT 量身定制

第三代合作伙伴计划（3rd Generation Partnership Project, 3GPP）自 Release 12 起在 LTE 内定义低成本机器类通信用户设备，Release 13 推出 LTE-M（Cat-M1）与 NB-IoT（Cat-NB1）[1][2][3]。

| 类别 | 下行峰值量级 | 上行峰值量级 | 定位 | 3GPP 版本 |
|------|--------------|--------------|------|-----------|
| Cat-4 | 约 150 Mbps | 约 50 Mbps | 智能手机 | Rel-8 |
| Cat-1 | 约 10 Mbps | 约 5 Mbps | 中速 IoT | Rel-8 |
| Cat-0 | 约 1 Mbps | 约 1 Mbps | 低速 IoT | Rel-12 |
| Cat-M1 | 约 1 Mbps | 约 1 Mbps | LPWAN 移动向 | Rel-13 |
| Cat-NB1 | 约数十 kbps | 约数十 kbps | 大规模固定传感 | Rel-13 |
| Cat-NB2 | 约百余 kbps | 约百余 kbps | NB 增强 | Rel-14 |

**LTE-M**：约 1.4 MHz 带宽；扩展非连续接收（extended Discontinuous Reception, eDRX）与省电模式（Power Saving Mode, PSM）拉长休眠；覆盖增强靠重复传输，代价是时延上升。适合共享出行、可穿戴、物流追踪、需一定移动性或语音（Voice over LTE, VoLTE）的终端[2]。

**NB-IoT**：约 200 kHz 带宽；最大耦合损耗（Maximum Coupling Loss, MCL）相对 GSM/LTE 可提升约 20 dB 量级，利于地下室/井盖等深覆盖；单小区连接密度目标为数万量级（依部署与业务模型）[3]。适合表计、固定环境监测等。

## 4. 5G：mMTC、URLLC 与 RedCap

| 场景 | 目标倾向 | IoT 含义 |
|------|----------|----------|
| 增强移动宽带（eMBB） | 极高峰值速率 | 手机/高清媒体为主 |
| mMTC | 每平方公里百万级连接量级 | NB-IoT/LTE-M 纳入 5G 体系延续 |
| URLLC | 毫秒级时延、极高可靠性 | 工业控制、部分车联网 |

3GPP 明确将 NB-IoT/LTE-M 作为 5G mMTC 组成部分，并经后续版本与 5G 核心网、非地面网络（Non-Terrestrial Network, NTN）等增强衔接——既有 LPWAN 投资不因“5G 换代”自动作废[3][5]。

| 参数 | 4G LTE 典型 | 5G URLLC 目标量级 |
|------|-------------|-------------------|
| 端到端时延 | 约 10–50 ms | 约 1 ms 量级（场景相关） |
| 可靠性 | 约 99.9% 量级 | 约 99.999% 量级 |
| 确定性 | 较弱 | 更强调有界时延/抖动 |

Release 17 RedCap（NR-Light）填补 NB-IoT/LTE-M 与完整新空口（New Radio, NR）之间的空白：带宽与天线数相对完整 NR 精简，下行峰值可达约百 Mbps 量级，面向工业传感、可穿戴、中等视频等[4][10]。

| 参数 | LTE-M | RedCap（Rel-17） | 完整 NR |
|------|-------|------------------|---------|
| 最大带宽量级 | 1.4 MHz | 约 20 MHz（FR1） | 可达 100 MHz 量级 |
| 下行峰值量级 | 约 1 Mbps | 约 150 Mbps | Gbps 量级 |
| 天线数 | 1 | 1–2 | 可达 4 |
| 模组成本倾向 | 较低 | 中等 | 较高 |

## 5. 选型与退网迁移

| 区域倾向 | 2G/3G 状态（概览） | 常见迁移目标 |
|----------|-------------------|--------------|
| 北美 | 多已关停 | LTE-M / Cat-1 |
| 欧洲 | 2020 年代中后期窗口 | NB-IoT / LTE-M |
| 中国 | 逐步退网与重耕 | NB-IoT 为主推之一 |
| 日韩 | 多已关停 | LTE-M / Cat-1 |
| 东南亚等 | 进度不一 | 依运营商路线 |

决策维度：数据量与时延、是否需连接态切换、是否需语音、成本与覆盖。固定、极低成本、深覆盖偏 NB-IoT；移动、交互、语音偏 LTE-M；中高速率中等成本看 RedCap/Cat-1。硬件替换与多模模组是两类迁移手段，后者可降低退网窗口风险但抬高单机成本[5][9]。

## 6. 案例要点：车队追踪 2G→LTE-M

物流车队需周期上报全球定位系统（Global Positioning System, GPS）点、行驶中保持连接。NB-IoT 连接态移动性弱，高速场景易断连；Cat-1 性能过剩、模组更贵。LTE-M 在移动性、速率与成本之间更匹配。迁移收益除规避退网外，还包括更低时延与运营商 IoT 套餐结构变化——具体资费因地而异，需以合同测算[2][5]。

## 7. 局限、挑战与可改进方向

### 1. 退网时间表碎片化

**局限**：同一品牌设备在不同国家面临不同关停节奏，全球 SKU 难统一。
**改进**：新部署优先多模或目标技术直上；存量按国家建迁移清单与备件窗口。

### 2. “5G IoT”叙事与现网能力错位

**局限**：宣传常把 URLLC/eMBB 指标直接套到表计类业务，造成选型过度。
**改进**：按业务把需求映射到 NB-IoT/LTE-M/RedCap/URLLC；以覆盖实测与 SLA 为准，而非代际口号。

### 3. 覆盖增强与时延/功耗权衡不透明

**局限**：重复传输提升 MCL，但拉长空口占用与能耗，数据表峰值易误导。
**改进**：在目标 MCL 下测端到端时延与电池模型；区分“能连上”与“业务可接受”。

### 4. RedCap 生态与价格仍在爬坡

**局限**：相对 NB-IoT/LTE-M，模组供给、认证与资费成熟度因地而异。
**改进**：中高带宽需求做 Cat-1 vs RedCap 双轨试点；关注 Rel-18 进一步降能力变体。

## 参考文献

[1] 3GPP, "Study on Provision of Low-Cost Machine-Type Communications (MTC) User Equipment Based on LTE," TR 36.888.
[2] R. Ratasuk et al., "Narrowband LTE-M System for M2M Communication," IEEE VTC Fall, 2014.
[3] Y.-P. E. Wang et al., "A Primer on 3GPP Narrowband Internet of Things," IEEE Communications Magazine, 2017.
[4] 3GPP, "Study on Support of Reduced Capability NR Devices," TR 38.875, Rel-17.
[5] GSMA, "Mobile IoT / 5G IoT use cases and device roadmap," GSMA Intelligence / Mobile IoT 相关报告.
[6] 3GPP, "Evolved Universal Terrestrial Radio Access (E-UTRA); User Equipment (UE) radio access capabilities," TS 36.306.
[7] 3GPP, "NR; Overall description," TS 38.300（含 mMTC/URLLC 相关能力描述）.
[8] ITU-R, "IMT-2020 / 5G 场景与能力框架" 相关建议书（eMBB/mMTC/URLLC）.
[9] GSMA / 各国运营商公开材料, "2G/3G sunset and IoT migration guidance," 多年度更新.
[10] 3GPP, "NR; User Equipment (UE) radio access capabilities," TS 38.306（RedCap 能力项）.
[11] 3GPP, "LTE; Evolved Universal Terrestrial Radio Access (E-UTRA) and Evolved Universal Terrestrial Radio Access Network (E-UTRAN); Overall description," TS 36.300.
[12] Ericsson / Nokia 等, "Cellular IoT in the 5G era" 白皮书（NB-IoT/LTE-M 与 5G 核心网集成论述）.
