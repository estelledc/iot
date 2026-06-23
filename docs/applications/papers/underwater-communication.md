# 水下通信与探测技术

> **难度**：🟡 中级 | **领域**：海洋工程、通信技术 | **阅读时间**：约 28 分钟

## 日常类比

你在游泳池里试过对着水面喊话吗？声音传不远，而且听起来完全变形。现在想象要在几千米深的海底让两台机器人对话——水是一个对电磁波极其不友好的环境。陆地上我们用 WiFi、4G、5G 通信畅通无阻，但在水下，无线电波几米就衰减到几乎为零。

水下通信面对的困难，就好比你要在一个巨大的、回声不断的山洞里，用对讲机和几公里外的人通话——信号被四面八方的墙壁反射（多径效应），对方可能在移动导致声音忽高忽低（多普勒效应），而且传输速度慢到像用 1990 年代的拨号上网。

但人类对水下通信的需求越来越大：海底油气管道巡检、水产养殖监测、海洋科学研究、军事潜艇通信、水下考古。这篇文章系统梳理水下通信的三条技术路线（声、光、电磁），以及水下传感器网络的设计挑战。

## 1 水下通信的物理约束

### 1.1 为什么无线电在水下不行

无线电波（RF）在空气中传播速度接近光速（3×10⁸ m/s），衰减很小。但在海水中，电导率约 4 S/m（空气几乎为 0），电磁波被迅速吸收。衰减公式中的趋肤深度 δ = √(2/ωμσ)，频率越高衰减越快：

| 频率 | 水下趋肤深度 | 实际通信距离 | 数据率 |
|------|-------------|-------------|--------|
| 1 Hz (ELF) | ~250 m | 数千 km | 几 bit/min |
| 77 Hz (SLF) | ~60 m | 数百 km | ~几十 bit/s |
| 1 kHz | ~16 m | 几十 km | 几百 bit/s |
| 1 MHz | ~0.5 m | 几米 | 不实用 |
| 1 GHz (WiFi) | ~0.02 m | 几厘米 | 不可能 |

这就是为什么潜艇要接收 VLF/ELF 信号需要拖曳长达几百米的天线——频率越低天线越长。

### 1.2 三条技术路线对比

| 维度 | 水声通信 | 水下光通信 | 电磁/磁感应 |
|------|---------|-----------|------------|
| 典型距离 | 1-100 km | 10-100 m | 1-100 m |
| 数据率 | 0.1-100 kbps | 1-500 Mbps | 1-100 kbps |
| 延迟 | 高（声速 1500m/s） | 低（光速） | 中等 |
| 抗浑浊 | 强 | 弱（散射严重） | 中等 |
| 能耗 | 中 | 低 | 中 |
| 成熟度 | 高（主流） | 中（快速发展） | 低（研究阶段） |

## 2 水声通信

### 2.1 声波在水中的传播

声波是水下远距离通信的唯一实用手段。声波在海水中的传播速度约 1500 m/s（空气中约 340 m/s），受温度、盐度、深度影响：

```python
def sound_speed_water(T, S, D):
    """
    Mackenzie 公式 (1981)：计算海水中声速
    T: 温度 (°C), S: 盐度 (ppt), D: 深度 (m)
    返回: 声速 (m/s)
    """
    c = (1448.96 + 4.591 * T - 0.05304 * T**2 
         + 2.374e-4 * T**3 + 1.340 * (S - 35) 
         + 1.630e-2 * D + 1.675e-7 * D**2
         - 1.025e-2 * T * (S - 35) - 7.139e-13 * T * D**3)
    return c

# 表层 (20°C, 35ppt, 0m) → 约 1521 m/s
# 深海 (2°C, 35ppt, 4000m) → 约 1553 m/s
```

声速随深度先减后增形成"声道轴"（SOFAR channel，约 700-1200m 深），声波被折射困在这个深度范围内传播，衰减极小，理论上可以传播上万公里——这是海洋声学最神奇的现象。

### 2.2 水声信道的三大挑战

