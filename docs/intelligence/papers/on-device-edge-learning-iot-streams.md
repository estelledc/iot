---
schema_version: '1.0'
id: on-device-edge-learning-iot-streams
title: IoT 数据流的端侧边缘学习：持续学习与资源约束
layer: 5
content_type: paper_reading
difficulty: advanced
reading_time: 22
prerequisites:
  - tinyml-mcu-deployment
  - edge-ai-inference-optimization
tags:
  - 端侧学习
  - 持续学习
  - TinyML
  - 数据流
  - 概念漂移
  - 边缘智能
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "On-device edge learning for IoT data streams: a survey"
  authors:
    - Afonso Lourenco
    - Joao Rodrigo
    - Joao Gama
    - Goreti Marreiros
  year: 2025
  doi: 10.48550/arXiv.2502.17788
  url: https://arxiv.org/abs/2502.17788
---
# IoT 数据流的端侧边缘学习：持续学习与资源约束

> 初读范围：本文只基于 arXiv 页面元数据与摘要建立阅读卡片；尚未完成 PDF 逐段精读、方法分类复核或实验表抽取，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

很多 IoT 设备面对的是持续到来的数据流，而不是一次性训练好的静态数据集。温湿度、振动、电流、摄像头事件都会随时间变化，模型如果永远不更新，就会遇到概念漂移；但如果在设备上不断训练，又会受到内存、能耗和稳定性的限制。

这篇综述把问题聚焦到端侧训练：神经网络和决策树如何在资源受限设备上处理分类任务、数据流、遗忘和开放环境。

## 论文要回答的问题

论文关注的核心问题包括：

1. IoT 数据流与传统批量训练有什么不同。
2. 端侧训练为什么会遇到灾难性遗忘、数据低效和收敛不稳定。
3. 神经网络与决策树在内存、表达力和适应能力上如何权衡。
4. 如何用多指标评估端侧学习，而不是只看准确率。

## 关键对比

| 维度 | 神经网络端侧学习 | 决策树/在线树方法 |
| --- | --- | --- |
| 表达能力 | 强，适合复杂模式 | 相对弱，依赖特征和动态调整 |
| 内存压力 | 激活、梯度、优化器状态开销大 | 通常更轻，但树增长需控制 |
| 概念漂移 | 需要持续学习机制 | 可通过剪枝、增量更新适配 |
| 灾难性遗忘 | 风险高 | 风险相对可控但表达受限 |
| IoT 适配难点 | 训练能耗和收敛稳定性 | 开放世界和复杂模式表达 |

## 放进全栈框架

这篇论文连接 Layer 1 和 Layer 5：

- Layer 1 决定设备能否承担训练开销，如 SRAM、Flash、电源和采样频率。
- Layer 4 决定是否有网关或边缘服务器分担训练。
- Layer 5 决定模型更新策略，如在线学习、持续学习、蒸馏或元学习。
- Layer 7 决定评价指标，例如工业异常检测更关心漏报，智能家居更关心误报和能耗。

## 初读结论

端侧学习不是“把云上训练搬到设备上”，而是要重新设计学习循环。稳定性与可塑性、旧知识保留与新分布适配、输出指标与内部表示指标，都需要一起评估。对 IoT 工程来说，先判断是否真的需要端侧训练，再决定模型类型，通常比直接追求更大的模型更重要。

## 后续核验清单

- 提取论文对 continual learning、online learning、edge learning 的术语边界。
- 列出文中比较的神经网络和决策树方法，并补充内存/计算指标。
- 核对多指标评价框架：准确率、遗忘度、前向/后向迁移、能耗、延迟和收敛。
- 对接 `tinyml-mcu-deployment`，区分端侧推理和端侧训练的资源差异。

## 参考文献

[1] Afonso Lourenco, Joao Rodrigo, Joao Gama, Goreti Marreiros, "On-device edge learning for IoT data streams: a survey," arXiv:2502.17788, 2025.
