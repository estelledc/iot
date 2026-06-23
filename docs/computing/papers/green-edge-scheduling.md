# 绿色边缘调度策略

> **难度**：🟡 中级 | **领域**：绿色计算、调度优化、边缘计算 | **阅读时间**：约 20 分钟

## 日常类比

假设你家装了太阳能板和一块储能电池。白天太阳好的时候，电是"免费的"而且是清洁的；晚上或阴天就得用电网的电（可能是火力发电）。聪明的做法是：把洗衣机、充电桩这些"不着急"的任务安排在白天太阳最好的时候跑。

绿色边缘调度做的事情类似，但对象变成了计算任务。边缘节点散布在不同地方——有的靠近风力发电场，有的用市电，有的自带太阳能板。当一个计算任务不那么紧急时（比如模型更新、日志归档、数据同步），可以把它调度到当前用绿色能源的节点上执行，或者等本地太阳能板发电高峰再跑。

这不只是环保情怀。全球数据中心碳排放约占 ICT 行业的 2-3%（2024 年约 3.5 亿吨 CO2e），其中边缘计算设施的碳效率通常比大型云数据中心更差——因为小规模部署很难用到高效的散热和供电系统。

## 1. 碳感知计算基础

### 1.1 碳排放的两个来源

| 类型 | 定义 | 优化空间 |
|------|------|---------|
| 运营碳（Operational Carbon） | 运行时用电产生的碳排放 | 大：通过调度和效率优化可减少 30-60% |
| 内嵌碳（Embodied Carbon） | 制造硬件产生的碳排放 | 有限：通过延长硬件寿命间接减少 |

边缘设备的内嵌碳占比通常高于云服务器（因为生命周期短、利用率低）。一台边缘服务器的制造碳排放约 1-2 吨 CO2e，运行 5 年的用电碳排放约 3-8 吨 CO2e（取决于电网碳强度）。

### 1.2 碳强度（Carbon Intensity）

碳强度衡量每度电产生的碳排放，单位 gCO2eq/kWh。不同时间、不同地区差异巨大：

```
中国各地区电网碳强度（2024 年平均）：
  云南/四川（水电为主）：~50 gCO2/kWh
  北京/河北（火电为主）：~800 gCO2/kWh
  全国平均：            ~540 gCO2/kWh

对比其他国家/地区：
  法国（核电为主）：~60 gCO2/kWh
  德国（混合）：    ~350 gCO2/kWh
  印度（煤电为主）：~700 gCO2/kWh

同一地区一天内也会波动：
  白天（太阳能高峰）：碳强度低
  晚上（火电顶峰）：  碳强度高
  波动幅度：30-60%
```

### 1.3 碳强度数据来源

实时碳强度数据可以从这些 API 获取：

```python
import requests

# 方式 1：Electricity Maps API（全球覆盖）
def get_carbon_intensity_electricitymaps(zone="CN-SH"):
    """获取指定区域的实时碳强度"""
    resp = requests.get(
        f"https://api.electricitymap.org/v3/carbon-intensity/latest",
        params={"zone": zone},
        headers={"auth-token": "YOUR_API_KEY"}
    )
    data = resp.json()
    return data["carbonIntensity"]  # gCO2eq/kWh

# 方式 2：WattTime API（北美覆盖更细）
def get_carbon_intensity_watttime(latitude, longitude):
    resp = requests.get(
        "https://api.watttime.org/v3/signal-index",
        params={"latitude": latitude, "longitude": longitude},
        headers={"Authorization": f"Bearer {token}"}
    )
    return resp.json()

# 方式 3：本地估算（无外网时的降级方案）
def estimate_carbon_intensity_local(hour: int, has_solar: bool):
    """基于时段和本地发电的简单估算"""
    base = 540  # 全国平均
    if has_solar and 9 <= hour <= 16:
        return base * 0.3  # 太阳能高峰，碳强度大幅下降
    elif 0 <= hour <= 6:
        return base * 0.8  # 夜间低谷，火电占比高但负载低
    else:
        return base
```

## 2. 碳感知工作负载调度

### 2.1 时间迁移（Temporal Shifting）

把非紧急任务推迟到碳强度低的时段执行：

