# 端侧 Diffusion Model 部署

> **难度**：🟡 中级 | **领域**：扩散模型、模型压缩、移动端推理 | **阅读时间**：约 21 分钟

## 日常类比

想象你有一块干净的白板，然后不断往上泼墨水——墨水越泼越多，白板变得面目全非。现在，如果我教你一个技能：看着一块被泼满墨水的板子，一步步擦除墨水，最终还原出一幅精美的画。这就是 **Diffusion Model（扩散模型）** 的核心思想。

"泼墨水"是**正向过程**（加噪）——简单可控；"擦墨水还原画作"是**反向过程**（去噪）——需要学习的复杂技能。模型学会了从纯噪声中逐步去噪生成图像这个技能后，就能创造出极其逼真的图像。

挑战在于：这个擦除过程需要很多步（通常 20-1000 步），每步都要跑一次完整的神经网络。在手机或 IoT 设备上，一次推理就需要几十秒。如何加速到实时可用，是端侧部署的核心问题。

## 1. 扩散模型基础

### 1.1 正向过程（加噪）

给原始图像逐步添加高斯噪声，经过 T 步后变成纯噪声：

```python
import torch
import numpy as np

class DiffusionSchedule:
    """扩散噪声调度器"""

    def __init__(self, T=1000, beta_start=1e-4, beta_end=0.02):
        self.T = T
        self.betas = torch.linspace(beta_start, beta_end, T)
        self.alphas = 1 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)

    def add_noise(self, x0, t, noise=None):
        """一步到位加噪到时间步 t"""
        if noise is None:
            noise = torch.randn_like(x0)
        alpha_bar_t = self.alpha_bars[t].view(-1, 1, 1, 1)
        x_t = torch.sqrt(alpha_bar_t) * x0 + torch.sqrt(1 - alpha_bar_t) * noise
        return x_t
```

关键性质：不需要逐步加噪，利用累积乘积可以从 x0 直接跳到任意时间步 t。

### 1.2 反向过程（去噪）

学习一个网络来预测每步添加的噪声：

```python
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.GroupNorm(8, out_ch),
            nn.SiLU(),
        )

    def forward(self, x):
        return self.net(x)


class SimpleUNet(nn.Module):
    """简化版 UNet 去噪网络"""

    def __init__(self, in_channels=3, base_channels=64, time_dim=256):
        super().__init__()
        self.time_mlp = nn.Sequential(
            nn.Linear(1, time_dim),
            nn.SiLU(),
            nn.Linear(time_dim, time_dim)
        )
        self.enc1 = ConvBlock(in_channels, base_channels)
        self.enc2 = ConvBlock(base_channels, base_channels * 2)
        self.enc3 = ConvBlock(base_channels * 2, base_channels * 4)
        self.bottleneck = ConvBlock(base_channels * 4, base_channels * 4)
        self.dec3 = ConvBlock(base_channels * 8, base_channels * 2)
        self.dec2 = ConvBlock(base_channels * 4, base_channels)
        self.dec1 = ConvBlock(base_channels * 2, base_channels)
        self.final = nn.Conv2d(base_channels, in_channels, 1)

    def forward(self, x, t):
        t_emb = self.time_mlp(t.float().unsqueeze(-1))
        e1 = self.enc1(x)
        e2 = self.enc2(nn.functional.avg_pool2d(e1, 2))
        e3 = self.enc3(nn.functional.avg_pool2d(e2, 2))
        b = self.bottleneck(nn.functional.avg_pool2d(e3, 2))
        d3 = self.dec3(torch.cat([nn.functional.interpolate(b, e3.shape[2:]), e3], 1))
        d2 = self.dec2(torch.cat([nn.functional.interpolate(d3, e2.shape[2:]), e2], 1))
        d1 = self.dec1(torch.cat([nn.functional.interpolate(d2, e1.shape[2:]), e1], 1))
        return self.final(d1)
```

### 1.3 训练目标

训练非常简单——预测噪声的 MSE 损失：

