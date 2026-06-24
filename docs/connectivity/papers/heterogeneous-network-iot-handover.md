# 异构网络IoT设备切换与连接选择
> **难度**：🔴 高级 | **领域**：网络融合 | **阅读时间**：约 22 分钟

## 引言

想象你站在一个大型商场的美食广场, 周围有中餐, 日料, 西餐, 快餐四种餐厅. 你要选择去哪家吃午饭 -- 考虑的因素包括价格, 口味, 等待时间, 营养搭配. 如果你正在吃中餐但发现等菜太久, 可能会换到隔壁的快餐店. 异构网络中的IoT设备面临的就是这样的"选餐厅"问题: 周围同时存在多种网络(蜂窝, WiFi, LoRaWAN等), 设备需要在它们之间做出最优选择, 并在必要时平滑切换.

异构网络(Heterogeneous Network, HetNet)是指在同一区域内部署多种不同类型网络技术的网络架构. 在物联网场景中, 一个工厂车间可能同时覆盖着蜂窝宏基站, WiFi热点, LoRaWAN网关和蓝牙信标. IoT设备需要一套智能机制来选择最佳网络, 并在不同网络之间进行切换, 同时尽可能保证服务的连续性.

## 1 异构网络架构

### 1.1 多层网络覆盖

一个典型的IoT异构网络由多个层次的网络覆盖组成:

**宏蜂窝层**: LTE/5G宏基站, 覆盖范围最广(数公里), 提供广域连接. 适合移动设备和需要高可靠性的场景.

**小基站层**: Small Cell, 覆盖半径几十到几百米, 在人员密集区提供额外容量. 适合工业园区, 大型建筑内部.

**WiFi层**: WiFi接入点, 覆盖半径几十到一百米, 室内高速数据传输. 成本最低, 适合固定部署的设备.

**LPWAN层**: LoRaWAN网关或NB-IoT基站, 专为低功耗广域物联网设计. 数据速率低但覆盖广, 功耗极低.

### 1.2 核心网络集成

不同接入技术最终汇聚到统一的核心网络或IoT平台:

```
     IoT应用平台 / 云端
          |
    +-----+------+
    |  核心网关   |  <-- 统一数据接入和设备管理
    +-----+------+
    /    |    |     \
 LTE   WiFi  LoRa  NB-IoT
  |     |     |      |
 设备   设备  设备   设备
```

核心网关负责将来自不同接入网络的数据进行协议转换和统一管理, 使上层应用无需关心底层使用的是哪种网络技术.

### 1.3 设备能力差异

在异构网络中, IoT设备的能力差异很大:

- 单射频设备: 只有一种网络接口, 依赖网络侧完成切换
- 多射频设备: 具备多种网络接口, 可以自主选择网络
- 网关设备: 聚合多种网络, 为下游简单设备提供网络选择服务

## 2 网络选择问题建模

### 2.1 多属性决策框架

网络选择本质上是一个多属性决策问题(Multiple Attribute Decision Making, MADM). 设备面前有N个候选网络, 每个网络有M个属性, 需要选出综合最优的网络.

属性通常包括: 可用带宽, 端到端延迟, 延迟抖动, 通信成本, 能量消耗, 连接可靠性, 信号质量. 这些属性的量纲和方向不同(有些越大越好, 有些越小越好), 需要归一化处理.

### 2.2 AHP层次分析法确定权重

不同应用场景下, 各属性的重要程度不同. AHP(Analytic Hierarchy Process)通过成对比较确定权重:

```
目标: 选择最佳网络
    |
    +-- 带宽 (权重: 0.15)
    +-- 延迟 (权重: 0.25)  <-- 实时监控场景延迟最重要
    +-- 能耗 (权重: 0.30)  <-- IoT场景能耗权重通常最高
    +-- 成本 (权重: 0.20)
    +-- 可靠性 (权重: 0.10)
```

权重反映了当前应用对各属性的偏好程度. 例如, 电池供电的传感器会给能耗更高的权重, 而实时控制系统会更看重延迟.

### 2.3 TOPSIS排序法

TOPSIS(Technique for Order of Preference by Similarity to Ideal Solution)是一种常用的排序方法:

```python
import numpy as np

def topsis_network_selection(decision_matrix, weights, benefit_criteria):
    """
    decision_matrix: 行=候选网络, 列=属性
    weights: 各属性权重
    benefit_criteria: 哪些属性越大越好(True), 哪些越小越好(False)
    """
    # 归一化
    norm = decision_matrix / np.sqrt((decision_matrix ** 2).sum(axis=0))
    # 加权
    weighted = norm * weights
    # 确定正理想解和负理想解
    ideal_best = []
    ideal_worst = []
    for j in range(weighted.shape[1]):
        if benefit_criteria[j]:
            ideal_best.append(weighted[:, j].max())
            ideal_worst.append(weighted[:, j].min())
        else:
            ideal_best.append(weighted[:, j].min())
            ideal_worst.append(weighted[:, j].max())
    # 计算到正负理想解的距离
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    # 计算相对贴近度
    closeness = dist_worst / (dist_best + dist_worst)
    # 返回排名(贴近度最高的为最优)
    return np.argsort(-closeness)
```

TOPSIS的核心思想是: 最优方案应该离理想最优解最近, 同时离理想最差解最远.

## 3 基于效用函数的网络选择

### 3.1 效用函数定义

效用函数将各网络属性映射为一个综合效用值, 选择效用最高的网络:

```
U(network_i) = w1 * f1(throughput) + w2 * f2(delay) +
               w3 * f3(energy) + w4 * f4(cost) + w5 * f5(reliability)
```

其中f1到f5是各属性的效用映射函数, 将原始值转换为0到1之间的效用值.

### 3.2 效用映射函数

不同属性需要不同的映射函数:

**吞吐量**: 对于IoT设备, 超过需求的带宽并不会增加效用. 使用饱和函数:

```
f(throughput) = 1 - exp(-throughput / required_throughput)
```

当吞吐量达到需求的3倍时, 效用接近1, 再增加也无意义.

**延迟**: 低于阈值时效用为1, 超过阈值后快速下降:

```
f(delay) = 1    如果 delay < threshold
f(delay) = exp(-(delay - threshold) / tolerance)  否则
```

**能耗**: 与吞吐量类似但方向相反, 能耗越低效用越高:

```
f(energy) = exp(-energy / baseline_energy)
```

### 3.3 上下文自适应权重

在实际应用中, 权重不应该是固定的, 而应该根据设备当前上下文动态调整:

- 电池电量低于20%时, 能耗权重从0.3提升到0.5
- 有紧急数据需要发送时, 延迟和可靠性权重提升
- 设备静止在室内时, 成本权重提升(优先选免费网络)
- 设备快速移动时, 可靠性权重提升(优先选覆盖广的网络)

## 4 模糊逻辑方法

### 4.1 为什么用模糊逻辑

传统方法需要精确的数值和阈值, 但IoT环境中很多输入是不精确的. "信号好不好"很难用一个精确的dBm值来划分. 模糊逻辑允许使用语义化的描述(好, 中等, 差), 更符合实际决策过程.

### 4.2 模糊化输入

将精确的输入值模糊化为语义标签:

```
信号质量:
  差(Poor):     RSSI < -90 dBm (隶属度1.0)
  中(Medium):   RSSI = -90 ~ -70 dBm
  好(Good):     RSSI > -70 dBm (隶属度1.0)

电池电量:
  低(Low):      < 20%
  中(Medium):   20% ~ 60%
  高(High):     > 60%

数据优先级:
  低(Low):      常规遥测
  中(Medium):   状态更新
  高(High):     紧急告警
```

在过渡区域, 一个输入值可以同时属于两个类别, 只是隶属度不同. 例如RSSI为-80dBm, 可能同时属于"中"(隶属度0.6)和"差"(隶属度0.3).

### 4.3 模糊规则

基于模糊化的输入, 定义IF-THEN规则:

```
规则1: IF 信号质量 IS 好 AND 电池 IS 低
        THEN 选择 LPWAN (强度: 高)
规则2: IF 信号质量 IS 好 AND 电池 IS 高 AND 数据优先级 IS 高
        THEN 选择 蜂窝 (强度: 高)
规则3: IF WiFi可用 IS 是 AND 数据量 IS 大
        THEN 选择 WiFi (强度: 高)
规则4: IF 信号质量 IS 差 AND 数据优先级 IS 高
        THEN 选择 蜂窝 (强度: 中)
```

### 4.4 IoT中的优势

模糊逻辑的一个重要优势是计算开销小. 模糊推理引擎不需要矩阵运算或迭代优化, 只需要简单的比较和查表操作, 非常适合在MCU上运行. 一个具有30条规则的模糊推理引擎在Cortex-M4上运行时间不到1毫秒.

## 5 强化学习方法

### 5.1 问题建模

将网络选择建模为马尔科夫决策过程(MDP):

**状态(State)**: 各网络的信号强度, 设备电池电量, 数据队列长度, 当前时间, 设备位置/速度

