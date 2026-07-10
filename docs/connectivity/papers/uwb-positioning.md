---
schema_version: '1.0'
id: uwb-positioning
title: UWB 超宽带高精度定位技术
layer: 2
content_type: UNKNOWN
difficulty: UNKNOWN
reading_time: UNKNOWN
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# UWB 超宽带高精度定位技术

> 难度：🟡 进阶 | 领域：短距通信与定位 | 更新：2025-06

---

## 一句话总结

UWB（超宽带）用纳秒级的极窄脉冲实现厘米级精度的无线测距与定位，是目前消费电子中最精准的室内定位技术。从 iPhone 的"精确查找"到数字车钥匙，UWB 正从小众走向主流。

---

## 从日常场景说起

你在沙发缝里找 AirTag——手机屏幕上出现一个箭头，指着沙发左下角，显示"距离 0.3 米"。你顺着箭头伸手一摸，真的找到了。

这个"精确查找"用的就是 UWB。它能告诉你目标在**哪个方向、距离多远**，精度达到 ±10 厘米。相比之下，蓝牙只能告诉你"大概在附近"（±2 米），WiFi 定位精度更是在 ±3-5 米级别。

UWB 的精度为什么能高一个数量级？因为它用了一种完全不同的信号方式。

---

## UWB 的物理层原理

### 脉冲无线电

传统无线技术（蓝牙、WiFi、4G）都用"连续波"——信号是持续振荡的正弦波，信息编码在振幅、频率或相位的变化中。

UWB 不一样。它发射的是**极短的脉冲**——每个脉冲只有 1-2 纳秒宽（1 纳秒 = 十亿分之一秒）。在这么短的时间内，脉冲的频谱会展开到 500 MHz 以上的带宽（所以叫"超宽带"）。

日常类比：想象你在一个空旷的大厅里拍了一下手。你能从回声的延迟准确判断墙壁有多远。如果你改成持续哼一个音，回声和原声混在一起，就很难分辨了。UWB 的脉冲就像那一下清脆的拍手——干净利落、时间精确。

### 为什么脉冲能实现高精度？

测距的本质是测量信号的**飞行时间（Time of Flight, ToF）**。光速约 3×10⁸ m/s，1 纳秒走 30 厘米。如果你的时钟精度是 1 纳秒，距离精度就是 30 厘米；如果是 0.1 纳秒，精度就是 3 厘米。

UWB 脉冲的超大带宽（>500 MHz）使得接收机能以亚纳秒精度分辨脉冲到达时刻。带宽越宽，时间分辨率越高——这是傅里叶变换的基本原理。相比之下，蓝牙信号带宽只有 1-2 MHz，时间分辨率差了两个数量级。

另一个好处：UWB 脉冲能分辨**多径信号**。在室内环境中，无线信号会被墙壁、家具反射，产生多条路径。UWB 的窄脉冲可以把直射路径和反射路径在时间上分开，只用最先到达的直射信号来测距。蓝牙和 WiFi 的窄带信号无法分辨多径，RSSI 测距会被反射信号严重干扰。

---

## IEEE 802.15.4z 标准

UWB 的标准化历程比较曲折。最早的 IEEE 802.15.4a（2007 年）定义了 UWB 物理层，但安全性不够。2020 年发布的 **IEEE 802.15.4z** 是关键更新，增加了大量安全特性。

### 802.15.4z 的核心改进

**Scrambled Timestamp Sequence (STS)**：这是 802.15.4z 最重要的安全特性。STS 是一个只有通信双方知道的伪随机序列，嵌入在 UWB 帧的时间戳部分。接收方用预共享密钥验证 STS 的正确性，防止攻击者伪造或重放测距信号。

**为什么需要 STS？** 因为 UWB 测距用于安全敏感场景（如车钥匙开锁）。如果攻击者能伪造 UWB 测距结果，就能在车主不知情的情况下开走汽车。STS 使得只有合法设备才能参与测距，从物理层保证了安全性。

**两种帧结构**：802.15.4z 定义了 HRP（High Rate Pulse）和 LRP（Low Rate Pulse）两种模式。HRP 用于消费电子（Apple、Samsung、NXP 的方案都基于 HRP），LRP 用于工业和汽车（更长的帧，更远的测距范围）。

### 关键参数

| 参数 | HRP 模式 | LRP 模式 |
|------|----------|----------|
| 脉冲重复频率 (PRF) | 62.4 / 124.8 MHz | 1 / 4 / 16 MHz |
| 信道带宽 | 499.2 MHz (Channel 5/9) | 1.3 MHz |
| 标称测距精度 | ±5-10 cm | ±30 cm |
| 最大测距范围 | ~75 m (室内) | ~200 m |
| 数据速率 | 6.8 / 27.2 Mbps | 低 |
| 典型功耗 | 中等 | 较低 |

---

## 定位算法

UWB 的测距是基础，定位需要在此基础上做几何计算。主流算法有三种：

### TWR（Two-Way Ranging，双向测距）

