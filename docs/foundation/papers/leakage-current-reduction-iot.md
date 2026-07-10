---
schema_version: '1.0'
id: leakage-current-reduction-iot
title: IoT设备漏电流控制与PCB设计注意事项
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - ldo-vs-dcdc-power-supply
  - duty-cycling-sensor-node
tags:
  - 漏电流
  - 低功耗
  - GPIO配置
  - 负载开关
  - PCB设计
  - 休眠电流
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT设备漏电流控制与PCB设计注意事项

> **难度**：🟡 中级 | **领域**：低功耗硬件 | **关键词**：Iq, 负载开关, GPIO | **阅读时间**：约 16 分钟

## 日常类比

水龙头关了仍滴水，一年也能积一桶——IoT 深睡眠的微安级漏电同样会吃光电池。漏电很少来自“MCU 标称睡眠电流” alone，而是上拉、ESD 管、分压电阻、未关外设与受潮 PCB 的总和[1][2]。

## 摘要

梳理漏电路径、nA～μA 测量、负载开关、GPIO 模拟态与 PCB 防潮。目标睡眠电流须整板实测，手册 MCU 值只是下限参考[1][3]。

## 1. 六大来源（常见）

| 来源 | 例子 |
|------|------|
| 电源芯片 Iq | LDO/Buck 静态 |
| 外设常电 | 传感器、Flash、USB-UART |
| GPIO | 浮空、错误上拉、外部电平冲突 |
| 保护器件 | TVS/ESD 漏电 |
| 电阻网络 | 电池分压、LED 假负载 |
| 板级 | 助焊剂、受潮、三防不当 |

| 手段 | 作用 |
|------|------|
| 负载开关 | 切断外设轨 |
| GPIO 模拟高阻 | 降低数字输入漏 |
| 高阻分压+开关 | 测量时才接通 |
| 干燥与清洁 | 降表面漏电 |

## 2. 测量与调试

用串联电阻+仪表或专用电源分析仪；先拔外设分区供电定位。典型“隐藏”路径：调试器仍连接、串口 TX 顶牛、湿气。Sub-μA 目标需要温湿度可控环境[2][4]。

## 3. 局限、挑战与可改进方向

### 1. 只优化 MCU 睡眠

**局限**：外设轨常电占主导。
**改进**：电源域划分与负载开关清单[1]。

### 2. ESD 与漏电权衡

**局限**：强防护器件漏电大。
**改进**：选低漏 ESD；关键口才加强[4]。

### 3. 量产助焊剂残渣

**局限**：实验室干净板，量产漏电升。
**改进**：清洗工艺与三防；抽测睡眠电流[5]。

### 4. GPIO 复用遗漏

**局限**：某一脚内部外设时钟未关。
**改进**：睡眠前寄存器检查表与自动化测试[3]。

## 总结

漏电流是系统账：电源 Iq、外设、GPIO、防护与污染。分区供电、可测、可关，才能把纸面 μA 变成年续航。

## 参考文献

[1] Texas Instruments, Ultra-Low Power MCU Design Guide (SLAA711).
[2] Nordic, nRF52 低功耗设计指南.
[3] STMicroelectronics, STM32L4 硬件开发相关 AN.
[4] Johanson 等, ESD 二极管漏电与电池应用技术文.
[5] IPC-HDBK-830, 三防涂覆相关手册.
[6] 负载开关选型与软启动应用笔记.
[7] 电池寿命估算与睡眠电流模型文献.
[8] 源表/电源分析仪测量 μA 的实践指南.
[9] GPIO 浮空与闩锁风险说明（MCU 手册）.
[10] 湿气敏感等级与板级清洁工艺资料.
[11] 超低 Iq LDO/Buck 数据手册对比方法.
[12] 调试器对目标板漏电影响的应用笔记.
