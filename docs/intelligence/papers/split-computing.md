---
schema_version: '1.0'
id: split-computing
title: 分割计算：DNN 端-边最优切分
layer: 5
content_type: technical_analysis
difficulty: advanced
reading_time: 24
prerequisites:
  - collaborative-inference-survey
  - model-compression-edge
tags:
- 分割计算
- Neurosurgeon
- SPINN
- 早退
- 端边协同
- DNN切分
- 特征隐私
- 延迟优化
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 分割计算：DNN 端-边最优切分

> **难度**：🟠 进阶 | **领域**：边缘推理 / 模型切分 | **阅读时间**：约 24 分钟

## 日常类比

翻译一封长信：自己英语一般（弱设备），朋友是专家但联络要时间（网络 + 服务器）。全自己翻慢且易错；整封拍照发给朋友则传输重。折中：自己先标关键词做「粗翻」，只寄压缩后的粗翻稿请朋友精修——这就是分割计算（Split Computing）：深度神经网络（Deep Neural Network, DNN）前几层在端侧提特征，中间张量往往小于原始输入，后半段在边缘/云完成[1][5]。

## 摘要

本文说明端–边切分点选择（Neurosurgeon、DADS、SPINN 等）、早退（Early Exit）、特征隐私与面向大语言模型（Large Language Model, LLM）的新约束，并给出局限与改进。加速比与能耗降幅来自各论文实验设定，换模型与链路后需重测。

## 1 为何有效

CNN 等网络随层深入，激活体积常先增后减，存在相对输入更小的瓶颈层；在瓶颈附近切分可显著减传输。权衡仍在：端侧多算 → 端延迟升、传输可能降；带宽高时可更早切。与协作推理对比：

| 维度 | 分割计算 | 协作推理 |
|------|---------|---------|
| 动机 | 单端算力不足 + 带宽紧 | 单机装不下整模 |
| 角色 | 弱端 + 强边/云 | 多台对等或流水线 |
| 切分 | 常单点两段 | 多层多段 |
| 目标 | 延迟/能耗/隐私联合 | 延迟/吞吐 |
| 代表 | Neurosurgeon、SPINN[1][3] | Jupiter、EdgeShard 等 |

## 2 切分点算法

**Neurosurgeon**：对每层测端延迟 \(t_{device}\)、云延迟 \(t_{server}\)、输出传输 \(t_{transfer}\)，穷举切分点 \(k\) 最小化

\[
\sum_{l=1}^{k} t_{device}(l) + t_{transfer}(k) + \sum_{l=k+1}^{L} t_{server}(l)
\]

最优 \(k\) 强依赖带宽与端算力：带宽高时切点偏前，带宽极低时「全本地」可能优于任何切分。论文在 AlexNet 等设定下报告相对纯云可达约数倍延迟改善与可观能耗下降量级——**非跨模型保证**[1]。

**DADS**：运行时测带宽，查「带宽→切分点」表做动态切换；并扩展到有向无环图（Directed Acyclic Graph, DAG）结构（如含跳跃连接的网络）[2]。

**SPINN**：水平切分 + 垂直早退联合；简单样本可在端侧浅层退出，难样本再上云；并支持先出粗结果再精修的渐进推理。相对纯切分，论文报告平均延迟可再降约三成量级（设定相关）[3]。

| 系统 | 年份 | 切分 | 早退 | 动态 | DAG | 延迟/能耗（论文量级） |
|------|------|------|------|------|-----|----------------------|
| Neurosurgeon | 2017 | 单点 | 否 | 否 | 否 | 约 2–3× 延迟改善量级；能耗明显降[1] |
| DADS | 2019/2020 | 动态单点 | 否 | 是 | 是 | 进一步动态收益[2] |
| SPINN | 2020 | 切分+早退 | 是 | 是 | 有限 | 平均延迟再降一截[3] |
| BranchyNet 等 | 2016+ | — | 是 | — | — | 早退奠基[4] |

## 3 早退

观察：多数输入「简单」，仅少数需全深度。ImageNet 等设定下，文献报告相当比例样本可在较浅层以高置信度正确分类；工业质检「绝大多数正常品」时早退更吃香[4][5]。策略含：置信度/熵阈值、可学习退出头、预算感知调阈值。端侧早退直接省焦耳；具体毫焦/次与「电池翻倍」类表述必须对本板测量，不可照搬他文。

## 4 隐私

传中间特征而非原图，但浅层特征可被反演逼近原输入[8]。对策：校准噪声、切分点瓶颈压缩、可学习噪声层（如 Shredder）、对抗重建惩罚[9]。

| 切分位置 | 传输量 | 端算力 | 隐私 | 精度倾向 |
|---------|--------|--------|------|---------|
| 很浅 | 大 | 少 | 差 | 高 |
| 中间瓶颈 | 小 | 中 | 中 | 高 |
| 很深 | 很小 | 多 | 较好 | 高 |
| 浅层+噪声/瓶颈 | 视设计 | 中 | 较好 | 中–高 |

