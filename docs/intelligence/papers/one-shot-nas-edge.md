# 神经架构搜索 One-Shot NAS 在边缘的应用

> **难度**：🟡 中级 | **领域**：NAS、模型压缩、边缘部署 | **阅读时间**：约 20 分钟

## 日常类比

你要装修一套房子，但不知道哪种布局最好。最笨的方法是：试 1000 种方案，每种都请工人完整装修一遍，住一个月看哪种最舒服。这太贵了——每种方案都要全部建造成本。

**One-Shot NAS** 的思路像乐高积木：先搭一个"万能大房子"（超网络），里面包含所有可能的隔断、家具摆放方式。然后你只需要在这个大房子里"拆掉一些隔断"来尝试不同布局——不需要每次从零建造。一次训练，无限采样。

在边缘设备上，我们不仅要找到准确的模型，还要找到满足延迟、功耗、内存约束的模型。这就像装修时不仅要好看，还要控制在预算内——**硬件感知 NAS** 同时优化精度和硬件效率。

## 1. NAS 基础概念

### 1.1 三要素

| 要素 | 说明 | 常见选择 |
|------|------|---------|
| 搜索空间 | 可能的网络结构集合 | 卷积类型、通道数、连接方式 |
| 搜索策略 | 如何在空间中探索 | 随机搜索、进化算法、强化学习、梯度 |
| 性能评估 | 如何判断架构好坏 | 完整训练、权重共享、预测器 |

### 1.2 NAS 方法演进

| 代际 | 方法 | 搜索成本 | 代表工作 |
|------|------|---------|---------|
| 第一代 | 每个架构独立训练 | 3000+ GPU-days | NASNet (2018) |
| 第二代 | 权重共享 One-Shot | 1-5 GPU-days | ENAS, DARTS |
| 第三代 | Once-for-All | 训练1次 部署无限 | OFA, BigNAS |
| 第四代 | Zero-Shot | 小于 1 GPU-hour | ZenNAS, NASWOT |

### 1.3 搜索空间设计

```python
# 典型的边缘 NAS 搜索空间定义
SEARCH_SPACE = {
    'conv_ops': [
        'conv3x3',           # 标准 3x3 卷积
        'conv5x5',           # 标准 5x5 卷积
        'dwconv3x3',         # 深度可分离 3x3
        'dwconv5x5',         # 深度可分离 5x5
        'mbconv3_e3',        # MBConv k=3 expand=3
        'mbconv3_e6',        # MBConv k=3 expand=6
        'mbconv5_e3',        # MBConv k=5 expand=3
        'mbconv5_e6',        # MBConv k=5 expand=6
        'skip',              # 跳过连接
        'zero',              # 不连接
    ],
    'channels': [16, 24, 32, 48, 64, 96, 128],
    'layers_per_stage': [1, 2, 3, 4],
    'kernel_sizes': [3, 5, 7],
    'se_ratio': [0, 0.25],  # Squeeze-and-Excitation
}
# 搜索空间大小约 10^13 种可能架构
```

## 2. One-Shot Supernet 方法

### 2.1 核心思想

训练一个包含所有可能路径的超网络（Supernet），然后通过采样子网络来评估不同架构的质量。

```python
import torch
import torch.nn as nn
import random

class SupernetBlock(nn.Module):
    """超网络中的一个可选操作块"""

    def __init__(self, in_channels, out_channels, stride=1):
        super().__init__()
        self.ops = nn.ModuleList([
            MBConv(in_channels, out_channels, 3, stride, expand_ratio=3),
            MBConv(in_channels, out_channels, 3, stride, expand_ratio=6),
            MBConv(in_channels, out_channels, 5, stride, expand_ratio=3),
            MBConv(in_channels, out_channels, 5, stride, expand_ratio=6),
            SkipConnect(in_channels, out_channels, stride),
        ])
        self.n_ops = len(self.ops)

    def forward(self, x, op_idx=None):
        """前向传播：训练时随机选操作，搜索时指定"""
        if op_idx is None:
            op_idx = random.randint(0, self.n_ops - 1)
        return self.ops[op_idx](x)


class Supernet(nn.Module):
    """完整超网络"""

    def __init__(self, n_classes=10, n_stages=5, blocks_per_stage=4):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU6()
        )

        channels = [32, 48, 64, 96, 128]
        self.stages = nn.ModuleList()
        in_ch = 32
        for stage_idx in range(n_stages):
            stage = nn.ModuleList()
            for block_idx in range(blocks_per_stage):
                out_ch = channels[stage_idx]
                stride = 2 if block_idx == 0 else 1
                stage.append(SupernetBlock(in_ch, out_ch, stride))
                in_ch = out_ch
            self.stages.append(stage)

        self.head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(channels[-1], n_classes)
        )

    def forward(self, x, architecture=None):
        """
        architecture: list of lists, 指定每个块的操作选择
        None 则随机采样
        """
        x = self.stem(x)
        for stage_idx, stage in enumerate(self.stages):
            for block_idx, block in enumerate(stage):
                op_idx = None
                if architecture is not None:
                    op_idx = architecture[stage_idx][block_idx]
                x = block(x, op_idx)
        return self.head(x)
```

