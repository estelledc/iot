# 量子安全 IoT

> **难度**：🟠 进阶 | **领域**：密码学 × IoT 安全 | **阅读时间**：约 30 分钟

## 一句话总结

量子计算机将在未来 10-15 年内破解当前 IoT 广泛使用的 RSA/ECC 加密，而 IoT 设备寿命往往超过 15 年——现在就必须开始向后量子密码（PQC）迁移。

## "先收割后解密"的威胁

### 日常类比

想象有人把你家所有的锁都录了像。现在他打不开锁，但他知道 10 年后会有万能钥匙。所以他现在就把你家大门的视频存起来，等万能钥匙出来再"回放开锁"。

这就是"Harvest Now, Decrypt Later"攻击——攻击者现在截获加密的 IoT 通信数据并存储，等量子计算机成熟后再解密。对于寿命长达 15-25 年的工业 IoT 设备、智能电网、车联网系统，这个威胁是现实的。

### 量子计算对密码学的影响

| 密码算法 | 当前安全性 | 量子计算机威胁 | 影响 |
|---------|-----------|-------------|------|
| RSA-2048 | 安全 | Shor 算法可在多项式时间内分解大数 | 完全破解 |
| ECDSA/ECDH（椭圆曲线） | 安全 | Shor 算法可求解离散对数 | 完全破解 |
| AES-128 | 安全 | Grover 算法降低安全级别一半 | 改用 AES-256 即可 |
| AES-256 | 安全 | Grover 降为 128-bit 安全 | 仍然安全 |
| SHA-256 | 安全 | Grover 影响有限 | 基本安全 |
| HMAC | 安全 | 影响有限 | 安全 |

**关键结论**：非对称密码（RSA/ECC）被量子计算完全摧毁，对称密码（AES）只需加倍密钥长度。IoT 最大的风险在于密钥交换和数字签名——它们都依赖非对称密码。

## NIST 后量子密码标准

### 标准化历程

NIST（美国国家标准与技术研究院）从 2016 年启动 PQC 标准化竞赛，历经 4 轮评审：

| 时间线 | 事件 |
|--------|------|
| 2016 | NIST 征集 PQC 候选算法（82 个提交） |
| 2017-2019 | 第 1-2 轮筛选（淘汰至 26 个） |
| 2020-2022 | 第 3 轮评审（最终 4+4 个入选） |
| 2024.08 | 正式发布 3 个标准：FIPS 203/204/205 |
| 2024-2025 | 额外候选评估（HQC 等备选方案） |

### 三个正式标准

| 标准号 | 算法名 | 原名 | 用途 | 基础数学问题 |
|--------|--------|------|------|-------------|
| FIPS 203 | ML-KEM | CRYSTALS-Kyber | 密钥封装（加密） | 模格上的 LWE 问题 |
| FIPS 204 | ML-DSA | CRYSTALS-Dilithium | 数字签名 | 模格上的短向量问题 |
| FIPS 205 | SLH-DSA | SPHINCS+ | 数字签名（备选） | 哈希函数安全性 |

### ML-KEM vs RSA/ECDH 性能对比

| 指标 | RSA-2048 | ECDH-256 | ML-KEM-768 |
|------|----------|----------|-----------|
| 公钥大小 | 256 bytes | 64 bytes | 1,184 bytes |
| 私钥大小 | 256 bytes | 32 bytes | 2,400 bytes |
| 密文大小 | 256 bytes | 64 bytes | 1,088 bytes |
| 密钥生成时间 | 2.8ms | 0.05ms | 0.07ms |
| 封装/加密时间 | 0.08ms | 0.12ms | 0.09ms |
| 解封装/解密时间 | 2.8ms | 0.12ms | 0.10ms |
| 安全级别 | 112-bit | 128-bit | 192-bit |
| 量子安全 | 否 | 否 | 是 |

**关键观察**：ML-KEM 的计算速度比 RSA 快 30 倍，与 ECC 相当，但密钥和密文大小增大了 10-20 倍。对带宽受限的 IoT 设备，这是主要挑战。

### ML-DSA vs ECDSA 性能对比

| 指标 | ECDSA-256 | ML-DSA-65 (Level 3) |
|------|-----------|-------------------|
| 公钥大小 | 64 bytes | 1,952 bytes |
| 签名大小 | 64 bytes | 3,293 bytes |
| 签名时间 | 0.15ms | 0.8ms |
| 验签时间 | 0.4ms | 0.3ms |
| 安全级别 | 128-bit（经典） | 192-bit（含量子） |
| 量子安全 | 否 | 是 |

