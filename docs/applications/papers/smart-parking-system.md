# 智慧停车系统

> **难度**：🟡 中级 | **领域**：智慧城市、交通管理 | **阅读时间**：约 25 分钟

## 日常类比

周末带家人去商场，在停车场里绕了 20 分钟才找到一个空位——这种经历每个开车的人都有。IBM 2024 年的一项研究发现，城市中约 30% 的交通拥堵是由"找车位"造成的。司机平均每次停车要花 8 分钟寻找空位，每年因此浪费的燃油价值约 $345。

智慧停车系统要做的事情很直观：把每个车位的"空/满"状态实时告诉你——还没到停车场就知道哪层哪个区域有空位，APP 直接导航到最近的空车位。更进一步，系统还能预测未来半小时的空位数（帮你决定要不要先去下一个目的地），甚至根据供需关系做动态定价（闹市区高峰期贵一点，引导车辆分流到周边停车场）。

从技术角度看，这个系统看似简单，实际涉及传感器选型（地磁 vs 超声波 vs 摄像头）、低功耗通信（LoRa/NB-IoT）、后端大数据平台、前端 APP、支付系统等完整技术链条——是一个麻雀虽小五脏俱全的 IoT 项目。

## 1 车位检测技术

### 1.1 传感器方案对比

检测"这个车位有没有车"看起来简单，但每种传感器都有优缺点：

| 技术 | 原理 | 精度 | 安装方式 | 功耗 | 单位成本 | 最佳场景 |
|------|------|------|----------|------|----------|----------|
| 地磁传感器 | 检测车辆金属体对地球磁场的扰动 | 95-98% | 嵌入地面 | 极低 | 200-500 元 | 路侧停车 |
| 超声波传感器 | 测量车位上方到地面/车顶的距离 | 97-99% | 吊装车位上方 | 低 | 100-300 元 | 室内车库 |
| 红外对射 | 车辆阻断红外光束 | 90-95% | 车位两侧 | 低 | 150-400 元 | 通道计数 |
| 摄像头 + AI | 图像识别车辆和车位 | 98-99.5% | 高处俯拍 | 高 | 500-2000 元 | 大型停车场 |
| 毫米波雷达 | 检测反射信号 | 96-99% | 车位上方/侧面 | 中 | 300-800 元 | 室外/恶劣天气 |
| 地面压力传感器 | 检测车辆重量 | 99%+ | 嵌入地面 | 极低 | 500-1000 元 | 高精度场景 |

### 1.2 地磁传感器详解

地磁传感器是路侧停车最主流的方案。原理：地球磁场在任意一点有一个稳定的三维矢量（约 25-65 μT），当一辆含有大量铁磁材料的汽车停在传感器上方时，会使磁场矢量发生 5-20 μT 的偏移。传感器检测这个偏移量来判断有无车辆。

```python
import numpy as np

class MagneticParkingSensor:
    def __init__(self):
        self.baseline = None  # 无车时的磁场基线
        self.threshold = 5.0  # μT，判定阈值
    
    def calibrate(self, samples):
        """上电后采集 100 个无车样本建立基线"""
        self.baseline = np.mean(samples, axis=0)  # [Bx, By, Bz] 基线
        self.noise_std = np.std(samples, axis=0)
    
    def detect(self, reading):
        """
        reading: [Bx, By, Bz] 当前磁场矢量 (μT)
        返回: (occupied, confidence)
        """
        if self.baseline is None:
            return False, 0.0
        
        # 计算磁场变化量
        delta = reading - self.baseline
        magnitude = np.linalg.norm(delta)
        
        # 自适应阈值（考虑环境噪声）
        adaptive_threshold = max(
            self.threshold,
            3 * np.linalg.norm(self.noise_std)
        )
        
        occupied = magnitude > adaptive_threshold
        confidence = min(magnitude / (2 * adaptive_threshold), 1.0)
        
        return occupied, confidence
    
    def update_baseline(self, reading, alpha=0.001):
        """缓慢更新基线以适应温度/季节变化"""
        if not self.detect(reading)[0]:  # 只在无车时更新
            self.baseline = (1 - alpha) * self.baseline + alpha * reading
```

