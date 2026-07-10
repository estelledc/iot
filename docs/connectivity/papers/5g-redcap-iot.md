---
schema_version: '1.0'
id: 5g-redcap-iot
title: 5G RedCap：为物联网量身定制的 5G 技术
layer: 2
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 5G RedCap：为物联网量身定制的 5G 技术

> 难度：🟡 进阶 | 领域：蜂窝物联网 | 更新：2025-06

---

## 一句话总结

5G RedCap（Reduced Capability）是 3GPP 在 Release 17 中定义的"轻量版 5G"，通过削减天线数量、带宽和功能来降低成本和功耗，填补了 NB-IoT/LTE-M 和完整 5G NR 之间的空白。它瞄准的是可穿戴设备、工业传感器和视频监控这类"需要 5G 但不需要全部 5G"的场景。

---

## 从日常场景说起

你可能听说过"5G 改变世界"，但到 2025 年，大部分物联网设备用的还是 4G（NB-IoT、LTE-M）甚至 2G。为什么？因为完整版 5G NR 太"重"了——一个 5G NR 模组要 $20-40，功耗高达数百毫安，需要 4 根天线和 100 MHz 带宽。给一个传感器或智能手表装这么一套 5G，就像给自行车装了一台法拉利的发动机——用不上、装不下、养不起。

但 NB-IoT 又太"轻"了——速率只有几十 kbps，不能传视频、不能做实时控制。

RedCap 就是为了填这个空缺而生的"刚刚好"的 5G。

类比：如果完整版 5G 是一辆满配的 SUV（大马力、全尺寸、四驱），NB-IoT 是一辆电动自行车（极省电但载重小、速度慢），那 RedCap 就是一辆紧凑型轿车——够用、不贵、省油。

---

## RedCap 的技术规格

### 3GPP Release 17 RedCap (2022)

Release 17 是 RedCap 的首个版本，核心思路是从完整 5G NR 做"减法"：

| 参数 | 完整 5G NR | RedCap (Rel-17) | NB-IoT | LTE-M |
|------|-----------|-----------------|--------|-------|
| 最大带宽 | 100 MHz (FR1) | 20 MHz (FR1) | 180 kHz | 1.4 MHz |
| 天线数量 (下行) | 4×4 MIMO | 1×2 或 2×2 | 1×1 | 1×1 或 1×2 |
| 天线数量 (上行) | 2 或 4 | 1 | 1 | 1 |
| 下行峰值速率 | >1 Gbps | ~150 Mbps (20MHz, 2Rx) | 26 kbps | 1 Mbps |
| 上行峰值速率 | >500 Mbps | ~50 Mbps | 66 kbps | 1 Mbps |
| 双工模式 | FDD + TDD | FDD + TDD + HD-FDD | HD-FDD | HD-FDD / FDD |
| 移动性 | 完整切换 | 完整切换 | 不支持 | 支持 |
| 定位 | 完整 | 支持 | OTDOA | OTDOA |
| 模组成本 (预估) | $20-40 | $5-10 | $2-4 | $5-10 |
| 功耗模式 | C-DRX | C-DRX + eDRX + RRC Inactive | PSM + eDRX | PSM + eDRX |

### 具体削减了什么？

**带宽从 100 MHz 降到 20 MHz**：这是成本降低最大的一项。带宽越宽，ADC/DAC（模数转换器）的采样率越高，功耗和成本呈超线性增长。从 100 MHz 降到 20 MHz，射频前端成本可降低 40-60%。

**天线从 4 根降到 1-2 根**：完整 5G NR 需要 4×4 MIMO 才能达到 Gbps 级速率。RedCap 只保留 1-2 根接收天线，物料成本和 PCB 面积都大幅减少。对于手表这种小尺寸设备，2 根天线都嫌多——RedCap 允许 1×1 配置。

**支持半双工 FDD（HD-FDD）**：完整 NR 需要同时收发（需要双工器，昂贵且功耗高）。HD-FDD 允许设备在同一时刻只收或只发，省掉双工器，射频成本进一步降低。

