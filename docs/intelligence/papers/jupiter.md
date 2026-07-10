---
schema_version: '1.0'
id: jupiter
title: '论文阅读报告：Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative
  LLMs on Edge Devices'
layer: 5
content_type: paper_reading
difficulty: advanced
reading_time: 28
prerequisites:
  - collaborative-inference-survey
  - llm-quantization-gptq-awq
  - split-computing
tags:
- Jupiter
- 协作推理
- 流水线并行
- 投机解码
- 边缘LLM
- INFOCOM
- Prefill
- Decoding
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
target_paper:
  title: 'Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices'
  authors:
  - Shengyuan Ye
  - Bei Ouyang
  - Liekang Zeng
  - Tianyi Qian
  - Xiaowen Chu
  - Jian Tang
  - Xu Chen
  year: 2025
  doi: 10.1109/INFOCOM55648.2025.11044734
  url: https://arxiv.org/abs/2504.08242
---
# 论文阅读报告：Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices

> **难度**：🔴 进阶 | **领域**：边缘协作推理、生成式大语言模型 | **关键词**：流水线并行, 投机解码, Prefill/Decoding | **阅读时间**：约 28 分钟

## 日常类比

把 7B–13B 级大语言模型（Large Language Model, LLM）塞进单台 Jetson，像让一间小厨房独自做满汉全席：灶台（算力）与冰箱（内存）都不够。Jupiter 的思路是把几间相邻小厨房连成流水线——前厨切配（prefill 子序列）、中厨过油、后厨装盘（decoding），只在相邻工位之间递半成品（hidden states），而不是每道菜都全员开会同步整本菜谱（张量并行的 all-reduce）。带宽像窄走廊时，少开会、多传半成品，往往更快。

## 摘要

本文精读 IEEE INFOCOM 2025 论文 Jupiter[1]：面向边缘设备集群的生成式 LLM 协作推理系统。核心主张是流水线并行（Pipeline Parallelism, PP）通信开销最低，并据此设计序列内流水线 prefill、动态规划并行规划，以及投机解码（Speculative Decoding）+ 大纲式并行 decoding。文中加速比、带宽占比等为论文实验报告量级，跨硬件/模型需复现验证。

## 论文信息

| 字段 | 内容 |
|------|------|
| 标题 | Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices |
| 作者 | Shengyuan Ye, Bei Ouyang, Liekang Zeng, Tianyi Qian, Xiaowen Chu, Jian Tang, Xu Chen |
| 机构 | 中山大学；香港中文大学；港科大（广州）；美的集团 |
| 发表 | IEEE INFOCOM 2025 |
| DOI | 10.1109/INFOCOM55648.2025.11044734 |
| 预印本 | https://arxiv.org/abs/2504.08242 |
| 开源 | https://github.com/ysyisyourbrother/Jupiter |

## 1 研究动机

### 1.1 背景与问题

生成式 LLM 正从云端迁向边缘以保护隐私。单台边缘设备（如 Jetson 系列，常见约 8 GB 统一内存）难以独立承载 7B–13B 级模型：即便 INT4 量化，延迟仍高，且易内存溢出（Out of Memory, OOM）[1]。

### 1.2 现有方案不足

| 策略 | 通信模式 | 边缘痛点 |
|------|----------|----------|
| 张量并行（Tensor Parallelism, TP） | 每层 all-reduce | 低带宽下通信易成瓶颈 |
| 序列并行（Sequence Parallelism, SP） | 每层 all-gather | 需完整模型副本；decoding 易退化 |
| 传统流水线并行 | 点对点传激活 | 单序列时易退化为串行 |
| 既有边缘协作 | 多偏 prefill | 常忽视自回归 decoding |

### 1.3 关键观察

论文 measurement study 称：流水线仅在相邻 stage 传递激活，通信-计算比在常见并行策略中最低，更适合百兆–千兆级边缘链路[1]。据此以 PP 为原则，对 prefill 与 decoding 分别优化。

## 2 系统设计

### 2.1 总体架构

| 组件 | 职责 |
|------|------|
| Profiler | 不同长度校准序列上测层级延迟、内存、利用率 |
| Parallelism Planner | 动态规划离线求层划分与序列划分 |
| Runtime Engine | Prefill：序列内流水线；Decoding：投机解码 + 大纲式并行 |

### 2.2 Prefill：序列内流水线并行

