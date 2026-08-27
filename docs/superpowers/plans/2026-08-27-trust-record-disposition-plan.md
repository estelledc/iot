# IOT-T066 批量占位 trust 记录处置计划

> 本文档是处置计划，不是 source audit，不是 review record，不改变任何 trust 状态。它回答一个问题：如何让 642 篇文章的投影不再把 2026-07-13 批量生成的占位记录呈现为已完成的人类审核，同时不伪造新证据、不删除历史。缺陷证据本身见 [IOT-T065 trust evidence findings](../review-packets/2026-08-27-trust-evidence-findings.md)。

## 一、为什么 agent 不能单独执行处置（schema 硬约束实测）

处置的目标状态是"降级"，而当前 schema 把每一条降级通道都绑定到真实人类：

1. **revocation 块只接受 HUMAN governance 身份**。`schemas/source-audit.schema.json`（`by_actor_type` 为 const `HUMAN`，`by_role` 为 const `GOVERNANCE_REVIEWER`，`by_actor_id` 必须匹配 `^human-`；第 764–786 行）与 `schemas/review-record.schema.json`（第 406–424 行）完全一致。运行时还要求该 actor 在 `data/trust-authorities.yml` 中真实注册了 `GOVERNANCE_REVIEWER` 角色（`tools/trust_records.py` 第 744–751 行）——当前 registry 没有任何 governance actor。
2. **supersede 降级路径被三重封死**：`CLAIM_VERIFICATION` 的合法 `status_transition` 只有升级或原地（to `PARTIAL`：from 不允许 `VERIFIED`，`schemas/source-audit.schema.json` 第 564–580 行；to `VERIFIED`：auditor 必须 HUMAN，第 288–294 行；`NEEDS_CHANGES`/`ERROR`：只允许 noop，第 349–362 行）；且 trust graph 强制 successor 的 `from` 等于 predecessor 的 `to`（`tools/trust_records.py` 第 1344–1351 行），伪造 `UNVERIFIED→UNVERIFIED` noop 去 supersede 一条 `VERIFIED` 记录会被图校验拒绝。noop `VERIFIED→VERIFIED` 即使写成 `ERROR` outcome，投影取 `transition.to`，结果仍是 `VERIFIED`——不降级。
3. **review 层 agent 完全无权**：任何 review record 的 reviewer 都必须是 `human-*` + `HUMAN`（`schemas/review-record.schema.json` 第 63、219 行）。
4. **删除记录被 AGENTS.md 禁止**（观察历史必须保留），且删除会同时破坏 supersedes 链与 ledger 语义。

结论：agent 代签任何一条降级记录都等于重演 `0c641cd` 的同类伪造。本 goal（IOT-T066）因此只交付计划，不触碰 `data/`。

## 二、处置后的目标终态（由投影机制推导，非人为设定）

对 642 篇批量文章执行完整撤销（每篇撤 `CLAIM_VERIFICATION` + `START_REVIEW` + `APPROVE` 三条）后，投影机制给出：

| 指标 | 现值 | 终态 | 机制依据（`tools/trust_records.py` / `tools/validate_trust_state.py`） |
| --- | ---: | ---: | --- |
| `source_records` | 1287 | **1287** | 撤销不删除文件，记录数不变 |
| `review_records` | 1284 | **1284** | 同上 |
| `verified` | 642 | **0** | 撤销记录退出 current 集合，`source_status` 回落 `UNVERIFIED`（第 1445–1449、1610–1621 行） |
| `approved` | 642 | **0** | 无 active review 叶（第 1898–1927 行） |
| `evidence_bound_review` | 642 | **0** | `active_review_ids` 清空（`validate_trust_state.py` 第 666–668 行） |
| `legacy_unbound` | 0 | **642** | ledger 绑定仍有效且无 active review 叶（第 669–671 行）；CI 使用 `--baseline-mode`，该值非零是合法状态 |
| 642 篇投影 | `VERIFIED`/`HUMAN_APPROVED` | **`UNVERIFIED`/`IN_REVIEW`** | 撤销后的投影地板是 `IN_REVIEW`（invalidated review history，第 1898–1927 行），不是 `UNREVIEWED` |

