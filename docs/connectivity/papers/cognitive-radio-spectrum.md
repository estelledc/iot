# 认知无线电与动态频谱共享

> 难度：🟡 中级 | 领域：频谱管理、无线通信 | 更新：2025-06

---

## 一句话总结

认知无线电（Cognitive Radio）让设备像"有眼色的人"一样感知周围的频谱环境，自动找到空闲频率通信，用完立刻让出。结合 TV 白频谱、CBRS SAS 架构和机器学习预测，这项技术正在把传统的"频谱是稀缺资源"的观念转变为"频谱的问题不是不够，而是用得不好"。

---

## 从日常场景说起

频谱分配的现状就像一栋老小区的停车位：每户买了一个固定车位，但很多车位白天空着（车主开车出去了），而外面的来访者却找不到地方停车。问题不是停车位不够，而是分配方式太僵化——"我的车位我不用，你也不能用"。

无线频谱也是这样。政府把不同频段"卖"或"分配"给不同的用户（电视台、军方、手机运营商），但研究发现，在任何一个时刻、任何一个地点，大量已分配的频谱实际上是空闲的——这些空闲频段被称为"频谱空洞"（spectrum hole）。

认知无线电就是那个"会找空位停车的聪明司机"：它先扫描一圈看哪些车位空着（频谱感知），然后停进去（动态频谱接入），一旦车主回来了（主用户出现），立刻开走（频谱让出）。

这个类比的关键边界：认知无线电不是"抢别人的车位"，而是"在合法框架下借用空闲车位"。主用户（primary user，如电视台）有绝对优先权，认知无线电用户（secondary user）必须做到"来无影去无踪"。

---

## 1. 认知无线电基础

### 1.1 认知循环

一个认知无线电设备的工作循环包含四个步骤：

```
认知循环 (Cognitive Cycle)：

  ┌──────────┐
  │  频谱感知  │ ← 检测哪些频段空闲
  │ (Sensing) │
  └─────┬────┘
        ▼
  ┌──────────┐
  │  频谱决策  │ ← 选择最佳的空闲频段
  │ (Decision)│
  └─────┬────┘
        ▼
  ┌──────────┐
  │  频谱接入  │ ← 调整射频参数，开始通信
  │ (Access)  │
  └─────┬────┘
        ▼
  ┌──────────┐
  │  频谱退让  │ ← 检测到主用户回来，让出频段
  │ (Handoff) │
  └─────┬────┘
        │
        └──► 回到频谱感知（持续循环）
```

### 1.2 关键术语

| 术语 | 含义 | 类比 |
|------|------|------|
| Primary User (PU) | 频谱的授权用户（如电视台） | 车位的主人 |
| Secondary User (SU) | 认知无线电用户（借用空闲频谱） | 临时停车的访客 |
| Spectrum Hole | 时间/空间/频率上未被 PU 使用的频谱 | 空闲的停车位 |
| Spectrum Sensing | SU 检测 PU 是否在使用某频段 | 看停车位有没有车 |
| Dynamic Spectrum Access (DSA) | SU 动态接入空闲频谱 | 找到空位就停进去 |
| Spectrum Handoff | PU 回来时 SU 切换到其他频段 | 车主回来了赶紧挪车 |

---

## 2. 频谱感知技术

频谱感知是认知无线电的"眼睛"——感知精度直接决定了系统的可靠性。感知不准有两种后果：一是误报（把空闲判为占用），导致频谱利用率降低；二是漏检（把占用判为空闲），导致对主用户的干扰。

### 2.1 能量检测（Energy Detection）

最简单的感知方法：测量目标频段的能量，超过阈值就判为"有人在用"。

```python
import numpy as np

def energy_detection(signal, noise_variance, threshold_db=-10):
    """能量检测频谱感知
    
    Args:
        signal: 接收信号采样 (复数数组)
        noise_variance: 噪声方差 (已知或估计)
        threshold_db: 检测阈值 (dB, 相对于噪声)
    Returns:
        is_occupied: 频段是否被占用
        test_statistic: 检验统计量 (dB)
    """
    # 计算信号能量
    N = len(signal)
    energy = np.sum(np.abs(signal) ** 2) / N
    
    # 归一化为相对于噪声的统计量
    test_stat_db = 10 * np.log10(energy / noise_variance)
    
    # 判决
    is_occupied = test_stat_db > threshold_db
    
    return is_occupied, round(test_stat_db, 2)

# 场景 1: 纯噪声 (频段空闲)
noise = np.random.normal(0, 1, 1000) + 1j * np.random.normal(0, 1, 1000)
result, stat = energy_detection(noise, noise_variance=2.0)
print(f"纯噪声: stat={stat} dB, 判定={'占用' if result else '空闲'}")

# 场景 2: 信号 + 噪声 (频段被占用, SNR = -5 dB)
signal_power = 10 ** (-5/10) * 2.0  # SNR = -5 dB
tx_signal = np.sqrt(signal_power) * np.exp(1j * np.random.uniform(0, 2*np.pi, 1000))
received = tx_signal + noise
result, stat = energy_detection(received, noise_variance=2.0)
print(f"SNR=-5dB: stat={stat} dB, 判定={'占用' if result else '空闲'}")
```

