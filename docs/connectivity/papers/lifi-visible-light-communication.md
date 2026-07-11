---
schema_version: '1.0'
id: lifi-visible-light-communication
title: 可见光通信 LiFi 技术：用灯光传数据
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - infrared-communication-irda-iot
  - hybrid-connectivity-multi-protocol
tags:
  - LiFi
  - VLC
  - 802.11bb
  - OFDM
  - 可见光定位
  - LED
  - 光无线通信
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 可见光通信 LiFi 技术：用灯光传数据

> **难度**：🟡 中级 | **领域**：短距光通信 | **阅读时间**：约 18 分钟

## 日常类比

红绿灯用亮灭传“停/走”。LiFi 让 LED 以人眼难察觉的高速闪烁编码比特；吸顶灯兼“光路由器”，光难穿墙——移动性差，但物理隔离利于防窃听。工厂金属环境射频乱、灯却到处都是，故被认真评估[1][2]。

## 摘要

可见光/近红外光通信用强度调制；商用磷光白光 LED 调制带宽常仅数 MHz，需均衡或滤波。IEEE 802.11bb 把光链路纳入 802.11 家族。实验室 Gbps 与产品百 Mbps 量级不可混谈，**峰值非现场吞吐**[2][3]。

## 1. 调制与 LED 瓶颈

| 调制 | 思路 | 复杂度 |
|------|------|--------|
| OOK | 亮/灭 | 低 |
| VPPM 等 | 兼顾调光 | 低–中 |
| 光 OFDM（DCO/ACO） | 多载波，须实值非负 | 高 |
| 光 MIMO | 多灯多探测器 | 最高 |

人眼对高频闪烁不敏感，LED 开关可远快于视觉；但磷光体拖尾限制带宽。手段：接收端蓝光滤波、模拟/数字预均衡、bit-loading。公开实验单灯十余 Gbps 属特定器件与条件[3]。

## 2. 接收与链路

| 探测器 | 特点 | 场景 |
|--------|------|------|
| PIN | 成本/带宽均衡 | 通用终端 |
| APD | 灵敏更高 | 弱光/更远 |
| 图像传感器 | 慢 | 低速/定位辅助 |

面积↑→光功率↑但电容↑带宽↓；常用光学集中器折中。跨阻放大器在带宽与噪声间权衡。

## 3. 与 Wi-Fi 互补

| 指标 | LiFi（802.11bb 等） | Wi-Fi 6E/7 |
|------|---------------------|------------|
| 频谱 | 光波段极宽 | GHz 级射频 |
| 实用速率 | 常百 Mbps 量级产品叙事 | 更高易得 |
| 覆盖 | 单灯米级 | 数十米级 |
| 穿墙 | 基本无 | 有 |
| 干扰 | 阳光/强光 | 同频射频 |

混合：下行光、上行红外或 Wi-Fi；出光斑回退射频。802.11bb（约 2024 年发布）复用 802.11 MAC 思路，PHY 定义光速率档位；波长实现可见光与近红外产品并存，**以标准与厂商文档为准**[2][4]。

## 4. 可见光定位（VLP）

光多径相对射频弱、灯密且位置已知，室内定位可达分米甚至更优（算法与标定相关）。RSS 三边、TDoA、摄像头几何为常见路线；Wi-Fi 指纹常米级——对比时注明方法[8]。

## 5. 局限、挑战与可改进方向

### 1. 视线依赖

**局限**：遮挡即断或严重降速。
**改进**：多灯；利用漫反射保底速；RF 回退；广角/多 PD。

### 2. 环境光

**局限**：阳光可使探测器饱和。
**改进**：窄带滤光；近红外波段；直流消除与自适应滤波。

### 3. 上行困难

**局限**：终端光功率受眼安全与朝向限制。
**改进**：低速红外上行；高速仍走 Wi-Fi。

### 4. 照明约束

**局限**：通信波形与调光 PWM 可能互扰。
**改进**：PWM 与 OFDM 参数协同；保证照明无闪烁与显色。

## 6. 实践要点

1. 入门：Arduino OOK → Python DCO-OFDM 仿真 → 读 802.11bb PHY 要点。
2. PD 不必盲目加大面积；优先光学增益。
3. 部署按照明布点做覆盖，并设计遮挡时的切换策略。

## 参考文献

[1] Haas, H., "LiFi is a paradigm-shifting 5G technology," Reviews in Physics, 2018.
[2] IEEE 802.11bb, Light Communications standard (publication year per IEEE).
[3] Bian, R. et al., high-rate VLC with off-the-shelf LEDs, J. Lightwave Technol., 2019.
[4] pureLiFi product documentation (treat rates/coverage as vendor claims).
[5] Ghassemlooy, Z. et al., Optical Wireless Communications, CRC Press.
[6] Rajagopal, S. et al., IEEE 802.15.7 VLC modulation and dimming, IEEE Commun. Mag., 2012.
[7] Tanaka, Y. et al., Indoor VLC with white LEDs, IEICE Trans., 2003.
[8] Uysal, M. et al., IEEE 802.15.7r1 VLC channel models, IEEE Commun. Mag., 2017.
[9] Tsonev, D. et al., Gb/s single-LED OFDM VLC, IEEE Photon. Technol. Lett., 2014.
[10] Yin, L. et al., NOMA in VLC, IEEE Trans. Commun., 2016.
[11] ITU/IEEE materials on optical wireless coexistence with lighting.
[12] Hybrid RF/VLC handover and scheduling research surveys.
