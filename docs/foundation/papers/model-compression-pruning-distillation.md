# 模型压缩：剪枝与知识蒸馏在边缘部署中的对比
> **难度**：高级 | **领域**：模型优化技术 | **阅读时间**：约 22 分钟

## 引言

把一头大象塞进冰箱需要三步，把一个大模型塞进MCU需要的步骤更多。现实中，我们训练出的模型动辄几十MB甚至几GB，而边缘MCU往往只有几百KB的Flash。模型压缩就是这门"瘦身"的技术 -- 剪枝像修剪树枝，砍掉没用的枝条让树更精干；知识蒸馏像师傅带徒弟，大模型把经验传授给小模型，让小模型也能做出好判断。

## 1 模型压缩的动机

### 1.1 边缘设备的资源约束

边缘设备与云服务器的资源差距巨大：

| 指标 | 云服务器(GPU) | 边缘MCU |
|------|---------------|----------|
| 内存 | 16-64GB | 64-512KB |
| 存储 | TB级 | 256KB-2MB |
| 算力 | TFLOPS | DMIPS |
| 功耗 | 200W+ | <100mW |

### 1.2 压缩目标

模型压缩要同时追求：

- **更小**：模型体积适合目标设备存储
- **更快**：推理延迟满足实时性要求
- **更省**：功耗在设备电池预算内
- **精度可接受**：压缩后精度损失在容忍范围内

## 2 剪枝概述

### 2.1 剪枝的基本思想

神经网络的参数中存在大量冗余。剪枝就是识别并移除这些冗余参数，使网络更精简。

```
原始网络:  O-O-O-O    剪枝后:  O---O
           |X|X|                |   |
           O-O-O-O              O---O
           |X|X|                |   |
           O-O-O-O              O---O
```

### 2.2 结构化 vs 非结构化

| 维度 | 非结构化剪枝 | 结构化剪枝 |
|------|-------------|-----------|
| 粒度 | 单个权重 | 整个滤波器/通道/层 |
| 稀疏性 | 需要稀疏计算支持 | 直接减少矩阵维度 |
| 硬件加速 | 不友好 | 友好 |
| 精度损失 | 较小 | 较大 |
| 实际加速 | 有限 | 显著 |

## 3 非结构化剪枝

### 3.1 幅度剪枝

最简单也最常用的方法：将绝对值最小的权重置零，认为小权重对输出贡献小。

```python
# 幅度剪枝示例
import numpy as np

def magnitude_prune(weights, sparsity=0.5):
    """按幅度剪枝，保留最大的(1-sparsity)比例权重"""
    threshold = np.percentile(np.abs(weights), sparsity * 100)
    mask = np.abs(weights) > threshold
    pruned = weights * mask
    return pruned, mask
```

### 3.2 彩票假设

Frankle & Carbin提出的彩票假设(Lottery Ticket Hypothesis)：

- 在随机初始化的大型网络中，存在一个稀疏子网络("中奖彩票")
- 这个子网络单独训练可以达到原网络的精度
- 意义：剪枝不仅是压缩手段，可能揭示了网络有效结构的本质

### 3.3 非结构化剪枝的局限

虽然非结构化剪枝能产生极高的稀疏率(90%+)，但实际加速有限：

- 稀疏矩阵运算需要特殊硬件支持
- 通用GPU/MCU无法高效跳过零值计算
- 内存访问模式不规则，cache利用率低

## 4 结构化剪枝

### 4.1 滤波器剪枝

卷积网络中最常用的结构化剪枝，移除整个卷积滤波器：

```python
# 滤波器剪枝：按L1范数移除最不重要的滤波器
def filter_prune(conv_weights, num_prune):
    """conv_weights shape: [out_ch, in_ch, kH, kW]"""
    # 计算每个输出通道的L1范数
    filter_norms = np.sum(np.abs(conv_weights), axis=(1, 2, 3))
    # 找到范数最小的滤波器索引
    prune_idx = np.argsort(filter_norms)[:num_prune]
    # 移除这些滤波器
    keep_idx = [i for i in range(conv_weights.shape[0])
                if i not in prune_idx]
    return conv_weights[keep_idx, :, :, :]
```

### 4.2 通道剪枝

移除输入通道，同时影响前后层。需要调整前后层的维度来保持一致性。

### 4.3 层剪枝

直接移除整个残差块或层，对深度网络的压缩效果明显。

