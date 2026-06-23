# Sub-GHz 频段技术对比：穿墙利器的选择之道

> **难度**：🟡 中级 | **领域**：LPWAN、射频传播、IoT 部署 | **阅读时间**：约 20 分钟

## 日常类比

声音有高音和低音之分。高音（像口哨声）清脆但穿不过隔壁房间；低音（像低音炮）能穿过好几面墙震到隔壁邻居。无线电波同理——2.4 GHz 就像高音，频率高但容易被墙壁吸收；Sub-GHz（低于 1 GHz）就像低音，频率低、波长长，轻松绕过障碍物，覆盖距离远得多。

这就是为什么你的 WiFi 信号到隔壁房间就弱了，但 FM 广播（88-108 MHz）在室内任何角落都清晰。Sub-GHz IoT 技术利用的正是这种物理优势。

当然，低频段也有代价——带宽窄意味着数据速率低。这对 IoT 传感器来说反而是优势：一个水表每天只需上报几十字节，用 Sub-GHz 一次传输就到了基站，完全不需要高速率。

## 1. Sub-GHz 频段监管规则

### 1.1 全球主要 Sub-GHz ISM 频段

| 频段 | 地区 | 带宽 | 最大发射功率 | 占空比限制 |
|------|------|------|-------------|-----------|
| 433.05-434.79 MHz | 全球（ITU Region 1） | 1.74 MHz | 10 mW ERP (EU) | 10% |
| 470-510 MHz | 中国 | 40 MHz | 50 mW | 1%（部分子带） |
| 863-870 MHz | 欧洲 (EU) | 7 MHz | 25 mW (g1) / 500 mW (g3) | 0.1%-10% |
| 902-928 MHz | 美国/加拿大 | 26 MHz | 1 W (FHSS) / 0.25 W | 无（FHSS） |
| 915-928 MHz | 澳大利亚 | 13 MHz | 1 W EIRP | 无 |
| 920-925 MHz | 日本/韩国 | 5 MHz | 20 mW | LBT 必须 |

### 1.2 中国频段详解

中国 Sub-GHz IoT 可用频段：

- **470-510 MHz**：主要用于 LoRaWAN CN470 频率计划，共有 96 个 125 kHz 上行信道
- **433 MHz**：小功率设备可用，但干扰较多（遥控器、对讲机共用）
- **779-787 MHz**：微功率设备，限制 10 mW
- **注意**：中国没有 868/915 MHz ISM 频段

### 1.3 功率与占空比对部署的影响

```python
# 计算不同地区占空比下的日最大发送时间
def max_airtime_per_day(duty_cycle_percent):
    """给定占空比，计算每天最多可发送多长时间"""
    seconds_per_day = 24 * 3600
    return seconds_per_day * duty_cycle_percent / 100

# 欧洲 868 MHz g1 子带 (1% duty cycle)
eu_g1 = max_airtime_per_day(1.0)
print(f"EU 868 g1 (1%): {eu_g1:.0f}s/天 = {eu_g1/60:.1f}min/天")
# 输出: 864s/天 = 14.4min/天

# 欧洲 868 MHz g3 子带 (10% duty cycle, 500mW)
eu_g3 = max_airtime_per_day(10.0)
print(f"EU 868 g3 (10%): {eu_g3:.0f}s/天 = {eu_g3/60:.1f}min/天")
# 输出: 8640s/天 = 144min/天

# 美国 915 MHz FHSS (无占空比限制)
print("US 915 FHSS: 无限制（前提是跳频 >= 50 信道，dwell < 0.4s）")

# LoRa SF12 单包空中时间 (10 bytes payload, 125kHz BW)
# ToA = 1.318s (EU) — 1% DC下每天只能发 ~655 包
toa_sf12 = 1.318  # seconds
packets_per_day_eu = eu_g1 / toa_sf12
print(f"SF12 10B payload: ToA={toa_sf12}s, EU 1% DC下 {packets_per_day_eu:.0f} 包/天")
```

## 2. 传播特性与链路预算

### 2.1 自由空间路径损耗对比

```
FSPL(dB) = 20*log10(d) + 20*log10(f) + 32.44
其中 d 单位为 km, f 单位为 MHz
```

