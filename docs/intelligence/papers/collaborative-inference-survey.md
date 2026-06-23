# 协作推理系统全景：多设备协同运行深度学习模型

> 难度：🟠 挑战 | 前置知识：了解 Transformer 架构基础、分布式系统基本概念

## 论文信息

- **主题**：多设备协作推理（Collaborative Inference）的系统设计、并行策略与前沿方案
- **核心对比**：Jupiter vs EdgeShard vs Petals vs PowerInfer-2 四大系统的深度解析
- **涵盖范围**：从经典数据中心并行策略到边缘场景的适应性演进（2019-2025）

## 1 为什么需要协作推理

### 1.1 问题的本质

一句话：**模型太大，单个设备装不下**。

一个 Llama2-7B 模型在 FP16 精度下需要约 14GB 内存——这已经超过了大多数边缘设备的内存上限。即使经过 INT4 量化降到 ~3.6GB，一个 4GB 内存的 Jetson Nano 加载模型后几乎没有剩余空间给 KV Cache 和中间激活值。更大的模型（13B、70B）在单个边缘设备上根本不可能运行。

协作推理的思路是：既然一台设备装不下，就让多台设备一起来——把模型拆成几块，每台设备负责一块，设备之间通过网络传递中间结果。这就像搬一个特别重的沙发上楼，一个人搬不动，三个人各抬一个部分就能搬上去。

### 1.2 协作推理 vs 云端推理

为什么不直接用云端？因为有些场景"不能"或"不想"用云：

| 维度 | 云端推理 | 边缘协作推理 |
|------|---------|------------|
| 延迟 | 50-200ms（含网络往返） | 10-50ms（局域网内） |
| 隐私 | 数据必须上传 | 数据不出局域网 |
| 可用性 | 依赖互联网连接 | 离线可用 |
| 成本 | 按 API 调用计费（持续支出） | 一次性硬件投入 |
| 带宽需求 | 需要稳定的广域网 | 仅需局域网通信 |
| 适用模型 | 70B-405B 超大模型 | 7B-13B 中等模型 |

## 2 并行策略基础

### 2.1 三种基本并行策略

在分布式深度学习中，模型可以按三种方式拆分到多台设备上：

**数据并行（Data Parallelism, DP）**：每台设备有完整的模型副本，各自处理不同的数据样本，然后同步梯度/结果。适合训练，但对推理来说——如果一台设备就能装下完整模型，为什么还需要协作推理？所以 DP 在"模型太大装不下"的场景中不适用。

**张量并行（Tensor Parallelism, TP）**：把每一层的权重矩阵切分到多台设备上。比如一个 4096×4096 的矩阵，分给两台设备，每台处理 4096×2048。问题是每一层计算完都需要 all-reduce 通信来合并结果，通信量巨大。在数据中心的 NVLink（600GB/s）上这不是问题，但在边缘的 WiFi（100Mbps=12.5MB/s）上，通信延迟会占到总时间的 60-80%。

**流水线并行（Pipeline Parallelism, PP）**：按层切分模型——设备 1 负责第 1-8 层，设备 2 负责第 9-16 层，以此类推。数据像工厂流水线一样依次通过每台设备。每台设备之间只需要传递中间激活值（通常是一个 [batch, seq_len, hidden_dim] 的张量），通信量远小于 TP。

### 2.2 边缘场景下的最优选择

Jupiter 论文通过系统性实测得出的关键结论：**流水线并行是边缘协作推理的最优基础策略**。原因在于通信计算比：

| 并行策略 | 每层通信量 | 通信模式 | 100Mbps 下通信时间占比 |
|---------|-----------|---------|---------------------|
| 张量并行 | O(hidden_size × batch) × all-reduce | 多对多 | 60-80% |
| 流水线并行 | O(hidden_size × batch) × 点对点 | 一对一 | 5-15% |

这个差距在高带宽环境（NVLink 600GB/s）中几乎不存在，但在低带宽边缘环境中被放大了几千倍。

