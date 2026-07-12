# IoT Reading Station Agent 推进契约

本文件只规定项目的推进方式，不定义无限期内容目标。所谓“持续推进”，是同一份有限 `run contract` 内连续完成多个可独立验收的切片；不是沿着 ROADMAP、旧计划或文章数量目标自动无限续跑。

## 权威顺序

发生冲突时按以下顺序处理：

1. 用户在当前会话中的明确目标、范围与外部动作授权。
2. 当前工作树和实时校验命令得到的事实。
3. `ops/active-goal.yml` 中状态为 `ACTIVE` 的唯一运行目标。
4. 当前 schema、`docs/content-schema.md`、`docs/architecture/release-policy.md` 与 CI 门禁。
5. `ROADMAP.md` 只提供方向；带日期的 plan、Web handoff、daily、Changelog 和 commit message 只提供历史背景。

任何标为 `SUPERSEDED` 的计划都不能授权执行。`docs/progress.md` 不是 agent 队列，不能覆盖 active goal 或实时状态。

## 开始前

1. 把本目录视为独立 Git 仓库。检查当前分支、`git status --short --branch`、现有 diff 和本地相对远端的提交；既有改动属于用户，不覆盖、不清理、不自动 rebase。
2. 读取并校验 `ops/active-goal.yml`：

   ```bash
   test -x .tmp/agent-venv/bin/python || python3.11 -m venv .tmp/agent-venv
   .tmp/agent-venv/bin/python -m pip install --require-hashes -r requirements.lock
   .tmp/agent-venv/bin/python -c "import sys, jsonschema, yaml; assert sys.version_info[:2] == (3, 11)"
   .tmp/agent-venv/bin/python tools/check_active_goal.py
   ```

3. 所有项目命令统一使用 `.tmp/agent-venv/bin/python`。它必须满足 `.python-version`，并按 `requirements.lock` 安装依赖。不要使用仓库现存 `.venv`，也不要假设系统 `python3` 已满足合同。
4. 用 active goal 列出的实时命令重取 inventory、trust、测试与构建基线。不要相信 handoff 中的数量快照。
5. 激活前确认 `AGENTS.md`、goal、lock、schema、checker 和测试已经进入同一个可追溯 Git 基线；若这些契约文件仍是未跟踪或未提交改动，停止并先完成方式变更的独立提交。
6. `PREPARED`、`PAUSED`、`BLOCKED`、`COMPLETE` 或 `SUPERSEDED` 状态只允许只读调查和契约维护，不允许写业务文件。`CLOSING` 只允许运行收口门禁和更新状态。只有用户明确启动同一个 goal 后，才能记录 activation ref、首批选择并切到 `ACTIVE`。

## Run contract

- 同时只能有一个 `ACTIVE` goal、一个可写切片和一个 writer。只读调查可以并行，但子 agent 不得同时修改同一工作树。
- 预算、允许路径、禁止路径、独立验收、external outcome 和停止条件只从 `ops/active-goal.yml` 获取；不得在执行中静默扩大。
- `ops/active-goal.lock.json` 冻结目标、预算、路径、验收和外部权限。普通执行只可更新 goal 的状态、选择、进度、D 轴和下一动作；lock 不匹配时立即停止。修改或重签 lock 属于新的推进方式变更，必须有用户明确授权。
- 首批必须使用 active goal 的 `first_batch_articles`。首批验收通过后，才可在同一 goal 的总预算内扩大；不需要逐片重新询问。
- goal 完成后立即收口。不得自行从 ROADMAP、历史 backlog 或下一个编号选择新 goal。
- commit、push、开 PR、merge、deploy 分别授权。只有当前用户指令和 `external_action_authority` 同时允许时才能执行。

## 单切片循环

1. 记录最小基线，区分原有失败与本切片回归。
2. 在 `selection.selected_articles` 中冻结本批对象及选择理由。证据不足时停止，不从标题猜来源、作者、结论或审核状态。
3. 若改工具或合同，先写能失败的定向测试；若只写证据记录，先写出会拒绝错误记录的验收断言。
4. 只修改 `allowed_mutations` 覆盖的文件。发现必须越界的问题时记录 blocker，不顺手修。
5. 先跑定向测试，再跑 active goal 的逐切片 `acceptance_checks`；结束前运行 `git diff --check`。
6. 对照基线记录 measurable delta、未覆盖风险、D/K 轴变化和本批是否产生 external delta，然后更新 `progress`、`review_after` 和 `next_action`。
7. 本批通过、预算未耗尽且下一切片仍属于同一 goal 时，直接继续。最后一批完成后切到 `CLOSING`，运行 `GOAL_CLOSE` 门禁；全部通过才切到 `COMPLETE`。

## IoT 可信状态硬边界

- `STRUCTURAL` 只证明结构检查，不能提升 `source_status` 或 `review_status`。
- 不把正文已存在、AI 已重写、测试通过或 agent 审阅写成 `VERIFIED` / `HUMAN_APPROVED`。
- `HUMAN_APPROVED` 必须来自外部 review record、当前正文 hash、真实人类 authority 和职责分离；agent 不能自报成人类。
- frontmatter 双状态是派生缓存，权威证据是 source audit、review record、authority registry 与当前正文 hash。
- 正文、frontmatter、legacy mirror、review record 和版本文件默认只读，除非 active goal 逐项授权。
- `data/trust-migration-ledger.yml` 的观察历史必须保留；不得用 squash、rebase 或历史重写破坏其祖先关系。
- 不通过放宽 schema、删除历史记录、跳过 baseline mode 或改测试期望制造“通过”。

## 验证层级

推进方式本身的最小门禁：

```bash
.tmp/agent-venv/bin/python tools/check_active_goal.py
.tmp/agent-venv/bin/python -m unittest tests.test_active_goal -v
git diff --check
```

业务切片使用 `ops/active-goal.yml::acceptance_checks`。涉及 trust 投影时至少跑定向 trust 测试和仓库 trust 命令；跨层或 goal 收口时再跑全量 unittest、严格 MkDocs 构建和现有 CI 对应门禁。

## 停止与交接

出现 active goal 任一 `stop_conditions`、预算耗尽、工作树重叠、基线不可复现、必须放宽门禁、需要新权限或没有证据充分的下一切片时，立即停止。

收尾只更新 `ops/active-goal.yml`：

- `progress`：已完成批次、对象、最后结果和无 external delta 批次数；
- `status`：`CLOSING`、`PAUSED`、`BLOCKED`、`COMPLETE` 或 `SUPERSEDED`；
- `next_action`：一条可直接执行的下一动作，或明确为空；
- `superseded_by`：只有新 goal 已被用户明确建立时才填写。

连续 3 个 agent 批次没有 external delta 必须暂停。测试数、文章数、commit 数、页面数和 agent 数只算成本或 K 轴证据，不能单独提升 D 轴。
