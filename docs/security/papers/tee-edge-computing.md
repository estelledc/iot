---
schema_version: '1.0'
id: tee-edge-computing
title: TEE与边缘计算安全：硬件隔离的信任锚
layer: 6
content_type: technical_analysis
difficulty: advanced
reading_time: 24
prerequisites:
  - secure-boot-root-of-trust
  - arm-trustzone-iot-security
  - side-channel-attack-defense
tags:
- TEE
- TrustZone
- SGX
- TDX
- Keystone
- 机密计算
- 远程证明
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# TEE与边缘计算安全：硬件隔离的信任锚

> **难度**：🟡 进阶 | **领域**：可信计算、边缘安全 | **关键词**：TEE, TrustZone, SGX, TDX, Keystone | **阅读时间**：约 24 分钟

## 日常类比

公寓楼有保安（防火墙），但保安被收买后，屋里财物仍暴露。可信执行环境（Trusted Execution Environment, TEE）像在家里再装银行级保险箱：即使操作系统被攻破，飞地内代码与数据仍受硬件隔离保护，并能向远端证明"保险箱没被撬过"（远程证明）。对边缘计算而言，模型与敏感推理可在不可信主机上运行，攻击者即便拿到 root 也难直接读出飞地内容——但仍须面对侧信道等现实攻击[6]。

## 摘要

本文对比 ARM TrustZone、Intel SGX/TDX 与 RISC-V Keystone 在边缘场景的隔离模型、证明机制与开销量级，并讨论机密计算（Confidential Computing）落地与已知攻击面。性能百分比与 TCB 行数来自公开论文/白皮书量级，跨芯片差异大，部署须实测。

## 1. TEE 核心概念

| 属性 | 含义 | 类比 |
|------|------|------|
| 机密性 | 外部不可读内部明文 | 保险箱锁住内容 |
| 完整性 | 内部代码/数据防篡改 | 防拆封条 |
| 远程证明 | 远端验证所跑度量 | 银行远程验箱 |

信任模型：只信任硬件与 TEE 固件，不默认信任操作系统、虚拟机监控器（Virtual Machine Monitor, VMM）乃至云运维人员——即最小化可信计算基（Trusted Computing Base, TCB）[5][7]。

## 2. ARM TrustZone

TrustZone 将处理器分为 Normal World 与 Secure World；内存控制器的 Non-Secure（NS）位在硬件上禁止普通世界访问安全世界内存，世界切换经 Secure Monitor Call（SMC）[1]。

| 变体 | 目标 | 特点 |
|------|------|------|
| TrustZone-A | Cortex-A 边缘网关 | 完整可信 OS（如 OP-TEE） |
| TrustZone-M | Cortex-M23/M33 等 | 切换开销低、固件可裁到数十 KB 量级 |
| CCA Realm | Armv9 机密计算 | 多实例 Realm，面向数据中心/高端边缘[9] |

TrustZone-M 用安全属性单元（Security Attribution Unit, SAU）与实现定义属性单元（IDAU）划分区域；Nordic nRF5340 等 SoC 将密钥与安全启动放安全世界，协议栈放普通世界。OP-TEE 实现 GlobalPlatform API，覆盖安全存储、密钥、DRM 等用例。

## 3. Intel SGX / TDX

**SGX（Software Guard Extensions）**：用户态 enclave，内存经 Memory Encryption Engine 保护；支持 Sealing 与远程证明[2]。早期 Enclave Page Cache（EPC）容量受限，超限换出开销显著；桌面酷睿后续世代弱化/移除客户端 SGX，服务器 Xeon 路线仍延续相关能力（以产品文档为准）。

**TDX（Trust Domain Extensions）**：保护整台虚拟机（Trust Domain），编程改动小于 SGX，面向多租户边缘/云[4]。

| 特性 | SGX | TDX |
|------|-----|-----|
| 粒度 | 进程内 enclave | 整 VM |
| 内存 | 受 EPC 等约束 | 相对宽松 |
| 信任 | 不信任 OS/VMM | 不信任 VMM |
| 改代码 | 通常需要 | 整 VM 可少改 |
| 证明 | SGX Attestation | TDX Attestation |

公开基准中，enclave 进出可达数千–上万周期量级；纯计算损失常见为数个百分点到数十个百分点，视工作负载而定——下表为示意，非排行榜。

## 4. RISC-V Keystone

Keystone 基于物理内存保护（Physical Memory Protection, PMP），Security Monitor 运行于 M-mode，公开材料称 TCB 可到约数千行量级，强调可定制与可审计[3]。

| 特性 | TrustZone-M | SGX | Keystone |
|------|-------------|-----|----------|
| 架构 | ARM | x86 | RISC-V |
| 开源程度 | 硬件闭源为主 | 闭源 ISA 扩展 | 框架开源 |
| TCB 倾向 | 中 | 较大 | 可裁较小 |
| 可定制 | 低 | 低 | 高 |
| IoT 终端 | 很适合 | 偏服务器 | 可裁剪 |
| 生态 | 成熟 | 成熟（服务器） | 发展中 |

