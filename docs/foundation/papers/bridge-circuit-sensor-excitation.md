---
schema_version: '1.0'
id: bridge-circuit-sensor-excitation
title: 电桥电路传感器激励与零点调整
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - strain-gauge-wheatstone-bridge
tags:
  - 惠斯通电桥
  - 激励
  - 零点调整
  - 比例测量
  - 应变片
  - 温度补偿
  - INA
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 电桥电路传感器激励与零点调整

> **难度**：🟡 中级 | **领域**：传感器接口 | **阅读时间**：约 14 分钟

## 日常类比

杆秤移动秤砣直到秤杆水平——惠斯通电桥四臂平衡时差分输出为零。制造公差与温漂像偷偷加的小砝码；零点调整是把秤杆调平，激励则是底座稳不稳[1][2]。

## 摘要

对比 1/4、半桥、全桥，电压/电流激励与比例测量，零点（电位器/DAC/软件）与温补、三/四线制，以及 INA 前端要点。mV/V 与误差数字为量级，**随传感器规格与布线变化**[3][4]。

## 1. 配置与激励

平衡条件：对角乘积相等则 \(V_o\approx 0\)。小信号下灵敏度随有效传感臂数增加（全桥最高）[1]。

| 配置 | 灵敏度倾向 | 温补 | 场景 |
|------|------------|------|------|
| 1/4 桥 | 低 | 无自补偿 | 低成本 |
| 半桥 | 中 | 部分 | 弯梁等 |
| 全桥 | 高 | 同温场自补偿 | 称重/压力 |

| 激励 | 优先场景 |
|------|----------|
| 电压 | 短线应变/称重，易做比例测量 |
| 电流 | 长线、RTD、多路切换 |

比例测量：ADC \(V_{\mathrm{ref}}\) 与 \(V_{\mathrm{ex}}\) 同源，激励波动在比值中抵消[3][5]。

## 2. 零点、温补与引线

偏移来源：臂阻公差、TCR 失配、安装应力、引线、时效。

| 调零 | 稳定性 | 动态范围 |
|------|--------|----------|
| 电位器 | 较差 | 可释放 ADC 量程 |
| DAC 注入 | 较好 | 可释放量程 |
| 软件减偏移 | 优 | 仍占用码字 |

工程上常硬件粗调 + 软件精调。温补：全桥同温自补偿、串并联温补电阻、或测温多项式。引线：二线无补偿；三线降大部分误差；四线（Kelvin）近乎消除压降误差[2][6]。

## 3. 放大与噪声

差分小信号经仪表放大器（INA）放大；增益按满量程输出对齐 ADC，并留裕量。注意供电抑制、屏蔽与同步采样；开关激励可抑制失调与部分 1/f，但需时序配合[4][7]。

## 4. 局限、挑战与可改进方向

### 1. “全桥自补偿”在温度梯度下失效

**局限**：四臂不同温时输出随温度漂。
**改进**：机械上保证同温；加本地温度传感器做残差补偿[2][8]。

### 2. 仅软件调零吃掉量程

**局限**：大偏移时有效分辨率下降。
**改进**：DAC/电位器粗调进中点，再软件细调[3][5]。

### 3. 长线电阻与共模干扰

**局限**：数十米线阻可占满精度预算。
**改进**：三/四线制；屏蔽双绞；电流激励评估[6][9]。

### 4. 激励自热改变读数

**局限**：应变片/RTD 功耗改变温度。
**改进**：降低激励、脉冲激励、标定含自热稳态[4][10]。

## 5. 实践要点

1. 先选桥型与激励，再定 INA 增益与 ADC 参考拓扑。
2. 校准流程写清：零点、跨度、温度点。
3. 布线对称，激励与参考共点。

## 参考文献

[1] Wheatstone bridge theory in sensor handbooks (Omega / Vishay class).
[2] Vishay / Micro-Measurements, strain gage temperature compensation notes.
[3] TI / ADI ratiometric measurement and bridge ANs.
[4] INA128 / INA333 / AD620 instrumentation amplifier datasheets.
[5] HX711 and bridge ADC ratiometric reference designs.
[6] IEC / ASTM practices for multi-wire RTD connections (3-wire/4-wire).
[7] Kester, W., Analog Devices sensor signal conditioning materials.
[8] Load-cell temperature effect and span compensation guides.
[9] Cable resistance and EMI in industrial weighing systems.
[10] Self-heating errors in resistive sensors application notes.
[11] DAC offset injection calibration architectures.
[12] Kelvin sensing for remote bridge excitation.