| 距离 | 433 MHz | 868 MHz | 915 MHz | 2400 MHz |
|------|---------|---------|---------|----------|
| 100m | 64.2 dB | 70.2 dB | 70.7 dB | 79.0 dB |
| 1 km | 84.2 dB | 90.2 dB | 90.7 dB | 99.0 dB |
| 5 km | 98.1 dB | 104.1 dB | 104.6 dB | 112.9 dB |
| 10 km | 104.2 dB | 110.2 dB | 110.7 dB | 119.0 dB |

关键结论：Sub-GHz 相比 2.4 GHz 在相同距离上路径损耗低 8-15 dB，等效于覆盖距离提升 2.5-5 倍。

### 2.2 穿透损耗对比

实测数据（2024 年欧洲城市环境）：

| 障碍物 | 433 MHz | 868 MHz | 2.4 GHz |
|--------|---------|---------|---------|
| 内墙（石膏板） | 3 dB | 4 dB | 5 dB |
| 外墙（混凝土 20cm） | 10 dB | 14 dB | 20 dB |
| 楼层（钢筋混凝土） | 15 dB | 18 dB | 25 dB |
| 地下室（穿 2 层楼板） | 28 dB | 34 dB | 48 dB |
| 电梯井（金属） | 25 dB | 30 dB | 40+ dB |

### 2.3 城市与农村实测覆盖

| 环境 | LoRa 868MHz SF12 | Sigfox 868MHz | 2.4GHz BLE LR |
|------|-------------------|---------------|---------------|
| 密集城区 | 2-5 km | 3-8 km | 200-400 m |
| 郊区 | 5-10 km | 8-15 km | 500-800 m |
| 农村开阔 | 10-20 km | 15-40 km | 1-1.5 km |
| 水面 | 20-30 km | 30-50 km | 2-3 km |

## 3. Sub-GHz 技术横向对比

### 3.1 主流技术对比表

| 特性 | LoRa/LoRaWAN | Sigfox | Z-Wave LR | Wi-SUN | DECT-2020 NR+ |
|------|-------------|--------|-----------|--------|---------------|
| 频段 | 433/470/868/915 | 868/915 | 908/868 | 470/868/915 | 1880-1900 MHz |
| 调制方式 | CSS | DBPSK/GFSK | FSK | FSK/OFDM | OFDM |
| 最大速率 | 50 kbps (SF5) | 600 bps | 100 kbps | 300 kbps | 1.2 Mbps |
| 典型覆盖 | 5-15 km | 10-40 km | 1.6 km | 1-3 km | 500 m |
| 拓扑 | 星形 | 星形 | Mesh | Mesh | Mesh/Star |
| 设备电池寿命 | 5-10 年 | 5-12 年 | 5-10 年 | 3-5 年 | 10+ 年 |
| 单网关容量 | ~20K 设备 | N/A(运营商) | 4000 节点 | 1000 节点 | 数千 |
| 双向通信 | 有限(Class A/B/C) | 极有限(4 DL/天) | 完整 | 完整 | 完整 |
| 适用场景 | 远距离遥测 | 资产追踪 | 智能家居 | 智慧城市/电网 | 智能楼宇 |

### 3.2 LoRa 详解

LoRa 使用啁啾扩频（CSS）调制，通过扩频因子（SF7-SF12）在速率和距离间灵活权衡：

| SF | 比特率(125kHz BW) | 灵敏度 | 10B ToA | 等效覆盖提升 |
|----|-------------------|--------|---------|-------------|
| SF7 | 5470 bps | -123 dBm | 56 ms | 基准 |
| SF8 | 3125 bps | -126 dBm | 103 ms | +1.5 dB |
| SF9 | 1760 bps | -129 dBm | 185 ms | +3 dB |
| SF10 | 977 bps | -132 dBm | 370 ms | +4.5 dB |
| SF11 | 537 bps | -134.5 dBm | 659 ms | +5.75 dB |
| SF12 | 293 bps | -137 dBm | 1318 ms | +7 dB |

### 3.3 Sigfox 特点

