# 边缘生成对抗网络

> **难度**：🟡 中级 | **领域**：生成模型、边缘计算、数据增强 | **阅读时间**：约 19 分钟

## 日常类比

想象一个造假高手和一个鉴定专家的博弈。造假高手（生成器）不断提升伪造水平，鉴定专家（判别器）也不断提升鉴别能力。双方持续对抗的结果是：造假高手最终能造出以假乱真的作品。这就是 **GAN（生成对抗网络）**的核心思想。

在 IoT 场景中，传感器数据往往"阳性样本"极少——一台运行了 3 年的电机可能只出过 2 次故障。用 GAN 生成"逼真的故障数据"来补充训练集，就像让一个经验丰富的工程师凭想象力描述"可能发生的故障场景"。

但 GAN 的训练需要大量计算资源，如何在边缘设备上部署轻量化的 GAN，是本文要解决的核心问题。

## 1. GAN 基本原理

### 1.1 对抗训练框架

```
随机噪声 z ~ N(0,1) → 生成器 G(z) → 生成样本 x_fake
                                           ↓
                         判别器 D → D(x_fake) → "假的"概率
真实数据 x_real →                  → D(x_real) → "真的"概率
```

目标函数（Min-Max Game）：
$$\min_G \max_D \; \mathbb{E}_{x \sim p_{data}}[\log D(x)] + \mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]$$

### 1.2 基本实现

```python
import torch
import torch.nn as nn

class Generator(nn.Module):
    """传感器数据生成器"""
    def __init__(self, noise_dim=100, output_channels=6, seq_len=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(noise_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, output_channels * seq_len),
            nn.Tanh()
        )
        self.output_channels = output_channels
        self.seq_len = seq_len
    
    def forward(self, z):
        out = self.net(z)
        return out.view(-1, self.output_channels, self.seq_len)

class Discriminator(nn.Module):
    """传感器数据判别器"""
    def __init__(self, input_channels=6, seq_len=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=5, stride=2, padding=2),
            nn.LeakyReLU(0.2),
            nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.2),
            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.2),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        return self.net(x)

# 训练循环
def train_gan(G, D, dataloader, epochs=200, lr=2e-4):
    opt_G = torch.optim.Adam(G.parameters(), lr=lr, betas=(0.5, 0.999))
    opt_D = torch.optim.Adam(D.parameters(), lr=lr, betas=(0.5, 0.999))
    criterion = nn.BCELoss()
    
    for epoch in range(epochs):
        for real_data in dataloader:
            batch_size = real_data.size(0)
            real_labels = torch.ones(batch_size, 1)
            fake_labels = torch.zeros(batch_size, 1)
            
            # 训练判别器
            z = torch.randn(batch_size, 100)
            fake_data = G(z).detach()
            d_real = D(real_data)
            d_fake = D(fake_data)
            loss_D = criterion(d_real, real_labels) + criterion(d_fake, fake_labels)
            opt_D.zero_grad()
            loss_D.backward()
            opt_D.step()
            
            # 训练生成器
            z = torch.randn(batch_size, 100)
            fake_data = G(z)
            d_fake = D(fake_data)
            loss_G = criterion(d_fake, real_labels)  # 让判别器认为是真的
            opt_G.zero_grad()
            loss_G.backward()
            opt_G.step()
```

## 2. 轻量化 GAN 架构

### 2.1 MobileStyleGAN

将 StyleGAN 的风格映射与 MobileNet 的深度可分离卷积结合：

```python
class DepthwiseSeparableConv1d(nn.Module):
    """深度可分离卷积：参数量减少 k 倍（k=kernel_size）"""
    def __init__(self, in_ch, out_ch, kernel_size=5, stride=1, padding=2):
        super().__init__()
        self.depthwise = nn.Conv1d(in_ch, in_ch, kernel_size, stride, padding, groups=in_ch)
        self.pointwise = nn.Conv1d(in_ch, out_ch, 1)
    
    def forward(self, x):
        return self.pointwise(self.depthwise(x))

class LightweightGenerator(nn.Module):
    """适用于边缘设备的轻量生成器"""
    def __init__(self, noise_dim=50, output_channels=6, seq_len=128):
        super().__init__()
        self.init_size = seq_len // 8
        self.fc = nn.Linear(noise_dim, 128 * self.init_size)
        
        self.net = nn.Sequential(
            nn.Upsample(scale_factor=2),
            DepthwiseSeparableConv1d(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Upsample(scale_factor=2),
            DepthwiseSeparableConv1d(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Upsample(scale_factor=2),
            DepthwiseSeparableConv1d(32, output_channels),
            nn.Tanh()
        )
    
    def forward(self, z):
        x = self.fc(z).view(-1, 128, self.init_size)
        return self.net(x)
```

