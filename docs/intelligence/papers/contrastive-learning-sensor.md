---
schema_version: '1.0'
id: contrastive-learning-sensor
title: 对比学习在传感器数据中的应用
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - self-supervised-pretraining-device
tags:
- 对比学习
- SimCLR
- BYOL
- 传感器
- HAR
- InfoNCE
- 数据增强
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 对比学习在传感器数据中的应用

> **难度**：🟡 中级 | **领域**：自监督学习、传感器、人体活动识别（HAR） | **阅读时间**：约 20 分钟

## 日常类比

学外语却没有老师批改：你能做的是听同一句话的不同录音（口音、语速），学会"这些是同一句"，并区分不同句子。**对比学习**（Contrastive Learning）即：相似拉近、不同推远。

传感器标注极贵——让人戴手环做海量跑步/走路并标注既贵又不自然。对比学习先用未标注数据学表示，再用极少标签做分类：像先培养"乐感"，再听几首示范曲就能分流派[1][4]。

## 摘要

本文说明 InfoNCE、温度系数、面向惯性/时序的增强策略，以及 SimCLR / BYOL / TS-TCC / CPC 在 HAR 等任务上的适配；强调小 batch 下 BYOL 的优势、线性评估与 few-shot 协议，并列出边缘部署局限与改进[1][2][3]。

## 1 原理

编码器 \(f\) 使同一样本两视角（正对）近、不同样本（负对）远。常用 **InfoNCE**（Noise-Contrastive Estimation）损失[6]：

```python
import torch
import torch.nn.functional as F

def info_nce_loss(z_i, z_j, temperature=0.07):
    batch_size = z_i.shape[0]
    z_i, z_j = F.normalize(z_i, dim=1), F.normalize(z_j, dim=1)
    z = torch.cat([z_i, z_j], dim=0)
    sim = torch.mm(z, z.T) / temperature
    labels = torch.cat([
        torch.arange(batch_size, 2 * batch_size),
        torch.arange(batch_size)
    ]).to(z.device)
    mask = torch.eye(2 * batch_size, dtype=torch.bool, device=z.device)
    sim.masked_fill_(mask, -1e9)
    return F.cross_entropy(sim, labels)
```

| 温度 \(\tau\) | 效果 | 适用 |
|---------------|------|------|
| 很小（如 0.01） | 梯度盯最难负样本 | 边界清晰 |
| ~0.07 | SimCLR 常用默认[1] | 通用起点 |
| ~0.1 | 更宽松 | 噪声数据 |
| 很大 | 难易几乎不分 | 少用 |

## 2 时序传感器增强

图像翻转/裁剪不能照搬：加速度"上下翻转"会改重力语义。需保物理含义的增强[7]。

| 增强 | 直觉 | 注意 |
|------|------|------|
| Jittering | 加传感器噪声 | \(\sigma\) 勿过大 |
| Scaling | 动作幅度差异 | 通道可共享或独立 |
| Time warp | 执行速度差异 | 插值保持连续 |
| Permutation | 打乱片段 | 可能伤长程依赖 |
| Rotation | 佩戴角度（三轴） | 勿随意对非向量通道 |
| Channel dropout | 通道故障 | 概率宜低 |
| Cropping | 截取片段 | 对齐长度 |

UCI-HAR 类消融常见趋势（示意，非跨实现承诺）[4][5]：

| 增强组合 | 线性评估趋势 |
|----------|--------------|
| 无增强 | 基准最低 |
| Jitter | 明显升 |
| Jitter+Scale | 再升 |
| +TimeWarp | 通常更好 |
| 随机组合 2 种 | 常接近最优档 |

## 3 SimCLR 适配

用 1D CNN 替 ResNet；投影头仅预训练使用[1][9]。

```python
import torch.nn as nn

class SensorSimCLR(nn.Module):
    def __init__(self, input_channels=6, hidden_dim=256, proj_dim=128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, 8, padding=4), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(64, 128, 3, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.projector = nn.Sequential(
            nn.Linear(128, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, proj_dim)
        )

    def forward(self, x):
        h = self.encoder(x).squeeze(-1)
        return h, self.projector(h)
```

SimCLR 依赖大 batch 提供负样本；边缘内存紧时吃力。

## 4 BYOL：无负样本

**BYOL**（Bootstrap Your Own Latent）：online 网络预测 target（EMA）输出，无需负样本，小 batch 更稳[2]。适合设备端/小批量预训练。

## 5 HAR 案例