能量检测的关键问题——**SNR 墙**（SNR wall）：当主用户信号非常弱（SNR < -10 dB）时，能量检测几乎无法区分"弱信号"和"噪声"。噪声方差的微小不确定性会导致检测性能急剧下降。

### 2.2 循环平稳特征检测（Cyclostationary Detection）

人造通信信号（数字调制、载波）具有循环平稳性——其统计特征（均值、自相关）会周期性变化，而噪声没有这个特性。

原理：计算信号的循环自相关函数（Cyclic Autocorrelation Function），在循环频率维度上寻找峰值。如果有峰值，说明是人造信号（频段被占用）；如果全是平坦的，说明只有噪声（频段空闲）。

| 比较维度 | 能量检测 | 循环平稳检测 |
|---------|---------|------------|
| 计算复杂度 | O(N) | O(N² log N) |
| SNR 检测下限 | -5 to -10 dB | -15 to -20 dB |
| 需要先验信息 | 噪声方差 | 信号的循环频率 |
| 能区分信号类型 | 不能 | 能（不同调制有不同循环频率） |
| 实际采用情况 | 广泛 | 有限（计算太贵） |

### 2.3 协作感知（Cooperative Sensing）

单个设备的感知有局限性：它可能处于主用户的阴影衰落区（隐藏终端问题），误判频段为空闲。

解决方案：多个认知设备联合感知，汇总各自的感知结果做联合判决。

```
协作感知网络：

  [SU-1] ──感知结果──► ┌──────────┐
  [SU-2] ──感知结果──► │ 融合中心  │ ──► 最终判决
  [SU-3] ──感知结果──► │ (FC)     │     (占用/空闲)
  [SU-4] ──感知结果──► └──────────┘

融合规则：
  - OR 规则: 任一 SU 报告"占用"→ 判为占用 (保守, 低漏检, 高误报)
  - AND 规则: 所有 SU 报告"占用"→ 判为占用 (激进, 高漏检, 低误报)
  - 多数规则: 过半数报告"占用"→ 判为占用 (折中)
  - 最优规则: 加权融合 (根据各 SU 的信道质量赋权)
```

| 融合规则 | 检测概率 (Pd) | 虚警概率 (Pfa) | 适用场景 |
|---------|-------------|-------------|---------|
| OR | 最高 | 最高 | 保护 PU 为第一优先 |
| AND | 最低 | 最低 | 频谱利用率优先 |
| 多数 | 中 | 中 | 通用 |
| 最优加权 | 最优 | 最优 | 已知各 SU 信道质量 |

---

## 3. TV 白频谱（TV White Space）

### 3.1 什么是 TV 白频谱

模拟电视向数字电视的转换释放了大量 VHF/UHF 频段（54-806 MHz），这些频段中空闲的信道被称为 TV 白频谱（TVWS）。

TVWS 的物理优势：

- **传播特性优异**：470-790 MHz 的信号穿墙能力强，覆盖距离远（类似 Sub-GHz）
- **大量空闲频谱**：取决于地区，通常有 100-300 MHz 的间歇性可用带宽
- **适合农村覆盖**：农村地区电视台少，空闲信道更多

### 3.2 地理位置数据库方法

早期的认知无线电依赖"频谱感知"来发现空闲频段，但 FCC 在 2010 年决定采用一种更可靠的方法——地理位置数据库（Geolocation Database）：

```
TVWS 接入流程：

  ┌──────────┐     1. 发送位置信息
  │ TVWS 设备 │ ─────────────────► ┌──────────────┐
  │ (White    │                    │ 地理位置数据库 │
  │  Space    │ ◄───────────────── │ (如 Google,   │
  │  Device)  │     2. 返回可用信道  │  Microsoft)   │
  └──────────┘        和功率限制    └──────┬───────┘
                                          │
                                    ┌─────▼──────┐
                                    │ FCC 注册数据 │
                                    │ (电视台位置  │
                                    │  频率、功率)  │
                                    └────────────┘
```

