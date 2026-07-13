---
schema_version: '1.0'
id: federated-learning-iot
title: 联邦学习与物联网：隐私保护下的分布式智能
layer: 5
content_type: survey
difficulty: advanced
reading_time: 28
prerequisites:
  - async-federated-learning
  - privacy-computing-tee-fl
tags:
  - 联邦学习
  - FedAvg
  - Non-IID
  - 个性化FL
  - FedGPA
  - 隐私保护
  - 边缘训练
  - IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 联邦学习与物联网：隐私保护下的分布式智能

> **难度**：🟠 进阶 | **领域**：联邦学习、隐私、物联网 | **阅读时间**：约 28 分钟

## 日常类比

连锁餐饮想优化口味：传统做法是把各店顾客反馈集中到总部——隐私与带宽都头疼。

**联邦学习（Federated Learning, FL）** 换做法：每店用本地反馈训"口味模型"，只把**模型参数**（不是顾客数据）交给总部做平均，再发回各店。几轮后，各店模型吸收了全国经验，原始数据从未离店[1]。

## 摘要

物联网（Internet of Things, IoT）数据天然分散、受法规约束，适合"数据不动、模型动"。本文沿 FedAvg → FedProx → SCAFFOLD → FedBN → 个性化方法 → FedGPA 梳理 Non-IID 对策，并讨论通信、异构、安全与应用。文中准确率数字来自各论文报告的实验设定，不可直接外推到任意传感器部署[1][2][5]。

## 1. 什么是联邦学习

一句话：多设备协作训练共享模型，原始数据留在本地，交换参数或梯度[1]。

IoT 特别需要 FL 的三点：

| 动机 | 说明 |
|------|------|
| 数据分散 | 海量终端各自产生数据，全量上云不现实 |
| 隐私合规 | 医疗/家居/产线数据受 GDPR 等约束 |
| 本地适应 | 希望模型在边缘持续进化，而非只靠云端下发 |

## 2. FedAvg：起点

### 2.1 流程

```
初始化全局模型 w₀
每轮 t：
  1. 选 C 比例客户端
  2. 下发 wₜ
  3. 各客户端本地 SGD E 个 epoch → wₜ₊₁ᵏ
  4. 服务器按数据量加权平均
```

关键超参：参与比例 \(C\)、本地轮数 \(E\)、batch \(B\)。\(E\) 大省通信，但加剧客户端漂移[1]。

### 2.2 为何在 IoT 上吃瘪

FedAvg 隐含独立同分布（Independent and Identically Distributed, IID）假设；真实 IoT 几乎总是 Non-IID：

| 偏斜类型 | IoT 表现 |
|----------|---------|
| 标签偏斜 | ICU 与门诊传感器所见类别比例迥异 |
| 特征偏斜 | 同型号传感器在高温车间 vs 空调房分布不同 |
| 数量偏斜 | 全天候设备与偶发设备数据量可差几个数量级 |

在图像基准的极端 Non-IID 划分下，FedAvg 相对 IID 设定可出现显著准确率下降甚至难收敛；具体幅度随数据集与划分而变[1][2]。

## 3. 应对 Non-IID：算法演进

### 3.1 FedProx

本地目标加近端项 \((\mu/2)\|w-w_t\|^2\)，限制本地模型跑离全局；\(\mu=0\) 退回 FedAvg。报告称在高度异构设定下收敛更稳，并对掉队设备更友好[2]。

### 3.2 SCAFFOLD

用控制变量修正客户端漂移；理论对数据异质性更不敏感，但每轮额外传控制变量，通信量约翻倍——带宽紧张的 IoT 需权衡[3]。

### 3.3 FedBN

联邦聚合时跳过批归一化（Batch Normalization, BN）层，让各客户端保留本地统计。实现极简，在特征偏斜场景常有几个百分点量级的收益报告[4]。

### 3.4 算法对比

| 算法 | 发表 | 核心策略 | 通信 | Non-IID 倾向 | IoT 适用 |
|------|------|----------|------|-------------|---------|
| FedAvg | 2017 | 加权平均 | 基准 | 弱 | 高（简单）[1] |
| FedProx | 2020 | 近端正则 | 基准 | 中 | 高[2] |
| SCAFFOLD | 2020 | 控制变量 | ~2× | 强 | 中（通信贵）[3] |
| FedBN | 2021 | 不聚合 BN | ≤基准 | 中（特征偏斜） | 高[4] |
| FedNova | 2020 | 归一化平均 | 基准 | 中 | 高 |
| MOON | 2021 | 对比正则 | 基准 | 中强 | 中 |
| Per-FedAvg | 2020 | 元学习 | 基准 | 强 | 低（算力重） |

## 4. 个性化联邦学习

全局"一个模型打天下"在南北供暖/空调等温控场景常不成立。个性化联邦学习（Personalized FL, PFL）在协作的同时保留本地适配。

| 类别 | 代表 | 优势 | 劣势 | IoT 场景 |
|------|------|------|------|---------|
| 参数解耦 | FedBN, FedPer | 简单、通信省 | 需定哪些层共享 | 多类型传感器 |
| 模型插值 | APFL, Ditto | 连续调节个性化 | 超参敏感 | 地域差异 |
| 元学习 | Per-FedAvg | 新客户端快适应 | 二阶/算力重 | 冷启动 |
| 聚类 | IFCA, CFL | 自动分组 | 组数难定 | 多区域 |
| 蒸馏 | FedDF, FedMD | 支持异构模型 | 常需公共数据 | 异构设备群 |

## 5. 前沿：FedGPA（INFOCOM 2025）

**问题**：全员平均可能负迁移；聚类又要额外通信探相似性。

