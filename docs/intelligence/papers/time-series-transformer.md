---
schema_version: '1.0'
id: time-series-transformer
title: 时序预测 Transformer 模型
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - transformer-edge-deployment
tags:
- 时序预测
- Transformer
- Informer
- PatchTST
- Autoformer
- iTransformer
- DLinear
- 边缘部署
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 时序预测 Transformer 模型

> **难度**：🟡 中级 | **领域**：时序预测 / Transformer / 边缘部署 | **阅读时间**：约 22 分钟

## 日常类比

看长剧猜下一集：长短期记忆网络（Long Short-Term Memory, LSTM）像按顺序回忆，越早越易忘；Transformer 像带索引的笔记本，可直接翻到相关集——即自注意力（Self-Attention）[6]。传感器温度、压力、负荷流同理：可同时关注「昨天同时段」与「上周同星期」，不受逐步衰减限制。但原版注意力复杂度约 \(O(N^2)\)，长序列贵，故有 Informer、Autoformer、PatchTST、iTransformer 等变体[1][2][3][4]。

## 摘要

本文对比时序 Transformer 族与线性基线（DLinear），说明稀疏/自相关/分块/变量维注意力等机制，以及边缘瘦身与选型决策，并列出局限与改进。基准均方误差（Mean Squared Error, MSE）为公开论文在特定数据集与协议下的量级，换划分或归一化后不可直接横比。

## 1 任务与相对 LSTM

给定回看窗 \(x_{1:L}\)，预测 \(x_{L+1:L+H}\)。

| 挑战 | LSTM | Transformer |
|------|------|-------------|
| 长依赖 | 易衰减 | 任意位置直连[6] |
| 多周期 | 常靠手工特征 | 可学周期/相关结构 |
| 训练并行 | 逐步 | 位置可并行 |
| 多变量耦合 | 需堆叠设计 | 多头可建模交互 |

## 2 代表模型

| 模型 | 核心机制 | 复杂度倾向 | 典型用途 |
|------|---------|-----------|---------|
| Informer | ProbSparse 注意力 | 约 \(O(L\log L)\) 量级[1] | 长序列预测 |
| Autoformer | 自相关 + 分解 | 周期延迟聚合[2] | 强周期序列 |
| PatchTST | 分块 + 通道独立[3] | token 数随 patch 降 | 长预测、边缘友好配置 |
| iTransformer | 变量维注意力[4] | 随变量数缩放 | 多变量耦合强 |
| DLinear | 分解 + 线性[5] | 极低 | 强基线/极低延迟 |
| TimesNet 等 | 时频/二维变化[7] | 中 | 通用分析 |

**Informer**：用采样估计 query「活跃度」，只对 top query 算全注意力[1]。
**Autoformer**：频域相关找 top 延迟再聚合[2]。
**PatchTST**：类似视觉 Transformer（Vision Transformer, ViT）的 patch，通道独立共享骨干[3]。
**iTransformer**：token=变量，整段历史嵌入后做变量间注意力[4]。
**DLinear**：简单线性在多基准上极强，迫使重新审视「是否必须上 Transformer」[5]。

## 3 基准表现（示意量级）

公开电力变压器温度等基准（如 ETTh1）上，论文报告的相对关系大致为：较新的 PatchTST / iTransformer 常优于早期 Informer；DLinear 以极少参数逼近甚至局部超过部分 Transformer；预测地平线越长，表达力差异往往更明显——**具体 MSE 以原论文表为准，下表仅示意排序而非可引用绝对值**[3][4][5]。

| 模型族 | 短地平线 | 长地平线 | 参数/算力 | 边缘友好 |
|--------|---------|---------|-----------|---------|
| LSTM | 中 | 偏弱 | 低–中 | 好 |
| Informer / Autoformer | 较好 | 较好 | 中–高 | 中 |
| PatchTST / iTransformer | 优（多设定） | 优（多设定） | 中 | 中–好（可缩配置） |
| DLinear | 强基线 | 强基线 | 极低 | 最好 |

## 4 边缘部署

