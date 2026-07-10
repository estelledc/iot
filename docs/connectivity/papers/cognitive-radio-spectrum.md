---
schema_version: '1.0'
id: cognitive-radio-spectrum
title: 认知无线电与动态频谱共享
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 24
prerequisites: UNKNOWN
tags:
  - 认知无线电
  - 动态频谱共享
  - CBRS
  - SAS
  - TVWS
  - 频谱感知
  - DSA
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 认知无线电与动态频谱共享

> **难度**：🟡 中级 | **领域**：频谱管理 | **阅读时间**：约 24 分钟

## 日常类比

固定车位白天常空着，访客却无处停车——问题不是车位不够，是分配僵化。无线频谱亦然：授权用户（Primary User, PU）独占牌照，但时空上存在频谱空洞。认知无线电（Cognitive Radio, CR）像会找空位的司机：感知→停入→车主回来立刻挪走；次级用户（Secondary User, SU）必须“来无影去无踪”[1][2]。

## 摘要

本文覆盖认知循环、能量/循环平稳/协作感知，电视白空间（TV White Space, TVWS）地理位置数据库，美国公民宽带无线电服务（Citizens Broadband Radio Service, CBRS）的频谱接入系统（Spectrum Access System, SAS），以及机器学习频谱预测与监管框架。预测准确率与可用带宽数字为研究/地区量级，需本地验证[5][8][3]。

## 1. 认知循环与术语

感知 → 决策 → 接入（动态频谱接入 Dynamic Spectrum Access, DSA）→ 退让/切换（Spectrum Handoff）→ 循环[1][2]。

| 术语 | 含义 |
|------|------|
| PU | 授权主用户 |
| SU | 认知次级用户 |
| Spectrum Hole | 时空频上空闲资源 |
| Sensing | 检测占用 |
| DSA | 动态接入空闲谱 |
| Handoff | PU 返回时切换 |

误报降低利用率；漏检干扰 PU——感知是可靠性瓶颈[5]。

## 2. 频谱感知

**能量检测**：比功率与阈值；实现简单，低信噪比受噪声不确定度限制（SNR 墙）[5]。

**循环平稳检测**：人造信号周期统计 vs 噪声；灵敏度更好，复杂度显著更高，嵌入式少用[5]。

| 维度 | 能量检测 | 循环平稳 |
|------|----------|----------|
| 复杂度 | 低 | 高 |
| 低 SNR 倾向 | 较弱 | 较强 |
| 先验 | 噪声估计 | 循环频率等 |
| 区分信号类型 | 难 | 较易 |

**协作感知**：多 SU 融合，缓解隐藏终端。

| 融合规则 | 检测概率倾向 | 虚警倾向 | 适用 |
|----------|----------------|----------|------|
| OR | 高 | 高 | 优先护 PU |
| AND | 低 | 低 | 偏利用率 |
| 多数 | 中 | 中 | 折中 |
| 加权 | 视信道质量 | 视质量 | 已知链路差异 |

## 3. TVWS

数字电视转换后 VHF/UHF 出现白空间；UHF 传播与覆盖对农村与部分物联网（Internet of Things, IoT）有利。FCC 等推动**地理位置数据库**为主合规路径：设备上报位置，库返回可用信道与功率上限，降低纯感知漏检风险[9][4]。

| 项目/标准 | 定位 | 备注 |
|-----------|------|------|
| IEEE 802.22 | TV 频段 WRAN | 广域覆盖 |
| IEEE 802.11af | TVWS Wi-Fi 类 | “Super Wi-Fi”叙事 |
| Weightless-W 等 | IoT 向 | 生态因监管与芯片而波动 |
| 农村 TVWS 试点 | 宽带接入 | 速率与可用信道强地域相关 |

## 4. CBRS SAS：三级共享范例

美国 3.5 GHz 附近 CBRS 由 SAS 自动协调[3]：

| 层级 | 角色 | 优先级 |
|------|------|--------|
| Incumbent | 如海军雷达等在位系统 | 最高 |
| PAL | 优先接入许可 | 中 |
| GAA | 一般授权接入 | 最低 |

