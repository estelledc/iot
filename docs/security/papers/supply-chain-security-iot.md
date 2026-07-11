---
schema_version: '1.0'
id: supply-chain-security-iot
title: IoT 供应链安全：从芯片到云端的信任链
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 25
prerequisites:
  - sbom-software-supply-chain
  - secure-boot-root-of-trust
  - ota-secure-update
tags:
- 供应链安全
- SBOM
- SLSA
- 硬件木马
- 安全启动
- NIST-800-161
- 安全供应
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT 供应链安全：从芯片到云端的信任链

> **难度**：🟡 中级 | **领域**：供应链安全、硬件安全 | **关键词**：SBOM, SLSA, C-SCRM, 安全启动 | **阅读时间**：约 25 分钟

## 日常类比

网购高档橄榄油时，你会看产地、防伪码、封条——但若工厂换原料、运输途中调包、防伪标本身是假的，标签帮不上忙。物联网（Internet of Things, IoT）供应链更复杂：芯片、电路板、固件、第三方库、云软件开发工具包（Software Development Kit, SDK）任一环被篡改，都可能污染整批设备。SolarWinds、Log4j、XZ Utils 等事件表明：攻破一个上游节点，等于同时打击大量下游用户[2][9][10]。

## 摘要

本文按芯片→固件→软件→云服务分层梳理 IoT 供应链攻击面，覆盖硬件木马、软件物料清单（Software Bill of Materials, SBOM）、构建完整性（SLSA / in-toto）、NIST SP 800-161 供应链风险管理（Cybersecurity Supply Chain Risk Management, C-SCRM）与安全供应（Secure Provisioning）。文中事件影响规模与响应时间来自公开复盘/调查口径，跨组织差异大，宜作量级参考。

## 1. IoT 供应链攻击向量

### 1.1 攻击面分层

| 层次 | 典型威胁 | 后果 |
|------|----------|------|
| 芯片/IP | 硬件木马、不可信 IP 核 | 后门潜伏、密钥泄露 |
| PCB/元器件 | 仿冒件、焊接篡改 | 功能降级或植入 |
| 固件/引导 | 未签名镜像、引导劫持 | 持久控制 |
| 软件依赖 | 恶意包、0-day 库 | 远程代码执行 |
| 构建/CI | 流水线投毒 | 合法签名的恶意产物 |
| 云/更新 | SDK 密钥、更新通道劫持 | 规模化沦陷 |

### 1.2 历史事件（公开口径）

| 事件 | 年份 | 方式 | 公开影响量级 | IoT 教训 |
|------|------|------|-------------|----------|
| SolarWinds Sunburst | 2020 | CI/CD 注入 | 上万组织量级 | 构建环境须隔离审计[9] |
| Log4Shell | 2021 | 开源库漏洞 | 极广（含大量联网系统） | SBOM 与依赖治理[5] |
| Codecov | 2021 | CI 脚本篡改 | 数万用户量级 | 工具链亦是攻击面 |
| 3CX | 2023 | 上游依赖链 | 数十万企业量级 | 多级传导 |
| XZ Utils | 2024 | 社工维护者 | 潜在全球 Linux 影响 | 开源维护信任薄弱[10] |

### 1.3 硬件木马

| 类型 | 触发方式 | 检测难度 | 示例 |
|------|----------|----------|------|
| 组合逻辑 | 稀有输入组合 | 高 | 特定包触发后门 |
| 时序 | 运行足够周期后 | 极高 | 延迟激活 |
| 模拟 | 温/压条件 | 极高 | 条件下泄露 |
| 参数 | 改电路参数 | 极高 | 加速老化 |

设计→综合→布局布线→掩膜→晶圆→封装各阶段均可成为植入点；检测成本高，故工程上更依赖可信代工、分割制造与运行时异常监测[6]。

## 2. 硬件信任根与安全启动

信任链：不可变 ROM/eFuse 信任根 → 签名引导 → 内核 → 应用 → 运行时完整性。MCUboot 等方案在资源受限 MCU 上验证分区镜像签名，失败则拒绝启动或回退 A/B 分区。

设备身份可结合芯片唯一 ID、物理不可克隆函数（Physical Unclonable Function, PUF）与出厂证书；供应链各站（晶圆、贴片、烧录、测试）写入可验证溯源记录，部署前校验阶段完整性。

## 3. 软件供应链安全

### 3.1 SBOM

SBOM 回答"产品里有什么"。常用 SPDX / CycloneDX；Syft 生成、Grype 等扫描已知漏洞[5][8]。公开调查称具备完整 SBOM 的组织在大型 0-day 事件中影响面评估更快——具体小时/天数字因组织成熟度而异，下表为示意量级而非承诺 SLA。

| 能力 | 有可用 SBOM（倾向） | 无 SBOM（倾向） |
|------|-------------------|----------------|
| 影响评估 | 小时–天级 | 天–周级 |
| 修复编排 | 可按组件定位 | 易遗漏暗依赖 |
| 遗漏风险 | 相对较低 | 相对较高 |

### 3.2 构建系统加固

