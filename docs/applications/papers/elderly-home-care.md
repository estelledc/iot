---
schema_version: '1.0'
id: elderly-home-care
title: 老年人居家看护物联网
layer: 7
content_type: UNKNOWN
difficulty: intermediate
reading_time: 25
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 老年人居家看护物联网

> **难度**：🟡 中级 | **领域**：民生与健康、智慧养老 | **阅读时间**：约 25 分钟

## 日常类比

想象你的父母独自住在老家。你每天打电话问"吃饭了没""睡得好不好"，但一天只有几分钟的沟通窗口，中间发生了什么你完全不知道。如果老人半夜起来上厕所摔了一跤，可能要等到第二天你打电话才知道——这几个小时的空窗期可能就是生与死的差距。

老年人居家看护物联网要做的事情，就是把"每天打一个电话"升级成"24 小时贴身管家"——但这个管家不是真的站在旁边盯着（那样老人也不舒服），而是通过分布在家里各处的传感器，"听"动静、"看"活动、"量"体征，在不打扰日常生活的前提下判断"一切正常"还是"需要干预"。一旦发现异常——跌倒、长时间不活动、心率突变——系统立刻通知家人或急救中心。

这套系统的核心挑战不是技术本身有多难（传感器、算法都是成熟的），而是如何平衡"安全"和"隐私"。老人不喜欢被摄像头盯着，也不愿意戴一堆设备。好的解决方案是"无感知"的——你几乎忘记它的存在，但它一直在默默工作。

## 1 为什么居家看护是刚需

### 1.1 老龄化的数字现实

中国 65 岁以上人口已超过 2.17 亿（2024 年统计），其中超过 4,000 万独居或空巢老人。全球范围内，WHO 统计 60 岁以上人口将在 2050 年达到 21 亿。

跌倒是老年人意外伤害的首要原因：全球每年约 68.4 万人死于跌倒，其中 80% 是 65 岁以上老人。更关键的是跌倒后的"黄金救援时间"——如果老人跌倒后 1 小时内得到救治，死亡率降低 80%。但独居老人跌倒后平均被发现时间超过 12 小时。

### 1.2 传统方案的局限

| 方案 | 覆盖率 | 局限 |
|------|--------|------|
| 家人同住 | 高 | 年轻人工作压力大，空间不够 |
| 养老院 | 中 | 费用高，老人抗拒离家 |
| 保姆 | 中 | 人力成本持续上涨，服务质量不一 |
| 紧急呼叫按钮 | 低 | 需要老人主动按下，昏迷/瘫痪时无效 |
| 定期电话回访 | 低 | 只覆盖通话时段 |

物联网方案的核心优势：**被动监测**——不需要老人做任何操作，系统自动感知、自动判断、自动报警。

## 2 跌倒检测技术

### 2.1 基于加速度计的穿戴式检测

最成熟的方案是在腰部或手腕佩戴一个含三轴加速度计 + 三轴陀螺仪的设备（如手环、吊坠）。跌倒过程有一个标志性信号模式：

1. **自由落体阶段**：加速度突然接近 0g（约 200-500ms）
2. **撞击阶段**：加速度出现尖峰（通常 > 3g，严重跌倒可达 6-8g）
3. **静止阶段**：撞击后加速度回到 1g 附近，但姿态发生变化（从直立变为水平）

传统阈值算法用"合成加速度 > 阈值"来判断，但误报率高——拍桌子、坐沙发动作也可能触发。现在主流做法是用 ML 模型：

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# 从 6 轴 IMU 数据中提取特征
def extract_features(window):
    """
    window: shape (N, 6) — [ax, ay, az, gx, gy, gz]
    N = 采样点数 (e.g., 50Hz * 2s = 100)
    """
    acc = window[:, :3]
    gyro = window[:, 3:]
    
    acc_mag = np.linalg.norm(acc, axis=1)  # 合成加速度
    
    features = {
        'acc_mag_max': acc_mag.max(),
        'acc_mag_min': acc_mag.min(),
        'acc_mag_std': acc_mag.std(),
        'acc_mag_range': acc_mag.max() - acc_mag.min(),
        'gyro_mag_max': np.linalg.norm(gyro, axis=1).max(),
        'sma': np.sum(np.abs(acc)) / len(acc),  # 信号幅度面积
        'post_impact_angle': np.arccos(
            acc[-1, 2] / np.linalg.norm(acc[-1])
        ) * 180 / np.pi,  # 撞击后身体角度
    }
    return features

