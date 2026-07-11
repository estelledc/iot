---
schema_version: '1.0'
id: llm-quantization-gptq-awq
title: 大模型推理量化：GPTQ 与 AWQ
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 24
prerequisites:
  - model-compression-edge
  - neural-network-quantization-int8
tags:
- GPTQ
- AWQ
- LLM量化
- PTQ
- INT4
- GGUF
- QLoRA
- 边缘推理
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 大模型推理量化：GPTQ 与 AWQ

> **难度**：🟡 中级 | **领域**：模型压缩、大语言模型、边缘推理 | **关键词**：GPTQ, AWQ, PTQ, INT4 | **阅读时间**：约 24 分钟

## 日常类比

整面墙精装书（FP16 权重）要搬进只有四分之一书架的公寓（边缘内存）。GPTQ 像逐本压缩并微调邻书位置补偿信息损失；AWQ 先看你常翻哪 1% 的书（激活显著通道），对其加保护再大胆压其余——空间省了，阅读体验往往仍可用[1][2]。

## 摘要

对比训练后量化（Post-Training Quantization, PTQ）路线下的 GPTQ 与 AWQ，并对照 GGUF、bitsandbytes、SmoothQuant 等。困惑度（Perplexity, PPL）、耗时与 tokens/s 来自公开论文或社区报告量级，换模型/换板会变，部署须实测。

## 1 量化基础

### 1.1 为何需要

| 精度 | 每参数 | 7B 量级 | 13B 量级 | 70B 量级 |
|------|--------|---------|----------|----------|
| FP32 | 4 B | ~28 GB | ~52 GB | ~280 GB |
| FP16 | 2 B | ~14 GB | ~26 GB | ~140 GB |
| INT8 | 1 B | ~7 GB | ~13 GB | ~70 GB |
| INT4 | 0.5 B | ~3.5 GB | ~6.5 GB | ~35 GB |

上表为参数存储粗算，不含 KV Cache 与运行时碎片。Jetson Orin Nano 等约 8 GB 统一内存跑 7B，通常至少需要约 4-bit 权重[3]。

### 1.2 PTQ vs QAT

| 特性 | PTQ | 量化感知训练（QAT） |
|------|-----|---------------------|
| 数据 | 少量校准集 | 完整训练集 |
| 成本 | 分钟–小时级 | 天–周级 |
| 精度 | 中–好 | 通常最佳 |
| LLM 主流 | GPTQ, AWQ, SmoothQuant[1][2][4] | LLM-QAT 等，成本高 |

## 2 GPTQ

目标近似 \(\min \|WX - Q(W)X\|_2^2\)：逐列量化并用 Hessian 信息补偿后续列误差（Optimal Brain Quantization 思路）[1]。实践要点：列排序、lazy batch 更新、分组量化（常见 group_size=128）。

校准样本量论文常用约 128 条量级；7B 在 A100 上量化常为数分钟至十余分钟量级，视实现而定[1]。

## 3 AWQ

观察：少数与大激活对应的权重通道对输出影响大（论文称约 1% 量级显著通道）[2]。通过逐通道缩放放大重要权重再量化，反缩放后保护显著方向，且可用标准 GEMM，硬件友好。

### GPTQ vs AWQ（公开报告量级）

| 特性 | GPTQ[1] | AWQ[2] |
|------|---------|--------|
| 策略 | Hessian 误差补偿 | 激活感知缩放 |
| 校准 | ~128 样本 | ~128 样本 |
| 7B 量化时间 | 常略长 | 常略短 |
| LLaMA-7B 4-bit PPL | 论文约 5.85 量级 | 论文约 5.78 量级 |
| 推理 | 依赖专用 kernel | 标准 GEMM 友好 |
| 内存 | 需 Hessian 相关结构 | 主要需激活统计 |

PPL 数字绑定具体模型与评测集，换 Llama-2/3 或领域数据会漂移[1][2][5]。

## 4 其他方案

