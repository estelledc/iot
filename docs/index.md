---
template: home.html
title: 物联网全栈技术学习站
description: 从传感器、无线接入到边缘智能与 6G 前沿，用八层技术地图建立可导航、可检查的 IoT 全栈学习路径。
---

<section class="iot-hero" aria-labelledby="iot-title">
  <div class="iot-hero__copy">
    <p class="iot-hero__eyebrow">IoT SYSTEM ATLAS / 8-LAYER LAB</p>
    <div class="iot-hero__status">
      <span class="jx-chip" data-state="maintained">持续维护 · Maintained</span>
      <span><b>642 / 652</b> HUMAN_APPROVED</span>
      <span><b>642 / 652</b> SOURCE VERIFIED</span>
    </div>
    <h1 id="iot-title">先看依赖，再选择要深入的 IoT 层。</h1>
    <p class="iot-hero__lead">
      这不是 652 篇文章的陈列柜，而是一张可进入、可检查的系统地图。每层同时公开内容规模、上游依赖和审查状态；新增 10 篇保持 <code>UNVERIFIED</code> / <code>UNREVIEWED</code>，旧版 <code>NOT_TRACKED</code> 风险标签也会留在首屏，不被“内容很多”掩盖。
    </p>
    <p class="iot-hero__en" lang="en">Explore the stack as a dependency system. Every layer exposes its content volume and evidence state—without presenting review activity as source verification.</p>
    <div class="iot-hero__actions">
      <a class="jx-action" href="roadmap/">按依赖开始学习</a>
      <a class="jx-action jx-action--secondary" href="progress/">审查证据与口径</a>
      <a class="jx-action jx-action--secondary" href="https://github.com/estelledc/iot">检查仓库</a>
    </div>
    <p class="iot-hero__role"><strong>协作边界：</strong>Jason Xun 负责八层体系、里程碑、发布门禁与验收判断；AI 辅助资料研究、内容初稿、批量审查与站点实现，不自行授予 <code>VERIFIED</code> 或 <code>HUMAN_APPROVED</code>。</p>
  </div>

  <aside class="iot-stack-lab" aria-labelledby="stack-lab-title">
    <header class="iot-stack-lab__head">
      <div><span>DEPENDENCY MAP</span><strong id="stack-lab-title">选择一层，沿依赖进入</strong></div>
      <span class="iot-stack-lab__truth">TRUTH MODE · ON</span>
    </header>
    <ol class="iot-stack-map">
      <li><a href="frontier/"><span class="iot-stack-map__id">L8</span><strong>前沿方向</strong><small>25 files</small><em>IN_REVIEW</em><b>NOT_TRACKED</b></a></li>
      <li><a href="applications/"><span class="iot-stack-map__id">L7</span><strong>综合应用</strong><small>26 files · depends on L4–L6</small><em>MIXED</em><b>1 UNVERIFIED</b></a></li>
      <li><a href="security/"><span class="iot-stack-map__id">L6</span><strong>安全与隐私</strong><small>26 files · cross-cutting</small><em>MIXED</em><b>1 UNVERIFIED</b></a></li>
      <li><a href="intelligence/"><span class="iot-stack-map__id">L5</span><strong>边缘智能</strong><small>26 files · depends on L4</small><em>MIXED</em><b>1 UNVERIFIED</b></a></li>
      <li><a href="computing/"><span class="iot-stack-map__id">L4</span><strong>计算平台</strong><small>25 files · depends on L1–L3</small><em>IN_REVIEW</em><b>NOT_TRACKED</b></a></li>
      <li><a href="network/"><span class="iot-stack-map__id">L3</span><strong>网络协议</strong><small>25 files · depends on L2</small><em>IN_REVIEW</em><b>NOT_TRACKED</b></a></li>
      <li><a href="connectivity/"><span class="iot-stack-map__id">L2</span><strong>无线接入</strong><small>219 files · depends on L1</small><em>MIXED</em><b>2 UNVERIFIED</b></a></li>
      <li><a href="foundation/"><span class="iot-stack-map__id">L1</span><strong>感知与硬件</strong><small>275 files · foundation</small><em>IN_REVIEW</em><b>NOT_TRACKED</b></a></li>
    </ol>
    <div class="iot-stack-lab__legend" aria-label="审查状态图例">
      <span><i data-state="review"></i>正文进入审查</span>
      <span><i data-state="source"></i>新增卡片未核验；NOT_TRACKED 为历史风险标签</span>
      <a href="architecture/release-policy/">状态如何升级？</a>
    </div>
  </aside>
</section>

