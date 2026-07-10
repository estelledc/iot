---
schema_version: '1.0'
id: mcu-boot-process-secure-boot
title: MCU启动流程与安全启动链实现
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# MCU启动流程与安全启动链实现

> **难度**：🟡 中级 | **领域**：嵌入式安全启动 | **阅读时间**：约 20 分钟

## 引言

想象你每天早上起床的过程:闹钟响(复位信号)->睁开眼确认是自己家(Reset Vector)->穿衣服(堆栈初始化)->洗漱(SystemInit)->出门上班(main)。MCU的启动过程与此类似,每一步都有严格顺序,任何一步被篡改,后面的行为就不可信了。

在物联网时代,设备部署在无人值守的环境中,攻击者可以物理接触设备、刷入恶意固件。安全启动链(Secure Boot Chain)就是确保MCU从上电第一条指令开始,每一步都经过验证,建立起从硬件根信任到应用程序的完整信任链。

本文将系统梳理MCU启动流程的每个阶段,深入分析安全启动链的设计与实现,并对比主流平台方案。

## 1. MCU启动流程全景

### 1.1 从上电到main()的完整路径

```
上电/复位
  |
  v
CPU从向量表读取初始SP (0x00000000)
  |
  v
CPU从向量表读取Reset_Handler地址 (0x00000004)
  |
  v
Reset_Handler执行:
  |- 将.data段从Flash拷贝到RAM
  |- 将.bss段清零
  |- 调用SystemInit()  -- 配置时钟、FPU等
  |- 调用__libc_init_array()  -- C++构造函数
  |- 调用main()
  |
  v
应用程序运行
```

向量表(Vector Table)是MCU启动的核心数据结构。Cortex-M系列默认从地址0x0读取向量表,前两个字分别为初始栈指针和Reset_Handler入口地址。CPU复位后自动从0x00000000加载SP,从0x00000004加载PC,这是硬件自动完成的。

```c
// 启动文件中的向量表定义 (GCC语法)
__vector_table:
    .word   _estack           /* 初始栈指针,指向RAM末尾 */
    .word   Reset_Handler      /* 复位向量,第一条执行的代码 */
    .word   NMI_Handler
    .word   HardFault_Handler
    /* ... 更多异常向量 ... */
```

### 1.3 startup文件解剖

以ARM CMSIS标准的startup文件为例:

```assembly
/* startup_stm32f4xx.s - 核心结构 */
Reset_Handler:
    ldr   sp, =_estack       /* 1. 设置栈指针 */

    /* 2. 拷贝.data段从Flash到RAM */
    ldr   r0, =_sdata
    ldr   r1, =_edata
    ldr   r2, =_sidata
copy_data_loop:
    cmp   r0, r1
    bge   copy_data_done
    ldr   r3, [r2], #4
    str   r3, [r0], #4
    b     copy_data_loop
copy_data_done:

    /* 3. 清零.bss段 */
    /* 4. bl SystemInit */
    /* 5. bl __libc_init_array */
    /* 6. bl main */
    b     .   /* main不应返回,若返回则死循环 */
```

启动文件的核心职责:建立C语言运行环境,让后续代码能在正确的内存布局下运行。SystemInit在C运行时环境完全建立之前执行,因此不能使用全局变量(未初始化)、不能调用标准库函数。

## 2. 向量表重定位与Bootloader

### 2.1 VTOR寄存器与向量表搬移

Cortex-M3/M4/M7的VTOR(Vector Table Offset Register)允许运行时重定位向量表,新地址需256字节对齐:

```c
SCB->VTOR = 0x08008000;  /* 偏移32KB,跳过bootloader区域 */
```

### 2.2 双Bank与A/B升级

| 特性 | 双Bank (Dual-Bank) | A/B分区 |
|------|---------------------|----------|
| Flash布局 | 两个等大物理Bank,硬件切换 | 逻辑分区,slot A + slot B |
| 升级方式 | 写入备用Bank,原子切换 | 写入非活动slot,标记交换 |
| 回滚机制 | 切回原Bank即可 | 需要额外标记 |
| 典型芯片 | STM32F7/H7(硬件双Bank) | MCUboot标准设计 |
| 空间利用率 | 50%(始终有半个Bank空闲) | 灵活,可调比例 |

A/B分区状态管理: INVALID(0x00) -> TESTING(0x01,首次启动新固件) -> CONFIRMED(0x02,运行正常确认)。若未确认(看门狗复位),bootloader自动回滚到旧固件。

## 3. 安全启动链原理

### 3.1 信任根(Root of Trust)

安全启动的核心:信任必须有一个不可篡改的起点,然后逐级传递。

