# 群体智能（Swarm Intelligence）：从蚁群到万物协作

> **难度**：🟡 中级 | **领域**：群体智能、优化算法、分布式协调 | **阅读时间**：约 25 分钟

## 日常类比

观察一群蚂蚁搬运食物。没有一只蚂蚁是"总指挥"，没有蚂蚁拿着地图规划路线。但神奇的是，整个蚁群总能找到从巢穴到食物的最短路径。秘密在于"信息素"——走过的蚂蚁留下化学痕迹，后来的蚂蚁跟随浓度高的路径，短路径信息素越积越浓（正反馈），长路径信息素蒸发（负反馈），最终全群收敛到最短路径。

再看鸟群飞行。几千只椋鸟组成令人惊叹的"飞行云"——没有指挥家，每只鸟只遵循三条规则：别靠太近（避碰）、大致同向（对齐）、别飞太远（聚合）。简单局部规则产生复杂全局行为——这就是"涌现"。

群体智能在 IoT 中：当你有 10000 个传感器要协调、100 架无人机要协作巡逻、1000 个机器人要同时搬货——中央调度既慢又不可靠。让每个节点像蚂蚁一样只看局部信息、遵循简单规则，就能涌现全局最优行为。

## 1. 群体智能基础

### 1.1 核心特征

| 特征 | 定义 | IoT 对应 |
|------|------|---------|
| 去中心化 | 无全局控制者 | 无需中央服务器 |
| 自组织 | 结构从局部交互涌现 | 网络拓扑自动形成 |
| 正反馈 | 好方案被放大 | 优质路由被强化 |
| 负反馈 | 差方案被抑制 | 过载路径被避开 |
| 鲁棒性 | 个体故障不影响整体 | 设备故障可容忍 |
| 可扩展 | 增加个体不增复杂度 | 新设备即插即用 |

### 1.2 经典算法族

| 算法 | 年份 | 灵感来源 | 适合问题 |
|------|------|---------|---------|
| 蚁群优化 (ACO) | 1992 | 蚂蚁觅食 | 路径优化、网络路由 |
| 粒子群优化 (PSO) | 1995 | 鸟群飞行 | 连续优化、参数调优 |
| 人工蜂群 (ABC) | 2005 | 蜜蜂采蜜 | 多目标优化 |
| 萤火虫算法 (FA) | 2008 | 萤火虫发光 | 多峰优化、传感器部署 |
| 灰狼优化 (GWO) | 2014 | 狼群捕猎 | 工程设计优化 |
| 鲸鱼优化 (WOA) | 2016 | 座头鲸狩猎 | 特征选择 |

## 2. 蚁群优化（ACO）

### 2.1 算法原理

```python
import numpy as np

class AntColonyOptimizer:
    """蚁群优化 - IoT 路由优化示例"""
    
    def __init__(self, n_nodes, n_ants=50, alpha=1.0, beta=2.0, rho=0.1):
        self.n_nodes = n_nodes
        self.n_ants = n_ants
        self.alpha = alpha   # 信息素重要度
        self.beta = beta     # 启发信息重要度
        self.rho = rho       # 信息素蒸发率
        self.pheromone = np.ones((n_nodes, n_nodes))
    
    def solve(self, distances, source, dest, iterations=100):
        """求解最优路由路径"""
        best_path = None
        best_cost = float('inf')
        
        for iteration in range(iterations):
            paths = []
            costs = []
            
            for ant in range(self.n_ants):
                path = self._construct_path(distances, source, dest)
                cost = self._path_cost(path, distances)
                paths.append(path)
                costs.append(cost)
                
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
            
            self._update_pheromone(paths, costs)
        
        return best_path, best_cost
    
    def _construct_path(self, distances, source, dest):
        """单只蚂蚁构建路径"""
        path = [source]
        current = source
        visited = {source}
        
        while current != dest:
            neighbors = [n for n in range(self.n_nodes)
                        if n not in visited and distances[current][n] > 0]
            if not neighbors:
                break
            
            # 转移概率
            probs = []
            for n in neighbors:
                tau = self.pheromone[current][n] ** self.alpha
                eta = (1.0 / distances[current][n]) ** self.beta
                probs.append(tau * eta)
            
            probs = np.array(probs) / sum(probs)
            next_node = np.random.choice(neighbors, p=probs)
            
            path.append(next_node)
            visited.add(next_node)
            current = next_node
        
        return path
    
    def _update_pheromone(self, paths, costs):
        """信息素更新"""
        self.pheromone *= (1 - self.rho)  # 蒸发
        for path, cost in zip(paths, costs):
            deposit = 1.0 / cost
            for i in range(len(path) - 1):
                self.pheromone[path[i]][path[i+1]] += deposit
```