```python
def train_step(model, schedule, x0, optimizer):
    """一步训练"""
    batch_size = x0.shape[0]
    # 随机采样时间步
    t = torch.randint(0, schedule.T, (batch_size,))
    # 添加噪声
    noise = torch.randn_like(x0)
    x_t = schedule.add_noise(x0, t, noise)
    # 预测噪声
    noise_pred = model(x_t, t)
    # MSE 损失
    loss = nn.functional.mse_loss(noise_pred, noise)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    return loss.item()
```

## 2. DDPM / DDIM / LCM 采样方法

### 2.1 DDPM 采样（慢但质量高）

```python
@torch.no_grad()
def sample_ddpm(model, schedule, shape, device='cpu'):
    """DDPM 采样：需要 T 步（通常 1000 步）"""
    x = torch.randn(shape).to(device)

    for t in reversed(range(schedule.T)):
        t_batch = torch.full((shape[0],), t, device=device)
        noise_pred = model(x, t_batch)

        alpha = schedule.alphas[t]
        alpha_bar = schedule.alpha_bars[t]
        beta = schedule.betas[t]

        # 去噪公式
        mean = (1 / torch.sqrt(alpha)) * (
            x - (beta / torch.sqrt(1 - alpha_bar)) * noise_pred
        )

        if t > 0:
            noise = torch.randn_like(x)
            sigma = torch.sqrt(beta)
            x = mean + sigma * noise
        else:
            x = mean

    return x
```

### 2.2 DDIM 采样（快，可控步数）

DDIM 的关键创新：采样过程是确定性的，且可以跳步。

```python
@torch.no_grad()
def sample_ddim(model, schedule, shape, num_steps=50, eta=0.0, device='cpu'):
    """DDIM 采样：只需 20-50 步"""
    # 均匀选取 num_steps 个时间步
    step_indices = torch.linspace(0, schedule.T - 1, num_steps).long()

    x = torch.randn(shape).to(device)

    for i in reversed(range(len(step_indices))):
        t = step_indices[i]
        t_batch = torch.full((shape[0],), t, device=device)

        noise_pred = model(x, t_batch)
        alpha_bar_t = schedule.alpha_bars[t]

        # 预测 x0
        x0_pred = (x - torch.sqrt(1 - alpha_bar_t) * noise_pred) / torch.sqrt(alpha_bar_t)

        if i > 0:
            alpha_bar_prev = schedule.alpha_bars[step_indices[i - 1]]
            # DDIM 更新公式
            dir_xt = torch.sqrt(1 - alpha_bar_prev) * noise_pred
            x = torch.sqrt(alpha_bar_prev) * x0_pred + dir_xt
        else:
            x = x0_pred

    return x
```

### 2.3 LCM（Latent Consistency Model）

LCM 进一步将步数压缩到 1-4 步：

| 采样方法 | 所需步数 | 512x512 延迟(A100) | 质量(FID) | 适合端侧 |
|---------|---------|-------------------|-----------|---------|
| DDPM | 1000 | 45s | 最优 | 不可能 |
| DDIM | 50 | 2.3s | 接近最优 | 困难 |
| DDIM | 20 | 0.9s | 轻微下降 | 边缘可行 |
| DPM-Solver | 10 | 0.5s | 几乎无损 | 可行 |
| LCM | 4 | 0.2s | 可接受 | 推荐 |
| LCM | 1 | 0.05s | 明显下降 | 实时场景 |

```python
# LCM 的核心：一致性蒸馏
# 教师（多步 DDIM）指导学生（少步生成）
def lcm_distillation_loss(student, teacher, schedule, x0):
    """一致性蒸馏损失"""
    # 学生：1 步预测
    t_student = torch.randint(1, schedule.T, (x0.shape[0],))
    x_t = schedule.add_noise(x0, t_student)
    x0_student = student.predict_x0(x_t, t_student)

    # 教师：多步 DDIM（目标）
    with torch.no_grad():
        x0_teacher = teacher.multistep_predict(x_t, t_student, steps=4)

    # 一致性损失
    loss = nn.functional.mse_loss(x0_student, x0_teacher)
    return loss
```

