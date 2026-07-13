---
schema_version: '1.0'
id: on-device-training
title: 设备端在线训练：让边缘模型持续进化
layer: 5
content_type: technical_analysis
difficulty: advanced
reading_time: 25
prerequisites:
  - continual-learning-edge
  - federated-learning-iot
  - model-compression-edge
tags:
- 设备端训练
- TinyTL
- LoRA
- QLoRA
- PockEngine
- 迁移学习
- PEFT
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 设备端在线训练：让边缘模型持续进化

> **难度**：🟡 进阶 | **领域**：迁移学习、参数高效微调、边缘训练 | **阅读时间**：约 25 分钟

## 日常类比

出厂的导航地图在实验室路况上很准，开到新城市却总偏航——分布变了。把所有行车视频回传云端重训，又慢又不想泄露轨迹。设备端训练像让车机在本地「开一会、记一会」：只改少量可调参数（或旁路模块），适应当地口音、光照与产线，数据尽量不出设备。代价是训练比推理吃内存得多，像边开车边在副驾上摊开厚厚的草稿纸（激活、梯度、优化器状态）。

## 摘要

本文对比推理与训练的资源差，梳理 TinyTL、PockEngine、LoRA/QLoRA 与联邦参数高效微调（Parameter-Efficient Fine-Tuning, PEFT）在微控制器（MCU）到边缘图形处理器上的路径。内存与加速倍数来自公开论文量级，跨框架差异大，须在目标板验证[1][3][4][5]。

## 1 为何需要设备端训练

部署后分布偏移常见：语音助手遇地方口音、质检换产线光照、视觉模型遇季节变化。云端回流链路慢、依赖网络且触碰隐私。设备端训练追求就地适应；与持续学习（见 continual-learning-edge）共享「学新不忘旧」问题。

| 资源 | 推理 | 训练 | 差异倾向 |
|------|------|------|---------|
| 参数相关内存 | 权重 | 权重 + 梯度 + 优化器状态 | 约 3–4× |
| 中间激活 | 可逐层释放 | 反向传播需保留 | 约 5–10× |
| 计算 | 前向 | 前向 + 反向 | 约 2–3× |
| ResNet-50 量级总内存 | 约百 MB | 可达约 GB 级 | 约一个数量级 |

激活存储通常是训练内存大头：冻结大部分层可避免为其保存激活，这是边缘可行微调的关键杠杆。

## 2 迁移学习策略

预训练底层特征可迁移；边缘上优先少更新参数。

| 策略 | 更新参数比例倾向 | 内存 | 速度 | 精度倾向 | 适用 |
|------|-----------------|------|------|---------|------|
| 全量微调 | 100% | 最高 | 最慢 | 最好 | 云/强 GPU |
| 只调分类头 | 约 2–5% | 低 | 快 | 中 | 弱边缘 |
| 解冻最后 N 层 | 约 10–30% | 中 | 中 | 较好 | 中等算力 |
| LoRA / Adapter | 约 0.1–1% | 很低 | 快 | 较好 | 极受限 / 大模型[4] |

## 3 TinyTL：MCU 级迁移学习

TinyTL（Tiny Transfer Learning）面向约数百 KB SRAM 的 MCU：仅调头仍可能因 backbone 前向激活爆内存[1]。方案在冻结主干旁加极轻量 Lite Residual 旁路（降维–少量可训参数–升维），主干不反传故无需存其激活。

| 方法（论文设定） | 峰值内存倾向 | 迁移精度倾向 | 可训参数倾向 |
|-----------------|-------------|-------------|-------------|
| 全量微调 | >2 MB（易 OOM） | — | 100% |
| 只调最后 1 层 | ~1 MB（易 OOM） | — | ~2% |
| TinyTL Bias-only | ~230 KB | 较低 | ~0.5% |
| TinyTL Lite Residual | ~285 KB | 更高 | ~1% |

公开称相对标准微调内存可降约数倍；后续工作进一步讨论 256 KB 级设备端训练[2]。精度数字依赖 Cars→CUB 等设定，换任务需重测。

## 4 PockEngine：把训练当编译

PockEngine 在部署前静态分析训练图：融合反向、消除冻结层反传、规划张量生命周期；支持稀疏反向（只更新梯度较大的部分通道）与量化感知训练扩展[3]。公开报告在 Jetson AGX 上相对 PyTorch 微调可达约一个数量级加速与显著降内存；树莓派 4 上使 ResNet-50 级微调从「无法运行」变为可运行（约 GB 以下内存量级）[3]。具体倍数随模型与批大小变化。

## 5 LoRA / QLoRA 上边缘

LoRA（Low-Rank Adaptation）假设微调增量 \(\Delta W\) 低秩：\(\Delta W=BA\)，秩 \(r\ll d\)。例如 \(4096\times4096\) 全量对比 \(r=8\) 时，可训参数可降到约百分之一以下量级[4]。