**RRC Inactive 状态优化**：RedCap 设备可以在 RRC Inactive 状态下收发小数据包（SDT, Small Data Transmission），不需要每次通信都完成完整的 RRC 连接建立流程。这大幅降低了信令开销和延迟。

### 3GPP Release 18 eRedCap (2024)

Release 18 引入了 **eRedCap（enhanced RedCap）**，进一步做减法：

| 参数 | RedCap (Rel-17) | eRedCap (Rel-18) |
|------|-----------------|------------------|
| 最大带宽 | 20 MHz | 5 MHz |
| 天线 (下行) | 1×2 或 2×2 | 1×1 |
| 下行峰值速率 | ~150 Mbps | ~10 Mbps |
| 目标模组成本 | $5-10 | $3-5 |
| 定位 | 支持标准 NR 定位 | 纳入 Rel-18 定位增强（≤1m） |
| 目标功耗 | 接近 LTE-M | 接近 NB-IoT |

eRedCap 的定位更清晰地对标 LTE-M：速率在 1-10 Mbps 之间，成本接近 LTE-M 但具备 5G 的全部网络特性（切片、定位、URLLC QoS）。这意味着未来 eRedCap 可能逐步替代 LTE-M，成为运营商的统一中端 IoT 接入方案。

---

## 目标应用场景

### 场景 1：可穿戴设备

智能手表是 RedCap 最直观的目标用户。当前的 4G LTE 智能手表（如 Apple Watch Cellular）已经很受欢迎，但 LTE 模组功耗偏高，影响电池续航。

RedCap 的优势：
- 带宽 20 MHz 足以支持语音通话、消息推送、健康数据同步
- HD-FDD 省掉双工器，缩小 PCB 面积（手表空间极宝贵）
- eDRX 和 RRC Inactive 大幅降低待机功耗
- 支持 5G 定位（精度 < 1m），比 4G 定位提升一个量级

高通在 2024 年发布了 Snapdragon X35 5G Modem——首款商用 RedCap 调制解调器，专门针对可穿戴和工业 IoT。X35 支持 20 MHz 最大带宽、1×1 MIMO、HD-FDD，集成在 4nm 工艺上，功耗比传统 5G modem 降低约 60%。

### 场景 2：工业传感器与网关

工厂中有大量传感器需要联网上报数据。传统方案是"传感器 → 有线/无线 → 本地网关 → 蜂窝上云"。RedCap 可以让部分传感器直接蜂窝联网，跳过本地网关。

适用条件：
- 数据量中等（温度、振动、图像，每次几 KB 到几百 KB）
- 需要运营商级 QoS（生产线数据不能丢）
- 设备有稳定电源（工业传感器通常有线供电或大容量电池）
- 需要 5G 网络切片保障（将 IoT 流量和其他流量隔离）

### 场景 3：视频监控

中低端视频监控摄像头是 RedCap 的"甜蜜点"：

- 720p/1080p 视频编码后码率 1-5 Mbps → RedCap 20 MHz 足够
- 摄像头通常有 PoE 或交流供电，不是功耗敏感
- 蜂窝连接免去布网线的麻烦（如室外或临时监控点）
- 完整 5G 模组太贵（$30+ vs RedCap $8-10）

### 场景 4：车联网 C-V2X

RedCap 可以作为车辆中非安全关键应用的蜂窝通道：

- 远程诊断数据上传
- OTA 固件更新下载
- 远程信息处理（Telematics）
- 车内乘客的数据连接（如后座 WiFi 热点）

安全关键的 V2X 通信（如碰撞预警）仍需要完整 5G NR 的 URLLC 能力，或 C-V2X 的直连模式（PC5 sidelink）。RedCap 在车辆中更可能作为"第二蜂窝连接"——高优先级流量走完整 NR，低优先级走 RedCap，降低总成本。

---

## RedCap vs NB-IoT vs LTE-M：怎么选？