**多径效应**：声波不只从发射器直达接收器，还会被海面、海底、温度梯度层反射和折射，产生多条路径。不同路径的延迟差（多径扩展）可达几十毫秒，导致信号在接收端"糊"在一起（符号间干扰）。

**多普勒效应**：水中声速只有 1500 m/s，远低于电磁波。一个以 3 m/s 速度运动的 AUV（水下自主潜航器），相对声速的比率达到 0.2%——这比陆地无线通信中的多普勒效应大了 1-2 个数量级。多普勒导致频率偏移，接收器必须做精确的频率补偿。

**时变性**：海流、温度变化、海面波浪导致声学信道不断变化。在陆地上，WiFi 信道可能几秒甚至几分钟才变化一次；水声信道可能每几百毫秒就发生显著变化。

### 2.3 调制与编码方案

```
传统方案：FSK（频移键控）
  优点：抗多径能力强
  缺点：频谱效率低（<1 bit/s/Hz）
  适用：低速率、长距离

主流方案：OFDM（正交频分复用）
  优点：频谱效率高（2-4 bit/s/Hz），天然抗多径
  缺点：对多普勒敏感，峰均比高
  适用：中短距离、高速率

前沿方案：OTFS（正交时频空间调制）
  优点：在时延-多普勒域调制，天然适应水声信道
  缺点：计算复杂度高，工程实现不成熟
  状态：学术研究阶段（2024）
```

典型商用水声调制解调器（Modem）性能：

| 产品 | 频段 | 距离 | 数据率 | 价格 |
|------|------|------|--------|------|
| EvoLogics S2C R 7/17 | 7-17 kHz | 8 km | 6.9 kbps | ~$8,000 |
| LinkQuest UWM3000 | 7-14 kHz | 3 km | 5 kbps | ~$6,000 |
| Teledyne Benthos ATM-90x | 9-14 kHz | 6 km | 2.4 kbps | ~$10,000 |
| Subnero M25M | 18-34 kHz | 3 km | 15 kbps | ~$5,000 |

## 3 水下光通信

### 3.1 蓝绿光窗口

海水对不同波长的光衰减差异极大。红外光和红光在几米内就被吸收，但蓝绿光（450-550 nm）有一个相对"透明"的窗口——在清澈的深海水中，衰减系数约 0.05/m，理论上可以传播 100+ 米。

光源选择：

- **LED**：便宜、可靠，但光束发散角大（30-60°），功率有限。适合短距离（<20m）
- **激光二极管（LD）**：光束集中（发散角 < 1°），功率高，传输距离远。但需要精确对准——在水流和平台晃动的环境下保持对准是工程难题

### 3.2 最新进展

2024 年哈尔滨工程大学团队在水下光通信取得突破：使用 micro-LED 阵列 + 自适应波束成形，在 50 米距离实现 500 Mbps 数据率。日本 JAMSTEC 的深海光通信系统在 4,000 米深海实现了 20 米距离、1 Gbps 数据率——这对水下高清视频传输意义重大。

```python
def underwater_optical_link_budget(P_tx, dist, c_atten, A_rx, theta):
    """
    水下光链路预算简化计算
    P_tx: 发射功率 (W)
    dist: 距离 (m)
    c_atten: 衰减系数 (1/m), 清水≈0.05, 沿海≈0.2, 港口≈0.5
    A_rx: 接收器面积 (m^2)
    theta: 光束发散角 (rad)
    返回: 接收功率 (W)
    """
    import math
    # 几何扩散损耗
    beam_area = math.pi * (dist * math.tan(theta))**2
    geo_loss = A_rx / beam_area if beam_area > A_rx else 1.0
    
    # 吸收+散射损耗 (Beer-Lambert 定律)
    absorption_loss = math.exp(-c_atten * dist)
    
    P_rx = P_tx * geo_loss * absorption_loss
    return P_rx

# 示例：100mW 激光, 50m 距离, 清水, 1cm^2 接收器, 1° 发散角
P_rx = underwater_optical_link_budget(0.1, 50, 0.05, 1e-4, 0.017)
# P_rx ≈ 0.57 μW (可检测, 但余量不大)
```

