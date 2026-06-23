# D2D 设备直连通信

> **难度**：🟡 中级 | **领域**：蜂窝通信、近距通信 | **阅读时间**：约 19 分钟

---

## 日常类比

你和同事坐在同一间办公室里，要传一份文件。正常流程是：你把文件上传到公司服务器（基站），服务器再下发给你的同事。文件走了"你→服务器→同事"这条路，明明你俩面对面坐着，文件却跑了一个大圈子。

D2D 通信就是让你直接把文件传给对面的同事——不经过服务器。距离近、速度快、不占用服务器带宽。这就是"设备直连"的核心思想：当两个设备距离足够近时，让它们直接通信，不再绕路经过基站。

在 IoT 场景中，D2D 的价值更加突出。想象一个智慧工厂里有几百个传感器，如果每个传感器的数据都要先上传到基站再转发给旁边的控制器，基站就成了瓶颈。让传感器直接和旁边的控制器对话，不仅延迟更低（< 1 ms vs 基站中转的 5-10 ms），还释放了基站的容量给真正需要远距离通信的设备。

V2V（车对车通信）是 D2D 最成功的应用。两辆相邻的车需要实时交换位置和速度信息，等数据绕到基站再回来可能要 20 ms——高速公路上 20 ms 意味着车又前进了半米。D2D 直连可以把延迟压到 3 ms 以内。

---

## 1. D2D 通信模式

### 1.1 频谱使用分类

D2D 通信首先要解决"用什么频段"的问题。根据频谱使用方式分为两大类：

| 类型 | 频谱来源 | 优点 | 缺点 | 典型技术 |
|------|---------|------|------|---------|
| 带内下行 (In-band Underlay) | 复用蜂窝下行频谱 | 不需要额外频谱 | 和蜂窝用户互相干扰 | LTE-D |
| 带内覆盖 (In-band Overlay) | 从蜂窝频谱中划出专用资源 | 无跨模式干扰 | 减少蜂窝可用资源 | 5G Sidelink |
| 带外 (Out-band) | 使用免授权频段 | 不影响蜂窝系统 | 频段拥挤、不可控 | WiFi Direct / BLE |

**带内 Underlay** 是最有挑战性也最有吸引力的方案：D2D 对和蜂窝用户在同一频率上同时工作，靠空间隔离和功率控制避免干扰。好处是频谱利用率最高；代价是干扰管理极其复杂。

**带内 Overlay** 是 5G NR Sidelink 的实际选择：从蜂窝频谱中预留一部分资源专门给 D2D/V2X 使用。简单可控，但浪费了一些蜂窝容量。

### 1.2 通信模式选择

当两个设备要通信时，网络需要决定走哪条路径：

```python
class D2DModeSelector:
    """D2D 模式选择器：决定两个设备是走蜂窝中转还是直连"""
    
    def __init__(self, d2d_max_distance=50, sinr_threshold_db=5):
        self.d2d_max_distance = d2d_max_distance  # D2D 最大通信距离 (m)
        self.sinr_threshold = sinr_threshold_db    # D2D 链路最低 SINR (dB)
    
    def select_mode(self, device_a, device_b, bs_position, 
                    cellular_load, qos_requirement):
        """
        返回: 'cellular' (蜂窝中转) 或 'd2d' (直连)
        """
        # 1. 距离检查
        d_ab = self._distance(device_a, device_b)
        if d_ab > self.d2d_max_distance:
            return 'cellular'  # 太远，D2D 不可行
        
        # 2. D2D 链路质量估计
        d2d_sinr = self._estimate_d2d_sinr(device_a, device_b)
        if d2d_sinr < self.sinr_threshold:
            return 'cellular'  # D2D 信道太差
        
        # 3. QoS 检查
        if qos_requirement.get('reliability') == 'ultra_high':
            # 超高可靠性业务（如安全类 V2X）优先走蜂窝（有基站协调）
            if cellular_load < 0.8:
                return 'cellular'
        
        # 4. 蜂窝负载检查
        if cellular_load > 0.7:
            return 'd2d'  # 蜂窝拥挤，卸载到 D2D
        
        # 5. 能效比较
        d2d_energy = self._d2d_energy(d_ab)
        cellular_energy = self._cellular_energy(device_a, device_b, bs_position)
        
        return 'd2d' if d2d_energy < cellular_energy else 'cellular'
    
    def _distance(self, a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2)**0.5
    
    def _estimate_d2d_sinr(self, a, b):
        d = self._distance(a, b)
        path_loss = 40 + 30 * np.log10(d)  # 简化室内模型
        tx_power = 10  # dBm（D2D 低功率发射）
        noise = -104   # dBm（10 MHz 带宽热噪声）
        return tx_power - path_loss - noise
    
    def _d2d_energy(self, distance):
        return 0.001 * distance**2  # 简化能量模型
    
    def _cellular_energy(self, a, b, bs):
        d_a_bs = self._distance(a, bs)
        d_b_bs = self._distance(b, bs)
        return 0.001 * (d_a_bs**2 + d_b_bs**2)
```