这是运营商和设备厂商最关心的问题。三种技术各有侧重：

| 维度 | NB-IoT | LTE-M | RedCap | eRedCap (Rel-18) |
|------|--------|-------|--------|------------------|
| 速率范围 | kbps 级 | ~1 Mbps | ~150 Mbps | ~10 Mbps |
| 成本定位 | 最低 ($2-4) | 中 ($5-10) | 中高 ($5-10) | 中 ($3-5) |
| 功耗定位 | 最低 | 低 | 中低 | 低 |
| 移动性 | 不支持切换 | 支持切换 | 完整 5G 移动性 | 完整 5G 移动性 |
| 语音 | 不支持 | VoLTE | VoNR | 可选 |
| 网络切片 | 不支持 | 不支持 | 支持 | 支持 |
| 定位精度 | ~50m | ~50m | <1m (Rel-18) | <1m (Rel-18) |
| 核心网 | 4G EPC | 4G EPC | 5G Core | 5G Core |
| 目标场景 | 抄表/追踪 | 资产管理/穿戴 | 视频/传感器/穿戴 | LTE-M 升级替代 |
| 频谱 | LTE 复用 | LTE 复用 | 5G NR 频段 | 5G NR 频段 |

**选型建议**：
- 数据量 < 1 KB/次，每天上报几次 → NB-IoT
- 需要移动性或语音，数据量中等 → LTE-M（当前）→ eRedCap（未来）
- 需要传图片/视频、需要 5G 网络特性 → RedCap
- 需要 Gbps 级速率或 URLLC → 完整 5G NR

---

## 运营商部署节奏

### 全球商用进展（截至 2025 年初）

| 运营商 | 地区 | RedCap 商用状态 | 频段 | 备注 |
|--------|------|----------------|------|------|
| 中国移动 | 中国 | 2024 Q1 商用 | n41 (2.6GHz), n28 (700MHz) | 全球首个大规模商用 |
| 中国电信 | 中国 | 2024 Q2 商用 | n78 (3.5GHz), n28 | 聚焦视频监控 |
| 中国联通 | 中国 | 2024 Q2 商用 | n78, n28 | 工业 IoT 试点 |
| Deutsche Telekom | 德国 | 2024 H2 试商用 | n78 | 聚焦工业场景 |
| Vodafone | 欧洲 | 2025 H1 试商用 | n78 | 与爱立信合作 |
| T-Mobile | 美国 | 2025 计划 | n41, n71 | 穿戴设备方向 |
| SK Telecom | 韩国 | 2024 Q4 试商用 | n78 | 智慧工厂 |

中国在 RedCap 部署上领先全球，这和中国在 NB-IoT 上的策略类似——政策推动 + 运营商快速响应 + 本土产业链配合。三大运营商在 2024 年已发放数百万 RedCap 连接。

### 芯片生态

| 芯片厂商 | 产品 | 状态 (2025) | 备注 |
|----------|------|------------|------|
| 高通 | Snapdragon X35 | 量产 | 首款商用 RedCap modem |
| 联发科 | T300 | 量产 | 面向 IoT 模组 |
| 紫光展锐 | V517 | 量产 | 中国市场主力 |
| 海思 | Balong 711 | 量产 | 华为生态 |
| 翱捷科技 | ASR5603 | 量产 | 模组价格最低 |
| Samsung | Exynos i T200 | 开发中 | 面向穿戴市场 |

RedCap 模组价格从 2024 年初的 $15-20 快速降至 2025 年初的 $8-12，预计 2025 年底将降至 $5-8，接近 LTE-M 模组价格。

---

## RedCap 的技术挑战

### 覆盖问题

RedCap 减少了天线数量和带宽，意味着接收灵敏度下降。和完整 5G NR 相比，RedCap 的覆盖范围缩小约 3-5 dB（对应约 20-30% 的覆盖半径缩小）。