因果解码器中 token \(t_i\) 仅依赖 \(t_1,\ldots,t_{i-1}\)。长输入可切为连续子序列 \((s_1,\ldots,s_M)\) 注入流水线：\(s_1\) 进 Stage 1 后传 Stage 2，同时 \(s_2\) 进 Stage 1。各 Stage 缓存已处理子序列的 hidden states（类 KV Cache），保证与整序列顺序计算数学等价[1]。

### 2.3 并行规划

| 子问题 | 目标 | 复杂度（论文） |
|--------|------|----------------|
| 层划分 | 最小化最慢 stage；参数+KV 不超内存 | \(O(L^2\|D\|)\) |
| 序列划分 | 段延迟均衡；段长 ≥ 阈值 \(b\) | \(O(S_{\max}^2\|D\|)\) |

规划为一次性离线过程；论文称边缘设备上可在约数分钟内完成[1]。

### 2.4 Decoding：双重加速

**投机解码**：参考 Medusa，在末层后附加 draft heads，自起草候选 token，经流水线回传验证；每次 draft+verify 约一次完整前向[2][1]。

**大纲式流水线并行解码**：先生成有序大纲（约数个要点），各要点作为独立请求并发注入 pipeline，共享初始 prefill 的 KV Cache，再按序拼接。模块可插拔；编程/数学等强链式推理任务上质量可能下降[1]。

## 3 相关工作对比

### 3.1 边缘/分布式 LLM 推理系统

| 系统 | 并行策略 | 解码优化 | 异构 | 论文报告加速量级 | 局限（本文归纳） |
|------|----------|----------|------|------------------|------------------|
| Jupiter (2025) | PP + 序列内分割 | 投机 + 大纲 | DP 规划 | 最高约 26.1×（相对 TP 类基线）[1] | 静态规划；实验约 4 设备 |
| EdgeShard (2024) | 纯 PP | 弱 | 有限 | 约 10× 量级（公开报告）[3] | bubble；decoding 弱 |
| Petals (2023) | PP | 弱 | 支持 | — | 面向互联网延迟[4] |
| PowerInfer / -2 | 单机稀疏/异构 | 热冷/NPU | 不适用 | 相对 llama.cpp 可达十余倍量级[5][6] | 非多机协作 |
| llama.cpp 分布式 | PP | 弱 | 有限 | 近线性（视实现）[7] | 调度与解码优化弱 |

### 3.2 并行策略通信特征

| 策略 | 通信 | 内存 | 边缘适用性（定性） |
|------|------|------|-------------------|
| TP | All-Reduce，每层 | 分片高 | 差（通信密） |
| SP | All-Gather | 常需完整副本 | 中 |
| PP | 点对点激活 | 分片高 | 较好 |
| Jupiter PP+ | 点对点 + 微批 | 分片 + 序列分割 | 论文主张最优[1] |

论文称在约 100 Mbps–1 Gbps 条件下，TP 的 all-reduce 可占延迟大部分，PP 点对点占比显著更低；序列内分割可压低传统 \((N-1)/N\) 量级 bubble——具体占比依赖实现与负载，宜实测[1]。

### 3.3 投机解码方法（选型背景）

| 方法 | Draft 来源 | 特点 |
|------|------------|------|
| Medusa[2] | 附加 FFN heads | 无独立小模型；Jupiter 采用 |
| EAGLE / EAGLE-2[8] | 特征级自回归 | 接受率常更高 |
| Lookahead[9] | Jacobi / n-gram | 可无额外训练 |
| 经典投机[10] | 独立小模型 | 额外内存 |

## 4 主要贡献（论文归纳）

1. Measurement 支撑“边缘协作优先 PP”的设计原则。
2. 序列内流水线并行，单序列下仍可填满 pipeline。
3. 动态规划同时优化层划分与序列划分，考虑异构与内存。
4. 将投机解码嵌入跨设备流水线并处理 KV 同步。
5. 大纲式并行 decoding，可插拔。
6. Jetson 实机实现与开源。

## 5 实验评估（论文报告）

### 5.1 设置

同构：4× Jetson Xavier NX（约 8 GB）；异构：NX + TX2 + Nano。带宽仿真约 100 Mbps / 500 Mbps / 1 Gbps。模型：Llama2-7B/13B（INT4）。数据：LiMA（延迟）、Vicuna-80 / WizardLM（质量）。基线含 SP、Megatron-LM、DeTransformer、Galaxy、EdgeShard[1]。

### 5.2 主要结果（均属论文报告，非独立复现）