```
硬件信任根 (不可篡改)
    |
    v
Bootloader验证 (签名校验)
    |
    v
应用程序验证 (签名校验)
    |
    v
运行时完整性 (可选)
```

| 信任根类型 | 实现方式 | 安全等级 | 典型应用 |
|-----------|---------|---------|---------|
| ROM中的公钥 | 出厂时烧录到只读存储器 | 高 | STM32 SBSFU |
| OTP/eFuse中的哈希 | 一次性可编程存储器 | 高 | ESP32 Secure Boot V2 |
| 外部安全元件 | 独立SE芯片 | 最高 | ATECC608B |

### 3.2 签名验证流程

```c
/**
 * 签名阶段(离线):
 *   1. 计算固件hash: H = SHA256(firmware)
 *   2. 用私钥签名: Sig = ECDSA-256(private_key, H)
 *   3. 将签名附加到固件尾部
 *
 * 验证阶段(设备端):
 *   1. 计算固件哈希: H' = SHA256(firmware)
 *   2. 用公钥验证签名: ECDSA_Verify(public_key, Sig, H')
 *   3. 验证通过则信任该固件
 */
int verify_firmware_signature(const uint8_t *fw, size_t fw_len,
                               const uint8_t *sig, size_t sig_len,
                               const uint8_t *pub_key)
{
    uint8_t hash[32];
    int ret;

    ret = mbedtls_sha256(fw, fw_len, hash, 0);  /* SHA-256 */
    if (ret != 0) return VERIFY_ERR_HASH;

    ret = ecdsa_verify(pub_key, hash, 32, sig, sig_len);
    if (ret != 0) return VERIFY_ERR_SIG;

    return VERIFY_OK;
}
```

### 3.3 签名算法对比

| 算法 | 密钥长度 | 签名长度 | 验证速度 | MCU适用性 |
|------|---------|---------|---------|-----------|
| RSA-2048 | 256字节 | 256字节 | 慢 | 性能好的MCU |
| ECDSA P-256 | 32字节 | 64字节 | 中等 | 推荐,平衡选择 |
| Ed25519 | 32字节 | 64字节 | 快 | 最佳(若库支持) |

ECDSA P-256是当前MCU安全启动的主流选择:签名短(64字节)、验证速度可接受、生态成熟。

## 4. 硬件安全机制

### 4.1 OTP与eFuse

OTP(One-Time Programmable)和eFuse是存储信任根的硬件基础:

```c
/**
 * OTP/eFuse在安全启动中的用途:
 * 1. 存储公钥哈希(而非公钥本身,节省空间)
 * 2. 存储安全配置位(Secure Boot使能、JTAG禁用、Flash读保护)
 * 3. 存储反回滚计数器(单调递增,只能从N写到N+1)
 */

/* STM32H7的OTP写入示例 */
#define OTP_AREA_BASE    0x1FF07000UL
void write_otp_key_hash(const uint8_t *hash)
{
    /* 注意:OTP只能写一次!生产环境需极其谨慎 */
    volatile uint32_t *otp = (volatile uint32_t *)OTP_AREA_BASE;
    for (int i = 0; i < 8; i++) {  /* 32字节 = 8个word */
        otp[i] = ((const uint32_t *)hash)[i];
    }
    *(volatile uint32_t *)0x1FF07A00UL = 0x1;  /* 锁定OTP */
}
```

### 4.2 安全密钥存储层次

```
应用层密钥 -> (由设备唯一密钥加密) -> 设备唯一密钥 -> (硬件派生自) -> PUF/出厂注入密钥 -> (存储在) -> HSM/安全区域
```

| MCU系列 | 密钥存储方式 | 访问控制 | 备注 |
|---------|-------------|---------|------|
| STM32L4/U5 | SAU + GTZC | 非安全区无法访问安全区密钥 | TrustZone-M |
| ESP32-S2/S3 | eFuse Key Block | 可配置读/写保护 | 支持密钥编译 |
| NXP LPC55S6x | PUF + KHXS | 密钥不可导出 | SRAM PUF |

## 5. 主流平台安全启动实现

### 5.1 STM32 SBSFU

STM32 SBSFU(Secure Boot and Secure Firmware Update)是ST官方的安全启动参考实现:

```
 +-------------------+
 |  Application (NS) |  非安全区
 +-------------------+
 |  Secure App  (S)  |  安全区
 +-------------------+
 |  SBSFU Bootloader |  安全启动 + 固件更新
 +-------------------+
 |  信任根:          |
 |  - OTP中的公钥哈希 |
 |  - Flash RDP Level |
 +-------------------+
```

