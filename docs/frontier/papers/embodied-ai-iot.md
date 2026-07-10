---
schema_version: '1.0'
id: embodied-ai-iot
title: 具身智能（Embodied AI）与 IoT
layer: 8
content_type: technical_analysis
difficulty: intermediate
reading_time: 28
prerequisites:
  - warehouse-robot-coordination
  - multimodal-edge-perception
  - reinforcement-learning-edge
tags:
- 具身智能
- Embodied AI
- Sim-to-Real
- 视觉语言动作
- 边缘推理
- 扩散策略
- 机器人
- 感知行动闭环
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 具身智能（Embodied AI）与 IoT

> **难度**：🟡 中级 | **领域**：具身智能 × 边缘计算 × 机器人 | **阅读时间**：约 28 分钟

## 日常类比

学骑自行车不能只看说明书——要亲自上车感受平衡（传感器），判断倾斜（决策），操控车把脚踏（执行器）。摔几次后，大脑与身体形成"骑车模型"。

具身智能（Embodied AI）同理：AI 不能只做云端文本大脑，必须有"身体"与真实世界交互。传统物联网（Internet of Things, IoT）更像只能看的摄像头；具身 IoT 像能看又能锁门的保安——感知、决策、行动闭环。

## 一句话总结

具身智能通过传感器感知、模型决策与执行器作用形成物理闭环，推动 IoT 从"数据采集器"走向"可在非结构化环境中执行任务的物理智能体"。

## 1. 什么是具身智能？

### 1.1 定义与核心循环

核心是**感知-决策-行动循环（Perception-Decision-Action Loop）**：

```
┌──────────────────────────────────────────┐
│              物理环境                      │
│   ┌──────┐    感知     ┌──────────┐      │
│   │传感器│──────────→ │  AI 大脑  │      │
│   │(眼/耳)│           │(边缘/云端)│      │
│   └──────┘    ←────── └──────────┘      │
│               行动     ┌──────────┐      │
│               ────────→│ 执行器   │      │
│                        │(手/脚/轮) │      │
│                        └──────────┘      │
└──────────────────────────────────────────┘
```

控制频率常需十到数十 Hz 以上；人类视觉-运动反应约数百毫秒量级，机器人在动态环境中往往需要更紧的端到端预算，因此云端往返很难承担底层控制。

### 1.2 具身智能 vs 传统 AI vs 传统机器人

| 维度 | 传统 AI（大语言模型等） | 传统工业机器人 | 具身智能 |
|------|----------------------|--------------|---------|
| 物理交互 | 无 | 有但固定 | 有且更灵活 |
| 环境理解 | 数字/文本空间 | 预编程单元 | 动态感知与推理 |
| 适应能力 | 文本域强 | 弱 | 物理域持续学习/适应 |
| 学习方式 | 大规模数据预训练 | 示教/编程 | 仿真 + 真实交互 |
| 延迟 | 秒级常可接受 | 毫秒级固定周期 | 毫秒–数十毫秒动态 |
| 代表方向 | GPT 类助手 | 焊接/搬运臂 | VLA 机器人、人形等 |

### 1.3 为什么近年加速？

- **基础模型**：视觉-语言模型（Vision-Language Model, VLM）提供更强语义先验
- **仿真**：Isaac Sim、MuJoCo 等提升并行与保真度
- **边缘算力**：Jetson 等平台使板载推理更可行（具体 TOPS/功耗以器件手册为准）

## 2. 基础模型驱动的机器人

### 2.1 RT-2：从语言到动作

Google DeepMind 的 RT-2（Robotics Transformer 2）将 VLM 微调为机器人策略：图像 + 语言指令 → 动作 token/轨迹。关键叙事是**涌现泛化**——组合未见指令的能力；实际成功率强烈依赖机器人本体、场景与评估协议，不宜跨论文直接比绝对百分比。

```
输入：摄像头图像 + 自然语言指令
     "把那个空瓶子扔进垃圾桶"
       ↓
RT-2 类 VLA 模型
       ↓
输出：动作序列 / 末端位姿与夹爪命令
```

