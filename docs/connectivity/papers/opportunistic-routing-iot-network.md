---
schema_version: '1.0'
id: opportunistic-routing-iot-network
title: 机会路由在IoT不稳定链路中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - flooding-vs-routing-mesh-iot
  - geographic-routing-gpsr-iot
tags:
  - 机会路由
  - ExOR
  - ORW
  - ETX
  - 链路多样性
  - WSN
  - 占空比
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 机会路由在IoT不稳定链路中的应用

> **难度**：🔴 高级 | **领域**：路由协议 | **阅读时间**：约 22 分钟

## 日常类比

传统寄信：指定一个邮递员，丢了再重寄。机会路由（Opportunistic Routing）：把信同时交给多个路过的人，谁先有效推进就由谁送，其余抑制——把“不可靠链路”变成多样性增益。

## 摘要

说明广播候选集、优先级协调、ExOR/ORW 思路，以及相对期望传输次数（ETX）的收益边界。吞吐与节能百分比来自特定实验，**占空比与协调开销会吞掉增益，须本网复测**[1][2][4]。

## 1. 为何传统单下一跳吃亏

无线 PRR（Packet Reception Rate）常落在“半好不好”区间：多径、遮挡、干扰使单链路重传多。固定路径上每跳 ETX≈1/p，多跳相加；中间质量链路被最短路径忽略却仍有用[3]。

## 2. 核心机制

发送者广播；任一更优邻居收到即算进展。多候选独立时，成功概率约 `1−Π(1−pi)`，有效 ETX 下降——链路越差，相对收益叙事通常越大（理想独立假设）[1][3]。

| 进展度量 | 直觉 |
|----------|------|
| 地理 | 更靠近目的 |
| 跳数/ETX | 到汇聚更“便宜” |
| 能量 | 兼顾剩余电量 |

必须抑制重复转发，否则变洪泛风暴。

## 3. ExOR 与协调

ExOR：包头带按优先级排序的转发者列表；最高优先级成功接收者转发，其余抑制。Wi-Fi mesh 实验曾报显著吞吐提升，但批处理、协调与常开监听**不直接适合深度睡眠传感网**[1]。

| 抑制方式 | 要点 |
|----------|------|
| 优先级定时器 | 高优先级先发，旁听则取消 |
| ACK/旁听 | 更稳、多一次空口 |
| 混合 | 定时器+序列号去重 |

## 4. 传感网：ORW 方向

ORW 等面向占空比：用 EDC（期望占空比唤醒）类度量，被动协调，适配睡眠–唤醒，而非 ExOR 式重批处理。相对 CTP 等收集树，文献报到达率/时延改善，幅度随拓扑变化[2][4]。

## 5. 能量账要算全

单跳上多接收者都耗 E_rx，发送次数虽降，接收侧可能升；端到端常靠“更少跳/更少重传”回本。低密度（候选<约 3）或 PRR 已很高时，机会路由易退化或得不偿失[3][5]。

| 更值得试 | 更应谨慎 |
|----------|----------|
| 中低 PRR、邻居较密 | PRR 很高、邻居极少 |
| 可容忍协调延迟 | 硬实时、RAM 极紧 |
| 汇聚收集流量 | 任意点对点复杂会话 |

## 6. 局限、挑战与可改进方向

### 1. 协调 vs 睡眠

**局限**：为旁听抑制而延长 RX，吃掉占空比收益。
**改进**：与异步 MAC 联合设计（ORW 类）；限制候选集大小。

### 2. 相关衰落

**局限**：邻居同时失败时，`1−(1−p)^n` 乐观。
**改进**：用实测联合接收统计；地理/相关感知选候选。

### 3. 状态与实现复杂度

**局限**：列表、缓存、定时器压 MCU RAM/栈。
**改进**：无显式列表的度量驱动；小候选集；关键路径才启用。

### 4. 与标准栈集成

**局限**：RPL/Thread 等默认单下一跳，改机会路由成本高。
**改进**：仅在有损骨干试验；或链路层协作 ACK 多样性，保持路由接口稳定。

## 7. 实践要点

1. 先画 PRR 与邻居度分布，再决定是否上机会路由。
2. 验收看端到端投递、重传次数、平均 RX-on 时间，而非只看一跳公式。
3. 抑制失败率（重复转发占比）作为一等指标。

## 参考文献

[1] S. Biswas, R. Morris, "ExOR: Opportunistic Multi-Hop Routing for Wireless Networks," ACM SIGCOMM, 2005.
[2] O. Landsiedel et al., "ORW: Opportunistic Routing for Duty-Cycled Wireless Sensor Networks," ACM SenSys / NSDI related ORW publications.
[3] H. Liu et al., opportunistic routing surveys for wireless ad hoc / sensor networks.
[4] R. Fonseca et al., "CTP: Collection Tree Protocol" (baseline comparison context), SenSys.
[5] D. S. J. De Couto et al., "A High-Throughput Path Metric for Multi-Hop Wireless Routing (ETX)," MobiCom, 2003.
[6] S. Chachulski et al., "Trading Structure for Randomness in Wireless Opportunistic Routing (MORE)," SIGCOMM, 2007.
[7] Geographic opportunistic routing variants (survey/experimental).
[8] IETF ROLL RPL (RFC 6550) — conventional single-next-hop baseline.
[9] Duty-cycled MAC and opportunistic forwarding interaction studies.
[10] Energy models for multi-receiver opportunistic forwarding (analytical/experimental).
[11] Link correlation aware opportunistic routing literature.
[12] Comparisons of opportunistic routing vs cooperative diversity / anypath routing.
