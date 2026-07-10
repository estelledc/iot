# 全量正文深审战役计划

> **任务号：** `IOT-T034`  
> **目标：** 对全部 642 篇存量文章做 SOP Phase 4 级正文深审重构，审后标为 `IN_REVIEW`。  
> **进度真相：** [`data/deep-review-progress.yml`](../../../data/deep-review-progress.yml)

## 锁定决策

| 决策 | 取值 |
| --- | --- |
| 顺序 | Layer 8 → 1；层内文件名升序 |
| 批次 | 每批 5 篇 |
| 分支 | `cursor/deep-review-l{n}-e0f9` |
| 状态 | 深审后 `review_status: IN_REVIEW`；不写 `HUMAN_APPROVED` / `VERIFIED` |

## 单篇检查表

1. 结构完整（含局限/挑战/批判专节）
2. 论证有机制/流程/对比，删空话
3. 量化主张尽量有出处
4. 至少 2 张有效对比表
5. 逻辑衔接成立
6. ≥3 个具体局限 + 可执行改进
7. 参考文献节；技术分析 ≥10 / 综述倾向 ≥15
8. 术语与缩写一致
9. 可读性；按主题自然补日常类比
10. 提质为主，禁止注水

## 批次流程

1. 取下一批 `pending`
2. 通读改写 + 编辑性 frontmatter
3. `validate_frontmatter.py --all`、`check_markdown_fences.py --all`、`git diff --check`
4. 进度标 `in_review` → commit（`IOT-T034` + `L{n}-B{mm}`）→ push → 更新层 PR

## 完成判据（已满足）

- `data/deep-review-progress.yml` 中 642 条均为 `in_review`
- 对应文章 frontmatter：`review_status: IN_REVIEW` 且 `last_reviewed` 为日期
- 全量门禁通过：`validate_frontmatter.py --all`、`check_markdown_fences.py --all`、`check_markdown_links.py --all --anchors --strict`
