---
schema_version: '1.0'
id: cascaded-pruning-on-device-llm-iiot
title: 工业 IoT 端侧 LLM 推理的级联多粒度剪枝
layer: 5
content_type: paper_reading
difficulty: frontier
reading_time: 20
prerequisites:
  - model-compression-edge
  - transformer-edge-deployment
  - edge-large-ai-models-iot-applications
tags:
  - Industrial IoT
  - LLM Compression
  - Pruning
  - On-Device Inference
  - Edge AI
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Cascaded Multi-Granularity Pruning for On-Device LLM Inference in Industrial IoT"
  authors:
    - Jinghan Wang
    - Yanjun Chen
    - Wei Zhang
    - Xiaotong Huang
    - Tianchen Liu
    - Gaoliang Peng
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2606.26861v1
---
# 工业 IoT 端侧 LLM 推理的级联多粒度剪枝

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、剪枝算法复现或工业设备指标核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

工业 IoT 设备要在现场运行 LLM，通常比手机和服务器更受限。普通结构化剪枝在高压缩率下可能一下子把模型能力剪坏。论文提出级联多粒度剪枝，按层、注意力头和前馈网络等粒度逐步压缩。

这篇论文适合补 Layer 5 的端侧大模型部署，连接 `model-compression-edge` 和工业 IoT 应用。

## 论文要回答的问题

1. 工业 IoT 端侧 LLM 推理为什么需要极高压缩率。
2. 单次结构化剪枝为什么在高压缩下容易崩溃。
3. 级联多粒度剪枝如何选择层、头和 FFN 单元。
4. 压缩后模型在准确率、延迟、内存和泛化上如何权衡。

## 初读要点

| 粒度 | 直觉 | 风险 |
| --- | --- | --- |
| Layer pruning | 剪掉整层，收益大 | 语义能力损失明显 |
| Head pruning | 剪注意力头 | 不同任务影响不同 |
| FFN pruning | 剪前馈单元 | 硬件加速需匹配 |
| Cascaded strategy | 分阶段降低风险 | 搜索和校准成本 |

## 放进全栈框架

- Layer 4 提供端侧推理运行环境。
- Layer 5 负责 LLM 压缩、校准和部署。
- Layer 7 的工业场景决定模型能否承受精度损失。

## 初读结论

这篇论文的价值在于把 LLM 压缩问题放进工业 IoT 的极端资源约束中。后续深读要核验实验是否在真实设备或工业任务上完成，以及剪枝后的模型是否仍满足安全和可靠性要求。

## 后续核验清单

- 抽取多粒度剪枝流程、重要性估计和校准方法。
- 核对目标模型、压缩率、任务和端侧硬件指标。
- 比较延迟、内存、能耗和精度损失。
- 对接 `llm-quantization-gptq-awq` 与 `edge-ai-inference-serving`。

## 参考文献

[1] J. Wang, Y. Chen, W. Zhang, X. Huang, T. Liu, and G. Peng, "Cascaded Multi-Granularity Pruning for On-Device LLM Inference in Industrial IoT," arXiv:2606.26861, 2026.