### 2.2 IoT 路由应用对比

| 场景 | 优化目标 | ACO 优势 | 传统方案 |
|------|---------|---------|---------|
| WSN 数据汇聚 | 最小能耗 | 自适应路径 | LEACH (固定) |
| 多跳中继 | 最小延迟 | 负载均衡 | Dijkstra (静态) |
| 移动节点 | 动态路由 | 实时更新 | AODV (频繁重建) |
| 异构网络 | 多约束 QoS | 多信息素 | OSPF (不适用) |

## 3. 粒子群优化（PSO）

### 3.1 传感器部署优化

```python
class PSO_SensorDeployment:
    """粒子群优化 - IoT 传感器最优部署"""
    
    def __init__(self, n_sensors, area_size, n_particles=30):
        self.n_sensors = n_sensors
        self.area = area_size
        self.n_particles = n_particles
        self.dims = n_sensors * 2  # 每个传感器 (x, y)
        
        # 初始化
        self.positions = np.random.uniform(0, area_size, (n_particles, self.dims))
        self.velocities = np.random.uniform(-1, 1, (n_particles, self.dims))
        self.pbest_pos = self.positions.copy()
        self.pbest_val = np.full(n_particles, float('inf'))
        self.gbest_pos = None
        self.gbest_val = float('inf')
    
    def coverage_fitness(self, position):
        """适应度函数：最大化区域覆盖率"""
        sensors = position.reshape(-1, 2)
        sensing_radius = 10.0  # 传感器感知半径
        
        # 网格采样计算覆盖率
        grid_size = 50
        covered = 0
        total = grid_size * grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                point = np.array([i * self.area / grid_size,
                                  j * self.area / grid_size])
                distances = np.linalg.norm(sensors - point, axis=1)
                if np.min(distances) <= sensing_radius:
                    covered += 1
        
        coverage_rate = covered / total
        # 同时考虑连通性（传感器间通信距离）
        connectivity = self._check_connectivity(sensors)
        
        # 最小化 = 负覆盖率 + 连通性惩罚
        return -(coverage_rate - 0.5 * (1 - connectivity))
    
    def optimize(self, iterations=200, w=0.7, c1=1.5, c2=1.5):
        """PSO 主循环"""
        for t in range(iterations):
            for i in range(self.n_particles):
                fitness = self.coverage_fitness(self.positions[i])
                
                if fitness < self.pbest_val[i]:
                    self.pbest_val[i] = fitness
                    self.pbest_pos[i] = self.positions[i].copy()
                
                if fitness < self.gbest_val:
                    self.gbest_val = fitness
                    self.gbest_pos = self.positions[i].copy()
            
            # 更新速度和位置
            r1 = np.random.random((self.n_particles, self.dims))
            r2 = np.random.random((self.n_particles, self.dims))
            
            self.velocities = (w * self.velocities +
                             c1 * r1 * (self.pbest_pos - self.positions) +
                             c2 * r2 * (self.gbest_pos - self.positions))
            self.positions += self.velocities
            
            # 边界约束
            self.positions = np.clip(self.positions, 0, self.area)
        
        return self.gbest_pos.reshape(-1, 2), -self.gbest_val
```

## 4. 群体机器人（Swarm Robotics）

### 4.1 无人机蜂群协作

