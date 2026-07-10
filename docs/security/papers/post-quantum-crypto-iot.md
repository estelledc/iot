---
schema_version: '1.0'
id: post-quantum-crypto-iot
title: 后量子密码学在 IoT 中的迁移
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 22
prerequisites:
  - firmware-security
  - ota-secure-update
tags:
- 后量子密码
- PQC
- Kyber
- Dilithium
- NIST
- 格密码
- 混合TLS
- 嵌入式安全
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 后量子密码学在 IoT 中的迁移

> **难度**：🟡 中级 | **领域**：密码学、嵌入式安全 | **阅读时间**：约 22 分钟

## 日常类比

想象你家门锁是一把需要特定形状钥匙才能打开的机械锁。现在有人发明了“万能钥匙制造机”（大规模量子计算机）：给足时间，它能试出许多传统锁的钥匙形状。你需要换一种全新原理的锁——比如同时满足多个条件才能开启的组合锁，万能钥匙机也难以在合理时间内破解。

后量子密码学（Post-Quantum Cryptography, PQC）就是这把“新锁”。它不依赖大数分解、椭圆曲线离散对数等经典难题，而基于量子计算机目前也难以高效求解的数学结构（如格上的最短向量问题）。对物联网（Internet of Things, IoT）设备来说，挑战在于：新锁不能太重（内存）、不能太慢（周期），否则传感器节点根本“装不上”。

## 1. 量子计算对现有密码体系的威胁

### 1.1 Shor 算法的破坏力

1994 年 Peter Shor 提出的量子算法能在多项式时间内分解大整数并求解离散对数。公开文献与标准讨论中的常见结论可概括为：

| 算法 | 经典安全性（量级） | 量子攻击后（常见表述） |
|------|-------------------|----------------------|
| RSA-2048 | 约 112 bit | 可被彻底破解 |
| ECC P-256 | 约 128 bit | 可被彻底破解 |
| AES-128 | 约 128 bit | Grover 下约减半 |
| AES-256 | 约 256 bit | Grover 下约减半 |

对称密码受 Grover 算法影响相对可控（安全性量级减半），非对称公钥体系则面临结构性失效。[1][8]

### 1.2 “先存后破”攻击

即使大规模密码学相关量子计算机尚未出现，攻击者仍可现在截获密文，待量子能力成熟后再解密。IoT 设备生命周期常达十余年量级，今天部署的链路在退役前可能面临历史流量泄露风险。

### 1.3 时间线评估

Global Risk Institute 等机构的专家调查给出过阶段性概率区间（不同年份报告数字会变）。[8] 对工程决策更有用的是：**迁移窗口由设备寿命与“先存后破”共同决定**，而不是赌某一精确年份。

## 2. NIST 后量子密码标准

### 2.1 标准化历程

美国国家标准与技术研究院（National Institute of Standards and Technology, NIST）自 2016 年启动 PQC 标准化，2024 年 8 月发布首批标准：[1][2]

| 标准编号 | 算法名称 | 用途 | 基础数学问题 |
|---------|---------|------|-------------|
| FIPS 203 | ML-KEM（CRYSTALS-Kyber） | 密钥封装 | Module-LWE |
| FIPS 204 | ML-DSA（CRYSTALS-Dilithium） | 数字签名 | Module-LWE/SIS |
| FIPS 205 | SLH-DSA（SPHINCS+） | 数字签名 | 哈希函数 |

### 2.2 CRYSTALS-Kyber（ML-KEM）

Kyber 是基于格的密钥封装机制（Key Encapsulation Mechanism, KEM），用于替代椭圆曲线 Diffie–Hellman（Elliptic Curve Diffie–Hellman, ECDH）类密钥交换。[5]

```python
# 概念演示：Kyber KEM 流程（liboqs Python 绑定）
import oqs

kem = oqs.KeyEncapsulation("Kyber768")
public_key = kem.generate_keypair()
ciphertext, shared_secret_client = kem.encap_secret(public_key)
shared_secret_server = kem.decap_secret(ciphertext)
assert shared_secret_client == shared_secret_server
```

规范中的参数集量级（以公开规格为准，实现可能有填充差异）：[5]

