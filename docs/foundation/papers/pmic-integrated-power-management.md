---
schema_version: '1.0'
id: pmic-integrated-power-management
title: 集成PMIC电源管理芯片选型与设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - buck-converter-design-iot
  - battery-management-bms
  - power-sequencing-multi-rail
tags:
  - PMIC
  - 电源管理
  - Buck
  - LDO
  - 电池充电
  - 电量计
  - I2C
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 集成PMIC电源管理芯片选型与设计

> **难度**：🟡 中级 | **领域**：集成电源管理 | **关键词**：PMIC, Buck, LDO, 充电, 电量计 | **阅读时间**：约 16 分钟

## 日常类比

开小餐馆若每道菜从种菜开始，成本极高；去批发市场买半成品再加工更划算。电源管理集成电路（Power Management IC, PMIC）就是电源设计的“批发市场”：把多路降压（Buck）、低压差线性稳压器（Low-Dropout Regulator, LDO）、充电器与电量计等装进一颗芯片，省板面积与焊接点[1][2]。

## 摘要

梳理 PMIC 相对分立方案的取舍、典型架构（电源路径、上电时序）、常见 IoT 器件对比，以及可穿戴级选型要点。电流、静态电流（Iq）与价格为公开资料常见量级，以现行数据手册为准[3][4]。

## 1. 概念与对比

PMIC 常见能力：多路 Buck/LDO、锂电充电与保护、电量计、USB/VBUS 管理、电压监测与复位、看门狗、动态电压调节（Dynamic Voltage Scaling, DVS）、I2C 配置[1]。

| 维度 | PMIC | 分立方案 |
|------|------|----------|
| BOM / 面积 | 少、紧凑 | 多 IC、占板 |
| Iq 优化 | 多路同开时可能偏高 | 可逐路极致优化 |
| 上电时序 | 常内置可编程 | 需外电路或 GPIO |
| 灵活度 | 受内部拓扑限制 | 自由组合 |
| 周期 | 验证面少、上手快 | 联调与布局更重 |

## 2. 架构要点

典型路径：VBUS/电池 → 充电器与电源路径管理（Power Path）→ Buck/LDO 分轨 → 监测与 I2C。USB 接入时优先给系统供电并充电；断开后无缝切电池，避免“先充满再启动”的延迟[3][5]。

多轨须按数据手册顺序上电（常先内核再 I/O/射频），由片内状态机完成，减少外部延时网络[6]。

## 3. 常见器件量级对比

| 参数 | AXP192/2101 系 | BQ25895+电量计 | nPM1300 |
|------|----------------|----------------|---------|
| 转换器 | 多路 Buck+LDO | 充电/路径为主 | 2 Buck + 2 LDO 量级 |
| 充电 | 有 | 可至数安级快充 | 数百 mA 量级 |
| 电量计 | 偏电压/简化 | 阻抗追踪类高精度 | 库仑计类 |
| 生态 | ESP 开发板常见 | 通用 TI 生态 | Nordic nRF 匹配 |
| 倾向 | 消费原型/小系统 | 充电精度优先 | 低功耗 BLE 节点 |

电量估计：电压查表误差大；库仑计中等；阻抗追踪需校准、精度更高——数字以厂商条件为准[4][7]。

## 4. 选型与实践

优先列清电压轨与峰值/平均电流、是否 USB 充电、PCB 面积、目标睡眠 Iq，再匹配 MCU 生态（如 nRF↔nPM、ESP↔AXP、STM32↔STPMIC）[1][8]。运行时用 I2C 关断闲置轨、读电量、响应低电/插拔中断。

可穿戴示意：小容量锂电 + 双 Buck 覆盖内核与 3.3 V 外设 + 内置充电；续航须按占空比与整机睡眠电流实测，文中天数仅为量级[9]。

| 检查项 | 要点 |
|--------|------|
| 热与保护 | 热关断、NTC 充电温度窗、过充过放 |
| 看门狗 | MCU 喂狗失败时复位系统 |
| 布局 | 电感/电容紧靠、电池与 VBUS 走线短粗 |
| 何时不用 PMIC | 仅 1–2 轨且极致 Iq → 分立更合适 |

## 5. 局限、挑战与可改进方向

### 1. 集成度与极致 Iq 冲突

**局限**：多路常开时静态电流难压到分立最优。
**改进**：睡眠关断闲置轨；单轨场景改分立 LDO/Buck[2][9]。

### 2. 厂商锁定与供货

**局限**：寄存器与时序绑定特定 PMIC，二供困难。
**改进**：抽象电源驱动层；关键轨预留分立备选 footprint[8]。

### 3. 电量计精度依赖校准

**局限**：未校准或温度漂移导致 SOC 偏差大。
**改进**：出厂学习周期；选阻抗追踪方案并按 AN 校准[4][7]。

### 4. 上电时序误配损坏风险

**局限**：自定义时序错误可致闩锁或异常复位。
**改进**：优先用手册预设；示波器验证各轨与复位释放顺序[6]。

## 总结

多轨、需充电与小面积的 IoT 产品，PMIC 常缩短设计与提高可靠性；选型以轨需求、Iq、生态与保护闭环为准，并用整机电流验证续航。

## 参考文献

[1] Nordic Semiconductor, nPM1300 Product Specification.
[2] X-Powers, AXP2101 Advanced Power Management Unit Datasheet.
[3] Texas Instruments, BQ25895 Fast Charge Switch-Mode Buck Charger Datasheet.
[4] Texas Instruments, Impedance Track / fuel gauge application notes.
[5] Power-path management concepts in USB-powered portable systems (vendor ANs).
[6] Multi-rail power sequencing and latch-up avoidance (PMIC / sequencer ANs).
[7] Battery fuel gauging methods: OCV, coulomb counting, model-based.
[8] STMicroelectronics, STPMIC1 Power Management IC Datasheet.
[9] Wearable IoT power budget and duty-cycle lifetime estimation practice.
[10] I2C-controlled DVS and rail enable strategies for low-power MCUs.
[11] Li-ion CC-CV charging and NTC charge-temperature windows.
[12] PCB layout guidelines for multi-buck PMICs (inductor hot loop).
