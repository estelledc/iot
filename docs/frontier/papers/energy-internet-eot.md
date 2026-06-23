# 能量互联网（Energy Internet/EoT）：能源的 IoT 化转型

> **难度**：🟡 中级 | **领域**：智能电网、分布式能源、能源交易 | **阅读时间**：约 25 分钟

## 日常类比

想象互联网出现之前的电话系统——只能打电话，从电话局单向连到你家。现在的互联网呢？任何人可以既消费内容也生产内容（自媒体），信息双向甚至多向流动。能量互联网就是把电力系统从"单向电话"变成"双向互联网"——你家屋顶的光伏板可以发电卖给邻居，你的电动车电池可以在电价高时"反向卖电"给电网。

再想想快递物流网络。传统电网是"中央大工厂生产，单向配送到家"。能量互联网是"人人都是生产者+消费者（prosumer），能源像快递包裹一样在网络中智能路由"。IoT 在其中扮演的角色就是"物流追踪系统"——实时知道每个节点的发电量、用电量、储能余量，从而做出最优的能源调度决策。

## 1. 能量互联网架构

### 1.1 核心概念

| 概念 | 传统电网 | 能量互联网 |
|------|---------|-----------|
| 能源流向 | 单向（电厂到用户） | 双向（任意节点互通） |
| 参与角色 | 生产者/消费者分离 | Prosumer（产消合一） |
| 调度方式 | 中心化调度 | 分布式自治 + 协调 |
| 信息感知 | 有限 SCADA | 全网 IoT 实时感知 |
| 交易模式 | 统购统销 | P2P 市场化交易 |
| 储能 | 集中式抽蓄 | 分布式电池 + V2G |
| 韧性 | 集中故障影响大 | 微网独立运行 |

### 1.2 分层架构

```
能量互联网分层模型：

+-----------------------------------------------+
| 应用层 | 能源交易平台、需求响应、碳管理          |
+-----------------------------------------------+
| 平台层 | 能源路由器、优化调度、数字孪生          |
+-----------------------------------------------+
| 网络层 | 通信网（5G/LoRa/PLC）、区块链           |
+-----------------------------------------------+
| 感知层 | 智能电表、传感器、PMU、气象站            |
+-----------------------------------------------+
| 物理层 | 光伏/风电/储能/微网/EV/负荷             |
+-----------------------------------------------+
```

## 2. IoT 赋能智能电网

### 2.1 分布式能源资源（DER）管理

```python
class DistributedEnergyResource:
    """分布式能源资源节点"""
    
    def __init__(self, resource_type, capacity_kw, location):
        self.type = resource_type  # solar, wind, battery, ev
        self.capacity = capacity_kw
        self.location = location
        self.iot_sensors = []
        self.current_output = 0
    
    def get_status(self):
        """IoT 传感器实时状态上报"""
        if self.type == 'solar':
            return {
                'output_kw': self.current_output,
                'panel_temp_c': read_sensor('temperature'),
                'irradiance_w_m2': read_sensor('pyranometer'),
                'efficiency_pct': self.current_output / (self.capacity + 0.01) * 100,
                'dust_level': read_sensor('soiling'),
                'inverter_status': read_sensor('inverter'),
                'forecast_next_hour': self.predict_output(horizon=1)
            }
        elif self.type == 'battery':
            return {
                'soc_pct': read_sensor('state_of_charge'),
                'power_kw': self.current_output,  # 正=放电，负=充电
                'temperature_c': read_sensor('battery_temp'),
                'health_pct': read_sensor('state_of_health'),
                'cycles': read_sensor('cycle_count'),
                'available_capacity_kwh': self.get_available_energy()
            }
    
    def predict_output(self, horizon=1):
        """短期发电预测（结合气象IoT数据）"""
        weather = get_weather_forecast(self.location, hours=horizon)
        model_input = {
            'irradiance_forecast': weather['ghi'],
            'temperature_forecast': weather['temp'],
            'cloud_cover': weather['clouds'],
            'historical_pattern': self.get_historical(days=7)
        }
        return solar_forecast_model.predict(model_input)
```

