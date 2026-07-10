---
schema_version: '1.0'
id: nas-edge-models
title: NAS 自动化边缘模型设计：让机器设计机器
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
# NAS 自动化边缘模型设计：让机器设计机器

> 难度：🟡 进阶 | 前置知识：了解 CNN 基本结构（卷积、池化、残差连接）和模型部署概念

## 论文信息

- **主题**：神经架构搜索（Neural Architecture Search, NAS）在边缘模型设计中的应用——从人工设计到自动化发现最优的边缘 AI 模型
- **核心问题**：MobileNet 为什么长这样？EfficientNet 的缩放系数怎么来的？能不能让算法自动找到更好的架构？
- **涵盖范围**：手工设计演进 (MobileNet → EfficientNet) → NAS 基础 → 硬件感知 NAS → Once-for-All → MCUNet (2019-2024)

## 1 从手工设计到自动搜索

### 1.1 手工设计的困境

设计一个边缘 AI 模型需要回答无数个"选择题"：用几层卷积？每层多少通道？卷积核多大？要不要残差连接？在哪里放池化层？Activation 用 ReLU 还是 Swish？

这些选择构成了一个庞大的设计空间——光是一个 20 层的 CNN，如果每层有 10 种可能的配置，就有 10^20 种可能的架构。人类设计者通过经验和直觉在这个空间中"探索"，但能覆盖的范围极为有限。

而且，"最好的架构"取决于目标硬件。在 GPU 上最快的架构在 CPU 上不一定最快，在 NPU 上可能又不一样。这意味着每更换一种硬件，可能就需要重新设计模型——这对边缘 AI 的碎片化硬件生态（Jetson、Raspberry Pi、手机 SoC、MCU、FPGA...）来说是不可承受的。

NAS 的愿景是：**用算法代替人类设计者，在给定硬件约束下自动搜索最优的神经网络架构**。

### 1.2 边缘模型的设计空间演进

在理解 NAS 之前，先回顾手工设计的边缘模型是如何演进的——因为 NAS 的搜索空间正是基于这些人工积累的设计原语。

## 2 手工设计里程碑

### 2.1 MobileNet 家族

**MobileNetV1 (2017, Google)**：提出深度可分离卷积（Depthwise Separable Convolution），将标准卷积分解为深度卷积（Depthwise）+ 逐点卷积（Pointwise）。

标准卷积的计算量：D_K × D_K × C_in × C_out × D_F × D_F
深度可分离卷积的计算量：D_K × D_K × C_in × D_F × D_F + C_in × C_out × D_F × D_F

以 3×3 卷积、128 通道为例，计算量降低为原来的 1/8 到 1/9，而精度仅下降 1-2%。

**MobileNetV2 (2018, Google)**：引入倒残差块（Inverted Residual Block, IRB）。传统残差块是"宽-窄-宽"（先压缩再还原），IRB 是"窄-宽-窄"——先用 1×1 卷积扩展通道（expansion ratio 通常为 6），再用 3×3 深度卷积处理，最后用 1×1 卷积压缩回来。

为什么倒过来？因为深度卷积的计算量与通道数成正比，在"宽"的中间层用深度卷积（而非标准卷积）可以保持特征的丰富性，同时控制计算量。线性瓶颈（Linear Bottleneck）——最后的 1×1 卷积后不加 ReLU，因为在低维空间中 ReLU 会丢失信息。

**MobileNetV3 (2019, Google)**：首次引入 NAS——使用 MnasNet 搜索框架搜索出基础架构，再用 NetAdapt 进行逐层微调。引入了 h-swish 激活函数（Swish 的计算友好版本）和 SE 模块（Squeeze-and-Excitation，通道注意力）。

### 2.2 EfficientNet 家族

**EfficientNet-B0 到 B7 (2019, Google)**：核心贡献是复合缩放策略（Compound Scaling）。传统做法是单独增加深度（更多层）、宽度（更多通道）或分辨率（更大输入）。EfficientNet 证明，三者按一定比例同时缩放效果最好。

具体来说，设深度缩放系数为 α，宽度缩放系数为 β，分辨率缩放系数为 γ，则约束条件为 α × β² × γ² ≈ 2（每次缩放计算量翻倍）。通过网格搜索确定的最优比例为 α=1.2, β=1.1, γ=1.15。

B0 是用 NAS 搜索出的基础架构（~5.3M 参数），B1-B7 是按复合缩放逐步放大的变体。EfficientNet-B0 在 ImageNet 上达到 77.1% Top-1（与 ResNet-50 相当），但参数量和 FLOPs 分别只有后者的 1/5 和 1/11。

