# UWB IEEE 802.15.4z精密测距协议
> **难度**：🔴 高级 | **领域**：UWB精密定位 | **阅读时间**：约 22 分钟

## 引言

想象你在停车场找车, 手机显示"你的车在附近", 但附近可能是隔了三排车位。如果手机能告诉你"车在你左前方 8.3 米", 精确到厘米级, 体验就完全不同了。这种精确测距能力正是 UWB(超宽带)技术的核心价值, 而 IEEE 802.15.4z 标准则为这种测距加上了安全保障, 确保没有人能欺骗你的手机, 让它误以为车就在旁边。

本文深入解析 UWB 测距原理、802.15.4z 的安全增强机制、物理层规格和多锚点定位方案。

## 1 UWB技术概述

### 1.1 什么是超宽带

UWB(Ultra-Wideband)是一种使用极宽频谱带宽的无线电技术: 带宽 500MHz 以上(对比 BLE 仅 2MHz, WiFi 20-160MHz), 使用极短射频脉冲(不到 2ns), 主要使用 6-9 GHz 频段, 发射功率极低(功率谱密度低于 -41.3 dBm/MHz)。

### 1.2 UWB为什么能精确测距

测距精度与信号带宽直接相关:

```
时间分辨率 = 1 / 带宽

窄带(BLE, 2MHz):  时间分辨率 500ns -> 距离分辨率 150m
UWB(500MHz):       时间分辨率 2ns   -> 距离分辨率 0.6m

配合前导边沿检测和超分辨算法, 实际精度可达 5-10cm
```

### 1.3 802.15.4z的定位

IEEE 802.15.4z 是 802.15.4 标准的修订版(2020年发布), 全称 Enhanced Impulse Radio。基于 802.15.4a(2007)的 UWB 物理层, 增加了安全测距能力(STS), 改进了性能和可靠性。是 Apple U1/U2、Android UWB 等商用实现的基础标准。

## 2 UWB测距原理

### 2.1 双向测距(TWR)

UWB 测距的基本方法是 TWR(Two-Way Ranging), 通过测量射频信号飞行时间来计算距离:

```
Single-Sided TWR (SS-TWR):

设备 A (发起者)              设备 B (响应者)
    |                            |
    |--- POLL(时间戳 T1) ------->|
    |                            | 处理时间 Treply
    |<-- RESPONSE(时间戳 T2) ----|
    |                            |
    记录 T3 = 收到 RESPONSE 时间

飞行时间 ToF = (Tround - Treply) / 2
  Tround = T3 - T1 (往返时间)
  Treply = B 回传的响应处理时间
距离 = ToF * c (光速)
```

### 2.2 双边双向测距(DS-TWR)

SS-TWR 的时钟偏差会引入误差。DS-TWR 通过额外一轮交换来消除:

```
DS-TWR 流程:

设备 A                       设备 B
    |--- POLL ------------------>|  T_roundA
    |<-- RESPONSE ---------------|  T_replyB
    |--- FINAL ----------------->|  T_roundB, T_replyA

ToF = (T_roundA * T_roundB - T_replyA * T_replyB)
      / (T_roundA + T_roundB + T_replyA + T_replyB)

优势: 消除时钟频偏一阶影响, 不依赖两端时钟同步
代价: 多一次消息交换
```

### 2.3 ToF到距离的转换

```python
def tof_to_distance(tof_ns):
    """将飞行时间(纳秒)转换为距离(米)"""
    c = 299792458.0  # 光速 (m/s)
    return tof_ns * 1e-9 * c

# 1ns ToF = 0.3m = 30cm
# 10cm 精度需要约 0.33ns 时间测量精度
# UWB 64GHz 时钟(15.65ps 分辨率)可以做到
```

## 3 802.15.4z安全增强

### 3.1 为什么需要安全测距

UWB 测距被用于安全敏感场景: 汽车无钥匙进入、门禁、支付等。如果攻击者能操纵测距结果, 后果严重。

```
中继攻击(Relay Attack):

正常: [车钥匙]---2m---[汽车] -> 解锁

攻击: [车钥匙]---100m---[攻击者A]===中继===[攻击者B]---2m---[汽车]
      汽车看到距离很短 -> 误解锁

BLE/NFC 无钥匙系统已有大量真实中继攻击案例
```

### 3.2 STS(加扰时间戳序列)

STS(Scrambled Timestamp Sequence)是 802.15.4z 的核心安全机制:

```
STS 工作原理:

1. 密钥协商: 设备 A 和 B 预先共享密钥 K
2. STS 生成: STS = AES(K, counter), 每次测距不同 counter
3. 嵌入测距帧: [SHR][PHR][PHY Payload][STS]
4. 接收端验证:
   - 生成期望 STS, 与收到的做互相关
   - 相关峰值高 -> 匹配, 测距可信
   - 相关峰值低 -> 不匹配, 拒绝
```

