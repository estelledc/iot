---
schema_version: '1.0'
id: underwater-communication
title: 水下通信与探测技术
layer: 7
content_type: technical_analysis
difficulty: intermediate
reading_time: 28
prerequisites:
  - ocean-buoy-sensor-network
tags:
- 水下通信
- 水声通信
- 水下光通信
- UWSN
- AUV
- SOFAR
- 水下定位
- 海洋物联网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 水下通信与探测技术

> **难度**：🟡 中级 | **领域**：海洋工程、通信技术 | **阅读时间**：约 28 分钟

## 日常类比

在游泳池里对着水面喊话，声音传不远且严重变形。把场景放大到千米级深海：两台机器人要对话，却处在对电磁波极不友好的介质里。陆地上的无线局域网（Wi-Fi）与蜂窝网络在海水中会在极短距离内被吸收殆尽。

更贴切的类比是：在巨大、回声不断的山洞里用对讲机联络数公里外的同伴——多径反射把音节糊在一起，移动造成多普勒起伏，端到端速率往往只相当于早期拨号调制解调器量级。需求却真实存在：海底管线巡检、养殖网箱、海洋观测、潜艇通信与水下考古。

## 1 水下通信的物理约束

### 1.1 为什么无线电在水下很难

无线电波在空气中近光速传播；海水电导率约数西门子每米量级，趋肤深度 δ ≈ √(2/ωμσ)，频率越高衰减越快[1]。下表为数量级示意，实际还受盐度、海况影响。

| 频率 | 水下趋肤深度（示意） | 实际通信距离（示意） | 数据率（示意） |
|------|-------------|-------------|--------|
| 极低频（ELF）量级 | 百米级 | 可至远程 | 极低（bit/min 量级） |
| 超低频（SLF）量级 | 数十米级 | 远程可能 | 很低 |
| 千赫兹 | 十余米级 | 视功率与噪声 | 很低–中低 |
| 兆赫兹 | 亚米级 | 近距 | 通常不实用 |
| 吉赫兹（Wi-Fi 频段） | 厘米级 | 几乎不可用 | — |

潜艇接收甚低频/极低频信号常需很长接收天线，正是低频物理代价的工程体现。

### 1.2 三条技术路线对比

| 维度 | 水声通信 | 水下光通信 | 电磁/磁感应 |
|------|---------|-----------|------------|
| 典型距离 | 公里至数十公里量级 | 十米至百米量级（清水更优） | 米至百米量级 |
| 数据率 | 0.1–100 kbps 量级常见 | Mbps–数百 Mbps 量级（短距） | kbps 量级常见 |
| 延迟 | 高（声速约 1500 m/s） | 低（近光速） | 中等 |
| 抗浑浊 | 强 | 弱（散射） | 中等 |
| 能耗 | 中–高（发射） | 相对较低（短距） | 中 |
| 成熟度 | 高（主流远距） | 中（快速发展）[2] | 偏低（研究/niche） |

## 2 水声通信

### 2.1 声波在水中的传播

远距离实用手段仍是声波。声速随温度、盐度、深度变化，可用 Mackenzie 等经验公式估算[7]：

```python
def sound_speed_water(T, S, D):
    """
    Mackenzie 公式 (1981)：海水声速近似
    T: 温度 (°C), S: 盐度 (ppt), D: 深度 (m)
    返回: 声速 (m/s)
    """
    c = (1448.96 + 4.591 * T - 0.05304 * T**2
         + 2.374e-4 * T**3 + 1.340 * (S - 35)
         + 1.630e-2 * D + 1.675e-7 * D**2
         - 1.025e-2 * T * (S - 35) - 7.139e-13 * T * D**3)
    return c

# 表层偏暖与深海低温高压下，声速可差数十 m/s
```

声速剖面可形成深海声道（SOFAR channel）：声波被折射约束在声道轴附近，远程传播衰减相对较小——这是海洋声学的经典现象，具体轴深随海区变化。

### 2.2 水声信道三大挑战

**多径**：海面/海底/温跃层反射折射造成数十毫秒量级多径扩展，引发符号间干扰[1]。

**多普勒**：声速远低于光速，自主水下航行器（Autonomous Underwater Vehicle, AUV）以数米每秒运动即可产生相对显著的多普勒，需精细补偿。

**时变**：海流、浪、温盐变化使信道相干时间可能短至亚秒–秒级，远快于许多陆地无线局域网场景。

### 2.3 调制与编码

