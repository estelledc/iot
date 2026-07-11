---
schema_version: '1.0'
id: edge-anomaly-detection
title: 边缘异常检测：Autoencoder 与 Isolation Forest
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - model-compression-edge
tags:
  - 异常检测
  - Autoencoder
  - Isolation Forest
  - TinyML
  - 预测性维护
  - 边缘推理
  - 半监督
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 边缘异常检测：Autoencoder 与 Isolation Forest

> **难度**：🟡 中级 | **领域**：异常检测、边缘部署、工业物联网 | **阅读时间**：约 22 分钟

## 日常类比

你是流水线质检员：正常品见过几万个，异常品一出现就觉得"不对劲"——不是因为见过这种缺陷，而是它偏离了"正常"的直觉。

**自编码器（Autoencoder, AE）** 像这位质检员：只学正常数据的压缩与还原，异常输入重建误差大。

**孤立森林（Isolation Forest, IF）** 像找人群里的独行侠：正常点难隔离，异常点用少数分割就能切开[1]。

## 摘要

工业物联网（Internet of Things, IoT）异常样本稀少且形态多变，半监督（只学正常）是主流范式[3]。本文对比 AE / 变分自编码器（Variational Autoencoder, VAE）、IF、单类支持向量机（One-Class Support Vector Machine, OC-SVM），给出边缘平台选型、振动监测骨架与阈值策略，并讨论局限与改进。文中代码为教学骨架，非生产完备实现。

## 1. 异常检测分类体系

### 1.1 三种异常类型

| 类型 | 定义 | 传感器场景举例 |
|------|------|--------------|
| 点异常（Point） | 单个数据点偏离 | 温度突然跳到异常高温 |
| 上下文异常（Contextual） | 在特定上下文中异常 | 同读数在夏季正常、冬季偏低 |
| 集体异常（Collective） | 一组点合起来异常 | 单拍心跳正常，连续节律异常 |

### 1.2 检测范式对比

| 范式 | 方法 | 需要标注 | 适用场景 |
|------|------|---------|---------|
| 监督式 | 二分类器 | 正常+异常样本 | 已知异常模式 |
| 半监督 | 只学正常模式 | 只需正常样本 | 异常罕见、多样 |
| 无监督 | 假设异常是少数 | 不需要标注 | 探索性检测 |

工业现场异常往往远少于正常样本，且新故障形态不断出现，因此半监督更常见[3][7]。

## 2. Autoencoder 重建误差法

### 2.1 基本原理

AE 被训练来压缩再还原正常数据；异常输入因未见过，重建误差升高[2][9]。

```python
import torch
import torch.nn as nn

class SensorAutoencoder(nn.Module):
    """适用于传感器时序数据的 1D 卷积 Autoencoder（教学骨架）"""

    def __init__(self, input_channels=6, seq_len=100, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool1d(2),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Linear(128, latent_dim),
        )
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
        return self.decoder(z), z

    def anomaly_score(self, x):
        x_recon, _ = self.forward(x)
        return ((x - x_recon) ** 2).mean(dim=[1, 2])
```

### 2.2 训练与阈值设定

```python
def train_anomaly_detector(model, normal_dataloader, epochs=100, lr=1e-3):
    """只用正常数据训练；阈值用验证集正常分数估计"""
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(epochs):
        for batch in normal_dataloader:
            x_recon, _ = model(batch)
            loss = nn.MSELoss()(x_recon, batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    scores = []
    with torch.no_grad():
        for batch in normal_dataloader:
            scores.append(model.anomaly_score(batch))
    all_scores = torch.cat(scores)
    # 均值+3σ 仅当分数近似高斯时合理；否则优先百分位
    threshold = all_scores.mean() + 3 * all_scores.std()
    return threshold
```

航天等时序场景常用非参数动态阈值，比固定 3σ 更稳[5]。

### 2.3 变分 Autoencoder (VAE) 增强

VAE 学习潜在分布，异常分数可组合重建误差与 KL 散度（Kullback–Leibler divergence）[2]。

```python
class SensorVAE(nn.Module):
    def __init__(self, input_channels=6, seq_len=100, latent_dim=16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 32, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
            nn.Conv1d(32, 64, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
            nn.Flatten(),
            nn.Linear(64 * (seq_len // 4), 256), nn.ReLU(),
        )
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_logvar = nn.Linear(256, latent_dim)
        # decoder 与 AE 类似，此处省略

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        return mu + torch.randn_like(std) * std

    def anomaly_score(self, x):
        h = self.encoder(x)
        mu, logvar = self.fc_mu(h), self.fc_logvar(h)
        z = self.reparameterize(mu, logvar)
        x_recon = self.decoder(z)
        recon_error = ((x - x_recon) ** 2).mean(dim=[1, 2])
        kl_div = -0.5 * (1 + logvar - mu.pow(2) - logvar.exp()).sum(dim=1)
        return recon_error + 0.1 * kl_div
```