```python
from datetime import datetime, timedelta
from typing import Optional

class CarbonAwareScheduler:
    """碳感知调度器：将可延迟任务安排在低碳时段"""

    def __init__(self, carbon_api, max_delay_hours=6):
        self.carbon_api = carbon_api
        self.max_delay_hours = max_delay_hours

    def schedule_task(self, task, priority: str) -> Optional[datetime]:
        """
        priority:
          - 'realtime': 立即执行（不受碳调度影响）
          - 'best-effort': 在 max_delay 内选最低碳时段
          - 'batch': 可以等到下一个最低碳窗口
        """
        if priority == "realtime":
            return datetime.utcnow()  # 立即执行

        # 获取未来 N 小时的碳强度预测
        forecast = self.carbon_api.get_forecast(
            hours=self.max_delay_hours)

        if priority == "best-effort":
            # 在允许延迟范围内选碳强度最低的时段
            best_slot = min(forecast, key=lambda x: x["carbon_intensity"])
            return best_slot["timestamp"]

        elif priority == "batch":
            # 等待碳强度低于阈值（如 200 gCO2/kWh）
            threshold = 200
            for slot in forecast:
                if slot["carbon_intensity"] < threshold:
                    return slot["timestamp"]
            # 如果超过最大延迟仍没有低碳窗口，强制执行
            return datetime.utcnow() + timedelta(hours=self.max_delay_hours)
```

Google 在其数据中心实践中，通过时间迁移将碳排放降低了约 12%（2023 年报告）。边缘场景由于碳强度波动更大（本地光伏/风电的间歇性），潜在减排比例更高。

### 2.2 空间迁移（Spatial Shifting）

把任务迁移到当前碳强度更低的边缘节点执行：

```
场景：3 个边缘节点
  A（北京）：碳强度 750 gCO2/kWh（全火电）
  B（上海）：碳强度 450 gCO2/kWh（混合）
  C（成都）：碳强度 120 gCO2/kWh（水电为主）

一个非紧急的模型训练任务（需 4 小时）：
  在 A 执行：4h × 0.3kW × 750 = 900 gCO2
  在 C 执行：4h × 0.3kW × 120 = 144 gCO2
  减排：84%
  
代价：将数据传输到 C 的网络延迟和带宽消耗
```

空间迁移的约束条件：

- 数据传输成本（带宽和延迟）
- 数据主权法规（某些数据不能跨区域）
- 目标节点的可用资源
- 网络连接可靠性

## 3. 能量比例计算

### 3.1 什么是能量比例计算

理想状态下，服务器空闲时功耗为零，满载时功耗最大——功耗与负载成正比。现实中，服务器在空闲时也会消耗峰值功耗的 40-60%：

```
理想能量比例：
  功耗 = 峰值功耗 × 利用率
  空闲功耗 = 0

现实情况（典型 x86 服务器）：
  功耗 = 静态功耗 + 动态功耗 × 利用率
  空闲功耗 ≈ 0.5 × 峰值功耗

示例（Dell PowerEdge R750, TDP 750W）：
  空闲：310W (41%)
  25% 负载：420W (56%)
  50% 负载：530W (71%)
  75% 负载：620W (83%)
  100% 负载：750W (100%)
```

这意味着一台 10% 利用率的服务器在浪费大量电力。解决方案有两个方向：

### 3.2 节点合并（Consolidation）

把低负载节点的任务集中到少数节点上，关闭空闲节点：

```python
class GreenConsolidator:
    """将低负载边缘节点的任务合并，关闭空闲节点"""

    def __init__(self, nodes, utilization_threshold=0.3):
        self.nodes = nodes
        self.threshold = utilization_threshold

    def evaluate_consolidation(self):
        """评估哪些节点可以合并"""
        low_util = [n for n in self.nodes if n.cpu_util < self.threshold]
        high_util = [n for n in self.nodes if n.cpu_util >= self.threshold]

        migrations = []
        for src in sorted(low_util, key=lambda n: n.cpu_util):
            for dst in high_util:
                if dst.cpu_util + src.cpu_util < 0.85:  # 不超过 85%
                    migrations.append({
                        "source": src.id,
                        "destination": dst.id,
                        "tasks": src.running_tasks,
                        "energy_saved_watts": src.idle_power
                    })
                    dst.cpu_util += src.cpu_util
                    break

        return migrations
```

边缘场景的合并比云端更谨慎——关掉一个边缘节点可能意味着某些用户的延迟增加（必须走更远的节点）。

## 4. DVFS 与功耗管理

### 4.1 动态电压频率调节（DVFS）

DVFS 通过降低 CPU 频率和电压来节省功耗。功耗与频率近似立方关系：

```
P ∝ V² × f
降频 20% → 功耗降低约 50%（因为电压也可以降）
```

Linux 上的 DVFS 控制：

```bash
# 查看当前频率策略
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# 常见策略：performance | powersave | ondemand | schedutil

# 边缘节点推荐：schedutil（内核调度器感知）
echo schedutil | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 或者手动设置最大频率（限制功耗上限）
echo 2000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq
# 将最大频率限制为 2GHz（原始可能是 3.5GHz）

# ARM 边缘设备（如 Jetson Orin）的功耗模式
sudo nvpmodel -m 2    # 15W 模式（低功耗）
sudo nvpmodel -m 0    # MAXN 模式（最大性能）
sudo jetson_clocks     # 锁定最大频率（禁用 DVFS，仅测试用）
```

