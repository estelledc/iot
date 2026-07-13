---
schema_version: '1.0'
id: indoor-positioning-survey
title: 室内定位技术综述
layer: 7
content_type: survey
difficulty: beginner
reading_time: 26
prerequisites:
  - uwb-positioning
  - ble-direction-finding-aoa-aod
tags:
  - 室内定位
  - UWB
  - BLE AoA
  - WiFi RTT
  - VLP
  - 融合定位
  - Channel Sounding
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 室内定位技术综述

> **难度**：🟢 入门 | **领域**：定位与导航、智慧空间 | **阅读时间**：约 26 分钟

## 日常类比

户外用全球定位系统（Global Positioning System, GPS）找路，像在空旷操场看太阳和路牌——天空开阔，参照物稳定。一进商场、医院、地下车库，就像钻进没有窗户的迷宫：卫星信号被楼板挡住，还在金属货架之间来回反弹，距离读数会"骗人"。

室内定位系统（Indoor Positioning System, IPS）要回答的是：没有 GPS 时，人和物在哪？超宽带（Ultra-Wideband, UWB）、蓝牙到达角、Wi-Fi 往返时延、可见光与射频识别（Radio Frequency Identification, RFID）各像不同工具——卷尺、指南针、已有电灯与廉价贴纸——精度、成本与施工量不同，常常要组合使用。

## 一句话总结

本综述对比 UWB、蓝牙低功耗（Bluetooth Low Energy, BLE）到达角/出发角（Angle of Arrival / Angle of Departure, AoA/AoD）、Wi-Fi 精细授时测量（Fine Timing Measurement, FTM/RTT）、可见光定位（Visible Light Positioning, VLP）与 RFID 的精度–成本–基础设施权衡，并讨论融合滤波与 2024–2025 标准进展；市场与精度数字来自报告与论文，现场应以勘测验收为准 [1][4]。

## 1 室内定位为什么难？

**遮挡与多径**：混凝土墙可使 GNSS 信号衰减数十 dB；反射路径使基于飞行时间的测距出现偏差 [1]。

**缺基础设施**：每种技术通常要额外部署锚点/信标/改造灯具，带来成本与施工。

**精度需求多样**：商场导航约数米即可；仓储资产约 1 m；自动导引车（Automated Guided Vehicle, AGV）常要分米甚至厘米；手术器械可能要厘米级——没有单一技术通吃。

市场研究机构对全球室内定位市场给出高速增长预测（例如从约百亿美元增至数百亿、年复合增长率约两成量级），口径随定义（硬件/软件/服务）变化，仅作产业热度参考 [4]。

## 2 主流技术详解

### 2.1 UWB

IEEE 802.15.4z 定义安全测距等增强。UWB 发射极窄脉冲（亚纳秒–数纳秒），带宽常 >500 MHz，时间分辨率高，可测飞行时间（Time of Flight, ToF）；双向测距（Two-Way Ranging, TWR）或到达时间差（Time Difference of Arrival, TDoA）解算位置 [3][7]。

- **精度**：视距（Line of Sight, LOS）常见约 10–30 cm；非视距（Non-Line of Sight, NLOS）可退化到约 0.3–1 m
- **优势**：抗多径相对强、可安全测距（STS 等）
- **劣势**：专用锚点成本与密度；单锚覆盖常约数十米
- **成本示意**：锚点数十–数百美元，标签十–五十美元；万平米仓库锚点数十个量级，硬件总成本数千–两万美元量级（视密度）

代表：手机 UWB 芯片、NXP/Qorvo 模组等。

### 2.2 BLE AoA/AoD

蓝牙 5.1 方向寻找：天线阵列测相位差得入射角。AoA 适合大量廉价标签 + 贵定位器；AoD 适合基础设施发射、手机接收导航 [1]。

- **精度**：开阔约 0.5–1 m，复杂环境约 1–3 m
- **优势**：手机生态、标签便宜、功耗极低
- **劣势**：多径敏感；阵列定位器单价较高

### 2.3 Wi-Fi RTT/FTM

