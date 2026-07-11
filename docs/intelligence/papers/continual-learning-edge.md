---
schema_version: '1.0'
id: continual-learning-edge
title: 边缘持续学习：学新知识不忘旧知识
layer: 5
content_type: technical_analysis
difficulty: advanced
reading_time: 28
prerequisites:
  - on-device-training
tags:
- 持续学习
- 灾难性遗忘
- EWC
- 经验回放
- 概念漂移
- PackNet
- 边缘AI
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 边缘持续学习：学新知识不忘旧知识

> **难度**：🟠 挑战 | **领域**：持续学习（Continual Learning, CL）、边缘智能 | **阅读时间**：约 28 分钟

## 日常类比

只有一块白板的老师：第一学期写满数学，第二学期擦一部分写物理，第三学期再擦写化学。期末化学还行、物理勉强、数学几乎没了——这就是**灾难性遗忘**（Catastrophic Forgetting）。

神经网络参数空间像这块白板：用新数据梯度更新时，会覆盖旧任务学到的权重配置。物联网（IoT）设备还常**不能**把历史数据全存下来重训，必须在"只看新数据"时既学会新知识又保住旧能力[1]。

## 摘要

本文梳理边缘场景下的持续/增量学习：遗忘机制，正则化（EWC/SI/MAS）、架构（PackNet/SupSup）、回放（ER/DER++）三大策略，内存高效回放与概念漂移检测，以及 LoRA/提示式 CL 等进展，并给出 IoT 选型与局限改进[1][4][10]。

## 1 灾难性遗忘

形式化：先在任务 A 得到 \(\theta_A^*\)，再在 B 上标准 SGD 只优化 \(L_B\)，得到的 \(\theta_B^*\) 可能远离 \(\theta_A^*\)，A 上性能骤降。

教学示意：ResNet 类模型在 CIFAR 前后半类顺序训练时，旧类准确率可从高位跌至近随机——遗忘主要来自优化覆盖，而非单纯模型过小[1]。

IoT 特有压力：非平稳数据流、旧数据不可重访；季节变化、传感器更换、语音命令增量等。存储不足以保留全历史联合训练。

## 2 三大策略家族

### 2.1 正则化：保护重要权重

**EWC**（Elastic Weight Consolidation）：用 Fisher 信息对角近似衡量权重对旧任务重要性，新任务损失加二次惩罚，锁住重要参数[1]。

\[
L = L_{\text{new}} + \frac{\lambda}{2}\sum_i F_i(\theta_i-\theta_{A,i}^*)^2
\]

在 Permuted MNIST 等基准上可显著降遗忘；但每任务存 Fisher 与最优权重，任务增多时存储线性涨——MCU 不友好。

**SI**（Synaptic Intelligence）：训练中在线累积重要性，免离线 Fisher[2]。**MAS**：对输出敏感度作重要性，可少依赖任务标签[相关 2018 工作]。

### 2.2 架构：专属参数子集

**PackNet**：训完剪枝→冻结重要权重→剩余容量训新任务；旧任务零遗忘，但容量逐渐耗尽[3]。**SupSup**：每任务二值掩码，推理按任务 ID 激活子网络。

### 2.3 回放：小缓冲重温

**ER**：固定缓冲 + reservoir sampling，新 batch 混旧样本。小缓冲即可大幅抬平均准确率（相对裸微调）[4]。**GDumb**：几乎只维护缓冲并周期性重训，质疑复杂方法必要性[5]。**DER++**：回放 logits 做蒸馏，常优于硬标签 ER[4]。

### 2.4 对比

| 维度 | 正则化 (EWC/SI) | 架构 (PackNet) | 回放 (ER/DER++) |
|------|-----------------|----------------|-----------------|
| 遗忘 | 中（软约束） | 近零（硬冻结） | 低（视缓冲） |
| 额外存储 | Fisher/分数 | 掩码 | 数据/特征 |
| 任务数 | 无硬限，质量降 | 容量耗尽 | 无硬限 |
| 任务 ID | 常需要 | 推理常需要 | 可不需要 |
| 实现 | 中 | 高 | 低 |
| IoT | 存储可控时好 | 掩码管理复杂 | 视缓冲预算 |

Split-CIFAR-100 等基准上，DER++ 类回放常处前列；精确数字随协议而变，横比须固定缓冲与划分[4][5]。

## 3 IoT 内存高效 CL

224×224 RGB 约百 KB 量级，数百张即可达数十 MB，可能大于 MobileNet 级模型。

| 手法 | 思想 | 优点 | 风险 |
|------|------|------|------|
| 特征回放 | 存中间特征 | 体积小一个数量级以上 | 特征随骨干更新而过时 |
| 生成式回放 | 小 VAE/GAN 记分布 | 存模型非样本 | 训练难、模式崩塌 |
| 量化回放 | INT4/INT2 存样本 | 实现简单 | 效用略降 |

