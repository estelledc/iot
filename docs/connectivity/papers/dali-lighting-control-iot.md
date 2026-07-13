---
schema_version: '1.0'
id: dali-lighting-control-iot
title: DALI数字照明控制在IoT智能照明中的应用
layer: 2
content_type: technical_analysis
difficulty: beginner
reading_time: 18
prerequisites:
  - knx-smart-building-protocol
tags:
- DALI
- DALI-2
- 照明控制
- IEC 62386
- DiiA
- 智能建筑
- 人因照明
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# DALI数字照明控制在IoT智能照明中的应用

> **难度**：🟢 初级 | **领域**：照明控制、楼宇 IoT | **阅读时间**：约 18 分钟

## 日常类比

老式旋钮调光像「整条走廊共用一个音量旋钮」——同线上的灯只能同升同降。DALI（Digital Addressable Lighting Interface，数字可寻址照明接口）像给每盏灯发门牌号：控制器可单独「@」某一盏，也可按组/场景一键切换。双向总线让灯能「回话」（故障、亮度、寿命），再经网关接到 BMS（Building Management System，楼宇管理系统）或云平台，就从本地调光升级为可运维的照明 IoT。

## 摘要

梳理 IEC 62386 / DALI-2 总线参数、命令与场景、相对 1-10V 与 DMX512 的定位，以及网关上云与节能策略。总线设备数、线长与节能百分比随线径、拓扑与传感器策略变化，须按项目实测，不宜直接外推[1][2][5]。

## 1 从模拟到数字

1-10V 模拟调光无地址、多为单向、分区靠布线。DALI 由 DiiA（Digital Illumination Interface Alliance）推动互操作认证，物理与应用由 IEC 62386 分册定义[1][2]。

| 参数 | 典型取值（规范/常见工程） |
|------|---------------------------|
| 每总线设备数 | 最多约 64（短地址 0–63） |
| 速率 | 约 1200 bps |
| 方式 | 半双工、主从 |
| 空闲总线电压 | 约 16 V 量级 |
| 总线长度 | 常按线径约束，工程上常见数百米量级上限 |

两线无极性，与强电分设；拓扑可星/树/链混合[1]。

## 2 命令、组与场景

亮度常用 0–254 等级（0 熄灭）；对数曲线更贴近人眼感知。灯具可属多个组（常见最多 16 组）；场景（常见 16 个）为各灯预存亮度组合，一键调用[1]。

| 能力 | 作用 |
|------|------|
| 直接调光 | 逐灯设等级 |
| 组命令 | 窗边/走道等同组同动 |
| 场景 | 工作/演示/清洁等预设 |
| 查询 | 实际亮度、故障、工作小时等 |

```
控制器 → 灯具：设亮度 / 调场景
灯具 → 控制器：状态、故障、寿命相关计数
```

## 3 DALI-2 与色彩

DALI-1 侧重输出设备；DALI-2 将按钮、占空/光照等输入设备纳入标准，并加强认证互操作[2]。DT8（Device Type 8）支持 Tc 色温、RGBWAF、xy 色度，为人因照明（按昼夜节律调色温）提供基础[1][2]。

## 4 与 IoT / BMS 集成

DALI 网关把总线命令映射为 BACnet/IP、Modbus TCP、REST 等，供 BMS、云与 App 使用。多总线由应用控制器（Application Controller）汇聚后上以太网[2][5]。

| 对比 | 1-10V | DALI | DMX512 |
|------|-------|------|--------|
| 寻址 | 按区域 | 逐灯（总线内有限地址） | 通道级（舞台常用） |
| 方向 | 多为单向 | 双向 | 多为单向 |
| 典型域 | 简单商业 | 建筑/商业照明 | 演出动态光 |

D4i 等扩展面向灯具内数据与 IoT 接口，选型时核对认证范围[5]。

## 5 节能与运维（机制，非固定百分比）

占空感应、日光采集（Daylight Harvesting）、时间表是常见手段；文献与厂商案例常报可观节电，但幅度强烈依赖建筑、气候与基线灯具，本文不固化「50%–70%」一类无出处总括[4][6]。运维侧：自动编址、平面图映射、远程改场景与故障告警，缩短现场调试与巡检[2]。

应急照明常独立总线以满足法规；分区按楼层/功能切总线，避免单总线过载[1]。

## 6 局限、挑战与可改进方向

### 1. 单总线规模与速率

**局限**：约 64 设备与约 1200 bps 限制大开间与高频遥测。
**改进**：多总线 + 应用控制器；高频数据走 IP 侧聚合，总线侧重控制与状态。

### 2. 网关与语义碎片

**局限**：各厂商网关对象模型不一，BMS 集成成本高。
**改进**：优先 DALI-2/D4i 认证产品；在网关统一映射到 BACnet/Matter 等北向模型[2][5][9]。

### 3. 调试与地址漂移

**局限**：换灯、扩容后短地址与平面图易不一致。
**改进**：强制竣工图与 OBIS 式资产台账；支持自动编址 + 抽检闪灯确认流程。

### 4. 节能数字被营销放大

**局限**：案例节电率不可直接复制到异地项目。
**改进**：以照度达标与 kWh 分项计量做前后对比；分开报告 LED 换灯收益与控制策略收益[4][6]。

## 参考文献

[1] IEC 62386, "Digital addressable lighting interface," International Electrotechnical Commission.
[2] DiiA, "DALI-2 Overview," https://www.dali-alliance.org
[3] DiiA, "IEC 62386 Parts overview and certification," DALI Alliance technical resources.
[4] Illuminating Engineering Society, *The Lighting Handbook* (IES), relevant editions on controls and daylighting.
[5] DiiA, "D4i: DALI for IoT," https://www.dali-alliance.org/d4i/
[6] ASHRAE / IES energy guides on lighting controls (occupancy, daylight harvesting) — project-specific savings.
[7] ANSI E1.11, "USITT DMX512-A," entertainment lighting control (contrast with DALI).
[8] BACnet International, BACnet lighting-related application profiles and gateway practices.
[9] Connectivity Standards Alliance, Matter lighting clusters (northbound interop context).
[10] Lighting Industry Association (LIA) / industry DALI technical guides.
[11] ISO/IEC building automation literature on BMS–lighting integration.
[12] Human-centric lighting reviews (circadian lighting) — apply DT8 carefully with measured lux/CCT.
