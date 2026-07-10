---
schema_version: '1.0'
id: wsn-routing-drl
title: AI 驱动的无线传感网路由优化
layer: 3
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# AI 驱动的无线传感网路由优化

> 难度：🟠 进阶 | 预计阅读：35 分钟 | 最后更新：2025-06

## 摘要

无线传感器网络（WSN）中的路由问题本质上是一个"能量管理"问题：如何在有限的电池能量下，让数据从源节点以最高效的方式传递到汇聚节点（Sink），同时最大化整个网络的生存时间。传统路由协议（LEACH、PEGASIS 等）依靠静态规则做出路由决策，难以适应动态变化的网络环境。近年来，深度强化学习（DRL）的引入为 WSN 路由优化提供了全新思路——让每个节点或中心控制器"学会"最优的转发策略。本文系统梳理从经典 WSN 路由到 AI 驱动路由的演进脉络，重点介绍 DQN、PPO 等 DRL 方法在路由优化中的应用，以及 2024-2025 年图神经网络（GNN）增强路由的最新进展。

**关键词**：无线传感器网络；路由优化；深度强化学习；DQN；PPO；多智能体强化学习；图神经网络；网络寿命

## 1 引言：传感器网络为什么这么"在意"能量

想象你在森林里部署了 1000 个传感器来监测火灾。每个传感器靠两节 5 号电池工作，没法充电，换电池也不现实——森林太大了。这些传感器需要每 10 分钟发一次温湿度数据到山脚下的基站。

问题来了：靠近基站的传感器不仅要发自己的数据，还要帮远处的传感器"转发"数据。结果就是离基站越近的传感器消耗能量越快，最先没电。一旦基站周围的传感器全部死掉，远处的传感器即使还有电也无法把数据送出来——整个网络就"断裂"了。

这个问题在 WSN 领域叫做"热区问题"（Hotspot Problem）或"能量空洞"（Energy Hole）。好的路由协议需要尽量均衡所有节点的能量消耗，避免某些节点过早死亡导致网络分裂。

## 2 经典 WSN 路由协议

### 2.1 LEACH — 分簇路由的开山之作

LEACH（Low-Energy Adaptive Clustering Hierarchy，2000 年 Heinzelman 等人提出）是 WSN 路由研究中被引用最多的协议。它的核心思想是"分簇 + 轮换"：

把网络中的节点分成若干个"簇"（Cluster），每个簇选一个"簇头"（Cluster Head, CH）。普通节点只需要把数据发给自己的簇头（短距离通信，省电），簇头负责汇聚数据并发给基站（长距离通信，费电）。关键创新是：簇头不是固定的，而是每轮随机轮换——这样就把"当簇头的能量开销"均摊到所有节点上。

LEACH 的局限性也很明显：簇头选举是随机的，不考虑节点的剩余能量和地理位置。可能出现两个簇头紧挨着，或者所有簇头都在网络一角的情况。LEACH 假设所有节点都能直接与基站通信，这在大规模网络中不现实。

### 2.2 PEGASIS — 链式路由

PEGASIS（Power-Efficient Gathering in Sensor Information Systems，2002 年 Lindsey 等人提出）将所有节点组织成一条"链"。每个节点只需要和链上的前后两个邻居通信，链上的一个节点被选为"链头"负责和基站通信。

PEGASIS 的优势是每个节点只需和最近的邻居通信，极大减少了传输能耗。但构建和维护"链"需要全局拓扑信息，且链头成为瓶颈。

### 2.3 TEEN 和 APTEEN — 事件驱动路由

TEEN（Threshold-sensitive Energy Efficient sensor Network）引入了"硬阈值 + 软阈值"机制：只有当传感器值超过硬阈值、且变化量超过软阈值时才上报数据。这在环境监测等"大部分时间没变化"的场景中极其节能。APTEEN 是 TEEN 的改进版，兼顾周期性和事件驱动两种上报模式。

### 2.4 Directed Diffusion — 以数据为中心

Directed Diffusion（2000 年 Intanagonwiwat 等人提出）开创了"以数据为中心"的路由范式：基站广播"兴趣"（Interest），描述它想要什么数据（如"温度 > 50°C 的读数"）。节点收到兴趣后设置"梯度"（Gradient），数据沿梯度方向向基站流动。基站可以"强化"数据质量高的路径，形成稳定的数据传输通道。

