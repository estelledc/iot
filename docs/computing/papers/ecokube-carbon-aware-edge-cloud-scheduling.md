---
schema_version: '1.0'
id: ecokube-carbon-aware-edge-cloud-scheduling
title: EcoKube：异构边云环境中的碳感知调度模拟
layer: 4
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - container-orchestration-edge
  - green-edge-scheduling
  - service-mesh-edge
tags:
  - Edge-Cloud
  - Carbon-Aware Scheduling
  - Kubernetes
  - 绿色计算
  - 调度模拟
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "EcoKube: Simulating Carbon-Aware Scheduling Policies in Heterogeneous Edge-Cloud Environments"
  authors:
    - Gonçalo Ferreira
    - Shashikant Ilager
  year: 2026
  doi: 10.1145/3802513.3803486
  url: https://arxiv.org/abs/2607.09318v1
---
# EcoKube：异构边云环境中的碳感知调度模拟

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、模拟器安装或调度策略复现，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

边缘计算过去常把调度目标写成“离用户近、延迟低、资源够”。但如果不同地点的电网碳强度和 PUE 不一样，同一个任务放到哪里跑还会影响碳排。EcoKube 把这个问题放进异构 edge-cloud 调度模拟中，适合作为绿色边缘计算的工程入口。

这篇论文的价值不只是“节能”，而是把碳强度、硬件异构、AI 负载和 Kubernetes 式调度策略放在同一个实验框架里比较。

## 论文要回答的问题

1. 边云调度如何把实时碳强度纳入决策。
2. 异构硬件和不同 PUE 会怎样改变调度结果。
3. 碳感知策略是否会牺牲延迟、吞吐或资源利用率。
4. 模拟器能否帮助比较策略，而不是只给单个算法结果。

## 初读要点

| 因素 | 传统调度 | EcoKube 关注 |
| --- | --- | --- |
| 位置 | 近端优先 | 位置和电网碳强度共同决策 |
| 硬件 | CPU/内存容量 | 异构设备能耗差异 |
| 时间 | 当前资源状态 | 碳强度随时间变化 |
| 目标 | 延迟和资源利用 | 碳、性能和稳定性权衡 |

## 放进全栈框架

- Layer 4 直接对应边云调度和容器平台。
- Layer 5 的 AI 推理负载会加剧能耗和碳排。
- Layer 8 的绿色计算议题需要回到可测量的调度策略。

## 初读结论

EcoKube 的启发是：边缘平台的“绿色”不能只靠设备低功耗，还要把任务放置、时间、硬件和电网条件一起算账。后续深读应重点核验模拟器假设是否接近真实 Kubernetes/边缘集群，以及碳收益是否建立在过强的负载迁移前提上。

## 后续核验清单

- 抽取 EcoKube 的系统模型、输入数据和调度策略集合。
- 核对 carbon intensity、PUE、硬件功耗模型的来源。
- 对比碳收益与延迟、任务失败率之间的 trade-off。
- 对接 `green-edge-scheduling` 和 `container-orchestration-edge`。

## 参考文献

[1] G. Ferreira and S. Ilager, "EcoKube: Simulating Carbon-Aware Scheduling Policies in Heterogeneous Edge-Cloud Environments," arXiv:2607.09318, 2026. Related DOI: 10.1145/3802513.3803486.
