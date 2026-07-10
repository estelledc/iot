---
schema_version: '1.0'
id: swipt-energy-harvesting
title: 射频能量收集与通信一体化 SWIPT
layer: 2
content_type: UNKNOWN
difficulty: intermediate
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 射频能量收集与通信一体化 SWIPT

> **难度**：🟡 中级 | **领域**：无线通信、能量收集 | **阅读时间**：约 18 分钟

---

## 日常类比

想象你在家里给手机无线充电：把手机放在充电板上，电磁波从充电板传到手机，转换成电能给电池充电。现在设想一下：如果这个充电板不仅给你的手机充电，同时还通过同一束电磁波传输数据（比如充电进度、电池健康状态），那就是 SWIPT（Simultaneous Wireless Information and Power Transfer）的核心思想——用同一个射频信号同时做两件事：传数据和送电。

更贴切的类比是太阳能板加日晷。太阳光照在日晷上，你通过影子的位置读取"信息"（时间）；同时旁边的太阳能板把阳光转化为电能。SWIPT 做的就是类似的事情——同一个射频信号到达接收器后，一部分能量被用来"读取信息"（解调数据），另一部分被用来"发电"（整流为直流电）。

对 IoT 来说，SWIPT 的价值在于解决最头疼的问题：**电池寿命**。如果部署在桥梁结构内部、水下、人体植入物等地方的传感器能从基站的射频信号中收获能量，就不再需要定期更换电池甚至不需要电池。基站发送数据查询的同时，也在给传感器"充电"——读数据和供电一箭双雕。

---

## 1. SWIPT 基本原理

### 1.1 信息与能量的根本矛盾

在同一个射频信号中同时传递信息和能量，面临一个根本性的矛盾：

- **信息接收**需要尽可能精确地检测信号的波形细节（幅度、相位、频率的微小变化），对信号的"形状"敏感
- **能量收集**需要尽可能多地提取信号的**总功率**，不关心波形细节

一个极端的例子：恒定的直流信号（没有任何变化）功率最大，但信息量为零；而一个极弱的精巧调制信号包含大量信息，但能量几乎可以忽略。

信息论的分析表明，在功率受限的信道上，信息速率 R 和可收集能量 Q 之间存在一个基本的 tradeoff：

```python
import numpy as np
import matplotlib.pyplot as plt

def rate_energy_tradeoff(P_total, noise_power, bandwidth=1.0):
    """信息速率与可收集能量的基本 tradeoff
    
    假设总功率 P_total 分为两部分：
    - P_info: 用于信息传输
    - P_energy = P_total - P_info: 用于能量收集
    
    返回 (R, Q) 的帕累托前沿
    """
    rho_values = np.linspace(0, 1, 100)  # 信息功率占比
    rates = []
    energies = []
    
    for rho in rho_values:
        P_info = rho * P_total
        P_energy = (1 - rho) * P_total
        
        # Shannon 速率
        R = bandwidth * np.log2(1 + P_info / noise_power)
        # 可收集能量（假设 RF-DC 转换效率 50%）
        Q = 0.5 * P_energy
        
        rates.append(R)
        energies.append(Q)
    
    return rates, energies

# P_total = 1W, noise = 0.01W
R, Q = rate_energy_tradeoff(1.0, 0.01)
# R-Q 曲线是一条向右下倾斜的曲线：
# 全部功率给信息 → R_max, Q=0
# 全部功率给能量 → R=0, Q_max
```

### 1.2 接收器架构

为了在实际系统中处理信息-能量 tradeoff，学术界提出了四种接收器架构：

| 架构 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 理想接收器 | 同一信号同时做信息解码和能量收集 | 理论最优 | 物理上不可行 |
| 时间切换 (TS) | 交替在信息解码和能量收集之间切换 | 简单、一套硬件 | 时间效率低 |
| 功率分割 (PS) | 将信号功率按比例分配给两个支路 | 连续操作 | 需要功率分配器 |
| 天线切换 (AS) | 部分天线收信息、部分天线收能量 | 适合 MIMO | 天线利用率低 |

**时间切换（Time Switching, TS）** 是最简单的方案。接收器在 α 比例的时间内做能量收集，在 (1-α) 比例的时间内做信息解码。就像你白天用太阳能板充电，晚上用电池供电听收音机——两件事不同时做。