# 训练：用 SisFall / MobiAct 公开数据集
# 典型准确率：Random Forest 95-97%, LSTM 97-99%
```

### 2.2 非穿戴式跌倒检测

很多老人不愿意戴手环（忘记充电、觉得丑、洗澡要摘），所以非穿戴方案是重要补充：

**毫米波雷达**（如 TI IWR6843）：发射 60-64GHz 毫米波，通过反射信号的多普勒频移和距离变化检测人体动作。可以穿透衣物，不受光线影响，不采集图像所以隐私友好。Vayyar 的 Walabot HOME 产品用这个方案，检测范围约 7 米。

**环境传感器融合**：PIR（被动红外）+ 振动传感器 + 声音传感器组合。PIR 检测有无活动，振动传感器检测地板冲击（跌倒撞地），声音传感器检测异常声响（喊叫、碰撞声）。三者融合的准确率约 90-93%。

| 方案 | 准确率 | 隐私性 | 佩戴要求 | 成本 |
|------|--------|--------|----------|------|
| 加速度计手环 | 95-99% | 高 | 需要佩戴 | 200-500 元 |
| 毫米波雷达 | 92-96% | 高 | 无 | 800-2000 元 |
| 摄像头 + AI | 97-99% | 低 | 无 | 300-800 元 |
| 环境传感器融合 | 88-93% | 高 | 无 | 500-1000 元 |

## 3 日常活动识别（ADL）

### 3.1 为什么 ADL 很重要

ADL（Activities of Daily Living）是评估老人自理能力的医学标准，包括 6 项基本活动：进食、穿衣、洗浴、如厕、移动、保持个人卫生。老人如果某一项 ADL 出现退化（比如开始不按时吃饭、不出卧室），往往预示着健康问题。

传统评估靠护理人员定期上门打分，频率低且主观。IoT 方案可以实现连续自动评估。

### 3.2 传感器部署方案

```
厨房: 水流传感器(水龙头) + 柜门传感器 + 电器功率计(微波炉/电饭煲)
卧室: 床压传感器 + PIR + 光照传感器
浴室: 水流传感器 + 门磁传感器 + 温湿度传感器
客厅: PIR + 沙发压力传感器 + 电视功率计
大门: 门磁传感器 + 智能门锁
药箱: 开合传感器 + 重量传感器
```

通过这些传感器的时序组合，可以推断出日常活动模式：

- 早上 7:00 起床（床压传感器释放）→ 去卫生间（PIR 触发）→ 刷牙洗脸（水流持续 3-5 分钟）→ 去厨房做早餐（电饭煲通电）
- 如果某天早上 10:00 还没离开床，或者连续 3 天没用过厨房，系统标记为异常

### 3.3 模式异常检测

```python
from datetime import datetime, timedelta

class ADLMonitor:
    def __init__(self):
        self.baseline = {}  # 学习 2 周建立基线
        self.alert_thresholds = {
            'wake_up_delay': timedelta(hours=2),     # 比平常晚起 2 小时
            'no_kitchen_days': 2,                     # 连续 2 天没进厨房
            'bathroom_too_long': timedelta(minutes=45), # 卫生间待超过 45 分钟
            'no_movement_hours': 4,                   # 白天连续 4 小时无活动
        }
    
    def check_anomaly(self, today_events):
        alerts = []
        
        # 检查起床时间
        wake_time = self._get_wake_time(today_events)
        if wake_time and self.baseline.get('avg_wake_time'):
            delay = wake_time - self.baseline['avg_wake_time']
            if delay > self.alert_thresholds['wake_up_delay']:
                alerts.append({
                    'type': 'late_wake',
                    'severity': 'medium',
                    'message': f'比平常晚起 {delay}',
                })
        
        # 检查白天活动间隔
        gaps = self._find_inactivity_gaps(today_events)
        for gap in gaps:
            if gap['duration'] > self.alert_thresholds['no_movement_hours']:
                alerts.append({
                    'type': 'prolonged_inactivity',
                    'severity': 'high',
                    'message': f'{gap["start"]}~{gap["end"]} 无活动',
                })
        
        return alerts
