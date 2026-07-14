---
schema_version: '1.0'
id: multi-satellite-noma-irsa-iot
title: 多卫星 NOMA-IRSA 随机接入用于 IoT 网络
layer: 8
content_type: paper_reading
difficulty: frontier
reading_time: 19
prerequisites:
  - satellite-iot-leo-connectivity
  - noma-iot-access
  - grant-free-access-massive-iot
tags:
  - Satellite IoT
  - NOMA
  - IRSA
  - Random Access
  - NTN
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
target_paper:
  title: "Multi-Satellite NOMA-Irregular Repetition Slotted ALOHA for IoT Networks"
  authors:
    - Estefanía Recayte
    - Carla Amatetti
  year: 2026
  doi: 10.1109/ICC52391.2025.11160766
  url: https://arxiv.org/abs/2601.00341v1
---
# 多卫星 NOMA-IRSA 随机接入用于 IoT 网络

> 初读范围：本文基于 arXiv 元数据、摘要和公开条目信息建立阅读卡片；尚未完成 PDF 全文逐段复核、数学模型复算或仿真结果复现，因此保持 `UNVERIFIED / UNREVIEWED`。

## 为什么值得读

卫星 IoT 要服务大量低速率设备，设备常是偶发上报，不适合复杂调度。IRSA 通过不规则重复和时隙 ALOHA 提升随机接入性能，NOMA 则尝试让同一资源上多个信号可分离。多卫星场景进一步带来覆盖和干扰的新问题。

这篇论文适合补 `satellite-iot-leo-connectivity` 的随机接入细节，也连接 massive IoT 和 NTN。

## 论文要回答的问题

1. 多卫星 IoT 随机接入为什么容易产生碰撞和容量瓶颈。
2. NOMA 与 IRSA 结合如何提高可接入设备数量。
3. 多卫星接收会怎样改变冲突解析和性能上界。
4. 复杂度、同步和功率控制是否适合低功耗 IoT 终端。

## 初读要点

| 技术 | 作用 | 深读风险 |
| --- | --- | --- |
| Slotted ALOHA | 简化随机接入 | 碰撞概率高 |
| IRSA | 通过重复和 SIC 解碰撞 | 重复带来能耗 |
| NOMA | 同资源多用户复用 | 功率控制和接收复杂 |
| Multi-satellite | 增强覆盖和分集 | 同步和回传协调 |

## 放进全栈框架

- Layer 2 包含卫星链路和随机接入。
- Layer 3 关注接入协议和冲突恢复。
- Layer 8 对应 NTN 和大规模 IoT 前沿。

## 初读结论

这篇论文把卫星 IoT 的“能连上多少设备”问题具体化到随机接入协议。后续深读要核验终端复杂度和能耗假设，避免只从系统吞吐角度评估而忽略电池设备代价。

## 后续核验清单

- 抽取 NOMA-IRSA 的系统模型、度分布和解码流程。
- 核对多卫星接收、SIC 和功率控制假设。
- 比较吞吐、包丢失率、时延和终端能耗。
- 对接 `grant-free-access-massive-iot` 与 `satellite-direct-to-device-nbiot`。

## 参考文献

[1] E. Recayte and C. Amatetti, "Multi-Satellite NOMA-Irregular Repetition Slotted ALOHA for IoT Networks," arXiv:2601.00341, 2026. Related DOI: 10.1109/ICC52391.2025.11160766.
