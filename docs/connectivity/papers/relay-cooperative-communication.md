---
schema_version: '1.0'
id: relay-cooperative-communication
title: 中继协作通信：IoT 网络的"接力赛跑"
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - diversity-techniques-iot-reliability
tags:
  - 中继
  - AF
  - DF
  - 协作分集
  - 全双工中继
  - 缓冲辅助中继
  - UAV中继
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 中继协作通信：IoT 网络的"接力赛跑"

> **难度**：🟡 中级 | **领域**：协作通信、分集技术 | **阅读时间**：约 18 分钟

## 日常类比

商场地下停车场收不到门口基站信号时，在楼梯口放“信号中转站”，像接力赛一层层传下去。中继（Relay）在源（Source）与目的（Destination）直达差时转发；协作通信则让多节点配合，形成虚拟多天线，换空间分集[1][2]。

## 摘要

本文讲清放大转发（AF）与解码转发（DF）的机制与中断直觉、最大最小中继选择、半双工代价与全双工自干扰、缓冲辅助与无人机（UAV）中继边界。仿真曲线与 dB 增益为模型/文献量级，**部署以链路预算与实测为准**[1][4]。

## 1. AF 与 DF

| 维度 | AF | DF |
|------|-----|-----|
| 中继行为 | 放大再发 | 解码再编码 |
| 噪声 | 同放大 | 不跨跳累积（错解可传播） |
| 复杂度/时延 | 低 | 高 |
| 适用直觉 | S–R 较好、实现极简 | S–R 高于解码门限、多跳更稳 |

AF 等效端到端信噪比常写为 \(\gamma_{eq}=(\gamma_{sr}\gamma_{rd})/(\gamma_{sr}+\gamma_{rd}+1)\)；DF 瓶颈常取 \(\min(\gamma_{sr},\gamma_{rd})\)。两时隙协议相对单时隙直传有速率折半，比较中断时须统一频谱效率定义[1]。

## 2. 协作分集

时隙 1 源广播，时隙 2 中继转发，目的端最大比合并（MRC）可得约 2 阶分集；\(K\) 个候选做选择式中继时，理想分集阶数叙事可达 \(K+1\)[1][4]。分布式空时编码可模拟 Alamouti 结构，但对同步与相位要求高，物联网（IoT）现场少见完整落地。

| 方案 | 分集阶数（理想） | 说明 |
|------|------------------|------|
| 直传 | 1 | 单路径 |
| 单中继 AF/DF | 2 | 直达+中继 |
| 选择式 \(K\) 中继 | \(K+1\) | 选最佳再转发 |

## 3. 中继选择

最大最小：\(R^*=\arg\max_k\min(\gamma_{sk},\gamma_{kd})\)。调和均值近似最大化 AF 端到端信噪比。反应式选择先筛 S–R 过门限者，再比 R–D，降低全网 CSI 开销[4]。定时器法：\(T_k=T_{\max}/f(\gamma_k)\)，先超时者发 FLAG，其余静默。

## 4. 全双工与缓冲

半双工占两时隙，频谱效率损失约一半。全双工同时收发，自干扰（Self-Interference, SI）相对期望信号可强数十至上百 dB 量级；传播域隔离、模拟对消、数字对消级联后，残余须压到噪声底附近才有净增益[6]。低功率 IoT 发射功率小，SI 相对易处理，但仍非“免调参”。

缓冲辅助中继在 R–D 差时暂存、好时再发（Max-Link 等），吞吐可高于固定交替，但引入排队时延——实时控制须设缓冲与等待上限[4]。

## 5. 能量收集与 UAV 中继

同时无线信息与功率传输（SWIPT）把接收功率按时间切换或功率分流用于解码与充电；转换效率与 \(\rho\) 为设备相关，**不可套用单一典型值当设计保证**[8]。UAV 中继视距概率高、位置可调，高度与水平位置需在路径损耗与视距概率间折中；轨迹优化多为研究热点，运维与空域合规是工程主成本[5][9]。

| 方案 | 优点 | 主要代价 |
|------|------|----------|
| 地面固定中继 | 简单、可市电 | 覆盖受建筑限制 |
| SWIPT 中继 | 少布电线 | 能量/信息折中紧 |
| UAV 中继 | 灵活 LoS | 续航、空域、运维 |

## 6. 局限、挑战与可改进方向

### 1. 半双工频谱损失

**局限**：两时隙协议吞吐上限受半双工约束[1]。
**改进**：增量中继；业务允许时评估全双工与 SI 预算。

### 2. CSI 与选择开销

**局限**：最优选择依赖及时 CSI，移动与休眠网络开销大[4]。
**改进**：反应式/定时器分布式选择；降低选择频率。

### 3. 缓冲时延

**局限**：吞吐增益可能换来不可接受的时延[4]。
**改进**：缓冲上限+截止时间；实时流与尽力而为分流。

### 4. UAV/SWIPT 工程化

**局限**：论文最优轨迹与能量效率难直接变成可运维产品[5][8]。
**改进**：先固定悬停点与市电/换电策略；能量参数以实测标定。

## 7. 实践要点

1. S–R 信噪比充足时 AF/DF 接近，优先简单 AF；门限附近优先 DF。
2. 对称几何放中点；弱链路侧偏向放置中继。
3. LoRaWAN 等标准中继（TS011）优先于自研多跳协议[7]。

## 参考文献

[1] Laneman, J. N. et al., "Cooperative Diversity in Wireless Networks," IEEE Trans. Inf. Theory, 2004.
[2] Nosratinia, A. et al., "Cooperative Communication in Wireless Networks," IEEE Commun. Mag., 2004.
[3] Bletsas, A. et al., "A Simple Cooperative Diversity Method Based on Network Path Selection," IEEE JSAC, 2006.
[4] Zlatanov, N. et al., "Buffer-Aided Cooperative Communications: Opportunities and Challenges," IEEE Commun. Mag., 2014.
[5] Zeng, Y. et al., "Wireless Communications with Unmanned Aerial Vehicles," IEEE Commun. Mag., 2016.
[6] Sabharwal, A. et al., "In-Band Full-Duplex Wireless: Challenges and Opportunities," IEEE JSAC, 2014.
[7] LoRa Alliance, "TS011: LoRaWAN Relay Specification," 2023.
[8] Liu, Y. et al., "Cooperative NOMA with SWIPT," IEEE JSAC, 2016.
[9] Wu, Q. et al., "Joint Trajectory and Communication Design for Multi-UAV Networks," IEEE TWC, 2018.
[10] Chen, X. et al., "Full-Duplex Relay for IoT Networks," IEEE IoT J., 2024 (treat claims as case-specific).
[11] Cover/El Gamal relay channel capacity foundations (CF).
