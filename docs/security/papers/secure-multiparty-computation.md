---
schema_version: '1.0'
id: secure-multiparty-computation
title: 安全多方计算 MPC 在 IoT 中的应用
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 24
prerequisites:
  - homomorphic-encryption-practical
  - differential-privacy-iot
tags:
- MPC
- 安全多方计算
- 秘密共享
- SPDZ
- 隐私计算
- 混淆电路
- IoT隐私
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 安全多方计算 MPC 在 IoT 中的应用

> **难度**：🟡 中级 | **领域**：隐私计算、密码学 | **阅读时间**：约 24 分钟

## 日常类比

三个邻居想算平均月收入，却不愿暴露各自工资。传统做法找“可信公证人”代收代算。

安全多方计算（Secure Multi-Party Computation, MPC）不需要这个公证人：各方只交换加密或随机份额，最终得到约定函数结果，却推不出他人输入。物联网（Internet of Things, IoT）里，这意味着多网关可联合统计用电或训练模型，而不必汇集原始读数。[10]

## 1. 核心概念与安全模型

### 1.1 目标

n 方各持私有输入 x₁…xₙ，共同计算 f(x₁…xₙ)，只学到允许输出。安全性常用**理想-现实模拟范式**：现实协议应与“理想可信第三方代算”不可区分。[10]

### 1.2 敌手模型

| 敌手类型 | 行为 | 假设强度 | 典型场景 |
|----------|------|----------|----------|
| 半诚实（Semi-honest） | 守协议但窥探消息 | 较弱 | 企业联合分析 |
| 恶意（Malicious） | 可任意偏离 | 较强 | 对抗强 |
| 隐蔽（Covert） | 敢作弊但怕被抓 | 居中 | 有声誉约束的商业 |

IoT 设备可被物理攻破，恶意模型更贴近现实，但通信/计算开销也更大——这是部署核心矛盾。

### 1.3 安全强度用语

- **计算安全**：多项式敌手不可破（如基于困难假设）
- **统计安全**：允许极小出错概率（如 2⁻ᵏ 量级）
- **信息论安全**：不依赖计算假设（如诚实多数下的 Shamir 共享）[3]

## 2. 基础原语

### 2.1 秘密共享（Secret Sharing）

把秘密拆成多份，单份无信息，够门限可恢复。Shamir 为多项式门限方案；加法共享则 s = s₁+…+sₙ，天然支持本地加法同态。[3]

### 2.2 不经意传输（Oblivious Transfer, OT）

发送方有 m₀,m₁，接收方选 bit b：只得 m_b，发送方不知 b，接收方不知另一条。混淆电路用 OT 传输入标签；OT 扩展与 Silent OT 等持续降低通信。[8]

### 2.3 混淆电路（Garbled Circuits, GC）

Yao 协议把函数编成布尔电路并加密真值表，求值方逐门解密得输出标签。[1] 适合两方、布尔味重的计算。

## 3. 协议族对比

| 协议 | 年代 | 基础 | 参与方 | 安全模型 | 适合 |
|------|------|------|--------|----------|------|
| Yao GC | 1986 | 混淆电路 | 2 | 半诚实起 | 布尔 |
| GMW | 1987 | OT+共享 | 多方 | 半诚实/恶意 | 通用 |
| BGW | 1988 | Shamir | 诚实多数 | 信息论 | 算术 |
| SPDZ | 2012 | 加法共享+MAC | 不诚实多数 | 恶意 | 算术 |
| ABY | 2015 | 混合共享 | 2 | 半诚实 | 混合 |
| ABY3 | 2018 | 三方复制共享 | 3 | 恶意 | ML 等 |

### 3.1 SPDZ 直觉

离线预生成 Beaver 三元组 (a,b,c=a·b)；在线用公开掩码把乘法变成本地运算加一轮通信。[4] 工业与学术框架（如 MP-SPDZ）广泛实现该族。[7]

### 3.2 ABY 混合

Arithmetic / Boolean / Yao 三种共享可转换，按子电路选最优表示，常比单一共享更快——具体加速比依赖电路结构，文献报告有数倍量级，需实测。[5][6]

## 4. 实用框架

| 框架 | 语言 | 协议覆盖 | 恶意安全 | IoT 适配 | 活跃度 |
|------|------|----------|----------|----------|--------|
| MP-SPDZ | Python DSL 等 | 很广 | 支持 | 中（偏服务器/网关） | 高 |
| ABY/ABY3 | C++ | 聚焦 | ABY3 等 | 中 | 中 |
| CrypTen | PyTorch | 偏 ML | 有限 | 低–中 | 高 |
| MOTION | C++ | 多种 | 支持 | 相对更易嵌入 | 中 |

终端 MCU 很少直接跑完整恶意 MPC；常见模式是**终端只做份额拆分，网关/边缘跑协议**。[7][9]

## 5. IoT 应用场景

### 5.1 隐私聚合

智能电网等场景需要区域总量调度，又不希望细粒度用电曲线暴露作息。[10] 工程上要在采集周期（如十余分钟级）内完成；公开演示常给出百节点、百毫秒到秒级延迟的量级，**强依赖网络与协议变体，不能当 SLA**。

