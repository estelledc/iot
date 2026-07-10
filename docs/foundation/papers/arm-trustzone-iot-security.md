---
schema_version: '1.0'
id: arm-trustzone-iot-security
title: ARM TrustZone在IoT安全隔离中的应用
layer: 1
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# ARM TrustZone在IoT安全隔离中的应用
> **难度**：🔴 高级 | **领域**：可信执行环境 | **阅读时间**：约 22 分钟

## 引言

想象一栋办公楼,普通员工在大厅里自由活动,但机密文件室只有持证人员才能进入,而且文件室的门只能从外面刷卡打开——外面的人无法从里面反锁,但里面的人也无法把文件带出来。ARM TrustZone就是CPU内部的这扇"门"——它在同一颗芯片上划出安全世界和非安全世界,硬件强制隔离,非安全世界的代码无论如何都无法访问安全世界的资源。

对于资源不足以运行独立安全处理器的IoT设备,TrustZone-M提供了一种优雅的方案:不需要额外芯片,不需要双CPU,单颗Cortex-M处理器就能实现可信执行环境(TEE)。

## 1. TrustZone概念

### 1.1 什么是TrustZone

TrustZone是ARM提供的硬件安全扩展,在单个处理器核心内实现安全隔离:

- **硬件强制**:隔离由硬件实现,不依赖软件正确性
- **双世界架构**:安全世界(Secure World)和非安全世界(Non-Secure World)
- **同一CPU**:不需要额外的安全处理器
- **细粒度控制**:内存、外设、中断都可以独立配置安全属性

```
传统双芯片方案:
[应用MCU] <--SPI/I2C--> [安全MCU]
  成本高,通信延迟,PCB面积大

TrustZone方案:
[单一MCU with TrustZone]
  安全世界 + 非安全世界在同一芯片内
  成本低,零通信延迟,硬件强制隔离
```

### 1.2 TrustZone的发展

| 版本 | 架构 | 目标 | 代表核心 |
|------|------|------|---------|
| TrustZone-A | ARMv7-A/v8-A | 应用处理器 | Cortex-A7/A15/A53/A72 |
| TrustZone-M | ARMv8-M | 微控制器 | Cortex-M23/M33/M55 |

本文重点讨论TrustZone-M,因为它直接面向IoT MCU场景。

## 2. TrustZone-M架构

### 2.1 ARMv8-M架构

TrustZone-M引入的安全扩展:

```
ARMv8-M特权模型:

非安全世界:
  Thread mode (NS Priv)    -- 非安全特权
  Thread mode (NS Unpriv)  -- 非安全非特权
  Handler mode (NS Priv)   -- 非安全中断处理

安全世界:
  Thread mode (S Priv)     -- 安全特权
  Thread mode (S Unpriv)   -- 安全非特权
  Handler mode (S Priv)    -- 安全中断处理

状态切换:
  NS --> S: 通过SG指令进入(Non-Secure Callable)
  S --> NS: 通过BXNS/BLXNS指令返回
```

### 2.2 Cortex-M安全核心

| 核心 | 架构 | 特点 | 典型应用 |
|------|------|------|---------|
| Cortex-M23 | ARMv8-M Baseline | 最简单的TrustZone核心 | 简单IoT传感器 |
| Cortex-M33 | ARMv8-M Mainline | 性能与安全的平衡 | 主流IoT设备 |
| Cortex-M55 | ARMv8.1-M Mainline | 支持Helium向量扩展 | AIoT设备 |
| Cortex-M85 | ARMv8.1-M Mainline | 最高性能的TrustZone核心 | 高性能IoT网关 |

### 2.3 SAU与IDAU

TrustZone-M使用两级硬件进行安全属性判定:

```
安全属性判定:
+------------------+     +------------------+
|      IDAU        |     |      SAU         |
| (Implementation  |     | (Security        |
|  Defined         |     |  Attribution     |
|  Attribution     |     |  Unit)           |
|  Unit)           |     |                  |
|  固化在芯片中    |     |  软件可配置      |
|  厂商定义默认    |     |  运行时修改      |
|  安全属性        |     |  安全区域划分     |
+--------+---------+     +--------+---------+
         |                        |
         v                        v
    +----------------------------+
    |   最终安全属性判定          |
    |   IDAU标记为安全 + SAU标记  |
    |   为安全 = 安全区域         |
    |   否则 = 非安全区域         |
    +----------------------------+
```

