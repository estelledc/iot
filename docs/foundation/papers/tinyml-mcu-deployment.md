---
schema_version: '1.0'
id: tinyml-mcu-deployment
title: TinyML在微控制器上的部署实践
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 16
prerequisites:
  - neural-network-quantization-int8
  - tflite-micro-model-optimization
  - low-power-design-patterns
tags:
  - TinyML
  - MCU部署
  - 边缘推理
  - 量化
  - 内存
  - 基准测试
  - IoT
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# TinyML在微控制器上的部署实践

> **难度**：🟡 中级 | **领域**：边缘 AI | **关键词**：TinyML, 部署, 基准, 内存 | **阅读时间**：约 16 分钟

## 日常类比

把厨房料理机食谱改成一人份便当：同样逻辑，容器（SRAM/Flash）小得多。TinyML 研究如何在微控制器（MCU）上完成有用推理[1][2]。

## 摘要

给出问题选型、工具链（TFLM 等）、内存/延迟/能耗三角与验收基准。宣称“可在 MCU 运行”不等于满足产品时延与续航[2]。

## 1. 何时用 TinyML

| 适合 | 不适合 |
|------|--------|
| 关键词、异常、简单视觉事件 | 大模型生成 |
| 需离线低延迟 | 需频繁重训大模型 |
| 带宽贵/隐私敏感 | 已有常开网关可卸载 |

## 2. 部署清单

| 步骤 | 产出 |
|------|------|
| 任务与指标 | 精度、FAR、延迟、mA |
| 数据 | 代表现场分布 |
| 模型 | 为 MCU 设计的小网 |
| 转换量化 | 检查算子 |
| 板级基准 | 真实周期与内存 |
| 系统集成 | 占空比、安全、OTA |

| 资源 | 经验 |
|------|------|
| Flash | 权重主导 |
| SRAM | 激活峰值+运行时 |
| CPU | 无加速器时瓶颈 |
| 外设 | 采样与预处理开销常被低估 |

## 3. 局限、挑战与可改进方向

### 1. 基准与现场落差

**局限**：干净数据集虚高。
**改进**：现场数据回归；持续采集难例[3]。

### 2. 预处理不一致

**局限**：训练脚本与固件特征不同。
**改进**：同一参考实现；黄金向量测试[2]。

### 3. 更新与版本

**局限**：模型与固件耦合。
**改进**：模型分区 OTA；版本兼容矩阵[4]。

### 4. 安全攻击面

**局限**：对抗样本/模型窃取。
**改进**：安全启动、加密存储、输入校验[5]。

## 总结

TinyML 部署是系统工程：数据、模型、运行时与电源策略一起验收。先写清指标，再选框架与芯片。

## 参考文献

[1] TinyML Foundation / 相关教材概述.
[2] TensorFlow Lite Micro 文档.
[3] 数据集偏移与边缘模型监控文献.
[4] 模型 OTA 与 A/B 分区实践.
[5] 边缘 AI 安全威胁概述.
[6] CMSIS-NN 性能说明.
[7] MCU 选型与 AI 工作负载匹配指南.
[8] 能耗测量（推理/等待）方法.
[9] 量化误差分析基础.
[10] Zephyr/RTOS 上推理任务调度注意.
[11] 端侧 MLOps 轻量流程建议.
[12] 公开 TinyML 基准套件说明.
