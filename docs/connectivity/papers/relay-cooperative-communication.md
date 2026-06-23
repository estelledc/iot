# 中继协作通信：IoT 网络的"接力赛跑"

> **难度**：🟡 中级 | **领域**：协作通信、分集技术、IoT 覆盖延伸 | **阅读时间**：约 21 分钟

## 日常类比

想象你在一个大型商场里，手机信号从一楼大门口的基站根本穿不到地下二层的停车场。但如果在每层楼梯口放一个"信号中转站"，信号就能像接力赛跑一样，从一楼传到负一楼再到负二楼。

中继通信就是这个原理：当源节点（Source）和目的节点（Destination）之间直达路径太差时，引入一个或多个中继节点（Relay）做"信号接力"。更精妙的是"协作通信"——多个节点不只是简单转发，而是互相配合，形成虚拟的多天线系统，获得空间分集增益。

对 IoT 来说，大量传感器部署在信号难以直达的位置（地下管道、密集建筑深处、农田远端）。中继协作技术用低成本方式扩展覆盖，不需要额外部署昂贵的基站。

## 1. 两种基本中继协议

### 1.1 放大转发（Amplify-and-Forward, AF）

中继节点收到信号后直接放大并转发，不做解码。

```
时隙 1: S --> R:  y_r = h_sr * x + n_r
时隙 2: R --> D:  y_d = h_rd * (G * y_r) + n_d
                     = h_rd * G * h_sr * x + h_rd * G * n_r + n_d
                       \_________信号________/   \____噪声放大____/
```

其中放大增益 G 通常设为：

```
G = sqrt(P_r / (|h_sr|^2 * P_s + sigma^2))  (功率约束)
```

优点：中继复杂度极低（模拟放大即可），延迟小。缺点：噪声也被放大了。

### 1.2 解码转发（Decode-and-Forward, DF）

中继节点先完整解码收到的信号，再重新编码发送。

```
时隙 1: S --> R:  y_r = h_sr * x + n_r  --> R 解码得到 x_hat
时隙 2: R --> D:  y_d = h_rd * x_hat + n_d  (重新编码发送)
```

优点：不传播噪声。缺点：中继解码失败时会传播错误；复杂度高；引入解码延迟。

### 1.3 性能对比

| 维度 | AF | DF |
|------|-----|-----|
| 中继复杂度 | 极低 | 高（需完整收发链） |
| 噪声处理 | 放大传播 | 消除（但可能引入解码错误） |
| 延迟 | 低 | 高（解码+重编码） |
| 分集阶数 | 2（单中继） | 2（单中继） |
| 适用场景 | S-R 链路好 | S-R 链路 SNR 高于解码门限 |
| IoT 适用性 | 低功耗中继 | 有算力的网关级中继 |

### 1.4 Python 仿真：AF vs DF 中断概率

```python
import numpy as np

def af_outage_prob(snr_sr, snr_rd, rate_threshold):
    """
    AF 中继中断概率 (瑞利衰落)
    基于等效端到端 SNR: gamma_eq = (gamma_sr * gamma_rd) / (gamma_sr + gamma_rd + 1)
    """
    gamma_th = 2**(2*rate_threshold) - 1  # 两时隙, 速率减半
    # 蒙特卡洛仿真
    n_trials = 100000
    h_sr = np.random.exponential(snr_sr, n_trials)  # |h_sr|^2 * P_s/N0
    h_rd = np.random.exponential(snr_rd, n_trials)  # |h_rd|^2 * P_r/N0

    # AF 等效 SNR (上界近似)
    gamma_eq = (h_sr * h_rd) / (h_sr + h_rd + 1)
    outage = np.mean(gamma_eq < gamma_th)
    return outage

def df_outage_prob(snr_sr, snr_rd, rate_threshold):
    """
    DF 中继中断概率
    中断 = S-R 链路中断 OR R-D 链路中断 (取瓶颈)
    """
    gamma_th = 2**(2*rate_threshold) - 1
    n_trials = 100000
    h_sr = np.random.exponential(snr_sr, n_trials)
    h_rd = np.random.exponential(snr_rd, n_trials)

    # DF: 等效 SNR = min(gamma_sr, gamma_rd)
    gamma_eq = np.minimum(h_sr, h_rd)
    outage = np.mean(gamma_eq < gamma_th)
    return outage

# 对比不同 SNR 下的性能
print("平均 SNR(dB) | AF中断概率  | DF中断概率  | 直传中断概率")
print("-" * 55)
for snr_db in [5, 10, 15, 20, 25]:
    snr_linear = 10**(snr_db/10)
    af_out = af_outage_prob(snr_linear, snr_linear, rate_threshold=1.0)
    df_out = df_outage_prob(snr_linear, snr_linear, rate_threshold=1.0)
    # 直传 (无中继, 单时隙)
    gamma_th_direct = 2**1.0 - 1  # 单时隙不需翻倍
    direct_out = 1 - np.exp(-gamma_th_direct / snr_linear)
    print(f"    {snr_db:2d}      | {af_out:.4f}    | {df_out:.4f}    | {direct_out:.4f}")
```