**IDAU(Implementation Defined Attribution Unit)**:
- 芯片厂商在出厂时固化
- 定义默认的安全内存映射
- 例如:Flash的某些区域默认标记为安全

**SAU(Security Attribution Unit)**:
- 软件可配置(由安全世界代码配置)
- 可将IDAU标记为安全的区域设为非安全
- 可设置Non-Secure Callable(NSC)区域
- 典型配置:8个区域

```
SAU区域配置示例:
Region 0: 0x0C000000-0x0C0FFFFF, Secure    (安全Flash)
Region 1: 0x0C100000-0x0C1FFFFF, Non-Secure (应用Flash)
Region 2: 0x20000000-0x2000FFFF, Secure    (安全RAM)
Region 3: 0x20010000-0x2001FFFF, Non-Secure (应用RAM)
Region 4: 0x00200000-0x00200FFF, NSC       (NSC网关)
```

## 3. 安全世界与非安全世界

### 3.1 安全世界(Secure World)

安全世界运行可信代码,拥有对所有资源的完全访问权限:

```
安全世界包含:
+------------------------------------------+
| Trusted Firmware (TF-M)                  |
|  +------------+  +----------+            |
|  | Secure     |  | Crypto   |            |
|  | Boot      |  | Service  |            |
|  +------------+  +----------+            |
|  +------------+  +----------+            |
|  | Secure     |  | Attest-  |            |
|  | Storage    |  | ation    |            |
|  +------------+  +----------+            |
+------------------------------------------+
| 安全世界可访问:                            |
| - 所有安全内存                             |
| - 所有非安全内存(读/写)                    |
| - 安全外设                                 |
| - 非安全外设                               |
+------------------------------------------+
```

### 3.2 非安全世界(Non-Secure World)

非安全世界运行应用代码,访问受限:

```
非安全世界包含:
+------------------------------------------+
| Application Code                         |
|  +------------+  +----------+            |
|  | RTOS      |  | Network  |            |
|  |           |  | Stack    |            |
|  +------------+  +----------+            |
|  +------------+  +----------+            |
|  | Sensor    |  | Display  |            |
|  | Drivers   |  | Logic    |            |
|  +------------+  +----------+            |
+------------------------------------------+
| 非安全世界可访问:                          |
| - 仅非安全内存                             |
| - 仅非安全外设                             |
| - 通过NSC网关调用安全服务                   |
+------------------------------------------+
```

### 3.3 访问规则

| 访问 | 安全世界代码 | 非安全世界代码 |
|------|-------------|---------------|
| 安全内存 | 允许 | 拒绝(硬件阻止) |
| 非安全内存 | 允许 | 允许 |
| 安全外设 | 允许 | 拒绝 |
| 非安全外设 | 允许 | 允许 |
| NSC区域 | 允许(执行) | 允许(仅通过SG入口) |

硬件强制执行这些规则——非安全代码尝试访问安全资源时,CPU产生安全违规异常,由安全世界处理。

## 4. 内存分区

### 4.1 SAU区域类型

SAU将内存划分为三种类型:

```
1. Secure (S)
   - 只有安全世界可以访问
   - 存放:安全固件、密钥、安全数据

2. Non-Secure (NS)
   - 两个世界都可以访问
   - 存放:应用代码、普通数据

3. Non-Secure Callable (NSC)
   - 特殊区域:包含SG指令的安全代码
   - 非安全世界通过此区域进入安全世界
   - 是安全世界暴露给非安全世界的"门"
```

### 4.2 Flash分区实例