## 3. Isolation Forest

### 3.1 核心直觉

正常点"藏在人群中"，平均路径长；异常点易被随机分割隔离，路径短[1]。

```python
from sklearn.ensemble import IsolationForest

def isolation_forest_detector(train_data, test_data, contamination=0.01):
    clf = IsolationForest(
        n_estimators=100,
        max_samples="auto",
        contamination=contamination,
        random_state=42,
    )
    clf.fit(train_data)
    predictions = clf.predict(test_data)  # 1=正常，-1=异常
    scores = clf.decision_function(test_data)
    return predictions, scores
```

### 3.2 算法要点

1. 随机选特征；2. 在 [min, max] 随机切分；3. 重复至隔离或达最大深度。

异常分数：

$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$

其中 \(E(h(x))\) 为平均路径长度，\(c(n)\) 为归一化因子[1]。

### 3.3 流式变体（示意）

```python
class StreamingIsolationForest:
    """滑动窗口定期重训；非严格增量 IF"""

    def __init__(self, window_size=1000, n_estimators=50, update_interval=100):
        self.window_size = window_size
        self.buffer = []
        self.n_estimators = n_estimators
        self.update_interval = update_interval
        self.model = None
        self.sample_count = 0

    def update(self, new_sample):
        self.buffer.append(new_sample)
        if len(self.buffer) > self.window_size:
            self.buffer.pop(0)
        self.sample_count += 1
        if self.sample_count % self.update_interval == 0 and len(self.buffer) >= 100:
            import numpy as np
            self.model = IsolationForest(n_estimators=self.n_estimators)
            self.model.fit(np.array(self.buffer))

    def predict(self, sample):
        if self.model is None:
            return 0.0
        return self.model.decision_function(sample.reshape(1, -1))[0]
```

## 4. One-Class SVM

OC-SVM 在特征空间找包围正常数据的紧边界；对特征尺度敏感，需标准化[6]。

```python
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler

def one_class_svm_detector(train_data, test_data, kernel="rbf", nu=0.01):
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_data)
    test_scaled = scaler.transform(test_data)
    clf = OneClassSVM(kernel=kernel, nu=nu, gamma="scale")
    clf.fit(train_scaled)
    return clf.predict(test_scaled), clf.decision_function(test_scaled)
```

## 5. 方法对比与选型

### 5.1 综合对比（量级示意，非跨论文统一基准）

| 方法 | 相对检测力（示意） | 推理延迟量级 | 内存量级 | 训练 | 流式 | 适用倾向 |
|------|-------------------|-------------|---------|------|------|---------|
| Autoencoder | 高（复杂时序） | 数毫秒 | 数十–数百 KB | 分钟级 | 弱 | 复杂时序 |
| VAE | 高（可概率解释） | 数毫秒 | 百 KB–MB | 分钟级 | 弱 | 需不确定性 |
| Isolation Forest | 中高（表格特征） | 亚毫秒–毫秒 | MB 级 | 秒级 | 部分 | 手工特征 |
| One-Class SVM | 中 | 毫秒级 | 数–数十 MB | 分钟级 | 弱 | 小样本 |
| LOF | 中（局部密度） | 毫秒级 | 较大 | 秒级 | 难 | 局部异常 |
| LSTM-AE | 很高（长依赖） | 十余毫秒量级 | 数百 KB–MB | 更久 | 较好 | 长序列[9] |

绝对 F1 / 延迟强依赖数据集与硬件；跨论文数字不可直接横比[3][4][10]。

### 5.2 边缘平台约束（硬件规格为公开量级）

| 平台 | RAM 量级 | Flash/存储 | 推荐倾向 |
|------|---------|-----------|---------|
| ESP32 | 约 520KB | 约 4MB | 轻量 IF / 极简规则 |
| ESP32-S3 | 约 512KB + PSRAM | 约 16MB | INT8 小型 AE[8] |
| RPi Zero 2W | 约 512MB | SD | AE / IF |
| RPi 4 | GB 级 | SD | 多数方法可试 |

## 6. 工业振动监测骨架

