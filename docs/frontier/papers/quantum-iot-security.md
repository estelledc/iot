---
schema_version: '1.0'
id: quantum-iot-security
title: 量子安全 IoT
layer: 8
content_type: technical_analysis
difficulty: advanced
reading_time: 30
prerequisites:
  - post-quantum-crypto-iot
  - ota-secure-update
  - secure-boot-root-of-trust
tags:
- 后量子密码
- PQC
- ML-KEM
- ML-DSA
- QKD
- 密码敏捷性
- IoT安全
- Harvest-Now-Decrypt-Later
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 量子安全 IoT

> **难度**：🟠 进阶 | **领域**：密码学 × IoT 安全 | **阅读时间**：约 30 分钟

## 一句话总结

容错量子计算机一旦成熟，可能用 Shor 算法威胁当前 IoT 广泛使用的 RSA/椭圆曲线密码；而工业与基础设施设备寿命常达十余年——因此需要尽早规划后量子密码（Post-Quantum Cryptography, PQC）迁移与密码敏捷性。

## "先收割后解密"的威胁

### 日常类比

想象有人把你家所有的锁都录了像。现在他打不开锁，但他预期未来会出现万能钥匙。所以他现在就把你家大门的视频存起来，等万能钥匙出来再"回放开锁"。

这就是"Harvest Now, Decrypt Later"（先收割后解密）攻击——攻击者现在截获加密的 IoT 通信数据并存储，待具备足够能力的量子计算机后再尝试解密。对寿命很长、机密性要求持久的工业 IoT、智能电网、车联网系统，该威胁需要纳入风险模型。

### 量子计算对密码学的影响

| 密码算法 | 经典安全性（现状） | 量子算法影响 | 工程含义 |
|---------|-------------------|-------------|---------|
| RSA-2048 | 当前广泛认为安全 | Shor 可多项式时间分解大数（需足够规模容错量子机） | 长期机密性风险高 |
| ECDSA/ECDH（椭圆曲线） | 当前广泛认为安全 | Shor 可求解离散对数 | 密钥交换/签名需替换 |
| AES-128 | 安全 | Grover 使穷举代价近似平方根下降 | 常建议升到 AES-256 |
| AES-256 | 安全 | Grover 后仍有较大安全边际 | 通常可保留 |
| SHA-256 | 安全 | Grover 影响有限 | 一般可保留 |
| HMAC | 安全 | 影响有限 | 一般可保留 |

**关键结论**：非对称密码（RSA/ECC）面临结构性风险；对称密码通常通过加长密钥缓解。IoT 最大暴露面往往在密钥交换与数字签名。

## NIST 后量子密码标准

美国国家标准与技术研究院（National Institute of Standards and Technology, NIST）自 2016 年启动 PQC 标准化。

### 标准化历程

| 时间线 | 事件 |
|--------|------|
| 2016 | NIST 征集 PQC 候选算法 |
| 2017-2019 | 第 1–2 轮筛选 |
| 2020-2022 | 第 3 轮评审 |
| 2024.08 | 发布 FIPS 203/204/205 |
| 2024-2025 | 继续评估额外候选（如 HQC 等） |

### 三个正式标准

| 标准号 | 算法名 | 原名 | 用途 | 基础数学问题 |
|--------|--------|------|------|-------------|
| FIPS 203 | ML-KEM | CRYSTALS-Kyber | 密钥封装（Key Encapsulation Mechanism, KEM） | 模格上的 LWE 问题 |
| FIPS 204 | ML-DSA | CRYSTALS-Dilithium | 数字签名 | 模格上的短向量问题 |
| FIPS 205 | SLH-DSA | SPHINCS+ | 数字签名（哈希备选） | 哈希函数安全性 |

### ML-KEM vs RSA/ECDH 性能对比

下表为常见公开基准的数量级对照，具体取决于实现、平台与参数集。

| 指标 | RSA-2048 | ECDH-256 | ML-KEM-768 |
|------|----------|----------|-----------|
| 公钥大小 | ~256 B | ~64 B | ~1.2 KB |
| 私钥大小 | ~256 B | ~32 B | ~2.4 KB |
| 密文/共享材料大小 | ~256 B | ~64 B | ~1.1 KB |
| 计算延迟 | RSA 私钥运算较慢 | 较快 | 通常与 ECC 同量级或更快 |
| 安全目标 | 经典约 112-bit 量级 | 经典约 128-bit | NIST Level 3 量级（含量子设定） |
| 量子安全设计目标 | 否 | 否 | 是 |

**关键观察**：ML-KEM 计算开销对许多网关/高端 MCU 可接受，但公钥/密文体积显著增大，对窄带 IoT 链路与小 MTU 协议是主要摩擦点。

### ML-DSA vs ECDSA 性能对比

| 指标 | ECDSA-256 | ML-DSA-65（Level 3 量级） |
|------|-----------|---------------------------|
| 公钥大小 | ~64 B | ~2 KB |
| 签名大小 | ~64 B | ~3 KB |
| 签名/验签 | 较快 | 通常可接受，签名更大 |
| 量子安全设计目标 | 否 | 是 |