基于 IEEE 802.11mc 等：手机与接入点（Access Point, AP）交换 FTM，用 RTT/2×光速估距，多 AP 三边定位 [5]。

- **精度**：Wi-Fi 6/6E 常见约 1–2 m；更宽带宽（Wi-Fi 7 的 320 MHz）有望进一步改善，但仍受多径制约
- **优势**：复用已有 AP；Android 对 RTT API 有支持
- **劣势**：需 AP 支持 FTM；功耗高于 BLE

### 2.4 VLP

LED 以人眼难察频率调制 ID/位置；摄像头或光电接收解码。高精度模式可达分米级，ID 近似定位约米级 [8]。

- **优势**：无射频干扰友好；可借照明改造
- **劣势**：需 LOS；驱动改造；终端支持有限

### 2.5 RFID

无源超高频标签靠读写器供能回 ID；可用接收信号强度（Received Signal Strength Indicator, RSSI）或相位粗定位。有源标签精度与距离更好但需电池。

- **精度**：无源约 1–3 m（强依赖密度）；有源约 0.5–2 m
- **优势**：无源标签成本极低、可批量盘点
- **劣势**：实时性与精度一般

## 3 技术全面对比

| 维度 | UWB | BLE AoA | Wi-Fi RTT | VLP | RFID（无源） |
|------|-----|---------|-----------|-----|--------------|
| 精度 | 约 10–30 cm | 约 0.5–1 m | 约 1–2 m | 约 10–50 cm | 约 1–3 m |
| 覆盖/锚点 | 约 30–50 m | 约 30–50 m | 约 30–50 m | 灯具间距 | 约 3–10 m |
| 标签功耗 | 低 | 极低 | 高（手机 Wi-Fi） | 可无标签 | 零 |
| 标签成本 | 中 | 低 | 手机复用 | 手机复用 | 极低 |
| 基础设施 | 高 | 中–高 | 低（复用） | 中 | 中 |
| 实时性 | 优 | 良 | 中 | 良 | 较差 |
| 抗多径 | 强 | 弱–中 | 弱 | 强（需 LOS） | 弱 |
| 安全测距 | 支持（4z） | 传统不支持 | 不支持 | 不支持 | 不支持 |
| 典型场景 | AGV/仓储 | 资产/导航 | 商场/机场 | 零售/博物馆 | 库存盘点 |

## 4 场景选型指南

| 场景 | 核心需求 | 推荐倾向 |
|------|----------|----------|
| 商场/机场导航 | 大覆盖、手机可用、成本可控 | Wi-Fi RTT + BLE AoD |
| 仓库资产追踪 | 大量标签、约 1 m | BLE AoA；要亚米则 UWB |
| 工业 AGV | <10 cm、<100 ms | UWB + IMU 紧耦合 |
| 医院敏感区 | 低 RF 干扰 | VLP + 一般区 BLE |
| 大规模盘点 | 极低标签成本 | 无源 RFID |

零售盘点效率提升可达一个数量级以上（视原流程），以企业案例为准。

## 5 融合定位

| 融合方案 | 互补逻辑 | 典型精度（示意） |
|----------|----------|------------------|
| UWB + IMU | 绝对校准 + 短时航迹 | 约 10–20 cm |
| BLE + Wi-Fi | 粗定位 + 房间级精化 | 约 1–3 m |
| UWB + BLE | 关键区高精度 / 一般区低成本 | 自适应 |
| VLP + BLE | 灯下精定位 / 过道补盲 | 约 0.2–1 m |
| Wi-Fi + 地磁 | 初始定位 + 指纹航迹 | 约 2–5 m |

算法：扩展卡尔曼滤波（Extended Kalman Filter, EKF）工程常用；粒子滤波适合强非线性；图优化精度高但偏离线；深度学习融合在复杂室内可优于经典滤波，但需大量标注 [6][10]。

## 6 部署实践要点

- **站点勘测**：平面图、墙体材质、多径热点；可用 Ekahau/iBwave 等辅助
- **密度经验**：UWB 锚点间距常约 15–20 m（保证可见 ≥3）；BLE AoA 定位器更密；Wi-Fi 还受容量规划约束
- **坐标系**：本地原点 + 必要时与户外 GNSS 衔接

