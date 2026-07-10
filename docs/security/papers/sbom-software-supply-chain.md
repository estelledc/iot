---
schema_version: '1.0'
id: sbom-software-supply-chain
title: SBOM 软件物料清单在 IoT 中的实践
layer: 6
content_type: UNKNOWN
difficulty: intermediate
reading_time: 17
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# SBOM 软件物料清单在 IoT 中的实践

> **难度**：🟡 中级 | **领域**：供应链安全、合规 | **阅读时间**：约 17 分钟

## 日常类比

去超市买一包薯片，包装背面有"配料表"：马铃薯粉 60%、植物油 25%、食盐 3%……你能清楚知道吃进去的是什么。如果某批次植物油被检出问题，厂家能立刻定位哪些产品受影响并召回。

SBOM（Software Bill of Materials，软件物料清单）就是软件的"配料表"。一个 IoT 设备的固件可能包含 Linux 内核、OpenSSL、busybox、自研业务代码等几十个组件。当 OpenSSL 爆出 Heartbleed 这样的漏洞时，有 SBOM 的厂商能在几小时内确认哪些设备受影响；没有 SBOM 的厂商可能几周都搞不清楚。

## 1. SBOM 基础概念

### 1.1 什么是 SBOM

SBOM 是一份结构化的清单，记录软件产品中包含的所有组件及其关系：

```
固件 v2.3.1
├── Linux Kernel 5.15.120 (GPL-2.0)
├── OpenSSL 3.2.1 (Apache-2.0)
├── busybox 1.36.1 (GPL-2.0)
├── libcurl 8.5.0 (MIT)
├── zlib 1.3.1 (Zlib)
├── FreeRTOS 10.6.1 (MIT)
├── lwIP 2.2.0 (BSD-3-Clause)
└── 自研代码 (Proprietary)
    ├── device-agent 1.0.3
    └── sensor-driver 2.1.0
```

### 1.2 SBOM 的核心字段

每个组件条目应包含：
- 组件名称和版本
- 供应商/作者
- 唯一标识符（CPE、PURL）
- 许可证信息
- 依赖关系
- 哈希值（完整性校验）

### 1.3 为什么 IoT 特别需要 SBOM

| 挑战 | 说明 |
|------|------|
| 长生命周期 | 设备运行 10-20 年，组件漏洞持续暴露 |
| 更新困难 | 很多设备无法 OTA，需要精确评估影响 |
| 供应链复杂 | 芯片厂 SDK + RTOS + 中间件 + 应用层 |
| 合规要求 | 各国法规逐步强制要求 SBOM |

## 2. SPDX vs CycloneDX 格式

### 2.1 SPDX（Software Package Data Exchange）

由 Linux Foundation 维护，ISO/IEC 5962:2021 国际标准：

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "iot-gateway-firmware",
  "documentNamespace": "https://example.com/sbom/gateway-v2.3.1",
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-OpenSSL",
      "name": "openssl",
      "versionInfo": "3.2.1",
      "supplier": "Organization: OpenSSL Software Foundation",
      "downloadLocation": "https://www.openssl.org/source/openssl-3.2.1.tar.gz",
      "licenseConcluded": "Apache-2.0",
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "83c7329fe52c850677d75e5d0b0ca245..."
        }
      ],
      "externalRefs": [
        {
          "referenceCategory": "SECURITY",
          "referenceType": "cpe23Type",
          "referenceLocator": "cpe:2.3:a:openssl:openssl:3.2.1:*:*:*:*:*:*:*"
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-OpenSSL"
    }
  ]
}
```

### 2.2 CycloneDX

由 OWASP 维护，更侧重安全和漏洞管理：

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "component": {
      "type": "firmware",
      "name": "iot-gateway",
      "version": "2.3.1"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "openssl",
      "version": "3.2.1",
      "purl": "pkg:generic/openssl@3.2.1",
      "licenses": [{"license": {"id": "Apache-2.0"}}],
      "hashes": [
        {"alg": "SHA-256", "content": "83c7329fe52c..."}
      ]
    },
    {
      "type": "library",
      "name": "freertos",
      "version": "10.6.1",
      "purl": "pkg:generic/freertos@10.6.1"
    }
  ],
  "vulnerabilities": [
    {
      "id": "CVE-2024-0727",
      "source": {"name": "NVD"},
      "ratings": [{"severity": "medium", "score": 5.5}],
      "affects": [{"ref": "openssl@3.2.1"}],
      "analysis": {"state": "not_affected", "justification": "code_not_reachable"}
    }
  ]
}
```