## 3. 模型压缩技术

### 3.1 知识蒸馏

将大型扩散模型（如 SD 1.5 的 860M 参数 UNet）蒸馏为小模型：

```python
class DistillationTrainer:
    """扩散模型知识蒸馏"""

    def __init__(self, teacher, student, schedule):
        self.teacher = teacher  # 大模型，冻结
        self.student = student  # 小模型，训练
        self.schedule = schedule

    def distill_step(self, x0, optimizer):
        batch_size = x0.shape[0]
        t = torch.randint(0, self.schedule.T, (batch_size,))
        noise = torch.randn_like(x0)
        x_t = self.schedule.add_noise(x0, t, noise)

        # 教师的预测（不计算梯度）
        with torch.no_grad():
            teacher_pred = self.teacher(x_t, t)

        # 学生的预测
        student_pred = self.student(x_t, t)

        # 组合损失：噪声预测 + 教师匹配
        loss_noise = nn.functional.mse_loss(student_pred, noise)
        loss_distill = nn.functional.mse_loss(student_pred, teacher_pred)
        loss = 0.5 * loss_noise + 0.5 * loss_distill

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return loss.item()
```

### 3.2 量化

```python
# INT8 量化扩散模型
import torch.quantization as quant

def quantize_diffusion_model(model, calibration_data, schedule):
    """训练后量化（PTQ）"""
    model.eval()
    model.qconfig = quant.get_default_qconfig('fbgemm')

    # 准备量化
    model_prepared = quant.prepare(model)

    # 校准：用真实数据跑几个 batch
    with torch.no_grad():
        for x0 in calibration_data:
            t = torch.randint(0, schedule.T, (x0.shape[0],))
            x_t = schedule.add_noise(x0, t)
            model_prepared(x_t, t)

    # 转换为量化模型
    model_quantized = quant.convert(model_prepared)
    return model_quantized
```

### 3.3 结构化剪枝

| 压缩方法 | 压缩比 | FID 变化 | 推理加速 | 适用场景 |
|---------|--------|---------|---------|---------|
| INT8 量化 | 4x 大小 | +2-5 | 2-3x | 通用 |
| INT4 量化 | 8x 大小 | +5-15 | 3-5x | 质量可容忍 |
| 知识蒸馏 | 5-10x 参数 | +3-8 | 5-10x | 有教师模型 |
| 通道剪枝 50% | 2-3x | +5-10 | 2x | CNN backbone |
| Token 合并 | - | +2-4 | 1.5-2x | Transformer |

## 4. 移动端 Stable Diffusion

### 4.1 Snapdragon 上的部署

高通在 2023 年演示了在 Snapdragon 8 Gen 2 上运行 Stable Diffusion：

| 配置 | 推理时间 | 分辨率 | 步数 | 芯片 |
|------|---------|--------|------|------|
| SD 1.5 原版 | 15s | 512x512 | 20 | Snapdragon 8 Gen 2 |
| SD 1.5 优化版 | 8s | 512x512 | 20 | Snapdragon 8 Gen 3 |
| SD Turbo | 2s | 512x512 | 4 | Snapdragon 8 Gen 3 |
| SDXL Turbo | 5s | 1024x1024 | 4 | Snapdragon 8 Gen 3 |
| LCM-LoRA | 1.5s | 512x512 | 4 | Snapdragon 8 Gen 3 |

优化技术栈：
- Hexagon NPU 加速（INT8/FP16 混合精度）
- 模型分割：UNet 分块加载，避免峰值内存溢出
- 注意力优化：Flash Attention 的移动版本
- 缓存复用：相邻步之间共享中间特征

### 4.2 Apple Neural Engine 部署