### 2.3 流水线并行的经典问题：Pipeline Bubble

流水线并行的 Achilles' heel 是 pipeline bubble——当只有一个请求时，各 stage 只能依次执行，造成大量空闲时间。假设有 N 个 stage，每个 stage 耗时 T，那么单请求的总延迟是 N×T，但实际有用计算时间只有 T×L/N（L 是总层数），空闲率高达 (N-1)/N。

这就是为什么 GPipe 和 PipeDream 需要将一个 mini-batch 拆成多个 micro-batch 来填充 pipeline——但在边缘推理场景中，通常就一个请求，没有多余的 micro-batch 来填充。Jupiter 提出的"序列内流水线并行"正是解决这个问题的关键创新。

### 2.4 混合并行

实际系统经常组合使用多种策略。最常见的模式是：节点间用流水线并行（通信量小，适合跨节点的低带宽链路），节点内用张量并行（通信量大，但节点内有高速互联）。Megatron-LM 就是这种 TP+PP 混合策略的代表。

在边缘场景中，如果存在两类网络——设备间的 WiFi（100Mbps）和同一设备内的内存总线（GB/s），也可以类似地采用混合策略。但目前的边缘系统（如 Jupiter）还主要使用纯流水线策略。

## 3 四大系统深度对比

### 3.1 Jupiter (INFOCOM 2025)

Jupiter 是本层的基石论文（详见 [Jupiter 论文阅读报告](jupiter.md)），其核心创新在于三个层面：

**Prefill 阶段**：利用因果注意力的单向依赖特性，将输入序列切分为子序列注入流水线，消除 pipeline bubble。这是一个非常精巧的观察——因为 token i 只依赖 token 1 到 i-1，所以可以把序列 [1, ..., S] 切成 [1, ..., s₁] 和 [s₁+1, ..., S]，先把第一段推进 stage 2，第二段就可以在 stage 1 上开始处理了。

**Decoding 阶段**：结合投机解码（Medusa draft heads 并行预测多个 token）和大纲式并行解码（先生成提纲再并行展开各点），双重加速自回归生成。

**规划算法**：基于动态规划的层划分和序列划分，考虑设备异构性和内存约束，离线求解最优并行策略。

核心指标：4 台 Jetson Xavier NX (8GB) 协作运行 Llama2-7B/13B (INT4)，最高 26.1x 端到端延迟缩减。

### 3.2 EdgeShard (2024)

EdgeShard 是一个面向边缘设备的 LLM 推理系统，采用纯流水线并行策略。它是 Jupiter 之前最具代表性的边缘协作推理系统。

**架构设计**：EdgeShard 将模型按 Transformer 层切分到多台边缘设备上，使用简单的层分配算法。与 Jupiter 不同，EdgeShard 不做序列内分割——整个输入序列作为一个整体通过流水线。

**层分配策略**：EdgeShard 使用基于设备计算能力和内存容量的贪心算法进行层分配，考虑设备异构性但优化目标较为简单（最小化最大 stage 延迟）。

**性能特点**：在 Jetson 平台上的实测数据显示，EdgeShard 能将 Llama2-7B 的推理延迟缩短约 10x（相比单设备），但因为缺乏序列内分割和解码加速，其性能约为 Jupiter 的 1/2.7。

**主要局限**：Prefill 阶段 pipeline bubble 率高达 (N-1)/N；Decoding 阶段纯自回归，无加速；不支持动态调整并行策略。

### 3.3 Petals (2023)

Petals 的定位与 Jupiter/EdgeShard 截然不同——它面向互联网规模的志愿者 GPU 集群，让用户可以像 BitTorrent 一样众包 GPU 资源来运行大模型。

**网络模型**：Petals 假设参与节点分布在互联网上，节点间延迟 50-200ms，带宽 1-10Gbps。这与边缘场景的局域网环境（延迟 < 1ms，带宽 100Mbps-1Gbps）有本质区别。

