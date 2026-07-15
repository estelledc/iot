# 发布与变更规则

## 版本口径

项目使用语义化版本：

- **major**：公开 URL 或内容 schema 出现不兼容变化；必须提供迁移或重定向方案。
- **minor**：新增目录、搜索、质量门禁或生产流水线能力。
- **patch**：修复事实、链接、样式或工具缺陷，不改变公开契约。

`VERSION` 是当前版本的唯一机器可读来源，`CHANGELOG.md` 的最新版本必须与它一致。

## 每批变更必须记录

1. 至少一个 `IOT-Txxx`；修复问题时同时记录 `IOT-Fxxx`。
2. 影响文件和是否存在迁移要求。
3. 可在干净工作树复现的验证命令。
4. 审查基线 commit；使用交接包时记录 ZIP SHA-256，但不能记录本机路径。

## 部署验收 SHA 口径

`data/deploy-acceptance.yml` 的 `target_sha` 指**被验收的内容提交**，不是写入验收记录的收口提交。原因是验收记录提交本身也会触发一次新的 Pages deploy；如果要求记录提交的 SHA 也写进同一个记录，会形成“记录验收 -> 新 SHA -> 再记录验收”的无限收口。

收口提交仍必须满足两点：

1. `data/deploy-acceptance.yml` 通过 `tools/check_deploy_acceptance.py --file ... --target-sha <被验收内容提交>`。
2. 收口提交 push 后，Repository quality 与 Pages deploy 也必须成功，证明记录本身没有破坏站点。

## 批次边界

- 一个批次只处理一个并行组或一个可回滚主题。
- 机械元数据迁移不能和文章正文重写混在同一批。
- 只有自动门禁通过且必要的手工验收有证据时，才能把任务标为 `VERIFIED`。
- Layer 3–8 扩容必须先通过 shadow pilot，正式发布每批最多 5 篇。

## 验证

```bash
python tools/check_release_metadata.py --version-file VERSION --changelog CHANGELOG.md
git diff --check
```
