---
schema_version: '1.0'
id: carbon-aware-mec-task-offloading-marl
title: 碳感知 MEC 任务卸载与多智能体强化学习
layer: 4
content_type: paper_reading
difficulty: frontier
reading_time: 20
prerequisites:
  - task-offloading-drl
  - mec-5g-integration
  - green-edge-scheduling
tags:
  - MEC
  - Task Offloading
  - Multi-Agent RL
  - MIMO
  - Carbon-Aware
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Carbon-aware decentralized dynamic task offloading in MIMO-MEC networks via multi-agent reinforcement learning"
  authors:
    - Mubshra Zulfiqar
    - Muhammad Ayzed Mirza
    - Basit Qureshi
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2602.18797v1
---
# 碳感知 MEC 任务卸载与多智能体强化学习

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、算法细节复现或仿真参数核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

MEC 任务卸载像把现场工作分给附近服务台：本地算、省通信，边缘算、省电但占网络。若再加入可再生能源和碳强度，决策就不只是“谁快谁算”，还要考虑什么时候算、用哪块能源、是否会造成无线干扰。

这篇论文把 MIMO-MEC、动态任务卸载、绿色能源和多智能体强化学习放在一起，适合补 `task-offloading-drl` 的可持续计算视角。

## 论文要回答的问题

1. MEC 卸载如何同时考虑延迟、能耗、碳排和无线干扰。
2. 去中心化 MARL 为什么适合多用户、多边缘节点场景。
3. 可再生能源间歇性如何进入状态和奖励设计。
4. 算法是否能在任务到达和信道变化下保持稳定。

## 初读要点

| 模块 | 直觉 | 关键风险 |
| --- | --- | --- |
| MIMO uplink | 多用户同时上传任务 | 干扰和 CSI 假设 |
| MEC server | 近端执行任务 | 排队和能耗模型 |
| Green energy | 低碳但不稳定 | 预测误差 |
| MARL | 多设备分别决策 | 收敛和安全性 |

## 放进全栈框架

- Layer 2 的无线链路决定卸载成本。
- Layer 4 负责 MEC 资源和任务调度。
- Layer 5 使用 RL 做策略学习，但不能忽略可解释性和稳定性。
- Layer 8 连接绿色计算和自治网络趋势。

## 初读结论

这篇论文把“绿色 MEC”从口号变成可建模的调度问题。后续深读应重点核验奖励函数是否平衡多目标、仿真是否覆盖极端负载，以及 MARL 策略是否有安全约束，避免为了省碳牺牲关键业务可靠性。

## 后续核验清单

- 抽取状态、动作、奖励和训练流程。
- 核对 MIMO 信道、任务到达、绿色能源和碳强度模型。
- 比较 MARL 与启发式、集中式优化的指标差异。
- 对接 `green-edge-scheduling` 与 `reinforcement-learning-edge`。

## 参考文献

[1] M. Zulfiqar, M. A. Mirza, and B. Qureshi, "Carbon-aware decentralized dynamic task offloading in MIMO-MEC networks via multi-agent reinforcement learning," arXiv:2602.18797, 2026.
