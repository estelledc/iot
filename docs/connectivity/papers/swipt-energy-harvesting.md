---
schema_version: '1.0'
id: swipt-energy-harvesting
title: 射频能量收集与通信一体化 SWIPT
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - noma-iot-access
tags:
  - SWIPT
  - 能量收集
  - WPT
  - 整流
  - Rate-Energy
  - Powercast
  - 无电池
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 射频能量收集与通信一体化 SWIPT

> **难度**：🟡 中级 | **领域**：无线通信、能量收集 | **阅读时间**：约 18 分钟

## 日常类比

无线充电板给手机送电；若同一束电磁波既传“充电进度”又送电，就是同时无线信息与功率传输（Simultaneous Wireless Information and Power Transfer, SWIPT）的直觉。也可想成：阳光既让日晷读出时间（信息），又让光伏板发电（能量）——同一射频（Radio Frequency, RF）到达后，一部分解调，一部分整流为直流[1][2]。

对物联网（IoT）的吸引力在于：植入物、结构内传感器等难换电池场景，希望基站查询时顺带“充电”。工程上多数商用模块仍是纯无线功率传输（Wireless Power Transfer, WPT），完整 SWIPT 产品化仍受限[7][9]。

## 摘要

梳理信息–能量折衷、时间切换/功率分割接收机、非线性整流模型、中继与非正交多址（Non-Orthogonal Multiple Access, NOMA）结合，并以 Powercast 类硬件说明距离天花板。效率与 μW 级功率为数据手册/论文量级，**随频率、波形、匹配与输入功率剧烈变化**[3][8]。

## 1. 信息与能量的矛盾

信息接收关心波形细节；能量收集关心总功率。功率受限信道上，速率 R 与可收集能量 Q 存在帕累托折衷（Rate-Energy 区域）[1][3]。

| 接收机架构 | 思路 | 优点 | 代价 |
|------------|------|------|------|
| 理想接收机 | 同信号同时解码+整流 | 理论最优 | 物理上不可行 |
| 时间切换（Time Switching, TS） | 时段 α 收能、(1−α) 收信 | 硬件简单 | 时间互斥 |
| 功率分割（Power Splitting, PS） | 功率比 ρ/(1−ρ) 分两路 | 可连续工作 | 需功分器与额外噪声 |
| 天线切换（Antenna Switching, AS） | 部分天线收信/收能 | 适合多天线 | 孔径利用率低 |

## 2. 帧结构与波形

TS 帧常见：能量段发连续波（Continuous Wave, CW）或多音（multi-tone）高峰值平均功率比（Peak-to-Average Power Ratio, PAPR）信号，信息段再传前导与数据。文献表明高 PAPR 波形可利用二极管非线性提升整流效率，相对 CW 的增益**随整流器与功率区而变**，不宜写成固定“高 20–40%”[6][8]。

| 场景（示意） | 策略倾向 | α 或 ρ |
|--------------|----------|--------|
| 电量低 + 信道好 | 优先充电 | α 高 / ρ 低 |
| 电量高 + 紧急数据 | 优先传信 | α 低 / ρ 高 |
| 信道差 | 积能等待 | 中等 α |
| 无数据 | 纯 WPT | α→1 |

## 3. 非线性整流：线性模型会骗人

早期常设 RF–DC 效率为常数；实际整流器强非线性，低输入功率时效率骤降[8]：

| 输入功率（量级） | 线性模型假设 | 实际效率量级 |
|------------------|--------------|--------------|
| −30 dBm | 如 40% | 常仅百分之几 |
| −20 dBm | 如 40% | 约十余% |
| −10–0 dBm | 如 40% | 可接近峰值 |
| 过高 | 常数 | 饱和/下降 |

IoT 远场接收常落在 −30 至 −10 dBm——正是非线性最显著区。基于线性模型的“最优 ρ/α”现场常失效[8][9]。

## 4. 距离天花板与中继

自由空间功率随距离平方衰减。以 GHz 级、瓦级发射的示意链路：

| 距离量级 | 接收功率量级 | 可收集直流（η 示意） | 含义 |
|----------|--------------|----------------------|------|
| ~1 m | 约 −10 dBm 级 | 数十 μW 级 | 低占空比传感可能 |
| ~10 m | 约 −30 dBm 级 | 亚 μW 级 | 多需蓄能突发 |
| ≥100 m | 更低 | nW–pW 级 | 远场 SWIPT 基本不可行 |

中继可自收能再转发，但发射能量受收集能量约束，α/(1−ρ) 与转发功率形成闭环折衷[4]。NOMA-SWIPT 常让近用户做 PS 收能、远用户专注信息，需谨慎处理串行干扰消除（Successive Interference Cancellation, SIC）失败[5]。

## 5. 硬件参照：Powercast 类 WPT

P2110 等模块工作在 915 MHz 等 ISM，数据手册给出输入范围与效率曲线（如 0 dBm 附近效率较高，冷启动门限约 −5 dBm 量级）[7]。配套数瓦有效全向辐射功率（Equivalent Isotropically Radiated Power, EIRP）发射器时，可用距离多为米级；**具体以实测与法规 EIRP/SAR 为准**。注意：此类产品多为纯 WPT，通信另走 BLE/LoRa 等，并非完整 SWIPT[7][9]。

## 6. 局限、挑战与可改进方向

### 1. 远场能量密度不够

**局限**：十米外 μW 级难支撑持续传感+发射。
**改进**：缩短距离、定向波束、超级电容蓄能突发；或改近场/电感方案[7][10]。

### 2. 线性模型误导调度

**局限**：低功率区效率被高估，节点“假活”。
**改进**：标定非线性曲线；按输入功率分段优化 ρ/α[8]。

### 3. SWIPT 与 WPT 概念混用

**局限**：采购“能量收集芯片”却期望同信号解调。
**改进**：规格书区分信息支路；原型分别测 BER 与 DC 输出[3][9]。

### 4. 法规与人体安全

**局限**：抬高 EIRP 受 FCC/ETSI 与比吸收率（Specific Absorption Rate, SAR）约束。
**改进**：合规链路预算；波束对准减少无效辐射[7][10]。

## 7. 实践要点

1. 先仿真/测量整流效率–功率曲线，再谈协议。
2. 多级 Dickson 提高灵敏度，但峰值效率常下降——按工作点选型。
3. 能量段优先考虑高 PAPR 波形；信息段单独优化调制[6]。
4. 与 NOMA/中继结合前，先确认单链路能量是否过冷启动门限[4][5]。

## 参考文献

[1] R. Zhang and C. K. Ho, MIMO broadcasting for SWIPT, IEEE TWC, 2013.
[2] L. R. Varshney, Transporting information and energy simultaneously, ISIT, 2008.
[3] X. Zhou et al., Architecture design and rate-energy tradeoff, IEEE TCOM, 2013.
[4] A. A. Nasir et al., Relaying protocols for wireless energy harvesting, IEEE TWC, 2013.
[5] Y. Liu et al., Cooperative SWIPT NOMA, IEEE TCOM, 2017.
[6] B. Clerckx and E. Bayguzina, Waveform design for WPT, IEEE TSP, 2016.
[7] Powercast, P2110-915 Powerharvester datasheet.
[8] E. Boshkovska et al., Practical non-linear energy harvesting model, IEEE CL, 2015.
[9] I. Krikidis et al., SWIPT in modern communication systems, IEEE Comm. Mag., 2014.
[10] D. W. K. Ng et al., Multi-antenna techniques for WIPT, IEEE Comm. Mag., 2014.
[11] FCC / ETSI ISM EIRP and RF exposure guidance relevant to WPT deployments.