## 4 水下传感器网络

### 4.1 网络架构

水下传感器网络（UWSN）的典型架构分四层：

```
海面浮标 (Surface Buoy)
  ↑ 声学/光学/电缆
海底锚定节点 (Bottom Nodes)  ← 传感器：温度/盐度/压力/浊度
  ↑ 声学多跳
中间层中继节点 (Relay Nodes)
  ↑ 声学
水下机器人 (AUV)  ← 移动数据骡子 (Data Mule)
```

**数据骡子策略**：由于水声通信速率低、能耗高，一种聪明的做法是让 AUV 按预设路径巡游，在靠近每个传感器节点时用高速短距光通信下载数据，然后浮出水面通过卫星或 4G 上传。这样传感器节点不需要做远距离通信，大幅延长电池寿命。

### 4.2 水下定位（没有 GPS）

GPS 信号在水下几厘米就衰减殆尽，水下定位必须另想办法：

| 方法 | 原理 | 精度 | 基础设施 |
|------|------|------|----------|
| LBL (长基线) | 海底锚定信标阵列，三边测量 | 0.1-1 m | 需要部署信标 |
| SBL (短基线) | 船底多个换能器阵列 | 1-10 m | 需要支持船 |
| USBL (超短基线) | 单个紧凑换能器阵列 | 0.2°方位角 | 需要支持船 |
| 惯性导航 (INS) | 加速度计+陀螺仪积分 | 累积漂移 | 自主 |
| 地形匹配 | 声纳扫描地形与已知地图匹配 | 5-20 m | 需要地形数据库 |
| DVL 底跟踪 | 多普勒速度仪测对地速度 | 0.1-0.5% 航程 | 自主 |

实际 AUV 通常融合多种方案：INS + DVL 做连续导航，定期浮到近水面用 GPS 校准，或者在 LBL 信标范围内用声学定位修正。

## 5 能量获取与供电

### 5.1 水下能量困境

水下设备的电池更换极其困难和昂贵——深海设备一次维护可能需要专用船只，成本数十万元。所以水下传感器必须要么超长待机（5-10 年），要么具备能量自给能力。

能量获取途径：

**海流/波浪发电**：利用海流推动涡轮机或振荡浮子发电。Sea-Bird Scientific 的 WET Labs 传感器配备的微型涡轮机可在 0.5 m/s 海流下产生约 1W 功率。

**温差发电**：深海温差可达 20-25°C。利用热电效应（塞贝克效应），温差 10°C 可以产生约 10 mW/cm² 的功率——足以驱动低功耗传感器。

**微生物燃料电池（MFC）**：利用海底沉积物中的微生物氧化有机物产生电流。功率密度很低（~10 mW/m²），但理论上可以"永续"供电。

### 5.2 低功耗策略

```c
// 水下传感器节点的超低功耗工作周期
// 大部分时间深度睡眠, 只在采集/传输时醒来

#define SLEEP_DURATION_S    3600   // 睡眠 1 小时
#define SAMPLE_DURATION_MS  500    // 采样 500ms
#define TX_DURATION_MS      5000   // 传输 5 秒

typedef enum {
    STATE_SLEEP,
    STATE_SAMPLE,
    STATE_TRANSMIT,
} NodeState;

void sensor_node_loop() {
    while (1) {
        // 深度睡眠: 功耗 ~5 μA
        enter_deep_sleep(SLEEP_DURATION_S);
        
        // 唤醒采样: 功耗 ~10 mA
        float temp = read_temperature();
        float salinity = read_salinity();
        float pressure = read_pressure();
        store_to_buffer(temp, salinity, pressure);
        
        // 每 6 次采样传输一次 (每 6 小时)
        if (++sample_count >= 6) {
            // 声学传输: 功耗 ~2W (最大功耗)
            acoustic_modem_power_on();
            transmit_buffer();
            acoustic_modem_power_off();
            sample_count = 0;
        }
    }
}
// 平均功耗: ~50 μW → 一节 D 型锂电池可用 5 年+
```

