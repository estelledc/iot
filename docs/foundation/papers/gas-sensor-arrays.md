---
schema_version: '1.0'
id: gas-sensor-arrays
title: 气体传感器阵列与电子鼻
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 18
prerequisites:
  - electrochemical-gas-sensor-principle
  - mox-metal-oxide-gas-sensor
tags:
  - 电子鼻
  - 气体传感器阵列
  - MOX
  - 模式识别
  - 交叉灵敏度
  - 漂移补偿
  - 气味识别
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 气体传感器阵列与电子鼻

> **难度**：🟡 中级 | **领域**：化学传感 | **关键词**：电子鼻, MOX 阵列, 交叉灵敏度, 漂移 | **阅读时间**：约 18 分钟

## 日常类比

人鼻不是靠一个受体认咖啡香，而是一群受体的响应模式。电子鼻（Electronic Nose）用多种气体传感器组成阵列，配合模式识别区分气味或气体混合物——单传感器常因交叉灵敏度“认错人”[1][2]。

## 摘要

说明金属氧化物（Metal Oxide, MOX）、电化学、光电等阵列单元，交叉灵敏度、特征与分类，以及标定与漂移维护。识别率与寿命为实验/产品宣称量级，**以场景实测为准**[3][4]。

## 1. 阵列单元

| 类型 | 优点 | 代价 |
|------|------|------|
| MOX | 便宜、对多 VOC 有响应 | 加热功耗、漂移、湿度敏感 |
| 电化学 | 对目标气体选择性较好 | 寿命、温湿度、交叉气体 |
| NDIR 等 | 对特定分子更专一 | 成本、体积 |

电子鼻故意利用“半选择性”差异，形成高维指纹；也可用温度调制让单 MOX 产生类阵列特征[5][10]。

## 2. 算法与架构

流程：基线/ΔR/R₀ 等特征 → 降维或特征选择 → 分类/回归（SVM、随机森林、浅层网络等）[2][8]。边缘可跑轻量模型；云端做重训练。系统含气路（或扩散腔）、加热控制、温湿度同步测量。

| 问题 | 常见对策 |
|------|----------|
| 交叉灵敏度 | 阵列 + 多变量模型 |
| 湿度耦合 | 同板温湿度补偿 |
| 慢响应 | 动态特征 / 储备池计算等[4] |

## 3. 应用与维护

食品新鲜度、室内空气、工业泄漏筛查、研究用气味区分。标定：目标场景气袋/发生器；维护：周期重标定、漂移自适应、OTA 更新模型[7][9]。

## 4. 局限、挑战与可改进方向

### 1. 长期漂移

**局限**：MOX 基线与灵敏度随时间/中毒变化，模型失效。
**改进**：集成学习漂移补偿；定期用标准气校准；特征用相对变化[7]。

### 2. 实验室精度难迁移现场

**局限**：温湿、风速、干扰气体与训练集不同。
**改进**：现场数据微调；域自适应；限制宣称类别[9]。

### 3. 加热功耗

**局限**：阵列常开加热不适合电池节点。
**改进**：占空比加热、低温材料、电化学/光学混搭[6]。

### 4. 标注数据贵

**局限**：监督学习需要昂贵配气。
**改进**：半监督/异常检测先做报警；共享开放数据集[2]。

## 总结

电子鼻的核心是“差异化交叉响应 + 稳健特征 + 持续标定”，不是堆更多传感器。物联网部署必须把漂移与现场域偏移写进运维，而不是一次性训练。

## 参考文献

[1] K. Persaud, G. Dodd, Model nose discrimination mechanisms, Nature.
[2] S. Marco, A. Gutierrez-Galvez, Signal and data processing for machine olfaction, IEEE Sensors J.
[3] Bosch Sensortec, BME688 开发套件用户指南.
[4] J. Fonollosa et al., Reservoir computing for chemosensor arrays, Sens. Actuators B.
[5] W. Hu et al., Edge-AI electronic nose, Nature Food（应用对照）.
[6] Sensirion, SGP41 multi-pixel gas sensor datasheet.
[7] A. Vergara et al., Drift compensation using classifier ensembles, Sens. Actuators B.
[8] K. Yan, D. Zhang, Feature selection on correlated gas sensors, Sens. Actuators B.
[9] J. A. Covington et al., Artificial olfaction roadmap, IEEE Sensors J.
[10] T. Liu et al., 1D-CNN with temperature-modulated MOX, Sens. Actuators B.
[11] Figaro / 其他 MOX 应用笔记（交叉灵敏度表）.
[12] ISO / 气味与室内空气评价相关标准选篇（应用边界）.