### 2.2 IoT 传感器部署

| 监测对象 | 传感器类型 | 通信方式 | 采集频率 | 数据量/天 |
|----------|-----------|---------|---------|----------|
| 智能电表 | 电流/电压/功率 | PLC/RF Mesh | 15 min | 1-5 MB |
| 光伏板 | 辐照/温度/电流 | LoRa/NB-IoT | 1 min | 10-50 MB |
| 储能电池 | SOC/温度/电压 | WiFi/BLE | 10 s | 50-200 MB |
| 配变 | 油温/负载/气体 | 4G/5G | 1 min | 5-20 MB |
| 电动车桩 | 充电功率/SOC | 4G/WiFi | 实时 | 10-100 MB |
| 气象站 | 风速/辐照/温度 | LoRa | 5 min | 2-5 MB |

## 3. 能源路由与微网

### 3.1 能源路由器

```python
class EnergyRouter:
    """能源路由器：能量互联网的核心设备"""
    
    def __init__(self, node_id, connected_ders, connected_loads):
        self.id = node_id
        self.ders = connected_ders     # 连接的分布式电源
        self.loads = connected_loads    # 连接的负荷
        self.neighbors = []            # 相邻能源路由器
        self.routing_table = {}
    
    def balance_power(self):
        """本地功率平衡"""
        total_generation = sum(der.current_output for der in self.ders)
        total_demand = sum(load.current_demand for load in self.loads)
        surplus = total_generation - total_demand
        
        if surplus > 0:
            # 发电多余：存储或卖给邻居
            self.store_or_export(surplus)
        else:
            # 发电不足：从储能取或从邻居买
            self.discharge_or_import(abs(surplus))
    
    def route_energy(self, amount_kw, destination):
        """能源路由（类比数据包路由）"""
        # 最短路径/最低损耗/最低成本 路由算法
        path = self.find_optimal_path(destination)
        for hop in path:
            hop.forward_energy(amount_kw)
        return path
    
    def participate_market(self, surplus_kw, min_price):
        """参与 P2P 能源交易市场"""
        offer = {
            'seller': self.id,
            'amount_kw': surplus_kw,
            'min_price_per_kwh': min_price,
            'available_duration_min': 60,
            'location': self.location,
            'carbon_intensity': self.get_carbon_intensity()
        }
        return market.submit_offer(offer)
```

### 3.2 微网独立运行

```
微网运行模式：

并网模式（正常）：
  微网 <--> 大电网（自由购售电）

孤岛模式（故障/主动）：
  微网 [独立运行]，自发自用，储能平衡

切换条件：
- 大电网故障 -> 自动切换孤岛（<100ms）
- 电价过高 -> 主动脱网省钱
- 绿电自给 -> 主动脱网减碳

IoT 在微网中的角色：
- 实时监测所有 DER 和负荷状态
- 预测未来 24h 发电和用电曲线
- 优化充放电策略
- 检测异常并保护设备
```

## 4. P2P 能源交易

### 4.1 区块链 + IoT 能源交易

```python
class P2PEnergyMarket:
    """基于区块链的点对点能源交易平台"""
    
    def __init__(self):
        self.order_book = []      # 挂单簿
        self.completed_trades = []
        self.smart_contracts = {}
    
    def create_sell_order(self, prosumer_id, amount_kwh, price, time_slot):
        """卖方挂单（光伏/储能有余电时）"""
        order = {
            'type': 'sell',
            'prosumer': prosumer_id,
            'amount_kwh': amount_kwh,
            'price_per_kwh': price,       # 元/kWh
            'time_slot': time_slot,        # 供电时段
            'green_certificate': True,     # 绿电认证
            'verified_by_iot': True        # IoT 智能电表验证
        }
        self.order_book.append(order)
        return order
    
    def match_orders(self):
        """撮合交易"""
        sells = sorted([o for o in self.order_book if o['type'] == 'sell'],
                      key=lambda x: x['price_per_kwh'])
        buys = sorted([o for o in self.order_book if o['type'] == 'buy'],
                     key=lambda x: -x['price_per_kwh'])
        
        trades = []
        for buy in buys:
            for sell in sells:
                if sell['price_per_kwh'] <= buy['price_per_kwh']:
                    trade = self.execute_trade(buy, sell)
                    trades.append(trade)
                    break
        return trades
    
    def settle_with_iot(self, trade):
        """IoT 智能电表结算验证"""
        # 1. 读取卖方电表实际输出
        actual_sold = read_smart_meter(trade['seller'], trade['time_slot'])
        # 2. 读取买方电表实际消费
        actual_bought = read_smart_meter(trade['buyer'], trade['time_slot'])
        # 3. 比对并结算
        if abs(actual_sold - trade['amount_kwh']) < 0.1:
            execute_payment(trade)  # 区块链自动转账
```

