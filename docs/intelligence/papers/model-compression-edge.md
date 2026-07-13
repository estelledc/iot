---
schema_version: '1.0'
id: model-compression-edge
title: 边缘 AI 模型压缩技术全景
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 26
prerequisites:
  - neural-network-quantization-int8
  - tflite-micro-model-optimization
tags:
- 模型压缩
- 量化
- 剪枝
- GPTQ
- AWQ
- 知识蒸馏
- 边缘AI
- TensorRT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 边缘 AI 模型压缩技术全景

> **难度**：🟡 中级 | **领域**：边缘 AI、模型优化 | **关键词**：量化, 剪枝, 蒸馏, NAS | **阅读时间**：约 26 分钟

## 日常类比

云端 A100 像仓库级冷库，MCU 像保温杯：同一份“食材”（神经网络）必须脱水（量化）、剔骨（剪枝）、换小锅菜谱（蒸馏/NAS）才能装进保温杯还不馊（精度可接受）。压缩不是免费的——每少一位或每砍一条连接，都在赌信息冗余够不够[1]。

## 摘要

覆盖量化、剪枝、与蒸馏/NAS 的分工，以及推理引擎落地。资源倍数、精度损失与 tokens/s 为公开文献或厂商材料的**量级示意**，跨芯片差异大，须在目标板上验收。蒸馏与 NAS 细节见专题文。

## 1 为何需要压缩

| 约束 | 云端 GPU（A100 级） | 边缘 GPU（Jetson 级） | MCU（STM32 级） |
|------|---------------------|----------------------|-----------------|
| 内存 | 数十 GB HBM | 数 GB 共享 | 数百 KB SRAM |
| 算力 | 数百 TFLOPS 量级 | 亚 TFLOPS–数 TFLOPS | mTFLOPS 量级 |
| 功耗 | 数百 W | 数–十余 W | 数十 mW 量级 |
| 存储 | TB 级 | GB 级 eMMC | MB 级 Flash |

ResNet-50 约 25M 参数、FP32 约百 MB 量级，云端轻松、MCU 存不下[1]。

```
模型压缩
├── 量化 → 降位宽（FP32→INT8→INT4…）
├── 剪枝 → 去不重要权重/通道/层
├── 知识蒸馏 → 大教小（专题）
└── NAS → 自动搜高效结构（专题）
```

本文重点：量化与剪枝 + 部署工具链。

## 2 量化

### 2.1 概念

均匀量化：\(q=\mathrm{round}(w/\mathrm{scale})+z\)，反量化 \(w\approx(q-z)\cdot\mathrm{scale}\)。位宽越低，动态范围与分辨率越差[12]。

### 2.2 PTQ 与 QAT

| 方法 | 位宽 | 精度损失量级 | 成本 | 数据 |
|------|------|--------------|------|------|
| 朴素 PTQ | INT8 | 常 <1 pp | 分钟级 | 少量校准 |
| 朴素 PTQ | INT4 | 可达数–十余 pp | 分钟级 | 校准 |
| QAT[12] | INT8 | 常 <0.5 pp | 小时–天 | 训练集 |
| QAT | INT4 | 常约 1–2 pp | 小时–天 | 训练集 |
| GPTQ[2] | INT4/3 | PPL +约 0.3–0.5 量级 | 小时级 | ~128 条 |
| AWQ[3] | INT4 | PPL +约 0.1–0.3 量级 | 小时级 | 少量 |
| SmoothQuant[4] | W8A8 | 常 <0.5 pp | 分钟级 | 少量 |
| GGUF[10] | Q4_K 等 | PPL +约 0.3 量级 | 分钟级 | 可无 |

**PTQ**：训练后直接映射；快，但低比特易崩。
**QAT**：前向模拟量化，反向用直通估计器（Straight-Through Estimator, STE）[12]。
**LLM 专用**：GPTQ 用 Hessian 补偿列误差[2]；AWQ 保护高激活通道[3]；SmoothQuant 把激活 outlier 难度迁到权重[4]。

## 3 剪枝

### 3.1 非结构化 vs 结构化

Deep Compression 等显示 VGG/AlexNet 可达约 9–13× 参数压缩且精度损失很小，但不规则稀疏在通用 GPU/CPU 上难兑现同等加速[1]。结构化剪枝删通道/头/层，形状仍规整，更易加速。

| 方法 | 粒度 | 压缩率量级 | 精度 | 实际加速 | 硬件友好 |
|------|------|------------|------|----------|----------|
| 非结构化权重剪枝 | 单权重 | 可达 10×+ | 常优 | 低（无稀疏核） | 差 |
| 通道剪枝 | 卷积通道 | 约 2–5× | 中 | 约 1.5–3× | 好 |
| 注意力头剪枝 | head | 约 1.5–2.5× | 中 | 约 1.3–2× | 好 |
| 层剪枝 | 整层 | 约 1.5–3× | 较差 | 约 1.5–2.5× | 好 |
| N:M（如 2:4）[7] | 结构化稀疏 | 约 2× | 常优 | 约 1.5–2×（支持硬件） | 极好（Ampere+） |

