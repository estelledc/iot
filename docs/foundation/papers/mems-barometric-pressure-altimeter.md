---
schema_version: '1.0'
id: mems-barometric-pressure-altimeter
title: MEMS气压计高度测量原理与温度补偿
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 15
prerequisites:
  - pressure-sensor-piezoresistive
tags:
  - 气压计
  - 高度计
  - MEMS
  - 温度补偿
  - BMP
  - 导航导航
  - IIR
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# MEMS气压计高度测量原理与温度补偿

> **难度**：🟡 中级 | **领域**：气压高度 | **关键词**：hPa, 国际标准大气, 温度补偿 | **阅读时间**：约 15 分钟

## 日常类比

叠被子：越往上压得越少——大气柱越往高越“薄”，气压下降。经验上大约数米量级高度对应约 1 hPa 量级变化（随温度/纬度变），室内楼层可用气压辅助，但天气系统也会让“同一楼层”气压自己变[1][2]。

## 摘要

说明静压–高度关系、MEMS 膜片传感、温度补偿与滤波、相对高度应用边界。分辨率与噪声**以具体芯片（如 BMP/LPS 系列）手册为准**[3][4]。

## 1. 物理与器件

| 项 | 说明 |
|----|------|
| 静压 p | 随几何高度大致指数下降 |
| 标准大气模型 | 由 p（及温度假设）反推气压高度 |
| MEMS 结构 | 薄膜 + 压阻/电容检测腔压 |

| 误差源 | 影响 |
|--------|------|
| 温度 | 灵敏度与偏移 |
| 天气/气团 | 绝对高度漂移 |
| 气流与安装 | 动压干扰 |
| 量化噪声 | 高度抖动 |

相对高度（短时差分）往往比绝对海拔更可用：先记录参考气压再算 Δh[2]。

## 2. 补偿与滤波

| 手段 | 作用 |
|------|------|
| 片内校准系数 | 出厂温压补偿 |
| 用户二次拟合 | 针对安装微腔 |
| IIR/中值滤波 | 抑抖，代价是延迟 |
| 与加速度计融合 | 楼层检测更稳 |

| 应用 | 注意 |
|------|------|
| 楼层识别 | 门窗通风导致跳变 |
| 无人机定高 | 螺旋桨气流需导管/位置优化 |
| 气象节点 | 需通风防辐射罩 |

## 3. 局限、挑战与可改进方向

### 1. 天气漂移

**局限**：几小时天气变化可等效数米～更多误差。
**改进**：定期 GPS/已知海拔重标定；只报相对高度。

### 2. 温度滞后

**局限**：快速温变时补偿跟不上。
**改进**：热隔离安装；延长稳定时间；双温度点模型。

### 3. 外壳密封错误

**局限**：密封腔压不随环境变，或进水腐蚀。
**改进**：按手册开通气孔；防水透气膜。

### 4. 过度滤波

**局限**：楼梯快速变化被抹平。
**改进**：自适应滤波；事件检测用短窗。

## 4. 实践要点

1. 上电后等待热稳定再取参考点。
2. 数据手册补偿公式逐步实现并对照原始 FIFO。
3. 压阻基础见 `pressure-sensor-piezoresistive`。

## 参考文献

[1] ICAO / US Standard Atmosphere documentation summaries.
[2] Application notes: altitude from barometric pressure.
[3] Bosch BMP280/BMP388 datasheets（示例）.
[4] ST LPS22 series datasheets.
[5] MEMS pressure sensor design reviews.
[6] Temperature compensation of piezoresistive sensors.
[7] Indoor floor detection using barometer papers.
[8] UAV barometer placement and pitot static notes.
[9] Filtering techniques for altimeter data.
[10] Weather-induced barometric drift discussions.
[11] Waterproof breathable membrane packaging notes.
