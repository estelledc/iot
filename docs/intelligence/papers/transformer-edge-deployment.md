# Transformer 模型边缘部署技术

> **难度**：🟡 中级 | **领域**：边缘智能、模型压缩、深度学习推理 | **阅读时间**：约 20 分钟

## 日常类比

想象你有一本百科全书（Transformer 模型），内容丰富但重达 50 公斤。你需要带着它去野外考察（边缘部署），但背包只能装 5 公斤。你有几个选择：把百科全书拍照缩印成口袋本（量化）、只撕下你需要的章节（剪枝）、或者请人帮你写一本精简版摘要（知识蒸馏）。

Transformer 的核心——注意力机制——就像一个会议室里每个人都要和其他所有人握手。10 个人需要 45 次握手，100 个人需要 4950 次。这种"全员握手"的计算量随序列长度呈平方增长，是边缘部署的最大瓶颈。

本文将系统介绍如何把这些"大块头"模型塞进边缘设备，同时保持可接受的精度。

## 1. 注意力机制的计算瓶颈

### 1.1 标准自注意力的复杂度

标准 Multi-Head Self-Attention 的计算复杂度为 O(n^2 * d)，内存复杂度为 O(n^2)，其中 n 是序列长度，d 是特征维度。

| 序列长度 | 注意力矩阵大小 | FP32 内存占用 | 典型计算时间(RPi 4) |
|----------|---------------|--------------|-------------------|
| 128      | 16 KB         | 64 KB        | ~5 ms             |
| 512      | 256 KB        | 1 MB         | ~80 ms            |
| 2048     | 4 MB          | 16 MB        | ~1.2 s            |
| 8192     | 64 MB         | 256 MB       | 不可行            |

### 1.2 边缘设备的硬件约束

典型边缘设备的资源对比：

| 设备 | RAM | 算力 | 功耗 | 典型场景 |
|------|-----|------|------|----------|
| Raspberry Pi 4 | 4-8 GB | 13.5 GFLOPS | 5-15W | 智能家居网关 |
| Jetson Nano | 4 GB | 472 GFLOPS | 5-10W | 视觉推理 |
| Jetson Orin Nano | 8 GB | 40 TOPS (INT8) | 7-15W | 多模态AI |
| STM32H7 (MCU) | 1 MB | 0.48 GFLOPS | <1W | 传感器前处理 |

## 2. 高效注意力机制

### 2.1 线性注意力 (Linear Attention)

核心思想：用核函数分解 softmax，将 O(n^2) 降为 O(n)。

```python
import torch
import torch.nn as nn

class LinearAttention(nn.Module):
    """线性注意力：用 elu+1 替代 softmax，复杂度 O(n*d^2)"""
    def __init__(self, dim, heads=8):
        super().__init__()
        self.heads = heads
        self.dim_head = dim // heads
        self.to_qkv = nn.Linear(dim, dim * 3, bias=False)
        
    def feature_map(self, x):
        # elu + 1 作为核函数近似
        return torch.nn.functional.elu(x) + 1
    
    def forward(self, x):
        b, n, _ = x.shape
        qkv = self.to_qkv(x).chunk(3, dim=-1)
        q, k, v = map(
            lambda t: t.view(b, n, self.heads, self.dim_head).transpose(1, 2), 
            qkv
        )
        
        q = self.feature_map(q)  # [b, h, n, d]
        k = self.feature_map(k)
        
        # 关键：先算 k^T @ v (d x d)，再乘 q，避免 n x n 矩阵
        kv = torch.einsum('bhnd,bhnm->bhdm', k, v)  # [b, h, d, d]
        z = 1.0 / (torch.einsum('bhnd,bhd->bhn', q, k.sum(dim=2)) + 1e-6)
        out = torch.einsum('bhnd,bhdm,bhn->bhnm', q, kv, z)
        
        return out.transpose(1, 2).reshape(b, n, -1)
```

### 2.2 稀疏注意力 (Sparse Attention)

只计算部分位置对的注意力分数，典型模式包括：

- **局部窗口**：每个 token 只关注前后 w 个位置，复杂度 O(n*w)
- **扩张稀疏**：间隔采样，类似空洞卷积
- **Top-k 稀疏**：只保留注意力分数最高的 k 个连接

### 2.3 FlashAttention

FlashAttention 不改变数学结果，而是优化 GPU 内存访问模式：

```
标准注意力：Q x K^T -> 写入 HBM -> softmax -> 写入 HBM -> x V
FlashAttention：分块计算，中间结果留在 SRAM，减少 HBM 读写

实测加速（Jetson Orin，序列长度 512）：
- 标准实现：12.3 ms
- FlashAttention-2：4.1 ms（3x 加速）
- 内存节省：从 O(n^2) 降至 O(n)
```

## 3. 轻量级 Transformer 架构

### 3.1 知识蒸馏系列

