---
schema_version: '1.0'
id: collaborative-inference-survey
title: 协作推理系统全景：多设备协同运行深度学习模型
layer: 5
content_type: survey
difficulty: advanced
reading_time: 30
prerequisites:
  - jupiter
  - split-computing
tags:
- 协作推理
- 流水线并行
- Jupiter
- EdgeShard
- Petals
- PowerInfer
- Prefill-Decode
- 边缘LLM
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 协作推理系统全景：多设备协同运行深度学习模型

> **难度**：🟠 挑战 | **领域**：协作推理（Collaborative Inference）、边缘大模型 | **阅读时间**：约 30 分钟

## 日常类比

搬特别重的沙发上楼：一个人搬不动，三个人各抬一段就能上去。协作推理同理——模型太大单机装不下，就拆成几块，多台设备各负责一段，中间结果像"交接棒"在设备间传递。

云端像请搬家公司：能力强但贵、要出门（数据上传）、还依赖路况（广域网）。边缘协作像邻居互助：数据不出小区（局域网），但要协调谁抬哪一段、别互相绊脚（通信与流水线气泡）。

## 摘要

本文综述多设备协作推理：从数据/张量/流水线并行（Data / Tensor / Pipeline Parallelism, DP/TP/PP）基础，到 Jupiter、EdgeShard、Petals、PowerInfer-2 等系统，以及 Prefill/Decode 差异、KV Cache 与新兴方案。面向边缘局域网与广域众包两类场景，给出选型表与开放问题[1][2][3][4]。

## 1 为什么需要协作推理

Llama2-7B 在 FP16 下权重约 14GB 量级，常超边缘内存；INT4 可压到约数 GB，但仍需为 KV Cache（Key-Value Cache）与激活留余量[1][10]。更大模型单机更不可行。

协作思路：按层或张量切分，设备间传中间激活。与纯云端对比：

| 维度 | 云端推理 | 边缘协作推理 |
|------|----------|--------------|
| 延迟 | 含广域往返，常数十–数百 ms | 局域网内，通常更低 |
| 隐私 | 数据上传 | 数据可不出局域网 |
| 可用性 | 依赖外网 | 可离线/弱网 |
| 成本 | 持续 API/算力费 | 硬件一次性投入为主 |
| 带宽 | 需稳定 WAN | 主要 LAN |
| 适用模型 | 可至超大 | 常见中等（如 7B–13B 协作） |

## 2 并行策略基础

**数据并行（DP）**：每机完整副本，分样本。推理若单机已能装下全模型，协作动机弱。

**张量并行（TP）**：切分层内矩阵，层间需 all-reduce。数据中心 NVLink 等高带宽下可行；边缘 Wi-Fi（如百 Mbps 量级）上通信占比可主导总时延[7]。

**流水线并行（PP）**：按层切分，点对点传激活，通信量通常远小于 TP，更适边缘[1][8]。

| 并行策略 | 通信量特征 | 通信模式 | 低带宽下通信占比（示意） |
|----------|------------|----------|--------------------------|
| 张量并行 | 每层 all-reduce | 多对多 | 常很高 |
| 流水线并行 | 激活点对点 | 一对一 | 相对低 |

**Pipeline bubble**：单请求时各 stage 串行空闲，空闲率可随 stage 数升高。GPipe/PipeDream 用 micro-batch 填泡[8]；边缘常单请求，故 Jupiter 等用序列内流水线缓解[1]。

混合并行：节点间 PP、节点内 TP（Megatron-LM 思路）[7]；边缘系统目前仍以纯 PP 为主。

## 3 四大系统对比

### 3.1 Jupiter (INFOCOM 2025)

Prefill：利用因果注意力单向依赖做序列内切分，填 bubble[1]。Decode：投机解码（如 Medusa 类 draft）与大纲式并行。规划：动态规划层/序列划分，考虑异构与内存。报告在多台 Jetson 级设备上协作运行量化 Llama2-7B/13B，端到端延迟相对基线可有数量级改善（以论文实测为准）[1]。详见 [jupiter](jupiter.md)。

### 3.2 EdgeShard (2024)

纯 PP，层分配偏贪心最小化最大 stage 延迟；无序列内分割与解码加速。Prefill bubble 仍高；性能通常弱于 Jupiter 同类设定[2]。

### 3.3 Petals (2023)

面向互联网志愿者 GPU，像 BitTorrent 众包大模型[3]。节点延迟与带宽假设为 WAN；强调容错与动态加入离开。延迟高于 LAN 边缘系统，但可拼出更大模型。

### 3.4 PowerInfer-2 (2024)

单机异构（NPU/CPU/GPU + DRAM/外存），按神经元激活稀疏加载"热/冷"参数[4]。不支持多机协作；依赖稀疏性与特定硬件。

### 3.5 总表

| 维度 | Jupiter[1] | EdgeShard[2] | Petals[3] | PowerInfer-2[4] |
|------|------------|--------------|-----------|-----------------|
| 策略 | PP+序列内 | 纯 PP | PP | 单机稀疏/异构 |
| 场景 | 边缘 LAN | 边缘 LAN | 志愿者 WAN | 旗舰手机 |
| 模型 | 约 7B–13B | 约 7B–13B | 可达更大 | 单机内存+外存内 |
| 设备数 | 少数几台 | 少数几台 | 可很多 | 1 |
| Decode 优化 | 投机等 | 弱 | 弱 | 稀疏推理 |
| 容错 | 弱 | 弱 | 强 | N/A |
| 开源 | 是 | 是 | 是 | 是 |

互补：Jupiter/EdgeShard 覆盖"多弱机+LAN"；Petals 覆盖"众包+WAN"；PowerInfer-2 覆盖"单强机"。融合方向：机内稀疏 + 机间 PP[1][4]。