## 5 LLM 新约束

自回归与键值缓存（Key-Value Cache, KV Cache）使切分需同步缓存；Transformer 层间激活尺寸常近似恒定，缺少 CNN 式明显瓶颈；端侧层数过多会撑爆内存。实践上更多按算力/内存动态决定本地层数，或按注意力与前馈网络（Feed-Forward Network, FFN）对硬件友好度分工——相关系统仍快速演进，需跟进最新评测[5][6]。

## 6 实验表（示意，来自文献设定）

| 模型 | WiFi 倾向 | 蜂窝较差时倾向 | 相对纯云延迟 |
|------|-----------|----------------|--------------|
| 经典 CNN（AlexNet/VGG 等） | 中部切 | 切点后移或全本地 | 约数倍改善量级[1] |
| ResNet 类 | 中前–中后随带宽变 | 更靠后 | 约数倍量级 |
| MobileNet 类 | 视带宽 | 常更易全本地 | 改善幅度常小于大 CNN |
| BERT-base 类 | 中部层 | 后移或全本地 | 约两倍量级（设定相关） |

| 设定 | 平均退出深度（相对全深） | 延迟降低（示意） | 精度损失（示意） |
|------|--------------------------|------------------|------------------|
| 简单视觉集 | 约三到四成深度 | 可观 | 很小 |
| ImageNet 类 | 约一半深度量级 | 中等偏好 | 小幅 |
| 工业缺陷（正常品为主） | 更浅 | 更大 | 很小（若阈值得当） |

## 7 局限、挑战与可改进方向

### 1. 延迟模型与真机偏差

**局限**：层独立加和忽略缓存、调度与驱动开销，预测切点可偏约一成以上。
**改进**：在线校准层耗时；切点附近做短时 A/B；把传输模型换成实测带宽分布而非均值。

### 2. 单切分点表达力不足

**局限**：只允许「前缀在端、后缀在边」，无法表达交错执行。
**改进**：在复杂度可控前提下探索多切分或与流水线协作推理融合；先用启发式限搜索空间。

### 3. 动态/条件计算难切

**局限**：混合专家（Mixture-of-Experts, MoE）、动态路由使静态切点表失效。
**改进**：按最大激活路径做保守切分；运行时再协商；或改为整段卸载。

### 4. 隐私与瓶颈目标冲突

**局限**：为减传输选浅瓶颈，却最易被特征反演。
**改进**：强制最小切分深度或瓶颈+噪声；对反演攻击做回归测试；敏感数据默认更深切或全本地。

### 5. LLM/多模态栈不成熟

**局限**：CNN 时代结论直接套到 LLM 会误判内存与同步成本。
**改进**：单独建 KV/激活账本；优先量化与投机解码等，切分作补充而非唯一手段。

## 参考文献

[1] Y. Kang et al., "Neurosurgeon: Collaborative Intelligence Between the Cloud and Mobile Edge," ASPLOS, 2017.
[2] C. Hu et al., "Dynamic Adaptive DNN Surgery for Inference Acceleration on the Edge," IEEE INFOCOM, 2019.
[3] S. Laskaridis et al., "SPINN: Synergistic Progressive Inference of Neural Networks over Device and Cloud," MobiCom, 2020.
[4] S. Teerapittayanon et al., "BranchyNet: Fast Inference via Early Exiting from Deep Neural Networks," ICPR, 2016.
[5] Y. Matsubara et al., "Split Computing and Early Exiting for Deep Neural Networks: A Survey," ACM Computing Surveys, 2023.
[6] J. Shao and J. Zhang, "Communication-Computation Trade-off in Resource-Constrained Edge Inference," IEEE Communications Magazine, 2020.
[7] E. Li et al., "Edge AI: On-Demand Accelerating Deep Neural Network Inference via Edge Computing," IEEE Transactions on Wireless Communications, 2020.
[8] A. Dosovitskiy and T. Brox, "Inverting Visual Representations with Convolutional Networks," CVPR, 2016.
[9] F. Mireshghallah et al., "Shredder: Learning Noise Distributions to Protect Inference Privacy," ASPLOS, 2020.
[10] A. E. Eshratifar et al., "JointDNN: An Efficient Training and Inference Engine for Intelligent Mobile Cloud Computing Services," IEEE Transactions on Mobile Computing, 2019.
[11] M. Almeida et al., "EmBench: Quantifying Performance Variations of Deep Neural Networks across Modern Commodity Devices," EMDL Workshop, 2019.
[12] J. Chen and X. Ran, "Deep Learning With Edge Computing: A Review," Proceedings of the IEEE, 2019.
