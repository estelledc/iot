# IoT Reading Station

从传感器、无线接入到边缘智能与 6G 前沿的中文 IoT 全栈学习站。八层技术地图先回答“一个方向在系统里的什么位置”，再把读者带到可追溯的教程、论文阅读与工程对比。

[在线学习站](https://estelledc.github.io/iot/) · [学习路线](https://estelledc.github.io/iot/roadmap/) · [事实与审核口径](https://estelledc.github.io/iot/progress/) · [发布规则](docs/architecture/release-policy.md)

## 对外展示摘要

- **问题**：IoT 横跨硬件、连接、协议、计算、智能、安全与应用；单篇阅读很容易失去依赖关系和学习顺序。
- **系统**：Markdown 源真相 → frontmatter schema 与确定性清单 → 自动 catalog、搜索与 MkDocs Pages → CI 结构、链接和发布门禁。
- **可核查证据**：8 层技术体系；642 个内容文件已全部进入可发现目录；M1 治理基线已完成。
- **协作分工**：Jason 负责分层、里程碑、发布门禁与验收判断；AI 辅助研究、初稿、批量深审和站点实现，不能自行授予 `VERIFIED` 或 `HUMAN_APPROVED`。
- **当前局限**：已有 29 条 `STRUCTURAL` 结构审计，但事实核验仍为 0；642/642 正文处于 `IN_REVIEW`，不表示技术事实已经人工验证；Pages 验收记录见 [`data/deploy-acceptance.yml`](data/deploy-acceptance.yml)。

<!-- content-inventory:start -->
## 当前内容基线

- 内容文件：**642** 篇（八层依次为 275/217/25/25/25/25/25/25）。
- 显式导航：**200** 篇；目录页入口：**642** 篇；可发现：**642** 篇；层级首页直接入口：**80** 篇。
- 扩展计划：`plans/*.json` 共 **1761** 条；按当前口径的目标容量为 **1962** 篇。
- 来源审计：current valid `STRUCTURAL` 结构审计 **29** 条，覆盖 **29** 个内容文件；事实核验：**0** 篇（`PARTIAL`/`VERIFIED`）。`STRUCTURAL` 只证明结构可审计，不代表技术事实已验证。

统计由 `python tools/content_inventory.py --write` 生成；`python tools/content_inventory.py --check` 用于检查漂移。

配置的 Pages 地址：<https://estelledc.github.io/iot/>（运行状态必须针对目标 commit 单独验收）。
<!-- content-inventory:end -->

## 流程

每篇论文的内容生产流程见 [SOP.md](SOP.md)。

## 扩展原则与未来方向

M1 治理基线已完成（v0.2.0）：642 篇 frontmatter、八层 catalog 可发现、CI 全量校验。继续扩展 Layer 3–8 前，先完成 M2 来源抽样与可重复生产门禁；不要一次性批量生成计划中的全部条目。

项目按四个里程碑推进——**M1 治理基线**（已完成）→ **M2 可信基线**（来源审计与抽样核验）→ **M3 受控生长**（流水线化扩容 Layer 3–8）→ **M4 体验与社区**（学习路径图与共建设施）。完整方向与各里程碑完成判据见 [ROADMAP.md](ROADMAP.md#三未来方向四个里程碑)。
