---
schema_version: '1.0'
id: wsn-routing-drl
title: AI 驱动的无线传感网路由优化
layer: 3
content_type: survey
difficulty: advanced
reading_time: 26
prerequisites:
  - ipv6-6lowpan-rpl
tags:
  - WSN
  - 深度强化学习
  - DQN
  - PPO
  - 图神经网络
  - 路由优化
  - 网络寿命
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# AI 驱动的无线传感网路由优化

> **难度**：🟠 进阶 | **领域**：无线传感网、强化学习路由 | **阅读时间**：约 26 分钟

## 日常类比

森林里上千个靠电池的传感器要定期把温湿度送到山脚基站：离基站近的节点还得帮远处转发，结果「热区」先没电，全网像抽掉中心的蛛网一样断掉。**无线传感器网络（Wireless Sensor Network, WSN）** 路由的核心是把能量耗散摊匀并延长寿命。传统协议靠固定规则；**深度强化学习（Deep Reinforcement Learning, DRL）** 试图让节点或控制器学会选下一跳——多在仿真里好看，落地仍难[1][4]。

## 摘要

本文回顾 LEACH、PEGASIS、TEEN、Directed Diffusion、HEED 等经典路由，说明将路由建模为马尔可夫决策过程（Markov Decision Process, MDP）后，深度 Q 网络（Deep Q-Network, DQN）、近端策略优化（Proximal Policy Optimization, PPO）、多智能体强化学习（Multi-Agent RL, MARL）与图神经网络（Graph Neural Network, GNN）增强路线的思路与证据边界。文中「相对 LEACH 寿命 +X%」均来自特定仿真设定，**换能量模型与拓扑会变**[4][7]。

## 1 热区与优化目标

靠近汇聚节点（Sink）的转发负担更高，易出现能量空洞。常见指标：首个节点死亡（First Node Death, FND）、半数节点死亡（Half Node Death, HND）、最后节点死亡（Last Node Death, LND）、投递率、能耗/包、剩余能量变异系数、端到端延迟。论文必须写清寿命定义，否则排名不可比[1]。

## 2 经典协议

**LEACH**：分簇并轮换簇头（Cluster Head, CH），均摊远距发送；随机选头可能不均，且常假设可直达基站[1]。

**PEGASIS**：链上邻接通信，链头对基站；省传输但构链与链头瓶颈明显[2]。

**TEEN / APTEEN**：硬/软阈值抑制无变化上报，事件稀少时很省电[10]。

**Directed Diffusion**：兴趣扩散与梯度强化，数据为中心[3]。

**HEED**：簇头竞选考虑剩余能量等，改善 LEACH 类随机性[9]。

| 协议 | 结构 | 模式 | 全局信息 | 相对寿命叙事 | 适用倾向 |
|------|------|------|----------|--------------|----------|
| LEACH | 随机分簇 | CH→基站 | 少 | 基准 | 小规模均匀 |
| LEACH-C | 基站选 CH | 同上 | 要 | 常略优 | 基站可达 |
| PEGASIS | 链 | 链头→基站 | 邻距等 | 常优于 LEACH | 规则部署 |
| TEEN | 分簇+阈值 | 事件 | 少 | 低事件率下很省 | 告警监测 |
| Directed Diffusion | 梯度 | 查询驱动 | 少 | 场景依赖 | 查询型 |
| HEED | 能量感知分簇 | 多跳常见 | 局部 | 常优于 LEACH | 更大规模 |

表中倍数来自文献综述式归纳，**不是可移植常数**。

## 3 DRL 路由

### 3.1 MDP 要素

- **状态**：剩余能量、队列、邻居、链路质量等
- **动作**：选下一跳（及可选功率）
- **奖励**：投递正奖励、能耗与选低能邻居惩罚、均衡项

训练好后推理可为一次前向，适合「算得动」的节点或簇头；Class 0/1 级设备往往仍过重[4]。

### 3.2 DQN / PPO

DQN 估各下一跳 Q 值；PPO 直接优化策略，更易处理连续/混合动作（功率+下一跳）[4][5]。单篇 IEEE IoT-J / TMC 仿真报告过相对 LEACH 数十百分点寿命提升、PPO 相对 DQN 再增一截——**均依赖节点数、流量与能量模型，引用时需带设定**[4][5]。

### 3.3 MARL

