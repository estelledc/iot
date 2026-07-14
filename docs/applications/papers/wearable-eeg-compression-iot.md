---
schema_version: '1.0'
id: wearable-eeg-compression-iot
title: 可穿戴设备 EEG 深度学习模型复杂度压缩
layer: 7
content_type: paper_reading
difficulty: advanced
reading_time: 18
prerequisites:
  - wearable-sensors
  - iomt-health-monitoring
  - model-compression-edge
tags:
  - Wearable IoT
  - EEG
  - Model Compression
  - Healthcare
  - Edge AI
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Reducing the Complexity of Deep Learning Models for EEG Analysis on Wearable Devices"
  authors:
    - Farough Shayeste Roodi
    - Parham Zilouchian Moghaddam
    - Mahdi Mohammadi-nasab
    - Mehdi Modarressi
    - Mostafa Ersali Salehi Nasab
    - Masoud Daneshtalab
  year: 2026
  doi: UNKNOWN
  url: https://arxiv.org/abs/2606.12742v4
---
# 可穿戴设备 EEG 深度学习模型复杂度压缩

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、模型压缩方法抽取或可穿戴硬件指标核验，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

可穿戴医疗设备要处理 ECG、EEG 等生理信号，但电池、算力和内存都很紧。EEG 模型若太大，就像让手环背着工作站跑步，理论准确率再高也难以部署。

这篇论文关注降低 EEG 深度学习模型复杂度，适合补 Layer 7 的 IoMT 应用，并和 Layer 5 的模型压缩形成直接连接。

## 论文要回答的问题

1. EEG 分析模型在可穿戴设备上主要受哪些资源约束限制。
2. 复杂度压缩会怎样影响准确率、延迟、内存和能耗。
3. 压缩方法是否适合实时或近实时健康监测。
4. 模型是否能跨个体、跨设备和跨场景泛化。

## 初读要点

| 维度 | 重要性 | 深读核验 |
| --- | --- | --- |
| Accuracy | 医疗判断不能乱 | 数据集和任务定义 |
| Latency | 实时监测需要及时响应 | 端侧实测还是估算 |
| Memory | 可穿戴设备资源紧 | 参数量和峰值 RAM |
| Energy | 决定续航 | 是否有功耗测量 |

## 放进全栈框架

- Layer 1 提供生理传感器和采样约束。
- Layer 5 提供模型压缩和端侧推理方法。
- Layer 7 用可穿戴健康场景检验工程可行性。

## 初读结论

这篇论文的价值在于把模型复杂度和真实可穿戴约束绑在一起。后续深读要核验“复杂度降低”是否包含真实能耗和内存测量，而不是只报告参数量或 FLOPs。

## 后续核验清单

- 抽取 EEG 任务、数据集和模型结构。
- 核对压缩策略、复杂度指标和准确率变化。
- 检查是否有真实可穿戴设备或 MCU/NPU 实测。
- 对接 `wearable-sensors` 与 `on-device-training`。

## 参考文献

[1] F. S. Roodi, P. Z. Moghaddam, M. Mohammadi-nasab, M. Modarressi, M. E. S. Nasab, and M. Daneshtalab, "Reducing the Complexity of Deep Learning Models for EEG Analysis on Wearable Devices," arXiv:2606.12742, 2026.
