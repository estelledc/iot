---
schema_version: '1.0'
id: self-supervised-pretraining-device
title: 自监督预训练在端侧的应用
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - contrastive-learning-sensor
  - on-device-training
tags:
- 自监督
- SimCLR
- MoCo
- MAE
- TS2Vec
- 少样本
- 端侧预训练
- 传感器
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 自监督预训练在端侧的应用

> **难度**：🟡 中级 | **领域**：自监督学习 / 时序 / 端侧 AI | **阅读时间**：约 22 分钟

## 日常类比

到新城市没有地图（无标注）：散步记住路口相连（对比学习）、猜被遮挡建筑（掩码预测）、判断两张照片是否同地不同角（相似性）。有人问「最近超市」时，已有空间认知可快速答。

自监督预训练（Self-Supervised Learning, SSL）即「先探索再答题」。物联网（Internet of Things, IoT）设备产生海量无标注传感器流，故障等标注极稀。模型先从无标注数据学表示，再用少量标注微调到下游任务[10]。

## 摘要

本文梳理对比学习（SimCLR、动量对比 MoCo）、时序掩码自编码器（Masked Autoencoder, MAE）与 TS2Vec 等在端侧/边缘的适配，少样本微调与跨传感器迁移，并给出计算量级示意、局限与改进。准确率与时长数字为文献或教学量级，依赖数据集与硬件。

## 1 为何端侧需要自监督

| 场景 | 无标注 | 有标注 | 标注成本 |
|------|--------|--------|---------|
| 工业监控 | 海量连续流 | 故障样本极少 | 需专家 |
| 环境传感 | 连续采集 | 极端事件稀 | 事后标 |
| 可穿戴 | 近全天流 | 用户很少标 | 用户负担 |
| 智能电网 | 全网实时 | 故障极少 | 代价高 |

相对优势：吃无标注、可多下游复用、少样本适应、预训练可本地完成以减上传[8][10]。

## 2 对比学习

**SimCLR**：两视图增强 → 编码器 + 投影头 → NT-Xent / InfoNCE 损失；推理丢弃投影头[1]。IoT 时序常用一维卷积（1D Convolutional Neural Network, CNN）作编码器。

**时序增强须符合物理**：抖动（传感器噪声）、缩放（漂移）、时间扭曲（采样不稳）、通道丢弃（传感器失效）、裁剪拉伸。过强增强（如振动信号随意翻转）会破坏语义。文献在人体活动识别（Human Activity Recognition, HAR）等集上报告：合理组合增强相对无增强可有约十余个百分点量级的线性评估提升，**非通用保证**[9]。

**MoCo**：动量更新的键编码器 + 队列负样本，减轻大 batch 依赖，更贴边缘显存受限训练[2]。

| 方法 | 负样本来源 | Batch 压力 | 端侧训练友好度 |
|------|-----------|-----------|---------------|
| SimCLR | 同 batch | 高 | 中（要大 batch 或大显存）[1] |
| MoCo | 队列 | 较低 | 较好[2] |
| TS2Vec | 时间/实例层次 | 中 | 好（编码器轻）[4] |

## 3 掩码与层次对比

**时序 MAE**：按 patch 随机遮挡，编码器只看可见 patch，解码器重建被遮部分；掩码比例时序上常低于视觉（文献多试约四到六成量级）[3]。

**TS2Vec**：扩张因果卷积 + 时间维与实例维层次对比，面向通用时序表示[4]。相近思路还有时序邻域编码（Temporal Neighborhood Coding, TNC）、时序上下文对比（Temporal and Contextual Contrasting, TS-TCC）、时频一致性等[5][6][7]。

## 4 少样本适应

| 策略 | 做法 | 适用 |
|------|------|------|
| 线性探测 | 冻编码器，训线性头 | 标注极少、防过拟合 |
| 末层微调 | 解冻末几层 | 域差中等 |
| 原型网络 | 类中心距离分类 | 1–5 shot 量级 |

工业故障等 5-shot 设定下，文献常报告自监督预训练显著高于随机初始化；具体百分点随任务与划分变化，宜报告置信区间而非单点[4][10]。