---

## 2. 邻近发现

### 2.1 怎么知道身边有谁

D2D 通信的前提是设备先发现彼此。邻近发现（Proximity Discovery）分为两种模式：

**网络辅助发现**：基站知道所有设备的位置（通过测量报告、定位信息），当检测到两个设备距离很近时，通知它们可以建立 D2D 连接。优点是高效可控，缺点是设备必须在蜂窝覆盖范围内。

**直接发现**：设备自己周期性广播发现信号（类似 BLE 的 advertising），附近的设备收到后响应。不依赖基站，但会消耗额外的能量和频谱资源。

3GPP 定义了两种发现模型：

| 模型 | 描述 | 场景 |
|------|------|------|
| Model A (I am here) | 设备主动广播自己的存在 | 社交网络、广告推送 |
| Model B (Who is there?) | 设备查询附近有没有特定的对象 | V2X 安全消息、IoT 对等组网 |

### 2.2 发现信号设计

发现信号需要在低功耗和快速发现之间折衷：

```python
class ProximityDiscovery:
    """3GPP ProSe 风格的邻近发现协议"""
    
    DISCOVERY_PERIOD_MS = 320     # 发现周期（ms）
    DISCOVERY_SLOTS = 44          # 每周期的发现时隙数
    TX_POWER_DBM = 0              # 发现信号发射功率
    
    def __init__(self, device_id, group_ids=None):
        self.device_id = device_id
        self.group_ids = group_ids or []
        self.discovered_peers = {}
    
    def generate_discovery_message(self, model='A'):
        """生成发现消息"""
        if model == 'A':
            # Model A：广播 "我在这里"
            return {
                'type': 'announcement',
                'device_id': self.device_id,
                'groups': self.group_ids,
                'timestamp': self._get_timestamp(),
                'capabilities': ['relay', 'data_aggregation'],
            }
        else:
            # Model B：查询 "谁在附近？"
            return {
                'type': 'query',
                'target_group': self.group_ids[0] if self.group_ids else '*',
                'device_id': self.device_id,
            }
    
    def select_resource(self):
        """选择发现时隙（避免碰撞）"""
        # 基于设备 ID 的伪随机时隙选择
        import hashlib
        hash_val = int(hashlib.md5(
            str(self.device_id).encode()).hexdigest(), 16)
        slot = hash_val % self.DISCOVERY_SLOTS
        return slot
    
    def process_received_discovery(self, message, rsrp_dbm):
        """处理收到的发现消息"""
        peer_id = message['device_id']
        self.discovered_peers[peer_id] = {
            'rsrp': rsrp_dbm,
            'capabilities': message.get('capabilities', []),
            'last_seen': self._get_timestamp(),
        }
        
        # 距离粗估（基于 RSRP）
        # 路径损耗 = TX_POWER - RSRP
        path_loss = self.TX_POWER_DBM - rsrp_dbm
        estimated_distance = 10 ** ((path_loss - 40) / 30)  # 简化模型
        self.discovered_peers[peer_id]['est_distance_m'] = estimated_distance
    
    def _get_timestamp(self):
        import time
        return int(time.time() * 1000)
```

