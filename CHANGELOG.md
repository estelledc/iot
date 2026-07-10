# Changelog

本项目从 `0.1.0` 起使用语义化版本。每条变更必须引用实施任务，并记录可重复验证命令。

## [0.1.2] - 2026-07-10

### Added

- `IOT-T028`：新增 M1 治理基线可执行推进计划 `docs/superpowers/plans/2026-07-10-m1-governance-baseline.md`（T1–T7：frontmatter 迁移 → catalog 可发现 → 标签索引 → CI `--all` → v0.2.0 验收）；在 `docs/progress.md` 与 `ROADMAP.md` M1 小节挂上入口，并锁定「层级 catalog 收编孤立页、不塞满侧栏」方案。本版本不执行迁移或导航改动。验证：`python tools/content_inventory.py --check`、`python tools/check_markdown_links.py --all --anchors --strict`、`python tools/check_markdown_fences.py --all`。

### Review baseline

- Source commit: `16f5b2cfac071e7f53bd450c01d7b3e7a125b600`
- 迁移说明：纯文档变更；无 URL、schema 或内容正文迁移。

## [0.1.1] - 2026-07-10

### Changed

- `IOT-T026`：在 `ROADMAP.md` 新增「三、未来方向：四个里程碑」（M1 治理基线 → M2 可信基线 → M3 受控生长 → M4 体验与社区，均含可机械验证的完成判据），把已过时的内容填充选题表改为历史归档并重排章节编号；`README.md` 扩展原则小节同步指向新方向章节。不改动任何站点 URL、导航、内容正文或自动生成块。验证：`python tools/content_inventory.py --check`、`python tools/check_markdown_links.py --all --anchors --strict`、`python tools/check_markdown_fences.py --all`。

### Review baseline

- Source commit: `7d937fd02de4b5345f614065fe27cefb8b5d9ec8`
- 迁移说明：纯文档变更，无 URL、schema 或内容正文迁移要求。

## [0.1.0] - 2026-07-10

### Added

- `IOT-T001` / `IOT-F003`：新增确定性内容清单、公开统计生成块和漂移检查；验证：`python tools/content_inventory.py --check`。
- `IOT-T002` / `IOT-F004`：首页模板只保留布局样式并渲染 `page.content`，首页可编辑内容统一回到 `docs/index.md`；验证：`python tools/validate_site.py --site-dir site --page index.html --assert-single-main --assert-single-footer --assert-single-h1`。
- `IOT-T003`（PARTIAL）/ `IOT-F001`：把发布、构建兼容性和内容契约纳入维护导航；442 个历史孤立内容页的完整治理留待目录/集合方案确定后实施。
- `IOT-T006` / `IOT-F008` / `IOT-F012`：新增 Markdown fence、相对链接和锚点检查；验证：`python tools/check_markdown_fences.py --all`、`python tools/check_markdown_links.py --all --anchors --strict`。
- `IOT-T007`（PARTIAL）/ `IOT-F015` / `IOT-F016`：移除未引用的重复 CSS，忽略本地构建目录，并为受正文只读约束保护的两篇 legacy mirror 建立 SHA-256 一致性门禁。
- `IOT-T008` / `IOT-F017`：统一首页与普通页 footer landmark，移除静态发布日期，并检查新窗口外链的 `rel` 属性。
- `IOT-T009` / `IOT-F002` / `IOT-F005` / `IOT-F013`：新增 versioned frontmatter JSON Schema、枚举说明、正反 fixtures 与验证器；当前不批量修改 642 篇正文。
- `IOT-T016`（PARTIAL）/ `IOT-F009`：固定 Python 3.11 与 MkDocs/Material 直接依赖，增加带哈希锁文件和兼容性说明；完整内容门禁仍依赖 `IOT-T010/T011`。
- `IOT-T017`（PARTIAL）/ `IOT-F008`：新增 pull request 质量 workflow，固定第三方 Action SHA，把 Pages 写权限限制在 deploy job，并添加 workflow policy 与 Dependabot；分支保护和真实部署仍需仓库设置与人工验收。
- `IOT-T025`：建立版本、Changelog 和发布规则检查；验证：`python tools/check_release_metadata.py --version-file VERSION --changelog CHANGELOG.md`。

### Fixed

- `IOT-T001`：统一公开入口为 642 个内容文件、200 个显式导航条目、80 个层级首页入口和 1761 条 plan 记录，并明确“文件存在”不等于“来源已审核”。
- `IOT-T006`：修复 `power-integrity-pdn-design.md` 的游离 fence、首页目录链接和 Layer 8 跨层标签错位。
- `IOT-T002`：修复首页 Markdown 与模板双源；保留八层卡片和统计视觉结构，窄屏表格不再造成页面级横向溢出。

### Review baseline

- Source commit: `2a18aec69793494156ffca67848ca0639c145fe4`
- Validated handoff ZIP SHA-256: `3774bd66affa2c59f3631a8bd2f5d547fe15e8f2dab87aff9642714b13b0b394`
- Ship decision: `SHIP_WITH_FOLLOWUPS`
- 迁移说明：本版本不改变既有文章 URL，不批量重写内容正文，也不执行 Layer 3–8 扩容。
