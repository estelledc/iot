# WiFi HaLow (802.11ah)：专为物联网设计的长距离 WiFi

> 难度：🟡 中级 | 领域：低功耗广域网、Sub-GHz 通信 | 更新：2025-06

---

## 一句话总结

WiFi HaLow 把传统 WiFi 的协议栈搬到了 Sub-1GHz 频段，用更窄的信道和更低的频率换来了 1-3 km 的覆盖距离和极低的功耗，同时保留了 IP 原生通信和 WPA3 安全性——这让它成为 LoRa 和 NB-IoT 之间的"中间地带"选手。

---

## 从日常场景说起

你有没有注意过，低音炮的声音能穿过好几堵墙传到隔壁，但高音的人声走出房间就听不清了？这是因为低频声波的波长长，绕过障碍物的能力更强。

WiFi HaLow 做的事情本质上一样：把 WiFi 信号的"音调降低"——从 2.4 GHz（波长 12.5 cm）降到 900 MHz 附近（波长 33 cm）。波长变长了将近 3 倍，信号穿墙能力和覆盖距离大幅提升。代价是什么？就像低音炮没法播放清晰的人声一样，低频意味着可用带宽变窄、数据速率降低。但对于只需要传几十字节温度数据的传感器来说，速率根本不是瓶颈——能传得远、省电、用 IP 协议直接上云，才是真正需要的。

再打一个比方：如果说传统 WiFi 是市内高速公路（快但覆盖小），LoRa 是乡间小路（慢但能到很远的地方），那 WiFi HaLow 就是省道——速度适中，距离够远，最关键的是它和高速公路用的是同一套交通规则（TCP/IP），不需要在路口换乘。

---

## 1. 技术起源与标准化历程

### 1.1 为什么需要一个新的 WiFi 标准

2010 年前后，物联网市场面临一个尴尬的"协议鸿沟"：

- 传统 WiFi（802.11n/ac）：速度快，但功耗高、覆盖只有几十米，电池供电的传感器用不起
- ZigBee/BLE：功耗低，但覆盖只有 10-30 米，大面积部署需要大量中继
- LoRa/Sigfox：覆盖远、功耗低，但速率太低（几百 bps 到几十 kbps），且不是 IP 原生，需要专用网关

市场需要一个"速率适中（几百 kbps 到几 Mbps）、覆盖 1 km 级、IP 原生、低功耗"的方案。IEEE 802.11ah 工作组在 2010 年成立，2016 年标准正式发布，WiFi 联盟将其品牌命名为 WiFi HaLow（发音"halo"）。

### 1.2 标准化时间线

| 年份 | 事件 |
|------|------|
| 2010 | IEEE 802.11ah 工作组成立 |
| 2013 | Draft 1.0 发布 |
| 2016 | IEEE 802.11ah 标准正式发布 |
| 2021 | WiFi 联盟启动 HaLow 认证项目 |
| 2023 | Morse Micro MM6108 芯片量产，首批认证产品上市 |
| 2024 | WiFi 联盟发布 HaLow R2 规范，增强安全和互操作性 |
| 2025 | 全球部署开始加速，尤其在智慧农业和安防领域 |

---

## 2. 物理层设计：Sub-1GHz 的工程取舍

### 2.1 频段分配

WiFi HaLow 使用的频段因地区而异，这是部署时需要关注的重要因素：

| 地区 | 频段 | 可用带宽 | 监管框架 |
|------|------|---------|---------|
| 美国 | 902-928 MHz | 26 MHz | FCC Part 15 (免授权) |
| 欧洲 | 863-868 MHz | 5 MHz | ETSI EN 300 220 |
| 中国 | 755-787 MHz | 32 MHz | MIIT（需型号核准） |
| 日本 | 916.5-927.5 MHz | 11 MHz | ARIB STD-T108 |
| 韩国 | 917-923.5 MHz | 6.5 MHz | KCC |
| 澳大利亚 | 915-928 MHz | 13 MHz | ACMA |

需要注意，这些频段在很多国家是 ISM 免授权频段，同时也被 LoRa、Sigfox、Z-Wave 等技术使用，存在共存干扰的问题。

### 2.2 信道带宽选项

WiFi HaLow 支持 1/2/4/8/16 MHz 五种信道带宽，这是它灵活性的关键来源：

