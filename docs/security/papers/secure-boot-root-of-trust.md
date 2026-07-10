---
schema_version: '1.0'
id: secure-boot-root-of-trust
title: 安全启动链与 Root of Trust
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - firmware-security
  - ota-secure-update
tags:
- 安全启动
- Root of Trust
- TPM
- MCUboot
- SBSFU
- 防回滚
- 信任链
- 安全元件
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 安全启动链与 Root of Trust

> **难度**：🟡 中级 | **领域**：嵌入式安全、固件保护 | **阅读时间**：约 20 分钟

## 日常类比

早上你信任闹钟时间（它对过网络授时），信任天气 App（你认准来源），信任牛奶没过期（你看了日期）。每一步信任都建立在前一步核验上。

安全启动链同理：上电后最先跑的一小段代码固化在只读存储器（Read-Only Memory, ROM）里，验证下一阶段签名通过才交权。第一个“门卫”焊在墙上（硬件信任根），再验下一岗工牌——任一环失败，启动停止。

## 1. 启动链架构

### 1.1 典型阶段

```
上电
 → Stage 0: Boot ROM（不可变）验证 Stage 1
 → Stage 1: 一级引导（SPL/BL2）初始化 DRAM，验证 Stage 2
 → Stage 2: U-Boot/BL33 等验证内核与设备树
 → Stage 3: OS 内核（可选 dm-verity 等）
 → Stage 4: 应用与运行时完整性
```

### 1.2 信任传递

- **信任根（Root of Trust, RoT）**：不可变硬件/固件，整条链起点
- **信任链（Chain of Trust）**：每阶段验证下一阶段再交权
- **最小化**：RoT 代码越小，攻击面越小

## 2. 硬件信任根

### 2.1 类型对比

| 类型 | 实现方式 | 代表方向 | 安全级别（相对） |
|------|---------|---------|-----------------|
| 片上 ROM | 出厂固化代码 | 多数 MCU | 基础 |
| 安全元件（Secure Element, SE） | 独立安全芯片 | ATECC608B 等 | 高 |
| 可信平台模块（Trusted Platform Module, TPM） | 标准安全协处理器 | TPM 2.0 | 高 |
| 可信执行环境（Trusted Execution Environment, TEE） | 如 ARM TrustZone | 应用处理器 | 中高 |
| 物理不可克隆函数（PUF） | 硅指纹派生密钥 | Intrinsic ID 等 | 高（实现相关） |

### 2.2 TPM 2.0 在 IoT 中的角色

TPM 提供密钥隔离、平台配置寄存器（Platform Configuration Register, PCR）度量扩展、远程证明等能力。[3] PCR 扩展概念上为 `PCR_new = Hash(PCR_old || measurement)`。适合网关/工控主机；极低成本传感器更常靠 MCU RoT + SE。

### 2.3 安全元件对照（公开资料量级）

| 特性 | ATECC608B | OPTIGA Trust M | SE050 |
|------|-----------|----------------|-------|
| 厂商 | Microchip | Infineon | NXP |
| 接口 | I2C | I2C | I2C/SPI |
| 算法 | ECC P-256, SHA-256 等 | ECC/RSA/AES 等 | 更广，含 Ed25519 等 |
| 认证 | CC EAL5+ 级宣传 | EAL6+ 级宣传 | EAL6+ 级宣传 |
| 单价（量产量级） | 亚美元–约 1 美元级 | 约 1 美元级 | 更高 |
| PQC | 基本无 | 路线图表述 | 部分新品演进 |

价格与认证以当期数据手册/证书为准，上表仅作选型地图。[5][6][7]

## 3. Verified Boot vs Measured Boot

| 维度 | Verified Boot（验证启动） | Measured Boot（度量启动） |
|------|--------------------------|---------------------------|
| 行为 | 验签失败则拒绝启动 | 记录度量，不必然停机 |
| 保证 | 强阻止 | 偏检测与证明 |
| 可用性 | 可能变砖需恢复路径 | 更高可用 |
| 复杂度 | 中 | 高（需证明基础设施） |
| IoT | 多数消费/工控推荐 | 关键基础设施、远程证明 |
| 典型 | Android AVB、MCUboot、STM32 SBSFU | TPM + IMA 等 |

## 4. STM32 / MCUboot 实践要点