环境传感能力（Environmental Sensing Capability, ESC）等检测在位活动；公民宽带无线电服务设备（CBSD）向 SAS 申请授权，授权短时有效需心跳续约，并受动态功率约束。多 SAS 运营商需互操作以免冲突授权[3][6]。

## 5. 频谱占用预测

占用常有时间相关，可用隐马尔可夫模型（HMM）、长短期记忆（LSTM）等预测以减少盲切换。公开频谱观测数据集上，短时预测可高于朴素持续基线，长时域下降——具体百分点随数据集与特征变化，下表仅为文献量级示意，不可当产品指标[8][7]。

| 方法倾向 | 短时预测 | 较长时域 |
|----------|----------|----------|
| 持续（上一值） | 高 | 明显下降 |
| HMM | 更高 | 中 |
| 深度序列模型 | 更高 | 相对更好但仍降 |

IoT 端侧宜用极小模型或云侧预测下发信道建议。

## 6. 监管与 IoT 含义

| 模式 | 代表 | 特点 |
|------|------|------|
| 固定授权 | 传统牌照 | 保护强、利用率常低 |
| 免授权 | ISM | 创新易、干扰重 |
| 轻授权/共享 | CBRS、欧洲 LSA | 保护与效率折中 |
| 交易/二次市场 | 部分国家试点 | 制度复杂 |

| 地区 | TVWS / 共享倾向 |
|------|-----------------|
| 美国 FCC | TVWS 数据库；CBRS 成熟度相对高 |
| 欧洲 ETSI | 白空间设备标准；LSA 等 |
| 中国等 | 政策与试点节奏不同，需跟主管部门 |

对 IoT：可能获得更干净或传播更好的谱，但感知/SAS 协议超出传感器能力时，应把智能放在网关与云，终端只做简单重配[10]。

## 7. 局限、挑战与可改进方向

### 1. 感知不可靠与合规责任

**局限**：漏检导致干扰投诉与关停风险。
**改进**：数据库/SAS 主路径；感知仅辅助；保守功率与排除区。

### 2. 受限 IoT 无法跑完整认知循环

**局限**：持续感知耗电，循环平稳/深度模型不适合 MCU。
**改进**：网关代理查询；终端预配置信道列表；唤醒后短时确认。

### 3. SAS/数据库可用性成为依赖

**局限**：回传中断则无法获授权或续约失败。
**改进**：短时本地缓存策略（须符合监管）；关键业务双连接。

### 4. 机器学习预测过拟合与漂移

**局限**：换城市/换季节后准确率崩塌。
**改进**：在线校准；预测仅用于排序候选信道，最终仍以实时检测/库为准。

## 参考文献

[1] J. Mitola III, "Cognitive Radio: An Integrated Agent Architecture for Software Defined Radio," PhD Dissertation, KTH, 2000.
[2] S. Haykin, "Cognitive Radio: Brain-Empowered Wireless Communications," IEEE JSAC, 2005.
[3] FCC, "Citizens Broadband Radio Service," 47 CFR Part 96.
[4] IEEE 802.22, "Cognitive Wireless RAN MAC and PHY Specifications," 2011 及后续修订.
[5] T. Yucek and H. Arslan, "A Survey of Spectrum Sensing Algorithms for Cognitive Radio Applications," IEEE Communications Surveys & Tutorials, 2009.
[6] Google / Federated Wireless 等, "Spectrum Access System (SAS) API" 公开文档.
[7] M. Bkassiny et al., "A Survey on Machine-Learning Techniques in Cognitive Radios," IEEE Communications Surveys & Tutorials, 2013.
[8] Y. Sun et al., "Deep Learning for Spectrum Sensing: A Survey," IEEE Access（及后续频谱预测综述）.
[9] ETSI, "EN 301 598: White Space Devices (WSD)."
[10] ITU-R, "SM.2152: Definitions of SDR and Cognitive Radio System (CRS)."
[11] FCC, "Unlicensed Operation in the TV Broadcast Bands," 相关 MO&O.
[12] M. M. Sohul et al., "Spectrum Access System for the Citizen Broadband Radio Service," IEEE Communications Magazine, 2015.