## 5. 边缘机密计算

机密计算联盟（Confidential Computing Consortium）强调保护"使用中的数据"[7]。典型分层：云端密钥/策略 ↔ 边缘网关 TEE（推理/预处理）↔ 终端 TrustZone-M（密钥与安全启动）。

| 场景 | 平台倾向 | 要点 |
|------|----------|------|
| 工厂视觉质检 | Jetson 类 + TrustZone | 模型在安全世界解密推理 |
| 医疗联合分析 | Xeon 边缘 + SGX/TDX | 聚合在飞地，满足合规叙事需法务确认 |
| 车载 V2X | S32G 等 + TrustZone-A | 私钥不出安全世界 |

案例中的"性能损失百分之几"为单点报告量级，换模型/换板会变。

## 6. 已知攻击与缓解代价

| 攻击类型 | 主要影响 | 缓解倾向 |
|----------|----------|----------|
| Cache Timing | SGX/TZ | 缓存分区、常量时间 |
| 推测执行变种 | SGX 等 | 微码/屏障 |
| Page Fault 控制信道 | SGX | ORAM、运行时加固 |
| 电压毛刺 | TZ-M 等 | 电压监测 |
| 回滚 | 密封数据 | 单调计数器 |
| Controlled-Channel | SGX | 减少可观测控制流[6] |

| 缓解 | 开销量级 | 实用性 |
|------|----------|--------|
| ORAM | 可达数量级变慢 | 低 |
| 缓存分区 | 约一成量级 | 高 |
| 常量时间 | 数百分数–三成 | 高 |
| 微码补丁 | 较低 | 高（针对已知洞） |

## 7. 性能对比（示意量级）

公开对比常显示 TrustZone 相对开销较小、SGX 在频繁进出与 I/O 密集负载上惩罚更大、Keystone 介于其间[3][10]。AES/RSA/CNN/SQLite 等具体 MB/s 或 qps 强依赖 CPU 代际与编译选项，本文不绑定单一绝对数；选型以目标板上的证明延迟、飞地切换与业务 SLA 实测为准。

## 8. 局限、挑战与可改进方向

### 1. TEE ≠ 免疫侧信道

**局限**：硬件隔离不消除缓存、页错误、电压等旁路；把"在 TEE 里"当成绝对安全会导致错误架构决策[6]。
**改进**：高价值密钥路径叠加常量时间与 SE；威胁模型写明是否防物理邻近攻击；关键产品做针对性评估。

### 2. 远程证明与密钥基础设施复杂

**局限**：厂商证明服务、证书链、撤销与多 TEE 互信（RATS 等）集成成本高；边缘离线时证明刷新困难。
**改进**：缓存短期证明会话；边缘本地策略+定期补证明；跨平台优先标准声明格式而非专有 blob。

### 3. 资源与移植成本

**局限**：MCU 上 TrustZone-M 安全固件挤占 Flash/RAM；SGX 需改应用；闭源 blob 增大审计盲区。
**改进**：仅把密钥、许可证、模型解密放入 TEE；普通推理可加密内存+权限隔离折中；开源 SM（如 Keystone）用于可审计场景。

### 4. 产品路线变动风险

**局限**：客户端 SGX 退场等说明厂商路线可能突变，长周期 IoT 设备面临"设计时有、量产时无"风险。
**改进**：抽象证明与密封 API；硬件选型绑定服务器/车规长期支持清单；关注 CCA/CoVE/GPU 机密计算演进但避免过早绑定单一扩展[8][9]。

## 参考文献

[1] Arm, "Arm TrustZone Technology," Architecture Reference Manual, 2024.
[2] V. Costan and S. Devadas, "Intel SGX Explained," IACR ePrint, 2016.
[3] D. Lee et al., "Keystone: An Open Framework for Architecting Trusted Execution Environments," EuroSys, 2020.
[4] Intel, "Intel Trust Domain Extensions (TDX) Architecture," White Paper, 2024.
[5] M. Sabt et al., "Trusted Execution Environment: What It Is, and What It Is Not," IEEE TrustCom, 2015.
[6] J. Van Bulck et al., "A Tale of Two Worlds: Assessing the Vulnerability of Enclave Shielding Runtimes," CCS, 2019.
[7] Confidential Computing Consortium, "A Technical Analysis of Confidential Computing," White Paper, 2024.
[8] NVIDIA, "Confidential Computing on NVIDIA Hopper GPUs," Technical Brief, 2024.
[9] Arm, "Arm Confidential Compute Architecture (CCA)," Architecture Specification, 2024.
[10] B. Feng et al., "TEE-based Edge AI: Challenges and Solutions," ACM Computing Surveys, 2025.
[11] IETF, "Remote ATtestation procedureS (RATS) Architecture," RFC 9334, 2023.
[12] GlobalPlatform, "TEE Internal Core API Specification," 相关版本.