Sigfox 采用超窄带（UNB）技术，每条消息仅占 100 Hz 带宽。优势是极高的链路预算（164 dB），单基站覆盖半径可达 40 km（农村）。劣势是每天仅允许 140 条上行、4 条下行消息，每条最多 12 字节。2024 年 Sigfox 经历破产重组后由 UnaBiz 接管，网络仍在运营但扩展放缓。

### 3.4 Wi-SUN（Wireless Smart Utility Networks）

Wi-SUN 是 IEEE 802.15.4g 的商业品牌，主攻智能电网和智慧城市。其关键特点是支持 IPv6 mesh 组网、可扩展到数千节点、由电力公司主导部署。日本东京已部署超 3000 万 Wi-SUN 智能电表。

## 4. 天线设计

### 4.1 Sub-GHz 天线挑战

低频段意味着更长的波长——433 MHz 四分之一波长天线长约 17 cm，868 MHz 约 8.6 cm。对于小型 IoT 设备，天线尺寸是主要约束。

常见方案：

| 天线类型 | 尺寸 (868 MHz) | 增益 | 适用场景 |
|----------|---------------|------|----------|
| 四分之一波长鞭状 | 8.6 cm | 2 dBi | 外置天线设备 |
| PCB 蛇形天线 | 3-5 cm | -2 to 0 dBi | 紧凑型设备 |
| 陶瓷贴片天线 | 10x5 mm | -3 to -1 dBi | 极小型模块 |
| 螺旋天线 | 2-3 cm 高 | 1-2 dBi | 圆柱形外壳 |
| 倒 F 天线（IFA） | 4 cm | 0-1 dBi | 平板设备 |

### 4.2 天线匹配网络

```
         L-match 网络
信号源 ---[L1]---+--- 天线
               |
              [C1]
               |
              GND

L1 = 典型 6.8-15 nH (868 MHz)
C1 = 典型 1-3.3 pF (868 MHz)
目标: 将天线阻抗匹配到 50 ohm
```

实际开发中，使用矢量网络分析仪（VNA）测量 S11 参数，目标是在工作频率处 S11 < -10 dB（即回波损耗优于 10 dB，90% 以上功率辐射出去）。

## 5. 共存与干扰问题

### 5.1 Sub-GHz 频段干扰源

433 MHz 频段尤其拥挤：汽车遥控钥匙、气象站、婴儿监视器、对讲机、无线门铃等设备都在此频段工作。

868/915 MHz 相对"干净"，但随着 LoRaWAN 和 Sigfox 设备增长，未来密集部署区也会面临自干扰问题。

### 5.2 干扰缓解策略

| 策略 | 原理 | 适用技术 |
|------|------|----------|
| 跳频（FHSS） | 信号在多个频点间跳跃 | US 915 MHz LoRa |
| 自适应数据率（ADR） | 根据信道质量调整 SF/功率 | LoRaWAN |
| LBT（先听后发） | 发送前检测信道是否空闲 | Wi-SUN, 日本法规要求 |
| 时分复用 | 设备在预分配时隙发送 | DECT-2020 |
| 空间分集 | 多网关接收，选最优 | LoRaWAN/Sigfox |

### 5.3 LoRaWAN ADR 算法简化实现

```python
class SimpleADR:
    """简化版 LoRaWAN ADR 算法"""

    # 所需 SNR 余量表 (dB above demod floor)
    SNR_MARGIN = {7: -7.5, 8: -10, 9: -12.5, 10: -15, 11: -17.5, 12: -20}
    TARGET_MARGIN = 10  # dB 目标余量

    def __init__(self):
        self.snr_history = []  # 最近 20 包 SNR

    def update(self, snr_measured: float, current_sf: int, current_tx_power: int):
        """根据最新 SNR 计算建议的 SF 和功率"""
        self.snr_history.append(snr_measured)
        if len(self.snr_history) < 20:
            return current_sf, current_tx_power  # 数据不足，不调整

        # 取最近 20 包的最大 SNR
        max_snr = max(self.snr_history[-20:])
        snr_floor = self.SNR_MARGIN[current_sf]
        margin = max_snr - snr_floor - self.TARGET_MARGIN

        new_sf = current_sf
        new_power = current_tx_power

        # margin > 0: 信号过好，可降低 SF 或功率
        while margin > 0 and new_sf > 7:
            new_sf -= 1
            margin -= 2.5  # 每降一级 SF 约需多 2.5 dB

        while margin > 0 and new_power > 2:
            new_power -= 2  # 每步降 2 dBm
            margin -= 2

        return new_sf, new_power
```

