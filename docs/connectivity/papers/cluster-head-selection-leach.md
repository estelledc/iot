---
schema_version: '1.0'
id: cluster-head-selection-leach
title: 簇头选择LEACH协议与改进算法
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags:
  - LEACH
  - 簇头选择
  - WSN路由
  - HEED
  - DEEC
  - 能量均衡
  - 分层路由
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 簇头选择LEACH协议与改进算法

> **难度**：🔴 高级 | **领域**：无线传感路由 | **阅读时间**：约 22 分钟

## 日常类比

全班每人直接找校长汇报会堵死门口。分成小组、组长汇总后再汇报，校长只接待少数代表——无线传感器网络（Wireless Sensor Network, WSN）分层路由同理：成员短距发给簇头（Cluster Head, CH），CH 聚合后再发往汇聚节点（sink）。

## 摘要

低功耗自适应分簇层次协议（Low-Energy Adaptive Clustering Hierarchy, LEACH）以轮转式随机簇头选举、簇内时分多址（Time Division Multiple Access, TDMA）与数据聚合奠定 WSN 分层路由范式[1][2]。本文说明阈值函数机制，并对比集中式 LEACH-C、稳定选举协议（Stable Election Protocol, SEP）、分布式能量高效聚类（Distributed Energy-Efficient Clustering, DEEC）、混合能量高效分布式聚类（Hybrid Energy-Efficient Distributed clustering, HEED）等改进。仿真寿命数字为示意量级，依赖能量模型与部署假设[1][4]。

## 1. 为何分层

扁平路由中靠近 sink 的转发节点易过早耗尽，导致网络分裂。分层后：簇内短距、聚合降流量、TDMA 允许成员休眠、CH 角色轮转分散负载[1]。

| 指标 | 泛洪 | 直传 sink | LEACH 类分层 |
|------|------|-----------|--------------|
| 簇内/近距能耗 | 高（广播） | 高（远传） | 相对低 |
| 总传输量 | 极高 | 中（无聚合） | 低（可聚合） |
| 协调复杂度 | 低 | 低 | 中 |
| 寿命倾向 | 差 | 中 | 较好（模型相关） |

## 2. LEACH 轮结构与选举

每轮含建立阶段（选举、入簇、TDMA 表）与更长的稳态阶段（按时隙上报、CH 聚合、发往 sink）[1]。

节点 \(n\) 抽随机数，若小于阈值 \(T(n)\) 则当选。对最近 \(1/p\) 轮未当过 CH 的集合 \(G\)：

\[
T(n)=\frac{p}{1-p\cdot(r \bmod (1/p))}
\]

其中 \(p\) 为期望簇头比例（文献常用约 5% 量级），\(r\) 为轮次。直觉：越久未当 CH，概率越高，使节点在约 \(1/p\) 轮周期内轮流承担[1]。

流程：CH 广播通告 → 非 CH 按信号强度入簇 → JOIN → CH 下发 TDMA → 稳态发送。原始 LEACH 中 CH 常单跳直达 sink，远端 CH 发射功率更高[1][2]。

## 3. 机制收益与原始局限

| 机制 | 作用 | 代价 |
|------|------|------|
| CH 轮转 | 均衡高能耗角色 | 每轮建立开销 |
| 数据聚合 | 降长距传输量 | 信息损失（如只报均值） |
| 簇内 TDMA | 减碰撞、成员可休眠 | 需同步与调度 |
| 分布式随机选举 | 无中心、实现简单 | CH 数/位置波动 |

原始局限包括：可能选中低剩余能量或边缘位置节点；CH 数量随机偏离期望；单跳 sink 限制规模；阈值不显式含剩余能量[1][2]。

## 4. 主要改进族

| 协议 | 核心思路 | 信息需求 | 异构适应 |
|------|----------|----------|----------|
| LEACH-C | sink 用位置/能量做近似最优分簇 | 全局上报 | 可排除低能节点[2] |
| SEP | 高级/普通节点不同当选概率 | 知初始能量比 | 两级异构[3] |
| DEEC | 概率 ∝ 剩余能量/平均能量 | 估网络均值 | 多级异构[5] |
| HEED | 主参量剩余能量 + 副参量通信代价，迭代收敛 | 邻域信息 | 较好[4] |
| PEGASIS 等 | 链式近邻聚合，弱化簇形成 | 拓扑构造 | 另类均衡[6] |

