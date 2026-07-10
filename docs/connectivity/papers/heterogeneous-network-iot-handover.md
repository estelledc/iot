---
schema_version: '1.0'
id: heterogeneous-network-iot-handover
title: 异构网络IoT设备切换与连接选择
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - hybrid-connectivity-multi-protocol
  - cellular-iot-evolution-2g-5g
tags:
- 异构网络
- HetNet
- 垂直切换
- MADM
- TOPSIS
- 网络选择
- ABC
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 异构网络IoT设备切换与连接选择

> **难度**：🔴 高级 | **领域**：网络融合 | **阅读时间**：约 22 分钟

## 日常类比

异构网络（Heterogeneous Network, HetNet）选网像美食广场选餐厅：比价格、等待、口味、是否还吃得下（电池）。正在吃中餐若太慢，可换快餐——对应垂直切换（Vertical Handover）。IoT 设备周围可能同时有蜂窝、Wi-Fi、LoRaWAN 等，要在不断网体验与能耗/成本之间做多属性决策（MADM）。

## 摘要

给出 HetNet 分层与设备能力差异，比较 AHP+TOPSIS、效用函数、模糊逻辑与强化学习选网，并讨论预测切换、乒乓抑制与应用层会话连续。案例中的能耗/成本百分比为实验量级，部署须复测[1][3][4]。

## 1 架构与设备能力

| 层 | 技术例 | 特点 |
|----|--------|------|
| 宏蜂窝 | LTE/5G | 广覆盖、移动性好 |
| 小基站 | Small Cell | 热点扩容 |
| Wi-Fi | 802.11 | 室内高带宽、成本低 |
| LPWAN | LoRaWAN / NB-IoT | 低功耗、低速率 |

数据经网关/核心汇聚到统一 IoT 平台。设备分：单射频（靠网络侧）、多射频（端侧选网）、网关代选。

## 2 MADM：AHP + TOPSIS

属性常含带宽、延迟、抖动、成本、能耗、可靠性、信号质量；量纲不同需归一化。AHP（Analytic Hierarchy Process）成对比较得权重——电池场景能耗权重大，实时控制延迟权重大[1]。

TOPSIS：距正理想解近、距负理想解远者优先。适合网关/边缘有一定算力的节点；MCU 上可预计算或简化。

## 3 效用与上下文权重

综合效用 $U=\sum w_i f_i(\cdot)$。吞吐用饱和函数（超过需求增益递减）；延迟低于阈值高效用、超过后指数下降；能耗反向映射。上下文：电量低抬高能耗权重；紧急告警抬高可靠/延迟权重；静止室内抬高「免费网络」权重[2]。

## 4 模糊逻辑与强化学习

| 方法 | 优点 | 代价 |
|------|------|------|
| 模糊规则 | MCU 友好、语义阈值 | 规则需专家调 |
| Q-Learning | 适应非平稳环境 | 探索期性能差 |
| 多臂赌博机 | 无复杂状态 | 弱上下文建模 |

模糊输入例：RSSI 差/中/好，电量低/中/高，优先级低/中/高。RL 状态含各网信号、电量、队列；动作为选网；奖励综合成功与能耗。探索率需衰减，可迁移同类设备经验[3]。

## 5 垂直切换与 ABC

触发：当前效用过低或出现显著更优候选。预测性切换看 RSSI 趋势、移动、历史拥塞时段，优于「掉线再切」。乒乓抑制：迟滞、最短驻留、降权频繁切换目标、趋势确认。

Always Best Connected（ABC）要求持续扫描、快决策、上下文引擎（位置、速度、室内外、应用 QoS）[2][4]。

## 6 会话连续

IP 变址会断 TCP。网络侧可用 PMIPv6、GTP 等；IoT 更常用应用层：MQTT 持久会话（固定 ClientID）、CoAP Observe 重注册。小包离散遥测通常可容忍短暂中断。

3GPP 亦研究接入流量转向/切换/分流（ATSSS 等）作为 5G 系统能力[4]。

## 7 案例要点（智慧城市传感）

常态 LoRaWAN 低频上报；污染事件切 LTE-M 提频；近 Wi-Fi 时批量卸载缓存。公开 Q-Learning 实验报告相对「始终蜂窝」可显著降能耗与通信成本，到达率略降——数字勿直接当 SLA[3]。

| 策略 | 能耗（相对） | 成本（相对） | 到达率 |
|------|--------------|--------------|--------|
| 始终蜂窝 | 基准 | 基准 | 很高 |
| 智能多网 | 常明显更低 | 常明显更低 | 略降或持平 |

## 8 局限、挑战与可改进方向

### 1. 端侧算力与多射频成本

**局限**：完整 TOPSIS/RL 与多模射频超 MCU/BOM 预算。
**改进**：选网放网关；终端单模 + 策略下发；模糊表固化。

### 2. 探索期与乒乓

**局限**：RL 探索浪费电；阈值不当导致来回切。
**改进**：迟滞+驻留；仿真预热策略再上线。

### 3. 「最佳」目标冲突

**局限**：成本、延迟、能耗不可同时最优。
**改进**：按业务剖面多策略配置文件，运行时切换权重。

### 4. 测量噪声

**局限**：RSSI/负载估计不准导致错选。
**改进**：滑动平均、多指标融合、黑名单劣质 AP。

## 参考文献

[1] E. Stevens-Navarro et al., "MADM methods for vertical handoff decision," IEEE Trans. Wireless Commun. / related works.
[2] R. Trestian et al., "Game Theory-Based Network Selection: Solutions and Challenges," IEEE COMST, 2018.
[3] L. Wang et al., "Reinforcement Learning Based Network Selection for IoT Heterogeneous Networks," IEEE IoT J., 2021.
[4] 3GPP, "TR 23.793: Study on Access Traffic Steering, Switch and Splitting (ATSSS)," 2019.
[5] A. Keshavarz-Haddad et al., "Fuzzy Logic Based Vertical Handover Decision," Wireless Personal Commun., 2020.
[6] J. McNair, F. Zhu, "Vertical handoffs in fourth-generation multinetwork environments," IEEE Wireless Commun., 2004.
[7] S. Fernandes, A. Karmouch, "Vertical Mobility Management Architectures in Wireless Networks," IEEE COMST, 2012.
[8] IETF, "Proxy Mobile IPv6," RFC 5213.
[9] OASIS, "MQTT Version 5.0," 2019.
[10] C. Perkins et al., mobility and multipath related RFCs (context).
[11] IEEE 802.21 Media Independent Handover services (historical reference).
[12] GSMA / multi-access edge connectivity white papers for IoT.