**部署注意事项**：地磁传感器要嵌入路面（钻一个直径 8cm、深 5cm 的孔），用环氧树脂密封。施工需要临时封路。传感器必须距离井盖、钢结构 > 2m，否则会有永久磁场干扰。温度变化会导致基线漂移（热退磁效应），需要自适应校准。

### 1.3 摄像头方案详解

一个摄像头可以同时覆盖 20-50 个车位（地磁传感器是一对一），性价比在大型停车场中更优。主流做法：

1. **车位标定**：安装时在画面中标注每个车位的四边形区域（ROI）
2. **车辆检测**：用 YOLOv8 或 SSD 检测画面中的车辆
3. **占位判断**：车辆 bounding box 与车位 ROI 的 IoU > 0.5 则判定为占用
4. **车牌识别（LPR）**：同时识别车牌号，实现"无感支付"和"反向寻车"

```python
# 摄像头方案的核心逻辑
from ultralytics import YOLO

class CameraParkingDetector:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        self.parking_rois = {}  # {spot_id: [(x1,y1), (x2,y2), ...]}
    
    def process_frame(self, frame):
        results = self.model(frame, classes=[2, 5, 7])  # car, bus, truck
        vehicles = results[0].boxes.xyxy.cpu().numpy()
        
        spot_status = {}
        for spot_id, roi in self.parking_rois.items():
            occupied = False
            for vbox in vehicles:
                iou = self._compute_iou(roi, vbox)
                if iou > 0.5:
                    occupied = True
                    break
            spot_status[spot_id] = occupied
        
        return spot_status
```

## 2 通信方案

### 2.1 路侧停车通信选型

路侧停车传感器分布在城市各条道路上，对通信方案要求：覆盖范围广（几公里）、功耗极低（电池寿命 > 5 年）、数据量小（每次几十字节的状态更新）。

| 技术 | 覆盖 | 功耗 | 月租 | 适用 |
|------|------|------|------|------|
| LoRaWAN | 2-5 km（城市） | 极低 | 0（自建网关） | 自建网络 |
| NB-IoT | 运营商覆盖 | 低 | 5-10 元 | 运营商网络 |
| Sigfox | 3-10 km | 极低 | $1/年 | 欧洲市场 |
| BLE Mesh | 100-300 m | 极低 | 0 | 小型停车场 |

中国市场 NB-IoT 是主流选择（三大运营商全覆盖），海外 LoRaWAN 更常见（免频谱费）。

### 2.2 数据上报策略

```c
// 地磁传感器的省电上报策略
// 不是定时上报, 而是状态变化时上报

void parking_sensor_main() {
    bool last_state = false;
    uint32_t last_report_time = 0;
    
    while (1) {
        bool current_state = detect_vehicle();
        uint32_t now = get_timestamp();
        
        // 状态变化时立即上报
        if (current_state != last_state) {
            send_report(current_state, PRIORITY_HIGH);
            last_state = current_state;
            last_report_time = now;
        }
        // 无变化也每 30 分钟心跳上报 (证明传感器还活着)
        else if (now - last_report_time > 1800) {
            send_report(current_state, PRIORITY_LOW);
            last_report_time = now;
        }
        
        // 状态稳定时可以降低检测频率
        if (now - last_report_time > 300) {
            sleep(10);    // 5 分钟无变化, 10 秒检测一次
        } else {
            sleep(1);     // 刚变化后, 1 秒检测一次 (防抖)
        }
    }
}
```

## 3 停车引导系统

### 3.1 室内引导架构

大型商场地下停车场的引导系统由三部分组成：

**入口引导屏**：显示每层剩余车位数（"B1：可用 38 位 / B2：可用 105 位 / B3：可用 212 位"），引导车辆直接去空位多的楼层。

**区域引导屏**：每个岔路口显示左/右/前方各有多少空位，用绿色/红色指示灯。

**车位指示灯**：每个车位上方一个 LED 灯——绿色=空、红色=满。司机远远就能看到哪里有绿灯。

### 3.2 寻车位路径规划