| 模型 | 参数量 | BERT-base 比例 | GLUE 分数 | 推理速度(RPi4) |
|------|--------|---------------|-----------|---------------|
| BERT-base | 110M | 100% | 79.6 | 不可行 |
| DistilBERT | 66M | 60% | 77.0 | ~450 ms/句 |
| TinyBERT-6L | 67M | 61% | 77.8 | ~420 ms/句 |
| MobileBERT | 25M | 23% | 77.7 | ~180 ms/句 |
| TinyBERT-4L | 14.5M | 13% | 74.3 | ~95 ms/句 |

### 3.2 MobileBERT 架构创新

MobileBERT 的核心设计：

```
教师模型 (IB-BERT)          学生模型 (MobileBERT)
+-------------------+      +-------------------+
| Embedding: 768    |      | Embedding: 128    |
| FFN: 3072         |  ->  | FFN: 512          |
| Attention: 768    | 蒸馏  | Attention: 128    |
| Layers: 24        |      | Layers: 24        |
| Bottleneck: 无    |      | Bottleneck: 有    |
+-------------------+      +-------------------+
```

关键技巧：使用瓶颈结构（bottleneck）在层间压缩维度，保持层数不变以维持表达能力。

### 3.3 Vision Transformer 剪枝

ViT 的剪枝策略与 NLP Transformer 不同，因为 patch embedding 的空间结构很重要：

```python
# Token 剪枝示例：根据 [CLS] 注意力分数移除不重要的 patch
def token_pruning(attention_scores, tokens, keep_ratio=0.7):
    """
    attention_scores: [batch, heads, seq_len, seq_len]
    tokens: [batch, seq_len, dim]
    """
    # CLS 对其他 token 的注意力
    cls_attn = attention_scores[:, :, 0, 1:]
    cls_attn = cls_attn.mean(dim=1)  # 多头平均 [batch, seq_len-1]
    
    num_keep = int((tokens.shape[1] - 1) * keep_ratio)
    _, indices = cls_attn.topk(num_keep, dim=-1)
    indices = indices.sort(dim=-1).values
    
    # 保留 CLS + top-k tokens
    cls_token = tokens[:, :1, :]
    kept_tokens = torch.gather(
        tokens[:, 1:, :], 1, 
        indices.unsqueeze(-1).expand(-1, -1, tokens.shape[-1])
    )
    return torch.cat([cls_token, kept_tokens], dim=1)
```

## 4. 量化技术

### 4.1 INT8 量化

对称量化公式：`x_quant = round(x / scale)`，其中 `scale = max(|x|) / 127`

```python
# PyTorch 动态量化示例
import torch.quantization
from transformers import MobileBertModel

model = MobileBertModel.from_pretrained("google/mobilebert-uncased")
quantized_model = torch.quantization.quantize_dynamic(
    model, 
    {torch.nn.Linear},  # 量化所有线性层
    dtype=torch.qint8
)

# 模型大小对比
# FP32: 100 MB -> INT8: 25 MB (4x 压缩)
# 推理加速: 1.5-2x on ARM CPU
```

### 4.2 INT4 量化

INT4 将每个权重压缩到 4 bit，但需要更精细的量化策略：

| 量化方案 | 位宽 | 模型大小 | 精度损失(GLUE) | 适用场景 |
|----------|------|----------|---------------|----------|
| FP32 | 32 bit | 100% | 基准 | 训练 |
| FP16 | 16 bit | 50% | <0.1% | GPU 推理 |
| INT8 | 8 bit | 25% | 0.5-1% | 通用边缘 |
| INT4 | 4 bit | 12.5% | 1-3% | 极端受限 |
| 混合精度 | 4-8 bit | 15-20% | 0.5-1.5% | 推荐方案 |

### 4.3 Transformer 特有的量化挑战

注意力层中的 softmax 输出分布高度不均匀（大部分接近 0，少数接近 1），直接量化会导致严重精度损失。解决方案：

- **Per-channel 量化**：每个注意力头独立计算 scale
- **混合精度**：softmax 保持 FP16，线性层用 INT8
- **SmoothQuant**：将激活的量化难度转移到权重上

## 5. 部署框架与实践

### 5.1 ONNX Runtime Mobile

```python
# 模型导出为 ONNX
import torch
from transformers import MobileBertModel

model = MobileBertModel.from_pretrained("google/mobilebert-uncased")
model.eval()

dummy_input_ids = torch.randint(0, 30522, (1, 128))
dummy_attention_mask = torch.ones(1, 128, dtype=torch.long)

torch.onnx.export(
    model, 
    (dummy_input_ids, dummy_attention_mask),
    "mobilebert.onnx",
    opset_version=14,
    input_names=["input_ids", "attention_mask"],
    output_names=["last_hidden_state"],
    dynamic_axes={"input_ids": {0: "batch", 1: "seq_len"}}
)

# ONNX Runtime 推理
import onnxruntime as ort
import numpy as np

session = ort.InferenceSession("mobilebert.onnx", providers=["CPUExecutionProvider"])
result = session.run(None, {
    "input_ids": dummy_input_ids.numpy(),
    "attention_mask": dummy_attention_mask.numpy()
})
```

### 5.2 Jetson 部署流程

