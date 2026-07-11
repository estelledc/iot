---
schema_version: '1.0'
id: on-device-diffusion-model
title: 端侧 Diffusion Model 部署
layer: 5
content_type: technical_analysis
difficulty: intermediate
reading_time: 24
prerequisites:
  - model-compression-edge
  - knowledge-distillation-edge
  - edge-gan-generation
tags:
- 扩散模型
- DDPM
- DDIM
- LCM
- Stable Diffusion
- 端侧推理
- 量化
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 端侧 Diffusion Model 部署

> **难度**：🟡 中级 | **领域**：扩散模型、模型压缩、移动端推理 | **阅读时间**：约 24 分钟

## 日常类比

干净白板上不断泼墨（正向加噪），再学一步步擦墨还原成画（反向去噪）——这就是扩散模型（Diffusion Model）的直觉。擦墨往往要几十到上千步，每步跑一遍神经网络；在手机或物联网（Internet of Things, IoT）网关上，整段采样可能要数秒到数十秒。端侧部署的核心是：**少步采样 + 小模型 + 硬件友好推理**，而不是把云端 Stable Diffusion 原样搬下来。

## 摘要

本文说明去噪扩散概率模型（Denoising Diffusion Probabilistic Models, DDPM）与隐式采样（DDIM）、一致性模型（Latent Consistency Model, LCM）等加速路径，以及蒸馏、量化、特征缓存与潜在空间扩散在端侧的取舍。延迟、FID 与芯片算力数字来自公开论文/厂商演示量级，跨设备差异大，须实测[1][2][3][5]。

## 1 扩散基础

正向过程按噪声调度 \(\beta_t\) 向数据加高斯噪声；利用 \(\bar\alpha_t=\prod_{s=1}^{t}\alpha_s\) 可从 \(x_0\) 一步跳到任意 \(t\)。反向过程训练网络预测噪声（或 \(x_0\)），损失多为均方误差（Mean Squared Error, MSE）[1]。

去噪骨干多为 U-Net：编码器下采样、瓶颈、解码器上采样并拼接跳跃连接；时间步经多层感知机嵌入后调制各层。教学实现可参考开源 diffusers；生产部署应绑定具体导出格式（ONNX / Core ML / TFLite 等）。

## 2 采样方法对比

| 采样方法 | 步数量级 | 质量倾向 | 端侧可行性 |
|---------|---------|---------|-----------|
| DDPM | 约 10³ | 高 | 通常不可行[1] |
| DDIM | 约 20–50 | 接近多步 | 边缘勉强–可行[2] |
| DPM-Solver 系 | 约 10 | 接近多步 | 较可行[7] |
| LCM / Turbo 类 | 约 1–4 | 可接受–下降 | 更适合实时[3] |

DDIM 将采样改为可跳步的确定性（或弱随机）更新，显著减少网络调用次数[2]。LCM 通过一致性蒸馏，让学生网络用极少步逼近教师多步轨迹[3]。公开 A100 上 512×512 延迟从数十秒量级（千步）降到亚秒–数百毫秒量级（少步），端侧绝对时间仍取决于芯片与实现[3][7]。

## 3 模型压缩

大型潜在扩散（如 SD 1.5 的 U-Net 约数亿参数）需压缩才能进手机内存预算[4]。

| 方法 | 体积/参数倾向 | 质量风险 | 加速倾向 | 适用 |
|------|--------------|---------|---------|------|
| INT8 量化 | 约 4× 体积 | FID 常升数点 | 约 2–3× | 通用[9] |
| INT4 量化 | 约 8× 体积 | 质量掉点更明显 | 更高 | 可容忍失真 |
| 知识蒸馏 | 参数可降数倍–约一个数量级 | 依赖教师与数据 | 显著 | 有教师时 |
| 通道剪枝 | 约 2–3× | 中等 | 约 2× | CNN 骨干 |
| Token 合并等 | 视实现 | 较小–中等 | 约 1.5–2× | Transformer 块 |

训练后量化（Post-Training Quantization, PTQ）需用校准集跑若干加噪时间步；扩散对激活分布敏感，公开工作指出需针对时间步或模块定制量化策略[9]。蒸馏可同时匹配噪声目标与教师预测。

## 4 移动端 Stable Diffusion（公开演示量级）

| 配置 | 时间量级 | 分辨率 | 步数 | 平台（演示） |
|------|---------|--------|------|-------------|
| SD 1.5 优化 | 约数秒–十余秒 | 512×512 | ~20 | Snapdragon 8 Gen 系列 |
| SD Turbo / LCM-LoRA | 约 1–数秒 | 512×512 | ~4 | 旗舰手机 NPU/GPU |
| SnapFusion 等 | 约 2 秒内目标 | 文本生图 | 少步 | 移动端专项优化[5] |

