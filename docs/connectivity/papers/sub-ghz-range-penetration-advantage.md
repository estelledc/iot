---
schema_version: '1.0'
id: sub-ghz-range-penetration-advantage
title: Sub-GHz频段穿透力与传输距离优势分析
layer: 2
content_type: technical_analysis
difficulty: beginner
reading_time: 16
prerequisites:
  - radio-propagation-model-iot
  - link-budget-calculation-lpwan
tags:
  - Sub-GHz
  - 路径损耗
  - 穿透
  - LoRa
  - Z-Wave
  - ISM
  - 链路预算
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# Sub-GHz频段穿透力与传输距离优势分析

> **难度**：🟢 初级 | **领域**：无线传播基础 | **阅读时间**：约 16 分钟

## 日常类比

站在公寓外喊话：低沉嗓音更容易穿墙，尖哨声在第一堵墙就衰减。无线电波类似——频率越低、波长越长，绕射与穿透通常越好。物联网（Internet of Things, IoT）里常说的 Sub-GHz（约 433/868/915 MHz 等低于 1 GHz 的工业科学医疗频段）相对 2.4 GHz，更像“能穿墙的男低音”[1][2]。

## 摘要

从自由空间路径损耗（Free-Space Path Loss, FSPL）、材料穿透与法规约束，说明 Sub-GHz 相对 2.4 GHz 的距离/穿透优势来源。文中 dB 差与“几倍距离”为公式示意或厂商/标准量级，**随天线效率、发射功率、接收灵敏度与环境而变**[1][3]。

## 1. 频率、波长与绕射

| 频率 | 约波长 | 典型用途 |
|------|--------|----------|
| 433 MHz | ~69 cm | 遥控/部分遥测 |
| 868 MHz | ~35 cm | 欧区 LoRa/Z-Wave 等 |
| 915 MHz | ~33 cm | 北美 ISM |
| 2.4 GHz | ~12.5 cm | Wi-Fi/BLE/Zigbee/Thread |

障碍物尺寸与波长可比时，绕射更有效；长波长更易绕过拐角与家具尺度障碍。穿透时材料吸收常随频率升高而加重（水分子在 2.4 GHz 附近吸收显著），故潮湿环境中 Sub-GHz 往往更稳[2]。

## 2. FSPL：先天距离优势

ITU 自由空间衰减形式可写为（d 为 km，f 为 MHz）[1]：

```
FSPL(dB) ≈ 20·log10(d) + 20·log10(f) + 32.44
```

频率翻倍约多 6 dB 损耗。同距下 2.4 GHz 相对 868 MHz 约多 **~8.8 dB**；若功率与灵敏度相同，自由空间距离比约 `10^(8.8/20) ≈ 2.7`——这是物理上限示意，**不是协议实测保证**[1][3]。

| 频率 | FSPL@1 km（示意） | 相对 868 MHz |
|------|-------------------|--------------|
| 433 MHz | ~84 dB | 约少 6 dB |
| 868 MHz | ~90 dB | 基准 |
| 915 MHz | ~91 dB | 约多 0.5 dB |
| 2.4 GHz | ~99 dB | 约多 8.8 dB |

## 3. 材料穿透：量级对比

建筑材料衰减依赖厚度、含水率与入射角，下表为文献/应用笔记常见**量级区间**，部署须现场测[2][3]：

| 材料（示意） | 868 MHz | 2.4 GHz | Sub-GHz 相对优势 |
|--------------|---------|---------|------------------|
| 混凝土墙 ~15 cm | 约 5–10 dB | 约 10–20 dB | 常数 dB |
| 砖墙（单层） | 约 4–8 dB | 约 8–15 dB | 常数 dB |
| 木质/玻璃 | 约 1–3 dB | 约 2–5 dB | 较小 |
| 金属板 | 很高 | 很高 | 均差（反射为主） |

