---
schema_version: '1.0'
id: modulation-schemes-iot-comparison
title: IoT调制方式对比：FSK/LoRa/OFDM/CSS
layer: 2
content_type: comparison
difficulty: intermediate
reading_time: 18
prerequisites: UNKNOWN
tags:
  - 调制
  - FSK
  - LoRa
  - CSS
  - OFDM
  - OOK
  - 链路预算
  - LPWAN
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# IoT调制方式对比：FSK/LoRa/OFDM/CSS

> **难度**：🟡 中级 | **领域**：数字调制 | **阅读时间**：约 18 分钟

## 日常类比

对岸灯光约定：亮灭传比特像幅度键控；闪烁快慢像频移；何时亮像相移。IoT 选调制，就是在**距离、速率、功耗、复杂度**间权衡；电池设备更偏恒包络与高功率效率[1][5]。

## 摘要

对比 OOK、FSK/GFSK、PSK/QAM、LoRa CSS 与 OFDM 的机制与适用边界，并给出灵敏度/带宽直觉与选型流程。灵敏度 dBm 与覆盖公里数为典型量级，**随芯片、带宽、编码与天线而变**[2][4]。

## 1. 基本权衡

载波 \(A\cos(2\pi ft+\phi)\) 可变幅度/频率/相位。IoT 常优先：功率效率、实现成本、抗干扰；频谱效率往往次之。

## 2. 主要体制

| 调制 | 要点 | 典型去向 |
|------|------|----------|
| OOK | 极简能量检测，抗扰弱 | 遥控、唤醒接收 |
| FSK/GFSK | 恒包络，功放可高效 | Sigfox/Z-Wave/wM-Bus 等 |
| BPSK/QPSK/… | 功率↔频谱效率阶梯 | NB-IoT/LTE-M 等 |
| CSS (LoRa) | 啁啾位置编码，SF 换灵敏度 | LoRaWAN |
| OFDM | 多子载波，PAPR 高 | Wi-Fi、蜂窝下行等 |

LoRa：SF 升高则符号更长、速率降、灵敏度改善（约数 dB/档的经验叙事）[2]。OFDM：抗多径与高频谱效率，但峰均比迫使功放回退，电池设备不友好[1][3]。

## 3. 对比表

| 维度 | OOK | FSK | CSS | OFDM |
|------|-----|-----|-----|------|
| 复杂度 | 极低 | 低 | 中 | 高 |
| 距离潜力 | 短 | 中–长 | 很长（低速时） | 短–中（常） |
| 速率 | 极低 | 低 | 低 | 高 |
| 功放 | 简单 | 恒包络友好 | 恒包络友好 | 需线性 |

灵敏度直觉：热噪底 \(-174+10\log_{10}(B)\) dBm，再加噪声系数与所需 SNR。窄带换灵敏度、牺牲速率——LPWAN 常用策略[1][2][4]。

## 4. 选型指引

| 需求 | 更常见选择 |
|------|------------|
| 远距+小包+长电池 | CSS 或窄带 FSK |
| 蜂窝覆盖+移动/QoS | NB-IoT/LTE-M（蜂窝调制与重复） |
| 高吞吐+有电 | Wi-Fi OFDM |
| 极低成本近距 | OOK/FSK |

混合系统很常见：传感走 LPWAN，视频走 Wi-Fi，勿强求单一调制打天下[5]。

## 5. 局限、挑战与可改进方向

### 1. 只看灵敏度忽略法规占空比

**局限**：链路预算够但法定空中时间不够。
**改进**：同步算占空比/跳频约束与网关容量。

### 2. 高阶调制迷信

**局限**：室内短距也上高阶 QAM，功耗与鲁棒性变差。
**改进**：按边缘 SNR 选最低够用阶数；启用 AMC 时验证回退。

### 3. 把 LoRa SF 当无限旋钮

**局限**：SF12 覆盖好但空中时间与冲突升。
**改进**：ADR/人工限 SF；容量与电池联合评估。

### 4. OFDM 用于纽扣电池

**局限**：PAPR 与基带复杂度拖垮续航。
**改进**：有电再用 Wi-Fi；电池侧改 BLE/FSK/CSS。

## 6. 实践要点

1. 先写清距离、日报文量、供电，再选调制族。
2. 用目标模组测 PER–功率曲线，不抄宣传灵敏度。
3. 多技术共存时做带内干扰与共存测试。

## 参考文献

[1] Proakis, J. G., Digital Communications (modulation chapters).
[2] Semtech, LoRa Modulation Basics, AN1200.22.
[3] IEEE 802.11ah / Wi-Fi HaLow materials for Sub-GHz OFDM IoT.
[4] 3GPP TS 36.211 (and related), NB-IoT physical channels and modulation.
[5] Raza, U. et al., "Low Power Wide Area Networks: An Overview," IEEE COMST, 2017.
[6] Bluetooth Core Specification, GFSK related clauses.
[7] Sigfox technical documentation (UNB FSK/DBPSK narratives).
[8] IEEE 802.15.4 modulation options overview.
[9] OFDM PAPR and PA efficiency literature for battery devices.
[10] LoRaWAN Regional Parameters (duty cycle / channel plans context).
[11] Sklar / other digital comm textbooks on FSK vs PSK power efficiency.
