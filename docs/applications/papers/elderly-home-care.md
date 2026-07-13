---
schema_version: '1.0'
id: elderly-home-care
title: 老年人居家看护物联网
layer: 7
content_type: technical_analysis
difficulty: intermediate
reading_time: 25
prerequisites:
  - wearable-sensors
  - mmwave-radar-sensing
tags:
  - 智慧养老
  - 跌倒检测
  - ADL
  - 毫米波雷达
  - 隐私保护
  - 边缘计算
  - 非侵入监测
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 老年人居家看护物联网

> **难度**：🟡 中级 | **领域**：民生与健康、智慧养老 | **阅读时间**：约 25 分钟

## 日常类比

想象父母独自住在老家。你每天打电话问"吃饭了没""睡得好不好"，但一天只有几分钟窗口，中间发生了什么你完全不知道。若老人半夜起夜摔倒，可能要等到第二天打电话才发现——这几个小时的空窗期可能就是生与死的差距。

老年人居家看护物联网（Internet of Things, IoT）要做的，是把"每天打一个电话"升级成"24 小时贴身管家"：不是真人盯着（老人也不舒服），而是用分布在家里的传感器"听"动静、"看"活动、"量"体征，在不打扰日常的前提下判断"一切正常"还是"需要干预"。一旦发现跌倒、长时间不活动、心率突变等异常，立刻通知家人或急救中心。

核心挑战往往不在传感器与算法是否成熟，而在**安全与隐私的平衡**：老人不喜欢被摄像头盯着，也不愿戴一堆设备。好的方案尽量"无感知"——几乎忘记它的存在，但它一直在默默工作。

## 一句话总结

居家看护 IoT 用穿戴式惯性测量单元（Inertial Measurement Unit, IMU）、毫米波雷达与环境传感器做被动监测，结合日常活动（Activities of Daily Living, ADL）异常检测与分级告警，在尽量少侵入隐私的前提下缩短跌倒与失能事件的发现时间；文中准确率、人口与成本数字多为公开材料或实验室量级，部署前需用目标人群实测校准。

## 1 为什么居家看护是刚需

### 1.1 老龄化与跌倒风险

中国 65 岁以上人口规模已达数亿量级（国家统计口径随年份更新）[10]；全球 60 岁以上人口在本世纪中叶将进一步显著增长（世界卫生组织 World Health Organization, WHO 口径）[1]。独居/空巢老人比例高，使"无人发现"成为独立风险因素。

跌倒是老年人意外伤害的重要原因之一。WHO 等机构持续发布跌倒相关事实摘要：全球每年有大量跌倒相关死亡，其中高龄人群占比很高 [1]。更关键的是跌倒后的**发现与救援时延**——文献与临床经验普遍强调尽早干预可改善结局，但独居场景下发现时间可能长达数小时甚至更久，具体中位数因研究样本而异，不宜当作全国统一常数 [1][9]。

### 1.2 传统方案的局限

| 方案 | 覆盖率（示意） | 局限 |
|------|----------------|------|
| 家人同住 | 高 | 年轻人工作与住房约束大 |
| 养老院 | 中 | 费用高，部分老人抗拒离家 |
| 保姆 | 中 | 人力成本高，质量不一 |
| 紧急呼叫按钮 | 低 | 需主动按下，昏迷/瘫痪时无效 |
| 定期电话回访 | 低 | 只覆盖通话时段 |

物联网方案的核心优势是**被动监测**：不要求老人操作，系统自动感知、判断与报警。

## 2 跌倒检测技术

### 2.1 基于加速度计的穿戴式检测

较成熟的方案是在腰部或手腕佩戴含三轴加速度计 + 三轴陀螺仪的设备（手环、吊坠等）。跌倒过程常见标志性模式：

1. **自由落体阶段**：合成加速度短时接近 0g（约数百毫秒量级）
2. **撞击阶段**：加速度尖峰（常大于数个 g，严重跌倒可更高）
3. **静止阶段**：撞击后回到约 1g，但姿态由直立变为接近水平