## 7 标准与产业进展（2024–2025）

- **IEEE 802.15.4z / FiRa**：安全测距与互操作认证推进 [3][7]
- **Bluetooth 6.0 Channel Sounding**：基于相位的测距，目标缩小与 UWB 的精度差距，生态设备基数大 [2]
- **Wi-Fi 7**：更宽带宽改善 RTT 时间分辨率；多链路可稳定测距 [5]
- **3GPP**：新空口定位增强、载波相位与旁路链路等方向，使基站兼作锚点 [9]
- **消费地图**：厂商室内 AR 导航覆盖场馆数持续增加（以产品公告为准）

## 局限、挑战与可改进方向

### 1. NLOS 仍是主误差源

**局限**：人体遮挡、墙体、金属货架使 ToF/角度误差陡增 [1]。
**改进**：NLOS 识别与剔除；UWB+IMU；地图约束与粒子滤波。

### 2. 部署与运维成本被低估

**局限**：锚点校准、电池更换、位置漂移导致精度缓慢恶化。
**改进**：供电优先有线锚点；健康心跳与自标定；运维 SLA 写入合同。

### 3. 隐私与合规

**局限**：连续轨迹属敏感个人信息，受 GDPR 等约束。
**改进**：目的限定与最短留存；默认聚合热力而非个体轨迹；显式同意。

### 4. 单技术指标难复现

**局限**：厂商"10 cm"多在空旷 LOS 实验室；商场实测可能差一个数量级。
**改进**：按场景验收（分位数误差、可用性）；公开测试路线与遮挡条件。

### 5. 标准碎片化

**局限**：UWB/BLE/Wi-Fi 生态互操作仍不完善。
**改进**：优先认证产品（FiRa 等）；融合层抽象多种测距源；关注 Channel Sounding 成熟度再押注单一路线。

## 参考文献

[1] F. Zafari et al., "A Survey of Indoor Localization Systems and Technologies," IEEE Communications Surveys & Tutorials, 2024.
[2] Bluetooth SIG, "Bluetooth Core Specification 6.0: Channel Sounding," 2024.
[3] IEEE Std 802.15.4z, "Enhanced Ultra-Wideband Physical Layer," 2020/Amd updates.
[4] Markets and Markets, "Indoor Location Market: Global Forecast to 2029," 2024.
[5] D. Feng et al., "WiFi FTM-Based Indoor Positioning: A Comprehensive Study," IEEE Internet of Things Journal, 2024.
[6] L. Chen et al., "Deep Learning for Indoor Positioning: A Comprehensive Survey," ACM Computing Surveys, 2024.
[7] FiRa Consortium, "UWB Indoor Positioning Interoperability Specification," 2024.
[8] Signify (Philips), "Visible Light Communication Indoor Positioning: Retail Case Studies," 2024.
[9] 3GPP TR 38.857, "Study on NR Positioning Enhancements," Rel-18, 2024.
[10] L. Pei et al., "Fusion of UWB and IMU for Robust Indoor Navigation," IEEE TIM, 2024.
[11] Y. Gu et al., "A Survey of Indoor Positioning Systems," IEEE Communications Surveys & Tutorials, earlier foundational survey.
[12] D. Dardari et al., "Indoor Tracking: Theory, Methods, and Technologies," IEEE Transactions on Vehicular Technology.
[13] S. He and S.-H. G. Chan, "Wi-Fi Fingerprint-Based Indoor Positioning: Recent Advances and Comparisons," IEEE Communications Surveys & Tutorials.
[14] A. Alarifi et al., "Ultra Wideband Indoor Positioning Technologies: Analysis and Recent Advances," Sensors.
[15] M. Ji et al., "Analysis of Bluetooth 5.1 Angle of Arrival for Indoor Localization," IEEE Access.
[16] P. Bahl and V. Padmanabhan, "RADAR: An In-Building RF-based User Location and Tracking System," IEEE INFOCOM (经典指纹定位).
