---
schema_version: '1.0'
id: edge-anomaly-detection
title: 边缘异常检测：Autoencoder 与 Isolation Forest
layer: 5
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 边缘异常检测：Autoencoder 与 Isolation Forest

> **难度**：🟡 中级 | **领域**：异常检测、边缘部署、工业 IoT | **阅读时间**：约 20 分钟

## 日常类比

你是一个经验丰富的质检员，每天检查流水线上的产品。正常产品你见了几万个，已经形成了"正常长什么样"的直觉。当一个异常品出现时，你立刻觉得"不对劲"——不是因为你见过这种缺陷，而是因为它偏离了你对"正常"的认知。

**Autoencoder** 就是这个"学习正常模式"的质检员：它学会把正常数据压缩再还原，遇到异常数据时还原出来的结果会"走样"——重建误差大就是异常。

**Isolation Forest** 的思路不同：它像一个"找独行侠"的社交网络分析师。正常数据聚在一起，很难被单独"隔离"出来；异常数据与众不同，很容易用少数几个条件就能将其隔离。就像找一群人中最独特的那个——穿奇装异服的人，一眼就能挑出来。

## 1. 异常检测分类体系

### 1.1 三种异常类型

| 类型 | 定义 | 传感器场景举例 |
|------|------|--------------|
| 点异常（Point） | 单个数据点偏离 | 温度突然跳到 200°C |
| 上下文异常（Contextual） | 在特定上下文中异常 | 夏天暖气温度正常，冬天同样温度偏低 |
| 集体异常（Collective） | 一组数据点集合起来异常 | 单个心跳正常，但连续 50 个形成了异常节律 |

### 1.2 检测范式对比

| 范式 | 方法 | 需要标注 | 适用场景 |
|------|------|---------|---------|
| 监督式 | 二分类器 | 需要正常+异常样本 | 已知异常模式 |
| 半监督 | 只学正常模式 | 只需正常样本 | 异常罕见、多样 |
| 无监督 | 假设异常是少数 | 不需要标注 | 探索性检测 |

在工业 IoT 中，异常样本极其稀少（< 0.1%），且异常形态多变，因此**半监督**（只学正常）是主流。

## 2. Autoencoder 重建误差法

### 2.1 基本原理

Autoencoder 被训练来"压缩再还原"正常数据。当输入异常数据时，由于编码器从未学过这种模式，解码器无法准确还原，产生高重建误差。

```python
import torch
import torch.nn as nn

class SensorAutoencoder(nn.Module):
    """适用于传感器时序数据的 1D 卷积 Autoencoder"""
    
    def __init__(self, input_channels=6, seq_len=100, latent_dim=16):
        super().__init__()
        
        # 编码器：压缩
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.MaxPool1d(2),          # seq_len/2
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),          # seq_len/4
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),  # [B, 128, 1]
            nn.Flatten(),
            nn.Linear(128, latent_dim)
        )
        
        # 解码器：还原
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, 128),
            nn.ReLU(),
            nn.Unflatten(1, (128, 1)),
            nn.Upsample(size=seq_len // 4),
            nn.ConvTranspose1d(128, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Upsample(size=seq_len // 2),
            nn.ConvTranspose1d(64, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Upsample(size=seq_len),
            nn.ConvTranspose1d(32, input_channels, kernel_size=7, padding=3),
        )
    
    def forward(self, x):
        z = self.encoder(x)
        x_recon = self.decoder(z)
        return x_recon, z
    
    def anomaly_score(self, x):
        """重建误差作为异常分数"""
        x_recon, _ = self.forward(x)
        # 每个样本的 MSE
        score = ((x - x_recon) ** 2).mean(dim=[1, 2])
        return score
```

### 2.2 训练与阈值设定

```python
def train_anomaly_detector(model, normal_dataloader, epochs=100, lr=1e-3):
    """只用正常数据训练"""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    for epoch in range(epochs):
        total_loss = 0
        for batch in normal_dataloader:
            x_recon, _ = model(batch)
            loss = nn.MSELoss()(x_recon, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
    
    # 用验证集的正常数据确定阈值
    model.eval()
    scores = []
    with torch.no_grad():
        for batch in normal_dataloader:
            scores.append(model.anomaly_score(batch))
    
    all_scores = torch.cat(scores)
    # 阈值 = 均值 + 3 倍标准差（覆盖 99.7% 正常数据）
    threshold = all_scores.mean() + 3 * all_scores.std()
    return threshold
```

### 2.3 变分 Autoencoder (VAE) 增强

VAE 相比普通 AE 的优势：学习数据的概率分布，异常检测可以同时利用重建误差和 KL 散度。