**动作(Action)**: 选择网络1, 选择网络2, ..., 选择网络N

**奖励(Reward)**: 成功传输且低能耗得正奖励, 传输失败或高能耗得负奖励

### 5.2 Q-Learning实现

```python
class NetworkSelectionAgent:
    def __init__(self, n_states, n_networks, alpha=0.1, gamma=0.9):
        self.q_table = {}  # 稀疏Q表节省内存
        self.alpha = alpha  # 学习率
        self.gamma = gamma  # 折扣因子
        self.epsilon = 0.3  # 探索率, 逐渐降低

    def discretize_state(self, signal_levels, battery, queue_len):
        """将连续状态离散化"""
        sig_state = tuple(
            'good' if s > -70 else 'medium' if s > -90 else 'poor'
            for s in signal_levels
        )
        bat_state = 'high' if battery > 60 else 'medium' if battery > 20 else 'low'
        q_state = 'full' if queue_len > 10 else 'some' if queue_len > 0 else 'empty'
        return (sig_state, bat_state, q_state)

    def select_network(self, state):
        """epsilon-greedy选择"""
        if random.random() < self.epsilon:
            return random.randint(0, self.n_networks - 1)  # 探索
        q_values = [self.q_table.get((state, a), 0) for a in range(self.n_networks)]
        return max(range(len(q_values)), key=lambda a: q_values[a])  # 利用

    def update(self, state, action, reward, next_state):
        """更新Q值"""
        current_q = self.q_table.get((state, action), 0)
        max_next_q = max(
            self.q_table.get((next_state, a), 0)
            for a in range(self.n_networks)
        )
        new_q = current_q + self.alpha * (reward + self.gamma * max_next_q - current_q)
        self.q_table[(state, action)] = new_q
```

### 5.3 多臂赌博机方法

对于更简单的场景, 可以将网络选择建模为多臂赌博机(Multi-Armed Bandit)问题:

- 每个网络是一个"臂"
- 每次选择一个网络就是"拉一次臂"
- 奖励是传输成功率和能效的综合指标
- UCB(Upper Confidence Bound)算法平衡探索与利用

多臂赌博机比Q-Learning更简单, 不需要状态建模, 适合资源极其受限的设备.

### 5.4 学习过程中的权衡

强化学习方法的关键挑战是学习阶段的代价. 在学习初期, 设备会"探索"一些非最优的网络选择, 导致能耗增加或传输失败. 因此需要合理设置:

- 初始探索率: 不能太高避免前期性能太差
- 探索衰减速率: 逐渐减少探索, 更多利用已学知识
- 经验迁移: 从相似设备的学习经验初始化, 加速收敛

## 6 垂直切换决策

### 6.1 切换决策触发

垂直切换的决策需要综合考虑时机和目标网络:

**何时切换**: 当前网络的效用值下降到某个阈值以下, 或者有一个显著更优的网络可用.

**切向哪里**: 在所有可用的候选网络中, 选择效用值最高的.

### 6.2 预测性切换

被动等待信号恶化再切换会导致短暂的服务中断. 更好的方法是预测性切换:

- 基于信号趋势预测: RSSI连续下降, 预测即将失去覆盖
- 基于移动预测: 设备正在移开WiFi覆盖区
- 基于时间模式: 历史数据显示每天下午3点该区域WiFi拥塞

预测性切换可以提前准备新网络的连接, 实现真正的零中断切换.

### 6.3 避免乒乓效应的综合机制

多种机制配合使用:

- 迟滞量: 新网络效用必须比当前网络高出一定阈值才触发切换
- 驻留时间: 切换后必须停留一段最短时间
- 历史加权: 最近频繁切换的网络降低其选择优先级
- 趋势确认: 信号变化趋势持续一定时间才确认切换需求

## 7 永远最佳连接(ABC)

### 7.1 概念

Always Best Connected(ABC)是异构网络的终极目标: 设备始终连接到当前上下文下最优的网络. 这要求:

- 持续监控所有可用网络的状态
- 快速的切换决策和执行
- 全面的上下文感知: 位置, 移动状态, 应用需求, 能量状态

### 7.2 上下文感知引擎

实现ABC需要一个上下文感知引擎来收集和分析环境信息:

```python
class ContextEngine:
    def get_context(self):
        return {
            "location": self.gps.get_position(),
            "velocity": self.imu.get_speed(),
            "indoor": self.detect_indoor(),
            "battery": self.power.get_level(),
            "app_requirements": self.app.get_current_qos_needs(),
            "time_of_day": self.clock.get_hour(),
            "available_networks": self.scanner.get_all_networks(),
            "history": self.get_recent_handover_history()
        }
```

