---
schema_version: '1.0'
id: private-lte-cbrs-iot-deployment
title: 私有LTE CBRS频段IoT部署方案
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 18
prerequisites:
  - private-5g-networks
  - cellular-iot-evolution-2g-5g
tags:
  - 私有LTE
  - CBRS
  - SAS
  - CBSD
  - 企业专网
  - GAA
  - PAL
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 私有LTE CBRS频段IoT部署方案

> **难度**：🔴 高级 | **领域**：私有网络 | **阅读时间**：约 18 分钟

## 日常类比

仓库里上千台 AGV：Wi-Fi 像商场公共热点，切换易“断片”；公网蜂窝像合租带宽。私有 LTE 是厂区自管蜂窝；美国公民宽带无线电服务（CBRS, 3.55–3.7 GHz）用频谱接入系统（SAS）动态协调，企业常走免许可的一般授权接入（GAA）[1][2]。

## 摘要

架构：终端 —Uu— CBSD/eNB —S1— 本地 EPC（MME/S-GW/P-GW/HSS）— 企业应用。CBRS 三层：在位用户 > 优先接入许可（PAL）> GAA。相对 Wi-Fi：覆盖半径与移动性切换通常更稳；相对私有 5G：生态与模组更成熟、峰值能力较低。**覆盖米数、切换毫秒、TCO 美元均为场景绑定，须路测与报价**[3][4]。

## 1. CBRS 与设备档

| 层级 | 谁 | 要点 |
|------|-----|------|
| Incumbent | 海军雷达等 | 最高优先，他者避让 |
| PAL | 拍卖许可 | 有干扰保护 |
| GAA | 免许可 | 须让位，企业常用 |

| 参数 | Cat-A | Cat-B |
|------|-------|-------|
| 场景 | 室内为主 | 室外 |
| EIRP 上限量级 | 较低（室内） | 较高（室外） |
| 安装 | 标准认证 | 常需专业安装（CPI） |
| 用途 | 厂房/仓 | 园区/港/矿 |

SAS：注册位置与功率 → 授权频段 → Incumbent 活动时限时释放（规则见 FCC Part 96）[1]。

## 2. 为何 IoT 看私有 LTE

| 维度 | Wi-Fi 痛点 | 私有 LTE 倾向 |
|------|------------|---------------|
| 切换 | 易百毫秒级抖动 | 蜂窝切换更可控 |
| 调度 | CSMA 争用 | OFDMA 可调度/QoS |
| 干扰 | 2.4/5/6 GHz 拥挤 | 3.5 GHz SAS 协调 |
| 数据路径 | 视企业网设计 | 可完全本地 EPC |

QoS 用 QCI 区分 AGV 控制、视频、传感；控制面优先于尽力视频[3]。

## 3. 与私有 5G、他国框架

| 路线 | 适合 |
|------|------|
| 私有 LTE CBRS | 要成熟模组、中等时延 |
| LTE→5G NSA/SA | 已有 LTE 投资的演进 |
| 直接私有 5G SA | 强 URLLC/切片需求 |

| 地区 | 类似思路 |
|------|----------|
| 英国 | Shared Access 等 |
| 德国/日 | 本地 5G 许可 |
| 中国 | 工业互联网专网政策（以当期为准） |

## 4. 局限、挑战与可改进方向

### 1. GAA 无硬保障

**局限**：须避让 Incumbent/PAL，沿海等区域更敏感。
**改进**：关键产线评估 PAL；多载波与降功率预案；监控 SAS 连接。

### 2. 金属仓覆盖

**局限**：货架阴影使“一站数百米”失效。
**改进**：加密站址 + 定向天线；以热力图验收，不按空场半径采购。

### 3. 运维复杂度

**局限**：EPC、SIM、SAS、干扰排查超普通 IT。
**改进**：NaaS/集成商；双 EPC 冗余演练；变更先非生产验证。

### 4. 案例数字外推

**局限**：公开 ROI/停车次数多为单一仓库叙事。
**改进**：自建 Wi-Fi vs LTE A/B 对照；用停机损失算 TCO。

## 5. 实践要点

1. 先 RF 勘测与容量（峰值并发、上下行）。
2. 终端确认 Band 48/CBRS 认证与运营商无关的专网 PLMN 规划。
3. 切换参数与 AGV 路径联动，避免乒乓。

## 参考文献

[1] FCC, 47 CFR Part 96, Citizens Broadband Radio Service.
[2] CBRS Alliance, architecture and deployment guides.
[3] Nokia / Qualcomm private wireless & CBRS enterprise materials.
[4] MulteFire Alliance specifications (related shared/unlicensed LTE concepts).
[5] 3GPP LTE EPC architecture specifications (TS 23.401 et al.).
[6] WInnForum / SAS provider operational requirements summaries.
[7] UK Ofcom Shared Access and DE/JP local 5G regulator notes.
[8] Industrial AGV/AMR private LTE case studies (treat KPIs as site-specific).
[9] Comparison studies: Wi-Fi 6 vs private LTE in warehouses.
[10] CBSD Cat-A/B certification and CPI installation guidance.
[11] Private 5G migration path notes from LTE CBRS estates.
