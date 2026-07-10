---
schema_version: '1.0'
id: lpwan-comparison
title: LPWAN 技术全面对比：LoRaWAN vs NB-IoT vs LTE-M vs Sigfox
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
# LPWAN 技术全面对比：LoRaWAN vs NB-IoT vs LTE-M vs Sigfox

> 难度：🟢 入门 | 领域：低功耗广域网 | 更新：2025-06

---

## 一句话总结

LPWAN（低功耗广域网）是物联网的"长跑选手"——不追求速度，但能用一块电池跑好几年、信号穿墙越野传好几公里。四种主流技术各有侧重，选型的关键是搞清楚你的设备要传多少数据、多快传、电池能用多久。

---

## 从日常场景说起

假设你在乡下有一片果园，想监测每棵果树的土壤湿度。几百棵树，每棵树底下埋一个传感器，每小时报一次数据（就一个数字：湿度 65%）。

这个场景有三个特点：
- **数据量极小**：每次就几个字节
- **电池供电**：果园没有电源，传感器靠电池活着，最好能撑 5-10 年
- **距离远**：果园方圆几公里，传感器离最近的基站可能好几百米甚至几公里

WiFi 不行（耗电太大、传不远）、蓝牙不行（传不远）、4G/5G 不行（太贵、太耗电）。这就是 LPWAN 的舞台——专门为"少量数据 + 长距离 + 低功耗"设计的无线技术。

---

## 四大 LPWAN 技术一览

### LoRaWAN：社区的力量

**LoRa** 是物理层调制技术（由 Semtech 发明），**LoRaWAN** 是基于 LoRa 的网络协议（由 LoRa Alliance 定义）。

工作原理：LoRa 使用 **CSS（啁啾扩频）** 调制——信号频率像鸟叫一样从低到高扫过一段频谱。这种调制方式的好处是：即使信号比噪声还弱（信噪比 < 0），接收机也能正确解码。

核心参数：
- 频段：非授权频段（中国 470-510 MHz，欧洲 868 MHz，北美 915 MHz）
- 速率：0.3 - 50 kbps（取决于扩频因子 SF7-SF12）
- 范围：城市 2-5 km，郊外 10-15 km，极限案例 > 700 km（世界纪录 832 km，2024 年由 Thomas Telkamp 团队在瑞士-法国间创下）
- 电池寿命：5-15 年（典型场景，每小时上报一次）

LoRaWAN 的一大特色是**任何人都可以自建网络**。买一个 LoRa 网关（几百元），插上网线，就能覆盖周围几公里。The Things Network（TTN）就是一个全球志愿者自建的免费 LoRaWAN 网络，已有 20,000+ 网关覆盖 170+ 国家。

### NB-IoT：运营商的标准答案

NB-IoT（窄带物联网）由 3GPP 在 Release 13 中标准化（2016 年），是运营商主推的 LPWAN 技术。

工作原理：NB-IoT 运行在 **授权频段**（运营商的 LTE 频段），使用 180 kHz 窄带宽、OFDM 调制。它直接复用运营商现有的 LTE 基站，通过软件升级就能开通。

核心参数：
- 频段：授权频段（如中国移动 Band 8 900MHz，中国电信 Band 5 850MHz）
- 速率：上行 66 kbps，下行 26 kbps（单载波模式）；多载波模式可更高
- 范围：等同 LTE 覆盖范围 + 额外 20dB 覆盖增强（MCL 164 dB）
- 电池寿命：10+ 年（理论值，5Wh 电池，每天上报 200 字节）
- 连接密度：单小区 50,000-100,000 设备

NB-IoT 的最大优势是**运营商背书**——不用自己建网，插卡就能用，全国覆盖。中国的 NB-IoT 网络已覆盖 150 万+基站（截至 2024 年底），是全球最大的 NB-IoT 网络。

详见 [NB-IoT 规模部署](nb-iot-deployment.md)。

### LTE-M：NB-IoT 的"快速版"

LTE-M（也叫 eMTC，enhanced Machine Type Communication）同样来自 3GPP，但定位比 NB-IoT 更"全能"：速率更高、支持移动性和语音。

核心参数：
- 频段：授权频段（1.4 MHz 带宽，占用一个 LTE PRB 组）
- 速率：上行/下行各 1 Mbps（比 NB-IoT 快 10-40 倍）
- 范围：MCL 155.7 dB（比 NB-IoT 稍短，但仍远优于传统 LTE）
- 移动性：支持小区切换（NB-IoT 不支持）
- 语音：支持 VoLTE（NB-IoT 不支持）
- 电池寿命：5-10 年（典型场景）