| 措施 | 做法 | 工具/框架 |
|------|------|-----------|
| 环境隔离 | 一次性构建器 | GitHub Actions / GitLab CI |
| 可重现构建 | 同源同环境同产物 | Yocto 等 |
| 产物签名与溯源 | 签名+provenance | Sigstore / in-toto[7] |
| 依赖锁定 | 版本+哈希 | west.lock 等 |
| 双人审核 | 关键路径强制评审 | CODEOWNERS |
| 成熟度分级 | 文档→加固→可重现 | SLSA L1–L4[4] |

| SLSA 级别 | 要求摘要 | IoT 对应 |
|-----------|----------|----------|
| L1 | 构建有文档 | 记录固件步骤 |
| L2 | 版本控制+构建服务 | 自动化 CI |
| L3 | 平台加固+可追溯 | 隔离构建+in-toto |
| L4 | 双人审核+可重现 | 完整审计（成本高） |

## 4. NIST SP 800-161 C-SCRM

NIST SP 800-161 Rev.1 将供应链风险拆到组织策略、任务/采购与运营控制三层：定义风险偏好 → 供应商评估与合同条款 → 技术验证与事件响应[1]。供应商评估应覆盖认证、安全开发生命周期（Secure SDLC）、漏洞披露与补丁时效、下级供应商透明度与地缘风险。

## 5. 芯片级安全与供应

| 器件（示例） | 类型 | 能力摘要 | 接口 |
|-------------|------|----------|------|
| ATECC608B 等 | 安全元素 | ECC/AES/SHA 等 | I2C |
| OPTIGA / SE050 / STSAFE 等 | 安全芯片/元素 | 证书与密钥保护 | I2C/SPI |
| PSA 认证 MCU | 集成安全 | TrustZone+安全存储 | 片上 |

批量单价随用量与年份波动，选型以当期报价与认证级别为准。出厂安全供应：一次性令牌、私钥写入不可读槽位、根 CA 哈希烧 eFuse、锁定二次供应、清除 RAM 敏感残留。

## 6. 仿冒检测与优先级清单

| 检测方法 | 成本 | 可靠性倾向 |
|----------|------|-----------|
| 外观/包装 | 低 | 低 |
| 电气参数 | 低 | 中 |
| X 射线 | 中 | 中 |
| PUF 认证 | 低（需芯片支持） | 高 |
| 去盖分析 | 高 | 高 |
| 侧信道指纹 | 中 | 高（需基线） |

| 优先级 | 措施 | 成本 | 影响 |
|--------|------|------|------|
| P0 | 维护 SBOM + 漏洞扫描 | 低 | 极高 |
| P0 | 安全启动与固件签名 | 低 | 极高 |
| P1 | CI 依赖审计、构建隔离 | 低–中 | 高 |
| P2 | 供应商评估、安全元素 | 中 | 高 |
| P3 | 可重现构建、SLSA≥3 | 高 | 高 |
| P4 | 硬件入库深度检测 | 高 | 视威胁 |

## 7. 局限、挑战与可改进方向

### 1. SBOM 覆盖不全与"生成即过时"

**局限**：二进制第三方 blob、私有 SDK、运行时动态加载常不在 SBOM；一次生成后未随构建更新会误导响应。
**改进**：每次发布流水线强制产出并签名 SBOM；对闭源组件要求供应商附带组件清单；定期用实装扫描反证。

### 2. 硬件木马检测对中小 OEM 不现实

**局限**：去盖、侧信道金样对比成本高，中小厂商难独立完成。
**改进**：采购合同绑定可信代工与批次追溯；关键密钥路径用独立 SE；运行时行为基线作补偿控制。

### 3. SLSA 高等级与嵌入式工具链摩擦

**局限**：可重现构建在交叉编译、专有链接器、时间戳嵌入场景易失败；双人审核拖慢紧急补丁。
**改进**：先达到 L2/L3 可追溯；对引导与密码组件单独提高门禁；紧急补丁走加急双人+事后复盘。

### 4. 多级供应商透明度不足

**局限**：一级供应商不愿或不能披露晶圆厂/封测厂；地缘与合规要求冲突。
**改进**：分级披露（关键安全芯片强制、通用阻容宽松）；用 C-SCRM 评分驱动替代源；监控公开漏洞与仿冒预警。

## 参考文献

[1] NIST, "SP 800-161 Rev.1: Cybersecurity Supply Chain Risk Management Practices," 2022.
[2] CISA, "Defending Against Software Supply Chain Attacks," 2021.
[3] T. Herr et al., "Breaking Trust: Shades of Crisis Across an Insecure Software Supply Chain," Atlantic Council, 2020.
[4] SLSA, "Supply-chain Levels for Software Artifacts," https://slsa.dev/
[5] NTIA, "Minimum Elements for a Software Bill of Materials," 2021.
[6] M. Tehranipoor et al., *Counterfeit Integrated Circuits: Detection, Avoidance, and Tolerance*, Springer, 2023.
[7] in-toto, "A Framework for Supply Chain Integrity," https://in-toto.io/
[8] CycloneDX / SPDX, "SBOM Standards," 2024 相关文档.
[9] S. Peisert et al., "Perspectives on the SolarWinds Incident," IEEE Security & Privacy, 2021.
[10] L. Jia, "The XZ Utils Backdoor: Lessons for Open Source Security," IEEE Software, 2024.
[11] The Linux Foundation, "Open Source Software Supply Chain Security," 相关白皮书/报告, 2023–2024.
[12] NIST, "SSDF (SP 800-218): Secure Software Development Framework," 2022.
