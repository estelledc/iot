---
schema_version: '1.0'
id: mine-safety-monitoring
title: 矿山安全监测物联网
layer: 7
content_type: technical_analysis
difficulty: intermediate
reading_time: 25
prerequisites:
  - uwb-positioning
tags:
- 矿山安全
- 瓦斯监测
- 矿用5G
- 人员定位
- UWB
- 边缘计算
- 漏泄通信
- 防爆
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 矿山安全监测物联网

> **难度**：🟡 中级 | **领域**：工业安全、矿业工程 | **阅读时间**：约 25 分钟

## 摘要

中国煤矿安全生产指标长期改善，但矿难风险仍在。矿山安全物联网（Internet of Things, IoT）用传感器网络实时监测瓦斯、粉尘、温度、顶板压力与人员位置等，力争在危险升级前预警。井下爆炸性气体、电磁屏蔽、高湿高尘与狭长巷道，使通信、防爆与可靠性成为独特工程约束。本文梳理传感器部署、井下通信、人员定位、告警链路、边缘计算与案例边界。

## 日常类比

想象在一条数公里长的黑暗地下隧道工作：无色无味的有毒/可燃气体可能积聚，顶板可能失稳，涌水可能突发。这些危险往往“看不见”。

矿山安全监测像给隧道装上感官系统：气体传感器是“鼻子”，温度是“皮肤”，顶板压力是“触觉”，摄像头是“眼睛”，人员定位是“位置感”。信息汇到地面调度中心（“大脑”），超限即报警并启动断电/撤离。关键点是：井下局部也要能在断联时自主断电——不能只靠地面“大脑”。

## 1 矿山安全风险体系

### 1.1 主要灾害类型

| 灾害类型 | 致因 | 监测参数 | 相对频率 | 后果严重度 |
|----------|------|----------|----------|-----------|
| 瓦斯爆炸 | CH₄ 达爆炸限+火源 | 甲烷浓度 | 中 | 极高 |
| 煤尘爆炸 | 煤尘浓度+火源 | 粉尘浓度 | 低 | 极高 |
| 瓦斯突出 | 高压煤层突然释放 CH₄ | CH₄+CO+风速 | 中 | 高 |
| 顶板坍塌 | 岩层应力超限 | 位移+支撑压力 | 高 | 高 |
| 矿井涌水 | 含水层突水 | 水位+水压+水量 | 中 | 高 |
| CO 中毒 | 自然发火/爆炸后 | CO 浓度 | 中 | 高 |
| 火灾 | 自然发火/电气火灾 | CO+温度+烟雾 | 中 | 高 |

### 1.2 监测参数与阈值

下表依据《煤矿安全规程》等公开条文的常见阈值整理，现场以现行有效法规与矿井设计为准[1][8]。

| 参数 | 报警阈值（示意） | 断电阈值（示意） | 精度要求（示意） | 响应时间（示意） |
|------|------------------|------------------|------------------|------------------|
| CH₄（甲烷） | ≥ 1.0% | ≥ 1.5% | ≤ ±0.1% | ≤ 20 s |
| CO（一氧化碳） | ≥ 24 ppm | — | ≤ ±2 ppm | ≤ 30 s |
| CO₂ | ≥ 1.5% | — | ≤ ±0.1% | ≤ 30 s |
| O₂ | ≤ 18% | — | ≤ ±0.3% | ≤ 30 s |
| 温度 | ≥ 26°C（采掘面） | ≥ 30°C | ≤ ±0.5°C | ≤ 60 s |
| 风速 | 低于/高于规定 | — | ≤ ±0.1 m/s | ≤ 10 s |
| 粉尘 | ≥ 最大允许浓度 | — | ≤ ±20% | ≤ 60 s |

## 2 传感器部署方案

### 2.1 瓦斯监测传感器

瓦斯（甲烷 CH₄）是煤矿重大风险源之一。两类主流传感原理：