### 2.5 经典协议对比

| 协议 | 拓扑结构 | 数据传输模式 | 是否需要全局信息 | 网络寿命(相对LEACH) | 适用场景 |
|------|----------|-------------|-----------------|-------------------|----------|
| LEACH | 分簇(随机选CH) | CH→BS(单跳) | 否 | 1.0× | 小规模均匀分布 |
| LEACH-C | 分簇(BS选CH) | CH→BS(单跳) | 是(位置+能量) | 1.2-1.5× | 有BS全局可达 |
| PEGASIS | 链式 | 链头→BS | 是(邻居距离) | 1.5-2.0× | 线性/规则分布 |
| TEEN | 分簇+阈值 | 事件驱动 | 否 | 2-3×(低事件率) | 突发事件监测 |
| Directed Diffusion | 无固定结构(梯度) | 以数据为中心 | 否 | 1.3-1.8× | 查询驱动应用 |
| HEED | 分簇(剩余能量权重) | 多跳CH→BS | 否 | 1.5-2.0× | 大规模异构网络 |

## 3 深度强化学习驱动的路由优化

### 3.1 为什么 DRL 适合 WSN 路由

WSN 路由决策天然适合被建模为马尔可夫决策过程（MDP）：

**状态（State）**：节点的剩余能量、缓冲区占用、邻居节点信息、到基站的距离估计、信道质量指标等。

**动作（Action）**：选择下一跳转发节点（从邻居节点集合中选择一个）。

**奖励（Reward）**：综合考虑多个目标——成功投递加正奖励、能量消耗扣负奖励、选择低能量节点作为下一跳额外扣分、网络不均衡度作为惩罚项。

传统优化方法（整数线性规划、凸优化）在网络规模大、环境动态变化时计算量爆炸。DRL 的优势是一旦训练好策略网络，推理阶段只需要一次前向传播（毫秒级），可以实时做出路由决策。

### 3.2 DQN-based 路由

深度 Q 网络（DQN）是最早被应用于 WSN 路由的 DRL 方法。2019 年 Liu 等人首次提出 Q-learning 增强的 LEACH 协议（QL-LEACH），随后多个研究团队将其升级为 DQN 版本。

核心思路：每个节点维护一个 Q 网络（或共享一个全局 Q 网络），输入是当前状态向量（自身能量、邻居信息等），输出是对每个候选下一跳的 Q 值估计。节点选择 Q 值最高的邻居作为下一跳。

2023 年 IEEE IoT Journal 上 Zhang 等人的研究（DRLR-WSN）在 200 节点网络中的实验结果表明：DQN 路由相比 LEACH 延长网络寿命 **42%**，相比 HEED 延长 **23%**。首个节点死亡（FND）时间从 LEACH 的约 1200 轮提升到约 1700 轮。

### 3.3 PPO-based 路由

近端策略优化（PPO）是目前 DRL 领域最稳定的策略梯度方法，也被广泛应用于 WSN 路由。与 DQN 不同，PPO 直接输出动作概率分布，天然支持连续动作空间（如同时决定传输功率和下一跳）。

2024 年 Chen 等人在 IEEE Transactions on Mobile Computing 上发表的 PPO-Routing 研究表明：PPO 在非均匀节点分布场景中的表现显著优于 DQN——因为 PPO 的策略梯度方法更擅长处理高维、连续的动作空间。在 500 节点的网络中，PPO-Routing 相比 DQN-Routing 进一步延长了 **12-18%** 的网络寿命，且收敛速度更快（训练 episode 减少 30%）。

### 3.4 多智能体强化学习（MARL）

在大规模 WSN 中，集中式 DRL（一个全局控制器为所有节点做决策）面临状态空间爆炸和通信开销问题。多智能体强化学习（MARL）让每个节点（或每个簇头）作为独立的智能体，用局部观测做出分布式决策。

主要方法包括：

**独立学习（Independent Learners）**：每个智能体独立训练自己的策略，不考虑其他智能体的策略变化。简单但可能导致策略振荡。

**CTDE（集中训练分布式执行）**：训练时用全局信息（所有智能体的状态和动作），执行时每个智能体只用自己的局部观测。QMIX、MAPPO 等算法属于此类。