### 2.3 格式对比

| 维度 | SPDX | CycloneDX |
|------|------|-----------|
| 标准化 | ISO 国际标准 | OWASP/ECMA |
| 侧重点 | 许可证合规 | 安全漏洞 |
| 格式 | JSON/RDF/Tag-Value | JSON/XML/Protobuf |
| 漏洞集成 | 需外部工具 | 原生支持 |
| IoT 适用性 | 好 | 更好（firmware type） |
| 工具生态 | 成熟 | 快速增长 |

## 3. 漏洞追踪

### 3.1 CVE/NVD 工作流

```
组件发现漏洞 → CVE 编号分配 → NVD 评分(CVSS)
                                    ↓
SBOM 匹配 → 影响评估 → 修复/缓解 → 更新 SBOM
```

### 3.2 VEX（Vulnerability Exploitability eXchange）

VEX 声明某个漏洞对特定产品是否真正有影响：

```json
{
  "vulnerability": "CVE-2024-0727",
  "product": "iot-gateway-v2.3.1",
  "status": "not_affected",
  "justification": "vulnerable_code_not_in_execute_path",
  "detail": "OpenSSL PKCS12 解析功能未在本固件中启用"
}
```

状态选项：
- `not_affected`：不受影响（附理由）
- `affected`：受影响，需修复
- `fixed`：已修复
- `under_investigation`：调查中

### 3.3 自动化漏洞匹配

```python
# 使用 SBOM 进行漏洞匹配的简化示例
import requests
import json

def check_vulnerabilities(sbom_path):
    with open(sbom_path) as f:
        sbom = json.load(f)
    
    results = []
    for component in sbom['components']:
        # 构造 CPE 或 PURL 查询
        purl = component.get('purl', '')
        
        # 查询 OSV (Open Source Vulnerabilities) API
        response = requests.post(
            'https://api.osv.dev/v1/query',
            json={'package': {'purl': purl}}
        )
        
        vulns = response.json().get('vulns', [])
        if vulns:
            results.append({
                'component': component['name'],
                'version': component['version'],
                'vulnerabilities': [v['id'] for v in vulns]
            })
    
    return results
```

## 4. SBOM 生成工具

### 4.1 工具对比

| 工具 | 类型 | 输入 | 输出格式 | IoT 适用性 |
|------|------|------|---------|-----------|
| Syft | 容器/文件系统扫描 | 镜像/目录 | SPDX, CycloneDX | 中 |
| Trivy | 综合扫描器 | 镜像/代码/二进制 | SPDX, CycloneDX | 高 |
| FOSSA | 商业 SCA | 源码 | SPDX | 中 |
| Yocto/bitbake | 构建系统集成 | Recipe | SPDX | 高 |
| west + Zephyr | RTOS 构建 | Kconfig | SPDX | 高 |

### 4.2 使用 Syft 生成 SBOM

```bash
# 扫描固件文件系统目录
syft dir:./firmware-rootfs -o cyclonedx-json > sbom.json

# 扫描 Docker 镜像（用于网关类设备）
syft registry:mycompany/iot-gateway:v2.3.1 -o spdx-json > sbom-spdx.json

# 扫描二进制文件（提取编译信息）
syft file:./firmware.bin -o cyclonedx-json > sbom-binary.json
```

### 4.3 使用 Trivy 扫描漏洞

```bash
# 基于 SBOM 扫描漏洞
trivy sbom sbom.json --severity HIGH,CRITICAL

# 直接扫描固件文件系统
trivy fs ./firmware-rootfs --format cyclonedx --output sbom-with-vulns.json

# 输出示例
# openssl (3.2.1)
# ===============
# Total: 2 (HIGH: 1, CRITICAL: 1)
# ┌──────────────────┬────────────────┬──────────┐
# │ Vulnerability    │ Severity       │ Fixed In │
# ├──────────────────┼────────────────┼──────────┤
# │ CVE-2024-XXXX    │ CRITICAL       │ 3.2.2    │
# │ CVE-2024-YYYY    │ HIGH           │ 3.2.2    │
# └──────────────────┴────────────────┴──────────┘
```

## 5. 固件组成分析

### 5.1 嵌入式固件的特殊性

嵌入式固件的 SBOM 生成比服务器软件更复杂：

- 没有包管理器（无 apt/npm/pip 记录）
- 组件可能以源码形式编译进二进制
- 芯片厂 SDK 通常不提供 SBOM
- 静态链接使得组件边界模糊