```python
import heapq

def find_nearest_spot(current_pos, empty_spots, graph):
    """
    用 Dijkstra 找到距离当前位置最近的空车位
    考虑的是驾驶距离(沿通道), 不是直线距离
    """
    distances = {node: float('inf') for node in graph}
    distances[current_pos] = 0
    pq = [(0, current_pos)]
    prev = {}
    
    while pq:
        dist, node = heapq.heappop(pq)
        if node in empty_spots:
            # 回溯路径
            path = []
            while node in prev:
                path.append(node)
                node = prev[node]
            path.append(current_pos)
            return path[::-1], dist
        
        for neighbor, weight in graph[node]:
            new_dist = dist + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(pq, (new_dist, neighbor))
    
    return None, float('inf')  # 没有空位
```

## 4 车位占用预测

### 4.1 为什么要预测

实时数据只能告诉你"现在有多少空位"，但你开车过去还要 10-20 分钟——等你到了可能已经满了。预测模型可以回答："20 分钟后这个停车场还有空位吗？"

### 4.2 预测模型

车位占用率有明显的时间规律：

- **日周期**：办公楼停车场周一到五早 9 点满、下午 6 点空；商场周末下午 2 点最满
- **周周期**：工作日 vs 周末模式完全不同
- **特殊事件**：节假日、促销活动、大型会议

```python
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

def build_occupancy_model(historical_data):
    """
    特征工程 + 梯度提升回归预测未来占用率
    historical_data: DataFrame with columns [timestamp, occupancy_rate]
    """
    df = historical_data.copy()
    
    # 时间特征
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['month'] = df['timestamp'].dt.month
    
    # 滞后特征 (当前占用率通常与近期高度相关)
    df['occ_lag_1h'] = df['occupancy_rate'].shift(6)    # 6个10分钟=1小时前
    df['occ_lag_24h'] = df['occupancy_rate'].shift(144)  # 24小时前
    df['occ_lag_7d'] = df['occupancy_rate'].shift(1008)  # 7天前
    
    # 滑动窗口统计
    df['occ_rolling_mean_2h'] = (
        df['occupancy_rate'].rolling(12).mean()
    )
    
    features = ['hour', 'day_of_week', 'is_weekend', 'month',
                'occ_lag_1h', 'occ_lag_24h', 'occ_lag_7d',
                'occ_rolling_mean_2h']
    
    df = df.dropna()
    X = df[features]
    y = df['occupancy_rate']
    
    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=5, learning_rate=0.1
    )
    model.fit(X, y)
    return model
```

典型预测精度：30 分钟预测 RMSE ≈ 5-8%（即预测 70% 占用率，实际在 62-78% 之间）。

## 5 动态定价

### 5.1 原理

旧金山的 SFpark 项目（2011-2013）是动态停车定价的经典案例。核心逻辑：

- 占用率 > 80%：下一周期涨价 $0.25/h（最高 $6/h）
- 占用率 60-80%：价格不变
- 占用率 < 60%：下一周期降价 $0.25/h（最低 $0.25/h）

效果：试点区域平均占用率从 83% 降到 66%（减少了"转圈找车位"现象），周边交通拥堵减少 8%，停车收入反而增加了 2%。

### 5.2 动态定价算法

```python
class DynamicPricingEngine:
    def __init__(self, base_price=10.0, min_price=2.0, max_price=30.0):
        self.base_price = base_price  # 元/小时
        self.min_price = min_price
        self.max_price = max_price
    
    def calculate_price(self, occupancy_rate, time_of_day, 
                        predicted_demand, nearby_prices):
        """
        综合考虑当前占用率、时段、预测需求、周边竞品价格
        """
        # 供需因子
        if occupancy_rate > 0.9:
            demand_factor = 2.0   # 接近满 → 高价引导分流
        elif occupancy_rate > 0.7:
            demand_factor = 1.3
        elif occupancy_rate > 0.4:
            demand_factor = 1.0
        else:
            demand_factor = 0.6   # 大量空位 → 低价吸引
        
        # 时段因子 (高峰时段溢价)
        peak_hours = {8: 1.2, 9: 1.5, 17: 1.5, 18: 1.3}
        time_factor = peak_hours.get(time_of_day, 1.0)
        
        # 竞品因子 (不能比周边贵太多)
        avg_nearby = sum(nearby_prices) / len(nearby_prices) if nearby_prices else self.base_price
        competitive_cap = avg_nearby * 1.3
        
        price = self.base_price * demand_factor * time_factor
        price = min(price, competitive_cap, self.max_price)
        price = max(price, self.min_price)
        
        return round(price, 1)
```

