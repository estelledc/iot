---
schema_version: '1.0'
id: multi-band-antenna-iot-device
title: 多频段天线在IoT多模设备中的设计
layer: 2
content_type: technical_analysis
difficulty: advanced
reading_time: 22
prerequisites:
  - antenna-propagation-indoor-outdoor
  - antenna-testing-ota-measurement
tags:
  - 多频段天线
  - PIFA
  - IFA
  - 阻抗匹配
  - 隔离度
  - OTA
  - IoT模组
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 多频段天线在IoT多模设备中的设计

> **难度**：🔴 高级 | **领域**：天线设计 | **阅读时间**：约 22 分钟

## 日常类比

火柴盒里要同时塞进“长波收音机、对讲机、Wi-Fi”三根天线，还不能互相抢话——多模物联网（Internet of Things, IoT）设备的多频段天线就是这件事。资产追踪器常要 Sub-GHz（如 LoRa）、2.4 GHz（蓝牙低功耗 BLE）与蜂窝频段并存；波长差一个数量级，却挤在几平方厘米印刷电路板（Printed Circuit Board, PCB）上[1][2]。

## 摘要

说明四分之一波长尺寸矛盾、多谐振倒 F / 平面倒 F（IFA/PIFA）、独立天线、匹配与地平面、隔离与空中（Over-The-Air, OTA）验收。效率与隔离数字随地尺寸、外壳与人体负载变化，**仿真峰值不可直接当量产保证**[3][8]。

## 1. 频段与尺寸矛盾

自由空间波长 λ≈c/f；四分之一波长是常见电小天线起点：

| 技术（示意） | 频段量级 | λ/4 量级 |
|--------------|----------|----------|
| LoRa / NB-IoT Sub-GHz | ~0.8–0.9 GHz | ~8 cm |
| 蜂窝中频 | ~1.8 GHz | ~4 cm |
| BLE / Wi-Fi 2.4 GHz | 2.4 GHz | ~3 cm |
| Wi-Fi 5 GHz | 5.8 GHz | ~1.3 cm |

设备边长常远小于 Sub-GHz 的 λ/4，只能靠蜿蜒、加载、利用地平面与外壳，并接受效率下降[1][4]。

## 2. 拓扑选择

| 方案 | 做法 | 优点 | 代价 |
|------|------|------|------|
| 多谐振 IFA/PIFA | 一贴片多枝节/开槽 | 省面积、单馈 | 调谐耦合强、带宽窄 |
| 独立天线 | 每频段一辐射体 | 隔离与匹配更可控 | 占板、布线与成本 |
| 芯片天线 | 外购陶瓷/LTCC | 缩短设计周期 | Sub-GHz 效率常偏低 |
| 可调匹配 | 开关/变容管 | 覆盖多运营商频段 | 损耗、控制与可靠性 |

2.4 GHz 与 Sub-GHz 同板时，常把高频短臂与低频蜿蜒臂分区，并预留净空（keep-out）[2][5]。

## 3. 匹配、地平面与隔离

多频段匹配要在多个谐振点同时靠近 50 Ω；单节 L 网络往往不够，需多节或可调网络，并计入开关插入损耗[5]。

地平面是电小天线的镜像与回流路径：地过小会使 Sub-GHz 效率显著变差、谐振偏移。公开对比中“几十毫米方地”相对“更大板”效率可差一截——**具体百分比依赖结构，需实测**[4][6]。

| 手段 | 作用 |
|------|------|
| 空间分离 / 正交极化 | 降互耦 |
| 地缝、中和线、陷波 | 提高端口隔离 |
| 分时关断未用射频 | 降干扰与功耗 |

隔离目标常看 S21 与总辐射效率；共存还要看接收机阻塞与谐波，不只看天线口[7]。

## 4. 仿真、工艺与验收

常用工具：有限元（HFSS 类）、时域（CST/openEMS）、电路–电磁联合（ADS）。关键指标：S11 带宽、效率、方向图、包络相关系数（多天线时）、人体/手摸失谐[3][8]。

PCB 介电常数公差、阻焊、金属外壳与电池位置都会拉偏谐振；芯片天线厂商效率多为参考板数据。量产应以传导校准 + OTA（总辐射功率 TRP / 总全向灵敏度 TIS）抽测闭环[8][9]。

## 5. 局限、挑战与可改进方向

### 1. 尺寸换效率

**局限**：极小地平面上 Sub-GHz 效率低，链路预算被天线吃掉[4]。
**改进**：优先加长有效地或外置鞭状/柔性天线；协议侧用更低速率/更高扩频换余量。

### 2. 多模互扰

**局限**：同板多射频同时工作，隔离不足导致灵敏度恶化[7]。
**改进**：分时调度；滤波与屏蔽腔；关键接收链路独立天线。

### 3. 仿真–实机偏差

**局限**：理想边界与忽略外壳/电池导致“仿真很好、OTA 很差”[3][8]。
**改进**：早期导入完整装配模型；样机用矢量网络分析仪 + 暗室迭代。

### 4. 可调网络可靠性

**局限**：开关寿命、ESD、温漂改变匹配[5]。
**改进**：少档位覆盖主市场频段；老化与高低温纳入 DFMEA。

## 6. 实践要点

1. 先冻结频段组合与板级净空，再画辐射体，勿先堆模组后补天线。
2. 验收写清自由空间与手持/金属桌面两种工况。
3. 与 `antenna-testing-ota-measurement` 中的 TRP/TIS 流程对齐。

## 参考文献

[1] Balanis, C. A., Antenna Theory: Analysis and Design.
[2] Volakis et al. / IoT multi-band antenna design surveys.
[3] Ansys HFSS / CST application notes on electrically small antennas.
[4] Ground plane size effects on PIFA/IFA efficiency (IEEE APS literature).
[5] Impedance matching and tunable matching networks for multi-band IoT.
[6] Chip antenna vendor datasheets (reference-board efficiency caveats).
[7] Antenna isolation and coexistence in multi-radio handsets/IoT modules.
[8] CTIA / 3GPP OTA test methodologies (TRP, TIS).
[9] PCB manufacturing tolerances impact on resonant antennas.
[10] 3GPP UE antenna performance related TR/TS materials.
[11] Compact dual-band IFA/PIFA case studies for LoRa+BLE trackers.
[12] Human body loading and detuning of wearable/IoT antennas.
