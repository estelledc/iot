---
schema_version: '1.0'
id: iot-security-systematic-review
title: IoT安全系统性综述：威胁分类、攻击面与纵深防御
layer: 6
content_type: survey
difficulty: beginner
reading_time: 28
prerequisites: UNKNOWN
tags:
  - IoT安全
  - 威胁分类
  - 纵深防御
  - NIST
  - CRA
  - 攻击面
  - 综述
  - 零信任
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT安全系统性综述：威胁分类、攻击面与纵深防御

> **难度**：🟢 入门 | **领域**：物联网安全综述 | **阅读时间**：约 28 分钟

## 日常类比

智能音箱半夜突然自己出声——不是闹鬼，更像有人找到了门锁的备用钥匙（固件或云接口漏洞），远程让它播了一段音频。物联网（Internet of Things, IoT）安全事件往往如此：设备在你身边，攻击路径却在远方。

再比喻一层：传统电脑安全像给办公室装门禁与杀毒；IoT 更像同时要管门锁、电表、摄像头和工厂阀门——算力弱、难打补丁、生命周期长、还可能被物理碰到。

## 摘要

IoT 安全不是"加个密码"，而是从芯片到云的纵深防御（Defense-in-Depth）。本综述按物理/网络/数据/应用四层梳理攻击面与代表性案例，对照 NIST、ETSI、IEC、欧盟《网络弹性法案》（Cyber Resilience Act, CRA）等框架，并给出度量指标与局限[1][5][7]。设备保有量、漏洞占比、攻击峰值等数字来自行业报告，口径随样本变化，正文以量级表述并指向来源。

## 1. 规模与脆弱性（量级）

行业分析机构统计的全球联网 IoT 设备已达**百亿量级**并继续增长[3]。安全厂商报告常称过半抽检设备存在至少一个已知问题，具体比例依赖扫描范围与"漏洞"定义[2]。Mirai 及其变种证明：默认口令与暴露管理接口即可把摄像头/路由器编成分布式拒绝服务（Distributed Denial of Service, DDoS）武器；峰值流量随年份与观测点变化，公开报道已出现 Tbps 量级事件[4][8]。

## 2. 为什么 IoT 安全特别难？

| 维度 | 传统 IT | 物联网 |
|------|---------|--------|
| 算力 | 多核 GHz、内存充足 | 常为 Cortex-M 级、数十 KB 内存 |
| 更新 | 自动补丁常见 | 大量设备无可靠空中下载（Over-The-Air, OTA） |
| 寿命 | 数年换代 | 现场十余年常见 |
| 规模 | 千级端点 | 厂级可达十万传感器 |
| 物理可达 | 机房管控 | 户外/无人值守 |
| 异构性 | OS 种类有限 | 实时操作系统（Real-Time Operating System, RTOS）/裸机/裁剪 Linux 混杂 |
| 人因 | 有 IT 流程 | 消费者常不改默认密码 |

传统终端安全假设在此大量失效，需要分层重做[1]。

---

## 3. 威胁分类：四层攻击面

### 3.1 物理层

**侧信道（Side-Channel）**：功耗/电磁/时间泄漏可辅助恢复密钥；学术演示常用相对低成本采集链，具体曲线条数与成功率依实现与对策而定[1]。

**物理篡改**：联合测试行动组（Joint Test Action Group, JTAG）/串口拿到调试壳、读出固件。

**克隆**：复制身份凭证；物理不可克隆函数（Physical Unclonable Function, PUF）是硬件向缓解思路之一。

**故障注入**：电压毛刺/激光等跳过校验，风险是损坏器件。

### 3.2 网络层

**中间人（Man-in-the-Middle, MITM）**：未启用传输层安全（Transport Layer Security, TLS）的消息队列遥测传输（Message Queuing Telemetry Transport, MQTT）等协议暴露面大；互联网扫描引擎长期能发现大量开放代理，未加密占比随时间波动[2]。

