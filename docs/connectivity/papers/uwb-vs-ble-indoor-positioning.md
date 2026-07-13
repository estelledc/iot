---
schema_version: '1.0'
id: uwb-vs-ble-indoor-positioning
title: UWB与BLE室内定位精度对比
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 16
prerequisites:
  - uwb-positioning
  - ble-direction-finding-aoa-aod
tags:
  - UWB
  - BLE
  - 室内定位
  - AoA
  - RSSI
  - TDoA
  - 选型
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# UWB与BLE室内定位精度对比

> **难度**：🟡 中级 | **领域**：室内定位技术 | **阅读时间**：约 16 分钟

## 日常类比

仓库找货：“东边那片”对比“第三排第二层左三格”。BLE（Bluetooth Low Energy）RSSI/指纹常像前者；UWB（Ultra-Wideband）ToF 更像后者。AoA（Angle of Arrival）BLE 介于两者之间，但仍受多径制约[1][2][3]。

## 摘要

对比 UWB（TWR/TDoA）与 BLE（RSSI 指纹、5.1 方向寻找、后续信道探测叙事）的原理、精度量级、成本、功耗与场景映射。表中数字为文献与工程常见量级，**须用本场实测校准**[1][4]。

## 1. 室内定位共同模型

GPS 室内衰减与多径严重。通用做法：已知坐标参考点 + 测距/测角/指纹 → 解算位置[1][2]。

| 观测量 | 典型技术 | 主要误差源 |
|--------|----------|------------|
| ToF | UWB TWR | NLOS、校准 |
| 时差 | UWB TDoA | 锚点同步 |
| RSSI | BLE 指纹/测距 | 人体、家具、时变 |
| 相位角 | BLE AoA/AoD | 多径、阵列校准 |

## 2. UWB 路径

大带宽支撑细时间分辨与首达检测；DS-TWR 抑频偏；多锚三边或 TDoA 成网。基础设施需专用锚点、供电/回传；TDoA 另需纳秒级同步[1][5]。

## 3. BLE 路径

**RSSI 指纹**：离线建库、在线匹配；环境改动要重训，精度多为米级叙事[2]。
**AoA/AoD**：天线阵列测向，精度可到亚米量级（良好 LOS），定位器成本高于普通信标[3]。
**信道探测（如 BLE 高版本 CS 叙事）**：试图逼近更好测距，生态与现场成熟度需单独评估[3][6]。

## 4. 对比表

| 方案 | 精度量级（常见叙述） | 基建特点 | 手机普及 |
|------|----------------------|----------|----------|
| UWB TWR/TDoA | 分米到厘米级潜力 | 锚点贵、常需布线 | 旗舰增多 |
| BLE AoA | 亚米级常见目标 | 阵列定位器 | 广 |
| BLE RSSI 指纹 | 数米级常见 | 信标便宜 | 广 |

| 维度 | UWB 倾向 | BLE 倾向 |
|------|----------|----------|
| 刷新/时延 | 可更高、更低时延 | 受广播/扫描间隔限制 |
| 标签成本 | 更高 | 更低 |
| NLOS | 相对可检测/部分保持 | RSSI/角度退化重 |
| 电池 | 高刷新吃电 | 长寿命更容易 |

功耗与电池月数强烈依赖汇报周期，表意仅作相对比较[4][5]。

## 5. 场景与混合

- **偏 UWB**：叉车防碰撞、AGV、门哪一侧、座位级占用。
- **偏 BLE**：客流区域统计、展品接近触发、房间级资产存在。
- **混合**：高精度区 UWB + 大面积 BLE；双模标签；BLE 唤醒再开 UWB[4][7]。

## 6. 局限、挑战与可改进方向

### 1. 用单一标称精度选型

**局限**：忽略 P95、NLOS 占比与安装几何。
**改进**：按分区验收；报告误差分布而非均值广告[1][4]。

### 2. 指纹库腐烂

**局限**：装修/货架变动后 BLE 指纹失效。
**改进**：定期重采集；或改 AoA/UWB 减少指纹依赖[2]。

### 3. TCO 误判

**局限**：只比信标单价，忽略布线、同步、校准与维护。
**改进**：五年 TCO 模型；混合部署压成本[5][7]。

### 4. 技术边界快速变化

**局限**：BLE 测距增强与 UWB 降本改变“绝对分工”。
**改进**：架构预留融合定位服务，避免绑死单一无线电[3][6]。

## 7. 实践要点

1. 先定业务粒度（房间/货位/防撞）。
2. 实时安全链路优先 UWB 并做延迟预算。
3. 手机定位优先评估 BLE 覆盖，UWB 作增强。

## 参考文献

[1] Alarifi, A. et al., UWB indoor positioning, Sensors, 2016.
[2] Faragher, R. and Harle, R., BLE beacon fingerprinting, IEEE JSAC, 2015.
[3] Bluetooth SIG, Core Spec direction finding / related feature overviews.
[4] Sadowski, S. and Spachos, P., RSSI-based IoT localization, IEEE Access, 2018.
[5] FiRa Consortium, UWB technology and use cases.
[6] Bluetooth SIG materials on Channel Sounding (evaluate maturity separately).
[7] Industry deployment notes on hybrid UWB+BLE RTLS.
[8] IEEE 802.15.4z-2020.
[9] Sahinoglu et al., UWB positioning systems (book).
[10] Qorvo/NXP UWB RTLS application notes.
[11] Zafari, F. et al., indoor positioning systems survey, IEEE ComST.
[12] Ridolfi, M. et al., experimental UWB evaluation, Sensors.