**功率分割（Power Splitting, PS）** 更灵活。接收信号通过一个功率分配器，ρ 比例的信号功率送给信息解码电路，(1-ρ) 比例的功率送给整流电路。两个功能同时工作，但各自拿到的功率都打了折扣。

```python
class PowerSplittingReceiver:
    """功率分割 SWIPT 接收器模型"""
    
    def __init__(self, rho=0.5, rf_dc_efficiency=0.4):
        """
        rho: 分配给信息解码的功率比例 (0-1)
        rf_dc_efficiency: RF-DC 转换效率
        """
        self.rho = rho
        self.eta = rf_dc_efficiency
    
    def compute_rate_and_energy(self, received_power_dbm, noise_power_dbm, bandwidth_hz):
        """计算信息速率和收集能量"""
        P_rx = 10**((received_power_dbm - 30) / 10)   # dBm → W
        N0 = 10**((noise_power_dbm - 30) / 10)
        
        # 信息解码支路
        P_info = self.rho * P_rx
        # 功率分配器引入的额外噪声
        noise_splitter = 1e-9  # -60 dBm 典型值
        snr = P_info / (self.rho * N0 + noise_splitter)
        rate_bps = bandwidth_hz * np.log2(1 + snr)
        
        # 能量收集支路
        P_harvest = (1 - self.rho) * P_rx
        energy_harvested_w = self.eta * P_harvest
        
        return rate_bps, energy_harvested_w
    
    def optimize_rho(self, received_power_dbm, noise_power_dbm, 
                     bandwidth_hz, min_energy_w):
        """找到满足最低能量需求的最优 rho"""
        best_rate = 0
        best_rho = 0
        
        for rho in np.linspace(0.01, 0.99, 100):
            self.rho = rho
            rate, energy = self.compute_rate_and_energy(
                received_power_dbm, noise_power_dbm, bandwidth_hz)
            if energy >= min_energy_w and rate > best_rate:
                best_rate = rate
                best_rho = rho
        
        self.rho = best_rho
        return best_rho, best_rate
```

---

## 2. SWIPT 协议设计

### 2.1 帧结构

SWIPT 系统的帧结构需要考虑信息传输和能量收集的时序安排。典型的 TS-SWIPT 帧结构：

```
|<---------- 一帧周期 T ---------->|
|--- 能量收集 (αT) ---|-- 信息传输 ((1-α)T) --|
|   连续波/能量信号    | 前导码 | 数据 | ACK  |
```

能量收集阶段发送的信号可以是：
- **未调制连续波（CW）**：RF-DC 转换效率最高
- **多音信号（Multi-tone）**：多个频率的叠加信号，PAPR 高，整流效率更高
- **伪随机序列**：可以同时用于信道估计

2024 年的研究发现，多音信号的能量收集效率比单一连续波高 20-40%，因为整流二极管的非线性特性在高 PAPR 信号下更有利。

### 2.2 自适应切换策略

实际 IoT 场景中，信道条件和能量需求时刻变化。自适应策略根据当前状态动态调整 TS 的 α 值或 PS 的 ρ 值：

| 场景 | 策略 | α/ρ 设置 |
|------|------|---------|
| 电池电量低 + 信道好 | 优先充电 | α=0.8 / ρ=0.2 |
| 电池电量高 + 有紧急数据 | 优先传输 | α=0.1 / ρ=0.9 |
| 电池电量中 + 信道差 | 积攒能量等信道好 | α=0.6 / ρ=0.3 |
| 电池电量高 + 无数据 | 纯能量收集 | α=1.0 / ρ=0 |

---

## 3. 能量-信息 Tradeoff 深入分析

### 3.1 R-E 区域

R-E（Rate-Energy）区域是 SWIPT 系统设计的核心工具。它定义了在给定系统参数下，所有可实现的 (R, Q) 对的集合。R-E 区域的边界（帕累托前沿）代表了信息速率和收集能量的最优折衷。

对 MISO SWIPT（多天线发送、单天线接收）系统，波束赋形设计直接影响 R-E 区域的形状：