**EfficientNetV2 (2021)**：引入 Fused-MBConv（在网络浅层用标准卷积替代深度可分离卷积，因为浅层通道数少时标准卷积更快）和渐进式训练策略（训练初期用小分辨率，逐步增大），训练速度提升 5-11x。

### 2.3 手工设计演进对比

| 模型 | 年份 | 参数量 | FLOPs | ImageNet Top-1 | 关键创新 |
|------|------|--------|-------|---------------|---------|
| VGG-16 | 2014 | 138M | 15.5G | 71.5% | 基准（大而慢） |
| ResNet-50 | 2015 | 25.6M | 4.1G | 76.1% | 残差连接 |
| MobileNetV1 | 2017 | 4.2M | 569M | 70.6% | 深度可分离卷积 |
| MobileNetV2 | 2018 | 3.4M | 300M | 72.0% | 倒残差块 |
| MobileNetV3-L | 2019 | 5.4M | 219M | 75.2% | NAS + h-swish |
| EfficientNet-B0 | 2019 | 5.3M | 390M | 77.1% | NAS + 复合缩放 |
| EfficientNetV2-S | 2021 | 21.5M | 8.4G | 83.9% | Fused-MBConv |

## 3 NAS 基础

### 3.1 NAS 的三要素

每个 NAS 方法都需要定义三个组件：

**搜索空间（Search Space）**：定义"什么样的架构是合法的"——可以用哪些操作（3×3 conv、5×5 conv、skip connection 等）、怎么连接（顺序、残差、密集连接等）、有多少层等。搜索空间越大，可能找到更好的架构，但搜索成本也越高。

**搜索策略（Search Strategy）**：如何在搜索空间中高效探索——随机搜索、强化学习、进化算法、梯度优化等。

**评估策略（Evaluation Strategy）**：如何评估一个候选架构的好坏——完整训练再测试（准确但极慢）、权重共享（快速但有偏差）、性能预测器（最快但需要额外训练预测模型）。

### 3.2 搜索策略对比

| 策略 | 代表工作 | 搜索效率 | 搜索成本 | 搜索质量 | 原理 |
|------|---------|---------|---------|---------|------|
| 强化学习 | NASNet (2018) | 低 | ~2000 GPU-days | 高 | 控制器生成架构，准确率作为奖励 |
| 进化算法 | AmoebaNet (2019) | 低 | ~3150 GPU-days | 高 | 种群进化，适应度筛选 |
| 可微分搜索 | DARTS (2019) | 高 | ~4 GPU-days | 中-高 | 架构选择连续松弛，梯度优化 |
| 单路径搜索 | Single-Path NAS (2020) | 高 | ~1 GPU-day | 中 | 超网络中随机采样路径 |
| 预测器引导 | BANANAS (2021) | 高 | ~1 GPU-day | 中-高 | 训练精度预测器引导搜索 |

早期 NAS（如 NASNet）需要数千 GPU-天的搜索成本——约等于在 500 张 V100 上跑 4 天，以当时的云价格约 $15,000-50,000。这使得 NAS 只有大公司才能负担。DARTS 的出现是一个转折点——将搜索成本降低了 500 倍。

### 3.3 DARTS：可微分架构搜索

DARTS (Differentiable Architecture Search, 2019, ICLR) 的核心创新是将离散的架构选择问题转化为连续优化问题。

传统 NAS 需要评估每个候选架构的性能——这是一个离散选择问题，只能用强化学习或进化算法等黑盒优化方法。DARTS 的做法是：

1. 构建一个"超网络"（supernet），每两个节点之间有所有可能的操作（3×3 conv、5×5 conv、skip、none 等）
2. 为每个操作分配一个可学习的权重 α（架构参数），用 softmax 归一化
3. 将超网络当作一个正常的神经网络训练，同时优化模型权重 w 和架构参数 α
4. 训练完成后，保留每条边上权重最大的操作，得到最终架构

因为 α 是连续的（可以求梯度），架构搜索变成了一个标准的梯度下降优化问题——搜索成本从数千 GPU-天降到几个 GPU-天。

## 4 硬件感知 NAS

### 4.1 为什么需要硬件感知

传统 NAS 的优化目标是精度最大化，约束条件是 FLOPs（计算量）。但 FLOPs 并不能准确反映模型在真实硬件上的延迟——不同操作在不同硬件上的效率差异巨大。

例如：深度卷积的 FLOPs 很低，但在某些 GPU 上因为并行度不够反而比标准卷积更慢。3×3 卷积在 NVIDIA GPU 的 cuDNN 中有高度优化的实现，但 5×5 卷积没有，所以 5×5 的实际延迟可能是 3×3 的 3-4 倍（而非 FLOPs 比例的 2.8 倍）。

