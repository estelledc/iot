# IoT Reading Station — 从零到无穷 · 项目路线图

> 目标：建成一个覆盖物联网全栈技术的中文学习站，从硬件入门到前沿研究，任何人都能找到自己的起点并持续深入。

---

## 一、项目愿景

**一句话**：IoT 领域的 csdiy.wiki —— 结构化、可导航、持续生长的中文物联网知识站。

**设计原则**：

- 全面 > 深度（先铺开 8 层技术栈，再逐层深钻）
- 中文重写 > 翻译（零基础也能读懂，参考 Embodied AI Reading Station 风格）
- 源真相是 Markdown，网站是衍生物
- 每篇内容自带元数据（标签、难度、前置知识、关联内容）
- 持续生长：每周可增量添加新论文/新主题

<!-- content-inventory:start -->
### 当前内容基线（自动派生）

| 层级 | 方向 | 内容文件 | 显式导航 | 目录页入口 | 可发现 | 层级首页入口 | Plan 条目 | 目标容量 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Layer 1 | 感知与硬件 | 275 | 25 | 275 | 275 | 10 | 250 | 275 |
| Layer 2 | 无线接入 | 219 | 25 | 219 | 219 | 10 | 191 | 219 |
| Layer 3 | 网络协议 | 25 | 25 | 25 | 25 | 10 | 179 | 204 |
| Layer 4 | 计算平台 | 25 | 25 | 25 | 25 | 10 | 190 | 215 |
| Layer 5 | 边缘智能 | 26 | 25 | 26 | 26 | 10 | 301 | 326 |
| Layer 6 | 安全与隐私 | 26 | 25 | 26 | 26 | 10 | 197 | 222 |
| Layer 7 | 综合应用 | 26 | 25 | 26 | 26 | 10 | 205 | 230 |
| Layer 8 | 前沿方向 | 25 | 25 | 25 | 25 | 10 | 248 | 273 |
| **合计** | | **647** | **200** | **647** | **647** | **80** | **1761** | **1964** |

> “内容文件”只表示 Markdown 存在；“可发现”= 显式导航 ∪ 层级 catalog。当前有 **642** 条 current valid `STRUCTURAL` 结构审计记录；事实核验：**642** 篇。`STRUCTURAL` 不提升 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。继续扩展 Layer 3–8 前，先完成事实核验、来源抽样和可重复生产门禁。
<!-- content-inventory:end -->

---

## 二、内容架构：IoT 8 层技术栈

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 8: 前沿方向 (Frontier)                                │
│  数字孪生 · 6G ISAC · RIS · 语义通信 · 边缘原生 · Wasm      │
├─────────────────────────────────────────────────────────────┤
│  Layer 7: 综合应用 (Applications)                            │
│  智慧城市 · 自动驾驶 · IIoT · 医疗 · 智能家居 · 室内定位     │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: 安全与隐私 (Security & Privacy)                    │
│  威胁分类 · TEE · 联邦学习 · 差分隐私 · 零信任 · 区块链      │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: 边缘智能 (Edge Intelligence)                       │
│  TinyML · 模型压缩 · 协作推理 · 联邦学习 · LLM on Edge      │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: 计算平台 (Computing)                               │
│  云平台 · 边缘计算 · 雾计算 · MEC · Serverless · 开源框架    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 网络协议 (Networking)                              │
│  WSN MAC/路由 · MQTT/CoAP/LwM2M · TSN/DetNet · 时间同步     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 无线接入 (Connectivity)                            │
│  BLE · WiFi 6/7 · ZigBee · UWB · 星闪 · LoRaWAN · NB-IoT   │
│  LTE-M · 5G mMTC/URLLC · RedCap · 卫星 IoT                  │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 感知与硬件 (Sensing & Hardware)                    │
│  传感器 · Arduino/ESP32/RPi · RTOS · RFID · 嵌入式基础      │
└─────────────────────────────────────────────────────────────┘
```

每层包含：

- **概览页**（index.md）：该层的技术地图、核心概念、学习路径
- **论文阅读报告**（papers/）：精选论文的深度阅读笔记
- **综述/对比**（surveys/）：自写综述或技术对比分析
- **入门指南**（guides/）：零基础友好的概念讲解（可选，按需补充）

---

## 三、未来方向：四个里程碑

> 主线：**先可信，再可发现，后受控生长，最后体验与社区**。里程碑用可机械验证的完成判据界定，不用日历时间界定；前一个里程碑的判据是后一个的入口条件。存量与缺口的实时数字以上方自动派生基线为准。

```mermaid
flowchart LR
    M1["M1 治理基线：元数据与导航"] --> M2["M2 可信基线：来源审计"]
    M2 --> M3["M3 受控生长：流水线扩容"]
    M3 --> M4["M4 体验与社区：路径图与共建"]