```python
class DroneSwarm:
    """无人机蜂群 - 分布式巡逻覆盖"""
    
    def __init__(self, n_drones, patrol_area):
        self.drones = [Drone(i) for i in range(n_drones)]
        self.area = patrol_area
    
    def boids_rules(self, drone):
        """Boids 三规则实现群体协调"""
        neighbors = self.get_neighbors(drone, radius=50)
        
        # 规则1：分离（避碰）
        separation = np.zeros(2)
        for n in neighbors:
            if self.distance(drone, n) < 10:
                separation += (drone.position - n.position)
        
        # 规则2：对齐（速度一致）
        alignment = np.zeros(2)
        if neighbors:
            avg_velocity = np.mean([n.velocity for n in neighbors], axis=0)
            alignment = avg_velocity - drone.velocity
        
        # 规则3：聚合（保持群体）
        cohesion = np.zeros(2)
        if neighbors:
            center = np.mean([n.position for n in neighbors], axis=0)
            cohesion = center - drone.position
        
        # 规则4（扩展）：任务吸引力
        task_attraction = self.compute_task_force(drone)
        
        # 加权合成
        force = (1.5 * separation + 1.0 * alignment + 
                 1.0 * cohesion + 2.0 * task_attraction)
        return force
    
    def distributed_patrol(self):
        """分布式区域巡逻"""
        # 基于虚拟信息素的区域覆盖
        pheromone_map = np.ones(self.area.shape)  # 未巡逻区域信息素高
        
        for drone in self.drones:
            # 向信息素浓度最高的方向移动（未巡逻区域）
            local_pheromone = self.sense_local(drone, pheromone_map)
            target = self.highest_pheromone_direction(local_pheromone)
            
            # 施加 Boids 规则避免碰撞和重复覆盖
            swarm_force = self.boids_rules(drone)
            
            # 合成运动方向
            drone.move(target + swarm_force)
            
            # 经过的区域信息素降低（已巡逻）
            pheromone_map[drone.grid_position] *= 0.1
        
        # 信息素随时间恢复（需要重新巡逻）
        pheromone_map = np.minimum(pheromone_map * 1.01, 1.0)
```

### 4.2 应用场景

| 场景 | 蜂群规模 | 协调机制 | 通信方式 | 关键指标 |
|------|---------|---------|---------|---------|
| 农业植保 | 5-20 架 | 区域划分 | WiFi Mesh | 覆盖率>98% |
| 搜索救援 | 10-50 架 | 信息素扩散 | Ad-hoc | 发现时间-50% |
| 物流配送 | 50-200 架 | 拍卖算法 | 5G | 效率+40% |
| 军事侦察 | 100+ 架 | 涌现战术 | 抗干扰 | 生存率+60% |
| 仓储搬运 | 100-1000 | 交通规则 | UWB | 吞吐+80% |

## 5. 分布式共识与涌现

### 5.1 IoT 分布式共识

```python
class SwarmConsensus:
    """群体智能分布式共识（无中心协调）"""
    
    def __init__(self, n_agents):
        self.agents = [{'value': np.random.random(), 'id': i} 
                      for i in range(n_agents)]
    
    def average_consensus(self, adjacency_matrix, iterations=50):
        """平均共识协议：所有节点收敛到平均值"""
        values = np.array([a['value'] for a in self.agents])
        
        for t in range(iterations):
            new_values = values.copy()
            for i in range(len(self.agents)):
                neighbors = np.where(adjacency_matrix[i] > 0)[0]
                if len(neighbors) > 0:
                    # 每个节点向邻居的平均值靠拢
                    neighbor_avg = np.mean(values[neighbors])
                    epsilon = 0.3  # 收敛速率
                    new_values[i] = values[i] + epsilon * (neighbor_avg - values[i])
            values = new_values
        
        return values  # 所有值将收敛到初始平均值
    
    def application_scenarios(self):
        """共识在 IoT 中的应用"""
        return {
            'distributed_estimation': '多传感器融合估计（温度/位置）',
            'clock_synchronization': '无 GPS 环境下的时钟同步',
            'load_balancing': '计算负载在边缘节点间均衡',
            'formation_control': '机器人编队保持',
            'distributed_detection': '协作目标检测（多传感器投票）'
        }
```

### 5.2 涌现行为在 IoT 中的体现

| 微观规则 | 涌现的宏观行为 | IoT 应用 |
|----------|--------------|---------|
| 跟随邻居信号最强方向 | 数据汇聚树形成 | WSN 路由 |
| 空闲时随机移动，忙时不动 | 负载自均衡 | 边缘计算 |
| 检测到异常通知邻居 | 告警波传播 | 入侵检测 |
| 电量低时减少工作 | 网络寿命最大化 | 能量采集 |
| 复制成功邻居的参数 | 全网参数优化 | 自配置网络 |

## 6. 生物启发通信

### 6.1 仿生通信协议