```python
import numpy as np
from scipy.fft import fft

class VibrationAnomalyDetector:
    """电机振动：特征 + AE 分数 + 粗诊断（教学）"""

    def __init__(self, sampling_rate=1000, window_size=1024):
        self.sampling_rate = sampling_rate
        self.window_size = window_size
        self.autoencoder = SensorAutoencoder(input_channels=3, seq_len=window_size)
        self.threshold = None
        self.normal_rms = 1.0

    def extract_features(self, raw_signal):
        features = {
            "rms": float(np.sqrt(np.mean(raw_signal**2))),
            "peak": float(np.max(np.abs(raw_signal))),
        }
        features["crest_factor"] = features["peak"] / (features["rms"] + 1e-8)
        features["kurtosis"] = float(
            np.mean((raw_signal - raw_signal.mean()) ** 4) / (np.std(raw_signal) ** 4 + 1e-8)
        )
        spectrum = np.abs(fft(raw_signal))[: len(raw_signal) // 2]
        freqs = np.fft.fftfreq(len(raw_signal), 1 / self.sampling_rate)[: len(raw_signal) // 2]
        features["dominant_freq"] = float(freqs[np.argmax(spectrum)])
        return features

    def diagnose(self, anomaly_score, features):
        if self.threshold is None or anomaly_score < self.threshold:
            return "正常运行"
        if features["kurtosis"] > 5:
            return "可能冲击类故障（如轴承点蚀），需人工确认"
        if features["dominant_freq"] > 500:
            return "可能高频磨损相关，需人工确认"
        if features["rms"] > 2 * self.normal_rms:
            return "可能不平衡/松动，需人工确认"
        return "异常模式未知，建议人工检查"
```

部署示意：传感器 → 边缘节点特征与推理 → 正常本地记日志 / 异常上报。相对全量上传，边缘筛选通常可显著降低通信能耗，具体比例取决于采样率与上报策略[8]。

公开基准如 SWaT 可用于复现实验，但与真实产线分布仍有差距[7]。

## 7. 实践建议

1. 用 sklearn IF 在公开异常基准上跑通评估脚本（精确率/召回/F1）。
2. 实现全连接 AE，再换 1D CNN AE 处理传感器窗。
3. 在 SWaT 等工业数据集上对比 IF 与 AE[7]。
4. 导出开放神经网络交换格式（Open Neural Network Exchange, ONNX），在单板机测 p99 延迟。
5. 滑动窗口 + 定期重训，并监控概念漂移。

**阈值**：百分位（如 99 / 99.9）通常比盲目 3σ 更稳；可用指数加权移动平均（EWMA）跟踪漂移[5]。

**架构**：小样本偏全连接；数据充足用 1D CNN；长序列考虑 LSTM-AE[9]；需概率解释用 VAE[2]。

**部署**：INT8 量化与知识蒸馏可降体积与延迟，精度损失需实测[8]。

## 8. 局限、挑战与可改进方向

### 1. 阈值与概念漂移

**局限**：固定阈值在工况切换、季节性负载下误报/漏报上升[5]。
**改进**：动态阈值、分工况模型、漂移检测触发再训练。

### 2. 基准分数不可直接迁移

**局限**：论文 F1 多在清洗后的公开集上；现场噪声、传感器标定与标签定义不同[3][7]。
**改进**：影子模式标定；按设备分群；报告完整"采样→告警"延迟。

### 3. 微控制器内存墙

**局限**：完整 IF 森林或中等 AE 在无外部 RAM 的 MCU 上难落地[8]。
**改进**：特征级 IF、深度压缩、网关侧推理 + 终端粗筛。

### 4. 可解释性不足

**局限**：高重建误差不直接对应故障类型，运维难闭环。
**改进**：结合时频特征规则；注意力/关联差异类模型作辅助解释[10]。

## 参考文献

[1] F. T. Liu et al., "Isolation Forest," ICDM, 2008.
[2] J. An and S. Cho, "Variational Autoencoder based Anomaly Detection using Reconstruction Probability," SNU Tech. Report, 2015.
[3] G. Pang et al., "Deep Learning for Anomaly Detection: A Review," ACM Computing Surveys, 2021.
[4] J. Audibert et al., "USAD: UnSupervised Anomaly Detection on Multivariate Time Series," KDD, 2020.
[5] K. Hundman et al., "Detecting Spacecraft Anomalies Using LSTMs and Nonparametric Dynamic Thresholding," KDD, 2018.
[6] Y. Zhao et al., "PyOD: A Python Toolbox for Scalable Outlier Detection," JMLR, 2019.
[7] J. Goh et al., "A Dataset to Support Research in the Design of Secure Water Treatment Systems (SWaT)," CRITIS, 2017.
[8] D. Li et al., "TinyAD: Memory-Efficient Anomaly Detection on Microcontrollers," SenSys, 2023.
[9] P. Malhotra et al., "LSTM-based Encoder-Decoder for Multi-sensor Anomaly Detection," ICML Workshop, 2016.
[10] H. Xu et al., "Anomaly Transformer: Time Series Anomaly Detection with Association Discrepancy," ICLR, 2022.