不动的部分：642 条 `STRUCTURAL` 审计（真实结构证据，本来就不提升状态）；IOT-T057 的 3 条 agent `PARTIAL` claim（真实 agent 证据，正确地止步 `PARTIAL`）；`data/trust-migration-ledger.yml`（provenance 校验按历史 `observed_at_commit` 重建对账，正文 hash 未变则字节不必动，`validate_trust_state.py` 第 477–523 行）；`data/deep-review-progress.yml`（绑定战役字段 `status: in_review`，与降级后的 `IN_REVIEW` 一致）。

## 三、候选路径对比

### 路径 A（推荐）：HUMAN governance 撤销

**前置条件（一个独立小 goal，diff 极小，必须先行）**：用户以真实身份注册 governance actor 到 `data/trust-authorities.yml`，例如：

```yaml
- actor_id: human-estelledc-governance
  actor_type: HUMAN
  allowed_roles:
  - GOVERNANCE_REVIEWER
```

`actor_id` 必须对应真实的人（仓库 owner），不得再造第二批无身份占位 id——这是 T065 findings 的核心教训。

**撤销的原子分组约束（联动实测）**：同一篇文章的三条记录必须在同一批内一起撤。只撤 `CLAIM_VERIFICATION` 而保留 `APPROVE` 会立即触发 `LINKED_AUDIT_INACTIVE` / `LINKED_AUDITS_NOT_VERIFIED` issue，`validate_trust_state` 门禁失败（`tools/trust_records.py` 第 1683–1735 行）；只撤 `APPROVE` 虽不报错，但会留下 `VERIFIED` + `IN_REVIEW` 的误导性中间态。每篇的原子操作集：3 条记录各加 `revocation` 块 + frontmatter 双状态改为 `UNVERIFIED`/`IN_REVIEW`。

**revocation 块模板**（`reason_code` 用 `POLICY_VIOLATION`：违反 T051 packet Non-Goals 与 AGENTS.md 可信状态硬边界；`reason` 引用 findings packet 路径与 `0c641cd`）：

```yaml
revocation:
  revoked_at: "<用户授权时刻，ISO-8601>"
  by_actor_id: human-estelledc-governance
  by_actor_type: HUMAN
  by_role: GOVERNANCE_REVIEWER
  reason_code: POLICY_VIOLATION
  reason: >-
    Bulk-generated placeholder evidence from commit 0c641cd (2026-07-13):
    generic human-* actor without real identity, template-uniform timestamps,
    reused snapshot hash. See
    docs/superpowers/review-packets/2026-08-27-trust-evidence-findings.md.
```

**批次结构约束（goal 机制推导）**：`baseline.expected_trust` 属于 goal 的 immutable 字段（`tools/check_active_goal.py` 的 `IMMUTABLE_FIELDS`），checker 在每个切片都会把当前仓库数字与它对账。因此**一个 goal 只能承载一步到位达到其 baseline 终态的变更**，"goal 内多批渐进撤销"会让中间状态永远过不了 checker。可行的两种编排：

- **A1 单 goal 全量**：一个 goal、一个 PR 完成 642 篇。触达面约 2578 个文件（642 claim + 1284 review + 642 frontmatter + 2 mirror + registry 1 + inventory 自动块 7）。diff 巨大但每个 hunk 同构（同一 revocation 块 + 同一对 frontmatter 字段），可脚本生成、全门禁机械验证、抽样人审。
- **A2 多 goal 分批**：每个 goal 撤 N 篇（如 50 篇/批 → 13 个 goal/PR），每个 goal 的 baseline 写该批终态（`verified` 642→592→…→0）。每批 diff 可完整人审（约 200 文件/批），代价是 13 轮 goal/PR/merge 循环，且中间批次的站点会长期呈现"部分降级"的混合状态。
- 取舍建议：占位记录本身就是单提交批量生成的，同构撤销的正确性由 validator 保证而非逐行人审保证；**推荐 A1**，用抽样审查 + 全门禁替代逐行审查。若用户希望逐批把关，选 A2 并指定批量大小。

**职责分离（签发行为的外部证据）**，两种执行模式二选一：

