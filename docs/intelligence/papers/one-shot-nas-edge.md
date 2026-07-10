---
schema_version: '1.0'
id: one-shot-nas-edge
title: 神经架构搜索 One-Shot NAS 在边缘的应用
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - nas-edge-models
  - model-compression-edge
  - knowledge-distillation-edge
tags:
- One-Shot NAS
- Supernet
- OFA
- MCUNet
- 硬件感知
- DARTS
- 进化搜索
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 神经架构搜索 One-Shot NAS 在边缘的应用

> **难度**：🟡 中级 | **领域**：NAS、超网络、边缘部署 | **阅读时间**：约 22 分钟

## 日常类比

装修若每种布局都从零砌墙，成本不可承受。One-Shot NAS 像先搭一座「万能毛坯」（超网络, Supernet），墙体与管线预埋了多种隔断可能；试布局时只拆改隔断，不必每次重建。边缘场景还要同时满足延迟、功耗与内存预算——好比装修必须卡在造价与承重之内，于是需要硬件感知搜索，而不是只看「好不好看」（精度）。

## 摘要

本文聚焦权重共享的 One-Shot / Once-for-All 路线：超网络训练、延迟查找表、进化多目标搜索，以及 MCUNet/TinyNAS 在微控制器（MCU）上的约束处理。与总览文 [nas-edge-models](nas-edge-models.md) 互补，本文偏工程流水线。搜索成本与精度数字为公开论文量级[1][2][3][4]。

## 1 NAS 基础与代际

| 要素 | 说明 | 边缘常见选择 |
|------|------|-------------|
| 搜索空间 | 合法结构集合 | MBConv、深度卷积、通道、SE |
| 搜索策略 | 探索方式 | 随机、进化、可微分 |
| 性能评估 | 打分方式 | 超网络共享权重、LUT 延迟、短训 |

| 代际 | 方法 | 成本量级 | 代表 |
|------|------|---------|------|
| 独立训练 | 每架构完整训 | 约数千 GPU-天 | NASNet 等 |
| One-Shot | 权重共享超网络 | 约 1–5 GPU-天 | ENAS、DARTS、SPOS[3][4] |
| Once-for-All | 一训多抽 | 训练一次，多端部署 | OFA、BigNAS[1][7] |
| Zero-Shot | 不训候选 | 常 <1 GPU-hour | Zen-NAS 等[6] |

边缘搜索空间常含深度可分离/MBConv、通道档位、每 stage 层数、核大小、SE 比例等，组合可达约 \(10^{13}\) 量级——必须靠共享权重或代理，而非穷举。

## 2 One-Shot 超网络

核心：一个超网络包含多条候选路径；训练时每个 mini-batch 随机（或按规则）采样子路径更新共享权重；搜索时固定架构编码，用共享权重估计精度，再对优选子网重训或直接抽取（OFA 类）[3]。

单路径 One-Shot（Single Path One-Shot, SPOS）强调每次只激活一条路径，减轻多路径耦合[3]。可微分方法（DARTS）用连续 \(\alpha\) 混合算子，搜索快但离散化落差与跳连优势偏差已知[4]。

**训练要点（实践共识）**：足够长的 epoch；操作均匀采样；可用三明治规则（最大+最小+随机子网）与知识蒸馏稳住小子网；搜索结束后对部署候选做独立验证，不轻信超网络排序。

## 3 硬件感知：多目标与延迟预测

| 目标 | 度量 | 约束示例 |
|------|------|---------|
| 准确率 | Top-1 等 | ≥ 业务阈值 |
| 延迟 | ms/帧 | 如树莓派 <10 ms 量级 |
| 能耗 | mJ/次 | 电池节点严约束 |
| 模型体积 | Flash/磁盘 | MCU 常 <1–2 MB |
| 峰值内存 | SRAM/RAM | MCU 常 <256–512 KB |

延迟查找表（Lookup Table, LUT）：在目标设备上预测「算子×通道×特征图分辨率」延迟，搜索时累加预测，避免每个候选都上板。预测器网络适合更大空间，但有误差带。进化搜索在延迟超标时施加惩罚，维护种群至收敛；最终取帕累托（Pareto）前沿——无人同时更准且更快的集合。

| 方法 | 硬件耦合 | 部署灵活性 | 备注 |
|------|---------|------------|------|
| FBNet 等可微分硬件感知 | 强（延迟进损失） | 每硬件常需重搜 | 手机端经典路线[5] |
| OFA + 进化 | 训练一次，搜索多次 | 高 | 换硬件主要重测 LUT[1] |
| MCUNet/TinyNAS | 极强（含内存规划） | 绑定 MCU 工具链 | 引擎与架构联合[2] |

