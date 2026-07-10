---
schema_version: '1.0'
id: secure-boot-root-of-trust
title: 安全启动链与 Root of Trust
layer: 6
content_type: UNKNOWN
difficulty: intermediate
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 安全启动链与 Root of Trust

> **难度**：🟡 中级 | **领域**：嵌入式安全、固件保护 | **阅读时间**：约 18 分钟

## 日常类比

想象你每天早上起床后的"信任链"：你信任闹钟的时间是对的（因为它连着网络时间服务器），你信任手机推送的天气预报（因为你认识那个 App），你信任早餐牛奶没过期（因为你检查了日期标签）。每一步的信任都建立在前一步的验证之上。

安全启动链的原理完全一样：设备上电后，最先运行的一小段代码（固化在芯片 ROM 中，无法篡改）验证下一阶段代码的签名，通过后才把控制权交出去。就像一个严格的门卫系统——第一个门卫是焊死在墙里的（硬件信任根），他验证第二个门卫的工牌，第二个门卫再验证第三个……任何一环验证失败，整个启动过程就停止。

## 1. 启动链架构

### 1.1 典型启动阶段

```
┌─────────────────────────────────────────────────────┐
│  硬件上电                                            │
├─────────────────────────────────────────────────────┤
│  Stage 0: Boot ROM (不可变，芯片出厂固化)             │
│    → 验证 Stage 1 签名                              │
├─────────────────────────────────────────────────────┤
│  Stage 1: First-Stage Bootloader (SPL/BL2)          │
│    → 初始化 DRAM，验证 Stage 2 签名                  │
├─────────────────────────────────────────────────────┤
│  Stage 2: Second-Stage Bootloader (U-Boot/BL33)     │
│    → 加载内核，验证内核+设备树签名                    │
├─────────────────────────────────────────────────────┤
│  Stage 3: OS Kernel                                 │
│    → 验证文件系统完整性 (dm-verity)                   │
├─────────────────────────────────────────────────────┤
│  Stage 4: Application                               │
│    → 运行时完整性检查                                │
└─────────────────────────────────────────────────────┘
```

### 1.2 信任传递原则

- **信任根（Root of Trust）**：不可变的硬件/固件，是整条链的起点
- **信任链（Chain of Trust）**：每一阶段验证下一阶段后才移交控制权
- **最小化原则**：信任根代码越小越好（减少攻击面）

## 2. 硬件信任根

### 2.1 信任根的类型

| 类型 | 实现方式 | 代表产品 | 安全级别 |
|------|---------|---------|---------|
| 片上 ROM | 芯片内置不可变代码 | STM32 OTP | 基础 |
| 安全元件 | 独立安全芯片 | ATECC608B | 高 |
| TPM | 可信平台模块 | Infineon SLB9670 | 高 |
| TEE | 可信执行环境 | ARM TrustZone | 中高 |
| PUF | 物理不可克隆函数 | Intrinsic ID | 高 |

### 2.2 TPM 2.0 在 IoT 中的应用

TPM（Trusted Platform Module）提供：
- 安全密钥存储（密钥永不离开 TPM）
- 平台配置寄存器（PCR）记录启动度量
- 远程证明（Remote Attestation）

```c
// TPM 2.0 PCR 扩展操作（概念代码）
// PCR_new = SHA-256(PCR_old || measurement)

#include <tss2/tss2_esys.h>

int extend_pcr(ESYS_CONTEXT *ctx, uint32_t pcr_index, 
               uint8_t *measurement, size_t meas_len) {
    TPML_DIGEST_VALUES digests;
    digests.count = 1;
    digests.digests[0].hashAlg = TPM2_ALG_SHA256;
    
    // 计算度量值的 SHA-256
    SHA256(measurement, meas_len, 
           digests.digests[0].digest.sha256);
    
    // 扩展 PCR
    TSS2_RC rc = Esys_PCR_Extend(ctx, pcr_index,
        ESYS_TR_PASSWORD, ESYS_TR_NONE, ESYS_TR_NONE,
        &digests);
    
    return (rc == TSS2_RC_SUCCESS) ? 0 : -1;
}
```

### 2.3 安全元件对比

| 特性 | ATECC608B | OPTIGA Trust M | SE050 |
|------|-----------|----------------|-------|
| 厂商 | Microchip | Infineon | NXP |
| 接口 | I2C | I2C | I2C/SPI |
| 密钥存储 | 16 slots | 灵活对象存储 | 大容量 |
| 支持算法 | ECC P-256, SHA-256 | ECC, RSA, AES | ECC, RSA, AES, ED25519 |
| 认证 | CC EAL5+ | CC EAL6+ | CC EAL6+ |
| 价格(1K量) | ~$0.60 | ~$1.20 | ~$2.50 |
| PQC 支持 | 无 | 路线图中 | 部分(SE052) |
| 功耗(活跃) | 4 mA | 6 mA | 8 mA |