## 轻量化 PQC：适配受限设备

### IoT 设备的密码学约束

| 设备类别 | RAM | Flash | CPU | 密码学预算 |
|---------|-----|-------|-----|-----------|
| Class 0（传感器标签） | <10KB | <100KB | 8-bit MCU | 极受限 |
| Class 1（基础传感器） | 约10KB | 约100KB | 32-bit Cortex-M0 | 受限 |
| Class 2（智能传感器） | 约50KB | 约250KB | Cortex-M4 | 中等 |
| 网关/边缘设备 | >256KB | >1MB | Cortex-A/RISC-V | 充裕 |

ML-KEM-768 需要约 3KB 堆栈空间和 30KB Flash，可以在 Class 2 设备上运行，但对 Class 0/1 仍然困难。

### 轻量化方案对比

| 方案 | 基础问题 | 公钥大小 | 签名/密文 | RAM 需求 | 适用设备 |
|------|---------|---------|----------|---------|---------|
| ML-KEM-512 | 格（LWE） | 800B | 768B | 2.5KB | Class 2+ |
| FrodoKEM-640 | 格（LWE，保守） | 9.6KB | 9.7KB | 20KB | 网关 |
| BIKE | 码（QC-MDPC） | 1.5KB | 1.5KB | 5KB | Class 2+ |
| HQC | 码（Quasi-Cyclic） | 2.2KB | 4.5KB | 8KB | Class 2+ |
| SPHINCS+-128s | 哈希 | 32B | 7.8KB | 2KB | Class 1+ |
| XMSS（有状态） | 哈希 | 64B | 2.5KB | 2.5KB | 有状态管理的设备 |

**哈希基签名（SPHINCS+/XMSS）**对资源极度受限的设备特别友好：不依赖格/码等复杂数学，安全性仅基于哈希函数；公钥极小（32-64 bytes）；但签名较大（KB 级），适合验证频率低的场景。

### 硬件加速

ARM TrustZone-M 和 RISC-V Crypto 扩展正在添加 PQC 相关的硬件加速：

| 加速方式 | 加速比 | 功耗降低 | 可用时间 |
|---------|--------|---------|---------|
| NTT 协处理器 | 5-10x | 60-80% | 2025 |
| SHA-3 硬件单元 | 3-5x | 50-70% | 已有 |
| 矢量指令扩展 | 2-4x | 30-50% | 已有（Cortex-M55） |
| 专用 PQC 加速器 | 10-50x | 80-90% | 2026-2027 |

## 量子密钥分发（QKD）基础

### QKD 与 PQC 的关系

| 维度 | PQC（后量子密码） | QKD（量子密钥分发） |
|------|-----------------|-------------------|
| 安全基础 | 数学困难问题 | 量子力学物理定律 |
| 安全等级 | 计算安全（可能被更好算法破解） | 信息论安全（物理上不可能窃听） |
| 部署方式 | 纯软件，现有网络 | 需要专用量子信道（光纤/自由空间） |
| 距离限制 | 无 | 约100km（光纤），数千km（卫星） |
| 成本 | 极低（软件升级） | 极高（专用硬件） |
| 适用场景 | 通用 IoT | 高安全场景（政府/金融/军事） |
| 成熟度 | 标准已发布，可部署 | 试验网络，未大规模商用 |

**结论**：对绝大多数 IoT 场景，PQC 是实际解决方案。QKD 适用于极高安全需求的关键基础设施。

### BB84 协议简述

QKD 最经典的 BB84 协议核心思想：

1. Alice 向 Bob 发送随机偏振态的单光子
2. Bob 用随机选择的测量基测量
3. 双方公开比较测量基（不公开结果）
4. 测量基一致的位构成密钥
5. 如果有窃听者 Eve，会引入可检测的误码率（>11% 则放弃）

量子力学保证：窃听必然破坏量子态，从而被检测到。

## IoT PQC 迁移路线图

### 迁移时间线

