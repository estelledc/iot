---
schema_version: '1.0'
id: ble-direction-finding-aoa-aod
title: BLE测向技术AoA/AoD室内定位原理
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - ble-5-features-coded-phy
  - ble-periodic-advertising-sync
tags:
  - BLE
  - AoA
  - AoD
  - 室内定位
  - CTE
  - 天线阵列
  - 测向
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# BLE测向技术AoA/AoD室内定位原理

> **难度**：🔴 高级 | **领域**：BLE定位技术 | **阅读时间**：约 22 分钟

## 日常类比

闭眼坐在房间里听人拍手：双耳到达时间差告诉你声源偏左还是偏右。蓝牙低功耗（Bluetooth Low Energy, BLE）5.1 测向类似——多天线对同一恒定载波采相位差，估到达角或出发角，再配合多定位器三角测量做室内定位。精度高度依赖阵列校准与多径环境，**宜作量级参考**而非保证值[1][8]。

## 摘要

本文说明恒定音频扩展（Constant Tone Extension, CTE）、到达角（Angle of Arrival, AoA）与出发角（Angle of Departure, AoD）的机制、阵列约束、MUSIC 类估计算法，以及与超宽带（Ultra-Wideband, UWB）等方案的选型边界。文中精度、成本与续航数字多来自厂商白皮书与部署案例，**随芯片、天线与场景变化**[2][9]。

## 1. BLE 5.1 测向概述

### 1.1 为何需要测向

传统基于接收信号强度指示（Received Signal Strength Indicator, RSSI）的测距易受人体遮挡与多径影响，室内误差常到数米量级。BLE 5.1 在包尾追加 CTE，用相位而非功率估方向，再经多定位器融合，厂商材料常给出亚米级叙事——**需现场标定验证**[1][8]。

| 技术 | 典型精度量级 | 成本倾向 | 备注 |
|------|--------------|----------|------|
| RSSI 指纹 | 数米 | 低 | 环境敏感 |
| BLE AoA/AoD | 亚米～米级 | 中 | 依赖阵列与校准 |
| UWB | 分米级 | 高 | 标签与基础设施更贵 |
| Wi-Fi RTT | 米级 | 中 | 依赖 AP 支持 |

### 1.2 AoA 与 AoD

| 特性 | AoA | AoD |
|------|-----|-----|
| 天线阵列位置 | 固定定位器 | 固定信标 |
| 标签射频 | 单天线发射为主 | 单天线接收为主 |
| 角度计算位置 | 定位器/服务器 | 标签本地 |
| 隐私倾向 | 基础设施知位置 | 标签可自知位置 |
| 典型叙事场景 | 资产追踪 | 寻路导航 |

```
AoA: [Tag 单天线发射] ---> [Locator 阵列接收并算角]
AoD: [Beacon 阵列发射] --> [Tag 单天线接收并算角]
```

## 2. CTE 与天线切换

### 2.1 CTE 作用

普通 BLE 包用高斯频移键控（Gaussian Frequency Shift Keying, GFSK），瞬时频率变化，相位难稳。CTE 是包尾一段无调制载波（规范允许约 16–160 µs 量级），供同相/正交（In-phase/Quadrature, IQ）采样[1]。

```
+----------+--------+------+-----+-----+
| Preamble | Access | PDU  | CRC | CTE |
+----------+--------+------+-----+-----+
                              纯载波，供 IQ
```

### 2.2 切换时序

接收端在参考期用参考天线采相位，再按切换图案在各天线间采样。切换槽宽与 AoA/AoD 模式相关（规范定义 1 µs / 2 µs 等选项），实现须与芯片射频开关延迟匹配[2]。

| 阶段 | 作用 | 设计要点 |
|------|------|----------|
| 参考期 | 建立相位基准 | 通常固定在天线 0 |
| 切换采样期 | 多天线 IQ | 图案长度与 CTE 长度匹配 |
| 空闲/保护 | 开关稳定 | 避免切换瞬态污染样本 |

## 3. AoA 机制

平面波到达间距为 \(d\) 的阵列时，路径差 \(d\sin\theta\)，相位差 \(2\pi d\sin\theta/\lambda\)。2.4 GHz 波长约 12.5 cm，工程上常取 \(d\le\lambda/2\) 抑制角度模糊[3]。

二维定位至少需两个独立角度观测；三维与遮挡场景通常部署更多定位器。定位器几何应避免视线近似共线，否则几何精度因子（Geometric Dilution of Precision, GDOP）恶化。

## 4. AoD 与隐私

信标按已知图案切换天线发射 CTE，标签用单天线 IQ 与公开切换表反推出发角，再结合信标坐标本地解算位置。位置可不上传服务器，适合消费侧导航；代价是标签需算力与校准参数，电池与固件复杂度上升[1][9]。

## 5. 天线阵列

