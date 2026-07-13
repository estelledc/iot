---
schema_version: '1.0'
id: sbom-software-supply-chain
title: SBOM 软件物料清单在 IoT 中的实践
layer: 6
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - supply-chain-security-iot
  - firmware-security
tags:
- SBOM
- 软件物料清单
- SPDX
- CycloneDX
- 供应链安全
- VEX
- 合规
- 固件
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# SBOM 软件物料清单在 IoT 中的实践

> **难度**：🟡 中级 | **领域**：供应链安全、合规 | **阅读时间**：约 18 分钟

## 日常类比

超市薯片包装背面有“配料表”：出了问题的植物油批次，厂家能定位受影响产品并召回。

软件物料清单（Software Bill of Materials, SBOM）就是软件的配料表。物联网（Internet of Things, IoT）固件可能含内核、OpenSSL、busybox、自研代码等数十个组件。当某库爆出高危漏洞时，有 SBOM 的厂商能较快圈定受影响机型；没有的，可能长期说不清。[1][5]

## 1. SBOM 基础

### 1.1 是什么

结构化清单，记录产品中的组件、版本、供应商、标识符、许可证、依赖关系与完整性哈希等。

```
固件 v2.3.1
├── Linux Kernel x.y.z
├── OpenSSL a.b.c
├── busybox ...
├── FreeRTOS / lwIP ...
└── 自研 device-agent / sensor-driver
```

### 1.2 核心字段（NTIA 最低要素方向）

组件名与版本、供应商、唯一标识（CPE / PURL）、依赖关系、SBOM 作者与时间戳等。[1] 实践中还应补许可证、哈希、生成阶段（源码/构建/运行时）。

### 1.3 为何 IoT 更痛

| 挑战 | 说明 |
|------|------|
| 长生命周期 | 设备可服役十余年，漏洞窗口长 |
| 更新困难 | 无 OTA 或 OTA 率低，需精确影响面 |
| 供应链深 | 芯片 SDK + RTOS + 中间件 + 应用 |
| 合规加压 | 政府采购与 CRA 等要求透明性 |

## 2. SPDX vs CycloneDX

### 2.1 SPDX

Linux Foundation 维护，ISO/IEC 5962 国际标准方向，擅长许可证与包关系表达。[2]

### 2.2 CycloneDX

OWASP 维护，更偏安全与漏洞工作流，原生可携带漏洞与分析状态。[3]

### 2.3 格式对比

| 维度 | SPDX | CycloneDX |
|------|------|-----------|
| 标准化 | ISO 路线成熟 | OWASP / ECMA 生态 |
| 侧重点 | 许可证合规 | 安全漏洞运营 |
| 常见格式 | JSON / RDF / Tag-Value | JSON / XML / Protobuf |
| 漏洞集成 | 多靠外部工具 | 规格内支持更直接 |
| 固件建模 | 可用 | firmware 等类型友好 |
| 工具生态 | 成熟 | 增长快 |

IoT 团队常：**构建系统出 SPDX，安全运营用 CycloneDX**，或双向转换。[5][6][7]

## 3. 漏洞追踪与 VEX

### 3.1 工作流

组件披露 → CVE / OSV 等编号 → 用 SBOM 匹配资产 → 影响评估 → 修复或缓解 → 更新 SBOM / 发布 VEX。

### 3.2 VEX（Vulnerability Exploitability eXchange）

声明某漏洞对**本产品**是否真正可利用，避免“SBOM 命中即恐慌”。状态通常包括：`not_affected`、`affected`、`fixed`、`under_investigation`，并附理由（如代码路径未启用）。[5]

### 3.3 自动化匹配（示意）

用 PURL/CPE 查 OSV 等数据库；结果必须人工或规则引擎做可达性分析，不能只报 CVE 列表。

## 4. 生成与扫描工具

| 工具 | 类型 | 输入 | 输出 | IoT 适用性 |
|------|------|------|------|-----------|
| Syft | 清单生成 | 镜像/目录/文件 | SPDX, CycloneDX | 中（偏文件系统） |
| Trivy | 扫描+清单 | 镜像/FS/SBOM | 多种 | 高 |
| Yocto/bitbake | 构建集成 | Recipe | SPDX | 高 |
| Zephyr/west | RTOS 构建 | 依赖图 | SPDX 等 | 高 |
| 商业 SCA | 源码治理 | 仓库 | SPDX 等 | 中 |