**重放**：录制"开锁"再发送；需时间戳/计数器+消息认证码（Message Authentication Code, MAC）。

**DDoS**：IoT 僵尸网络仍是主要放大器之一[4][8]。

**选择性转发 / Sybil**：在无线传感与分布式信任场景中破坏路由或投票。

### 3.3 数据层

**窃取与画像**：设备使用习惯可推断在家/外出。

**流量侧信道**：即便不看载荷，元数据也可能高准确率推断设备类型与行为（具体准确率依设定，见相关研讨会论文）[1]。

**模型反演 / 梯度泄漏**：边缘人工智能（Artificial Intelligence, AI）与联邦学习场景的特有面，详见专题文。

### 3.4 应用层

**固件漏洞**：固件扫描报告常给出"平均每镜像数十个已知 CVE"量级，高危占比约一成上下，随语料变化[6]。

**应用编程接口（Application Programming Interface, API）滥用**：缺鉴权/缺限流可导致批量控设备。

**供应链**：第三方组件与构建链投毒（如影响广泛的开源维护事件）同样波及 IoT 镜像。

---

## 4. 纵深防御框架

| 防御层 | 技术手段（例） | 保护对象 | 约束 |
|--------|----------------|----------|------|
| 硬件 | PUF、可信执行环境（TEE）、安全启动、防篡改 | 身份与启动完整性 | 物料成本上升 |
| 固件 | 安全 OTA、签名、内存保护单元（MPU） | 运行完整性 | 需更新基础设施 |
| 通信 | TLS 1.3/DTLS、OSCORE、轻量密码 | 机密性/完整性 | 算力与电量 |
| 网络 | 零信任、微分段、IDS/IPS | 横向移动 | 网络改造 |
| 数据 | 差分隐私、联邦、同态（重） | 隐私 | 效用损失 |
| 应用 | API 网关、RBAC、审计 | 接口 | 云侧能力 |
| 管理 | 生命周期、软件物料清单（SBOM）、漏洞响应 | 态势 | 组织流程 |

NISTIR 8259 系列强调设备标识、安全默认配置、数据保护、逻辑访问、软件更新、安全状态上报等核心能力基线[5]。

---

## 5. 标准与监管对照

| 标准/框架 | 组织 | 覆盖 | 强制倾向 | IoT 针对性 |
|-----------|------|------|----------|-----------|
| NISTIR 8259 系列 | NIST | 设备能力基线 | 联邦采购等场景强相关 | 高 |
| ETSI EN 303 645 | ETSI | 消费 IoT | 与认证/市场准入联动 | 高 |
| IEC 62443 | IEC | 工业自动化控制 | 行业与合同常见 | 工业向 |
| ISO/IEC 27400 | ISO | IoT 安全与隐私 | 自愿为主 | 高 |
| OWASP IoT Top 10 | OWASP | 常见风险清单 | 自愿 | 中 |
| EU CRA | 欧盟 | 数字产品安全基线 | 强制（分阶段义务） | 含 IoT |
| 国标感知终端安全要求等 | 中国标准化 | 感知终端 | 视采用范围 | 高 |

后量子方面，NIST 已发布 ML-KEM/ML-DSA/SLH-DSA 等标准；公钥/签名体积对低带宽物联网仍是工程挑战[9]。

---

## 6. 事件年表（代表性，非穷尽）

| 年份 | 事件（公开） | 根因类型 |
|------|--------------|----------|
| 2020 | Ripple20 等 TCP/IP 栈问题 | 底层库缺陷传播 |
| 2021 | 摄像头云平台凭据类事件 | 硬编码/管理面弱点 |
| 2021 | NAME:WRECK 等 DNS 实现问题 | 协议栈实现缺陷 |
| 2022 | Industroyer2 等 | ICS 协议与流程弱点 |
| 2023+ | 供应链与文件传输软件连锁影响 | 零日/供应链 |
| 2024 | 大规模 IoT 放大 DDoS 报道 | 默认凭证+未修补 |
| 2024–2025 | 车联网/电表等行业通告 | API 或硬件假设失效 |

