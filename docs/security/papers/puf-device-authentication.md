---
schema_version: '1.0'
id: puf-device-authentication
title: PUF物理不可克隆函数：IoT设备的"硅指纹"认证
layer: 6
content_type: technical_analysis
difficulty: advanced
reading_time: 20
prerequisites:
  - secure-boot-root-of-trust
  - firmware-security
tags:
- PUF
- 物理不可克隆函数
- 设备认证
- SRAM PUF
- 硬件安全
- 机器学习攻击
- 硅指纹
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# PUF物理不可克隆函数：IoT设备的"硅指纹"认证

> **难度**：🟡 进阶 | **领域**：硬件安全、设备认证 | **阅读时间**：约 20 分钟

## 日常类比

你有两支同型号钢笔，肉眼看完全一样。用显微镜看笔尖，金属晶粒排列却不同——冷却结晶是随机过程。同一产线、同一批材料，也造不出两个一模一样的笔尖。

物理不可克隆函数（Physical Unclonable Function, PUF）就是芯片世界的“显微镜下笔尖”。两颗同设计、同批次芯片，因硅工艺纳米级波动，延迟、阈值电压、存储单元上电初值略有不同。PUF 把这些差异提成唯一数字“指纹”，用于物联网（Internet of Things, IoT）轻量身份。

## 一句话总结

PUF 利用制造过程不可避免的随机差异生成不可复制的硬件身份：无长期明文密钥落盘、难克隆，适合成本敏感的设备认证。[1][2]

## 1. 为什么 IoT 需要 PUF？

传统做法是在 Flash / eFuse 中烧写密钥，存在探针读取、克隆镜像、安全注入成本等问题。

| 问题 | 传统密钥存储 | PUF |
|------|-------------|-----|
| 物理攻击 | Flash 可被读取提取 | 无静态密钥可直接拷贝 |
| 克隆 | 复制存储内容即可 | 物理差异难复制 |
| 成本 | 常需 OTP/安全存储 | 可复用已有电路 |
| 密钥注入 | 需安全产线流程 | 响应天然形成 |
| 轮换 | 密钥固定难换 | 可用新挑战-响应对刷新 |

对亚美元到数美元级传感器节点，PUF 常被定位为“几乎零额外硅成本”的身份方案——具体仍取决于 IP 授权与测试开销。[4][10]

## 2. 工作原理：挑战-响应

### 2.1 机制

1. **注册**：制造商输入一系列挑战（Challenge），记录响应（Response），挑战-响应对（Challenge-Response Pair, CRP）存于安全服务端。
2. **认证**：服务器抽未用挑战；设备现场计算响应；匹配则通过。

期望性质：不同芯片对同一挑战响应差异大（汉明距离理想约 50%）；同芯片可重复但受噪声影响；未知实例难以预测新挑战响应。[2]

### 2.2 噪声与 Fuzzy Extractor

温度、电压、老化会使同挑战响应出现少量 bit 翻转。常用模糊提取器（Fuzzy Extractor）配合 BCH / Reed-Solomon 等纠错码，并存储公开辅助数据（Helper Data）以稳定出密钥；设计目标是 Helper Data 不泄露密钥信息。[2][9]

## 3. 主要 PUF 类型

### 3.1 SRAM PUF

静态随机存储器（Static Random-Access Memory, SRAM）单元上电时，交叉耦合反相器失配使每位随机稳定为 0/1。优点是可复用片上 SRAM、商业化程度高（如 Intrinsic ID / NXP 路线）。[4][9] 公开材料常称大部分 bit 相对稳定，仍有一定比例需纠错；老化会缓慢改变稳定性——具体比例随工艺与温度范围变化，应以供应商表征为准。

### 3.2 Arbiter PUF

信号沿两条对称路径竞赛，仲裁器输出谁先到。CRP 空间可随级数指数增长，属“强 PUF”，但延迟模型近似线性，易受机器学习（Machine Learning, ML）建模攻击。[3][7] 变体包括 XOR Arbiter、Feed-Forward、Interpose 等。

### 3.3 Ring Oscillator PUF（RO-PUF）

比较结构相同的环形振荡器频率差产生 bit。实现相对简单、现场可编程门阵列（Field-Programmable Gate Array, FPGA）友好，但 CRP 空间有限、面积与功耗更高。[2]

### 3.4 其他类型（成熟度参差）

| PUF 类型 | 原理 | 优势 | 成熟度（概览） |
|----------|------|------|----------------|
| DRAM PUF | 衰减/刷新模式 | 复用内存 | 偏研究 |
| Flash PUF | 编程噪声 | 复用存储 | 产品化推进中 |
| 量子隧穿等 | 隧穿/散射 | 强物理随机 | 小众/高安全定位 |

## 4. 类型综合对比

| 指标 | SRAM PUF | Arbiter PUF | RO-PUF |
|------|----------|-------------|--------|
| CRP 空间 | 弱（有限） | 强（指数级） | 弱（组合有限） |
| 面积 | 极低（复用） | 低 | 中 |
| 可靠性 | 中（需纠错） | 中 | 相对高 |
| 抗 ML | 强（弱 PUF） | 弱 | 较强 |
| 商业化 | 高 | 低 | 中 |
| IoT 适用 | 很好 | 需增强 | 好 |

## 5. 机器学习攻击与对策

Arbiter 类响应可近似为挑战的延迟加权函数；攻击者收集足够 CRP 后可训练预测模型。[3][7] 公开实验显示：简单 Arbiter 在较少样本下即可达很高预测准确率；XOR 层数增加会抬高样本与算力需求，但并非不可攻破。Transformer 等模型还探索了跨实例迁移。[5]

