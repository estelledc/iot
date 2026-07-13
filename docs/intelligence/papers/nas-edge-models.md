---
schema_version: '1.0'
id: nas-edge-models
title: NAS 自动化边缘模型设计：让机器设计机器
layer: 5
content_type: technical_analysis
difficulty: advanced
reading_time: 26
prerequisites:
  - model-compression-edge
  - one-shot-nas-edge
  - knowledge-distillation-edge
tags:
- NAS
- 硬件感知
- Once-for-All
- MCUNet
- MobileNet
- EfficientNet
- DARTS
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# NAS 自动化边缘模型设计：让机器设计机器

> **难度**：🟡 进阶 | **领域**：神经架构搜索、边缘模型设计 | **阅读时间**：约 26 分钟

## 日常类比

给手机挑相机镜头：焦距、光圈、镜片层数、镀膜组合构成天文数字的方案。人工设计师凭经验试几套；神经架构搜索（Neural Architecture Search, NAS）像自动试镜台——在给定重量与成本（延迟、内存、功耗）下，系统化试出更合适的镜头组合。边缘场景还要求同一套方法能适配手机、开发板与微控制器（Microcontroller Unit, MCU）等碎片化硬件。

## 摘要

本文梳理边缘友好手工模型（MobileNet / EfficientNet）如何演化为搜索原语，再对比强化学习、可微分与单次训练（Once-for-All）等 NAS 路线，以及 MCUNet 等极端约束实践。文中 ImageNet 精度、延迟与 GPU-天等数字来自公开论文量级，跨硬件差异大，部署须在目标板上实测[1][4][6][7]。

## 1 从手工设计到自动搜索

设计边缘模型要回答：层数、通道、卷积核、是否残差、激活函数等。约 20 层、每层约 10 种配置时，组合空间可达 \(10^{20}\) 量级——人类只能覆盖极小子集。更关键的是：**最优架构依赖硬件**。浮点运算次数（Floating Point Operations, FLOPs）低的深度卷积，在部分图形处理器（Graphics Processing Unit, GPU）上可能因并行度不足反而更慢[5]。

NAS 的目标：在给定硬件约束下，用算法搜索可部署架构，而非只优化 FLOPs 代理指标。

## 2 手工设计里程碑

### 2.1 MobileNet 家族

**MobileNetV1**：深度可分离卷积（Depthwise Separable Convolution）将标准卷积拆为深度卷积 + 逐点卷积，公开报告称 3×3、百通道量级下计算量可降到约 1/8–1/9，精度损失通常为数个百分点量级[1]。

**MobileNetV2**：倒残差块（Inverted Residual Block）采用「窄-宽-窄」：1×1 扩展 → 深度卷积 → 1×1 压缩；线性瓶颈（Linear Bottleneck）在低维处不加 ReLU，减轻信息丢失[2]。

**MobileNetV3**：用 MnasNet 搜索基础结构，再经 NetAdapt 微调；引入 h-swish 与 Squeeze-and-Excitation（SE）通道注意力[3]。

### 2.2 EfficientNet 家族

EfficientNet 用复合缩放（Compound Scaling）同时调深度、宽度与分辨率；公开给出 \(\alpha\approx1.2,\beta\approx1.1,\gamma\approx1.15\) 且 \(\alpha\cdot\beta^{2}\cdot\gamma^{2}\approx2\) 的网格搜索结果。B0 由 NAS 得到基础结构；B0 在 ImageNet 上约 77.1% Top-1，参数量与 FLOPs 相对 ResNet-50 约为约 1/5 与约 1/11[4]。EfficientNetV2 在浅层用 Fused-MBConv，并采用渐进分辨率训练，公开称训练速度可提升数倍至约一个数量级[11]。

### 2.3 演进对比（公开基准量级）

| 模型 | 年份 | 参数量（约） | FLOPs（约） | ImageNet Top-1（约） | 关键创新 |
|------|------|-------------|----------------|---------------------|---------|
| VGG-16 | 2014 | 138M | 15.5G | 71.5% | 大而慢基准 |
| ResNet-50 | 2015 | 25.6M | 4.1G | 76.1% | 残差连接 |
| MobileNetV1 | 2017 | 4.2M | 569M | 70.6% | 深度可分离 |
| MobileNetV2 | 2018 | 3.4M | 300M | 72.0% | 倒残差 |
| MobileNetV3-L | 2019 | 5.4M | 219M | 75.2% | NAS + h-swish |
| EfficientNet-B0 | 2019 | 5.3M | 390M | 77.1% | 复合缩放 |
| EfficientNetV2-S | 2021 | 21.5M | 8.4G | 83.9% | Fused-MBConv |

