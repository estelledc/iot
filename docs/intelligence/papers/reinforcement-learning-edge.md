---
schema_version: '1.0'
id: reinforcement-learning-edge
title: 强化学习在边缘自适应中的应用
layer: 5
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 强化学习在边缘自适应中的应用

> **难度**：🟡 中级 | **领域**：强化学习、资源管理、IoT 优化 | **阅读时间**：约 20 分钟

## 日常类比

想象你是一个外卖骑手（RL 智能体），每天要在城市里送餐（执行任务）。你不知道最优路线，但每次送达后会收到评价和小费（奖励信号）。经过几百单的尝试，你逐渐学会了：高峰期走小路更快、雨天提前出发、某些商圈午餐时段单量大。你的策略在不断"自适应"环境变化。

边缘设备面临类似问题：网络带宽在变、任务负载在变、电池在消耗、温度在波动。传统的固定规则（如"CPU 超过 80% 就降频"）太死板。强化学习让设备像骑手一样，通过试错学会在动态环境中做出最优决策。

## 1. 为什么边缘需要 RL

### 1.1 边缘资源管理的挑战

| 挑战 | 传统方法 | RL 方法 |
|------|---------|---------|
| 动态负载 | 固定阈值规则 | 学习负载模式，预测性调度 |
| 多目标权衡 | 手动调参 | 自动学习 Pareto 最优 |
| 环境变化 | 需要重新配置 | 在线自适应 |
| 组合爆炸 | 启发式近似 | 端到端策略学习 |
| 延迟约束 | 保守策略 | 学习精确边界 |

### 1.2 典型应用场景

- **计算卸载**：决定哪些任务在本地执行、哪些发送到云端
- **DVFS 调频**：动态调整 CPU/GPU 频率平衡性能和功耗
- **任务调度**：多设备间的任务分配和优先级排序
- **缓存管理**：边缘节点上缓存哪些数据/模型
- **网络资源分配**：带宽、信道、功率的动态分配

## 2. RL 基础算法在边缘的适配

### 2.1 DQN 用于离散决策

```python
import torch
import torch.nn as nn
import numpy as np
from collections import deque
import random

class EdgeDQN(nn.Module):
    """轻量级 DQN，用于边缘任务调度"""
    
    def __init__(self, state_dim, n_actions):
        super().__init__()
        # 极简网络，适合 MCU 部署
        self.network = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, n_actions)
        )
    
    def forward(self, state):
        return self.network(state)

class EdgeSchedulerAgent:
    """边缘任务调度 RL 智能体"""
    
    def __init__(self, state_dim=8, n_actions=4):
        """
        state: [cpu_util, mem_util, queue_len, bandwidth, 
                battery, temperature, time_of_day, task_priority]
        actions: [local_exec, offload_cloud, offload_peer, defer]
        """
        self.q_net = EdgeDQN(state_dim, n_actions)
        self.target_net = EdgeDQN(state_dim, n_actions)
        self.target_net.load_state_dict(self.q_net.state_dict())
        
        self.optimizer = torch.optim.Adam(self.q_net.parameters(), lr=1e-3)
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.gamma = 0.99
        self.batch_size = 32
    
    def select_action(self, state):
        """epsilon-greedy 策略"""
        if random.random() < self.epsilon:
            return random.randint(0, 3)
        
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_net(state_t)
            return q_values.argmax().item()
    
    def train_step(self):
        """从经验回放中学习"""
        if len(self.memory) < self.batch_size:
            return
        
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        
        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)
        
        # 当前 Q 值
        current_q = self.q_net(states).gather(1, actions.unsqueeze(1))
        
        # 目标 Q 值
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + self.gamma * next_q * (1 - dones)
        
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        self.epsilon *= self.epsilon_decay
```

### 2.2 PPO 用于连续控制