**通信学习（Communication Learning）**：智能体之间可以交换"消息"，通过学习决定发什么消息、听谁的消息。CommNet、TarMAC 等架构被应用于此。

2024 年 Sharma 等人在 Ad Hoc Networks 上发表的 MARL-WSN 使用 QMIX 算法，在 1000 节点的大规模网络中实现了接近集中式 DRL 的性能（网络寿命差距 <5%），同时通信开销降低了 **80%**——每个节点只需要和一跳邻居交换约 50 字节的策略信息。

## 4 图神经网络增强路由：2024-2025 前沿

传统 DRL 方法将网络状态"拍平"成一个向量输入策略网络，丢失了网络的拓扑结构信息。而 WSN 本身就是一个图结构——节点是顶点，通信链路是边。图神经网络（GNN）可以直接在图结构上学习，天然适合编码网络拓扑。

### 4.1 GNN + DRL 的融合架构

2024-2025 年出现的主流融合架构是"GNN 编码器 + DRL 决策器"：

**GNN 编码器**：将网络拓扑和节点特征（能量、负载、位置等）通过 Graph Attention Network（GAT）或 GraphSAGE 编码为节点嵌入向量。GNN 的消息传递机制天然模拟了 WSN 中信息沿跳扩散的过程。

**DRL 决策器**：将 GNN 输出的节点嵌入作为状态输入策略网络（PPO/SAC），输出路由决策。这种架构的优势是策略网络可以"看到"整个网络的拓扑特征，而不仅仅是当前节点的局部信息。

2025 年 Li 等人在 IEEE/ACM Transactions on Networking 上发表的 GNN-Route 是该方向的代表工作。在 500 节点网络的仿真实验中：

| 指标 | LEACH | DQN-Route | PPO-Route | GNN-Route (GAT+PPO) |
|------|-------|-----------|-----------|---------------------|
| 首个节点死亡(轮) | 1198 | 1706 | 1912 | 2247 |
| 半数节点死亡(轮) | 1543 | 2103 | 2389 | 2756 |
| 全网死亡(轮) | 1892 | 2487 | 2801 | 3198 |
| 网络寿命提升(vs LEACH) | 基准 | +42% | +60% | +88% |
| 投递率 | 91.3% | 96.8% | 97.5% | 98.9% |
| 训练收敛(episode) | — | ~5000 | ~3500 | ~2000 |

### 4.2 泛化能力

GNN 增强路由的另一个重要优势是**泛化能力**：在小规模网络上训练的 GNN 策略可以直接迁移到大规模网络上使用，因为 GNN 的消息传递是局部的、参数共享的，不依赖固定的网络规模。2024 年的实验表明，在 100 节点网络上训练的 GNN-Route 策略直接迁移到 500 节点网络后，性能仅下降 **8-12%**，而传统 DRL 方法（固定维度输入）根本无法迁移。

### 4.3 联合优化：路由 + 占空比 + 功率控制

最新的研究不再孤立地优化路由，而是将路由选择与 MAC 层占空比调度（Duty Cycling）和物理层传输功率控制联合优化。2025 年 Wang 等人提出的 Joint-GRL（Graph Reinforcement Learning）框架同时优化三个决策维度，在仿真中实现了比单独优化路由额外 **15-20%** 的网络寿命提升。

## 5 能量效率指标与评估方法

评估 WSN 路由协议的性能不能只看"好不好"，需要统一的量化指标：

**网络寿命**：最常用但定义不统一。常见的三种定义是首个节点死亡（FND）、半数节点死亡（HND）和最后节点死亡（LND）。不同定义下协议的排名可能不同——LEACH 的 FND 很早，但 LND 不算太差，因为随机轮换最终会让所有节点的能量趋于均匀。研究论文应明确使用哪种定义。

**能量效率**：每成功投递一个数据包消耗的总能量（J/packet）。包括发送能耗、接收能耗、空闲监听能耗和数据处理能耗。

**负载均衡度**：所有节点剩余能量的标准差与均值之比（变异系数）。值越小表示能量消耗越均匀。

**数据投递率（PDR）**：成功到达基站的数据包占总发送数据包的比例。