| 信道带宽 | 最大速率 (MCS9, 1SS) | 典型覆盖距离 | 适用场景 |
|---------|---------------------|------------|---------|
| 1 MHz | 4 Mbps | 1-3 km | 远距离传感器、农业 |
| 2 MHz | 7.8 Mbps | 0.8-2 km | 智能表计、资产追踪 |
| 4 MHz | 18 Mbps | 0.5-1.5 km | 安防摄像头、音频 |
| 8 MHz | 32.67 Mbps | 0.3-1 km | 视频监控、大数据量 |
| 16 MHz | 65.3 Mbps | 0.2-0.8 km | 高带宽 IoT 应用 |

1 MHz 信道是 HaLow 的"杀手级带宽"——在 LoRa 的覆盖距离上提供了高两个数量级的速率。下面的 Python 代码可以计算不同配置下的理论速率：

```python
def halow_data_rate(mcs, n_ss, bw_mhz):
    """计算 WiFi HaLow 理论速率 (Mbps)
    
    基于 802.11ah OFDM 参数，符号时间 = 40 μs (1MHz) 按比例缩放
    """
    # 每符号数据子载波数 (1 MHz 信道)
    n_sd_base = {1: 24, 2: 52, 4: 108, 8: 234, 16: 468}
    
    # MCS 调制和编码参数: (bits_per_subcarrier, coding_rate)
    mcs_params = {
        0: (1, 1/2),    # BPSK, 1/2
        1: (2, 1/2),    # QPSK, 1/2
        2: (2, 3/4),    # QPSK, 3/4
        3: (4, 1/2),    # 16-QAM, 1/2
        4: (4, 3/4),    # 16-QAM, 3/4
        5: (6, 2/3),    # 64-QAM, 2/3
        6: (6, 3/4),    # 64-QAM, 3/4
        7: (6, 5/6),    # 64-QAM, 5/6
        8: (8, 3/4),    # 256-QAM, 3/4
        9: (8, 5/6),    # 256-QAM, 5/6 (仅 2MHz+)
        10: (2, 1/2),   # BPSK rep, 用于 1MHz 最远距离
    }
    
    bpc, cr = mcs_params[mcs]
    n_sd = n_sd_base[bw_mhz]
    symbol_time_us = 40  # 1 MHz 基准，其他带宽按比例缩减
    
    bits_per_symbol = n_sd * bpc * cr * n_ss
    rate_mbps = bits_per_symbol / symbol_time_us  # Mbps
    
    return round(rate_mbps, 2)

# 示例：1 MHz 信道, MCS 0-8, 单天线
for mcs in range(9):
    rate = halow_data_rate(mcs, 1, 1)
    print(f"MCS{mcs}, 1MHz, 1SS: {rate} Mbps")
```

### 2.3 链路预算分析

WiFi HaLow 之所以能达到 1-3 km 的覆盖，主要靠三个因素叠加：

1. **频率更低**：900 MHz vs 2.4 GHz，自由空间路径损耗降低约 8.5 dB
2. **窄带宽**：1 MHz vs 20 MHz，噪声功率降低 13 dB，接收灵敏度对应提升
3. **更长符号时间**：抗多径能力更强

下面是一个典型的链路预算对比：

| 参数 | WiFi HaLow (1 MHz, MCS1) | WiFi 6 (20 MHz, MCS0) | LoRa (SF10, 125kHz) |
|------|--------------------------|----------------------|---------------------|
| 发射功率 | 14 dBm | 20 dBm | 14 dBm |
| 天线增益 (TX+RX) | 4 dBi | 4 dBi | 4 dBi |
| 接收灵敏度 | -104 dBm | -82 dBm | -137 dBm |
| 最大路径损耗 | 122 dB | 106 dB | 155 dB |
| 自由空间覆盖 | ~3.5 km | ~0.3 km | ~20 km |
| 城市覆盖 (实测) | 1-1.5 km | 50-80 m | 2-5 km |

---

## 3. MAC 层省电机制：TWT 与 RAW

### 3.1 TWT（Target Wake Time）

TWT 是 WiFi HaLow 和 WiFi 6 共享的省电机制，但 HaLow 的 TWT 实现针对 IoT 做了专门优化。

工作原理：设备在入网时和 AP 协商一个"唤醒时间表"。比如每 10 分钟唤醒一次，传 50 字节温度数据，然后立即回到深度睡眠。AP 会缓存发给该设备的下行数据，等设备唤醒时一起推送。

```
时间轴：
AP:     [---beacon---][---beacon---][---beacon---][---beacon---]
设备:   [睡眠..........][唤醒|TX|RX][睡眠..........................][唤醒|TX|RX]
                         ↑ TWT SP                                   ↑ TWT SP
         10 min 间隔                    10 min 间隔
```

