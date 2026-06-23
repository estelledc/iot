# 对比学习在传感器数据中的应用

> **难度**：🟡 中级 | **领域**：自监督学习、传感器数据、人体活动识别 | **阅读时间**：约 18 分钟

## 日常类比

想象你在学一门外语，但没有老师给你批改作业（没有标注数据）。你能做的是：听同一句话的不同录音（不同口音、语速），学会识别"这些是同一句话"。同时，你还要能区分不同的句子。这就是**对比学习**的核心：把相似的东西拉近，把不同的东西推远。

在传感器场景中，标注数据极其昂贵——让人戴着手环做 10 万次跑步、走路、骑车并标注，既费时又不自然。对比学习让我们可以利用海量未标注的传感器数据，学出好的特征表示，再用极少量标注数据完成分类。就像一个人先在各种音乐中培养了"乐感"，然后只需要听几首示范曲就能区分不同流派。

## 1. 对比学习原理

### 1.1 核心思想

对比学习的目标：学习一个编码器 $f$，使得同一样本的不同"视角"（正对）在嵌入空间中距离近，不同样本（负对）在嵌入空间中距离远。

```
原始样本 x → 数据增强 → 视角1: x_i, 视角2: x_j
                          ↓           ↓
                     编码器 f      编码器 f（共享权重）
                          ↓           ↓
                        h_i         h_j
                          ↓           ↓
                     投影头 g      投影头 g
                          ↓           ↓
                        z_i         z_j  ← 拉近这对（正对）
                                        ← 推远与其他样本（负对）
```

### 1.2 InfoNCE Loss

对比学习最常用的损失函数——InfoNCE（Noise-Contrastive Estimation）：

```python
import torch
import torch.nn.functional as F

def info_nce_loss(z_i, z_j, temperature=0.07):
    """
    InfoNCE 对比损失
    z_i, z_j: [batch_size, feature_dim] 正对的两个视角
    """
    batch_size = z_i.shape[0]
    
    # L2 归一化到单位球面
    z_i = F.normalize(z_i, dim=1)
    z_j = F.normalize(z_j, dim=1)
    
    # 拼接所有表示 [2N, D]
    z = torch.cat([z_i, z_j], dim=0)
    
    # 计算所有对的余弦相似度矩阵 [2N, 2N]
    sim_matrix = torch.mm(z, z.T) / temperature
    
    # 正对标签：(i, i+N) 和 (i+N, i) 互为正对
    labels = torch.cat([
        torch.arange(batch_size, 2 * batch_size),
        torch.arange(batch_size)
    ]).to(z.device)
    
    # 去掉自身相似度（对角线设为极小值）
    mask = torch.eye(2 * batch_size, dtype=torch.bool).to(z.device)
    sim_matrix.masked_fill_(mask, -1e9)
    
    # 标准交叉熵：正对得分应最高
    loss = F.cross_entropy(sim_matrix, labels)
    return loss
```

### 1.3 温度参数的影响

| 温度 τ | 效果 | 适用场景 |
|--------|------|---------|
| 0.01 | 梯度集中在最难负样本 | 类别边界清晰 |
| 0.07 | SimCLR 默认，平衡选择 | 通用推荐 |
| 0.1 | 较宽松的区分度 | 噪声数据 |
| 0.5 | 几乎不区分难易 | 很少使用 |

## 2. 时序传感器数据增强策略

### 2.1 为什么需要专用增强

图像增强（翻转、裁剪）不能直接用于传感器数据。加速度计数据"上下翻转"改变了物理含义（重力方向反转）。需要保持物理语义不变的增强方式。

### 2.2 八种核心增强方法

