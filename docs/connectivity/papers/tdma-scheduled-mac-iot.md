---
schema_version: '1.0'
id: tdma-scheduled-mac-iot
title: TDMA调度式MAC在工业IoT中的确定性通信
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - wireless-hart-industrial-sensor
tags:
  - TDMA
  - TSCH
  - WirelessHART
  - 6TiSCH
  - MAC
  - 确定性
  - 工业物联网
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# TDMA调度式MAC在工业IoT中的确定性通信

> **难度**：🔴 高级 | **领域**：MAC协议 | **阅读时间**：约 18 分钟

## 日常类比

流水线工位若随时往传送带放零件会撞车；改成固定时间窗口轮流放，就不碰撞。时分多址（Time Division Multiple Access, TDMA）把时间切成时隙，设备只在自己的格子发送。工业物联网里，控制命令若因碰撞抖动数百毫秒，可能触发停机——确定性比“平均更快”更重要[1][2]。

## 摘要

说明 TDMA 帧/时隙、时间同步、集中/动态调度，并对照 IEEE 802.15.4 时隙信道跳频（Time-Slotted Channel Hopping, TSCH）与 WirelessHART。文中 10 ms 时隙、99.9% 可靠、毫秒级延迟为标准/案例**量级**，随跳频集、重试与干扰而变[1][2][3]。

## 1. 帧与时隙

帧循环；帧内时隙分配给链路。时隙内含保护时间、射频稳定、数据、确认（Acknowledgement, ACK）与余量。保护时间吸收晶振漂移与传播时延。

| 设计旋钮 | 变短/变少 | 变长/变多 |
|----------|-----------|-----------|
| 帧长 | 延迟上界降 | 每设备带宽升、效率常升 |
| 时隙长 | 支持更密调度 | 保护与 ACK 占比升 |
| 时隙数 | 设备少、每设备机会多 | 可纳更多设备 |

## 2. 相对载波侦听多路访问

| 维度 | TDMA | CSMA/CA |
|------|------|---------|
| 碰撞 | 设计上避免（调度正确时） | 概率降低 |
| 延迟 | 上界≈等待己方时隙 | 负载相关、难给硬上界 |
| 同步 | 必须 | 通常不需要 |
| 低负载效率 | 空闲时隙浪费 | 按需发送更省 |
| 高负载效率 | 无碰撞开销 | 碰撞与退避恶化 |
| 入网 | 需分配时隙 | 即可竞争 |

能耗上，省去空闲信道评估（Clear Channel Assessment, CCA）与碰撞重传可降低每包能量，**具体百分比依赖实现与负载**，不宜写死“省 20%”[3]。

## 3. 时间同步

数十 ppm 晶振下，分钟级可累积毫秒漂移；对 ~10 ms 时隙与亚毫秒保护带，必须周期性再同步。常见：信标对齐；或如 TSCH 在 ACK 中带时间校正，通信即同步[1][3]。

## 4. 调度策略

- **集中式**：网络管理器全局分配，优但有单点与入网时延。
- **静态**：部署时按节点号映射时隙，适合流量恒定。
- **动态**：6TiSCH 调度函数（Scheduling Function, SF）按队列增减单元；最小调度 + 按需是常见路径[4]。

## 5. TSCH 与 WirelessHART

TSCH 在时间×信道二维调度：`channel = (ASN + channelOffset) mod N`。绝对时隙号（Absolute Slot Number, ASN）递增使同链路跳频，持续干扰被打散[1][3]。

| 项目 | TSCH / 6TiSCH 叙事 | WirelessHART 叙事 |
|------|--------------------|-------------------|
| 时隙 | 常 10–15 ms 量级 | 10 ms 常见 |
| 信道 | 2.4 GHz 上十余信道 | 常避开 Wi-Fi 重叠后约 15 |
| 路由 | RPL / 图路由等 | 图路由 + 路径冗余 |
| IP | 6TiSCH 走 IPv6/6LoWPAN | 偏工业过程栈 |
| 可靠手段 | 跳频 + 重试 + 备路径 | 同类 + 集中网络管理器 |

WirelessHART（IEC 62591）作为早期工业无线实践，强调高可靠与秒级内确定性；具体 SLA 以项目合同与现场验收为准[2][5]。

## 6. 混合 MAC

IEEE 802.15.4 可在竞争期（Contention Access Period, CAP）用 CSMA，在无竞争期用保证时隙（Guaranteed Time Slot, GTS）。工业现场常：控制回路固定 TDMA；监测走共享时隙；告警预留优先单元[1][4]。

## 7. 局限、挑战与可改进方向

### 1. 规模与延迟耦合

**局限**：节点增多→帧变长→最坏等待上升。
**改进**：空间复用远距同隙；多 slotframe 叠加；按关键级拆网[3][4]。

### 2. 突发流量与静态表不匹配

**局限**：固定分配遇突发则排队或丢弃。
**改进**：共享时隙 + MSF 类按需；监控队列水位触发扩容[4]。

### 3. 同步失败导致“假 TDMA”

**局限**：漂移使邻隙重叠，确定性崩溃。
**改进**：缩短同步周期；监测邻居时间源；冗余时间父节点[1]。

### 4. 协调器/管理器单点

**局限**：集中调度实体故障影响入网与重调度。
**改进**：备份网络管理器；评估分布式 SF；演练切换[2][5]。

## 8. 实践要点

1. 先写清延迟上界与可靠目标，再选纯 TDMA 或混合。
2. 验收：抽断链路、加 Wi-Fi 干扰，看跳频+重试是否仍达标。
3. 运维盯 ASN 同步健康、黑名单信道、队列与重传率，而非只看在线率。

## 参考文献

[1] IEEE Std 802.15.4, Low-Rate Wireless Personal Area Networks (TSCH amendments included in later revisions).
[2] IEC 62591, Industrial communication networks — WirelessHART.
[3] T. Watteyne et al., Using IEEE 802.15.4e TSCH in the IoT, IEEE ComST, 2015.
[4] D. Dujovne et al., 6TiSCH: Deterministic IP-enabled Industrial Internet of Things, IEEE Comm. Mag., 2014.
[5] S. Petersen and S. Carlsen, WirelessHART versus ISA100.11a, IEEE Ind. Electron. Mag., 2011.
[6] IETF 6TiSCH architecture and scheduling function RFCs (e.g. RFC 8480 family and successors).
[7] ISA-100.11a / IEC 62734 industrial wireless documentation (contrast).
[8] IEEE 802.15.4 MAC energy measurement studies in TSCH vs CSMA (treat numbers as study-specific).
[9] Crystal oscillator ppm and guard-time dimensioning notes for slotted MAC.
[10] Industrial wireless coexistence with Wi-Fi — channel blacklisting practices.
[11] Graph routing reliability analysis in WirelessHART deployments (vendor/case studies).