**容错设计**：Petals 的一大特色是处理节点的动态加入和离开。志愿者随时可能关机，系统需要自动检测故障、重新分配层、恢复服务。这在稳定的边缘部署中不是主要问题，但在开放网络中至关重要。

**路由与调度**：Petals 维护一个全局的层可用性表，客户端发起推理请求时，调度器自动选择延迟最低的节点组合来组装完整流水线。

**性能特点**：由于互联网延迟远高于局域网，Petals 的单请求延迟显著高于 Jupiter/EdgeShard。但它的优势在于可以集合大量 GPU 来运行 70B 甚至 175B 的模型——这在边缘场景中不可能实现。

### 3.4 PowerInfer-2 (2024)

PowerInfer-2 走的是一条完全不同的路——它不是多设备协作，而是在单一移动设备（智能手机）上通过异构计算来运行大模型。

**核心思想**：智能手机有 NPU（Neural Processing Unit）、CPU 和 GPU 三种计算单元，以及 DRAM 和外部存储（UFS/eMMC）两级内存。PowerInfer-2 将模型参数按"热度"分类——高频访问的"热参数"放在 DRAM 中由 NPU/GPU 处理，低频的"冷参数"放在外部存储中由 CPU 处理。

**关键技术**：基于神经元激活稀疏性（许多 LLM 的 FFN 层在推理时只有 ~10% 的神经元被显著激活），PowerInfer-2 只加载和计算活跃的神经元，大幅减少实际的内存访问和计算量。

**性能指标**：在一台配备 12GB DRAM 的旗舰手机上运行 47B 参数的模型，达到 11.68 tokens/s。相比 llama.cpp 在同一硬件上的基线实现，加速约 25x。

**局限**：完全不支持多设备协作——纯单设备方案。对于超出单设备内存+外存总量的模型无能为力。且高度依赖特定硬件（NPU）的可用性和激活稀疏性假设。

### 3.5 系统全面对比

| 维度 | Jupiter (2025) | EdgeShard (2024) | Petals (2023) | PowerInfer-2 (2024) |
|------|---------------|-----------------|--------------|-------------------|
| **并行策略** | PP + 序列内分割 | 纯 PP | PP | 单设备异构计算 |
| **目标场景** | 边缘设备集群 (LAN) | 边缘设备集群 (LAN) | 志愿者 GPU 集群 (WAN) | 单一移动设备 |
| **目标模型** | 7B-13B | 7B-13B | 7B-175B | 7B-47B |
| **设备数** | 2-4 台 | 2-4 台 | 10-100+ 台 | 1 台 |
| **网络假设** | WiFi 100Mbps-1Gbps | WiFi 100Mbps-1Gbps | 互联网 1-10Gbps | 无 |
| **Decoding 优化** | 投机解码 + 大纲式 | 无 | 无 | 稀疏推理 |
| **异构支持** | DP 规划 | 有限 | 路由选择 | NPU/CPU/GPU 协同 |
| **容错** | 无 | 无 | 有（节点动态加入/离开） | 不适用 |
| **Prefill 加速** | 1.4-7.4x | 基准 | N/A | N/A |
| **Decoding 加速** | 2.9-33.2x | 基准 | N/A | 25x (vs llama.cpp) |
| **开源** | 是 (GitHub) | 是 | 是 (GitHub) | 是 (GitHub) |

### 3.6 互补关系分析

这四个系统并非互相替代，而是覆盖了协作推理的不同象限：

**Jupiter + EdgeShard** 覆盖"多台弱设备 + 局域网"场景，如智慧家庭中多个智能设备协作运行私有 LLM。Jupiter 在 EdgeShard 基础上通过序列内分割和解码加速实现了显著的性能提升。

**Petals** 覆盖"多台异构设备 + 广域网"场景，如研究社区共享 GPU 资源运行超大模型。它不追求低延迟，而是追求资源共享和大模型可达性。