数值摘自各论文报告，训练配方与评估协议不完全一致，不宜直接当排行榜[1][2][3][4][11]。

## 3 NAS 三要素与搜索策略

| 要素 | 含义 | 常见选择 |
|------|------|---------|
| 搜索空间 | 合法架构集合 | 卷积类型、通道、连接方式 |
| 搜索策略 | 如何探索 | 强化学习、进化、梯度、随机 |
| 评估策略 | 如何打分 | 完整训练、权重共享、预测器 |

| 策略 | 代表 | 搜索成本量级 | 质量倾向 |
|------|------|-------------|----------|
| 强化学习 | NASNet | 约数千 GPU-天 | 高但极贵[10] |
| 进化算法 | AmoebaNet | 约数千 GPU-天 | 高但极贵 |
| 可微分 | DARTS | 约数 GPU-天 | 中–高[9] |
| 单路径 | Single-Path NAS | 约 1 GPU-天量级 | 中 |
| 预测器引导 | BANANAS 等 | 约 1 GPU-天量级 | 中–高 |

早期 NASNet 类成本使中小团队难以负担；DARTS（Differentiable Architecture Search）将离散选择松弛为连续架构参数 \(\alpha\)，用梯度同时优化权重与架构，公开称成本可降约两个数量级[9][10]。

**DARTS 流程**：构建含多候选操作的超网络 → softmax 加权各操作 → 联合训练权重 \(w\) 与 \(\alpha\) → 每条边保留最大 \(\alpha\) 的操作。偏差与离散化落差仍是已知问题，见局限节。

## 4 硬件感知 NAS

FLOPs 不能可靠代理真实延迟：深度卷积 FLOPs 低但部分 GPU 上更慢；5×5 相对 3×3 的实测延迟比常高于 FLOPs 比[5]。硬件感知 NAS 以目标设备延迟/能耗为约束。

**MnasNet**：在 Pixel 上实测延迟，奖励形如 \(\mathrm{ACC}(a)\times[\mathrm{LAT}(a)/T]^{w}\)（\(w\) 为负指数权重），分层搜索空间允许不同层不同算子。公开报告约 75.2% Top-1、约 78 ms（Pixel），相对同精度手工模型约 1.8× 加速；该结构亦成为 EfficientNet-B0 基础[5]。

| 延迟评估方式 | 准确度倾向 | 速度 | 适用 |
|-------------|-----------|------|------|
| 每次实测 | 最高 | 慢，需目标硬件 | 小空间 |
| 查找表（LUT） | 通常很高 | 快 | 规则空间 |
| 神经网络预测器 | 中–高 | 最快 | 大空间 |
| FLOPs 代理 | 常偏低相关 | 最快 | 粗筛 |

## 5 Once-for-All：一次训练，多端部署

Once-for-All（OFA）训练一个弹性超网络，部署时按硬件约束抽取子网，避免「每种硬件重训一遍」[6]。弹性维度包括深度、宽度、核大小与输入分辨率，组合空间可达约 \(10^{19}\) 量级。训练用渐进式收缩（Progressive Shrinking）：先训最大网，再逐步支持更小子配置并共享权重。

公开流程量级：超网络训练约数十 GPU-小时；目标机测延迟表后，进化搜索约数小时（可在中央处理器上）；抽出子网即可部署，无需再训[6]。

| 目标硬件（论文设定） | 延迟约束（约） | Top-1（约） | vs MobileNetV3（约） |
|---------------------|---------------|------------|---------------------|
| Samsung S7 Edge | 20 ms | 76.9% | +1.7% |
| Google Pixel 1 | 29 ms | 77.5% | +2.3% |
| Samsung Note 10 | 15 ms | 76.3% | +1.1% |
| Jetson TX2 GPU | 8 ms | 78.1% | +2.9% |

子网均来自同一超网络；换芯片代际后须重测 LUT，不可直接复用旧延迟表。

## 6 MCUNet：微控制器级联合搜索

MCUNet 面向约 256 KB SRAM、约 1 MB Flash 的 MCU：MobileNetV2 峰值激活可达约 MB 级，远超 SRAM[7]。方法把搜索扩展到「架构 + 推理引擎」：

