# IOT-T054 复盘：40 篇初读卡扩容后的不足与加固

## 结论

IOT-T054 已完成 40 篇论文初读卡扩容、697 篇内容基线和 Pages 部署，但它暴露出一个方向性问题：扩容速度已经跑在事实核验、来源稳定性和验收语义之前。下一轮不应继续追数量，而应优先修流程口径和事实证据链。

## 本轮已完成事实

- 新增 40 篇 `paper_reading` 初读卡，覆盖 Layer 3–8。
- 内容文件从 657 增至 697，catalog 与 inventory 已同步。
- 新增卡片均保持 `source_status: UNVERIFIED`、`review_status: UNREVIEWED`。
- trust projection 仍为 `verified=642`、`approved=642`，没有提升新增卡片可信状态。
- 内容提交 `4718949` 与收口提交 `daffb87` 均通过 Repository quality 与 Pages deploy。

## 不足

| 不足 | 影响 | 本轮处理 |
| --- | --- | --- |
| 论文来源工具不稳定：`lr auth status` 显示 valid，但 `lr search` 返回 API Key 失效 | 研究入口依赖临时 fallback，后续复现成本升高 | 复盘记录此问题；后续需要单独恢复 LightRead 或固定公开检索来源 |
| 40 篇一次性扩容过大 | reviewer 难以逐篇判断质量；新增内容只能是初读卡，不能替代事实核验 | 停止继续扩容；本轮转向流程加固 |
| active goal 对内容扩容仍使用 `max_articles=0` 绕开 article-selection policy | 合同里“新增 N 篇”的机器约束不直观，依赖 allowed paths 和 inventory 侧证 | 标为后续工具债；本轮不改 schema/tool，避免扩大范围 |
| 首页和测试中仍有静态数量断言 | 每次扩容都要手工同步，容易漏改 | IOT-T054 已补齐 697 基线；后续可考虑集中生成更多展示文案 |
| 部署验收 `target_sha` 语义容易混淆 | 如果追求“记录提交自身的 SHA”，会导致每次记录验收又触发新部署，形成无限收口 | 本轮更新发布规则：`target_sha` 指被验收内容提交；记录提交自身只需通过后续 CI/Pages |

## 下一步优先级

1. **先修 LightRead / 来源检索链路**：恢复 `lr search` 可用性，或给 arXiv fallback 写入明确操作记录。
2. **小批事实核验**：从新增 55 篇未核验内容中选 3–5 篇，做 PDF 全文核验或 claim-level source audit。
3. **合同工具债**：让内容扩容 goal 能表达 `max_articles > 0`，不再通过 `SOURCE_AUDIT_INVENTORY_PROJECTION + max_articles=0` 间接冻结篇数。
4. **展示口径去静态化**：减少首页和测试里的手写数量，优先从 inventory 派生。

## 本轮加固范围

IOT-T055 只做两件事：

1. 固化本复盘，作为后续推进前的检查点。
2. 在发布规则中明确部署验收 SHA 语义，避免后续重复追逐“最新记录提交”的 Pages 状态。

不新增论文、不修改 schema/tools/workflow、不创建 source/review record、不提升任何内容可信状态。
