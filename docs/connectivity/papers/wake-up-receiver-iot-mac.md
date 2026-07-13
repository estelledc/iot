---
schema_version: '1.0'
id: wake-up-receiver-iot-mac
title: 唤醒接收器在IoT MAC层中的超低功耗设计
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites: UNKNOWN
tags:
  - WuRx
  - 唤醒接收器
  - 占空比
  - MAC
  - 超低功耗
  - IEEE-802.11ba
  - OOK
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 唤醒接收器在IoT MAC层中的超低功耗设计

> **难度**：🔴 高级 | **领域**：超低功耗通信 | **阅读时间**：约 16 分钟

## 日常类比

占空比像夜班门卫定时出门看有没有快递——大多空跑。WuRx（Wake-up Receiver，唤醒接收器）像门铃：主射频与 MCU 深睡，只有专用低功耗电路听见“特定铃声”才叫醒整屋[1][2]。

## 摘要

空闲监听常主导 IoT 能耗。WuRx 用微瓦量级辅助接收检测 OOK 等唤醒帧，再启动主无线电。对比占空比的延迟—功耗耦合，并简述 802.11ba。文中 μW/mW 与距离为量级，**随灵敏度目标与工艺而变**[1][3]。

## 1. 问题：空闲监听

主接收机毫瓦级功耗，若事件稀疏，能量多耗在“等待”。降低占空比省电但抬高延迟、增加漏事件风险；提高占空比则空唤醒浪费仍大[1][4]。

## 2. 双射频架构

| 部件 | 角色 | 功耗叙事 |
|------|------|----------|
| 主射频 | 完整调制解调与数据 | mW 级收发 |
| WuRx | 常听唤醒模式 | μW 量级目标 |
| 地址逻辑 | 选择性唤醒 | 略增功耗、降误唤醒 |

链路概念：天线 → 包络检波 → 比较 →（可选）地址匹配 → 中断 MCU[2][3]。

流程：深睡 → 收唤醒 → 启主射频 → 数据/ACK → 再睡。

## 3. 唤醒信号与地址

常用 OOK（On-Off Keying）匹配包络检测。帧含前导、同步、地址、校验。广播简单但误唤醒多；单播/组播降连带唤醒[1][5]。

同频复用天线简单、干扰风险高；异频隔离好、天线/前端更复杂[2]。

| WuRx 功耗量级 | 灵敏度叙事 | 距离叙事 |
|---------------|------------|----------|
| 更低 μW | 较差 | 更短 |
| 较高 μW | 较好 | 更长 |

与主射频 −100 dBm 量级灵敏度相比，WuRx 常差数十 dB，唤醒距离可能短于数据距离——拓扑需补偿[1][3]。

## 4. MAC 与对比

发送方先打唤醒再传数据；多跳可逐跳唤醒以控全网活跃时间。异步常听延迟低；WuRx 再占空比可更省电但增延迟[4][5]。

| 指标 | 低占空比 | WuRx |
|------|----------|------|
| 空闲功耗 | 随占空比 | 近 WuRx 静态功耗 |
| 响应 | 受睡周期限制 | 可为毫秒—数十毫秒量级 |
| 突发/下行 | 易错过或需长听 | 更契合事件驱动 |
| 硬件 | 单射频 | 双前端成本 |

IEEE 802.11ba 将唤醒无线电纳入 Wi‑Fi 族，面向可达性与节能，功耗目标通常高于学术 μW 原型，但匹配 Wi‑Fi 覆盖叙事[6]。

## 5. 局限、挑战与可改进方向

### 1. 灵敏度—功耗墙

**局限**：μW 级难同时做到很远唤醒。
**改进**：提高唤醒发射功率、接受更高 WuRx 功耗、中继链式唤醒、缩小小区[1][3]。

### 2. 误唤醒

**局限**：包络检测易被同频能量触发。
**改进**：更长地址/特征、选频滤波、时域校验；权衡功耗[2][5]。

### 3. 标准与芯片碎片

**局限**：除 802.11ba 等外，跨联盟通用 WuRx 格式少；商用料号有限。
**改进**：垂直场景私有约定；优先有量产料的频段（如部分 LF WuRx）[3][6]。

### 4. 集成与共存

**局限**：双天线耦合、BOM、微瓦计量困难。
**改进**：模组化参考设计；产线电流测试夹具[2][4]。

## 6. 实践要点

1. 用事件率×响应时延证明 WuRx，而非默认上双射频。
2. 预算误唤醒能量，否则理论省电被吃掉。
3. 桥梁监测、火警、安防等“极稀有事件 + 快响应”优先评估。

## 参考文献

[1] Piyare, R. et al., "Ultra Low Power Wake-Up Radios: A Hardware and Networking Survey," ACM Comput. Surv., 2017.
[2] Magno, M. et al., wake-up receiver design / energy harvesting related works.
[3] ams AS3933 and similar WuRx datasheets.
[4] Polonelli, T. et al., long-range WSN wake-up radio architecture, IEEE Sensors J.
[5] Oller, J. et al. / related WuRx MAC protocol papers.
[6] IEEE Std 802.11ba-2021, Wake-Up Radio.
[7] Blanckenstein, J. et al., WuRx surveys in embedded networks.
[8] Sample duty-cycled WSN energy models (for contrast).
[9] Uncertain-IF / injection-locked WuRx circuit papers.
[10] Structural health monitoring IoT energy-latency case studies.
[11] Vendor app notes on false wake-up mitigation.
[12] 3GPP/802.15 discussions on wake-up related features (where applicable).
