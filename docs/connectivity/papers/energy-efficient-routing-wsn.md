---
schema_version: '1.0'
id: energy-efficient-routing-wsn
title: 无线传感器网络能量高效路由协议
layer: 2
content_type: survey
difficulty: advanced
reading_time: 22
prerequisites:
  - data-aggregation-wsn-energy
  - geographic-routing-gpsr-iot
  - mesh-network-self-healing-routing
tags:
  - WSN
  - LEACH
  - GPSR
  - 能量路由
  - 网络生命周期
  - 数据聚合
  - 多路径
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 无线传感器网络能量高效路由协议

> **难度**：🔴 高级 | **领域**：路由协议、无线传感器网络 | **阅读时间**：约 22 分钟

## 日常类比

快递网里每个快递员油量有限：全走最短路，干线上的人先没油，整网断裂。无线传感器网络（Wireless Sensor Network, WSN）同理——路由决定谁先耗尽电池。目标往往不是“每包最省电”，而是**均衡消耗、拉长网络生命周期**；文中寿命倍数与能耗比例多为仿真/案例量级，**换拓扑与占空比后须重测**[1][5]。

## 摘要

对比扁平与分层路由、最小能量与最大生命周期目标，梳理 SPIN、Directed Diffusion、地理路由（如 GPSR）、多路径与聚合感知策略，并说明能量收集场景下的动态调整。生命周期定义不同，最优策略也不同[5]。

## 1 能量约束与生命周期

典型电池节点中，射频收发常占能耗大头；“发 1 bit ≈ 大量本地运算”的数量级对比在经典文献中常见，用以强调**少传、短距、可聚合**优先于炫技算法[1]。

| 生命周期定义 | 含义 | 路由倾向 |
|--------------|------|----------|
| 首节点死亡 | 最严格 | 强均衡，保护每一节点 |
| 比例节点死亡 | 如半数失效 | 允许边缘牺牲 |
| 连通分裂 | sink 不可达 | 保护关键割点/近 sink 带 |
| 覆盖下降 | 感知质量不达标 | 保护覆盖关键区 |

不均衡最短路会使近汇聚点（sink）成为热点，远端能量浪费而网络已断。

## 2 扁平 vs 分层

| 特征 | 扁平路由 | 分层（分簇）路由 |
|------|----------|------------------|
| 结构 | 节点对等 | 簇头聚合/转发 |
| 可扩展 | 表项易膨胀 | 局部管理更好 |
| 聚合 | 不天然 | 簇头天然聚合 |
| 复杂度 | 相对低 | 簇维护开销 |
| 健壮性 | 无固定单点 | 簇头是关键 |
| 代表 | SPIN、Directed Diffusion | LEACH、HEED、PEGASIS 等 |

大规模可聚合传感数据时，分层常更省空口；小规模同构网扁平更简单[1][2]。

## 3 最小能量 vs 最大生命周期

| 目标 | 优化对象 | 典型后果 |
|------|----------|----------|
| 最小能量 | 单包路径能耗之和最小 | 最优路上节点反复使用，早死 |
| 最大生命周期 | 最大化“最先耗尽节点”的预期寿命 | 单包可能更耗，总采集量常更高 |

流量应倾向剩余能量高、避免固定热路径；多路径按能量/链路质量加权分配[5]。

## 4 经典协议机制

### 4.1 SPIN

协商式：ADV（元数据）→ REQ → DATA，避免盲目泛洪；低电量可拒转[3]。

### 4.2 Directed Diffusion

以数据为中心：sink 扩散 interest → 建梯度 → 数据回流 → 强化优质路径；中间可聚合，只传感兴趣数据[2]。

### 4.3 地理路由（GPSR 等）

每跳选地理上更近目的地的邻居，无需全局路由表；遇空洞则周边模式绕行[4]。需位置信息（GPS/定位），定位误差会伤路径质量。

### 4.4 多路径与聚合

| 策略 | 作用 | 代价 |
|------|------|------|
| 多路径分流 | 均衡与容错 | 发现/维护开销，需拓扑冗余 |
| 聚合感知树 | 早汇合少发包 | 应用须容忍聚合语义（均值/最大等） |

无聚合时 \(N\) 源≈\(N\) 次转发；可压缩聚合时中间转发可显著下降——**具体百分比依赖相关度与聚合函数**，不可写死为固定节能率。

