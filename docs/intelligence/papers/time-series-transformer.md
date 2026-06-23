# 时序预测 Transformer 模型

> **难度**：🟡 中级 | **领域**：时序预测、Transformer、边缘部署 | **阅读时间**：约 22 分钟

## 日常类比

想象你在看一部长篇电视剧并预测下一集剧情。传统方法（LSTM）就像从头到尾按顺序回忆——越早的剧情越容易忘。而 **Transformer** 像拥有一本完美的笔记本，你可以随时翻到任何一集去查看关键情节，并且自动标记出与当前最相关的几集——这就是"注意力机制"。

在时序预测中，传感器数据就是这部连续剧：温度、压力、流量等信号不断产生。Transformer 能直接"关注"历史中最相关的时间点，不管它们距离当前多远。比如预测今天的用电量时，它可以同时关注"昨天同时段"和"上周同一天"——不受距离限制。

但原版 Transformer 的自注意力复杂度是 $O(N^2)$——序列越长计算量越大。因此出现了 Informer、Autoformer、PatchTST 等专为时序优化的变体。

## 1. 从 NLP 到时序：为什么 Transformer 能用

### 1.1 时序预测的本质

时序预测任务：给定历史 $x_{1:L}$（lookback window），预测未来 $x_{L+1:L+H}$（forecast horizon）。

| 挑战 | LSTM 的问题 | Transformer 的优势 |
|------|------------|-------------------|
| 长距离依赖 | 梯度消失，难记 >100 步 | 注意力直接连接任意距离 |
| 多周期性 | 需要人工设计特征 | 自动发现周期模式 |
| 并行训练 | 必须顺序计算 | 全部位置并行 |
| 多变量关系 | 需要堆叠或设计结构 | 多头注意力自动建模 |

### 1.2 基本架构回顾

```python
import torch
import torch.nn as nn
import math

class TimeSeriesTransformer(nn.Module):
    """最基础的时序 Transformer"""
    
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2, 
                 seq_len=96, pred_len=24):
        super().__init__()
        self.input_projection = nn.Linear(input_dim, d_model)
        self.pos_encoding = PositionalEncoding(d_model, seq_len)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, 
            dim_feedforward=d_model*4, dropout=0.1, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        self.output_projection = nn.Linear(d_model, input_dim)
        self.pred_len = pred_len
    
    def forward(self, x):
        """x: [batch, seq_len, input_dim]"""
        x = self.input_projection(x)
        x = self.pos_encoding(x)
        x = self.encoder(x)
        # 取最后 pred_len 个位置的输出
        out = self.output_projection(x[:, -self.pred_len:, :])
        return out

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe.unsqueeze(0))
    
    def forward(self, x):
        return x + self.pe[:, :x.size(1)]
```

## 2. 关键模型演进

### 2.1 Informer（AAAI 2021 最佳论文）

核心创新：**ProbSparse Attention**——不是所有时间点都同样重要，只计算最"活跃"的 query 的注意力。

复杂度从 $O(L^2)$ 降到 $O(L \log L)$。

```python
class ProbSparseAttention(nn.Module):
    """Informer 的稀疏注意力"""
    
    def __init__(self, d_model, n_heads, factor=5):
        super().__init__()
        self.factor = factor  # 采样因子
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
    
    def forward(self, Q, K, V):
        B, H, L_Q, D = Q.shape
        L_K = K.shape[2]
        
        # 采样 u = factor * ln(L_K) 个 key 来估计每个 query 的"活跃度"
        u = min(self.factor * int(math.ceil(math.log(L_K))), L_K)
        U = min(self.factor * int(math.ceil(math.log(L_Q))), L_Q)
        
        # 随机采样 u 个 key
        sample_idx = torch.randint(L_K, (u,))
        K_sample = K[:, :, sample_idx, :]
        
        # 计算 Q 与采样 K 的注意力分数
        scores = torch.matmul(Q, K_sample.transpose(-2, -1)) / math.sqrt(D)
        
        # "活跃度"度量：最大分数 - 均匀分布的期望
        M = scores.max(dim=-1).values - scores.mean(dim=-1)
        
        # 只保留最活跃的 U 个 query
        top_u_idx = M.topk(U, dim=-1).indices
        
        # 只对这 U 个 query 计算完整注意力
        Q_selected = Q.gather(2, top_u_idx.unsqueeze(-1).expand(-1, -1, -1, D))
        full_scores = torch.matmul(Q_selected, K.transpose(-2, -1)) / math.sqrt(D)
        attn = torch.softmax(full_scores, dim=-1)
        output = torch.matmul(attn, V)
        
        return output
```