## 5 端侧算力示意

| 方法（小配置） | 数据量级 | 边缘 GPU 训练时长（示意） | 内存（示意） | 模型体积（示意） |
|----------------|----------|---------------------------|-------------|-----------------|
| SimCLR | 约万级样本 | 小时量级 | 约数 GB | 约数 MB |
| MoCo | 约万级 | 略短于 SimCLR | 略低 | 约数 MB |
| MAE | 约万级 | 偏长 | 偏高 | 略大 |
| TS2Vec | 约万级 | 相对短 | 相对低 | 约 1 MB 量级 |

微调常只更新末层、小 batch、少 epoch，分钟到小时级取决于板卡与样本数——**以本机 profiling 为准**。

## 6 跨传感器迁移

| 源 → 目标（示意） | 直接迁移 | 目标域无标注自监督适应后 |
|-------------------|----------|---------------------------|
| 加速度计 → 陀螺仪 | 中等 | 明显回升 |
| 振动 → 声学 | 中偏低 | 回升 |
| 温度 → 湿度 | 偏低 | 中等 |
| 电流 → 功率 | 较高 | 高 |

物理相关模态（同反映机械状态）更易迁；无关模态需目标域继续自监督或重新预训练[10]。

## 7 局限、挑战与可改进方向

### 1. 增强破坏物理语义

**局限**：从视觉抄来的强增强在振动/电力波形上制造「不可能」样本，表示学偏。
**改进**：按传感器物理设计增强；用领域专家审增强样例；对比「增强过强」消融。

### 2. 负样本过易或过难

**局限**：对比学习若负样本差异过大，模型只学粗糙判别；过难则崩塌。
**改进**：调温度与队列；难负挖掘要谨慎；监控表示坍塌指标（如特征方差）。

### 3. 少样本微调过拟合

**局限**：几十条故障样本上全参微调易背标签噪声。
**改进**：默认线性探测/原型；强正则与早停；保留无标注继续自监督正则。

### 4. 端侧持续预训练的热与寿命

**局限**：边缘盒长时间满载训练触发降频，结果不可复现，并影响同机业务。
**改进**：夜间/空闲窗训练；功率封顶；优先云端预训练 + 端侧轻量适应。

### 5. 跨设备分布漂移未声明

**局限**：预训练在 A 厂线、微调在 B 厂线，论文数字不可迁移。
**改进**：报告设备/工况划分；强制域适应段；用目标域无标注做短自监督适应。

## 参考文献

[1] T. Chen et al., "A Simple Framework for Contrastive Learning of Visual Representations," ICML, 2020.
[2] K. He et al., "Momentum Contrast for Unsupervised Visual Representation Learning," CVPR, 2020.
[3] K. He et al., "Masked Autoencoders Are Scalable Vision Learners," CVPR, 2022.
[4] Z. Yue et al., "TS2Vec: Towards Universal Representation of Time Series," AAAI, 2022.
[5] S. Tonekaboni et al., "Unsupervised Representation Learning for Time Series with Temporal Neighborhood Coding," ICLR, 2021.
[6] E. Eldele et al., "Time-Series Representation Learning via Temporal and Contextual Contrasting," IJCAI, 2021.
[7] X. Zhang et al., "Self-Supervised Contrastive Pre-Training for Time Series via Time-Frequency Consistency," NeurIPS, 2022.
[8] C. Tang et al., "Exploring Contrastive Learning for Long-Tailed IoT Data," IoTDI, 2023.
[9] H. Haresamudram et al., "Contrastive Predictive Coding for Human Activity Recognition," UbiComp, 2021.
[10] X. Liu et al., "Self-Supervised Learning for Sensor Data: A Survey," ACM Computing Surveys, 2024.
[11] J.-Y. Franceschi et al., "Unsupervised Scalable Representation Learning for Multivariate Time Series," NeurIPS, 2019.
[12] A. van den Oord et al., "Representation Learning with Contrastive Predictive Coding," arXiv:1807.03748, 2018.