硬件感知 NAS 直接以目标硬件上的实际延迟作为约束条件，而非 FLOPs 这个不准确的代理指标。

### 4.2 MnasNet (2019, CVPR)

MnasNet 是 Google 提出的首个硬件感知 NAS 方法，直接以 Pixel 手机上的推理延迟作为优化目标。

**多目标优化**：奖励函数为 ACC(a) × [LAT(a) / T]^w，其中 ACC 是精度，LAT 是延迟，T 是目标延迟，w 是权重指数（w=-0.07 到 -0.15）。这个奖励函数使得搜索在精度和延迟之间找到帕累托最优。

**分层搜索空间**：不同层可以使用不同的操作和配置——浅层可能用 3×3 MBConv（特征图大，需要控制计算），深层可能用 5×5 MBConv（特征图小，可以用更大卷积核提取更丰富的特征）。

**结果**：MnasNet 在 ImageNet 上达到 75.2% Top-1，延迟 78ms (Pixel 手机)，比同精度的手工设计模型快 1.8x。这个架构后来成为 EfficientNet-B0 的基础。

### 4.3 延迟预测器 vs 实际测量

| 评估方式 | 准确度 | 速度 | 适用场景 |
|---------|--------|------|---------|
| 每次实际测量 | 100% | 慢（需要目标硬件） | 小搜索空间 |
| 延迟查找表 | >95% | 快（提前测量各操作） | 规则搜索空间 |
| 延迟预测器（NN） | 90-95% | 最快（无需硬件） | 大搜索空间 |
| FLOPs 代理 | 60-80% | 最快 | 粗估计 |

## 5 Once-for-All：一次训练，到处部署

### 5.1 核心问题

传统 NAS 的问题是：每更换一种目标硬件，就需要重新搜索+训练一个模型。如果有 10 种硬件平台，就需要做 10 次 NAS——每次数天的 GPU 时间。

Once-for-All (OFA, 2020, ICLR, MIT Han Lab) 的解决思路：**只训练一个巨大的"超网络"（OFA Network），这个超网络包含了所有可能的子网络。部署时只需要搜索出适合目标硬件的子网络并提取出来，无需额外训练。**

### 5.2 设计原理

OFA Network 支持四个维度的弹性：

- **深度弹性**：每个 stage 可以有 2/3/4 个残差块
- **宽度弹性**：每层的通道数可以从 {0.65x, 0.8x, 1.0x} 中选择
- **核大小弹性**：卷积核大小可以是 3/5/7
- **分辨率弹性**：输入分辨率从 128 到 224，步长 4

这四个维度的组合产生了 ~10^19 种可能的子网络——一个超网络"包含"了海量的候选架构。

**训练方式——渐进式收缩（Progressive Shrinking）**：
1. 先训练最大的网络（全深度、全宽度、最大核）
2. 然后逐步支持更小的配置——在训练时随机采样子网络进行前向/反向传播
3. 大网络的权重被共享给小子网络（知识蒸馏思想）

### 5.3 部署流程

```
OFA Network（一次训练，约 40 GPU-hours）
    ↓ 在目标硬件上测量延迟表
    ↓ 进化算法搜索（~1-2小时，在CPU上）
    ↓ 提取最优子网络
目标设备部署（无需额外训练）
```

**实验结果**：在 ImageNet 上，OFA 搜索到的子网络在各种硬件上的表现：

| 目标硬件 | 延迟约束 | Top-1 精度 | 参数量 | vs MobileNetV3 |
|---------|---------|-----------|--------|--------------|
| Samsung S7 Edge | 20ms | 76.9% | 6.1M | +1.7% |
| Google Pixel 1 | 29ms | 77.5% | 6.3M | +2.3% |
| Samsung Note 10 | 15ms | 76.3% | 5.8M | +1.1% |
| Jetson TX2 GPU | 8ms | 78.1% | 7.2M | +2.9% |

所有这些不同的子网络都是从同一个 OFA 超网络中提取的，没有做任何额外训练。

## 6 MCUNet：为微控制器量身定制

### 6.1 极端约束

MCUNet (2020, NeurIPS, MIT Han Lab) 面对的是边缘 AI 的终极挑战——在 256KB SRAM、1MB Flash 的微控制器上运行图像分类模型。

这比手机/Jetson 的约束严格了 100-1000 倍。在这种约束下，MobileNetV2 都太大了——它的峰值激活值需要 ~1.3MB，远超 256KB SRAM。

