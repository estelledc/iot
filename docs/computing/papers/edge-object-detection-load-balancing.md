---
schema_version: '1.0'
id: edge-object-detection-load-balancing
title: 异构边缘目标检测系统的多目标负载均衡
layer: 4
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - edge-ai-inference-serving
  - resource-management-heterogeneous
  - multi-tenant-edge-isolation
tags:
  - Edge AI
  - Object Detection
  - Load Balancing
  - 异构硬件
  - SBC
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Multi-Objective Load Balancing for Heterogeneous Edge-Based Object Detection Systems"
  authors:
    - Daghash K. Alqahtani
    - Maria A. Rodriguez
    - Muhammad Aamir Cheema
    - Adel N. Toosi
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2603.15400v1
---
# 异构边缘目标检测系统的多目标负载均衡

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、实验平台核验或模型指标复现，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

边缘摄像头和传感节点常由不同 SBC、GPU 或 NPU 混搭，像一组能力不一的值班同学。目标检测任务来了，不能只问“谁空闲”，还要问延迟、准确率、能耗和硬件兼容性。

这篇论文围绕异构边缘目标检测系统做多目标负载均衡，适合补充 Layer 4 的资源管理与 Layer 5 的边缘推理之间的连接。

## 论文要回答的问题

1. 异构边缘设备上目标检测负载为什么难以简单轮询分配。
2. 多目标优化需要同时考虑哪些指标。
3. 硬件和软件异构会怎样影响推理延迟和检测质量。
4. 调度策略在负载变化时是否稳定。

## 初读要点

| 目标 | 直觉 | 深读关注 |
| --- | --- | --- |
| Latency | 任务尽快完成 | 尾延迟是否被控制 |
| Accuracy | 检测结果可靠 | 是否切换模型大小 |
| Energy | 设备少耗电 | 是否实测功耗 |
| Fairness | 不让单节点长期过载 | 是否考虑热和故障 |

## 放进全栈框架

- Layer 4 管理异构边缘资源和调度。
- Layer 5 提供可选模型、精度和推理服务。
- Layer 7 的视频监控、交通和工业视觉应用会直接受益或受限。

## 初读结论

这篇论文提醒我们：边缘 AI 的瓶颈不只在模型本身，还在“模型被谁、何时、在哪里执行”。后续深读要核验作者是否处理了动态摄像头流、模型切换成本和网络带宽，而不是只在固定任务队列上优化。

## 后续核验清单

- 抽取多目标函数、约束和调度流程。
- 核对硬件平台、模型种类、数据集和负载生成方式。
- 对比单目标调度与多目标调度的 trade-off。
- 对接 `edge-ai-video-analytics` 与 `resource-management-heterogeneous`。

## 参考文献

[1] D. K. Alqahtani, M. A. Rodriguez, M. A. Cheema, and A. N. Toosi, "Multi-Objective Load Balancing for Heterogeneous Edge-Based Object Detection Systems," arXiv:2603.15400, 2026.
