---
schema_version: '1.0'
id: zero-trust-iot
title: 零信任架构与IoT：从"城堡护城河"到"永不信任"
layer: 6
content_type: technical_analysis
difficulty: advanced
reading_time: 24
prerequisites:
  - compliance-framework-nist-etsi
  - intrusion-detection-edge
  - sbom-software-supply-chain
tags:
- 零信任
- ZTA
- 微分段
- MUD
- NIST-800-207
- 持续认证
- PEP-PDP
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 零信任架构与IoT：从"城堡护城河"到"永不信任"

> **难度**：🟡 进阶 | **领域**：网络安全架构 | **关键词**：ZTA, PDP, PEP, MUD, 微分段 | **阅读时间**：约 24 分钟

## 日常类比

传统网络安全像城堡：一道城墙（防火墙）隔开内外，进城后彼此默认信任。一旦有人混进城门，便可横向穿行。零信任（Zero Trust）则是每个房间独立上锁：每次进入都要验身份、只开最小权限房间。对物联网（Internet of Things, IoT）尤其关键——被攻破的智能灯泡不应能触达工业控制器[1][5]。

公开行业报告常称横向移动出现在多数严重泄露中；具体百分比随样本与定义变化，本文不绑定单一统计。

## 摘要

本文基于 NIST SP 800-207 零信任架构（Zero Trust Architecture, ZTA）原则，说明策略决策点（Policy Decision Point, PDP）与策略执行点（Policy Enforcement Point, PEP）在 IoT 中的落位，覆盖信任评分、微分段、制造商使用描述（Manufacturer Usage Description, MUD, RFC 8520）、持续认证与开源组件。规模化延迟数字为示意量级，需用自有策略引擎压测。

## 1. 零信任核心原则（IoT 映射）

| 原则（NIST SP 800-207） | IoT 映射 |
|-------------------------|----------|
| 数据源与计算服务皆为资源 | 传感器/执行器/网关均编目 |
| 通信不论位置皆需保护 | 内网亦加密认证，禁默认可信 |
| 按会话授予访问 | 禁止"一次认证永久通行" |
| 动态属性驱动策略 | 固件版本、补丁、行为、环境 |
| 资产保持安全态势 | 完整性与健康度持续监测 |
| 访问前严格认证授权 | 每次发布/订阅独立评估 |
| 尽量采集信号优化安全 | 行为基线 + 威胁情报[1][2] |

## 2. 逻辑组件

```
IoT 主体 ──请求──▶ PEP（网关/代理）──策略查询──▶ PDP（策略引擎）
                      │                              │
                   放行/拒绝                    CMDB / PKI / 威胁情报 / 行为基线
                      ▼
                  受保护资源
```

资源受限终端往往跑不动完整 PEP，执行点上移到网关、交换机或服务网格旁路；设备侧保留双向传输层安全（mutual Transport Layer Security, mTLS）或轻量令牌即可。

## 3. 信任评估（示意权重）

| 因素 | 权重示意 | 来源 | 更新 |
|------|----------|------|------|
| 身份强度 | 约四分之一 | 证书/PUF/Token | 注册与续期 |
| 固件状态 | 约五分之一 | 安全启动报告 | 启动时 |
| 行为偏离 | 约五分之一 | 流量/模型 | 近实时 |
| 漏洞暴露 | 约一成五 | CVE + SBOM | 日级 |
| 网络环境 | 约一成 | 网监 | 近实时 |
| 历史信誉 | 约一成 | 审计 | 累积 |

权重须按行业标定；示例"摄像头总分 70、阈值 60 则限速放行"仅说明策略形态，不是通用公式。

## 4. IT ZTA vs IoT ZTA

| 维度 | 传统 IT | IoT |
|------|---------|-----|
| 端点能力 | 可装 agent | 常无法跑客户端 |
| 协议 | HTTP/TLS 为主 | MQTT/CoAP/Modbus 等 |
| 认证 | 人机 MFA | 证书/Token/PUF |
| 补丁 | 相对频繁 | 长生命周期、难更新 |
| 规模 | 千–万 | 可达十万–百万 |
| 行为 | 多变 | 相对可预测 |
| 分段 | VLAN/SDN 成熟 | 需适配无线/LPWAN |

适配要点：代理式 ZTA、行为基线、按设备类型微分段。

## 5. 微分段与 MUD

| 技术 | 粒度 | 动态性 | 适用 |
|------|------|--------|------|
| VLAN | 子网 | 低 | 小规模 |
| SDN | 流 | 高 | 中规模 |
| 身份感知代理 | 设备 | 高 | 大规模 |
| eBPF/Cilium | 工作负载 | 很高 | 云边容器 |
| MUD | 设备类型 | 中 | IoT 原生[3] |