### 2.2 Autoformer（NeurIPS 2021）

核心创新：**Auto-Correlation** 取代 self-attention——利用序列的自相关性发现周期模式。

```python
class AutoCorrelation(nn.Module):
    """Autoformer 的自相关注意力"""
    
    def __init__(self, d_model, n_heads, factor=3):
        super().__init__()
        self.factor = factor
        self.n_heads = n_heads
    
    def forward(self, Q, K, V):
        B, H, L, D = Q.shape
        
        # 1. 在频域计算自相关（利用 FFT 加速）
        Q_fft = torch.fft.rfft(Q, dim=2)
        K_fft = torch.fft.rfft(K, dim=2)
        
        # 频域相乘 = 时域卷积 = 自相关
        corr = torch.fft.irfft(Q_fft * K_fft.conj(), dim=2)
        
        # 2. 找到 top-k 个最大相关的延迟（周期）
        k = min(self.factor * int(math.ceil(math.log(L))), L)
        top_k_values, top_k_delays = corr.topk(k, dim=2)
        
        # 3. 按延迟对 V 进行 roll（移位）并加权聚合
        weights = torch.softmax(top_k_values, dim=2)
        output = torch.zeros_like(V)
        for i in range(k):
            delay = top_k_delays[:, :, i:i+1, :]
            rolled_V = torch.roll(V, shifts=int(delay.mean().item()), dims=2)
            output += weights[:, :, i:i+1, :] * rolled_V
        
        return output
```

### 2.3 PatchTST（ICLR 2023）

核心创新：
1. **Patching**：把时序切成固定长度的 patch，类似 ViT 对图像的处理
2. **Channel-Independent**：每个变量独立建模，共享同一个 Transformer

```python
class PatchTST(nn.Module):
    """Patch Time Series Transformer"""
    
    def __init__(self, input_dim, seq_len=512, pred_len=96, 
                 patch_len=16, stride=8, d_model=128, n_heads=8, n_layers=3):
        super().__init__()
        self.patch_len = patch_len
        self.stride = stride
        self.input_dim = input_dim
        self.pred_len = pred_len
        
        # Patch 数量
        self.n_patches = (seq_len - patch_len) // stride + 1
        
        # Patch 嵌入
        self.patch_embedding = nn.Linear(patch_len, d_model)
        self.pos_encoding = nn.Parameter(torch.randn(1, self.n_patches, d_model))
        
        # Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads,
            dim_feedforward=d_model*4, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, n_layers)
        
        # 预测头：将 patch 表示映射到预测长度
        self.head = nn.Linear(self.n_patches * d_model, pred_len)
    
    def forward(self, x):
        """x: [batch, seq_len, input_dim]"""
        B, L, C = x.shape
        
        # Channel-Independent: 逐通道处理
        outputs = []
        for c in range(C):
            xc = x[:, :, c]  # [B, L]
            
            # 创建 patches
            patches = xc.unfold(1, self.patch_len, self.stride)  # [B, n_patches, patch_len]
            
            # Patch 嵌入 + 位置编码
            z = self.patch_embedding(patches) + self.pos_encoding  # [B, n_patches, d_model]
            
            # Transformer 编码
            z = self.encoder(z)  # [B, n_patches, d_model]
            
            # 展平并预测
            z_flat = z.reshape(B, -1)  # [B, n_patches * d_model]
            pred = self.head(z_flat)    # [B, pred_len]
            outputs.append(pred)
        
        return torch.stack(outputs, dim=-1)  # [B, pred_len, C]
```

### 2.4 iTransformer（ICLR 2024）

核心创新：**反转注意力维度**——在变量（通道）维度而非时间维度做注意力。