| 对比维度 | 论文报告量级 |
|----------|--------------|
| 相对 TP 类方案端到端 | 最高约 26.1× 延迟降低 |
| 相对 SP | 最高约 3.3×；13B 上 SP 可 OOM |
| 相对 EdgeShard | 最高约 2.7× |
| Prefill | 约 1.4×–7.4× |
| Decoding | 约 2.9×–33.2× |
| 投机+大纲消融 | decoding 合计最高约 3.9×（二者近似可叠加） |

生成质量：通用问答上大纲法与朴素生成接近；编程/数学上因破坏跨步依赖而明显下降[1]。

### 5.3 可扩展性

2→4 设备时，论文称 prefill 近线性（效率约八成量级），decoding 因投机固定开销呈亚线性（约七成量级）[1]。更大集群未充分验证。

## 6 局限、挑战与可改进方向

### 1. 大纲式解码任务适用面窄

**局限**：强链式推理（代码、证明）质量下降；自动启停机制讨论不足。
**改进**：轻量任务分类器/启发式（关键词、是否要求逐步推理）；默认关闭大纲，仅对列举型生成开启。

### 2. 实验规模与模型覆盖有限

**局限**：最多约 4 设备；主测 Llama2；未充分覆盖更新架构与更大参数。
**改进**：8–16 设备与多种拓扑；Llama3/Qwen/Mistral 等；报告 bubble 随 stage 数变化曲线。

### 3. 静态离线规划

**局限**：难适应带宽抖动、负载变化、设备加入/离开。
**改进**：轻量在线重规划或周期性 re-profile；带宽突变时回退保守划分。

### 4. 长上下文内存压力

**局限**：各 stage 缓存已处理子序列状态，4K–8K 级输入易挤占 8 GB 设备。
**改进**：结合 PagedAttention、StreamingLLM、H2O 等 KV 压缩/淘汰[11][12]。

### 5. 缺少端云决策对照

**局限**：未系统对比“边缘协作 vs 云端 API（含网络）”的延迟与成本。
**改进**：统一 SLA 下的端云协同路由：隐私/离线走边缘，复杂推理可授权上云。

### 6. Draft 训练成本

**局限**：Medusa heads 需额外训练；换模型成本高。
**改进**：评估 Lookahead/EAGLE-2 等低训练或动态 draft 方案在流水线上的集成[8][9]。

## 7 总结

Jupiter 将 HPC 流水线思想与因果注意力、自回归生成结合，针对边缘带宽与内存约束分别优化 prefill/decoding，并在 Jetson 集群上报告相对 TP 类基线最高约 26.1× 的端到端延迟降低[1]。其与 EdgeShard、Petals、PowerInfer 等形成互补版图；动态规划、长上下文与任务感知解码仍是落地关键缺口。

## 参考文献

[1] S. Ye et al., "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices," IEEE INFOCOM, 2025. DOI: 10.1109/INFOCOM55648.2025.11044734.
[2] T. Cai et al., "Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads," ICML, 2024.
[3] M. Zhang et al., "EdgeShard: Efficient LLM Inference via Collaborative Edge Computing," arXiv / 相关边缘分片工作, 2024.
[4] A. Borzunov et al., "Petals: Collaborative Inference and Fine-tuning of Large Models," BigScience Workshop / 相关工作, 2023.
[5] Y. Song et al., "PowerInfer: Fast Large Language Model Serving with a Consumer-grade GPU," SOSP, 2024.
[6] Y. Xue et al., "PowerInfer-2: Fast Large Language Model Inference on a Smartphone," arXiv, 2024.
[7] G. Gerganov et al., "llama.cpp," GitHub, 2023–2025.
[8] Y. Li et al., "EAGLE / EAGLE-2: Speculative Sampling via Feature-level Autoregression," 2024.
[9] Y. Fu et al., "Break the Sequential Dependency of LLM Inference Using Lookahead Decoding," ICML, 2024.
[10] Y. Leviathan et al., "Fast Inference from Transformers via Speculative Decoding," ICML, 2023.
[11] W. Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP, 2023.
[12] G. Xiao et al., "Efficient Streaming Language Models with Attention Sinks," ICLR, 2024.
[13] M. Shoeybi et al., "Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism," arXiv, 2019.
[14] Y. Huang et al., "GPipe: Efficient Training of Giant Neural Networks using Pipeline Parallelism," NeurIPS, 2019.
