---
schema_version: '1.0'
id: dynamic-spectrum-access
title: 动态频谱接入技术：从固定车道到智能导航
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - cognitive-radio-spectrum
  - frequency-band-regulation-iot
  - iot-spectrum-sharing-dynamic
tags:
  - DSA
  - CBRS
  - NR-U
  - 频谱感知
  - LBT
  - 认知无线电
  - SAS
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 动态频谱接入技术：从固定车道到智能导航

> **难度**：🟡 中级 | **领域**：频谱管理、认知无线电、IoT 连接 | **阅读时间**：约 20 分钟

## 日常类比

八车道高速若永久分给固定物流公司，凌晨空车道也不能借——这就是静态频谱分配。动态频谱接入（Dynamic Spectrum Access, DSA）像实时导航：先查空闲车道，行驶中持续感知，主人回来就平滑变道。物联网（Internet of Things, IoT）连接规模上升而可用频段增长有限，DSA 是缓解“频谱荒”的路径之一；文中占用率、连接数等为公开测量/预测量级，**不可当本地规划硬指标**[4][7]。

## 摘要

梳理授权/免授权/共享三类频谱模式，对比数据库驱动与感知驱动两条 DSA 路线，说明公民宽带无线电服务（Citizens Broadband Radio Service, CBRS）、先听后说（Listen-Before-Talk, LBT）与 NR-U 共存机制，并概述机器学习辅助频谱管理。选型与门限须按监管与实测校准[1][3][8]。

## 1 三种使用模式

| 模式 | 典型频段/例 | 优势 | 代价 |
|------|-------------|------|------|
| 授权 Licensed | 运营商拍卖频段（如 n41/n78） | 干扰可控、QoS 可谈 | 牌照与部署成本高 |
| 免授权 Unlicensed | ISM 2.4/5/6 GHz | 准入低 | 公地干扰、功率受限 |
| 共享 Shared | 美国 CBRS 3.5 GHz | 分级保护 + 机会接入 | 需 SAS/感知基础设施 |

CBRS 三级示意[1]：

| 层级 | 用户 | 优先级 | 保护机制 |
|------|------|--------|----------|
| Tier 1 Incumbent | 既有用户（如雷达） | 最高 | ESC 感知 + SAS 疏散 |
| Tier 2 PAL | 拍卖持有者 | 中 | 县级等地理独占 |
| Tier 3 GAA | 一般授权接入 | 低 | 尽力而为 |

## 2 两大技术路线

### 2.1 数据库驱动

设备发射前向频谱可用性数据库（如 TVWS WSDB、CBRS SAS、6 GHz AFC）上报位置与设备参数，取回可用信道、最大等效全向辐射功率（EIRP）与有效期[1][9]。

```
设备 → (坐标, 设备参数) → SAS/WSDB/AFC
设备 ← (可用频段, 最大功率, 有效时间)
```

适合需确定性保护主用户、可联网的网关/基站；查询延迟常为秒级量级，移动场景需按速度刷新缓存。

### 2.2 感知驱动

设备侧能量检测、特征检测或协作感知判断占用。能量检测实现简单，但对噪声不确定与隐藏终端敏感；门限需按虚警/漏检目标用 ROC 整定，而非照搬单一 dBm 数[4]。

| 维度 | 数据库驱动 | 感知驱动 |
|------|-----------|----------|
| 实时性 | 常秒级（查询） | 可达毫秒级本地判决 |
| 可靠性 | 监管侧确定性信息 | 受噪声/衰落影响 |
| 隐藏终端 | 基本不存在 | 严重 |
| 部署成本 | 需基础设施 | 设备侧算力/射频 |
| 标准化 | FCC/ETSI 等较成熟 | 研究与部分标准并存 |
| IoT 适用 | 常经网关代理查询 | 极低功耗端难持续感知 |

## 3 共存：LTE-U / LAA / NR-U

蜂窝进入 5/6 GHz 免授权频段须与 Wi-Fi 等公平共存[3][8]：

| 技术 | 标准脉络 | 共存机制 | 频段倾向 |
|------|----------|----------|----------|
| LTE-U | 非 3GPP 早期 | CSAT 占空比 | 5 GHz |
| LAA | 3GPP Rel-13 | LBT | 5 GHz |
| eLAA | Rel-14 | LBT + 上行 | 5 GHz |
| NR-U | Rel-16/17 | LBT Cat 等 | 5/6 GHz |
| NR-U Light / RedCap | Rel-18 方向 | 简化接入 | 面向更轻终端 |

LBT 流程概要：感知忙则随机退避；空闲则在最大信道占用时间（MCOT，常见数 ms～十余 ms 量级，视优先级）内发送。具体类别与参数以 3GPP TS 37.213 为准[3]。