| 方案 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| FSK（频移键控） | 较抗多径 | 频谱效率低 | 低速远距 |
| OFDM（正交频分复用） | 频谱效率较高、抗多径 | 对多普勒敏感、峰均比高 | 中短距较高速率 |
| OTFS 等时延-多普勒域方案 | 更贴合双选信道 | 复杂度高、工程成熟度有限 | 研究/试验 |

商用水声调制解调器（Modem）性能随频段与海况变化；下表为公开规格数量级，报价随配置浮动[4]。

| 产品系列（示例） | 频段（示意） | 距离（示意） | 数据率（示意） |
|------|------|------|--------|
| EvoLogics S2C 中低频段 | 约 7–17 kHz | 数公里 | 数 kbps |
| LinkQuest UWM 系列 | 约 7–14 kHz | 数公里 | 数 kbps |
| Teledyne Benthos ATM | 约 9–14 kHz | 数公里 | 数 kbps |
| Subnero 中高频段 | 约 18–34 kHz | 数公里内 | 十余 kbps 量级 |

## 3 水下光通信

### 3.1 蓝绿光窗口

海水对红外/红光吸收强，蓝绿光（约 450–550 nm）在清澈深海衰减相对较小，短距高速成为可能[2]。光源：

- **发光二极管（LED）**：成本低、发散角大，适合更短距。
- **激光二极管（LD）**：准直好、距离潜力大，但对准与平台晃动是工程难点。

### 3.2 进展与链路预算直觉

研究与试验系统已展示数十米距离、数百 Mbps 量级乃至更高峰值的水下光链路（清水、对准良好时）[6]；浑浊近岸性能会显著下降。链路预算可用几何扩散 × Beer–Lambert 吸收散射近似：

```python
def underwater_optical_link_budget(P_tx, dist, c_atten, A_rx, theta):
    """水下光链路预算简化：几何扩散 × 指数衰减"""
    import math
    beam_area = math.pi * (dist * math.tan(theta))**2
    geo_loss = A_rx / beam_area if beam_area > A_rx else 1.0
    absorption_loss = math.exp(-c_atten * dist)
    return P_tx * geo_loss * absorption_loss

# c_atten: 清水可低至约 0.05/m 量级；港口浑浊可高一个数量级以上
```

## 4 水下传感器网络

### 4.1 网络架构

水下无线传感器网络（Underwater Wireless Sensor Network, UWSN）常见分层：海面浮标、中继、海底锚定节点，以及作为数据骡子（Data Mule）的 AUV[3][5]。

```
海面浮标 (Surface Buoy)
  ↑ 声学/光学/电缆
海底锚定节点 ← 温盐深/浊度等传感
  ↑ 声学多跳
中继节点
  ↑ 声学
AUV ← 近距高速光/声下载后浮出回传
```

数据骡子策略：节点少做远距声学发射，等 AUV 靠近用短距高速链路卸载，以延长电池寿命。

### 4.2 水下定位（无 GNSS）

全球导航卫星系统信号在水下几乎不可用，需声学基线或惯性组合[8]：

| 方法 | 原理 | 精度（示意） | 基础设施 |
|------|------|------|----------|
| LBL（长基线） | 海底信标三边测量 | 亚米–米级 | 需布放信标 |
| SBL（短基线） | 船底换能器阵列 | 米–十米级 | 需支持船 |
| USBL（超短基线） | 紧凑阵列测距测向 | 角度误差主导 | 需支持船 |
| 惯性导航（INS） | 加速度/角速度积分 | 随时间漂移 | 自主 |
| 地形匹配 | 声纳与地图相关 | 米–数十米 | 需地形库 |
| DVL 底跟踪 | 多普勒测对地速 | 航程百分比误差 | 自主 |

工程上常见 INS + 多普勒速度仪（Doppler Velocity Log, DVL）连续推算，辅以声学修正或近水面 GNSS 校准。

## 5 能量获取与供电

深海换电池往往需专用船，单次维护成本可很高。策略是超长待机或环境能量采集：

- **海流/波浪**：微型涡轮等，功率随流速强相关。
- **温差发电**：温跃层温差驱动热电，功率密度通常为 mW/cm² 量级（视温差）。
- **微生物燃料电池（MFC）**：功率密度往往很低，但可长期微弱供电。

低功耗节点以长睡眠 + 少传输为主；声学发射瞬时功耗可比采样高两个数量级，故"多采少传/边缘压缩"是关键。

