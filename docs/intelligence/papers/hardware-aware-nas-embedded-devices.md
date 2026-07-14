---
schema_version: '1.0'
id: hardware-aware-nas-embedded-devices
title: 512MB 内存以下嵌入式设备上的硬件感知 NAS
layer: 5
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - nas-edge-models
  - model-compression-edge
  - on-device-training
tags:
  - NAS
  - Embedded AI
  - TinyML
  - MCU
  - 硬件感知
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Running hardware-aware neural architecture search on embedded devices under 512MB of RAM"
  authors:
    - Andrea Mattia Garavagno
    - Edoardo Ragusa
    - Paolo Gastaldo
    - Antonio Frisoli
  year: 2026
  doi: 10.1109/ICCE59016.2024.10444268
  url: https://arxiv.org/abs/2606.14824v1
---
# 512MB 内存以下嵌入式设备上的硬件感知 NAS

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、搜索空间复现或设备实测核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

NAS 通常像在大厨房里自动试菜谱：算力和内存越多，能试的组合越多。但 IoT 和可穿戴设备常只有很小的内存预算。如果搜索过程本身跑不动，再好的轻量模型也很难在现场自适应。

这篇论文关注在 512MB RAM 以下嵌入式设备上运行 hardware-aware NAS，适合补充 `nas-edge-models` 从“为边缘搜索模型”到“在边缘上搜索模型”的差别。

## 论文要回答的问题

1. NAS 搜索过程如何适配低内存嵌入式设备。
2. 硬件约束如何进入搜索目标和候选网络生成。
3. 端侧运行 NAS 与云端搜索再下发相比有什么收益。
4. 搜索成本、模型质量和设备资源之间如何权衡。

## 初读要点

| 维度 | 传统 NAS | 端侧硬件感知 NAS |
| --- | --- | --- |
| 搜索位置 | 云端或工作站 | 嵌入式设备本身 |
| 约束 | FLOPs、参数量 | 实际 RAM、延迟和平台限制 |
| 目标模型 | 通用小模型 | 面向具体设备的小 CNN |
| 风险 | 搜索成本高 | 结果可能依赖特定硬件 |

## 放进全栈框架

- Layer 1 的 MCU/嵌入式硬件决定内存和功耗上限。
- Layer 5 负责 NAS、压缩和端侧学习。
- Layer 7 的可穿戴、声学和工业检测任务会验证是否值得端侧搜索。

## 初读结论

这篇论文的关键价值在于把 NAS 从“离线设计工具”推进到“受限设备可运行的适配机制”。后续深读要核验搜索算法是否真的在目标设备上运行，以及性能收益是否超过搜索带来的能耗和时间成本。

## 后续核验清单

- 抽取搜索空间、约束和候选评估流程。
- 核对目标设备、内存占用、搜索时间和模型精度。
- 比较端侧搜索与云端搜索的成本差异。
- 对接 `tinyml-mcu-deployment` 与 `model-compression-edge`。

## 参考文献

[1] A. M. Garavagno, E. Ragusa, P. Gastaldo, and A. Frisoli, "Running hardware-aware neural architecture search on embedded devices under 512MB of RAM," arXiv:2606.14824, 2026. Related DOI: 10.1109/ICCE59016.2024.10444268.