## 轻量化 PQC：适配受限设备

### IoT 设备的密码学约束

| 设备类别 | RAM | Flash | CPU | 密码学预算 |
|---------|-----|-------|-----|-----------|
| Class 0（传感器标签） | <10KB | <100KB | 8-bit MCU | 极受限 |
| Class 1（基础传感器） | 约10KB | 约100KB | 32-bit Cortex-M0 | 受限 |
| Class 2（智能传感器） | 约50KB | 约250KB | Cortex-M4 | 中等 |
| 网关/边缘设备 | >256KB | >1MB | Cortex-A/RISC-V | 充裕 |

ML-KEM-768 在优化实现下可进入部分 Class 2 设备，但对 Class 0/1 仍困难；需结合参数降级、硬件加速或把握手上移到网关。

### 轻量化方案对比

| 方案 | 基础问题 | 公钥大小 | 签名/密文 | RAM 需求（量级） | 适用设备 |
|------|---------|---------|----------|-----------------|---------|
| ML-KEM-512 | 格（LWE） | ~800B | ~768B | 数 KB | Class 2+ |
| FrodoKEM-640 | 格（保守） | ~10KB | ~10KB | 更大 | 网关 |
| BIKE | 码 | ~KB | ~KB | 中 | Class 2+ |
| HQC | 码 | ~KB | ~KB | 中 | Class 2+ |
| SPHINCS+-128s | 哈希 | 极小 | 更大签名 | 较小 | 验证少的场景 |
| XMSS（有状态） | 哈希 | 小 | 中 | 小 | 能可靠管理状态的设备 |

**哈希基签名（SPHINCS+/XMSS）**对极度受限设备友好：安全性主要依赖哈希；公钥小；但签名大或需状态管理，适合固件签名等低频场景。

### 硬件加速

| 加速方式 | 加速比（宣称/预期量级） | 功耗影响 | 可用时间（展望） |
|---------|------------------------|---------|------------------|
| NTT 协处理器 | 数倍至十余倍 | 可显著降低 | 逐步落地 |
| SHA-3 硬件单元 | 数倍 | 降低 | 已有平台 |
| 矢量指令扩展 | 数倍 | 中等 | 部分 Cortex-M 已有 |
| 专用 PQC 加速器 | 更高 | 更高能效潜力 | 后续 SoC |

## 量子密钥分发（QKD）基础

量子密钥分发（Quantum Key Distribution, QKD）用量子态传输生成共享密钥，与 PQC 的数学困难问题路径不同。

### QKD 与 PQC 的关系

| 维度 | PQC（后量子密码） | QKD（量子密钥分发） |
|------|-----------------|-------------------|
| 安全基础 | 数学困难问题 | 量子力学物理定律 |
| 安全宣称 | 计算安全（依赖假设） | 信息论安全（理想模型下） |
| 部署方式 | 软件/固件可升级 | 需量子信道与专用硬件 |
| 距离限制 | 无物理距离限制 | 光纤约百公里量级，卫星可更远 |
| 成本 | 相对低 | 高 |
| 适用场景 | 通用 IoT | 高安全专网 |
| 成熟度 | 标准已发布，可工程部署 | 试验/专网为主 |

**结论**：绝大多数 IoT 场景应以 PQC + 密码敏捷为主；QKD 适合特定关键链路，而非海量终端标配。

### BB84 协议简述

BB84 核心机制：

1. Alice 向 Bob 发送随机偏振态的单光子
2. Bob 用随机选择的测量基测量
3. 双方公开比较测量基（不公开结果）
4. 测量基一致的位构成原始密钥材料
5. 窃听会扰动量子态，可通过误码率检测（超过阈值则放弃）

实际系统还需考虑探测器漏洞、边信道与可信节点中继等工程现实。

## IoT PQC 迁移路线图

### 迁移时间线（规划示意）

```
评估阶段：
  - 盘点现有 IoT 系统的密码学使用情况
  - 识别高风险资产（长寿命 + 持久机密性）
  - 在目标设备上测 PQC 内存/时延/能耗

混合部署阶段：
  - 新设备出厂支持经典+PQC 混合
  - 关键基础设施优先
  - TLS 等协议启用混合握手

全面迁移阶段：
  - 逐步淘汰纯经典长期机密性方案
  - PQC 成为默认
  - 证书与 PKI 体系同步

量子安全原生阶段：
  - 新协议原生 PQC
  - 关键节点可叠加 QKD
  - 密码敏捷性可快速切换算法
```

### 混合密码方案（Hybrid）

过渡期常用混合：经典与 PQC 同时贡献材料，任一路径未被攻破则会话仍受保护（具体安全证明依赖组合方式）。

```
混合密钥交换：
  共享密钥 = KDF(ECDH_shared_secret || ML-KEM_shared_secret)

混合签名：
  验证通过 = ECDSA_verify(msg) AND ML-DSA_verify(msg)
```

### IoT 特有挑战