传统 Transformer：token = 时间步，注意力在时间轴上。
iTransformer：token = 变量，注意力在变量轴上，捕获多变量之间的关系。

```python
class iTransformer(nn.Module):
    """Inverted Transformer - 在变量维度做注意力"""
    
    def __init__(self, n_vars, seq_len=96, pred_len=24, d_model=256, n_heads=8, n_layers=3):
        super().__init__()
        # 每个变量的整个历史序列作为一个 token
        self.var_embedding = nn.Linear(seq_len, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=n_heads,
            dim_feedforward=d_model*4, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, n_layers)
        self.head = nn.Linear(d_model, pred_len)
    
    def forward(self, x):
        """x: [batch, seq_len, n_vars]"""
        # 转置：每个变量的时间序列作为一个 token
        x = x.permute(0, 2, 1)  # [B, n_vars, seq_len]
        
        # 嵌入
        z = self.var_embedding(x)  # [B, n_vars, d_model]
        
        # 变量间注意力
        z = self.encoder(z)  # [B, n_vars, d_model]
        
        # 预测
        out = self.head(z)   # [B, n_vars, pred_len]
        return out.permute(0, 2, 1)  # [B, pred_len, n_vars]
```

## 3. 模型性能对比

### 3.1 标准基准测试（ETTh1 数据集，电力变压器温度预测）

| 模型 | MSE (96步) | MSE (336步) | MSE (720步) | 参数量 | 推理速度 |
|------|-----------|------------|------------|--------|---------|
| LSTM | 0.098 | 0.175 | 0.261 | 180K | 12ms |
| Prophet | 0.142 | 0.208 | 0.312 | - | 500ms |
| Informer | 0.075 | 0.134 | 0.197 | 4.8M | 25ms |
| Autoformer | 0.071 | 0.127 | 0.185 | 3.2M | 18ms |
| PatchTST | 0.058 | 0.108 | 0.166 | 1.5M | 8ms |
| iTransformer | 0.055 | 0.105 | 0.162 | 2.1M | 10ms |
| DLinear | 0.065 | 0.121 | 0.178 | 35K | 1ms |

### 3.2 关键发现

- PatchTST 和 iTransformer 是当前 SOTA
- DLinear（简单线性层）效果惊人地好——质疑 Transformer 的必要性
- 随着预测长度增加，Transformer 优势越明显
- 参数量不直接决定性能——PatchTST 参数比 Informer 少但效果更好

## 4. 边缘部署考量

### 4.1 模型瘦身策略

| 策略 | 压缩比 | 精度损失 | 适用平台 |
|------|--------|---------|---------|
| 知识蒸馏 | 5-10x | 1-3% | RPi/Jetson |
| INT8 量化 | 4x | 0.5-2% | NPU/DSP |
| 剪枝 (结构化) | 2-4x | 1-5% | 通用 CPU |
| 低秩近似 | 2-3x | 1-2% | 通用 |
| PatchTST (小配置) | 原生轻量 | 参考性能 | MCU/RPi |

### 4.2 边缘友好配置

```python
# 针对树莓派 4 优化的 PatchTST 配置
edge_config = {
    'patch_len': 16,       # 较大 patch 减少 token 数
    'stride': 16,          # 非重叠 patch
    'd_model': 64,         # 减小隐藏维度
    'n_heads': 4,          # 少量注意力头
    'n_layers': 2,         # 浅层网络
    'seq_len': 96,         # 较短输入
    'pred_len': 24,        # 适度预测长度
}
# 预计参数量: ~200K, 推理时间: <5ms on RPi4
```

### 4.3 ONNX 导出与优化

```python
import torch.onnx

# 导出为 ONNX
model = PatchTST(**edge_config, input_dim=7, n_vars=7)
dummy_input = torch.randn(1, 96, 7)

torch.onnx.export(
    model, dummy_input, "patchtst_edge.onnx",
    input_names=['input'], output_names=['forecast'],
    dynamic_axes={'input': {0: 'batch'}, 'forecast': {0: 'batch'}}
)

# 用 ONNX Runtime 优化推理
import onnxruntime as ort
session = ort.InferenceSession("patchtst_edge.onnx")
result = session.run(None, {'input': dummy_input.numpy()})
```