## 4 效率度量与占用观察

常用指标：频谱效率（bps/Hz 或加地理维度）、时间-空间占用度、频谱空洞（空闲资源块）。多地测量常显示：低频段城市占用相对高，更高频段空闲更多——**具体百分比随城市、时段、测量方法变化很大**，下表仅作量级示意，部署前须本地扫频[7]。

| 频段量级 | 城市核心倾向 | 农村倾向 |
|----------|--------------|----------|
| 亚 GHz～2 GHz | 占用相对高 | 明显更低 |
| 2～6 GHz | 中等、空洞增多 | 大量空闲 |
| 6 GHz+ | 往往很低 | 极低 |

## 5 机器学习辅助（可选）

| 任务 | 常见方法 | 输入 | 输出 |
|------|----------|------|------|
| 占用预测 | LSTM/Transformer 等 | 历史占用序列 | 未来时隙占用概率 |
| 信号识别 | CNN 等 | IQ/频谱图 | 主/次用户类别 |
| 功率/接入 | DRL（DQN/PPO 等） | 信道与干扰状态 | 功率或接入动作 |
| 分配 | 图神经网络等 | 拓扑与需求 | 频率规划 |

联邦学习可在不共享原始感知样本下协作训练预测模型；公开实验中的准确率数字依赖数据集与节点数，**不可外推为产品 SLA**[5]。低功耗 IoT 端更宜把重模型放在网关，终端只做轻量策略或查库。

## 6 实践要点

1. 先读清目标市场监管（CBRS SAS、TVWS、AFC、ETSI 等），再谈算法。
2. 能量检测：从目标 \(P_d\)/\(P_{fa}\) 反推门限与感知时长；感知过长会吃吞吐。
3. 数据库结果在有效期内缓存；步行/车载刷新周期应不同。
4. 室内补容可评估 6 GHz；企业专网可评估 CBRS 等共享带；RedCap/轻量 NR-U 功耗需实测。

## 7 局限、挑战与可改进方向

### 1. 感知不可靠与隐藏终端

**局限**：单点能量检测在深衰落或障碍后易漏检主用户，引发有害干扰[4]。
**改进**：协作感知、数据库优先、提高保护余量；IoT 网关集中感知再下发可用集。

### 2. 查询延迟与移动性

**局限**：SAS/AFC 往返与证书开销使秒级决策难支撑高速移动细粒度跳频。
**改进**：预测性预取信道列表；按速度分级刷新；路边单元/网关代查。

### 3. 与 Wi-Fi 共存争议

**局限**：LBT/CSAT 参数不对称时，蜂窝与 Wi-Fi 吞吐公平性依赖场景，实验室结论难直接搬用[3][8]。
**改进**：同址实测空闲信道评估（CCA）统计与占空比；室内优先错开主用信道。

### 4. 端侧算力与合规证据

**局限**：DRL/深度感知模型难进 MCU；监管更认可审计的数据库与认证设备。
**改进**：云/边训练、端侧查表策略；保留查询与退避日志以备审计[1][9]。

## 8 总结

DSA 把“固定车道”变为可查询、可感知、可退避的共享。IoT 落地优先数据库/网关代理与合规 LBT，机器学习作增强而非替代监管接口；一切占用率与性能数字以本地测量为准。

## 参考文献

[1] FCC, "Report and Order: Rules for the 3.5 GHz Band," FCC 15-47, 2015 (amended).
[2] ETSI, "Reconfigurable Radio Systems; Cognitive Radio System Concepts," EN 303 387 (相关版本).
[3] 3GPP TS 37.213, "Physical layer procedures for shared spectrum channel access."
[4] I. F. Akyildiz et al., "NeXt generation/dynamic spectrum access/cognitive radio wireless networks: A survey," Computer Networks, 2006.
[5] S. Yin et al., "Federated Deep Reinforcement Learning for Dynamic Spectrum Access," IEEE Trans. Wireless Commun. (及相关研究).
[6] NTIA, "National Spectrum Strategy" / Implementation Plan, U.S. DoC.
[7] Spectrum occupancy measurement surveys (IEEE COMST 及同类综述中的多城测量汇总).
[8] Qualcomm / 产业白皮书, "NR-U: Unlicensed Spectrum for 5G NR."
[9] CBRS SAS 部署与架构实践文献（如 DySPAN 等会议中的 SAS 运营经验）.
[10] Y. Zhang et al., "Blockchain-Enabled Spectrum Trading" 及相关动态频谱市场研究, IEEE JSAC 等.
[11] IEEE 802.11ax/be 与 6 GHz AFC 相关规范与监管文件.
[12] 3GPP 关于 NR RedCap / 共享频谱接入的 Release 说明.