- **信息波束赋形**：最大化信号方向的功率 → 最大化 R，但能量收集方向功率弱
- **能量波束赋形**：最大化接收端总功率 → 最大化 Q，但信号方向性差
- **联合波束赋形**：在 R 和 Q 之间做 tradeoff

### 3.2 非线性能量收集模型

早期 SWIPT 研究假设 RF-DC 转换效率是常数（线性模型）。但实际的整流器是高度非线性的：

| 输入功率 (dBm) | 线性模型效率 | 实际效率 | 差距 |
|---------------|------------|---------|------|
| -30 | 40% | 2% | 20× |
| -20 | 40% | 15% | 2.7× |
| -10 | 40% | 35% | 1.1× |
| 0 | 40% | 45% | 0.9× |
| +10 | 40% | 50% | 0.8× |
| +20 | 40% | 30%（饱和） | 1.3× |

关键观察：在低输入功率（< -20 dBm）时，实际效率远低于线性模型的预测。而 IoT 设备距离基站通常较远，接收功率往往在 -30 到 -10 dBm 范围——恰好是非线性效应最显著的区域。

使用非线性模型后，很多基于线性模型得出的"最优策略"不再最优。2024 年的研究表明，考虑非线性后，多音波形的优势更加显著（因为高 PAPR 信号能更好地利用整流器的非线性区间）。

---

## 4. 中继辅助 SWIPT

### 4.1 为什么需要中继

SWIPT 的致命弱点是距离。射频信号的功率衰减遵循反平方律——距离翻倍，功率降为 1/4。在 1 GHz 频段，基站发射 1W 功率：

| 距离 | 接收功率 | 可收集直流功率（η=30%）| 足够供电？|
|------|---------|---------------------|---------|
| 1 m | -10 dBm | 30 μW | IoT 传感器可用 |
| 10 m | -30 dBm | 0.3 μW | 勉强维持待机 |
| 100 m | -50 dBm | 3 nW | 完全不够 |
| 1 km | -70 dBm | 30 pW | 不可行 |

10 米以上的 SWIPT 能量收集基本不可行。中继节点可以解决这个问题：在源和目的之间放置一个中继，中继自己从源的信号中收集能量，用这些能量转发信息给远处的目的节点。

### 4.2 中继 SWIPT 协议

**TS 中继协议**（时间切换）：

```
阶段 1：源 → 中继（中继做能量收集，时长 αT）
阶段 2：源 → 中继（中继做信息接收，时长 (1-α)T/2）
阶段 3：中继 → 目的（中继用收集的能量转发，时长 (1-α)T/2）
```

**PS 中继协议**（功率分割）：

```
阶段 1：源 → 中继（中继同时做能量收集和信息接收，时长 T/2）
         - ρ 比例功率给信息解码
         - (1-ρ) 比例功率给能量收集
阶段 2：中继 → 目的（中继转发，时长 T/2）
```

中继的发射功率受限于收集到的能量：$P_{relay} = E_{harvested} / (T_{transmit})$。这形成了一个闭环约束——中继收集的能量越多（α 或 1-ρ 越大），可用的转发功率越高，但留给信息传输的时间或功率就越少。

---

## 5. NOMA-SWIPT：非正交多址与能量收集

### 5.1 NOMA 与 SWIPT 的结合

NOMA（Non-Orthogonal Multiple Access）允许多个用户在同一时频资源上通过功率域复用共享信道。强用户（信道好、距离近）分配较少功率，弱用户（信道差、距离远）分配较多功率。强用户先用 SIC 去掉弱用户的信号后解码自己的信号。

在 SWIPT 场景中，NOMA 有天然的协同效应：

- 近用户信道好 → 可以少分一些功率给信息、多做能量收集
- 远用户信道差 → 基站给更多功率，远用户不做能量收集（信号太弱）