```

### 为什么是这个顺序

存量内容最初背着三笔债务：内容正文没有 frontmatter 元数据、来源审计状态不可统计、大部分内容文件未进入显式导航。M1 已解决元数据与可发现性，M2 已把 29 条结构审计与部署验收转为机器可读证据；剩余债务是事实核验与人工审批证据。缺少这条证据链时继续批量生成，只会让可信债务按比例放大。M1/M2 建立的元数据与审计能力，既是 M3 流水线「新增内容不产生新债务」的前提，也是 M4 学习路径的数据基础。

### M1 治理基线 — 让全部存量内容可发现、可分类

**状态**：已完成（v0.2.0）。

**目标**：消除「内容存在但不可发现」的断层，为每篇内容建立机器可读元数据。

**可执行计划**：[docs/superpowers/plans/2026-07-10-m1-governance-baseline.md](docs/superpowers/plans/2026-07-10-m1-governance-baseline.md)（任务 T1–T7）。

**工作项**：

1. **frontmatter 全量机械迁移**：严格按 [data/content-enums.yml](data/content-enums.yml) 的 `migration_rules` 执行——只从路径、文件名、H1 和显式可见元信息提取确定值；不能确认的字段一律填 `UNKNOWN`；自动迁移禁止产生 `VERIFIED` 或 `HUMAN_APPROVED`。机械元数据迁移与正文重写不得混在同一批（见[发布规则](docs/architecture/release-policy.md)）。
2. **层级目录页收编孤立页**：不把全部篇目塞进 `mkdocs.yml` 侧栏。为每层生成自动 `catalog.md`，链出该层全部 `papers/*.md`；侧栏仍保留现有精选约 25 篇/层。清单「可发现」口径 = 显式导航 ∪ 目录页链接；不改变任何现有内容 URL。
3. **标签索引**：打通 `mkdocs.yml` 已启用的 material tags 插件，建立标签索引页，作为跨层发现的第二入口。

**完成判据**：

- 清单口径下「内容文件数 = 可发现内容数」（显式导航或自动目录覆盖全部内容文件）；
- `tools/validate_frontmatter.py --all` 通过并进入 CI required 步骤；
- 现有 URL 全部不变，CI 全绿。

### M2 可信基线 — 从「文件存在」到「来源可查」

**状态**：`PARKED_HUMAN_EVIDENCE`。结构审计投影与 Pages 验收已收口；事实核验和人工审批证据尚未建立，因此不发布 v0.3.0。

**历史输入**：[docs/superpowers/plans/2026-07-10-m2-trust-baseline.md](docs/superpowers/plans/2026-07-10-m2-trust-baseline.md)（保留为历史计划；其中“STRUCTURAL 审计自动升格 PARTIAL”的旧步骤已被当前 schema 废止）。

**目标**：把「文件存在 ≠ 技术事实已验证」的免责声明替换为机器可读的审计事实。

**工作项**：

1. **结构审计记录**：29 条 current valid `STRUCTURAL` source audit 已入库并投影到 inventory；它们只证明结构可审计，不提升 `source_status`。
2. **事实核验链**：`PARTIAL` / `VERIFIED` 必须由当前正文的 `CLAIM_VERIFICATION` 记录投影，并需要 `CONTENT_AUTHOR`、`FACT_AUDITOR` 与锁定的 `critical_claim_ids`。
3. **review record 流程**：`HUMAN_APPROVED` 必须绑定独立人工证据与当前正文 hash，审批权威是 [review record schema](schemas/review-record.schema.json)；frontmatter 只保存兼容缓存字段。
4. **线上验收**：已对 <https://estelledc.github.io/iot/> 针对目标 commit 做部署健康验收，结果写入 [`data/deploy-acceptance.yml`](data/deploy-acceptance.yml)。

**完成判据**：

- 全部内容文件有显式 `source_status`（允许 `UNVERIFIED`，不允许缺失）；
- 每层至少 3 篇 current valid `STRUCTURAL` 抽样报告入库，并在 inventory 中显示 `SAMPLED_STRUCTURAL`；
- 至少一个样本完成合法 `CLAIM_VERIFICATION`，使 `source_audited_files > 0` 且 `PARTIAL` 或 `VERIFIED` 由 validator 投影产生；
- 若声明 `HUMAN_APPROVED`，必须有独立 `HUMAN` approver 的 review record，且职责分离由 authority registry 复核；
- Pages 部署验收记录绑定目标 SHA，且 main 的 quality / Pages workflow 成功。

### M3 受控生长 — 按门禁恢复 Layer 3–8 扩容

**目标**：把 `plans/*.json` 的计划条目变成可重复、可审计的内容生产流水线，向基线表中的目标容量推进。

**工作项**：

1. **流水线工具化**：选题锁定（从 plans 取号）、与既有内容去重、幂等生成、失败恢复、人工批准检查点一体化。
2. **shadow pilot**：先做 4 篇（建议从 Layer 5 边缘智能开始——plan 条目最多且是项目主题重心），验证流水线与全部质量门禁。
3. **常态扩容**：每批最多 5 篇，内容质量走 [SOP.md](SOP.md) Phase 1–4，批次边界遵守[发布规则](docs/architecture/release-policy.md)。
4. **顶会追踪**：定期跟踪 INFOCOM / MobiCom / SenSys / NSDI / IoTDI 等会议，把新论文补入 plans。

**完成判据**：

- 4 篇 shadow pilot 全部通过质量门禁并留有人工批准记录；
- 扩容批次严格 ≤5 篇且逐批可回滚；
- 新增内容 100% 自带完整 frontmatter 与来源记录，不再产生存量债务。

### M4 体验与社区 — 从「目录」到「学习系统」

**目标**：把静态目录升级为可导航的学习系统，并开放共建。

**工作项**：

1. **学习路径依赖图**：用 frontmatter 的 `prerequisites` 驱动，把站内[学习路线页](docs/roadmap.md)升级为难度分级 + 前置依赖导航。
2. **交互式八层技术全景图**：承接下文特色功能表中的 P0 项。
3. **社区设施**：CONTRIBUTING.md 贡献指南、giscus 评论（基于 GitHub Discussions）、RSS 订阅（`mkdocs-rss-plugin`）。

**完成判据**：

- 学习路径页由元数据派生而非手工维护；
- 贡献流程有文档，并至少走通一次外部贡献；
- 评论与 RSS 上线并通过站点验收。

---

## 四、内容填充计划（历史归档）

> 下列选题表是仓库创建时的头 32 个选题，已被 `plans/*.json` 的扩展计划和上一节的四里程碑方向替代；保留用于解释项目演进，不再作为选题来源。

### 早期样例（历史记录，不代表当前内容清单）

| # | 内容 | 层级 | 类型 |
|---|------|------|------|
| 1 | 边缘计算与物联网综述 | Layer 4 | 综述报告 |
| 2 | Jupiter (INFOCOM 2025) | Layer 5 | 论文阅读报告 |

### 规划中（按层级铺开，优先覆盖空白层）

#### Layer 1: 感知与硬件

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 3 | IoT RTOS 对比 | FreeRTOS vs Zephyr vs LiteOS：架构、生态、适用场景 | 对比分析 |
| 4 | TinyML 端侧部署 | "Empowering Edge Intelligence: On-Device AI Models" (ACM CSUR 2025) | 论文报告 |
| 5 | RFID 技术与应用 | RFID 感知识别技术现状综述 | 综述 |

#### Layer 2: 无线接入

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 6 | 星闪 vs BLE 6.0 | SparkLink/SLE 技术分析 + 与蓝牙 6.0 Channel Sounding 对比 | 对比分析 |
| 7 | LPWAN 技术实测 | LoRaWAN/NB-IoT/LTE-M/5G RedCap 多场景性能对比 | 综述 |
| 8 | UWB 高精度定位 | UWB 定位技术及其在工业/消费场景的应用 | 论文报告 |
| 9 | WiFi 6/7 for IoT | 802.11ax/be 对物联网接入的适用性分析 | 综述 |

#### Layer 3: 网络协议

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 10 | IoT 应用层协议 | MQTT 5.0 / CoAP / LwM2M / AMQP 全面对比 | 对比分析 |
| 11 | TSN/DetNet | 5G+TSN/DetNet 融合：确定性工业网络 | 论文报告 |
| 12 | WSN 路由优化 | AI 驱动的无线传感网路由协议 (DRL-based) | 论文报告 |
| 13 | 时间同步 | IEEE 1588 PTP / 802.1AS 精密时间同步综述 | 综述 |

#### Layer 4: 计算平台（已有综述，补充深钻）

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 14 | Serverless 边缘 | "Serverless Edge Computing: Taxonomy & Systematic Review" (2025) | 论文报告 |
| 15 | 开源平台对比 | KubeEdge vs OpenYurt vs EdgeX Foundry 架构对比 | 对比分析 |
| 16 | 任务卸载 | DRL-based 任务卸载最新进展（DAG 结构感知） | 论文报告 |

#### Layer 5: 边缘智能（已有 Jupiter，补充广度）

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 17 | 联邦学习 for IoT | FedGPA (INFOCOM 2025): 全局-个性化协作边缘异常检测 | 论文报告 |
| 18 | 模型压缩 | 量化/剪枝/蒸馏：边缘 AI 模型压缩技术全景 | 综述 |
| 19 | 协作推理 | EdgeShard / Petals / PowerInfer-2 对比分析 | 对比分析 |

#### Layer 6: 安全与隐私

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 20 | IoT 安全全景 | "A Systematic Review of IoT Security" (ACM CSUR 2024) | 论文报告 |
| 21 | 隐私保护 FL | FL + 差分隐私 + TEE 融合方案 | 论文报告 |
| 22 | PUF 与硬件安全 | 物理不可克隆函数在 IoT 设备认证中的应用 | 论文报告 |

#### Layer 7: 综合应用

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 23 | 自动驾驶 V2X | MEC-V2X 任务卸载 + 协同感知 | 论文报告 |
| 24 | 工业 IoT | 预测性维护 + 数字孪生在 IIoT 中的应用 | 综述 |
| 25 | 室内定位 | VLP / UWB / BLE AoA 多技术融合定位 | 综述 |
| 26 | 智慧医疗 IoMT | 边缘计算 + 可穿戴的实时健康监测系统 | 论文报告 |

#### Layer 8: 前沿方向

| # | 选题方向 | 候选论文/主题 | 类型 |
|---|----------|--------------|------|
| 27 | 数字孪生 + 边缘 | "DT-empowered intelligent computation offloading" (2025) | 论文报告 |
| 28 | 6G + ISAC | 通感一体化技术及其在 IoT 中的应用 | 综述 |
| 29 | Wasm on Edge | WebAssembly 作为边缘轻量运行时：基准测试与分析 | 论文报告 |
| 30 | 绿色边缘计算 | 能效优化 + 碳感知调度 + 可再生能源集成 | 论文报告 |
| 31 | RIS 智能超表面 | RIS + ISAC + UAV + MEC 多技术融合 | 论文报告 |
| 32 | 语义通信 | 面向 IoT 的语义通信：从传统比特传输到意义传输 | 综述 |

---

## 五、站点工程方案

### 技术选型：MkDocs Material

**选择理由**：

- csdiy.wiki（68k+ stars）已验证大规模中文知识库场景
- 论文笔记只需写 Markdown，YAML 配置导航
- 数学公式（KaTeX）、代码高亮、Admonitions、标签系统原生支持
- 内置本地搜索（中文分词友好）
- GitHub Pages 一键部署，GitHub Actions 自动构建

### 目标目录结构

```
iot-reading-station/
├── docs/
│   ├── index.md                    # 首页：项目介绍 + 全景技术地图
│   ├── roadmap.md                  # 学习路线图（难度分级导航）
│   ├── progress.md                 # 阅读进度追踪
│   │
│   ├── foundation/                 # Layer 1: 感知与硬件
│   │   ├── index.md               # 层级概览 + 技术地图
│   │   ├── papers/
│   │   │   └── rtos-comparison.md
│   │   └── guides/
│   │       └── getting-started.md  # 零基础入门指南
│   │
│   ├── connectivity/              # Layer 2: 无线接入
│   │   ├── index.md
│   │   ├── papers/
│   │   │   ├── sparklink-vs-ble6.md
│   │   │   └── lpwan-comparison.md
│   │   └── guides/
│   │
│   ├── network/                   # Layer 3: 网络协议
│   │   ├── index.md
│   │   ├── papers/
│   │   │   ├── iot-protocols.md
│   │   │   └── tsn-detnet.md
│   │   └── guides/
│   │
│   ├── computing/                 # Layer 4: 计算平台
│   │   ├── index.md
│   │   ├── papers/
│   │   │   ├── edge-computing-survey.md   # 已有
│   │   │   └── serverless-edge.md
│   │   └── guides/
│   │
│   ├── intelligence/              # Layer 5: 边缘智能
│   │   ├── index.md
│   │   ├── papers/
│   │   │   ├── jupiter.md                 # 已有
│   │   │   └── fedgpa.md
│   │   └── guides/
│   │
│   ├── security/                  # Layer 6: 安全与隐私
│   │   ├── index.md
│   │   ├── papers/
│   │   │   └── iot-security-survey.md
│   │   └── guides/
│   │
│   ├── applications/              # Layer 7: 综合应用
│   │   ├── index.md
│   │   ├── papers/
│   │   │   ├── v2x-mec.md
│   │   │   └── indoor-positioning.md
│   │   └── guides/
│   │
│   └── frontier/                  # Layer 8: 前沿方向
│       ├── index.md
│       ├── papers/
│       │   ├── digital-twin-edge.md
│       │   └── wasm-edge.md
│       └── guides/
│
├── mkdocs.yml                     # MkDocs 配置（导航、主题、插件）
├── requirements.txt               # Python 依赖（mkdocs-material 等）
├── .github/
│   └── workflows/
│       └── deploy.yml             # GitHub Actions: push → build → deploy
├── ROADMAP.md                     # 本文件
├── SOP.md                         # 内容生产流程（已有）
├── reading-progress.md            # 阅读进度（已有）
└── README.md                      # GitHub 仓库首页
```

### 特色功能规划

| 功能 | 实现方式 | 优先级 |
|------|---------|--------|
| 技术全景图（交互式） | Mermaid 或自定义 SVG + 点击跳转 | P0 |
| 学习路线图（难度分级） | 自定义页面，按 零基础/入门/进阶/前沿 分级 | P0 |
| 论文卡片列表 | MkDocs 标签系统 + 自定义 meta | P1 |
| 全文搜索（中文） | mkdocs-material 内置搜索 + jieba 分词 | P1 |
| 暗色模式 | mkdocs-material 原生支持 | P1 |
| 跨层级交叉引用 | Markdown 内链 + 标签关联 | P1 |
| RSS 订阅 | mkdocs-rss-plugin | P2 |
| 评论系统 | giscus（基于 GitHub Discussions） | P2 |
| 贡献指南 | CONTRIBUTING.md + 模板 | P2 |

---

## 六、早期执行方案（历史归档）

> 下列 1–3 阶段是仓库创建时的方案，已被上方自动派生基线和四里程碑方向替代；保留它用于解释项目演进，不再作为完成状态来源。

### 阶段 1：站点搭建 + 已有内容迁入（1-2 周）

- [ ] 初始化 MkDocs 项目（mkdocs.yml + 主题配置）
- [ ] 迁入已有 2 篇内容（边缘计算综述 → computing/，Jupiter → intelligence/）
- [ ] 编写首页（index.md）+ 全景技术地图
- [ ] 配置 GitHub Actions 自动部署
- [ ] 站点上线，验证可访问

### 阶段 2：覆盖全 8 层（3-8 周）

- [ ] 每层至少 1 篇内容（综述 or 论文报告 or 对比分析）
- [ ] 优先填补完全空白的 Layer 1/2/3/6
- [ ] 每篇走 SOP 流程（选题 → 初稿 → 扩充 → 审查）
- [ ] 目标：8 层全覆盖，总计 15+ 篇内容

### 阶段 3：体验优化 + 持续生长（第 9 周起）

- [ ] 交互式技术全景图上线
- [ ] 学习路线图完善（标注前置知识依赖关系）
- [ ] 评论系统 + 贡献指南
- [ ] 持续添加新论文（跟踪 INFOCOM/MobiCom/SenSys/SEC 等顶会）
- [ ] 邀请同学贡献内容

---

## 七、论文选题原则（不限课程）

1. **顶会/顶刊优先**：CCF A/B 级（INFOCOM、MobiCom、SenSys、MobiSys、NSDI、IoTDI、IEEE COMST、ACM CSUR）
2. **时效性**：2024-2025 年为主，经典工作不限年份
3. **有开源代码优先**：方便验证理解、复现实验
4. **覆盖广度优先**：先保证每层都有内容，再逐层深钻
5. **跨层关联优先**：能串联多层技术的论文（如 Jupiter 串联 Layer 4+5）更有价值
6. **实践导向**：有真实系统实现或实测数据的优先于纯理论

---

## 八、与已有产出的关系

| 已有内容 | 站点位置 | 覆盖层级 |
|----------|---------|---------|
| 边缘计算与物联网综述 | docs/computing/papers/edge-computing-survey.md | Layer 4（主）+ Layer 5/6/7/8（辅） |
| Jupiter 论文阅读报告 | docs/intelligence/papers/jupiter.md | Layer 5 |
| SOP 内容生产流程 | 根目录 SOP.md（不迁入站点，作为内部流程文档） | — |

综述报告因为覆盖面广（从边缘计算视角触及了安全、应用、前沿等多层），可在多个层级页面中交叉引用。

---

## 九、参考与灵感

| 项目 | 借鉴点 |
|------|--------|
| [csdiy.wiki](https://csdiy.wiki) | MkDocs Material 技术栈、学习路径组织方式、中文知识库规模验证 |
| [Embodied AI Reading Station](https://estelledc.github.io/embodied-ai-reading-station/) | "零基础也能读懂"的中文重写风格、论文编号系统、极简美学 |
| [roadmap.sh](https://roadmap.sh) | 交互式学习路线图、节点式导航 |
| [李沐 paper-reading](https://github.com/mli/paper-reading) | 论文精读的深度标准、视频+文字双轨 |
| [CS 自学指南](https://csdiy.wiki) | 前置依赖标注、难度分级、课程推荐模式 |

---

*创建日期：2026-06-23*
*最后更新：2026-07-10（M2 可执行推进计划已挂载；M1 已完成于 v0.2.0）*
