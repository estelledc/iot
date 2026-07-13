---
schema_version: '1.0'
id: power-line-communication-plc-iot
title: 电力线通信PLC在IoT智能电网中的应用
layer: 2
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - dlms-cosem-smart-meter-protocol
tags:
  - 电力线通信
  - PLC
  - G3-PLC
  - PRIME
  - 智能电网
  - AMI
  - HomePlug
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 电力线通信PLC在IoT智能电网中的应用

> **难度**：🟡 中级 | **领域**：有线IoT通信 | **阅读时间**：约 18 分钟

## 日常类比

已有铁轨走廊上再跑“电话线”：电力线通信（Power Line Communication, PLC）在 50/60 Hz 电力上叠加 kHz–MHz 数据。像在嘈杂工地用对讲——能通，但噪声、阻抗跳变和变压器“墙”会让链路忽好忽坏[1]。

## 摘要

窄带 PLC（NB-PLC：PRIME、G3-PLC、IEEE 1901.2）服务高级量测基础设施（AMI）电表回传；宽带 PLC（HomePlug、G.hn、IEEE 1901）服务户内骨干。核心调制多为正交频分复用（OFDM）+ 自适应子载波。全球电表部署规模以“亿级”公开叙述常见，**具体数量随运营商项目变化，宜查当期报告**[2][3][5]。

## 1. NB vs BB

| 参数 | 窄带 PLC | 宽带 PLC |
|------|----------|----------|
| 频率 | 约 3–500 kHz（区域法规不同） | 约 2–86 MHz 量级 |
| 速率 | kbps–数百 kbps 量级 | 数十 Mbps–Gbps 级峰值 |
| 距离 | 台区内数百米–数公里叙事 | 建筑内为主 |
| 标准 | PRIME, G3-PLC, 1901.2 | HomePlug, G.hn, 1901 |
| 典型 | 智能电表 AMI | 户内扩展、充电 PLC |

欧洲 CENELEC 与美国 FCC 频段上限不同，选型先查当地法规[4]。

## 2. 信道与 AMI 架构

电力线：频率选择性衰落、背景噪声、窄带干扰、与工频同步的脉冲噪声、开关浪涌。OFDM 关坏子载波 + FEC/交织/重传是标配[1]。

典型 AMI：电表 —(NB-PLC)— 台区集中器 —(光纤/蜂窝)— 主站。变压器常带来数十 dB 级阻断，跨变需中继或其他回传。

| 方案 | 优势 | 代价 |
|------|------|------|
| 纯 PLC | 无 SIM 费、复用电线 | 噪声台区失败率高 |
| 纯蜂窝 | 覆盖灵活 | 卡费与信号死角 |
| PLC+蜂窝双模 | 成功率更高 | 模组与运维复杂 |

公开项目中“双模把成功率抬到接近 99.9%”属**案例绑定数字**，验收须用本台区统计[5]。

## 3. 户内与相邻技术

HomePlug/G.hn 可做“电力线骨干 + 房间 Wi-Fi 末梢”；智能插座直连省 Wi-Fi 争用。同台区用户可互听信号 → 需 AES 等链路加密（HomePlug 等已内置）[1]。

电动汽车充电 ISO 15118 等可用 HomePlug Green PHY 做车桩会话——属能源 IoT 扩展，非电表专属。

## 4. 局限、挑战与可改进方向

### 1. 噪声与时变阻抗

**局限**：LED 驱动、充电器等使夜间/白天性能差一截。
**改进**：现场频谱摸底；自适应子载波；按最差时段做链路余量。

### 2. 变压器与拓扑墙

**局限**：跨变几乎不通；中继增加时延与运维点。
**改进**：集中器按台区规划；跨变走蜂窝/光纤；拓扑变更后重测。

### 3. 安全与隐私

**局限**：同台区可嗅探未加密流量。
**改进**：强制加密与密钥轮换；管理面与抄表面隔离。

### 4. 标准碎片

**局限**：PRIME vs G3 生态分区，芯片与工具不通用。
**改进**：按区域电力公司既有标准选型；预留双模或远程升级。

## 5. 实践要点

1. 先测目标台区噪声与衰减，再定 NB 标准与集中器密度。
2. 耦合电路按电气安全/EMC 认证设计，不可实验室飞线量产。
3. 合同指标用台区成功率与时延百分位，不用芯片标称峰值。

## 参考文献

[1] Ferreira, H. C. et al., Power Line Communications, Wiley, 2010.
[2] PRIME Alliance, PRIME Technology Whitepaper.
[3] G3-PLC Alliance, G3-PLC Technology Overview.
[4] IEEE Std 1901.2, Low-Frequency Narrowband PLC for Smart Grid.
[5] Enel Telegestore / Enedis Linky public project materials (treat counts as historical).
[6] IEEE Std 1901 / HomePlug AV/AV2 overviews.
[7] ITU-T G.hn recommendations for home networking.
[8] CENELEC EN 50065 / regional PLC spectrum rules.
[9] ISO 15118 and HomePlug Green PHY charging communications notes.
[10] Vendor PLC modem datasheets (Microchip, ST, Qualcomm, MaxLinear).
[11] Hybrid PLC + cellular AMI architecture case studies.
