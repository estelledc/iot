---
schema_version: '1.0'
id: pressure-sensor-piezoresistive
title: 压阻式压力传感器工作原理与MEMS制造
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - bridge-circuit-sensor-excitation
tags:
  - 压阻效应
  - 压力传感器
  - MEMS
  - 惠斯通电桥
  - 温度补偿
  - 膜片
  - 工业IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 压阻式压力传感器工作原理与MEMS制造

> **难度**：🟡 中级 | **领域**：压力传感 / MEMS | **关键词**：压阻, 膜片, 电桥, 温度补偿 | **阅读时间**：约 16 分钟

## 日常类比

人站在薄木板上会弯曲，体重越大弯得越明显。压阻传感器的“木板”是极薄硅膜片（diaphragm）；“读数”不是看弯曲，而是硅受力后电阻率变化——**压阻效应**。四个压敏电阻像手拉手围成圈，组成惠斯通电桥：压力打破平衡，输出毫伏级电压，像天平指针偏转[1][2]。

## 摘要

讲压阻机理、微机电系统（Micro-Electro-Mechanical Systems, MEMS）膜片与电桥、温度误差与补偿、封装介质隔离，并与电容式等对比。灵敏度与精度数字为量级，以具体型号数据手册为准[3]。

## 1. 压阻与电桥

半导体压阻系数远高于金属应变片，适合微型膜片。电阻置于膜片应力集中区，两增两减配置，差分输出抑制共模[1]。激励可用恒压或恒流；恒流对某些温度项更友好，视电桥设计而定[4]。

| 项目 | 要点 |
|------|------|
| 满量程输出 | 常为 mV/V 量级，需仪表放大 |
| 非线性 | 大挠度时几何非线性 |
| 过载 | 膜片触停挡或破裂风险 |
| 介质 | 干气直接；液体/腐蚀需隔离膜+油充 |

## 2. MEMS 制造要点

体硅/表面微加工形成腔与膜片，离子注入做压敏电阻，阳极键合等封腔。绝对压需真空参考腔，表压需导压孔。晶圆级工艺使成本随产量下降，但封装与标定常占成本大头[2][5]。

## 3. 温度与信号链

压阻温度系数显著：零点漂移与灵敏度漂移需电阻网络、模拟补偿或数字标定（查表/多项式）。工业变送常含前端专用集成电路（Application-Specific Integrated Circuit, ASIC）做放大、模数转换与补偿[3][6]。

| 误差源 | 表现 | 对策 |
|--------|------|------|
| 温度 | 零点/满度漂移 | 标定、温度传感器共封装 |
| 安装应力 | 零点跳 | 机械去耦、灌封分区 |
| 电源噪声 | 输出抖动 | 参考与激励滤波 |
| 长期蠕变 | 慢漂移 | 老化筛选、周期校准 |

## 4. 与其他原理对比

| 类型 | 优势 | 代价 |
|------|------|------|
| 压阻 MEMS | 灵敏、成熟、成本友好 | 温漂、需补偿 |
| 电容 MEMS | 低功耗、温漂可更优 | 电路复杂、量程/介质限制 |
| 金属应变 | 坚固大压力 | 体积大、灵敏低 |

## 5. 局限、挑战与可改进方向

### 1. 温度补偿依赖标定

**局限**：未充分多温点标定则现场误差大。
**改进**：出厂多温度标定；运行中用片上温度二次修正[6]。

### 2. 介质兼容与堵塞

**局限**：导压孔冷凝/颗粒改变读数。
**改进**：隔离膜充油；加热或过滤；选合适接口[5]。

### 3. 封装应力

**局限**：壳体拧紧力矩导致零点偏移。
**改进**：规定安装力矩；弹性结构；安装后现场调零[7]。

### 4. 过载与脉动

**局限**：水锤等尖峰永久损坏膜片。
**改进**：阻尼器、过压保护阀；选更高过载规格[3]。

## 总结

压阻 MEMS 是工业物联网压力传感主流：理解膜片-电桥-补偿-封装全链路，才能把数据手册精度落到现场可信读数。

## 参考文献

[1] Smith, Piezoresistance effect in germanium and silicon (classic).
[2] Senturia / MEMS textbooks: diaphragm mechanics and transduction.
[3] Commercial MEMS pressure sensor datasheets (Bosch/NXP/Honeywell class).
[4] Wheatstone bridge excitation: constant voltage vs constant current.
[5] Media-isolated pressure sensor packaging (oil-filled) notes.
[6] Digital temperature compensation and calibration of piezoresistive bridges.
[7] Packaging stress and mounting effects on pressure sensors.
[8] Comparison of piezoresistive vs capacitive MEMS pressure sensing.
[9] Overpressure and burst pressure design guidelines.
[10] Analog front-end and ADC considerations for mV-level bridges.
[11] Long-term drift and hysteresis in silicon pressure sensors.
[12] Industrial IoT pressure node integration practices.
