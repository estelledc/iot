---
schema_version: '1.0'
id: conformal-coating-iot-protection
title: 三防漆在IoT户外设备中的防护应用
layer: 1
content_type: technical_analysis
difficulty: beginner
reading_time: 14
prerequisites: UNKNOWN
tags:
  - 三防漆
  - 共形涂层
  - PCB防护
  - 派瑞林
  - IPC-CC-830
  - 户外IoT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 三防漆在IoT户外设备中的防护应用

> **难度**：🟢 初级 | **领域**：PCB防护工艺 | **阅读时间**：约 14 分钟

## 日常类比

没雨棚的房子遇风雨会渗水生锈；PCB 是设备的“房子”，三防漆（Conformal Coating，共形涂层）是贴合轮廓的薄防护膜——像薄手套包住板与器件，挡潮、盐雾、霉与灰尘[1][2]。

## 摘要

对比丙烯酸（AR）、有机硅（SR）、聚氨酯（UR）、环氧（ER）、派瑞林（Parylene）的取舍，说明涂覆/遮蔽/固化/检验，以及天线禁涂与连接器策略。厚度与寿命数字为工艺量级，**随材料、环境与工艺窗口变化**[1][3]。

## 1. 为何户外 IoT 需要

凝露、盐雾、吸湿灰尘与化学气体会引发漏电与腐蚀。室内消费电子常可省略；非受控环境应评估涂层或更高防护（灌封/密封壳）[2][4]。

| 威胁 | 无涂层风险叙事 | 有涂层叙事 |
|------|----------------|------------|
| 高湿凝露 | 表面水膜漏电 | 绝缘电阻更易保持 |
| 盐雾 | 铜/焊点加速腐蚀 | 延缓电化学通路 |
| 灰尘+湿 | 导电桥 | 灰尘不直接贴走线 |

## 2. 材料选型

| 类型 | 优点 | 代价 | 常见场景 |
|------|------|------|----------|
| AR 丙烯酸 | 易溶剂返修、快干 | 耐化学较弱 | 原型/需维修 |
| SR 有机硅 | 宽温、柔韧 | 返修难 | 高温/汽车电子 |
| UR 聚氨酯 | 耐化学、耐磨 | 固化慢、难返修 | 化工/恶劣 |
| ER 环氧 | 硬、耐化学 | 脆、应力、难返修 | 一次性高防护 |
| 派瑞林 | 气相均匀、可极薄 | 真空设备、成本高 | 高可靠/医疗级叙事 |

选型按温度、化学暴露、返修与射频敏感度匹配，而非“越贵越好”。派瑞林 N/C/D 介电与耐温不同，天线附近常关注低介电型号[3][5]。

## 3. 工艺与质量

刷涂/喷涂适合样机与小批量；选择性涂覆适合量产一致性；浸涂覆盖好但遮蔽重。必须遮蔽：连接器触点、测试点、开关、散热面、天线区、传感器感测窗[2][6]。

固化：室温、UV、热或湿气，视材料而定；UV 阴影区常需二次固化。检验：UV 荧光查覆盖与针孔；材料鉴定常对标 IPC-CC-830 等[1][6]。

| 失效 | 常见根因 | 预防 |
|------|----------|------|
| 脱层 | 助焊剂/油污 | 涂前清洗（可加等离子） |
| 开裂 | 过厚/热冲击 | 控厚、选柔性料 |
| 白化 | 高湿涂覆 | 控环境湿度 |

## 4. IoT 特殊点

涂层改变天线等效介电 → 谐振偏移与失配：禁涂、涂后重匹配，或选低介电材料。大功率器件表面涂层增加热阻；低功耗节点通常次要。连接器：IP 密封件与“根部涂、触点遮”常组合使用[4][7]。

## 5. 局限、挑战与可改进方向

### 1. 遮蔽失误

**局限**：触点/天线误涂导致接触不良或射频劣化。
**改进**：工艺文件明确 keep-out；工装/可剥胶；荧光全检。

### 2. 返修成本

**局限**：UR/ER/派瑞林难去除，现场维修昂贵。
**改进**：需维修产品优先 AR；模块化可换板设计。

### 3. 天线与传感器窗口

**局限**：介质层改变射频与气敏/光敏响应。
**改进**：禁涂区设计；涂后校准；传感器选型考虑窗口材料。

### 4. 清洁不足

**局限**：残留导致脱层，盐雾试验“看起来涂了却早失效”。
**改进**：焊后清洗→烘干→涂覆标准流程；抽检附着力。

## 6. 实践要点

1. 先定环境与返修策略，再定材料与涂覆方式。
2. 量产前做温湿/盐雾与射频回归，不只看外观荧光。
3. 成本含遮蔽不良与 VOC/设备摊销，勿只比桶装单价。

## 参考文献

[1] IPC-CC-830, Qualification and performance of electrical insulating compounds (conformal coating).
[2] IPC-A-610, Acceptability of electronic assemblies — conformal coating sections.
[3] HumiSeal / coating vendors, Selection and application guides for conformal coatings.
[4] MIL-I-46058C (historical reference) and industry mapping discussions.
[5] Parylene type N/C/D dielectric and deposition process overviews.
[6] Selective coating, masking, and UV inspection process notes (EMS guides).
[7] Antenna detuning due to conformal coatings (RF design application notes).
[8] SMTA / industry papers on conformal coating technology for electronic assemblies.
[9] VOC, pot life, and production yield considerations for AR/UR coatings.
[10] Combined IP-rated connectors and board-level coating strategies for outdoor IoT.
[11] Adhesion failure modes: contamination, thickness, and thermal shock.