**思路**：维护客户端更新方向的相似性，按"有用程度"加权聚合，并在训练早期偏均匀、后期偏个性化，以降低负迁移[5]。

作者在 CIFAR-10（Dirichlet 强 Non-IID）与 FEMNIST 等基准上报告个性化准确率优于若干经典基线，并称相对部分聚类方法可用更少轮次达到相近精度——**数字以原论文表格为准，迁移到传感器任务需重测**[5]。

对 IoT 的启示：同气候区土壤传感器可互借力，跨气候带强行聚合可能有害；选择性吸收比一刀切平均更贴现场。

## 6. IoT 特殊挑战

### 6.1 通信

LoRa / NB-IoT 等低速链路传完整深度模型不现实。常见手段：

| 手段 | 思路 | 代价 |
|------|------|------|
| 梯度压缩 | 只传 top-k 分量[8] | 可能损精度 |
| 稀疏更新 | 只传变化参数 | 实现复杂 |
| 量化 | 8-bit / 符号梯度 | 噪声增大 |
| 参数高效微调 | 只传 LoRA 等适配器[9] | 依赖预训练底座 |

Deep Gradient Compression 等工作报告在高压缩率下仍可保持接近基线精度，但取决于任务与实现[8]。

### 6.2 设备异构

MCU 与 Jetson 算力可差数量级。HeteroFL 等允许不同宽度子模型；蒸馏可在异构架构间传知识[7]。

### 6.3 安全

不传原始数据 ≠ 隐私自动满足。梯度反演可从更新中近似恢复样本[6]；恶意客户端可投毒。防御：差分隐私、安全聚合、Byzantine 鲁棒聚合——均有精度或延迟代价。

### 6.4 挑战汇总

| 挑战 | IoT 表现 | 代表对策 | 代价 |
|------|---------|---------|------|
| 通信瓶颈 | 低速链传大模型 | 压缩/量化/PEFT | 精度/复杂度 |
| Non-IID | 环境差异大 | Prox/SCAFFOLD/PFL | 算法复杂 |
| 异构 | MCU vs GPU | HeteroFL/蒸馏 | 设计复杂 |
| 隐私 | 梯度泄露 | DP/安全聚合 | 效用下降 |
| 投毒 | 失陷终端 | 鲁棒聚合 | 收敛变慢 |
| 掉线 | 电池/信号 | 异步 FL/部分参与 | 一致性↓ |

## 7. 应用案例（报告口径）

| 场景 | 做法要点 | 文献/报告倾向 |
|------|---------|---------------|
| 多中心医疗 | 影像不出院，协作分割/诊断 | 性能可接近集中训练量级，视任务而定[11] |
| 智能键盘 | 本地语言模型 + 全局聚合 | 大规模商用 FL 典范[1] |
| 工业预测维护 | 厂间不共享原始振动/工艺数据 | 行业报告称可提升故障识别，需独立验证 |
| 车联网 | 车端训练、路侧聚合 | 合规驱动，增益视数据与标注 |

## 8. 趋势（2024–2025）

- **联邦微调大模型**：LoRA 等只传极少参数，通信可降两个数量级量级[9]。
- **去中心化 FL**：无单点服务器，适合 P2P IoT，收敛与拓扑仍开放。
- **编排框架**：Flower、NVIDIA FLARE 等降低跨组织落地成本[10]。

## 9. 局限、挑战与可改进方向

### 1. 基准≠传感器现场

**局限**：CIFAR/FEMNIST 结论难直接映射到振动、电表、摄像头多模态流[1][5]。
**改进**：用真实 Non-IID 传感器划分重评；报告通信字节与能耗，不只准确率。

### 2. 隐私声明过度

**局限**：明文梯度仍可能泄露；加噪不足时合规叙事站不住[6]。
**改进**：明确威胁模型；默认安全聚合 + 适度 DP；审计成员推断风险。

### 3. 弱网与掉队

**局限**：同步 FedAvg 被最慢设备拖死；丢包导致偏置聚合。
**改进**：异步/半异步；参与感知加权；本地更多步 + 压缩上传。

### 4. 个性化与全局的张力

**局限**：过度个性化失去协作红利；过度全局伤害本地工况。
**改进**：相似性门控（如 FedGPA 思路）[5]；按区域/设备类型分层聚合。

## 参考文献

[1] B. McMahan et al., "Communication-Efficient Learning of Deep Networks from Decentralized Data," AISTATS, 2017.
[2] T. Li et al., "Federated Optimization in Heterogeneous Networks (FedProx)," MLSys, 2020.
[3] S. P. Karimireddy et al., "SCAFFOLD: Stochastic Controlled Averaging for Federated Learning," ICML, 2020.
[4] X. Li et al., "FedBN: Federated Learning on Non-IID Features via Local Batch Normalization," ICLR, 2021.
[5] FedGPA authors, "Federated Learning with Global Personalized Aggregation," IEEE INFOCOM, 2025.
[6] L. Zhu et al., "Deep Leakage from Gradients," NeurIPS, 2019.
[7] E. Diao et al., "HeteroFL: Computation and Communication Efficient Federated Learning for Heterogeneous Clients," ICLR, 2021.
[8] Y. Lin et al., "Deep Gradient Compression: Reducing the Communication Bandwidth for Distributed Training," ICLR, 2018.
[9] J. Zhang et al., "FedPETuning: When Federated Learning Meets the Parameter-Efficient Tuning Methods of Foundation Models," ACL Findings, 2024.
[10] D. J. Beutel et al., "Flower: A Friendly Federated Learning Framework," 相关期刊/预印本, 2024.
[11] M. J. Sheller et al., "Federated Learning in Medicine: Facilitating Multi-Institutional Collaborations without Sharing Patient Data," Scientific Reports, 2020.