| 挑战 | 描述 | 缓解策略 |
|------|------|---------|
| OTA 更新限制 | 许多设备难远程更新 | 设计预留算法槽位与闪存裕量 |
| 带宽受限 | PQC 材料更大 | 小参数集、会话复用、网关终结握手 |
| 长寿命设备 | 十余年在网 | 密码敏捷 + 可更新信任锚 |
| 供应链同步 | 芯片/模组/云需对齐 | 行业时间表与互操作测试 |
| 互操作性 | 新旧设备共存 | 协商 + 安全降级策略（避免被动降级攻击） |

### 密码敏捷性（Crypto-Agility）

```c
// 不好的设计（硬编码）
void sign_message(uint8_t* msg) {
    ecdsa_sign(msg, private_key);  // 无法更换
}

// 好的设计（密码敏捷）
void sign_message(uint8_t* msg, crypto_suite_t suite) {
    suite.sign(msg, private_key);  // 可替换算法
}
```

密码敏捷性意味着：算法可通过配置/OTA 切换；密钥存储与算法解耦；协议支持协商；预留存储/带宽裕量；并能安全地禁用已弃用套件。

## 行业进展

| 组织/企业 | 进展 | 时间 |
|----------|------|------|
| NIST | 发布 FIPS 203/204/205 | 2024.08 |
| Google Chrome | TLS 混合密钥交换试验/部署 | 2024 |
| Apple | iMessage PQ3（含 ML-KEM） | 2024 |
| Signal | PQXDH 等协议 | 2023 |
| AWS / Cloudflare 等 | 云与边缘 TLS 混合支持 | 2024 |
| IETF | 混合密钥交换相关工作（如 RFC 9370 方向） | 2024 |
| 3GPP | 研究对 5G/6G 安全的影响 | 进行中 |
| ISO | PQC 相关标准草案 | 推进中 |

## 局限、挑战与可改进方向

### 1. 窄带链路承载 PQC 握手困难

**局限**：LoRaWAN/部分 NB-IoT 场景下，KB 级公钥/密文会显著增加空口时间与能耗，甚至无法放入单帧。
**改进**：在网关/边缘终结 PQC 握手，终端维持对称会话；或采用更小参数集 + 会话票据复用；对固件签名改用哈希基方案并离线分发。

### 2. 侧信道与实现安全滞后于算法标准

**局限**：格密码的 NTT、采样等实现易受时序/功耗分析；MCU 上常数时间与掩码成本高。
**改进**：优先选用经过侧信道评估的实现；在 TrustZone/SE 内隔离；把高价值私钥运算放到安全元件。

### 3. 有状态哈希签名的状态丢失风险

**局限**：XMSS 等有状态方案若状态回滚（断电、克隆、快照恢复）会导致密钥复用灾难。
**改进**：默认优先无状态 SLH-DSA；若用有状态方案，状态必须单调持久化并防克隆；产线烧录与 OTA 流程单独审计。

### 4. 混合部署的降级攻击

**局限**：协商若允许回退到纯经典，攻击者可迫使双方放弃 PQC。
**改进**：对高价值会话强制混合或纯 PQC；策略由策略服务器签名下发；记录并告警降级事件。

### 5. 量子时间表不确定性导致投资错配

**局限**：容错量子机时间表不确定，过早全量替换成本高，过晚则 HNDL 风险累积。
**改进**：按数据机密性寿命分级迁移；先保护"今日截获、十年后仍敏感"的流量；持续跟踪密码分析与标准勘误。

## 参考文献

[1] NIST, "FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)," Federal Information Processing Standards, 2024.
[2] NIST, "FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)," Federal Information Processing Standards, 2024.
[3] NIST, "FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)," Federal Information Processing Standards, 2024.
[4] M. Chowdhury et al., "Post-Quantum Cryptography for IoT: A Comprehensive Survey," IEEE Communications Surveys and Tutorials, 2024.
[5] T. Prest et al., "Lightweight Post-Quantum Key Exchange for Constrained IoT Devices," IEEE Transactions on Information Forensics and Security, 2024.
[6] P. Kampanakis et al., "Post-Quantum TLS: Performance and Deployment Considerations," IEEE Security and Privacy, 2024.
[7] S. Bono et al., "Hybrid Key Encapsulation Mechanisms for Transitional Deployments," IETF RFC 9370, 2024.
[8] J. Bos et al., "CRYSTALS-Kyber on ARM Cortex-M4: Optimization and Side-Channel Protection," IACR Transactions on Cryptographic Hardware and Embedded Systems, 2024.
[9] BSI, "Migration to Post-Quantum Cryptography: Technical Guideline TR-02102-1," German Federal Office for Information Security, 2024.
[10] X. Lu et al., "Quantum-Safe IoT Security Architecture: From Theory to Deployment," IEEE Internet of Things Journal, 2024.
[11] P. W. Shor, "Algorithms for Quantum Computation: Discrete Logarithms and Factoring," Proceedings 35th Annual Symposium on Foundations of Computer Science, 1994.
[12] L. K. Grover, "A Fast Quantum Mechanical Algorithm for Database Search," Proceedings of the 28th Annual ACM Symposium on Theory of Computing, 1996.
