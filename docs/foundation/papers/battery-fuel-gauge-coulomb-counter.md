---
schema_version: '1.0'
id: battery-fuel-gauge-coulomb-counter
title: 电池电量计库仑计法与电压法对比
layer: 1
content_type: comparison
difficulty: intermediate
reading_time: 15
prerequisites:
  - battery-management-bms
  - battery-life-estimation-model
tags:
  - SOC
  - 库仑计
  - 电压法
  - Fuel Gauge
  - 电池
  - 卡尔曼滤波
  - IoT功耗
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 电池电量计库仑计法与电压法对比

> **难度**：🟡 中级 | **领域**：电池管理系统 | **阅读时间**：约 15 分钟

## 日常类比

油表两种读法：看油箱液位刻度——电压法（开路电压 OCV 估 SOC）；加油口装流量计加减油量——库仑计（电流积分）。刻度简单但颠簸时抖；流量计稳但要知道油箱多大且会累积误差。IoT 里 SOC（State of Charge）不准会导致早关机、误换电池或错误发起发射[1][2]。

## 摘要

电压法靠 OCV–SOC 曲线，静态尚可、负载/温度/滞后下误差大；LiFePO4 平台区尤差。库仑计积分电流，动态好但漂移。融合（阻抗跟踪/EKF 等）用电压校正积分。Fuel gauge IC 降低实现成本。文中精度百分比为厂商/文献量级，**依赖电芯与学习周期**[1][3][4]。

## 1. 电压法

| SOC 区间叙事 | OCV 形态 | 含义 |
|--------------|----------|------|
| 两端 | 较陡 | 电压法相对敏感 |
| 中段 | 平坦 | 小电压误差→大 SOC 误差 |

误差源：\(V=OCV-IR\) 负载效应、温度、充放电滞后。适用：粗分档、长休眠近 OCV、极低成本[2][5]。

## 2. 库仑计与融合

\[
\mathrm{SOC}(t)=\mathrm{SOC}(t_0)+\frac{1}{Q_{\max}}\int I\,\mathrm{d}t
\]

检流电阻 + 较高分辨率 ADC；误差来自初值、偏移/增益、电阻温漂——开环积分会漂[1][6]。

| 指标叙事 | 电压法 | 库仑计 | 融合 |
|----------|--------|--------|------|
| 静态 | 中–差 | 依赖初值 | 较好 |
| 动态 | 较差 | 较好 | 较好 |
| 长期漂移 | 低 | 有 | 电压校正抑制 |
| 复杂度 | 低 | 低 | 中高 |

## 3. IC 选型要点

| 特性 | 融合类（如 BQ27441 叙事） | 模型电压类（如 MAX17048） | 低功耗电压类（如 LC709203F） |
|------|---------------------------|---------------------------|-------------------------------|
| 检流电阻 | 常需外置 | 常不需 | 常不需 |
| 精度叙事 | 较高（需学习） | 稳态较好 | 中等 |
| 功耗叙事 | 数十 μA 级 | 数十 μA 级 | 更低 μA 级常见 |

学习周期：满充–静置–放空–静置以更新容量模型；换电芯后应重做。自放电与老化使 \(Q_{\max}\) 变化，长寿命 IoT 需补偿或选带学习的 IC[3][7][8]。

## 4. 局限、挑战与可改进方向

### 1. 脉冲发射把电压法打穿

**局限**：大电流脉冲下端电压骤降，误判低电。
**改进**：脉冲后静置再采样；或上库仑/融合 IC[2][5]。

### 2. 库仑计无初值、长期漂

**局限**：掉电丢积分；月级运行误差变大。
**改进**：NV 存储 SOC + 上电 OCV 校验；定期满充重置[1][6]。

### 3. 忽略温度与自放电

**局限**：户外节点冬天“掉电”、仓库存放后 SOC 虚高。
**改进**：NTC 进 gauge；固件自放电模型；选带温补 IC[7][8]。

### 4. 把手册 ±1% 当全寿命 SLA

**局限**：未学习、错化学 ID、老化后超差。
**改进**：产线学习流程；现场抽测；老化更新 \(Q_{\max}\)[3][4]。

## 5. 实践要点

1. 粗指示：电压或无检流 model gauge；长寿命高精度：融合 + 学习。
2. 预算 gauge 自身电流与 I2C 轮询频率。
3. 多串电池走向完整 BMS，不单靠单节 fuel gauge 思路。

## 参考文献

[1] G. L. Plett, Extended Kalman filtering for battery management systems, J. Power Sources.
[2] H. Rahimi-Eichi et al., Battery management system overview, IEEE Ind. Electron. Mag.
[3] TI, BQ27441-G1 Technical Reference Manual (SLUUAP5).
[4] Maxim/ADI, MAX17048/MAX17049 ModelGauge datasheet.
[5] Lithium-ion OCV–SOC characterization application notes.
[6] Shunt-based current sensing for coulomb counting (TI/ADI notes).
[7] ON Semiconductor, LC709203F datasheet.
[8] Battery self-discharge and temperature derating vendor guides.
[9] TI bqStudio / fuel gauge learning cycle documentation.
[10] IEC/IEEE literature on SOC estimation methods survey.
[11] LiFePO4 flat OCV region measurement notes (voltage method limits).