### 4.2 GPU 功耗管理

NVIDIA GPU 支持功耗限制：

```bash
# 查看当前功耗和温度
nvidia-smi --query-gpu=power.draw,temperature.gpu,clocks.gr --format=csv

# 设置 GPU 功耗上限（如从 300W 限制到 200W）
sudo nvidia-smi -pl 200

# 效果：
#   原始 300W → 限制 200W
#   性能下降约 15-20%（不是线性的！）
#   温度降低 10-15°C
#   适合边缘散热条件差的场景
```

## 5. 温度感知调度

### 5.1 边缘环境的热挑战

边缘节点部署环境多样——可能在空调机房，也可能在户外机柜（夏天 50°C+）。高温导致：

- CPU/GPU 自动降频（thermal throttling），性能下降 20-50%
- 风扇全速运转，额外功耗增加 30-50W
- 硬件寿命缩短（温度每升高 10°C，故障率翻倍）

```python
import subprocess
import json

class ThermalAwareScheduler:
    """根据温度调整任务分配"""

    TEMP_THRESHOLDS = {
        "normal": 65,     # 65°C 以下正常
        "warm": 80,       # 65-80°C 减少负载
        "critical": 90    # 80°C+ 紧急降载
    }

    def get_cpu_temp(self) -> float:
        """读取 CPU 温度"""
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read().strip()) / 1000.0  # 毫摄氏度→摄氏度

    def get_gpu_temp(self) -> float:
        """读取 GPU 温度"""
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu",
             "--format=csv,noheader"],
            capture_output=True, text=True)
        return float(result.stdout.strip())

    def decide_action(self):
        cpu_temp = self.get_cpu_temp()
        gpu_temp = self.get_gpu_temp()
        max_temp = max(cpu_temp, gpu_temp)

        if max_temp >= self.TEMP_THRESHOLDS["critical"]:
            return {
                "action": "emergency_throttle",
                "max_cpu_freq": "1.5GHz",
                "gpu_power_limit": "50%",
                "migrate_batch_tasks": True
            }
        elif max_temp >= self.TEMP_THRESHOLDS["warm"]:
            return {
                "action": "reduce_load",
                "max_cpu_freq": "2.5GHz",
                "gpu_power_limit": "75%",
                "defer_non_critical": True
            }
        else:
            return {"action": "normal", "max_cpu_freq": "auto"}
```

### 5.2 PUE 优化

PUE（Power Usage Effectiveness）= 总设施功耗 / IT 设备功耗。

```
理想 PUE = 1.0（所有电力都用于计算）
大型云数据中心：1.1-1.2（Google 平均 1.10）
传统数据中心：1.5-2.0
边缘微数据中心：1.3-1.8（散热效率低）
户外边缘节点：1.5-2.5（无空调，靠自然散热+风扇）
```

改善边缘 PUE 的手段：

- 液冷/浸没冷却（小型密封机柜可用单相浸没冷却）
- 自然冷却（高纬度或高海拔地区利用自然低温）
- 热回收（用 IT 设备余热给附近建筑供暖——北欧已有案例）

## 6. 太阳能-电池边缘节点

### 6.1 离网边缘系统设计

偏远地区的边缘节点（如农业 IoT、野生动物监测站）可能完全依赖太阳能 + 电池：

```
系统架构：
  太阳能板（200-400W）→ MPPT 控制器 → 锂电池（1-5 kWh）→ 边缘计算设备
                                                                │
  电池状态（SoC）←──── 能量管理系统（EMS）──────────────→ 工作负载调度器
```

### 6.2 基于电池状态的调度

```python
class SolarEdgeScheduler:
    """太阳能供电的边缘节点调度策略"""

    def __init__(self):
        self.battery_capacity_wh = 2000  # 2kWh 电池
        self.min_soc = 0.2               # 最低保留 20% 电量

    def get_available_energy_wh(self, current_soc: float) -> float:
        """可用能量 = (当前电量 - 保留电量) × 容量"""
        return max(0, (current_soc - self.min_soc) * self.battery_capacity_wh)

    def schedule(self, current_soc: float, solar_power_w: float,
                 tasks: list) -> list:
        """根据电池状态和太阳能功率调度任务"""
        available = self.get_available_energy_wh(current_soc)
        scheduled = []

        # 排序：紧急任务优先，然后按能耗从小到大
        sorted_tasks = sorted(tasks, key=lambda t: (-t.priority, t.energy_wh))

        for task in sorted_tasks:
            if task.priority >= 9:  # 最高优先级：无条件执行
                scheduled.append(task)
                available -= task.energy_wh

            elif solar_power_w > task.power_w * 1.2:
                # 太阳能功率足够覆盖（含 20% 余量）：执行
                scheduled.append(task)

            elif available > task.energy_wh * 1.5:
                # 电池余量充足（含 50% 余量）：执行
                scheduled.append(task)
                available -= task.energy_wh

            else:
                # 能量不足：推迟
                task.status = "deferred"

        return scheduled
```

