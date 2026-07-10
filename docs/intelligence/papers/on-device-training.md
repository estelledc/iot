---
schema_version: '1.0'
id: on-device-training
title: 设备端在线训练：让边缘模型持续进化
layer: 5
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 设备端在线训练：让边缘模型持续进化

> 难度：🟡 进阶 | 前置知识：了解迁移学习和微调（fine-tuning）的基本概念

## 论文信息

- **主题**：在资源受限的边缘设备上进行模型训练和微调——让部署后的模型能适应本地数据分布、持续学习新知识
- **核心问题**：训练比推理难 10-100 倍——推理只需前向传播，训练还需要反向传播、存储中间激活值、更新优化器状态。如何在 MCU/手机上实现训练？
- **涵盖范围**：迁移学习基础 → TinyTL (2020) → PockEngine (2023) → LoRA on Edge (2024) → 联邦设备端训练

## 1 为什么需要设备端训练

### 1.1 部署后的模型退化

一个在实验室训练好的模型，部署到真实世界后往往会"水土不服"。原因很简单：训练数据和部署环境的数据分布不一样。

举几个例子：

**语音助手**：在标准普通话数据上训练的语音模型，到了广东用户手上可能识别率从 95% 降到 70%——因为用户的口音、说话速度、背景噪音都和训练数据不同。

**工业质检**：在 A 工厂的产品图像上训练的缺陷检测模型，搬到 B 工厂后精度下降——因为 B 工厂的照明条件、摄像头角度、产品型号都不同。

**自动驾驶**：在加州阳光明媚的路面上训练的模型，到了北欧的冬天可能无法应对积雪覆盖的道路标线。

传统的做法是：收集新环境的数据 → 传回云端 → 重新训练 → 部署更新后的模型。但这个流程太慢（可能需要数天到数周）、不尊重隐私（数据要离开设备）、依赖网络连接（离线设备怎么办？）。

设备端训练让模型在部署位置就地学习、即时适应。

### 1.2 训练 vs 推理的资源差异

为什么推理能在边缘设备上跑，训练却难？因为训练的资源需求远高于推理：

| 资源 | 推理 | 训练 | 差异 |
|------|------|------|------|
| 内存（模型参数） | 模型权重 | 模型权重 + 梯度 + 优化器状态 | 3-4x |
| 内存（中间数据） | 只需当前层的激活 | 需要所有层的激活（用于反向传播） | 5-10x |
| 计算量 | 前向传播 | 前向传播 + 反向传播 | 2-3x |
| 总内存（典型） | ResNet-50: ~100MB | ResNet-50: ~1.2GB | ~12x |

推理时，每一层计算完就可以丢弃中间激活值（下一层会产生新的）。但训练时，所有层的中间激活值必须保留到反向传播阶段——因为计算梯度需要用到前向传播时的中间结果。这个"激活值存储"是训练内存开销的大头。

## 2 迁移学习：设备端训练的基础

### 2.1 核心思想

迁移学习（Transfer Learning）的核心假设是：一个在大规模数据集（如 ImageNet）上预训练的模型，其底层特征（边缘检测、纹理识别）是通用的，可以迁移到新任务上。

实践中的标准流程是：冻结预训练模型的大部分层（不更新权重），只微调最后几层（通常是分类头）。这样既利用了预训练的通用知识，又只需要更新很少的参数——计算和内存需求大幅降低。

### 2.2 全量微调 vs 冻结微调

| 策略 | 更新参数量 | 内存需求 | 训练速度 | 精度（相对） | 适用场景 |
|------|-----------|---------|---------|------------|---------|
| 全量微调 | 100% | 最高 | 最慢 | 最好 | 云端 / 强GPU |
| 冻结 backbone, 只调头 | ~2-5% | 低 | 快 | 中 | 边缘设备 |
| 只调最后 N 层 | 10-30% | 中 | 中 | 较好 | 中等算力设备 |
| LoRA / Adapter | 0.1-1% | 很低 | 最快 | 较好 | 极受限设备 |