应对措施：
- **覆盖增强技术**：3GPP 在 Rel-17 中定义了 RedCap 的覆盖增强（如 HARQ 重传增加、PUSCH 重复发送），可部分补偿覆盖损失
- **700 MHz 频段部署**：中国移动在 n28 (700 MHz) 频段部署 RedCap，低频段天然覆盖更广
- **上行覆盖增强（Rel-18）**：eRedCap 引入了上行 1/8π BPSK 调制和更多重复次数，进一步提升边缘覆盖

### 与现有 IoT 技术的共存

运营商需要在同一个网络中同时支持 NB-IoT、LTE-M 和 RedCap。频谱规划是关键：

- NB-IoT 占用 LTE 频谱的 180 kHz（影响极小）
- LTE-M 占用 1.4 MHz
- RedCap 占用 20 MHz NR 频谱

运营商的策略通常是：在 4G 频段保留 NB-IoT/LTE-M，在 5G 频段（如 n78 3.5GHz）部署 RedCap。随着 4G 网络逐步退网，NB-IoT/LTE-M 设备将迁移到 eRedCap。

### 设备识别与网络切片

5G 核心网需要识别 RedCap 设备并为其分配合适的资源。3GPP 定义了以下机制：

- **UE Capability 上报**：RedCap 设备在接入网络时声明自己是 RedCap 类型
- **接入控制**：运营商可以为 RedCap 设备配置专用的接入类别和优先级
- **网络切片**：RedCap 设备可以被分配到专用的网络切片（如 IoT 切片），保证 QoS

---

## 从 LTE IoT 到 5G IoT 的迁移路线

```
2016 ──── 2020 ──── 2024 ──── 2028 ──── 2032+
  │          │          │          │          │
NB-IoT    NB-IoT     RedCap   eRedCap    5G IoT
(R13)     成熟期     商用       成熟      统一平台
  │          │          │          │
LTE-M     LTE-M      LTE-M    eRedCap
(R13)     成熟期     维护期     替代
```

3GPP 的长期愿景是用 5G 核心网统一所有 IoT 接入。eRedCap 是关键过渡——它的成本和功耗接近 LTE-M，但运行在 5G 核心网上，具备切片、定位、安全等 5G 原生能力。

GSMA 预测，到 2030 年：
- RedCap/eRedCap 连接数将达到 10 亿以上
- NB-IoT 连接数将稳定在 30-40 亿（存量设备）
- LTE-M 新增部署将逐步转向 eRedCap
- 完整 5G NR IoT 连接将集中在自动驾驶、远程手术等 URLLC 场景

---

## 参考文献

1. 3GPP. "TR 38.875: Study on Support of Reduced Capability NR Devices," Release 17, 2021.
2. 3GPP. "TS 38.101-1: NR User Equipment Radio Transmission and Reception (RedCap)," Release 17, 2022.
3. 3GPP. "TR 38.865: Study on Further NR RedCap UE Complexity Reduction," Release 18, 2023.
4. Qualcomm. "Snapdragon X35 5G Modem-RF System: Bringing 5G to a Broad Range of IoT Devices," Product Brief, 2024.
5. MediaTek. "T300 5G RedCap Platform," Product Brief, 2024.
6. GSMA. "5G IoT: A Future Outlook on the Transition from LPWA to 5G RedCap," White Paper, 2024.
7. Ericsson. "5G RedCap: Opening New 5G Opportunities," Technology Review, 2024.
8. Nokia. "5G RedCap for Industrial IoT," White Paper, 2024.
9. 中国移动研究院. "5G RedCap 技术白皮书 (2024 版)," 2024.
10. S. Parkvall et al., "5G NR RedCap: Scalable 5G for IoT," IEEE Communications Magazine, vol. 62, no. 5, 2024.
11. R. Ratasuk et al., "NR RedCap: Reducing 5G Device Complexity for IoT Applications," IEEE Internet of Things Magazine, vol. 7, no. 2, 2024.
12. ABI Research. "5G RedCap Chipset and Module Market Analysis," Q2 2025.