### 2.2 参数量对比

| 模型 | 参数量 | FLOPs | 生成质量(FID↓) | 适用平台 |
|------|--------|-------|---------------|---------|
| 标准 GAN | 2.1M | 85M | 42.3 | GPU 服务器 |
| DCGAN | 3.5M | 120M | 35.6 | GPU/Jetson |
| LightweightGAN | 450K | 18M | 48.7 | RPi 4 |
| MobileGAN | 280K | 9M | 55.2 | ESP32-S3 |
| TinyGAN (蒸馏) | 150K | 5M | 52.1 | MCU |

### 2.3 条件 GAN (CGAN) 用于定向生成

```python
class ConditionalGenerator(nn.Module):
    """条件 GAN：生成特定类别的传感器数据"""
    
    def __init__(self, noise_dim=100, n_classes=5, output_channels=6, seq_len=128):
        super().__init__()
        self.label_embed = nn.Embedding(n_classes, 50)
        
        self.net = nn.Sequential(
            nn.Linear(noise_dim + 50, 256),  # 噪声 + 类别条件
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Linear(256, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Linear(512, output_channels * seq_len),
            nn.Tanh()
        )
        self.output_channels = output_channels
        self.seq_len = seq_len
    
    def forward(self, z, labels):
        label_emb = self.label_embed(labels)
        x = torch.cat([z, label_emb], dim=1)
        out = self.net(x)
        return out.view(-1, self.output_channels, self.seq_len)

# 使用：生成"轴承故障"类型的振动数据
z = torch.randn(16, 100)
labels = torch.full((16,), fill_value=3)  # 类别 3 = 轴承故障
fake_fault_data = cgan_generator(z, labels)
```

## 3. IoT 数据增强应用

### 3.1 解决类别不平衡

工业 IoT 典型数据分布：

| 类别 | 样本数 | 占比 |
|------|--------|------|
| 正常运行 | 98,500 | 98.5% |
| 轻微异常 | 1,200 | 1.2% |
| 严重故障 | 280 | 0.28% |
| 临界失效 | 20 | 0.02% |

用 CGAN 将少数类扩充到与多数类平衡：

```python
def augment_minority_class(generator, target_count, class_label, noise_dim=100):
    """用 GAN 生成少数类样本"""
    generator.eval()
    generated_samples = []
    
    with torch.no_grad():
        while len(generated_samples) < target_count:
            batch_size = min(64, target_count - len(generated_samples))
            z = torch.randn(batch_size, noise_dim)
            labels = torch.full((batch_size,), class_label)
            fake_samples = generator(z, labels)
            generated_samples.append(fake_samples)
    
    return torch.cat(generated_samples)[:target_count]

# 扩充后的效果对比（故障分类准确率）
# | 方法          | 准确率  | 召回率(故障类) |
# |--------------|---------|--------------|
# | 原始数据      | 89.2%   | 43.5%        |
# | SMOTE        | 91.5%   | 62.3%        |
# | GAN 增强     | 93.8%   | 78.6%        |
# | CGAN 增强    | 94.5%   | 82.1%        |
```

### 3.2 合成传感器数据质量验证