```python
def noma_swipt_design(P_total, h_near, h_far, noise, rho_near=0.5):
    """NOMA-SWIPT 系统设计
    
    下行 NOMA：基站同时服务近用户（做 SWIPT）和远用户（只做信息接收）
    近用户用功率分割，远用户只解码信息。
    """
    # NOMA 功率分配（远用户分更多功率）
    alpha_far = 0.8   # 80% 功率给远用户
    alpha_near = 0.2   # 20% 功率给近用户
    
    P_far = alpha_far * P_total
    P_near = alpha_near * P_total
    
    # 近用户：功率分割
    # 信息解码支路（SIC 先去掉远用户信号）
    P_near_info = rho_near * abs(h_near)**2 * P_near
    P_near_interf = rho_near * abs(h_near)**2 * P_far  # SIC 前的干扰
    
    # 近用户先解远用户信号（SIC 第一步）
    sinr_far_at_near = (abs(h_near)**2 * P_far) / \
                       (abs(h_near)**2 * P_near + noise)
    # SIC 成功后解自己的信号
    sinr_near = (rho_near * abs(h_near)**2 * P_near) / \
                (rho_near * noise + 1e-9)
    
    # 远用户：直接解码（把近用户信号当干扰）
    sinr_far = (abs(h_far)**2 * P_far) / \
               (abs(h_far)**2 * P_near + noise)
    
    # 近用户能量收集
    P_harvested = 0.4 * (1 - rho_near) * abs(h_near)**2 * P_total
    
    R_near = np.log2(1 + sinr_near)
    R_far = np.log2(1 + sinr_far)
    
    return R_near, R_far, P_harvested
```

---

## 6. 实际硬件：Powercast P2110 案例

### 6.1 系统概述

Powercast P2110-915 是目前市场上最成熟的 RF 能量收集产品之一，工作在 915 MHz ISM 频段。它是理解 SWIPT 实际工程约束的最佳案例。

| 参数 | P2110-915 规格 |
|------|---------------|
| 工作频率 | 902-928 MHz |
| 输入功率范围 | -12 dBm 至 +20 dBm |
| RF-DC 转换效率 | 75%（@ 0 dBm）/ 50%（@ -10 dBm）|
| 输出电压 | 可配置：1.2V / 1.8V / 2.5V / 3.3V / 4.2V |
| 最大输出电流 | ~50 mA（@ 0 dBm 输入） |
| 冷启动功率 | -5 dBm (约 0.3 mW) |
| 封装尺寸 | 20 × 25 mm |
| 配套发射器 | TX91501-3W（3W EIRP） |

### 6.2 实际覆盖测试数据

Powercast 官方和第三方测试数据（TX91501 3W EIRP 发射器）：

| 距离 | 接收功率 | DC 输出功率 | 可供电设备类型 |
|------|---------|-----------|-------------|
| 0.5 m | +5 dBm | ~2.4 mW | 低功耗 MCU 持续运行 |
| 1 m | -1 dBm | ~0.6 mW | 传感器周期采样（10s 周期）|
| 3 m | -10 dBm | ~50 μW | 传感器分钟级采样 |
| 5 m | -15 dBm | ~10 μW | 仅够维持 RTC + 超低功耗待机 |
| 10 m | -22 dBm | ~1 μW | 需要超级电容蓄能 + 突发工作 |

### 6.3 典型应用架构

```
[Powercast TX91501]     [IoT 传感器节点]
  3W EIRP 发射器          ┌─────────────────────┐
  915 MHz CW 信号   →→→   │  P2110 整流器模块     │
                          │    ↓ DC 输出          │
                          │  超级电容 (100mF)     │
                          │    ↓                  │
                          │  电压调节器 → MCU      │
                          │              ↓        │
                          │         温湿度传感器    │
                          │              ↓        │
                          │    低功耗无线发射       │
                          │   (BLE/LoRa/Zigbee)  │
                          └─────────────────────┘

工作模式：
1. 持续收集 RF 能量 → 充超级电容
2. 电容电压达到阈值 → MCU 上电
3. 读取传感器 → 发送数据（BLE/LoRa）
4. MCU 关机 → 继续充电
5. 循环...
```

注意：P2110 做的是**纯能量收集**（WPT），不是 SWIPT。完整的 SWIPT 商用产品在 2025 年仍未面世——这反映了从同一信号中同时提取信息和能量的工程难度。

---

## 7. 实践建议

### 7.1 初学者入门路径