**对策（设计）**：非线性组合、限制 CRP 暴露、用完即弃。
**对策（协议）**：Lockdown、挑战/响应混淆、查询限速。
**对策（系统）**：CRP 库放可信执行环境（Trusted Execution Environment, TEE）或硬件安全模块，结合异常查询检测。[5][6]

| PUF / 变体 | 攻击难度（相对） | 备注 |
|------------|-----------------|------|
| 明文 Arbiter | 低 | 经典 ML 即可 |
| 多 XOR Arbiter | 中–高 | 样本需求上升 |
| Interpose 等 | 较高 | 仍需持续评估 |
| SRAM（弱 PUF） | 不适用 CRP 建模 | 威胁面转向 Helper Data / 协议 |

（具体样本数与准确率随论文设定变化大，上表只给相对排序，不绑定单一实验数字。）

## 6. IoT 认证协议要点

轻量协议目标：无公钥运算、通信量适配低功耗广域网（Low-Power Wide-Area Network, LPWAN）、设备端少存 CRP。

典型流程：服务器发挑战 → 设备算 PUF 响应 → 回传 `Hash(响应 || Nonce)` → 服务器用注册响应校验 → 标记 CRP 已用。[6]

| 方案 | 计算（量级） | 通信量（量级） | 设备密钥存储 | 主要风险 |
|------|-------------|---------------|-------------|---------|
| 预共享密钥 | 极低 | 很小 | 有 | 提取/克隆 |
| TLS-PSK | 中 | 中 | 有 | 依赖安全存储 |
| 证书 TLS | 高 | 大 | 有 | PKI 与算力 |
| PUF + Hash | 低 | 小 | 无静态密钥 | CRP 耗尽/协议弱点 |
| PUF + Fuzzy Extractor | 低–中 | 小 | Helper Data | 纠错失败/辅助数据设计 |

## 7. 商业化与生态（概览）

| 厂商/产品线 | PUF 类型（公开表述） | 目标市场 |
|------------|---------------------|---------|
| Intrinsic ID QuiddiKey | SRAM PUF | MCU/SoC |
| Synopsys PUF IP | 多类型 | SoC |
| ICTK 等 | Via 等 | 汽车/工业 |
| Crypto Quantique QDID | 量子隧穿类 | 高安全 IoT |
| PUFsecurity 等 | 多类型 | RISC-V 等 |

NXP LPC55S6x 等系列集成 SRAM PUF IP，用于片内密钥派生与安全存储；售价与出货量随渠道变化，选型以数据手册与安全认证为准。[4][10]

## 8. 局限、挑战与可改进方向

### 1. 环境噪声导致认证失败或纠错过重

**局限**：宽温、低压、老化使比特错误率上升，Fuzzy Extractor 消耗更多熵与代码。[2]
**改进**：按工作温区做出厂表征；自适应 Helper Data；关键设备定期重注册稳定 CRP。

### 2. 强 PUF 易被 ML 建模

**局限**：Arbiter 族在 CRP 泄露下可被高精度预测。[3][5][7]
**改进**：优先弱 PUF + 密钥派生；强 PUF 必须限流、一次性 CRP，并持续红队建模。

### 3. Helper Data 与协议实现短板

**局限**：硅指纹再好，协议重放、CRP 数据库泄露、辅助数据设计不当仍会垮。[6]
**改进**：服务端 HSM/TEE；挑战绑定会话与设备证书；形式化/渗透测试认证协议。

### 4. 供应链与 IP 依赖

**局限**：商用 PUF 依赖授权 IP 与工艺角；自研 PUF 难保证熵与可靠性。[4]
**改进**：要求供应商提供熵测试报告与生命周期老化数据；双供应商策略。

### 5. 与后量子/长生命周期协同不足

**局限**：协议若只依赖短哈希或弱口令式构造，长期安全模型不清晰。[6]
**改进**：哈希与 KDF 选对标算法；与安全启动、安全元件统一密钥层次。

## 9. 实践建议（简）

1. IoT 默认优先 SRAM/弱 PUF 做密钥派生，而不是裸奔强 PUF 认证。
2. 量产前做温压老化与唯一性/可靠性统计，而不是只看实验室室温数据。
3. CRP 或派生密钥的服务端保护与设备侧同等重要。

## 参考文献

[1] B. Gassend et al., "Silicon Physical Random Functions," CCS, 2002.
[2] C. Herder et al., "Physical Unclonable Functions and Applications: A Tutorial," Proceedings of the IEEE, vol. 102, no. 8, 2014.
[3] U. Rührmair et al., "PUF Modeling Attacks on Simulated and Silicon Data," Journal of Cryptographic Engineering, 2013.
[4] Intrinsic ID, "QuiddiKey: SRAM PUF-based Security IP," Product Documentation, 2024.
[5] Y. Wu et al., "Transformer-based Modeling Attacks on PUFs," CHES, 2024.
[6] U. Chatterjee et al., "PUF-based Authentication Protocols for IoT: A Comprehensive Survey," IEEE Internet of Things Journal, vol. 11, no. 5, 2024.
[7] J. Delvaux, "Machine-Learning Attacks on PolyPUFs, OB-PUFs, RPUFs, LHS-PUFs, and PUF-FSMs," IEEE TIFS, 2019.
[8] Crypto Quantique, "QDID: Quantum-Driven Identity for IoT," Technical Whitepaper, 2024.
[9] J. Guajardo et al., "FPGA Intrinsic PUFs and Their Use for IP Protection," CHES, 2007.
[10] NXP Semiconductors, "LPC55S6x Security Features," Application Note AN13079, 2024.
[11] R. Maes, *Physically Unclonable Functions: Constructions, Properties and Applications*, Springer, 2013.
[12] C. Helfmeier et al., "Cloning Physically Unclonable Functions," HOST, 2013.
