# 智慧城市交通信号优化

> **难度**：🟡 中级 | **领域**：智慧城市、交通工程 | **阅读时间**：约 25 分钟

## 摘要

你在早高峰等红灯时一定有过这种体验：明明你这个方向排了几百米的车，对面方向一辆车都没有，但绿灯偏偏亮在对面。传统的固定配时信号灯就像一个"闭眼指挥交通的警察"——它不知道路上有多少车，只是按预设的时间表机械地切换红绿灯。自适应交通信号控制（Adaptive Traffic Signal Control, ATSC）的目标是让信号灯"睁开眼睛"——通过传感器实时感知车流量，用算法动态调整绿灯时长，使整个路网的车辆延误最小化。本文系统介绍车辆检测技术、经典自适应控制系统（SCATS/SCOOT）、强化学习新方法、绿波协调、特殊车辆优先、仿真工具及实际部署效果。

## 日常类比

把一个十字路口想象成一个餐厅的传菜口。厨房（各方向来车）不断出菜，传菜口（绿灯）每次只能让一个方向通过。固定配时就像"每个方向固定传 30 秒"——不管某个方向有没有菜要传。自适应信号就像一个聪明的传菜主管，他会看哪个方向的菜已经堆了很多，就多给那个方向一点时间。

更进一步，如果整条街上有 10 个餐厅（10 个路口），一个好的协调系统（绿波）会让传菜节奏衔接上——你在第一个路口刚通过绿灯，到第二个路口时绿灯也刚好亮了。这就是"绿波带"的概念——让驾驶员在一条干道上以特定速度行驶时，能连续通过多个绿灯。

但现实比餐厅复杂得多：路口不是单向的而是四方向交叉，"传菜"有左转、直行、右转三种方式，还有行人、公交车、救护车等"VIP 菜品"需要优先处理。

## 1 车辆检测技术

### 1.1 检测方式对比

| 检测技术 | 精度 | 检测能力 | 安装成本 | 维护成本 | 适用场景 |
|----------|------|----------|----------|----------|----------|
| 感应线圈 | 95-99% | 存在/计数 | ¥3,000-5,000/车道 | 高（需开挖路面） | 传统路口改造 |
| 视频检测 | 90-97% | 计数/速度/分类/轨迹 | ¥8,000-20,000/路口 | 中 | 多车道、需要车型分类 |
| 微波雷达 | 93-98% | 存在/速度/计数 | ¥5,000-12,000/路口 | 低 | 恶劣天气（雨雪雾） |
| 激光雷达 | 97-99% | 高精度 3D 检测 | ¥20,000-80,000 | 中 | 高精度、多目标跟踪 |
| 地磁传感器 | 90-95% | 存在/计数 | ¥1,000-3,000/车道 | 低 | 低成本改造 |
| V2I 通信 | 100%(联网车) | 位置/速度/意图 | 高（基础设施） | 中 | 网联车环境（未来） |

### 1.2 视频检测的 AI 进化

传统视频检测使用"虚拟线圈"——在视频画面上画一条线，车辆越过这条线时计数。精度受光照变化、阴影、雨滴等影响大。

2024 年的主流方案是基于深度学习的目标检测 + 跟踪：

```python
# 基于 YOLOv8 的交通流视频检测示例
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt')  # nano 模型，边缘设备可跑

# 车辆类别: car=2, motorcycle=3, bus=5, truck=7
VEHICLE_CLASSES = {2, 3, 5, 7}

def count_vehicles_crossing_line(video_path, line_y=400):
    """统计越过检测线的车辆数"""
    cap = cv2.VideoCapture(video_path)
    trackers = {}  # id -> last_y
    total_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model.track(frame, persist=True, 
                              classes=list(VEHICLE_CLASSES),
                              conf=0.5, verbose=False)
        
        if results[0].boxes.id is not None:
            ids = results[0].boxes.id.int().cpu().tolist()
            boxes = results[0].boxes.xyxy.cpu().numpy()
            
            for track_id, box in zip(ids, boxes):
                center_y = (box[1] + box[3]) / 2
                
                if track_id in trackers:
                    # 检测是否越过检测线（从上到下）
                    if trackers[track_id] < line_y <= center_y:
                        total_count += 1
                
                trackers[track_id] = center_y
    
    return total_count
```