```bash
# Jetson Orin Nano 部署步骤
# 1. 转换为 TensorRT 引擎
trtexec --onnx=mobilebert.onnx \
        --saveEngine=mobilebert.trt \
        --fp16 \
        --workspace=2048 \
        --minShapes=input_ids:1x1,attention_mask:1x1 \
        --optShapes=input_ids:1x128,attention_mask:1x128 \
        --maxShapes=input_ids:4x512,attention_mask:4x512

# 2. 性能测试
trtexec --loadEngine=mobilebert.trt --batch=1 --iterations=1000

# 典型结果 (Jetson Orin Nano, FP16):
# MobileBERT seq=128: 3.2 ms (312 句/秒)
# DistilBERT seq=128: 5.8 ms (172 句/秒)
# BERT-base seq=128: 15.4 ms (65 句/秒)
```

### 5.3 Raspberry Pi 部署

```python
# RPi 4 使用 TFLite 部署
import tflite_runtime.interpreter as tflite
import numpy as np

# 加载量化后的 TFLite 模型
interpreter = tflite.Interpreter(
    model_path="mobilebert_int8.tflite",
    num_threads=4  # 使用全部 4 核
)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# 推理
input_ids = np.array(
    [[101, 2023, 2003, 1037, 3231, 102] + [0]*122], 
    dtype=np.int32
)
interpreter.set_tensor(input_details[0]['index'], input_ids)
interpreter.invoke()

output = interpreter.get_tensor(output_details[0]['index'])
# RPi 4 INT8 推理: ~95 ms/句 (seq=128)
```

## 6. 延迟-精度权衡曲线

### 6.1 实测数据 (2024-2025)

在 GLUE 基准上的延迟-精度 Pareto 前沿：

```
精度(GLUE)
80 |          * BERT-base(FP32, 不可行)
   |        * DistilBERT(FP16)
78 |      * TinyBERT-6L(INT8)
   |    * MobileBERT(INT8)        <-- 推荐
76 |  * MobileBERT(INT4)
   |
74 |* TinyBERT-4L(INT8)
   |________________________
   0   50  100  150  200  延迟(ms, Jetson Nano)
```

### 6.2 选型决策树

```
需要部署 Transformer 到边缘？
|-- 设备有 GPU (Jetson 系列)?
|   |-- 精度优先 -> DistilBERT + FP16 + TensorRT
|   +-- 速度优先 -> MobileBERT + INT8 + TensorRT
|-- 只有 CPU (RPi/x86 嵌入式)?
|   |-- RAM > 2GB -> MobileBERT + INT8 + ONNX Runtime
|   +-- RAM < 2GB -> TinyBERT-4L + INT4 + TFLite
+-- MCU (< 1MB RAM)?
    +-- 不适合 Transformer，考虑 CNN/RNN 替代
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：在 PC 上用 Hugging Face 跑通 MobileBERT 推理
2. **第二步**：导出 ONNX，用 ONNX Runtime 测速
3. **第三步**：应用 INT8 动态量化，对比精度和速度
4. **第四步**：在目标设备（如 RPi 4）上部署 TFLite 版本
5. **第五步**：根据实际需求调整序列长度和批大小

### 7.2 具体调优建议

- **序列长度**：边缘场景通常不需要 512 token，128 甚至 64 就够用（IoT 文本通常很短）
- **批处理**：单条推理延迟敏感时 batch=1；吞吐优先时适当增大
- **模型选择**：先确定精度底线，再在 Pareto 前沿上选最快的
- **缓存策略**：对重复输入做 KV-cache，避免重复计算
- **异步流水线**：数据预处理和模型推理并行，隐藏 I/O 延迟

### 7.3 常见陷阱

- 不要在 ARM 设备上用 FP32 推理——没有硬件加速，比 INT8 慢 3-4 倍
- 量化前务必做 calibration，随机初始化的量化参数会导致输出全乱
- TensorRT 引擎不跨设备——在 Jetson Nano 上编译的不能直接用在 Orin 上
- 动态形状（dynamic shape）会显著降低 TensorRT 性能，尽量用固定形状

## 参考文献

1. Vaswani, A. et al. "Attention Is All You Need." NeurIPS 2017.
2. Sun, Z. et al. "MobileBERT: a Compact Task-Agnostic BERT for Resource-Limited Devices." ACL 2020.
3. Jiao, X. et al. "TinyBERT: Distilling BERT for Natural Language Understanding." EMNLP 2020.
4. Dao, T. et al. "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning." ICLR 2024.
5. Katharopoulos, A. et al. "Transformers are RNNs: Fast Autoregressive Transformers with Linear Attention." ICML 2020.
6. Xiao, G. et al. "SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models." ICML 2023.
7. NVIDIA. "TensorRT Developer Guide." 2024.
8. Rao, Y. et al. "DynamicViT: Efficient Vision Transformers with Dynamic Token Sparsification." NeurIPS 2021.
9. ONNX Runtime Team. "ONNX Runtime Mobile: Optimizing ML for Edge Devices." Microsoft, 2024.
10. Dettmers, T. et al. "The case for 4-bit precision: k-bit Inference Scaling Laws." ICML 2023.