## 6 城市级部署

### 6.1 规模与挑战

以深圳为例：全市约 300 万个停车位，其中路侧约 18 万个。如果全部安装地磁传感器，硬件成本约 18 万 × 400 元 = 7,200 万元。加上网关、平台、安装维护，总投资约 1.5-2 亿元。

挑战不只是钱：施工期间的交通管制、传感器被碾压损坏（路侧环境恶劣，要求 IP68 防水 + 抗 20 吨碾压）、大量传感器的运维管理、不同停车场系统的数据互通。

### 6.2 数据平台架构

```
传感器层: 地磁/摄像头/超声波 (百万级设备)
    ↓ NB-IoT / LoRa / 有线
接入层: IoT 网关 + MQTT Broker (集群)
    ↓
平台层: 时序数据库(TDengine/InfluxDB) + 流计算(Flink)
    ↓
应用层: 停车引导 / 动态定价 / 城市交通管理 / 开放 API
    ↓
用户层: 手机 APP / 车载导航 / 微信小程序
```

## 7 实践建议

### 7.1 初学者入门路径

1. **最简原型**：用 ESP32 + HMC5883L 地磁传感器，检测桌面上放不放铁块，理解地磁检测原理
2. **通信接入**：加 LoRa 模块（SX1276），做一个"远程车位状态显示器"
3. **后端搭建**：用 EMQX（开源 MQTT Broker）+ InfluxDB + Grafana 搭建最简监控平台
4. **APP 开发**：用微信小程序做一个车位状态查看界面（调用后端 API）
5. **AI 进阶**：收集一周的数据，训练占用率预测模型，在小程序里展示"预计 XX 分钟后有空位"

### 7.2 具体调优建议

**传感器可靠性**：地磁传感器最容易出问题的是"基线漂移"——随着温度变化和传感器老化，无车时的磁场读数会缓慢变化，导致误判。解决方案是在凌晨 3-4 点（几乎没车的时段）自动重新校准基线。

**防误报**：送外卖的摩托车、推着购物车经过、装满铁制品的拖车——这些都可能触发短暂误判。加入时间滤波（持续检测到 > 30 秒才认定为"有车"）可以过滤 90% 的误报。

**车牌识别精度**：中国车牌识别准确率在白天可达 99%+，但夜间/雨天/车牌脏污时降至 90-95%。部署补光灯 + 多角度摄像头可以改善。

**数据同步延迟**：从传感器检测到车辆到 APP 上显示更新，端到端延迟应控制在 5 秒以内。否则用户看到"空位"赶过去发现已经被占了，体验极差。NB-IoT 的上报延迟约 2-5 秒，加上后端处理和推送，总延迟约 3-8 秒——基本可接受。

## 参考文献

1. Shoup D. The High Cost of Free Parking. APA Planners Press, 2011 (updated 2024).
2. SFpark. SFpark Pilot Project Evaluation. SFMTA, 2014.
3. Lin T, et al. A Survey on Internet of Things: Architecture, Enabling Technologies, Security and Privacy, and Applications. IEEE IoT Journal, 2017.
4. Dixit S, et al. Smart Parking System Using IoT: A Comprehensive Review. IEEE Access, 2023.
5. 中国停车行业发展白皮书. 中国城市公共交通协会, 2024.
6. Semtech. LoRa for Smart Parking: Application Note AN1200.58. 2023.
7. 中国移动 NB-IoT 智慧停车解决方案白皮书. 2024.
8. Fedchenkov P, et al. Parking Occupancy Prediction Using Machine Learning. Transportation Research Part C, 2023.
9. INRIX. 2024 Global Traffic Scorecard: Parking Pain Index. 2024.
10. 深圳市智慧停车信息平台建设技术规范. 深圳市交通运输局, 2023.