## 6 应用场景

### 6.1 海底管道巡检

全球海底油气管道总长超过 50 万公里。传统巡检靠定期派潜水员或 ROV（遥控水下机器人），成本高、频率低。IoT 方案是沿管道部署传感器网络，持续监测压力、温度、声发射（泄漏信号），一旦异常立即触发 AUV 前往精确定位。

### 6.2 智慧水产养殖

深海网箱养殖需要监测水质（溶解氧、pH、氨氮）、鱼群行为（水下摄像头+AI）、网箱结构完整性（应变传感器）。挪威 AKVA Group 的 CCS（Cage Control System）在 2,000+ 个深海网箱部署了 IoT 传感器网络，通过声学通信和水面浮标中继，实现远程自动投喂和水质调控。

### 6.3 海洋科学观测

中国的"海底科学观测网"（OOI 中国版）在南海部署了 3,000+ 米深海观测站，通过海底光缆供电和通信（有线方案），配合 AUV 做大范围巡航观测（无线方案）。数据包括：地震波形、海底热液活动、深海生物观测。

## 7 实践建议

### 7.1 初学者入门路径

1. **声学基础**：用 MATLAB/Python 模拟水声信道——生成多径信号、加多普勒偏移、测 BER（误码率）
2. **硬件实验**：用压电陶瓷片（PZT，几块钱一片）DIY 水下声学发射/接收器，在游泳池或浴缸里做短距离通信实验
3. **协议仿真**：用 Aqua-Sim（ns-3 的水下网络仿真模块）模拟 UWSN 拓扑和路由
4. **真实平台**：参与开源项目——如 Project NEMO（水下传感器网络开源框架）
5. **进阶挑战**：基于 TI CC1352R LaunchPad + 外接水听器，做一个低成本水声 Modem 原型

### 7.2 关键设计取舍

**距离 vs 速率**：水声通信的"距离×速率"积大约是常数（~40 km·kbps）。要 10 km 通信距离就只能 4 kbps；要 100 kbps 就只能 400 m。根据应用场景在这条曲线上选择工作点。

**定位精度 vs 成本**：LBL 系统精度最高但部署成本高（每个信标 $5,000-15,000 + 专用布放船）。如果应用不需要亚米级精度，INS+DVL 的组合可以大幅降低成本。

**电池寿命 vs 采样率**：降低声学传输频率是省电最有效的手段——传输功耗是采样功耗的 200 倍。"多采少传"（边缘压缩后再传）是核心策略。

## 参考文献

1. Stojanovic M, Preisig J. Underwater Acoustic Communication Channels: Propagation Models and Statistical Characterization. IEEE Communications Magazine, 2009.
2. Zeng Z, et al. A Survey of Underwater Optical Wireless Communications. IEEE Communications Surveys & Tutorials, 2017, 19(1): 204-238.
3. Akyildiz IF, et al. Underwater Acoustic Sensor Networks: Research Challenges. Ad Hoc Networks, 2005, 3(3): 257-279.
4. EvoLogics. S2C R Series Underwater Acoustic Modems. Product Specification, 2024.
5. Heidemann J, et al. Underwater Sensor Networks: Applications, Advances, and Challenges. Phil. Trans. Royal Society A, 2012.
6. JAMSTEC. Deep-sea Optical Communication System for Real-time Video Transmission. Technical Report, 2024.
7. Mackenzie KV. Nine-term Equation for Sound Speed in the Oceans. JASA, 1981, 70(3): 807-812.
8. Murad M, et al. Underwater Localization: Current Challenges and Future Directions. IEEE Access, 2023.
9. AKVA Group. Cage Control System (CCS) for Aquaculture IoT. Product Overview, 2024.
10. 中国科学院南海海洋研究所. 南海海底科学观测网建设进展. 2024.