### 2.2 PaLM-E：多模态具身语言模型

PaLM-E 将图像、其他传感与文本映射到统一 token 空间，由大 Transformer 联合推理，再解码为语言或动作：

```python
# PaLM-E 的核心思想（简化伪代码）
def palm_e_forward(image, lidar_points, language_instruction):
    img_tokens = vision_encoder(image)
    lidar_tokens = pointcloud_encoder(lidar_points)
    text_tokens = text_tokenizer(language_instruction)
    combined = concat([img_tokens, lidar_tokens, text_tokens])
    output = palm_transformer(combined)
    actions = action_decoder(output)
    return actions
```

### 2.3 模型对比（公开报告量级，评估集不同）

| 模型 | 参数量级 | 泛化叙事 | 推理延迟倾向 | 部署倾向 |
|------|---------|---------|-------------|---------|
| RT-1 | 较小 | 有限 | 较低 | 更易边缘 |
| RT-2 / RT-2-X | 很大 | 较强/跨本体 | 较高 | 常云端或强边缘 |
| Octo | ~1e8 量级 | 中等通用 | 较低 | 边缘友好 |
| OpenVLA | ~7B 量级 | 较强开源 VLA | 中 | 边缘/近边缘 |
| PaLM-E | 极大 | 很强多模态 | 高 | 云端研究向 |

选择模型时优先对齐：**控制频率、板载算力、是否需要开放词汇指令**。

## 3. 仿真到真实（Sim-to-Real）迁移

### 3.1 为什么需要仿真？

真实试错贵、慢、有安全风险。仿真可并行与加速，但存在现实差距（Reality Gap）。

### 3.2 域随机化（Domain Randomization）机制

在仿真中随机化视觉（光照、纹理、相机噪声）与物理（摩擦、质量、延迟），迫使策略学习对扰动鲁棒的特征，而非记忆单一仿真纹理：

```python
domain_randomization_config = {
    "lighting": {"intensity": (0.3, 1.5), "color_temp": (3000, 8000)},
    "camera": {"fov": (55, 75), "noise_std": (0, 0.02)},
    "texture": {"randomize": True, "style_transfer": True},
    "friction": {"range": (0.3, 1.2)},
    "mass": {"scale_factor": (0.8, 1.2)},
    "actuator_delay": {"range_ms": (0, 20)},
    "sensor_noise": {"imu_gyro_std": 0.01, "force_torque_std": 0.5},
    "object_position": {"xy_range_cm": (-5, 5)},
    "distractor_objects": {"count": (0, 10)},
}
```

过度随机化会导致策略过于保守；宜从窄范围扩到宽，并以仿真成功率门禁决定是否实机。

### 3.3 Sim-to-Real 案例对比（公开数字，任务各异）

| 任务 | 训练资源叙事 | 真实成功率叙事 | 方法要点 |
|------|-------------|----------------|---------|
| 灵巧手魔方（OpenAI） | 极大规模仿真 | 中等成功区间 | 大规模域随机化 |
| 四足行走（学术） | 相对较少 GPU 时 | 较高 | 教师-学生等 |
| 双臂操作（近年） | 中等 GPU 时 | 中高 | 扩散策略 + DR |
| 人形平衡/行走 | 中高 | 场景依赖 | RL + 课程学习 |

## 4. 传感器-执行器集成

### 4.1 多模态融合

```
视觉 (RGB/RGB-D)：识别、分割、深度
触觉 (GelSight 等)：接触、滑动、材质
惯性 (IMU)：姿态、碰撞线索
力/力矩 (F/T)：交互力、阻抗、安全
本体感觉（编码器）：关节角/速/矩
```

融合可在特征级（拼接进策略）或估计级（状态估计后再控制）；触觉对接触丰富任务往往比对纯视觉更关键。

### 4.2 带宽与延迟预算（量级）