```c
/* SBSFU启动验证简化流程 */
int SBSFU_boot_verify(void)
{
    uint32_t app_entry = *(volatile uint32_t *)(APP_ADDRESS + 4);
    if ((app_entry & 0xFFF) != 0) return BOOT_FAIL;  /* 未对齐 */

    firmware_header_t *hdr = (firmware_header_t *)APP_ADDRESS;

    /* 验证签名(使用OTP中公钥哈希对应的公钥) */
    if (verify_signature(hdr->signature, hdr->fw_len,
                          APP_ADDRESS + sizeof(*hdr)) != 0)
        return BOOT_FAIL;

    /* 检查反回滚版本号 */
    if (hdr->version < get_otp_min_version())
        return BOOT_FAIL_ROLLBACK;

    jump_to_app(APP_ADDRESS);
    return BOOT_OK;
}
```

### 5.2 ESP32 Secure Boot V2

```
Secure Boot V2 验证流程:

ROM Bootloader (固化,不可修改)
  |- 读取eFuse中的公钥摘要
  |- 从Flash读取签名块(最多3个)
  |- 计算公钥SHA-256,与eFuse摘要比对
  |- 使用该公钥验证bootloader签名
  |
  v (验证通过)
  2nd Stage Bootloader
  |- 验证应用程序签名
  |
  v (验证通过)
  执行应用程序
```

| 特性 | V1 | V2 |
|------|----|----|
| 签名算法 | RSA-1024(已不安全) | RSA-3072 / ECDSA P-256 |
| 密钥管理 | 单一密钥 | 最多3个签名密钥(可轮换) |
| 密钥撤销 | 不支持 | 支持通过eFuse撤销 |
| 应用签名 | 由bootloader验证 | 可由ROM直接验证 |

### 5.3 MCUboot (Zephyr RTOS)

MCUboot是跨RTOS生态的安全启动管理器事实标准,三种升级策略:

| 策略 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| Overwrite | Slot B覆盖Slot A | 简单 | 无法回滚,断电可能砖化 |
| Swap | Slot A/B逐页交换 | 原子性,支持回滚 | 需要scratch区,Flash磨损大 |
| Direct-XIP | 在Slot B原地执行 | 零拷贝 | slot大小必须一致 |

```c
/* MCUboot映像头关键字段 */
struct image_header {
    uint32_t magic;     /* 0x96f3b83c */
    uint32_t load_addr;
    uint32_t img_size;
    uint32_t flags;
    struct { uint16_t major, minor, rev, build; } ver;  /* 用于反回滚 */
    /* TLV区域: 签名、公钥等 */
};
/* 签名: imgtool sign --key key.pem --version 1.2.0 --align 4 firmware.bin firmware-signed.bin */
```

## 6. 反回滚保护

### 6.1 降级攻击原理

降级攻击(Downgrade Attack):攻击者将固件回退到有已知漏洞的旧版本。例如设备当前为v2.1(已修补漏洞),攻击者刷入v1.0(存在漏洞),若没有反回滚检查,设备会接受旧版本。

### 6.2 实现方案

```c
/**
 * 方案1: 基于OTP单调计数器 (STM32)
 * OTP区域中每个位代表一个版本号,只能从0写1(不可逆)
 */
uint32_t read_otp_counter(void)
{
    return *(volatile uint32_t *)OTP_COUNTER_ADDR;
}

int check_anti_rollback(uint32_t fw_version)
{
    uint32_t otp_counter = read_otp_counter();
    if (fw_version < otp_counter) return ROLLBACK_DETECTED;
    return ROLLBACK_OK;
}

/* 方案2: 基于eFuse (ESP32)
 * 使用ABS_MAX_VERSION字段,配合Secure Boot V2自动检查 */
```

| 考量 | 过于激进 | 过于保守(推荐) |
|------|---------|---------------|
| 版本步长 | 每个小版本都烧OTP位 | 只在重大安全更新时烧 |
| OTP消耗 | 快速耗尽 | 节省OTP空间 |
| 安全性 | 高 | 中(可能漏掉安全补丁) |

## 7. OTA更新与安全启动集成

### 7.1 安全OTA完整流程

```
云端服务器                          设备端
    |  1. 构建新固件                  |
    |  2. 计算哈希 + 签名             |
    |  3. 打包(fw + 签名 + 版本)      |
    |---4. 推送OTA通知-------------->|
    |                                |- 5. 下载固件到备用slot
    |                                |- 6. 验证签名 + 版本号
    |                                |- 7. 标记TESTING,重启
    |                                |- 8. Bootloader验证 + 启动新固件
    |                                |- 9. 应用自检:通过则CONFIRMED
    |                                |       失败则INVALID,重启回滚
    |<--10. 上报更新结果-------------|
```

