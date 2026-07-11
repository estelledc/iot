# 内容 frontmatter 契约

## 为什么先定义契约

目录里有 642 个 Markdown 文件，但“文件存在”不能回答它是论文精读、综述还是教程，也不能证明来源已经审核。frontmatter 的作用像图书馆书脊：先给每份内容一个可机读身份，目录、搜索、路线和质量门禁才有稳定输入。

JSON Schema 的机器源真相是 `schemas/content-frontmatter.schema.json`，枚举中文解释与迁移规则在 `data/content-enums.yml`。

## 最小字段

```yaml
---
schema_version: "1.0"
id: mqtt5-deep-dive
title: MQTT 5.0 深入解析
layer: 3
content_type: technical_analysis
difficulty: intermediate
reading_time: 25
prerequisites:
  - iot-app-protocols
tags:
  - MQTT
  - 消息协议
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
```

字段边界：

- `id` 必须等于文件名 slug，避免元数据改名导致公开 URL 漂移。
- `layer` 必须与 `docs/<layer>/papers/` 路径一致。
- `reading_time` 使用分钟整数；无法从显式字段确定时使用 `UNKNOWN`。
- `prerequisites: []` 表示明确没有先修；`prerequisites: UNKNOWN` 表示尚未判断，二者不能混用。
- `source_status` 描述来源核验，不描述文件是否已生成。
- `review_status: HUMAN_APPROVED` 必须来自人工 review record，自动迁移不能设置。

## 双状态机与证据边界

frontmatter 中的 `source_status` 和 `review_status` 是可校验的派生缓存，不是审批证据本体。来源审计记录与人工审阅记录分别遵循 `schemas/source-audit.schema.json` 和 `schemas/review-record.schema.json`；只有记录仍有效、绑定当前正文 hash 且满足角色约束时，缓存状态才成立。

两条状态轴保持正交：

- `source_status` 只回答“正文主张被一手来源核验到什么程度”。
- `review_status` 只回答“内容是否进入独立人工审阅流程”。
- `STRUCTURAL` 只判断内容是否具备可审计结构。无论 checklist 是 `AUDITABLE`、`NEEDS_CHANGES` 还是 `ERROR`，都不能单独把 `source_status` 升为 `PARTIAL` 或 `VERIFIED`。
- 正文 hash 不匹配、记录被撤销或被后继记录取代时，旧记录保留为历史，但不再参与当前状态投影。

### source_status 主动记录迁移

| from | 允许的 to | 必要证据 |
| --- | --- | --- |
| `UNKNOWN` | `UNKNOWN`, `PARTIAL`, `VERIFIED` | 结构审计只能 no-op；事实审计按覆盖度解析未知状态 |
| `UNVERIFIED` | `UNVERIFIED`, `PARTIAL`, `VERIFIED` | `PARTIAL`/`VERIFIED` 必须来自当前正文的 `CLAIM_VERIFICATION` |
| `PARTIAL` | `PARTIAL`, `VERIFIED` | 重新核验可保持状态；覆盖全部关键主张且无阻塞项才可升格 |
| `VERIFIED` | `VERIFIED` | 新的有效事实审计只能确认当前状态；降级由失效后重新投影产生 |

`PARTIAL` 要求至少一项主张已由可追踪来源核验，同时明确列出尚未覆盖项；`VERIFIED` 还要求 `HUMAN` 类型的事实审计员、全部关键主张通过、没有未覆盖项和阻塞项。hash 失配或撤销不是删除历史记录，而是让投影器忽略失效记录，再依据剩余有效证据重算为 `UNVERIFIED`、`PARTIAL` 或 `VERIFIED`。

### review_status 主动记录迁移

| from | 允许的 to | 决策 |
| --- | --- | --- |
| `UNKNOWN` | `IN_REVIEW` | `START_REVIEW` |
| `UNREVIEWED` | `IN_REVIEW` | `START_REVIEW` |
| `NEEDS_CHANGES` | `IN_REVIEW` | 修复后 `START_REVIEW` |
| `HUMAN_APPROVED` | `IN_REVIEW` | 正文变化或主动重开审阅 |
| `IN_REVIEW` | `NEEDS_CHANGES`, `HUMAN_APPROVED` | `REQUEST_CHANGES` 或 `APPROVE` |

`HUMAN_APPROVED` 最低 `source_status`：`VERIFIED`。

批准还必须同时满足：reviewer 是 `HUMAN` 类型的 `APPROVER`；review record 与当前 `body_sha256` 匹配；关联的 audit ID 可追踪；author、fact auditor、approver 的稳定 actor ID 两两独立；所有 review checks 通过。T041 只能校验记录内的 independence declaration；仓库级 validator 还必须用权威作者/actor 映射复核，不能信任自报数组。仅在 frontmatter 写入 `HUMAN_APPROVED` 不构成批准。

### 撤销与失效

撤销必须写明时间、操作者、治理角色、原因代码和文字说明。时间必须满足 `retrieved_at ≤ audited_at ≤ reviewed_at`、前序 review 不晚于后继 review，且撤销时间不早于被撤销事件。撤销或 supersede 不删除旧记录；当前投影只使用未撤销、未被取代、hash 与当前正文一致的记录。

T041 fixtures 只证明记录内部合同，不代表真实内容已经覆盖全部关键主张。生产状态提升默认关闭；后续仓库级 validator 必须同时取得当前正文 hash、权威作者/actor 映射、锁定的关键主张清单并解析全部跨记录引用，才能投影 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。

## 论文精读的额外要求

只有目标论文身份明确时才能使用 `paper_reading`，并必须提供 `target_paper`：

```yaml
content_type: paper_reading
target_paper:
  title: "Jupiter: Fast and Resource-Efficient Collaborative Inference of Generative LLMs on Edge Devices"
  authors:
    - UNKNOWN
  year: 2025
  doi: UNKNOWN
  url: UNKNOWN
```

如果现有内容只是围绕一个技术主题展开，不能因为目录名是 `papers/` 就自动标记为 `paper_reading`；使用 `technical_analysis` 或 `UNKNOWN`。

## 兼容与 URL 稳定性

- schema `1.x` 可以增加可选字段，但不能删除、改名或收紧既有合法值。
- 不兼容变化需要新的 major schema version、迁移工具和 Changelog 说明。
- `id` 或文件路径变更默认禁止；确有必要时必须同时提供重定向与链接回归证据。
- 正文迁移独立执行。插入 frontmatter 前后必须验证 642 篇 body SHA-256 完全一致。

## 验证

```bash
python tools/validate_frontmatter.py --schema-only --fixtures
python tools/validate_frontmatter.py --all
```

CI 与 Pages 构建均要求全量内容文件通过 schema + 路径语义校验。