```
STM32L5 Flash布局 (512KB):
+--------------------+ 0x0C000000
| Secure Flash       |
| (TF-M + 安全服务)  | 256KB
|                    |
+--------------------+ 0x0C040000 (NSC区域入口)
| NSC Gateway        | ~4KB
| (Veneer Table)     |
+--------------------+ 0x0C041000
| Non-Secure Flash   |
| (应用代码)         | ~252KB
|                    |
+--------------------+ 0x0C080000
```

### 4.3 RAM分区实例

```
STM32L5 RAM布局 (256KB):
+--------------------+ 0x20000000
| Secure RAM         |
| (安全栈、安全数据)  | 64KB
+--------------------+ 0x20010000
| Non-Secure RAM     |
| (应用栈、应用数据)  | 192KB
+--------------------+ 0x20040000
```

## 5. Non-Secure Callable (NSC)网关

### 5.1 NSC机制

NSC是安全世界向非安全世界暴露服务的唯一合法通道:

```
调用流程:
[Non-Secure Code]          [NSC Gateway]           [Secure Code]
      |                          |                        |
      | 1. BLXNS target_addr     |                        |
      |------------------------->|                        |
      |                          | 2. 执行SG指令           |
      |                          |   (验证来自NSC区域)     |
      |                          |                        |
      |                          | 3. 跳转到安全函数       |
      |                          |----------------------->|
      |                          |                        | 4. 执行安全操作
      |                          |                        |    (签名/解密等)
      |                          |                        |
      |                          | 5. 返回结果             |
      |                          |<-----------------------|
      | 6. 返回到非安全代码       |                        |
      |<-------------------------|                        |
```

### 5.2 SG指令与Veneer Table

```
SG (Secure Gateway)指令:
  - 必须位于NSC区域
  - 非安全代码调用NSC区域时,CPU验证SG指令存在
  - 没有SG指令的NSC区域跳转将触发安全违规

Veneer Table (贴面函数表):
  - 编译器/链接器自动生成
  - 每个暴露给非安全世界的安全函数对应一个veneer
  - Veneer包含: SG指令 + 跳转到实际安全函数

Veneer示例:
  // 链接器生成的veneer代码
  veneer_secure_sign:
      SG              ; Secure Gateway指令
      B.W secure_sign ; 跳转到实际安全函数
```

### 5.3 安全函数声明(CMSE)

ARM编译器提供CMSE(Cortex-M Security Extensions)属性:

```c
// 安全世界的函数声明
// __attribute__((cmse_nonsecure_entry))
// 表示此函数可被非安全世界调用

#include <arm_cmse.h>

// 安全世界的签名函数
__attribute__((cmse_nonsecure_entry))
int32_t secure_sign(const uint8_t *hash, uint8_t *signature)
{
    // 1. 验证输入指针指向非安全内存
    cmse_check_pointed_object(hash, CMSE_NONSECURE);
    cmse_check_pointed_object(signature, CMSE_NONSECURE);

    // 2. 执行安全操作
    int32_t result = internal_ecdsa_sign(hash, signature);

    // 3. 返回结果(返回值会自动清除安全标记)
    return result;
}
```

## 6. TrustZone-M vs TrustZone-A

### 6.1 架构对比

| 维度 | TrustZone-M | TrustZone-A |
|------|-------------|-------------|
| 目标处理器 | Cortex-M23/M33/M55 | Cortex-A系列 |
| 安全OS | 不需要,裸机或RTOS | OP-TEE等安全OS |
| 上下文切换 | 简单(寄存器少) | 复杂(大量寄存器) |
| 切换延迟 | ~20个时钟周期 | 数百到数千周期 |
| 内存管理 | SAU(简单) | TZASC + SMMU |
| 确定性 | 确定(无cache影响) | 不确定(cache、MMU) |
| 典型应用 | IoT MCU | 手机、平板、服务器 |

### 6.2 选择建议

```
选择TrustZone-M的场景:
  - 资源受限: RAM < 1MB, Flash < 2MB
  - 实时性要求: 确定性响应时间
  - 低功耗: 电池供电设备
  - 简单安全服务: 密钥存储、签名、加密

选择TrustZone-A的场景:
  - 复杂安全OS需求: 多任务、文件系统
  - 丰富外设: GPU、多媒体
  - 大量安全应用: 支付、DRM、生物识别
  - 需要标准TEE: GlobalPlatform TEE规范
```