---

## 3. 资源分配与干扰管理

### 3.1 D2D 干扰场景

带内 D2D 面临四种干扰场景：

```
场景 1：D2D TX → 蜂窝 BS（上行干扰）
  D2D 发射器的信号被基站当作干扰

场景 2：蜂窝 UE → D2D RX（上行干扰）
  蜂窝用户的上行信号干扰 D2D 接收器

场景 3：D2D TX → 蜂窝 UE（下行干扰）
  D2D 发射器的信号干扰蜂窝用户的下行接收

场景 4：BS → D2D RX（下行干扰）
  基站的下行信号干扰 D2D 接收器
```

实际系统中，D2D 通常复用**上行资源**（场景 1 和 2），原因是：

- 上行功率控制本来就存在，容易扩展到 D2D
- 基站有先进的干扰消除能力（SIC/MMSE），可以处理 D2D 干扰
- 下行频段的干扰管理更难（基站发射功率远大于 D2D 设备）

### 3.2 资源分配算法

D2D 资源分配的核心问题是：给每个 D2D 对分配哪个资源块（RB），以及多大的发射功率。

| 方法 | 复杂度 | 最优性 | 适用规模 |
|------|--------|--------|---------|
| 穷举搜索 | O(N^M) | 最优 | < 10 个 D2D 对 |
| 图着色 | O(N·M) | 次优 | 中等规模 |
| 匈牙利算法 | O(N³) | 最优（二部图） | 中等规模 |
| 深度强化学习 | 训练慢，推理快 | 近优 | 大规模 |
| 分布式博弈论 | 低（分布式） | Nash 均衡 | 任意规模 |

```python
def d2d_resource_allocation_graph_coloring(d2d_pairs, cellular_users, 
                                           n_rbs, interference_threshold_db):
    """基于图着色的 D2D 资源分配
    
    思路：构建干扰图，相互干扰强的 D2D 对不能用同一个 RB。
    等价于图着色问题（NP-hard，用贪心近似）。
    """
    n_d2d = len(d2d_pairs)
    
    # 1. 构建干扰图
    interference_graph = [[False] * n_d2d for _ in range(n_d2d)]
    for i in range(n_d2d):
        for j in range(i+1, n_d2d):
            # 计算 D2D_i 的 TX 对 D2D_j 的 RX 的干扰
            d_ij = distance(d2d_pairs[i]['tx'], d2d_pairs[j]['rx'])
            interference_ij = 10 - 30 * np.log10(d_ij)  # 简化路径损耗
            if interference_ij > interference_threshold_db:
                interference_graph[i][j] = True
                interference_graph[j][i] = True
    
    # 2. 贪心图着色
    colors = [-1] * n_d2d  # -1 = 未分配
    # 按干扰度（邻居数）降序排列
    order = sorted(range(n_d2d), 
                   key=lambda x: sum(interference_graph[x]), reverse=True)
    
    for node in order:
        # 找出邻居已用的颜色
        used_colors = set()
        for neighbor in range(n_d2d):
            if interference_graph[node][neighbor] and colors[neighbor] != -1:
                used_colors.add(colors[neighbor])
        
        # 分配最小可用颜色
        for color in range(n_rbs):
            if color not in used_colors:
                colors[node] = color
                break
    
    return colors  # 每个 D2D 对分配的 RB 编号

def distance(a, b):
    return ((a[0]-b[0])**2 + (a[1]-b[1])**2)**0.5
```

---

## 4. 中继辅助 D2D

### 4.1 用户中继场景

当两个设备距离较远或之间有障碍物时，可以利用中间的设备做中继。IoT 场景中特别适合：固定部署的传感器节点可以为移动设备提供中继服务。

中继选择的关键指标：