阈值算法（"合成加速度 > 阈值"）误报高——拍桌子、猛坐沙发也可能触发。主流做法是用机器学习（Machine Learning, ML）在滑动窗口上提取特征：

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def extract_features(window):
    """
    window: shape (N, 6) — [ax, ay, az, gx, gy, gz]
    N = 采样点数 (e.g., 50Hz * 2s = 100)
    """
    acc = window[:, :3]
    gyro = window[:, 3:]
    acc_mag = np.linalg.norm(acc, axis=1)

    features = {
        'acc_mag_max': acc_mag.max(),
        'acc_mag_min': acc_mag.min(),
        'acc_mag_std': acc_mag.std(),
        'acc_mag_range': acc_mag.max() - acc_mag.min(),
        'gyro_mag_max': np.linalg.norm(gyro, axis=1).max(),
        'sma': np.sum(np.abs(acc)) / len(acc),
        'post_impact_angle': np.arccos(
            acc[-1, 2] / (np.linalg.norm(acc[-1]) + 1e-8)
        ) * 180 / np.pi,
    }
    return features

# 训练常用公开集：SisFall / MobiAct 等
# 实验室准确率常报 95%+，真实居家会因佩戴依从性与类跌倒动作下降
```

公开数据集上随机森林、长短期记忆网络（Long Short-Term Memory, LSTM）等常报很高准确率 [2][9]；真实居家因佩戴依从性、类跌倒动作与个体差异，现场指标通常更保守，需单独验收。

### 2.2 非穿戴式跌倒检测

很多老人不愿戴手环（忘记充电、觉得丑、洗澡要摘），非穿戴是重要补充：

**毫米波雷达**（如 TI IWR6843）：发射约 60 GHz 频段毫米波，用多普勒与距离变化检测人体动作；可穿透衣物、不受光线影响，不采集图像，隐私相对友好 [8]。商用产品（如 Vayyar 相关方案）检测距离多为数米量级，以厂商白皮书与现场标定为准 [3]。

**环境传感器融合**：被动红外（Passive Infrared, PIR）+ 振动 + 声音。PIR 判有无活动，振动捕地板冲击，声音捕喊叫/碰撞。融合准确率在部分研究中可达约九成量级，但依赖布局与阈值，不能直接照搬 [6][9]。

| 方案 | 准确率（示意/文献量级） | 隐私性 | 佩戴要求 | 成本量级（示意） |
|------|-------------------------|--------|----------|------------------|
| 加速度计手环 | 高（实验室常 >95%） | 高 | 需佩戴 | 数百元 |
| 毫米波雷达 | 较高 | 高 | 无 | 千元级 |
| 摄像头 + AI | 高 | 低 | 无 | 数百元 |
| 环境传感器融合 | 中–高 | 高 | 无 | 数百–千元 |

## 3 日常活动识别（ADL）

### 3.1 为什么 ADL 很重要

ADL 是评估老人自理能力的医学标准，基本项通常包括进食、穿衣、洗浴、如厕、移动、个人卫生。某一项持续退化（不按时吃饭、不出卧室）往往预示健康问题。传统靠护理人员定期上门打分，频率低且主观；IoT 可做连续自动评估 [5][6]。

### 3.2 传感器部署方案

```
厨房: 水流传感器 + 柜门传感器 + 电器功率计
卧室: 床压传感器 + PIR + 光照传感器
浴室: 水流 + 门磁 + 温湿度
客厅: PIR + 沙发压力 + 电视功率计
大门: 门磁 + 智能门锁
药箱: 开合 + 重量传感器
```

时序组合可推断模式：起床（床压释放）→ 卫生间（PIR）→ 洗漱（水流持续数分钟）→ 厨房（电饭煲通电）。若某日上午很晚仍未离床，或连续多日未进厨房，系统标记异常。

### 3.3 模式异常检测

```python
from datetime import timedelta

class ADLMonitor:
    def __init__(self):
        self.baseline = {}  # 建议学习约 2 周建立个人基线
        self.alert_thresholds = {
            'wake_up_delay': timedelta(hours=2),
            'no_kitchen_days': 2,
            'bathroom_too_long': timedelta(minutes=45),
            'no_movement_hours': 4,
        }

    def check_anomaly(self, today_events):
        alerts = []
        wake_time = self._get_wake_time(today_events)
        if wake_time and self.baseline.get('avg_wake_time'):
            delay = wake_time - self.baseline['avg_wake_time']
            if delay > self.alert_thresholds['wake_up_delay']:
                alerts.append({
                    'type': 'late_wake',
                    'severity': 'medium',
                    'message': f'比平常晚起 {delay}',
                })
        for gap in self._find_inactivity_gaps(today_events):
            if gap['duration'] > self.alert_thresholds['no_movement_hours']:
                alerts.append({
                    'type': 'prolonged_inactivity',
                    'severity': 'high',
                    'message': f'{gap["start"]}~{gap["end"]} 无活动',
                })
        return alerts