LTE-M 适合需要"多传点数据"或"设备在移动"的场景。比如共享单车的定位器（需要移动中上报 GPS 坐标），用 NB-IoT 做不了（不支持切换），用 LTE-M 就行。

### Sigfox：极简主义者

Sigfox 是法国公司 Sigfox SA（后被 UnaBiz 收购）开发的超窄带（Ultra-Narrow Band）LPWAN 技术。

核心参数：
- 频段：非授权频段（868/915 MHz）
- 速率：100 bps（你没看错，每秒 100 比特）
- 消息限制：上行每天 140 条 × 12 字节 = 每天最多传 1,680 字节
- 范围：城市 3-10 km，郊外 30-50 km
- 电池寿命：10-15 年

Sigfox 的理念是"极简"：设备只管发数据，不需要建立连接、不需要握手、不需要确认。每条消息只有 12 字节（像发一条极短的短信）。这使得 Sigfox 设备的硬件成本极低、功耗极低。

但 Sigfox 的商业模式遇到了困难——2022 年母公司破产，被新加坡 UnaBiz 收购后重组。目前网络仍在运营，但新部署明显放缓。

---

## 定量对比

### 技术参数全维度对比

| 参数 | LoRaWAN | NB-IoT | LTE-M | Sigfox |
|------|---------|--------|-------|--------|
| 标准组织 | LoRa Alliance | 3GPP | 3GPP | Sigfox/ETSI |
| 频谱类型 | 非授权 | 授权 | 授权 | 非授权 |
| 频段 | Sub-GHz (470/868/915) | 运营商 LTE 频段 | 运营商 LTE 频段 | Sub-GHz (868/915) |
| 信道带宽 | 125/250/500 kHz | 180 kHz | 1.4 MHz | 100 Hz (UNB) |
| 调制方式 | CSS (啁啾扩频) | OFDM / SC-FDMA | OFDM / SC-FDMA | DBPSK / GFSK |
| 最大速率 (上行) | 50 kbps | 66 kbps | 1 Mbps | 100 bps |
| 最大速率 (下行) | 50 kbps | 26 kbps | 1 Mbps | 600 bps |
| 最大有效载荷 | 242 字节 | 1600 字节 | 1600 字节 | 12 字节 |
| 每日消息上限 | 无硬限制 (受占空比限制) | 无硬限制 | 无硬限制 | 140 条/天 |
| 覆盖范围 (城市) | 2-5 km | 1-10 km | 1-5 km | 3-10 km |
| 覆盖范围 (郊外) | 10-15 km | 可达 100+ km | 可达 11 km | 30-50 km |
| MCL (最大耦合损耗) | 157 dB (SF12) | 164 dB | 155.7 dB | 160 dB |
| 双向通信 | 有限 (Class A/B/C) | 完整 | 完整 | 有限 (下行 4条/天) |
| 移动性支持 | 不支持切换 | 不支持切换 | 支持切换 | 不支持 |
| 定位能力 | TDoA (~50m) | OTDOA (~50m) | OTDOA (~50m) | RSSI (~1km) |
| 安全性 | AES-128 | LTE 级 (USIM) | LTE 级 (USIM) | AES-128 |
| 部署模式 | 自建/公网 | 运营商公网 | 运营商公网 | Sigfox 公网 |
| 网络拓扑 | 星型 (可多网关) | 蜂窝 | 蜂窝 | 星型 |
| QoS 保证 | 无 (尽力而为) | 有 | 有 | 无 |
| 模组成本 (2025) | $2-5 | $2-4 | $5-10 | $2-3 |
| 连接费 (年) | 免费 (自建) / $1-3 (公网) | $1-5 (运营商资费) | $2-10 | $1-3 |

### 功耗与电池寿命对比

以 AA 电池 (2400 mAh, 3.6V, ~8.64 Wh) 为基准，每小时上报一次 50 字节数据：