基于 YOLOv8 的方案在标准交通视频数据集上的检测精度达到 mAP@0.5 = 92.3%，在 NVIDIA Jetson Orin Nano 上可以处理 4 路 1080p 视频（每路 30fps）。

### 1.3 V2I（车对基础设施）通信

V2I 是未来方向——车辆通过 C-V2X 或 DSRC 直接告诉信号灯自己的位置、速度和行驶意图。这比任何传感器都精确，但目前渗透率太低（2024 年全球新车 V2X 装配率约 5-8%），短期内只能作为辅助信息源。

## 2 经典自适应控制系统

### 2.1 SCATS（悉尼协调自适应交通系统）

SCATS 由澳大利亚新南威尔士交通局于 1979 年开发，目前在全球 180+ 个城市部署，控制 45,000+ 个路口。

核心思路是"自下而上"——每个路口独立根据感应线圈的车辆到达数据，从预设的信号配时方案库中选择最优方案。路口之间通过区域协调器实现绿波联动。

SCATS 的控制层次：

```
中央系统（全市监控+统计）
    ↓
区域协调器（协调 5-10 个路口的绿波）
    ↓
路口控制器（选择本路口最优配时方案）
    ↓
感应线圈/视频检测器（车辆数据采集）
```

### 2.2 SCOOT（分段偏移优化技术）

SCOOT 由英国 TRL 研发，与 SCATS 的"选方案"思路不同，SCOOT 采用"微调"策略——每个信号周期都在当前方案基础上做小幅调整（绿灯加减几秒），逐步逼近最优。

SCOOT 的三个优化器每个周期独立运行：周期优化器（Cycle Optimizer）调整信号周期总长度；绿信比优化器（Split Optimizer）调整各相位的绿灯占比；相位差优化器（Offset Optimizer）调整相邻路口的绿灯启始时刻，实现绿波。

### 2.3 SCATS vs SCOOT 对比

| 维度 | SCATS | SCOOT |
|------|-------|-------|
| 优化方式 | 方案选择（从库中选） | 微调（在线增量优化） |
| 检测器需求 | 停车线前 40m 处 | 上游进口 + 每条链路 |
| 通信需求 | 低（定时上传） | 高（实时传输） |
| 适应速度 | 5 分钟级 | 秒级 |
| 部署城市 | 悉尼、上海、深圳等 | 伦敦、北京、曼谷等 |
| 典型延误降低 | 15-25% | 12-20% |

## 3 强化学习方法

### 3.1 为什么用强化学习？

SCATS/SCOOT 的局限在于：方案库/调整规则是人工设计的，难以应对极端交通模式；路口之间的协调依赖启发式规则，不是真正的全局最优。

强化学习（RL）把信号灯控制建模为马尔可夫决策过程（MDP），让智能体通过与环境交互学习最优策略，无需人工设计规则。

```python
# 简化的交通信号 RL 环境定义
import gymnasium as gym
import numpy as np

class TrafficSignalEnv(gym.Env):
    """单路口交通信号强化学习环境"""
    
    def __init__(self, intersection_config):
        super().__init__()
        self.n_phases = 4  # 4 个信号相位
        # 状态空间: 每个进口道的排队长度 + 当前相位 + 已持续时间
        self.observation_space = gym.spaces.Box(
            low=0, high=100, shape=(8 + self.n_phases + 1,)
        )
        # 动作空间: 保持当前相位 or 切换到下一相位
        self.action_space = gym.spaces.Discrete(2)
        
    def _get_state(self):
        """获取当前交通状态"""
        queue_lengths = self._get_queue_lengths()  # 8个方向排队数
        phase_onehot = np.zeros(self.n_phases)
        phase_onehot[self.current_phase] = 1
        elapsed = np.array([self.phase_elapsed / self.max_green])
        return np.concatenate([queue_lengths, phase_onehot, elapsed])
    
    def _compute_reward(self):
        """奖励函数: 负的总排队长度 + 吞吐量"""
        total_queue = sum(self._get_queue_lengths())
        throughput = self._get_throughput()
        # 惩罚长排队，奖励高吞吐
        return -0.5 * total_queue + 1.0 * throughput
    
    def step(self, action):
        """执行动作并返回新状态"""
        if action == 1:  # 切换相位
            self.current_phase = (self.current_phase + 1) % self.n_phases
            self.phase_elapsed = 0
        else:
            self.phase_elapsed += 1
        
        self._simulate_traffic(steps=5)  # 模拟 5 秒交通
        
        state = self._get_state()
        reward = self._compute_reward()
        done = self.sim_time >= self.max_sim_time
        
        return state, reward, done, False, {}
```