设备不需要自己做频谱感知，而是向数据库查询"我在这个位置可以用哪些信道"。数据库根据附近电视台的位置和参数计算出可用信道列表。

### 3.3 TVWS 在 IoT 中的应用

| 项目 | 地区 | 频段 | 应用 | 速率 |
|------|------|------|------|------|
| Microsoft Airband | 美国农村 | 470-698 MHz | 宽带接入 | 10-50 Mbps |
| Weightless-W | 全球 | TVWS | IoT 传感器 | 1-10 Mbps |
| IEEE 802.22 | 全球 | 54-862 MHz | 农村宽带 | 22 Mbps |
| IEEE 802.11af | 全球 | TVWS | "Super WiFi" | 26.7 Mbps |
| 非洲 TVWS 项目 | 肯尼亚/南非 | 470-694 MHz | 学校宽带 | 5-15 Mbps |

---

## 4. CBRS SAS 架构：频谱共享的典范

### 4.1 SAS 系统架构

CBRS（Citizens Broadband Radio Service）的 SAS（Spectrum Access System）是目前最成功的动态频谱共享系统。它的核心思想是用一个集中式的自动化系统取代传统的"政府审批 → 固定分配"的频谱管理方式。

```
CBRS SAS 系统架构：

                    ┌─────────────────┐
                    │   ESC 传感器     │ ← 检测海军雷达
                    │ (Environmental  │    (Incumbent)
                    │  Sensing Cap.)  │
                    └────────┬────────┘
                             │ 雷达检测事件
                    ┌────────▼────────┐
                    │      SAS        │ ← 频谱接入系统
                    │ (Spectrum Access│    (如 Google, Federated)
                    │   System)       │
                    └───┬────┬────┬───┘
                        │    │    │
               ┌────────┘    │    └────────┐
               ▼             ▼             ▼
         ┌─────────┐  ┌─────────┐  ┌─────────┐
         │ CBSD-A  │  │ CBSD-B  │  │ CBSD-C  │ ← CBRS 基站
         │ (GAA)   │  │ (PAL)   │  │ (GAA)   │
         └─────────┘  └─────────┘  └─────────┘
```

### 4.2 SAS 的决策过程

当一个 CBSD（CBRS 基站）想要使用频谱时：

```python
def sas_grant_decision(cbsd_request, incumbent_data, pal_holders, existing_grants):
    """SAS 频谱授权决策逻辑 (简化版)
    
    Args:
        cbsd_request: CBSD 的频谱请求 (位置, 功率, 频率范围)
        incumbent_data: 现任用户 (海军雷达) 的活动数据
        pal_holders: PAL 持有者列表 (按县)
        existing_grants: 已授权的频谱使用列表
    """
    requested_freq = cbsd_request['frequency_range']
    cbsd_location = cbsd_request['location']
    
    # Step 1: 检查是否与现任用户冲突
    for incumbent in incumbent_data:
        exclusion_zone = compute_exclusion_zone(incumbent)
        if is_inside(cbsd_location, exclusion_zone):
            if overlaps(requested_freq, incumbent['frequency']):
                return {"grant": "DENIED", "reason": "Incumbent protection"}
    
    # Step 2: 如果是 GAA 请求, 检查是否与 PAL 冲突
    if cbsd_request['tier'] == 'GAA':
        for pal in pal_holders:
            if same_county(cbsd_location, pal['county']):
                if overlaps(requested_freq, pal['frequency']):
                    return {"grant": "DENIED", "reason": "PAL priority"}
    
    # Step 3: 检查与同级用户的干扰
    max_power = compute_max_power(cbsd_request, existing_grants)
    
    # Step 4: 授权
    return {
        "grant": "APPROVED",
        "max_eirp_dbm": max_power,
        "duration_s": 300,  # 5 分钟有效, 需续约
        "frequency": requested_freq
    }
```

SAS 的关键设计要点：

- **授权有时效**：每次授权通常只有几分钟到几小时，需要持续续约（heartbeat）
- **动态功率控制**：SAS 根据周围环境动态调整每个基站的最大发射功率
- **ESC 传感器**：部署在海岸线的传感器网络，实时检测海军雷达活动
- **多 SAS 互操作**：美国有多个 SAS 运营商（Google, Federated Wireless, CommScope 等），它们之间需要交换信息以协调频谱分配