**催化燃烧式**：CH₄ 在催化元件表面燃烧引起电阻变化。成本较低、量程可选；易受硅/硫化物“中毒”，寿命常以年计。

**非分散红外（Non-Dispersive Infrared, NDIR）**：利用 CH₄ 在约 3.3 μm 吸收峰测衰减。不易中毒、寿命更长、精度更好，成本更高。

```c
// 催化燃烧式甲烷传感器信号处理（STM32 示意）
#include <stdint.h>

#define ADC_RESOLUTION  4096
#define VREF_MV         3300
#define ZERO_GAS_MV     500
#define SPAN_GAS_MV     2500
#define FULL_SCALE_PCT  4.0f

typedef struct {
    float ch4_pct;
    float temperature;
    uint8_t alarm_level;  // 0正常 1预警 2报警 3断电
} GasReading;

GasReading read_ch4_sensor(uint16_t adc_value, float temp_c) {
    GasReading result;
    float voltage_mv = (float)adc_value / ADC_RESOLUTION * VREF_MV;
    float raw_pct = (voltage_mv - ZERO_GAS_MV)
                    / (SPAN_GAS_MV - ZERO_GAS_MV) * FULL_SCALE_PCT;
    float temp_coeff = 1.0f - 0.005f * (temp_c - 20.0f);
    result.ch4_pct = raw_pct / temp_coeff;
    if (result.ch4_pct < 0) result.ch4_pct = 0;
    result.temperature = temp_c;
    if (result.ch4_pct >= 1.5f) result.alarm_level = 3;
    else if (result.ch4_pct >= 1.0f) result.alarm_level = 2;
    else if (result.ch4_pct >= 0.8f) result.alarm_level = 1;
    else result.alarm_level = 0;
    return result;
}
```

### 2.2 部署密度要求

《煤矿安全监控系统及检测仪器使用管理规范》（AQ 1029）等对采煤工作面上隅角、回风巷、掘进迎头等位置有强制布点要求[8]。中型矿井井下传感器常达数百量级，具体以矿井设计与验收为准。

## 3 井下通信方案

### 3.1 井下通信的独特挑战

岩石/煤层衰减、狭长弯曲巷道、矿用防爆认证（如 MA/KA）、高湿高尘、采掘面推进导致基础设施需跟进——这些在地面蜂窝网中不常见。

### 3.2 通信技术对比

| 技术 | 覆盖（示意） | 带宽（示意） | 延迟（示意） | 防爆实现 | 适用场景 |
|------|--------------|--------------|--------------|----------|----------|
| 漏泄通信（Leaky Feeder） | 全矿井级 | 约 1–10 Mbps | 约 10–50 ms | 本安等 | 语音+低速数据 |
| 矿用 Wi‑Fi | 约数百米/AP | 数十–数百 Mbps | 约 5–20 ms | 隔爆等 | 视频+高速数据 |
| 矿用 5G | 约数百米/基站 | 百 Mbps–Gbps 级 | 约数–十余 ms | 隔爆/本安 | 视频+遥控 |
| ZigBee/Mesh | 数十–百米/节点 | 约 250 kbps | 约 50–200 ms | 本安 | 传感器组网 |
| 电力线载波（PLC） | 约公里级 | 约 1–10 Mbps | 约 10–100 ms | — | 利用既有电缆 |

### 3.3 漏泄通信原理

漏泄馈线外导体开槽，使射频能量沿巷道“泄漏”形成覆盖，类似多孔水管均匀喷洒。可铺设很长距离，但带宽有限，难撑高清视频。

### 3.4 矿用 5G

近年矿用第五代移动通信（5G）在部分矿井试点/部署，用于高清回传、远程操控与辅助定位[4][9]。基站须通过矿用防爆认证，功率与结构不同于地面宏站。公开材料中的“部署座数”随统计口径变化，宜以监管与企业年报为准，不宜当作统一全国覆盖率。

## 4 人员定位系统

### 4.1 定位技术选型