**推荐**：在**构建时**生成 SBOM（Yocto、CMake 组件登记），二进制事后逆向只作补洞，不作为唯一真相源。[9]

## 5. 嵌入式固件的特殊性

- 常无包管理器元数据
- 静态链接模糊组件边界
- 芯片厂 SDK 往往不附 SBOM
- 专有 blob 难命名版本

可用 binwalk / strings / FACT 等辅助识别，但误报漏报常见，需与构建清单交叉验证。[8]

| 方法 | 优点 | 缺点 |
|------|------|------|
| 构建时生成 | 准确、可重复 | 要改流水线 |
| 文件系统扫描 | 快 | 缺静态链接细节 |
| 二进制指纹 | 可审计存量固件 | 噪声大、版本难定 |
| 供应商提供 | 覆盖 SDK | 合同与质量参差 |

## 6. 法规要点（勿当法律意见）

**美国 EO 14028 相关实践**：向联邦销售的软件常被要求提供机器可读 SBOM，并覆盖传递依赖、持续更新。[1][5]

**欧盟网络弹性法案（Cyber Resilience Act, CRA）**：对含数字元素的产品提出网络安全与漏洞处理义务，SBOM 与披露时限是讨论焦点；罚款上限以官方法规文本为准，工程上应按法务解读落地。[4]

**自检（NTIA 最低要素）**：供应商名、组件名、版本、唯一标识、依赖关系、SBOM 作者、时间戳；并建议补许可证与哈希。[1]

## 7. 局限、挑战与可改进方向

### 1. 静态链接与 SDK 黑洞

**局限**：事后扫描看不到编译进固件的库版本，芯片 SDK 无清单。[8][9]
**改进**：构建系统强制登记第三方；采购合同要求 SDK SBOM；对 blob 做哈希台账。

### 2. “有 CVE 命中 ≠ 真受影响”

**局限**：仅 SBOM 匹配制造告警疲劳，运营不可持续。[3][5]
**改进**：强制 VEX/可达性分析；按 CVSS×暴露面×资产关键级分流。

### 3. SBOM 本身被投毒或过期

**局限**：错误或过时清单比没有更危险（虚假安全感）。
**改进**：SBOM 签名与在线完整性；与构建产物同版本发布；抽检二进制对照。

### 4. 格式与工具碎片化

**局限**：SPDX/CycloneDX 版本、字段方言导致客户拒收。[2][3]
**改进**：对内选一种主格式，对外提供转换；锁定规格小版本与验证器。

### 5. 长尾设备无法 OTA

**局限**：已识别漏洞却无法修复，合规与风险并存。[4]
**改进**：网络隔离与虚拟补丁；明确支持周期；召回/置换策略写进产品政策。

## 8. 实践建议（简）

1. 先让 CI 每次构建产出已签名 SBOM。
2. Trivy/OSV 每日扫存量清单，输出带 VEX 的工单。
3. 要求一级供应商交付其组件 SBOM，否则视为残缺物料。

## 参考文献

[1] NTIA, "The Minimum Elements For a Software Bill of Materials (SBOM)," 2021.
[2] Linux Foundation, "SPDX Specification v2.3," 2023.
[3] OWASP, "CycloneDX Specification v1.5," 2024.
[4] European Commission, "Cyber Resilience Act (EU CRA)," Official Journal, 2024.
[5] CISA, "SBOM Sharing Roles and Considerations," 2024.
[6] Anchore, "Syft: A CLI Tool for Generating SBOMs," GitHub / docs, 2024.
[7] Aqua Security, "Trivy: Comprehensive Security Scanner," Documentation, 2024.
[8] K. Stewart et al., "Software Transparency: Supply Chain Security for IoT," IEEE S&P Workshop, 2023.
[9] Yocto Project, "Creating SPDX SBOMs with Yocto," Documentation, 2024.
[10] NIST, "SP 800-218: Secure Software Development Framework," 2022.
[11] NVD/OSV, "Vulnerability databases for component matching," ongoing.
[12] CISA, "Vulnerability Exploitability eXchange (VEX) documents," guidance, 2023–2024.
