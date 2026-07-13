---
schema_version: '1.0'
id: arm-trustzone-iot-security
title: ARM TrustZone在IoT安全隔离中的应用
layer: 1
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - arm-cortex-m-architecture-overview
  - secure-element-se-iot
tags:
  - TrustZone
  - TEE
  - ARMv8-M
  - SAU
  - TF-M
  - PSA
  - IoT安全
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# ARM TrustZone在IoT安全隔离中的应用

> **难度**：🔴 高级 | **领域**：可信执行环境 | **阅读时间**：约 16 分钟

## 日常类比

办公楼大厅谁都能走，机密室只能刷卡进出，且规则由硬件门禁强制。TrustZone 在同一颗 CPU 上划出安全世界（Secure）与非安全世界（Non-Secure）：非安全代码无法直接摸到安全内存/外设。资源不够再加独立安全 MCU 时，TrustZone-M 提供单芯片 TEE（Trusted Execution Environment）路径[1][2]。

## 摘要

TrustZone-A 面向应用处理器；TrustZone-M 面向 Cortex-M23/M33/M55 等。IDAU/SAU 标定内存属性，NSC（Non-Secure Callable）经 `SG` 受控调用。TF-M（Trusted Firmware-M）与 PSA Certified 提供参考实现与分级。隔离是必要非充分：安全世界仍可能有漏洞。文中周期/KB 开销为量级[2][3][4]。

## 1. 双世界与判定硬件

| 版本 | 架构 | 代表 |
|------|------|------|
| TrustZone-A | A-profile | Cortex-A 类 |
| TrustZone-M | ARMv8-M | M23/M33/M55/M85 等 |

安全世界可访问更广资源；非安全仅 NS 资源，越权触发安全故障并由安全侧处理[1][2]。

| 访问 | Secure 代码 | Non-Secure 代码 |
|------|-------------|-----------------|
| 安全内存/外设 | 允许 | 硬件拒绝 |
| 非安全内存/外设 | 通常允许 | 允许 |
| NSC 入口 | 可实现 | 仅经合法 veneer/`SG` |

IDAU 为硅厂固化默认；SAU 由安全固件配置区域（含 NSC）。典型把密钥、安全启动、密码服务放 Secure，协议栈与业务放 NS[2][5]。

## 2. 软件栈与认证

TF-M 提供安全启动、存储、加密、证明等 PSA 服务接口；NS 应用经 Client API 调用。开发常需双工程、双链接脚本与严格参数校验（避免把 Secure 指针泄露给 NS）[3][6]。

| PSA 级别（叙事） | 侧重 | 适用粗分 |
|------------------|------|----------|
| Level 1 | 问卷/架构宣称 | 入门 |
| Level 2 | 实验室评估 | 商业/工业常见目标 |
| Level 3 | 更深入测试 | 高保证场景 |

威胁面仍含物理调试、侧信道、安全世界实现缺陷；TrustZone 不替代安全元件（SE）的抗物理能力叙事[4][7]。

## 3. 开销与适用边界

| 维度 | 量级叙事 | 备注 |
|------|----------|------|
| 跨界调用 | 数十周期量级 | 视实现 |
| Flash | 常数十–百余 KB 级 TF-M | 配置相关 |
| RAM | 常数–十余 KB 级以上 | 服务集相关 |

适合：密钥保管、安全 OTA、无人值守、需 PSA。不适合：无安全需求的极简传感；已有强 SE；Flash 极紧且安全固件放不下；“只要 TLS 库”却无隔离资产[5][8]。

## 4. 局限、挑战与可改进方向

### 1. 把硬件隔离当成“已安全”

**局限**：Secure 世界 bug、错误 SAU、调试口开放仍可破。
**改进**：最小 TCB、威胁建模、关闭/认证调试、持续补丁[4][7]。

### 2. NSC 接口成为攻击面

**局限**：缺校验的网关等于提权跳板。
**改进**：所有入口做 `cmse_check_*`、拷贝后再用、模糊测试边界[3][6]。

### 3. 双世界工程复杂度被低估

**局限**：构建、调试、日志跨界成本高，进度风险大。
**改进**：早期引入 TF-M 参考集成；安全/非安全 CI 分开门禁[3][5]。

### 4. 与 SE/HSM 边界不清

**局限**：TrustZone 抗物理弱于专用 SE 的常见叙事。
**改进**：高价值根密钥放 SE；TrustZone 做运行时隔离与策略执行[7][9]。

## 5. 实践要点

1. 先列资产（密钥、启动链、证明），再画 SAU 图，最后写业务。
2. 量产前做非法 NS 访问与调试攻击回归。
3. 需要合规时尽早选 PSA 目标级别，避免后期翻版图。

## 参考文献

[1] Arm, ARMv8-M Architecture Reference Manual (DDI 0553).
[2] Arm, TrustZone Technology for the ARMv8-M Architecture (DEN0024).
[3] Trusted Firmware Project, TF-M Documentation.
[4] Arm, Platform Security Architecture (PSA) Certified requirements (public materials).
[5] STMicroelectronics, STM32L5/U5 TrustZone development guides (e.g. AN5393 class).
[6] Arm Compiler/CMSE (Cortex-M Security Extensions) user guidance.
[7] Common criteria / PSA threat model overviews for IoT devices.
[8] NXP/Nordic TrustZone-M application notes (M33 based SoCs).
[9] Secure Element vs TEE comparison industry whitepapers.
[10] Arm Platform Security Architecture security model documents.
[11] GlobalPlatform TEE related background (contrast with TrustZone-M).