## 2. 协作分集

### 2.1 虚拟 MIMO 概念

单天线 IoT 设备无法获得 MIMO 分集增益。但如果多个单天线设备互相协作，就能形成"虚拟多天线阵列"。

三节点协作模型：

```
时隙 1: S 广播 --> R 和 D 都收到
时隙 2: R 转发 --> D 收到 (额外独立路径)

D 端有两个独立的信号副本:
  - 直达路径: y_sd = h_sd * x + n_sd   (时隙 1)
  - 中继路径: y_rd = h_rd * f(y_sr) + n_rd  (时隙 2)

MRC 合并: 获得 2 阶分集 (分集阶数 = 独立路径数)
```

### 2.2 分集增益与编码增益

分集阶数 d 决定了中断概率曲线在高 SNR 时的斜率：

```
P_out 约等于 (c / SNR)^d   (高 SNR 近似)
```

| 方案 | 分集阶数 | 说明 |
|------|---------|------|
| 无中继直传 | 1 | 单路径 |
| 单中继 AF/DF | 2 | S-D + S-R-D 两条路径 |
| 选择式中继 (K 个候选) | K+1 | 选最好的一个中继 |
| 全协作 (K 个中继) | K+1 | 所有中继都转发 |

### 2.3 Alamouti 式分布式空时编码

两个中继模拟 2x1 Alamouti STBC：

```
        时隙 1    时隙 2
中继 1:   x1       -x2*
中继 2:   x2        x1*

目的节点收到:
y1 = h1*x1 + h2*x2 + n1
y2 = -h1*x2* + h2*x1* + n2

等效为 2x1 MIMO, 获得完整 2 阶发射分集
```

## 3. 中继选择算法

### 3.1 最优中继选择

在多中继网络中，选择哪个中继转发对性能影响巨大。

最大最小（Max-Min）准则：

```
R* = arg max_k { min(gamma_sk, gamma_kd) }
选择瓶颈链路最好的中继
```

最大调和均值准则：

```
R* = arg max_k { (gamma_sk * gamma_kd) / (gamma_sk + gamma_kd) }
等效 AF 端到端 SNR 最大化
```

```python
import numpy as np

class RelaySelector:
    """中继选择算法实现"""

    def __init__(self, n_relays):
        self.n_relays = n_relays

    def max_min_selection(self, snr_sr: np.ndarray, snr_rd: np.ndarray) -> int:
        """
        最大最小准则: 选瓶颈链路最好的中继
        snr_sr: shape (n_relays,) - 源到各中继的 SNR
        snr_rd: shape (n_relays,) - 各中继到目的的 SNR
        """
        bottleneck = np.minimum(snr_sr, snr_rd)
        return int(np.argmax(bottleneck))

    def max_harmonic_selection(self, snr_sr: np.ndarray, snr_rd: np.ndarray) -> int:
        """调和均值准则 (AF 最优)"""
        harmonic = (snr_sr * snr_rd) / (snr_sr + snr_rd + 1)
        return int(np.argmax(harmonic))

    def reactive_selection(self, snr_sr: np.ndarray, snr_rd: np.ndarray,
                          threshold: float) -> int:
        """
        反应式选择: 只考虑 S-R 链路 SNR 超过门限的中继
        减少 CSI 获取开销 (只需 R-D 的部分 CSI)
        """
        candidates = np.where(snr_sr > threshold)[0]
        if len(candidates) == 0:
            return -1  # 无合格中继, 直传
        return candidates[np.argmax(snr_rd[candidates])]

# 仿真示例
selector = RelaySelector(n_relays=5)
np.random.seed(42)
snr_sr = np.random.exponential(15, 5)  # 5 个中继的 S-R SNR
snr_rd = np.random.exponential(12, 5)  # 5 个中继的 R-D SNR

best_relay = selector.max_min_selection(snr_sr, snr_rd)
print(f"最优中继 (Max-Min): Relay {best_relay}")
print(f"  S-R SNR: {snr_sr[best_relay]:.1f}, R-D SNR: {snr_rd[best_relay]:.1f}")
print(f"  瓶颈 SNR: {min(snr_sr[best_relay], snr_rd[best_relay]):.1f}")
```

