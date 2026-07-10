---
schema_version: '1.0'
id: backscatter-communication-ambient-iot
title: 反向散射通信在环境IoT中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - backscatter-communication
  - link-budget-calculation-lpwan
tags:
  - Ambient IoT
  - 环境反向散射
  - RFID
  - 能量收集
  - 3GPP
  - WiFi Backscatter
  - 无电池
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 反向散射通信在环境IoT中的应用

> **难度**：🔴 高级 | **领域**：超低功耗通信 | **阅读时间**：约 22 分钟

## 日常类比

晴天用小镜子把阳光反射给远处朋友发摩尔斯码：你不发电，只拧手腕改反射角；太阳免费。环境反向散射（Ambient Backscatter）同理——不造载波，只改天线反射系数，把电视塔/Wi-Fi/基站已有射频“借”来传比特，功耗可到微瓦（μW）量级，为无电池物联网（Internet of Things, IoT）铺路[1][3]。

## 摘要

从射频识别（Radio Frequency Identification, RFID）到环境反向散射，说明 Wi-Fi/蓝牙路径、调制、双重路径损耗、射频能量收集与第三代合作伙伴计划（3GPP）Ambient IoT 设备分类。吞吐、距离、标签单价多为研究或试点量级，**不可直接当部署 SLA**[2][3][5]。

## 1 原理：反射而非发射

传统链路：振荡→调制→功放→天线，功耗常在 mW～W。反向散射：射频开关在匹配/失配间切换，改变反射系数；接收端解调幅度/相位变化。省掉功放与本振，功耗可低数个数量级——具体取决于开关工艺与基带占空比[5]。

## 2 从 RFID 到 Ambient

被动超高频（UHF）RFID（如 EPC Gen2 / ISO 18000-6C，约 860–960 MHz）：读写器发连续波，标签整流供能并反向散射；读取距离常见约数米量级。局限：必须专用读写器持续大功率发射[5]。

环境反向散射：载波改为已有广播/Wi-Fi/蜂窝，标签与接收机可分离于专用读写器架构[1]。

| 信号源 | 强度/连续性 | 带宽 | 覆盖 | 适用 |
|--------|-------------|------|------|------|
| TV 广播 | 强、较持续 | 相对窄 | 广域 | 室外 |
| Wi-Fi | 中、间歇 | 宽 | 室内局部 | 室内标签 |
| 蜂窝 | 中、较持续 | 中 | 城域 | 城市 Ambient IoT |
| 多源融合 | 动态 | 动态 | 动态 | 鲁棒性优先 |

## 3 Wi-Fi / BLE 反向散射

Wi-Fi 反向散射：选择性反射接入点帧，生成可被标准 802.11 接收的包；研究吞吐可到约数 Mbps 量级，有效距离常约 1–5 m 量级，受双重路径损耗约束[2]。

蓝牙低功耗（BLE）反向散射：反射整形为广播包，手机可直接收——适合智能包装、近场传感；演示距离常约 1–3 m 量级[4]。

## 4 调制与双重路径损耗

常见：开关键控（ON-OFF Keying）、频移键控（Frequency-Shift Keying, FSK）；更高阶/正交频分复用（OFDM）类方案吞吐更高、实现更重。时钟恢复常用 Manchester/FM0。

```
P_rx ∝ P_tx · G1/(d1²) · σ · G2/(d2²)
```

相对有源 1/d²，反向散射近似 1/(d1² d2²)，距离通常卡在约 1–10 m 量级（专用双基地/LoRa 类可更远，见姊妹文）[5]。缓解：靠近接收机、提高反射效率、协作反射。

## 5 能量收集与 3GPP 分类

同一天线可分路：整流天线（rectenna）供传感器/微控制器，开关做通信。环境可收集功率常仅 μW 量级，设备多为“久睡短醒”[1][5]。

| 类型 | 特征 | 类比 |
|------|------|------|
| A 被动 | 纯反向散射，无电池 | 增强 RFID |
| B 半被动 | 电池供传感，通信仍反向散射 | 电池辅助 RFID |
| C 主动 | 极低功耗主动发射 | 接近极简蜂窝终端 |

3GPP Rel-19 起推进 Ambient IoT，目标供应链标签、电子货架、海量低成本节点等[3]。

## 6 应用与仓库盘点示意

供应链温湿度标签、土壤传感、结构健康埋入传感、电子货架标签、无电池健康贴片等。仓库示意：数千～数万标签 + 顶置阅读器/既有 Wi-Fi；标签成本可到美分级宣传、盘点分钟级——**依赖阅读器密度与防碰撞**，须试点验证[3][8]。

## 7 局限、挑战与可改进方向

### 1. 距离与密度天花板

**局限**：四次方衰减与多标签碰撞限制仓库级覆盖[5]。
**改进**：阅读器网格规划、防碰撞/机器学习解码、分区激励。

### 2. 能量预算过紧

**局限**：μW 级收集撑不起复杂传感与加密[1]。
**改进**：事件触发、电容储能、半被动（类型 B）过渡。

### 3. 标准与互操作未稳

**局限**：研究原型与商用芯片帧格式不一[3]。
**改进**：按 3GPP/产业联盟冻结配置；网关侧多协议适配。

### 4. 安全与隐私

**局限**：反射链路易被窃听/重放，货架标签可被伪造[4]。
**改进**：短暂标识、应用层签名、与门禁支付解耦。

## 参考文献

[1] V. Liu et al., Ambient Backscatter, ACM SIGCOMM, 2013.
[2] B. Kellogg et al., Wi-Fi Backscatter, ACM SIGCOMM, 2014.
[3] 3GPP TR 38.858 / TR 38.848, Study on Ambient IoT, Release 19.
[4] P. Hu et al., Bluetooth Backscatter 相关工作, HotNets 等.
[5] C. Boyer and S. Roy, Backscatter Communication and RFID, IEEE Trans. Commun., 2014.
[6] B. Kellogg et al., Passive Wi-Fi, USENIX NSDI, 2016.
[7] V. Iyer et al., Inter-Technology Backscatter, ACM SIGCOMM, 2016.
[8] Wiliot 等无电池传感商业试点资料, 2024.
[9] EPCglobal / ISO 18000-6C, UHF RFID.
[10] Y. Peng et al., PLoRa, ACM SIGCOMM, 2018.
[11] IEEE 802.11ba, Wake-Up Radio（与超低功耗接收互补）.