## 6. 实际部署案例

### 6.1 智慧水务（LoRa 470 MHz，中国）

某省会城市自来水公司部署方案：15 万只 LoRa 水表，200 个网关覆盖 800 km2 城区。使用 CN470 频率计划（470-510 MHz），SF10 为主，地下井覆盖使用 SF12。实测抄表成功率 99.2%，电池寿命 8 年（每天上报 2 次）。

### 6.2 农业监测（Sigfox 868 MHz，法国）

葡萄园土壤湿度监测：每个传感器每小时上报一次（12 字节），单基站覆盖 20 km2。设备成本（含 Sigfox 5 年套餐）约 30 欧元/个。2000 个传感器替代了人工巡检，节水 30%。

### 6.3 智能家居（Z-Wave 908 MHz，北美）

典型家庭部署 30-50 个 Z-Wave 设备（门锁、灯开关、传感器）。Mesh 组网确保全屋覆盖，最远节点通过 2-3 跳到达控制器。Z-Wave Long Range（2020 年推出）将覆盖扩展到 1.6 km（户外），支持星形拓扑直连。

## 7. 实践建议

### 7.1 初学者入门路径

1. 入门选择：LoRa 开发套件（如 Heltec WiFi LoRa 32 V3，约 80 元）是最佳起点，社区资源丰富
2. 频段选择：中国用户选 CN470 频率计划；如做出口产品，EU868 和 US915 双频段支持
3. 实测练习：在城市环境中实测不同 SF 的覆盖距离，建立直觉
4. 对比实验：同一位置分别用 Sub-GHz LoRa 和 2.4 GHz BLE 发送，体会穿墙差异

### 7.2 具体调优建议

链路预算计算是 Sub-GHz 部署的核心技能。公式为：最大允许路径损耗 = 发射功率(dBm) + 发射天线增益(dBi) + 接收天线增益(dBi) - 接收灵敏度(dBm) - 余量(dB)。以 LoRa SF12 为例：14 + 2 + 6 - (-137) - 10 = 149 dB 链路预算。对应自由空间约 40 km，城市环境实际 3-8 km。

天线放置方面，网关天线尽可能高（楼顶最佳）。终端天线避免被金属外壳包裹。PCB 天线需确保净空区（ground clearance）足够——至少天线下方 5mm 无铜层。

频率规划方面，多网关部署时使用不同频率组避免自干扰。LoRaWAN CN470 有 8 个子频段，按地理区域分配。上行和下行使用不同频段（CN470 上行 470-490，下行 500-510）。

## 参考文献

1. ETSI EN 300 220, "Short Range Devices operating in the frequency range 25 MHz to 1 GHz," v3.2.1, 2024.
2. FCC Part 15.247, "Operation within the bands 902-928 MHz, 2400-2483.5 MHz," 2023.
3. 中国工信部, "微功率短距离无线电发射设备目录和技术要求," 2019 (修订 2023).
4. LoRa Alliance, "LoRaWAN Regional Parameters RP002-1.0.4," 2024.
5. Mekki, K., et al., "A Comparative Study of LPWAN Technologies," ICT Express, 2019.
6. Sigfox/UnaBiz, "Sigfox Technical Overview," v2.1, 2024.
7. Wi-SUN Alliance, "Wi-SUN FAN 1.1 Technical Profile Specification," 2023.
8. Z-Wave Alliance, "Z-Wave Long Range Technical Whitepaper," 2023.
9. Petajajarvi, J., et al., "On the Coverage of LPWANs: Range Evaluation and Channel Attenuation Model for LoRa Technology," ITS Telecommunications, 2015.
10. Augustin, A., et al., "A Study of LoRa: Long Range and Low Power Networks for IoT," Sensors, vol. 16, 2016.