典型功耗数据（Morse Micro MM6108 实测）：

| 状态 | 电流 (@ 3.3V) |
|------|-------------|
| 深度睡眠 | 1.2 μA |
| TWT 唤醒监听 | 18 mA |
| 数据接收 | 42 mA |
| 数据发送 (14 dBm) | 280 mA |
| 数据发送 (0 dBm) | 85 mA |

假设每 15 分钟唤醒一次，每次活跃 50 ms（发 100 字节 + 收 ACK），使用 2× AA 电池（3000 mAh, 3V）：

- 活跃期平均电流：(42 + 280) / 2 ≈ 161 mA，持续 50 ms
- 休眠期电流：1.2 μA，持续 ~15 min
- 每周期平均电流：(161 × 0.05 + 0.0012 × 899.95) / 900 ≈ 0.01 mA
- 理论电池寿命：3000 / 0.01 / 24 / 365 ≈ **34 年**（理想值，实际因自放电约 8-12 年）

### 3.2 RAW（Restricted Access Window）

RAW 是 WiFi HaLow 独有的 MAC 层机制，专门解决大量设备同时竞争信道的"惊群效应"。

问题场景：假设一栋大楼里有 2000 个传感器连接到同一个 HaLow AP。如果 AP 发一个 beacon，所有设备都在同一时刻竞争信道，碰撞会非常严重。

RAW 的解决方案：AP 把时间分成多个"窗口"（RAW slot），每个窗口只允许一组设备访问信道。

```
Beacon 间隔 (1 秒)
├── RAW 1: 设备组 A (ID 0-499)    [250ms]
├── RAW 2: 设备组 B (ID 500-999)   [250ms]
├── RAW 3: 设备组 C (ID 1000-1499) [250ms]
└── RAW 4: 设备组 D (ID 1500-1999) [250ms]
```

RAW 和 TWT 可以组合使用：设备只在自己被分配的 RAW 窗口内唤醒，其他时间全部休眠。

实际效果（来自 2024 年学术仿真数据）：

| 设备数量 | 不用 RAW 吞吐量 | 用 RAW 吞吐量 | 提升 |
|---------|---------------|-------------|------|
| 100 | 1.8 Mbps | 1.9 Mbps | 5% |
| 500 | 0.9 Mbps | 1.7 Mbps | 89% |
| 2000 | 0.1 Mbps | 1.4 Mbps | 14× |
| 6000 | ~0 (崩溃) | 1.1 Mbps | ∞ |

---

## 4. 与 LoRa 和 NB-IoT 的深度对比

WiFi HaLow、LoRaWAN 和 NB-IoT 是三种覆盖 1 km 以上的 IoT 无线技术，但它们的设计哲学完全不同。

### 4.1 核心差异总结

| 维度 | WiFi HaLow | LoRaWAN | NB-IoT |
|------|-----------|---------|--------|
| 频段 | Sub-GHz (免授权) | Sub-GHz (免授权) | 授权频段 (运营商) |
| 网络架构 | 星型 (AP-STA) | 星型 (GW-Node) | 蜂窝 (基站-终端) |
| 协议栈 | TCP/IP 原生 | LoRaWAN 专有 | 3GPP LTE 子集 |
| 最大速率 | 32.67 Mbps | 50 kbps | 127 kbps (DL) |
| 典型延迟 | 10-100 ms | 1-10 s | 1-5 s |
| 部署成本 | AP 硬件 (~$200) | 网关 (~$300) + NS | SIM + 月租 ($0.5-2/月) |
| OTA 固件升级 | 原生支持 (高速) | 极慢 (数小时) | 支持但速率有限 |
| 双向通信 | 全双工 | 受限 (Class A/B/C) | 全双工 |
| 安全性 | WPA3 | AES-128 | LTE 级 |
| 标准组织 | IEEE / WiFi 联盟 | LoRa 联盟 | 3GPP |

### 4.2 场景适配矩阵

| 应用场景 | 最佳选择 | 原因 |
|---------|---------|------|
| 远程农田土壤监测 (5km) | LoRaWAN | 超远距离，极低数据量 |
| 智慧楼宇环境传感 (500m) | WiFi HaLow | IP 直连，中等数据量，OTA 便捷 |
| 安防摄像头 (1km) | WiFi HaLow | 需要 Mbps 级带宽 |
| 智能水表 (城区全覆盖) | NB-IoT | 运营商基础设施现成 |
| 工厂无线传感器 (大面积) | WiFi HaLow | 私有网络，低延迟 |
| 跨国资产追踪 | NB-IoT | 全球蜂窝漫游 |

