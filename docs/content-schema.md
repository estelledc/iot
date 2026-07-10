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