| 技术 | 精度（示意） | 成本量级/人 | 容量 | 实时性 | 适用场景 |
|------|--------------|-------------|------|--------|----------|
| RFID 区域定位 | 区域级 | 较低 | 大 | 秒–数十秒 | 考勤/区域管理 |
| Wi‑Fi 指纹 | 约数米 | 中 | 中 | 秒级 | 较精确定位 |
| 超宽带（UWB） | 约分米级 | 较高 | 中 | 亚秒 | 危险区高精度 |
| 蓝牙到达角（AOA） | 约米级 | 中 | 中 | 秒级 | 中等精度 |
| 惯性导航（INS） | 累积漂移 | 中–高 | — | 实时 | 盲区辅助 |

### 4.2 中国煤矿人员定位规范

AQ 6210 等标准对静态/动态精度、刷新周期与并发容量提出下限要求[3]。部分大型矿井采用 UWB 追求更高精度以服务应急救援[7]。

```python
# UWB 双边双程测距与三边定位（示意）
import numpy as np

def uwb_twr_distance(t_round1, t_reply1, t_round2, t_reply2, c=3e8):
    tof = ((t_round1 * t_round2 - t_reply1 * t_reply2) /
           (t_round1 + t_round2 + t_reply1 + t_reply2))
    return tof * c

def trilateration_3d(anchors, distances):
    A, b = [], []
    x0, y0, z0 = anchors[0]
    d0 = distances[0]
    for i in range(1, len(anchors)):
        xi, yi, zi = anchors[i]
        di = distances[i]
        A.append([2*(xi-x0), 2*(yi-y0), 2*(zi-z0)])
        b.append([xi**2 - x0**2 + yi**2 - y0**2 + zi**2 - z0**2
                  + d0**2 - di**2])
    position, _, _, _ = np.linalg.lstsq(np.array(A), np.array(b).flatten(), rcond=None)
    return position
```

## 5 实时告警与应急响应

### 5.1 分级告警机制

```
正常(绿) → 预警(黄) → 报警(橙) → 断电撤离(红)
```

从超限检测到断电/声光报警，规程对监控系统响应时限有明确要求（常见为数十秒量级）[1][8]。这对本地控制闭环提出硬实时约束。

### 5.2 边缘计算的价值

若仅依赖地面中心，井下链路损毁即失控。边缘节点可在本地完成阈值判断与断电——通信中断时仍能执行安全动作[6][10]。

```python
class MineEdgeProcessor:
    """井下边缘：本地告警 + 上行汇报（示意）"""

    THRESHOLDS = {
        'CH4': {'warning': 0.8, 'alarm': 1.0, 'cutoff': 1.5},
        'CO': {'warning': 18, 'alarm': 24, 'cutoff': None},
        'O2': {'warning': 19, 'alarm': 18, 'cutoff': None},
        'temp': {'warning': 24, 'alarm': 26, 'cutoff': 30},
    }

    def process_reading(self, sensor_id, param, value):
        thresholds = self.THRESHOLDS.get(param)
        if not thresholds:
            return None
        is_inverse = (param == 'O2')
        if thresholds.get('cutoff') is not None:
            if (not is_inverse and value >= thresholds['cutoff']) or \
               (is_inverse and value <= thresholds['cutoff']):
                self.execute_cutoff(sensor_id)
                return 'CUTOFF'
        if (not is_inverse and value >= thresholds['alarm']) or \
           (is_inverse and value <= thresholds['alarm']):
            self.trigger_alarm(sensor_id, param, value)
            return 'ALARM'
        if (not is_inverse and value >= thresholds['warning']) or \
           (is_inverse and value <= thresholds['warning']):
            return 'WARNING'
        return 'NORMAL'

    def execute_cutoff(self, sensor_id):
        for device in self.get_controlled_devices(sensor_id):
            device.power_off()
        self.log_event('CUTOFF', sensor_id)
```

## 6 实际案例与效益边界

### 6.1 大型矿企实践（边界说明）