### 5.2 联合异常检测 / 安全推理

多方工厂或医院联合建模、推理：模型方护参数，数据方护样本。[6][9]

| 运算类型（示意） | 相对明文开销（文献量级） | 工程含义 |
|------------------|--------------------------|---------|
| 加法 | 数倍 | 常可接受 |
| 乘法 | 数十–上百倍 | 需预计算与批处理 |
| 比较 | 上百倍级 | 尽量少用或改电路 |
| 简单 ML 推理 | 百倍级常见 | 放边缘/云，不放 MCU |

上表数字来自公开基准的粗量级，换硬件与协议会变；上线前必须用本拓扑复测。[6][7]

### 5.3 与同态加密 / TEE 对比

| 维度 | MPC | 同态加密（HE） | TEE |
|------|-----|----------------|-----|
| 信任 | 密码学假设+阈值 | 密码学 | 硬件厂商与实现 |
| 通信 | 高（多轮） | 相对单向 | 低 |
| 计算 | 中 | 常极重 | 接近明文 |
| 侧信道 | 协议层较少 | 较少 | 需防微架构泄漏 |
| IoT | 需分层优化 | 端侧难 | 有硬件时友好 |

实践中常组合：TEE 护本地，MPC 做跨域，HE 做单向外包。[9][10]

## 6. 性能优化方向

| 技术 | 原理 | 作用 |
|------|------|------|
| OT 扩展 / Silent OT | 少次基 OT 扩大量 OT | 降通信 [8] |
| 函数秘密共享（FSS） | 部分函数本地化 | 减在线轮次 |
| 电路优化 | 减 AND/乘法门 | 直接降成本 |
| 分层架构 | MCU 只共享，边缘跑在线阶段 | 适配异构 IoT |
| 离峰预计算 | Beaver 等放夜间/云 | 削峰在线延迟 |

## 7. 局限、挑战与可改进方向

### 1. 通信轮次与 LPWAN 不兼容

**局限**：每次乘法常需交互；LoRa 等几十 kbps 链路撑不住中等电路。[8]
**改进**：聚合放到宽带网关；终端仅上传份额；严格限制乘法门并批处理多周期数据。

### 2. 恶意安全代价过高

**局限**：半诚实原型到恶意部署，带宽与 CPU 可再涨一个数量级。[4][7]
**改进**：三方诚实一者模型（ABY3）换成本；关键任务才上恶意；其余用合同+审计。

### 3. 设备掉线破坏协议假设

**局限**：IoT 节点间歇在线，同步 MPC 易卡死。
**改进**：选支持退出/鲁棒的协议变体；法定人数网关代持；超时降级为延迟批处理。

### 4. 实现与侧信道缺口

**局限**：学术原型常量时间、随机数质量参差，嵌入式移植易引入泄漏。
**改进**：选用活跃框架并跟进 CVE；份额与密钥进 SE/TEE；做功耗/时序回归。

### 5. 功能与合规预期错配

**局限**：MPC 不自动满足“最小必要”或差分隐私；输出仍可能泄露聚合敏感信息。[10]
**改进**：输出加噪或门限；数据最小化；与法务共同定义可发布统计。

## 8. 实践建议（简）

**选型树**：2 方布尔 → Yao/ABY；3 方且可信一者 → ABY3；多方恶意 → SPDZ 族。
**部署**：树莓派/网关先测带宽与轮次，再谈 MCU。
**入门**：加法共享跑通 → MP-SPDZ 示例 → 再读 Evans 等教材。[7][10]

## 参考文献

[1] A. C. Yao, "How to Generate and Exchange Secrets," FOCS, 1986.
[2] O. Goldreich, S. Micali, and A. Wigderson, "How to Play ANY Mental Game," STOC, 1987.
[3] M. Ben-Or, S. Goldwasser, and A. Wigderson, "Completeness Theorems for Non-Cryptographic Fault-Tolerant Distributed Computation," STOC, 1988.
[4] I. Damgård et al., "Multiparty Computation from Somewhat Homomorphic Encryption," CRYPTO, 2012. (SPDZ)
[5] D. Demmler, T. Schneider, and M. Zohner, "ABY – A Framework for Efficient Mixed-Protocol Secure Two-Party Computation," NDSS, 2015.
[6] P. Mohassel and P. Rindal, "ABY3: A Mixed Protocol Framework for Machine Learning," CCS, 2018.
[7] M. Keller, "MP-SPDZ: A Versatile Framework for Multi-Party Computation," CCS, 2020.
[8] E. Boyle et al., "Silent OT Extension and Its Applications," CRYPTO, 2023.
[9] B. Knott et al., "CrypTen: Secure Multi-Party Computation Meets Machine Learning," NeurIPS, 2021.
[10] D. Evans, V. Kolesnikov, and M. Rosulek, "A Pragmatic Introduction to Secure Multi-Party Computation," Foundations and Trends in Privacy and Security, 2018.
[11] I. Damgård et al., "Practical Covertly Secure MPC for Dishonest Majority – Or: Breaking the SPDZ Limits," ESORICS, 2013.
[12] C. Hazay and Y. Lindell, *Efficient Secure Two-Party Protocols*, Springer, 2010.