MUD 让制造商声明"灯泡只应与控制器、特定端口通信"；控制器据此自动下发允许列表，超出即拒——即便终端沦陷也难扫网或打外部目标[3][10]。声明不完整或被恶意厂商滥用时，需运营方覆盖策略兜底。

## 6. 持续认证

| 方案 | 频率倾向 | 开销 | 能力 |
|------|----------|------|------|
| 短周期重认证 | 小时–天 | 低 | 凭证失效 |
| 心跳+证明 | 分钟级 | 低 | 固件完整性 |
| 流量指纹 | 近实时 | 中 | 类型冒充 |
| RF 指纹 | 近实时 | 中 | 物理替换 |
| 行为分析 | 近实时 | 中高 | 异常用途 |

设备类型识别在研究中可达到较高准确率，但依赖数据集与特征；工程上应把"偏离基线"当作降权/隔离信号，而非唯一判决[7]。

## 7. 平台与部署

| 项目 | 类型 | IoT 相关能力 |
|------|------|-------------|
| OpenZiti | 覆盖网络 | SDK 可嵌入 |
| Tailscale/Headscale | WireGuard 网格 | 有限 |
| Istio | 服务网格 | 边缘网关 mTLS/RBAC |
| Cilium | eBPF | 身份感知策略 |
| SPIFFE/SPIRE | 身份 | 工作负载身份 |
| MUD Manager | MUD | 制造商描述执行 |

入网示意：证书认证 → 加载 MUD → 下发分段 → 基线学习窗口 → 持续监控。Google BeyondCorp、DoD 零信任参考与工业现场改造等公开材料提供组织级经验，但战术断连、OT 协议与安全仪表要求需单独设计[4][6][8][9]。

| 设备规模量级 | 策略规模量级 | PDP 延迟倾向 |
|-------------|-------------|-------------|
| 千 | 数百规则 | 毫秒级 |
| 万 | 数千 | 数毫秒 |
| 十万–百万 | 万级 | 需本地缓存/分级 PDP |

大规模下常见优化：边缘缓存允许决策、仅复杂/异常上送全局 PDP。

## 8. 局限、挑战与可改进方向

### 1. 遗留 OT/IoT 无法终结点强化

**局限**：老旧 PLC、无证书传感器无法 mTLS；若强行替换成本不可接受。
**改进**：网关终止安全会话并做协议允许列表；网络层 MUD/VLAN 补偿；淘汰计划与风险登记绑定。

### 2. 策略爆炸与误阻断

**局限**：每设备细策略导致变更恐惧；误阻断可能停产或影响安全相关控制。
**改进**：按设备类型模板+例外；变更金丝雀；对安全仪表链路提供只读监测旁路与人工覆盖审计。

### 3. PDP 可用性成为新单点

**局限**：PDP 故障可能导致"全拒绝"或错误"全放行"。
**改进**：定义失败模式（fail-closed vs 降级允许列表）；本地缓存短 TTL；多活 PDP 与演练。

### 4. 行为基线在固件更新后漂移

**局限**：合法 OTA 后流量模式变化会触发误报；攻击者也可慢漂逃避。
**改进**：更新事件与基线重置联动；双阈值（告警/隔离）；结合 SBOM 与证明，而非单靠流量[7][10]。

## 参考文献

[1] NIST, "SP 800-207: Zero Trust Architecture," 2020 (updates through mid-2020s as applicable).
[2] S. Rose et al., "Zero Trust Architecture," NIST Special Publication, 2020.
[3] E. Lear et al., "Manufacturer Usage Description Specification," RFC 8520, IETF, 2019.
[4] Google, "BeyondCorp: A New Approach to Enterprise Security," USENIX ;login:, 2014.
[5] J. Kindervag et al., related Zero Trust network concepts / O'Reilly *Zero Trust Networks*, 2017.
[6] U.S. Department of Defense, "DoD Zero Trust Reference Architecture," v2.0, 2024.
[7] R. Meier et al., "IoT Zero Trust: Challenges and Solutions for Constrained Environments," IEEE IoT Journal, 2024.
[8] D. Ferraiolo et al., "Implementing a Zero Trust Architecture," NIST SP 1800-35, 2024.
[9] CISA, "Zero Trust Maturity Model v2.0," 2024.
[10] A. Hamza et al., "MUD-based Network Segmentation for IoT: Effectiveness and Scalability," IEEE TNSM, 2024.
[11] NIST, "SP 800-207A: A Zero Trust Architecture Model for Access Control in Cloud-Native Applications in Multi-Location Environments," 相关文本.
[12] NSA / CISA, "Zero Trust security guidance for network infrastructure / identity," 近年联合或各自公开材料.