| 布局 | 可测角度 | 适用 |
|------|----------|------|
| 均匀线性阵列（ULA） | 单平面角 | 走廊、货架线 |
| 均匀矩形阵列（URA） | 方位+俯仰 | 仓库三维 |

间距过大产生栅瓣模糊；过小则相位差淹没在噪声中。射频开关、馈线等长与互耦校准往往比“多加天线”更关键[2][4]。

## 6. 角度估计

简单相位差法算力低，多径下易偏。多重信号分类（MUSIC）等子空间方法可分辨多路径，代价是协方差估计与谱扫描算力更高；ESPRIT 利用平移不变性，常要求均匀阵列[3][5]。

| 方法 | 优点 | 代价 |
|------|------|------|
| 相位差 | 实现简单 | 多径脆弱 |
| MUSIC | 分辨率较高 | CPU/内存 |
| ESPRIT | 免密谱搜索 | 阵列几何约束 |

## 7. 多径与部署

| 策略 | 原理 | 预期 |
|------|------|------|
| 子空间算法 | 区分直达/反射 | 改善尖峰误差 |
| 多样本平均 | 时间滤波 | 降瞬时噪声 |
| 多信道/跳频 | 频率分集 | 削弱特定多径 |
| 环境校准 | 偏差图 | 场景绑定 |
| 高处安装 | 减少水平遮挡 | 视距更好 |

校准带来的改善幅度因场而异，**不宜套用固定百分比**[8]。

## 8. 硬件与实现要点

| 芯片倾向 | 天线切换能力叙事 | 备注 |
|----------|------------------|------|
| Nordic nRF52833/5340 | 多路 GPIO 控开关 | SDK/方向查找示例较全 |
| Silicon Labs EFR32BG22 等 | 多路切换 | 需核对手册引脚与时序 |

开发应验证：CTE 长度、切换图案、IQ 上报速率与定位引擎输入格式一致；产线需相位校准流程[2][6]。

## 9. 与其他技术对比

| 维度 | BLE AoA/AoD | UWB | Wi-Fi 指纹 |
|------|-------------|-----|-----------|
| 精度叙事 | 亚米～米 | 分米 | 数米 |
| 标签成本倾向 | 较低 | 较高 | 可借手机 |
| 功耗倾向 | 标签可很低（AoA 只发） | 中 | 手机侧高 |
| 基础设施 | 阵列定位器 | 锚点 | AP/指纹库 |

大量低成本标签、可接受亚米级时，BLE 测向常更经济；厘米级安全测距（如数字车钥匙）更常看 UWB[7][10]。

## 10. 局限、挑战与可改进方向

### 1. 精度宣传与现场落差

**局限**：白皮书 0.5–1 m 多在视距、校准良好条件下测得；货架金属、人群会显著拉大误差[8]。
**改进**：按分位数（如 P50/P90）验收；分区标定；关键区混合 UWB 或视觉。

### 2. 阵列与开关非理想

**局限**：互耦、开关插入损耗、馈线不等长引入系统相位偏置。
**改进**：产线相位校准表；温度漂移补偿；限制 CTE 图案中的无效切换。

### 3. 容量与射频占空比

**局限**：标签广播过密导致定位器 IQ 处理与空口碰撞瓶颈。
**改进**：自适应广播间隔；分区信道规划；边缘预滤波后再上云。

### 4. AoD 隐私与算力权衡

**局限**：本地解算保护隐私，但标签 MCU/校准参数管理成本上升。
**改进**：粗定位在标签、精定位按需上传；密钥保护校准参数防伪造环境。

## 11. 实践要点

1. 先固定阵列几何与 \(d\le\lambda/2\)，再调算法。
2. 用已知坐标标定点做端到端误差直方图，而非只看平均角误差。
3. 同步核对芯片 CTE/IQ API 与定位引擎坐标系（含天线 0 朝向）。

## 参考文献

[1] Bluetooth SIG, "Bluetooth Core Specification," Vol 6 (Direction Finding / CTE), v5.1+.
[2] Nordic Semiconductor, Direction Finding / Antenna switching application documentation.
[3] Schmidt, R. O., "Multiple Emitter Location and Signal Parameter Estimation," IEEE Trans. Antennas Propag., 1986 (MUSIC).
[4] Bluetooth SIG, "Bluetooth Direction Finding: A Technical Overview," white paper.
[5] Roy, R. and Kailath, T., "ESPRIT—Estimation of Signal Parameters via Rotational Invariance Techniques," IEEE Trans. ASSP, 1989.
[6] Zephyr Project, Bluetooth Direction Finding API documentation.
[7] FiRa Consortium / UWB ranging overviews for indoor positioning comparison.
[8] Industry AoA deployment reports (warehouse RTLS case studies; treat metrics as scenario-bound).
[9] Silicon Labs, Bluetooth Angle of Arrival application notes.
[10] IEEE / academic surveys on BLE vs UWB indoor localization.
[11] Bluetooth SIG Assigned Numbers and CTE field definitions.