**第一步：理解整流器原理**（1-2 天）。用 LTspice 仿真一个单级 Dickson 电荷泵整流器（1 个二极管 + 1 个电容），观察不同输入功率下的 RF-DC 转换效率曲线。理解为什么低功率时效率骤降（二极管阈值电压问题）。

**第二步：信息论仿真**（3 天）。用 Python 画出不同系统配置下的 R-E 区域。对比 TS 和 PS 架构在不同信道条件下的性能。

```python
# R-E 区域计算：对比 TS 和 PS 架构
import numpy as np

def ts_rate_energy(P_rx, N0, BW, alpha_values):
    """时间切换架构的 R-E 对"""
    results = []
    for alpha in alpha_values:
        E = 0.4 * alpha * P_rx           # 能量收集
        R = (1-alpha) * BW * np.log2(1 + P_rx/N0)  # 信息速率
        results.append((R, E))
    return results

def ps_rate_energy(P_rx, N0, BW, rho_values):
    """功率分割架构的 R-E 对"""
    results = []
    for rho in rho_values:
        E = 0.4 * (1-rho) * P_rx
        R = BW * np.log2(1 + rho*P_rx / (rho*N0 + 1e-10))
        results.append((R, E))
    return results
```

**第三步：硬件实验**（1-2 周）。购买 Powercast P2110 开发套件（约 $300），搭建一个最简的 RF 能量收集系统。测量不同距离下的输出功率，与理论计算对比。

### 7.2 具体调优建议

- **整流器级数**：单级 Dickson 适合高输入功率（> -5 dBm），多级（3-5 级）适合低功率（< -15 dBm）。级数越多，灵敏度越高但效率峰值越低
- **匹配网络**：整流器的输入阻抗随功率变化很大。使用自适应匹配网络（可变电容）可以在宽功率范围保持高效率
- **波形设计**：对于 SWIPT 的能量传输阶段，使用多音信号或 OFDM 信号（高 PAPR）比纯连续波的收集效率高 20-40%
- **超级电容选型**：100 mF 的超级电容可以存储约 0.5 mJ（@3.3V）。对于 10 mW 峰值功耗的 BLE 发送，可以支撑约 50 ms 的发送时间——足够发一个短数据包
- **安全考虑**：RF 能量发射功率受 FCC/ETSI 限制（915 MHz ISM 频段最大 1W EIRP 或 4W EIRP 视扩频方式）。实际部署需要确保符合 SAR（特定吸收率）安全标准

---

## 参考文献

1. R. Zhang and C. K. Ho, "MIMO broadcasting for simultaneous wireless information and power transfer," *IEEE Trans. Wireless Communications*, vol. 12, no. 5, pp. 1989-2001, 2013.
2. L. R. Varshney, "Transporting information and energy simultaneously," *IEEE Int. Symposium on Information Theory*, pp. 1612-1616, 2008.
3. X. Zhou et al., "Wireless information and power transfer: Architecture design and rate-energy tradeoff," *IEEE Trans. Communications*, vol. 61, no. 11, pp. 4754-4767, 2013.
4. A. A. Nasir et al., "Relaying protocols for wireless energy harvesting and information processing," *IEEE Trans. Wireless Communications*, vol. 12, no. 7, pp. 3622-3636, 2013.
5. Y. Liu et al., "Cooperative SWIPT NOMA," *IEEE Trans. Communications*, vol. 65, no. 5, pp. 2159-2171, 2017.
6. B. Clerckx and E. Bayguzina, "Waveform design for wireless power transfer," *IEEE Trans. Signal Processing*, vol. 64, no. 23, pp. 6313-6328, 2016.
7. Powercast Corporation, "P2110-915 Powerharvester Datasheet," Rev. B, 2023.
8. E. Boshkovska et al., "Practical non-linear energy harvesting model and resource allocation for SWIPT systems," *IEEE Communications Letters*, vol. 19, no. 12, pp. 2082-2085, 2015.
9. I. Krikidis et al., "Simultaneous wireless information and power transfer in modern communication systems," *IEEE Communications Magazine*, vol. 52, no. 11, pp. 104-110, 2014.
10. D. W. K. Ng et al., "Wireless information and power transfer: Multi-antenna techniques," *IEEE Communications Magazine*, vol. 52, no. 4, pp. 104-110, 2014.
