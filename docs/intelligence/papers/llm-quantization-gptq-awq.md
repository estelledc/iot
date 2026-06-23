# 大模型推理量化：GPTQ 与 AWQ

> **难度**：🟡 中级 | **领域**：模型压缩、大语言模型、边缘推理 | **阅读时间**：约 22 分钟

## 日常类比

想象你要搬家，有一整面墙的书（模型权重）。每本书都是精装硬皮版（FP16，每个参数 2 字节）。你的新公寓书架只有原来的四分之一大（边缘设备内存）。

GPTQ 的做法像是：逐本检查每本书，把不太重要的换成口袋平装版（4-bit），但对于那些你经常翻阅的关键参考书，会特别小心地保留关键内容。它还会在压缩一本书时，微调旁边几本书的摆放位置来补偿信息损失。

AWQ 则更聪明：它先观察你平时最常翻哪些书（激活感知），发现只有 1% 的书被频繁使用。对这 1% 的关键书籍保持高精度，其余 99% 大胆压缩。这样整体空间省了，但阅读体验几乎不变。

## 1. 量化基础回顾

### 1.1 为什么需要量化

一个 7B 参数的 LLM 在不同精度下的内存需求：

| 精度 | 每参数字节 | 7B 模型大小 | 13B 模型大小 | 70B 模型大小 |
|------|-----------|------------|-------------|-------------|
| FP32 | 4 B | 28 GB | 52 GB | 280 GB |
| FP16 | 2 B | 14 GB | 26 GB | 140 GB |
| INT8 | 1 B | 7 GB | 13 GB | 70 GB |
| INT4 | 0.5 B | 3.5 GB | 6.5 GB | 35 GB |
| 3-bit | 0.375 B | 2.6 GB | 4.9 GB | 26.3 GB |

Jetson Orin Nano 只有 8 GB 统一内存，要跑 7B 模型必须至少 INT4。

### 1.2 PTQ vs QAT

| 特性 | 训练后量化 (PTQ) | 量化感知训练 (QAT) |
|------|-----------------|-------------------|
| 需要训练数据 | 少量校准集 (128-1024 样本) | 完整训练集 |
| 计算成本 | 几分钟到几小时 | 数天到数周 |
| 精度恢复 | 中等 | 最佳 |
| 适用场景 | 部署阶段快速压缩 | 精度要求极高 |
| 代表方法 | GPTQ, AWQ, SmoothQuant | QLoRA, LLM-QAT |

对于大模型，QAT 的计算成本通常不可接受，因此 PTQ 是主流选择。

## 2. GPTQ 算法详解

### 2.1 核心思想：最优脑量化

GPTQ 基于 Optimal Brain Quantization (OBQ) 框架，核心目标是最小化量化误差：

```
min ||WX - Q(W)X||^2
```

其中 W 是原始权重，Q(W) 是量化后的权重，X 是校准数据的激活值。

### 2.2 算法流程

```python
import torch
import numpy as np

def gptq_quantize_layer(W, X, bits=4, group_size=128):
    """
    GPTQ 逐列量化算法简化实现
    W: [out_features, in_features] 权重矩阵
    X: [n_samples, in_features] 校准数据激活
    """
    rows, cols = W.shape
    Q = torch.zeros_like(W)  # 量化后的权重
    
    # 计算 Hessian: H = 2 * X^T @ X
    H = 2 * X.T @ X  # [in_features, in_features]
    H_inv = torch.linalg.cholesky_inv(torch.linalg.cholesky(
        H + 1e-6 * torch.eye(cols)  # 正则化确保正定
    ))
    
    # 按列处理
    for col in range(cols):
        w = W[:, col].clone()
        d = H_inv[col, col]  # Hessian 逆的对角元素
        
        # 量化当前列
        q = quantize_to_nbit(w, bits)
        Q[:, col] = q
        
        # 关键步骤：用 Hessian 信息补偿后续列的误差
        error = (w - q) / d
        W[:, col+1:] -= error.unsqueeze(1) * H_inv[col, col+1:].unsqueeze(0)
    
    return Q

def quantize_to_nbit(w, bits, group_size=128):
    """对称量化到 n-bit"""
    max_val = w.abs().max()
    scale = max_val / (2**(bits-1) - 1)
    q = torch.round(w / scale).clamp(-(2**(bits-1)), 2**(bits-1) - 1)
    return q * scale
```

