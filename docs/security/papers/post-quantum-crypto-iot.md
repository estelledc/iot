# 后量子密码学在 IoT 中的迁移

> **难度**：🟡 中级 | **领域**：密码学、嵌入式安全 | **阅读时间**：约 20 分钟

## 日常类比

想象你家的门锁是一把需要特定形状钥匙才能打开的机械锁。现在有人发明了一台"万能钥匙制造机"（量子计算机），只要给它足够时间，它能试出任何传统锁的钥匙形状。你需要换一种全新原理的锁——比如需要同时满足多个条件才能开启的组合锁，即使万能钥匙机也无法在合理时间内破解。

后量子密码学就是这把"新锁"。它不依赖传统的数学难题（大数分解、椭圆曲线离散对数），而是基于量子计算机也难以高效求解的数学结构，比如格（lattice）上的最短向量问题。对 IoT 设备来说，挑战在于：这把新锁不能太重（内存占用）、不能太慢（计算周期），否则小小的传感器节点根本"装不上"。

## 1. 量子计算对现有密码体系的威胁

### 1.1 Shor 算法的破坏力

1994 年 Peter Shor 提出的量子算法能在多项式时间内分解大整数和求解离散对数。这意味着：

| 算法 | 经典安全性 | 量子攻击后 |
|------|-----------|-----------|
| RSA-2048 | 112 bit | 完全破解 |
| ECC P-256 | 128 bit | 完全破解 |
| AES-128 | 128 bit | 降至 64 bit（Grover） |
| AES-256 | 256 bit | 降至 128 bit（Grover） |

对称密码受 Grover 算法影响较小（安全性减半），但非对称密码面临彻底崩溃。

### 1.2 "先存后破"攻击

即使大规模量子计算机尚未出现，攻击者可以现在截获加密通信数据，等量子计算机成熟后再解密。对于 IoT 设备（生命周期 10-20 年），这意味着今天部署的设备在退役前就可能面临数据泄露风险。

### 1.3 时间线评估

根据 2024 年 Global Risk Institute 报告，专家预测：
- 2030 年前出现密码学相关量子计算机的概率：~15%
- 2035 年前：~50%
- 考虑到 IoT 设备的长生命周期，迁移窗口已经很紧迫

## 2. NIST 后量子密码标准

### 2.1 标准化历程

NIST 从 2016 年启动 PQC 标准化竞赛，经过三轮筛选，2024 年 8 月正式发布首批标准：

| 标准编号 | 算法名称 | 用途 | 基础数学问题 |
|---------|---------|------|-------------|
| FIPS 203 | ML-KEM (CRYSTALS-Kyber) | 密钥封装 | Module-LWE |
| FIPS 204 | ML-DSA (CRYSTALS-Dilithium) | 数字签名 | Module-LWE/SIS |
| FIPS 205 | SLH-DSA (SPHINCS+) | 数字签名 | 哈希函数 |

### 2.2 CRYSTALS-Kyber（ML-KEM）

Kyber 是一种基于格的密钥封装机制（KEM），用于替代 ECDH 密钥交换：

```python
# 概念演示：Kyber KEM 流程（使用 liboqs Python 绑定）
import oqs

# 密钥生成（服务器端）
kem = oqs.KeyEncapsulation("Kyber768")
public_key = kem.generate_keypair()

# 封装（客户端用服务器公钥）
ciphertext, shared_secret_client = kem.encap_secret(public_key)

# 解封装（服务器用私钥）
shared_secret_server = kem.decap_secret(ciphertext)

assert shared_secret_client == shared_secret_server
print(f"共享密钥长度: {len(shared_secret_server)} bytes")
```

Kyber 参数集对比：

| 参数集 | 安全级别 | 公钥大小 | 密文大小 | 共享密钥 |
|--------|---------|---------|---------|---------|
| Kyber-512 | AES-128 等价 | 800 B | 768 B | 32 B |
| Kyber-768 | AES-192 等价 | 1,184 B | 1,088 B | 32 B |
| Kyber-1024 | AES-256 等价 | 1,568 B | 1,568 B | 32 B |

### 2.3 CRYSTALS-Dilithium（ML-DSA）

Dilithium 用于数字签名，替代 ECDSA/EdDSA：

| 参数集 | 安全级别 | 公钥 | 签名大小 | 签名速度(Cortex-M4) |
|--------|---------|------|---------|-------------------|
| Dilithium2 | 128 bit | 1,312 B | 2,420 B | ~1.5 ms |
| Dilithium3 | 192 bit | 1,952 B | 3,293 B | ~2.5 ms |
| Dilithium5 | 256 bit | 2,592 B | 4,595 B | ~4.0 ms |

### 2.4 SPHINCS+（SLH-DSA）

