---
schema_version: '1.0'
id: antenna-testing-ota-measurement
title: 天线OTA测试与辐射性能评估
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - antenna-propagation-indoor-outdoor
  - link-budget-calculation-lpwan
tags:
  - OTA
  - TRP
  - TIS
  - 天线测试
  - 暗室
  - 辐射效率
  - IoT射频
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 天线OTA测试与辐射性能评估

> **难度**：🔴 高级 | **领域**：天线测试 | **阅读时间**：约 22 分钟

## 日常类比

规格写“通信距离约 10 m”，音箱贴金属书架后 3 m 就断续——像体检只看化验单、不看整个人能不能爬楼。空中（Over-The-Air, OTA）测试不拆天线、不接电缆，直接量整机向空间辐射的能量，检验外壳、电池、螺丝把“纸面天线”打了几折[1][4]。

## 摘要

说明为何传导测试不够、总辐射功率（Total Radiated Power, TRP）与总全向灵敏度（Total Isotropic Sensitivity, TIS）含义、暗室/紧凑场/近场设施与物联网（Internet of Things, IoT）特殊挑战，并给出分阶段低成本策略。文中美元成本与 dB 差值为公开/案例量级，**不可当报价单**[1][2]。

## 1 为何需要 OTA

```
电磁仿真 → 原型 → 传导测试 → OTA
理想环境     接近现实   端口匹配     整机真实辐射
```

| 因素 | 影响量级（示意） | 说明 |
|------|------------------|------|
| 塑料外壳 | 约 −0.5～−2 dB | 介质加载、频偏 |
| 金属外壳 | 约 −3～−15 dB 或更差 | 屏蔽/涡流 |
| 电池/LCD | 约 −1～−4 dB | 吸收或导电层 |
| 人手握持 | 约 −3～−8 dB | 组织吸收 |

传导测回波损耗/驻波比（Voltage Standing Wave Ratio, VSWR）看不到方向图扭曲与握持退化[3][4]。

## 2 核心指标

**TRP**：全向辐射功率积分。直觉：灯泡总光通量。粗关系：TRP ≈ 传导功率 + 天线相关增益项 − 损耗（具体定义以标准为准）[1]。

**TIS**：全向接收综合灵敏度，数值越低（更负）越好。蓝牙低功耗（Bluetooth Low Energy, BLE）设备公开/实验室常见约 −90～−75 dBm 量级跨度，以本机实测为准[1][5]。

**方向图与效率**：总效率 ≈ 反射效率 × 辐射效率。PCB 倒 F 常见约 40–70%；外置鞭状更高；金属壳内可低至约 5–30%。效率每差约 3 dB，自由空间距离约缩三成量级——室内另计[4]。

## 3 测试设施与方法

| 设施 | 建设成本量级 | 适用 |
|------|--------------|------|
| 全电波暗室（约 3 m） | 约数十万～数百万美元 | 标准 TRP/TIS |
| 紧凑天线测试场（Compact Antenna Test Range, CATR） | 往往更高 | 高频/大静区 |
| 近场扫描 | 相对较低 | 研发迭代 |
| 简易屏蔽室 | 更低 | 相对对比、非正式 |

球面扫描：θ/φ 步进越密越准（粗测数百点至细测数千点量级）。大圆切面快，但精确 TRP 仍需近全 3D 数据[3]。

## 4 标准与 IoT 挑战

| 标准 | 内容 | 设备 |
|------|------|------|
| CTIA Test Plan | TRP/TIS 方法 | 蜂窝等 |
| 3GPP TS 37.544 / 38.151 | E-UTRA / NR OTA | 4G/5G |
| CTIA IoT OTA | IoT 射频性能 | NB-IoT/Cat-M 等 |

IoT 尚无统一强制 OTA，常参考 CTIA IoT、LoRa Alliance 射频要求、Bluetooth SIG 射频物理层（传导为主、OTA 可选）[1][2][5]。

小型化受 Chu-Harrington 类电尺寸极限约束：天线远小于波长时效率上限低。夹具、供电线缆易成为“第二天线”；多协议网关需分天线测互耦。触发方案：连续载波固件、定时发包、线控（线缆需处理）、远程触发[4]。

## 5 低成本策略与案例要点

分阶段：桌面软件无线电粗查 → 频谱仪+小转台相对对比 → 定型后认可实验室。内置 RSSI 可做相对评估，精度常仅约 ±3 dB 量级。

金属壳案例（工程示意）：传导 S11 正常，现场距离腰斩；暗室有壳/无壳 TRP 差约 6 dB 量级，效率从约六成跌至约一成五。机制：近场涡流、法拉第笼、去谐。迭代：塑料窗（损防护）、外置天线、外壳集成天线并保持与金属足够间距（经验：>λ/8 量级作起点）[4][6]。

## 6 报告解读

以传导约 +20 dBm 为参考时的粗分级（非标准强制）：TRP 约 >+17 / >+14 / >+11 dBm 对应效率约 >50% / >25% / >12% 量级；方向图峰谷差约 <8 / <12 / <18 dB。关注：配置是否贴近实机、不确定度（常约 ±1–2 dB）、主瓣/零点是否对准部署方向[1]。

## 7 局限、挑战与可改进方向

### 1. 成本与节奏

**局限**：正式暗室贵且档期长，初创易拖到量产前才测[1]。
**改进**：早期相对 OTA + 关键里程碑外包；把 TRP 目标写进设计评审。

### 2. 夹具与线缆污染

**局限**：供电/夹具改变方向图，小型 IoT 尤甚[3]。
**改进**：光纤/电池供电、夹具去嵌入、重复装夹统计不确定度。

### 3. 测试模式≠业务模式

**局限**：连续载波 TRP 好看，真实占空比/协议时序下覆盖仍差[5]。
**改进**：补充协议态触发与现场链路预算闭环。

### 4. 金属壳余量不足

**局限**：链路预算按塑料壳写，量产改铝合金后失效[4]。
**改进**：金属壳预留约 4–6 dB、塑料约 2 dB 量级余量，并以 OTA 验证。

## 参考文献

[1] CTIA, Test Plan for Wireless Device Over-the-Air Performance, v3.8.2, 2021.
[2] 3GPP TS 37.544, User Equipment Over The Air (OTA) performance.
[3] M. Foegelle, Antenna Pattern Measurement: Concepts and Techniques, Compliance Engineering, 2002.
[4] C. A. Balanis, *Antenna Theory: Analysis and Design*, 4th ed., Wiley, 2016.
[5] Bluetooth SIG, RF PHY Test Specification（传导/可选 OTA）.
[6] Y. Rahmat-Samii et al., OTA testing approaches for wireless devices, IEEE AP-S 相关工作.
[7] CTIA IoT OTA Test Plan, 2019 及后续修订.
[8] 3GPP TS 38.151, NR OTA.
[9] LoRa Alliance, RF performance / certification 相关要求.
[10] L. J. Chu, Physical limitations of omni-directional antennas, J. Appl. Phys., 1948（电尺寸极限背景）.
[11] IEEE / IEC 暗室与场地衰减测量实践文献.
