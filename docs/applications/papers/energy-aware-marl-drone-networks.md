---
schema_version: '1.0'
id: energy-aware-marl-drone-networks
title: 面向任务型无人机网络的能量感知多智能体强化学习
layer: 7
content_type: paper_reading
difficulty: frontier
reading_time: 20
prerequisites:
  - drone-iot-inspection
  - reinforcement-learning-edge
  - green-edge-scheduling
tags:
  - Drone Networks
  - MARL
  - Energy-Aware
  - Mission-Oriented
  - IoT应用
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Scaling up Energy-Aware Multi-Agent Reinforcement Learning for Mission-Oriented Drone Networks with Individual Reward"
  authors:
    - Changling Li
    - Ying Li
  year: 2026
  doi: 10.1109/JIOT.2024.3511253
  url: https://arxiv.org/abs/2605.24992v1
---
# 面向任务型无人机网络的能量感知多智能体强化学习

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、奖励函数抽取或仿真实验复现，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

无人机 IoT 网络要在有限电池下完成巡检、覆盖或灾害响应任务。多智能体强化学习能让多架无人机协作，但规模变大后训练和信用分配都很难。论文强调 individual reward，试图让每个 agent 的学习信号更清楚。

这篇论文适合补 `drone-iot-inspection` 的智能调度部分，也能和绿色边缘调度形成交叉。

## 论文要回答的问题

1. 任务型无人机网络为什么需要能量感知 MARL。
2. Individual reward 如何帮助多智能体规模扩展。
3. 轨迹、任务完成率和电池约束如何一起建模。
4. 方法在更多无人机、更复杂任务下是否稳定。

## 初读要点

| 维度 | 关注点 | 风险 |
| --- | --- | --- |
| Mission reward | 是否完成巡检或覆盖目标 | 奖励稀疏 |
| Energy reward | 是否避免过早耗尽电池 | 可能牺牲任务效率 |
| Coordination | 多无人机协作 | 碰撞和通信限制 |
| Scalability | agent 数增加 | 训练不稳定 |

## 放进全栈框架

- Layer 2 提供无人机通信链路。
- Layer 5 提供 MARL 策略学习。
- Layer 7 对应巡检、应急和智能城市应用。

## 初读结论

这篇论文的关键是把能量约束纳入任务协同，而不是事后评估续航。后续深读要核验奖励函数是否避免短视行为，以及仿真是否包含通信中断、碰撞约束和真实电池模型。

## 后续核验清单

- 抽取状态、动作、individual reward 和训练流程。
- 核对任务场景、无人机数量、通信模型和电池模型。
- 比较集中式、共享奖励和 individual reward 的表现。
- 对接 `drone-iot-inspection` 与 `task-offloading-drl`。

## 参考文献

[1] C. Li and Y. Li, "Scaling up Energy-Aware Multi-Agent Reinforcement Learning for Mission-Oriented Drone Networks with Individual Reward," arXiv:2605.24992, 2026. Related DOI: 10.1109/JIOT.2024.3511253.