### 3.2 多智能体协调

单路口 RL 相对简单，真正的挑战在于多路口协调——一个城市可能有几千个信号灯路口，它们之间存在强耦合（上游放行的车辆会影响下游的到达）。

主流方法包括：独立 DQN（每个路口独立训练，简单但忽略协调）、集中式训练分散式执行 CTDE（如 QMIX, MAPPO）、图注意力网络（GAT）建模路口间空间关系。

2024 年的 SOTA 结果显示，基于 MAPPO + GAT 的多智能体 RL 在杭州 16 路口路网上相比 SCATS 降低了 22% 的平均车辆延误、18% 的排队长度。

### 3.3 Sim-to-Real 挑战

RL 模型通常在仿真器（SUMO）中训练，但部署到真实路口时性能会下降（sim-to-real gap），原因在于仿真器的车辆跟驰模型与真实驾驶行为有差异、仿真中的检测器数据无噪声，真实中有误检和漏检、仿真不含行人和非机动车的干扰。

解决方案包括域随机化（Domain Randomization，在训练时随机扰动仿真参数）和在线微调（先在仿真中预训练，再用真实数据 fine-tune）。

## 4 绿波协调

### 4.1 绿波带原理

"绿波"是让一条干道上的信号灯协调配合，使以特定速度行驶的车辆在每个路口都遇到绿灯。实现绿波的关键参数是"相位差"（offset）——相邻路口绿灯启动时刻的差值。

```
路口1: ████████░░░░░░░░  (绿灯 0-8s)
        |----→ 车辆行驶时间 3s
路口2: ░░░████████░░░░░  (绿灯 3-11s, offset=3s)
        |----→ 车辆行驶时间 4s
路口3: ░░░░░░░████████░  (绿灯 7-15s, offset=7s)

时间 →

offset = 路口间距 / 设计车速
```

### 4.2 双向绿波的困难

单向绿波相对容易，但双向绿波（两个方向同时享受绿波）非常困难——除非路口间距恰好是"半周期×车速"的整数倍。实际中常用的折中方案是：主方向（如进城方向早高峰）全程绿波，反方向部分绿波。

MAXBAND 和 MULTIBAND 是求解绿波带宽最大化问题的经典算法，本质是一个混合整数线性规划问题（MILP）。

## 5 特殊场景处理

### 5.1 公交优先

公交优先信号（Transit Signal Priority, TSP）的策略是：当公交车接近路口时，提前给绿灯或延长绿灯。

实现方式包括被动优先（公交车到达时如果是绿灯就延长）、主动优先（提前检测公交车接近，调整相位提前给绿灯）、有条件优先（只有当公交车晚点时才给优先，准时或早到的不给）。

### 5.2 紧急车辆抢先

救护车、消防车等紧急车辆需要"绿色通道"——一路绿灯。实现方式是紧急车辆装载 V2I 设备或 GPS 定位，当系统检测到紧急车辆接近时，提前清空冲突方向的车辆（给冲突方向红灯），为紧急车辆开辟通路。纽约市的 EMCS 系统可以将救护车的平均到达时间缩短 15-20%。

### 5.3 行人过街

传统的行人过街是固定时间，2024 年的趋势是"自适应行人信号"——通过视频检测行人数量和等待时间，动态调整行人绿灯时长。老年人和残疾人过街速度慢，可以通过检测到轮椅或拐杖自动延长绿灯。

## 6 仿真与评估

### 6.1 SUMO 交通仿真

SUMO（Simulation of Urban Mobility）是最广泛使用的开源交通仿真器，支持微观交通仿真（单车级别）。