## 4 OFA 与 MCUNet

**OFA**：弹性深度/宽度/核/分辨率；渐进式收缩先训最大网再引入更小配置；部署时按约束抽子网，公开称常无需重训即可用[1]。仍建议在关键产品上做短微调与量化校准。

**MCUNet**：面向约 256–320 KB SRAM 级 MCU，对比手机/云资源差可达数个数量级[2]。

| 约束维 | MCU 量级 | 手机量级 | 云 GPU 量级 |
|--------|---------|---------|------------|
| 片上内存 | 数百 KB | 数 GB | 数十 GB |
| 存储 | ~1 MB Flash | 很大 | 很大 |
| 功耗 | 约百 mW | 数 W | 数百 W |

| 模型（论文） | SRAM（约） | Flash（约） | ImageNet Top-1（约） | 延迟（约） |
|-------------|-----------|------------|---------------------|-----------|
| MCUNet-5FPS | 293 KB | 741 KB | 60.3% | 200 ms |
| MCUNet-12FPS | 195 KB | 488 KB | 51.5% | 83 ms |
| MobileNetV2 0.35× | 398 KB | 543 KB | 49.7% | 320 ms |

TinyNAS 会按目标 FLOPs/内存缩放搜索空间宽度，使「满足约束且质量代理高」的采样比例上升，避免空间里大量非法点浪费搜索[2]。

## 5 端到端流水线

1. 按硬件缩放搜索空间
2. 目标板构建算子延迟/内存 LUT
3. 训练超网络（单路径 / 渐进收缩）
4. 多目标进化或可微分搜索
5. 优选子网短训或完整重训
6. 量化与编译（TFLite / ONNX / TVM 等）
7. 板级验证延迟、精度、功耗、峰值内存

**何时用 NAS**：多硬件要极致折中 → OFA；MCU 极限 → MCUNet；空间小 → 随机+早停往往够用；只要换数据集微调头，优先手工 EfficientNet/MobileNet，勿为 NAS 而 NAS。

## 6 局限、挑战与可改进方向

### 1. 共享权重排序不可靠

**局限**：超网络上的精度序与独立训练后序常不一致，导致「搜到的最优」上板掉点[3][4]。
**改进**：Pareto 前沿保留 K 个候选完整重训；报告 Kendall 序相关；关键型号禁止跳过重训。

### 2. LUT 与真实流水线偏差

**局限**：算子微基准忽略框架开销、内存带宽、热降频与前后处理。
**改进**：端到端测「相机→后处理」；LUT 加常数开销项；CI 定期重测。

### 3. 与量化/编译耦合不足

**局限**：浮点搜到的结构在 INT8 后瓶颈移位（如 SE、5×5 不被 NPU 支持）。
**改进**：搜索空间只含部署后端支持的算子；搜索阶段用量化感知或 INT8 代理延迟。

### 4. 成本与人才门槛

**局限**：超网络训练与多硬件 LUT 维护成本高，小团队易半途而废。
**改进**：复用公开 OFA 权重；先固定空间做随机搜索基线；工具优先 NNI/厂商 NAS 套件而非自研可微分框架。

## 参考文献

[1] H. Cai et al., "Once-for-All: Train One Network and Specialize it for Efficient Deployment," ICLR, 2020.
[2] J. Lin et al., "MCUNet: Tiny Deep Learning on IoT Devices," NeurIPS, 2020.
[3] Z. Guo et al., "Single Path One-Shot Neural Architecture Search with Uniform Sampling," ECCV, 2020.
[4] H. Liu et al., "DARTS: Differentiable Architecture Search," ICLR, 2019.
[5] B. Wu et al., "FBNet: Hardware-Aware Efficient ConvNet Design via Differentiable NAS," CVPR, 2019.
[6] M. Lin et al., "Zen-NAS: A Zero-Shot NAS for High-Performance Image Recognition," ICCV, 2021.
[7] J. Yu et al., "BigNAS: Scaling Up Neural Architecture Search with Big Single-Stage Models," ECCV, 2020.
[8] M. Tan and Q. Le, "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks," ICML, 2019.
[9] A. Howard et al., "Searching for MobileNetV3," ICCV, 2019.
[10] J. Lin et al., "On-Device Training Under 256KB Memory," NeurIPS, 2022.
[11] M. Tan et al., "MnasNet: Platform-Aware Neural Architecture Search for Mobile," CVPR, 2019.
[12] X. Dong and Y. Yang, "NAS-Bench-201: Extending the Scope of Reproducible Neural Architecture Search," ICLR, 2020.