1. **agent 备稿 + 用户 merge 签发**：agent 在分支上机械生成全部 revocation 块与 frontmatter 同步（`by_actor_id` 写用户已注册的真实身份，`revoked_at` 写用户批准本计划的时刻），**PR 由用户亲自 review 并 merge**。merge 是 GitHub 记录下的真实人类动作，构成签发证据；agent 被 goal 禁止 merge。用户在 merge 前对照本计划的验收表核验。
2. **用户本地亲自执行**：agent 只交付生成脚本的规格（或用户手工操作清单），用户本地运行、自己 commit 并 push。人类署名最彻底，代价是用户操作量大。

**每批（或全量批）验收命令与期望值**：

```bash
.tmp/agent-venv/bin/python tools/check_active_goal.py            # 执行 goal 的 baseline 写终态
.tmp/agent-venv/bin/python tools/validate_source_audits.py --all   # SOURCE_AUDITS_OK checked=1287
.tmp/agent-venv/bin/python tools/validate_review_records.py --all  # REVIEW_RECORDS_OK checked=1284
.tmp/agent-venv/bin/python tools/validate_trust_state.py --all --baseline-mode
#   全量后：TRUST_STATE_OK canonical_content=697 source_records=1287 review_records=1284
#           legacy_unbound=642 evidence_bound_review=0 verified=0 approved=0
.tmp/agent-venv/bin/python tools/content_inventory.py --write && \
.tmp/agent-venv/bin/python tools/content_inventory.py --check
#   自动块联动：source_audited_files 645→3（仅剩 3 条 agent PARTIAL）
.tmp/agent-venv/bin/python tools/sync_legacy_mirrors.py --write    # edge-computing-survey、jupiter 两对镜像
.tmp/agent-venv/bin/python tools/validate_frontmatter.py --all
.tmp/agent-venv/bin/python -m unittest discover -s tests -v
.tmp/agent-venv/bin/mkdocs build --strict --site-dir .tmp/site
git diff --check
```

连带更新（同一执行 goal 的 allowed_mutations 必须逐项覆盖）：`data/source-audits/`、`data/review-records/`、`data/trust-authorities.yml`、`docs/*/papers/*.md`（仅 frontmatter 双状态字段，正文一个字节都不能动，否则 STRUCTURAL 审计全部 STALE）、`papers/computing/edge-computing-survey/index.md` 与 `papers/intelligence/jupiter/index.md`（声明镜像，整文件字节一致，`tools/sync_legacy_mirrors.py` 第 112–117 行）、`data/content-inventory.json` 及 6 处 Markdown 自动块、`ops/` goal 文件、`CHANGELOG.md`。README/progress/ROADMAP 的手写段落也应在同批把"642 篇投影来自占位记录"的表述更新为"已由 governance 撤销"。

### 路径 B（schema 封死，仅记录为不可行）：agent supersede 降级

第一节第 2 点已给出三重封锁的行号证据。此路径无论怎么组合 outcome/transition 都无法把投影从 `VERIFIED` 拉下来，且伪造 `from` 会被图校验拒绝。**不可行，不再考虑。**

### 路径 C（否决）：删除记录文件或改写历史

机械上最简单（`verified` 立即归零），但：违反 AGENTS.md"观察历史必须保留"与"不通过删除历史记录制造通过"；销毁的恰恰是伪造行为的证据本身；`legacy_unbound` 等派生语义随之失真。**否决。**

## 四、需要用户决定的事项

1. **governance 身份**：注册什么 `actor_id`（建议 `human-estelledc-governance`，必须是真实仓库 owner 身份）。
2. **编排**：A1 单 goal 全量（推荐）还是 A2 分批（若分批，指定批量大小）。
3. **执行模式**：agent 备稿 + 用户 merge 签发（推荐），还是用户本地亲自执行。
4. **`revoked_at` 口径**：建议用用户批准执行 goal 的时刻，写入全部 revocation 块。
5. 批准后需要两个新 goal：先"registry 注册"（小），后"撤销执行"（大，per 上表授权 `data/` 与 frontmatter 变更）。IOT-T066 本身不执行任何一步。

## 五、本计划自身的验证

本文档随 IOT-T066 交付，该 goal 的验收命令证明计划阶段未动任何数据：`validate_source_audits --all` 仍为 1287、`validate_review_records --all` 仍为 1284、`validate_trust_state --all --baseline-mode` 仍为 `verified=642 approved=642`（与 main 基线逐字节一致）。上述行号引用可用 `rg -n` 在对应文件中复核。
