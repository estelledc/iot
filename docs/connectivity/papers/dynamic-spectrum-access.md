---
schema_version: '1.0'
id: dynamic-spectrum-access
title: 动态频谱接入技术：从"固定车道"到"智能导航"
layer: 2
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 动态频谱接入技术：从"固定车道"到"智能导航"

> **难度**：🟡 中级 | **领域**：频谱管理、认知无线电、IoT 连接 | **阅读时间**：约 20 分钟

## 日常类比

想象一条八车道的高速公路。传统的频谱分配方式就像把每条车道永久指定给某家物流公司——即使凌晨三点没有一辆卡车在跑，其他公司也不能借用空闲车道。这就是静态频谱分配的现实：大量已授权频段在时间和空间维度上利用率不足 15%。

动态频谱接入（DSA）的思路是引入"实时导航系统"。车辆（设备）出发前先查询哪些车道当前空闲，行驶中持续感知周围交通状况，一旦原车道的"主人"回来，立刻平滑变道。这套机制既保护了车道主人的优先权，又让空闲资源不再浪费。

对于 IoT 场景，频谱资源日益紧张——到 2025 年全球 IoT 连接数超过 180 亿，而可用频段增长极为有限。DSA 是解决"频谱荒"的关键技术路径之一。

## 1. 频谱的三种使用模式

### 1.1 授权频谱（Licensed）

运营商通过拍卖获得独占使用权，如中国移动的 2.6 GHz（n41）、中国电信/联通的 3.5 GHz（n78）。优势是干扰可控、QoS 有保障；劣势是成本极高——2024 年全球 5G 频谱拍卖总支出已超 2000 亿美元。

### 1.2 免授权频谱（Unlicensed）

ISM 频段（2.4 GHz、5 GHz、6 GHz）任何人都可使用，前提是遵守发射功率限制。WiFi、BLE、Zigbee 都在此类频段工作。问题是"公地悲剧"：设备密集区域干扰严重。

### 1.3 共享频谱（Shared）

介于两者之间的新模式。美国的 CBRS（3.5 GHz 频段）是最成功的案例：

| 层级 | 用户 | 优先级 | 保护机制 |
|------|------|--------|----------|
| Tier 1 Incumbent | 美国海军雷达 | 最高 | ESC 感知 + SAS 疏散 |
| Tier 2 PAL | 拍卖获得者 | 中 | 频段独占（县级） |
| Tier 3 GAA | 任意用户 | 低 | 尽力而为 |

## 2. 两大技术路线

### 2.1 数据库驱动（Database-Driven）

核心思想：设备在发射前查询"频谱可用性数据库"，获得当前位置/时间可用的频段列表。

工作流程：

```
设备 --> 上报(GPS坐标, 设备参数) --> 频谱数据库(SAS/WSDB)
                                           |
设备 <-- 返回(可用频段列表, 最大功率, 有效时间) <-- 频谱数据库
```

典型系统包括 TV 白空间（TVWS）数据库（Ofcom/FCC 已运营超 10 年）、CBRS SAS（Google/Federated Wireless/CommScope 提供商用服务）、AFC 6 GHz（WiFi 6E/7 标准功率模式必须查询）。

Python 示例——查询 CBRS SAS 可用频段：

```python
import requests
import json

class SASClient:
    def __init__(self, sas_url, cbsd_id):
        self.sas_url = sas_url
        self.cbsd_id = cbsd_id

    def spectrum_inquiry(self, lat, lon, bandwidth_mhz=10):
        """查询当前位置可用频段"""
        payload = {
            "spectrumInquiryRequest": [{
                "cbsdId": self.cbsd_id,
                "inquiredSpectrum": [{
                    "lowFrequency": 3550_000_000,
                    "highFrequency": 3700_000_000
                }],
                "measReport": {
                    "latitude": lat,
                    "longitude": lon,
                    "height": 10,
                    "heightType": "AGL"
                }
            }]
        }
        resp = requests.post(
            f"{self.sas_url}/spectrumInquiry",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        available = resp.json()["spectrumInquiryResponse"][0]
        return available["availableChannel"]

# 使用示例
client = SASClient("https://sas.example.com/v1.2", "cbsd-001")
channels = client.spectrum_inquiry(37.7749, -122.4194)
for ch in channels:
    print(f"频段: {ch['lowFrequency']/1e6}-{ch['highFrequency']/1e6} MHz, "
          f"最大EIRP: {ch['maxEirp']} dBm")
```

### 2.2 感知驱动（Sensing-Driven）

设备自身通过能量检测、特征检测或协作感知判断频段是否被占用。

能量检测是最简单的方法：

