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

撤销必须写明时间、操作者、治理角色、原因代码和文字说明；操作者还必须在全局 actor registry 中获授 `GOVERNANCE_REVIEWER`。时间必须满足 `retrieved_at ≤ audited_at ≤ reviewed_at`、前序 review 不晚于后继 review，且撤销时间不早于被撤销事件。撤销或 supersede 不删除旧记录；当前投影只使用未撤销、未被取代、hash 与当前正文一致的记录。

T041 fixtures 只证明记录内部合同，不代表真实内容已经覆盖全部关键主张。生产状态提升默认关闭；T044 仓库级 validator 必须同时取得当前正文 hash、权威作者/actor 映射、锁定的关键主张清单并解析全部跨记录引用，才能投影 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。

### 当前正文绑定校验（T042）

`python tools/validate_source_audits.py --all` 与 `python tools/validate_review_records.py --all` 负责单记录层的 fail-closed 校验：确认记录符合 Draft 2020-12 schema、只指向 `docs/<layer>/papers/<id>.md` canonical 身份，并把记录声明的 `body_sha256` 与当前原始正文 bytes 计算值比较。frontmatter 单独变化不影响正文 hash；正文任意 byte 变化都会让未撤销旧记录变为 `STALE`。已撤销且身份正确的记录保留为 `REVOKED` 历史，但不再是当前证据。

这里的 `ACTIVE` 只表示“一条记录与当前 canonical 正文局部绑定”，不表示它已通过跨记录引用、角色分离或状态投影。记录目录尚未建立或为空时，`--all` 返回 `checked=0`，这同样不代表任何内容已核验；T043 负责 legacy 对账，T044 才负责仓库级有效记录图和可信状态投影。

### 存量 `IN_REVIEW` 对账（T043）

`data/trust-migration-ledger.yml` 是 642 篇现有内容的只读迁移账本。它逐篇记录 `observed_at_commit` 对应 Git tree 中的 canonical `content_id`、仓库相对路径、`body_sha256` 和当时 frontmatter 双状态，但不创建 reviewer、auditor 或批准证据。当前统计必须明确分开：`observed_in_review=642` 只表示历史状态，`evidence_bound_review=0` 才表示尚无独立记录完成绑定。

所有当前条目都标为 `LEGACY_UNBOUND`：既不把历史 `IN_REVIEW` 批量回退为 `UNREVIEWED`，也不把它解释为已人工审阅。只有 T044 的跨记录 validator 确认新 audit/review record 与当前正文 hash、引用和职责分离全部有效后，后续实现才可把对应条目转为 `BOUND`；历史观察继续保留。

```bash
python tools/reconcile_legacy_review_state.py --write
python tools/reconcile_legacy_review_state.py --check
```

`--write` 要求 canonical 论文树与一个不可变 Git commit 完全一致，且发现真实 trust record 时会 fail-closed 交给 T044。`--check` 则从账本冻结的 `observed_at_commit` 重新归档当时的 papers 与 progress，重建后逐字节比较；因此它能与后续真实 trust record 共存，也不会因当前正文合法演进而重写历史。观察 commit 必须存在且是当前 `HEAD` 的祖先，CI checkout 必须使用完整 Git 历史；承载 T043/T044 的提交只能 fast-forward/direct push 或 merge-commit 集成，不能 squash/rebase。集成后必须再执行 `git merge-base --is-ancestor <observed_at_commit> HEAD`，否则账本检查与部署都会失败关闭。两个命令都不修改 `docs/*/papers/*.md`。

### 仓库级 trust graph 与迁移基线（T044）

`python tools/validate_trust_state.py --all --baseline-mode` 是跨记录可信状态投影门禁。`--all` 要求扫描全部 canonical 内容、source audit、review record 和迁移账本；`--baseline-mode` 必须显式给出，它只允许账本中已经冻结的 legacy `IN_REVIEW` 观察继续作为兼容投影，不放宽任何新记录或状态提升规则。

当前迁移基线必须保持 `canonical_content=642`、`legacy_unbound=642`、`evidence_bound_review=0`、`verified=0`、`approved=0`。`data/trust-migration-ledger.yml` 只证明这 642 条历史观察与首次观察 Git tree 一一对应；它不是 source evidence、review evidence 或 authority source，不能单独生成 `PARTIAL`、`VERIFIED` 或 `HUMAN_APPROVED`。只有当前身份、路径、layer 和正文 hash 仍与历史条目相同的内容才保留 legacy `IN_REVIEW` 兼容投影；正文变化会让该 binding 失效，但不会破坏或重写历史账本。缺少 `--baseline-mode` 时，任何当前有效的 `LEGACY_UNBOUND` 条目都会以 `LEGACY_UNBOUND_REQUIRES_BASELINE` 失败；baseline mode 下出现无绑定提升则以 `LEGACY_UNBOUND_PROMOTION` 失败。

