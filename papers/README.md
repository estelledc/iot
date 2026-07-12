# Legacy paper mirrors

本目录保留项目早期的两篇课程报告归档，不是站点内容的编辑入口。

站点唯一 canonical 正文位于：

- `docs/computing/papers/edge-computing-survey.md`
- `docs/intelligence/papers/jupiter.md`

由于现有学习正文按约束不可删除或作为独立正文手工重写，本目录文件暂时作为 `READ_ONLY_MIRROR` 保留。需要修改内容时只改 `docs/` 下 canonical 文件，再运行：

```bash
python tools/sync_legacy_mirrors.py --write
python tools/sync_legacy_mirrors.py --check
```

同步命令只允许从 `docs/` 单向生成 `papers/`，并保持两边全文件 SHA-256 一致；`tools/check_duplicates.py` 继续作为发布门禁。请勿手工双写 mirror。