### 5.2 二进制分析方法

```bash
# 使用 binwalk 提取固件组件
binwalk -e firmware.bin

# 使用 strings 识别版本信息
strings firmware.bin | grep -E "(version|OpenSSL|libcurl)"

# 使用 FACT (Firmware Analysis and Comparison Tool)
# 自动识别已知库的版本
fact_extractor firmware.bin --output-dir ./analysis/
```

### 5.3 构建时 SBOM 生成（推荐）

```cmake
# CMakeLists.txt 中集成 SBOM 生成
# 在构建时记录所有依赖版本

set(SBOM_COMPONENTS "")

# 记录每个第三方库
function(add_sbom_component name version license)
    list(APPEND SBOM_COMPONENTS 
         "{\"name\":\"${name}\",\"version\":\"${version}\",\"license\":\"${license}\"}")
    set(SBOM_COMPONENTS ${SBOM_COMPONENTS} PARENT_SCOPE)
endfunction()

add_sbom_component("freertos" "10.6.1" "MIT")
add_sbom_component("lwip" "2.2.0" "BSD-3-Clause")
add_sbom_component("mbedtls" "3.5.2" "Apache-2.0")

# 构建完成后生成 SBOM 文件
configure_file(sbom-template.json.in ${CMAKE_BINARY_DIR}/sbom.json)
```

## 6. 法规要求

### 6.1 美国行政令 EO 14028

2021 年发布，要求：
- 向联邦政府销售软件必须提供 SBOM
- SBOM 必须机器可读（SPDX 或 CycloneDX）
- 必须包含直接和传递依赖
- 需要持续更新（不是一次性的）

### 6.2 欧盟网络弹性法案（EU CRA）

2024 年正式通过，2027 年全面生效：
- 所有含数字元素的产品必须提供 SBOM
- 已知漏洞必须在 24 小时内报告
- 产品生命周期内持续提供安全更新
- 违规罚款最高 1500 万欧元或全球营收 2.5%

### 6.3 合规检查清单

```yaml
# SBOM 合规自检（基于 NTIA 最低要素）
compliance_check:
  supplier_name: true        # 组件供应商名称
  component_name: true       # 组件名称
  version: true              # 版本号
  unique_identifier: true    # CPE/PURL
  dependency_relationship: true  # 依赖关系
  author_of_sbom: true       # SBOM 作者
  timestamp: true            # 生成时间�  
  
  # 额外推荐
  license_info: true         # 许可证
  hash_values: true          # 完整性哈希
  lifecycle_phase: "build"   # 生成阶段
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 用 Syft 扫描一个 Docker 镜像，理解 SBOM 结构
2. 用 Trivy 对生成的 SBOM 做漏洞扫描
3. 手动为一个小型嵌入式项目编写 CycloneDX SBOM
4. 在 CI/CD 中集成自动 SBOM 生成
5. 建立漏洞响应流程（SBOM → 匹配 → VEX → 修复）

### 7.2 具体调优建议

**构建系统集成**：
- Yocto/Buildroot 项目：使用内置 SPDX 生成功能
- Zephyr RTOS：利用 west 工具链的依赖追踪
- 裸机项目：在 CMake/Makefile 中手动维护组件清单

**持续监控**：
- 将 SBOM 存入版本控制，每次构建更新
- 配置 Dependabot/Renovate 监控上游更新
- 订阅关键组件的安全公告邮件列表

**供应商管理**：
- 要求芯片厂/SDK 供应商提供其组件的 SBOM
- 合同中明确 SBOM 交付要求
- 建立供应商安全评估流程

## 参考文献

1. NTIA. "The Minimum Elements For a Software Bill of Materials (SBOM)." 2021.
2. Linux Foundation. "SPDX Specification v2.3." 2023.
3. OWASP. "CycloneDX Specification v1.5." 2024.
4. European Commission. "Cyber Resilience Act (EU CRA)." Official Journal, 2024.
5. CISA. "SBOM Sharing Roles and Considerations." 2024.
6. Anchore. "Syft: A CLI Tool for Generating SBOMs." GitHub, 2024.
7. Aqua Security. "Trivy: Comprehensive Security Scanner." Documentation, 2024.
8. Stewart, K. et al. "Software Transparency: Supply Chain Security for IoT." IEEE S&P Workshop, 2023.
9. Yocto Project. "Creating SPDX SBOMs with Yocto." Documentation, 2024.
10. NIST. "SP 800-218: Secure Software Development Framework." 2022.