### 2.3 GPTQ 的关键优化

- **列排序**：按 Hessian 对角线元素排序，先量化"容易"的列（对角元素大的列量化误差影响小）
- **Lazy Batch Updates**：累积多列的误差补偿，一次性更新，减少内存访问次数
- **分组量化 (Group Quantization)**：每 128 列共享一组 scale/zero-point，平衡精度和额外存储开销

## 3. AWQ 算法详解

### 3.1 核心观察：1% 的显著权重

AWQ 的关键发现：在 LLM 中，只有约 1% 的权重通道对模型输出有显著影响，这些通道对应着激活值较大的输入特征。

```python
def find_salient_channels(activations, threshold_percentile=99):
    """
    找到激活值显著的通道
    activations: [n_samples, in_features]
    """
    # 计算每个通道的平均激活幅度
    channel_importance = activations.abs().mean(dim=0)  # [in_features]
    
    # 找到 top 1% 的通道
    threshold = torch.quantile(channel_importance, threshold_percentile / 100)
    salient_mask = channel_importance > threshold
    
    return salient_mask, channel_importance
```

### 3.2 激活感知缩放

AWQ 不是简单地跳过显著权重的量化，而是通过缩放来保护它们：

```python
def awq_scale_search(W, X, bits=4, n_grid=20):
    """
    AWQ 缩放因子搜索
    对显著通道乘以 s > 1（放大权重，缩小激活），减少量化误差
    """
    importance = X.abs().mean(dim=0)  # [in_features]
    
    best_scale = torch.ones(W.shape[1])
    best_error = float('inf')
    
    # 网格搜索最优缩放因子
    for ratio in torch.linspace(0, 1, n_grid):
        # 缩放因子：重要通道放大
        scale = importance.pow(ratio).clamp(min=1e-4)
        
        # 应用缩放：W_scaled = W * diag(s)
        W_scaled = W * scale.unsqueeze(0)
        
        # 量化缩放后的权重
        W_quant = quantize_to_nbit(W_scaled, bits)
        
        # 反缩放得到最终量化权重
        W_final = W_quant / scale.unsqueeze(0)
        
        # 计算量化误差
        error = ((W @ X.T) - (W_final @ X.T)).pow(2).mean()
        
        if error < best_error:
            best_error = error
            best_scale = scale
    
    return best_scale
```

### 3.3 AWQ vs GPTQ 对比

| 特性 | GPTQ | AWQ |
|------|------|-----|
| 核心策略 | Hessian 引导的误差补偿 | 激活感知的权重缩放 |
| 校准数据量 | 128 样本 | 128 样本 |
| 量化时间 (7B) | ~10 分钟 (A100) | ~5 分钟 (A100) |
| 4-bit PPL (LLaMA-7B) | 5.85 | 5.78 |
| 硬件友好性 | 需要特殊 kernel | 标准 GEMM 即可 |
| 推理速度 | 依赖 kernel 实现 | 通常更快 1.2-1.5x |
| 内存开销 | 需存 Hessian | 只需激活统计 |

## 4. 其他量化方案对比

### 4.1 GGML/GGUF (llama.cpp)

llama.cpp 使用自定义的量化格式，专为 CPU 推理优化：

```bash
# 使用 llama.cpp 量化模型
./quantize ./models/llama-7b-f16.gguf ./models/llama-7b-q4_k_m.gguf q4_k_m

# 常用量化级别
# q4_0: 最基础的 4-bit，每 32 权重共享 1 个 scale
# q4_k_m: 混合精度 4-bit，attention 层用更高精度
# q5_k_m: 5-bit 混合，精度接近 FP16
# q3_k_s: 3-bit，极端压缩
```

