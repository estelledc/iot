---
schema_version: '1.0'
id: sub-ghz-band-comparison
title: Sub-GHz 频段技术对比：穿墙利器的选择之道
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 14
prerequisites:
  - lpwan-comparison
tags:
  - Sub-GHz
  - LoRa
  - Sigfox
  - Wi-SUN
  - 链路预算
  - ISM
  - 传播
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Sub-GHz 频段技术对比：穿墙利器的选择之道

> **难度**：🟡 中级 | **领域**：LPWAN / 射频传播 | **阅读时间**：约 14 分钟

## 日常类比

口哨（高音）穿不过墙，低音炮（低音）能震到隔壁——2.4 GHz 像高音，Sub-GHz（通常指 <1 GHz ISM/SRD）像低音：路径损耗与穿透叙事更优，但可用带宽更窄、速率更低。水表日传几十字节时，低速率反而是匹配而非缺陷[1][2]。

## 摘要

选型同时看**法规**（功率、占空比、LBT/跳频）与**波形**（LoRa CSS、Sigfox UNB、Wi-SUN、Z-Wave 等）。自由空间损耗随频率上升；城市实测覆盖远小于理论视距。**公里数与电池年数仅为量级对照**[3][4]。

## 1. 法规与频段（须本地核实）

| 频段叙事 | 地区 | 约束要点 |
|----------|------|----------|
| ~433 MHz | 多地 SRD | 功率低、干扰源多 |
| 470–510 MHz | 中国等 | LoRaWAN CN470 等规划 |
| 863–870 MHz | 欧洲 | 子带功率与占空比分档 |
| 902–928 MHz | 北美 | FHSS/数字调制条款，无欧式统一占空比 |
| 920 MHz 附近 | 日韩等 | 常强制 LBT 等 |

中国常见无欧 868/美 915 同等 ISM 可用叙事，出口产品需多区域频率方案[5][6]。

## 2. 传播与链路

自由空间路径损耗随 \(20\log_{10}(f)\) 增加：同距下 Sub-GHz 相对 2.4 GHz 可低约十余 dB 量级，等效距离优势显著，但墙体/楼板附加损耗主导室内结果[1][7]。

| 对照项 | Sub-GHz 叙事 | 2.4 GHz 叙事 |
|--------|--------------|--------------|
| 穿墙 | 相对更好 | 相对更差 |
| 天线尺寸 | 更长（λ/4 更大） | 更紧凑 |
| 速率/带宽 | 常更受限 | 更宽裕 |

## 3. 技术横向

| 特性 | LoRa/LoRaWAN | Sigfox | Wi-SUN | Z-Wave LR 等 |
|------|--------------|--------|--------|--------------|
| 调制 | CSS | UNB | FSK/OFDM 等 | FSK 等 |
| 拓扑 | 多为星型 | 运营商星型 | Mesh | Mesh/星型 |
| 双向 | Class 相关 | 极弱 | 完整叙事 | 完整叙事 |
| 典型场景 | 遥测私网/公网 | 极简上行 | 公用事业 | 家居 |

LoRa 用扩频因子在速率与灵敏度间滑动；占空比地区（如欧 1% 子带）会卡死日包数[4][8]。

## 4. 局限、挑战与可改进方向

### 1. 法规表过时

**局限**：功率/占空比修订后仍按旧表设计会违法。
**改进**：以现行 ETSI/FCC/工信部文本与认证实验室为准。

### 2. 覆盖承诺过度

**局限**：农村视距 km 被写进城市场标。
**改进**：分区路测；地下室单独 SF/网关密度方案。

### 3. 天线净空不足

**局限**：小壳体贴片天线实增益为负，吞掉链路预算。
**改进**：外置天线、净空与匹配（VNA）；网关架高。

### 4. 同频自干扰

**局限**：密集 LoRa/私有协议抬高底噪。
**改进**：信道规划、ADR、多网关空间复用、必要时 LBT。

## 5. 实践要点

1. 先定销售国法规，再选芯片与频率计划。
2. 链路预算：\(P_t+G_t+G_r-S_{\min}-\)余量，余量含衰落与实现损失。
3. 中国项目优先评估 CN470 LoRa 与蜂窝 IoT，勿照搬 EU868 参数。

## 参考文献

[1] Rappaport, T. S., Wireless Communications (propagation).
[2] ETSI EN 300 220, Short Range Devices 25 MHz–1 GHz.
[3] Mekki, K. et al., "A Comparative Study of LPWAN Technologies," ICT Express, 2019.
[4] LoRa Alliance, LoRaWAN Regional Parameters.
[5] 中国工信部微功率短距离无线电相关规定（以现行有效文本为准）.
[6] FCC Part 15.247 / 15.249 materials.
[7] Petäjäjärvi, J. et al., LoRa coverage / channel attenuation studies.
[8] Sigfox/UnaBiz technical overview.
[9] Wi-SUN Alliance FAN profile specifications.
[10] Z-Wave Alliance Long Range materials.
[11] Augustin, A. et al., "A Study of LoRa," Sensors, 2016.
