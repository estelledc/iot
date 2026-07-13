---
schema_version: '1.0'
id: esd-protection-circuit-design
title: ESD静电防护电路设计与TVS选型
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 18
prerequisites:
  - emc-fundamentals-iot-device
  - decoupling-capacitor-placement
tags:
  - ESD
  - TVS
  - IEC61000-4-2
  - HBM
  - CDM
  - 静电防护
  - PCB布局
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# ESD静电防护电路设计与TVS选型

> **难度**：🟢 初级 | **领域**：静电防护设计 | **关键词**：TVS, HBM, CDM, IEC 61000-4-2 | **阅读时间**：约 18 分钟

## 日常类比

冬天脱毛衣被门把手电一下，就是**静电放电**（ElectroStatic Discharge, ESD）。对人只是一激灵；对物联网（IoT）芯片可能当场击穿，或留下潜伏缺陷，数周后才死机。防护要靠系统级器件与布局，不能只靠芯片自带的弱保护[1][2]。

## 摘要

从摩擦起电、人体模型（Human Body Model, HBM）与带电器件模型（Charged Device Model, CDM）出发，对照 IEC 61000-4-2 与元件级标准，讲解 TVS（Transient Voltage Suppressor）选型、阵列、布局与测试判据。电压/电容数值为常见量级，以器件手册与实测钳位为准[3][4]。

## 1. 机理与损伤

低湿度更易积累静电；人体可带数千伏量级，经指尖放电峰值电流可达安培量级[1]。

| 模型 | 电容/电阻量级 | 特点 |
|------|---------------|------|
| HBM | 约 100 pF + 1.5 kΩ | 人手触摸 |
| CDM | 数–数十 pF，电阻极低 | 器件自身对地，上升更快 |

损伤：栅氧击穿、结熔融、**潜伏损伤**（出厂可测过、现场早死）。故须预防为主[2]。

## 2. 标准

| IEC 61000-4-2 等级 | 接触放电（kV） | 空气放电（kV） |
|--------------------|----------------|-----------------|
| 1 | 2 | 2 |
| 2 | 4 | 4 |
| 3 | 6 | 8 |
| 4 | 8 | 15 |

IoT 整机常瞄等级 3 或 4，以产品标准为准。元件级 JS-001（HBM）、JS-002（CDM）等与系统级**数值不可直接换算**[1][5]。

## 3. 防护策略与 TVS 选型

外部 TVS 在连接器入口泄放；片上保护通常远不够 IEC 接触数千伏；布局决定寄生电感[2][3]。

| 类型 | 适用 |
|------|------|
| 单向 | 单极性 0–VCC |
| 双向 | 可能为负或差分（USB D± 等） |

| 参数 | 要点 |
|------|------|
| VRWM | > 信号最高电压并留余量 |
| VBR | 正常不导通 |
| VCL | 钳位须低于 IC 绝对最大 |
| IPP | 覆盖目标 ESD 电流量级 |
| CJ | 高速接口要足够小 |

高速：USB2 常要求约 pF 级或更低；更高速率更严。响应时间通常皮秒级，一般非瓶颈；聚合物抑制器钳位高、须慎用在精密数字脚[3][4]。

## 4. 阵列、其他器件与放置

多线接口用 TVS 阵列省面积。压敏电阻能量大但钳位高、电容大，偏电源粗保护；火花间隙零成本但不稳定，仅辅助。

**正确**：连接器 → 极近 TVS → 再进 IC；TVS 到连接器走线宜短（毫米量级经验）。**错误**：TVS 放在 IC 旁、长走线先到芯片[2]。

## 5. PCB 布局

`V = L·di/dt`：纳亨级电感在安培/纳秒沿下可额外抬数伏。TVS 接地多过孔直通地平面；保护环与连续地平面降低地弹耦合[3]。

| 接口示例 | 注意 |
|----------|------|
| USB | VBUS 保险丝+TVS；D± 低 CJ 双向 |
| 天线 | 极低 CJ；接受较高钳位时用聚合物等 |
| GPIO | TVS + 可选串联电阻限流 |

## 6. 测试与常见错误

ESD 枪按等级对可触及点放电；判据 A–D（正常/自恢复/需干预/损坏）[1]。由低到高、接触优先、记录响应。

| 错误 | 后果 | 纠正 |
|------|------|------|
| TVS 离连接器远 | 钳位抬升 | ≤数 mm 入口放置 |
| 接地过孔不足 | 地弹、误复位 | 多过孔+地连续 |
| VRWM 过高 | VCL 伤 IC | 在满足 VRWM 下选低 VCL |
| 忽略天线 | 强耦合入口 | 低电容保护 |

## 7. 局限、挑战与可改进方向

### 1. VCL 与 IC 耐压窗口窄

**局限**：逻辑摆幅与 IC Abs Max 接近时，可选 TVS 很少。
**改进**：串联电阻分担；选专用低钳位工艺；升级更耐 ESD 的 IO 型号[3][4]。

### 2. 高速眼图与 CJ 冲突

**局限**：加 TVS 后 USB/HDMI 眼图塌陷。
**改进**：通道仿真；共封装阵列；必要时改连接器与走线阻抗[4]。

### 3. 重复放电老化

**局限**：部分 MOV/聚合物多次冲击后漏电或钳位漂移。
**改进**：关键口用硅 TVS；定期抽测；浪涌与 ESD 分级防护[4]。

### 4. 系统级与芯片级混淆

**局限**：采购“HBM 8 kV”芯片就取消板级 TVS，整机 IEC 仍失败。
**改进**：芯片级仅作制造防护参考；整机按 IEC 61000-4-2 设计验证[1][5]。

## 总结

ESD 防护是入口 TVS + 短低感接地 + 按接口选 CJ/VCL，并用 ESD 枪闭环。木桶最短板决定整机；每个外露接口都要有策略。

## 参考文献

[1] IEC 61000-4-2, Electrostatic discharge immunity test.
[2] STMicroelectronics, AN4835 ESD protection design guide for STM32.
[3] Texas Instruments, SLVA680 ESD protection guide for high-speed interfaces.
[4] Littelfuse, TVS Diode Selection / Application Notes.
[5] JEDEC JS-001 / JS-002, HBM / CDM 元件级标准.
[6] AEC-Q101, 分立半导体应力鉴定（车规防护器件背景）.
[7] ESD Association, ESD 基础与控制实践文件.
[8] Nexperia / Infineon USB/HDMI TVS 阵列应用笔记.
[9] IEC 61000-4-2 系统级与 HBM 对比技术文章（厂商白皮书）.
[10] PCB 地弹与保护环设计应用笔记.
[11] 聚合物 ESD 抑制器数据手册与局限说明.
[12] Soft fails vs hard fails 在便携设备 ESD 中的分类讨论（行业文献）.
