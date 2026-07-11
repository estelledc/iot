---
schema_version: '1.0'
id: link-budget-calculation-lpwan
title: LPWAN链路预算计算与覆盖估算
layer: 2
content_type: tutorial
difficulty: intermediate
reading_time: 20
prerequisites:
  - lora-vs-sigfox-vs-nbiot
  - fading-multipath-iot-channel
tags:
  - 链路预算
  - LPWAN
  - MAPL
  - LoRa
  - NB-IoT
  - 路径损耗
  - 接收灵敏度
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# LPWAN链路预算计算与覆盖估算

> **难度**：🟡 中级 | **领域**：无线工程 | **阅读时间**：约 20 分钟

## 日常类比

嘈杂体育场喊话：你能多大声（发射功率）、中间损耗多少、对方听力多好（灵敏度）。链路预算把增益与损耗列成“收支账”，看到达信号是否够解码。对低功耗广域网（LPWAN），多 1 dB 都可能决定地下室水表通不通[1][2]。

## 摘要

链路余量 ≈ 发射与天线增益 − 各类损耗 − 灵敏度（注意灵敏度多为大负数）。最大允许路径损耗（MAPL）再扣阴影/穿透余量后，用传播模型估距离。表中灵敏度与公里数是典型量级，**须用本机数据手册与实测校准**[2][3]。

## 1. 基本式与单位

```
链路余量 = P_tx + G_tx − L_feed_tx − L_path − L_extra + G_rx − L_feed_rx − S_rx
```

余量 >0 才谈得通；工程常留约 10–20 dB 量级抗波动。dBm 以 1 mW 为参考；dBi 相对全向天线。

| 组成 | 例子 |
|------|------|
| 发射 | 功率、天线增益、馈线 |
| 传播 | 路径损耗、阴影、穿透 |
| 接收 | 天线、馈线、灵敏度 |

## 2. 发射与灵敏度

| 技术（示意） | 发射功率量级 | 限制来源 |
|--------------|--------------|----------|
| LoRa 欧 868 | 约 14 dBm | ETSI 等 |
| LoRa 美 915 | 可更高至约 20+ dBm | FCC EIRP |
| NB-IoT / LTE-M | 约 23 dBm | 3GPP |

终端 PCB 天线增益常在约 −3～+2 dBi。EIRP = P_tx + G_ant − L_feed，且须合规。

| 技术 | 带宽观感 | 灵敏度量级 |
|------|----------|------------|
| Wi-Fi | 宽 | 约 −85 dBm 量级 |
| BLE | 中 | 约 −97 dBm 量级 |
| LoRa SF7/SF12 | 窄+扩频 | 约 −123～−137 dBm 量级 |
| NB-IoT / Sigfox | 极窄 | 可至约 −140 dBm 量级 |

SF↑灵敏度↑、速率↓、空中时间↑。手册值随带宽、码率、芯片而变[2]。

## 3. MAPL 与余量

```
MAPL ≈ EIRP + G_rx − S_rx   （S_rx 为负数时等价加上其绝对值）
有效 MAPL = MAPL − 阴影余量 − 穿透 − 其他余量
```

| 技术（示意条件） | MAPL 观感 |
|------------------|-----------|
| LoRa SF12 + 网关天线增益 | 约 150+ dB |
| NB-IoT（基站天线更高） | 可更高 |
| Wi-Fi / BLE | 显著更低 |

阴影余量由 σ 与目标覆盖概率决定（如 90%/95% 对应不同倍数）。建筑外墙与地下室可再叠加十余至数十 dB——**结构差异大，宜现场测**。

Okumura-Hata 等把有效 MAPL 转为公里数：城市数公里、郊区更远是常见叙事；扣余量后显著收缩。上行常因终端功率/天线成为瓶颈；规划应以上行为主[1][3]。

## 4. 技术对比要点

| 维度 | LoRa | Sigfox | NB-IoT |
|------|------|--------|--------|
| 频谱 | 免许可为主 | 免许可 | 授权蜂窝 |
| 覆盖手段 | SF/网关密度 | 超窄带 | MCL/基站 |
| 成本结构 | 可自建 | 运营商 | SIM/套餐 |

室内深覆盖且有蜂窝时 NB-IoT 常更省心；无覆盖农村自建 LoRa；极小报文超远可评估 Sigfox 类——仍做链路预算。

## 5. 案例要点（地下室水表）

2 km 外楼顶网关 + 砖混 + 一层地下室：路径损耗与穿透叠加后，RSSI 可能低于 SF12 灵敏度十余 dB，链路失败。对策：就近加网关、天线引出、楼内中继或改 NB-IoT。加网关往往同时服务周边多楼——**用预算在部署前否决幻想距离**。

## 6. 局限、挑战与可改进方向

### 1. 模型乐观

**局限**：自由空间/Hata 忽略巷道、金属柜、新建筑玻璃。
**改进**：余量分项列清；关键点 CW/实测；地下室单独测。

### 2. 上下行不对称

**局限**：只算下行或忽略占空比限制。
**改进**：上下行分别算；核对网关下行法规与占空比。

### 3. 灵敏度当常数

**局限**：SF/带宽/温度/晶振偏差改变解码门限。
**改进**：按实际配置查手册；高低温抽测。

### 4. 余量堆叠过度或不足

**局限**：处处加 10 dB 导致过密建站，或裸算导致掉线。
**改进**：按覆盖概率选阴影余量；穿透用本地经验值；迭代站址。

## 7. 实践要点

1. 先写清频率、EIRP 上限、天线与目标覆盖概率。
2. 输出有效 MAPL 再进传播模型，最后用路测闭合。
3. 验收看边缘百分位 RSSI/SNR 与成功率，不看实验室最佳 SF。

## 参考文献

[1] Rappaport, T. S., Wireless Communications: Principles and Practice, Prentice Hall.
[2] Semtech, LoRa Modulation Basics / related application notes.
[3] 3GPP TR 36.888 (and later MTC/NB-IoT coverage studies).
[4] Sigfox technical overview documentation.
[5] Centenaro, M. et al., Long-range communications in unlicensed bands, IEEE Wireless Commun., 2016.
[6] ETSI regulations for SRD / 868 MHz power limits.
[7] FCC Part 15 rules relevant to 915 MHz LPWAN.
[8] Okumura-Hata / COST propagation model references.
[9] 3GPP NB-IoT MCL and link budget presentations.
[10] LoRa Alliance coverage and ADR related documents.
[11] ITU-R recommendations on path loss and building entry loss.
[12] Vendor gateway antenna and feeder loss application notes.
