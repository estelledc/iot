---
schema_version: '1.0'
id: battery-life-estimation-model
title: IoT电池寿命估算模型与实测验证
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - battery-management-bms
tags:
  - 电池寿命
  - Peukert
  - 功耗模型
  - PPK2
  - 锂亚电池
  - CR2032
  - 能量预算
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT电池寿命估算模型与实测验证

> **难度**：🟡 中级 | **领域**：IoT电源管理 | **阅读时间**：约 14 分钟

## 日常类比

长途徒步只带一壶水：上坡喝得多、平路少、夜间几乎不喝，水壶还会蒸发。电池寿命同理——IoT 在睡眠/采样/射频间切换，温度与自放电都会改写“能走多久”。用标称容量除以平均电流，常与实测差一个量级[1][2]。

## 摘要

建立分状态加权电流模型，叠加 Peukert（大电流有效容量缩水）、温度与自放电修正，再用 Nordic Power Profiler Kit II（PPK2）校准。文中寿命与电流为示意量级，**随固件、射频占空比与温度强烈变化**[3][4]。

## 1. 电池选型速览

| 类型 | 标称电压 | 典型容量量级 | 自放电倾向 | 常见用途 |
|------|----------|--------------|------------|----------|
| CR2032 | 3.0 V | 约 220 mAh | 低（年计） | BLE 信标 |
| AA 锂铁 | 1.5 V | 约数 Ah | 很低 | 远程传感 |
| LiPo | 3.7 V | 数百–数千 mAh | 较高（月计） | 可穿戴/可充 |
| ER14505 锂亚 | 3.6 V | 约 2 Ah 级 | 低 | LoRa 长寿命 |

截止电压须对齐 MCU/射频最低工作电压，否则标称容量用不完[3][5]。

## 2. Peukert 与温度

Peukert：大电流时有效容量下降，\(C_{\mathrm{eff}} \propto I^{1-k}\)。锂亚 \(k\) 往往明显高于 LiPo；脉冲发射（如 LoRa TX）不可只按平均电流算容量[1][3]。

| 工况 | 粗略影响（示意） |
|------|------------------|
| 低温（如 −20 °C） | 纽扣/LiPo 可用容量明显下降 |
| 高温长期 | 自放电与老化加速 |
| 高脉冲电流 | 锂亚有效容量缩水更显著 |

数字须用厂商放电曲线与本板实测校准，勿直接当规格[3][6]。

## 3. 加权电流与修正

\(I_{\mathrm{avg}}=\sum I_i t_i/\sum t_i\)。休眠占绝大部分时间时，微安级漏电与状态切换开销决定寿命。

| 修正项 | 作用 |
|--------|------|
| Peukert | 脉冲/高平均电流下缩容量 |
| 温度 | 户外/工业温区降额 |
| 自放电 | 多年部署不可忽略（LiPo 尤甚） |
| 安全裕度 | 产品类型不同，常取约 0.5–0.7 量级 |

手册电流常低于板级实测：GPIO 漏电、协议栈收尾、射频前导都会抬高平均电流；工程上常再乘约 1.15–1.5 的经验修正后再选型[2][4]。

## 4. 实测：PPK2

| 能力 | 量级（手册级） |
|------|----------------|
| 电流范围 | 约 nA–A 级 |
| 采样 | 可达约 100 kSa/s |
| 用途 | 完整唤醒周期平均电流 |

陷阱：线阻压降、采样漏掉短脉冲、旁路电容充电尖峰、多电源串扰。应用 Source 模式、最短线缆、框选完整周期积分电荷[2]。

## 5. 选型决策要点

1. \(I_{\mathrm{avg}}\) 偏高时排除纽扣；目标寿命数年且不可充时慎用高自放电化学体系。
2. 极端温区优先查锂亚/锂铁曲线，而非室温标称。
3. 验收：标称工况达标，且最差温区+最短上报间隔仍留裕度。

## 6. 局限、挑战与可改进方向

### 1. 平均电流掩盖脉冲损伤

**局限**：Peukert 对间歇大脉冲的适用性有限，简单加权会乐观。
**改进**：按发射脉冲峰值与宽度分段建模；必要时加超级电容缓冲射频尖峰[3][7]。

### 2. 手册与板级偏差

**局限**：芯片 Deep Sleep 不含外围漏电与固件路径。
**改进**：PPK2/同类仪表测完整产品；建立板级功耗基线再写规格书[2][4]。

### 3. 温度与老化耦合

**局限**：静态温度表无法覆盖日历老化与循环衰减。
**改进**：结合 BMS/电量计 SoH；户外样机做温循抽测[6][8]。

### 4. 安全裕度过保守或过激进

**局限**：同一系数套所有产品线。
**改进**：按失效代价分层裕度；用最差工况仿真驱动标称寿命声明[5][9]。

## 7. 实践要点

1. 先建状态表算 \(I_{\mathrm{avg}}\)，再叠 Peukert/温度/自放电/裕度。
2. 量产前用 PPK2 校准，勿只信数据手册。
3. 规格书写“目标寿命 + 测试条件（间隔、温度、发射功率）”。

## 参考文献

[1] Peukert, W., Elektrotechnische Zeitschrift, 1897 (capacity vs discharge rate).
[2] Nordic Semiconductor, Power Profiler Kit II User Guide.
[3] Saft / lithium thionyl chloride cell technical manuals (e.g. ER14505 class).
[4] Raghunathan, V. et al., "Energy-Aware Wireless Sensor Networks," IEEE SPM, 2006.
[5] MCU/RF datasheets: minimum operating voltage and TX current (nRF52, SX127x class).
[6] Battery vendor temperature derating and self-discharge application notes.
[7] Supercapacitor buffering for pulsed radio loads (vendor ANs).
[8] Barré, A. et al., Li-ion ageing review, Journal of Power Sources, 2013.
[9] Industrial IoT battery sizing and SLA design guides.
[10] IEC / UL primary lithium cell safety and storage guidance (context).
[11] LoRaWAN / BLE advertising duty-cycle power budgeting notes.
[12] Coulomb counting vs voltage-based remaining capacity limitations.
