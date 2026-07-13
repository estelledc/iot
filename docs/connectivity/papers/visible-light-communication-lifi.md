---
schema_version: '1.0'
id: visible-light-communication-lifi
title: 可见光通信LiFi在IoT室内定位中的应用
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 16
prerequisites:
  - lifi-visible-light-communication
tags:
  - LiFi
  - VLC
  - 可见光通信
  - 室内定位
  - LED
  - IEEE-802.15.7
  - OWC
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 可见光通信LiFi在IoT室内定位中的应用

> **难度**：🔴 高级 | **领域**：光无线通信 | **阅读时间**：约 16 分钟

## 日常类比

商场天花板灯像固定灯塔：每盏以人眼难察的节奏“报出自己的编号”，手机摄像头/光传感器认灯即知所在区域。VLC（Visible Light Communication）是用光传信息；LiFi（Light Fidelity）是把 VLC 做成可组网的接入体系，类比 Wi‑Fi 之于无线电[1][2]。

## 摘要

LED 照明兼通信：下行可见光、上行常红外或 RF 回传。定位从灯 ID 区域定位、RSS 三边到成像/AoA。文中速率与精度为文献/厂商量级，**受照度、遮挡与接收机带宽约束**[1][3]。

## 1. 原理与调制

LED 可高速调光；高于视觉暂留的调制表现为“稳光”。链路：驱动/调制 → 光信道 → PD（Photodiode）+ TIA → 解调[3][4]。

| 调制 | 用途倾向 | 备注 |
|------|----------|------|
| OOK / VPPM | 低速 ID/控制、兼顾调光 | 实现简单 |
| DCO-OFDM 等 | 更高频谱效率 | 光强非负约束需偏置 |

可见光频段无需像蜂窝那样授权，但**器件调制带宽**远小于“THz 量级频谱”的宣传口径[1][4]。

## 2. LiFi 与 Wi‑Fi

| 维度 | LiFi/VLC | Wi‑Fi |
|------|----------|-------|
| 介质 | 可见光/红外 | RF |
| 穿墙 | 基本不 | 能 |
| 与 RF 干扰 | 正交 | 同频拥挤 |
| 移动性 | 依赖灯覆盖与切换 | 较成熟 |
| 商用速率 | 常远低于实验室峰值 | 生态成熟 |

IEEE 802.15.7 等定义短距光无线 PHY/MAC 选项（OOK/VPPM/CSK 等）[2]。

## 3. 室内定位

灯位置已知 → 识别灯 ID 得区域；多灯 RSS（光功率—距离模型）可三边；成像传感器估入射角可更高精度。编码可用频分、时分或类 CDMA 区分多灯[3][5]。

| 技术 | 精度叙事 | 基建 |
|------|----------|------|
| VLC | 分米级常见目标 | 改造/兼容驱动的灯 |
| UWB | 分米—厘米 | 专用锚点 |
| BLE | 米—亚米 | 信标/阵列 |

光不穿墙带来房间级隔离，也带来口袋遮挡即失锁[5][6]。

## 4. IoT 场景

零售导航与货架级触达、展陈导览、RF 敏感环境（部分医疗叙事）、工业区域追踪、清水域短距光通信等。常与 BLE/Wi‑Fi 融合：有光用 VLC，无光降级[5][6][7]。

## 5. 局限、挑战与可改进方向

### 1. 上行与终端硬件

**局限**：手机难发强可见光；专用 PD/IR 抬成本。
**改进**：IR 上行、RF 上行混合；IoT 标签集成 PD 而非依赖手机摄像头帧率[1][7]。

### 2. 环境光与遮挡

**局限**：日光/遮挡淹没或中断链路。
**改进**：光学滤波、差分检测；多灯冗余与快速切换；融合定位兜底[3][4]。

### 3. 灯具改造与调光冲突

**局限**：驱动不支持高频调制则无法“顺便”上 VLC。
**改进**：新建项目指定兼容驱动；改造评估 ROI，高价值区优先[6][7]。

### 4. 生态小于 Wi‑Fi

**局限**：芯片、协议栈、运维工具链窄。
**改进**：定位-only 轻量部署；数据面仍走 Wi‑Fi/有线[1][5]。

## 6. 实践要点

1. 先确认是“定位广播”还是“替代 Wi‑Fi 接入”，需求差一个数量级。
2. 验收含窗边强光与人体遮挡用例。
3. 灯具资产坐标与 ID 映射纳入 BIM/运维。

## 参考文献

[1] Haas, H., LiFi / optical wireless overview papers (e.g. Reviews in Physics, 2018).
[2] IEEE Std 802.15.7-2018, Short-Range Optical Wireless Communications.
[3] Komine, T. and Nakagawa, M., VLC with LED lights analysis, IEEE Trans. Consum. Electron., 2004.
[4] Survey literature on VLC modulation (OOK, VPPM, DCO-OFDM).
[5] Signify / retail VLC indoor positioning case materials.
[6] pureLiFi product and technology overviews.
[7] Oledcomm and aviation/medical LiFi trial reports (treat as anecdotal).
[8] Pathak, P. et al., VLC survey, IEEE ComST.
[9] Optical camera communication (OCC) papers for smartphone receivers.
[10] ITU/related optical wireless discussion documents.
[11] Underwater optical communication surveys (blue-green light).
[12] Hybrid RF-optical indoor positioning system papers.