```c
// 能量检测伪代码 (嵌入式 C)
#define THRESHOLD_DBM  -72.0  // 判决门限
#define NUM_SAMPLES    1024   // 采样点数

float energy_detection(float* iq_samples, int n) {
    float energy = 0.0f;
    for (int i = 0; i < n; i++) {
        energy += iq_samples[i] * iq_samples[i];
    }
    float avg_power_dbm = 10.0f * log10f(energy / n) + 30.0f;
    return avg_power_dbm;
}

bool is_channel_free(float* samples) {
    float power = energy_detection(samples, NUM_SAMPLES);
    return power < THRESHOLD_DBM;
}
```

两种路线对比：

| 维度 | 数据库驱动 | 感知驱动 |
|------|-----------|----------|
| 实时性 | 秒级（查询延迟） | 毫秒级 |
| 可靠性 | 高（确定性信息） | 受噪声/衰落影响 |
| 隐藏终端问题 | 不存在 | 严重 |
| 部署成本 | 需基础设施 | 设备侧计算 |
| 标准化程度 | 成熟（FCC/ETSI） | 研究阶段居多 |
| IoT 适用性 | 需网络连接 | 低功耗设备可用 |

## 3. 频谱拍卖与激励机制

### 3.1 频谱拍卖机制

常见机制包括同时多轮拍卖（SMRA，FCC 传统方式）、组合时钟拍卖（CCA，允许打包竞价）、以及激励拍卖（FCC 600 MHz 频段，电视台自愿退出获得补偿）。

### 3.2 动态频谱交易

实时频谱市场 2024-2025 年开始有实际部署：

- 频谱即服务（SPaaS）：CBRS PAL 持有者可将闲置频段分时租给其他用户
- 区块链频谱交易：利用智能合约自动执行频谱租赁，IBM 和 Nokia 有原型系统
- 博弈论定价：Nash 均衡定价确保买卖双方获益

## 4. 共存协议：LTE-U / LAA / NR-U

### 4.1 蜂窝网络进入免授权频段

运营商希望利用 5 GHz 免授权频段补充容量，但必须与 WiFi 公平共存：

| 技术 | 标准 | 共存机制 | 频段 |
|------|------|----------|------|
| LTE-U | 非 3GPP | CSAT（占空比调节） | 5 GHz |
| LAA | 3GPP R13 | LBT（先听后发） | 5 GHz |
| eLAA | 3GPP R14 | LBT + 上行 | 5 GHz |
| NR-U | 3GPP R16/17 | LBT cat4 + 多种信道接入 | 5/6 GHz |
| NR-U Light | 3GPP R18 | 简化 LBT + RedCap | 6 GHz |

### 4.2 LBT（Listen-Before-Talk）机制

```
[感知信道] --信道忙--> [退避等待(随机CW)] --CW=0--> [再次感知信道]
     |                                                    |
     | 信道空闲                                     信道空闲 |
     v                                                    v
[立即发送(小于等于MCOT)]                           [立即发送]
```

NR-U 定义了 4 种信道接入优先级（Cat 1-4），MCOT 从 2ms 到 10ms 不等，与 WiFi 的 EDCA 优先级对应。

## 5. 频谱效率度量

### 5.1 关键指标

频谱利用率衡量实际吞吐量与理论容量的比值（bps/Hz/km2）。频谱占用度衡量特定频段在时间-空间维度上被使用的比例。频谱空洞则是未被使用的频率-时间-空间资源块。

### 5.2 实测数据（2024 年研究）

全球多地频谱占用度测量结果：

| 频段 | 北京 | 纽约 | 伦敦 | 农村平均 |
|------|------|------|------|----------|
| 400-800 MHz | 72% | 65% | 58% | 12% |
| 800-2000 MHz | 81% | 73% | 69% | 18% |
| 2-3 GHz | 45% | 41% | 38% | 8% |
| 3-6 GHz | 23% | 19% | 21% | 3% |
| 6+ GHz | <5% | <5% | <5% | <1% |

结论：即使在城市核心区，3 GHz 以上频段仍有大量空闲资源可供 DSA 利用。

## 6. 机器学习驱动的频谱管理

### 6.1 典型应用场景

| 任务 | ML 方法 | 输入特征 | 输出 |
|------|---------|----------|------|
| 频谱预测 | LSTM/Transformer | 历史占用序列 | 未来 N 时隙占用概率 |
| 用户识别 | CNN | IQ 信号图 | 主用户 vs 次用户 |
| 功率控制 | DRL (DQN/PPO) | 信道状态 + 干扰 | 最优发射功率 |
| 频谱分配 | 图神经网络 | 网络拓扑 + 需求 | 频率规划 |

### 6.2 基于 DRL 的频谱接入策略