数据集如 UCI-HAR（多用户、多活动）。标注极少时，对比预训练 + 线性/微调常显著优于同比例纯监督[4][5]。

| 设定 | 方法 | 趋势 |
|------|------|------|
| 全标注监督 | CNN | 上界 |
| 预训练+全量线性 | SimCLR 等 | 接近上界 |
| 预训练+1%–10% 标注 | 对比+线性 | 远好于同比例纯监督 |
| 跨用户 few-shot | 原型/KNN | 迁移关键能力 |

## 6 表示评估与方法对比

| 评估 | 优点 | 缺点 |
|------|------|------|
| 线性探测 | 隔离表示质量 | 低估非线性 |
| KNN | 无需再训头 | 算距离贵 |
| 全微调 | 接近部署上限 | 混入适应效应 |
| t-SNE / Silhouette | 直观/无标签 | 定性或敏感 |

| 数据集（示意） | 全监督 | SimCLR | BYOL | TS-TCC[3] | CPC[6] |
|----------------|--------|--------|------|-----------|--------|
| UCI-HAR | 最高档 | 接近 | 接近 | 常略优 | 略低 |
| PAMAP2 等 | 最高档 | 接近 | 接近 | 时序建模强 | 依赖预测视野 |

TS-TCC 显式做时间/上下文对比，传感器上常优于原版视觉 SimCLR[3]。

## 7 实践要点

- 必选增强：Jitter + Scale；推荐 Time warp；慎用 Permutation；避免无物理意义的翻转。
- \(\tau\) 从 ~0.07 起；SimCLR batch 尽量大，否则转 BYOL。
- 预训练 epoch 数百量级常见（数据量通常小于视觉）。
- 标注 <10% 或要跨设备/用户迁移时优先对比预训练[5]。

## 8 局限、挑战与可改进方向

### 1. 增强可能破坏语义

**局限**：Permutation/过强 warp 把"走路"扭成不像走路，正对变假正对。
**改进**：按模态白名单增强；用标签子集做增强毒性抽检；物理约束（重力轴）。

### 2. 负样本与小 batch

**局限**：端侧 batch 小，InfoNCE 退化；假负对（同活动不同窗）伤害表示。
**改进**：BYOL/SimSiam；内存队列负样本；时间邻近排除假负[2][3]。

### 3. 域偏移（设备/佩戴位置）

**局限**：手机裤袋 vs 手表预训练，线性评估虚高、现场崩。
**改进**：多位置混合预训练；测试时适配；明确报告跨域协议[5]。

### 4. 算力与能耗

**局限**：双视角前向约 2× 监督一轮，MCU 难承受长时间预训练。
**改进**：网关/云上预训练、端上只微调头；蒸馏到小编码器；降投影维与通道。

### 5. 评测泡沫

**局限**：只报全数据线性准确率，掩盖 few-shot 与漂移。
**改进**：固定 1%/5%/10% 与跨用户协议；报告置信区间与种子[5][10]。

## 参考文献

[1] T. Chen et al., "A Simple Framework for Contrastive Learning of Visual Representations," ICML, 2020.
[2] J.-B. Grill et al., "Bootstrap Your Own Latent: A New Approach to Self-Supervised Learning," NeurIPS, 2020.
[3] E. Eldele et al., "Time-Series Representation Learning via Temporal and Contextual Contrasting," IJCAI, 2021.
[4] C. I. Tang et al., "Exploring Contrastive Learning in Human Activity Recognition," arXiv:2011.11542, 2020.
[5] H. Haresamudram et al., "Assessing the State of Self-Supervised Human Activity Recognition," IMWUT, 2022.
[6] A. van den Oord et al., "Representation Learning with Contrastive Predictive Coding," arXiv:1807.03748, 2018.
[7] T. T. Um et al., "Data Augmentation of Wearable Sensor Data for Parkinson's Disease Monitoring," ICMI, 2017.
[8] A. Saeed et al., "Multi-task Self-Supervised Learning for Human Activity Detection," IMWUT, 2019.
[9] B. Khaertdinov et al., "Contrastive Self-Supervised Learning for Sensor-Based HAR," IEEE JBHI, 2022.
[10] H. Yuan et al., "Self-Supervised Contrastive Learning for Medical Time Series: A Systematic Review," Sensors, 2024.
[11] J. Y. Franceschi et al., "Unsupervised Scalable Representation Learning for Multivariate Time Series," NeurIPS, 2019.
[12] K. Sohn, "Improved Deep Metric Learning with Multi-class N-pair Loss," NeurIPS, 2016.
