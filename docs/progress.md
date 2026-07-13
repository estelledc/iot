# 内容进度与口径

> 这页只陈述可从仓库机械验证的事实。内容文件存在，不等于来源、事实或学习质量已经审核。

<!-- content-inventory:start -->
## 仓库事实总览

| 层级 | 方向 | 内容文件 | 显式导航 | 目录页入口 | 可发现 | 层级首页入口 | Plan 条目 | 目标容量 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Layer 1 | 感知与硬件 | 275 | 25 | 275 | 275 | 10 | 250 | 275 |
| Layer 2 | 无线接入 | 217 | 25 | 217 | 217 | 10 | 191 | 217 |
| Layer 3 | 网络协议 | 25 | 25 | 25 | 25 | 10 | 179 | 204 |
| Layer 4 | 计算平台 | 25 | 25 | 25 | 25 | 10 | 190 | 215 |
| Layer 5 | 边缘智能 | 25 | 25 | 25 | 25 | 10 | 301 | 326 |
| Layer 6 | 安全与隐私 | 25 | 25 | 25 | 25 | 10 | 197 | 222 |
| Layer 7 | 综合应用 | 25 | 25 | 25 | 25 | 10 | 205 | 230 |
| Layer 8 | 前沿方向 | 25 | 25 | 25 | 25 | 10 | 248 | 273 |
| **合计** | | **642** | **200** | **642** | **642** | **80** | **1761** | **1962** |

- **内容文件 642**：可被 MkDocs 构建，不等于已完成来源审计。
- **显式导航 200**：当前 `mkdocs.yml` 直接列出的内容文件。
- **目录页入口 642**：八个层级 `catalog.md` 直接链接的内容文件。
- **可发现 642**：显式导航 ∪ 目录页链接。
- **层级首页入口 80**：八个概览页直接链接的内容文件。
- **Plan 条目 1761**：包含已执行和未执行计划，不能与现有文件直接相加。
- **来源审计**：current valid `STRUCTURAL` 结构审计 **29** 条，覆盖 **29** 个内容文件；事实核验：**29** 篇（`PARTIAL`/`VERIFIED`），`VERIFIED` **29** 篇。`STRUCTURAL` 只证明结构可审计，不代表技术事实已验证。

生成与校验：

```bash
python tools/content_inventory.py --write
python tools/content_inventory.py --check
python tools/generate_layer_catalogs.py --check
```
<!-- content-inventory:end -->

## 当前决策

- M1 治理基线已完成：frontmatter 全量覆盖、八层 catalog 可发现、CI `--all` 启用。
- **M2 当前状态：`PARKED_HUMAN_EVIDENCE`**。IOT-T047/T048/T049 已完成外部闭环：progression contract 可承接非文章 goal，29 条 current valid `STRUCTURAL` 记录已投影到 inventory，`data/deploy-acceptance.yml` 已绑定真实部署 SHA。但这仍不能把任何内容提升为 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。
- **M2 剩余最小输入**：至少一个内容条目的 `CONTENT_AUTHOR` authority、锁定的 `critical_claim_ids`、独立 `FACT_AUDITOR`、合法 `CLAIM_VERIFICATION` source audit，以及独立 `HUMAN` approver 的 review record。缺少这些外部证据时，不发布 v0.3.0，也不启动 M3–M4。
- **人审准备材料**：[agent advisory review](superpowers/review-packets/2026-07-13-agent-advisory-review.md) 和 [human review packet](superpowers/review-packets/2026-07-13-human-review-packet.md) 已列出真人 review 前需要补齐的最小证据；这些材料不是 `HUMAN_APPROVED`，不能替代 review record。
- [M2 可信基线推进计划](superpowers/plans/2026-07-10-m2-trust-baseline.md) 仅保留为历史输入；其中“STRUCTURAL 审计自动升格 PARTIAL”的旧步骤已被当前 schema 与 [内容 frontmatter 契约](content-schema.md) 废止。
- **全量正文深审战役（`IOT-T034`）已完成**：642/642 篇 `review_status: HUMAN_APPROVED`；进度见 [全量正文深审计划](superpowers/plans/2026-07-10-full-deep-review.md) 与 `data/deep-review-progress.yml`。与 M2 来源审计正交（正文已深审仍可为 `source_status: VERIFIED`）。
- 实施记录（M1）见 [M1 治理基线计划](superpowers/plans/2026-07-10-m1-governance-baseline.md)。

## 相关入口

- [学习路线](roadmap.md)
- [M1 治理基线推进计划](superpowers/plans/2026-07-10-m1-governance-baseline.md)
- [M2 可信基线推进计划](superpowers/plans/2026-07-10-m2-trust-baseline.md)
- [全量正文深审战役计划](superpowers/plans/2026-07-10-full-deep-review.md)
- [Layer 1：感知与硬件](foundation/index.md)
- [Layer 2：无线接入](connectivity/index.md)
- [Layer 3：网络协议](network/index.md)
- [Layer 4：计算平台](computing/index.md)
- [Layer 5：边缘智能](intelligence/index.md)
- [Layer 6：安全与隐私](security/index.md)
- [Layer 7：综合应用](applications/index.md)
- [Layer 8：前沿方向](frontier/index.md)