```

阈值必须按个人基线与家属偏好配置；统一全国标准会制造告警疲劳。

## 4 生命体征非侵入式监测

### 4.1 无感知生理指标采集

**睡眠期间**：床垫下压电薄膜（如 Emfit 类方案）可通过体表微振动提取心率（心冲击图 Ballistocardiography, BCG）、呼吸率、睡眠分期与离床事件；精度以产品说明书与临床对照为准，常见宣传为数 bpm / 数次每分钟量级。

**日间静坐**：椅/沙发压力阵列，或毫米波雷达在约 1–2 m 距离提取呼吸与心率 [8]。

**厕所**：智能马桶盖原型可分析尿液成分作代理指标——多数仍处产品/研究阶段，不宜当作已普及医疗诊断。

### 4.2 异常预警逻辑

```python
class VitalSignsAlert:
    THRESHOLDS = {
        'heart_rate': {'low': 50, 'high': 120, 'unit': 'bpm'},
        'resp_rate': {'low': 10, 'high': 25, 'unit': '次/min'},
        'spo2': {'low': 90, 'high': 100, 'unit': '%'},
        'hr_variability_drop': 0.3,
    }

    def evaluate(self, vitals, baseline):
        risk_score = 0
        if vitals['heart_rate'] > self.THRESHOLDS['heart_rate']['high']:
            risk_score += 3
        if vitals['heart_rate'] < self.THRESHOLDS['heart_rate']['low']:
            risk_score += 4
        hrv_change = (vitals['hrv'] - baseline['hrv_7day_avg']) / baseline['hrv_7day_avg']
        if hrv_change < -self.THRESHOLDS['hr_variability_drop']:
            risk_score += 2
        # 分数阈值需临床顾问与家属共同设定；示例：>=5 通知家属，>=8 拨打急救
        return risk_score
```

上述阈值仅为工程示意，不能替代医嘱。

## 5 用药提醒与依从性追踪

老年人常见多重用药；WHO 等材料指出慢性病用药依从性整体不理想，老年人群依从率常被概括为约半数量级，具体因病种与地区差异大 [1]。

智能药盒：药格称重 + LED + 蜂鸣。到点提醒；重量变化确认取药；超时通知家属；短时重复开合可提示可能重复服药。

```
药盒(BLE) → 床头网关(WiFi) → 云端
                                 ↓
                           家属 APP 推送
                                 ↓
                        未响应 → 拨打老人电话
                                 ↓
                        仍未响应 → 通知社区工作者
```

蓝牙低功耗（Bluetooth Low Energy, BLE）链路需考虑网关掉线与老人拒接电话时的升级策略。

## 6 隐私保护与系统设计

### 6.1 隐私分级框架

| 隐私等级 | 传感器类型 | 采集信息 | 用户接受度（示意） |
|----------|-----------|----------|-------------------|
| L1 低侵入 | 门磁、PIR、功率计 | 只知"有活动" | 高 |
| L2 中等 | 加速度计、雷达 | 知"在做什么"类推断 | 中 |
| L3 高侵入 | 摄像头、麦克风 | 看到/听到具体内容 | 低 |

原则：**能用 L1 不用 L2，能用 L2 不用 L3** [6]。

### 6.2 边缘计算保隐私

即使使用摄像头，也可在边缘做姿态估计，只上传结构化结果：

```python
def process_frame_locally(frame, pose_model, fall_detector):
    """原始视频帧不离开本地；只上传结构化结果"""
    skeleton = pose_model.detect(frame)
    is_fallen = fall_detector.predict(skeleton)
    return {
        'timestamp': time.time(),
        'fallen': is_fallen,
        'skeleton': skeleton.tolist(),
    }