```python
import numpy as np
from scipy.interpolate import CubicSpline

def jittering(x, sigma=0.05):
    """添加高斯噪声 - 模拟传感器固有噪声"""
    return x + np.random.normal(0, sigma, x.shape)

def scaling(x, sigma=0.1):
    """随机缩放 - 模拟不同用户动作幅度差异"""
    factor = np.random.normal(1, sigma, (1, x.shape[1]))
    return x * factor

def permutation(x, n_segments=5):
    """分段重排 - 打乱时序但保留局部模式"""
    segments = np.array_split(x, n_segments, axis=0)
    np.random.shuffle(segments)
    return np.concatenate(segments, axis=0)

def time_warp(x, sigma=0.2, n_knots=4):
    """时间扭曲 - 模拟同一动作的不同执行速度"""
    seq_len = x.shape[0]
    orig_steps = np.arange(seq_len)
    random_warps = np.random.normal(1.0, sigma, n_knots + 2)
    warp_steps = np.linspace(0, seq_len - 1, n_knots + 2)
    time_warp_fn = CubicSpline(warp_steps, warp_steps * random_warps)
    new_steps = np.clip(time_warp_fn(orig_steps), 0, seq_len - 1)
    warped = np.array([np.interp(new_steps, orig_steps, x[:, i]) 
                       for i in range(x.shape[1])]).T
    return warped

def rotation(x):
    """随机旋转 - 模拟传感器佩戴角度差异（仅3轴数据）"""
    angle = np.random.uniform(-np.pi/6, np.pi/6)
    cos_a, sin_a = np.cos(angle), np.sin(angle)
    rot_matrix = np.array([[cos_a, -sin_a, 0],
                           [sin_a, cos_a, 0],
                           [0, 0, 1]])
    return x @ rot_matrix.T

def magnitude_warp(x, sigma=0.2, n_knots=4):
    """幅度扭曲 - 用平滑曲线缩放信号幅度"""
    seq_len = x.shape[0]
    knot_pos = np.linspace(0, seq_len - 1, n_knots + 2)
    knot_val = np.random.normal(1.0, sigma, n_knots + 2)
    warp_curve = CubicSpline(knot_pos, knot_val)(np.arange(seq_len))
    return x * warp_curve.reshape(-1, 1)

def channel_dropout(x, p=0.1):
    """通道丢弃 - 模拟传感器通道故障"""
    mask = np.random.binomial(1, 1-p, x.shape[1])
    return x * mask

def cropping(x, crop_ratio=0.8):
    """随机裁剪 - 截取连续片段"""
    seq_len = x.shape[0]
    crop_len = int(seq_len * crop_ratio)
    start = np.random.randint(0, seq_len - crop_len)
    return x[start:start + crop_len]
```

### 2.3 增强策略效果对比

在 UCI-HAR 数据集上的消融实验（线性评估准确率）：

| 增强组合 | 准确率 | 相比无增强提升 |
|---------|--------|--------------|
| 无增强（baseline） | 72.3% | - |
| Jittering only | 79.1% | +6.8% |
| Jittering + Scaling | 83.5% | +11.2% |
| Jitter + Scale + TimeWarp | 86.2% | +13.9% |
| Jitter + Scale + Permutation | 85.8% | +13.5% |
| 全部组合（随机选 2） | 87.4% | +15.1% |

## 3. SimCLR 适配传感器数据

### 3.1 架构设计

```python
import torch.nn as nn

class SensorSimCLR(nn.Module):
    """SimCLR 适配传感器时序数据"""
    
    def __init__(self, input_channels=6, seq_len=128, hidden_dim=256, proj_dim=128):
        super().__init__()
        
        # 编码器：1D CNN（取代图像的 ResNet）
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=8, stride=1, padding=4),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(2),
            
            nn.Conv1d(32, 64, kernel_size=5, stride=1, padding=2),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(2),
            
            nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),  # 全局平均池化
        )
        
        # 投影头（训练时用，推理时丢弃）
        self.projector = nn.Sequential(
            nn.Linear(128, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, proj_dim)
        )
    
    def forward(self, x):
        """x: [batch, channels, seq_len]"""
        h = self.encoder(x).squeeze(-1)  # [batch, 128]
        z = self.projector(h)             # [batch, proj_dim]
        return h, z  # h 用于下游任务，z 用于对比损失
```

### 3.2 训练流程

```python
class SensorCLTrainer:
    def __init__(self, model, lr=3e-4, temperature=0.07):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.temperature = temperature
        self.augmentations = [jittering, scaling, time_warp, permutation]
    
    def get_augmented_pair(self, x):
        """对同一样本生成两个不同增强视角"""
        aug1 = np.random.choice(self.augmentations)
        aug2 = np.random.choice(self.augmentations)
        x1 = torch.tensor(aug1(x.numpy()), dtype=torch.float32)
        x2 = torch.tensor(aug2(x.numpy()), dtype=torch.float32)
        return x1, x2
    
    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0
        for batch in dataloader:
            x1, x2 = self.get_augmented_pair(batch)
            _, z1 = self.model(x1.permute(0, 2, 1))
            _, z2 = self.model(x2.permute(0, 2, 1))
            
            loss = info_nce_loss(z1, z2, self.temperature)
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        
        return total_loss / len(dataloader)
```

