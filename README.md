# IoT Reading Station

物联网论文阅读站——覆盖边缘计算、协作推理、联邦学习、智能感知等 IoT 相关方向。

## 内容

- `papers/edge-computing-survey/` — 边缘计算与物联网综述
- `papers/jupiter/` — Jupiter: 边缘设备协作推理 LLM (INFOCOM 2025)

## 流程

每篇论文的内容生产流程见 [SOP.md](SOP.md)。

## 扩展计划

后续目标是部署为 GitHub Pages 站点（参考 [embodied-ai-reading-station](https://estelledc.github.io/embodied-ai-reading-station/)），需要：

1. 添加 `site/` 构建脚本（md → html）
2. 配置 `.github/workflows/deploy.yml`
3. 持续添加新论文（IoT 各方向均可）