国能神东等企业公开材料描述了大规模传感器、矿用 5G 与人员定位覆盖[5]。其中“零事故”“减人比例”等表述依赖统计口径与年份，本文不作未经核验的绝对断言；工程价值应落在：远程操控降低暴露、视频辅助违章识别、定位服务救援。

### 6.2 成本效益对比（示意）

| 项目 | 传统监测（示意） | IoT 增强（示意） | 说明 |
|------|------------------|------------------|------|
| 瓦斯超限响应 | 分钟级人工/轮询 | 秒–数十秒自动闭环 | 取决于本地控制 |
| 人员定位 | 区域级 | 米级–分米级 | 技术选型相关 |
| 预警能力 | 弱/滞后 | 可结合多参数趋势 | 需模型校验 |
| 年均安全投入 | 因矿而异 | 通常更高 | 相对重大事故损失仍常为正 |

## 7 局限、挑战与可改进方向

### 1. 传感器漂移与校准负担

**局限**：催化元件中毒/漂移导致假阴性风险；井下校准成本高。
**改进**：关键点双传感器交叉验证；催化与 NDIR 混部；按规程缩短校准周期并自动提示到期。

### 2. 通信单点与防爆约束

**局限**：漏缆/光纤中断或无线遮挡造成盲区；防爆认证延长设备迭代。
**改进**：有线主用 + 无线备用；分区边缘自治断电；选型阶段预留认证周期。

### 3. 定位与告警的运维缺口

**局限**：标签掉电、基站未随采掘面推进导致“名义全覆盖、实际空洞”。
**改进**：标签电量与在线率纳入班前检查；采掘进度与基站搬迁工单联动。

### 4. 数据可信与问责

**局限**：边缘日志被篡改或补传缺失影响事故追溯。
**改进**：本地只追加存储、签名时间戳；恢复链路后强制补传校验。

## 8 实践建议

### 8.1 初学者入门路径

1. 阅读《煤矿安全规程》中监测与阈值章节
2. 学习催化燃烧与 NDIR 气体传感原理
3. 理解漏泄馈线与矿用无线防爆差异
4. 用开发板 + 气体传感器做**开放空间**原型（严禁密闭空间危险实验）

### 8.2 具体调优建议

- **冗余**：上隅角等关键点双传感器
- **校准**：催化类缩短周期，NDIR 可相对延长但仍需点检
- **通信**：主备异质链路
- **边缘自主**：断联可断电是底线
- **存储**：边缘保留不少于规程要求的历史数据以便补传

## 参考文献

[1] 国家矿山安全监察局, "煤矿安全规程（2022 修订版）," 2022.
[2] 中国煤炭工业协会, "中国煤矿安全生产统计相关年报," 2024.
[3] AQ 6210-2021, "煤矿井下人员位置监测系统通用技术条件," 应急管理部, 2021.
[4] Wang, J., et al., "Application of 5G Technology in Coal Mine Safety Monitoring," IEEE Access, 2024.
[5] 国能神东煤炭集团, "智能矿山建设实践与成效," 2024.
[6] Zhang, Y., et al., "Edge Computing for Real-time Mine Safety Monitoring: Architecture and Implementation," Journal of Mining Science, 2024.
[7] Li, X., et al., "UWB-based Personnel Positioning System for Underground Coal Mines," Measurement, 2024.
[8] AQ 1029-2019, "煤矿安全监控系统及检测仪器使用管理规范," 应急管理部, 2019.
[9] 华为, "矿用 5G 解决方案白皮书," 2024.
[10] Mishra, D. P., et al., "IoT-based Real-Time Monitoring System for Underground Mines: A Comprehensive Review," Tunnelling and Underground Space Technology, 2024.
[11] IEC 60079, "Explosive Atmospheres — Equipment Protection," IEC series.
[12] 应急管理部, "煤矿安全生产标准化管理体系考核定级办法（试行）相关文件," 近年修订版.
