---
schema_version: '1.0'
id: differentiable-nas-darts
title: DARTS 可微分架构搜索与边缘模型设计
layer: 5
content_type: paper_reading
difficulty: advanced
reading_time: 24
prerequisites:
  - nas-edge-models
  - one-shot-nas-edge
tags:
  - DARTS
  - NAS
  - 可微分搜索
  - 边缘模型
  - AutoML
  - 模型设计
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "DARTS: Differentiable Architecture Search"
  authors:
    - Hanxiao Liu
    - Karen Simonyan
    - Yiming Yang
  year: 2019
  doi: 10.48550/arXiv.1806.09055
  url: https://arxiv.org/abs/1806.09055
---
# DARTS 可微分架构搜索与边缘模型设计

> 初读范围：本文基于 arXiv 元数据、摘要和公开论文信息建立阅读卡片；尚未完成 PDF 全文逐段复核，因此保持 `UNVERIFIED / UNREVIEWED`。

## 日常类比

传统 NAS 像在一个巨大菜单里逐道点菜试吃：今天试“3x3 卷积 + 残差”，明天试“5x5 卷积 + 池化”，每试一套都要完整训练，非常贵。DARTS 换了一个思路：先把所有菜都摆成自助餐，每道菜前面放一个可学习的旋钮，训练时同时调模型权重和旋钮大小。最后把旋钮最大的菜留下，得到最终架构。

这就是“可微分”的直觉：把原本离散的选项变成连续权重，让梯度下降也能参与搜索。

## 论文信息

| 字段 | 内容 |
| --- | --- |
| 标题 | DARTS: Differentiable Architecture Search |
| 作者 | Hanxiao Liu, Karen Simonyan, Yiming Yang |
| 发表 | ICLR 2019 |
| arXiv | https://arxiv.org/abs/1806.09055 |
| DOI | 10.48550/arXiv.1806.09055 |
| 代码 | https://github.com/quark0/darts |

## 1 研究动机

早期神经架构搜索（Neural Architecture Search, NAS）常用强化学习或进化算法。它们能找到好结构，但代价很高：大量候选架构要单独训练，搜索成本可达数百到数千 GPU-天量级。

DARTS 关注的问题是：能不能把架构搜索变成一个可用梯度优化的问题，让搜索成本从“试很多完整模型”降到“训练一个连续松弛的超网络”？

## 2 核心机制

### 2.1 连续松弛

在一条边上，传统 NAS 会从候选操作集合中选一个，例如：

- 3x3 separable convolution
- 5x5 separable convolution
- max pooling
- skip connection
- zero

DARTS 不直接选，而是为每个候选操作分配一个架构参数 \(\alpha\)，用 softmax 加权：

\[
\bar{o}(x) = \sum_{o \in O} \frac{\exp(\alpha_o)}{\sum_{o' \in O}\exp(\alpha_{o'})} o(x)
\]

这样，架构参数 \(\alpha\) 和模型权重 \(w\) 都能通过梯度更新。

### 2.2 双层优化

DARTS 把训练分成两类目标：

| 参数 | 用什么数据优化 | 含义 |
| --- | --- | --- |
| 模型权重 \(w\) | 训练集 | 让当前超网络能完成任务 |
| 架构参数 \(\alpha\) | 验证集 | 让架构选择能泛化 |

这对应双层优化：内层训权重，外层调架构。论文还提出一阶近似以降低二阶梯度成本。

### 2.3 离散化

搜索结束后，连续超网络不能直接作为最终架构使用。DARTS 会在每条边上保留 \(\alpha\) 最大的操作，再按 cell 结构导出离散网络，然后重新训练最终模型。

## 3 为什么和边缘模型有关

边缘模型设计需要在准确率、延迟、内存和功耗之间取舍。手工设计 MobileNet / EfficientNet 已经很强，但不同硬件的最优结构常常不同。

DARTS 的价值是提供一个低成本 NAS 基础框架：

| 边缘需求 | DARTS 可借鉴点 |
| --- | --- |
| 搜索成本低 | 不需要每个候选架构完整训练 |
| 可扩展候选操作 | 可加入 depthwise conv、skip、轻量 attention |
| 可加约束 | 可在目标中叠加 FLOPs、延迟或内存代理 |
| 可作为后续方法地基 | ProxylessNAS、FBNet 等硬件感知方法吸收了类似连续搜索思想 |

原始 DARTS 并不是硬件感知 NAS。要用于 IoT，需要把目标从单纯验证准确率扩展为“准确率 + 设备延迟/内存约束”。

## 4 论文报告贡献

| 贡献 | 说明 |
| --- | --- |
| 可微分搜索空间 | 把离散架构选择松弛成连续参数 |
| 搜索效率提升 | 相比早期 RL / Evolution NAS，搜索速度快很多[1] |
| CNN 与 RNN 同框架 | 在图像分类和语言建模上都验证 |
| 开源实现 | 提供代码便于复现和改进 |

论文摘要指出，DARTS 能在 CIFAR-10、ImageNet、Penn Treebank、WikiText-2 等任务上找到高性能架构，并比非可微搜索方法快几个数量级[1]。

## 5 已知局限

### 5.1 连续松弛和离散架构有落差

搜索时所有操作以 softmax 混合运行，部署时只保留少数操作。搜索阶段表现好的混合结构，不一定离散化后仍最优。

### 5.2 容易偏向 skip connection

后续研究指出，DARTS 搜索可能过度选择跳连，导致退化架构。原因包括优化不稳定、验证损失曲面和候选操作竞争不公平。

### 5.3 FLOPs 不等于真实延迟

原始 DARTS 更关注准确率。边缘设备上的真实瓶颈常是内存访问、算子支持、并行度和 kernel 实现。直接把 DARTS 搜出的结构部署到手机或 MCU，可能不是最快。

## 6 和现有站内内容的关系

- `nas-edge-models`：给出 NAS 全景和硬件感知路线，DARTS 是其中的可微分代表。
- `one-shot-nas-edge`：DARTS 的超网络思想与一次训练多架构共享权重有相通之处。
- `model-compression-edge`：NAS 可以和剪枝、量化、蒸馏组合，形成完整边缘模型优化流水线。

## 7 初读结论

DARTS 的关键贡献不是“直接给 IoT 一个可部署模型”，而是把 NAS 从昂贵黑盒搜索推进到可梯度优化的框架。对边缘智能来说，它提供了可扩展的搜索工具箱；但真正落地还必须引入硬件实测延迟、内存约束和目标设备算子支持，否则搜索到的“理论好模型”可能在板端并不好用。

## 后续核验清单

- 从 PDF 抽取 CIFAR-10、ImageNet、PTB 的具体结果和搜索成本。
- 对比 DARTS、ProxylessNAS、FBNet 的硬件约束建模差异。
- 补充 DARTS 退化问题的后续论文证据。
- 在 `nas-edge-models` 中建立从 DARTS 到硬件感知 NAS 的交叉链接。

## 参考文献

[1] H. Liu, K. Simonyan, and Y. Yang, "DARTS: Differentiable Architecture Search," ICLR, 2019. arXiv:1806.09055.
