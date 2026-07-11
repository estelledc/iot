---
schema_version: '1.0'
id: energy-harvesting-iot
title: IoT 能量收集技术
layer: 1
content_type: survey
difficulty: advanced
reading_time: 28
prerequisites:
  - boost-converter-energy-harvesting
  - supercapacitor-iot-energy-buffer
  - duty-cycling-sensor-node
tags:
  - 能量收集
  - 光伏
  - 热电
  - 压电
  - RF收集
  - PMIC
  - 间歇计算
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# IoT 能量收集技术

> **难度**：🟠 进阶 | **领域**：能量收集、自供电系统 | **关键词**：MPPT, TEG, PMIC, 间歇计算 | **阅读时间**：约 28 分钟

## 日常类比

太阳能计算器靠小光伏板工作。把同一思路推到桥梁振动、蒸汽管温差、环境射频（Radio Frequency, RF）：传感器从环境“偷”能量维持运行。大规模部署时，换电池的人工与可达性往往比电池本身更贵——能量收集试图让节点自给[1][10]。

## 摘要

综述光伏、RF、热电（Thermoelectric Generator, TEG）、压电等收集方式，以及电源管理芯片（Power Management IC, PMIC）、储能与间歇计算。功率密度与效率多为文献/手册量级，须按现场实测做能量预算[2][7]。

## 1. 为何需要与功耗预算

| 痛点 | 说明（量级示意） |
|------|------------------|
| 换电成本 | 工业现场人工可达数十美元量级/次 |
| 不可达部署 | 埋入结构、密封腔体 |
| 峰值 vs 平均 | 无线发送瞬时高、平均可极低 |

占空比设计下，深度睡眠占绝大部分时间时，平均功耗可落到微瓦量级，才与室内光/微弱振动等匹配[3][10]。

| 场景倾向 | 方案 |
|----------|------|
| 有稳定光照 | 光伏 |
| 持续振动 | 压电/电磁 |
| 稳定温差 | TEG |
| 有可控 RF 发射 | 专用无线供电（WPT） |
| 仅环境 RF | 超低功耗标签级 |
| 无可用能源 | 长寿命电池或混合 |

## 2. 光伏

室内外功率密度可差多个数量级：正午户外可达约百 mW/cm² 量级，办公室照度下常仅数十 μW/cm² 量级（与电池效率、光谱相关）[1][9]。

| 材料倾向 | 室外 | 室内 | 备注 |
|----------|------|------|------|
| 晶硅 | 效率较高 | 室内相对弱 | 成熟 |
| 非晶硅/有机/钙钛矿等 | 各异 | 室内研究活跃 | 寿命/稳定须验证 |

产品形态从自供电开关到光伏+RF 标签均有；宣称成本与部署量以厂商口径为准，设计勿绑定单一营销数字[3]。

## 3. RF 收集

天线 → 整流 → 升压 → 储能。环境 RF 功率密度通常很低；专用发射器可提高可用功率但受法规 EIRP 限制[6][7]。

| 维度 | 专用 WPT | 环境 RF |
|------|----------|---------|
| 功率 | 可达 mW 级（近距） | 常 μW 级 |
| 距离 | 受链路与法规约束 | 更远但更弱 |
| 发射器 | 需要 | 不需要 |

SoC 集成 RF 收集与蓝牙低功耗（Bluetooth Low Energy, BLE）的路径在演进，仍须验证冷启动与最坏射频环境[6]。

## 4. 热电与压电

塞贝克效应：`V ≈ α·ΔT`。人体数摄氏度温差功率密度常为数十 μW/cm² 量级；工业管道更大 ΔT 可达 mW/cm² 量级（强烈依赖热阻设计）[10]。

| 振动源 | 频率量级 | 备注 |
|--------|----------|------|
| 人体行走 | 数 Hz | 鞋底等结构 |
| 桥梁 | 数–数十 Hz | 加速度往往很小 |
| 电机/HVAC | 工频及谐波 | 需调谐到谐振 |

MEMS 压电体积小，输出常偏 μW；宏观悬臂梁可更高但体积大[1]。

## 5. PMIC 与储能