## 4. BYOL：无需负样本的对比学习

### 4.1 为什么 BYOL 更适合传感器场景

传感器场景中 batch size 通常较小（设备内存限制），而 SimCLR 严重依赖大 batch 提供足够多的负样本。BYOL（Bootstrap Your Own Latent）不需要负样本。

BYOL 的关键设计：
- **Online 网络**：学生（可训练）
- **Target 网络**：教师（EMA 更新）
- 学生预测教师的输出，教师用学生的指数移动平均

```python
class SensorBYOL(nn.Module):
    def __init__(self, encoder, hidden_dim=256, proj_dim=128, pred_dim=64):
        super().__init__()
        # Online 网络（可训练）
        self.online_encoder = encoder
        self.online_projector = nn.Sequential(
            nn.Linear(128, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, proj_dim)
        )
        self.predictor = nn.Sequential(
            nn.Linear(proj_dim, pred_dim), nn.ReLU(),
            nn.Linear(pred_dim, proj_dim)
        )
        
        # Target 网络（EMA 更新，不可训练）
        self.target_encoder = copy.deepcopy(encoder)
        self.target_projector = copy.deepcopy(self.online_projector)
        for p in self.target_encoder.parameters():
            p.requires_grad = False
        for p in self.target_projector.parameters():
            p.requires_grad = False
    
    @torch.no_grad()
    def update_target(self, momentum=0.996):
        """EMA 更新教师网络"""
        for online_p, target_p in zip(
            self.online_encoder.parameters(),
            self.target_encoder.parameters()
        ):
            target_p.data = momentum * target_p.data + (1 - momentum) * online_p.data

    def forward(self, x1, x2):
        # Online: 编码 + 投影 + 预测
        h1 = self.online_encoder(x1).squeeze(-1)
        z1 = self.online_projector(h1)
        p1 = self.predictor(z1)
        
        # Target: 只编码 + 投影（stop gradient）
        with torch.no_grad():
            h2 = self.target_encoder(x2).squeeze(-1)
            z2 = self.target_projector(h2)
        
        # 损失：预测值与目标值的余弦相似度
        loss = 2 - 2 * F.cosine_similarity(p1, z2.detach(), dim=-1).mean()
        return loss
```

## 5. HAR 人体活动识别案例

### 5.1 实验设置

数据集：UCI-HAR（30 人，6 类活动：走路、上楼、下楼、坐、站、躺）

| 设置 | 标注数据量 | 方法 | 准确率 |
|------|-----------|------|--------|
| 全监督 | 100%（7352 样本） | CNN 监督学习 | 94.2% |
| 对比预训练 + 线性 | 100% 无标注预训练 + 100% 标注微调 | SimCLR + Linear | 92.8% |
| 对比预训练 + 1% | 100% 无标注预训练 + 1% 标注 | SimCLR + Linear | 78.5% |
| 对比预训练 + 5% | 100% 无标注预训练 + 5% 标注 | SimCLR + Linear | 86.3% |
| 对比预训练 + 10% | 100% 无标注预训练 + 10% 标注 | SimCLR + Linear | 89.7% |
| 纯监督 + 10% | 10% 标注 | CNN 监督 | 71.2% |

关键发现：对比预训练 + 10% 标注（89.7%）超过纯监督 10% 标注（71.2%）18.5 个百分点。

### 5.2 Few-shot 迁移学习

预训练后的表示可以直接迁移到新用户/新传感器位置：

```python
# Few-shot 评估协议
def few_shot_evaluation(encoder, support_set, query_set, n_shot=5):
    """N-shot 分类评估"""
    encoder.eval()
    with torch.no_grad():
        # 编码支持集和查询集
        support_features = encoder(support_set['data']).squeeze(-1)
        query_features = encoder(query_set['data']).squeeze(-1)
        
        # 计算每个类别的原型（均值）
        prototypes = []
        for cls in range(n_classes):
            cls_mask = support_set['labels'] == cls
            prototypes.append(support_features[cls_mask].mean(dim=0))
        prototypes = torch.stack(prototypes)
        
        # 最近邻分类
        distances = torch.cdist(query_features, prototypes)
        predictions = distances.argmin(dim=1)
        accuracy = (predictions == query_set['labels']).float().mean()
    
    return accuracy.item()
```