### 4.2 bitsandbytes

```python
# bitsandbytes 4-bit 量化加载
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",       # NormalFloat4 量化类型
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,   # 双重量化：量化 scale 本身
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=quantization_config,
    device_map="auto"
)
# 内存占用: ~3.9 GB (vs FP16 的 14 GB)
```

### 4.3 量化质量对比 (LLaMA-2-7B, WikiText-2 PPL)

| 方法 | 位宽 | PPL | 模型大小 | 推理框架 |
|------|------|-----|----------|----------|
| FP16 基准 | 16 | 5.47 | 14 GB | PyTorch |
| GPTQ | 4 | 5.85 | 3.6 GB | AutoGPTQ |
| AWQ | 4 | 5.78 | 3.6 GB | vLLM/TGI |
| GGUF q4_k_m | 4.5 | 5.72 | 4.1 GB | llama.cpp |
| bitsandbytes NF4 | 4 | 5.82 | 3.9 GB | HF Transformers |
| GPTQ | 3 | 6.61 | 2.7 GB | AutoGPTQ |
| GGUF q3_k_s | 3 | 6.45 | 2.9 GB | llama.cpp |

## 5. 边缘设备实战部署

### 5.1 Jetson Orin 部署 7B 模型

```bash
# 在 Jetson Orin Nano (8GB) 上部署 Llama-2-7B-Q4
# 使用 llama.cpp 的 CUDA 后端

# 编译 llama.cpp with CUDA
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j$(nproc)

# 运行推理
./build/bin/llama-cli \
    -m models/llama-2-7b-q4_k_m.gguf \
    -n 128 \
    -ngl 33 \       # 所有层 offload 到 GPU
    --ctx-size 2048 \
    -p "Explain IoT edge computing in simple terms:"

# 实测性能 (Jetson Orin Nano, 8GB):
# - 首 token 延迟: ~180 ms
# - 生成速度: ~12 tokens/s (q4_k_m)
# - 内存占用: ~5.2 GB (模型 + KV cache)
# - 功耗: ~12W
```

### 5.2 内存预算计算

```python
def estimate_memory(params_b, bits, ctx_len, n_layers, d_model, n_heads):
    """估算 LLM 推理内存需求"""
    # 模型权重
    model_mem = params_b * 1e9 * bits / 8  # bytes
    
    # KV Cache (FP16)
    head_dim = d_model // n_heads
    kv_per_layer = 2 * ctx_len * d_model * 2  # K和V, FP16
    kv_total = kv_per_layer * n_layers
    
    # 激活内存 (推理时较小)
    activation_mem = 2 * ctx_len * d_model * 2  # 约 2 层的激活
    
    total = model_mem + kv_total + activation_mem
    return {
        "model_gb": model_mem / 1e9,
        "kv_cache_gb": kv_total / 1e9,
        "activation_gb": activation_mem / 1e9,
        "total_gb": total / 1e9
    }

# LLaMA-2-7B, 4-bit, ctx=2048
mem = estimate_memory(
    params_b=7, bits=4, ctx_len=2048,
    n_layers=32, d_model=4096, n_heads=32
)
# model: 3.5 GB, kv_cache: 1.0 GB, total: ~4.6 GB
# 适合 8GB Jetson Orin Nano
```

### 5.3 Perplexity 退化分析

量化位宽与困惑度的关系呈非线性：

```
PPL 退化率 (相对 FP16)
|
15%|                              * 2-bit
|
10%|                    * 3-bit
|
5% |          * 4-bit
|
2% |  * 5-bit
1% |* 8-bit
|_________________________________
   8    5    4    3    2    位宽

关键发现：
- 8->4 bit: PPL 增加 ~7% (可接受)
- 4->3 bit: PPL 增加 ~15% (任务相关)
- 3->2 bit: PPL 增加 >30% (通常不可用)
- 混合精度 (attention 8-bit + FFN 4-bit) 可在 4.5-bit 均值下接近 8-bit 精度
```

