---
schema_version: '1.0'
id: low-power-wide-area-network-survey
title: 低功耗广域网LPWAN技术综合综述
layer: 2
content_type: survey
difficulty: beginner
reading_time: 22
prerequisites: UNKNOWN
tags:
  - LPWAN
  - LoRaWAN
  - NB-IoT
  - LTE-M
  - Sigfox
  - 免许可频谱
  - mMTC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 低功耗广域网LPWAN技术综合综述

> **难度**：🟢 初级 | **领域**：LPWAN | **阅读时间**：约 22 分钟

## 日常类比

远郊大棚要装温湿度传感器：电池得撑数年、信号要穿田过岭、单价还得压得住。Wi-Fi（Wireless Fidelity）传不远，4G/5G 模组与电费偏贵，蓝牙（Bluetooth Low Energy, BLE）省电但覆盖短。低功耗广域网（Low Power Wide Area Network, LPWAN）用“少传、慢传”换“远传、久用”——像用明信片代替视频通话[1][2]。

## 摘要

综述 LoRaWAN、Sigfox、窄带物联网（Narrowband IoT, NB-IoT）与 LTE-M（Cat-M1）的定位、频谱与选型框架，并简述卫星 LPWAN 与 5G 大规模机器类通信（massive Machine-Type Communications, mMTC）演进。覆盖距离、电池年数、模组美元价为**量级叙事**，随地区监管、占空比与流量模型变化，不可当 SLA[1][5][9]。

## 1. LPWAN 是什么

| 特征 | 含义 | 代价 |
|------|------|------|
| 低功耗 | 高睡眠占比、协议简化 | 不适合持续高吞吐 |
| 广域 | 低速率换灵敏度/链路预算 | 时延与容量需规划 |
| 低速率 | 常为百 bps～数十 kbps | 不适配视频/大固件频繁下发 |

在“距离–速率”平面上，LPWAN 占据远距离、低速率象限，补 Wi-Fi/BLE 与宽带蜂窝之间的空白[1]。

## 2. 主流技术速览

### 2.1 LoRaWAN

物理层 LoRa 用啁啾扩频（Chirp Spread Spectrum, CSS）；LoRaWAN 是 MAC/网络协议，由 LoRa Alliance 维护。可私有部署网关，适合园区/农场自建[4][10]。

| 维度 | 量级（示意） |
|------|----------------|
| 频谱 | 免许可 ISM（如欧 868 / 美 915 / 中 470 MHz 段） |
| 速率 | 约 0.3–50 kbps（随 SF） |
| 拓扑 | 星型（终端–网关） |
| 特点 | 可自建；QoS 尽力而为 |

### 2.2 Sigfox

超窄带（Ultra Narrow Band, UNB）运营商型网络：上行载荷与日消息数严格受限，硬件与协议极简，适合“发了就走”的状态上报。商业主体历经重组，**新项目需核实当地覆盖与合同连续性**[2][11]。

### 2.3 NB-IoT 与 LTE-M

二者均为 3GPP 蜂窝物联网：授权频谱、运营商运维。NB-IoT 偏固定深覆盖小包；LTE-M 带宽更宽，更易支持移动性与语音（VoLTE）[3][5]。

| 维度 | NB-IoT | LTE-M |
|------|--------|-------|
| 带宽量级 | ~200 kHz | 1.4 MHz |
| 移动性 | 重选为主（早期版本） | 连接态切换更成熟 |
| 语音 | 通常不支持 | 可支持 VoLTE |
| 深覆盖 | MCL 目标常引用更高 | 仍显著优于传统 LTE |

部署模式含独立、保护带、带内等，容量与干扰取决于运营商配置[3]。

## 3. 对比与频谱

| 维度 | LoRaWAN | Sigfox | NB-IoT | LTE-M |
|------|---------|--------|--------|-------|
| 频谱 | 免许可 | 免许可 | 授权 | 授权 |
| 私有网 | 易 | 难 | 依赖运营商 | 依赖运营商 |
| QoS | 尽力 | 尽力 | 可有 SLA | 可有 SLA |
| 下行 | Class 相关 | 极受限 | 较好 | 较好 |
| 典型定位 | 自建/混合 | 极简上报 | 表计/深覆盖 | 移动/中等速率 |

