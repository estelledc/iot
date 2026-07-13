---
schema_version: '1.0'
id: lpwan-comparison
title: LPWAN 技术全面对比：LoRaWAN vs NB-IoT vs LTE-M vs Sigfox
layer: 2
content_type: comparison
difficulty: beginner
reading_time: 20
prerequisites:
  - low-power-wide-area-network-survey
tags:
  - LPWAN
  - LoRaWAN
  - NB-IoT
  - LTE-M
  - Sigfox
  - 技术选型
  - TCO
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# LPWAN 技术全面对比：LoRaWAN vs NB-IoT vs LTE-M vs Sigfox

> **难度**：🟢 入门 | **领域**：低功耗广域网 | **阅读时间**：约 20 分钟

## 日常类比

果园里每棵树埋土壤湿度传感器：每次几个字节、电池想撑多年、基站可能在数公里外。Wi-Fi 耗电且近，蓝牙更近，宽带蜂窝往往过贵过耗电。低功耗广域网（LPWAN）像“长跑选手”——不拼速度，拼续航与距离[1][8]。

## 摘要

按频谱、速率、移动性、部署模式与总拥有成本（Total Cost of Ownership, TCO）对比 LoRaWAN、NB-IoT、LTE-M、Sigfox。连接数、模组价、覆盖公里数为**公开资料量级**，随地区与年份变化，选型以本地覆盖与实测为准[4][5][9]。

## 1. 四技术定位

| 技术 | 一句话 | 网络谁来建 |
|------|--------|------------|
| LoRaWAN | CSS 物理层 + 联盟 MAC；可自建 | 私有/公网均可 |
| NB-IoT | 3GPP 窄带蜂窝，深覆盖小包 | 运营商 |
| LTE-M | 更宽的蜂窝 IoT，偏移动/中等速率 | 运营商 |
| Sigfox | UNB 极简上行，日消息受限 | 运营商标定网络 |

LoRa 是调制；LoRaWAN 是网络协议——类似“无线电制式”与“整网规约”的分工[1][10]。

## 2. 参数对比（量级）

| 参数 | LoRaWAN | NB-IoT | LTE-M | Sigfox |
|------|---------|--------|-------|--------|
| 频谱 | 免许可 | 授权 | 授权 | 免许可 |
| 上行速率倾向 | 亚 kbps～数十 kbps | 数十 kbps 量级 | ~Mbps 量级 | ~100 bps |
| 载荷 | 相对灵活 | 较大 | 较大 | 上行约 12 B 级 |
| 移动性 | 有限 | 重选为主 | 切换更成熟 | 基本无 |
| QoS | 尽力 | 可有 | 可有 | 尽力 |
| 私有部署 | 强 | 弱 | 弱 | 弱 |

最大耦合损耗（Maximum Coupling Loss, MCL）常被用来比深覆盖：NB-IoT 目标值常引用最高一档，但**实地穿透仍取决于站址与终端天线**[2][3]。

## 3. 授权 vs 免许可

授权频谱像专用车道：干扰可控、有运维主体，但要 SIM/eSIM 与连接费。免许可像公共道路：可自建、灵活，但有占空比/功率上限与共存风险[6][8]。

| 需求 | 更贴哪边 |
|------|----------|
| 计费级可靠、少自维 | 蜂窝（NB-IoT/LTE-M） |
| 园区/跨国仓库统一私网 | LoRaWAN |
| 日消息极少、硬件极简 | Sigfox 等 UNB（先查覆盖） |

## 4. 场景映射

| 场景 | 常见选择 | 注意 |
|------|----------|------|
| 地下表计 | NB-IoT | 确认运营商深覆盖 |
| 城市传感自建 | LoRaWAN | 网关密度与占空比 |
| 共享出行定位 | LTE-M | 需要移动性时 |
| 管网极低频上报 | Sigfox/LoRa | 电池与下行几乎为零 |

市场连接数叙事上 NB-IoT 体量常最大且高度地区集中；LoRaWAN 在可自建市场增长快；Sigfox 经历主体变更后新部署需谨慎评估[5][9][16]。

## 5. 功耗与 TCO

电池寿命宣传值依赖：发送周期、ToA/信令、温度与自放电。蜂窝侧 PSM/eDRX 休眠电流可到微安级，但**连接建立开销**在极低频上报时占比大；LoRa/Sigfox 协议更瘦，却受免许可空口与重复发送影响[7][8]。

TCO = 模组 + 网关/基站分摊 + 连接费 + 电费/换电池人工 + 平台。自建 LoRa“免月租”不等于免费——网关、回传与值守都要进账。

## 6. 局限、挑战与可改进方向

### 1. 参数表误导选型

**局限**：把峰值速率、纪录距离、白皮书年限当合同指标[7][11]。
**改进**：用业务流量剖面做 Pilot；SLA 写 PDR/时延分位数。

### 2. 地区碎片化

**局限**：北美偏 LTE-M、中国偏 NB-IoT、免许可分区规则不同[4][5]。
**改进**：全球产品优先多模或明确 SKU 分国家。

### 3. 商业与标准演进

**局限**：UNB 公网连续性、5G RedCap 分流中端市场[14]。
**改进**：合同退出条款；路线图预留蜂窝档位。

### 4. 下行与 OTA

**局限**：Class A/Sigfox 下行窗口极窄，大固件 OTA 痛苦。
**改进**：需 OTA 时选 LTE-M/NB-IoT 或 LoRa Class C/有电设备。

## 7. 实践要点

1. 三个问题：动不动？要不要语音/强下行？能不能自建网？
2. 用对比表缩到双候选，再比本地覆盖与五年 TCO。
3. 混合组网往往优于单技术教条。

## 参考文献

[1] LoRa Alliance, LoRaWAN 1.0.4 Specification, 2022.
[2] 3GPP TR 45.820, CIoT, 2015.
[3] 3GPP TS 36.211, E-UTRA physical channels (NB-IoT related), Rel-17.
[4] GSMA, Mobile IoT Deployment Map / Mobile IoT resources.
[5] IoT Analytics, LPWAN market reports (treat figures as estimates).
[6] K. Mekki et al., ICT Express comparative LPWAN study, 2019.
[7] J. Petäjäjärvi et al., LoRa range evaluation, 2015.
[8] U. Raza et al., IEEE COMST LPWAN overview, 2017.
[9] CAICT, 物联网白皮书（市场语境）.
[10] Semtech, LoRa/LoRaWAN technical overview.
[11] T. Telkamp et al., long-range LoRa link reports (record ≠ planning default).
[12] ETSI EN 300 220, SRD regulations.
[13] 3GPP LTE-M / eMTC feature summaries.
[14] 3GPP RedCap overviews (migration context).
