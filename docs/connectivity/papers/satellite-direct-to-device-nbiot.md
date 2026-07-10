---
schema_version: '1.0'
id: satellite-direct-to-device-nbiot
title: 卫星直连设备NTN NB-IoT技术分析
layer: 2
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 卫星直连设备NTN NB-IoT技术分析
> **难度**：🔴 高级 | **领域**：卫星直连IoT | **阅读时间**：约 22 分钟

## 引言

假设你买了一个快递追踪器贴在包裹上, 它在城市里用 NB-IoT 基站汇报位置。但当包裹装上远洋货轮, 驶入大海后, 基站信号消失了。如果这个追踪器不需要换芯片、不需要换天线, 只要固件升级一下就能连上天上的卫星继续汇报位置, 那该多好? 这正是 3GPP NTN(非地面网络)标准要实现的目标: 让现有的 NB-IoT 设备直接连接卫星。

本文深入分析 NTN NB-IoT 的技术挑战、3GPP 的适配方案、链路预算、芯片支持和部署前景。

## 1 NTN概述

### 1.1 什么是非地面网络

NTN(Non-Terrestrial Network)是 3GPP 在 Release 17 中引入的标准, 将卫星(以及高空平台 HAPS)纳入蜂窝网络架构。核心思想是: 卫星不再是独立的通信系统, 而是蜂窝网络的一个组成部分。

### 1.2 NTN的标准化历程

```
3GPP NTN 时间线:
Release 15 (2018): 开始研究卫星与 5G 的融合(TR 38.811)
Release 16 (2020): 进一步研究, 定义架构和信道模型
Release 17 (2022): 正式标准化 NR NTN 和 IoT NTN(NB-IoT/eMTC)
Release 18 (2024): 增强功能, 覆盖优化, 移动性改进
```

### 1.3 NTN for IoT的价值

NTN 对 IoT 的核心价值在于复用: 复用现有蜂窝协议(NB-IoT/eMTC)、复用现有芯片架构(固件更新即可支持)、复用现有产业生态(运营商、设备商、云平台), 无需建立全新的卫星 IoT 生态系统。

## 2 卫星链路的关键挑战

### 2.1 传播延迟

地面蜂窝通信的基站距离通常在几百米到几十公里, 传播延迟可以忽略。但卫星链路完全不同:

```
传播延迟计算(光速 c = 300000 km/s):

LEO 600km 轨道:
  单程最短距离(天顶): 600km -> 延迟 2ms
  加上仰角影响, 实际单程延迟: 2-13ms
  往返延迟(RTT): 4-26ms

GEO 36000km 轨道:
  单程延迟: 约 120ms, 往返延迟: 约 240ms

对比地面蜂窝(基站 10km): 往返延迟约 0.067ms
```

这意味着 NB-IoT 协议中所有基于时间的参数(定时提前量 TA、HARQ 反馈时间)都需要重新设计。

### 2.2 多普勒频移

LEO 卫星相对地面高速运动, 导致严重的多普勒频移:

```
多普勒频移计算:
卫星速度 v = 7.5 km/s (LEO 600km)
载波频率 f = 2 GHz

最大多普勒频移:
  fd = f * v / c = 2e9 * 7500 / 3e8 = 50 kHz (理论最大)
  实际最大值(考虑仰角): 约 24 kHz

NB-IoT 子载波间隔: 15 kHz 或 3.75 kHz
多普勒频移远大于子载波间隔 -> 不补偿则无法解调
```

### 2.3 大小区

卫星覆盖的小区远大于地面基站: 地面基站小区半径 1-30km, LEO 卫星波束覆盖直径可达数百公里。同一小区内设备到卫星的距离差异巨大, 导致差分延迟和差分多普勒。

## 3 3GPP NTN适配方案

### 3.1 定时提前量预补偿

地面 NB-IoT 中, 基站告诉设备 TA 值来补偿传播延迟。但卫星链路的延迟太大, 超出了原有 TA 范围:

```
解决方案: 设备端预补偿
设备通过 GNSS 获取自身位置 (lat, lon, alt)
设备获取卫星星历数据 (卫星位置和轨迹)
设备自主计算到卫星的距离和延迟
设备在发射时提前发送, 补偿传播延迟

预补偿精度要求:
  残余定时误差需 < 循环前缀(CP)长度
  NB-IoT CP 约 4.7us(对应约 1.4km 距离误差)
  GNSS 定位精度 10-50m, 足够满足要求
```

### 3.2 多普勒预补偿

```python
# 多普勒预补偿流程
def doppler_precompensation(device_pos, sat_ephemeris, carrier_freq):
    # 1. 根据星历计算当前时刻卫星位置和速度
    sat_pos, sat_vel = compute_satellite_state(sat_ephemeris)

    # 2. 计算设备到卫星的径向速度
    los_vector = sat_pos - device_pos
    los_unit = los_vector / norm(los_vector)
    radial_vel = dot(sat_vel, los_unit)

    # 3. 计算并反向补偿多普勒频移
    doppler_shift = carrier_freq * radial_vel / 3e8
    tx_freq = carrier_freq - doppler_shift
    return tx_freq
```