```python
# 用 Core ML 部署到 Apple Neural Engine
import coremltools as ct

def convert_to_coreml(model, input_shape=(1, 4, 64, 64)):
    """将 PyTorch 扩散模型转换为 Core ML"""
    model.eval()
    example_input = torch.randn(input_shape)
    example_t = torch.tensor([500.0])

    traced = torch.jit.trace(model, (example_input, example_t))

    mlmodel = ct.convert(
        traced,
        inputs=[
            ct.TensorType(name="latent", shape=input_shape),
            ct.TensorType(name="timestep", shape=(1,))
        ],
        compute_units=ct.ComputeUnit.ALL,  # 使用 ANE + GPU + CPU
        minimum_deployment_target=ct.target.iOS16
    )

    # 量化为 float16
    mlmodel = ct.models.neural_network.quantization_utils.quantize_weights(
        mlmodel, nbits=16
    )
    mlmodel.save("diffusion_unet.mlpackage")
    return mlmodel
```

Apple 设备性能参考：

| 设备 | 芯片 | ANE 算力 | SD 512x512 20步 |
|------|------|---------|----------------|
| iPhone 15 Pro | A17 Pro | 35 TOPS | 6s |
| iPad Pro M4 | M4 | 38 TOPS | 4s |
| MacBook Air M3 | M3 | 18 TOPS | 8s |
| iPhone 14 | A15 | 15.8 TOPS | 12s |

## 5. 推理优化技巧

### 5.1 减少采样步数

```python
# DPM-Solver++: 高阶求解器，10 步达到 50 步 DDIM 的质量
class DPMSolverPP:
    def __init__(self, schedule, order=2):
        self.schedule = schedule
        self.order = order

    def sample(self, model, shape, num_steps=10):
        """DPM-Solver++ 采样"""
        timesteps = self.get_time_steps(num_steps)
        x = torch.randn(shape)
        model_outputs = []

        for i, t in enumerate(timesteps):
            noise_pred = model(x, t)
            model_outputs.append(noise_pred)

            if self.order == 2 and i >= 1:
                # 二阶更新：利用前两步的预测
                x = self.multistep_update(x, model_outputs[-2:], timesteps[i-1:i+1])
            else:
                # 一阶更新
                x = self.singlestep_update(x, noise_pred, t)

        return x
```

### 5.2 特征缓存 (DeepCache)

相邻去噪步骤之间，UNet 高层特征变化很小，可以缓存复用：

```python
class CachedUNet:
    """DeepCache: 缓存 UNet 中间层特征"""

    def __init__(self, unet, cache_interval=3):
        self.unet = unet
        self.cache_interval = cache_interval
        self.cached_features = None
        self.step_count = 0

    def forward(self, x, t):
        if self.step_count % self.cache_interval == 0:
            # 完整推理并缓存中间特征
            output, features = self.unet.forward_with_cache(x, t)
            self.cached_features = features
        else:
            # 只跑浅层，高层用缓存
            output = self.unet.forward_with_reuse(x, t, self.cached_features)

        self.step_count += 1
        return output

# 效果：推理加速 2-3x，FID 仅增加 1-2 点
```

### 5.3 Latent Diffusion 的优势

不在像素空间（512x512x3）做扩散，而在潜在空间（64x64x4）做——计算量减少 64 倍：

```
原始图像 512x512x3 → VAE 编码器 → 潜在表示 64x64x4
                                        ↓
                              扩散过程在潜在空间进行
                                        ↓
潜在表示 64x64x4 → VAE 解码器 → 生成图像 512x512x3
```

## 6. IoT 应用场景

### 6.1 图像增强/超分辨率

IoT 摄像头（如安防、农业监测）通常分辨率低、噪声大。用小型扩散模型做边缘超分辨率：

| 场景 | 输入 | 输出 | 模型大小 | 推理时间 |
|------|------|------|---------|---------|
| 安防摄像头增强 | 320x240 | 1280x960 | 15MB | 200ms (Jetson) |
| 农业病害检测 | 低光照模糊图 | 增强清晰图 | 8MB | 500ms (RPi4) |
| 文档扫描增强 | 手机拍照 | 去模糊去阴影 | 20MB | 100ms (手机) |

### 6.2 合成训练数据