### 3.2 分布式中继选择（定时器法）

集中式选择需要全局 CSI，开销大。分布式方法让每个中继自行决定：

```
每个中继 k 设置定时器: T_k = T_max / f(gamma_k)
gamma_k 越大, T_k 越短, 越早超时

第一个超时的中继发送 FLAG 信号
其他中继听到 FLAG 后保持沉默

--> 无需中央协调, 自然选出最佳中继
```

## 4. 全双工中继

### 4.1 半双工 vs 全双工

传统中继是半双工（HD）：收和发不能同时进行，占用两个时隙，频谱效率损失 50%。

全双工（FD）中继同时收发，但面临自干扰（Self-Interference, SI）问题：

```
FD 中继接收信号: y_r = h_sr * x_s + h_SI * x_r + n_r
                      \__期望信号__/  \___自干扰___/

自干扰 h_SI * x_r 可能比期望信号强 80-120 dB!
```

### 4.2 自干扰消除技术

| 级别 | 技术 | 消除量 | 原理 |
|------|------|--------|------|
| 传播域 | 天线隔离 | 40-60 dB | 物理距离 + 方向性 |
| 模拟域 | 射频对消 | 30-50 dB | 参考信号反相叠加 |
| 数字域 | 数字对消 | 20-40 dB | 估计 SI 信道并减去 |
| 总计 | 级联 | 90-130 dB | 三级联合 |

当自干扰消除足够（残余 SI < 噪声底），FD 中继的频谱效率接近直传的 2 倍（消除了半双工的 50% 损失）。

### 4.3 FD 中继在 IoT 中的应用

低功率 IoT 场景下，设备发射功率小（0-14 dBm），自干扰相对容易处理。2024 年已有商用 FD 中继芯片（如 Kumu Networks 的方案）支持 sub-6 GHz 频段。

## 5. 缓冲辅助中继（Buffer-Aided Relay）

### 5.1 动机

传统中继在时隙 1 接收、时隙 2 立即转发。但如果时隙 2 的 R-D 信道恰好很差呢？缓冲辅助中继有"存储"能力——在 R-D 信道差时暂存数据，等信道好时再发。

### 5.2 自适应链路选择

```python
class BufferAidedRelay:
    """缓冲辅助中继: 自适应链路选择"""

    def __init__(self, buffer_size=10):
        self.buffer = []
        self.buffer_size = buffer_size

    def decide_link(self, snr_sr: float, snr_rd: float) -> str:
        """
        决定当前时隙使用哪条链路
        返回: "sr" (源->中继), "rd" (中继->目的), "idle"
        """
        buffer_level = len(self.buffer)

        # 缓冲区满: 必须发送
        if buffer_level >= self.buffer_size:
            return "rd"
        # 缓冲区空: 必须接收
        if buffer_level == 0:
            return "sr"

        # 自适应选择: 选择瞬时信道更好的链路
        # Max-Link 策略
        if snr_sr > snr_rd:
            return "sr"  # S-R 更好, 接收存入缓冲
        else:
            return "rd"  # R-D 更好, 从缓冲取出发送

    def receive(self, data):
        """从源接收数据存入缓冲"""
        if len(self.buffer) < self.buffer_size:
            self.buffer.append(data)

    def transmit(self):
        """从缓冲取数据发送到目的"""
        if self.buffer:
            return self.buffer.pop(0)
        return None

# 仿真: 缓冲辅助 vs 传统交替
relay = BufferAidedRelay(buffer_size=8)
np.random.seed(123)
throughput_buffer = 0
throughput_fixed = 0

for slot in range(1000):
    snr_sr = np.random.exponential(10)
    snr_rd = np.random.exponential(10)

    # 缓冲辅助: 自适应选择
    link = relay.decide_link(snr_sr, snr_rd)
    if link == "sr":
        rate = np.log2(1 + snr_sr)
        relay.receive(rate)
    elif link == "rd":
        rate = np.log2(1 + snr_rd)
        throughput_buffer += min(rate, relay.transmit() or 0)

    # 传统交替: 奇数时隙收, 偶数时隙发
    if slot % 2 == 0:
        fixed_rate_sr = np.log2(1 + snr_sr)
    else:
        fixed_rate_rd = np.log2(1 + snr_rd)
        throughput_fixed += min(fixed_rate_sr, fixed_rate_rd)

print(f"缓冲辅助吞吐量: {throughput_buffer:.0f}")
print(f"传统交替吞吐量: {throughput_fixed:.0f}")
print(f"增益: {(throughput_buffer/throughput_fixed - 1)*100:.1f}%")
# 典型增益: 20-50%
```