| 生物启发 | 通信机制 | IoT 协议 | 优势 |
|----------|---------|---------|------|
| 蚂蚁信息素 | 路径标记+蒸发 | AntNet 路由 | 自适应拥塞 |
| 蜜蜂摇摆舞 | 方向+距离编码 | 数据聚合 | 高效压缩 |
| 萤火虫同步 | 脉冲耦合振荡 | 时钟同步 | 去中心化 |
| 细菌趋化性 | 梯度跟随 | 源定位 | 分布式搜索 |
| 免疫应答 | 克隆选择+记忆 | 入侵检测 | 自适应学习 |

### 6.2 蚂蚁信息素路由

```python
class AntNetRouting:
    """AntNet 自适应路由协议"""
    
    def __init__(self, network_topology):
        self.topology = network_topology
        self.routing_tables = {}  # 概率路由表
        self.pheromone_tables = {}
    
    def forward_ant(self, source, destination):
        """前向蚂蚁：探索路径"""
        path = [source]
        current = source
        
        while current != destination:
            # 根据概率路由表选择下一跳
            probs = self.routing_tables[current][destination]
            next_hop = self.probabilistic_select(probs)
            path.append(next_hop)
            current = next_hop
        
        return path
    
    def backward_ant(self, path, trip_time):
        """后向蚂蚁：更新路由表"""
        # 沿原路返回，更新信息素
        for i in range(len(path) - 1, 0, -1):
            node = path[i]
            prev = path[i-1]
            
            # 好路径（低延迟）增加信息素
            reinforcement = 1.0 / trip_time
            self.pheromone_tables[node][prev] += reinforcement
            
            # 归一化为概率
            total = sum(self.pheromone_tables[node].values())
            for dest in self.pheromone_tables[node]:
                self.routing_tables[node][dest] = (
                    self.pheromone_tables[node][dest] / total)
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一周**：阅读 Boids 模型原始论文（Reynolds 1987），用 Python 实现 2D 鸟群仿真
2. **第二周**：实现 ACO 求解 TSP 问题，理解信息素正反馈机制
3. **第三周**：实现 PSO 求解传感器部署优化问题
4. **第四周**：用 NetLogo 或 Mesa(Python) 做多智能体仿真，观察涌现行为
5. **进阶**：研究 ROS2 多机器人编队、实际无人机蜂群系统（如 Crazyswarm）

### 7.2 具体调优建议

- **种群大小**：ACO 蚂蚁数通常取节点数的 1-2 倍，PSO 粒子 20-50 个
- **参数平衡**：探索(exploration) vs 利用(exploitation)，初期多探索后期多利用
- **信息素蒸发率**：太快忘记好路径，太慢陷入局部最优，通常 rho=0.1-0.3
- **通信开销**：实际 IoT 部署时，减少全局信息交换（只与邻居通信）
- **收敛判断**：连续 N 代最优解不变化时停止，避免无谓计算
- **混合策略**：ACO+局部搜索（2-opt）效果通常优于纯 ACO

## 参考文献

1. Dorigo, M., & Stutzle, T. (2004). Ant Colony Optimization. MIT Press.
2. Kennedy, J., & Eberhart, R. (1995). Particle Swarm Optimization. ICNN.
3. Reynolds, C. W. (1987). Flocks, Herds and Schools: A Distributed Behavioral Model. SIGGRAPH.
4. Bonabeau, E., Dorigo, M., & Theraulaz, G. (1999). Swarm Intelligence: From Natural to Artificial Systems. Oxford University Press.
5. Karaboga, D. (2005). An Idea Based on Honey Bee Swarm for Numerical Optimization. Technical Report.
6. Brambilla, M., et al. (2013). Swarm Robotics: A Review from the Swarm Engineering Perspective. Swarm Intelligence.
7. Di Caro, G., & Dorigo, M. (1998). AntNet: Distributed Stigmergetic Control for Communications Networks. JAIR.
8. Olfati-Saber, R., et al. (2007). Consensus and Cooperation in Networked Multi-Agent Systems. Proceedings of the IEEE.
9. Preiss, J. A., et al. (2017). Crazyswarm: A Large Nano-Quadcopter Swarm. ICRA.
10. Yang, X. S. (2010). Nature-Inspired Metaheuristic Algorithms. Luniver Press.