- **瓶颈链路质量**：中继路径的容量由最弱的一跳决定
- **中继的剩余电量**：避免选择电量低的设备
- **中继的当前负载**：已经在做中继的设备不宜再增加负担

### 4.2 多跳 D2D

在大范围 IoT 部署中（如智慧农业、环境监测），单跳 D2D 覆盖不够。多跳 D2D 让数据通过多个中继节点逐跳传递到目的地。

多跳 D2D 的挑战是端到端延迟随跳数线性增长，且每一跳都引入额外的干扰和差错传播。实际部署中通常限制最大跳数为 3-4 跳。

| 跳数 | 单跳延迟 | 端到端延迟 | 端到端可靠性 (每跳 99%) |
|------|---------|-----------|----------------------|
| 1 | 2 ms | 2 ms | 99% |
| 2 | 2 ms | 4 ms | 98% |
| 3 | 2 ms | 6 ms | 97% |
| 4 | 2 ms | 8 ms | 96% |
| 5 | 2 ms | 10 ms | 95% |

---

## 5. V2X：D2D 最成功的应用

### 5.1 C-V2X 与 Sidelink

C-V2X（Cellular V2X）是 D2D 在车联网中的具体实现。3GPP 定义了两种通信模式：

- **Uu 接口**：车辆通过基站中转通信（传统蜂窝模式），适合非时延敏感的信息服务
- **PC5 接口（Sidelink）**：车辆直接通信（D2D 模式），用于安全相关的低延迟消息

5G NR Sidelink（Release 16/17/18）相比 LTE Sidelink 的关键改进：

| 特性 | LTE V2X (Rel-14/15) | NR V2X (Rel-16+) |
|------|---------------------|-------------------|
| 延迟 | 20-100 ms | 3-10 ms |
| 可靠性 | 90-95% | 99.99% |
| 数据速率 | ~10 Mbps | ~1 Gbps |
| 定位精度 | ~10 m | ~0.1 m |
| HARQ 反馈 | 无（盲重传） | 有（单播/组播） |
| 资源分配 | Mode 3/4 | Mode 1/2 |
| 载波频率 | < 6 GHz | < 6 GHz + mmWave |
| QoS 支持 | 有限 | PPPP + PDB + PER |

### 5.2 Sidelink 资源分配

NR Sidelink 有两种资源分配模式：

**Mode 1（基站调度）**：基站为每个车辆分配 Sidelink 资源（时间/频率/功率）。优点是资源利用效率高、干扰可控。缺点是需要蜂窝覆盖，且调度延迟增加。

**Mode 2（自主选择）**：车辆自己选择发送资源，使用 sensing + reservation 机制。车辆先"感知"（sensing）哪些资源被占用，选择空闲资源并提前"预约"（reservation）未来的发送时机。

```python
class NRSidelinkMode2:
    """NR Sidelink Mode 2 资源选择（SB-SPS 机制）"""
    
    def __init__(self, n_subchannels=10, sensing_window_ms=1100, 
                 reservation_period_ms=100):
        self.n_subchannels = n_subchannels
        self.sensing_window = sensing_window_ms
        self.reservation_period = reservation_period_ms
        self.rsrp_threshold_dbm = -110  # RSRP 排除阈值
    
    def select_resource(self, sensing_results, candidate_slots):
        """
        sensing_results: 过去 sensing_window 内观测到的资源占用情况
            [{slot, subchannel, rsrp, reserved_by}]
        candidate_slots: 未来可用的发送时隙
        """
        # Step 1: 排除已被预约且信号强的资源
        excluded = set()
        for r in sensing_results:
            if r['rsrp'] > self.rsrp_threshold_dbm:
                # 该资源在未来会被对方继续占用（SPS 周期性预约）
                future_slot = r['slot'] + self.reservation_period
                if future_slot in candidate_slots:
                    excluded.add((future_slot, r['subchannel']))
        
        # Step 2: 在剩余候选资源中选择
        available = []
        for slot in candidate_slots:
            for sch in range(self.n_subchannels):
                if (slot, sch) not in excluded:
                    available.append((slot, sch))
        
        # Step 3: 如果可用资源 < 候选资源的 20%，放宽阈值重来
        if len(available) < 0.2 * len(candidate_slots) * self.n_subchannels:
            self.rsrp_threshold_dbm += 3  # 提高阈值 3 dB
            return self.select_resource(sensing_results, candidate_slots)
        
        # Step 4: 从可用资源中随机选择
        import random
        selected = random.choice(available)
        return selected
```