## 5 能量收集场景

能量可补充时，目标常转为在收集速率约束下最大化长期吞吐：优先用正在充电、避免“电池已满却仍低负载”造成的收集溢出；昼夜太阳能等使最优下一跳随时间变，协议需周期性重评分。

## 6 案例量级（示意）

森林监测类部署中，仿真/试验常报告：纯最短路使近 sink 先死、远端能量剩余；能量感知地理转发可使寿命与总数据量明显提升。下表为**示意对比**，非通用 SLA[5]：

| 指标 | 最小能量倾向 | 最大生命周期倾向 |
|------|--------------|------------------|
| 近 sink 命运 | 易早死 | 负载被摊开 |
| 死亡模式 | 热点先黑 | 更接近同时耗尽 |
| 远端能量 | 易浪费 | 利用率更高 |

评分示例：`score = w1/dist_to_sink + w2·E_remain/E_max`，权重须现场标定。

## 7 局限、挑战与可改进方向

### 1. 生命周期指标被误用

**局限**：论文报“寿命提升 × 倍”却未声明用的是首死还是连通定义，无法横向比[5]。
**改进**：报告中固定指标、给出死亡曲线与剩余能量分布，而非单一标量。

### 2. 理想链路与同步假设

**局限**：许多协议假设对称链路、可靠广播、精确位置，真实 WSN 丢包与占空比 MAC 会放大控制开销。
**改进**：与 B-MAC/TSCH 等占空比栈联调；用 ETX/RSSI 替代理想距离。

### 3. 簇头与热点仍在

**局限**：LEACH 类随机轮换减轻但不消除近 sink 与簇头负担[1]。
**改进**：多 sink、移动 sink、非均匀分簇、或有线/能量收集补给热点带。

### 4. 聚合损害可追溯性

**局限**：过度聚合丢失单点异常，安全与审计困难。
**改进**：异常走不聚合快路径；聚合带摘要/计数；关键告警端到端保留。

## 8 总结

能量高效 WSN 路由的核心是**均衡与少传**（聚合、短距、多路径），不是盲目最短路。按生命周期定义选型：小网协商/扩散，大网分簇+聚合，有位置则地理转发，有收集则动态重路由——并用与现场一致的死亡/覆盖指标验收。

## 参考文献

[1] W. Heinzelman, A. Chandrakasan, and H. Balakrishnan, "Energy-Efficient Communication Protocol for Wireless Microsensor Networks," Proc. HICSS, 2000.
[2] C. Intanagonwiwat, R. Govindan, and D. Estrin, "Directed Diffusion: A Scalable and Robust Communication Paradigm for Sensor Networks," ACM MobiCom, 2000.
[3] J. Kulik, W. Heinzelman, and H. Balakrishnan, "Negotiation-Based Protocols for Disseminating Information in Wireless Sensor Networks," Wireless Networks, 2002.
[4] B. Karp and H. T. Kung, "GPSR: Greedy Perimeter Stateless Routing for Wireless Networks," ACM MobiCom, 2000.
[5] J. Chang and L. Tassiulas, "Maximum Lifetime Routing in Wireless Sensor Networks," IEEE/ACM Trans. Networking, 2004.
[6] O. Younis and S. Fahmy, "HEED: A Hybrid, Energy-Efficient, Distributed Clustering Approach," IEEE Trans. Mobile Computing, 2004.
[7] S. Lindsey and C. Raghavendra, "PEGASIS: Power-Efficient Gathering in Sensor Information Systems," IEEE Aerospace, 2002.
[8] I. F. Akyildiz et al., "Wireless sensor networks: a survey," Computer Networks, 2002.
[9] K. Akkaya and M. Younis, "A survey on routing protocols for wireless sensor networks," Ad Hoc Networks, 2005.
[10] T. Voigt et al., "Solar-aware clustering in wireless sensor networks," IEEE ISCC (及能量收集路由后续工作).
[11] D. Ganesan et al., "Highly-resilient, energy-efficient multipath routing in wireless sensor networks," ACM Mobile Computing and Communications Review, 2001.
[12] A. Manjeshwar and D. P. Agrawal, "TEEN: A Routing Protocol for Enhanced Efficiency in Wireless Sensor Networks," IPDPS Workshops, 2001.