### 6.3 实际案例：农业 IoT

一个太阳能供电的农业监测站配置：

```
硬件：
  计算：Raspberry Pi 5 (5-15W)
  太阳能：300W 单晶硅板
  电池：1.2 kWh 磷酸铁锂
  传感器：土壤湿度/温度/pH/风速/雨量

任务调度：
  持续运行（最高优先级）：传感器采集 + MQTT 上报 (~3W)
  白天运行（太阳能充足时）：图像采集 + 本地推理 (~8W)
  每日一次（凌晨低负载）：数据汇总 + 云端同步 (~5W, 30min)
  每周一次（电量>80%时）：模型更新下载 (~10W, 1h)
  
年均功耗：~5W → 每日 120Wh
太阳能日均发电（华东地区）：300W × 4h 等效 = 1200Wh
电池可支撑无日照天数：1200Wh / 120Wh ≈ 10 天
```

## 7. 实践建议

### 7.1 初学者入门路径

**第一步：测量先行**。在你的边缘设备上安装 `powerstat`（x86）或用 `tegrastats`（Jetson）测量实际功耗。不了解基线就无法优化。

```bash
# x86 Linux 功耗测量
sudo apt install powerstat
sudo powerstat -d 0 1 60  # 每秒采样，持续 60 秒

# Jetson 设备
tegrastats --interval 1000  # 每秒输出功耗和温度
```

**第二步：尝试 DVFS**。在边缘设备上切换不同的 CPU 频率策略，观察功耗和性能的 trade-off。

**第三步：集成碳强度 API**。用 Electricity Maps 的免费 API 获取你所在地区的实时碳强度，写一个简单的脚本，在碳强度低于阈值时触发批处理任务。

**第四步：搭建监控仪表盘**。用 Prometheus + Grafana 展示功耗、温度、碳排放的实时仪表盘，作为绿色调度决策的基础。

### 7.2 具体调优建议

**从延迟不敏感的任务开始**。模型更新、日志归档、数据同步——这些任务延迟几小时不影响业务。先对它们做碳感知调度，风险最小、收益明确。

**不要在所有场景推碳优化**。实时推理、告警处理、安全监控这些任务绝不能因为碳优化而延迟。分清"可延迟"和"不可延迟"是第一步。

**GPU 功耗限制是最高性价比的优化**。`nvidia-smi -pl` 一条命令就能减少 30% 功耗，性能下降通常只有 15-20%。对于推理场景（往往不是 GPU bound），实际性能影响更小。

**电池系统要考虑深度放电保护**。锂电池深度放电会严重影响寿命。SoC（State of Charge）低于 20% 就应该停止非关键任务，低于 10% 只保留最基本的传感器采集和告警。

## 参考文献

1. Google. (2024). 24/7 Carbon-Free Energy: Methodology and Results. https://sustainability.google/operating-sustainably/
2. Microsoft. (2024). Carbon Aware SDK. https://github.com/Green-Software-Foundation/carbon-aware-sdk
3. Electricity Maps. (2024). Real-time Carbon Intensity API. https://www.electricitymaps.com/
4. Green Software Foundation. (2024). Software Carbon Intensity (SCI) Specification. https://sci.greensoftware.foundation/
5. WattTime. (2024). Marginal Emissions API Documentation. https://www.watttime.org/
6. Radovanovic, A., et al. (2022). Carbon-Aware Computing for Datacenters. IEEE Transactions on Power Systems, 38(2), 1623-1634.
7. IEA. (2024). Data Centres and Data Transmission Networks. https://www.iea.org/energy-system/buildings/data-centres-and-data-transmission-networks
8. NVIDIA. (2024). Jetson Power Management Guide. https://docs.nvidia.com/jetson/
9. Acun, B., et al. (2023). Carbon Explorer: A Holistic Framework for Designing Carbon Aware Datacenters. ACM ASPLOS.
10. Li, B., et al. (2024). Sustainable Edge Computing: A Survey on Energy-Efficient and Carbon-Aware Approaches. ACM Computing Surveys, 56(8), 1-42.