```python
class EdgePPO:
    """PPO 用于连续动作空间（如 DVFS 频率调节）"""
    
    def __init__(self, state_dim=6, action_dim=2):
        """
        state: [cpu_util, temperature, task_deadline, power_budget, ...]
        action: [cpu_freq_ratio, gpu_freq_ratio] in [0, 1]
        """
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
        )
        self.actor_mean = nn.Linear(32, action_dim)
        self.actor_std = nn.Parameter(torch.zeros(action_dim))
        
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, 1)
        )
        
        self.clip_epsilon = 0.2
    
    def get_action(self, state):
        """采样动作"""
        features = self.actor(state)
        mean = torch.sigmoid(self.actor_mean(features))  # [0, 1]
        std = torch.exp(self.actor_std).expand_as(mean)
        
        dist = torch.distributions.Normal(mean, std)
        action = dist.sample()
        log_prob = dist.log_prob(action).sum(-1)
        
        return action.clamp(0, 1), log_prob
    
    def compute_reward(self, state, action, next_state):
        """
        多目标奖励函数设计
        平衡性能、功耗、温度
        """
        # 性能奖励：任务完成越快越好
        perf_reward = -next_state["latency"] / state["deadline"]
        
        # 功耗惩罚：超出预算的部分
        power = estimate_power(action["cpu_freq"], action["gpu_freq"])
        power_penalty = -max(0, power - state["power_budget"]) * 10
        
        # 温度惩罚：过热保护
        temp_penalty = -max(0, next_state["temperature"] - 80) * 5
        
        # 综合奖励
        return perf_reward + power_penalty + temp_penalty
```

### 2.3 SAC 用于样本高效学习

SAC (Soft Actor-Critic) 的优势在于样本效率高，适合边缘场景（交互成本高）：

| 算法 | 样本效率 | 稳定性 | 适用动作空间 | 边缘适用性 |
|------|---------|--------|-------------|-----------|
| DQN | 中 | 高 | 离散 | 好（网络小） |
| PPO | 低 | 高 | 连续/离散 | 中（需要多次交互） |
| SAC | 高 | 高 | 连续 | 好（少量交互即可学习） |
| TD3 | 高 | 中 | 连续 | 好 |
| A2C | 低 | 中 | 连续/离散 | 中 |

## 3. 多智能体 RL 用于 IoT 协调

### 3.1 问题建模

多个边缘设备需要协作完成任务，但每个设备只能观察局部信息：

```python
class MultiAgentEdgeEnv:
    """多智能体边缘协调环境"""
    
    def __init__(self, n_devices=5, n_tasks=20):
        self.n_devices = n_devices
        self.n_tasks = n_tasks
        
    def get_observation(self, agent_id):
        """每个设备的局部观察"""
        return {
            "local_state": self.device_states[agent_id],  # 自身状态
            "neighbor_load": self.get_neighbor_loads(agent_id),  # 邻居负载
            "pending_tasks": self.task_queue[agent_id],  # 待处理任务
            "communication_cost": self.get_comm_costs(agent_id)  # 通信开销
        }
    
    def step(self, actions):
        """
        actions: dict of {agent_id: action}
        action: (task_id, target_device) - 将任务分配给哪个设备
        """
        rewards = {}
        for agent_id, action in actions.items():
            task_id, target = action
            
            if target == agent_id:
                # 本地执行
                latency = self.execute_local(agent_id, task_id)
            else:
                # 卸载到其他设备
                comm_delay = self.communicate(agent_id, target, task_id)
                exec_delay = self.execute_local(target, task_id)
                latency = comm_delay + exec_delay
            
            # 奖励：负延迟 + 负载均衡奖励
            rewards[agent_id] = -latency + self.balance_bonus()
        
        return self.get_all_observations(), rewards
```

### 3.2 QMIX 算法简化实现

```python
class QMIXAgent:
    """QMIX: 单调值分解的多智能体 RL"""
    
    def __init__(self, n_agents, state_dim, action_dim):
        # 每个智能体的局部 Q 网络
        self.agent_networks = nn.ModuleList([
            nn.Sequential(
                nn.Linear(state_dim, 32),
                nn.ReLU(),
                nn.Linear(32, action_dim)
            ) for _ in range(n_agents)
        ])
        
        # 混合网络：将局部 Q 值合成全局 Q 值
        # 关键约束：混合权重非负，保证单调性
        self.hyper_w = nn.Sequential(
            nn.Linear(state_dim * n_agents, 32),
            nn.ReLU(),
            nn.Linear(32, n_agents),
            nn.Abs()  # 保证非负
        )
    
    def get_joint_q(self, local_observations, global_state):
        """计算联合 Q 值"""
        local_qs = []
        for i, (obs, net) in enumerate(zip(local_observations, self.agent_networks)):
            q = net(obs).max(dim=-1).values  # 每个智能体的最优 Q
            local_qs.append(q)
        
        local_qs = torch.stack(local_qs, dim=-1)  # [batch, n_agents]
        
        # 混合
        weights = self.hyper_w(global_state)  # [batch, n_agents], 非负
        joint_q = (local_qs * weights).sum(dim=-1)
        
        return joint_q
```

## 4. Sim-to-Real 迁移

### 4.1 为什么需要仿真