```

骨架坐标仍可能被重建为行为轨迹，需配合访问控制、留存期限与知情同意。

## 7 商用系统与实践建议

### 7.1 主流商用产品对比（公开材料摘要）

| 产品 | 核心技术 | 特点 | 价格口径（示意） |
|------|----------|------|------------------|
| CarePredict Tempo | 腕带 + BLE 信标 | ADL 识别等 | 机构订阅制 [4] |
| Vayyar Home | 毫米波雷达 | 无穿戴跌倒检测 | 一次性硬件 [3] |
| Lively 等 | 紧急按钮 + 活动传感 | 简单易用 | 月费制 |
| Apple Watch 等 | IMU + 心率 + 血氧 | 跌倒检测 + SOS | 消费级手表价 [7] |
| 国产穿戴 | IMU + 心率 + 血氧 | 中文生态 | 千元级 |

价格与功能随型号与地区变化快，采购前以厂商报价与本地售后为准。

### 7.2 初学者入门路径

1. Arduino/ESP32 + MPU6050 做阈值跌倒检测原型
2. 加入 BLE，推送到手机
3. 用家人模拟数据训练 ML，替代阈值
4. 增加门磁/PIR，做简单 ADL
5. 进阶：毫米波评估板，对比穿戴 vs 非穿戴

### 7.3 部署调优

- **布局**：PIR 避免对窗；门磁用胶粘；床压放床垫下
- **告警分级**：轻度延迟通知，中度立即通知家属，重度跌倒直连急救 + 家属；告警疲劳是系统失败主因
- **基线**：至少约 2 周学习期
- **电源**：门磁/PIR 纽扣电池可撑较长时间；手环需定期充电——尽量减少要老人操心的设备

## 局限、挑战与可改进方向

### 1. 实验室准确率难迁移到真实居家

**局限**：SisFall 等数据集上的 95%+ 准确率，在真实居家因佩戴依从性、类跌倒动作与个体差异显著下降 [2][9]。
**改进**：用目标用户家庭做前瞻性验收；报告灵敏度/特异度/误报率而非单一准确率；穿戴与雷达互补。

### 2. 告警疲劳导致通知被关闭

**局限**：阈值过松或基线未个性化时，家属每天收到多条误报后关闭推送。
**改进**：分级延迟与确认窗口；按个人基线自适应阈值；对"已确认误报"做在线负反馈。

### 3. 隐私与伦理接受度不足

**局限**：摄像头方案准确但接受度低；即使边缘只传骨架，仍可能泄露行为模式 [6]。
**改进**：默认 L1/L2；摄像头仅作可选增强并本地处理；书面知情同意与数据最短留存。

### 4. 急救链路不可靠

**局限**：WiFi/手机欠费、老人拒接、社区无人响应时，告警无法闭环。
**改进**：双通道通信（蜂窝备份）；明确升级矩阵（家属→社区→120）；定期演练与心跳自检。

### 5. 医疗声明与产品合规边界模糊

**局限**：消费级设备若暗示"诊断/急救替代"，可能触及医疗器械监管。
**改进**：文案区分健康提示与医疗诊断；高风险功能走合规路径；与社区医疗协议绑定责任边界。

## 参考文献

[1] WHO, "Falls: Key Facts," World Health Organization, 2024.
[2] T. Mauldin et al., "SmartFall: A Smartwatch-Based Fall Detection System Using Deep Learning," Sensors, vol. 18, no. 10, 2018.
[3] Vayyar, "Walabot HOME Fall Detection Technology White Paper," 2023.
[4] CarePredict, "Tempo AI-Powered Senior Care Platform Technical Overview," 2024.
[5] J. Kaye et al., "Intelligent Systems for Assessing Aging Changes (ISAAC)," IEEE Pervasive Computing, 2011.
[6] P. Rashidi and A. Mihailidis, "A Survey on Ambient-Assisted Living Tools for Older Adults," IEEE JBHI, vol. 17, no. 3, 2013.
[7] Apple, "Fall Detection and Emergency SOS on Apple Watch," Apple Support, 2024.
[8] Texas Instruments, "IWR6843 Single-Chip mmWave Sensor for Vital Signs Monitoring," Application Note, 2023.
[9] S. Patel et al., "A Review of Wearable Sensors and Systems for Monitoring and Detection of Falls," Biomedical Engineering Online, vol. 11, 2012.
[10] 国家统计局, "第七次全国人口普查主要数据," 更新材料, 2024.
[11] Emfit, "QS Sleep Tracker Technical Overview," Product Documentation, 2023.
[12] M. Mubashir et al., "A Survey on Fall Detection: Principles and Approaches," Neurocomputing, vol. 100, 2013.