| 传感器类型 | 典型配置 | 原始数据率量级 | 处理后 |
|-----------|---------|---------------|--------|
| RGB | VGA@30fps | 十余 MB/s | 压缩后显著降低 |
| 深度 | VGA@30fps | 十余 MB/s | 仍较高 |
| LiDAR | 多线@10–20Hz | 十余 MB/s | 视点云裁剪 |
| 触觉阵列 | 百 Hz 量级 | KB/s 级 | 低 |
| IMU/编码器 | kHz 级 | KB/s 级 | 低 |

合计可达数十 MB/s 量级原始流；策略若要求端到端数十毫秒，必须边缘侧完成感知主干，云端只做慢速任务规划。

## 5. 操作技能学习

### 5.1 三种范式

| 范式 | 机制 | 优点 | 局限 |
|------|------|------|------|
| 模仿学习 | 从示范学策略 | 样本相对高效 | 难超越示范、分布外脆 |
| 强化学习 | 试错最大化回报 | 可发现新策略 | 样本贵、奖励难设计 |
| 扩散策略 | 对动作序列去噪生成 | 擅多模态动作分布 | 推理步数与延迟需折中 |

### 5.2 扩散策略示例

```python
import torch
import torch.nn as nn

class DiffusionPolicy(nn.Module):
    """简化的扩散策略模型"""
    def __init__(self, obs_dim=512, action_dim=7, horizon=16):
        super().__init__()
        self.horizon = horizon
        self.noise_pred_net = nn.Sequential(
            nn.Linear(obs_dim + action_dim * horizon + 1, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, action_dim * horizon),
        )
    
    def predict_action(self, obs, num_steps=20):
        action = torch.randn(1, self.horizon * 7)
        for t in reversed(range(num_steps)):
            t_embed = torch.tensor([t / num_steps])
            noise_pred = self.noise_pred_net(
                torch.cat([obs, action, t_embed], dim=-1)
            )
            action = action - 0.05 * noise_pred + 0.02 * torch.randn_like(action)
        return action.reshape(self.horizon, 7)
```

## 6. 非结构化环境中的导航

### 6.1 结构化 vs 非结构化

| 特征 | 结构化（工厂） | 非结构化（家庭/户外） |
|------|--------------|---------------------|
| 地面/障碍 | 较可控 | 动态未知 |
| 光照/语义 | 稳定、简单 | 多变、复杂 |
| 方法 | 预定义路径/二维码 | 实时规划 + 语义 |

### 6.2 语义导航机制

"去客厅拿茶几上的遥控器"需要：语言接地 → 空间语义图 → 运动规划 → 闭环避障与操作。SayCan 等把大语言模型（LLM）的高层计划与可执行技能（affordance）对接；低层仍靠局部控制器保证安全。

### 6.3 端到端 vs 模块化

| 方案 | 优点 | 缺点 | 代表方向 |
|------|------|------|---------|
| 模块化（感知+规划+控制） | 可解释、可测 | 误差累积 | SLAM + 采样规划 |
| 端到端 | 联合优化 | 黑盒、难认证 | ViNT 等 |
| 混合 | 折中 | 接口复杂 | LLM 规划 + 低层 RL |

## 7. 边缘计算与实时控制

### 7.1 延迟预算（示意）

```
总预算示例：≤ 50ms（约 20Hz）
├── 传感与预处理：数–十余 ms
├── 传输到计算单元：1–数 ms
├── AI 推理：十余–二十余 ms（常为瓶颈）
├── 规划平滑：数 ms
├── 执行器：数–十余 ms
└── 安全余量：数–十余 ms
```

云端 RTT 常达数十到数百毫秒，不能承担紧耦合伺服；云适合慢速重规划与大模型技能选择。

### 7.2 边缘平台对比（标称算力/功耗，以厂商为准）

| 平台 | 算力量级 | 功耗量级 | 适用倾向 |
|------|---------|---------|---------|
| Jetson Orin NX 类 | 高 | 十余–数十 W | 服务机器人 |
| Jetson AGX Orin 类 | 更高 | 更高 | 自动驾驶/人形研发 |
| 高通 RB 类 | 中 | 较低 | 无人机等 |
| Coral 等 | 低 | 很低 | 小型感知 |
| Hailo 等加速卡 | 中低 | 很低 | 低功耗视觉 |

### 7.3 云-边-端协同