<section class="iot-case" id="project-proof" aria-labelledby="project-proof-title">
  <header class="iot-case__header">
    <p class="jx-eyebrow"><span class="jx-eyebrow__rule"></span>Project proof</p>
    <h2 id="project-proof-title">先把知识地图做成系统，再讨论规模。</h2>
    <p>这个项目解决的不是“再写一批 IoT 摘要”，而是让初学者知道技术之间怎样依赖，并让维护者能区分内容存在、可发现、已审查与已验证。</p>
  </header>

  <div class="jx-proof">
    <div>
      <span class="jx-chip" data-state="maintained">v0.2.2 · Maintained</span>
      <p class="jx-proof__summary">Markdown 是源真相，MkDocs 是交付面；确定性清单、frontmatter schema、目录生成器、链接检查和 CI 把八层内容组织成可重复构建的学习站。</p>
      <p class="jx-proof__summary-en" lang="en">The public value is not raw volume. It is a navigable eight-layer model backed by reproducible inventories, schema checks, generated catalogs, link audits and explicit review states.</p>

      <div class="jx-proof__metrics" aria-label="可机械验证的项目证据">
        <div class="jx-proof__metric"><strong>8</strong><span>层 IoT 技术体系</span></div>
        <div class="jx-proof__metric"><strong>652</strong><span>个内容文件，全部可发现</span></div>
        <div class="jx-proof__metric"><strong>M1</strong><span>治理基线已完成</span></div>
      </div>

      <div class="jx-proof__links" aria-label="项目证据入口">
        <a class="jx-pill" href="progress/">仓库事实与口径</a>
        <a class="jx-pill" href="architecture/release-policy/">发布与验收规则</a>
        <a class="jx-pill" href="content-schema/">内容元数据契约</a>
        <a class="jx-pill" href="https://github.com/estelledc/iot">公开仓库</a>
      </div>
    </div>

    <dl class="jx-proof__meta">
      <div><dt>Problem / 问题</dt><dd>IoT 横跨八层，单篇阅读容易失去依赖关系与学习顺序。</dd></div>
      <div><dt>Jason Xun / 决策与验收</dt><dd>定义分层与里程碑，锁定“先治理、再可信、后扩容”，并决定发布是否满足证据门槛。</dd></div>
      <div><dt>AI / 辅助</dt><dd>帮助研究、起草、批量深审和工程实现；自动门禁通过仍不能替代人工验收。</dd></div>
      <div><dt>System / 系统</dt><dd>Markdown → schema 与清单 → catalog 与搜索 → MkDocs Pages；CI 对结构、链接、来源状态和发布规则做回归。</dd></div>
      <div><dt>Evidence / 证据</dt><dd>652 个文件全部进入可发现目录；642/652 正文已有 <code>VERIFIED</code> / <code>HUMAN_APPROVED</code> 投影，新增 10 篇保持初读状态。</dd></div>
      <div><dt>Limitations / 局限</dt><dd class="jx-proof__limitation">全量来源审计仍为当前目标外的待补工作；<code>NOT_TRACKED</code> 是旧版风险标签，新增卡片必须继续走事实核验和人工审查后才能升级。</dd></div>
    </dl>
  </div>
</section>

<!-- content-inventory:start -->
<section class="iot-stats" aria-label="内容基线">
  <div class="iot-stats__item">
    <span class="iot-stats__num">8</span>
    <span class="iot-stats__label">技术层级</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">657</span>
    <span class="iot-stats__label">内容文件</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">200</span>
    <span class="iot-stats__label">显式导航</span>
  </div>
  <div class="iot-stats__item">
    <span class="iot-stats__num">1761</span>
    <span class="iot-stats__label">Plan 条目</span>
  </div>
</section>

<div class="iot-prose" markdown>

## 内容统计

| 层级 | 方向 | 内容文件 |
| --- | --- | ---: |
| Layer 1 | [感知与硬件](foundation/index.md) | 275 |
| Layer 2 | [无线接入](connectivity/index.md) | 219 |
| Layer 3 | [网络协议](network/index.md) | 25 |
| Layer 4 | [计算平台](computing/index.md) | 25 |
| Layer 5 | [边缘智能](intelligence/index.md) | 34 |
| Layer 6 | [安全与隐私](security/index.md) | 28 |
| Layer 7 | [综合应用](applications/index.md) | 26 |
| Layer 8 | [前沿方向](frontier/index.md) | 25 |
| **合计** | | **657** |

> 上表统计的是仓库中的内容文件，不代表来源和技术事实已经审核。显式导航、目录覆盖与扩展计划见[阅读进度](progress.md)。

</div>
<!-- content-inventory:end -->

