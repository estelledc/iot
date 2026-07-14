---
schema_version: '1.0'
id: green-iot-data-computation-orchestration
title: Green IoT 网络中的数据采集与计算编排
layer: 8
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - green-edge-computing
  - energy-harvesting-iot
  - task-offloading-drl
tags:
  - Green IoT
  - Energy Harvesting
  - Data Collection
  - Computation Orchestration
  - MILP
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Orchestrating Data Collection and Computation in Green IoT Networks"
  authors:
    - Junfei Zhan
    - Tengjiao He
    - Kwan-Wu Chin
    - Benyu Chen
    - Fei Song
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2605.23152v1
---
# Green IoT 网络中的数据采集与计算编排

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、MILP 约束复算或实验数据核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

Green IoT 设备可能靠能量采集工作，什么时候采样、什么时候上传、在哪里计算，都要看电量和任务价值。论文提出 MILP 来联合调度采样时间、应用是否运行，以及设备、网关和服务器的能量使用。

这篇论文适合补 Layer 8 的绿色 IoT 编排问题，也能和 Layer 4 的 task offloading 形成对照。

## 论文要回答的问题

1. 能量采集节点上的数据采集和计算任务为什么必须联合调度。
2. MILP 如何表示采样、应用运行、网关和服务器能量约束。
3. 绿色网络中任务完成率、能耗和数据价值如何权衡。
4. 优化模型是否能扩展到大规模 IoT 网络。

## 初读要点

| 决策 | 含义 | 风险 |
| --- | --- | --- |
| Sampling time | 何时采集数据 | 采样太少影响任务质量 |
| Application admission | 是否运行应用 | 低电量时需取舍 |
| Computation placement | 端、网关或服务器 | 传输和计算能耗不同 |
| Energy allocation | 如何使用采集能量 | 预测误差影响策略 |

## 放进全栈框架

- Layer 1 关注能量采集和节点电池。
- Layer 4 负责计算放置与任务编排。
- Layer 8 体现绿色 IoT 的系统级优化。

## 初读结论

这篇论文把绿色 IoT 从单点省电推进到采样、通信和计算联合决策。后续深读要核验 MILP 的规模上限，以及是否有可在线部署的近似策略。

## 后续核验清单

- 抽取 MILP 变量、目标函数和约束。
- 核对能量采集、任务负载和网络拓扑假设。
- 比较最优策略、启发式和在线策略差异。
- 对接 `battery-life-estimation-model` 与 `green-edge-scheduling`。

## 参考文献

[1] J. Zhan, T. He, K.-W. Chin, B. Chen, and F. Song, "Orchestrating Data Collection and Computation in Green IoT Networks," arXiv:2605.23152, 2026.
