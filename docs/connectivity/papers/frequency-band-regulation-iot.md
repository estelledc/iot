---
schema_version: '1.0'
id: frequency-band-regulation-iot
title: IoT无线频段法规：ISM/免许可/许可频段
layer: 2
content_type: tutorial
difficulty: beginner
reading_time: 18
prerequisites:
  - lpwan-comparison
  - dynamic-spectrum-access
tags:
- ISM
- 频谱法规
- 占空比
- Sub-GHz
- FCC
- ETSI
- SRRC
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# IoT无线频段法规：ISM/免许可/许可频段

> **难度**：🟢 初级 | **领域**：无线法规 | **阅读时间**：约 18 分钟

## 日常类比

无线电频谱像受管的菜市场：公共摊位（免许可/ISM）免费但要限功率、限占空比，专属摊位（许可频段）付费后独占、干扰可追责。IoT 设备选频段，等于选摊位规则——美国合法的 915 MHz 方案，到欧洲可能因 868 MHz 与占空比不合规而无法销售。

## 摘要

梳理 ITU 区域框架下 ISM/免许可与许可频段的差异，对比欧/美/中 Sub-GHz 碎片化、占空比与 EIRP/ERP 限制，并给出场景选型与全球产品合规要点。功率、占空比数值以现行法规文本为准，跨版本须复核[1][2][3]。

## 1 为何需要频段管制

适合通信的频段有限；无管制则任意功率发射会干扰导航、航空与民用无线。国际电信联盟（ITU）经世界无线电通信大会（WRC）给出全球分配框架，并分区域 1（欧非中东）、区域 2（美洲）、区域 3（亚太）[4]。各国在框架下由本国机构落地：

| 国家/地区 | 管理机构 | 说明 |
|-----------|----------|------|
| 美国 | FCC | Federal Communications Commission |
| 欧洲 | ETSI / CEPT | 短距设备（SRD）等协调标准 |
| 中国 | 工信部（MIIT） | 微功率目录与型号核准（SRRC） |
| 日本 | MIC | 国内频段与技术条件 |
| 韩国 | MSIT / KCC | 国内 IoT 频段规定 |

产品设计阶段就必须锁定目标市场法规，否则后期改射频与固件成本极高。

## 2 ISM 与免许可

ISM（Industrial, Scientific and Medical）最初服务工业加热、科研与医疗（如 2.4 GHz 微波炉），后允许低功率通信，条件是容忍 ISM 干扰且不造成有害干扰[4]。

| 频段 | 频率范围（量级） | 可用性 | 典型 IoT |
|------|------------------|--------|----------|
| 2.4 GHz | 2400–2483.5 MHz | 全球较统一 | Wi-Fi、BLE、Zigbee、Thread |
| 5.8 GHz | 约 5725–5875 MHz | 多数地区 | Wi-Fi 5 GHz 段 |
| 433 MHz | 约 433.05–434.79 MHz | 区域 1 等 | 遥控、简单传感 |
| 915 MHz | 902–928 MHz | 美洲等 | LoRa、Sigfox、Z-Wave |
| 868 MHz | 约 863–870 MHz | 欧洲 | LoRa、Sigfox、Wireless M-Bus |

「免许可」仍须遵守：发射功率上限、占空比、带宽、杂散发射等；违规可面临处罚[1][2]。

## 3 2.4 GHz：全球统一与拥挤

2.4 GHz ISM 在多国均可用于通信，利于「一套硬件卖全球」。常见协议：Wi-Fi（高带宽、功耗偏高）、BLE（低功耗短距、手机友好）、Zigbee/Thread（低功耗 Mesh）。

挑战是频谱拥挤：家庭/办公中 Wi-Fi、蓝牙、微波炉等共享约 83.5 MHz。同等功率下，2.4 GHz 穿墙与覆盖通常弱于 Sub-GHz（量级上常差数 dB 路径损耗）[5]。

## 4 Sub-GHz：传播好、法规碎

Sub-GHz（<1 GHz）路径损耗更低、穿透与绕射更好，是 LPWAN（低功耗广域网）常用选择。但区域频段不一致：

| 地区 | 频段（量级） | 主要依据 |
|------|--------------|----------|
| 欧洲 | 863–870 MHz | ETSI EN 300 220[1] |
| 美洲 | 902–928 MHz | FCC Part 15[2] |
| 中国 | 470–510 / 779–787 MHz 等 | 工信部微功率规定[3] |
| 日本 | 920–928 MHz | ARIB STD-T108 |
| 韩国 | 约 917–923.5 MHz | 国内规定 |
| 印度 | 约 865–867 MHz | WPC 等 |

915 MHz 美国产品不能直接当欧洲 868 MHz 用；需改射频与固件以符合占空比等规则。LoRaWAN 区域参数由联盟文档给出[5]。

## 5 免许可 vs 许可

| 考量 | 免许可 | 许可（蜂窝 IoT） |
|------|--------|------------------|
| 频谱费 | 无 | 运营商持牌，用户付套餐 |
| 干扰保护 | 弱，需自抗扰 | 独占，可追责干扰 |
| 功率/占空比 | 严格受限 | 由运营商侧管理 |
| 覆盖 | 常需自建网关 | 借现有蜂窝覆盖 |
| QoS | 无保证 | 相对可预期 |
| 典型技术 | LoRa、Sigfox、Wi-Fi/BLE | NB-IoT、LTE-M |