## 7. 安全服务示例

### 7.1 密码学操作

```c
// 安全世界提供的密码学服务
typedef struct {
    psa_key_handle_t key_handle;
} secure_crypto_context_t;

// 生成密钥对(安全世界内部)
__attribute__((cmse_nonsecure_entry))
psa_status_t secure_generate_key(psa_key_id_t *key_id)
{
    psa_key_attributes_t attrs = PSA_KEY_ATTRIBUTES_INIT;
    psa_set_key_type(&attrs, PSA_KEY_TYPE_ECC_KEY_PAIR(PSA_ECC_FAMILY_SECP_R1));
    psa_set_key_bits(&attrs, 256);
    psa_set_key_usage_flags(&attrs, PSA_KEY_USAGE_SIGN_HASH);
    psa_set_key_algorithm(&attrs, PSA_ALG_ECDSA(PSA_ALG_SHA_256));

    return psa_generate_key(&attrs, key_id);
}

// 使用安全世界密钥签名
__attribute__((cmse_nonsecure_entry))
psa_status_t secure_sign_hash(psa_key_id_t key_id,
                               const uint8_t *hash, size_t hash_len,
                               uint8_t *sig, size_t sig_size, size_t *sig_len)
{
    // 验证指针安全性
    if (cmse_check_address_range((void *)hash, hash_len, CMSE_NONSECURE) == NULL)
        return PSA_ERROR_INVALID_ARGUMENT;

    return psa_sign_hash(key_id, PSA_ALG_ECDSA(PSA_ALG_SHA_256),
                         hash, hash_len, sig, sig_size, sig_len);
}
```

### 7.2 安全存储

```c
// 安全世界的安全存储服务
// 密钥和敏感数据存储在安全Flash区域

#define SECURE_STORAGE_OFFSET  0x0C000000
#define SECURE_STORAGE_SIZE    (64 * 1024)

__attribute__((cmse_nonsecure_entry))
psa_status_t secure_store_data(uint32_t id,
                                const uint8_t *data, size_t data_len)
{
    // 仅允许非安全世界的指针
    if (cmse_check_address_range((void *)data, data_len,
                                  CMSE_NONSECURE) == NULL)
        return PSA_ERROR_INVALID_ARGUMENT;

    // 数据加密后存储在安全Flash
    return internal_secure_write(id, data, data_len);
}

__attribute__((cmse_nonsecure_entry))
psa_status_t secure_read_data(uint32_t id,
                               uint8_t *data, size_t data_size,
                               size_t *data_len)
{
    if (cmse_check_address_range((void *)data, data_size,
                                  CMSE_NONSECURE) == NULL)
        return PSA_ERROR_INVALID_ARGUMENT;

    // 从安全Flash读取并解密
    return internal_secure_read(id, data, data_size, data_len);
}
```

### 7.3 安全启动验证

```c
// 安全世界的启动验证
void secure_boot_verify(void)
{
    // 1. Boot ROM验证安全世界固件
    if (!verify_firmware_signature(SECURE_FIRMWARE_ADDR,
                                    SECURE_FIRMWARE_SIZE,
                                    SECURE_BOOT_KEY))
    {
        halt_system();  // 验证失败,停机
    }

    // 2. 安全世界验证非安全世界固件
    if (!verify_firmware_signature(NONSECURE_FIRMWARE_ADDR,
                                    NONSECURE_FIRMWARE_SIZE,
                                    APPLICATION_BOOT_KEY))
    {
        halt_system();
    }

    // 3. 初始化SAU
    sau_configure();

    // 4. 跳转到非安全世界
    jump_to_nonsecure(NONSECURE_RESET_ADDR);
}
```

## 8. 开发工作流

### 8.1 双项目结构

TrustZone-M项目由两个独立的子项目组成:

