---
schema_version: '1.0'
id: ble-direction-finding-aoa-aod
title: BLE测向技术AoA/AoD室内定位原理
layer: 2
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# BLE测向技术AoA/AoD室内定位原理
> **难度**：🔴 高级 | **领域**：BLE定位技术 | **阅读时间**：约 22 分钟

## 引言

想象你闭着眼睛坐在房间里，有人在不同位置拍手。虽然看不到，但你能凭借双耳接收到声音的微小时间差来判断声源方向——左耳先听到说明声音来自左边。BLE 5.1 的测向技术原理类似：用多根天线接收同一信号，通过相位差来精确计算信号来源方向，实现亚米级室内定位。

本文解析 AoA(到达角)和 AoD(出发角)两种测向模式的原理和部署方案。

## 1. BLE 5.1测向技术概述

### 1.1 为什么需要测向

传统 BLE 定位依赖 RSSI 估算距离，精度通常 3-5 米且受环境影响严重。BLE 5.1 直接测量信号到达角度，配合三角定位可实现 0.5-1 米精度。

```
定位精度对比:
| 技术         | 典型精度 | 成本 |
|-------------|---------|------|
| RSSI指纹     | 3-5米   | 低   |
| BLE AoA/AoD | 0.5-1米 | 中   |
| UWB          | 10-30cm | 高   |
| WiFi RTT     | 1-2米   | 中   |
```

### 1.2 两种测向模式

```
AoA(Angle of Arrival):
   [Tag单天线发射] -------> [Locator天线阵列接收+计算角度]

AoD(Angle of Departure):
   [Beacon天线阵列发射] --> [Tag单天线接收+自己计算角度]
```

| 特性 | AoA | AoD |
|------|-----|-----|
| 天线阵列位置 | 定位器(固定) | 信标(固定) |
| 标签复杂度 | 低(单天线) | 低(单天线) |
| 计算位置 | 服务器端 | 标签端 |
| 标签电池寿命 | 更长(只发射) | 较短(需计算) |
| 隐私性 | 低(服务器知位置) | 高(标签自知位置) |
| 典型应用 | 资产追踪 | 导航寻路 |

## 2. CTE(恒定音频扩展)

### 2.1 CTE的作用

CTE(Constant Tone Extension)是 BLE 5.1 新增的包结构——在数据包末尾追加一段无调制载波，专门用于相位测量。

```
BLE 5.1测向数据包:
+----------+--------+------+-----+-----+
| Preamble | Access | PDU  | CRC | CTE |
|          | Addr   |      |     |     |
+----------+--------+------+-----+-----+
                                    |
                           纯载波(无调制) 16-160us
                           用于IQ采样
```

普通 BLE 包使用 GFSK 调制，频率不断变化，难以准确测量相位。CTE 提供恒定频率载波，使得接收端可在不同天线上采集稳定相位。

### 2.2 天线切换时序

```c
// CTE配置
struct ble_cte_config {
    uint8_t cte_type;      // 0: AoA, 1: AoD@1us, 2: AoD@2us
    uint8_t cte_length;    // 2-20 (单位8us, 最大160us)
    uint8_t switch_pattern_len;
    uint8_t *antenna_ids;
};
```

CTE 期间接收端按预定顺序切换天线采样：

```
|<- 参考期 ->|<------ 天线切换采样期 ------>|
| 4us | 4us  | 2us| 2us| 2us| 2us| 2us|...|
| A0  | A0   | A1 | A2 | A3 | A4 | A1 |...|
```

## 3. AoA(到达角)详解

### 3.1 工作原理

平面波到达天线阵列时，各天线因位置不同导致相位差异：

```
信号方向 \  theta
          \ |
           \|
---+----+----+----  天线阵列(间距d)
   A0   A1   A2

路径差 = d * sin(theta)
相位差 = 2*pi*d*sin(theta) / lambda
```

### 3.2 角度计算

```python
import numpy as np

def calculate_aoa(phase_diff, d, wavelength):
    """
    phase_diff: 相邻天线间相位差(弧度)
    d: 天线间距(米)
    wavelength: 波长(2.4GHz约0.125m)
    """
    sin_theta = phase_diff * wavelength / (2 * np.pi * d)
    sin_theta = np.clip(sin_theta, -1.0, 1.0)
    return np.degrees(np.arcsin(sin_theta))

# 示例: d=0.0625m, phase_diff=pi/2 --> 约30度
```

### 3.3 定位系统架构

```
         天花板
  [Locator1]  [Locator2]  [Locator3]
      \ angle1   | angle2    / angle3
       \         |          /
        \        |         /
         \       |        /
          *------*-------*    三角定位
        [Tag位置]

流程: Tag广播CTE包 -> 多Locator各测角度 -> 定位引擎三角计算
```

定位器数量要求：2D 至少 2 个，3D 至少 3 个，实际部署通常 4-6 个。

## 4. AoD(出发角)详解

### 4.1 工作原理

AoD 模式下信标用天线阵列按顺序发射 CTE，标签用单天线接收后根据已知切换模式计算角度：

```python
def aod_position(beacons, angles):
    """
    beacons: [(x,y),...] 信标坐标
    angles: [theta,...] 各信标方向测得角度
    """
    A, b = [], []
    for (bx, by), theta in zip(beacons, angles):
        t = np.tan(np.radians(theta))
        A.append([t, -1])
        b.append(t * bx - by)
    position, _, _, _ = np.linalg.lstsq(
        np.array(A), np.array(b), rcond=None)
    return position
```