### 4.3 总拥有成本 (TCO) 分析

以部署 1000 个传感器、覆盖 2 km² 园区为例，5 年 TCO 估算：

| 成本项 | WiFi HaLow | LoRaWAN | NB-IoT |
|-------|-----------|---------|--------|
| 终端芯片 (×1000) | $5/个 = $5,000 | $3/个 = $3,000 | $4/个 = $4,000 |
| AP/网关 (×3-5) | $200×5 = $1,000 | $300×3 = $900 | $0 (用运营商网络) |
| 网络服务器 | $0 (直连) | $500/年×5 = $2,500 | $0 |
| 通信月租 | $0 | $0 | $1×1000×60 = $60,000 |
| 安装调试 | $3,000 | $3,000 | $1,000 |
| **5 年总计** | **~$9,000** | **~$9,400** | **~$65,000** |

结论：在私有网络场景，WiFi HaLow 和 LoRaWAN 的 TCO 相近，但 HaLow 在速率和双向通信上有明显优势。NB-IoT 的优势在于无需自建网络，但持续月租费在大规模部署时代价高昂。

---

## 5. 芯片生态与开发平台

### 5.1 主要芯片厂商

截至 2025 年，WiFi HaLow 的芯片生态仍然较窄，但正在快速扩展：

| 厂商 | 芯片型号 | 特点 | 状态 |
|------|---------|------|------|
| Morse Micro (澳) | MM6108 | 业界最低功耗，集成 PA/LNA，支持 1-8 MHz | 量产中 |
| Newracom (韩) | NRC7394 | 高集成度 SoC，内置 MCU | 量产中 |
| Renesas | — | 2024 年宣布 HaLow SoC 路线图 | 开发中 |
| Espressif | — | 传闻中的 HaLow 产品线 | 未确认 |

Morse Micro MM6108 是目前市场占有率最高的 HaLow 芯片，其关键参数：

- 封装：QFN 5×5 mm
- 集成度：RF + 基带 + PA + LNA + PMU
- 发射功率：最高 +21 dBm (美国)，+14 dBm (欧洲/中国)
- 接收灵敏度：-104 dBm (MCS0, 1 MHz)
- 深度睡眠电流：< 1.5 μA
- 安全：WPA3-SAE，TLS 1.3 硬件加速
- 接口：SPI/SDIO（作为外挂 WiFi 模组连接主控 MCU）

### 5.2 开发板和 SDK

```
典型开发架构：

┌──────────────┐     SPI/SDIO     ┌──────────────┐
│  主控 MCU     │ ◄─────────────► │  HaLow 模组   │
│  (ESP32/STM32)│                  │  (MM6108)     │
│  应用逻辑     │                  │  WiFi HaLow   │
│  TCP/IP 栈    │                  │  MAC + PHY    │
└──────────────┘                  └──────────────┘
       │
       ▼
   传感器/执行器
```

Morse Micro 提供的 SDK 支持 FreeRTOS 和 Linux 两种模式，开发流程与标准 WiFi 模组类似。核心区别在于需要配置 Sub-GHz 频段参数：

```c
/* HaLow 连接配置示例 (基于 Morse Micro SDK 伪代码) */
#include "mmwlan.h"

static mmwlan_config_t halow_config = {
    .country_code = "CN",           /* 决定可用频段 755-787 MHz */
    .channel_bandwidth = BW_1MHZ,   /* 1 MHz 窄带，最远距离 */
    .mcs = MCS_AUTO,                /* 自动速率适配 */
    .twt_enabled = true,
    .twt_wake_interval_ms = 600000, /* 每 10 分钟唤醒一次 */
    .twt_wake_duration_ms = 100,    /* 每次活跃 100ms */
    .security = WPA3_SAE,
    .max_stations = 2048,           /* AP 模式下最大连接数 */
};

void app_main(void) {
    mmwlan_init(&halow_config);
    mmwlan_connect("HaLow-AP", "password123");
    
    while (1) {
        float temp = read_sensor();
        /* 直接用 TCP/UDP 发送，与普通 WiFi 编程完全一致 */
        udp_send("192.168.1.100", 8080, &temp, sizeof(temp));
        mmwlan_enter_twt_sleep();  /* 进入 TWT 深睡 */
    }
}
```

---

## 6. 部署注意事项与常见问题

### 6.1 天线设计

Sub-GHz 天线比 2.4 GHz 天线大得多（四分之一波长天线：~8 cm vs ~3 cm），这影响了终端设备的外形设计。常见方案：