```
Project Structure:
my-device/
  +-- secure/                    # 安全世界项目
  |     +-- CMakeLists.txt
  |     +-- tfm/                 # TF-M配置
  |     +-- src/
  |     |     +-- secure_main.c
  |     |     +-- secure_crypto.c
  |     |     +-- secure_storage.c
  |     +-- linker/
  |           +-- secure.ld      # 安全世界链接脚本
  |
  +-- nonsecure/                # 非安全世界项目
  |     +-- CMakeLists.txt
  |     +-- src/
  |     |     +-- main.c
  |     |     +-- app_logic.c
  |     +-- linker/
  |           +-- nonsecure.ld  # 非安全世界链接脚本
  |
  +-- interface/                # 接口定义
        +-- secure_api.h         # 安全服务API声明
```

### 8.2 CMSE编译支持

```c
// secure_api.h - 安全世界暴露的接口
// 使用cmse_nonsecure_entry属性标记

#ifndef SECURE_API_H
#define SECURE_API_H

#include <stdint.h>
#include <psa/crypto.h>

// 生成密钥对
int32_t secure_generate_key(psa_key_id_t *key_id);

// 签名
int32_t secure_sign_hash(psa_key_id_t key_id,
                          const uint8_t *hash, size_t hash_len,
                          uint8_t *sig, size_t sig_size, size_t *sig_len);

// 加密
int32_t secure_encrypt(psa_key_id_t key_id,
                        const uint8_t *input, size_t input_len,
                        uint8_t *output, size_t output_size, size_t *output_len);

#endif
```

### 8.3 链接脚本分区

```c
/* secure.ld - 安全世界链接脚本 */
MEMORY
{
    FLASH_SECURE  (rx)  : ORIGIN = 0x0C000000, LENGTH = 256K
    FLASH_NSC     (rx)  : ORIGIN = 0x0C040000, LENGTH = 4K
    RAM_SECURE    (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
}

/* nonsecure.ld - 非安全世界链接脚本 */
MEMORY
{
    FLASH_NS      (rx)  : ORIGIN = 0x0C041000, LENGTH = 252K
    RAM_NS        (rwx) : ORIGIN = 0x20010000, LENGTH = 192K
}

/* 非安全世界需要知道安全函数的NSC入口地址 */
SECURE_API = LOAD_VENEER_ADDRESS;
```

## 9. TF-M (Trusted Firmware-M)

### 9.1 TF-M概述

TF-M是ARM提供的PSA认证参考实现:

```
TF-M架构:
+--------------------------------------------------+
| Non-Secure Application                           |
|  +----------+  +----------+  +----------+        |
|  | App Code |  | RTOS     |  | Network |        |
|  +----------+  +----------+  +----------+        |
+--------------------------------------------------+
         | NSC Gateway
+--------------------------------------------------+
| TF-M (Secure World)                              |
|  +----------+  +----------+  +----------+        |
|  | Crypto   |  | Secure   |  | Attest-  |        |
|  | Service  |  | Storage  |  | ation    |        |
|  +----------+  +----------+  +----------+        |
|  +----------+  +----------+                      |
|  | Audit    |  | Platform |                      |
|  | Log      |  | Service  |                      |
|  +----------+  +----------+                      |
|                                                  |
|  +------------------------------------------+    |
|  | PSA Crypto API (mbed TLS)                |    |
|  +------------------------------------------+    |
|  +------------------------------------------+    |
|  | Secure Partition Manager (SPM)           |    |
|  +------------------------------------------+    |
+--------------------------------------------------+
```

### 9.2 TF-M安全服务

| 服务 | 功能 | API |
|------|------|-----|
| Crypto Service | 密钥管理、签名、加密、哈希 | PSA Crypto API |
| Secure Storage | 安全数据持久化 | PSA ITS API |
| Internal Trusted Storage | 安全Flash访问 | PSA ITS API |
| Attestation | 设备身份证明 | PSA Attestation API |
| Audit Log | 安全审计日志 | PSA Audit API |
| Platform Service | 系统信息、固件版本 | TF-M Platform API |

### 9.3 TF-M集成步骤

```
1. 选择目标硬件(如STM32L5)
2. 配置TF-M:
   - 选择需要的安全服务
   - 配置密钥和证书
   - 设置SAU区域
3. 编译TF-M安全固件
4. 编译非安全应用
5. 合并两个固件镜像
6. 烧录到设备
7. 通过NSC接口调用安全服务
```

