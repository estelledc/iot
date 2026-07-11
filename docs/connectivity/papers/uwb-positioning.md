---
schema_version: '1.0'
id: uwb-positioning
title: UWB 超宽带高精度定位技术
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites: UNKNOWN
tags:
  - UWB
  - 室内定位
  - TWR
  - TDoA
  - AoA
  - 802.15.4z
  - 资产追踪
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# UWB 超宽带高精度定位技术

> **难度**：🟡 中级 | **领域**：短距通信与定位 | **阅读时间**：约 16 分钟

## 日常类比

在大厅拍一下手，靠回声延迟估墙距；若持续哼音，原声与回声糊成一片。UWB（Ultra-Wideband）短脉冲像拍手，便于测 ToF（Time of Flight）并分辨多径首达；BLE/Wi‑Fi 窄带更像哼音，RSSI 易被环境搅乱[1][2]。

## 摘要

UWB 以大带宽脉冲支撑厘米量级测距潜力，再经 TWR、TDoA、AoA 等几何方法定位。802.15.4z 补充 STS 等安全测距能力。文中精度、功耗倍数与部署成本为量级对照，**依赖 LOS、锚点几何与刷新率**[1][3]。

## 1. 物理层要点

脉冲宽度纳秒量级、带宽常 ≥500 MHz，使到达时刻估计更细。室内多径下，宽带宽有助于在时间上分离直达与反射，测距优先用首达路径[1][4]。

发射功率谱密度受各国法规严格限制（如常见引用的 −41.3 dBm/MHz 量级上限），故单链路距离与穿透有限，需靠锚点密度补覆盖[5][6]。

## 2. 标准与模式

IEEE 802.15.4z 增强脉冲无线电测距安全（STS 等）。实现上常见 HRP（High Rate Pulse）消费/手机路线；LRP（Low Rate Pulse）等面向更长距离/特定工业叙事——**以标准条款与芯片支持矩阵为准**[1][7]。

| 维度 | TWR 路线 | TDoA 路线 | AoA 辅助 |
|------|----------|-----------|----------|
| 同步需求 | 链路内自洽 | 锚点紧同步 | 阵列校准 |
| 标签负担 | 收发交互 | 可偏发送 | 视实现 |
| 适合 | 少标签高精度 | 多标签追踪 | 方向+距离（如寻物 UI） |

## 3. 定位算法

**TWR / DS-TWR**：往返测距，DS 变体抑制时钟频偏[1][3]。
**TDoA**：到达时间差双曲线交会；容量与标签功耗友好，同步是工程核心[2][8]。
**AoA**：天线阵列相位差估入射角；可与测距组合（消费级“精确查找”常见叙事）[9]。

| 技术（示意） | 原理 | 精度量级叙事 |
|--------------|------|----------------|
| UWB TWR/TDoA | ToF / 时差 | 常优于米级 BLE RSSI |
| BLE AoA / CS | 角度 / 信道探测 | 亚米到数十厘米量级（视实现） |
| Wi‑Fi RTT/指纹 | FTM / RSSI | 米级常见 |

具体数字应引用现场测试，避免把营销标称当 SLA[2][10]。

## 4. 应用与生态

数字车钥匙（CCC + UWB）、工业资产/人员追踪、虚拟安全围栏、消费寻物等。芯片生态包括 NXP Trimension、Qorvo DW 系列、手机自研 UWB、三星等；价格随出货量下降，但仍高于纯 BLE 标签方案[7][11]。

## 5. 局限、挑战与可改进方向

### 1. 功耗高于 BLE 常开场景

**局限**：高频测距耗电，纽扣标签难支撑高刷新。
**改进**：BLE 发现/粗定位 + 按需 UWB；降低汇报率；短 STS 与休眠策略权衡安全[3][7]。

### 2. 锚点基建成本

**局限**：供电、回传、校准使 TCO 高于信标方案。
**改进**：仅对高精度区部署 UWB；其余区 BLE；统一坐标系融合[8][10]。

### 3. 法规与信道碎片

**局限**：美/欧/中等允许频段与 LBT 等要求不同。
**改进**：优先全球较通用信道（如常讨论的 Ch5/Ch9）；分区 SKU[5][6]。

### 4. NLOS 与几何劣化

**局限**：遮挡与共线锚点使误差膨胀。
**改进**：锚点立体布局；NLOS 检测；滤波与完整性告警[2][8]。

## 6. 实践要点

1. 先写清精度是 P50 还是 P95、LOS 还是全场。
2. 安全场景必须升到 STS/密钥生命周期，不只买“UWB 芯片”。
3. 产线天线延迟与固件配置绑定版本。

## 参考文献

[1] IEEE Std 802.15.4z-2020, Enhanced Impulse Radio.
[2] Alarifi, A. et al., UWB indoor positioning survey, Sensors, 2016.
[3] Singh, M. et al., UWB ranging/localization tutorials, IEEE literature.
[4] Sahinoglu, Z. et al., Ultra-Wideband Positioning Systems, CUP.
[5] FCC / ETSI UWB regulatory documents (power and band limits).
[6] 中国工信部等 UWB 设备无线电管理相关文件（以正式稿为准）.
[7] FiRa Consortium, UWB technical overview.
[8] Monica, S. and Ferrari, G., anchor placement for UWB localization, IEEE Access.
[9] Apple, Nearby Interaction framework documentation.
[10] Faragher, R. and Harle, R., BLE fingerprinting, IEEE JSAC, 2015 (contrast).
[11] Qorvo DW3000 / NXP Trimension product briefs.
[12] CCC, Digital Key UWB ranging profile public materials.
[13] Ridolfi, M. et al., experimental UWB positioning, Sensors.