原理：设备 A 发一个 UWB 包给设备 B，B 收到后回一个包给 A。A 测量从发送到接收的总时间，减去 B 的处理延迟，除以 2 再乘以光速，得到距离。

优点：不需要两个设备的时钟同步（因为用的是往返时间）。
缺点：每次测距需要双方交互，不适合大量设备同时测距。

改进版 **DS-TWR（Double-Sided TWR）**：A 和 B 各测一次往返时间，取几何平均值，消除因时钟漂移导致的误差。精度从 TWR 的 ±30cm 提升到 ±5cm。

### TDoA（Time Difference of Arrival，到达时间差）

原理：被定位设备（Tag）发一个 UWB 包，多个固定位置的锚点（Anchor）各自记录收到时间。通过不同锚点的时间差，算出 Tag 到各锚点的距离差，画出双曲线，交点就是 Tag 的位置。

优点：Tag 只需要发射（不需要接收），功耗极低；多个 Tag 不会互相干扰。
缺点：所有锚点需要精确时钟同步（纳秒级）。

TDoA 是大规模资产追踪的首选方案。工厂里可能有上千个 Tag 同时定位，TDoA 可以轻松应对。

### AoA（Angle of Arrival，到达角度）

原理：锚点使用多个天线阵列，通过测量 UWB 信号到达各天线的相位差，计算信号的入射角度。知道了方向和距离，就能确定 Tag 的位置。

优点：理论上只需要 1 个锚点就能实现 2D 定位（距离 + 角度）。
缺点：需要天线阵列，锚点成本高；角度测量受多径干扰。

iPhone 的"精确查找"实际上就是结合了 TWR（测距离）和 AoA（测方向），所以能在屏幕上同时显示方向箭头和距离数字。

### 定位精度对比（UWB vs 其他技术）

| 技术 | 测距/定位原理 | 典型精度 (2D) | 典型精度 (3D) | 刷新率 |
|------|-------------|-------------|-------------|--------|
| UWB TWR | 飞行时间 | ±10 cm | ±20 cm | 10-100 Hz |
| UWB TDoA | 到达时间差 | ±20 cm | ±30 cm | 100-1000 Hz |
| BLE 5.x AoA | 到达角度 | ±0.5-1 m | ±1-2 m | 1-10 Hz |
| BLE 6.0 CS | 信道探测 | ±10-30 cm | N/A | 1-10 Hz |
| WiFi RTT (FTM) | 飞行时间 | ±1-2 m | ±2-3 m | 0.5-2 Hz |
| WiFi 指纹 | RSSI 匹配 | ±3-5 m | N/A | 0.1-1 Hz |
| RFID | 场强/相位 | ±1-3 m | N/A | 1-10 Hz |

---

## 核心应用场景

### 数字车钥匙

这是 UWB 最高调的消费应用。两大联盟在推动：

**CCC（Car Connectivity Consortium）**：定义了数字车钥匙的标准架构。Release 3.0 引入 UWB 测距，要求：
- 测距精度 < 30 cm
- 安全测距（防中继攻击）
- 支持被动进入（Passive Entry）：车主手机在口袋里，走近汽车自动解锁
- 支持被动启动（Passive Start）：坐进驾驶座自动允许启动

**FiRa 联盟（Fine Ranging）**：由 NXP、Samsung、Sony、Bosch 等成立，负责 UWB 的互操作性认证和应用配置文件。FiRa 定义了 PACS（Physical Access Control Service）等标准化服务。

实际部署：BMW、Audi、Volkswagen、Genesis、Lincoln 等品牌已在部分车型中集成 UWB 车钥匙。Apple CarKey 和 Samsung Digital Key 都基于 CCC Release 3.0 + UWB。

### 工业资产追踪

在仓库和工厂中追踪物料、工具、叉车、人员的实时位置。典型部署：

- 仓库面积 10,000 m²，部署 20-40 个 UWB 锚点
- 使用 TDoA 定位，同时追踪 5,000+ 个 Tag
- 定位精度 ±30 cm，刷新率 10 Hz
- 应用：防碰撞预警（叉车与行人）、区域围栏、路径优化

代表厂商：Ubisense、Sewio、Decawave（现为 Qorvo 旗下）、Humatics。

### 工业安全围栏

在危险区域（如机器人工作区）设置虚拟围栏。当佩戴 UWB 标签的工人进入危险区域时，系统在 10ms 内触发报警或停机。

传统方案是激光帘幕或物理围栏。UWB 的优势是"虚拟"围栏可以灵活调整、不需要物理安装、支持 3D 区域定义。

### 消费电子：寻物与空间感知

- Apple AirTag / Samsung SmartTag+：UWB 精确查找
- iPhone / Apple Watch：空间共享（SharePlay 中显示朋友的方向和距离）
- 索尼 PS5 VR2 手柄：UWB 用于手柄 6DoF 追踪（实验性）

---

## 芯片生态

### 主要 UWB 芯片厂商