### 2.2 训练策略

```python
def train_supernet(supernet, dataloader, epochs=100, lr=0.05):
    """单路径采样训练超网络"""
    optimizer = torch.optim.SGD(supernet.parameters(), lr=lr, momentum=0.9)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs)

    for epoch in range(epochs):
        for images, labels in dataloader:
            # 关键：每个 mini-batch 随机采样一条路径
            architecture = sample_random_architecture(supernet)

            output = supernet(images, architecture)
            loss = nn.CrossEntropyLoss()(output, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        scheduler.step()


def sample_random_architecture(supernet):
    """随机采样一个子网络架构"""
    architecture = []
    for stage in supernet.stages:
        stage_choices = [random.randint(0, stage[0].n_ops - 1) for _ in stage]
        architecture.append(stage_choices)
    return architecture
```

## 3. 硬件感知 NAS

### 3.1 多目标优化

边缘部署需要同时优化多个目标：

| 目标 | 度量 | 约束示例 |
|------|------|---------|
| 准确率 | Top-1 Accuracy | 大于 85% |
| 延迟 | ms 每帧 | 小于 10ms on RPi4 |
| 能耗 | mJ 每推理 | 小于 5mJ |
| 模型大小 | MB | 小于 2MB Flash |
| 峰值内存 | KB | 小于 256KB SRAM |

### 3.2 延迟预测器

```python
class LatencyPredictor:
    """基于查找表的延迟预测器"""

    def __init__(self, target_device='rpi4'):
        self.lut = self._build_lookup_table(target_device)

    def _build_lookup_table(self, device):
        """在目标设备上逐个测量操作延迟"""
        lut = {}
        op_types = ['mbconv3_e3', 'mbconv3_e6', 'mbconv5_e3', 'mbconv5_e6', 'skip']
        for op_type in op_types:
            for in_ch in [16, 24, 32, 48, 64, 96, 128]:
                for out_ch in [16, 24, 32, 48, 64, 96, 128]:
                    for resolution in [56, 28, 14, 7]:
                        key = (op_type, in_ch, out_ch, resolution)
                        lut[key] = self._measure_on_device(key, device)
        return lut

    def predict(self, architecture, input_resolution=224):
        """预测整个架构的推理延迟"""
        total_latency = 0
        resolution = input_resolution // 2
        in_ch = 32
        channels = [32, 48, 64, 96, 128]
        op_names = ['mbconv3_e3', 'mbconv3_e6', 'mbconv5_e3', 'mbconv5_e6', 'skip']

        for stage_idx, stage_choices in enumerate(architecture):
            out_ch = channels[stage_idx]
            for block_idx, op_idx in enumerate(stage_choices):
                op_type = op_names[op_idx]
                key = (op_type, in_ch, out_ch, resolution)
                total_latency += self.lut.get(key, 0)
                in_ch = out_ch
            resolution //= 2

        return total_latency
```

### 3.3 进化搜索