SPHINCS+ 是基于哈希的签名方案，不依赖格假设，提供"保守"安全性：
- 优点：安全性仅依赖哈希函数的抗碰撞性，数学假设最少
- 缺点：签名尺寸大（8-50 KB），签名速度慢
- 适用场景：固件签名验证（不频繁、对大小不敏感）

## 3. 格密码学基础

### 3.1 什么是格

格是 n 维空间中由基向量线性组合（整数系数）生成的离散点集。直观理解：二维平面上的网格纸，每个交叉点就是格点。

### 3.2 核心困难问题

**最短向量问题（SVP）**：给定一个格的基，找到最短的非零格向量。维度增大时，已知最优算法的时间复杂度呈指数增长。

**Learning With Errors（LWE）**：给定矩阵 A 和带噪声的乘积 b = As + e，恢复秘密向量 s。噪声 e 使问题从简单的线性代数变为困难问题。

```
# LWE 问题示意
# 公开: A (m×n 矩阵), b = A·s + e
# 秘密: s (n维向量)
# 噪声: e (小的随机向量)
# 
# 没有噪声 → 高斯消元即可解
# 有噪声 → 目前最优算法需要 2^(n/log n) 时间
```

### 3.3 Module-LWE

Kyber 和 Dilithium 使用的是 Module-LWE 变体，在环上操作多项式模块，兼顾安全性和效率：
- 比标准 LWE 更紧凑（密钥更小）
- 比 Ring-LWE 更灵活（安全性假设更弱）

## 4. 受限设备上的实现挑战

### 4.1 资源约束

典型 IoT 设备资源：

| 设备类别 | RAM | Flash | CPU | 代表芯片 |
|---------|-----|-------|-----|---------|
| Class 0 | ~10 KB | ~100 KB | 16 MHz | ATmega328P |
| Class 1 | ~50 KB | ~256 KB | 48 MHz | nRF52832 |
| Class 2 | ~256 KB | ~1 MB | 120 MHz | STM32L4 |
| Class 3 | ~512 KB | ~2 MB | 240 MHz | ESP32-S3 |

### 4.2 性能基准（ARM Cortex-M4 @ 168 MHz）

基于 pqm4 项目的实测数据（2024）：

| 操作 | Kyber-768 | ECC P-256 | 倍数 |
|------|-----------|-----------|------|
| 密钥生成 | 514K cycles | 2,890K cycles | 0.18x |
| 封装/加密 | 649K cycles | 7,651K cycles | 0.08x |
| 解封装/解密 | 614K cycles | 7,651K cycles | 0.08x |
| 公钥大小 | 1,184 B | 64 B | 18.5x |
| 密文大小 | 1,088 B | 64 B | 17x |

关键发现：Kyber 的计算速度实际上比 ECC 更快，但密钥和密文尺寸大幅增加。

### 4.3 内存优化策略

```c
// 流式 NTT（数论变换）实现 - 减少峰值内存
// 传统方式需要完整多项式在内存中
// 流式方式逐层计算，峰值内存减半

void ntt_streaming(int16_t poly[256]) {
    uint16_t len, start, j, k;
    int16_t t, zeta;
    
    k = 1;
    for (len = 128; len >= 2; len >>= 1) {
        for (start = 0; start < 256; start = j + len) {
            zeta = zetas[k++];
            for (j = start; j < start + len; j++) {
                t = montgomery_reduce((int32_t)zeta * poly[j + len]);
                poly[j + len] = poly[j] - t;
                poly[j] = poly[j] + t;
            }
        }
    }
}
```

### 4.4 栈内存使用对比

| 算法 | 密钥生成栈 | 签名栈 | 验证栈 |
|------|-----------|--------|--------|
| Dilithium2 | ~6 KB | ~15 KB | ~6 KB |
| Ed25519 | ~1 KB | ~2 KB | ~1 KB |
| SPHINCS+-128s | ~3 KB | ~8 KB | ~3 KB |

## 5. 混合经典+后量子方案

### 5.1 为什么需要混合方案

- PQC 算法相对年轻，可能存在未发现的攻击
- 混合方案确保"至少和经典方案一样安全"
- 平滑过渡，兼容现有基础设施

### 5.2 混合 TLS 握手

```
Client                              Server
  |                                    |
  |--- ClientHello ------------------>|
  |    supported_groups:              |
  |      x25519_kyber768              |
  |      x25519 (fallback)           |
  |                                    |
  |<-- ServerHello -------------------|
  |    selected: x25519_kyber768      |
  |                                    |
  |--- Key Share: X25519 + Kyber --->|
  |                                    |
  |<-- Key Share: X25519 + Kyber ----|
  |                                    |
  | shared_secret = HKDF(             |
  |   X25519_secret || Kyber_secret)  |
```

### 5.3 IoT 场景的混合策略

