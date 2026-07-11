---
schema_version: '1.0'
id: duty-cycle-mac-protocol-iot
title: 占空比MAC协议在IoT低功耗通信中的设计
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - contention-based-mac-csma-aloha
  - iot-connectivity-energy-efficiency
tags:
- 占空比
- MAC
- ContikiMAC
- B-MAC
- S-MAC
- LPL
- 低功耗
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 占空比MAC协议在IoT低功耗通信中的设计

> **难度**：🔴 高级 | **领域**：低功耗 MAC、WSN | **阅读时间**：约 22 分钟

## 日常类比

保安不必 24 小时站门口：每 10 分钟出来看 30 秒，访客稍等，人却能长久值守。占空比（duty cycle）MAC 让无线电大多休眠，只在短窗口收发，把「空闲监听」（idle listening）从电池杀手降下来——代价是发送方要解决「对方何时醒」[1][2]。

## 摘要

对比 LPL/B-MAC、X-MAC、ContikiMAC/WiseMAC 与 S-MAC/T-MAC。占空比、寿命与延迟数字随射频电流与唤醒间隔变化，案例中的年寿命仅为量级估算[2][6]。

## 1 基本量

占空比 ≈ 活跃时间 / 周期。接收监听功耗常与发送同量级，故「只少发不少听」不够[6]。权衡：睡更久更省电，但延迟与漏包风险上升。

| 应用倾向 | 占空比量级（示意） |
|----------|-------------------|
| 偏实时控制 | 相对较高（如百分之一～十分之一） |
| 一般传感 | 千分之一量级常见设计区 |
| 超低功耗监测 | 更低，延迟更大 |

## 2 异步：前导码族

LPL（Low-Power Listening）：前导码长度 ≥ 接收方睡周期，保证醒来能撞上[1]。接收方极省，发送方很贵。B-MAC：CCA + 可配长前导，经典 TinyOS 实现[1]。

X-MAC：短前导序列 + 地址 + 早 ACK，缩短发送与误听[文献族，见 8]。

ContikiMAC：周期双 CCA；连续打数据包直至 ACK；相位锁定后对准邻居唤醒相，显著少打副本[2]。WiseMAC：学相位后缩前导，适稳定基础设施链路[5]。

## 3 同步：S-MAC / T-MAC

邻居对齐醒睡表，活跃期通信，无长前导；需 SYNC 与抗漂移[3]。T-MAC：超时无活动则提前睡，低负载更省，但有 early sleeping 风险[4]。

| 方案 | 同步 | 发送成本 | 接收成本 | 复杂度 |
|------|------|----------|----------|--------|
| B-MAC/LPL | 无 | 高 | 低 | 低 |
| X-MAC | 无 | 中 | 低 | 低 |
| ContikiMAC | 相位学习 | 低～中 | 低 | 中 |
| WiseMAC | 相位学习 | 低 | 低 | 中 |
| S-MAC | 需要 | 低 | 中 | 中 |
| T-MAC | 需要 | 低 | 低～中 | 中 |

确定性工业场景常另选 TSCH 等，不在本文展开。

## 4 多跳与报警

每跳可能垫一个唤醒周期，跳数一多延迟叠加。森林监测类叙事用 ContikiMAC 间隔估算端到端上界，须用真实 CCA 时长与重试模型校准，不能直接当 SLA[2][9]。

## 5 局限、挑战与可改进方向

### 1. 延迟抖动

**局限**：异步占空比使尾部延迟难界。
**改进**：关键告警提高占空比或走唤醒无线电；限制跳数；对 P99 做预算[2][10]。

### 2. 广播/泛洪与睡节点

**局限**：单次广播易打在睡窗口外。
**改进**：重复广播、同步调度、或 Trickle 类抑制算法配合[9]。

### 3. 固定占空比遇流量突变

**局限**：火灾/拥塞时窗口不够。
**改进**：负载自适应醒周期；分层：叶子低占空比、中继提高[4][11]。

### 4. 相位锁定失效

**局限**：时钟漂移、移动、偶发通信导致 ContikiMAC/WiseMAC 退化成长发送。
**改进**：周期性重学习；水晶与温漂纳入模型；稀疏流量改回短前导策略[2][5]。

## 参考文献

[1] J. Polastre et al., "Versatile Low Power Media Access (B-MAC)," ACM SenSys, 2004.
[2] A. Dunkels, "The ContikiMAC Radio Duty Cycling Protocol," SICS Technical Report, 2011.
[3] W. Ye et al., "S-MAC," IEEE/ACM ToN, 2004.
[4] T. van Dam, K. Langendoen, "T-MAC," ACM SenSys, 2003.
[5] A. El-Hoiydi, J.-D. Decotignie, "WiseMAC," ALGOSENSORS, 2004.
[6] Energy models of low-power radios (idle listening vs sleep).
[7] Survey papers on duty-cycled MAC for WSN/IoT.
[8] X-MAC and preamble sampling follow-on literature.
[9] Multihop latency under RDC analyses.
[10] Wake-up radio surveys (duty-cycle evolution path).
[11] Adaptive duty-cycling and traffic prediction MACs.
[12] IEEE 802.15.4 TSCH contrast notes for deterministic industrial links.