| 参数集 | 安全级别（约） | 公钥 | 密文 | 共享密钥 |
|--------|---------------|------|------|---------|
| Kyber-512 | AES-128 等价 | ~800 B | ~768 B | 32 B |
| Kyber-768 | AES-192 等价 | ~1,184 B | ~1,088 B | 32 B |
| Kyber-1024 | AES-256 等价 | ~1,568 B | ~1,568 B | 32 B |

### 2.3 CRYSTALS-Dilithium（ML-DSA）

Dilithium 用于数字签名，替代 ECDSA/EdDSA。[6] 嵌入式上的毫秒级耗时高度依赖主频、实现与编译选项；下表仅作量级对照，应以本板实测为准。[3]

| 参数集 | 安全级别（约） | 公钥 | 签名大小 | Cortex-M4 量级（公开基准） |
|--------|---------------|------|---------|---------------------------|
| Dilithium2 | 128 bit | ~1.3 KB | ~2.4 KB | 毫秒级 |
| Dilithium3 | 192 bit | ~2.0 KB | ~3.3 KB | 数毫秒 |
| Dilithium5 | 256 bit | ~2.6 KB | ~4.6 KB | 数毫秒 |

### 2.4 SPHINCS+（SLH-DSA）

SPHINCS+ 是基于哈希的签名方案，数学假设更少，但签名尺寸可达数 KB 至数十 KB 量级，签名更慢。[7] 适合不频繁、对带宽不敏感的固件签名验证。

## 3. 格密码学基础

### 3.1 什么是格

格是 n 维空间中由基向量整数线性组合生成的离散点集。二维直觉：网格纸上的交叉点。

### 3.2 核心困难问题

**最短向量问题（Shortest Vector Problem, SVP）**：给定格基，找最短非零格向量；高维下已知最优算法呈指数级代价。

**带误差学习（Learning With Errors, LWE）**：给定矩阵 A 与带噪声乘积 b = As + e，恢复秘密 s。噪声使问题从线性代数变为困难问题。

### 3.3 Module-LWE

Kyber 与 Dilithium 使用 Module-LWE：在多项式模块上运算，相对标准 LWE 更紧凑，相对 Ring-LWE 假设更灵活。[5][6]

## 4. 受限设备上的实现挑战

### 4.1 资源约束（量级）

| 设备类别 | RAM（量级） | Flash（量级） | CPU（量级） | 代表芯片 |
|---------|------------|--------------|------------|---------|
| Class 0 | ~10 KB | ~100 KB | 十余 MHz | ATmega328P 类 |
| Class 1 | ~50 KB | ~256 KB | 数十 MHz | nRF52832 类 |
| Class 2 | ~256 KB | ~1 MB | 百 MHz 级 | STM32L4 类 |
| Class 3 | ~512 KB | ~2 MB | 数百 MHz | ESP32-S3 类 |

### 4.2 性能对照（ARM Cortex-M4）

pqm4 等公开基准表明：Kyber 在周期数上常可快于同类 ECC 操作，但公钥/密文尺寸显著更大。[3][10] **具体倍数随实现与参数变化，部署前必须在目标 MCU 复测。**

| 维度 | Kyber-768（量级） | ECC P-256（量级） | 工程含义 |
|------|------------------|------------------|---------|
| 计算 | 常更快 | 相对更慢 | CPU 未必是瓶颈 |
| 公钥/密文 | KB 级 | 数十字节 | 带宽与 Flash 更痛 |
| 栈峰值 | 数 KB 起 | 更小 | Class 0/1 需流式/裁剪 |

### 4.3 内存优化

流式数论变换（Number Theoretic Transform, NTT）、关闭未用算法、硬件真随机数（True Random Number Generator, TRNG）、DMA 搬移大数组，是嵌入式移植的常见手段。[3][4]

## 5. 混合经典 + 后量子方案

### 5.1 为什么需要混合

PQC 算法相对年轻，可能存在未发现的经典攻击；混合方案保证“至少不低于经典方案”，并便于兼容现网。[4][9]

### 5.2 混合 TLS 握手（概念）

客户端与服务器同时协商 X25519 与 Kyber 份额，再用密钥派生函数（如 HKDF）拼接派生会话密钥。Cloudflare 等已有真实部署经验可参考。[9]

### 5.3 IoT 混合策略