### 7.2 安全OTA关键检查

```c
/* 1. 下载完整性: 写入Flash前验证CRC */
if (download_crc != calculated_crc) return OTA_ERR_CORRUPT;

/* 2. 签名验证: 不能只验CRC,必须验签名 */
if (verify_signature(downloaded_fw) != VERIFY_OK) return OTA_ERR_INVALID_SIG;

/* 3. 版本检查: 防止降级 */
if (new_fw_version <= current_version) return OTA_ERR_DOWNGRADE;

/* 4. 原子性: A/B分区或双Bank保证断电安全 */
/* 5. 回滚窗口: 5分钟内必须确认,否则自动回滚 */
/* 6. 加密传输: OTA通道使用TLS */
/* 7. 签密分离: 加密密钥与签名密钥分开管理 */
```

## 8. 常见漏洞与缓解措施

### 8.1 攻击面与缓解

| 漏洞 | 描述 | 缓解措施 |
|------|------|---------|
| 固件未签名 | 攻击者可替换整个固件 | 必须启用Secure Boot |
| 签名算法弱 | RSA-1024可被破解 | 使用ECDSA P-256或RSA-3072 |
| 信任根可修改 | OTP未烧写/未锁定 | 出厂时烧录并锁定OTP |
| 缺少反回滚 | 可降级到有漏洞的版本 | 实现OTP/eFuse单调计数器 |
| JTAG未禁用 | 调试口可读写内存 | 出厂烧录JTAG禁用位 |
| Flash未读保护 | 可通过调试器读取固件 | 启用RDP Level 2 |
| 时序侧信道 | 验证时间泄露信息 | 常量时间比较实现 |

### 8.2 关键缓解代码

```c
/* 常量时间内存比较 -- 防止时序攻击 */
/* 错误做法: memcmp(hash, expected, 32) -- 攻击者可逐字节猜测 */
int constant_time_compare(const uint8_t *a, const uint8_t *b, size_t len)
{
    uint8_t diff = 0;
    for (size_t i = 0; i < len; i++)
        diff |= a[i] ^ b[i];  /* 异或,不同则非零,不要提前返回! */
    return (diff == 0) ? 0 : 1;
}

/* Flash读保护 (STM32): Level 0=无保护; Level 1=调试器连接时擦除; Level 2=永久锁定(生产推荐) */
```

### 8.3 安全启动检查清单

- [ ] 信任根存储在OTP/eFuse/ROM,不可软件修改
- [ ] 启动链每一级都验证下一级的签名
- [ ] 使用ECDSA P-256或更强的签名算法
- [ ] 实现反回滚保护(OTP单调计数器)
- [ ] 固件签名与加密密钥分离管理
- [ ] 签名验证使用常量时间比较
- [ ] 出厂时烧录并锁定安全配置位
- [ ] 禁用JTAG/SWD调试口
- [ ] 启用Flash读保护(RDP Level 1或2)
- [ ] OTA更新通道使用TLS加密

## 总结

MCU安全启动是从硬件根信任出发、逐级验证的信任链构建过程。核心要点:

1. **启动流程**: 复位向量 -> 栈初始化 -> SystemInit -> main(),每一步都为安全启动提供验证锚点
2. **信任根**: 必须基于不可篡改的硬件(OTP/eFuse/ROM),软件层面的"信任根"不可靠
3. **签名验证**: ECDSA P-256是当前最优平衡点,签名短、验证快、安全性足够
4. **平台选型**: STM32 SBSFU适合ST生态,ESP32 Secure Boot V2开箱即用,MCUboot是跨平台标准选择
5. **反回滚**: 没有反回滚的安全启动是不完整的,降级攻击是真实威胁
6. **深度防御**: 安全启动不是银弹,需配合Flash保护、调试口禁用、常量时间比较等措施

安全启动的设计原则:不要追求完美,而要追求可验证--每一步都可以被审计,每一个假设都可以被检验。

## 参考文献

1. ARM. "ARMv7-M Architecture Reference Manual", DDI 0403, 2024. -- Cortex-M向量表与异常处理机制的权威参考
2. STMicroelectronics. "AN4968: STM32CubeMX SBSFU implementation", 2023. -- STM32 SBSFU的官方应用笔记
3. Espressif. "ESP32 Secure Boot V2 Guide", ESP-IDF Documentation v5.2, 2024. -- ESP32安全启动V2的完整设计文档
4. MCUboot Project. "MCUboot Design Documentation", https://docs.mcuboot.com/, 2024. -- MCUboot架构与升级策略的官方文档
5. NIST. "SP 800-193: Platform Firmware Resiliency Guidelines", 2023. -- 固件弹性与安全启动的标准化框架