室内多墙模型：`PL ≈ FSPL(d) + Σ墙损 + Σ楼板损`。同等链路预算下，Sub-GHz 往往能多穿若干墙；Z-Wave 类 Sub-GHz 家居方案常比 2.4 GHz mesh 少依赖中继，**仍取决于户型与网关位置**[5]。

## 4. 户外距离与干扰

厂商白皮书给出的城市/郊区/视距范围差异很大（扩频因子、天线高度、占空比均影响）。量级上：LoRa/Sigfox 类 Sub-GHz 常为公里级；Wi-Fi/BLE/Zigbee 多为百米内[4][5]。户外长距时 FSPL 已紧，那 ~8.8 dB 可能决定通断；非视距（Non-Line-of-Sight, NLOS）下绕射优势更明显。

2.4 GHz 工业科学医疗（Industrial, Scientific and Medical, ISM）段设备密度高（Wi-Fi、蓝牙、微波炉泄漏等），碰撞与重传更常见；Sub-GHz 使用者相对少，但欧洲等地区有严格占空比限制，不适合持续高占空比业务[3][6]。

## 5. 天线与法规权衡

| 频率 | λ/4 量级 | 设计含义 |
|------|----------|----------|
| 433 MHz | ~17 cm | 常需螺旋/外置 |
| 868/915 MHz | ~8–9 cm | PCB 倒 F/蛇形常见 |
| 2.4 GHz | ~3 cm | 芯片天线易集成 |

| 地区 | 典型 Sub-GHz | 功率/约束（示意） |
|------|--------------|-------------------|
| 欧洲 | 868 MHz | 常 14 dBm 级 + 占空比 |
| 北美 | 915 MHz | 可达更高 EIRP，常需跳频等 |
| 中国 | 470–510 MHz 等 | 需型号核准 |
| 全球统一优势 | 2.4 GHz | 规则相对一致，利于单 SKU |

## 6. 局限、挑战与可改进方向

### 1. 把 FSPL 倍数当部署承诺

**局限**：忽略天线效率、人体遮挡、金属机柜与法规功率上限。
**改进**：用链路预算工具 + 现场 RSSI/丢包测绘；报告写清天线与功率设定[3][7]。

### 2. 穿透表被当成精确工程值

**局限**：混凝土配筋、含水率可使衰减差数 dB 以上。
**改进**：关键路径做穿透抽测；潮湿季节复测[2]。

### 3. 忽视占空比与速率天花板

**局限**：Sub-GHz 适合稀疏上报，不适合音视频/频繁 OTA。
**改进**：双射频（Sub-GHz 远传 + BLE/Wi-Fi 近场配置/升级）[4][8]。

### 4. 全球产品单频段硬套

**局限**：868/915/470 硬件与认证不可互换。
**改进**：分区 SKU 或可切换射频前端；认证路径前置[6]。

## 7. 选型要点

- 选 Sub-GHz：穿墙/公里级、低占空比传感、2.4 GHz 干扰重。
- 选 2.4 GHz：高速率、全球统一频段、极小天线、手机直连。
- 组合：远传走 Sub-GHz，配网/调试走 BLE——产品上已常见[4][5]。

## 参考文献

[1] ITU-R P.525, Calculation of free-space attenuation.
[2] ITU-R P.2040, Effects of building materials and structures on radiowave propagation.
[3] Texas Instruments, Sub-1 GHz range and penetration application notes (e.g. AN1428 family).
[4] Semtech, LoRa / LoRaWAN technical overview white papers.
[5] Z-Wave Alliance, Z-Wave / Z-Wave Long Range technical overviews.
[6] ETSI EN 300 220 / FCC Part 15 — Sub-GHz ISM regulatory frameworks (region-specific).
[7] ITU-R P.1238, Indoor propagation over the frequency range relevant to IoT.
[8] Wirepas / dual-radio IoT product architecture notes (treat as vendor guidance).
[9] IEEE 802.15.4 Sub-GHz PHY options documentation.
[10] Sigfox / LPWAN coverage planning literature (ranges as order-of-magnitude).
[11] Antenna efficiency and electrically small antenna design notes for Sub-GHz IoT.