真实职责与 claim authority 使用固定可选文件 `data/trust-authorities.yml`，合同为 `schemas/trust-authorities.schema.json`。文件中的全局 `actors` registry 为每个稳定 `actor_id` 锁定 `actor_type` 和 `allowed_roles`；每个 content entry 则绑定当前 `content_id`、canonical 路径和 `body_sha256`，并提供非空 `author_ids`，这些 author 必须解析到获授 `CONTENT_AUTHOR` 的 actor。需要 `PARTIAL` / `VERIFIED` / `HUMAN_APPROVED` 时还必须提供非空、锁定的 `critical_claim_ids`。只有当前空记录基线可以没有该文件；任一未撤销 source/review record（包括 `STRUCTURAL` shadow audit）都必须解析 actor。仅有结构审计时可使用非空 `actors` 加 `entries: []`，无需 author 或 claim authority。authority 文件本身不能提升状态。

仓库级 validator 在单记录 schema/hash 校验之上继续检查：

- 每条当前记录的 `content_id`、canonical 路径和 `body_sha256` 必须指向当前正文；未撤销 `STALE` 记录失败。身份正确且已撤销的旧 hash 记录可作为历史保留，原 auditor/reviewer 不要求仍存在于当前 registry，但使该记录失效的 revocation actor 必须仍获授 `GOVERNANCE_REVIEWER`；历史记录不参与当前证据投影。存在 stale/revoked review 历史时，降级下限为 `IN_REVIEW`，而不是冒充从未审阅。
- source audit 与 review record 的 `supersedes` 必须解析到同类型、同内容且时间有序的前序记录；环、分叉、未知目标或跨身份取代都 fail closed。
- 状态驱动的 claim/review 非初始迁移必须有合法 predecessor；`STRUCTURAL` 独立 no-op 不跨 kind 取代 claim chain，也不能改变 `source_status`。
- 所有 review 的 `linked_audit_ids` 必须存在、早于 review、绑定同一正文，并在各自 `reviewed_at` 时是有效 evidence；`source_status_at_review` 必须由这些历史时点链接实际投影。validator 会先裁剪无效 successor 与依赖边，再对最终暴露的 active approval 复验当前 evidence；复验若产生新的无效节点，就继续裁剪并重算到固定点后才投影。当前 active approval 的链接必须在当前 `as-of` 保持 active/current 并共同投影出 `VERIFIED`，不能借用未链接的全局事实审计。
- 每条未撤销记录的 auditor/reviewer 都必须在全局 registry 中解析，权威 type 必须匹配记录 type，且记录声明的 role 必须位于 `allowed_roles`；自报 `human-*`、同步篡改 type/role 不能自授信任。author、`FACT_AUDITOR`、approver 的职责分离必须用该权威映射复核；author 可以执行不会提升状态的 `STRUCTURAL_AUDITOR`，但 reviewer 仍须与全部 linked auditors 独立。来源提升还需要锁定的关键主张清单；缺少这些 authority 输入时 fail closed。
- 只从完整有效记录图计算预期 `source_status` / `review_status`，再与 frontmatter 缓存比较；不匹配以 `SOURCE_STATUS_PROJECTION_MISMATCH` 或 `REVIEW_STATUS_PROJECTION_MISMATCH` 失败，不自动批量重写 Markdown、记录或账本。

命令成功输出 `TRUST_STATE_OK` 和计数摘要；发现合同违规时返回非零，按稳定错误码排序输出安全的仓库相对路径，例如 `BODY_HASH_MISMATCH`、`SUPERSEDES_CYCLE`、`LINKED_AUDIT_NOT_FOUND`、`REVIEWER_AUDITOR_CONFLICT`。I/O、schema 或不安全路径等无法可靠继续的情况使用 `TRUST_STATE_ERROR [<CODE>]`，不得泄露本机绝对路径。`--as-of` 可指定严格 RFC3339 回放边界；未指定时使用当前 UTC，未来 audit、review、reference 或 revocation 一律失败。

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
python tools/validate_source_audits.py --all
python tools/validate_review_records.py --all
python tools/validate_trust_state.py --all --baseline-mode
```

CI 与 Pages 构建均要求全量内容文件通过 schema、路径语义、当前正文绑定和仓库级 trust graph 校验。
