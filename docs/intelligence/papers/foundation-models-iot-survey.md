---
schema_version: '1.0'
id: foundation-models-iot-survey
title: IoT 基础模型综述：分类法与选型准则
layer: 5
content_type: paper_reading
difficulty: frontier
reading_time: 24
prerequisites:
  - federated-learning-iot
  - multimodal-edge-perception
  - edge-rag-retrieval
tags:
  - Foundation Model
  - IoT
  - 边缘智能
  - 多模态感知
  - 安全与隐私
  - 评估指标
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "A Survey of Foundation Models for IoT: Taxonomy and Criteria-Based Analysis"
  authors:
    - Hui Wei
    - Dong Yoon Lee
    - Shubham Rohal
    - Zhizhang Hu
    - Ryan Rossi
    - Shiwei Fang
    - Shijia Pan
  year: 2025
  doi: 10.48550/arXiv.2506.12263
  url: https://arxiv.org/abs/2506.12263
---
# IoT 基础模型综述：分类法与选型准则

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、引用链核验或实验表抽取，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

IoT 里的 AI 过去常像“每个岗位都单独培训一个新人”：温度异常检测训练一个模型，动作识别训练一个模型，设备故障预测再训练一个模型。基础模型的想法更像先训练一个“通用实习生”，再针对具体传感器和任务微调。

这篇综述的价值在于不只列模型名字，而是把 IoT 基础模型按目标拆成效率、上下文感知、安全、安全与隐私等准则。对学习站来说，它可以作为 Layer 5 从“单点模型优化”走向“跨任务可迁移智能”的入口。

## 论文要回答的问题

1. IoT 场景中哪些任务正在使用 foundation models。
2. 不同 IoT 任务之间，能否用统一准则比较模型能力。
3. 选择 IoT foundation model 时，应优先看效率、上下文、安全还是隐私。
4. 现有研究还缺哪些标准化评估指标。

## 分类视角速读

| 准则 | 在 IoT 中的含义 | 工程关注 |
| --- | --- | --- |
| 效率 | 模型能否在端侧或边缘侧跑得动 | 参数量、延迟、能耗、通信量 |
| 上下文感知 | 是否理解设备位置、时间、场景和用户状态 | 多模态融合、时序建模、个性化 |
| 安全 | 模型输出是否能被攻击诱导或误用 | 对抗鲁棒性、异常输入、控制边界 |
| 安全与隐私 | 数据是否能少出域、少暴露 | 联邦学习、差分隐私、访问控制 |

## 放进全栈框架

- Layer 1/2 提供传感器与连接条件，决定数据形态和带宽预算。
- Layer 4 提供边缘部署环境，决定模型是否有运行空间。
- Layer 5 负责模型迁移、微调、压缩与多模态理解。
- Layer 6 需要约束隐私泄露、模型供应链和提示注入等风险。

## 初读结论

这篇论文提醒我们：IoT foundation model 不是“把大模型塞进设备”这么简单，而是要回答模型能否跨设备、跨任务、跨场景复用。后续深读时，重点不是记住所有模型名，而是抽取一张选型表：在给定数据类型、延迟预算、隐私边界和安全等级后，该选哪类模型与部署策略。

## 后续核验清单

- 从 PDF 中提取完整 taxonomy，并标注每类对应的 IoT 数据类型。
- 核对论文提到的代表性模型、指标和数据集。
- 区分作者给出的事实统计、方法归纳和未来方向判断。
- 对接 `edge-rag-retrieval`、`multimodal-edge-perception` 与 `llm-iot-security-survey`。

## 参考文献

[1] H. Wei, D. Y. Lee, S. Rohal, Z. Hu, R. Rossi, S. Fang, and S. Pan, "A Survey of Foundation Models for IoT: Taxonomy and Criteria-Based Analysis," arXiv:2506.12263, 2025.