### 4.2 AoD的隐私优势

位置计算完全在标签本地完成，服务器不知道标签确切位置。对消费者导航应用很重要——用户掌控自己的位置数据。

## 5. 天线阵列设计

### 5.1 阵列布局

```
均匀线性阵列(ULA):          均匀矩形阵列(URA):
A0  A1  A2  A3              A00 A01 A02 A03
|<-d->|                     A10 A11 A12 A13
仅测1个平面角度             可测方位角+俯仰角
```

### 5.2 间距要求

```
关键约束: d <= lambda/2
2.4GHz: lambda=12.5cm, 最大间距=6.25cm

间距太大: 角度模糊(多解)
间距太小: 相位差太小, 噪声影响大
最优: 接近lambda/2, 实际取5-6cm
```

### 5.3 硬件设计

```
PCB参考设计(4x4阵列):
- 天线类型: 倒F天线(IFA), 适合PCB集成
- RF开关: SKY13418 (SP12T)
- 连接nRF52833 GPIO + RADIO
- PCB尺寸: 约15cm x 10cm
```

## 6. 角度估算算法

### 6.1 IQ采样

I(同相)和 Q(正交)分量描述信号幅度和相位：

```
复信号: s_n = A * e^(j*(phi0 + n*delta_phi))
其中 delta_phi = 2*pi*d*sin(theta)/lambda
```

### 6.2 MUSIC算法

高分辨率谱估计算法，多径环境下性能优于简单相位差法：

```python
def music_aoa(iq_matrix, d, wavelength, num_signals=1):
    """iq_matrix: (num_antennas, num_snapshots)"""
    num_ant = iq_matrix.shape[0]
    # 协方差矩阵
    R = iq_matrix @ iq_matrix.conj().T / iq_matrix.shape[1]
    # 特征分解, 取噪声子空间
    eigvals, eigvecs = np.linalg.eigh(R)
    noise = eigvecs[:, :num_ant - num_signals]
    # 角度谱扫描
    angles = np.linspace(-90, 90, 361)
    spectrum = []
    for theta in angles:
        sv = np.exp(-1j * 2*np.pi*d * np.arange(num_ant)
                    * np.sin(np.radians(theta)) / wavelength)
        proj = sv.conj() @ noise
        spectrum.append(1.0 / np.abs(proj @ proj.conj()))
    return angles[np.argmax(spectrum)]
```

### 6.3 ESPRIT算法

利用阵列平移不变性，无需谱搜索，计算量 O(N^3)，需要均匀阵列。

## 7. 多径问题与对策

### 7.1 多径效应

室内信号经墙壁、天花板反射产生多条路径，干扰直接路径的相位测量。

### 7.2 应对策略

| 策略 | 原理 | 效果 |
|------|------|------|
| MUSIC算法 | 分辨多信号源 | 区分直达和反射 |
| 多次采样平均 | 时间滤波 | 减少瞬时噪声 |
| 频率跳变 | 不同频率多径不同 | 降低特定频率影响 |
| 环境校准 | 预存偏差映射 | 软件补偿 |
| 天花板安装 | 减少水平反射 | 结构减少多径 |

校准后精度通常改善 30-50%。

## 8. 硬件支持

### 8.1 支持BLE 5.1测向的芯片

| 芯片 | 厂商 | 天线端口 | 特点 |
|------|------|----------|------|
| nRF52833 | Nordic | 最多12路 | 主流, SDK完善 |
| nRF5340 | Nordic | 最多12路 | 双核更强 |
| EFR32BG22 | Silicon Labs | 最多8路 | 低功耗 |

### 8.2 开发示例

```c
// nRF52833 AoA接收配置(Zephyr)
#include <zephyr/bluetooth/direction.h>

static uint8_t ant_pattern[] = {0, 1, 2, 3, 4, 5, 6, 7};

void iq_report_cb(struct bt_le_per_adv_sync *sync,
    struct bt_df_per_adv_sync_iq_samples_report *report)
{
    float angle = calculate_angle(report->sample,
                                  report->sample_count);
    send_to_positioning_engine(angle);
}
```

## 9. 实际部署案例

### 9.1 仓库资产追踪

```
场景: 2000平米仓库, 500个资产标签
- 定位器: 16个(4x4网格, 间距10米), 天花板4米
- 标签广播间隔: 1秒, 刷新率1Hz
- 精度: 0.5米(90%置信度)

成本: 定位器16x50USD + 标签500x5USD = 3300USD
```

### 9.2 布局注意事项

```
好的布局(角度交叉大):    差的布局(近似平行):
    L1      L2               L1 L2
     \    /                   |  |
      \  /                    |  |
       \/                     |  |
     [Tag]                  [Tag]
   精度高                   精度差
```

## 10. 与其他技术对比

| 维度 | BLE AoA/AoD | UWB | WiFi指纹 |
|------|-------------|-----|----------|
| 精度 | 0.5-1m | 10-30cm | 3-5m |
| 部署成本 | 中 | 高 | 低 |
| 标签成本 | 2-5 USD | 10-20 USD | 0(手机) |
| 功耗 | 低 | 中 | 高 |
| 扩展性 | 好 | 好 | 一般 |

BLE 测向在精度和成本之间取得良好平衡，特别适合大量标签、功耗敏感的资产追踪场景。

## 总结

BLE 5.1 测向通过 CTE 和天线阵列实现精确