## 3 TinyTL：为微控制器设计的迁移学习

### 3.1 问题与动机

TinyTL (Tiny Transfer Learning, 2020, NeurIPS) 来自 MIT Han Lab，专门解决在微控制器（256KB SRAM）上进行迁移学习的问题。

关键洞察：标准的"冻结 backbone + 微调头"方法虽然减少了参数更新量，但前向传播仍然需要计算完整 backbone 的所有层，中间激活值仍然需要存储（用于微调头的反向传播）。在 256KB SRAM 上，即使只微调一个线性层，存储中间激活值的内存开销也可能超出预算。

### 3.2 核心方案：Lite Residual Learning

TinyTL 的核心创新是 Lite Residual Module：在冻结的 backbone 旁边添加一条极轻量的旁路（residual branch）。这条旁路由降维投影 + 少量可训练参数 + 升维投影组成，参数量仅为主干的 1% 左右。

```
输入
├── 冻结的 backbone（前向传播，但无需存储激活——因为不反向传播）
├── Lite Residual Module（前向 + 反向传播，需存储激活——但极小）
↓
输出 = backbone 输出 + 残差输出
```

由于 backbone 被完全冻结（不参与反向传播），其中间激活值不需要保存——这直接砍掉了训练内存的大头。只有 Lite Residual Module 的（极小的）激活值需要保留。

### 3.3 实验结果

在 MCUNet 架构 + STM32F746 (320KB SRAM, 1MB Flash) 上：

| 方法 | 峰值内存 | 精度（Cars → CUB迁移） | 可训练参数 |
|------|---------|---------------------|----------|
| 全量微调 | >2MB（OOM） | - | 100% |
| 只调最后1层 | 1.1MB（OOM） | - | 2% |
| TinyTL（Bias only） | 230KB | 74.2% | 0.5% |
| TinyTL（Lite Residual） | 285KB | 78.5% | 1.1% |

TinyTL 是首个在真实 MCU 上实现迁移学习的工作，内存开销比标准微调降低了 6.5x。

## 4 PockEngine：训练编译器

### 4.1 设计理念

PockEngine (2023, MIT Han Lab) 的核心理念是：**把训练当作编译问题来解决**。与其在运行时动态分配内存和计算，不如在部署前就静态分析训练计算图，生成针对目标硬件优化的训练代码。

### 4.2 关键优化

**图优化**：PockEngine 在编译时分析训练计算图，进行操作融合（如 Conv+BN 融合的反向传播）、死代码消除（冻结层的反向传播可以完全跳过）、内存规划（提前计算每个时刻的内存峰值并优化张量生命周期）。

**稀疏反向传播**：不是所有梯度都同等重要。PockEngine 支持"梯度剪枝"——在反向传播中只计算和更新梯度值最大的 top-k% 通道，其余跳过。在 50% 稀疏率下，训练速度提升 1.8x，精度仅下降 0.3%。

**量化训练**：将训练过程中的权重、激活和梯度都用 INT8 量化表示（量化感知训练的扩展），进一步减少内存和计算。

### 4.3 实验结果

| 平台 | 框架 | ResNet-50 微调速度 | 内存 |
|------|------|------------------|------|
| Jetson AGX | PyTorch | 基准 (1.0x) | 4.2GB |
| Jetson AGX | PockEngine | 11x | 0.95GB |
| Raspberry Pi 4 | PyTorch | 无法运行 | OOM |
| Raspberry Pi 4 | PockEngine | 可运行 | 0.8GB |
| Apple M1 | PyTorch | 1.0x | 3.8GB |
| Apple M1 | PockEngine | 7.6x | 0.7GB |

PockEngine 首次让完整的 ResNet-50 微调在 Raspberry Pi 4 (4GB) 上成为可能。

## 5 LoRA on Edge：参数高效微调

### 5.1 LoRA 回顾