### 3.3 STS防中继攻击

攻击者不知道密钥 K, 无法预测 STS 内容。中继转发引入额外延迟(即使纳秒级)会被检测。攻击者试图提前发送也无法构造有效 STS, 接收端验证必然失败。

### 3.4 STS模式

| STS 模式 | STS 位置 | 特点 |
|----------|---------|------|
| Mode 0 | 无 | 兼容旧设备, 无安全保护 |
| Mode 1 | Payload 后 | STS 和数据在同一帧 |
| Mode 2 | 无 Payload | 最安全, 攻击面最小 |
| Mode 3 | Payload 前 | STS 先于数据 |

安全性排序: Mode 2 > Mode 3 > Mode 1 > Mode 0。

## 4 物理层规格

### 4.1 信道配置

```
主要信道:
信道 5: 中心频率 6489.6 MHz, 带宽 499.2 MHz (最广泛使用)
信道 9: 中心频率 7987.2 MHz, 带宽 499.2 MHz
```

### 4.2 脉冲重复频率与数据速率

| 参数 | 选项 A | 选项 B |
|------|--------|--------|
| PRF | 15.6 MHz | 62.4 MHz |
| 数据速率 | 850 kbps | 6.8 Mbps |
| 特点 | 低功耗, 长距离 | 高精度, 高速数据 |

### 4.3 前导码

前导码用于同步和信道估计, 长度从 16 到 4096 符号可选。短前导码(16-64)适合短距离高信噪比环境, 快速同步低开销。长前导码(1024-4096)适合长距离复杂多径环境, 更强的同步能力和测距精度。

## 5 测距协议流程

### 5.1 完整DS-TWR流程

```
发起者(Initiator)               响应者(Responder)
    |  生成 STS_poll              |
    |--- POLL [SHR|Data|STS] --->|
    |  记录 T_poll_tx             | 记录 T_poll_rx
    |                             | 生成 STS_resp
    |<-- RESP [SHR|Data|STS] ----|
    |  记录 T_resp_rx             | 记录 T_resp_tx
    |  验证 STS_resp              |
    |  生成 STS_final             |
    |--- FINAL [SHR|Data|STS] -->|
    |                             | 验证 STS_final
    |                             | 计算 ToF
    |<-- RESULT [距离值] ---------|
```

### 5.2 时间戳精度

UWB 芯片使用高精度计数器。以 Qorvo DW3000 为例: 内部时钟约 64 GHz, 时间戳分辨率约 15.65 ps, 对应距离分辨率约 4.7mm。实际测距精度受限于多径、天线延迟等因素。

## 6 多锚点定位

### 6.1 从测距到定位

单次测距只得到距离。2D 定位需至少 3 个锚点(三边测量), 3D 需至少 4 个:

```
示例(2D 三边测量):
  锚点 A 在 (0, 0), 测距 5m
  锚点 B 在 (10, 0), 测距 7m
  锚点 C 在 (5, 8), 测距 4m
  解三个圆的交点 -> 标签位置 (x, y)
```

### 6.2 TDoA模式

TWR 需要标签与每个锚点分别测距。TDoA 更高效: 锚点之间精确同步, 标签只发一次帧, 各锚点记录到达时间, 计算时间差定义双曲线, 交点即标签位置。标签只发不收, 功耗极低, 支持大量标签同时定位。

### 6.3 定位算法

```python
import numpy as np

def trilateration_2d(anchors, distances):
    """2D 最小二乘三边定位"""
    n = len(anchors)
    A = np.zeros((n - 1, 2))
    b = np.zeros(n - 1)
    x0, y0 = anchors[0]
    d0 = distances[0]
    for i in range(1, n):
        xi, yi = anchors[i]
        di = distances[i]
        A[i-1, 0] = 2 * (xi - x0)
        A[i-1, 1] = 2 * (yi - y0)
        b[i-1] = (d0**2 - di**2 + xi**2 - x0**2 + yi**2 - y0**2)
    return np.linalg.lstsq(A, b, rcond=None)[0]
```

## 7 精度影响因素

### 7.1 视距与非视距

```
LOS (Line-of-Sight, 视距):
  直射路径无遮挡
  精度: 5-10cm 典型值
  首达路径清晰, ToA 估计准确

NLOS (Non-Line-of-Sight, 非视距):
  直射路径被墙壁、人体等遮挡
  精度: 退化到 30-100cm
  信号绕射/穿透, 到达时间偏大
  需要 NLOS 检测和补偿算法

NLOS 检测方法:
  首达路径信号质量指标(FP_POWER vs RX_POWER 比值)
  信道脉冲响应(CIR)形状分析
  机器学习分类器(基于多个射频特征)
```

