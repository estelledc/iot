---
schema_version: '1.0'
id: firmware-security
title: IoT固件安全分析：从提取到防护的全链路
layer: 6
content_type: technical_analysis
difficulty: advanced
reading_time: 30
prerequisites:
  - secure-boot-root-of-trust
  - ota-secure-update
  - sbom-software-supply-chain
tags:
- 固件安全
- 逆向工程
- 安全启动
- OTA
- Fuzzing
- SBOM
- MCUboot
- 漏洞分析
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT固件安全分析：从提取到防护的全链路

> **难度**：🟠 进阶 | **领域**：固件安全 / 逆向工程 | **阅读时间**：约 30 分钟

## 日常类比

家用路由器的“系统”往往不是桌面操作系统，而是几 MB 到几十 MB 的固件：内核、应用、配置甚至密钥被打包装进 Flash。

拿到固件并拆开分析，就像拿到一栋楼的施工图与钥匙柜清单——既能帮厂商找漏洞，也能被攻击者用来找默认口令、过时组件和未鉴权调试口。攻防双方用的是同一套“拆包—理解—验证”流程。

## 摘要

物联网（Internet of Things, IoT）固件是攻防焦点。本文覆盖提取路径、静态/动态逆向、模糊测试（Fuzzing）与符号执行、安全启动链与安全空中下载（Over-The-Air, OTA）更新，并对照 OWASP 固件测试方法与自动化扫描工具。行业统计数字口径不一，文中作软化处理并以参考文献为线索。

## 1 现状：公开报告中的常见问题

Finite State 等机构的年度固件分析报告[1]常给出“平均 CVE 数、硬编码凭证比例、安全启动普及率”等指标。不同年份样本与检测方法不同，**具体百分比应回查原报告**，下文只保留定性结论：

| 问题类型 | 公开报告中的常见趋势 | 工程含义 |
|----------|----------------------|----------|
| 已知 CVE 堆积 | 单镜像常含大量已知漏洞 | 需要 SBOM + 持续补丁 |
| 不安全 API / 过时组件 | 占比高 | 供应链与 SDK 老化 |
| 硬编码凭证 | 反复出现 | 提取固件即可横向移动 |
| 安全 OTA / 安全启动 | 普及率仍有限 | 被攻破后难恢复信任 |

根因常是：硬件公司软件安全投入不足、SDK 多年不升级、更新通道缺失。

## 2 固件提取

| 方法 | 难度 | 典型工具/设备 | 风险 |
|------|------|---------------|------|
| 官网/支持站下载 | 低 | 浏览器 | 无 |
| 截获 OTA | 低–中 | 抓包；若明文则易得 | 无设备损伤 |
| UART/JTAG | 中 | USB‑TTL、OpenOCD | 低 |
| SPI Flash 直读 | 中 | 编程器；或需热风 | 可能损硬件 |
| 芯片脱焊 | 高 | BGA 返修 | 高 |
| 故障注入绕过读保护 | 很高 | 毛刺/激光等 | 可能砖机 |

### 常见格式

| 格式 | 常见设备 | 提取线索 |
|------|----------|----------|
| SquashFS + 内核 | 路由器、NVR | binwalk、unsquashfs |
| JFFS2 / UBIFS | 网关类 | jefferson、ubi_reader |
| 裸机 binary | MCU | 直接进 Ghidra |
| 加密/签名容器 | 高安全产品 | 先破密钥或从调试口拿 |

大规模嵌入式固件安全研究的早期基线见 Costin 等[2]。

## 3 逆向与仿真

### 3.1 工具链

| 工具 | 用途 | 开源 |
|------|------|------|
| Ghidra | 反汇编/反编译 | 是 |
| IDA Pro / Binary Ninja | 商业逆向 | 否 |
| radare2/rizin | CLI 逆向 | 是 |
| binwalk | 解包 | 是 |
| EMBA / Firmwalker | 自动化检查 | 是 |
| FirmAE 等 | 系统级仿真 | 是 |

### 3.2 静态流程

解包 → 搜口令/密钥/证书 → 逆向 httpd 等关键二进制 → 识别第三方库版本 → 匹配 CVE。

### 3.3 动态仿真

FirmAE/QEMU 等可在 PC 上模拟 ARM/MIPS 固件网络栈[3]。论文报告的“成功仿真率”依赖样本集，部署时以本仓库固件实测为准，不宜写死单一百分比。

## 4 自动化漏洞发现

### 4.1 Fuzzing 挑战与工具

| 挑战 | 说明 | 常见对策 |
|------|------|----------|
| 设备上难跑覆盖率 | MCU 资源少 | 仿真 / rehosting |
| 外设依赖 | MMIO、中断 | 精确 MMIO 模型[4] |
| 协议状态机 | 需握手后才到深路径 | 协议感知种子 |
| 反馈弱 | 裸机缺 sanitizer | 仿真插桩 / 硬件追踪 |

| 工具（代表） | 思路 | 适用 |
|--------------|------|------|
| Fuzzware[4] | 精确 MMIO + 模糊 | Cortex‑M 等 |
| SaTC 等 | Web 入口提取 + fuzz | Linux IoT |
| Greenhouse 等 LLM 辅助[9] | 种子/重托管辅助 | 研究前沿 |
| AFL 家族 + 系统仿真 | 经典覆盖率引导 | 能仿真的 Linux 固件 |

### 4.2 符号执行

angr、KLEE、Triton 等可生成触发路径的输入[7]。限制是路径爆炸与环境建模成本；常与 fuzz 组合而非替代。

### 4.3 LLM 辅助