```python
# 使用 SUMO + TraCI API 控制信号灯
import traci

def run_adaptive_signal(sumo_config, duration=3600):
    """运行自适应信号控制仿真"""
    traci.start(["sumo", "-c", sumo_config, 
                 "--no-step-log", "--no-warnings"])
    
    step = 0
    while step < duration:
        traci.simulationStep()
        
        # 获取各进口道排队车辆数
        tl_id = "intersection_0"
        n_waiting = {}
        for lane in traci.trafficlight.getControlledLanes(tl_id):
            n_waiting[lane] = traci.lane.getLastStepHaltingNumber(lane)
        
        # 简单的自适应逻辑: 排队最长方向延长绿灯
        current_phase = traci.trafficlight.getPhase(tl_id)
        phase_duration = traci.trafficlight.getPhaseDuration(tl_id)
        
        max_queue_lane = max(n_waiting, key=n_waiting.get)
        if max_queue_lane in get_green_lanes(current_phase):
            # 当前绿灯方向排队最长，延长 5 秒（不超过 60 秒）
            if phase_duration < 60:
                traci.trafficlight.setPhaseDuration(tl_id, 
                                                     phase_duration + 5)
        
        step += 1
    
    # 收集评估指标
    avg_delay = traci.simulation.getParameter("", "avg_delay")
    traci.close()
    return float(avg_delay)
```

### 6.2 评估指标

| 指标 | 定义 | 优化目标 |
|------|------|----------|
| 平均车辆延误 | 实际行程时间 - 自由流行程时间 | 最小化 |
| 排队长度 | 路口各进口道排队车辆数 | 最小化 |
| 停车次数 | 车辆在行程中的停车次数 | 最小化 |
| 通行能力 | 单位时间通过路口的车辆数 | 最大化 |
| 绿灯利用率 | 绿灯期间实际通过车辆 / 理论最大通行量 | 最大化 |

## 7 实际部署效果

### 7.1 全球案例数据

| 城市 | 系统 | 规模 | 延误降低 | 排放降低 |
|------|------|------|----------|----------|
| 匹兹堡 | Surtrac (RL) | 50 路口 | 25% | 21% |
| 悉尼 | SCATS | 3,800 路口 | 15-20% | — |
| 伦敦 | SCOOT | 6,000+ 路口 | 12% | 15% |
| 杭州 | 城市大脑 | 1,300 路口 | 15.3% | — |
| 深圳 | 华为TrafficGo | 200+ 路口 | 17% | — |
| 多伦多 | InSync | 2,000 路口 | 19% | 10% |

### 7.2 具体调优建议

- **检测器选型**：新建路口优先用视频检测（信息最丰富）；改造路口如果已有感应线圈，可以保留线圈 + 增加视频作为补充
- **RL 部署策略**：先在 SUMO 中用真实交通数据训练，再以 SCATS/SCOOT 作为 baseline 做 A/B 测试，逐步替换
- **绿波设计**：先保证主干道的单向绿波，再尝试双向绿波；设计车速应低于限速（通常取限速的 80-85%）
- **数据基础设施**：建设全市交通数据平台是一切智能化的前提，优先实现路口检测数据的实时汇聚和标准化
- **成本控制**：不要一步到位全市部署，先选 3-5 条主干道做试点，验证效果后再推广

## 参考文献

1. Wei, H., et al. "A Survey on Traffic Signal Control Methods." arXiv:1904.08117, 2023 (updated).
2. Smith, S. F., et al. "Smart Urban Signal Networks: Initial Application of the Surtrac Adaptive Traffic Signal Control System." Proceedings of ICAPS, 2023.
3. SCATS. "Sydney Coordinated Adaptive Traffic System Technical Reference." Roads and Maritime Services NSW, 2024.
4. Zheng, G., et al. "Diagnosing Reinforcement Learning for Traffic Signal Control." IEEE Transactions on ITS, 2024, 25(3), 2567-2581.
5. Wang, X., et al. "Multi-Agent Reinforcement Learning for Urban Traffic Signal Control Using Graph Attention Networks." Transportation Research Part C, 2024, 158, 104413.
6. 公安部交通管理局. "城市道路交通信号控制方式设置规范（GA/T 527-2023）." 2023.
7. Krajzewicz, D., et al. "SUMO – Simulation of Urban Mobility: An Overview." Proceedings of SIMUL, 2024.
8. He, K., et al. "Real-World Deployment of RL-based Traffic Signal Control: Challenges and Solutions." KDD, 2024.
9. Gregoire, J., et al. "Green Wave Optimization for Urban Traffic Networks: A Review." Transportation Research Record, 2024.
10. 杭州城市大脑交通平台. "2024 年交通治理报告." 2024.