补偿后残余多普勒通常在几百 Hz 以内, NB-IoT 接收机可以处理。

### 3.3 扩展HARQ时序

地面 NB-IoT 的 HARQ 假设很短的 RTT。NTN 中 RTT 增大到数十毫秒, 需要更多 HARQ 进程并行运行, 或者禁用 HARQ 依赖 RLC 层重传。3GPP 选择扩展 HARQ 反馈定时器, 增加并行进程数。

### 3.4 随机接入适配

RACH 过程也需要修改: 设备发送 Preamble 前已预补偿 TA, 竞争窗口需要扩大(RTT 更长), 随机接入响应(RAR)窗口需要扩展。

## 4 架构选项

### 4.1 透明转发(Transparent Payload)

```
[IoT设备] --上行射频--> [LEO卫星(弯管)] --馈电链路--> [地面gNB]

特点:
- 卫星只做频率转换和放大, 所有基带处理在地面完成
- 实现简单, 卫星成本低
- 缺点: 需要地面站在卫星波束覆盖范围内
```

### 4.2 再生转发(Regenerative Payload)

```
[IoT设备] --NB-IoT空口--> [LEO卫星(星上gNB)] --星间/馈电链路--> [核心网]

特点:
- 卫星搭载 gNB 处理功能, 在星上解调处理
- 无需地面站实时连接, 灵活性好
- 复杂度高, 卫星成本高
```

目前大多数 NTN IoT 方案采用透明转发, 再生转发是长期演进方向。

## 5 NB-IoT NTN技术细节

### 5.1 支持的轨道

| 轨道类型 | 高度 | 典型RTT | 多普勒特性 |
|---------|------|---------|-----------|
| LEO-600 | 600km | 8-26ms | 高多普勒, 变化快 |
| LEO-1200 | 1200km | 16-48ms | 中等多普勒 |
| GEO | 36000km | 540ms | 低多普勒 |

LEO 是 IoT NTN 的主要目标, 延迟更低、终端成本更低。

### 5.2 频段

NTN IoT 主要使用 S-band(2 GHz 附近): 上行 1980-2010 MHz, 下行 2170-2200 MHz。该频段与地面蜂窝频段接近, 可以复用终端射频设计。

### 5.3 覆盖增强

NB-IoT 本身具备强大的覆盖增强能力, 在 NTN 场景中至关重要:

- 重复传输(Repetition): 最大 2048 次重复, 每次重复增加约 3dB 增益(理论上)
- 窄带集中能量: NB-IoT 带宽仅 180kHz(1 个 PRB), 接收端噪声带宽小
- 低速率传输: 最低单子载波 3.75kHz 间隔, 链路预算好

## 6 链路预算分析

### 6.1 上行链路预算

```
NB-IoT NTN 上行链路预算(LEO 600km, S-band):

项目                           | 值
-------------------------------|----------
设备发射功率(23dBm)            | 23.0 dBm
设备天线增益                   | 0.0 dBi
EIRP                           | 23.0 dBm
自由空间路径损耗(600km, 2GHz)  | -154.0 dB
大气损耗                       | -0.5 dB
闪烁余量                       | -2.0 dB
卫星天线增益                   | 30.0 dBi
接收 C/N0                      | 102.3 dB-Hz
所需 C/N0 (含重复增益)          | 95.0 dB-Hz
链路余量                       | 7.3 dB

结论: 23dBm 功率等级的 NB-IoT 设备配合重复传输
和卫星高增益天线, 可以关闭 600km 上行链路, 约 7dB 余量。
```

## 7 多普勒处理详解

### 7.1 多普勒动态特性

```
LEO 600km 卫星过顶场景(2GHz 载波):

仰角    | 距离    | 多普勒频移
--------|---------|------------
10度    | 1932km  | +24 kHz (接近)
30度    | 936km   | +18 kHz
90度    | 600km   | 0 kHz (天顶)
30度    | 936km   | -18 kHz
10度    | 1932km  | -24 kHz (远离)
```

### 7.2 预补偿精度

设备通过 GNSS 位置和卫星星历预补偿多普勒。补偿后残余通常小于 500 Hz, 而 NB-IoT 3.75kHz 子载波可容忍约 950 Hz 偏移, 在可接受范围内。

## 8 功耗考量

### 8.1 GNSS的额外功耗

```
功耗对比(每天发一次数据):

纯地面 NB-IoT:
  休眠: 5uA * 24h = 120 uAh
  发射 + 接收: 约 12 uAh
  日均: 约 132 uAh

NTN NB-IoT:
  休眠: 5uA * 24h = 120 uAh
  GNSS 定位(热启动): 30mA * 30s = 250 uAh
  发射(含重复) + 接收: 约 139 uAh
  日均: 约 509 uAh

NTN 功耗约为地面的 3-4 倍, 但仍可接受。
1000mAh 电池: 地面约 21 年, NTN 约 5 年。
```

### 8.2 优化策略

优化手段包括: A-GNSS 辅助数据加速定位、星历缓存减少重复获取、过顶预测减少无效唤醒, 以及 PSM/eDRX 节能模式在非传输时段深度休眠。