### 4.2 典型交易场景

| 场景 | 卖方 | 买方 | IoT 作用 | 区块链作用 |
|------|------|------|---------|-----------|
| 邻里共享 | 屋顶光伏 | 邻居家 | 电表计量 | 信任+结算 |
| V2G 卖电 | 电动车 | 电网 | SOC 监测 | 自动触发 |
| 虚拟电厂 | DER 聚合 | 大用户 | 协调调度 | 收益分配 |
| 碳交易 | 绿电生产 | 碳排企业 | 发电认证 | 碳证追溯 |

## 5. 车联网与 V2G

### 5.1 Vehicle-to-Grid 系统

```python
class V2GManager:
    """车网互动管理系统"""
    
    def __init__(self):
        self.connected_evs = {}
        self.grid_signal = None
    
    def register_ev(self, ev_id, battery_capacity, current_soc, 
                    departure_time, target_soc):
        """电动车接入登记"""
        self.connected_evs[ev_id] = {
            'capacity_kwh': battery_capacity,
            'soc': current_soc,
            'departure': departure_time,
            'target_soc': target_soc,
            'available_for_v2g': current_soc > target_soc + 0.1
        }
    
    def optimize_charging_schedule(self, ev_id, electricity_prices):
        """优化充放电时间表"""
        ev = self.connected_evs[ev_id]
        schedule = []
        
        # 找电价最低时段充电
        sorted_slots = sorted(enumerate(electricity_prices), key=lambda x: x[1])
        energy_needed = (ev['target_soc'] - ev['soc']) * ev['capacity_kwh']
        
        for slot_idx, price in sorted_slots:
            if energy_needed <= 0:
                break
            charge_amount = min(7, energy_needed)  # 7kW 充电桩
            schedule.append({'slot': slot_idx, 'action': 'charge', 'kw': charge_amount})
            energy_needed -= charge_amount
        
        # 电价高时段放电（V2G）
        if ev['available_for_v2g']:
            expensive_slots = sorted_slots[-3:]  # 最贵的 3 个时段
            for slot_idx, price in expensive_slots:
                schedule.append({'slot': slot_idx, 'action': 'discharge', 'kw': 5})
        
        return schedule
```

### 5.2 V2G 经济性

```
V2G 经济账（一辆60kWh电动车）：

每日可参与 V2G 的电量：约 10-20 kWh（保留足够行驶里程）
峰谷电价差：约 0.5-1.0 元/kWh
电池退化成本：约 0.1-0.2 元/kWh（循环次数折算）
净收益：约 0.3-0.8 元/kWh

每月额外收入：
- 保守估计：10 kWh/天 * 0.3 元 * 30 天 = 90 元/月
- 乐观估计：20 kWh/天 * 0.8 元 * 30 天 = 480 元/月

规模效应：
- 一个小区 200 辆 EV = 12 MWh 虚拟电厂
- 相当于 3-4 台风力发电机的储能配套
```

## 6. 需求响应与 IoT

### 6.1 IoT 驱动的需求响应