---

## 6. ProSe 协议与能效

### 6.1 3GPP ProSe 协议栈

ProSe（Proximity Services）是 3GPP 在 Release 12 引入的邻近服务框架，是 D2D 通信的标准化基础：

```
应用层
  └── ProSe 应用服务器（网络侧）
  └── ProSe 应用（终端侧）
        │
ProSe 协议层
  └── ProSe 发现协议（邻近发现）
  └── ProSe 直连通信协议（D2D 数据传输）
        │
接入层
  └── PC5 接口（Sidelink 物理层/MAC 层）
```

ProSe 功能实体：

| 实体 | 位置 | 职责 |
|------|------|------|
| ProSe Function | 核心网 | 授权管理、发现参数配置 |
| ProSe App Server | 应用层 | 用户身份映射、组管理 |
| ProSe UE | 终端 | 执行发现和直连通信 |

### 6.2 D2D 能效增益

D2D 通信的能效优势来自两个方面：

**缩短传输距离**：蜂窝通信中，设备到基站的距离通常是 100m-1km。D2D 通信距离通常 < 50m。路径损耗随距离的 3-4 次方增长，距离缩短 10 倍意味着路径损耗降低 30-40 dB。

**减少基站参与**：蜂窝中转需要两跳（上行+下行），D2D 只需一跳。消除了基站的处理延迟和能耗。

定量分析：

| 场景 | 设备间距 | 设备发射功率 | 每比特能耗 | 相对基准 |
|------|---------|------------|-----------|---------|
| 蜂窝中转（设备距 BS 500m） | 10 m | 23 dBm | 10 μJ/bit | 100% |
| D2D 直连（10m 距离） | 10 m | 0 dBm | 0.1 μJ/bit | 1% |
| D2D 直连（50m 距离） | 50 m | 10 dBm | 1 μJ/bit | 10% |

D2D 通信可以将每比特能耗降低 10-100 倍——对电池供电的 IoT 设备来说，这直接意味着电池寿命延长 10-100 倍。

### 6.3 系统级能效

从整个网络的角度看，D2D 的能效增益还包括基站的能耗节省。当近距离通信从蜂窝卸载到 D2D 后，基站可以降低发射功率或关闭部分射频链路。

2024 年中国移动的试点数据：在密集城区部署 D2D 覆盖后，基站能耗降低约 15%，小区边缘用户的吞吐量提升约 40%。

---

## 7. 实践建议

### 7.1 初学者入门路径

**第一步：模式选择仿真**（2-3 天）。用 Python 搭建一个简单的单小区场景：1 个基站、若干蜂窝用户和 D2D 对。实现模式选择算法——根据设备间距和信道条件决定走蜂窝还是 D2D。比较两种模式下的吞吐量和能效。

**第二步：干扰分析**（3-5 天）。在上述仿真中加入干扰模型。D2D 对复用蜂窝上行资源，观察不同 D2D 功率和密度下对蜂窝用户的干扰影响。实现简单的功率控制算法。