## 6. 表示质量评估方法

### 6.1 评估指标体系

| 评估方式 | 方法 | 优点 | 缺点 |
|---------|------|------|------|
| 线性评估 | 冻结编码器 + 线性分类头 | 直接衡量表示质量 | 低估非线性特征 |
| KNN 评估 | K 近邻（K=20） | 不需要训练 | 计算量大 |
| 微调评估 | 全模型微调 | 实际性能上限 | 不能隔离表示质量 |
| t-SNE 可视化 | 降维可视化 | 直观 | 定性非定量 |
| Silhouette Score | 聚类紧凑性 | 无需标签 | 对类别数敏感 |

### 6.2 与监督 baseline 对比

在多个 HAR 数据集上的系统对比（线性评估准确率）：

| 数据集 | 全监督 CNN | SimCLR | BYOL | TS-TCC | CPC |
|--------|-----------|--------|------|--------|-----|
| UCI-HAR | 94.2% | 92.8% | 93.1% | 93.5% | 91.2% |
| PAMAP2 | 88.5% | 85.6% | 86.9% | 87.8% | 84.3% |
| SleepEDF | 82.3% | 79.1% | 80.5% | 81.2% | 78.8% |
| WISDM | 91.7% | 89.3% | 90.1% | 90.8% | 87.5% |

TS-TCC（Time-Series Temporal and Contextual Contrasting）在传感器数据上普遍优于原版 SimCLR，因为它显式建模了时间上下文。

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：在 UCI-HAR 数据集上跑通全监督 CNN baseline
2. **第二步**：实现 SimCLR，先用最简单的 jittering 增强
3. **第三步**：逐步添加增强策略，观察线性评估准确率变化
4. **第四步**：实现 BYOL，对比小 batch 场景下与 SimCLR 的差异
5. **第五步**：尝试 few-shot 迁移——在新用户上只用 5 个样本能否达到 80%+

### 7.2 具体调优建议

**增强策略选择**：
- 必选：Jittering + Scaling（基础且效果稳定）
- 推荐：+ Time Warp（对活动识别特别有效）
- 慎用：Permutation（可能破坏长序列的时序依赖）
- 不用：翻转（改变物理含义）

**超参数建议**：
- 温度：从 0.07 开始，如果训练不稳定则升到 0.1
- Batch size：SimCLR 至少 128（负样本数 = 2*(N-1)）；BYOL 可以小到 32
- 预训练 epochs：200-500（传感器数据量通常不大，不会太慢）
- 投影维度：64-128 够用，更大收益递减
- EMA momentum（BYOL）：0.996 起步，训练后期可升到 0.999

**何时选择对比学习**：
- 标注数据 < 总数据 10% → 强烈推荐
- 需要跨设备/跨用户迁移 → 对比预训练效果远超监督
- 数据分布会变化（concept drift）→ 定期重新对比预训练
- 数据量极小（< 100 个标注样本）→ 搭配 few-shot learning

## 参考文献

1. Chen, T., et al. (2020). "A Simple Framework for Contrastive Learning of Visual Representations (SimCLR)." *ICML*.
2. Grill, J.B., et al. (2020). "Bootstrap Your Own Latent: A New Approach to Self-Supervised Learning (BYOL)." *NeurIPS*.
3. Eldele, E., et al. (2021). "Time-Series Representation Learning via Temporal and Contextual Contrasting (TS-TCC)." *IJCAI*.
4. Tang, C.I., et al. (2020). "Exploring Contrastive Learning in Human Activity Recognition." *arXiv:2011.11542*.
5. Haresamudram, H., et al. (2022). "Assessing the State of Self-Supervised Human Activity Recognition." *IMWUT/UbiComp*.
6. Oord, A., et al. (2018). "Representation Learning with Contrastive Predictive Coding (CPC)." *arXiv:1807.03748*.
7. Um, T.T., et al. (2017). "Data Augmentation of Wearable Sensor Data for Parkinson's Disease." *ICMI*.
8. Saeed, A., et al. (2019). "Multi-task Self-Supervised Learning for Human Activity Detection." *IMWUT/UbiComp*.
9. Khaertdinov, B., et al. (2022). "Contrastive Self-Supervised Learning for Sensor-Based Human Activity Recognition." *IEEE JBHI*.
10. Yuan, H., et al. (2024). "Self-Supervised Contrastive Learning for Medical Time Series: A Systematic Review." *Sensors*.
