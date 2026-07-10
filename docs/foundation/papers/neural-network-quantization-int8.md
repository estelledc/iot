---
schema_version: '1.0'
id: neural-network-quantization-int8
title: 神经网络INT8量化在边缘设备上的实现
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - tflite-micro-model-optimization
  - model-compression-pruning-distillation
tags:
  - INT8量化
  - PTQ
  - QAT
  - TFLite
  - CMSIS-NN
  - 边缘推理
  - 嵌入式AI
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 神经网络INT8量化在边缘设备上的实现

> **难度**：🔴 高级 | **领域**：边缘推理 | **关键词**：INT8, PTQ, QAT, scale/zero-point | **阅读时间**：约 16 分钟

## 日常类比

全精度浮点像用天平称菜精确到毫克；**INT8 量化**像改用只读到克的弹簧秤——更快更省内存，但要选好刻度（scale）和零点，不然菜谱（模型）味道就变了。MCU/NPU 上 INT8 乘加往往比 FP32 快且省电一个数量级量级宣称，以算子库与芯片为准[1][2]。

## 摘要

讲清对称/非对称量化公式、PTQ 与 QAT、按张量/按通道与混合精度，并落到 TFLite/CMSIS-NN。精度损失为任务常见量级，须在目标数据集与板子上验收[3]。

## 1. 收益与表示

| 收益 | 表现 |
|------|------|
| 体积 | 权重大约 4× 缩小（相对 FP32） |
| 带宽/缓存 | 更友好 |
| 吞吐 | 依赖 INT8 kernel/NPU |

\[
x_{int} \approx \mathrm{round}(x/s) + z
\]
对称常令 \(z=0\)；非对称更好覆盖激活分布。按通道权重量化通常优于按张量[1]。

## 2. PTQ 与 QAT

| 方法 | 流程 | 适用 |
|------|------|------|
| PTQ | 校准集估 min/max 或直方图 | 快速、数据少 |
| QAT | 训练中模拟量化 | 精度敏感 |

校准算法：MinMax、KL、百分位等；离群值会撑爆动态范围。敏感层（首层/注意力/小通道）可留 FP16/FP32 做混合精度[4][5]。

## 3. 工具链与 MCU

TFLite/ONNX Runtime/TensorRT 等提供校准与导出；MCU 侧 CMSIS-NN、TFLite Micro 吃 INT8 图。K210 等 NPU 有各自量化器——对齐训练工具与部署后端是第一坑[2][6]。

| 任务倾向 | 损失直觉 |
|----------|----------|
| 分类 | 常 <1% Top-1 量级可达成 |
| 检测 | 更敏感 |
| 语音/ASR | 视模型 |

## 4. 局限、挑战与可改进方向

### 1. 校准集不代表性

**局限**：PTQ 在真实光照/噪声下崩。
**改进**：用设备域数据校准；不够则 QAT[3]。

### 2. 离群激活

**局限**：偶发大激活迫使 scale 变粗。
**改进**：百分位裁剪、按通道、敏感层混合精度[4]。

### 3. 算子不支持

**局限**：导出后仍回退到浮点慢路径。
**改进**：换支持的算子集；查 TFLite Micro/NPU 兼容表[6]。

### 4. 只报模型体积

**局限**：峰值 Arena/堆不够仍失败。
**改进**：以内存剖析与延迟门禁验收[2]。

## 总结

INT8 是边缘部署默认档：先 PTQ，精度不够再 QAT/混合精度。刻度与零点选错比“有没有量化”更致命；以目标芯片 kernel 为准做验收。

## 参考文献

[1] Jacob et al., Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference, *CVPR* 2018.
[2] ARM CMSIS-NN 文档与论文.
[3] TensorFlow Lite 训练后量化与 QAT 指南.
[4] Nagel et al., 量化白皮书 / *A White Paper on Neural Network Quantization*.
[5] TensorRT INT8 校准文档.
[6] TFLite Micro 与 MCU 部署指南.
[7] ONNX Quantization 工具文档.
[8] 按通道权重量化相关论文.
[9] MLPerf Tiny 基准公开结果说明.
[10] 混合精度量化自动搜索相关工作.
[11] K210 / 其他边缘 NPU 量化用户指南.
[12] 激活离群值与量化误差分析文献.