```

## 4 生命体征非侵入式监测

### 4.1 无感知生理指标采集

目标是在老人完全无感知的情况下持续监测核心生理指标：

**睡眠期间**：床垫下放置压电薄膜传感器（如 Emfit QS），通过体表微振动提取：心率（BCG 心冲击图，精度 ±2 bpm）、呼吸率（±1 次/分钟）、睡眠分期（浅睡/深睡/REM）、离床事件。

**日间静坐**：椅子/沙发内嵌压力传感器阵列，提取心率和坐姿。或者用毫米波雷达（非接触式），在 1-2 米距离内提取呼吸率和心率。

**厕所**：智能马桶盖（如日本 TOTO 的 Flowsky 产品原型）可以分析尿液成分，监测血糖代理指标和泌尿系统健康。

### 4.2 异常预警逻辑

```python
class VitalSignsAlert:
    THRESHOLDS = {
        'heart_rate': {'low': 50, 'high': 120, 'unit': 'bpm'},
        'resp_rate': {'low': 10, 'high': 25, 'unit': '次/min'},
        'spo2': {'low': 90, 'high': 100, 'unit': '%'},
        'hr_variability_drop': 30,  # HRV 下降超过 30% 预警
    }
    
    def evaluate(self, vitals, baseline):
        risk_score = 0
        
        if vitals['heart_rate'] > self.THRESHOLDS['heart_rate']['high']:
            risk_score += 3  # 心动过速
        if vitals['heart_rate'] < self.THRESHOLDS['heart_rate']['low']:
            risk_score += 4  # 心动过缓更危险
        
        # HRV 趋势分析 —— 连续 3 天 HRV 下降可能预示感染
        hrv_change = (vitals['hrv'] - baseline['hrv_7day_avg']) / baseline['hrv_7day_avg']
        if hrv_change < -0.3:
            risk_score += 2
        
        # risk_score >= 5 自动通知家属
        # risk_score >= 8 自动拨打 120
        return risk_score
```

## 5 用药提醒与依从性追踪

### 5.1 系统架构

老年人常见多重用药（平均每人 5-8 种药），漏服或重复服药都是严重问题。WHO 统计老年人用药依从率只有约 50%。

智能药盒方案：每个药格装有微型称重传感器 + LED 指示灯 + 蜂鸣器。到服药时间，对应药格 LED 闪烁 + 蜂鸣提醒。老人取出药物后，重量变化确认已取药。如果 30 分钟未取药，通知家属。如果同一药格短时间内被打开两次（可能重复服药），立即报警。

### 5.2 通信链路

```
药盒(BLE) → 床头网关(WiFi) → 云端
                                 ↓
                           家属 APP 推送
                                 ↓
                        未响应 → 拨打老人电话
                                 ↓
                        仍未响应 → 通知社区工作者
```

## 6 隐私保护与系统设计

### 6.1 隐私分级框架

居家看护最大的非技术障碍是隐私。很多老人和家属对"被监控"有强烈抵触情绪。需要建立分级框架：

| 隐私等级 | 传感器类型 | 采集的信息 | 用户接受度 |
|----------|-----------|-----------|-----------|
| L1 低侵入 | 门磁、PIR、功率计 | 只知道"有活动" | 高（>90%） |
| L2 中等 | 加速度计、雷达 | 知道"在做什么" | 中（60-80%） |
| L3 高侵入 | 摄像头、麦克风 | 看到/听到具体内容 | 低（<30%） |

设计原则：**能用 L1 就不用 L2，能用 L2 就不用 L3**。

### 6.2 边缘计算保隐私

即使使用摄像头，也可以通过边缘 AI 保护隐私——原始视频在本地处理，只上传分析结果：

```python
# 边缘设备上运行（如 Jetson Nano）
import cv2

