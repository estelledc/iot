---
schema_version: '1.0'
id: antenna-propagation-indoor-outdoor
title: 室内外天线传播特性与IoT部署考量
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - link-budget-calculation-lpwan
  - fading-multipath-iot-channel
tags:
  - 天线
  - 传播
  - 链路预算
  - 室内覆盖
  - Sub-GHz
  - 2.4GHz
  - IoT部署
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 室内外天线传播特性与IoT部署考量

> **难度**：🟡 中级 | **领域**：天线与传播 | **阅读时间**：约 20 分钟

## 日常类比

天线像扩音器：把电信号变成可传播的“声音”（电磁波），或反过来把“声音”收回来。功率受限的物联网（Internet of Things, IoT）终端发射功率往往只有约 0–14 dBm 量级，扩音器（天线）差一点，整栋楼就听不见；选对频段与安装位置，往往比换更贵的射频芯片更管用[1][6]。

## 摘要

梳理 IoT 常用天线类型、关键参数，对比室外自由空间/双径与室内材料穿透、多径、人体遮挡，并给出频段选型与链路预算部署要点。文中分贝与距离多为工程量级示意，**须以现场实测为准**[3][8][9]。

## 1 天线角色与类型

天线是换能器：发送时把传输线上的高频电流转为空间电磁波，接收时相反；互易性（Reciprocity）使同一天线收发特性对称[1]。

| 类型 | 特点 | 典型场景 |
|------|------|----------|
| PCB 走线（IFA/PIFA 等） | BOM 近零，受地平面/外壳影响大 | 小型低成本终端 |
| 芯片天线 | 极小 SMD，效率常低于 PCB | 可穿戴、微型传感 |
| 线天线（约 λ/4） | 简单、效率好，体积大 | 室外传感器 |
| 外置（胶棒/玻璃钢/定向） | 性能优可更换，成本与馈线损耗上升 | 网关、远距链路 |

尺寸量级示意：2.4 GHz PCB 约十余毫米；868 MHz 四分之一波长约 80–90 mm 量级（常需折叠）[6]。

## 2 关键参数

| 参数 | 含义 | 工程要点 |
|------|------|----------|
| 增益 | 某方向聚焦能力（dBi） | PCB 约 2–3 dBi；外置全向约 5–6 dBi；定向更高——以实测为准 |
| 方向图 | 空间辐射分布 | 全向适合方向不定；定向适合点对点 |
| 极化 | 电场振动方向 | 收发不匹配可带来约数 dB 至十余 dB 附加损耗 |
| 匹配 | 与约 50 Ω 线一致 | 回波损耗常要求优于约 −10 dB（VSWR < 2） |
| 效率 | 输入功率中实际辐射比例 | PCB 常见约 50–80%；芯片天线往往更低 |

自由空间中增益每增约 3 dB，距离约增四成量级——仅作直觉，室内外附加损耗会改写结论[4][9]。

## 3 室外传播

自由空间路径损耗（Free-Space Path Loss, FSPL）：

```
FSPL(dB) ≈ 20·log₁₀(d_km) + 20·log₁₀(f_MHz) + 32.45
```

量级示意：868 MHz、1 km 约 91 dB；2.4 GHz、100 m 约 80 dB。频率翻倍 FSPL 约增 6 dB，故 Sub-GHz 常更远[4]。

实际室外还有地面反射（双径，远距可趋近距离四次方衰减）、绕射与菲涅尔区遮挡、植被吸收（2.4 GHz 穿越茂密树林可额外约十余 dB 量级，Sub-GHz 通常更轻）[8][9]。对 Sub-GHz/2.4 GHz，雨衰通常 <1 dB/km 量级，天气往往不是主因。

## 4 室内传播

室内障碍密、多径强、人员走动使衰减时变，多为非视距（Non-Line-of-Sight, NLOS）。