## 6. 高级技巧

### 6.1 混合精度量化策略

```python
# 不同层使用不同位宽
layer_config = {
    "embed_tokens": 8,        # 嵌入层保持高精度
    "lm_head": 8,             # 输出层保持高精度
    "self_attn.q_proj": 4,    # 注意力投影 4-bit
    "self_attn.k_proj": 4,
    "self_attn.v_proj": 4,
    "self_attn.o_proj": 4,
    "mlp.gate_proj": 4,       # FFN 层 4-bit (参数最多)
    "mlp.up_proj": 4,
    "mlp.down_proj": 4,
    "input_layernorm": 16,    # LayerNorm 保持 FP16
    "post_attention_layernorm": 16,
}
# 平均位宽约 4.3 bit，但关键层精度有保障
```

### 6.2 量化后微调 (QLoRA)

```python
from peft import LoraConfig, get_peft_model

# 在 4-bit 量化模型上添加 LoRA adapter
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
# 可训练参数: ~10M (vs 7B 总参数)
# 训练内存: ~6 GB (可在单张消费级 GPU 上完成)
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 bitsandbytes 加载 4-bit 模型，感受量化效果
2. **第二步**：用 llama.cpp 在本地 CPU 跑 GGUF 模型，理解不同量化级别
3. **第三步**：学习 GPTQ 原理，用 AutoGPTQ 量化自己的模型
4. **第四步**：对比 AWQ 和 GPTQ 在目标任务上的表现
5. **第五步**：在边缘设备上部署，测量实际延迟和精度

### 7.2 具体调优建议

- **选择量化方法**：GPU 推理优先 AWQ（kernel 优化好）；CPU 推理优先 GGUF（llama.cpp 生态成熟）
- **校准数据**：使用与目标任务相似的数据做校准，通用场景用 C4/WikiText
- **分组大小**：group_size=128 是精度和速度的最佳平衡点；64 更精确但更慢
- **评估指标**：不要只看 PPL，务必在下游任务上评估（PPL 低不代表任务表现好）
- **KV Cache 优化**：对长上下文场景，考虑 KV cache 也做量化（INT8 KV cache 几乎无损）

### 7.3 常见陷阱

- 不同量化工具的 4-bit 不完全等价——GPTQ 的 4-bit 和 GGUF 的 q4_0 精度差异明显
- 量化后的模型对 prompt 格式更敏感，确保使用正确的 chat template
- Jetson 上 llama.cpp 的 CUDA 后端需要手动编译，pip 安装的版本通常只有 CPU
- 3-bit 量化在数学推理和代码生成任务上退化严重，这些任务建议至少 4-bit

## 参考文献

1. Frantar, E. et al. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers." ICLR 2023.
2. Lin, J. et al. "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration." MLSys 2024.
3. Dettmers, T. et al. "QLoRA: Efficient Finetuning of Quantized Language Models." NeurIPS 2023.
4. Dettmers, T. et al. "The case for 4-bit precision: k-bit Inference Scaling Laws." ICML 2023.
5. Xiao, G. et al. "SmoothQuant: Accurate and Efficient Post-Training Quantization for LLMs." ICML 2023.
6. Gerganov, G. "llama.cpp: Inference of LLaMA model in pure C/C++." GitHub, 2023-2025.
7. Shao, W. et al. "OmniQuant: Omnidirectionally Calibrated Quantization for Large Language Models." ICLR 2024.
8. Liu, Z. et al. "KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache." ICML 2024.
9. Huang, W. et al. "BiLLM: Pushing the Limit of Post-Training Quantization for LLMs." ACL 2024.
10. NVIDIA. "TensorRT-LLM: A TensorRT Toolbox for Optimized LLM Inference." 2024.