挑战：即使只训 LoRA，仍需存前向激活。梯度检查点（Gradient Checkpointing）用重计算换内存，额外算力常约数十百分点，内存可降数倍。QLoRA 将基座以 4-bit（如 NF4）存储、LoRA 以较高精度训练，使更大模型进入单卡/边缘盒内存预算[5]。

| 设备类（示意） | 模型量级 | LoRA \(r\) | 内存倾向 | 相对全量精度 |
|---------------|---------|-----------|---------|-------------|
| 高端 Jetson | 7B INT4 | 8 | 约十余 GB | 接近 |
| 8GB 边缘盒 | 小 LLM INT4 | 4 | 约数–7 GB | 略降 |
| 消费级 ARM 笔记本 | 7B INT4 | 8 | 近内存上限 | 接近 |
| 树莓派级 | 更小模型 | 4 | 数 GB | 掉点更多 |

表中为公开实践/报告量级，非保证 SLA。

## 6 联邦设备端训练

各设备本地 PEFT（LoRA/TinyTL），只上传小适配器；与联邦学习（见 federated-learning-iot）结合。FedPETuning 等将 LoRA/Adapter/Prompt 与联邦聚合结合：通信量相对传全模型可降约两个数量级；异构设备可用不同秩再对齐聚合[6]。公开 GLUE 设定下可达接近集中式 LoRA 的性能比例，仍受 Non-IID 影响。

端到端示意：加载量化基座 → 挂 LoRA → 本地数个 epoch → 上传约百 KB–MB 级适配器 → 服务器聚合 → 回写。

## 7 方法对照与前沿

| 方法 | 年份 | 目标硬件倾向 | 最小内存量级 | 策略 |
|------|------|-------------|-------------|------|
| TinyTL | 2020 | MCU | 约 200+ KB | Lite Residual[1] |
| PockEngine | 2023 | RPi/Jetson | 约亚 GB | 编译+稀疏反传[3] |
| QLoRA | 2023 | GPU/强边缘 | 约十余 GB（7B） | NF4+LoRA[5] |
| FedPETuning | 2024 | 异构设备 | 视设备 | 联邦+PEFT[6] |
| 分层 LoRA / MoE 卸载 | 2024 | 2–8 GB | 更低峰值 | 逐层或专家换入[7] |

## 8 局限、挑战与可改进方向

### 1. 无标签与弱监督

**局限**：现场数据常无标签；纯自监督或伪标签在类别漂移下不稳定。
**改进**：主动学习只标不确定样本；半监督 + 少量专家标；与自监督预训练（见 self-supervised-pretraining-device）衔接。

### 2. 中断与检查点

**局限**：电池耗尽、OOM、进程被杀使长微调不可靠。
**改进**：按 step 持久化适配器与优化器；空闲/充电窗口训练；失败重试与幂等聚合。

### 3. 灾难性遗忘

**局限**：只拟合本地新数据会损害通用能力与他域性能。
**改进**：回放缓冲、正则（EWC 类）、只训低秩旁路；与持续学习方法组合评估旧任务指标。

### 4. 安全与投毒

**局限**：本地可写训练接口扩大攻击面；联邦场景恶意适配器可污染全局。
**改进**：签名与策略限制可训模块；聚合侧异常检测与范数裁剪；敏感模型训练放入 TEE（见 privacy-computing-tee-fl）。

## 参考文献

[1] H. Cai et al., "TinyTL: Reduce Memory, Not Parameters for Efficient On-Device Learning," NeurIPS, 2020.
[2] J. Lin et al., "On-Device Training Under 256KB Memory," NeurIPS, 2022.
[3] L. Liang et al., "PockEngine: Sparse and Efficient Fine-tuning in a Pocket," MLSys, 2023.
[4] E. J. Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models," ICLR, 2022.
[5] T. Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs," NeurIPS, 2023.
[6] J. Zhang et al., "FedPETuning: When Federated Learning Meets the Parameter-Efficient Tuning Methods of Foundation Models," ACL Findings, 2024.
[7] R. Yi et al., "EdgeMoE: Fast On-Device Inference of MoE-based Large Language Models," arXiv, 2024.
[8] J. Lin et al., "MCUNet: Tiny Deep Learning on IoT Devices," NeurIPS, 2020.
[9] E. Ben Zaken et al., "BitFit: Simple Parameter-efficient Fine-tuning for Transformer-based Masked Language-models," ACL, 2022.
[10] N. Houlsby et al., "Parameter-Efficient Transfer Learning for NLP," ICML, 2019.
[11] S. Mangrulkar et al., "PEFT: State-of-the-art Parameter-Efficient Fine-Tuning," Hugging Face, 2022–.
[12] D. J. Beutel et al., "Flower: A Friendly Federated Learning Framework," 相关技术报告/文档.