| 材料 | 868 MHz 损耗量级 | 2.4 GHz 损耗量级 |
|------|------------------|------------------|
| 石膏板墙 | 约 2–4 dB | 约 3–5 dB |
| 砖墙 | 约 5–10 dB | 约 8–15 dB |
| 混凝土/钢筋混凝土 | 约 10–25+ dB | 约 15–35+ dB |
| Low-E 玻璃 | 约 20–30 dB | 约 25–40 dB |
| 金属门/电梯 | 约 30–40+ dB | 往往更高 |

现代节能建筑的 Low-E 玻璃与金属隔热层是常见“意外盲区”[3]。楼板每层约十余至三十 dB 量级，跨 2–3 层后常需每层网关或中继。快衰落：半波长尺度（2.4 GHz 约 6 cm）上强度可起伏数十 dB；人体含水，单人遮挡约数 dB，人群更大[9]。

## 5 频段选型与部署

| 考量 | Sub-GHz（868/915 MHz） | 2.4 GHz |
|------|------------------------|---------|
| 覆盖/穿透 | 通常更好 | 通常更差 |
| 天线尺寸 | 更大 | 更小 |
| 带宽/速率 | 偏窄/偏低 | 更宽/更高 |
| 拥挤度 | 相对空闲 | 常很拥挤 |

覆盖优先 → Sub-GHz；高速率/极小型化 → 2.4 GHz。网关宜高挂、远离大金属面；室外注意菲涅尔区与雷电防护。链路预算：

```
P_rx ≈ P_tx + G_tx − 路径损耗 + G_rx − 裕度
```

部署前用临时网关做接收信号强度指示（Received Signal Strength Indicator, RSSI）/信噪比（Signal-to-Noise Ratio, SNR）热力行走测试，且在有人活动条件下复测[6][10]。

## 6 特殊环境与分集

地埋：土壤损耗可高达约 10–30 dB/m 量级（含水敏感），天线宜出地或地上中继。金属工业环境：贴片隔离、加大间距。水下：2.4 GHz 衰减可约 20 dB/cm 量级，通常改声波/有线。

网关侧空间/极化分集可抗深衰落；多输入多输出（Multiple-Input Multiple-Output, MIMO）在 Wi-Fi 网关常见，窄带 LoRaWAN/NB-IoT 终端侧通常不走多流 MIMO[1][9]。

## 7 局限、挑战与可改进方向

### 1. 模型与现场脱节

**局限**：FSPL/材料表无法覆盖装修变更、Low-E 玻璃与人员密度[3][8]。
**改进**：以链路预算定初值，强制现场热力图与半年复测基线。

### 2. 产品形态去谐

**局限**：实验室裸板调好，装壳/人手后效率与谐振漂移[1][6]。
**改进**：最终外壳与握持姿态下重调；关键产品做空中（Over-The-Air, OTA）抽测。

### 3. 极化与馈线被忽视

**局限**：终端水平、网关垂直可损失十余 dB；长馈线吃掉天线增益[1]。
**改进**：统一极化或网关圆极化；馈线尽量短，损耗预算不超过天线增益一半量级。

### 4. “一个网关打全楼”叙事

**局限**：把单次裕度充足写成永久承诺，忽略装修与干扰变化[10]。
**改进**：按子系统分频段（如跨层低频采集 + 单层高频控制），并预留中继位。

## 参考文献

[1] C. A. Balanis, *Antenna Theory: Analysis and Design*, 4th ed., Wiley.
[2] T. S. Rappaport, *Wireless Communications: Principles and Practice*.
[3] ITU-R P.1238, Propagation data and prediction methods for indoor planning.
[4] ITU-R P.525, Calculation of free-space attenuation.
[5] LoRa Alliance, LoRaWAN Regional Parameters (EU868 等).
[6] Texas Instruments, AN058 Antenna Selection Guide for ISM-Band.
[7] A. F. Molisch, *Wireless Communications*, 2nd ed., Wiley.
[8] ITU-R P.1411, Propagation data for outdoor short-range systems.
[9] A. Goldsmith, *Wireless Communications*, Cambridge University Press.
[10] ITU-R P.1546 / 现场覆盖测量实践文献（工程部署参考）.
[11] 3GPP / CTIA 等关于终端辐射与传播裕度的测试讨论（交叉参考）.