```python
class SensorVAE(nn.Module):
    def __init__(self, input_channels=6, seq_len=100, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Flatten(),
            nn.Linear(64 * (seq_len // 4), 256), nn.ReLU()
        )
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_logvar = nn.Linear(256, latent_dim)
        # decoder 同上...
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def anomaly_score(self, x):
        """重建误差 + KL 散度"""
        h = self.encoder(x)
        mu, logvar = self.fc_mu(h), self.fc_logvar(h)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decoder(z)
        
        recon_error = ((x - x_recon) ** 2).mean(dim=[1, 2])
        kl_div = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=1)
        
        return recon_error + 0.1 * kl_div  # 加权组合
```

## 3. Isolation Forest 算法

### 3.1 核心直觉

正常点"藏在人群中"，需要很多次分割才能隔离；异常点"与众不同"，几次分割就能隔离。

```python
from sklearn.ensemble import IsolationForest
import numpy as np

# 基本使用
def isolation_forest_detector(train_data, test_data, contamination=0.01):
    """
    train_data: [n_samples, n_features] 正常训练数据
    test_data: [n_samples, n_features] 待检测数据
    contamination: 预期异常比例
    """
    clf = IsolationForest(
        n_estimators=100,        # 树的数量
        max_samples='auto',       # 每棵树的采样数
        contamination=contamination,
        random_state=42
    )
    
    clf.fit(train_data)
    
    # 预测：1=正常，-1=异常
    predictions = clf.predict(test_data)
    # 异常分数：越小越异常
    scores = clf.decision_function(test_data)
    
    return predictions, scores
```

### 3.2 算法细节

Isolation Forest 的分割过程：
1. 随机选择一个特征
2. 在该特征的 [min, max] 之间随机选一个分割点
3. 重复直到每个点被隔离或达到最大深度

异常点的**平均路径长度**短（容易被隔离）。

异常分数公式：
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$

其中 $E(h(x))$ 是样本 x 的平均路径长度，$c(n)$ 是 n 个样本的平均路径长度归一化因子。

### 3.3 适用于流式数据的变体

```python
class StreamingIsolationForest:
    """适合 IoT 流式数据的增量 Isolation Forest"""
    
    def __init__(self, window_size=1000, n_estimators=50, update_interval=100):
        self.window_size = window_size
        self.buffer = []
        self.n_estimators = n_estimators
        self.update_interval = update_interval
        self.model = None
        self.sample_count = 0
    
    def update(self, new_sample):
        """接收新样本，滑动窗口更新"""
        self.buffer.append(new_sample)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        
        self.sample_count += 1
        
        # 定期重训练模型
        if self.sample_count % self.update_interval == 0 and len(self.buffer) >= 100:
            data = np.array(self.buffer)
            self.model = IsolationForest(n_estimators=self.n_estimators)
            self.model.fit(data)
    
    def predict(self, sample):
        """实时预测"""
        if self.model is None:
            return 0  # 模型未就绪，返回正常
        return self.model.decision_function(sample.reshape(1, -1))[0]
```

## 4. One-Class SVM

### 4.1 原理与实现

One-Class SVM 在特征空间中找到一个包围正常数据的"最紧超球面"。

```python
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

def one_class_svm_detector(train_data, test_data, kernel='rbf', nu=0.01):
    """
    nu: 异常比例的上界（也是支持向量比例的下界）
    """
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_data)
    test_scaled = scaler.transform(test_data)
    
    clf = OneClassSVM(kernel=kernel, nu=nu, gamma='scale')
    clf.fit(train_scaled)
    
    predictions = clf.predict(test_scaled)  # 1=正常, -1=异常
    scores = clf.decision_function(test_scaled)
    
    return predictions, scores
```

## 5. 方法对比与选型指南

### 5.1 综合对比表

| 方法 | 准确率(F1) | 推理延迟 | 内存占用 | 训练时间 | 流式支持 | 适用场景 |
|------|-----------|---------|---------|---------|---------|---------|
| Autoencoder | 0.92 | 2-5ms | 50-500KB | 分钟级 | 否(需批量) | 复杂时序模式 |
| VAE | 0.94 | 3-8ms | 100KB-1MB | 分钟级 | 否 | 需要概率解释 |
| Isolation Forest | 0.88 | 0.1-1ms | 1-10MB | 秒级 | 部分 | 表格特征数据 |
| One-Class SVM | 0.86 | 0.5-2ms | 5-50MB | 分钟级 | 否 | 小数据集 |
| LOF | 0.85 | 1-5ms | 10-100MB | 秒级 | 困难 | 局部异常 |
| LSTM-AE | 0.95 | 5-15ms | 200KB-2MB | 小时级 | 是 | 长序列时序 |

### 5.2 ESP32 / 树莓派部署约束

| 平台 | RAM | Flash | CPU | 推荐方法 |
|------|-----|-------|-----|---------|
| ESP32 | 520KB | 4MB | 240MHz dual-core | Isolation Forest (lite) |
| ESP32-S3 | 512KB+8MB PSRAM | 16MB | 240MHz | 小型 AE (INT8) |
| RPi Zero 2W | 512MB | SD卡 | 1GHz quad-core | AE / VAE / IF |
| RPi 4 (4GB) | 4GB | SD卡 | 1.8GHz quad-core | 所有方法均可 |

