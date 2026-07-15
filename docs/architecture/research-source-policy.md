# 研究来源检索与 fallback 规则

## 目标

新增论文初读卡或事实核验前，必须先确认来源检索链路可复现。这里的“可复现”不是要求所有外部服务永远可用，而是要求当主工具不可用时，能记录失败事实、使用明确 fallback，并保留边界说明。

## 当前链路状态

2026-07-15 复测结果：

| 通道 | 命令 | 结果 | 处理 |
| --- | --- | --- | --- |
| LightRead 认证 | `lr auth status --verify --format json` | `verify.valid=true` | 可作为 CLI 配置可读的证据 |
| LightRead arXiv 搜索 | `lr search arxiv "Internet of Things edge intelligence" --limit 2 --format json` | 成功返回 arXiv 论文条目 | 可用于 arXiv 初筛 |
| LightRead scholar 搜索 | `lr search scholar "Internet of Things edge intelligence" --limit 2 --format json` | 返回“API Key 无效或已过期” | 不作为当前必经检索通道 |

注意：认证状态可用不等于所有 backend 都可用。后续不能只凭 `auth status` 判断 `scholar` 可用。

## 检索顺序

1. **先跑 smoke test**：每轮批量研究前，先执行一条小查询确认目标 backend。
2. **优先使用结构化输出**：`--format json`，保留题名、作者、年份、URL、来源通道。
3. **只用可用 backend**：
   - arXiv 初筛：可用 `lr search arxiv ... --format json`。
   - Scholar 初筛：只有 smoke test 通过时才使用。
   - Scholar 失败时，不重试超过 2 次，不把认证状态写成搜索可用。
4. **fallback 到公开 arXiv API**：
   - 仅用于 arXiv 元数据和摘要级初读卡。
   - 查询间隔至少 3 秒，遇到 HTTP 429 必须降速或停止。
   - 卡片中写明“基于 arXiv 元数据、摘要和公开条目信息”，不得写成全文核验。

## 记录字段

每次新增初读卡或事实核验前，至少记录：

- `query`：英文检索 query。
- `backend`：`lr-arxiv`、`lr-scholar`、`arxiv-api` 等。
- `checked_at`：UTC 时间。
- `result_boundary`：metadata / abstract / PDF full text / claim verification。
- `failure`：失败 backend 的错误摘要，不记录 API key、token、账号密钥或本机私密路径。

## 停止条件

出现以下情况时停止扩容，转为复盘或人工确认：

- 所有可用来源都只能从标题猜测论文身份。
- 需要把未读 PDF 写成 `PARTIAL` / `VERIFIED` 才能通过。
- 检索工具返回认证或权限错误，且没有公开 fallback。
- arXiv API 触发 429 后仍无法降速恢复。
- 目标论文元数据不足以填写 `target_paper.title`、`year` 和 `url`。

## 与可信状态的边界

检索成功只证明“找到了候选来源”，不能提升 `source_status` 或 `review_status`。

- 元数据/摘要级卡片：保持 `UNVERIFIED / UNREVIEWED`。
- PDF 全文逐段核验：仍不能自动升格，除非有合法 source audit 记录。
- claim-level 核验：必须通过 source audit / review record / authority registry 的完整证据链。

## 后续工具债

- 修复或重新配置 LightRead scholar backend。
- 给批量研究保存一份脱敏 `source-selection-log`，避免只把来源散落在对话里。
- 让内容扩容 active goal 能表达真实 `max_articles`，不再靠 allowed paths 间接冻结篇数。