def process_frame_locally(frame):
    """
    原始视频帧绝不离开本地设备
    只上传结构化结果
    """
    # 姿态检测（骨架提取）
    skeleton = pose_model.detect(frame)
    
    # 跌倒判断（基于骨架而非原始图像）
    is_fallen = fall_detector.predict(skeleton)
    
    # 上传的只有：时间戳 + 是否跌倒 + 骨架坐标
    # 没有任何原始图像
    result = {
        'timestamp': time.time(),
        'fallen': is_fallen,
        'skeleton': skeleton.tolist(),  # 只有关节点坐标
    }
    return result
```

## 7 商用系统与实践建议

### 7.1 主流商用产品对比

| 产品 | 核心技术 | 特点 | 价格区间 |
|------|----------|------|----------|
| CarePredict Tempo | 腕带+BLE信标 | ADL 自动识别，抑郁检测 | $500+/月（机构） |
| Vayyar Home | 毫米波雷达 | 无穿戴跌倒检测，安装即用 | $300 一次性 |
| Lively (GreatCall) | 紧急按钮+活动传感器 | 简单易用，老人接受度高 | $25/月 |
| Apple Watch Ultra | IMU+心率+血氧 | 跌倒检测+ECG+SOS | 约 5,999 元 |
| 华为穿戴设备 | IMU+心率+血氧 | 中文生态好，价格合理 | 1,000-2,500 元 |

### 7.2 初学者入门路径

1. **第一步**：用 Arduino Nano + MPU6050（加速度计/陀螺仪）做一个最简跌倒检测原型，阈值算法即可
2. **第二步**：加入 BLE 通信（ESP32），把数据发到手机 APP
3. **第三步**：收集真实数据（让家人模拟日常活动 + 跌倒），训练 ML 模型替代阈值
4. **第四步**：增加环境传感器（门磁、PIR），实现简单的 ADL 识别
5. **进阶**：尝试毫米波雷达方案（TI IWR6843 评估板），对比穿戴 vs 非穿戴方案的优劣

### 7.3 部署调优建议

**传感器布局**：PIR 传感器避免对着窗户（阳光直射会误触发），门磁传感器用 3M 胶粘贴（不破坏装修），床压传感器放在床垫下方（完全无感知）。

**告警策略**：不要一有异常就报警，设置分级延迟——轻度异常（起床晚了 1 小时）等 30 分钟再通知；中度异常（4 小时无活动）立即通知家属；重度异常（跌倒检测触发）直接拨打 120 + 通知家属。告警疲劳是系统失败的主因——如果每天都收到 5 条"误报"，家属很快就会关掉通知。

**数据基线**：系统需要至少 2 周的"学习期"来建立个人基线。每个老人的作息不同，不能用统一标准。

**电源方案**：门磁/PIR 用纽扣电池可以撑 1-2 年；加速度计手环每周充一次；床压传感器用 USB 供电。尽量减少需要老人操心充电的设备。

## 参考文献

1. WHO. Falls - Key Facts. World Health Organization, 2024.
2. Mauldin T, Canby M, et al. SmartFall: A Smartwatch-Based Fall Detection System Using Deep Learning. Sensors, 2018, 18(10): 3363.
3. Vayyar. Walabot HOME Fall Detection Technology White Paper. 2023.
4. CarePredict. Tempo AI-Powered Senior Care Platform Technical Overview. 2024.
5. Kaye J, et al. Intelligent Systems for Assessing Aging Changes (ISAAC). IEEE Pervasive Computing, 2011.
6. Rashidi P, Mihailidis A. A Survey on Ambient-Assisted Living Tools for Older Adults. IEEE JBHI, 2013, 17(3): 579-590.
7. Apple. Fall Detection and Emergency SOS on Apple Watch. Apple Support, 2024.
8. Texas Instruments. IWR6843 Single-Chip mmWave Sensor for Vital Signs Monitoring. Application Note, 2023.
9. Patel S, et al. A Review of Wearable Sensors and Systems for Monitoring and Detection of Falls. Biomedical Engineering Online, 2012, 11: 27.
10. 国家统计局. 第七次全国人口普查主要数据. 2024 年更新.