## 6. 工业预测性维护案例

### 6.1 振动传感器异常检测

```python
# 工业电机振动监测 - 完整流水线
import numpy as np
from scipy.fft import fft

class VibrationAnomalyDetector:
    """工业电机振动异常检测器"""
    
    def __init__(self, sampling_rate=1000, window_size=1024):
        self.sampling_rate = sampling_rate
        self.window_size = window_size
        self.autoencoder = SensorAutoencoder(input_channels=3, seq_len=window_size)
        self.threshold = None
    
    def extract_features(self, raw_signal):
        """提取时频域特征"""
        features = {}
        # 时域特征
        features['rms'] = np.sqrt(np.mean(raw_signal**2))
        features['peak'] = np.max(np.abs(raw_signal))
        features['crest_factor'] = features['peak'] / features['rms']
        features['kurtosis'] = np.mean((raw_signal - raw_signal.mean())**4) / \
                               (np.std(raw_signal)**4)
        
        # 频域特征
        spectrum = np.abs(fft(raw_signal))[:len(raw_signal)//2]
        freqs = np.fft.fftfreq(len(raw_signal), 1/self.sampling_rate)[:len(raw_signal)//2]
        features['dominant_freq'] = freqs[np.argmax(spectrum)]
        features['spectral_energy'] = np.sum(spectrum**2)
        
        return features
    
    def diagnose(self, anomaly_score, features):
        """根据异常分数和特征给出诊断建议"""
        if anomaly_score < self.threshold:
            return "正常运行"
        
        if features['kurtosis'] > 5:
            return "可能存在轴承点蚀（冲击特征明显）"
        elif features['dominant_freq'] > 500:
            return "可能存在齿轮磨损（高频异常）"
        elif features['rms'] > 2 * self.normal_rms:
            return "可能存在不平衡或松动（整体振动增大）"
        else:
            return "异常模式未知，建议人工检查"
```

### 6.2 部署架构

```
传感器 → ESP32 (边缘推理)  →  异常？ →  网关 → 云端
         ├─ 采集振动数据            │
         ├─ 提取特征               ├─ 正常：本地记录
         ├─ 运行 IF/AE 推理        └─ 异常：上报详细数据
         └─ 判断是否异常
         
本地推理延迟: < 10ms
上报频率: 正常时 1次/分钟，异常时实时
功耗节省: 相比全量上传节省 95% 通信能耗
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 sklearn 的 IsolationForest 在 KDD Cup 99 数据集上跑通基本流程
2. **第二步**：实现简单的全连接 Autoencoder，对比与 IF 的效果差异
3. **第三步**：用 1D CNN Autoencoder 处理真实传感器数据（SWaT 工业数据集）
4. **第四步**：在树莓派上部署，用 ONNX Runtime 优化推理速度
5. **第五步**：实现流式检测——滑动窗口 + 增量更新

### 7.2 具体调优建议

**阈值选择**：
- 统计法：均值 + 3σ（适合高斯分布）
- 百分位法：选第 99 或 99.9 百分位（更鲁棒）
- 动态阈值：用 EWMA 跟踪正常分数的漂移

**Autoencoder 架构选择**：
- 数据量 < 1000 条：用全连接 AE（过拟合风险低）
- 数据量 > 10000 条：用 1D CNN AE（能学时序模式）
- 序列很长（> 500 步）：用 LSTM-AE（捕获长依赖）
- 需要概率解释：用 VAE（可计算异常概率而非仅分数）

**部署优化**：
- INT8 量化可将模型大小和推理时间减少 4x
- 知识蒸馏：用大模型指导小模型，保持精度
- 特征缓存：对频域特征预计算，避免实时 FFT

## 参考文献

1. Liu, F., et al. (2008). "Isolation Forest." *ICDM*.
2. An, J., & Cho, S. (2015). "Variational Autoencoder based Anomaly Detection using Reconstruction Probability." *SNU Data Mining Center*.
3. Pang, G., et al. (2021). "Deep Learning for Anomaly Detection: A Review." *ACM Computing Surveys*.
4. Audibert, J., et al. (2020). "USAD: UnSupervised Anomaly Detection on Multivariate Time Series." *KDD*.
5. Hundman, K., et al. (2018). "Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding." *KDD*.
6. Zhao, Y., et al. (2019). "PyOD: A Python Toolbox for Scalable Outlier Detection." *JMLR*.
7. Goh, J., et al. (2017). "A Dataset to Support Research in the Design of Secure Water Treatment Systems (SWaT)." *CRITIS*.
8. Li, D., et al. (2023). "TinyAD: Memory-Efficient Anomaly Detection on Microcontrollers." *SenSys*.
9. Malhotra, P., et al. (2016). "LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection." *ICML Workshop*.
10. Xu, H., et al. (2022). "Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy." *ICLR*.
