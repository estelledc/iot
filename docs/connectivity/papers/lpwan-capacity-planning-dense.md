---
schema_version: '1.0'
id: lpwan-capacity-planning-dense
title: LPWAN密集部署容量规划与干扰分析
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - lpwan-comparison
  - low-power-wide-area-network-survey
  - lpwan-mac-layer-comparison
tags:
  - LPWAN
  - 容量规划
  - ALOHA
  - ADR
  - 占空比
  - NB-IoT
  - 网关密度
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# LPWAN密集部署容量规划与干扰分析

> **难度**：🔴 高级 | **领域**：网络规划 | **阅读时间**：约 22 分钟

## 日常类比

广场上万人同时喊话：人人抢麦（Pure ALOHA）会互相淹没；有人按号筒排期（蜂窝调度）效率高但要协调成本。智慧城市若同时挂数万～数十万终端，不懂容量极限，系统会在“部署到一半”时堵死。低功耗广域网（LPWAN）容量是频谱、空口时间、接入机制与干扰的函数[1][2]。

## 摘要

以 LoRaWAN 碰撞与扩频因子（Spreading Factor, SF）、占空比、自适应数据速率（Adaptive Data Rate, ADR）、网关密度为主线，对照 Sigfox 超窄带冗余与 NB-IoT 调度容量，给出密集部署估算与混合组网思路。文中设备数、包/小时为**模型示意**，须用本地区信道数与实测 PDR 校准[1][4]。

## 1. 容量定义

在可接受服务质量（Quality of Service, QoS）下可服务的最大终端数。LPWAN 常见代理指标：分组到达率（Packet Delivery Ratio, PDR）阈值、可容忍时延、连续失败次数。影响因素：可用信道、每包空中时间（Time on Air, ToA）、占空比、随机接入 vs 调度、同/异网干扰[2]。

## 2. LoRaWAN：ALOHA 与 SF

Pure ALOHA 归一化吞吐 \(S=G e^{-2G}\)，峰值约 \(1/(2e)\approx 18.4\%\)（\(G=0.5\)）——即使最优负载，大量空口仍耗在碰撞上[1]。不同 SF 近似正交，但 SF12 的 ToA 可比 SF7 高一个数量级，**容量不是“6 个 SF 简单乘 6”**。

| 策略 | 相对容量倾向 |
|------|----------------|
| SF 均匀 | 基准偏低 |
| 按距离/链路自适应 | 常明显提升 |
| ADR 良好收敛 | 文献与部署常报数倍量级增益 |

粗算示意：\(N \propto (T_{period}\cdot DC)/(ToA\cdot(1+retry))\)。城市单网关在“每小时 1 包、PDR 达标”叙事下，稳定支撑常落到**千级而非纸面万级**，视信道数与干扰而定[2][4]。

## 3. 占空比约束

| 区域监管倾向 | 对容量含义 |
|--------------|------------|
| 欧洲 ETSI 子带 0.1%/1%/10% 等 | 高 SF 每小时可发包数骤降 |
| 美国 FCC 等更宽 ISM、功率规则不同 | 同技术容量常显著高于严占空比区 |

SF12 在 1% 占空比下每小时可发次数可落到数十量级；把边缘终端压到低 SF，对整网容量帮助最大[6]。

## 4. Sigfox 与 NB-IoT 对照

| 技术 | 容量逻辑 | 规划注意 |
|------|----------|----------|
| Sigfox UNB | 频域并行度高；消息 3 次分集 | 日消息上限；基站负载与 PDR 曲线 |
| NB-IoT | 调度为主，数据段少碰撞 | 重复次数随覆盖变差吞噬 RU；覆盖常先于容量决定站址 |

NB-IoT 在良好覆盖下单小区可服务设备数常远高于免许可 ALOHA 网；极端 MCL 下重复传输使容量掉档。授权频段异网同技术干扰相对可控，是相对 LoRa 共存的核心优势之一[3][5]。

## 5. 干扰与缓解

同城多 LoRaWAN 运营、LoRa↔Sigfox 同频段都会抬升碰撞/干扰。缓解：频率规划、LBT（Listen Before Talk）、时间同步、增加网关密度分散负载。异网流量进入碰撞公式后，PDR 随对方设备数近似指数变差，需联合规划而非“各算各的”[1][8]。

| 策略 | 效果倾向 | 代价 |
|------|----------|------|
| 频率分区 | 高 | 需协调 |
| LBT | 中高 | 时延/功耗；隐藏节点 |
| 多网关 | 高 | 基建与回传 |
| ADR/降功率 | 中高 | 依赖上行统计质量 |

## 6. ADR 与网关密集化

ADR 用近期 SNR 把终端推到“刚够用”的最低 SF/功率，缩短平均 ToA。多网关不仅线性加容量，还通过缩短跳距降低 SF、空间分集收同一包，使增益常**高于网关个数比**[2][7]。选址可用贪心、聚类或 ILP，约束覆盖、每关负载与 PDR 目标。

## 7. 智慧城市量级案例（示意）

假设十余万终端、日消息百万级、高峰系数 >1：LoRaWAN 可能需要数十～百余量级网关（视信道与 ADR）；NB-IoT 往往容量不是瓶颈，**站址由覆盖与室内穿透决定**。混合：固定低频表计走蜂窝；园区中频传感走 LoRa；移动资产走 LTE-M/NB-IoT——按流量剖面拆分[5]。

## 8. 局限、挑战与可改进方向

### 1. 解析模型过于乐观

**局限**：忽略确认下行、近远效应、异网后，纸面 N_max 虚高[1][2]。
**改进**：模型 → 仿真（NS-3/LoRaSim 等）→ Pilot 三段式校准。

### 2. ADR 在移动/突发场景失效

**局限**：统计窗口与静止假设不成立时，SF 分配失真。
**改进**：移动终端固定保守 SF；突发告警走确认或异技术。

### 3. 监管与地图差异

**局限**：把美规容量套到欧规占空比区会严重误判[6]。
**改进**：容量表按区域参数分册；工具链写入子带 DC。

### 4. 单技术一把梭

**局限**：停车地磁与车载追踪同网，MAC 与覆盖需求冲突。
**改进**：按业务切片到 LoRa / NB-IoT / LTE-M 混合。

## 9. 实践要点

1. 先固定：包长、周期、确认比、目标 PDR、区域频段表。
2. 用 ToA×ALOHA 上界做网关下界，再加 安全余量与异网。
3. 验收看高峰小时 PDR 与 SF 分布，不看空载演示。

## 参考文献

[1] O. Georgiou, U. Raza, "Low Power Wide Area Network Analysis: Can LoRa Scale?" IEEE Wireless Commun. Lett., 2017.
[2] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Commun. Mag., 2017.
[3] 3GPP TR 45.820, CIoT support, 2015.
[4] K. Mikhaylov et al., "Analysis of Capacity and Scalability of LoRa," European Wireless, 2016.
[5] GSMA, Mobile IoT deployment and capacity guidance materials.
[6] ETSI EN 300 220, duty cycle and power limits for SRD.
[7] J. Haxhibeqiri et al., "A Survey of LoRaWAN for IoT," Sensors, 2018.
[8] K. Mikhaylov et al., inter-network interference evaluations for LoRaWAN.
[9] Semtech, LoRaWAN ADR and capacity application notes.
[10] LoRaSim / NS-3 LoRaWAN community models (tooling references).
[11] Sigfox/UnaBiz technical notes on UNB capacity and triple transmission.
[12] Vendor/operator NB-IoT cell capacity white papers (treat as case-specific).