## 5. 应用场景

### 5.1 能源负荷预测

- 输入：历史 96 小时用电量 + 天气 + 日历特征
- 输出：未来 24-96 小时负荷预测
- 价值：峰谷错峰调度，节省 10-15% 电费

### 5.2 工业设备剩余寿命预测

- 输入：振动、温度、电流等传感器历史数据
- 输出：设备健康指数趋势预测
- 价值：提前 7-30 天预警故障，避免非计划停机

### 5.3 气象微观预测

- 输入：本地气象站数据（温度、湿度、气压、风速）
- 输出：未来 1-6 小时超局地天气预测
- 价值：精准农业灌溉、光伏发电功率预测

## 6. 与传统方法的深度对比

### 6.1 Transformer vs LSTM

| 维度 | LSTM | Transformer |
|------|------|-------------|
| 长序列建模 | 衰减严重 | 直接注意力 |
| 训练速度 | 无法并行 | 完全并行 |
| 可解释性 | 隐状态难解释 | 注意力可视化 |
| 小数据表现 | 较好 | 容易过拟合 |
| 部署复杂度 | 低 | 中 |
| 增量预测 | 天然支持 | 需要特殊设计 |

### 6.2 何时不需要 Transformer

- 序列短（< 50 步）且模式简单 → DLinear 或 ARIMA
- 数据量极少（< 1000 条）→ Prophet 或统计方法
- 对延迟极敏感（< 1ms）→ 线性模型
- 纯周期性信号 → 傅里叶分析

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 Prophet/ARIMA 建立 baseline（理解时序预测的评估指标）
2. **第二步**：用 PyTorch 实现最简 Transformer（上面的基础版本）
3. **第三步**：使用 [TSLib](https://github.com/thuml/Time-Series-Library) 库跑 PatchTST
4. **第四步**：在 ETTh1/Weather 数据集上对比各模型
5. **第五步**：导出 ONNX 到树莓派部署，测量真实推理延迟

### 7.2 具体调优建议

**模型选择决策树**：
- 单变量、短预测（< 48步）→ DLinear
- 多变量、变量间相关性强 → iTransformer
- 长序列（> 512步）输入 → PatchTST
- 强周期性 → Autoformer
- 需要概率预测 → TimeGrad 或 Informer + 概率头

**训练技巧**：
- 学习率：1e-4 到 3e-4（Adam），warmup 5-10 epochs
- Batch size：16-64（时序数据通常不需要太大 batch）
- Lookback 长度：通常是预测长度的 2-4 倍
- 归一化：RevIN（可逆实例归一化）效果好于全局归一化
- 正则化：Dropout 0.1-0.3，Patch Dropout 效果更好

## 参考文献

1. Zhou, H., et al. (2021). "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting." *AAAI* (Best Paper).
2. Wu, H., et al. (2021). "Autoformer: Decomposition Transformers with Auto-Correlation for Long-Term Series Forecasting." *NeurIPS*.
3. Nie, Y., et al. (2023). "A Time Series is Worth 64 Words: Long-term Forecasting with Transformers (PatchTST)." *ICLR*.
4. Liu, Y., et al. (2024). "iTransformer: Inverted Transformers Are Effective for Time Series Forecasting." *ICLR*.
5. Zeng, A., et al. (2023). "Are Transformers Effective for Time Series Forecasting? (DLinear)." *AAAI*.
6. Vaswani, A., et al. (2017). "Attention Is All You Need." *NeurIPS*.
7. Wu, H., et al. (2023). "TimesNet: Temporal 2D-Variation Modeling for General Time Series Analysis." *ICLR*.
8. Lim, B., et al. (2021). "Temporal Fusion Transformers for Interpretable Multi-horizon Time Series Forecasting." *IJF*.
9. Das, A., et al. (2024). "A Decoder-Only Foundation Model for Time-Series Forecasting (TimesFM)." *ICML*.
10. Liu, Y., et al. (2022). "Non-stationary Transformers: Exploring the Stationarity in Time Series Forecasting." *NeurIPS*.
