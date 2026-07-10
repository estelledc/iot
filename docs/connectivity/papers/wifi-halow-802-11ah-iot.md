---
schema_version: '1.0'
id: wifi-halow-802-11ah-iot
title: WiFi HaLow 802.11ah Sub-1GHz IoT长距离通信
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - wifi-halow-802-11ah
tags:
  - WiFiHaLow
  - 802.11ah
  - Sub-1GHz
  - LPWAN
  - TWT
  - RAW
  - 农业物联网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# WiFi HaLow 802.11ah Sub-1GHz IoT长距离通信

> **难度**：🟡 中级 | **领域**：WiFi IoT专用 | **阅读时间**：约 14 分钟

## 日常类比

农场里普通步话机（2.4/5 GHz Wi‑Fi）清晰但隔座小山就没声；低频大功率对讲（HaLow）慢一点，却能翻山几公里。HaLow 把 Wi‑Fi 协议栈放到 Sub‑1 GHz，换距离与穿透，并尽量保住 IP 原生与熟悉的安全模型[1][4]。

## 摘要

面向 IoT 的 HaLow 叙事：公里级覆盖、窄带宽灵活、单 AP 大规模关联、TWT/RAW 省电，并与 LoRa/NB‑IoT 等 LPWAN（低功耗广域网）对照选型。覆盖与速率为量级，**受法规功率、带宽与地形约束**；细节 PHY/地区频段见姊妹文 `wifi-halow-802-11ah`[1][2]。

## 1. 设计目标与参数量级

| 目标 | HaLow 手段 | IoT 含义 |
|------|------------|----------|
| 更远覆盖 | Sub‑1 GHz + 窄信道 | 大棚/园区少中继 |
| 低功耗 | TWT、RAW 等 | 电池传感器 |
| 大容量 | 大规模 AID/分层信标等机制 | 单 AP 大量终端 |
| IP 原生 | 标准 IP 栈 | 少协议网关 |

| 参数 | HaLow 量级 | 传统 2.4 GHz Wi‑Fi 量级 |
|------|------------|-------------------------|
| 带宽选项 | 1/2/4/8/16 MHz | 20/40 MHz 为主 |
| 吞吐 | 约百 kbps～数十 Mbps | 更高峰值 |
| 室外覆盖叙事 | 可达公里级 | 通常百米级 |
| 安全 | 认证项目强调 WPA3 | WPA2/3 |

## 2. 为何低频更“远”

FSPL（自由空间路径损耗）随频率降而减；波长更长则绕射/部分穿障叙事更好。相对 2.4 GHz，900 MHz 量级链路预算常更优，但**室内外实测差一截很常见**，须勘测[3]。与 LoRa 常共用邻近 ISM：LoRa 用 CSS 换极远极低速率；HaLow 用 OFDM 换更高吞吐——同频段不同“车型”[5]。

## 3. 与 LPWAN 选型对照

| 维度 | HaLow | LoRa/LoRaWAN | NB‑IoT |
|------|-------|--------------|--------|
| 速率 | 较高（窄带也可达较高 kbps+） | 很低 | 低～中 |
| 覆盖 | 公里级（视功率） | 常更远 | 运营商广域 |
| 网络 | 自建 AP | 自建/公网 | 蜂窝 |
| 协议 | IP 友好 | 常需应用适配/网关 | IP/非 IP 视实现 |
| 成本结构 | AP+终端模组 | 网关+模组 | 模组+套餐 |

适合：智慧农业传感、园区资产、中低码率安防（带宽够时）、想复用 IP/TLS 工具链的私有网。不适合：要运营商级广域漫游、或只要几十字节/小时且要十公里级极限链路预算时——后者常更看 LoRa/蜂窝[5][6]。

## 4. 省电与容量要点

TWT（Target Wake Time）约定唤醒窗；RAW（Restricted Access Window）限制谁在窗内竞争，减轻密集碰撞。窄 1 MHz 信道换距离与鲁棒，宽信道换视频类吞吐。单 AP“数千设备”是标准能力叙事，实际受业务占空比、上行模型和法规占空比限制——**以压测为准**[1][7]。

## 5. 局限、挑战与可改进方向

### 1. 地区频谱与认证碎片

**局限**：美/欧/中日韩频段与功率规则不同，全球 SKU 难统一。
**改进**：分区 SKU；软件信道表；认证前置。

### 2. 生态与模组成本

**局限**：相对 ESP 类 2.4 GHz，HaLow 芯片/模组选择仍少、单价常更高。
**改进**：网关先上 HaLow，末端按 TCO 混布；关注认证产品列表。

### 3. 与 Sub‑1 GHz 邻居干扰

**局限**：与 LoRa、其他 SRD 同带，CSMA 也不能消灭隐终端。
**改进**：信道规划、占空比治理、空间隔离；监测 PER。

### 4. “IP 原生”不等于“零运维”

**局限**：仍要 DHCP、安全、漫游/关联风暴与固件治理。
**改进**：沿用企业 Wi‑Fi 运维纪律；限制关联风暴场景的信标/探测负载。

## 6. 实践要点

1. 先画速率×距离×电池三角，再在 HaLow/LoRa/蜂窝间选型。
2. 农业/园区优先 1–2 MHz；视频试点再开宽信道。
3. 验收：边缘点 RSSI/MCS、电池平均电流、同频 LoRa 干扰用例。

## 参考文献

[1] IEEE Std 802.11ah-2016 — Sub-1 GHz license-exempt operation.
[2] Wi-Fi Alliance, Wi-Fi HaLow specification / certification (R1/R2 notes).
[3] ITU-R / propagation references for Sub-1 GHz vs 2.4 GHz path loss.
[4] Morse Micro / HaLow vendor white papers (treat marketing ranges cautiously).
[5] LoRa Alliance vs Wi-Fi HaLow positioning comparisons (industry notes).
[6] 3GPP NB-IoT overview for cellular LPWAN contrast.
[7] IEEE 802.11ah RAW and TWT related clauses; capacity discussion papers.
[8] Regional SRD rules: FCC Part 15, ETSI EN 300 220, etc.
[9] Wi-Fi Alliance security requirements for HaLow (WPA3 emphasis).
[10] Agricultural / campus IoT deployment case studies (anecdotal ranges).
[11] Coexistence studies of OFDM SRD with CSS LPWAN in 900 MHz ISM.
