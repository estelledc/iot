---
schema_version: '1.0'
id: satellite-iot
title: 卫星物联网：天地一体的连接覆盖
layer: 2
content_type: survey
difficulty: intermediate
reading_time: 18
prerequisites:
  - cellular-iot-evolution-2g-5g
tags:
  - 卫星物联网
  - NTN
  - LEO
  - D2S
  - NB-IoT
  - 天地一体
  - 混合连接
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 卫星物联网：天地一体的连接覆盖

> **难度**：🟡 中级 | **领域**：卫星通信 · 广域物联网 | **阅读时间**：约 18 分钟

## 日常类比

远洋冷藏箱要定时上报温度，但公海没有手机基站。传统海事卫星模组与按条计费对低价传感器往往不经济。卫星物联网方向是：用更接近地面窄带物联网（NB-IoT）/LoRa 成本结构的终端，在无覆盖区仍能回传小数据[1][2]。

## 摘要

地面蜂窝难以覆盖海洋、沙漠、极地等广阔区域。低地球轨道（LEO）星座与第三代合作伙伴计划（3GPP）非地面网络（NTN）推动“蜂窝协议上星”和直连卫星（Direct-to-Satellite, D2S）。本文综述轨道选择、传统卫星物联网与 NTN、透明/再生架构、应用与成本边界。连接数与价格预测来自市场报告叙事，**不作承诺**[9][10]。

## 1. 轨道与系统类型

| 轨道 | 高度叙事 | 时延 | IoT 含义 |
|------|----------|------|----------|
| GEO | ~36000 km | 大 | 终端更难做小低功耗 |
| MEO | 中间 | 中 | 较少作海量低成本 IoT |
| LEO | 约 300–2000 km | 相对小 | 更利小天线与链路预算 |

传统系统（如短突发、单向简易、VHF 小数据等）多用专用协议与模组。NTN（Rel-17 起）目标是让 NB-IoT/LTE-M 类终端经适配连卫星，复用芯片与运营生态[1][2]。

## 2. NTN 关键适配

| 挑战 | 原因 | 方向 |
|------|------|------|
| 大时延 | 星地距离 | 扩展定时提前/HARQ 等定时 |
| 多普勒 | LEO 高速运动 | GNSS+星历预补偿 |
| 大小区 | 波束覆盖广 | 随机接入与波束资源扩展 |

透明转发：星上变频放大，基站功能在关口站。再生：星上部分/全部基站功能，利于缺关口站几何，但卫星更复杂。手机应急卫星消息与物联网 NTN 芯片同属 D2S 热潮，能力与资费完全不同，不可混用指标。

## 3. 天地一体与应用

双模模组：有地面走蜂窝（通常更便宜），无覆盖切卫星。应用：海运冷链与渔船、偏远农牧、油气电力管线、灾后传感器。LoRa 星上网关等非 3GPP 路径以免授权与极低速率为特点，服务质量与标准成熟度不同[6]。

| 成本项 | 传统专用卫星 IoT 叙事 | NTN 复用叙事 |
|--------|----------------------|--------------|
| 模组 | 明显更高 | 接近蜂窝模组目标 |
| 连接/消息 | 按系统套餐 | 预期低于传统但高于纯地面 |
| 天线 | 常专用 | 力争复用 |

## 4. 局限、挑战与可改进方向

### 1. 切换与覆盖缝

**局限**：Rel-17 级天地切换未必“秒级无感”，常需重搜[1]。
**改进**：业务层重试与缓存；跟踪 Rel-18/19 移动性增强。

### 2. 频谱与干扰

**局限**：S/L 等频段需与地面系统协调[7]。
**改进**：按认证频段选型；部署区做共存评估。

### 3. LEO 补网成本

**局限**：卫星寿命短于 GEO，需持续发射替换。
**改进**：合同评估运营商补网能力与服务连续性条款。

### 4. 市场数字误用

**局限**：把预测连接数与“模组 $x”当采购依据[9]。
**改进**：以试点实测 TCO 与在网率为准；预测仅作背景。

## 5. 实践要点

1. 先区分“专用卫星物联网”与“3GPP NTN 双模”，再谈复用红利。
2. 公海/荒漠试点验证仰角、时延与功耗，再规模化。
3. 默认地面优先、卫星补盲的混合架构控制成本。

## 参考文献

[1] 3GPP TR 38.811, Study on NR to support NTN.
[2] 3GPP TR 36.763, NB-IoT/eMTC support for NTN.
[3] 3GPP TS 38.101-5, NR UE — satellite access (as applicable).
[4] Giordani, M. and Zorzi, M., "Non-Terrestrial Networks in the 6G Era," IEEE Network, 2021.
[5] Lin, X. et al., "5G NR Evolution Meets Satellite Communications," IEEE Commun. Standards Mag., 2021.
[6] Lacuna Space / LoRa-from-space public architecture materials.
[7] ITU/3GPP frequency arrangement discussions for NTN bands.
[8] Qualcomm / MediaTek NTN IoT product briefs (vendor-specific).
[9] ABI Research satellite IoT market analyses (forecasts non-binding).
[10] NSR Non-GEO satellite IoT market reports (forecasts non-binding).
[11] Fraire et al., Direct-to-Satellite IoT survey, IEEE COMST, 2022.
[12] Skylo / MNO partnership overviews (commercial context).
[13] Legacy MSS IoT (Iridium/Globalstar/ORBCOMM) service documentation for baseline comparison.
[14] Transparent vs regenerative payload architecture notes.
[15] Hybrid terrestrial–satellite IoT operational case studies (treat KPIs as case-bound).
