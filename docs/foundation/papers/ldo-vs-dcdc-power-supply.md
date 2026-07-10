---
schema_version: '1.0'
id: ldo-vs-dcdc-power-supply
title: LDO与DC-DC电源转换器效率对比与选型
layer: 1
content_type: comparison
difficulty: beginner
reading_time: 15
prerequisites:
  - buck-converter-design-iot
tags:
  - LDO
  - DC-DC
  - 降压转换
  - 电源效率
  - 低功耗IoT
  - 纹波噪声
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# LDO与DC-DC电源转换器效率对比与选型

> **难度**：🟢 入门 | **领域**：电源管理 | **关键词**：LDO, Buck, Iq, 纹波 | **阅读时间**：约 15 分钟

## 日常类比

低压差线性稳压器（Low-Dropout Regulator, LDO）像用闸门挡水泄压——简单安静，多出来的水头变成热。DC-DC 开关变换器像水车发电再调压——效率高，但有齿轮噪声（纹波）。IoT 电池两边都要：睡眠看静态电流（Iq），发射看效率与热[1][2]。

## 摘要

对比 LDO 与降压型 DC-DC 的效率、噪声、压差与 Iq，给出射频/模拟与数字轨的常见组合。效率公式 \(\eta \approx V_{out}/V_{in}\) 仅近似描述 LDO，开关电源以数据手册曲线为准[1][4]。

## 1. 原理与对比

| 维度 | LDO | DC-DC（Buck 等） |
|------|-----|------------------|
| 效率 | 压差大时差，变热 | 通常高 |
| 噪声/纹波 | 低（无开关） | 有纹波与 EMI |
| 外围 | 少 | 电感电容，布局敏感 |
| 轻载 | 看 Iq | 看轻载模式与 Iq |

| 场景 | 倾向 |
|------|------|
| 3.3 V→3.0 V 小电流模拟 | LDO |
| 锂电 4.2 V→1.8 V 大电流数字 | Buck |
| 射频 PA 干净电压 | Buck + 后级 LDO 常见 |
| 深睡眠 μA 级 | 超低 Iq LDO 或低 Iq Buck |

## 2. 热与压差

LDO 耗散约 \((V_{in}-V_{out}) I_{load}\)；封装热阻不够会限流或过温。注意“低压差”仍要求最小余量；极低 Iq 器件对输出电容 ESR/类型常有要求[2][3]。

## 3. 局限、挑战与可改进方向

### 1. 只看满载效率

**局限**：IoT 大部分时间在睡眠，Iq 主导寿命。
**改进**：用工况加权效率；选 nA～μA 级 Iq 器件[3][4]。

### 2. 开关噪声毁模拟/射频

**局限**：ADC/LNA 被纹波污染。
**改进**：分轨、后级 LDO、良好布局与滤波[1]。

### 3. 电感与布局

**局限**：环路过大导致 EMI 失败。
**改进**：按手册布局；必要的输入磁珠/电容[4]。

### 4. 压差估计不足

**局限**：电池到末期 LDO 掉出稳压。
**改进**：算最小电池电压与压差；或改 Buck[2]。

## 总结

大压差大电流用开关，小压差低噪声用 LDO；射频常“开关 + LDO”。先算睡眠 Iq 与最坏热，再挑型号。

## 参考文献

[1] Texas Instruments, LDO vs DC-DC for IoT 应用笔记.
[2] Maxim/ADI, 线性稳压器关键参数说明.
[3] Texas Instruments, TPS7A02 等超低 Iq LDO 数据手册.
[4] Texas Instruments, TPS62840 等超低 Iq Buck 数据手册.
[5] R. Moghimi, LDO 相关 EDN 文章.
[6] Buck 变换器电感器选型指南.
[7] PSRR 与后级 LDO 级联设计笔记.
[8] EMI 与开关电源布局基础（CISPR 背景）.
[9] 电池内阻与电源跌落联合分析应用笔记.
[10] 电荷泵作为第三选项的选型摘要.
[11] 热阻 θJA 与铜皮散热估算资料.
[12] 多轨 IoT 电源树设计案例.