| 场景 | LoRaWAN (SF10) | NB-IoT | LTE-M | Sigfox |
|------|----------------|--------|-------|--------|
| 发送功率 | 14 dBm | 23 dBm | 23 dBm | 14 dBm |
| 单次发送能耗 | ~0.05 mJ | ~0.5 mJ | ~1.0 mJ | ~0.03 mJ |
| 单次发送时间 | ~100 ms | ~1.5 s (含信令) | ~0.5 s | ~2 s |
| 休眠电流 | ~1 μA | ~3 μA (PSM) | ~3 μA (PSM) | ~1 μA |
| 估算电池寿命 | ~10 年 | ~8 年 | ~5 年 | ~12 年 |

注：以上为理论估算，实际电池寿命受温度、电池自放电、协议开销等因素影响，通常为理论值的 50-70%。

---

## 部署模式深度比较

### 授权频段 vs 非授权频段

这是最根本的差异。NB-IoT 和 LTE-M 使用运营商付费购买的"授权频段"，好比在高速公路上有专用车道——不会被其他人占用，服务质量有保障。LoRaWAN 和 Sigfox 使用"非授权频段"（ISM 频段），好比公共道路——免费但可能堵车。

授权频段的优势：无干扰、有 QoS 保障、运营商负责网络运维。
授权频段的劣势：需要 SIM 卡、按连接收费、受限于运营商覆盖区域。

非授权频段的优势：免费使用、可自建网络、部署灵活。
非授权频段的劣势：可能被干扰、有占空比限制（欧洲 868 MHz 限制每个信道每小时只能发射 1% 的时间）、无 QoS 保证。

### 自建网络 vs 运营商网络

LoRaWAN 允许自建网络，这在以下场景中特别有价值：

- **工厂/园区**：一个工厂可能在偏远地区，运营商信号弱。自己架几个 LoRa 网关就能覆盖整个厂区。
- **跨国部署**：一个全球性的物流公司可以在每个仓库部署 LoRa 网关，用同一套标准、同一个平台管理，不需要和每个国家的运营商谈合同。
- **研究/原型**：学生和研究者可以零成本搭建 LoRaWAN 网络做实验。

NB-IoT 则适合需要"即插即用"的场景——买个 NB-IoT 模组，插上 SIM 卡，设备就能联网。不需要自己操心基站、网关、服务器。

---

## 真实部署案例

### 案例 1：中国水表智能化（NB-IoT）

中国是全球最大的 NB-IoT 部署市场，智能水表是杀手级应用。截至 2024 年底：

- 中国已部署超过 2 亿只 NB-IoT 智能水表
- 覆盖 300+ 城市
- 中国移动 NB-IoT 网络连接数突破 4 亿（不限于水表）
- 典型部署：每 15 分钟上报一次水表读数（几十字节），电池寿命要求 6-8 年

为什么水表选 NB-IoT 而不是 LoRaWAN？因为水表在地下管井中，信号穿透要求极高；NB-IoT 的 164 dB MCL（比 LoRaWAN 多 7 dB）意味着信号能多穿透一两面墙或几米土层。而且运营商网络不需要物业配合安装网关。

### 案例 2：阿姆斯特丹智慧城市（LoRaWAN）

荷兰 KPN 电信和阿姆斯特丹市政府联合部署了 LoRaWAN 网络覆盖全城：

- 50+ 个 LoRa 网关覆盖整个阿姆斯特丹市区
- 应用：运河水位监测、桥梁开合计数、垃圾桶满溢检测、空气质量传感器
- 每个传感器每天上报 10-50 条数据
- 选择 LoRaWAN 的原因：城市传感器分布广但每个点数据量极小，自建网络成本远低于为每个传感器购买蜂窝连接

### 案例 3：共享电动滑板车追踪（LTE-M）

美国 Lime 公司的共享电动滑板车使用 LTE-M 追踪定位：

- 滑板车在城市中移动，需要持续上报 GPS 位置
- LTE-M 支持小区切换（蜂窝移动性），滑板车骑过几个小区也不会断连
- 每 30 秒上报一次位置（GPS 坐标 + 电池电量 ≈ 100 字节）
- 同时支持远程锁车/解锁命令（需要可靠的双向通信）
- NB-IoT 不行（不支持移动性）；LoRaWAN 不行（延迟太高、不支持移动中持续通信）

### 案例 4：法国供水管网泄漏监测（Sigfox）

法国 Veolia 水务公司使用 Sigfox 监测地下管网泄漏：

- 数万个声学传感器部署在地下管道接头处
- 每天凌晨 2-4 点（用水低峰期）测量管道振动，上报一次结果（12 字节）
- 传感器安装在地下，更换电池成本极高 → 需要 15 年电池寿命
- Sigfox 的超低功耗和每天仅 1-2 条消息的模式完美匹配