```
云端：大模型、仿真训练、多机全局（100–500ms 可容忍）
边缘：中等 VLA/感知、局部规划（10–50ms）
端侧 MCU：关节伺服、急停（<1ms 级）
```

## 8. 与传统工业机器人对比

| 能力 | 传统工业机器人 | 具身智能机器人 |
|------|---------------|---------------|
| 已知物体重复作业 | 极高（编程） | 高但通常低于产线六西格玛要求 |
| 未知物体/开放指令 | 弱 | 相对强 |
| 环境变化 | 常需重编程 | 更好适应（仍不完美） |
| 部署技能门槛 | 集成专家 | 示范/微调降低部分门槛 |
| 安全认证 | ISO 等成熟 | 仍在发展，NN 难形式化保证 |

## 9. 局限、挑战与可改进方向

### 1. 可靠性未达工业六西格玛

**局限**：实验室 80–95% 成功率在日均数万次操作下仍意味着大量故障。
**改进**：技能级监控与失败检测；失败自动重试/人工接管；先部署可回滚的半自动工位。

### 2. 长期运行漂移与错误累积

**局限**：数小时后状态估计、夹具磨损与分布漂移导致性能下降。
**改进**：在线标定；周期性回巢校准；检测分布外输入并降级到安全策略。

### 3. 安全不可形式化

**局限**：神经网络策略难以提供传统工业机器人那类可证明安全包络。
**改进**：低层力/速度硬限制与安全 PLC；AI 只输出受限集合内的设定点；人机协作区用标准传感器联锁。

### 4. Sim-to-Real 与数据成本

**局限**：现实差距与真实示范收集昂贵，开放世界泛化仍脆。
**改进**：系统化域随机化 + 实机微调；共享开源轨迹集；优先约束工作空间再谈通用人形。

### 5. 边缘算力与大 VLA 矛盾

**局限**：55B 级云模型无法满足数十毫秒控制；蒸馏后又损泛化。
**改进**：云边分层（慢计划/快控制）；Octo/OpenVLA 级板载；张量 RT/量化与动作分块缓存。

## 10. 实践建议

### 10.1 入门路径

1. Isaac Sim/MuJoCo 跑通抓取闭环
2. robomimic 等做行为克隆
3. 有臂则做小范围 Sim-to-Real；无臂则用 Octo/OpenVLA 微调公开数据
4. 再引入扩散策略与力控安全层

### 10.2 调优要点

- 域随机化由窄到宽，仿真成功率过低不要急着上实机
- 资源紧选较小通用策略；需要开放词汇再上 7B 级 VLA
- 精细接触任务优先加触觉
- 永远保留非学习的急停与力限幅

## 参考文献

[1] A. Brohan et al., "RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control," CoRL, 2023.
[2] D. Driess et al., "PaLM-E: An Embodied Multimodal Language Model," ICML, 2023.
[3] T. Z. Zhao et al., "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion," International Journal of Robotics Research, 2024.
[4] Octo Model Team, "Octo: An Open-Source Generalist Robot Policy," RSS, 2024.
[5] M. J. Kim et al., "OpenVLA: An Open-Source Vision-Language-Action Model," arXiv:2406.09246, 2024.
[6] J. Tobin et al., "Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World," IROS, 2017.
[7] S. Shah et al., "ViNT: A Foundation Model for Visual Navigation," CoRL, 2023.
[8] M. Ahn et al., "Do As I Can, Not As I Say: Grounding Language in Robotic Affordances (SayCan)," arXiv:2204.01691, 2022.
[9] A. Brohan et al., "RT-1: Robotics Transformer for Real-World Control at Scale," arXiv:2212.06817, 2022.
[10] E. Todorov, T. Erez, and Y. Tassa, "MuJoCo: A Physics Engine for Model-Based Control," IROS, 2012.
[11] O. M. Andrychowicz et al., "Learning Dexterous In-Hand Manipulation," International Journal of Robotics Research, 2020.
[12] C. Chi et al., "Diffusion Policy: Visuomotor Policy Learning via Action Diffusion," RSS, 2023.