| 厂商 | 芯片型号 | 特点 | 主要客户 |
|------|---------|------|----------|
| NXP | Trimension SR040/SR150/NCJ29D | 业界最全产品线，汽车级认证 | BMW, VW, Apple (部分) |
| Qorvo (Decawave) | DW3000/DW3720 | 社区生态好，性价比高 | 工业客户，Apple AirTag |
| Apple | U1/U2 | 自研芯片，不对外销售 | iPhone, AirTag, Apple Watch |
| Samsung | Exynos Connect U100 | 集成于 Galaxy 旗舰 | Galaxy S24+, SmartTag2 |
| STMicroelectronics | ST4A | 汽车+消费级 | 与 CCC 联盟合作 |

### 芯片价格趋势

2020 年 UWB 芯片单价约 $3-5，2024 年降至 $1.5-2.5。随着智能手机和汽车的集成量增加，预计 2026 年将降至 $1 以下。NXP 和 Qorvo 都在推动低成本集成方案（UWB + BLE 双模 SoC），减少物料清单成本。

---

## UWB 的挑战与局限

### 功耗

UWB 发射功耗比 BLE 高 3-5 倍。对于需要电池供电的小型 Tag（如资产追踪标签），持续高频率测距会快速消耗电池。应对策略：

- BLE 唤醒 + UWB 精确测距：平时用 BLE 低功耗保持连接，需要精确定位时才激活 UWB
- 降低测距频率：从 100 Hz 降到 1 Hz 可以让电池寿命从几天变成几年
- 优化 STS 长度：802.15.4z 允许可变长度 STS，短 STS 省电但安全性稍降

### 部署成本

UWB 定位需要部署固定锚点，这意味着前期基础设施投入。一个 10,000 m² 的仓库典型需要：
- 20-40 个锚点 × $100-300/个 = $2,000-12,000 硬件成本
- 安装、校准、软件平台 = 额外 $5,000-20,000
- 总成本 $10,000-30,000，远高于蓝牙信标方案（$3,000-8,000）

但 UWB 的精度是蓝牙的 5-10 倍，在需要高精度的场景中性价比更高。

### 法规限制

UWB 在不同国家的功率限制和允许频段不同：
- 美国 FCC：3.1-10.6 GHz，最大发射功率 -41.3 dBm/MHz
- 欧洲 ETSI：6.0-8.5 GHz，需要 LBT（先监听后发射）
- 中国 MIIT：6.0-9.0 GHz（2024 年新规），放宽了之前的限制
- 日本 MIC：3.4-4.8 GHz, 7.25-10.25 GHz

频段和功率差异意味着全球部署需要适配不同区域。Channel 5（6489.6 MHz）和 Channel 9（7987.2 MHz）是全球最通用的两个信道。

---

## 未来演进方向

**UWB + 5G 融合**：3GPP 正在研究将 UWB 测距信息融合到 5G 定位框架中，利用 5G 的覆盖 + UWB 的精度实现广域高精度定位。

**UWB 雷达**：利用 UWB 的超大带宽做近距离雷达感知（呼吸检测、手势识别、入侵检测），不需要摄像头就能感知环境。部分 UWB 芯片已经支持雷达模式（如 NXP SR040）。

**IEEE 802.15.4ab**：正在制定的下一代 UWB 标准，目标包括更低功耗、更高数据率、与蓝牙/WiFi 更好的共存。

**UWB Mesh**：当前 UWB 主要是星型拓扑（Tag ↔ Anchor），未来可能支持 Tag 之间互相测距组成 Mesh 网络，实现无需基础设施的相对定位（对机器人编队、无人机群很有价值）。

---

## 参考文献

1. IEEE. "IEEE 802.15.4z-2020: Enhanced Impulse Radio," 2020.
2. FiRa Consortium. "UWB Technical Overview," firaconsortium.org, 2024.
3. CCC (Car Connectivity Consortium). "Digital Key Release 3.0: UWB Ranging Profile," 2023.
4. Qorvo. "DW3000 Family Datasheet and Application Notes," 2024.
5. NXP. "Trimension UWB Portfolio: SR040, SR150, NCJ29D Product Briefs," 2024.
6. A. Alarifi et al., "Ultra Wideband Indoor Positioning Technologies: Analysis and Recent Advances," Sensors, vol. 16, no. 5, 2016.
7. Z. Sahinoglu, S. Gezici, I. Guvenc. "Ultra-Wideband Positioning Systems," Cambridge University Press, 2008.
8. S. Monica, G. Ferrari. "UWB-based Localization in Large Indoor Scenarios: Optimized Placement of Anchor Nodes," IEEE Access, vol. 8, 2020.
9. Apple. "Nearby Interaction Framework Documentation," developer.apple.com, 2024.
10. Samsung. "Exynos Connect U100: UWB Chipset for Smart Devices," Product Brief, 2024.
11. 中国工信部. "超宽带 (UWB) 设备无线电管理规定 (征求意见稿)," 2024.
12. M. Ridolfi et al., "Experimental Evaluation of UWB Indoor Positioning for Indoor Track Cycling," Sensors, vol. 18, no. 7, 2018.