LoRA (Low-Rank Adaptation, 2022, ICLR) 是当前最流行的参数高效微调（PEFT）方法。核心思想：大模型在微调时权重的变化矩阵 ΔW 通常是低秩的——即可以分解为两个小矩阵的乘积 ΔW = A × B，其中 A 是 (d_model, r) 维，B 是 (r, d_model) 维，r 远小于 d_model（典型值 r=4-16）。

```
原始权重矩阵 W: 4096 × 4096 = 16,777,216 参数
LoRA 低秩分解 (r=8): A(4096×8) + B(8×4096) = 65,536 参数
参数量比: 0.39%
```

### 5.2 在边缘设备上的 LoRA

将 LoRA 应用于边缘设备的 LLM 微调面临几个挑战：

**内存挑战**：即使只训练 LoRA 参数（0.39%），仍然需要存储完整模型的前向传播激活值用于反向传播。对于 Llama2-7B (INT4, ~3.6GB)，激活值可能额外占用 2-4GB——总内存需求超出 8GB 设备的预算。

**解决方案——梯度检查点（Gradient Checkpointing）**：不存储所有层的激活值，而是只在关键的"检查点"层保存激活值。反向传播到需要某层激活值但未保存时，从最近的检查点重新前向计算。以计算换内存，额外计算开销约 30-50%，但内存减少 5-10x。

**QLoRA (2023)**：将 LoRA 与量化结合——基础模型以 NF4（4-bit NormalFloat）量化存储，LoRA 参数以 FP16 训练，反向传播时将量化权重反量化再与 LoRA 参数组合。QLoRA 使得 65B 模型可以在单张 48GB GPU 上微调——类似思路缩小后可以在 Jetson AGX (32GB) 上微调 7B 模型。

### 5.3 边缘 LoRA 实践数据

| 设备 | 模型 | LoRA rank | 内存占用 | 微调速度 (tokens/s) | 精度 vs 全量微调 |
|------|------|-----------|---------|--------------------|--------------| 
| Jetson AGX 32GB | Llama2-7B (INT4) | r=8 | ~12GB | ~50 | -0.5% |
| Jetson Xavier NX 8GB | Phi-3-mini (INT4) | r=4 | ~6.5GB | ~20 | -1.2% |
| MacBook M2 16GB | Llama2-7B (INT4) | r=8 | ~14GB | ~80 | -0.5% |
| Raspberry Pi 5 8GB | Phi-2 (INT4) | r=4 | ~5.5GB | ~5 | -1.8% |

## 6 联邦设备端训练

### 6.1 概念融合

联邦学习（参见 [联邦学习与物联网](federated-learning-iot.md)）和设备端训练的结合是一个自然的演进：每台设备在本地用自己的数据进行 LoRA/TinyTL 微调，然后通过联邦聚合将微调结果（LoRA 参数或 Lite Residual 参数）汇聚成全局模型——数据不离开设备，模型持续进化。

### 6.2 FedPETuning (2024)

FedPETuning 将联邦学习与参数高效微调方法（LoRA、Adapter、Prompt Tuning）结合：

**通信效率**：只传输 LoRA 参数（< 1% 的参数量），通信量比传统 FedAvg 降低 100x 以上。对于 Llama2-7B (r=8)，每轮上传仅需 ~250KB——即使通过 LoRa（50kbps）也可以在 5 秒内完成。

**异构友好**：不同设备可以使用不同的 LoRA rank——强设备用 r=16（更精确），弱设备用 r=4（更轻量）。聚合时通过投影对齐不同 rank 的 LoRA 参数。

**实验结果**：在 GLUE 基准上，FedPETuning (LoRA, r=8) 达到集中训练 LoRA 性能的 98.5%，而通信量仅为 FedAvg 的 0.8%。

### 6.3 设备端联邦训练的端到端流程

```
每台设备：
1. 加载预训练模型 (INT4 量化)
2. 附加 LoRA 适配器 (FP16, r=4-8)
3. 用本地数据微调 LoRA 参数 (1-5 epochs)
4. 将 LoRA 参数发送给聚合服务器 (~250KB)
5. 接收聚合后的全局 LoRA 参数
6. 更新本地模型

聚合服务器：
1. 收集各设备的 LoRA 参数
2. 加权平均（按数据量 / 设备贡献）
3. 广播更新后的全局 LoRA 参数
```

