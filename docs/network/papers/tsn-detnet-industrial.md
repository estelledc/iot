---
schema_version: '1.0'
id: tsn-detnet-industrial
title: TSN/DetNet 确定性网络：工业物联网的实时通信基石
layer: 3
content_type: survey
difficulty: advanced
reading_time: 28
prerequisites:
  - time-sync-ptp
  - opc-ua-tsn-industrial
tags:
  - TSN
  - DetNet
  - 802.1Qbv
  - 确定性网络
  - 工业以太网
  - 5G-TSN
  - FRER
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# TSN/DetNet 确定性网络：工业物联网的实时通信基石

> **难度**：🟠 进阶 | **领域**：确定性网络、工业以太网 | **阅读时间**：约 28 分钟

## 日常类比

普通以太网像不设限速的城市道路——多数时候通畅，堵车时谁也说不准多久到。工厂机械臂却需要「最坏情况也准时」：控制指令晚到，轻则焊缝歪，重则臂撞臂。**时间敏感网络（Time-Sensitive Networking, TSN）** 像给道路加定时绿灯波与应急车道；**确定性网络（Deterministic Networking, DetNet）** 则把类似保证从二层园区延伸到三层/广域[5][7]。

## 摘要

本文梳理 IEEE 802.1 TSN 标准族（时间同步、门控调度、帧抢占、无缝冗余等）、IETF DetNet 架构及其与 TSN 的衔接、3GPP 体系下 5G 与 TSN 融合思路，并对比传统工业以太网。延迟与抖动数字多来自标准目标或特定实验床，**随跳数、负载与硬件时间戳能力变化**[1][7][10]。

## 1 为什么要「确定性」

确定性强调的是**有界延迟与有界抖动**，而非仅平均延迟低。传统以太网延迟呈长尾：多数包很快，偶发排队可到毫秒甚至更高量级。运动控制等场景常要求周期在数百微秒到数毫秒、抖动微秒级——专用工业以太网（PROFINET IRT、EtherCAT 等）曾各自解决，但互操作与 IT/OT 融合成本高。TSN 目标是在标准以太网上用开放标准提供可调度确定性，并与 IT 流量共存[7][12]。

## 2 TSN 标准族

TSN 是 IEEE 802.1 下多标准的统称，各解决确定性的一个维度。

### 2.1 802.1AS — gPTP 时间同步

**广义精确时间协议（generalized Precision Time Protocol, gPTP）** 是 IEEE 1588 的 TSN 配置文件：对表选出主时钟（Grandmaster），从时钟用带时间戳的消息估计偏差与路径延迟。硬件时间戳下，园区规模同步精度常可达亚微秒量级；每跳误差累积与晶振、实现相关，**不宜写成固定「全网 <1μs」而不加条件**[1]。

### 2.2 802.1Qbv — 时间感知整形器（TAS）

**时间感知整形器（Time-Aware Shaper, TAS）** 用门控列表（Gate Control List, GCL）按时间开闭最多 8 个优先级队列出口门，把关键窗口与尽力而为窗口隔开，形成端到端「绿波」前提是全网时间对齐[2]。端到端延迟上界取决于周期、窗口长度与跳数，工程上从数十微秒到低毫秒均有报道。

### 2.3 802.1Qbu / 802.3br — 帧抢占

大帧占用线路时，高优先级小帧需等待整帧发完；千兆下最大帧传输时间约十余微秒量级。帧抢占允许打断低优先级帧并分段重组，缩小保护带（guard band），提高与 TAS 联用时的带宽效率[3]。

### 2.4 802.1CB — FRER

**帧复制与消除（Frame Replication and Elimination for Reliability, FRER）** 沿不相交路径双发（或多发），接收端按序列号去重，追求接近零切换时间的冗余，对比生成树类秒级收敛[4]。

### 2.5 其他标准一览

| 标准 | 功能 | 要点 |
|------|------|------|
| 802.1Qcc | 流预留与配置 | 分布式 / 集中网络 / 全集中（CUC+CNC）模型 |
| 802.1Qci | 每流过滤与策略 | 入口监管，抑制不合规突发 |
| 802.1Qcr | 异步流量整形（ATS） | 弱化对全网严格同步的依赖 |
| 802.1Qch | 循环排队转发（CQF） | 用循环缓冲简化门控 |
| 802.1Qdj | 配置增强 | CNC 的 YANG 等自动化接口 |

## 3 DetNet：确定性上到 L3

DetNet（RFC 8655）把有界延迟、低丢包与冗余等服务语义扩展到 IP/MPLS 等[5]。

| 对比维度 | TSN (IEEE 802.1) | DetNet (IETF) |
|----------|------------------|---------------|
| 层次 | 主要为 L2 以太网 | L3（IP/MPLS 等） |
| 范围 | 同一 L2 域/园区 | 可跨域、广域 |
| 延迟量级（典型叙述） | 微秒～低毫秒 | 毫秒～更高（视子网） |
| 时间同步 | 常用 802.1AS | 取决于下层技术 |
| 冗余 | 802.1CB FRER | PREOF 等，可复用 FRER 思想 |
| 数据面 | 以太网帧 | MPLS 或 IP/SRv6 等 |

车间内 TSN、厂间 DetNet、边界互通，是常见分层叙事；具体互通配置与运维复杂度仍高[5][7]。

## 4 5G 与 TSN 融合