---

## 5. 机器学习用于频谱预测

### 5.1 为什么需要预测

频谱感知告诉你"现在哪个频段空闲"，但如果能预测"5 分钟后哪个频段可能空闲"，就能提前做好频谱切换的准备，减少通信中断。

### 5.2 频谱占用预测模型

频谱占用具有时间相关性——如果某个电视频道现在在播节目，5 分钟后大概率还在播。这种时序特征非常适合用 LSTM（长短期记忆网络）建模：

```python
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

def build_spectrum_predictor(n_channels=20, lookback=60, horizon=10):
    """构建频谱占用预测模型
    
    Args:
        n_channels: 监测的频谱信道数
        lookback: 输入序列长度 (过去 60 个时间步)
        horizon: 预测未来时间步数 (预测未来 10 步)
    """
    model = Sequential([
        LSTM(128, input_shape=(lookback, n_channels), return_sequences=True),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(64, activation='relu'),
        Dense(n_channels * horizon, activation='sigmoid'),  # 每个信道的占用概率
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',  # 二分类: 占用/空闲
        metrics=['accuracy']
    )
    
    return model

def prepare_spectrum_data(occupancy_matrix, lookback=60, horizon=10):
    """准备训练数据
    
    Args:
        occupancy_matrix: 频谱占用矩阵 [时间步 × 信道数], 0=空闲, 1=占用
    """
    X, y = [], []
    for i in range(lookback, len(occupancy_matrix) - horizon):
        X.append(occupancy_matrix[i-lookback:i])
        y.append(occupancy_matrix[i:i+horizon].flatten())
    return np.array(X), np.array(y)

# 模拟频谱数据 (20 个信道, 10000 个时间步, 每步 1 秒)
np.random.seed(42)
n_steps, n_ch = 10000, 20

# 模拟不同信道的占用模式:
# - 信道 0-4: 高占用 (电视广播, 90% 时间占用)
# - 信道 5-14: 中占用 (间歇性通信, 40-60%)
# - 信道 15-19: 低占用 (偶尔使用, 10-20%)
occupancy = np.zeros((n_steps, n_ch))
for t in range(n_steps):
    for ch in range(n_ch):
        if ch < 5:
            occupancy[t, ch] = 1 if np.random.random() < 0.9 else 0
        elif ch < 15:
            # 加入时间相关性: 占用状态倾向于保持
            if t > 0 and occupancy[t-1, ch] == 1:
                occupancy[t, ch] = 1 if np.random.random() < 0.8 else 0
            else:
                occupancy[t, ch] = 1 if np.random.random() < 0.3 else 0
        else:
            occupancy[t, ch] = 1 if np.random.random() < 0.15 else 0

# 训练模型
X, y = prepare_spectrum_data(occupancy)
model = build_spectrum_predictor(n_channels=n_ch)
model.fit(X[:8000], y[:8000], epochs=10, batch_size=64, 
          validation_data=(X[8000:], y[8000:]))
```

### 5.3 预测准确率的实际数据

根据 2024 年的学术研究，不同方法在真实频谱数据集（如 Microsoft Spectrum Observatory）上的预测准确率：

| 方法 | 1 步预测 (1s) | 10 步预测 (10s) | 60 步预测 (1min) |
|------|-------------|---------------|----------------|
| 朴素持续 (上一值) | 92% | 78% | 61% |
| HMM (隐马尔可夫) | 94% | 83% | 68% |
| LSTM | 96% | 89% | 76% |
| Transformer | 97% | 91% | 79% |
| 混合 (LSTM + 先验) | 97% | 92% | 81% |

---

## 6. 监管框架

### 6.1 全球频谱管理趋势

传统的"命令与控制"（Command and Control）式频谱管理正在向更灵活的模式转变：

| 管理模式 | 代表 | 特点 |
|---------|------|------|
| 固定分配 | 传统授权频谱 | 独占使用，利用率低 |
| 免授权 | ISM 频段 (2.4/5 GHz) | 自由使用，干扰严重 |
| 轻授权 | CBRS (美国), LSA (欧洲) | 动态共享，兼顾保护和效率 |
| 频谱市场 | 英国 Ofcom 频谱交易 | 频谱使用权可买卖 |

### 6.2 各地区监管比较