- **PCB 天线**：成本低，增益 1-2 dBi，适合短距离场景
- **弹簧天线**：小尺寸，增益 1.5-2.5 dBi，适合嵌入式场景
- **外置鞭状天线**：增益 3-5 dBi，适合远距离 AP 端
- **定向天线（Yagi）**：增益 8-12 dBi，适合点对点远距离链路

### 6.2 与 LoRa 共存

WiFi HaLow 和 LoRa 使用相同的 Sub-GHz 频段，共存是一个实际问题。好消息是两者的信号特征差异很大，互相干扰有限：

- LoRa 使用啁啾扩频，WiFi HaLow 使用 OFDM——调制方式完全不同
- HaLow 使用 CSMA/CA 先听后发，能检测到 LoRa 信号并退避
- LoRa 的扩频增益能抵抗 HaLow 信号的干扰

实际建议：在同一区域混合部署时，尽量给 HaLow 和 LoRa 分配不同的频率子段。

### 6.3 监管合规

Sub-GHz 频段的监管限制比 2.4 GHz 更复杂：

- **欧洲**：863-868 MHz 频段有严格的占空比限制（1% 或 10%），这会限制 HaLow 的吞吐量
- **美国**：902-928 MHz 频段要求跳频扩频（FHSS）或数字调制，HaLow 的 OFDM 满足数字调制要求
- **中国**：755-787 MHz 频段需要设备型号核准（SRRC 认证），发射功率限制 50 mW (17 dBm)

---

## 7. 实践建议

### 7.1 初学者入门路径

1. **了解基础**：先熟悉 WiFi 基本原理（CSMA/CA, OFDM, 关联过程），HaLow 的 MAC 层与 802.11ac/ax 80% 相同
2. **获取开发板**：购买 Morse Micro 或 Newracom 的开发套件（含 AP + STA 各一块，约 $150-300）
3. **跑通 Hello World**：用 SDK 建立 HaLow 连接，发送第一个 UDP 数据包
4. **测量覆盖距离**：在实际部署环境中测试不同 MCS 和带宽配置的覆盖距离
5. **优化功耗**：启用 TWT，测量不同唤醒间隔下的实际电池寿命
6. **对比测试**：如果你也有 LoRa 模组，在同一场景下做 A/B 对比

### 7.2 具体调优建议

- **信道带宽选择**：默认从 1 MHz 开始，只在确认距离足够的前提下提升到 2/4 MHz
- **MCS 自适应**：让 AP 自动调整 MCS。手动锁定 MCS 只在极端场景（如超远距离固定链路）使用
- **TWT 间隔**：根据业务需求设置，不要盲目追求超长睡眠——15 分钟间隔通常足够，30 分钟以上需要考虑 AP 缓冲区溢出
- **RAW 配置**：设备超过 200 台时开启 RAW 分组；分组策略可按 AID 范围、按流量类型、或按地理位置
- **安全**：必须启用 WPA3-SAE，不要使用开放网络——Sub-GHz 信号覆盖范围大意味着攻击面也大

---

## 参考文献

1. IEEE. "IEEE 802.11ah-2016: Sub 1 GHz License Exempt Operation," IEEE Standard, 2016.
2. WiFi Alliance. "Wi-Fi HaLow Technology Overview," wifi.org, 2024.
3. T. Adame et al., "IEEE 802.11ah: The WiFi Approach for M2M Communications," IEEE Wireless Communications, vol. 21, no. 6, pp. 144-152, 2014.
4. Morse Micro. "MM6108 Wi-Fi HaLow SoC Datasheet," Rev 2.1, 2024.
5. V. Baños-Gonzalez et al., "RAW Optimization in IEEE 802.11ah for Dense IoT Deployments," IEEE Internet of Things Journal, vol. 11, no. 3, 2024.
6. L. Tian et al., "Wi-Fi HaLow for IoT: A Performance Evaluation Against LoRaWAN and NB-IoT," IEEE Access, vol. 12, pp. 45678-45693, 2024.
7. Newracom. "NRC7394 Wi-Fi HaLow SoC Technical Reference Manual," 2023.
8. S. Aust et al., "Sub-1GHz WiFi for the Internet of Things – Design Challenges and Trends," Proc. IEEE LCN, 2023.
9. WiFi Alliance. "Wi-Fi HaLow R2 Specification," 2024.
10. Y. Zeng et al., "Coexistence of IEEE 802.11ah and LoRa in Sub-GHz ISM Bands," IEEE Communications Letters, vol. 28, no. 1, 2024.
