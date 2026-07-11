---
schema_version: '1.0'
id: contention-based-mac-csma-aloha
title: 竞争式MAC协议CSMA/ALOHA在IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags:
  - CSMA
  - ALOHA
  - MAC协议
  - LoRaWAN
  - IEEE-802.15.4
  - 碰撞
  - 隐藏终端
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 竞争式MAC协议CSMA/ALOHA在IoT中的应用

> **难度**：🟡 中级 | **领域**：MAC 协议 | **阅读时间**：约 20 分钟

## 日常类比

多人同屋交谈：有人“想说就说”，撞车就停一会再试——这是 ALOHA；有人“先听后说”，安静才开口——这是载波侦听多路访问（Carrier Sense Multiple Access, CSMA）。介质访问控制（Medium Access Control, MAC）没有中央话筒管理员时，靠这类规则减少碰撞[1][4]。

## 摘要

本文对比纯 ALOHA、时隙 ALOHA 与带碰撞避免的 CSMA（CSMA/CA），说明 LoRaWAN 为何偏 ALOHA、IEEE 802.15.4/Zigbee 为何偏 CSMA/CA，并讨论隐藏终端与能耗。经典利用率上限 \(1/(2e)\approx 18.4\%\)、\(1/e\approx 36.8\%\) 来自理想模型；现场碰撞率随负载、捕获效应与多信道而变[1][3][4]。

## 1. 竞争式 vs 调度式

| 类型 | 思路 | 优点 | 缺点 | 代表 |
|------|------|------|------|------|
| 竞争式 | 自由尝试发送 | 简单、弹性 | 碰撞、时延随机 | ALOHA、CSMA/CA |
| 调度式 | 预分配时隙 | 可无碰撞、更确定 | 需同步与编排 | TDMA、TSCH |

适合竞争式：节点数动态、流量突发、可容忍一定重传。

## 2. ALOHA 族

**纯 ALOHA**：有数据即发，无确认则随机退避重试。易受碰撞窗口约为两倍包时长，理想最大信道利用率约 \(1/(2e)\)[1]。

**时隙 ALOHA**：仅在时隙边界发送，窗口缩为约一倍包时长，理想上限约 \(1/e\)，代价是时间同步[1]。

**LoRaWAN 上行**：终端不做可靠空闲信道评估（Clear Channel Assessment, CCA）式侦听即发。原因包括：扩频信号可在噪底附近，CCA 不可靠；终端求简；占空比与低上报率使负载常远低于理论拐点。多信道 × 多扩频因子（Spreading Factor, SF）正交性与捕获效应进一步降低“同频同 SF 同时”的有效碰撞[3]。

| 条件 | 纯 ALOHA 倾向 | 时隙 ALOHA |
|------|---------------|------------|
| 同步 | 不需要 | 需要 |
| 理想利用率上限 | ~18% | ~37% |
| IoT 例 | LoRaWAN 上行 | 部分蜂窝随机接入简化模型 |

## 3. CSMA/CA 与 802.15.4

发送前做能量检测和/或载波侦听；忙则退避。CSMA/CA 用随机退避降低“同时听空同时发”。IEEE 802.15.4 定义多种 CCA 模式与退避指数参数；非信标模式常见于星型传感网，信标模式支持超帧与无竞争期[2]。

| 负载倾向 | ALOHA | CSMA/CA | 更合适 |
|----------|-------|---------|--------|
| 极稀疏 | 碰撞少、无 CCA 开销 | CCA 收益有限 | ALOHA |
| 中等 | 碰撞上升 | 侦听有效 | CSMA/CA |
| 很高 | 易崩溃 | 退避膨胀 | 考虑 TDMA/多信道 |
| LoRa 远距 | CCA 不可靠 | 不适用 | ALOHA |

隐藏终端：A 与 C 互听不见却都向 B 发，CSMA 失效。无线局域网常用请求发送/清除发送（RTS/CTS），但对短包 IoT 开销大，实务多用确认（ACK）+ 重传与拓扑规划缓解[4][2]。

## 4. 能耗直觉

碰撞浪费发射与空等 ACK 的能量；CCA 本身能量通常远小于一次成功发包。故中等负载下“先听”往往净省电；极稀疏网络则可能不值得[2][5]。

## 5. 案例对照（示意）

智慧停车：日级稀疏事件、LoRaWAN → ALOHA 足够。楼宇 Zigbee：分钟级上报、短距 CCA 有效 → CSMA/CA。具体碰撞率须按包时长与信道数核算，表中“<1%”仅为低负载示意[3][2]。

| 维度 | 稀疏 LPWAN | 楼宇 802.15.4 |
|------|------------|---------------|
| MAC | ALOHA | CSMA/CA |
| CCA | 基本不用 | 核心 |
| 复杂度 | 低 | 中 |

## 6. 局限、挑战与可改进方向

### 1. 理想吞吐公式误导容量规划

**局限**：把 \(1/e\) 当可运营目标，忽略重传、下行、占空比监管。
**改进**：用系统级仿真/试商用计数；以包成功率和电池寿命为验收。

### 2. CCA 跨技术失效

**局限**：只能可靠检测同类波形，对 Wi-Fi 等可能过保守或听不见。
**改进**：频段规划与共存设计；高干扰区降速率或加信道。

### 3. 负载突发导致相变

**局限**：活动触发同步上报时，网络从“稀疏良好”跳到拥塞崩溃。
**改进**：抖动上报相位；接入分级；超阈切调度 MAC 或多网关。

### 4. 公平性与捕获效应

**局限**：近网关强信号“赢”碰撞，远节点饿死。
**改进**：自适应数据速率与功率；网络侧监测边缘成功率并限近端占空比。

## 参考文献

[1] N. Abramson, "The ALOHA System—Another Alternative for Computer Communications," AFIPS, 1970.
[2] IEEE Std 802.15.4, "Low-Rate Wireless Networks."
[3] LoRa Alliance, "LoRaWAN Specification" 与区域参数.
[4] L. Kleinrock and F. Tobagi, "Packet Switching in Radio Channels: Part I—Carrier Sense Multiple-Access Modes," IEEE Trans. Communications, 1975.
[5] G. Bianchi, "Performance Analysis of the IEEE 802.11 Distributed Coordination Function," IEEE JSAC, 2000.
[6] A. Bachir et al., "MAC Essentials for Wireless Sensor Networks," IEEE Communications Surveys & Tutorials, 2010.
[7] I. Demirkol, C. Ersoy, and F. Alagoz, "MAC Protocols for Wireless Sensor Networks: A Survey," IEEE Communications Magazine, 2006.
[8] J. Polastre, J. Hill, and D. Culler, "Versatile Low Power Media Access for Wireless Sensor Networks," SenSys, 2004.
[9] A. Rahmadhani and F. Kuipers, "When LoRaWAN Meets CSMA" 等 LoRa 与侦听研究.
[10] T. Watteyne et al., "Industrial IEEE 802.15.4e TSCH" 相关（调度式对照）.
[11] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Communications Magazine, 2017.
[12] S. Gollakota et al., "Clearing the RF Smog" / 跨技术干扰与载波侦听相关工作.
