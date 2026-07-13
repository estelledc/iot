---
schema_version: '1.0'
id: ce-fcc-certification-iot
title: CE/FCC认证对IoT硬件设计的要求
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 15
prerequisites:
  - conducted-emi-filter-design
tags:
  - CE
  - FCC
  - RED
  - EMC
  - 认证
  - 模块认证
  - 合规
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# CE/FCC认证对IoT硬件设计的要求

> **难度**：🟢 初级 | **领域**：产品认证合规 | **阅读时间**：约 15 分钟

## 日常类比

餐厅没有卫生许可就不能合法营业。CE（Conformité Européenne）与美国联邦通信委员会（Federal Communications Commission, FCC）认证类似电子产品的市场“卫生许可”：功能再好，缺合规就不能在目标市场销售。物联网（Internet of Things, IoT）还叠加无线电、电磁兼容（Electromagnetic Compatibility, EMC）与电气安全[1][4]。

## 摘要

梳理欧盟无线电设备指令（Radio Equipment Directive, RED）路径、FCC Part 15、测试项与预认证模块捷径。周期与限值为常见工程叙事，**以现行法规、协调标准与实验室报价为准**[2][5]。

## 1. 为何必须做

| 因素 | 有认证 | 无认证 |
|------|--------|--------|
| 市场准入 | 可合法销售 | 禁售/下架风险 |
| 平台与渠道 | 可上架 | 易被拒 |
| 执法风险 | 合规经营 | 罚款/召回 |

欧盟侧重 CE 自我声明 + 技术文件；美国对有意辐射体多走 Certification；中国另有 SRRC/CCC 等，本文聚焦 CE/FCC 设计含义[1][4][10]。

## 2. CE / RED 要点

含无线的 IoT 常以 RED（2014/53/EU）为主导，并关联 EMC、低电压（Low Voltage Directive, LVD）与有害物质限制（RoHS）等[1][2]。

| 指令/领域 | 关注 |
|-----------|------|
| RED | 射频、EMC、安全 |
| EMC 指令 | 发射与抗扰 |
| LVD | 电压范围适用时的电气安全 |
| RoHS | 有害物质 |

射频：功率、杂散、占用带宽、频率容差等；EMC：辐射/传导发射与抗扰；安全：引用相关安全标准。未用协调标准或高风险时可能需公告机构（Notified Body）[2][6]。

## 3. FCC Part 15

| 设备类型 | 条款叙事 | 方式叙事 |
|----------|----------|----------|
| 无意辐射体（纯数字） | Subpart B | 供应商符合性声明（SDoC）常见 |
| Wi-Fi/BLE 等有意辐射 | 15.247 等 | Certification + FCC ID |
| 组合产品 | Subpart C 相关 | 按有意辐射路径 |

FCC ID = Grantee Code + Product Code，标签或电子标示。限值与频段细则以 Part 15 及实验室程序为准[4][5]。

## 4. 关键测试与模块路径

| 类别 | 示例 | IoT 关注 |
|------|------|----------|
| 发射 | 辐射/传导、杂散 | 时钟谐波、开关电源、天线谐波 |
| 抗扰 | ESD、RS、EFT、CS | 复位、误触、掉链 |
| 射频 | 功率、带宽、占空比 | 天线增益与区域限值 |

使用已认证无线模块可大幅减少射频重测，但仍须：遵守布局/天线指南、不改匹配、换天线常触发重认证，且整机 EMC 仍要做[7][8]。

| 路径 | 周期叙事 | 适用 |
|------|----------|------|
| 模块 + 整机 EMC | 相对短 | 大多数 IoT |
| 自研射频全测 | 更长更贵 | 定制天线/改模块 |
| SDoC（无意） | 较短 | 无无线数字设备 |

## 5. 局限、挑战与可改进方向

### 1. 原型能连上就当能量产

**局限**：认证失败才改板，成本爆炸。
**改进**：概念阶段锁定市场与指令清单；预扫（pre-scan）进迭代。

### 2. “用了认证模块=整机免测”

**局限**：改天线/净空不够/电源噪声仍挂。
**改进**：严格按模块指南；变更控制；整机 EMC 预算。

### 3. 文档与一致性缺失

**局限**：技术文件、DoC、标签与实机不一致。
**改进**：版本冻结；BOM/天线/固件射频参数受控；保存测试报告年限按法规。

### 4. 多国准入线性叠加被低估

**局限**：只做 CE/FCC，忽略 SRRC 等。
**改进**：按销售国列矩阵；射频参数取各国交集或分 SKU。

## 6. 实践要点

1. 优先选预认证模块 + 参考天线，减少射频变量。
2. 电源与时钟布局按 EMC 设计，认证不是后期“贴补丁”。
3. 提前约实验室做预合规，比正式失败后再改便宜。

## 参考文献

[1] EU, Radio Equipment Directive 2014/53/EU.
[2] EU, EMC Directive 2014/30/EU; LVD 2014/35/EU; RoHS 2011/65/EU.
[3] ETSI EN 300 328 / EN 301 893 (and related RED harmonised standards).
[4] FCC, Title 47 CFR Part 15.
[5] FCC, Supplier's Declaration of Conformity and Certification guidance.
[6] CISPR 32 / IEC 61000-4-2/3/4/6 (EMC emission and immunity).
[7] Module integrator guides (Espressif, Nordic, Silicon Labs examples).
[8] FCC KDB modular approval and antenna change guidance.
[9] ISO/IEC guides on technical documentation and DoC practices.
[10] MIIT SRRC / CCC overview notes for China market access (context).
[11] IEC 62368-1 safety standard family (where applicable).
