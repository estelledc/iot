# IoT Reading Station

物联网论文阅读站——覆盖边缘计算、协作推理、联邦学习、智能感知等 IoT 相关方向。

<!-- content-inventory:start -->
## 当前内容基线

- 内容文件：**642** 篇（八层依次为 275/217/25/25/25/25/25/25）。
- 显式导航：**200** 篇；目录页入口：**642** 篇；可发现：**642** 篇；层级首页直接入口：**80** 篇。
- 扩展计划：`plans/*.json` 共 **1761** 条；按当前口径的目标容量为 **1962** 篇。
- 来源审计：尚未建立全量机器可读记录，不能把“文件存在”表述为“技术事实已验证”。

统计由 `python tools/content_inventory.py --write` 生成；`python tools/content_inventory.py --check` 用于检查漂移。

配置的 Pages 地址：<https://estelledc.github.io/iot/>（运行状态必须针对目标 commit 单独验收）。
<!-- content-inventory:end -->

## 流程

每篇论文的内容生产流程见 [SOP.md](SOP.md)。

## 扩展原则与未来方向

仓库已包含 GitHub Pages 构建与部署配置，但这不代表线上部署当前健康。继续扩展 Layer 3–8 前，先补齐导航、内容 schema、来源抽样和可重复生产门禁；不要一次性批量生成计划中的全部条目。

项目未来按四个里程碑推进——**M1 治理基线**（frontmatter 迁移 + 导航收编）→ **M2 可信基线**（来源审计与抽样核验）→ **M3 受控生长**（流水线化扩容 Layer 3–8）→ **M4 体验与社区**（学习路径图与共建设施）。完整方向与各里程碑完成判据见 [ROADMAP.md](ROADMAP.md#三未来方向四个里程碑)。