```python
# 混合密钥协商示例
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)
import oqs
import hashlib

def hybrid_key_exchange():
    # 经典部分：X25519
    classical_private = X25519PrivateKey.generate()
    classical_public = classical_private.public_key()
    
    # PQC 部分：Kyber-768
    kem = oqs.KeyEncapsulation("Kyber768")
    pqc_public = kem.generate_keypair()
    
    # 组合共享密钥
    # classical_shared = X25519 DH result
    # pqc_shared = Kyber decapsulation result
    # final_key = SHA-256(classical_shared || pqc_shared)
    
    return classical_public, pqc_public
```

## 6. 迁移路线图与工具链

### 6.1 分阶段迁移策略

| 阶段 | 时间 | 行动 | 目标 |
|------|------|------|------|
| 评估 | 2024-2025 | 密码资产清查、风险评估 | 了解暴露面 |
| 试点 | 2025-2026 | 混合方案部署、性能测试 | 验证可行性 |
| 迁移 | 2026-2028 | 逐步替换纯经典方案 | 降低风险 |
| 完成 | 2028-2030 | 移除经典回退 | 全面 PQ 安全 |

### 6.2 liboqs 库使用

Open Quantum Safe (OQS) 项目提供了 C 语言实现：

```c
#include <oqs/oqs.h>

// Kyber-768 密钥封装示例
int main() {
    OQS_KEM *kem = OQS_KEM_new(OQS_KEM_alg_kyber_768);
    
    uint8_t *public_key = malloc(kem->length_public_key);
    uint8_t *secret_key = malloc(kem->length_secret_key);
    uint8_t *ciphertext = malloc(kem->length_ciphertext);
    uint8_t *shared_secret_e = malloc(kem->length_shared_secret);
    uint8_t *shared_secret_d = malloc(kem->length_shared_secret);
    
    // 密钥生成
    OQS_KEM_keypair(kem, public_key, secret_key);
    
    // 封装（发送方）
    OQS_KEM_encaps(kem, ciphertext, shared_secret_e, public_key);
    
    // 解封装（接收方）
    OQS_KEM_decaps(kem, shared_secret_d, ciphertext, secret_key);
    
    // shared_secret_e == shared_secret_d
    
    free(public_key); free(secret_key);
    free(ciphertext); free(shared_secret_e); free(shared_secret_d);
    OQS_KEM_free(kem);
    return 0;
}
```

### 6.3 嵌入式移植注意事项

- 使用 `pqm4` 项目获取 ARM Cortex-M4 优化实现
- 关闭不需要的算法以减小代码体积
- 使用硬件随机数生成器（TRNG）而非软件 PRNG
- 考虑使用 DMA 加速大数组操作

## 7. 实践建议

### 7.1 初学者入门路径

1. 理解经典密码学基础（RSA、ECC、DH 密钥交换）
2. 学习格密码学数学基础（线性代数、多项式环）
3. 使用 liboqs Python 绑定做实验
4. 在 STM32 开发板上运行 pqm4 基准测试
5. 尝试实现混合 TLS 连接

### 7.2 具体调优建议

**内存受限场景（< 64 KB RAM）**：
- 优先选择 Kyber-512（公钥 800B，最小参数集）
- 使用流式 API 避免同时加载完整密钥对
- 考虑 SPHINCS+-128f 用于不频繁的签名验证

**带宽受限场景（LoRa/NB-IoT）**：
- 密钥预分发 + 定期轮换，减少在线密钥交换
- 使用 Kyber 而非 NTRU（密文更小）
- 签名场景考虑 Falcon（签名仅 666B，但实现复杂）

**能耗敏感场景**：
- Kyber 的 NTT 运算可利用 DSP 指令加速
- 批量验证签名以摊销初始化开销
- 在休眠前完成密钥生成，唤醒后直接使用

## 参考文献

1. NIST. "FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism Standard." August 2024.
2. NIST. "FIPS 204: Module-Lattice-Based Digital Signature Standard." August 2024.
3. Kannwischer, M. et al. "pqm4: Testing and Benchmarking NIST PQC on ARM Cortex-M4." IACR ePrint, 2024.
4. Stebila, D. & Mosca, M. "Post-Quantum Key Exchange for the Internet and the Open Quantum Safe Project." SAC 2016.
5. Schwabe, P. et al. "CRYSTALS-Kyber: Algorithm Specifications and Supporting Documentation." Version 3.02, 2024.
6. Avanzi, R. et al. "CRYSTALS-Dilithium: Algorithm Specifications." Version 3.1, 2024.
7. Hülsing, A. et al. "SPHINCS+: Submission to the NIST PQC Standardization." Round 3, 2022.
8. Global Risk Institute. "Quantum Threat Timeline Report." 2024.
9. Cloudflare. "Post-Quantum Cryptography in TLS: Real-World Deployment." Blog, 2024.
10. Müller, T. et al. "Post-Quantum Cryptography for Embedded Systems: A Performance Study." IEEE IoT Journal, 2024.
