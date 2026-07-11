---
schema_version: '1.0'
id: grant-free-access-massive-iot
title: 免授权接入在大规模IoT连接中的方案
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - 5g-mmtc-massive-iot-connection
  - iot-massive-access-random-access
tags:
- 免授权接入
- Grant-free
- NOMA
- 压缩感知
- Configured Grant
- mMTC
- 活跃检测
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 免授权接入在大规模IoT连接中的方案

> **难度**：🔴 高级 | **领域**：大规模接入 | **阅读时间**：约 22 分钟

## 日常类比

传统蜂窝调度像超市排队：先举手（调度请求 SR），收银员叫号（Grant），再结账（传数据）。免授权接入（Grant-free Access）像把小票直接投进智能箱：设备有数据就发导频+载荷，基站负责「谁在发、发了什么」。适合「注册很多、同时活跃很少、包很小」的大规模物联网（mMTC）。

## 摘要

对比授权四步调度与免授权一步发送，说明 5G NR 配置授权（Configured Grant）、2 步 RACH、NOMA/SIC 与压缩感知活跃检测，并对照 LoRaWAN/Sigfox 的免协调实践。延迟与效率数字为公开分析量级，实网依赖负载与实现[1][2][3]。

## 1 授权接入的痛点

```
SR → Grant → Data → ACK/NACK
```

小包场景下，控制信令字节可与数据同量级甚至更大，信令占比过高[1]。整点闹钟式突发还会挤爆 PRACH，重试加剧拥塞。

| 维度 | 基于授权（量级） | 免授权（量级） |
|------|------------------|----------------|
| 步骤 | 约 4 步 | 约 1 步（导频+数据） |
| 接入延迟 | 常十余 ms 量级 | 可低至配置周期内 |
| 信令 | SR+Grant 等 | 主要是导频开销 |
| 碰撞 | 调度可避免数据碰撞 | 需接收端分离/重传 |

## 2 免授权三要素

1. **预配置资源**：时频池事先告知设备。
2. **竞争接入**：多设备可能同资源发送。
3. **活跃检测 + 解码**：基站识别稀疏活跃集并解调[1][3]。

与传统 RACH 不同：RACH 仍是「先入网/再调度」的前置；免授权在第一步就带数据。

## 3 为何契合大规模 IoT

注册数 N 可很大，同时活跃 K ≪ N。为每设备永久独占资源浪费；逐个调度开销又大于小包本身。免授权让「只有活跃者占用资源」[1]。

电池侧：少监听 Grant、少往返，射频开启时间可下降（比例依赖实现，文献有数十百分点量级报告，须本机测）[3][4]。

## 4 5G NR：Configured Grant 与 2 步 RACH

| 类型 | 机制 | 适用 |
|------|------|------|
| CG Type 1 | 纯 RRC 配周期资源 | 固定周期上报 |
| CG Type 2 | RRC + DCI 激活/去激活 | 半静态业务 |
| 2-step RACH | MsgA（前导+数据）→ MsgB | 降握手往返[2][5] |

参数含 periodicity、MCS、repetition、RB 数等，按覆盖与可靠性标定[2]。动态调度仍保留作失败回退。

## 5 碰撞解决与压缩感知

| 方法 | 思路 | 注意 |
|------|------|------|
| NOMA + SIC | 功率差逐级解 | 功率接近时失效 |
| 扩频码 | 相关检测分离 | 码资源有限 |
| 压缩感知 / AMP 等 | 利用 K≪N 稀疏性 | 导频设计与复杂度 |

导频同时承担身份、信道估计、定时。正交导频长度随 N 不可扩展；非正交 + 稀疏恢复是主流方向。导频过短漏检升，过长开销升——常按活跃度 K 量级选取[1][4]。

| 算法 | 复杂度 | 场景倾向 |
|------|--------|----------|
| OMP | 较低 | 实时性优先 |
| LASSO | 中 | 通用 |
| AMP | 中 | 大规模 |
| SBL | 较高 | 精度优先 |

## 6 LoRaWAN 与 Sigfox

LoRaWAN Class A 上行本质是免协调 ALOHA：自选信道与数据率直发，无 SR/Grant；理论纯 ALOHA 吞吐上限约 18.4%，高负载靠多网关分集、捕获效应等缓解[6]。Sigfox 以极窄带随机频点 + 重复发送换可靠性，基站侧持续监听——「无协调」的极端形态。

## 7 混合策略

```
先免授权直发 → 成功则结束
失败 → 回退授权调度 / 重传
```

一般遥测可接受偶发重传；工业高可靠与 URLLC 需额外保底（重复、免授权+授权混合、专用资源）[3][5]。

## 8 案例要点

大规模土壤传感若用蜂窝配置授权：正常稀疏负载下一跳成功率高、延迟受 CG 周期约束；突发时依赖碰撞解决与下时隙重传。效益应报告为「信令与射频开启时间相对下降」，避免未经测量的「电池十年」断言。

## 9 局限、挑战与可改进方向

### 1. 碰撞与可靠性上限

**局限**：无协调必然碰撞，纯免授权难达极高可靠。
**改进**：SIC/多网关/混合回退；按 SLA 分层业务。

### 2. 漏检与虚警权衡

**局限**：阈值严则漏检丢包，松则虚警耗算力。
**改进**：业务定漏检预算；导频加长或分组检测。

### 3. N 增大时复杂度

**局限**：活跃检测随 N、码本规模上升。
**改进**：时频分组、分层粗检+精检、基站侧加速器。

### 4. 终端简单、标准碎片

**局限**：CG/2-step/厂商 NOMA 能力不一致。
**改进**：以 3GPP 能力查询为准；互操作测试矩阵。

## 参考文献

[1] L. Liu et al., "Sparse Signal Processing for Grant-Free Massive Connectivity," IEEE Signal Processing Mag., 2018.
[2] 3GPP, "TS 38.214: NR; Physical layer procedures for data," Release 16+.
[3] M. B. Shahab et al., "Grant-Free Non-Orthogonal Multiple Access for IoT," IEEE COMST, 2020.
[4] K. Senel, E. G. Larsson, "Grant-Free Massive MTC-Enabled Massive MIMO," IEEE Trans. Commun., 2018.
[5] 3GPP, "TR 38.824: Study on physical layer enhancements for NR URLLC," Release 16.
[6] LoRa Alliance, "LoRaWAN Specification," 1.0.x / 1.1.
[7] Y. Wu et al., "A Survey of Grant-Free Access for Massive IoT," related IEEE surveys / tutorials.
[8] Z. Chen, F. Sohrabi, W. Yu, "Sparse Activity Detection for Massive Connectivity," IEEE Trans. Signal Process., 2018.
[9] 3GPP, "TS 38.321: NR MAC protocol specification (Configured Grant)," Release 15+.
[10] Sigfox, "Technical Overview / Radio Protocol," Sigfox documentation.
[11] E. Björnson, E. de Carvalho, et al., works on massive MIMO grant-free access.
[12] ITU-R / 3GPP mMTC requirements context (IMT-2020 massive connectivity).