- **TinyNAS**：在更极端配置（更小扩展比、更少通道等）下搜索，并约束峰值 SRAM。
- **TinyEngine**：算子融合、张量生命周期规划、生成专用 C 代码，削减框架开销。

| 平台（论文） | SRAM | Flash | 任务 | 精度（约） | vs TFLite Micro（约） |
|-------------|------|-------|------|-----------|----------------------|
| STM32F412 | 256KB | 1MB | Visual Wake Words | 88.1% | +16.5% |
| STM32F746 | 320KB | 1MB | ImageNet 子集 | 70.7% | +13.2% |
| STM32H743 | 512KB | 2MB | ImageNet 子集 | 74.6% | +8.7% |

MCUNetV2 用基于图像块（patch）的推理降低峰值内存，代价是多次前向、延迟上升[8]。MCUNetV3 / TinyEngine 2.0 进一步探索 MCU 上迁移学习，与设备端训练交叉[见 on-device-training]。

## 7 前沿方向（公开进展）

| 方向 | 思路 | 注意 |
|------|------|------|
| LLM 辅助 NAS | 用大模型生成/迭代候选架构描述 | 可复现性与成本依赖 API；增益需对照实验 |
| Zero-Shot / 零成本代理 | 用拓扑或梯度流指标不训网打分（如 Zen-Score）[12] | 代理与真实精度相关不稳定 |
| NPU/FPGA 联合 | 把数据流、算子映射纳入搜索 | 工具链碎片化，迁移成本高 |

## 8 局限、挑战与可改进方向

### 1. 搜索空间偏见

**局限**：空间多由 MobileNet 式 MBConv 等人工原语构成，难发现真正「出圈」结构；空间过大则评估噪声淹没信号。
**改进**：先用零成本代理或随机采样做空间裁剪；为新加速器单独扩充算子原语；报告空间定义与采样覆盖率。

### 2. 超网络排序与真实精度落差

**局限**：权重共享使子网排序与独立重训后的排序不一致；DARTS 离散化后性能常掉点[9]。
**改进**：对 Pareto 前沿候选做短训或完整重训验证；用渐进收缩/三明治规则减轻干扰；部署前强制目标硬件实测。

### 3. 硬件迁移与 LUT 过时

**局限**：延迟表绑定具体 SoC、驱动与运行时；换代或换框架后「最优子网」可能不再最优。
**改进**：抽象「操作×分辨率×通道」测量流水线；CI 中定期重测 LUT；多目标同时记录延迟、能耗与峰值内存。

### 4. 成本与可复现

**局限**：即便 One-Shot，超网络训练仍需可观 GPU；论文数字依赖特定数据集与种子。
**改进**：优先复用公开 OFA/MCUNet 权重再在自有约束下搜索；固定种子与评估协议；小团队可从预训练超网络 + 进化搜索起步，而非从零 RL-NAS。

## 参考文献

[1] A. G. Howard et al., "MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications," arXiv:1704.04861, 2017.
[2] M. Sandler et al., "MobileNetV2: Inverted Residuals and Linear Bottlenecks," CVPR, 2018.
[3] A. Howard et al., "Searching for MobileNetV3," ICCV, 2019.
[4] M. Tan and Q. V. Le, "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks," ICML, 2019.
[5] M. Tan et al., "MnasNet: Platform-Aware Neural Architecture Search for Mobile," CVPR, 2019.
[6] H. Cai et al., "Once-for-All: Train One Network and Specialize it for Efficient Deployment," ICLR, 2020.
[7] J. Lin et al., "MCUNet: Tiny Deep Learning on IoT Devices," NeurIPS, 2020.
[8] J. Lin et al., "MCUNetV2: Memory-Efficient Patch-based Inference for Tiny Deep Learning," NeurIPS, 2021.
[9] H. Liu, K. Simonyan, and Y. Yang, "DARTS: Differentiable Architecture Search," ICLR, 2019.
[10] B. Zoph et al., "Learning Transferable Architectures for Scalable Image Recognition," CVPR, 2018.
[11] M. Tan and Q. V. Le, "EfficientNetV2: Smaller Models and Faster Training," ICML, 2021.
[12] M. Lin et al., "Zen-NAS: A Zero-Shot NAS for High-Performance Image Recognition," ICCV, 2021.