<section class="iot-layers" aria-labelledby="layers-heading">
  <div class="iot-layers__header">
    <p class="iot-hero__eyebrow">Technology Stack</p>
    <h2 id="layers-heading">八层技术全景</h2>
    <p>从最底层的硬件感知到最前沿的 6G 研究，完整覆盖物联网全栈。</p>
  </div>
  <div class="iot-layers__grid">
    <a class="iot-layer-card" href="foundation/">
      <p class="iot-layer-card__eyebrow">Layer 1</p>
      <h3>感知与硬件</h3>
      <p class="iot-layer-card__desc">MCU、RTOS、MEMS 传感器、TinyML、能量收集——万物互联的「神经末梢」。</p>
      <span class="iot-layer-card__meta">Content catalog · Sensing & Hardware</span>
    </a>
    <a class="iot-layer-card" href="connectivity/">
      <p class="iot-layer-card__eyebrow">Layer 2</p>
      <h3>无线接入</h3>
      <p class="iot-layer-card__desc">BLE、星闪、LoRaWAN、5G RedCap、UWB——让设备开口「说话」。</p>
      <span class="iot-layer-card__meta">Content catalog · Wireless Connectivity</span>
    </a>
    <a class="iot-layer-card" href="network/">
      <p class="iot-layer-card__eyebrow">Layer 3</p>
      <h3>网络协议</h3>
      <p class="iot-layer-card__desc">MQTT、CoAP、TSN、DetNet、SDN——数据从端到云的「高速公路」。</p>
      <span class="iot-layer-card__meta">Content catalog · Network Protocols</span>
    </a>
    <a class="iot-layer-card" href="computing/">
      <p class="iot-layer-card__eyebrow">Layer 4</p>
      <h3>计算平台</h3>
      <p class="iot-layer-card__desc">边缘计算、Serverless、KubeEdge、任务卸载——离数据最近的「大脑」。</p>
      <span class="iot-layer-card__meta">Content catalog · Edge Computing</span>
    </a>
    <a class="iot-layer-card" href="intelligence/">
      <p class="iot-layer-card__eyebrow">Layer 5</p>
      <h3>边缘智能</h3>
      <p class="iot-layer-card__desc">联邦学习、模型压缩、协作推理、NAS——让 AI 在资源受限设备上「思考」。</p>
      <span class="iot-layer-card__meta">Content catalog · Edge Intelligence</span>
    </a>
    <a class="iot-layer-card" href="security/">
      <p class="iot-layer-card__eyebrow">Layer 6</p>
      <h3>安全与隐私</h3>
      <p class="iot-layer-card__desc">PUF 认证、TEE、零信任、差分隐私——万物互联的「免疫系统」。</p>
      <span class="iot-layer-card__meta">Content catalog · Security & Privacy</span>
    </a>
    <a class="iot-layer-card" href="applications/">
      <p class="iot-layer-card__eyebrow">Layer 7</p>
      <h3>综合应用</h3>
      <p class="iot-layer-card__desc">V2X、数字孪生、智慧农业、工业预测维护——技术落地的「试验田」。</p>
      <span class="iot-layer-card__meta">Content catalog · Applications</span>
    </a>
    <a class="iot-layer-card" href="frontier/">
      <p class="iot-layer-card__eyebrow">Layer 8</p>
      <h3>前沿方向</h3>
      <p class="iot-layer-card__desc">6G ISAC、语义通信、量子安全、AIGC 边缘生成——看见「后天」。</p>
      <span class="iot-layer-card__meta">Content catalog · Frontier Research</span>
    </a>
  </div>
</section>

<div class="iot-prose" markdown>

## 这是什么？

一个覆盖物联网全栈技术的中文学习站。每篇内容用“零基础也能读懂”的方式重写，不是翻译，而是用自己的话讲明白一个技术方向。

**适合谁**：对物联网感兴趣的任何人——无论你是刚接触 IoT 的本科生，还是想跨方向了解全景的研究者。

## 技术依赖图

```mermaid
graph TB
    L8[Layer 8: 前沿方向]
    L7[Layer 7: 综合应用]
    L6[Layer 6: 安全与隐私]
    L5[Layer 5: 边缘智能]
    L4[Layer 4: 计算平台]
    L3[Layer 3: 网络协议]
    L2[Layer 2: 无线接入]
    L1[Layer 1: 感知与硬件]

    L1 --> L2 --> L3 --> L4 --> L5 --> L6
    L4 --> L7
    L5 --> L7
    L6 --> L7
    L7 --> L8
```

## 如何使用

**如果你是零基础**：从 [Layer 1 感知与硬件](foundation/index.md) 开始，跟着[学习路线](roadmap.md)逐层向上。

**如果你有基础**：直接跳到感兴趣的层级。每层概览页会说明本层主题和建议起点。

**如果你在选研究方向**：先看[内容进度与口径](progress.md)，区分“文件存在”“进入导航”和“来源已审核”。

## 内容质量标准

每篇内容遵循统一生产流程（见仓库根目录 `SOP.md`）：

- 综述报告：目标为完整问题地图、可追溯参考来源和多维对比。
- 论文阅读报告：目标为问题、方法、证据、局限和可复现实验线索。
- 对比分析：至少覆盖三个对比维度，并说明适用边界。

现有内容仍需分层来源审计；“已构建”不能替代“事实已验证”。

</div>

<section class="iot-cta">
  <h2>从哪里开始？</h2>
  <p>零基础从 Layer 1 逐层向上；有基础可以直接进入感兴趣的层级。</p>
  <div class="iot-hero__actions">
    <a class="jx-action" href="roadmap/">查看学习路线</a>
    <a class="jx-action jx-action--secondary" href="https://github.com/estelledc/iot">查看 GitHub</a>
  </div>
</section>