## 10. 实战案例: STM32L5 TrustZone安全密钥存储

### 10.1 硬件平台

```
STM32L5特性:
- Cortex-M33 @ 110MHz
- 512KB Flash, 256KB RAM
- TrustZone-M支持
- 内置AES加速器
- 内置PKA(公钥加速器)
- RNG随机数发生器
- SAU: 8个可配置区域
```

### 10.2 系统架构

```
+--------------------------------------------------+
| Non-Secure World                                 |
|  +----------------+  +------------------------+  |
|  | FreeRTOS       |  | MQTT Client            |  |
|  | Task: Sensor   |  | (mbedTLS with PSA)     |  |
|  | Task: Display  |  |                        |  |
|  +----------------+  +------------------------+  |
|           |                    |                   |
|           | secure_api.h      | PSA Crypto API    |
+--------------------------------------------------+
         | NSC Gateway
+--------------------------------------------------+
| Secure World (TF-M)                              |
|  +----------------+  +------------------------+  |
|  | Key Management |  | Crypto Service         |  |
|  | (ECC Key Pairs)|  | (ECDSA/AES/SHA)        |  |
|  +----------------+  +------------------------+  |
|  +----------------+  +------------------------+  |
|  | Secure Storage |  | Attestation            |  |
|  | (Encrypted)    |  | (Device Certificate)   |  |
|  +----------------+  +------------------------+  |
+--------------------------------------------------+
```

### 10.3 非安全世界调用示例

```c
// 非安全世界的应用代码
#include "secure_api.h"
#include "psa/crypto.h"

void mqtt_publish_sensor_data(void)
{
    uint8_t sensor_data[64];
    uint8_t signature[64];
    size_t sig_len;

    // 1. 读取传感器数据
    read_sensor(sensor_data, sizeof(sensor_data));

    // 2. 计算哈希
    uint8_t hash[32];
    psa_hash_operation_t op = PSA_HASH_OPERATION_INIT;
    psa_hash_setup(&op, PSA_ALG_SHA_256);
    psa_hash_update(&op, sensor_data, sizeof(sensor_data));
    psa_hash_finish(&op, hash, sizeof(hash), NULL);

    // 3. 调用安全世界签名(密钥不暴露给非安全世界)
    psa_key_id_t key_id = SENSOR_SIGNING_KEY_ID;
    secure_sign_hash(key_id, hash, sizeof(hash),
                     signature, sizeof(signature), &sig_len);

    // 4. 发布签名数据
    mqtt_publish("sensor/data", sensor_data, sizeof(sensor_data),
                 signature, sig_len);
}
```

## 11. PSA认证

### 11.1 PSA安全框架

PSA(Platform Security Architecture)是ARM定义的IoT安全框架:

```
PSA层次:
  +-------------------------------------------+
  |  PSA Certified Level 3                    |
  |  (完整安全实现验证)                         |
  +-------------------------------------------+
  |  PSA Certified Level 2                    |
  |  (安全实现评估)                             |
  +-------------------------------------------+
  |  PSA Certified Level 1                    |
  |  (架构合规性检查)                           |
  +-------------------------------------------+
  |  PSA Root of Trust                        |
  |  (硬件信任根)                               |
  +-------------------------------------------+
```

### 11.2 认证等级

| 等级 | 要求 | 评估深度 | 适用场景 |
|------|------|---------|---------|
| Level 1 | 架构合规,自评估问卷 | 基础 | 消费级IoT |
| Level 2 | 独立实验室评估安全实现 | 中等 | 商业/工业IoT |
| Level 3 | 全面渗透测试和代码审计 | 深入 | 关键基础设施 |

### 11.3 PSA威胁模型

