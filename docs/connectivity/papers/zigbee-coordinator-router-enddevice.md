---
schema_version: '1.0'
id: zigbee-coordinator-router-enddevice
title: Zigbee协调器/路由器/终端设备角色分析
layer: 2
content_type: technical_analysis
difficulty: beginner
reading_time: 16
prerequisites:
  - zigbee-3-0-protocol-stack
tags:
  - Zigbee
  - 协调器
  - 路由器
  - 终端设备
  - Mesh角色
  - 信任中心
  - 低功耗
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# Zigbee协调器/路由器/终端设备角色分析

> **难度**：🟢 初级 | **领域**：Zigbee 网络基础 | **阅读时间**：约 16 分钟

## 日常类比

公司组织：总经理创建公司、定规则（协调器 Coordinator）；部门经理上传下达、扩展覆盖（路由器 Router）；员工做好本职、不负责传话（终端 End Device）。角色选错——让“员工”通宵传话——网络不稳或电池速死[1][2]。

## 摘要

对比三角色在建网、路由、子设备接纳、休眠与信任中心上的能力边界，并给出供电与部署建议。子设备容量与表项上限依栈实现，**勿把理论最大值当设计值**[3][5]。

## 1. 能力矩阵

| 能力 | 协调器 | 路由器 | 终端 |
|------|--------|--------|------|
| 创建网络 | 是 | 否 | 否 |
| 路由转发 | 是 | 是 | 否 |
| 允许子节点加入 | 是 | 是 | 否 |
| 可深睡 | 否 | 否 | 是 |
| 信任中心（典型） | 是 | 否 | 否 |

每网通常一个协调器；路由器扩展射频覆盖与子树；终端挂到父节点，由父缓存下行[1][4]。

## 2. 协调器

扫描信道、选 PAN ID、分配短地址、管理密钥与准入。同时可作路由器参与转发。故障时整网管理面受创，故 Hub 供电与备份重要[2]。

## 3. 路由器

必须常供电（灯、插座、有电线关是常见载体）。邻居过少会形成脆弱桥；过多子设备可能触达栈表项上限。部署目标：关键路径上有冗余路由，避免单点走廊[3][5]。

## 4. 终端

电池传感/遥控典型角色：不中继，与父节点同步唤醒取缓存。父节点丢失需重关联，期间可能丢下行；父节点应选稳定市电路由[4]。

| 设备例子 | 推荐角色 | 原因 |
|----------|----------|------|
| 网关/Hub | 协调器 | 建网与密钥 |
| 智能灯/插座 | 路由器 | 市电 + 扩覆盖 |
| 门窗/温湿度 | 终端 | 电池寿命 |
| 电池墙贴开关当路由 | 错误 | 无法持续中继 |

## 5. 局限、挑战与可改进方向

### 1. 路由密度不足

**局限**：大户型只有几个路由，末端不稳。
**改进**：按平面图强制市电路由密度；验收抽测多跳 PER。

### 2. 终端挂错父节点

**局限**：挂到边缘弱链路父节点，频繁丢包。
**改进**：安装时看 LQI/RSSI；允许重新入网优化父选择。

### 3. 协调器不可替换认知

**局限**：用户随意断电网关导致全屋失控。
**改进**：UPS/说明文档；评估支持备份的商业 Hub。

### 4. 角色与 Matter/Thread 混淆

**局限**：把 Thread Router/SED 概念直接套用。
**改进**：培训区分协议角色名；混网项目画清角色图。

## 6. 实践要点

1. 设计阶段先标市电可路由点，再铺电池终端。
2. 监控子设备数、邻居数与路由表使用率。
3. 不要把电池设备配置成路由器。

## 参考文献

[1] CSA, Zigbee Specification — device types / node capabilities.
[2] CSA, Trust center and network formation documentation.
[3] Silicon Labs / NXP Zigbee routing table and child table limits (stack AN).
[4] IEEE 802.15.4, parent-child and indirect transmission concepts.
[5] Zigbee deployment best-practice guides (vendor / alliance).
[6] Mesh self-healing behavior notes for router failure scenarios.
[7] Power-supply requirements for FFDs vs RFDs in 802.15.4 terms.
[8] Smart-home hub high-availability recommendations.
[9] LQI/RSSI based parent selection literature in Zigbee nets.
[10] Comparison with Thread Router / SED roles (conceptual contrast).
[11] CSA certification notes affecting role behavior consistency.