### 5.3 缓冲带来的代价

缓冲辅助中继提升吞吐量，但引入额外延迟。对于实时性要求高的应用（如工业控制），需要在吞吐量增益和延迟约束之间折中。典型方案是设置缓冲上限 + 最大等待时间。

## 6. 能量收集中继与无人机中继

### 6.1 无线能量收集中继（SWIPT Relay）

中继节点从接收信号中同时获取信息和能量（Simultaneous Wireless Information and Power Transfer）：

```
接收信号分流:
  - rho 比例用于信息解码
  - (1-rho) 比例用于能量收集

收集能量: E_h = eta * (1-rho) * |h_sr|^2 * P_s * T
其中 eta 是能量转换效率 (典型 0.3-0.7)
```

时间切换（TS）方案：前 alpha*T 时间收集能量，后 (1-alpha)*T 时间转发信息。适合能量需求大的场景。

功率分流（PS）方案：同一时刻将接收功率按比例 rho 分流。适合延迟敏感场景。

### 6.2 UAV 中继

无人机作为空中中继节点，优势是视距（LoS）概率高、位置可灵活调整。

```python
import numpy as np

def uav_relay_placement(src_pos, dst_pos, altitude=100):
    """
    UAV 中继最优放置 (简化2D)
    假设: 空对地信道以 LoS 为主, 路径损耗与距离平方成正比
    最优位置: S-R 和 R-D 链路几何均衡点
    """
    # 对于对称信道, 最优位置在 S-D 连线中点
    # 对于非对称 (如 S 在室内, D 是基站), 偏向弱链路侧
    mid_x = (src_pos[0] + dst_pos[0]) / 2
    mid_y = (src_pos[1] + dst_pos[1]) / 2

    # UAV 高度优化: 过高增加路径损耗, 过低降低 LoS 概率
    # 经验公式 (ITU-R 城市环境)
    d_2d = np.sqrt((src_pos[0]-dst_pos[0])**2 + (src_pos[1]-dst_pos[1])**2)
    optimal_alt = 0.3 * d_2d  # 经验值: 高度约为水平距离的 30%
    optimal_alt = np.clip(optimal_alt, 50, 300)  # 限制在 50-300m

    return (mid_x, mid_y, optimal_alt)

# 示例: 地面传感器群 -> UAV 中继 -> 远端基站
sensor_cluster = (0, 0)       # 传感器群中心
base_station = (2000, 0)      # 基站距离 2km
uav_pos = uav_relay_placement(sensor_cluster, base_station)
print(f"UAV 最优位置: x={uav_pos[0]:.0f}m, y={uav_pos[1]:.0f}m, 高度={uav_pos[2]:.0f}m")

# 路径损耗计算
def path_loss_a2g(d_3d, f_mhz=900, env="urban"):
    """空对地路径损耗 (简化 LoS 模型)"""
    fspl = 20*np.log10(d_3d/1000) + 20*np.log10(f_mhz) + 32.44
    # LoS 额外损耗较小 (1-3 dB)
    return fspl + 2.0  # 加 2dB 余量

d_sr = np.sqrt(uav_pos[0]**2 + uav_pos[2]**2)
d_rd = np.sqrt((uav_pos[0]-2000)**2 + uav_pos[2]**2)
pl_sr = path_loss_a2g(d_sr)
pl_rd = path_loss_a2g(d_rd)
print(f"S-R 路径损耗: {pl_sr:.1f} dB (距离 {d_sr:.0f}m)")
print(f"R-D 路径损耗: {pl_rd:.1f} dB (距离 {d_rd:.0f}m)")
```