## 7 前沿进展（2024-2025）

### 7.1 Memlore (2024)：面向内存受限设备的 LoRA

Memlore 提出了"分层 LoRA 训练"——不同时加载所有层的 LoRA 参数，而是逐层加载、训练、释放。这样内存中同一时刻只有一层的 LoRA 参数和激活值，峰值内存大幅降低。代价是训练速度变慢（无法利用层间并行），但使得 2GB 内存的设备也能进行 LoRA 微调。

### 7.2 EdgeMoE (2024)：专家混合模型的设备端训练

MoE（Mixture of Experts）模型在推理时只激活部分专家，天然适合边缘设备的内存约束。EdgeMoE 将未激活的专家参数卸载到外部存储（SD 卡/UFS），只在需要时加载到内存。设备端训练时，只更新被激活的专家的 LoRA 参数，进一步减少训练的计算和内存需求。

### 7.3 设备端训练方法对比

| 方法 | 年份 | 目标硬件 | 最小内存 | 训练策略 | 精度保持 |
|------|------|---------|---------|---------|---------|
| TinyTL | 2020 | MCU (320KB) | 230KB | Lite Residual | 93% |
| PockEngine | 2023 | RPi/Jetson | 800MB | 编译优化 | 99% |
| QLoRA | 2023 | GPU 16-48GB | 12GB (7B) | NF4+LoRA | 99.5% |
| FedPETuning | 2024 | 异构设备 | 视设备 | 联邦+LoRA | 98.5% |
| Memlore | 2024 | 2GB 设备 | 2GB | 分层LoRA | 97% |
| EdgeMoE | 2024 | 手机 8GB | 4GB | MoE+LoRA | 98% |

## 8 技术挑战与展望

### 8.1 训练数据标注

设备端训练需要带标签的本地数据，但边缘设备上的数据通常是无标签的。解决思路包括：半监督学习（用少量标签 + 大量无标签数据）、自监督学习（用数据本身的结构作为监督信号）、主动学习（只标注最不确定的样本）。

### 8.2 训练稳定性

边缘设备的训练可能随时被中断（电池耗尽、设备重启）。需要设计 checkpoint 机制来保存训练进度，以及鲁棒的恢复策略来在中断后继续训练。

### 8.3 灾难性遗忘

设备端训练如果只用新数据微调，模型可能"忘记"预训练阶段学到的通用知识。如何在有限的设备内存中维护"记忆缓冲区"来防止遗忘，是一个与持续学习（见 [边缘持续学习](continual-learning-edge.md)）交叉的研究问题。

## 9 参考文献

- Cai, H., et al. "TinyTL: Reduce Memory, Not Parameters for Efficient On-Device Learning." NeurIPS 2020.
- Lin, J., et al. "On-Device Training Under 256KB Memory." NeurIPS 2022.
- Liang, L., et al. "PockEngine: Sparse and Efficient Fine-tuning in a Pocket." MLSys 2023 (Outstanding Paper Award).
- Hu, E. J., et al. "LoRA: Low-Rank Adaptation of Large Language Models." ICLR 2022.
- Dettmers, T., et al. "QLoRA: Efficient Finetuning of Quantized LLMs." NeurIPS 2023.
- Zhang, J., et al. "FedPETuning: When Federated Learning Meets the Parameter-Efficient Tuning Methods of Foundation Models." ACL Findings 2024.
- Yi, R., et al. "EdgeMoE: Fast On-Device Inference of MoE-based Large Language Models." arXiv 2024.
- Lin, J., et al. "MCUNet: Tiny Deep Learning on IoT Devices." NeurIPS 2020.
- Zaken, E. B., et al. "BitFit: Simple Parameter-efficient Fine-tuning for Transformer-based Masked Language-models." ACL 2022.