影响范围数字以监管与厂商通告为准，表中不绑定单一"受害台数"[2][4]。

---

## 7. 开源工具与度量

| 工具 | 用途 |
|------|------|
| EMBA / Firmwalker | 固件检查 |
| Ghidra | 逆向 |
| Shodan / Censys | 暴露面 |
| Zephyr + MCUboot / SUIT | 安全启动与更新 |
| MbedTLS / wolfSSL | 轻量 TLS |

常用度量：平均检测时间（Mean Time To Detect, MTTD）、平均修复时间（Mean Time To Repair, MTTR）、补丁覆盖率、暴露服务数。行业报告给出的 IoT MTTD 往往显著长于传统 IT，因更新与可见性差[2]。

---

## 8. 局限、挑战与可改进方向

### 1. 综述数字不可当验收指标

**局限**：设备总量、漏洞率、DDoS 峰值来自不同样本，媒体二次引用易夸大[2][3][4]。
**改进**：产品与项目以自有资产扫描、补丁率、暴露端口为 KPI；引用报告时保留年份与口径。

### 2. 纵深防御清单难以一次买齐

**局限**：MCU 成本、电量与认证周期限制 TEE/PUF/全量 OTA 同时落地。
**改进**：按暴露面分级（互联网可达 > 局域网 > 气隙）；先做身份、更新、安全默认三项基线[5]。

### 3. 标准多轨并行导致合规疲劳

**局限**：CRA、ETSI、IEC、国标要求重叠但证据形式不同[7]。
**改进**：建控制映射矩阵（一份控制多项标准）；SBOM 与漏洞响应流程优先自动化。

### 4. IT 方案硬搬 IoT

**局限**：代理杀毒、频繁全量扫描在 RTOS 上不可行。
**改进**：网关侧检测 + 设备轻量能力；网络微分段补偿终端弱性。

### 5. 人因与默认配置

**局限**：默认密码与开放调试口仍反复出现在事件通告中[8]。
**改进**：出厂唯一凭证、强制首次轮换、生产熔断调试；纳入 CRA/ETSI 测试用例。

---

## 参考文献

[1] W. U. Hassan et al., "A Taxonomy of Attacks and Defenses in IoT Ecosystems: A Systematic Survey," ACM Computing Surveys, 2024.
[2] Palo Alto Networks Unit 42, "IoT/OT Threat Report," 2024.
[3] IoT Analytics, "State of IoT" 设备数量相关发布, 2024.
[4] Cloudflare, "DDoS Threat Report," 2024.
[5] NIST, "NISTIR 8259: IoT Device Cybersecurity Capability Core Baseline," 修订版 2024.
[6] Finite State, "The State of IoT/Connected Device Security," 2024.
[7] European Union, "Cyber Resilience Act (CRA)," Official Journal, 2024.
[8] M. Antonakakis et al., "Understanding the Mirai Botnet," USENIX Security, 2017.
[9] NIST, "FIPS 203/204/205" 后量子标准 (ML-KEM, ML-DSA, SLH-DSA), 2024.
[10] E. Bertino and N. Islam, "Botnets and Internet of Things Security," IEEE Computer, 2017/相关讨论更新.
[11] ETSI, "EN 303 645: Cyber Security for Consumer Internet of Things," 近年版本.
[12] IEC, "IEC 62443" 工业自动化与控制系统安全系列.
[13] ISO/IEC 27400:2022, "Cybersecurity — IoT security and privacy — Guidelines."
[14] OWASP, "OWASP IoT Top 10," 近年版本.
[15] NIST, "NIST SP 800-213 / 相关 IoT 网络安全指南," 近年修订.
[16] ENISA, IoT 安全基线与威胁全景相关报告, 近年.