当真实数据不足时，用扩散模型在边缘生成合成训练数据：

```python
# 在 Jetson Nano 上生成合成缺陷图像
def generate_defect_images(model, n_samples=100, defect_type="crack"):
    """为工业质检生成合成缺陷样本"""
    prompt_embedding = encode_text(f"industrial surface with {defect_type} defect")

    synthetic_images = []
    for i in range(0, n_samples, 4):  # 批量 4 张
        latent = torch.randn(4, 4, 32, 32)
        images = sample_lcm(model, latent, prompt_embedding, steps=4)
        synthetic_images.extend(images)

    return synthetic_images

# 用合成数据扩充后的检测效果:
# 真实数据 50 张: 检测准确率 72%
# 真实 50 + 合成 200: 检测准确率 89%
```

### 6.3 隐私保护的数据增强

敏感场景（医疗、人脸）中，用扩散模型生成不包含真实个体信息的合成数据：

```
真实医疗影像 → 训练扩散模型 → 生成合成影像 → 用于训练/分享
              (本地完成)        (不含真实患者信息)
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：理解 DDPM 原理，用 PyTorch 在 MNIST 上训练最简扩散模型
2. **第二步**：实现 DDIM 采样，对比 50 步 vs 1000 步的生成质量
3. **第三步**：使用 diffusers 库加载预训练 SD 模型，体验完整流程
4. **第四步**：用 ONNX + onnxruntime 在 CPU 上推理，测量基准延迟
5. **第五步**：应用 INT8 量化 + 减少步数，在树莓派或手机上运行

### 7.2 具体调优建议

**步数与质量的权衡**：
- 艺术创作（质量优先）：20-50 步 DDIM / DPM-Solver
- 实时应用（速度优先）：1-4 步 LCM / Turbo
- 超分辨率（确定性）：4-8 步 DPM-Solver++
- 数据增强（质量够用就好）：4 步 LCM

**内存优化策略**：
- 分块推理：将 UNet 按层加载，每次只计算一部分
- FP16 推理：几乎无精度损失，内存减半
- 注意力切片：将 attention 按 head 分批计算
- VAE 切片解码：大图分块解码避免 OOM

**选择合适的基座模型**：
- 通用图像生成：SD 1.5 / SDXL (压缩后)
- 超分辨率：Real-ESRGAN 或 StableSR
- 图像修复：SD Inpainting
- IoT 特定场景：自训练小型 diffusion (基于 DDPM)

**部署平台选择**：
- Jetson Orin (GPU)：可跑完整 SD，8-15s
- 树莓派 5：只能跑极小模型，分钟级
- 手机旗舰 (2024)：SD Turbo 2-6s
- 专用 NPU：取决于算子支持度

## 参考文献

1. Ho, J., et al. (2020). "Denoising Diffusion Probabilistic Models (DDPM)." *NeurIPS*.
2. Song, J., et al. (2021). "Denoising Diffusion Implicit Models (DDIM)." *ICLR*.
3. Luo, S., et al. (2023). "Latent Consistency Models: Synthesizing High-Resolution Images with Few-Step Inference." *arXiv:2310.04378*.
4. Rombach, R., et al. (2022). "High-Resolution Image Synthesis with Latent Diffusion Models." *CVPR*.
5. Li, Y., et al. (2024). "SnapFusion: Text-to-Image Diffusion Model on Mobile Devices within Two Seconds." *NeurIPS*.
6. Ma, X., et al. (2024). "DeepCache: Accelerating Diffusion Models for Free." *CVPR*.
7. Lu, C., et al. (2022). "DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling." *NeurIPS*.
8. Castells, T., et al. (2024). "EdgeFusion: On-Device Text-to-Image Generation." *MobiSys*.
9. Shang, Y., et al. (2023). "Post-training Quantization on Diffusion Models." *CVPR*.
10. Chen, Y., et al. (2024). "Speed Is All You Need: On-Device Acceleration of Large Diffusion Models via GPU-Aware Optimizations." *CVPR Workshop*.