| 响应级别 | 响应时间 | IoT 设备 | 动作 | 用户感知 |
|----------|---------|---------|------|---------|
| 紧急 | 秒级 | 空调/热水器 | 短时关停 | 几乎无感 |
| 快速 | 分钟级 | 充电桩/储能 | 降功率/放电 | 充电变慢 |
| 常规 | 15 分钟 | 工业负荷 | 错峰生产 | 计划调整 |
| 日前 | 小时级 | 综合负荷 | 用电计划优化 | 提前安排 |

### 6.2 智能家居需求响应

```python
class SmartHomeEnergyAgent:
    """智能家居能源代理"""
    
    def __init__(self, home_devices):
        self.devices = home_devices
        self.comfort_preferences = {}
        self.flexibility_score = {}
    
    def respond_to_signal(self, grid_signal):
        """响应电网调度信号"""
        if grid_signal['type'] == 'peak_reduction':
            # 削峰请求：降低非必要负荷
            actions = []
            
            # 空调温度上调 2 度（最大灵活性来源）
            if self.devices['ac'].is_running:
                actions.append(('ac', 'set_temp', self.devices['ac'].temp + 2))
            
            # 热水器延后加热
            if self.devices['water_heater'].is_running:
                actions.append(('water_heater', 'defer', 30))  # 延后 30 分钟
            
            # EV 暂停充电或反向放电
            if self.devices['ev_charger'].is_charging:
                actions.append(('ev_charger', 'pause', None))
            
            return actions
```

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一周**：了解电力系统基础（发输配用），理解为什么需要能量互联网
2. **第二周**：学习智能电表和 MQTT/DLMS 协议，搭建简单能源数据采集系统
3. **第三周**：研究微网能量管理（EMS），用 Python 实现简单的发电-负荷平衡优化
4. **第四周**：了解 P2P 能源交易和 V2G 概念，阅读 Power Ledger/LO3 Energy 案例
5. **进阶**：学习电力市场机制、碳交易体系、虚拟电厂（VPP）聚合技术

### 7.2 具体调优建议

- **数据采集频率**：电池储能 10s，光伏 1min，电表 15min——按控制需求匹配
- **预测精度**：光伏预测误差 <15% 才能有效参与电力市场，结合多源气象数据
- **通信冗余**：能源关键基础设施必须双链路（如 4G + PLC），保证可控可观
- **安全隔离**：IT（信息网）和 OT（运行网）严格隔离，IoT 网关做安全边界
- **经济性评估**：V2G 参与前评估电池退化成本，保证净收益为正
- **标准遵循**：IEC 61850（变电站）、IEEE 2030.5（DER 互联）、OCPP（充电桩）

## 参考文献

1. Rifkin, J. (2011). The Third Industrial Revolution: How Lateral Power Is Transforming Energy, the Economy, and the World.
2. Huang, A. Q., et al. (2011). The Future Renewable Electric Energy Delivery and Management (FREEDM) System. Proceedings of the IEEE.
3. Tushar, W., et al. (2021). Peer-to-Peer Energy Systems for Connected Communities: A Review of Recent Advances and Emerging Challenges. Applied Energy.
4. IEA. (2023). Global EV Outlook 2023: Electric Vehicle - Grid Integration.
5. Mengelkamp, E., et al. (2018). Designing Microgrid Energy Markets: A Case Study: The Brooklyn Microgrid. Applied Energy.
6. Zhou, K., et al. (2016). Smart Home Energy Management Systems: A Survey. Renewable and Sustainable Energy Reviews.
7. Palensky, P., & Dietrich, D. (2011). Demand Side Management: Demand Response, Intelligent Energy Systems, and Smart Loads. IEEE Transactions on Industrial Informatics.
8. Khorasany, M., et al. (2020). Market Framework for Local Energy Trading: A Review of Opportunities, Challenges, and Research Directions. Renewable and Sustainable Energy Reviews.
9. Kempton, W., & Tomic, J. (2005). Vehicle-to-Grid Power Fundamentals. Journal of Power Sources.
10. Li, D., et al. (2023). Energy Internet: Concept, Architecture and Frontier Outlook. Automation of Electric Power Systems.
