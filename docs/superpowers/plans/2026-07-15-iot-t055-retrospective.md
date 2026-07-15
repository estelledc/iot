# IOT-T055 复盘：部署口径加固后的剩余不足

## 结论

IOT-T055 解决了部署验收 `target_sha` 语义混淆，但它没有处理 IOT-T054 暴露出的另一个核心不足：研究来源检索链路不稳定。IOT-T056 选择继续推进这一点，先把可用通道、失败通道和 fallback 规则固化，避免下一轮研究继续依赖临时判断。

## T055 已解决的问题

- 新增 IOT-T054 复盘，明确 40 篇扩容只产生初读卡，不等于事实核验。
- 发布规则中明确 `data/deploy-acceptance.yml::target_sha` 指被验收内容提交，而不是记录提交。
- IOT-T055 两个提交均通过 Repository quality 与 Pages deploy。

## T055 后仍存在的不足

| 不足 | 影响 | IOT-T056 处理 |
| --- | --- | --- |
| LightRead backend 状态不一致：认证 valid，但 scholar 搜索失败 | 后续若默认走 scholar，会在批量研究中途失败 | 记录 smoke test 结果；规定 backend 必须先小查询验证 |
| arXiv fallback 曾只存在于对话和临时脚本里 | 复现路径不稳定，下一次 agent 可能不知道何时可用 | 新增 `research-source-policy.md`，固定 fallback 规则 |
| 批量研究缺少 `source-selection-log` | 只能从卡片反推来源选择，审查成本高 | 标为后续工具债，不在本轮改 tools/schema |
| 事实核验仍落后于内容数量 | 697 篇中 55 篇仍是初读状态 | 后续应选 3–5 篇做小批 claim-level 核验，而不是继续扩容 |

## 本轮验证事实

2026-07-15 UTC 复测：

- `lr auth status --verify --format json`：返回 `verify.valid=true`。
- `lr search arxiv "Internet of Things edge intelligence" --limit 2 --format json`：成功返回结构化 arXiv 条目。
- `lr search scholar "Internet of Things edge intelligence" --limit 2 --format json`：返回“API Key 无效或已过期”。

这些事实说明：LightRead CLI 不是整体不可用，而是至少存在 backend 分化；后续必须把 backend 粒度写进研究记录。

## 下一步

1. 修复或重新配置 LightRead scholar backend。
2. 为批量研究新增脱敏 `source-selection-log` 记录格式。
3. 从新增未核验内容中挑 3–5 篇做 PDF 全文核验或 claim-level source audit。
4. 再处理 active goal 的 `max_articles` 表达能力，不再用 `max_articles=0` 间接冻结内容扩容。