```c
// 示意：长睡眠、短采样、稀疏声学上报
#define SLEEP_DURATION_S    3600
// 平均功耗取决于占空比与 Modem 发射能量，需按实测电池曲线核算
```

## 6 应用场景

### 6.1 海底管道巡检

全球海底油气管线总长可达数十万公里量级。IoT 思路是沿线传感持续监测压力、温度、声发射，异常时调度 AUV/遥控水下机器人（Remotely Operated Vehicle, ROV）精定位，降低纯人工巡检频率。

### 6.2 智慧水产养殖

深海网箱需溶解氧、pH、氨氮、影像行为与结构应变等。行业系统通过声学与水面浮标中继做远程投喂与水质调控[9]。

### 6.3 海洋科学观测

有线海底观测网以光缆供电通信，无线 AUV 做大范围补盲；二者互补而非互斥[10]。

## 7 局限、挑战与可改进方向

### 7.1 声信道容量与可靠性天花板

**局限**：多径、多普勒与噪声使水声链路误码与中断率远高于陆地蜂窝；"距离×速率"近似受物理约束，难以同时要远距与高吞吐[1]。
**改进**：自适应调制编码；环境感知的功率/频段选择；关键指令用强编码重复，大数据走 AUV 卸载。

### 7.2 光通信对准与水质敏感

**局限**：浑浊与相对运动使对准失败，实验室峰值速率难复现到近岸作业[2][6]。
**改进**：宽波束 LED 兜底 + 窄波束激光提速；微机电系统（MEMS）指向与合作信标；仅在对接/近距窗口启用光链路。

### 7.3 定位与授时基础设施昂贵

**局限**：高精度长基线信标布放与回收成本高，纯惯性方案漂移限制任务时长[8]。
**改进**：任务分级精度；协作 AUV 相对定位；定期上浮 GNSS 校准与地形匹配融合。

### 7.4 能源与运维闭环未打通

**局限**：能量采集功率不稳定，维护窗口稀缺，导致保守采样策略浪费观测价值。
**改进**：能量预测驱动的自适应占空比；故障可诊断的传感器健康字段；标准化湿插拔接口降低维护时间。

### 7.5 协议与仿真到海试鸿沟

**局限**：理想声速剖面仿真低估突发干扰与生物噪声；开源协议栈与商用 Modem 互操作有限[3][5]。
**改进**：海试数据集驱动的信道模型；Modem 抽象层；小规模湖试/港试门禁后再深海部署。

## 8 实践建议

1. **先仿真信道**：生成多径 + 多普勒，评估误码率，再谈组网。
2. **低成本声学实验**：压电换能器在泳池验证帧同步与简单调制。
3. **用 Aqua-Sim 等**做拓扑与路由，明确能耗模型假设。
4. **选型口诀**：远距低速选声；对接高速选光；极近距磁感应作补充。

## 参考文献

[1] M. Stojanovic and J. Preisig, "Underwater Acoustic Communication Channels: Propagation Models and Statistical Characterization," IEEE Communications Magazine, 2009.
[2] Z. Zeng et al., "A Survey of Underwater Optical Wireless Communications," IEEE Communications Surveys & Tutorials, 2017.
[3] I. F. Akyildiz et al., "Underwater Acoustic Sensor Networks: Research Challenges," Ad Hoc Networks, 2005.
[4] EvoLogics, "S2C R Series Underwater Acoustic Modems," Product Specification, 2024.
[5] J. Heidemann et al., "Underwater Sensor Networks: Applications, Advances, and Challenges," Philosophical Transactions of the Royal Society A, 2012.
[6] JAMSTEC, "Deep-sea Optical Communication System for Real-time Video Transmission," Technical Report, 2024.
[7] K. V. Mackenzie, "Nine-term Equation for Sound Speed in the Oceans," Journal of the Acoustical Society of America, 1981.
[8] M. Murad et al., "Underwater Localization: Current Challenges and Future Directions," IEEE Access, 2023.
[9] AKVA Group, "Cage Control System (CCS) for Aquaculture IoT," Product Overview, 2024.
[10] 中国科学院南海海洋研究所等相关单位, "南海海底科学观测网建设进展," 2024.
[11] M. Chitre, S. Shahabudeen, and M. Stojanovic, "Underwater Acoustic Communications and Networking: Recent Advances and Future Challenges," Marine Technology Society Journal, 2008.
[12] H. Kaushal and G. Kaddoum, "Underwater Optical Wireless Communication," IEEE Access, 2016.