PMIC 职责：最大功率点追踪（Maximum Power Point Tracking, MPPT）、升降压、冷启动、充放电管理[2][5]。

| 能力 | 设计要点 |
|------|----------|
| 冷启动 | 启动电压须低于收集器最坏开路/工作点 |
| 效率 | 手册峰值≠轻载实测 |
| 多源 | 光+热+振动切换需策略 |

| 储能 | 特点 | 角色 |
|------|------|------|
| 超级电容 | 功率密度高、循环多、自放电偏高 | 发送峰值缓冲 |
| 薄膜锂等 | 能量密度较高 | 夜间/无能源时段 |
| 混合 | 常见 | 峰值与长期分工 |

## 6. 间歇计算

能量不足时系统反复掉电。挑战：RAM/外设状态丢失、时间基失效、任务原子性。路径包括检查点、任务化编程、非易失存储器（如 FRAM）MCU 等；开销与正确性模型因框架而异[4][8]。

## 7. 能量预算模板（示意）

1. 算周期平均功耗：`P_avg = Σ(P_i·t_i)/T`
2. 估最差可收集功率（阴天/静止/最小 ΔT）并乘安全系数
3. 只有 `P_harvest_worst > P_avg` 才称“可自持”；峰值靠电容支撑

| 常见错误 | 改进 |
|----------|------|
| 忽略冷启动 | 选匹配 PMIC 并实测启动 |
| 储能过小 | 按发送能量+电压降落容 |
| 忽略自放电 | 夜间能量衡算 |
| 只用平均天气 | 按最差季节设计 |
| 盲信 MPPT 峰值效率 | 轻载实测 |

## 8. 局限、挑战与可改进方向

### 1. 环境能量非平稳

**局限**：夜间无光、设备停振、温差消失会使“自供电”中断。
**改进**：多源混合；尺寸化最差工况；允许间歇计算或备用一次电池[1][2]。

### 2. 峰值无线与平均收集不匹配

**局限**：LoRa/蜂窝发送脉冲功率远超收集器连续输出。
**改进**：超级电容缓冲；拉长上报周期；选更低能量空中协议[3][5]。

### 3. 间歇计算工程化不足

**局限**：检查点磨损 NVM、外设恢复复杂，业务逻辑难保证恰好一次语义。
**改进**：任务边界清晰的固件架构；FRAM 类 MCU；关键动作用电容保证原子完成[4][8]。

### 4. 宣称效率与现场落差

**局限**：室内光伏/RF 白皮书数字在脏污、遮挡、多径下大幅下滑。
**改进**：现场照度/场强测绘；留 2× 以上能量余量；可维护的板面清洁与天线朝向[7][9]。

## 总结

能量收集可行的前提是占空比把平均功耗压到与环境功率密度同量级，并用 PMIC+储能扛峰值。选型按能源种类，验证按最坏日，软件按可能掉电来写。

## 参考文献

[1] S. Roundy et al., Energy harvesting for IoT 相关综述, *IEEE IoT Journal* / 同类期刊.
[2] e-peas, AEM30940 Multi-Source Energy Harvesting PMIC Datasheet.
[3] Wiliot, IoT Pixel battery-free Bluetooth tag 白皮书（产品口径参考）.
[4] J. Hester et al., Batteries Not Included / intermittent computing 综述, *ACM Computing Surveys* 相关工作.
[5] Texas Instruments, BQ25570 Ultra Low-Power Harvester PMIC 数据手册.
[6] Atmosic, ATM33 Bluetooth SoC with RF Energy Harvesting 产品文档.
[7] Yole 等, Energy Harvesting Technologies for IoT 市场/技术报告（量级参考）.
[8] A. Colin et al., Reconfigurable energy storage for energy-harvesting devices, ASPLOS 相关.
[9] 室内钙钛矿/有机光伏效率报道（如 *Nature Energy* 等，须核对具体条件）.
[10] P. Maharjan et al., Self-powered IoT sensors 能量收集技术综述, *Nano Energy* 等.
[11] Powercast / Energous 等 WPT 应用笔记与法规说明.
[12] IEEE 802.11ba Wake-up Radio 等低功耗唤醒相关标准文本.