## 5 剪枝工作流

### 5.1 训练-剪枝-微调循环

```
1. 训练完整模型至收敛
2. 按剪枝准则移除参数/滤波器
3. 微调恢复精度(重要!)
4. 回到步骤2，逐步增加剪枝率
5. 重复直到达到目标大小或精度下限
```

### 5.2 渐进式剪枝

一次性大幅剪枝会导致精度崩塌。推荐渐进策略：

- 每次剪枝5-10%的参数
- 微调1-2个epoch恢复精度
- 反复迭代直到达到目标稀疏率

### 5.3 微调策略

微调是恢复剪枝后精度的关键：

- 使用较小学习率(原学习率的1/10)
- 可能需要重新设定学习率调度
- 知识蒸馏可作为微调的辅助(用原模型做教师)

## 6 知识蒸馏概述

### 6.1 蒸馏的基本思想

让小模型(学生)学习大模型(教师)的输出分布，而不仅仅是硬标签：

```
教师模型(大) --> 软标签(概率分布) --> 学生模型(小) 学习模仿
硬标签(0/1)  --> 标准交叉熵训练    --> 学生模型(小) 直接学习
```

软标签携带了更多信息：教师对"错误答案"的相对置信度，这些暗知识(Dark Knowledge)帮助学生学到更丰富的模式。

### 6.2 温度参数

softmax中加入温度T来软化输出分布：

```python
import torch
import torch.nn.functional as F

def distillation_loss(student_logits, teacher_logits, labels,
                      T=4.0, alpha=0.7):
    """蒸馏损失 = alpha * KL散度 + (1-alpha) * 交叉熵"""
    # 软标签损失：学生和教师的软化输出之间的KL散度
    soft_loss = F.kl_div(
        F.log_softmax(student_logits / T, dim=1),
        F.softmax(teacher_logits / T, dim=1),
        reduction='batchmean') * (T * T)

    # 硬标签损失：标准交叉熵
    hard_loss = F.cross_entropy(student_logits, labels)

    return alpha * soft_loss + (1 - alpha) * hard_loss
```

温度T越大，输出分布越平滑，类别间的关系信息越丰富。常用T=3-5。

## 7 蒸馏变体

### 7.1 离线蒸馏

最常见的方式：教师模型已训练好且固定，只训练学生模型。

- 优点：简单，教师模型可复用
- 缺点：教师模型的质量直接决定蒸馏上限

### 7.2 在线蒸馏

教师和学生同时训练，互相促进：

- 教师从学生的反馈中改进
- 适合没有预训练大模型的场景
- 实现更复杂，训练成本更高

### 7.3 自蒸馏

同一架构不同深度的输出之间做蒸馏：

- 深层输出作为浅层的教师
- 不需要额外的教师模型
- 本质上是一种正则化

### 7.4 特征蒸馏

不仅匹配最终输出，还匹配中间层特征：

```python
# 特征蒸馏：匹配中间层激活
def feature_distill_loss(student_feat, teacher_feat):
    """匹配中间层特征图"""
    # 可能需要1x1卷积对齐通道数
    if student_feat.shape != teacher_feat.shape:
        student_feat = align_channels(student_feat, teacher_feat.shape[1])
    return F.mse_loss(student_feat, teacher_feat)
```

## 8 剪枝与蒸馏对比

### 8.1 核心对比

| 维度 | 剪枝 | 知识蒸馏 |
|------|------|----------|
| 架构 | 同架构，更稀疏 | 不同架构，从头设计 |
| 前提 | 需要已训练好的大模型 | 需要已训练好的大模型做教师 |
| 训练成本 | 微调(少量epoch) | 完整训练学生模型 |
| 灵活性 | 受原架构限制 | 可自由设计学生架构 |
| 硬件友好 | 结构化剪枝友好 | 天然友好(紧凑架构) |
| 精度恢复 | 依赖微调质量 | 依赖教师质量和温度设置 |

### 8.2 选择决策树

```
是否已有训练好的大模型?
    |
    +-- 否 --> 先训练大模型(两种都需要)
    |
    +-- 是 --> 是否需要保持相同架构?
                |
                +-- 是 --> 剪枝
                |
                +-- 否 --> 目标硬件是否明确?
                            |
                            +-- 是 --> 知识蒸馏(为学生量身设计)
                            |
                            +-- 否 --> 两者都试，选结果更好的
```