| 场景 | 建议 | 理由 |
|------|------|------|
| 网关/高算力节点 | 混合 KEM + 经典回退 | 兼容与安全冗余 |
| 带宽极紧（LoRa 等） | 预分发 + 少次在线交换 | 密文膨胀难承受 |
| 固件签名 | Dilithium 或 SPHINCS+ | 验证频率低、可接受大签名 |
| 极低 RAM | Kyber-512 + 流式 API | 先活下来再升档 |

## 6. 迁移路线图与工具链

### 6.1 分阶段策略（示意）

| 阶段 | 行动 | 目标 |
|------|------|------|
| 评估 | 密码资产清查、威胁建模 | 摸清暴露面 |
| 试点 | 混合方案、板级基准 | 验证可行性 |
| 迁移 | 逐步替换纯经典 | 降低“先存后破”风险 |
| 收尾 | 移除不安全回退 | 全面 PQ 就绪 |

时间表应绑定产品寿命与合规窗口，不宜照搬单一行业白皮书年份。

### 6.2 工具

Open Quantum Safe（OQS）的 liboqs、pqm4（Cortex-M4）是常见起点。[3][4] 生产代码需审计侧信道与常量时间实现。

## 7. 局限、挑战与可改进方向

### 1. 密文与密钥膨胀挤压 LPWAN

**局限**：Kyber 公钥/密文相对 ECC 增大一个数量级以上，LoRa/NB-IoT 等链路难以频繁在线 KEM。[5][10]
**改进**：会话密钥预分发与轮换；网关终结 TLS、终端只跑对称；压缩握手与证书裁剪。

### 2. 栈与 Flash 吃掉 Class 0/1 余量

**局限**：Dilithium 签名栈可达十余 KB 量级，与业务共存困难。[3][6]
**改进**：签名下沉到安全元件或网关；设备侧只做验证；选用更小参数集并做流式 NTT。

### 3. 实现侧信道与常量时间缺口

**局限**：规范安全 ≠ 芯片上安全；NTT、拒绝采样等步骤易泄漏。[3][10]
**改进**：采用经审计的 pqm4/厂商 IP；强制掩码与时序测试；把 TRNG 质量纳入量产测试。

### 4. 混合部署增加状态机复杂度

**局限**：双算法协商、回退与证书体积上升，易引入配置错误。[9]
**改进**：明确“仅混合 / 仅 PQ”策略矩阵；CI 中做互操作矩阵测试；监控回退比例。

### 5. 标准与库版本漂移

**局限**：Kyber→ML-KEM 命名与参数迁移期，库标识不一致会导致互操作失败。[1][5]
**改进**：锁定 FIPS 编号与测试向量；SBOM 记录算法 OID；OTA 支持算法能力位协商。

## 8. 实践建议（简）

1. 先清点：哪些链路怕“先存后破”，哪些只需短期机密性。
2. 网关先混合上线，终端按 RAM/带宽分级。
3. 固件签名可优先 PQ；高频会话密钥交换要算字节账。
4. 一切性能数字以目标板 + 目标库复测为准。

## 参考文献

[1] NIST, "FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard," Aug. 2024.
[2] NIST, "FIPS 204: Module-Lattice-Based Digital Signature Standard," Aug. 2024.
[3] M. Kannwischer et al., "pqm4: Testing and Benchmarking NIST PQC on ARM Cortex-M4," IACR ePrint, 2024.
[4] D. Stebila and M. Mosca, "Post-Quantum Key Exchange for the Internet and the Open Quantum Safe Project," SAC, 2016.
[5] P. Schwabe et al., "CRYSTALS-Kyber: Algorithm Specifications and Supporting Documentation," v3.02, 2024.
[6] R. Avanzi et al., "CRYSTALS-Dilithium: Algorithm Specifications," v3.1, 2024.
[7] A. Hülsing et al., "SPHINCS+: Submission to the NIST PQC Standardization," Round 3, 2022.
[8] Global Risk Institute, "Quantum Threat Timeline Report," 2024.
[9] Cloudflare, "Post-Quantum Cryptography in TLS: Real-World Deployment," Blog, 2024.
[10] T. Müller et al., "Post-Quantum Cryptography for Embedded Systems: A Performance Study," IEEE Internet of Things Journal, 2024.
[11] NIST, "FIPS 205: Stateless Hash-Based Digital Signature Standard," Aug. 2024.
[12] IETF, "Hybrid key exchange in TLS 1.3" (draft work), ongoing.
