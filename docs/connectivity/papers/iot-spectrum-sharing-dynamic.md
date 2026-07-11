---
schema_version: '1.0'
id: iot-spectrum-sharing-dynamic
title: IoT动态频谱共享与频谱数据库
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - dynamic-spectrum-access
  - cognitive-radio-spectrum
tags:
  - 动态频谱共享
  - CBRS
  - SAS
  - LSA
  - 频谱数据库
  - GAA
  - DSA
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT动态频谱共享与频谱数据库

> **难度**：🔴 高级 | **领域**：频谱管理 | **阅读时间**：约 22 分钟

## 日常类比

城市车道若永久分给个别车主，多数时间空置，而免费路段堵死。动态频谱共享（Dynamic Spectrum Sharing, DSS）像智能导航：查哪些授权“车道”空闲，临时借用，主人回来立刻让出[1][2]。

## 摘要

动态频谱接入（Dynamic Spectrum Access, DSA）含感知、数据库与混合三类。美国公民宽带无线电服务（CBRS）三层 + 频谱接入系统（SAS）是成熟实践；欧洲授权共享接入（LSA）偏两层、对免许可物联网不太友好。利用率与丢包改善数字高度场景化，**不可外推为普遍 KPI**[2][5]。

## 1. 稀缺与空洞

工业科学医疗（ISM）2.4 GHz 等承载 Wi-Fi/BLE/Zigbee 等，密集区易饱和；部分授权频段时空利用率波动大，存在频谱空洞。物联网规模化需要额外可靠频谱，DSS 是路径之一——**设备总量预测随来源变化，作趋势理解即可**。

| 频段（示意） | 主要用途 | 拥挤观感 |
|--------------|----------|----------|
| Sub-GHz ISM | LoRa 等 | 中–高（地区差） |
| 2.4 GHz | Wi-Fi/BLE/Zigbee | 常极高 |
| 5/6 GHz | Wi-Fi | 较高且在演变 |
| CBRS 3.55–3.7 GHz | 共享蜂窝/专用 | 受 SAS 协调 |

## 2. DSA 模型与数据库

| 模型 | 做法 | IoT 适用 |
|------|------|----------|
| 频谱感知 | 终端自听空闲 | 耗电、隐藏终端 |
| 地理数据库 | 报位置换频道/功率 | 较省电、可审计 |
| 混合 | 库给候选 + 本地确认 | 可靠但复杂 |

流程：设备报位置与能力 → 库结合现有用户保护规则算可用频道与等效全向辐射功率（EIRP）上限与有效期 → 到期前重查[2][5]。

## 3. CBRS 三层与 SAS

| 层 | 名称 | 要点 |
|----|------|------|
| 1 | Incumbent | 海军雷达等，最高保护 |
| 2 | PAL | 拍卖优先许可，让位于 1 |
| 3 | GAA | 免许可机会接入，物联网常用 |

| 设备类 | 功率量级（规则上限） | 覆盖观感 |
|--------|----------------------|----------|
| Category A | 较低（室内向） | 短距 |
| Category B | 较高（室外向） | 更远但约束多 |

SAS 注册、算干扰、分配频道、在现有用户活动时命令退避；环境感知能力（ESC）检测雷达等。动态保护区响应有监管时限要求，设计需能缓存与切频道[1][5]。

## 4. LSA 对比

| 特性 | CBRS | LSA |
|------|------|-----|
| 典型频段 | 3.55–3.7 GHz | 如 2.3–2.4 GHz 框架 |
| 层级 | 三层含 GAA | 两层为主 |
| 管控 | SAS | LSA 仓库+控制器 |
| IoT 友好 | GAA 较友好 | 多经运营商间接 |

## 5. 感知 vs 数据库

| 维度 | 感知 | 数据库 |
|------|------|--------|
| 基建 | 低 | 高 |
| 能耗 | 持续听则高 | 周期查询较低 |
| 隐藏终端 | 有 | 相对无 |
| 监管审计 | 难 | 易 |

物联网电池节点更倾向数据库或基站代理查询；时延敏感控制需评估查询与切换额外延迟（可达百毫秒量级），工业亚十毫秒级控制往往不适合纯机会共享[2]。

## 6. 案例要点（城市场景叙事）

密集 ISM 丢包升高时，可评估 CBRS GAA 小基站：带宽与协调更好，但功率与覆盖半径常小于 Sub-GHz LPWAN，基站密度上升。退避时段本地缓存、多候选频道可降低业务中断。对比表中的丢包率/速率为**案例叙事量级，非保证值**。

## 7. 局限、挑战与可改进方向

### 1. 可用性不确定

**局限**：GAA 无干扰保护，高层用户出现必须退避[1]。
**改进**：多候选频道；ISM 回退；非关键业务优先上 GAA。

### 2. 查询与切换时延

**局限**：唤醒、建链、查库、切频累加延迟。
**改进**：有效期缓存；空闲预刷新；基站代理 SAS。

### 3. 数据库误差

**局限**：传播模型与登记信息不准导致误分配。
**改进**：混合短感知确认；上报异常；选成熟 SAS 运营商。

### 4. 终端复杂度

**局限**：定位、多频、SAS 协议抬高成本。
**改进**：能力下沉到关口/小站；终端只做简单客户端。

## 8. 实践要点

1. 先判业务能否接受退避与秒级（或亚秒）额外时延。
2. CBRS 部署算清 Category 与站址密度，勿用 LoRa 站距硬套。
3. 始终保留 ISM 或授权锚备份通道。

## 参考文献

[1] FCC, 47 CFR Part 96, Citizens Broadband Radio Service.
[2] Sohul, M. et al., "Spectrum Access System for the Citizen Broadband Radio Service," IEEE Commun. Mag., 2015.
[3] ETSI, Licensed Shared Access (LSA) related TS (e.g. TS 103 235 family).
[4] Ghosh, A. et al., "5G Evolution..." IEEE Access, 2019 (spectrum context).
[5] Wireless Innovation Forum, SAS functional architecture (WINNF-TS-0112 et al.).
[6] FCC materials on ESC and DPA for CBRS incumbents.
[7] ITU reports on spectrum occupancy and sharing frameworks.
[8] Dynamic spectrum access survey literature (IEEE/Elsevier surveys).
[9] 6 GHz AFC / unlicensed sharing related FCC materials (adjacent topic).
[10] CBRS Alliance / OnGo deployment guides for enterprise and IoT.
[11] ETSI RRS (Reconfigurable Radio Systems) overview documents.
[12] Vendor SAS provider technical overviews (Google, Federated Wireless, etc.).