上下文信息帮助做出更准确的网络选择. 例如, 检测到设备在室内且静止时, WiFi是最佳选择; 检测到设备高速移动时, 蜂窝网络更合适.

## 8 移动性管理

### 8.1 IP会话连续性挑战

异构网络切换的最大技术挑战之一是IP会话连续性. 当设备从WiFi切换到蜂窝网络时, IP地址会变化, 所有基于IP的连接(TCP)都会断开.

### 8.2 网络层解决方案

**PMIPv6(代理移动IPv6)**: 网络侧管理移动性, 设备无需参与, 适合能力有限的IoT设备. 移动锚点(MAG)在不同接入网之间代理设备的IP会话.

**GTP隧道**: 3GPP标准的移动性管理, 将数据封装在GTP隧道中, 设备保持相同的IP地址.

### 8.3 应用层解决方案

对于大多数IoT场景, 应用层的解决方案更实用也更轻量:

**MQTT持久会话**: 设备使用固定的ClientID, 设置cleanSession为false. 切换网络后重连, broker自动恢复订阅和未送达消息.

**CoAP观察**: CoAP的Observe选项支持服务器端维护观察关系. 设备重连后重新注册观察即可恢复数据推送.

对于IoT设备来说, 应用层方案通常已经足够, 因为IoT数据通常是小型的, 离散的传感器读数, 短暂的切换中断可以接受.

## 9 实际案例: 智慧城市多网络部署

### 9.1 场景描述

一个智慧城市环境监测系统, 部署区域同时覆盖有LTE-M基站, LoRaWAN网关和WiFi热点三种网络.

### 9.2 设备行为

环境传感器节点在正常情况下使用LoRaWAN每小时上报一次温湿度, 空气质量等常规数据. LoRaWAN功耗最低, 完全满足小数据量周期上报的需求.

当检测到污染事件(某个指标突然飙升)时, 传感器切换到LTE-M进行实时数据流传输. 此时数据频率从每小时一次变为每10秒一次, 数据量和实时性要求大幅提升.

当传感器靠近WiFi热点时, 利用WiFi批量卸载历史数据. 传感器本地缓存的几天历史数据可以通过WiFi一次性上传, 避免占用昂贵的蜂窝带宽.

### 9.3 效果

该系统使用Q-Learning进行网络选择, 经过30天训练后设备学会了在不同时段和位置选择最优网络, 自动避开高峰时段拥塞的WiFi热点, 并在恶劣天气主动切换到LTE-M.

| 指标 | 始终蜂窝 | Q-Learning多网络 |
|------|----------|-------------------|
| 能耗 | 100% | 60%(节省40%) |
| 数据送达率 | 99.8% | 99.5% |
| 通信成本 | 100% | 35% |
| 电池寿命 | 6个月 | 10个月 |

在数据送达率仅下降0.3个百分点的情况下, 实现了40%的能耗节省和65%的成本降低, 充分体现了异构网络智能选择的价值.

## 总结

异构网络中的IoT设备切换与连接选择是一个综合性的优化问题. 网络选择方面, MADM, 效用函数, 模糊逻辑和强化学习提供了从简单到复杂的一系列工具. 切换决策方面, 预测性切换优于被动切换, 迟滞和驻留机制防止乒乓效应. 移动性管理方面, 应用层方案(MQTT持久会话, CoAP观察)对IoT场景最为实用. 实践方面, 多种方法的组合往往优于单一方法, 需要根据设备能力和应用需求灵活选择.

异构网络融合是IoT基础设施发展的必然趋势, 掌握网络选择和切换技术, 是构建可靠高效IoT系统的关键能力.

## 参考文献

1. E. Stevens-Navarro et al., "Using MADM Methods for Vertical Handoff Decision Making in Beyond 3G Networks," IEEE Transactions on Wireless Communications, 2020
2. R. Trestian et al., "Game Theory-Based Network Selection: Solutions and Challenges," IEEE Communications Surveys & Tutorials, 2018
3. L. Wang et al., "Reinforcement Learning Based Network Selection for IoT Heterogeneous Networks," IEEE Internet of Things Journal, 2021
4. 3GPP TR 23.793, "Study on Access Traffic Steering, Switch and Splitting Support in the 5G System Architecture," 2019
5. A. Keshavarz-Haddad et al., "Fuzzy Logic Based Vertical Handover Decision in Heterogeneous Wireless Networks," Wireless Personal Communications, 2020