```python
import numpy as np

class SpectrumDQNAgent:
    """Deep Q-Network 频谱接入智能体"""

    def __init__(self, n_channels, n_actions=2):
        self.n_channels = n_channels
        self.n_actions = n_actions    # 0=等待, 1=接入
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.q_table = np.zeros((n_channels, 2, n_actions))

    def choose_action(self, state):
        """epsilon-贪心策略选择动作"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        ch, sense = state
        return np.argmax(self.q_table[ch, sense])

    def update(self, state, action, reward, next_state):
        """Q-learning 更新"""
        ch, sense = state
        nch, nsense = next_state
        lr, gamma = 0.1, 0.95
        target = reward + gamma * np.max(self.q_table[nch, nsense])
        self.q_table[ch, sense, action] += lr * (
            target - self.q_table[ch, sense, action]
        )
        self.epsilon = max(self.epsilon_min,
                          self.epsilon * self.epsilon_decay)

# 仿真循环
agent = SpectrumDQNAgent(n_channels=10)
for episode in range(1000):
    channel = np.random.randint(10)
    occupied = np.random.choice([0, 1], p=[0.6, 0.4])
    state = (channel, occupied)
    action = agent.choose_action(state)

    if action == 1 and occupied == 0:
        reward = 1.0   # 成功接入空闲信道
    elif action == 1 and occupied == 1:
        reward = -5.0  # 碰撞惩罚（保护主用户）
    else:
        reward = -0.1  # 等待的小惩罚

    next_state = (np.random.randint(10),
                  np.random.choice([0, 1], p=[0.6, 0.4]))
    agent.update(state, action, reward, next_state)
```

### 6.3 联邦学习在频谱管理中的应用

2024-2025 年热点方向：多个次用户联合训练频谱预测模型，不共享原始感知数据，保护各自的频谱使用隐私。实测表明，联邦 LSTM 模型在 10 个节点协作时，预测准确率可达 92%，接近集中式训练的 95%。

## 7. 实践建议

### 7.1 初学者入门路径

1. 理论基础（1-2 周）：学习信号检测理论（Neyman-Pearson 准则）、基本通信原理
2. 仿真实践（2-3 周）：用 Python + GNU Radio 搭建频谱感知仿真
3. 标准阅读（1 周）：ETSI EN 301 598（TVWS）、3GPP TS 37.213（NR-U LBT）
4. 动手项目：用 RTL-SDR（约 200 元）做本地频谱占用度测量；实现简单的能量检测 + 数据库查询 demo；在 ns-3 中仿真 LAA 与 WiFi 共存

### 7.2 具体调优建议

感知参数设计方面，能量检测门限根据目标虚警概率（Pfa）和检测概率（Pd）通过 ROC 曲线确定。建议 Pd 大于等于 0.9、Pfa 小于等于 0.1 作为起点。感知时长与吞吐量存在 trade-off：IEEE 802.22 建议感知时长不超过帧周期的 10%。

数据库查询策略方面，缓存有效期内复用结果以减少查询延迟。IoT 设备可通过网关代理查询降低自身功耗。移动设备根据速度调整查询频率：步行 5min/次，车载 30s/次。

NR-U 部署考量方面，室内场景优先考虑 6 GHz（WiFi 6E 设备尚少，干扰低）。企业专网场景 CBRS 3.5 GHz 是成熟选择。IoT 设备如使用 NR-U Light（R18 RedCap），功耗约为常规 NR-U 的 40%。

## 参考文献

1. FCC, "Report and Order: Rules for the 3.5 GHz Band," FCC 15-47, 2015 (amended 2023).
2. ETSI EN 303 387, "Reconfigurable Radio Systems; Cognitive Radio System Concepts," v1.2.1, 2024.
3. 3GPP TS 37.213, "Physical layer procedures for shared spectrum channel access," Release 18, 2024.
4. Akyildiz, I. F., et al., "Next Generation Dynamic Spectrum Access/Cognitive Radio Networks," Computer Networks, 2006.
5. Yin, S., et al., "Federated Deep Reinforcement Learning for Dynamic Spectrum Access," IEEE TWC, vol. 23, no. 4, 2024.
6. NTIA, "National Spectrum Strategy Implementation Plan," U.S. DoC, Nov. 2023.
7. Paisana, F., et al., "Spectrum Occupancy Statistics and Prediction: A Machine Learning Perspective," IEEE COMST, 2024.
8. Qualcomm, "NR-U: Unlicensed Spectrum for 5G NR," White Paper, 2024.
9. Google, "SAS as a Service: Architecture and Deployment Lessons from CBRS," IEEE DySPAN, 2024.
10. Zhang, Y., et al., "Blockchain-Enabled Spectrum Trading: Market Design and Performance," IEEE JSAC, vol. 42, 2024.