```python
import numpy as np

def evolutionary_search(supernet, latency_predictor,
                        n_generations=50, population_size=100,
                        latency_target=10.0):
    """进化搜索：在延迟约束下找最优架构"""

    population = [sample_random_architecture(supernet)
                  for _ in range(population_size)]

    for gen in range(n_generations):
        fitness_scores = []
        for arch in population:
            acc = evaluate_on_supernet(supernet, arch)
            latency = latency_predictor.predict(arch)

            if latency > latency_target:
                penalty = (latency - latency_target) * 10
                fitness = acc - penalty
            else:
                fitness = acc
            fitness_scores.append(fitness)

        # 选择 top-20%
        top_k = population_size // 5
        top_indices = np.argsort(fitness_scores)[-top_k:]
        parents = [population[i] for i in top_indices]

        # 变异生成新种群
        new_population = list(parents)
        while len(new_population) < population_size:
            parent = random.choice(parents)
            child = mutate(parent)
            new_population.append(child)

        population = new_population

        best_idx = np.argmax(fitness_scores)
        best_lat = latency_predictor.predict(population[best_idx])
        print(f"Gen {gen}: Best fitness={fitness_scores[best_idx]:.3f}, "
              f"latency={best_lat:.1f}ms")

    return population[np.argmax(fitness_scores)]
```

## 4. OFA (Once-for-All)

### 4.1 核心思想

训练一个支持弹性深度、宽度和分辨率的超网络。部署时根据目标设备约束直接抽取最优子网络，无需重新训练。

```python
class ElasticBlock(nn.Module):
    """支持弹性宽度和核大小的块"""

    def __init__(self, max_in_ch=128, max_out_ch=128, max_kernel=7):
        super().__init__()
        self.max_kernel = max_kernel
        self.conv = nn.Conv2d(max_in_ch, max_out_ch, max_kernel,
                              padding=max_kernel // 2)
        self.bn = nn.BatchNorm2d(max_out_ch)

    def forward(self, x, active_in_ch=None, active_out_ch=None, active_kernel=None):
        """弹性前向：只使用部分权重"""
        active_in_ch = active_in_ch or x.size(1)
        active_out_ch = active_out_ch or self.conv.out_channels
        active_kernel = active_kernel or self.max_kernel

        weight = self.conv.weight[:active_out_ch, :active_in_ch]

        if active_kernel < self.max_kernel:
            start = (self.max_kernel - active_kernel) // 2
            end = start + active_kernel
            weight = weight[:, :, start:end, start:end]

        padding = active_kernel // 2
        out = nn.functional.conv2d(x[:, :active_in_ch], weight, padding=padding)
        out = self.bn(out)[:, :active_out_ch]
        return nn.functional.relu6(out)
```

### 4.2 渐进式训练

OFA 的训练分 4 个阶段，逐步引入弹性：

```
阶段 1: 训练最大网络（正常训练）
阶段 2: 引入弹性核大小（7 -> 5 -> 3）
阶段 3: 引入弹性深度（4 -> 3 -> 2 层）
阶段 4: 引入弹性宽度（128 -> 96 -> 64 通道）
```

## 5. MCUNet / TinyNAS

### 5.1 专为微控制器设计的 NAS

MCUNet（MIT, 2020）针对 256KB SRAM、1MB Flash 的 MCU 搜索架构：

| 约束 | MCU (STM32F746) | 手机 (Snapdragon) | 云 (V100) |
|------|----------------|-------------------|-----------|
| SRAM | 320KB | 4GB | 32GB |
| Flash | 1MB | 128GB | - |
| 算力 | 216MHz ARM | 2.84GHz x 8 | 5120 CUDA |
| 功耗 | 150mW | 5W | 300W |

搜索结果对比：

| 模型 | SRAM | Flash | ImageNet Top-1 | 延迟 |
|------|------|-------|---------------|------|
| MCUNet-5FPS | 293KB | 741KB | 60.3% | 200ms |
| MCUNet-12FPS | 195KB | 488KB | 51.5% | 83ms |
| MobileNetV2 0.35x | 398KB | 543KB | 49.7% | 320ms |

### 5.2 TinyNAS 的搜索空间优化