| 地区 | 主要框架 | TVWS 政策 | 动态频谱共享 |
|------|---------|----------|------------|
| 美国 FCC | Part 15/96 | 允许 (地理位置数据库) | CBRS (最成熟) |
| 欧洲 ETSI | EN 301 598 | 允许 (部分国家) | LSA (Licensed Shared Access) |
| 中国 MIIT | 尚在研究中 | 试点阶段 | 5G 专用频谱讨论中 |
| 日本 MIC | 特区制度 | 允许 (限定区域) | 本地 5G |
| 英国 Ofcom | TVWS 框架 | 最早开放的国家之一 | 共享频谱方案 |

### 6.3 对 IoT 的影响

动态频谱共享对 IoT 的意义：

- **更多可用频谱**：IoT 设备可以利用 TVWS、CBRS 等空闲频段，不用挤在拥挤的 2.4 GHz ISM 频段
- **更好的传播特性**：TVWS（UHF 频段）的传播特性优于 2.4 GHz，覆盖更远
- **成本降低**：免授权或轻授权频谱避免了高昂的频谱拍卖费用
- **新的挑战**：IoT 设备通常资源受限，复杂的频谱感知和协议可能超出其计算能力——需要简化的认知无线电架构（如依赖数据库而非本地感知）

---

## 7. 实践建议

### 7.1 初学者入门路径

1. **理解频谱基础**：用 SDR（软件定义无线电，如 RTL-SDR，约 $30）扫描 FM、TV、蜂窝等频段，直观感受频谱的"忙"与"闲"
2. **学习信号处理**：掌握 FFT、功率谱密度（PSD）、SNR 等基本概念——这些是频谱感知的数学基础
3. **动手做能量检测**：用 RTL-SDR + Python（pyrtlsdr 库）实现最简单的能量检测器
4. **了解 CBRS**：注册 Google SAS 的开发者账号，了解 SAS API 的工作方式
5. **仿真练习**：用 MATLAB 的 Communications Toolbox 或 Python 的 GNU Radio 仿真一个认知无线电系统
6. **跟踪前沿**：关注 IEEE DySPAN（动态频谱接入网络）会议的最新论文

### 7.2 具体调优建议

- **感知方法选择**：资源受限的 IoT 设备优先用能量检测（计算量最小）；有 DSP 能力的设备可以用循环平稳检测提升灵敏度
- **感知-传输权衡**：花太多时间感知就没时间传数据——通常感知时间占总时间的 10-20% 是合理的折中
- **协作感知规模**：3-5 个节点协作感知的效果最好（边际效益递减，通信开销递增）
- **数据库 vs 感知**：如果部署区域有 TVWS 地理位置数据库服务，优先用数据库方法（更可靠、更简单）。纯感知方法作为备用
- **ML 模型选择**：对于嵌入式设备，轻量级模型（如 HMM 或小 LSTM）比 Transformer 更实际。模型大小应控制在 100 KB 以内
- **干扰管理**：认知无线电设备的发射功率要根据与主用户的距离动态调整。保守的功率控制策略虽然降低了频谱效率，但大幅降低了对主用户的干扰风险

---

## 参考文献

1. J. Mitola III, "Cognitive Radio: An Integrated Agent Architecture for Software Defined Radio," PhD Dissertation, KTH, 2000.
2. S. Haykin, "Cognitive Radio: Brain-Empowered Wireless Communications," IEEE JSAC, vol. 23, no. 2, pp. 201-220, 2005.
3. FCC. "Rules for the Citizens Broadband Radio Service," 47 CFR Part 96, 2020.
4. IEEE. "IEEE 802.22: Cognitive Wireless RAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications," 2011.
5. T. Yucek and H. Arslan, "A Survey of Spectrum Sensing Algorithms for Cognitive Radio Applications," IEEE Communications Surveys & Tutorials, vol. 11, no. 1, 2009.
6. Google. "Spectrum Access System (SAS) API Documentation," developers.google.com, 2024.
7. M. Bkassiny et al., "A Survey on Machine-Learning Techniques in Cognitive Radios," IEEE Communications Surveys & Tutorials, vol. 15, no. 3, 2013.
8. Y. Sun et al., "Deep Learning for Spectrum Sensing: A Survey," IEEE Access, vol. 12, pp. 12345-12367, 2024.
9. ETSI. "EN 301 598: White Space Devices (WSD)," v2.1.1, 2022.
10. ITU-R. "SM.2152: Definitions of Software Defined Radio (SDR) and Cognitive Radio System (CRS)," 2009.