免许可频段需遵守功率与占空比（如欧洲部分子带 1%）：即使网关空闲，终端也不能无限连发。授权频段干扰更可控，但有连接费与覆盖绑定运营商[1][6]。

## 4. 场景选型（示意）

| 场景 | 常见倾向 | 理由（需本地验证） |
|------|----------|-------------------|
| 偏远农业自建 | LoRaWAN | 蜂窝弱覆盖时可自建网关 |
| 城市表计计费 | NB-IoT | 深覆盖与运营商运维 |
| 车队/共享出行 | LTE-M | 移动性与较高速率 |
| 极简全球资产 | Sigfox 等 | 日消息极少；先查覆盖 |

决策顺序可简化为：要移动/语音？→ LTE-M；要计费级可靠与深覆盖？→ NB-IoT；要私有/无蜂窝？→ LoRaWAN；极小包全球？→ 再评估 UNB 公网[2][5]。

## 5. 演进线索

卫星直连（LoRa 星座、3GPP NTN 上的 NB-IoT 等）把覆盖伸向海洋与荒漠，时延常为分钟级量级。5G 框架下 NB-IoT/LTE-M 继续演进并服务 mMTC 目标密度；多模终端可按覆盖在蜂窝与免许可间回退，但成本与认证更复杂[5][12][15]。

## 6. 局限、挑战与可改进方向

### 1. 参数表被当成承诺

**局限**：公开白皮书的 km、年、美元价常绑定特定 SF/占空比/电池模型[1][9]。
**改进**：用本地区监管 + 实测链路预算 + TCO 重算，再写 SLA。

### 2. 免许可共存

**局限**：同频多网与异技术干扰使 PDR 随密度恶化[6][13]。
**改进**：网关规划、ADR/功率控制、信道分区；高可靠业务改授权频谱。

### 3. 技术生命周期

**局限**：Sigfox 等商业网络存在运营不确定性；蜂窝侧有 RedCap 等新档位分流[11][14]。
**改进**：合同与双模备份；路线图对齐 3GPP/联盟版本。

### 4. 容量与下行短板

**局限**：ALOHA 类 MAC 与严格下行配额限制遥控/OTA。
**改进**：见容量规划与 MAC 专文；需要强下行时优先蜂窝调度制式。

## 7. 实践要点

1. 先写清：包大小、上报周期、移动性、是否自建、是否要 SLA。
2. 用一张对比表筛到 1–2 候选，再做小范围 Pilot。
3. 把占空比、资费、覆盖地图放进 TCO，而不是只比模组标价。

## 参考文献

[1] U. Raza, P. Kulkarni, M. Sooriyabandara, "Low Power Wide Area Networks: An Overview," IEEE Commun. Surveys Tuts., 2017.
[2] K. Mekki et al., "A Comparative Study of LPWAN Technologies for Large-Scale IoT Deployment," ICT Express, 2019.
[3] 3GPP TR 45.820, Cellular System Support for CIoT, Release 13.
[4] LoRa Alliance, LoRaWAN Specification v1.0.4, 2020.
[5] GSMA, Mobile IoT in the 5G Future: NB-IoT and LTE-M, 2020.
[6] ETSI EN 300 220, Short Range Devices (relevant sub-GHz rules).
[7] J. Petäjäjärvi et al., "On the Coverage of LPWANs: Range Evaluation for LoRa," 2015.
[8] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[9] Semtech, LoRa and LoRaWAN Technical Overview (white paper).
[10] LoRa Alliance, LoRaWAN regional parameters (family of docs).
[11] UnaBiz / Sigfox technical and network status materials (verify locally).
[12] 3GPP NTN / IoT-NTN related releases (Rel-17+ overviews).
[13] K. Mikhaylov et al., analyses of LoRaWAN capacity and interference.
[14] 3GPP RedCap / eRedCap overviews for mid-tier 5G IoT.
[15] ITU-R / 3GPP materials on mMTC connection density targets.
[16] China Academy of Information and Communications Technology (CAICT), IoT white papers (market context).
[17] Haxhibeqiri et al., "A Survey of LoRaWAN for IoT," Sensors, 2018.