## 9 组合技术

### 9.1 压缩流水线

多种压缩技术可以串联使用：

```
原始大模型
    |
    v
[剪枝] 移除冗余滤波器
    |
    v
[蒸馏] 用剪枝后模型做教师，训练更小的学生
    |
    v
[量化] INT8量化进一步减小体积和加速
    |
    v
[部署] TFLite Micro / ONNX Runtime
```

### 9.2 剪枝后蒸馏

先用剪枝得到中等大小的模型，再用它做教师蒸馏到更小的学生：

- 剪枝保持了原模型的知识
- 蒸馏进一步压缩到目标大小
- 两步精度损失比一步到位更小

### 9.3 蒸馏后量化

蒸馏得到的学生模型已经是紧凑架构，再用量化进一步压缩：

- 量化几乎不影响精度(对于INT8)
- 模型体积再减小4倍
- 推理速度提升2-4倍

## 10 实际效果

### 10.1 剪枝效果

| 模型 | 剪枝率 | 精度变化 | 大小变化 |
|------|--------|----------|----------|
| MobileNetV2 | 50% | -1.0% | 50% |
| ResNet-50 | 70% | -1.5% | 70% |
| VGG-16 | 90% | -0.5% | 90% |

### 10.2 蒸馏效果

| 教师模型 | 学生模型 | 教师精度 | 学生精度 | 参数比 |
|----------|----------|----------|----------|--------|
| ResNet-50 | MobileNetV2 | 76.0% | 73.5% | 1:7 |
| BERT-Base | TinyBERT | 79.6% | 72.5% | 1:10 |
| EfficientNet-B7 | EfficientNet-B0 | 84.3% | 77.1% | 1:16 |

### 10.3 组合效果

MobileNetV2在CIFAR-10上的压缩实验：

| 阶段 | 模型大小 | 精度 |
|------|----------|------|
| 原始 | 9.2MB | 94.1% |
| 剪枝50% | 4.8MB | 93.2% |
| 剪枝+蒸馏 | 2.1MB | 92.8% |
| 剪枝+蒸馏+INT8 | 540KB | 92.5% |

## 11 边缘部署考量

### 11.1 剪枝模型的部署

结构化剪枝后的模型：

- 直接导出为标准格式(ONNX/TFLite)
- 无需特殊推理引擎
- 配合TFLite Micro可直接在MCU运行

### 11.2 蒸馏模型的部署

蒸馏设计的紧凑架构：

- 从一开始就针对目标硬件优化
- 卷积层深度、核大小都可定制
- 避免MCU不友好的操作(如大矩阵乘法)

### 11.3 MCU上的资源规划

```c
// 模型部署资源检查
typedef struct {
    uint32_t flash_used;    // Flash占用
    uint32_t ram_peak;      // RAM峰值
    uint32_t infer_time_ms; // 推理时间
    float    accuracy;       // 精度
} model_profile_t;

// 示例：STM32L4上的模型配置
// 目标: Flash < 256KB, RAM < 64KB, 推理 < 50ms
model_profile_t compressed_model = {
    .flash_used = 89600,      // 87.5KB
    .ram_peak = 32768,        // 32KB
    .infer_time_ms = 28,      // 28ms
    .accuracy = 0.925         // 92.5%
};
```

## 总结

剪枝和知识蒸馏是模型压缩的两大支柱技术。剪枝在同一架构内做减法，适合已有大模型需要快速瘦身；蒸馏跨架构做知识迁移，适合为目标硬件量身打造高效模型。实际项目中，两者往往组合使用：先剪枝去冗余，再蒸馏到紧凑架构，最后量化到INT8，最终在MCU上获得百KB级的高精度模型。选择哪种技术取决于：是否已有训练好的模型、目标架构是否固定、以及精度-大小权衡的容忍度。

## 参考文献

1. Frankle J, Carlin M. The Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks. ICLR, 2019.
2. Hinton G, et al. Distilling the Knowledge in a Neural Network. arXiv:1503.02531, 2015.
3. Li H, et al. Pruning Filters for Efficient ConvNets. ICLR, 2017.
4. Sanh V, et al. DistilBERT: A Distilled Version of BERT. arXiv:1910.01108, 2019.
5. Han S, et al. Learning both Weights and Connections for Efficient Neural Networks. NeurIPS, 2015.