| 策略 | 压缩倾向 | 精度风险 | 平台 |
|------|---------|---------|------|
| 知识蒸馏 | 数倍–十余倍 | 小–中 | 单板电脑/边缘 GPU |
| INT8 量化 | 约 4× 体积 | 通常较小 | NPU/DSP/CPU |
| 结构化剪枝 | 约 2–4× | 中 | 通用 CPU |
| 小配置 PatchTST | 原生轻 | 相对大模型掉点 | 树莓派等 |

边缘配置思路：更大 patch / 非重叠、降低 `d_model` 与层数、缩短回看与预测长度，再导出 ONNX Runtime 实测。宣称「数毫秒」必须注明硬件与序列长度。

## 5 应用与何时不用 Transformer

| 场景 | 输入倾向 | 输出 | 价值点 |
|------|---------|------|--------|
| 负荷预测 | 历史负荷+天气+日历 | 未来数十小时 | 错峰与采购 |
| 剩余寿命 | 振动/温度/电流 | 健康指数趋势 | 减少非计划停机 |
| 局地气象 | 微站多要素 | 未来数小时 | 灌溉/光伏功率 |

**更宜简单模型**：序列很短且模式简单；样本极少；硬延迟亚毫秒；纯周期可用傅里叶/统计法。小数据上 Transformer 更易过拟合[5]。

| 维度 | LSTM | Transformer |
|------|------|-------------|
| 长序列 | 弱 | 强 |
| 训练吞吐 | 低 | 高 |
| 可解释 | 隐状态难读 | 注意力可可视化（仍需谨慎解读） |
| 小数据 | 相对稳 | 易过拟合 |
| 增量步进 | 自然 | 需专门设计 |

## 6 局限、挑战与可改进方向

### 1. 基准协议敏感

**局限**：同一模型换归一化、回看长度或零样本划分，排名可翻转；DLinear 已暴露部分「虚假复杂度」收益[5]。
**改进**：固定协议复现；必报强线性/统计基线；多数据集与多随机种子。

### 2. 分布漂移与非平稳

**局限**：工厂换产线、电网季节切换后，历史注意力模式失效。
**改进**：可逆实例归一化等；在线微调；显式非平稳模块[10]；监控预测残差告警。

### 3. 边缘延迟与内存被低估

**局限**：论文 GPU 毫秒数不能代表树莓派多变量长窗。
**改进**：目标硬件 profiling；优先 DLinear/小 PatchTST；量化与算子融合。

### 4. 多变量泄漏与通道独立误用

**局限**：通道独立忽略关键耦合；变量维注意力在变量极多时内存涨。
**改进**：按物理分组混合架构；对耦合做消融；变量多时降维或稀疏注意力。

### 5. 概率预测与决策缺口

**局限**：点预测 MSE 最优不等于调度/库存决策最优。
**改进**：分位数/扩散等概率头[8][9]；用业务损失（缺货、弃光）做最终指标。

## 参考文献

[1] H. Zhou et al., "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting," AAAI, 2021.
[2] H. Wu et al., "Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting," NeurIPS, 2021.
[3] Y. Nie et al., "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers," ICLR, 2023.
[4] Y. Liu et al., "iTransformer: Inverted Transformers Are Effective for Time Series Forecasting," ICLR, 2024.
[5] A. Zeng et al., "Are Transformers Effective for Time Series Forecasting?," AAAI, 2023.
[6] A. Vaswani et al., "Attention Is All You Need," NeurIPS, 2017.
[7] H. Wu et al., "TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis," ICLR, 2023.
[8] B. Lim et al., "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting," International Journal of Forecasting, 2021.
[9] A. Das et al., "A Decoder-Only Foundation Model for Time-Series Forecasting," ICML, 2024.
[10] Y. Liu et al., "Non-stationary Transformers: Exploring the Stationarity in Time Series Forecasting," NeurIPS, 2022.
[11] S. Li et al., "Enhancing the Locality and Breaking the Memory Bottleneck of Transformer on Time Series Forecasting," NeurIPS, 2019.
[12] N. Kitaev et al., "Reformer: The Efficient Transformer," ICLR, 2020.