---

## 选型决策指南

### 按需求选技术

| 你的需求 | 推荐技术 | 原因 |
|----------|----------|------|
| 每天只传几十字节数据 | LoRaWAN 或 Sigfox | 极低功耗，免授权频谱 |
| 需要运营商级 QoS | NB-IoT | 授权频谱，有保障 |
| 设备在移动中 | LTE-M | 唯一支持小区切换的 LPWAN |
| 需要语音功能 | LTE-M | 唯一支持 VoLTE 的 LPWAN |
| 地下/深室内覆盖 | NB-IoT | MCL 最高 (164 dB) |
| 想自建网络 | LoRaWAN | 唯一支持私有部署的主流 LPWAN |
| 全球统一部署 | LoRaWAN | 非授权频段全球可用，不依赖运营商 |
| 超长电池寿命 (>10年) | Sigfox 或 LoRaWAN | 最低功耗设计 |
| 每次传数据 >100 字节 | LTE-M 或 NB-IoT | 有效载荷更大 |
| 需要 firmware OTA | LTE-M | 带宽足够做 OTA 升级 |

### 2024-2025 市场数据

根据 IoT Analytics 和 GSMA 的数据：

| 技术 | 全球连接数 (2024) | 年增长率 | 主要市场 |
|------|-------------------|----------|----------|
| NB-IoT | ~25 亿 | ~30% | 中国 (>80%)、欧洲 |
| LoRaWAN | ~4 亿 | ~40% | 全球分散 |
| LTE-M | ~3 亿 | ~25% | 北美、欧洲 |
| Sigfox | ~2000 万 | 下降 | 法国、西班牙 |

NB-IoT 的连接数远超其他技术，但大部分集中在中国（受政策推动）。LoRaWAN 增长最快，在非中国市场份额领先。LTE-M 在北美市场占优（AT&T、Verizon 主推）。Sigfox 因公司重组而增长放缓。

---

## 未来趋势

**LoRaWAN 2.4 GHz**：LoRa Alliance 正在推动 2.4 GHz 版本的 LoRa，虽然传输距离缩短，但避开了 Sub-GHz 的区域性频率差异，实现全球统一频段。

**NB-IoT 演进**：3GPP Release 17/18 持续优化 NB-IoT 的功耗和覆盖，并引入卫星回传（NTN）使 NB-IoT 可通过卫星覆盖海洋和偏远地区。详见 [卫星物联网](satellite-iot.md)。

**LTE-M 与 5G RedCap 融合**：5G RedCap（见 [5G RedCap](5g-redcap-iot.md)）定位在 LTE-M 和全功能 5G 之间，未来可能逐步承接 LTE-M 的部分场景。

**融合网关**：越来越多的网关同时支持 LoRaWAN + NB-IoT + BLE，设备可以根据场景动态切换接入技术。

---

## 参考文献

1. LoRa Alliance. "LoRaWAN 1.0.4 Specification," 2022.
2. 3GPP. "TR 45.820: Cellular System Support for Ultra-Low Complexity and Low Throughput IoT," 2015.
3. 3GPP. "TS 36.211: E-UTRA Physical Channels and Modulation (NB-IoT)," Release 17, 2023.
4. GSMA. "Mobile IoT Deployment Map," gsma.com/iot, accessed 2025.
5. IoT Analytics. "LPWAN Market Report 2024-2030," Q4 2024.
6. K. Mekki et al., "A Comparative Study of LPWAN Technologies for Large-Scale IoT Deployment," ICT Express, vol. 5, no. 1, pp. 1-7, 2019.
7. J. Petäjäjärvi et al., "On the Coverage of LPWANs: Range Evaluation and Channel Attenuation Model for LoRa Technology," ITS Telecommunications, 2015.
8. Raza, U., Kulkarni, P., & Sooriyabandara, M. "Low Power Wide Area Networks: An Overview," IEEE Communications Surveys & Tutorials, vol. 19, no. 2, pp. 855-873, 2017.
9. 中国信息通信研究院. "物联网白皮书 (2024)," 2024.
10. Semtech. "LoRa and LoRaWAN: A Technical Overview," White Paper, 2024.
11. T. Telkamp et al., "Record-Breaking 832km LoRa Link," The Things Conference, 2024.