用于注释反编译、生成协议种子、识别常见缺陷模式；需人工验证，避免幻觉当 CVE。

## 5 安全启动与信任根

```
ROM/eFuse 信任根 → BL1 → BL2/U-Boot → 内核 → 应用
         （每级验证下一级签名，失败则停）
```

| 信任根 | 强度 | 灵活性 | 典型形态 |
|--------|------|--------|----------|
| Mask ROM | 高 | 无 | 多数 MCU |
| OTP/eFuse | 高 | 低 | i.MX、STM32H7 等 |
| 独立安全芯片 | 很高 | 中 | ATECC、SE050 等 |
| PUF + ROM | 高 | 中 | 抗克隆取向 |

**MCUboot** 是 MCU 场景常见开源安全引导：支持多种签名算法、版本回滚保护、可选镜像加密与 A/B 槽[6]。Flash 占用随配置变化（数十 KB 量级），以官方文档为准。

## 6 安全 OTA

OTA 是补丁主通道，也是“一次攻破、百万设备中招”的通道。

IETF SUIT 定义面向受限设备的清单（Manifest）与 COSE 签名更新架构[5]。

| 方案 | 签名 | 传输保护 | 回滚保护 | 适合 |
|------|------|----------|----------|------|
| 明文 HTTP + 校验和 | 弱 | 弱 | 常无 | 不推荐 |
| HTTPS + 哈希 | 完整性有限 | TLS | 常无 | 最低基线 |
| MCUboot + SUIT | 强 | COSE 等 | 版本单调 | MCU |
| Mender / 云厂商 OTA | 强 | mTLS/TLS | 通常有 | Linux IoT |

## 7 评估框架与案例（示意）

OWASP 固件安全测试方法覆盖信息泄露、过时组件、危险服务、弱密码学、权限与更新机制等[10]。EMBA 等工具可自动化部分检查[8]。

| 测试项 | 常见发现类型 |
|--------|--------------|
| 密钥与口令 | 硬编码、测试账号残留 |
| 组件清单 | 多年未升级的 OpenSSL/BusyBox |
| 网络服务 | Telnet、未鉴权调试口 |
| 更新 | 无签名、可降级 |

真实案例模式（细节以 CVE 公告为准）：Web 诊断命令注入 → RCE；无回滚保护的降级攻击；固件内硬编码设备间对称密钥。修复分别对应输入净化、MCUboot 版本检查、每设备唯一密钥 + 双向认证。

## 8 局限、挑战与可改进方向

### 1. 加密固件与读保护提高分析成本，也提高盲区

**局限**：无法提取时，厂商与第三方都难做完整审计；安全靠“藏”不靠“可验证”。
**改进**：向客户/实验室提供受控审计镜像或 SBOM + 签名证明；读保护与安全启动并行，而不是只靠混淆。

### 2. 仿真成功不等于漏洞可利用

**局限**：QEMU 外设模型不完整会导致漏报/误报；设备特有 DMA 路径仿真不到。
**改进**：关键漏洞在实机或硬件在环上复现；维护外设模型回归集。

### 3. Fuzz 发现量不等于产品风险下降

**局限**：论文“N 个零日”难对比；修复与 OTA 覆盖率才是风险函数。
**改进**：以“可利用性 + 影响面 + 补丁时效”排序；绑定 CRA/SBOM 义务做组件级追踪。

### 4. 安全启动被错误配置抵消

**局限**：调试熔丝未烧、签名密钥共用、允许降级，使信任链名存实亡。
**改进**：量产熔丝清单；每产品线独立签名密钥；强制单调版本；出厂抽检。

### 5. 工具链与法规要求脱节

**局限**：只会 binwalk 不够满足欧盟 CRA 等对漏洞处理与 SBOM 的要求。
**改进**：EMBA/sca 流水线进 CI；维护机器可读 SBOM；披露与 SLA 流程产品化。

## 9 趋势（简）

SBOM 强制化、Rust 等内存安全语言用于新固件、Linux IoT 上 eBPF 运行时监控、LLM+fuzz 提效，都在推进，但都需与安全启动/OTA 闭环结合才有防御深度。

## 参考文献

[1] Finite State, "The State of IoT/Connected Device Security," Annual Report, 2024（具体统计以原报告表格为准）.
[2] A. Costin et al., "A Large-Scale Analysis of the Security of Embedded Firmwares," USENIX Security, 2014.
[3] D. Chen et al., "FirmAE: Towards Large-Scale Emulation of IoT Firmware for Dynamic Analysis," USENIX Security, 2020.
[4] T. Scharnowski et al., "Fuzzware: Using Precise MMIO Modeling for Effective Firmware Fuzzing," USENIX Security, 2022.
[5] IETF, "SUIT: Software Updates for Internet of Things," RFC 9019 及 manifest 相关草案/RFC, 2021–2024.
[6] MCUboot Project, "MCUboot: Secure Boot for 32-bit Microcontrollers," Documentation, 2024.
[7] Y. Shoshitaishvili et al., "SOK: (State of) The Art of War: Offensive Techniques in Binary Analysis," IEEE S&P, 2016.
[8] EMBA Project, "EMBA: The Firmware Security Analyzer," GitHub, 2024.
[9] Q. Feng et al., "Greenhouse: LLM-assisted Firmware Rehosting and Fuzzing," USENIX Security, 2024（或同行评议最终版）.
[10] OWASP, "Firmware Security Testing Methodology," OWASP IoT Project, 近年版本.
[11] EU Cyber Resilience Act (CRA) 相关文本与指导, 2024–2026.
[12] Google OSS-Fuzz / AI 辅助漏洞发现公开材料, 2023–2024.