```
PSA定义的典型威胁:

T1: 物理攻击
  - 调试接口访问(JTAG/SWD)
  - Flash读取
  - 侧信道攻击

T2: 软件攻击
  - 恶意固件注入
  - 运行时代码注入
  - 特权提升

T3: 网络攻击
  - 中间人攻击
  - 重放攻击
  - 设备冒充

TrustZone-M应对:
  T1: SAU隔离 + 调试访问控制
  T2: 安全启动 + 内存隔离
  T3: 密钥安全存储 + 安全TLS
```

## 12. 限制与开销

### 12.1 上下文切换延迟

```
TrustZone-M上下文切换开销:

NS -> S 调用:
  1. 压缩非安全上下文(仅必要寄存器)
  2. 执行SG指令 + 分支
  3. 堆栈切换(NS -> S堆栈)
  4. 进入安全函数
  估计: ~20个时钟周期 @ 110MHz = ~180ns

S -> NS 返回:
  1. 安全函数返回
  2. 堆栈切换(S -> NS堆栈)
  3. 执行BXNS指令
  估计: ~15个时钟周期 = ~136ns

对TLS握手的影响:
  握手约10-20次签名操作
  20次 x 180ns = 3.6us (可忽略)
```

### 12.2 内存开销

```
TrustZone-M内存开销:

Flash:
  - 安全固件(TF-M最小配置): ~80-120KB
  - NSC Veneer Table: ~2-4KB
  - 总计额外: ~85-125KB

RAM:
  - 安全世界栈和堆: ~4-8KB
  - 安全服务数据: ~4-16KB
  - 总计额外: ~8-24KB

对于STM32L5 (512KB Flash / 256KB RAM):
  Flash开销: ~17-24%
  RAM开销: ~3-9%
```

### 12.3 开发复杂度

```
增加的开发工作量:

1. 安全/非安全项目分离
   - 两套CMake/Makefile
   - 两套链接脚本
   - 交叉引用管理

2. 接口定义
   - NSC网关函数声明
   - 参数安全验证(cmse_check_*)
   - 数据拷贝(避免指针泄露)

3. 调试挑战
   - 调试器需要配置安全/非安全视图
   - 断点可能跨越安全边界
   - 日志系统需要区分安全级别

4. 测试
   - 安全服务需要独立测试
   - NSC接口需要边界测试
   - 安全违规场景测试
```

### 12.4 适用性评估

```
适合使用TrustZone-M的场景:
  + 需要密钥安全存储
  + 需要合规认证(PSA Level 2+)
  + 设备部署在无人看守环境
  + 需要安全OTA
  + 已选择Cortex-M23/M33/M55

不适合TrustZone-M的场景:
  - 简单传感器,无安全需求
  - 已有独立安全芯片(SE/HSM)
  - 资源极度受限(Flash < 256KB)
  - 安全需求仅为TLS(软件库即可)
```

## 总结

ARM TrustZone-M为IoT MCU提供了硬件强制的安全隔离,核心要点:

1. **硬件隔离**:SAU/IDAU硬件强制,非安全代码无法访问安全资源,这是根本保障
2. **单芯片TEE**:不需要额外安全处理器,降低BOM成本和PCB复杂度
3. **NSC网关**:安全服务通过Non-Secure Callable区域受控暴露,接口清晰可控
4. **TF-M生态**:PSA认证的参考实现,开箱即用的安全服务
5. **PSA认证**:从Level 1到Level 3,适配不同安全需求
6. **权衡取舍**:额外的Flash/RAM开销、开发复杂度增加,换取硬件级安全隔离

对于选择Cortex-M33/M55的IoT项目,TrustZone-M是"免费"的安全能力——硬件已经支持,关键在于是否启用并正确使用。结合TF-M和PSA认证,可以快速构建符合行业标准的设备安全架构。

## 参考文献

1. ARM, "ARMv8-M Architecture Reference Manual", DDI 0553A, 2016
2. ARM, "TrustZone Technology for the ARMv8-M Architecture", ARM DEN0024A, 2017
3. Trusted Firmware Project, "TF-M Documentation", trustedfirmware.org, 2022
4. ARM, "Platform Security Architecture (PSA) Certified Level 2 Requirements", 2021
5. STMicroelectronics, "STM32L5 TrustZone Development Guide", AN5393, 2021