### 7.2 多径效应

室内环境中信号会被墙壁、地面、天花板反射, 产生多条路径:

- 首达路径(First Path): 直射路径, 到达时间最早
- 反射路径: 经过一次或多次反射, 到达时间稍晚
- UWB 的宽带宽使其能分辨不同路径(时间分辨率 2ns = 0.6m)
- 关键技术: 首达路径检测(First Path Detection), 找到最早到达的脉冲
- 与 WiFi/BLE 对比: 窄带系统无法区分多径, 看到的是所有路径的叠加

### 7.3 天线延迟校准

UWB 信号在天线和芯片之间存在固定延迟:

```
天线延迟影响:
  实际 ToF = 测量 ToF - TX天线延迟 - RX天线延迟
  延迟通常 16-17ns(约 5m), 必须校准
  不校准 -> 所有距离测量有固定偏差

校准方法:
  1. 将两设备放在已知距离处(如 5m)
  2. 进行多次测距, 计算平均值
  3. 已知距离与测量距离的差 = 总天线延迟
  4. 将总延迟平分给两端(对称情况)
  5. 写入芯片寄存器, 后续自动补偿
```

### 7.4 温度影响

温度变化影响晶振频率和天线特性:

- 晶振频偏: 约 1-2 ppm 每 10 度变化
- 天线延迟变化: 约 0.1-0.3ns 每 10 度变化
- 在工业环境(温差大)中影响显著
- 高精度应用需要温度补偿(查表或实时校准)

## 8 硬件生态

### 8.1 主流UWB芯片

| 芯片 | 厂商 | 特点 |
|------|------|------|
| SR150/Trimension | NXP | 汽车 UWB, 集成安全元件接口 |
| DW3000 | Qorvo | 通用 802.15.4z, 功耗优化 |
| U1/U2 | Apple | iPhone/AirTag, 深度生态集成 |
| Exynos Connect U100 | Samsung | Galaxy 系列, SmartTag 配合 |

### 8.2 开发平台

| 平台 | 芯片 | 特点 |
|------|------|------|
| Qorvo DWM3000 | DW3000 | 通用开发板, 文档丰富 |
| NXP NCJ29D5 | SR150 | 汽车级, CCC 认证 |
| Nordic nRF5340+DW3000 | DW3000 | BLE+UWB 组合 |

## 9 应用场景

### 9.1 数字车钥匙

CCC(Car Connectivity Consortium)定义了基于 UWB 的数字车钥匙: 手机接近自动解锁, UWB 验证手机在 1-2m 内, 防中继攻击。BMW、Audi、VW 等已量产采用。

### 9.2 精准寻物

Apple AirTag 和 Samsung SmartTag: BLE 粗略发现, UWB 精确导航(方向和距离), 手机显示箭头指向目标, 厘米级精度。

### 9.3 室内定位

仓库叉车和货物追踪、工厂工人和设备安全定位、医院医疗设备追踪。精度 10-30cm, 远超 WiFi/BLE 方案。

### 9.4 门禁和支付

手机靠近门或支付终端时 UWB 验证物理距离。比 NFC 更方便(不需贴近), 比 BLE 更安全(防中继攻击)。

## 总结

IEEE 802.15.4z 将 UWB 测距从纯物理层技术提升为安全的定位基础设施。500MHz 带宽带来 2ns 时间分辨率使厘米级测距成为可能, STS 机制通过密码学确保测距结果不可伪造, DS-TWR 消除时钟偏差影响, 多锚点三边测量或 TDoA 实现空间定位。

从数字车钥匙到精准寻物, 从工业定位到安全门禁, 802.15.4z UWB 正在成为精确感知距离和位置的标准技术。随着 Apple、Samsung、NXP、Qorvo 等厂商持续推动, UWB 生态将覆盖更多需要精确、安全测距的 IoT 场景。

## 参考文献

- [IEEE 802.15.4z-2020. "Enhanced Impulse Radio." IEEE Standards Association, 2020.](https://standards.ieee.org/ieee/802.15.4z/10230/)
- [Coppens, D. et al. "An Overview of UWB Standards and Organizations." IEEE Access, 2022.](https://ieeexplore.ieee.org/document/9855217)
- [Singh, M. et al. "UWB Ranging and Localization: A Tutorial." IEEE Communications Surveys and Tutorials, 2023.](https://ieeexplore.ieee.org/document/10012345)
- [FiRa Consortium. "UWB Secure Ranging: Technical Overview." 2021.](https://www.firaconsortium.org/technical-resources)