**端到端延迟**：数据从源节点到基站的平均传输时间。多跳路由延迟 = 跳数 × 每跳延迟 + 排队延迟。

**仿真工具**：NS-3 是 WSN 路由仿真的事实标准，提供了 LEACH、RPL 等协议的参考实现。MATLAB/Simulink 常用于快速原型验证。针对 DRL 路由研究，OpenAI Gym + NS-3 的集成环境（ns3-gym）允许用 Python 编写 DRL 算法、用 NS-3 做网络仿真。

## 6 挑战与开放问题

**Sim-to-Real 差距**：几乎所有 DRL 路由研究都在仿真中验证，实际部署面临无线信道的不可预测性、硬件差异和计算资源限制。策略网络的推理需要一定的计算资源（几 KB 的模型参数 + 矩阵乘法），对于 Class 0/1 受限设备可能过重。

**训练成本**：DRL 训练需要大量的探索，在实际网络中做探索意味着真实的能量消耗。离线训练 + 在线微调（Offline RL + Fine-tuning）是一个有前景的方向。

**安全性**：DRL 策略网络容易受到对抗性攻击——恶意节点可以通过报告虚假状态来操纵路由决策。如何设计鲁棒的 DRL 路由策略是开放问题。

**标准化**：目前 DRL 路由停留在学术研究阶段，没有标准化协议。与 IETF RPL 等标准协议的集成路径尚不清晰。

## 7 总结

WSN 路由优化经历了从静态规则（LEACH/PEGASIS）→ 自适应启发式（HEED/TEEN）→ 单智能体 DRL（DQN/PPO）→ 多智能体 DRL（QMIX/MAPPO）→ GNN 增强 DRL 的演进。每一代方法都在"利用更多信息、做出更好决策"这条主线上推进。

GNN + DRL 的融合是当前最有前景的方向，因为它同时解决了两个核心问题：GNN 捕获了网络拓扑结构，DRL 处理了动态决策优化。2024-2025 年的研究表明，GNN-Route 可以将网络寿命相比经典 LEACH 协议提升约 **88%**，相比纯 DRL 方法（不含 GNN）也有 **15-28%** 的额外提升。

未来的关键挑战是缩小 Sim-to-Real 差距——让 DRL 路由从论文走向部署。轻量化模型（TinyML 级别的策略网络）、迁移学习（小网络训练，大网络部署）和鲁棒性增强将是突破口。

## 参考文献

1. Heinzelman, W., et al. "Energy-efficient communication protocol for wireless microsensor networks." HICSS, 2000.
2. Lindsey, S., Raghavendra, C. "PEGASIS: Power-efficient gathering in sensor information systems." IEEE Aerospace Conference, 2002.
3. Intanagonwiwat, C., et al. "Directed diffusion: A scalable and robust communication paradigm for sensor networks." ACM MobiCom, 2000.
4. Zhang, Y., et al. "Deep Reinforcement Learning-Based Routing for Energy-Efficient Wireless Sensor Networks." IEEE Internet of Things Journal, 2023.
5. Chen, X., et al. "PPO-Based Adaptive Routing for Heterogeneous Wireless Sensor Networks." IEEE Transactions on Mobile Computing, 2024.
6. Sharma, R., et al. "Multi-Agent Reinforcement Learning for Distributed Routing in Large-Scale WSNs." Ad Hoc Networks, 2024.
7. Li, W., et al. "GNN-Route: Graph Neural Network Enhanced Deep Reinforcement Learning for WSN Routing Optimization." IEEE/ACM Transactions on Networking, 2025.
8. Wang, H., et al. "Joint Routing, Duty Cycling and Power Control via Graph Reinforcement Learning." IEEE INFOCOM, 2025.
9. Younis, O., Fahmy, S. "HEED: A Hybrid, Energy-Efficient, Distributed Clustering Approach for Ad-Hoc Sensor Networks." IEEE Transactions on Mobile Computing, 2004.
10. Manjeshwar, A., Agrawal, D. "TEEN: A Routing Protocol for Enhanced Efficiency in Wireless Sensor Networks." IPDPS, 2001.
11. Guo, Z., et al. "ns3-gym: Extending OpenAI Gym for Networking Research." ACM WiNTECH, 2019.
