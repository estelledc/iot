---
schema_version: '1.0'
id: relay-cooperative-communication-iot
title: 中继协作通信在IoT覆盖扩展中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - diversity-techniques-iot-reliability
  - lorawan-relay-coverage-extension
tags:
  - 中继通信
  - 协作分集
  - AF/DF
  - LoRaWAN Relay
  - 覆盖扩展
  - 虚拟MIMO
  - LPWAN
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 中继协作通信在IoT覆盖扩展中的应用

> **难度**：🔴 高级 | **领域**：协作通信 | **阅读时间**：约 18 分钟

## 日常类比

村庄传话：一端喊不到另一端时，中间站几人接力。每人只对最近的人喊，总能量远低于一次超远吼叫。协作分集则像多人同喊一句话，对面把几路声音合在一起听清——多个单天线设备合作，接近多天线效果[1][2]。

## 摘要

当物联网（Internet of Things, IoT）终端功率与天线受限、直达网关不可靠时，中继把一跳长传拆成多跳短传；协作协议再叠加空间分集。本文对比放大转发（Amplify-and-Forward, AF）/解码转发（Decode-and-Forward, DF）/压缩转发（Compress-and-Forward, CF）、中继选择与 LoRaWAN Relay，并给出地下覆盖类部署边界。路径损耗指数与能耗倍数为模型结论，**实地须用链路预算与路测校准**[1][3]。

## 1. 为何需要中继

典型低功耗广域（LPWAN）终端发射功率常约 0–14 dBm，天线增益约 0–2 dBi，电池寿命要求常以年计；手机约 23 dBm 量级，约束不同[3]。功率随距离约 \(d^n\) 衰减（自由空间 \(n\approx2\)，室内常更高）：两跳各 \(d/2\) 时，理想模型下总发射能量可低于直传约 \(2^{n-1}\) 倍——**仅为路径损耗模型推论，忽略监听与协议开销**[1]。

| 约束 | IoT 终端（量级） | 手机（量级） |
|------|------------------|--------------|
| 发射功率 | 约 0–14 dBm | 约 23 dBm |
| 天线 | 小型 PCB，增益低 | 多天线/调谐更成熟 |
| 电池目标 | 数年常见 | 日充 |

## 2. 转发类型

| 类型 | 中继行为 | 优点 | 代价 |
|------|----------|------|------|
| AF | 放大再发 | 硬件简单、时延低 | 噪声同放大 |
| DF | 解码再编码 | 噪声不跨跳累积 | 复杂度/时延；错解可传播 |
| CF | 压缩观测再发 | 中继信道不足以可靠解码时可用 | 实现与联合解码复杂 |

固定中继始终转发，直达好时浪费半双工时隙；选择性 DF 仅在解码成功时转发；增量中继在目的节点否定应答（NACK）后才转发，平均频谱效率通常更高[1][2]。

## 3. 协作分集与选择

源广播、中继转发，目的端合并独立衰落副本，单中继理想分集阶数可达 2（误码随信噪比平方下降的高信噪比叙事）[1]。多候选时常用瓶颈准则：\(R^*=\arg\max_k\min(\gamma_{sk},\gamma_{kd})\)；分布式定时器法让信道越好者越早超时抢发，降低集中式信道状态信息（CSI）开销[4]。能量感知可把剩余电量并入评分，避免“信道最好但电量将尽”的中继被反复选中。

## 4. LoRaWAN 与拓扑

LoRaWAN 原生星形；地下室、室内深处仍可能盲区。LoRa Alliance 中继规范（TS011）定义专用信道/扩频因子上的监听与透明转发，网络服务器识别中继帧[3]。中继若持续接收，电流可达数 mA 量级叙事，**电池中继寿命常以周计而非年计，市电或严格占空比更常见**[3]。

| 协议/模式 | 拓扑 | 典型跳数叙事 | 场景 |
|-----------|------|--------------|------|
| LoRaWAN Relay | 星形经中继 | 常限 1 跳 | LPWAN 覆盖补盲 |
| Thread | 网状 | 家居数跳 | 智能家居 |
| WirelessHART | 网状 | 工业有限跳 | 过程监控 |
| BLE Mesh | 泛洪/受管 | 视配置 | 照明等 |

端到端可靠度为各跳乘积：每跳 95% 时，10 跳约 60% 量级——**多跳必须抬高每跳可靠度或限跳**[5]。

## 5. 地下停车场类案例要点

混凝土楼板衰减常按约 15–25 dB/层量级估算；屋顶网关到深层时链路余量可能不足。楼梯间市电中继、每跳只穿一层，常比每层独立网关更省回程与设备费——**具体 dB、元与余量须现场测**，公开案例数字不可当服务等级协议（SLA）[3]。

## 6. 局限、挑战与可改进方向

### 1. 半双工与频谱效率

**局限**：经典两时隙中继牺牲约一半时隙；直达好时固定转发浪费资源[1]。
**改进**：增量/选择性中继；有条件再评估全双工与自干扰消除成本。

### 2. 中继能耗与供电

**局限**：空闲监听往往主导能耗；电池中继难支撑“常听”[3]。
**改进**：市电专用中继；唤醒前导；监听窗口与业务占空比联调。

### 3. 多跳可靠度与时延

**局限**：跳数增加时端到端丢包与时延乘积恶化[5]。
**改进**：优先加网关密度；工业场景硬限跳数；关键告警走短路径。

### 4. 协作同步开销

**局限**：分布式波束成形/虚拟多输入多输出（MIMO）需紧同步与信道信息，工程落地难[2]。
**改进**：先落地单中继 DF/选择式方案；同步密集型能力标为研究项。

## 7. 实践要点

1. 先做直达链路预算与楼板/遮挡实测，再决定中继还是加网关。
2. S–R 链路差时慎用纯 AF；能可靠解码再优先 DF。
3. 验收看端到端投递率与电池寿命，不看单跳峰值信噪比。

## 参考文献

[1] Laneman, J. N., Tse, D. N. C., and Wornell, G. W., "Cooperative Diversity in Wireless Networks: Efficient Protocols and Outage Behavior," IEEE Trans. Inf. Theory, vol. 50, no. 12, 2004.
[2] Nosratinia, A., Hunter, T. E., and Hedayat, A., "Cooperative Communication in Wireless Networks," IEEE Commun. Mag., vol. 42, no. 10, 2004.
[3] LoRa Alliance, "LoRaWAN Relay Specification," TS011, 2022/2023.
[4] Bletsas, A. et al., "A Simple Cooperative Diversity Method Based on Network Path Selection," IEEE J. Sel. Areas Commun., vol. 24, no. 3, 2006.
[5] Surveys on multi-hop reliability and hop-count limits in WSN/IoT mesh.
[6] Cover, T. and El Gamal, A., "Capacity Theorems for the Relay Channel," IEEE Trans. Inf. Theory, 1979 (CF foundations).
[7] 3GPP / cellular relay and IAB overviews (when comparing LPWAN relay to cellular).
[8] WirelessHART / Thread mesh hop and latency design notes.
[9] BLE Mesh flooding delay and hop guidance (vendor/alliance docs).
[10] Energy models for idle listening vs TX/RX in duty-cycled relays.
[11] Indoor path-loss and floor attenuation measurement literature.