许可频段 IoT 典型路径是 NB-IoT / LTE-M（Cat-M1）：设备经 SIM/eSIM 间接使用运营商频谱[6]。

## 6 占空比与功率

占空比（Duty Cycle）= 单位时间内发射时长占比。欧洲 868 MHz 子带限制示例（以标准为准，下表为常见量级）[1]：

| 子频段 | 频率范围（量级） | 占空比 | 功率（量级） |
|--------|------------------|--------|--------------|
| g | 863.0–868.0 MHz | 1% | 25 mW ERP |
| g1 | 868.0–868.6 MHz | 1% | 25 mW ERP |
| g2 | 868.7–869.2 MHz | 0.1% | 25 mW ERP |
| g3 | 869.4–869.65 MHz | 10% | 500 mW ERP |
| g4 | 869.7–870.0 MHz | 1% | 25 mW ERP |

1% 占空比意味着每小时最多约 36 s 发射；SF12 等长空中时间会进一步压缩可发次数。美国 915 MHz 多用 FHSS/DTS 规则而非欧洲式占空比，功率上限可达约 1 W EIRP（条件满足时）[2]。

EIRP（等效全向辐射功率）与 ERP（相对半波偶极）换算约 EIRP ≈ ERP + 2.15 dB。天线增益升高则允许的发射机功率须相应下调，否则超标。

## 7 中国要点

微功率短距离设备目录（如 2019 年 52 号公告）约束 470–510 MHz（抄表/传感等）、779–787 MHz（功率更严）及 2.4 GHz 等[3]。蜂窝 IoT 走运营商许可频段（如 Band 5/8 上的 NB-IoT 部署，以运营商公告为准）。在华销售无线电设备通常需 SRRC 型号核准；未核准销售/使用可能面临没收与罚款。

## 8 选型与全球产品

| 场景 | 常见选择 | 理由 |
|------|----------|------|
| 智能家居 | 2.4 GHz（BLE/Zigbee/Thread） | 短距、全球、生态成熟 |
| 智能计量 | Sub-GHz（区域频段） | 穿墙、低功耗 |
| 资产追踪 | NB-IoT / LTE-M | 广覆盖、移动性 |
| 工业监测 | 私有 Sub-GHz + 蜂窝备份 | 可控 + 兜底 |
| 农业传感 | LoRa 等 Sub-GHz | 广域、自建网关 |
| 穿戴 | BLE | 手机兼容、低功耗 |

全球资产追踪器常采用：多频段 LoRa（欧/美）+ 中国 470 MHz 变体 + BLE 近场配置 + 可选 NB-IoT 备份；固件按区域切频段与功率。认证路径示例：FCC Part 15、CE/RED（EN 300 220/328 等）、SRRC（及适用时 CCC）。周期与费用因实验室与产品复杂度而异，立项阶段应计入[1][2][3]。

## 9 局限、挑战与可改进方向

### 1. 法规文本易过时

**局限**：正文中的功率/占空比表是快照，修订后可能失效。
**改进**：以 ETSI/FCC/工信部现行文本与 LoRaWAN Regional Parameters 为权威；发版前做合规 diff[1][2][5]。

### 2. Sub-GHz 碎片化抬高全球 SKU

**局限**：868/915/470 等无法「一射频通吃」，库存与认证翻倍。
**改进**：多频段前端 + 区域固件配置；或全球统一走 2.4 GHz / 蜂窝，牺牲部分覆盖与功耗。

### 3. 「免许可=无规则」误解

**局限**：超功率、超占空比导致干扰与执法风险。
**改进**：设计评审强制 EIRP/占空比预算；量产抽测杂散与占空比。

### 4. 许可频段依赖运营商生命周期

**局限**：2G/3G 退网类事件可使旧模组失联。
**改进**：合同约定技术支持年限；模组选型预留多模/多频；关键业务保留第二路径。

## 参考文献

[1] ETSI, "EN 300 220-2: Short Range Devices (SRD) operating in the frequency range 25 MHz to 1000 MHz," 2022.
[2] FCC, "Title 47 CFR Part 15 — Radio Frequency Devices," Code of Federal Regulations.
[3] 工业和信息化部, "微功率短距离无线电发射设备目录和技术要求," 2019 年第 52 号公告.
[4] ITU, "Radio Regulations," Edition of 2020.
[5] LoRa Alliance, "LoRaWAN Regional Parameters," RP002-1.0.4, 2023.
[6] 3GPP, "TS 36.300 / TS 23.501: E-UTRA and 5G System architecture (NB-IoT / LTE-M context)," Releases as applicable.
[7] CEPT/ECC, "ERC Recommendation 70-03: Relating to the use of Short Range Devices (SRD)," updated editions.
[8] ARIB, "STD-T108: 920 MHz-Band Telemeter, Telecontrol and Data Transmission Radio Equipment," Japan.
[9] GSMA, "Mobile IoT Deployment Guidelines / NB-IoT & LTE-M," GSMA resources.
[10] IEC / CISPR related EMC guidance for radio equipment (as applicable to product certification).
[11] RED Directive 2014/53/EU, Official Journal of the European Union.
[12] 工信部, "无线电发射设备管理规定" 及相关型号核准实施细则.