## 3. Verified Boot vs Measured Boot

### 3.1 Verified Boot（验证启动）

每阶段在加载下一阶段前验证其数字签名。验证失败则拒绝启动。

特点：
- 主动阻止未授权代码执行
- 需要预置公钥/证书
- Android Verified Boot (AVB) 是典型实现

### 3.2 Measured Boot（度量启动）

每阶段计算下一阶段的哈希值并记录到 TPM PCR 中，但不阻止启动。事后通过远程证明判断设备状态。

特点：
- 不阻止启动，只记录
- 适合需要高可用性的场景
- 配合远程证明实现"信任但验证"

### 3.3 对比选择

| 维度 | Verified Boot | Measured Boot |
|------|--------------|---------------|
| 安全保证 | 强（阻止执行） | 弱（仅检测） |
| 可用性 | 可能无法启动 | 始终可启动 |
| 复杂度 | 中等 | 高（需要证明基础设施） |
| IoT 适用性 | 推荐（大多数场景） | 适合关键基础设施 |
| 典型实现 | STM32 SBSFU, MCUboot | TPM + IMA |

## 4. STM32 安全启动实现

### 4.1 STM32 SBSFU 架构

STM32 Secure Boot and Secure Firmware Update (SBSFU) 是 ST 官方的安全启动参考实现：

```
Flash 布局:
┌──────────────────────┐ 0x0800_0000
│  SBSFU (Secure Boot) │ 32 KB
│  - 验证签名           │
│  - 解密固件           │
├──────────────────────┤ 0x0800_8000
│  Active Slot         │ 
│  (当前运行固件)       │ 256 KB
├──────────────────────┤ 0x0804_8000
│  Download Slot       │
│  (新固件暂存区)       │ 256 KB
├──────────────────────┤ 0x0808_8000
│  Swap Area           │ 16 KB
└──────────────────────┘
```

### 4.2 配置安全启动

```c
// STM32 安全启动配置（se_crypto_config.h）
#define SECBOOT_CRYPTO_SCHEME    SECBOOT_ECCDSA_WITH_AES128_CBC_SHA256

// 密钥配置
// OEM 根公钥（用于验证固件签名）
const uint8_t oem_pub_key[] = {
    // ECC P-256 公钥 (64 bytes: X || Y)
    0x04, 0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F, 0x70,
    // ... 省略完整密钥
};

// 启用写保护（防止 SBSFU 代码被篡改）
#define SFU_WRP_PROTECT_ENABLE   1
// 启用 PCROP（防止密钥被读取）
#define SFU_PCROP_PROTECT_ENABLE 1
// 启用 RDP Level 2（永久锁定调试接口）
#define SFU_RDP_PROTECT_ENABLE   1
```

### 4.3 启动验证流程

```c
// 简化的安全启动验证逻辑
typedef enum {
    BOOT_OK = 0,
    BOOT_SIGNATURE_INVALID,
    BOOT_VERSION_ROLLBACK,
    BOOT_INTEGRITY_FAIL
} boot_status_t;

boot_status_t secure_boot_verify(void) {
    firmware_header_t *header = (firmware_header_t *)ACTIVE_SLOT_ADDR;
    
    // 1. 检查魔数和头部完整性
    if (header->magic != FW_MAGIC_NUMBER) {
        return BOOT_INTEGRITY_FAIL;
    }
    
    // 2. 防回滚检查
    uint32_t current_version = read_anti_rollback_counter();
    if (header->version < current_version) {
        return BOOT_VERSION_ROLLBACK;
    }
    
    // 3. ECDSA 签名验证
    if (!ecdsa_verify(oem_pub_key, 
                      header->signature,
                      (uint8_t*)(ACTIVE_SLOT_ADDR + HEADER_SIZE),
                      header->fw_size)) {
        return BOOT_SIGNATURE_INVALID;
    }
    
    // 4. 更新防回滚计数器
    if (header->version > current_version) {
        write_anti_rollback_counter(header->version);
    }
    
    return BOOT_OK;
}
```

## 5. 证书链与密钥管理

### 5.1 多级证书架构

```
Root CA (离线存储，永不联网)
  │
  ├── Intermediate CA (签发设备证书)
  │     │
  │     ├── Device Cert (设备身份)
  │     └── Firmware Signing Cert (固件签名)
  │
  └── Recovery CA (紧急恢复用)
```

### 5.2 密钥轮换策略