| 方法 | 位宽 | 框架 | 备注 |
|------|------|------|------|
| GGUF q4_k_m 等[6] | 混合约 4–5 bit | llama.cpp | CPU/Metal/CUDA 生态成熟 |
| bitsandbytes NF4[3] | 4 | HF Transformers | 加载即用；双重量化可选 |
| SmoothQuant[4] | 常 W8A8 | 研究/部分引擎 | 迁激活 outlier 到权重 |
| OmniQuant 等[7] | 可变 | 研究 | 可学习量化参数 |
| KV 量化（如 KIVI）[8] | KV 可至 2–4 bit | 研究/集成中 | 长上下文内存关键 |

### WikiText 类 PPL 对照（示意，非排行榜）

| 方法 | 位宽 | PPL 量级 | 权重大小量级 |
|------|------|----------|--------------|
| FP16 | 16 | ~5.5 | ~14 GB |
| GPTQ | 4 | ~5.8–5.9 | ~3.6 GB |
| AWQ | 4 | ~5.7–5.8 | ~3.6 GB |
| GGUF q4_k_m | ~4.5 | 常接近上列 | ~4 GB |
| 3-bit 诸方法 | 3 | 常明显升高 | ~2.7–3 GB |

## 5 边缘部署要点

### 5.1 内存预算

总内存 ≈ 权重量化大小 + KV Cache（常 FP16，除非另量化）+ 激活与碎片。7B、4-bit、ctx≈2048 时，权重约 3.5 GB 量级，KV 可达约 1 GB 量级，合计常需约 5 GB+ 余量——8 GB 设备可行但紧张[3][11]。

### 5.2 位宽与任务

公开 scaling 观察：8→4 bit 对许多生成任务可接受；3 bit 及以下在数学/代码上退化更明显；混合精度（嵌入/lm_head 更高位）可改善均值位宽与质量折中[5][9]。

### 5.3 QLoRA

在 4-bit 基座上挂 LoRA 适配器微调，可训练参数远小于全量，消费级 GPU 常可完成[3]。边缘推理仍需合并或保留适配器加载路径。

## 6 实践建议

- GPU 服务优先试 AWQ/vLLM 生态；CPU/多后端优先 GGUF[2][6]。
- 校准数据尽量贴近下游分布。
- 验收看下游任务，不只看 PPL。
- 不同工具的“4-bit”不可互换；注意 chat template。
- Jetson 上 llama.cpp CUDA 常需源码编译[6]。

## 7 局限、挑战与可改进方向

### 1. 校准集与域偏移

**局限**：通用 C4/Wiki 校准在垂直术语、代码、多语言上可能次优。
**改进**：用目标域无标签文本做校准；固定黄金集做回归。

### 2. Kernel 与可移植性

**局限**：GPTQ 速度强依赖 kernel；MCU/NPU 工具链支持参差。
**改进**：优先选目标运行时原生格式（TRT-LLM、GGUF、厂商 INT4）；抽象“量化产物”与“运行时”接口[10]。

### 3. 低于 4-bit 与激活量化

**局限**：权重量化不等于激活/KV 也低比特；端到端 W4A4 仍难。
**改进**：权重 4-bit + INT8 KV；关注 BiLLM 等极低比特研究但谨慎上生产[9]。

### 4. 评测单一

**局限**：只报 PPL 会掩盖指令遵循与安全退化。
**改进**：任务套件 + 延迟/功耗/热节流联合验收。

## 参考文献

[1] E. Frantar et al., "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers," ICLR, 2023.
[2] J. Lin et al., "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration," MLSys, 2024.
[3] T. Dettmers et al., "QLoRA: Efficient Finetuning of Quantized Language Models," NeurIPS, 2023.
[4] G. Xiao et al., "SmoothQuant," ICML, 2023.
[5] T. Dettmers et al., "The case for 4-bit precision: k-bit Inference Scaling Laws," ICML, 2023.
[6] G. Gerganov et al., "llama.cpp / GGUF," GitHub, 2023–2025.
[7] W. Shao et al., "OmniQuant," ICLR, 2024.
[8] Z. Liu et al., "KIVI: Asymmetric KV Cache Quantization," ICML, 2024.
[9] W. Huang et al., "BiLLM," ACL, 2024.
[10] NVIDIA, "TensorRT-LLM," 2024.
[11] W. Kwon et al., "PagedAttention / vLLM," SOSP, 2023.
[12] B. Jacob et al., "Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference," CVPR, 2018.