```python
# 简单的 D2D 功率控制
import numpy as np

def d2d_power_control(d2d_pairs, cellular_users, bs_position,
                      target_sinr_cellular_db=10, max_d2d_power_dbm=20):
    """
    约束：D2D 发射功率不能让蜂窝用户的 SINR 低于目标值。
    """
    d2d_powers = []
    
    for d2d in d2d_pairs:
        max_allowed = max_d2d_power_dbm
        
        for cu in cellular_users:
            # 蜂窝用户当前 SINR
            cu_signal = cu['rx_power_dbm']
            cu_noise = -104  # dBm
            
            # D2D TX 对蜂窝用户 RX（基站）的干扰
            d_d2d_bs = np.sqrt(
                (d2d['tx'][0]-bs_position[0])**2 + 
                (d2d['tx'][1]-bs_position[1])**2)
            path_loss_d2d_bs = 128.1 + 37.6 * np.log10(d_d2d_bs/1000)
            
            # D2D 功率上限：保证蜂窝 SINR
            # SINR_cellular = P_cellular / (I_d2d + N0) >= target
            # I_d2d = P_d2d - PL_d2d_bs
            # P_d2d <= target_sinr * N0 + P_cellular - path_loss (dB)
            max_interference = (10**(cu_signal/10) / 
                              10**(target_sinr_cellular_db/10) - 
                              10**(cu_noise/10))
            if max_interference > 0:
                max_power_for_cu = 10*np.log10(max_interference) + path_loss_d2d_bs
                max_allowed = min(max_allowed, max_power_for_cu)
        
        d2d_powers.append(max(0, max_allowed))  # 最低 0 dBm
    
    return d2d_powers
```

**第三步：阅读 3GPP 规范**（1 周）。重点看 TS 23.303（ProSe 架构）和 TS 36.300（Sidelink 过程）。NR Sidelink 部分参考 TS 38.331（RRC）和 TS 38.321（MAC）。

### 7.2 具体调优建议

- **发现周期**：ProSe 发现周期默认 320 ms，IoT 场景可以放宽到数秒以节省能量。移动场景（V2X）需要更短的发现周期（100 ms）
- **功率控制步长**：D2D 功率控制的步长设为 1 dB（比蜂窝的 1-3 dB 更精细），因为 D2D 距离短、信道变化快
- **最大 D2D 距离**：实际部署中限制在 50 m 以内，超过这个距离 D2D 的能效优势消失
- **复用比例**：不要让所有蜂窝资源都可被 D2D 复用——预留 20-30% 的"保护资源"给对干扰敏感的蜂窝用户
- **Mode 2 感知窗口**：NR Sidelink Mode 2 的感知窗口设为 1100 ms（约 10 个 SPS 周期），太短会漏检占用资源，太长增加存储和计算开销
- **中继选择**：优先选择固定部署（电源供电）的 IoT 设备作为中继，避免消耗移动设备的电池

---

## 参考文献

1. A. Asadi et al., "A survey on device-to-device communication in cellular networks," *IEEE Communications Surveys & Tutorials*, vol. 16, no. 4, pp. 1801-1819, 2014.
2. L. Wei et al., "Device-to-device communications underlaying cellular networks," *IEEE Trans. Communications*, vol. 61, no. 8, pp. 3541-3551, 2013.
3. 3GPP TS 23.303, "Proximity-based services (ProSe); Stage 2," v17.2.0, 2022.
4. 3GPP TS 38.300, "NR; Overall description; Stage 2," v18.1.0, 2024.
5. G. Fodor et al., "Design aspects of network assisted device-to-device communications," *IEEE Communications Magazine*, vol. 50, no. 3, pp. 170-177, 2012.
6. S. A. A. Shah et al., "5G NR V2X sidelink for vehicular communication," *IEEE Access*, vol. 9, pp. 129907-129930, 2021.
7. Z. Ding et al., "A survey on resource allocation for device-to-device communication," *IEEE Communications Surveys & Tutorials*, vol. 20, no. 4, pp. 2763-2800, 2018.
8. D. Feng et al., "Device-to-device communications underlaying cellular networks," *IEEE Trans. Communications*, vol. 61, no. 8, pp. 3541-3551, 2013.
9. L. Liang et al., "Spectrum sharing in vehicular networks based on multi-agent reinforcement learning," *IEEE JSAC*, vol. 37, no. 10, pp. 2282-2292, 2019.
10. China Mobile Research Institute, "5G D2D technology white paper," v2.0, 2024.