ST 的 Secure Boot and Secure Firmware Update（SBSFU）给出双槽（Active / Download）、写保护、PCROP、读出保护（Readout Protection, RDP）等参考布局。[2] 开源侧 MCUboot 覆盖多架构，文档与社区更友好。[4]

验证逻辑应至少覆盖：头部完整性、防回滚版本、公钥验签、（可选）固件解密。RDP Level 2 等熔丝策略不可逆，量产前必须用可恢复级别完成测试。[2]

## 5. 证书链与密钥管理

```
Root CA（离线）
 ├─ Intermediate CA → 设备证 / 固件签名证
 └─ Recovery CA（应急）
```

| 密钥类型 | 存储 | 轮换 | 泄露影响 |
|---------|------|------|---------|
| Root | HSM/离线 | 极罕见 | 灾难 |
| 固件签名 | 构建 HSM | 年际 | 高 |
| 设备身份 | SE/TPM | 生命周期 | 单设备 |
| 会话 | RAM | 每次 | 低 |

工厂注入须经安全通道，注入后锁定导出；私钥不应以明文长期落在产测电脑磁盘。[1][5]

## 6. 防回滚

攻击者可能刷回含已知漏洞的旧固件。机制包括：一次性可编程（One-Time Programmable, OTP）熔丝计数、RPMB / SE 内安全计数器等。OTP 槽位有限；安全存储可支持更大版本空间但依赖硬件防篡改。[2][4]

## 7. 局限、挑战与可改进方向

### 1. RoT 实现缺陷会一击致命

**局限**：Boot ROM 或早期引导若有漏洞，整条链失效；部分 SoC 历史问题已公开。[1][9]
**改进**：跟踪芯片勘误；尽量缩短 Stage 0/1；启用硬件写保护与调试熔丝策略。

### 2. 安全与可维护性冲突

**局限**：RDP/熔丝过狠导致返修困难；过松则调试口成后门。[2]
**改进**：分阶段保护（试产 Level 1、量产 Level 2）；保留受控恢复分区与物理授权流程。

### 3. 防回滚槽位耗尽或不同步

**局限**：OTP 次数有限；多槽固件版本与计数器不一致会变砖。[4]
**改进**：版本号编码预留空间；升级事务化（A/B + 确认启动）；计数器与签名头原子更新。

### 4. 仅启动时验证、运行时被篡改

**局限**：Verified Boot 不自动等于运行时完整。[8][10]
**改进**：配合 dm-verity/IMA、安全 OTA、TEE 存关键资产；零信任式持续证明（网关级）。

### 5. 密钥与供应链薄弱

**局限**：产线注入被窃听、签名密钥在 CI 明文，等于安全启动归零。[1]
**改进**：HSM 签名；注入屏蔽与审计；双人授权与密钥仪式记录。

## 8. 实践建议（简）

1. 新项目优先 MCUboot 或芯片厂官方 SBSFU 参考，再裁剪。
2. 成本敏感用 SE（如 ATECC 类），需要证明再用 TPM。
3. 启动耗时用硬件哈希加速，但不要为省时间跳过关键段校验。

## 参考文献

[1] ARM, "Platform Security Architecture (PSA) Certified," 2024.
[2] STMicroelectronics, "UM2262: STM32 Secure Boot and Secure Firmware Update," Rev 5, 2024.
[3] Trusted Computing Group, "TPM 2.0 Library Specification," 2024.
[4] MCUboot Project, "MCUboot: Secure Boot for 32-bit Microcontrollers," Documentation, 2024.
[5] Microchip, "ATECC608B CryptoAuthentication Device Datasheet," 2023.
[6] Infineon, "OPTIGA Trust M Solution Reference Manual," 2024.
[7] NXP, "EdgeLock SE050: Plug & Trust Secure Element," Application Note, 2024.
[8] Google, "Android Verified Boot 2.0," AOSP Documentation, 2024.
[9] K. Eldefrawy et al., "SMART: Secure and Minimal Architecture for Establishing Dynamic Root of Trust," NDSS, 2012.
[10] S. Pinto and N. Santos, "Demystifying ARM TrustZone: A Comprehensive Survey," ACM Computing Surveys, 2019.
[11] GlobalPlatform, "TEE System Architecture," specifications, ongoing.
[12] NIST, "SP 800-193: Platform Firmware Resiliency Guidelines," 2018.
