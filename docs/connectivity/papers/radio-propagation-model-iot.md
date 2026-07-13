---
schema_version: '1.0'
id: radio-propagation-model-iot
title: 无线电传播模型在IoT覆盖规划中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - antenna-propagation-indoor-outdoor
  - fading-multipath-iot-channel
tags:
  - 传播模型
  - 路径损耗
  - Okumura-Hata
  - FSPL
  - 覆盖规划
  - LoRaWAN
  - 链路预算
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 无线电传播模型在IoT覆盖规划中的应用

> **难度**：🟡 中级 | **领域**：无线传播 | **阅读时间**：约 18 分钟

## 日常类比

城中心广播塔：近处清晰、楼后死角、郊外意外能听清。传播模型就是画“信号地图”的公式工具，用来估路径损耗，决定 LoRaWAN/NB-IoT/Wi-Fi 网关该放几个、放哪——不做预测易欠覆盖或过部署[1][2]。

## 摘要

接收功率 ≈ 发射功率 + 天线增益 − 路径损耗（Path Loss）。自由空间路径损耗（FSPL）给下限；对数距离模型用指数 n 与阴影衰落 σ；Okumura-Hata 等经验模型适合成区 Sub-GHz 宏覆盖。模型输出是中值/统计量，**必须加余量并用路测校准**[3]。

## 1. 基础模型

FSPL（d、f 用 km/MHz 常见形式）：距离或频率加倍，损耗约 +6 dB。故 LPWAN 偏 Sub-GHz[1]。

| 环境 | 路径损耗指数 n（量级） |
|------|------------------------|
| 自由空间 | ≈2 |
| 郊区/开阔 | ≈2–2.5 |
| 城区 NLOS | ≈3–4 |
| 室内跨层 | 可更高 |

对数距离：`PL(d)=PL(d0)+10 n log10(d/d0)+X_σ`。规划常留阴影余量（与目标覆盖概率相关），具体 dB 数应本地拟合，不宜照搬教科书默认[2]。

## 2. 经验模型与室内

| 模型 | 适用线索 | 注意 |
|------|----------|------|
| Okumura-Hata | 约 150–1500 MHz、宏站高天线 | 超参范围外勿外推 |
| COST-231 等 | 更高频扩展 | 查适用带 |
| 多墙/楼层模型 | 室内 | 墙体材料主导 |
| 射线追踪 | 复杂室内/厂区 | 成本高，需几何模型 |

Hata 城市/郊区差可达约 10 dB 量级（算例依赖 f、hb、d）——说明环境类选错比微调常数更致命[3]。

## 3. IoT 规划用法

1. 定频率、EIRP、接收灵敏度与噪声系数 → 最大允许路径损耗。
2. 选模型与 n/σ → 估半径。
3. 加干扰与人体/金属余量。
4. 路测校准；容量（上行占空、网关密度）与覆盖分开算。

| 技术 | 规划侧重点 |
|------|------------|
| LoRaWAN | 室外传播 + 室内穿透余量 |
| NB-IoT | 运营商图层 + 深度覆盖 |
| Wi-Fi | 室内墙损与同频干扰 |

## 4. 局限、挑战与可改进方向

### 1. 模型误用

**局限**：把 FSPL 当城区预测会严重乐观。
**改进**：按场景选模型；默认加保守余量。

### 2. 参数未校准

**局限**：n、σ 来自别的城市。
**改进**：短距路测回归；分区（室内/巷道）多套参数。

### 3. 忽略干扰与负荷

**局限**：只算热噪声灵敏度。
**改进**：测底噪与占空；网关密度看容量不只看覆盖圆。

### 4. 时变环境

**局限**：货架/季节植被改变损耗。
**改进**：变更后复测；监控边缘 RSSI 趋势。

## 5. 实践要点

1. 链路预算表公开假设（频率、天线、余量）。
2. 验收用边缘百分位成功率，不用中心点 RSSI。
3. 仿真工具辅助，不能替代抽测点。

## 参考文献

[1] Rappaport, T. S., Wireless Communications: Principles and Practice (path loss chapters).
[2] ITU-R P-series recommendations on propagation (e.g., P.1238 indoor, P.1411 street).
[3] Hata, M., "Empirical formula for propagation loss in land mobile radio services," IEEE Trans. Veh. Technol., 1980.
[4] Okumura field measurement reports (historical basis for Hata).
[5] COST 231 final report (propagation models).
[6] LoRa Alliance / Semtech regional coverage planning application notes.
[7] 3GPP NB-IoT coverage evaluation related TRs.
[8] 3GPP/ITU materials comparing Sub-GHz vs 2.4 GHz IoT coverage.
[9] Indoor multi-wall model literature for enterprise IoT.
[10] Shadow fading margin and cell-edge reliability planning notes.
[11] Drive-test / walk-test methodology for LPWAN gateway siting.