| 密钥类型 | 存储位置 | 轮换周期 | 泄露影响 |
|---------|---------|---------|---------|
| Root Key | HSM/离线 | 永不轮换 | 灾难性 |
| Signing Key | 构建服务器 HSM | 1-2 年 | 高 |
| Device Key | 安全元件 | 设备生命周期 | 单设备 |
| Session Key | RAM | 每次连接 | 极低 |

### 5.3 密钥注入流程

```python
# 工厂密钥注入脚本示例
import serial
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

def inject_device_key(serial_port, device_id):
    # 1. 生成设备唯一密钥对
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    
    # 2. 用中间 CA 签发设备证书
    cert = sign_device_certificate(public_key, device_id)
    
    # 3. 通过安全通道注入私钥到安全元件
    with serial.Serial(serial_port, 115200) as ser:
        ser.write(b'KEY_INJECT\n')
        ser.write(private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
        # 4. 验证注入成功
        response = ser.readline()
        assert response == b'KEY_OK\n'
    
    # 5. 锁定安全元件（禁止后续密钥导出）
    lock_secure_element(serial_port)
    
    return cert
```

## 6. 防回滚保护

### 6.1 为什么需要防回滚

攻击者可能将设备固件降级到已知存在漏洞的旧版本。即使新版本修复了漏洞，如果能回滚，修复就毫无意义。

### 6.2 实现机制

**OTP Fuse 计数器**：
- 芯片内置一次性可编程熔丝
- 每次升级烧断一个 fuse，物理不可逆
- 缺点：fuse 数量有限（通常 32-64 个）

**安全存储计数器**：
- 存储在安全元件或 RPMB（Replay Protected Memory Block）中
- 可以支持更多版本号
- 需要硬件支持防篡改

```c
// 防回滚计数器实现
#define ANTI_ROLLBACK_OTP_BASE  0x1FFF7800
#define MAX_ROLLBACK_SLOTS      32

uint32_t read_anti_rollback_counter(void) {
    uint32_t count = 0;
    volatile uint32_t *otp = (uint32_t *)ANTI_ROLLBACK_OTP_BASE;
    
    for (int i = 0; i < MAX_ROLLBACK_SLOTS; i++) {
        if (otp[i] == 0xFFFFFFFF) break;  // 未烧写
        count++;
    }
    return count;
}

int write_anti_rollback_counter(uint32_t new_version) {
    uint32_t current = read_anti_rollback_counter();
    if (new_version <= current) return -1;
    
    // 烧写 OTP fuse（不可逆操作）
    volatile uint32_t *otp = (uint32_t *)ANTI_ROLLBACK_OTP_BASE;
    for (uint32_t i = current; i < new_version; i++) {
        otp[i] = 0x00000000;  // 烧断 fuse
    }
    return 0;
}
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 从 STM32CubeIDE 的 SBSFU 示例项目开始，理解启动流程
2. 使用 ATECC608B 开发板练习安全元件操作
3. 学习 MCUboot 源码（开源，文档完善）
4. 在开发板上实现完整的签名验证流程
5. 尝试攻击自己的实现（调试接口、故障注入）

### 7.2 具体调优建议

**选择安全元件**：
- 成本敏感：ATECC608B（$0.60，功能够用）
- 需要 RSA/多算法：OPTIGA Trust M（灵活性好）
- 高安全需求：SE050（EAL6+，支持更多算法）

**启动时间优化**：
- 使用 SHA-256 硬件加速器（STM32 HASH 外设）
- 仅验证固件头部 + 关键段，延迟验证非关键段
- 缓存验证结果（配合防篡改存储）

**生产部署**：
- 必须在安全环境中注入密钥（屏蔽房/HSM）
- RDP Level 2 一旦设置不可逆转，测试阶段用 Level 1
- 保留紧急恢复通道（物理按键 + Recovery 分区）

## 参考文献

1. ARM. "Platform Security Architecture (PSA) Certified." 2024.
2. STMicroelectronics. "UM2262: STM32 Secure Boot and Secure Firmware Update." Rev 5, 2024.
3. Trusted Computing Group. "TPM 2.0 Library Specification." 2024.
4. MCUboot Project. "MCUboot: Secure Boot for 32-bit Microcontrollers." Documentation, 2024.
5. Microchip. "ATECC608B CryptoAuthentication Device Datasheet." 2023.
6. Infineon. "OPTIGA Trust M Solution Reference Manual." 2024.
7. NXP. "EdgeLock SE050: Plug & Trust Secure Element." Application Note, 2024.
8. Google. "Android Verified Boot 2.0." AOSP Documentation, 2024.
9. Eldefrawy, K. et al. "SMART: Secure and Minimal Architecture for Establishing Dynamic Root of Trust." NDSS 2012.
10. Pinto, S. & Santos, N. "Demystifying ARM TrustZone: A Comprehensive Survey." ACM Computing Surveys, 2019.