```python
from scipy.stats import wasserstein_distance
import numpy as np

def evaluate_synthetic_quality(real_data, fake_data):
    """评估合成数据质量"""
    metrics = {}
    
    # 1. 统计分布匹配
    for ch in range(real_data.shape[1]):
        metrics[f'wasserstein_ch{ch}'] = wasserstein_distance(
            real_data[:, ch].flatten(),
            fake_data[:, ch].flatten()
        )
    
    # 2. 自相关匹配（时序特性）
    def autocorrelation(x, lag=10):
        return np.corrcoef(x[:-lag], x[lag:])[0, 1]
    
    real_autocorr = np.mean([autocorrelation(real_data[i, 0]) for i in range(len(real_data))])
    fake_autocorr = np.mean([autocorrelation(fake_data[i, 0]) for i in range(len(fake_data))])
    metrics['autocorr_diff'] = abs(real_autocorr - fake_autocorr)
    
    # 3. 频谱匹配
    real_spectrum = np.abs(np.fft.fft(real_data[:, 0], axis=1)).mean(axis=0)
    fake_spectrum = np.abs(np.fft.fft(fake_data[:, 0], axis=1)).mean(axis=0)
    metrics['spectral_mse'] = np.mean((real_spectrum - fake_spectrum)**2)
    
    return metrics
```

## 4. GAN 用于异常检测

### 4.1 AnoGAN 思路

训练 GAN 只学习正常数据的分布。推理时，对每个新样本找到其在潜在空间的最优投影。如果找不到好的投影（重建误差大），说明这个样本不在正常分布内——即异常。

```python
class AnoGAN:
    """基于 GAN 的异常检测"""
    
    def __init__(self, generator, discriminator, noise_dim=100, lambda_recon=0.9):
        self.G = generator
        self.D = discriminator
        self.noise_dim = noise_dim
        self.lambda_recon = lambda_recon
    
    def anomaly_score(self, x, n_iterations=500, lr=0.01):
        """计算样本 x 的异常分数"""
        # 优化潜在向量 z，使 G(z) 尽量接近 x
        z = torch.randn(1, self.noise_dim, requires_grad=True)
        optimizer = torch.optim.Adam([z], lr=lr)
        
        for _ in range(n_iterations):
            fake = self.G(z)
            
            # 重建损失
            recon_loss = torch.mean((fake - x) ** 2)
            
            # 判别器特征匹配损失
            real_feat = self.D.extract_features(x)
            fake_feat = self.D.extract_features(fake)
            feat_loss = torch.mean((real_feat - fake_feat) ** 2)
            
            # 总损失
            loss = self.lambda_recon * recon_loss + (1 - self.lambda_recon) * feat_loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        return loss.item()
```

## 5. 隐私保护数据共享

### 5.1 差分隐私 GAN (DP-GAN)

多个 IoT 设备可以共享 GAN 生成的合成数据，而非原始数据，从而保护隐私。

```python
# 差分隐私 SGD 训练判别器
def dp_train_discriminator(D, real_data, fake_data, 
                           max_grad_norm=1.0, noise_multiplier=1.1):
    """
    使用差分隐私训练判别器
    - 梯度裁剪：限制单样本的影响
    - 噪声注入：添加高斯噪声
    """
    D.zero_grad()
    
    # 逐样本计算梯度（per-sample gradient）
    per_sample_grads = []
    for i in range(len(real_data)):
        loss_i = criterion(D(real_data[i:i+1]), torch.ones(1, 1))
        loss_i.backward(retain_graph=True)
        
        # 裁剪单样本梯度
        grad_i = [p.grad.clone() for p in D.parameters()]
        grad_norm = torch.sqrt(sum(g.norm()**2 for g in grad_i))
        clip_factor = min(1.0, max_grad_norm / (grad_norm + 1e-6))
        clipped_grad = [g * clip_factor for g in grad_i]
        per_sample_grads.append(clipped_grad)
        D.zero_grad()
    
    # 聚合并添加噪声
    batch_size = len(real_data)
    for i, p in enumerate(D.parameters()):
        avg_grad = sum(g[i] for g in per_sample_grads) / batch_size
        noise = torch.randn_like(avg_grad) * max_grad_norm * noise_multiplier / batch_size
        p.grad = avg_grad + noise
    
    optimizer_D.step()
```

### 5.2 联邦 GAN

```
设备 A: 训练本地 GAN → 上传生成器权重（不上传数据）
设备 B: 训练本地 GAN → 上传生成器权重
设备 C: 训练本地 GAN → 上传生成器权重
                    ↓
        服务器聚合生成器权重 → 全局 GAN
                    ↓
        生成合成数据用于集中训练
```

