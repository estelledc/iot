---
schema_version: '1.0'
id: power-side-channel-tinyml-anomaly-detection
title: 基于功耗侧信道数据的自治 TinyML 异常检测
layer: 5
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - edge-anomaly-detection
  - tinyml-mcu-deployment
  - side-channel-attack-defense
tags:
  - TinyML
  - Power Side-Channel
  - Anomaly Detection
  - MCU
  - On-Device Training
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Fully Autonomous Z-Score-Based TinyML Anomaly Detection on Resource-Constrained MCUs Using Power Side-Channel Data"
  authors:
    - Abdulrahman Albaiz
    - Fathi Amsaad
  year: 2026
  doi: 10.1109/SATC69565.2026.11542250
  url: https://arxiv.org/abs/2604.08581v1
---
# 基于功耗侧信道数据的自治 TinyML 异常检测

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、硬件实验复现或功耗数据核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

功耗侧信道通常被当作安全风险，但也可以变成设备行为监测信号。论文用低功耗 MCU 上的 TinyML 和 Z-score 方法做自治异常检测，强调训练和推理都在资源受限设备上完成。

这篇论文适合补 Layer 5 的端侧异常检测，也能和 Layer 6 的侧信道安全形成有趣对照：同一种信号既可能泄露信息，也可能帮助诊断。

## 论文要回答的问题

1. 功耗侧信道数据能否反映设备行为异常。
2. Z-score-based TinyML 如何在 MCU 上完成训练和推理。
3. 自治本地检测相比云端分析有什么收益。
4. 噪声、负载变化和设备差异会怎样影响阈值和误报。

## 初读要点

| 环节 | 作用 | 深读风险 |
| --- | --- | --- |
| Power sensing | 捕捉设备功耗模式 | 测量硬件成本 |
| Z-score model | 简化异常判定 | 阈值敏感 |
| TinyML runtime | MCU 本地运行 | 内存和采样开销 |
| Autonomous training | 不依赖云端训练 | 数据漂移处理 |

## 放进全栈框架

- Layer 1 提供功耗测量和 MCU 资源边界。
- Layer 5 负责 TinyML 训练和异常检测。
- Layer 6 需要同时考虑侧信道泄露和防护。

## 初读结论

这篇论文的启发是：边缘智能不一定要复杂模型，简单统计方法在正确的信号上也可能有价值。后续深读要核验异常定义、阈值稳定性和 MCU 实测资源。

## 后续核验清单

- 抽取功耗采样、Z-score 训练和异常判定流程。
- 核对 MCU 型号、内存、延迟和能耗指标。
- 检查异常类别和真实设备场景。
- 对接 `side-channel-attack-defense` 与 `edge-anomaly-detection`。

## 参考文献

[1] A. Albaiz and F. Amsaad, "Fully Autonomous Z-Score-Based TinyML Anomaly Detection on Resource-Constrained MCUs Using Power Side-Channel Data," arXiv:2604.08581, 2026. Related DOI: 10.1109/SATC69565.2026.11542250.