**PowerInfer-2** 覆盖"单台强设备"场景，如旗舰手机离线运行 LLM。它不需要网络通信，但依赖设备自身的硬件能力。

**未来的融合方向**：将 PowerInfer-2 的稀疏推理技术与 Jupiter 的流水线并行结合——每台设备内部用稀疏推理减少计算量，设备之间用流水线并行分担模型。

## 4 新兴协作推理方案

### 4.1 HexGen (2024)

HexGen 面向异构 GPU 集群（混合不同型号的 GPU），核心贡献是一个"灵活的并行策略规划器"——能在 TP、PP 和 DP 之间为异构环境找到最优组合。与 Jupiter 的纯 PP 策略不同，HexGen 可能对某些层使用 TP（如果设备间有高速互联），对另一些层使用 PP。

### 4.2 FusionAI (2024)

FusionAI 专注于去中心化的 LLM 推理——没有中心调度器，设备通过 P2P 协议自组织。每台设备广播自己持有的模型层和可用资源，推理请求被自动路由到一组能覆盖完整模型的设备上。这种设计更适合不可靠的边缘网络。

### 4.3 DistServe (2024, OSDI)

DistServe 的核心创新是将 Prefill 和 Decoding 两个阶段分离到不同的 GPU 集群上——Prefill 是计算密集型（适合高算力 GPU），Decoding 是内存密集型（适合大内存 GPU）。通过不同的资源分配和并行策略，DistServe 实现了比 vLLM 更高的吞吐量和更低的延迟。

### 4.4 新兴系统对比

| 系统 | 年份 | 核心创新 | 目标场景 | 与 Jupiter 的关系 |
|------|------|---------|---------|-----------------|
| HexGen | 2024 | 异构混合并行规划 | 异构 GPU 集群 | 规划思路可借鉴 |
| FusionAI | 2024 | 去中心化 P2P 推理 | 不可靠网络 | 容错机制互补 |
| DistServe | 2024 | Prefill-Decode 分离 | 云端推理服务 | 阶段分离思路相通 |
| ExeGPT | 2024 | 执行计划优化 | 数据中心 | 调度算法可参考 |
| Splitwise | 2024 | 异构机器混搭 | 混合集群 | 异构优化可借鉴 |

## 5 LLM 推理的特殊挑战

### 5.1 Prefill vs Decoding 的特性差异

LLM 推理分为两个本质不同的阶段，它们对系统设计提出了截然不同的要求：

| 特性 | Prefill 阶段 | Decoding 阶段 |
|------|------------|-------------|
| 计算模式 | 一次处理完整输入序列 | 逐 token 自回归生成 |
| 计算密度 | 高（大矩阵乘法） | 低（向量-矩阵乘法） |
| 瓶颈 | 计算绑定 (compute-bound) | 内存带宽绑定 (memory-bound) |
| GPU 利用率 | 高 (50-90%) | 低 (5-20%) |
| 总延迟占比 | 较小（通常 10-30%） | 较大（通常 70-90%） |

这个差异解释了为什么 Jupiter 需要分别为两个阶段设计不同的优化策略——Prefill 用序列内分割来增加并行度，Decoding 用投机解码来减少步数。

### 5.2 KV Cache 管理

KV Cache 是 LLM 推理中的关键数据结构——存储已处理 token 的 Key 和 Value 矩阵，避免重复计算。在协作推理中，KV Cache 带来特殊挑战：

**内存增长**：KV Cache 大小 = 2 × num_layers × hidden_size × seq_len × precision。对于 Llama2-7B (FP16)，每 1000 个 token 的 KV Cache 约占 1GB——在 8GB 的边缘设备上，这是不可忽视的开销。

**跨设备一致性**：在流水线并行中，每个 stage 只需要存储自己负责的层的 KV Cache，但投机解码中的"回滚"操作需要跨设备协调 KV Cache 的更新——被拒绝的候选 token 对应的 KV Cache 条目必须被删除。