## 6. 训练挑战与解决方案

### 6.1 边缘设备上的训练难题

| 挑战 | 原因 | 解决方案 |
|------|------|---------|
| 模式坍塌 | 生成器只产出单一模式 | Wasserstein Loss / 谱归一化 |
| 训练不稳定 | G 和 D 失衡 | 学习率比例调整 / TTUR |
| 内存不足 | 完整模型放不下 | 渐进式训练 / 低精度 |
| 训练太慢 | 边缘 CPU 算力不足 | 知识蒸馏 / 预训练迁移 |

### 6.2 Wasserstein GAN 稳定训练

```python
def wasserstein_loss_D(D, real_data, fake_data, lambda_gp=10):
    """WGAN-GP 判别器损失：更稳定的训练"""
    d_real = D(real_data).mean()
    d_fake = D(fake_data).mean()
    
    # 梯度惩罚
    alpha = torch.rand(real_data.size(0), 1, 1).to(real_data.device)
    interpolated = alpha * real_data + (1 - alpha) * fake_data
    interpolated.requires_grad_(True)
    d_interp = D(interpolated)
    
    gradients = torch.autograd.grad(
        outputs=d_interp, inputs=interpolated,
        grad_outputs=torch.ones_like(d_interp),
        create_graph=True
    )[0]
    grad_penalty = ((gradients.norm(2, dim=(1,2)) - 1) ** 2).mean()
    
    loss = d_fake - d_real + lambda_gp * grad_penalty
    return loss
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 PyTorch 实现最简 GAN 生成 1D 正弦波
2. **第二步**：升级为 DCGAN（1D 卷积版），生成加速度计数据
3. **第三步**：加入条件（CGAN），控制生成特定活动类型
4. **第四步**：用 FID/IS 评估生成质量
5. **第五步**：将训练好的生成器量化后部署到树莓派

### 7.2 具体调优建议

**训练稳定性**：
- 使用 WGAN-GP 而非原始 GAN loss
- 判别器训练 5 次，生成器训练 1 次（TTUR）
- 学习率：G 用 1e-4，D 用 4e-4
- 使用谱归一化（Spectral Normalization）
- Batch size 尽量大（>= 32）

**生成质量评估**：
- FID (Frechet Inception Distance)：越低越好，< 50 为可接受
- IS (Inception Score)：越高越好
- 时序数据专用：DTW 距离、自相关匹配、频谱匹配
- 下游任务验证：用合成数据训练分类器，在真实数据上测试

**边缘部署策略**：
- 只部署生成器（判别器训练后丢弃）
- INT8 量化生成器（精度损失 < 5%）
- 批量生成后缓存，而非实时生成
- 对生成数据做后处理（物理约束裁剪、平滑）

## 参考文献

1. Goodfellow, I., et al. (2014). "Generative Adversarial Nets." *NeurIPS*.
2. Arjovsky, M., et al. (2017). "Wasserstein GAN." *ICML*.
3. Li, C., et al. (2022). "TinyGAN: Distilling BigGAN for Conditional Image Generation." *ICLR*.
4. Esteban, C., et al. (2017). "Real-valued (Medical) Time Series Generation with Recurrent Conditional GANs." *NIPS Workshop*.
5. Yoon, J., et al. (2019). "Time-series Generative Adversarial Networks (TimeGAN)." *NeurIPS*.
6. Zhang, C., et al. (2021). "Data Augmentation for IoT Sensor Data Using GANs." *IEEE IoT Journal*.
7. Xie, L., et al. (2020). "Differentially Private Generative Adversarial Network." *arXiv:1802.06739*.
8. Schlegl, T., et al. (2017). "Unsupervised Anomaly Detection with GANs (AnoGAN)." *IPMI*.
9. Lin, Z., et al. (2020). "Using GANs for Sharing Networked Time Series Data." *IMC*.
10. Lee, D., et al. (2024). "Lightweight GAN for Edge Intelligence: A Survey." *IEEE Communications Surveys*.
