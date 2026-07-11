---
schema_version: '1.0'
id: iot-massive-access-random-access
title: 大规模IoT随机接入与拥塞控制
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - grant-free-access-massive-iot
  - lpwan-capacity-planning-dense
tags:
  - 随机接入
  - RACH
  - ACB
  - EAB
  - 拥塞控制
  - mMTC
  - NB-IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 大规模IoT随机接入与拥塞控制

> **难度**：高级 | **领域**：大规模接入 | **阅读时间**：约 22 分钟

## 日常类比

演唱会散场万人同时发朋友圈，基站像只有几十个窗口的售票处——这就是随机接入拥塞。蜂窝物联网里，一个小区可能面对远超传统语音设计的并发；不加控制会“越重试越堵”[1][2]。

## 摘要

分析随机接入信道（Random Access Channel, RACH）过载、接入类别限制（Access Class Barring, ACB）、扩展接入限制（Extended Access Barring, EAB）、退避、窄带 RACH、两步 RACH 与免竞争/预配置授权。碰撞概率与案例设备数为**教学近似**，以 3GPP 与现网参数为准[1][3]。

## 1 问题本质

传统 RACH 假设小区内数百人偶发接入；大规模机器类通信（mMTC）目标密度可到每平方公里百万量级（需求目标）[1]。

| 场景 | 密度倾向 | 到达特征 |
|------|----------|----------|
| 人类通信 | 较低 | 近似泊松 |
| 智慧城市 | 高 | 周期可预测 |
| 事件驱动 | 极高 | Beta 类突发 |

前导码有限（常用约数十个量级）时，同时尝试数上升，碰撞概率急剧恶化——公式为近似，用于建立直觉[2][4]。

## 2 过载与分层控制

碰撞 → 重试 → 更多碰撞，可致拥塞崩溃。

| 层级 | 机制 | 位置 |
|------|------|------|
| 接入前 | ACB/EAB | UE 过滤 |
| 接入中 | 退避 | 碰撞后等待 |
| 核心网 | 拥塞控制 | MME/AMF |
| 应用 | 错峰 | 服务器 |

**ACB**：SIB 广播 `ac-BarringFactor` 与 `ac-BarringTime`，概率放行；高优先级接入类别可免检。动态 ACB 随负载调因子，受系统信息更新周期限制[3]。

**EAB**：面向延迟容忍 IoT，可按类别位图更强硬限制，紧急时给人类/高优先级腾资源。

**退避**：RAR 指示 Backoff Indicator；指数退避拉大重试窗。ACB 减同时尝试数，退避在时间上打散重试——参数需协同[2]。

## 3 NB-IoT 与 5G 两步 RACH

窄带物理随机接入信道（NPRACH）可配周期、重复与覆盖等级（CE0/1/2）。两步 RACH（MsgA/MsgB）减信令往返，利小数据与功耗；需较好信道与额外资源，失败可回退四步[5]。

## 4 免竞争路径

| 方案 | 效率 | 灵活性 | 碰撞 | 适用 |
|------|------|--------|------|------|
| 预配置授权 | 低（易闲置） | 低 | 无 | 严格周期 |
| 半持续调度 SPS | 中 | 中 | 无 | 半固定周期 |
| 免授权 + NOMA | 高 | 高 | 可能 | 随机小数据 |

## 5 地震传感示意

十万级设备同时醒：无控制时过载倍数可达极端。EAB 先放行高优先级类别 + 动态 ACB + 退避，用数十秒到数分钟换“全体同时成功”。要点：分级、时间换容量、多机制协同、灾害场景预规划[1][2]。

## 6 机制对照

| 技术 | 时机 | 思想 | 代价 |
|------|------|------|------|
| ACB | 接入前 | 概率减载 | 延迟↑ |
| EAB | 接入前 | 禁低优先级 | 容忍业务更慢 |
| 退避 | 碰撞后 | 时间分散 | 单次更慢 |
| 两步 RACH | 接入中 | 少往返 | 条件苛刻 |
| 预配置/免授权 | 事前 | 少竞争 | 资源预留 |

## 7 局限、挑战与可改进方向

### 1. 参数难自适应

**局限**：静态 ACB 因子在突发前后都不合适。
**改进**：负载估计驱动动态 ACB；与应用层错峰联动[2]。

### 2. 仿真乐观

**局限**：忽略核心网信令与重传积压。
**改进**：端到端模型含 MME/AMF；用现网计数器校准[1]。

### 3. 预配置浪费

**局限**：周期资源在静默期空转。
**改进**：SPS/Configured Grant 可释放；混合动态调度[5]。

### 4. 优先级配置错误

**局限**：抄表与告警同类，EAB 一刀切误伤。
**改进**：入网前规划接入类别；合同明确告警豁免。

## 8 总结

大规模接入的核心是把突发抹平：接入前减载、碰撞后分散、能预配置则少竞争。工程上多机制叠加，并用现网指标验证，而非只看理论吞吐峰值。

## 参考文献

[1] 3GPP TR 37.868, "Study on RAN Improvements for Machine-type Communications," Rel-11.

[2] A. Laya et al., "Is the Random Access Channel of LTE and LTE-A Suitable for M2M Communications?" IEEE Communications Surveys & Tutorials, 2014.

[3] 3GPP TS 36.321, "E-UTRA MAC protocol specification."

[4] C. H. Wei et al., "Modeling and Estimation of One-Shot Random Access for Finite-User Multichannel Slotted ALOHA," IEEE Communications Letters, 2012.

[5] 3GPP TS 38.321, "NR MAC protocol specification," Rel-16+.

[6] 3GPP TR 45.820, "Cellular System Support for Ultra-Low Complexity and Low Throughput IoT."

[7] 3GPP TS 36.331, "E-UTRA RRC" (ACB/EAB related SIBs).

[8] M. Hasan et al., "Random Access for Machine-to-Machine Communication in LTE-Advanced Networks," IEEE Communications Magazine, related MTC surveys.

[9] 3GPP TS 38.300, "NR overall description" (two-step RACH overview).

[10] ITU-R M.2410 / IMT-2020 mMTC related requirements notes.

[11] F. Adelantado et al., "Understanding the Limits of LoRaWAN," IEEE Communications Magazine, 2017 (ALOHA intuition for unlicensed massive access).