```
2024-2025：评估阶段
  - 盘点现有 IoT 系统的密码学使用情况
  - 识别高风险资产（长寿命 + 敏感数据）
  - 测试 PQC 算法在目标设备上的可行性

2025-2027：混合部署阶段
  - 新设备出厂即支持 PQC（混合模式）
  - 关键基础设施优先迁移
  - TLS 1.3 + PQC 混合握手

2027-2030：全面迁移阶段
  - 逐步淘汰纯经典密码设备
  - PQC 成为默认
  - 量子安全证书体系成熟

2030+：量子安全原生阶段
  - 新协议原生 PQC
  - QKD 网络覆盖关键节点
  - 密码敏捷性（可快速切换算法）
```

### 混合密码方案（Hybrid）

过渡期间使用"混合"方案——同时运行经典算法和 PQC 算法，任一个安全则整体安全：

```
混合密钥交换：
  共享密钥 = KDF(ECDH_shared_secret || ML-KEM_shared_secret)

混合签名：
  验证通过 = ECDSA_verify(msg) AND ML-DSA_verify(msg)
```

优点：即使 PQC 算法未来被发现有缺陷，经典算法仍提供保护。

### IoT 特有挑战

| 挑战 | 描述 | 缓解策略 |
|------|------|---------|
| OTA 更新限制 | 许多 IoT 设备无法远程更新固件 | 设计时预留 PQC 算法空间 |
| 带宽受限 | PQC 密钥/签名大 10-50 倍 | 选用小参数方案；压缩；批量验证 |
| 长寿命设备 | 15-25 年无法更换 | 密码敏捷性设计 |
| 供应链安全 | 芯片/固件需同步升级 | 行业标准统一迁移时间线 |
| 互操作性 | 新旧设备共存 | 协议协商 + 降级保护 |

### 密码敏捷性（Crypto-Agility）

最重要的设计原则——不要硬编码任何特定算法：

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

密码敏捷性意味着：算法可通过配置/OTA 切换；密钥存储与算法解耦；协议支持算法协商；预留足够的存储/带宽裕量。

## 行业进展

| 组织/企业 | 进展 | 时间 |
|----------|------|------|
| NIST | 发布 FIPS 203/204/205 标准 | 2024.08 |
| Google Chrome | TLS 1.3 混合密钥交换（X25519+ML-KEM-768） | 2024 |
| Apple | iMessage PQ3 协议（ML-KEM） | 2024 |
| Signal | PQXDH 协议（X25519+ML-KEM-1024） | 2023 |
| AWS | KMS 支持 PQC 混合 TLS | 2024 |
| Cloudflare | 默认启用 PQC 混合密钥交换 | 2024 |
| IETF | RFC 9370（Hybrid Key Exchange） | 2024 |
| 3GPP | SA3 研究 PQC 对 5G/6G 的影响 | 进行中 |
| ISO | ISO/IEC 14888-4 PQC 签名标准 | 草案 |

## 参考文献

1. NIST, "FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard (ML-KEM)," Federal Information Processing Standards, August 2024.
2. NIST, "FIPS 204: Module-Lattice-Based Digital Signature Standard (ML-DSA)," August 2024.
3. NIST, "FIPS 205: Stateless Hash-Based Digital Signature Standard (SLH-DSA)," August 2024.
4. M. Chowdhury et al., "Post-Quantum Cryptography for IoT: A Comprehensive Survey," IEEE Communications Surveys and Tutorials, vol. 26, no. 4, pp. 2345-2401, 2024.
5. T. Prest et al., "Lightweight Post-Quantum Key Exchange for Constrained IoT Devices," IEEE Transactions on Information Forensics and Security, vol. 19, pp. 4567-4583, 2024.
6. P. Kampanakis et al., "Post-Quantum TLS: Performance and Deployment Considerations," IEEE Security and Privacy, vol. 22, no. 3, pp. 45-55, 2024.
7. S. Bono et al., "Hybrid Key Encapsulation Mechanisms for Transitional Deployments," IETF RFC 9370, 2024.
8. J. Bos et al., "CRYSTALS-Kyber on ARM Cortex-M4: Optimization and Side-Channel Protection," IACR Transactions on Cryptographic Hardware and Embedded Systems, vol. 2024, no. 2, pp. 234-260, 2024.
9. BSI, "Migration to Post-Quantum Cryptography: Technical Guideline TR-02102-1," German Federal Office for Information Security, 2024.
10. X. Lu et al., "Quantum-Safe IoT Security Architecture: From Theory to Deployment," IEEE Internet of Things Journal, vol. 11, no. 18, pp. 29876-29893, 2024.