常见优化：神经网络处理单元（Neural Processing Unit, NPU）上 INT8/FP16 混合；U-Net 分块加载控峰值内存；移动版 Flash Attention；相邻去噪步特征缓存（如 DeepCache，公开称可约 2–3× 加速、FID 升约 1–2 点量级）[6]。

| 设备类（示意） | 芯片算力量级 | 512×512 多步生图 |
|---------------|-------------|-----------------|
| 旗舰手机 A 系列 / 8 Gen | 十余–数十 TOPS | 约数秒–十余秒 |
| 平板/笔记本 M 系 | 十余–数十 TOPS | 常快于同代手机 |
| 上一代中端 | 更低 | 可达十余秒以上 |

厂商 TOPS 与端到端延迟不可直接换算；以板级 profiling 为准。

潜在扩散（Latent Diffusion）在约 64×64×4 潜在空间而非 512×512×3 像素空间扩散，空间体积约降两个数量级，是端侧可行的前提之一[4]。

## 5 IoT 场景与实践要点

| 场景 | 输入倾向 | 输出 | 模型体量倾向 | 延迟目标倾向 |
|------|---------|------|-------------|-------------|
| 安防增强/超分 | 低分辨率帧 | 更高清帧 | 十余 MB 量级 | 百毫秒–秒级 |
| 农业/低光增强 | 噪声模糊图 | 增强图 | 数–十余 MB | 亚秒–秒级 |
| 合成缺陷数据 | 条件/文本 | 训练样本 | 视基座 | 可离线批跑 |

隐私敏感场景可在本地训/跑扩散，只外发合成样本；仍须评估成员推断与训练数据记忆风险，不能默认「合成=无隐私」。

**选型**：质量优先用约 20–50 步 DDIM/DPM；交互优先用 1–4 步 LCM/Turbo；超分可用较少步确定性求解器。内存：FP16、注意力切片、VAE 分块解码、层间换入换出。

## 6 局限、挑战与可改进方向

### 1. 少步质量与模式崩塌

**局限**：1–4 步生成易丢细节、纹理重复或语义漂移；FID 改善不代表业务指标（检测召回、OCR）同步改善[3]。
**改进**：按任务选步数；用下游任务指标而非只看 FID；关键路径保留 8–20 步回退模式。

### 2. 量化与算子支持碎片化

**局限**：注意力、GroupNorm、时间嵌入在部分 NPU 上回退 CPU，端到端加速远低于纸面 INT8 倍数[9][10]。
**改进**：导出前做算子覆盖审计；不支持的模块保留 FP16；优先厂商已验证的 SD/LCM 参考实现。

### 3. 峰值内存与热节流

**局限**：U-Net + VAE + 文本编码器同时驻留易超移动内存；持续推理触发降频，演示延迟不可持续。
**改进**：分阶段加载；缓存复用；限制并发与分辨率；量产测温升曲线而非单次冷启动。

### 4. 数据与合规

**局限**：端侧用扩散做「隐私增强」仍可能记忆训练个体；开源权重许可与商用场景冲突。
**改进**：训练数据治理与去重；对外合成数据做再识别评估；许可证审查纳入发布清单。

## 参考文献

[1] J. Ho et al., "Denoising Diffusion Probabilistic Models," NeurIPS, 2020.
[2] J. Song et al., "Denoising Diffusion Implicit Models," ICLR, 2021.
[3] S. Luo et al., "Latent Consistency Models: Synthesizing High-Resolution Images with Few-Step Inference," arXiv:2310.04378, 2023.
[4] R. Rombach et al., "High-Resolution Image Synthesis with Latent Diffusion Models," CVPR, 2022.
[5] Y. Li et al., "SnapFusion: Text-to-Image Diffusion Model on Mobile Devices within Two Seconds," NeurIPS, 2024.
[6] X. Ma et al., "DeepCache: Accelerating Diffusion Models for Free," CVPR, 2024.
[7] C. Lu et al., "DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling," NeurIPS, 2022.
[8] T. Castells et al., "EdgeFusion: On-Device Text-to-Image Generation," MobiSys, 2024.
[9] Y. Shang et al., "Post-training Quantization on Diffusion Models," CVPR, 2023.
[10] Y. Chen et al., "Speed Is All You Need: On-Device Acceleration of Large Diffusion Models via GPU-Aware Optimizations," CVPR Workshop, 2024.
[11] A. Sauer et al., "Adversarial Diffusion Distillation," arXiv, 2023.
[12] Hugging Face, "Diffusers Documentation," 持续更新.