在真实边缘设备上训练 RL 的问题：

- 训练需要数万次交互，真实设备太慢
- 探索阶段可能导致设备过热/崩溃
- 难以重置环境状态

### 4.2 域随机化 (Domain Randomization)

```python
class EdgeSimulator:
    """带域随机化的边缘设备仿真器"""
    
    def __init__(self):
        # 基础参数
        self.base_cpu_speed = 1.5e9  # 1.5 GHz
        self.base_memory = 4e9  # 4 GB
        
    def randomize(self):
        """每个 episode 随机化环境参数"""
        self.cpu_speed = self.base_cpu_speed * np.random.uniform(0.8, 1.2)
        self.memory = self.base_memory * np.random.uniform(0.7, 1.0)
        self.network_bandwidth = np.random.uniform(1e6, 100e6)  # 1-100 Mbps
        self.ambient_temp = np.random.uniform(15, 40)  # 环境温度
        self.task_arrival_rate = np.random.exponential(0.1)  # 泊松到达
        
        # 噪声注入
        self.sensor_noise_std = np.random.uniform(0.01, 0.1)
    
    def step(self, action):
        """仿真一步，加入随机噪声"""
        # 执行动作
        true_state = self._compute_next_state(action)
        
        # 观察噪声（模拟真实传感器不精确）
        observed_state = true_state + np.random.normal(
            0, self.sensor_noise_std, size=true_state.shape
        )
        
        return observed_state, self._compute_reward(true_state)
```

### 4.3 迁移效果

| 训练方式 | 仿真性能 | 真实设备性能 | 迁移差距 |
|----------|---------|-------------|---------|
| 无随机化 | 95% | 62% | 33% |
| 轻度随机化 | 92% | 78% | 14% |
| 强域随机化 | 88% | 83% | 5% |
| 仿真+少量真实微调 | 90% | 89% | 1% |

## 5. 奖励函数设计

### 5.1 IoT 场景的多目标奖励

```python
def iot_reward_function(state, action, next_state, config):
    """
    IoT 边缘场景的多目标奖励函数
    需要平衡：延迟、功耗、可靠性、公平性
    """
    # 1. 延迟奖励（越低越好）
    latency = next_state["task_completion_time"]
    deadline = state["task_deadline"]
    if latency <= deadline:
        latency_reward = 1.0 - latency / deadline  # [0, 1]
    else:
        latency_reward = -2.0 * (latency - deadline) / deadline  # 超时重罚
    
    # 2. 功耗奖励
    power = next_state["power_consumption"]
    power_budget = config["power_budget"]
    power_reward = 1.0 - power / power_budget
    
    # 3. 可靠性奖励（任务成功率）
    reliability_reward = 1.0 if next_state["task_success"] else -1.0
    
    # 4. 公平性奖励（Jain's fairness index）
    loads = next_state["device_loads"]
    jain_index = (sum(loads)**2) / (len(loads) * sum(x**2 for x in loads))
    fairness_reward = jain_index  # [0, 1]
    
    # 加权组合
    total_reward = (
        config["w_latency"] * latency_reward +
        config["w_power"] * power_reward +
        config["w_reliability"] * reliability_reward +
        config["w_fairness"] * fairness_reward
    )
    
    return total_reward

# 典型权重配置
reward_config = {
    "w_latency": 0.4,      # 延迟最重要
    "w_power": 0.2,        # 功耗次之
    "w_reliability": 0.3,  # 可靠性很重要
    "w_fairness": 0.1,     # 公平性辅助
    "power_budget": 5.0    # 5W 功耗预算
}
```

## 6. 轻量级 RL 在 MCU 上的部署

### 6.1 模型压缩