**LEACH-C**：基站排除低于平均能量的节点，再用启发式（如模拟退火）选 CH，保证数量与分布，但每轮上报与广播开销大[2]。

**SEP**：高级节点初始能量为 \(E_0(1+\alpha)\)，提高其当选概率，使“能量多者多承担”[3]。

**DEEC**：\(p_i \propto E_{\mathrm{remain}}(i)/E_{\mathrm{avg}}\)，运行中动态拉平[5]。

**HEED**：\(CH_{prob}\) 随剩余能量上升，并以簇内通信代价做副参量；迭代中概率倍增，有限步内确定角色，不依赖全局[4]。

多跳 CH 骨干（或 PEGASIS 链）缓解远端直传，但增加延迟与路由复杂度[6]。

## 5. 案例解读（示意）

农田传感网格上，文献/教材常用仿真对比：随机 LEACH 因簇结构不合理浪费能量；LEACH-C 寿命提升可观但需全局信息；HEED 接近集中式表现且保持分布式——具体“月数”随电池、占空比、无线电模型剧变，只能作相对排序参考，不能当现场承诺[1][4]。

| 协议 | 全局信息 | 复杂度 | 实用倾向 |
|------|----------|--------|----------|
| LEACH | 否 | 低 | 基准/教学 |
| LEACH-C | 是 | 中 | 小网、有可靠回传 |
| HEED | 否（邻域） | 中 | 大规模更常被引用 |

## 6. 局限、挑战与可改进方向

### 1. 理想无线电与同步假设

**局限**：经典模型常忽略占空比 MAC、隐藏终端与时钟漂移，现场寿命远低于仿真。
**改进**：与 IEEE 802.15.4/TSCH 等真实 MAC 联合评估；建立阶段开销计入能量账本。

### 2. 聚合语义与应用不匹配

**局限**：均值/最大等聚合可能丢掉告警尖峰。
**改进**：按应用定义可压缩语义（阈值上报、草图、压缩感知）；紧急量绕过聚合直传。

### 3. CH 单点与安全

**局限**：CH 被俘获或故障影响整簇；轮转增加密钥与信任管理难度。
**改进**：簇内备份 CH、入侵检测与轻量认证；安全开销纳入能耗模型。

### 4. 移动与异构流量

**局限**：LEACH 族多假设静态、均匀周期上报。
**改进**：移动感知重分簇；对突发流量用混合 TDMA/CSMA 或多 CH。

## 参考文献

[1] W. Heinzelman, A. Chandrakasan, and H. Balakrishnan, "Energy-Efficient Communication Protocol for Wireless Microsensor Networks," Proc. HICSS, 2000.
[2] W. Heinzelman, A. Chandrakasan, and H. Balakrishnan, "An Application-Specific Protocol Architecture for Wireless Microsensor Networks," IEEE Trans. Wireless Communications, 2002.
[3] G. Smaragdakis, I. Matta, and A. Bestavros, "SEP: A Stable Election Protocol for Clustered Heterogeneous Wireless Sensor Networks," Proc. SANPA, 2004.
[4] O. Younis and S. Fahmy, "HEED: A Hybrid, Energy-Efficient, Distributed Clustering Approach for Ad Hoc Sensor Networks," IEEE Trans. Mobile Computing, 2004.
[5] L. Qing, Q. Zhu, and M. Wang, "Design of a Distributed Energy-Efficient Clustering Algorithm for Heterogeneous Wireless Sensor Networks," Computer Communications, 2006.
[6] S. Lindsey and C. Raghavendra, "PEGASIS: Power-Efficient Gathering in Sensor Information Systems," IEEE Aerospace Conference, 2002.
[7] A. A. Abbasi and M. Younis, "A survey on clustering algorithms for wireless sensor networks," Computer Communications, 2007.
[8] N. A. Pantazis et al., "Energy-Efficient Routing Protocols in Wireless Sensor Networks: A Survey," IEEE Communications Surveys & Tutorials, 2013.
[9] M. C. M. Thein and T. Thein, "An Energy Efficient Cluster-Head Selection for Wireless Sensor Networks," 相关 LEACH 改进研究.
[10] D. Kumar et al., "EEHC: Energy efficient heterogeneous clustered scheme for wireless sensor networks," Computer Communications, 2009.
[11] I. F. Akyildiz et al., "A survey on sensor networks," IEEE Communications Magazine, 2002.
[12] K. Akkaya and M. Younis, "A survey on routing protocols for wireless sensor networks," Ad Hoc Networks, 2005.