BERT 上可去掉相当比例注意力头而指标变化有限——比例与任务相关[6]。彩票假说指出大网中存在可独立训练的稀疏“中奖票”，解释了过度参数化的搜索价值[5]。

## 4 推理引擎

| 引擎 | 目标硬件 | 量化 | 要点 |
|------|----------|------|------|
| TensorRT | NVIDIA GPU/Jetson | INT8/FP16 | 层融合、核调优 |
| TFLite | ARM CPU/GPU/DSP | INT8 等 | 移动/MCU 生态 |
| ONNX Runtime | 跨平台 | INT8/FP16 | 格式统一 |
| OpenVINO | Intel | INT8/FP16 | 特化优化 |
| NCNN / MNN | 移动端 | INT8/FP16 | 端侧极致 |
| llama.cpp / MLC-LLM | CPU/GPU 多后端 | GGUF/INT4 | LLM |

典型流水线：训练框架 → ONNX → 量化 → 引擎编译（融合 Conv-BN-ReLU 等）→ 设备。层融合可在量化之外再带来可观加速，幅度视图而定。

## 5 Benchmark 量级（示意）

### 图像

| 模型 | FP32 大小量级 | INT8 | Jetson 级延迟趋势 | INT8 精度 |
|------|---------------|------|-------------------|-----------|
| ResNet-50 | ~98 MB | ~1/4 | 常明显下降 | 损失常 <1 pp |
| MobileNetV2 | ~14 MB | ~1/4 | 常近半 | 损失可略大 |
| YOLO 小模型 | 数十 MB | ~1/4 | 常近半 | mAP 损失常 <1 pp |

### LLM

| 模型 | FP16 量级 | INT4 量级 | 设备示例 | 速度量级 |
|------|-----------|-----------|----------|----------|
| Llama2-7B | ~13–14 GB | ~3.5–4 GB | Jetson AGX / 笔记本 | 十余 tokens/s 量级 |
| 更小 1–4B | 数 GB | <2 GB | RPi / Nano | 数 tokens/s 量级 |

具体数字随量化格式、ctx、功耗模式变化[2][3][10]。

## 6 局限、挑战与可改进方向

### 1. 精度悬崖

**局限**：FP32→INT8 常温和，再降 INT4 时轻量网与回归/分割任务易骤降。
**改进**：敏感层保留更高位；QAT 或 GPTQ/AWQ；按任务设硬门槛而非只看均值精度。

### 2. 剪枝结构难迁移

**局限**：在数据集 A 上“重要”的通道，换域可能不再重要。
**改进**：目标域轻量微调；结构化剪枝 + 再训练；IoT 多场景用多稀疏掩码或动态路由（成本更高）。

### 3. 组合拳无标准菜谱

**局限**：蒸馏→剪枝→量化顺序与超参爆炸。
**改进**：先定延迟/内存/功耗预算，再小网格搜；记录每次组合的板级曲线。

### 4. 理论加速 ≠ 板级加速

**局限**：FLOPs 减半不等于时延减半；内存带宽与算子支持是瓶颈。
**改进**：以目标引擎 profiler 为准；优先选引擎已深度优化的算子与稀疏模式（如 2:4）[7]。

## 参考文献

[1] S. Han, H. Mao, W. J. Dally, "Deep Compression," ICLR, 2016.
[2] E. Frantar et al., "GPTQ," ICLR, 2023.
[3] J. Lin et al., "AWQ," MLSys, 2024.
[4] G. Xiao et al., "SmoothQuant," ICML, 2023.
[5] J. Frankle, M. Carbin, "The Lottery Ticket Hypothesis," ICLR, 2019.
[6] P. Michel, O. Levy, G. Neubig, "Are Sixteen Heads Really Better than One?" NeurIPS, 2019.
[7] A. Mishra et al., "Accelerating Sparse Deep Neural Networks," arXiv, 2021.
[8] M. Nagel et al., "A White Paper on Neural Network Quantization," arXiv, 2021.
[9] NVIDIA, "TensorRT Documentation," 2024.
[10] G. Gerganov et al., "llama.cpp," GitHub, 2023–2025.
[11] Google, "TensorFlow Lite for Microcontrollers," 2024.
[12] B. Jacob et al., "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference," CVPR, 2018.
[13] G. Hinton, O. Vinyals, J. Dean, "Distilling the Knowledge in a Neural Network," NeurIPS Workshop, 2015.