### 6.3 UAV 轨迹优化

固定位置 UAV 中继是起点，更高级的做法是优化 UAV 飞行轨迹。UAV 在飞行中持续为地面设备提供中继服务，通过调整路径以接近不同设备。2024-2025 年研究热点包括基于 DRL 的在线轨迹优化和多 UAV 协作中继。

## 7. 实践建议

### 7.1 初学者入门路径

1. 理论基础（1-2 周）：学习分集合并技术（MRC/EGC/SC）、瑞利/莱斯衰落模型
2. 仿真入门（2 周）：用 Python 实现 AF/DF 单中继 BER 仿真，画中断概率曲线
3. 中继选择（1 周）：实现多中继选择算法，对比集中式和分布式方案
4. 进阶主题（按兴趣选）：全双工中继（需了解自干扰消除）、缓冲辅助中继、SWIPT
5. 实际应用：在 LoRaWAN 中配置多跳中继（LoRa Alliance TS011 中继规范）

### 7.2 具体调优建议

中继位置规划方面，对称信道下中继放在源-目的中点最优。非对称场景（一侧有遮挡）中继偏向弱链路侧。实际部署用射线追踪工具（如 Wireless InSite）做覆盖仿真。

协议选择方面，S-R 链路 SNR > 15 dB：AF 和 DF 性能接近，选 AF（简单）。S-R 链路 SNR 在 5-15 dB：DF 优于 AF（避免噪声放大）。S-R 链路 SNR < 5 dB：DF 解码可能失败，考虑压缩转发（CF）。多中继可用时，先做中继选择再决定 AF/DF。

IoT 特别考量方面，LoRaWAN 中继（TS011 规范，2023 年发布）支持 Class A 设备通过 Class C 中继接入网络。BLE Mesh 每一跳引入约 10ms 延迟，7 跳约 70ms，适合非实时应用。Zigbee 网状网络最多支持 30 跳，但实际建议不超过 5-7 跳（避免累积延迟和路由开销）。

链路预算核算方面，中继引入的增益约等于将一条长链路拆成两条短链路的路径损耗差。例如：1km 直传在 868 MHz 路径损耗约 90 dB；拆成 2 个 500m 跳，每跳约 84 dB——节省 6 dB，但需要额外一个时隙（半双工损失 3 dB），净增益约 3 dB。

## 参考文献

1. Laneman, J. N., et al., "Cooperative Diversity in Wireless Networks: Efficient Protocols and Outage Behavior," IEEE TIT, vol. 50, no. 12, 2004.
2. Nosratinia, A., et al., "Cooperative Communication in Wireless Networks," IEEE Communications Magazine, vol. 42, no. 10, 2004.
3. Bletsas, A., et al., "A Simple Cooperative Diversity Method Based on Network Path Selection," IEEE JSAC, vol. 24, no. 3, 2006.
4. Zlatanov, N., et al., "Buffer-Aided Cooperative Communications: Opportunities and Challenges," IEEE Communications Magazine, vol. 52, no. 4, 2014.
5. Zeng, Y., et al., "Wireless Communications with Unmanned Aerial Vehicles: Opportunities and Challenges," IEEE Communications Magazine, vol. 54, no. 5, 2016.
6. Sabharwal, A., et al., "In-Band Full-Duplex Wireless: Challenges and Opportunities," IEEE JSAC, vol. 32, no. 9, 2014.
7. LoRa Alliance, "TS011: LoRaWAN Relay Specification v1.0," 2023.
8. Liu, Y., et al., "Cooperative Non-Orthogonal Multiple Access with Simultaneous Wireless Information and Power Transfer," IEEE JSAC, vol. 34, 2016.
9. Wu, Q., et al., "Joint Trajectory and Communication Design for Multi-UAV Enabled Wireless Networks," IEEE TWC, vol. 17, no. 3, 2018.
10. Chen, X., et al., "Full-Duplex Relay for IoT Networks: Design, Analysis, and Prototype," IEEE IoT Journal, vol. 11, no. 5, 2024.