| 设备（示意） | 可用内存量级 | 原始图像缓冲 | 特征缓冲 |
|--------------|--------------|---------------|----------|
| MCU（数百 KB–数 MB） | 极紧 | 几乎不可行 | 数十–数千条特征 |
| ESP32 类 | 数 MB | 极少图像 | 更可行 |
| Jetson / RPi | GB 级 | 可较大缓冲 | 充裕 |

MCU 上特征回放几乎是默认选项；网关级才考虑原图 ER。

## 4 概念漂移

持续学习常假设任务边界已知；真实 IoT 多为渐进/无标注分布变化（Concept Drift）[10]。

| 类型 | 例子 |
|------|------|
| 渐进 | 传感器老化偏置 |
| 突变 | 换产线/换镜头 |
| 循环 | 季节性外观变化 |

| 方法 | 原理 | 开销 |
|------|------|------|
| ADWIN[11] | 自适应窗口统计检验 | 低 |
| Page-Hinkley | 累积和检均值偏移 | 极低 |
| DDM | 监测错误率突增 | 低 |
| KSWIN | KS 检验窗口 | 中 |

闭环：漂移检测 → 触发微调/回放/更新基线；无漂移则不浪费算力。

## 5 前沿（简）

O-LoRA 等：每任务新 LoRA、旧适配器冻结[12]。L2P/DualPrompt：提示池 + 冻骨干，近零改权重遗忘[6][7]。CLS-ER：互补学习系统双模型蒸馏[8]。联邦类增量 FedCIL：多设备不同增量类别[13]。

## 6 实验对比（示意）

| 方法 | 缓冲 | 相对裸微调 | 遗忘 |
|------|------|------------|------|
| Fine-tune | 0 | 基准最差 | 很高 |
| EWC/SI | 0 | 小幅改善 | 高 |
| PackNet | 0 | 高（容量内） | 近 0 |
| ER / DER++ | 小–中 | 通常最好档 | 中–低 |
| 特征 ER | 特征 | 略低于原图 ER | 中 |

工业质检类模拟：云端全量重训为上界；边缘 ER/EWC/特征回放在内存与更新时延间折中——具体 mAP/时延以现场数据为准。

## 7 局限、挑战与可改进方向

### 1. 无标签流占主导

**局限**：传感器流常无类别标签，有监督 CL 基准难直接迁移。
**改进**：自监督表示 + 漂移触发；半监督/活跃学习标少量关键帧；与对比学习管线结合。

### 2. 任务边界未知

**局限**：错检漂移导致误更新或漏更新，造成静默遗忘。
**改进**：多检测器投票；更新前在缓冲上做保留集校验；失败则回滚检查点。

### 3. 回放隐私与存储合规

**局限**：原图缓冲可能含人脸/工位隐私，与"数据不出域"政策冲突。
**改进**：特征/合成回放；缓冲加密与最短留存；联邦 CL 只传统计或适配器[13]。

### 4. 与设备端训练栈割裂

**局限**：LoRA/量化训练工具链与 CL 缓冲、Fisher 会计未统一。
**改进**：在 on-device-training 栈上挂统一"记忆模块"API；优先 LoRA+小回放。

### 5. 基准乐观

**局限**：清晰任务边界与平衡类别高估真实 IoT 表现。
**改进**：用含渐进漂移的现场日志评测；报告遗忘、缓冲字节、更新焦耳三联指标[10]。

## 参考文献

[1] J. Kirkpatrick et al., "Overcoming catastrophic forgetting in neural networks," PNAS, 2017.
[2] F. Zenke, B. Poole, S. Ganguli, "Continual Learning Through Synaptic Intelligence," ICML, 2017.
[3] A. Mallya and S. Lazebnik, "PackNet: Adding Multiple Tasks to a Single Network by Iterative Pruning," CVPR, 2018.
[4] P. Buzzega et al., "Dark Experience for General Continual Learning: a Strong, Simple Baseline," NeurIPS, 2020.
[5] A. Prabhu, P. Torr, P. Dokania, "GDumb: A Simple Approach that Questions Our Progress in Continual Learning," ECCV, 2020.
[6] Z. Wang et al., "Learning to Prompt for Continual Learning," CVPR, 2022.
[7] Z. Wang et al., "DualPrompt: Complementary Prompting for Rehearsal-free Continual Learning," ECCV, 2022.
[8] E. Arani et al., "Learning Fast, Learning Slow: A General Continual Learning Method based on Complementary Learning System," ICLR, 2022.
[9] F. Wiewel and B. Yang, "Entropy-based Sample Selection for Experience Replay," 相关持续学习工作, 2021.
[10] J. Gama et al., "A Survey on Concept Drift Adaptation," ACM Computing Surveys, 2014.
[11] A. Bifet and R. Gavaldà, "Learning from Time-Changing Data with Adaptive Windowing," SDM, 2007.
[12] X. Wang et al., "Orthogonal Subspace Learning for Language Model Continual Learning (O-LoRA)," 相关工作 / arXiv, 2023–2024.
[13] J. Dong et al., "Federated Class-Incremental Learning," CVPR, 2023.
[14] G. I. Parisi et al., "Continual Lifelong Learning with Neural Networks: A Review," Neural Networks, 2019.
