# 内容进度与口径

> 这页只陈述可从仓库机械验证的事实。内容文件存在，不等于来源、事实或学习质量已经审核。

<!-- content-inventory:start -->
## 仓库事实总览

| 层级 | 方向 | 内容文件 | 显式导航 | 层级首页入口 | Plan 条目 | 目标容量 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Layer 1 | 感知与硬件 | 275 | 25 | 10 | 250 | 275 |
| Layer 2 | 无线接入 | 217 | 25 | 10 | 191 | 217 |
| Layer 3 | 网络协议 | 25 | 25 | 10 | 179 | 204 |
| Layer 4 | 计算平台 | 25 | 25 | 10 | 190 | 215 |
| Layer 5 | 边缘智能 | 25 | 25 | 10 | 301 | 326 |
| Layer 6 | 安全与隐私 | 25 | 25 | 10 | 197 | 222 |
| Layer 7 | 综合应用 | 25 | 25 | 10 | 205 | 230 |
| Layer 8 | 前沿方向 | 25 | 25 | 10 | 248 | 273 |
| **合计** | | **642** | **200** | **80** | **1761** | **1962** |

- **内容文件 642**：可被 MkDocs 构建，不等于已完成来源审计。
- **显式导航 200**：当前 `mkdocs.yml` 直接列出的内容文件。
- **层级首页入口 80**：八个概览页直接链接的内容文件。
- **Plan 条目 1761**：包含已执行和未执行计划，不能与现有文件直接相加。
- **来源审计**：尚无机器可读的全量记录，状态为 `NOT_TRACKED`。

生成与校验：

```bash
python tools/content_inventory.py --write
python tools/content_inventory.py --check
```
<!-- content-inventory:end -->

## 当前决策

- Layer 1–2 已有较大规模内容，Layer 3–8 各有种子内容和扩展计划。
- 在导航覆盖、内容 schema、来源抽样和可重复生产门禁完成前，暂停大批量扩展。
- 后续扩展先做 4 篇 shadow pilot，再以每批最多 5 篇发布。

## 相关入口

- [学习路线](roadmap.md)
- [Layer 1：感知与硬件](foundation/index.md)
- [Layer 2：无线接入](connectivity/index.md)
- [Layer 3：网络协议](network/index.md)
- [Layer 4：计算平台](computing/index.md)
- [Layer 5：边缘智能](intelligence/index.md)
- [Layer 6：安全与隐私](security/index.md)
- [Layer 7：综合应用](applications/index.md)
- [Layer 8：前沿方向](frontier/index.md)