### 6.2 联合搜索

MCUNet 的核心创新是将 NAS 的搜索空间扩展到整个推理系统——不仅搜索模型架构，还搜索推理引擎的执行策略（内存分配、执行顺序）。

**TinyNAS（架构搜索）**：在 OFA 搜索空间的基础上，增加了更极端的配置选项（如 1×1 卷积替代 3×3、更小的扩展比、更少的通道）。搜索目标不仅是精度和延迟，还加入了峰值 SRAM 占用约束。

**TinyEngine（推理引擎）**：为搜索到的架构生成专用的推理代码。通过算子融合、内存规划（提前计算每个时刻的 SRAM 使用并优化张量的生命周期管理）、代码生成（直接生成 C 代码，避免框架开销），最大限度地压缩运行时内存。

### 6.3 实验结果

| 平台 | SRAM | Flash | 任务 | 精度 | vs TFLite Micro |
|------|------|-------|------|------|----------------|
| STM32F412 | 256KB | 1MB | VWW (Visual Wake Words) | 88.1% | +16.5% |
| STM32F746 | 320KB | 1MB | ImageNet-子集 | 70.7% | +13.2% |
| STM32H743 | 512KB | 2MB | ImageNet-子集 | 74.6% | +8.7% |

MCUNet 首次在商用 MCU 上实现了 ImageNet 级别的图像分类——此前被认为是不可能的。

### 6.4 MCUNet 的后续演进

**MCUNetV2 (2021)**：引入"patch-based inference"——不一次处理完整图像，而是将图像分成小块（patch）逐块处理。每次只有一个 patch 在 SRAM 中，峰值内存降低到 patch 大小对应的内存需求。代价是推理延迟增加（需要多次前向传播），但使得更大的模型和更高分辨率的输入在相同 SRAM 约束下成为可能。

**MCUNetV3 / TinyEngine 2.0 (2023)**：将设备端训练引入 MCU 平台（参见 [设备端训练](on-device-training.md)），实现了在 256KB SRAM 上的迁移学习——这是此前完全不可能的。

## 7 前沿进展（2024-2025）

### 7.1 LLM 辅助 NAS

利用大语言模型来指导 NAS 搜索——将架构描述为文本，让 LLM 根据之前的搜索历史和硬件约束生成新的候选架构。GENIUS (2024) 使用 GPT-4 作为"架构设计助手"，通过自然语言交互迭代优化架构，搜索效率比传统方法提升 3-5x。

### 7.2 Zero-Shot NAS

不训练任何候选架构，仅通过分析架构的拓扑属性（如层间相关性、梯度流特征）来预测其性能。ZEN-NAS (2024) 通过计算每个架构的"禅得分"（Zen-Score，一种基于高斯复杂度的指标），在几秒内评估数千个候选架构，搜索成本接近于零。

### 7.3 面向 NPU/FPGA 的硬件感知 NAS

随着越来越多的边缘设备配备专用 AI 加速器（如 Qualcomm Hexagon DSP、Samsung NPU、FPGA），NAS 需要针对这些非标准硬件的执行特性（如定制数据流、算子映射、内存层级）进行优化。NA-NAS (2024) 将 NPU 的数据流编译策略纳入搜索空间，实现了架构-编译联合优化。

## 8 参考文献

- Howard, A. G., et al. "MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications." arXiv 2017.
- Sandler, M., et al. "MobileNetV2: Inverted Residuals and Linear Bottlenecks." CVPR 2018.
- Howard, A., et al. "Searching for MobileNetV3." ICCV 2019.
- Tan, M., Le, Q. V. "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks." ICML 2019.
- Tan, M., et al. "MnasNet: Platform-Aware Neural Architecture Search for Mobile." CVPR 2019.
- Cai, H., et al. "Once-for-All: Train One Network and Specialize it for Efficient Deployment." ICLR 2020.
- Lin, J., et al. "MCUNet: Tiny Deep Learning on IoT Devices." NeurIPS 2020.
- Lin, J., et al. "MCUNetV2: Memory-Efficient Patch-based Inference for Tiny Deep Learning." NeurIPS 2021.
- Liu, H., Simonyan, K., Yang, Y. "DARTS: Differentiable Architecture Search." ICLR 2019.
- Zoph, B., et al. "Learning Transferable Architectures for Scalable Image Recognition (NASNet)." CVPR 2018.
- Tan, M., Le, Q. V. "EfficientNetV2: Smaller Models and Faster Training." ICML 2021.
- Lin, M., et al. "Zen-NAS: A Zero-Shot NAS for High-Performance Image Recognition." ICCV 2021.