## 9 芯片支持

### 9.1 已发布的NTN IoT芯片

| 芯片 | 厂商 | 特点 |
|------|------|------|
| 212S/215S | Qualcomm | NB-IoT + eMTC NTN, 集成 GNSS |
| MT6825 | MediaTek | NB-IoT NTN, 低功耗设计 |
| ALT1350 | Sony Altair | NTN + 地面双模, 超低功耗 |
| nRF9151 | Nordic | 计划支持 NTN, 强开发者生态 |

### 9.2 芯片设计要点

NTN IoT 芯片与纯地面芯片的主要差异: 集成 GNSS 接收机、更大的频率补偿范围(覆盖多普勒频移)、更大的定时提前量范围、星历数据存储和处理能力。

## 10 应用场景

### 10.1 全球资产追踪

最直接的应用场景:

```
集装箱全程追踪示例:

1. 工厂装货: NB-IoT 地面网络, 每 10 分钟上报
2. 运往港口: 沿途有基站, 继续用地面
3. 装船出海: 自动检测无地面覆盖, 切换 NTN
4. 远洋运输: 每小时通过卫星上报位置和状态
5. 到达目的港: 检测到地面信号, 切回 NB-IoT
6. 内陆运输: 继续使用地面网络

全程无缝, 同一个芯片和 SIM 卡
运营商通过 NTN 漫游协议统一计费
```

### 10.2 远程农业

```
场景: 偏远牧场监测系统

设备配置:
  传感器: 土壤温湿度 + 风速 + 降雨量
  通信模块: NB-IoT NTN 双模
  电池: 2000mAh 锂亚硫酰氯
  预期寿命: 3-5 年

工作模式:
  有基站覆盖区域: 普通 NB-IoT, 低成本
  偏远牧场(无基站): 自动切换 NTN
  上报频率: 每小时一次
  数据量: 每次约 50 字节
```

### 10.3 海上监测

海上场景天然需要卫星连接: 渔船安全追踪和电子围栏、海洋浮标的水温和盐度和洋流监测、海上风电设施结构健康监控、远洋货轮集装箱温湿度和开关门状态。

### 10.4 应急通信

地面网络中断时, NTN 可作为备用: 自然灾害后的传感器数据回传、偏远地区的 SOS 信标、灾后基础设施状态评估、救援队伍定位和协调。

## 11 部署时间线

### 11.1 标准与产业进展

```
里程碑:
2022 Q2: Release 17 冻结, IoT NTN 规范完成
2023:    芯片厂商开始流片 NTN IoT 芯片
2024:    首批商用 NTN IoT 服务启动
2025-26: 大规模商用, 设备成本进一步降低

运营商合作示例:
  Vodafone + AST SpaceMobile: 手机直连卫星
  T-Mobile + SpaceX: Starlink Direct-to-Cell
  多家运营商与 Skylo, MediaTek, Qualcomm 合作
  目标: NB-IoT NTN 作为蜂窝 IoT 的全球覆盖补充
```

### 11.2 挑战

```
主要挑战:

频谱协调:
  不同国家的 S-band 分配差异
  需要全球统一或至少区域协调

星地干扰:
  卫星和地面网络共用频谱
  需要干扰管理和频率协调机制

商业模式:
  NTN 漫游协议设计
  地面+卫星混合计费体系
  运营商和卫星运营商的分成

设备认证:
  NTN 设备需要额外射频测试
  跨国认证流程复杂
```

## 总结

NTN NB-IoT 是卫星 IoT 领域最具变革性的技术方向。它不是建立一个全新的卫星通信系统, 而是将已经拥有数十亿设备生态的蜂窝 IoT 协议延伸到太空。通过 GNSS 辅助的定时和多普勒预补偿, 标准 NB-IoT 设备只需固件更新就能连接 LEO 卫星。

链路预算分析表明, 23dBm 功率等级的设备配合 NB-IoT 的重复传输机制和卫星高增益天线, 可以关闭 600km LEO 链路并留有余量。功耗虽然比纯地面场景高 3-4 倍, 但对于多数 IoT 应用仍然可接受。

随着 Qualcomm、MediaTek、Sony 等芯片厂商的 NTN IoT 芯片陆续量产, 以及运营商与卫星运营商的合作推进, NTN NB-IoT 有望在 2025-2026 年进入规模商用, 真正实现 IoT 设备的全球连接。

## 参考文献

- [3GPP TS 36.331. "NB-IoT and eMTC support for Non-Terrestrial Networks." Release 17, 2022.](https://www.3gpp.org/specifications)
- [Lin, X. et al. "5G New Radio Evolution Meets Satellite Communications." IEEE Communications Magazine, 2021.](https://ieeexplore.ieee.org/document/9508897)
- [Liberg, O. et al. "Satellite NB-IoT: Design and Analysis." IEEE Trans. Vehicular Technology, 2023.](https://ieeexplore.ieee.org/document/10036405)
- [Qualcomm. "Satellite IoT NTN: Connecting the Unconnected." White Paper, 2023.](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/satellite-iot-ntn-whitepaper.pdf)
