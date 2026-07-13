---
schema_version: '1.0'
id: cognitive-radio-spectrum-sensing-iot
title: 认知无线电频谱感知在IoT中的应用前景
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags:
  - 认知无线电
  - 频谱感知
  - TVWS
  - 动态频谱接入
  - 协作感知
  - 能量检测
  - IoT频谱
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 认知无线电频谱感知在IoT中的应用前景

> **难度**：🔴 高级 | **领域**：频谱管理 | **阅读时间**：约 22 分钟

## 日常类比

公寓楼有 100 间房，同时只有约 20 间亮灯。若每户只能用“自己的房”，空房就浪费；若允许在空闲房活动且房主回来立刻退出，整栋利用率上升。无线电频谱类似：授权频段常有时间/空间空闲（频谱空洞），认知无线电（Cognitive Radio, CR）让次级用户在不干扰主用户（Primary User, PU）前提下机会式使用[1]。

## 摘要

物联网（Internet of Things, IoT）挤在工业科学医疗（ISM）免授权频段，而测量研究常报告授权频段平均利用率仅数成甚至更低（口径随频段与地点变化）[1][5]。本文对比能量检测、匹配滤波、循环平稳特征检测，说明电视白空间（TV White Space, TVWS）、地理位置数据库与协作感知，并强调感知–吞吐–能量三重权衡。案例中的网关数与丢包率为示意对比，非通用现场指标。

## 1. 稀缺与浪费并存

ISM（433/868/915 MHz、2.4 GHz 等）免许可但拥挤；电视/部分蜂窝子带等授权频谱存在空洞。CR 循环：观察 → 决策 → 行动 → 学习 → 主用户返回时退出（Vacate）[1]。

## 2. 感知方法

| 方法 | 先验知识 | 复杂度 | 低信噪比 | IoT 适用 |
|------|----------|--------|----------|----------|
| 能量检测 | 几乎无 | 最低 | 差（存在噪声不确定“SNR 墙”） | 最广 |
| 匹配滤波 | 信号模板完整 | 中 | 最优（AWGN） | 硬件重 |
| 循环平稳特征 | 部分周期统计 | 高 | 较好 | 受限节点难 |

能量检测：功率与阈值比较，无法区分 PU 与其他干扰。匹配滤波需专用相关器。循环平稳利用调制信号周期统计，观测时间与算力开销大[5][2]。

## 3. TVWS 与数据库

超高频（UHF）电视频段传播与穿透相对有利。IEEE 802.22 无线区域网、IEEE 802.11af 等面向 TV 频段接入；美国联邦通信委员会（FCC）、英国通信管理局（Ofcom）等允许次级使用，但多要求数据库查询和/或感知能力[3][4]。

| 步骤 | 内容 |
|------|------|
| 定位 | 设备获地理位置 |
| 查询 | 向频谱数据库提交位置与设备参数 |
| 授权参数 | 返回可用信道、功率上限、有效期 |
| 重询 | 周期刷新（量级常为分钟级，依监管） |

优点：比纯本地感知更可审计。局限：引导连接可能依赖已有回传（“先有网才能查库”）；对高度动态占用不够灵敏；库维护责任重[3]。

## 4. 动态接入与协作

动态频谱接入（Dynamic Spectrum Access, DSA）：感知/查库 → 选信道 → 传数并监测 → PU 出现则切换 → 记录模式以利预测。

单节点有隐藏终端、深衰落与多径导致漏检。协作感知由融合中心汇聚硬/软判决（OR/AND/多数/似然比），提高检测概率，但上报本身耗能与带宽[2]。

## 5. 感知–吞吐–能量

单射频下感知时间 \(T_s\) 与数据时间互斥：\(T_s\) 升则检测更好、吞吐降。IoT 还要把接收机开启能耗计入目标函数，常需睡眠–感知–传输调度、轮值协作或唤醒无线电（Wake-up Radio）把主射频大部分时间关掉[6][8]。

## 6. 案例要点（智慧城市示意）

环境监测传感器在 ISM 干扰重时，可经网关查询 TVWS 使用 UHF 上行：传播更好、可用带宽潜力更大、网关密度可下降——幅度依赖城市地形与可用白空间，文中“网关减半、丢包降一个数量级”仅作机制说明，部署前必须做覆盖与合规验证[3][4][9]。

## 7. 局限、挑战与可改进方向

### 1. 受限节点算不动“好检测器”

**局限**：循环平稳/深度学习感知超出微控制器预算。
**改进**：默认能量检测 + 网关侧协作/数据库；把重计算上移。

### 2. 监管碎片与商用稀疏

**局限**：各国 TVWS/CR 规则不一，模组与认证生态弱于 ISM。
**改进**：产品按目标市场做合规矩阵；优先数据库模式满足审计。

### 3. 退出时限与业务连续性

**局限**：PU 返回后须在短时内腾频（量级常为百毫秒级要求，依条款），切换造成丢包。
**改进**：多信道预留、快速重配射频；关键告警走蜂窝/有线备份。

### 4. 隐藏终端无法靠协作彻底消除

**局限**：协作节点若同处阴影，仍会集体漏检。
**改进**：数据库主用、感知备用；保守功率与排除区。

## 参考文献

[1] S. Haykin, "Cognitive Radio: Brain-Empowered Wireless Communications," IEEE JSAC, 2005.
[2] I. F. Akyildiz et al., "Cooperative spectrum sensing in cognitive radio networks: A survey," Physical Communication, 2011.
[3] FCC, "Unlicensed Operation in the TV Broadcast Bands," Second Memorandum Opinion and Order, FCC 10-174.
[4] IEEE 802.22, "Cognitive Wireless RAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications," TV 频段 WRAN.
[5] T. Yucek and H. Arslan, "A Survey of Spectrum Sensing Algorithms for Cognitive Radio Applications," IEEE Communications Surveys & Tutorials, 2009.
[6] R. Zhang et al., "Energy-efficient spectrum sensing for cognitive radio-based IoT," IEEE Internet of Things Journal（及同类能效感知研究）.
[7] J. Mitola III, "Cognitive Radio: An Integrated Agent Architecture for Software Defined Radio," PhD dissertation, KTH, 2000.
[8] Y.-C. Liang et al., "Sensing-Throughput Tradeoff for Cognitive Radio Networks," IEEE Trans. Wireless Communications, 2008.
[9] Ofcom, "TV White Spaces" 监管与数据库框架相关文件.
[10] IEEE 802.11af, "Television White Spaces (TVWS) operation" 相关标准.
[11] ITU-R, "Definitions of Software Defined Radio (SDR) and Cognitive Radio System (CRS)," SM.2152.
[12] ETSI, "EN 301 598: White Space Devices (WSD)" 欧洲白空间设备要求.