## 4 新兴方案

| 系统 | 年份 | 核心 | 场景 | 与 Jupiter |
|------|------|------|------|------------|
| HexGen[5] | 2024 | 异构混合并行规划 | 异构 GPU | 规划可借鉴 |
| FusionAI[11] | 2024 | 去中心 P2P | 不可靠网 | 容错互补 |
| DistServe[6] | 2024 | Prefill/Decode 分离 | 云端服务 | 阶段分离相通 |
| Splitwise[12] | 2024 | 异构机混搭 | 混合集群 | 异构优化 |
| ExeGPT 等 | 2024 | 执行计划优化 | 数据中心 | 调度参考 |

## 5 LLM 推理特殊挑战

| 特性 | Prefill | Decoding |
|------|---------|----------|
| 模式 | 一次吃满输入 | 逐 token 自回归 |
| 瓶颈 | 偏计算密集 | 偏内存带宽 |
| GPU 利用率 | 相对高 | 常很低 |
| 优化 | 增并行度/切序列 | 减步数（投机等）[1][6] |

KV Cache：随层数、隐层、序列长度与精度增长；流水线中各 stage 只存本层 Cache，但投机回滚需跨设备协调删除[10]。长上下文可用 PagedAttention 类分页管理[10]。

## 6 性能与扩展（示意）

带宽与延迟关系依赖实现；低带宽下消除 bubble 的收益往往更突出[1][2]。设备数增加时 Prefill 较易扩展，Decode 常因验证/通信呈亚线性，边际收益递减。

| 设备数（示意） | Prefill 效率趋势 | Decode 效率趋势 |
|----------------|------------------|-----------------|
| 2 | 高 | 较高 |
| 3–4 | 仍可用 | 开始下降 |
| 更多 | 通信占比升 | 边际收益减 |

| 带宽档（示意） | 协作延迟趋势 | 相对纯 PP 基线 |
|----------------|--------------|----------------|
| 低（百 Mbps） | 较高但优化空间大 | 序列内 PP 优势更明显 |
| 中高（Gbps） | 更低 | 优势收窄 |

具体数字以各论文实验设置为准，跨文不可直接横比。

## 7 开放问题

动态带宽/掉线重规划；中间激活隐私（类似梯度泄露风险）；更大模型与更多设备拓扑；端云按查询复杂度智能切分[13][14]。

## 8 局限、挑战与可改进方向

### 1. 静态规划难适应真实边缘

**局限**：多数系统离线假定带宽与在线集合，Wi-Fi 波动与电池掉线会打破最优切分。
**改进**：轻量在线重划分；心跳+降级为更少 stage；与带宽探测联动[1][11]。

### 2. 激活传输的隐私缺口

**局限**：中间激活可被恶意 stage 反推输入，边缘设备物理暴露面大。
**改进**：激活量化/加噪、TEE 执行关键层、最小必要层暴露；威胁模型写进部署文档[13]。

### 3. Decode 扩展性差

**局限**：自回归逐步生成，加设备对 Decode 加速有限，投机又引入同步与回滚复杂度。
**改进**：Prefill/Decode 分离部署[6]；机内稀疏[4]+机间 PP；限制协作主要用于 Prefill。

### 4. 评测不可比

**局限**：模型量化、网络仿真、token 数与硬件世代不同，加速比广告难横比。
**改进**：固定模型检查点与 trace；报告 tokens/s、尾延迟与能耗；开源复现脚本[1][10]。

### 5. 运维与版本一致性

**局限**：多机权重分片版本不一致会导致静默错误。
**改进**：分片哈希清单、滚动升级仲裁、失败自动缩容到可运行子集[3]。

## 参考文献

[1] S. Ye et al., "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices," IEEE INFOCOM, 2025.
[2] S. Wang et al., "EdgeShard: Efficient LLM Inference via Collaborative Edge Computing," arXiv, 2024.
[3] A. Borzunov et al., "Petals: Collaborative Inference and Fine-tuning of Large Models," ACL System Demonstrations, 2023.
[4] Z. Xue / R. Zheng et al., "PowerInfer-2: Fast Large Language Model Inference on a Smartphone," arXiv, 2024.
[5] Y. Jiang et al., "HexGen: Generative Inference of Foundation Model over Heterogeneous Decentralized Environment," ICML, 2024.
[6] Y. Zhong et al., "DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving," OSDI, 2024.
[7] D. Narayanan et al., "Efficient Large-Scale Language Model Training on GPU Clusters Using Megatron-LM," SC, 2021.
[8] Y. Huang et al., "GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism," NeurIPS, 2019.
[9] D. Narayanan et al., "PipeDream: Generalized Pipeline Parallelism for DNN Training," SOSP, 2019.
[10] W. Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP, 2023.
[11] Z. Xue et al., "FusionAI: Decentralized Training and Deploying LLMs with Massive Consumer-Level GPUs," arXiv, 2024.
[12] P. Patel et al., "Splitwise: Efficient Generative LLM Inference Using Phase Splitting," ISCA / 相关技术报告, 2024.
[13] Y. Kang et al., "Neurosurgeon: Collaborative Intelligence Between the Cloud and Mobile Edge," ASPLOS, 2017.
[14] J. Li et al., "Survey on Collaborative Intelligence and Edge-Cloud Inference," IEEE Communications Surveys & Tutorials / 相关综述, 2023–2024.
[15] T. Cai et al., "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads," arXiv, 2024.
[16] H. Touvron et al., "Llama 2: Open Foundation and Fine-Tuned Chat Models," arXiv, 2023.
[17] W. Xiao et al., "SmoothQuant / 边缘量化相关实践综述线索," 参见量化与压缩文献, 2023–2024.