```python
def optimize_search_space(target_flops, initial_space):
    """
    根据目标 FLOPs 自动调整搜索空间的宽度上限,
    使得搜索空间中满足约束的好架构比例最大化
    """
    best_space = None
    best_score = 0

    for width_mult in [0.25, 0.35, 0.5, 0.75, 1.0]:
        scaled_space = scale_channels(initial_space, width_mult)

        valid_count = 0
        total_quality = 0
        for _ in range(1000):
            arch = random_sample(scaled_space)
            flops = compute_flops(arch)
            if flops <= target_flops:
                valid_count += 1
                total_quality += zen_score(arch)

        score = total_quality / max(valid_count, 1)
        if score > best_score:
            best_score = score
            best_space = scaled_space

    return best_space
```

## 6. 从搜索到部署的完整流水线

### 6.1 端到端流程

```
1. 定义搜索空间 -> 基于目标硬件约束缩放
2. 构建硬件延迟查找表 -> 在目标设备上实测每个操作
3. 训练超网络 -> 单路径采样 / 渐进式缩小
4. 进化搜索 -> 多目标: 准确率 + 延迟/功耗
5. 重新训练最优架构 -> 从头训练到收敛
6. 量化 + 编译 -> TFLite / ONNX / TVM
7. 设备部署验证 -> 实测延迟/精度/功耗
```

### 6.2 Pareto 最优架构选择

```python
def find_pareto_front(architectures, accuracies, latencies):
    """找到 Pareto 前沿: 没有其他架构同时更准且更快"""
    n = len(architectures)
    is_pareto = [True] * n

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if accuracies[j] >= accuracies[i] and latencies[j] <= latencies[i]:
                if accuracies[j] > accuracies[i] or latencies[j] < latencies[i]:
                    is_pareto[i] = False
                    break

    pareto_archs = [architectures[i] for i in range(n) if is_pareto[i]]
    return pareto_archs
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：理解 MobileNetV2/V3 的手工设计思路（NAS 的搜索目标）
2. **第二步**：用 NNI (Neural Network Intelligence) 框架跑一个简单 NAS
3. **第三步**：实现最简 One-Shot Supernet + 随机搜索
4. **第四步**：加入延迟预测器实现硬件感知搜索
5. **第五步**：用 OFA 的预训练模型在自己的硬件上搜索子网

### 7.2 具体调优建议

**何时使用 NAS**：
- 有明确硬件约束且需要极致优化 -> OFA / MCUNet
- 模型精度瓶颈在架构设计 -> One-Shot NAS
- 需要部署到多种设备 -> OFA (一次训练多次部署)
- 数据集特定且通用模型效果不好 -> 数据集感知 NAS

**搜索策略选择**：
- 搜索空间小 (< 10^6) -> 随机搜索 + 早停已够好
- 搜索空间中等 -> 进化算法 (50 代 x 100 种群)
- 搜索空间大且可微分 -> DARTS 类梯度方法
- 极致效率 -> Zero-cost proxy (几分钟完成)

**超网络训练技巧**：
- Sandwich Rule: 每个 batch 训练最大 + 最小 + 2 个随机子网
- 知识蒸馏: 用最大子网指导小子网
- 足够长的训练: 至少 120 epochs (权重共享需要充分训练)
- 公平采样: 确保每种操作被均匀采样到

## 参考文献

1. Cai, H., et al. (2020). "Once-for-All: Train One Network and Specialize it for Efficient Deployment." *ICLR*.
2. Lin, J., et al. (2020). "MCUNet: Tiny Deep Learning on IoT Devices." *NeurIPS*.
3. Guo, Z., et al. (2020). "Single Path One-Shot Neural Architecture Search." *ECCV*.
4. Liu, H., et al. (2019). "DARTS: Differentiable Architecture Search." *ICLR*.
5. Wu, B., et al. (2019). "FBNet: Hardware-Aware Efficient ConvNet Design via Differentiable NAS." *CVPR*.
6. Lin, M., et al. (2021). "Zen-NAS: A Zero-Shot NAS for High-Performance Image Recognition." *ICCV*.
7. Yu, J., et al. (2020). "BigNAS: Scaling Up Neural Architecture Search with Big Single-Stage Models." *ECCV*.
8. Tan, M., and Le, Q. (2019). "EfficientNet: Rethinking Model Scaling for CNNs." *ICML*.
9. Howard, A., et al. (2019). "Searching for MobileNetV3." *ICCV*.
10. Lin, J., et al. (2022). "On-Device Training Under 256KB Memory." *NeurIPS*.