```c
// STM32 上的极简 DQN 推理 (C 语言)
// 网络结构: 8 -> 32 -> 16 -> 4
// 总参数: 8*32 + 32 + 32*16 + 16 + 16*4 + 4 = 868 参数
// 内存占用: 868 * 4 = 3.5 KB (FP32) 或 868 bytes (INT8)

#include <stdint.h>

#define STATE_DIM 8
#define HIDDEN1 32
#define HIDDEN2 16
#define ACTION_DIM 4

// 量化权重 (INT8)
static const int8_t w1[STATE_DIM][HIDDEN1] = { /* ... */ };
static const int8_t w2[HIDDEN1][HIDDEN2] = { /* ... */ };
static const int8_t w3[HIDDEN2][ACTION_DIM] = { /* ... */ };
static const int8_t b1[HIDDEN1] = { /* ... */ };
static const int8_t b2[HIDDEN2] = { /* ... */ };
static const int8_t b3[ACTION_DIM] = { /* ... */ };

static float scale1 = 0.015f, scale2 = 0.012f, scale3 = 0.018f;

int select_action(const float state[STATE_DIM]) {
    float h1[HIDDEN1], h2[HIDDEN2], q[ACTION_DIM];
    
    // Layer 1: state -> hidden1 (ReLU)
    for (int j = 0; j < HIDDEN1; j++) {
        float sum = b1[j] * scale1;
        for (int i = 0; i < STATE_DIM; i++) {
            sum += state[i] * w1[i][j] * scale1;
        }
        h1[j] = sum > 0 ? sum : 0;  // ReLU
    }
    
    // Layer 2: hidden1 -> hidden2 (ReLU)
    for (int j = 0; j < HIDDEN2; j++) {
        float sum = b2[j] * scale2;
        for (int i = 0; i < HIDDEN1; i++) {
            sum += h1[i] * w2[i][j] * scale2;
        }
        h2[j] = sum > 0 ? sum : 0;
    }
    
    // Layer 3: hidden2 -> Q values
    int best_action = 0;
    float best_q = -1e9f;
    for (int j = 0; j < ACTION_DIM; j++) {
        float sum = b3[j] * scale3;
        for (int i = 0; i < HIDDEN2; i++) {
            sum += h2[i] * w3[i][j] * scale3;
        }
        q[j] = sum;
        if (sum > best_q) {
            best_q = sum;
            best_action = j;
        }
    }
    
    return best_action;
}

// 推理时间: ~0.05 ms on STM32H7 @ 480MHz
// 内存占用: < 4 KB
```

### 6.2 在线学习 vs 离线学习

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 离线训练+部署 | 稳定、可控 | 不能适应新环境 | 环境变化小 |
| 在线学习 | 持续适应 | 不稳定、需要探索 | 环境动态变化 |
| 离线预训练+在线微调 | 兼顾两者 | 实现复杂 | 推荐方案 |

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 OpenAI Gym 的 CartPole 学习 DQN 基础
2. **第二步**：自定义一个简单的边缘调度环境（3 个设备，5 种任务）
3. **第三步**：实现 DQN 智能体，对比随机策略和贪心策略
4. **第四步**：尝试 PPO 处理连续动作（如频率调节）
5. **第五步**：将训练好的策略网络导出为 C 代码，部署到 MCU

### 7.2 具体调优建议

- **状态设计**：包含足够信息但不要太多维度——8-16 维通常够用
- **奖励塑形**：避免稀疏奖励，每步都给中间反馈（如"接近目标"的奖励）
- **探索策略**：初期 epsilon=1.0 充分探索，后期衰减到 0.01
- **经验回放**：优先经验回放（PER）在样本少时效果显著
- **目标网络**：更新频率不要太高（每 100-1000 步同步一次）

### 7.3 HVAC/交通控制应用

```
HVAC 智能控制:
- 状态: [室温, 室外温, 湿度, 人数, 时间, 电价]
- 动作: [设定温度, 风速, 模式]
- 奖励: 舒适度 - 能耗成本
- 效果: 比固定规则节能 15-25%

交通信号控制:
- 状态: [各方向车流量, 等待时间, 时段]
- 动作: [绿灯时长分配]
- 奖励: -总等待时间 - 排队长度
- 效果: 比固定配时减少等待 20-30%
```

## 参考文献

1. Mnih, V. et al. "Human-level control through deep reinforcement learning." Nature 2015.
2. Schulman, J. et al. "Proximal Policy Optimization Algorithms." arXiv 2017.
3. Haarnoja, T. et al. "Soft Actor-Critic: Off-Policy Maximum Entropy Deep RL." ICML 2018.
4. Rashid, T. et al. "QMIX: Monotonic Value Function Factorisation for Deep Multi-Agent RL." ICML 2018.
5. Mao, H. et al. "Resource Management with Deep Reinforcement Learning." HotNets 2016.
6. Zhang, C. et al. "Deep Reinforcement Learning for IoT Network Dynamic Clustering." IEEE IoT Journal 2023.
7. Tobin, J. et al. "Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World." IROS 2017.
8. Wei, T. et al. "Deep Reinforcement Learning for Building HVAC Control." DAC 2017.
9. Liang, E. et al. "RLlib: Abstractions for Distributed Reinforcement Learning." ICML 2018.
10. Chen, X. et al. "Deep Reinforcement Learning for Internet of Things: A Comprehensive Survey." IEEE CST 2024.