3GPP 将 5G 系统建模为**逻辑 TSN 桥**，向集中网络配置（Centralized Network Configuration, CNC）暴露延迟/带宽等能力，使无线段可纳入端到端调度叙事[6][8]。无线链路抖动通常远大于有线 TSN 单跳；时间感知调度、包延迟预算（Packet Delay Budget）、5G 侧时钟同步等用于收紧分布。实验室与试验网报告中，端到端延迟有进入数毫秒～十余毫秒量级的案例，**能否覆盖运动控制要按周期与可靠性等级单独论证**[10]。

## 5 应用分层与工业以太网对比

| 应用类型 | 周期量级 | 延迟/抖动倾向 | 可靠性叙述 |
|----------|----------|---------------|------------|
| 运动控制 | 数百μs～1ms | 极严 | 极高 |
| PLC↔I/O | 1～10ms | 严 | 很高 |
| 过程监控 | 10～100ms | 中 | 高 |
| HMI/SCADA | 100ms～1s | 松 | 中 |
| IT 流量 | 尽力而为 | 无保证 | 尽力而为 |

TSN 价值常在于**同一物理网上共存**上述等级，减少独立 OT 布线[7][12]。

| 维度 | TSN | PROFINET IRT | EtherCAT | CC-Link IE TSN |
|------|-----|--------------|----------|----------------|
| 标准开放性 | IEEE 开放族 | PI 生态 | ETG 生态 | 基于 TSN |
| 与标准以太网 | 高兼容目标 | 部分场景需约束 | 常需专用路径 | 继承 TSN |
| 极短周期 | 视实现 | 可至数十μs 级 | 常更具竞争力 | 视配置 |
| IT/OT 融合 | 原生叙事强 | 常需分隔/网关 | 常需网关 | 融合叙事强 |
| 5G 集成 | 3GPP 有研究/规范路径 | 弱 | 弱 | 随 TSN |

性能上 EtherCAT 等在极短周期仍常领先；TSN 卖点更在互操作与融合[12]。

## 6 配置与工具链要点

802.1Qcc 三类模型：全分布式协商简单但能力有限；集中网络+分布式用户由 CNC 算调度；全集中式由集中用户配置（Centralized User Configuration, CUC）汇聚需求再交 CNC，大规模工厂更常见。

Linux 侧有 taprio（Qbv 类）、etf、mqprio 等；网卡/交换芯片需确认硬件时间戳与 TSN 特性。OPC UA Pub/Sub over TSN 是常见应用层组合叙事[11]。开源协议栈与 GCL 验证工具在演进中，**产线仍以认证交换机与厂商工具链为主**。

## 7 局限、挑战与可改进方向

### 1. 调度可扩展性与工程成本

**局限**：大规模 GCL 手工/求解器配置难；流量变更要重算，运维负担高[9]。
**改进**：CNC + YANG/自动化；流量分级，仅对真正关键流做门控，其余用优先级/ATS。

### 2. 有线指标不能外推到 5G 段

**局限**：把有线「微秒抖动」话术套到 5G+TSN 端到端会误导验收[8][10]。
**改进**：按 3GPP 延迟预算与现场无线测量验收；运动控制与过程监控分档签约。

### 3. 时钟与冗余的单点风险

**局限**：Grandmaster 失效、路径共模故障会使 AS/FRER 假设破产[1][4]。
**改进**：热备 GM、多域同步演练；冗余路径做真正不相交与故障注入测试。

### 4. 与遗留工业以太网共存

**局限**：存量 EtherCAT/PROFINET 岛与 TSN 骨干之间仍需网关，确定性在网关处可能被打破[12]。
**改进**：分阶段：先骨干 TSN 承载非最严流量；最严环保留专用技术并明确边界 SLA。

## 8 小结

TSN 用同步、门控、抢占与 FRER 等把以太网做成可调度的确定性载体；DetNet 尝试把服务语义扩展到 L3/广域。5G 融合与 AI 辅助排程是活跃方向，但部署成功取决于硬件时间戳、CNC 工程与分档验收，而非单一标准名[5][7][9]。

## 参考文献

[1] IEEE 802.1AS-2020, "Timing and Synchronization for Time-Sensitive Applications."
[2] IEEE 802.1Qbv-2015, "Enhancements for Scheduled Traffic."
[3] IEEE 802.1Qbu-2016, "Frame Preemption."
[4] IEEE 802.1CB-2017, "Frame Replication and Elimination for Reliability."
[5] N. Finn et al., "Deterministic Networking Architecture," RFC 8655, IETF, 2019.
[6] 3GPP TR 23.734, "Study on 5GS Enhanced Support for Vertical and LAN Services," Rel-16.
[7] A. Nasrallah et al., "Ultra-Low Latency (ULL) Networks: The IEEE TSN and IETF DetNet Standards and Related 5G ULL Research," IEEE COMST, 2019.
[8] D. Cavalcanti et al., "Extending Accurate Time Distribution and Timeliness Capabilities over the Air...," Proceedings of the IEEE, 2019.
[9] Y. Seol et al., "AI-Assisted TSN Gate Control List Scheduling Using Deep Reinforcement Learning," IEEE RTSS, 2024.
[10] A. Gogolev et al., "TSN-Enabled 5G for Industrial IoT: Experimental Evaluation," IEEE Access, 2024.
[11] OPC Foundation, "OPC UA over TSN" joint white paper / related materials.
[12] L. Wisniewski et al., "Comparison of Industrial Ethernet Solutions: PROFINET, EtherCAT, and TSN," IEEE Industrial Electronics Magazine, 2024.
[13] IEEE 802.1Qcc, "Stream Reservation Protocol (SRP) Enhancements and Performance Improvements."