**长上下文支持**：8K-32K 的长上下文推理会导致 KV Cache 占满设备内存。PagedAttention（vLLM 提出）通过分页管理 KV Cache 来减少碎片化，这一技术正在被引入边缘系统。

## 6 实验数据与性能分析

### 6.1 不同网络条件下的性能

以 Llama2-7B (INT4) 在 4 台 Jetson Xavier NX 上为例：

| 带宽 | Jupiter 延迟 | EdgeShard 延迟 | Jupiter 优势 |
|------|------------|---------------|-------------|
| 100 Mbps | ~3.2s | ~8.6s | 2.7x |
| 500 Mbps | ~2.1s | ~5.4s | 2.6x |
| 1 Gbps | ~1.8s | ~4.3s | 2.4x |

可以看到，带宽越低，Jupiter 的优势越明显——因为序列内分割产生的通信开销很小，而它消除的 pipeline bubble 在低带宽下更加突出。

### 6.2 设备数量的可扩展性

| 设备数 | Prefill 效率 | Decoding 效率 | 总加速比 |
|--------|------------|-------------|---------|
| 2 台 | ~95% | ~85% | 1.8x |
| 3 台 | ~90% | ~78% | 2.5x |
| 4 台 | ~85% | ~70% | 3.1x |

Prefill 阶段接近线性扩展，Decoding 阶段因投机解码的固定开销（draft heads 生成 + 验证通信）而呈亚线性。超过 4 台设备后，通信开销开始显著增加，继续加设备的边际收益递减。

## 7 开放问题与研究方向

### 7.1 动态环境适应

现有系统大多假设静态的网络和计算条件。真实的边缘环境中，WiFi 带宽可能在 10Mbps 到 1Gbps 之间波动，设备可能因为电池耗尽而离线。动态重规划（在线调整层分配和并行策略）是一个重要但尚未充分解决的问题。

### 7.2 安全性

协作推理中，中间激活值在设备间传输。恶意设备可能通过分析这些激活值推断原始输入内容（类似联邦学习中的梯度泄露）。如何在保护隐私的同时不显著增加通信开销，是安全协作推理的核心挑战。

### 7.3 更大模型的边缘部署

当前边缘协作推理主要针对 7B-13B 模型。随着更高效的压缩技术出现（如 1-bit LLM、BitNet），未来可能在边缘集群上运行 30B-70B 的模型。这需要更多设备的协作（8-16 台），对通信拓扑和调度算法提出更高要求。

### 7.4 端云协同推理

不是所有推理都需要完全在边缘完成。对于简单查询，边缘本地处理即可；对于复杂推理（如长文档总结、多步推理），可以将部分计算卸载到云端。设计一个智能的端云切分决策器——根据查询复杂度、隐私级别和网络状况动态选择执行位置——是一个有价值的研究方向。

## 8 参考文献

- Ye, S., et al. "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices." IEEE INFOCOM 2025.
- Wang, S., et al. "EdgeShard: Efficient LLM Inference via Collaborative Edge Computing." arXiv 2024.
- Borzunov, A., et al. "Petals: Collaborative Inference and Fine-tuning of Large Models." ACL 2023 (System Demonstration).
- Zheng, R., et al. "PowerInfer-2: Fast Large Language Model Inference on a Smartphone." arXiv 2024.
- Jiang, Y., et al. "HexGen: Generative Inference of Foundation Model over Heterogeneous Decentralized Environment." ICML 2024.
- Zhong, Y., et al. "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized Large Language Model Serving." OSDI 2024.
- Narayanan, D., et al. "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM." SC 2021.
- Huang, Y., et al. "GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism." NeurIPS 2019.
- Kwon, W., et al. "Efficient Memory Management for Large Language Model Serving with PagedAttention (vLLM)." SOSP 2023.
- Xue, Z., et al. "FusionAI: Decentralized Training and Deploying LLMs with Massive Consumer-Level GPUs." arXiv 2024.