集中式状态随规模爆炸。独立学习简单但非平稳；集中训练分布执行（Centralized Training with Decentralized Execution, CTDE）如 QMIX、MAPPO 用全局信息训练、局部执行。通信学习再决定交换什么消息。大规模仿真中有报告称接近集中式寿命且大幅降控制开销——同样属单文证据[6]。

## 4 GNN 增强与联合优化

WSN 是图：GNN（如 GAT、GraphSAGE）编码拓扑与节点特征，再交给 PPO/SAC 决策，避免把图「拍平」丢结构[7]。小图训练迁到大图的参数共享是卖点；迁移性能下降幅度因文而异。进一步工作把路由、占空比、功率联合进同一策略，仿真中有额外寿命增益报告[8]。

| 方法族 | 拓扑利用 | 执行方式 | 证据形态 |
|--------|----------|----------|----------|
| 经典分簇/链 | 弱～中 | 分布式规则 | 长期仿真传统 |
| DQN/PPO | 向量状态 | 中心或每节点 | 单文仿真为主 |
| MARL | 局部观测 | 分布执行 | 大规模仿真 |
| GNN+DRL | 显式图 | 视部署 | 较新，仿真为主 |

## 5 评估与工具

统一报告 FND/HND/LND、PDR、J/包、能量变异系数与延迟。NS-3、MATLAB 常见；ns3-gym 等把 Gym 智能体接到网络仿真[11]。对比必须固定能量模型、MAC 与流量，避免「只改路由标签」。

## 6 局限、挑战与可改进方向

### 1. Sim-to-Real 鸿沟

**局限**：信道、硬件个体差与干扰使仿真策略失效；论文几乎都在仿真收场[4][7]。
**改进**：先在试验床做小规模迁移；策略蒸馏为规则/查表以适配 MCU。

### 2. 训练探索烧能量

**局限**：在线探索等于真实耗电与丢包；安全关键监测不可乱试。
**改进**：离线 RL + 保守微调；数字孪生里训，现场只推理。

### 3. 对抗与虚假状态

**局限**：恶意邻居谎报能量/RSSI 可操纵下一跳，形成黑洞。
**改进**：信誉/异常检测；动作掩码限制可疑邻居；与安全路由工作交叉验证。

### 4. 与标准协议脱节

**局限**：IETF **RPL** 等已部署栈与学术 DRL 代理之间缺少标准集成路径。
**改进**：把 DRL 限在目标函数/父节点排序的插件层，保留 RPL 互操作；明确回退到 OF0/MRHOF。

## 7 小结

WSN 路由从静态分簇/链走到 DRL 与 GNN，方向是「更多状态、更好决策」。当前可信结论应写成：在**给定仿真假设**下寿命与投递可改善；工业落地关键仍是轻量推理、标准互操作与真实性验证[4][7][11]。

## 参考文献

[1] W. Heinzelman et al., "Energy-efficient communication protocol for wireless microsensor networks," HICSS, 2000.
[2] S. Lindsey and C. Raghavendra, "PEGASIS: Power-efficient gathering in sensor information systems," IEEE Aerospace, 2002.
[3] C. Intanagonwiwat et al., "Directed diffusion," ACM MobiCom, 2000.
[4] Y. Zhang et al., "Deep Reinforcement Learning-Based Routing for Energy-Efficient Wireless Sensor Networks," IEEE Internet of Things Journal, 2023.
[5] X. Chen et al., "PPO-Based Adaptive Routing for Heterogeneous Wireless Sensor Networks," IEEE Transactions on Mobile Computing, 2024.
[6] R. Sharma et al., "Multi-Agent Reinforcement Learning for Distributed Routing in Large-Scale WSNs," Ad Hoc Networks, 2024.
[7] W. Li et al., "GNN-Route: Graph Neural Network Enhanced Deep Reinforcement Learning for WSN Routing Optimization," IEEE/ACM Transactions on Networking, 2025.
[8] H. Wang et al., "Joint Routing, Duty Cycling and Power Control via Graph Reinforcement Learning," IEEE INFOCOM, 2025.
[9] O. Younis and S. Fahmy, "HEED," IEEE Transactions on Mobile Computing, 2004.
[10] A. Manjeshwar and D. Agrawal, "TEEN," IPDPS, 2001.
[11] P. Gawłowicz and A. Zubow, "ns-3 meets OpenAI Gym" / ns3-gym related publications (e.g., WiNTECH).
[12] IETF RFC 6550, "RPL: IPv6 Routing Protocol for Low-Power and Lossy Networks."
