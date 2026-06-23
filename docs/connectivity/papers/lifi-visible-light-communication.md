# 可见光通信 LiFi 技术：用灯光传数据

> **难度**：🟡 中级 | **领域**：短距无线通信、光通信 | **阅读时间**：约 18 分钟

---

## 日常类比

你在交通路口等红灯时，红黄绿灯告诉你"停"、"准备"、"走"——这就是最原始的可见光通信，用光的亮灭传递信息。LiFi 做的事情本质上和红绿灯一样：让 LED 灯泡在人眼不可察觉的速度下快速闪烁（每秒数百万次），把数据编码进光信号中。

你可以把家里的 LED 吸顶灯想象成一个"光路由器"。它在正常照明的同时，以极高的频率调制亮度，房间里的笔记本电脑上有一个光电探测器（类似手机的光线传感器），接收这些光信号并还原成数据。和 WiFi 不同的是，光穿不过墙壁，所以你的"网络"天然被限制在一个房间内——这既是缺点（移动性差），也是优点（物理层安全性极高，隔壁邻居无法窃听）。

在工厂场景中，WiFi 信号经常被金属设备反射干扰，而工厂照明本来就到处都是——如果这些灯同时就是通信基站，不仅不增加额外设备成本，还避开了射频干扰问题。这就是 LiFi 在工业 IoT 中被认真考虑的根本原因。

---

## 1. LiFi 基本原理

### 1.1 LED 调制方式

LiFi 的核心是让 LED 光源的亮度变化携带信息。人眼对超过 200 Hz 的闪烁已无法察觉，而 LED 的开关速度可以达到 MHz 甚至 GHz 级别，这个巨大的"感知盲区"就是可用的通信带宽。

常用的调制方案从简单到复杂排列：

| 调制方式 | 原理 | 典型速率 | 实现复杂度 |
|---------|------|---------|-----------|
| OOK (On-Off Keying) | 亮=1，灭=0 | ~100 Mbps | 最低 |
| VPPM (Variable PPM) | 脉冲位置编码+调光 | ~200 Mbps | 低 |
| OFDM | 多载波并行传输 | 1-10 Gbps | 高 |
| CAP (Carrierless Amplitude Phase) | 振幅相位联合调制 | ~5 Gbps | 中高 |
| Optical MIMO | 多LED多探测器空间复用 | >10 Gbps | 最高 |

**OOK** 是最直观的方案：LED 亮代表比特"1"，灭代表比特"0"。实现极其简单，一个 GPIO 引脚驱动 LED 就行。但问题也很明显——频谱利用率低，且长串的"0"会导致灯变暗，影响照明功能。改进方案是用 Manchester 编码保证直流平衡。

**OFDM** 是目前高速 LiFi 的主流方案。原理和 WiFi、4G/5G 的 OFDM 完全一致：将宽带信道划分为多个窄带子载波，每个子载波独立调制。不同点在于，光通信中信号必须是实值且非负的（LED 亮度不能为负数），所以使用 DCO-OFDM（DC-biased Optical OFDM）或 ACO-OFDM（Asymmetrically Clipped）。

```python
import numpy as np

def dco_ofdm_modulate(data_symbols, n_subcarriers=64, dc_bias=7.0):
    """DCO-OFDM 调制示例
    
    关键：对子载波施加 Hermitian 对称，确保 IFFT 输出为实值；
    加 DC 偏置使信号非负，适配 LED 驱动。
    """
    # 构造 Hermitian 对称的频域信号
    X = np.zeros(n_subcarriers, dtype=complex)
    n_data = n_subcarriers // 2 - 1
    X[1:n_data+1] = data_symbols[:n_data]                    # 正频率
    X[n_data+1:] = np.conj(data_symbols[:n_data][::-1])      # 负频率镜像
    
    # IFFT 得到时域实信号
    x_time = np.fft.ifft(X).real
    
    # 加 DC 偏置使信号非负（LED 亮度 >= 0）
    x_biased = x_time + dc_bias
    x_clipped = np.clip(x_biased, 0, None)  # 负值截断为 0
    
    return x_clipped
```

### 1.2 LED 带宽限制与预均衡

商用磷光白光 LED 的调制带宽只有约 3-5 MHz——这是 LiFi 工程中最大的瓶颈之一。磷光体的慢响应特性严重限制了可用带宽。

解决方案有三种思路：

**蓝光滤波**：在接收端加蓝光滤波器，只接收 LED 的蓝光成分（蓝光 LED 芯片的带宽约 20 MHz），滤掉慢速磷光成分。代价是接收功率降低约 50%。

**模拟预均衡**：在发射端加一个高通滤波电路，增强高频分量以补偿 LED 的低通特性。可以将有效带宽从 3 MHz 扩展到 50 MHz 以上。

**数字预均衡**：用 DSP 算法做信道预补偿。2024 年牛津大学的实验中，结合 bit-loading OFDM 和自适应预均衡，单颗商用 LED 达到了 15.73 Gbps 的传输速率。

---

## 2. 接收端设计

### 2.1 光电探测器选型

接收端的核心是光电探测器（Photodetector, PD），将光信号转换为电信号。IoT 场景中常用的有三种：

| 类型 | 带宽 | 灵敏度 | 成本 | 适用场景 |
|------|------|--------|------|---------|
| PIN 光电二极管 | ~1 GHz | 中 | 低（<$1） | 通用 LiFi 终端 |
| APD（雪崩光电二极管）| ~2 GHz | 高（增益 10-100×）| 中（$5-20） | 长距离/弱光 |
| SiPM / SPAD | ~100 MHz | 极高（单光子级）| 高（$50+） | 超灵敏场景 |
| CMOS 图像传感器 | ~10 kHz | 低 | 极低（手机自带） | 低速场景 |

PIN 光电二极管是 LiFi 产品中的标准选择，它在带宽、成本和灵敏度之间取得了最佳平衡。接收面积越大，接收到的光功率越多（灵敏度高），但寄生电容也越大（带宽低）——这是一对根本矛盾。

一种折衷方案是使用**光学集中器**（compound parabolic concentrator, CPC）：用小面积 PD 配合大口径光学透镜，在不增加 PD 面积的前提下增大等效接收面积。2024 年 pureLiFi 的产品中使用了 0.7mm² PIN PD + 集成透镜，等效接收面积达到 10mm²。

### 2.2 前端模拟电路

PD 输出的是微安级光电流，需要跨阻放大器（TIA）转换为电压信号。TIA 设计的核心指标是带宽和噪声的折衷：

```c
// TIA 等效噪声计算（简化模型）
// 输入等效噪声电流 = 热噪声 + 散粒噪声

#include <math.h>

typedef struct {
    double responsivity;    // PD 响应度 (A/W)，典型 0.4
    double area_mm2;        // PD 面积 (mm²)
    double bandwidth_mhz;   // TIA 带宽 (MHz)
    double feedback_kohm;   // 反馈电阻 (kΩ)
} lifi_receiver_t;

double calc_snr_db(lifi_receiver_t *rx, double optical_power_dbm) {
    double P_opt = pow(10, optical_power_dbm / 10) * 1e-3; // dBm -> W
    double I_sig = rx->responsivity * P_opt;                // 信号电流
    
    double q = 1.602e-19;
    double kB = 1.381e-23;
    double T = 300;
    double BW = rx->bandwidth_mhz * 1e6;
    double Rf = rx->feedback_kohm * 1e3;
    
    // 散粒噪声
    double i_shot_sq = 2 * q * I_sig * BW;
    // TIA 热噪声
    double i_thermal_sq = 4 * kB * T * BW / Rf;
    
    double snr = (I_sig * I_sig) / (i_shot_sq + i_thermal_sq);
    return 10 * log10(snr);
}
```

---

## 3. LiFi vs WiFi：不是替代而是互补

### 3.1 性能对比

| 指标 | LiFi (802.11bb) | WiFi 6E/7 (802.11be) |
|------|-----------------|---------------------|
| 频谱 | 380-780 nm（~400 THz 带宽） | 2.4/5/6 GHz（~1 GHz 带宽） |
| 实验室峰值速率 | 224 Gbps (MIMO) | 46 Gbps |
| 实用速率 | 100-1000 Mbps | 1-10 Gbps |
| 延迟 | <1 ms | 1-10 ms |
| 覆盖范围 | 3-5 米（单灯） | 30-50 米 |
| 穿墙能力 | 无 | 有 |
| 频谱许可 | 不需要 | 需要（部分频段） |
| 安全性 | 天然物理隔离 | 需加密协议 |
| 功耗（终端） | 100-300 mW | 500-2000 mW |
| 干扰 | 阳光/强光源 | 其他 WiFi/蓝牙/微波炉 |

### 3.2 混合 RF/VLC 架构

实际部署中，LiFi 不会单独使用，而是与 WiFi 构成混合网络。IEEE 802.11bb 标准（2024 年正式发布）定义了 LiFi 作为 802.11 家族的一员，允许在同一网络架构中无缝切换 RF 和光链路。

典型的混合架构是：

- **下行用 LiFi**：高速数据（视频流、文件下载）通过天花板 LED 传输，带宽充裕
- **上行用 WiFi/IR**：终端的小功率 LED 或红外发射器向天花板回传数据
- **切换逻辑**：当用户移出 LiFi 覆盖区域（离开灯光照射范围），自动切回 WiFi

```python
class HybridRfVlcScheduler:
    """混合 RF/VLC 链路选择器"""
    
    def __init__(self, vlc_snr_threshold=15.0, hysteresis_db=3.0):
        self.vlc_threshold = vlc_snr_threshold  # VLC 最低可用 SNR (dB)
        self.hysteresis = hysteresis_db          # 防乒乓切换的迟滞量
        self.current_link = "wifi"
    
    def select_link(self, vlc_snr_db, wifi_snr_db, traffic_type):
        """根据信道质量和业务类型选择链路"""
        if traffic_type == "control":
            return "wifi"  # 控制信令始终走 RF（可靠性优先）
        
        if self.current_link == "wifi":
            # 从 WiFi 切到 VLC 需要信号足够好（加迟滞）
            if vlc_snr_db > self.vlc_threshold + self.hysteresis:
                self.current_link = "vlc"
        else:
            # 从 VLC 切回 WiFi 信号低于阈值即切
            if vlc_snr_db < self.vlc_threshold:
                self.current_link = "wifi"
        
        return self.current_link
```

---

## 4. 室内可见光定位

### 4.1 为什么 VLP 比 WiFi 定位更准？

WiFi 指纹定位的精度通常在 1-3 米，基于 WiFi RTT 的测距精度约 1 米。而可见光定位（VLP）可以轻松达到 10 cm 以下的精度，原因有二：

- **光不穿墙，多径效应弱**：WiFi 信号在室内反射严重，到达时间差（TDoA）被多径扭曲。光信号虽然也有漫反射，但强度远低于直射分量（通常低 20 dB 以上），对定位精度影响小。
- **LED 布局密集**：室内照明灯间距通常 2-3 米，且位置固定已知。每盏灯就是一个定位锚点，密度远高于 WiFi AP。

### 4.2 定位算法

主流 VLP 算法有三类：

**RSS（接收信号强度）定位**：测量接收到的光强度，利用朗伯辐射模型反推距离。需要至少 3 个 LED 的信号做三边定位。精度约 10-30 cm。

```python
import numpy as np
from scipy.optimize import minimize

def lambertian_channel_gain(d, phi, psi, m, A_pd, Ts, g_con):
    """朗伯信道增益模型
    d: LED-PD 距离, phi: 发射角, psi: 入射角
    m: 朗伯阶数 (半功率角60°时 m=1), A_pd: PD 面积
    Ts: 光学滤波器增益, g_con: 聚光器增益
    """
    if psi > np.pi/3:  # 超出 FOV
        return 0
    H = ((m + 1) * A_pd / (2 * np.pi * d**2)) * \
        np.cos(phi)**m * Ts * g_con * np.cos(psi)
    return H

def vlp_trilateration(led_positions, received_powers, led_power, m=1):
    """三边定位：已知 LED 位置和接收功率，求解接收器位置
    led_positions: shape (N, 3)，N >= 3
    received_powers: shape (N,)
    """
    def cost_function(pos_2d):
        x, y = pos_2d
        z_rx = 0.85  # 接收器高度（桌面）
        total_error = 0
        for i, (led_pos, p_rx) in enumerate(zip(led_positions, received_powers)):
            dx, dy = x - led_pos[0], y - led_pos[1]
            dz = z_rx - led_pos[2]
            d = np.sqrt(dx**2 + dy**2 + dz**2)
            cos_phi = abs(dz) / d
            H_est = ((m+1) / (2*np.pi*d**2)) * cos_phi**(m+1)
            p_est = led_power * H_est
            total_error += (p_rx - p_est)**2
        return total_error
    
    result = minimize(cost_function, x0=[2.0, 2.0], method='Nelder-Mead')
    return result.x
```

**TDoA 定位**：利用不同 LED 信号到达接收器的时间差定位，精度可达 5 cm 以下。但需要所有 LED 严格时间同步，实现成本高。

**基于图像传感器的定位**：用手机摄像头拍摄天花板 LED，通过图像中 LED 的位置分布直接计算相机姿态（类似视觉 SLAM）。不需要专用 PD，但速率低（受限于帧率）。

---

## 5. IEEE 802.11bb 标准与产业进展

### 5.1 802.11bb 标准要点

IEEE 802.11bb 于 2024 年 1 月正式发布，是 LiFi 的第一个 IEEE 标准。核心定义包括：

- **PHY 层**：定义了基于 OFDM 的光物理层，支持 10-224 Mbps 的数据速率。调制方式涵盖 BPSK/QPSK/16-QAM/64-QAM，配合不同编码率。
- **MAC 层**：完全复用 802.11 的 MAC 帧格式和接入机制（CSMA/CA），使 LiFi 可以无缝集成进现有 WiFi 网络架构。
- **波长范围**：800-1000 nm（近红外），避开照明光谱以减少环境光干扰。标准本身不覆盖可见光波段，但 pureLiFi 等公司的产品在可见光波段也兼容此架构。
- **双向通信**：上下行都使用光信道，或光下行+RF 上行的混合方式。

### 5.2 pureLiFi 产品分析

pureLiFi（苏格兰）是目前 LiFi 商用化最领先的公司。2024-2025 年的产品线：

- **Light Antenna ONE**：集成在 LED 灯具中的 LiFi AP 模块，支持 >100 Mbps 双向，覆盖半径约 3 米。
- **LiFi-XC**：USB 加密狗形态的 LiFi 终端，内置 PD 和小型 LED 发射器。
- **集成方案**：与 GlobalFoundries 合作，将 LiFi 收发芯片做成单芯片 SoC，目标是集成进笔记本电脑和手机中。2025 年 CES 展上展示了手机原型。

2025 年的实际部署案例包括：德国大众汽车工厂（用于产线机器人通信，避免 WiFi 干扰）、法国航空客舱娱乐系统（避免与航电系统的 RF 干扰）、迪拜世博城商场（顾客导航定位）。

---

## 6. 挑战与局限

### 6.1 视线（LoS）要求

LiFi 的最大工程挑战是对视线路径的强依赖。用手遮住接收器、身体挡住光路、笔记本电脑合上——都会导致通信中断。

缓解策略：

- **多灯覆盖**：同一区域由多个 LED 覆盖，用户的阴影只会挡住部分光源
- **漫反射利用**：墙壁和天花板的反射光也可以携带信息，虽然信号弱但可以在 LoS 被遮挡时维持低速连接
- **广角接收器**：使用半球形接收器或多个 PD 组成的阵列，扩大视场角（FOV）
- **RF 回退**：混合网络中，LoS 中断时自动切换到 WiFi

### 6.2 环境光干扰

阳光是 LiFi 的"天敌"。阳光的光谱覆盖整个可见光波段，且功率密度远高于室内 LED（阳光直射约 100,000 lux，LED 照明约 500 lux）。直射阳光会使 PD 饱和，完全淹没 LiFi 信号。

应对方法：
- 使用窄带光学滤波器，只接收 LED 发射的特定波长
- 802.11bb 选择近红外波段（850-950 nm），避开可见光谱最强的部分
- 数字域的直流消除和自适应滤波

### 6.3 上行链路设计

天花板灯具做下行很自然，但上行怎么做？终端设备的 LED 或红外发射器功率有限（眼安全限制），且朝向天花板的光路容易被用户自己的身体遮挡。

当前的工程方案是：
- 低速场景（IoT 传感器上报）：用红外 LED 上行，几十 kbps 足够
- 高速场景（视频上传）：上行仍走 WiFi

---

## 7. 实践建议

### 7.1 初学者入门路径

**第一步：LED 通信实验**（1 天）。用 Arduino + LED + 光敏电阻，实现最简单的 OOK 通信。发送端用 GPIO 控制 LED 亮灭，接收端用 ADC 读取光敏电阻值并解码。

```c
// Arduino 发送端：OOK 调制
#define LED_PIN 13
#define BIT_DURATION_US 1000  // 1ms 每比特 -> 1 kbps

void send_byte(uint8_t data) {
    // 起始位
    digitalWrite(LED_PIN, HIGH);
    delayMicroseconds(BIT_DURATION_US);
    
    // 8 个数据位（LSB first）
    for (int i = 0; i < 8; i++) {
        digitalWrite(LED_PIN, (data >> i) & 0x01 ? HIGH : LOW);
        delayMicroseconds(BIT_DURATION_US);
    }
    
    // 停止位
    digitalWrite(LED_PIN, LOW);
    delayMicroseconds(BIT_DURATION_US);
}
```

**第二步：OFDM 仿真**（3-5 天）。用 Python + NumPy 仿真 DCO-OFDM 系统，理解子载波分配、Hermitian 对称、DC 偏置等光 OFDM 的特殊问题。GNU Radio 有 VLC 的开源工具包可以参考。

**第三步：阅读 802.11bb 标准**（1 周）。重点看 PHY 层规范（clause 33），理解帧格式、前导码设计和自适应调制切换。

### 7.2 具体调优建议

- **PD 选型**：面积不是越大越好。0.5-1 mm² 的 PIN PD 配合光学集中器，在带宽和灵敏度之间取得最佳平衡
- **DC 偏置**：DCO-OFDM 的偏置点选在 LED 线性区中点，偏置过高浪费功率，过低导致底部截断失真
- **多灯协调**：相邻 LED 使用不同的 OFDM 子载波集（频分）或不同的时隙（时分），避免小区间干扰
- **调光兼容**：LiFi 信号叠加在调光 PWM 信号之上时，需要确保 PWM 频率和 OFDM 符号率不产生拍频。实践中 PWM 频率应 > OFDM 子载波间隔的 10 倍以上
- **运动场景**：用户行走速度下（1-2 m/s），LiFi 信道的相干时间约 10 ms，远长于 OFDM 符号长度（~μs），信道估计不成问题。但 LoS 路径的遮挡/恢复是毫秒级事件，需要快速链路切换机制

---

## 参考文献

1. H. Haas, "LiFi is a paradigm-shifting 5G technology," *Reviews in Physics*, vol. 3, pp. 26-31, 2018.
2. IEEE 802.11bb-2023, "IEEE Standard for Information Technology—Light Communications," Jan. 2024.
3. R. Bian et al., "15.73 Gb/s visible light communication with off-the-shelf LEDs," *Journal of Lightwave Technology*, vol. 37, no. 10, pp. 2418-2424, 2019.
4. pureLiFi, "Light Antenna ONE Product Datasheet," 2024. [https://www.purelifi.com](https://www.purelifi.com)
5. Z. Ghassemlooy et al., *Optical Wireless Communications: System and Channel Modelling with MATLAB*, 2nd ed., CRC Press, 2019.
6. S. Rajagopal et al., "IEEE 802.15.7 visible light communication: modulation schemes and dimming support," *IEEE Communications Magazine*, vol. 50, no. 3, pp. 72-82, 2012.
7. Y. Tanaka et al., "Indoor visible light data transmission system utilizing white LED lights," *IEICE Transactions*, vol. E86-B, no. 8, pp. 2440-2454, 2003.
8. M. Uysal et al., "IEEE 802.15.7r1 reference channel models for visible light communications," *IEEE Communications Magazine*, vol. 55, no. 1, pp. 212-217, 2017.
9. D. Tsonev et al., "A 3-Gb/s single-LED OFDM-based wireless VLC link using a Gallium Nitride μLED," *IEEE Photonics Technology Letters*, vol. 26, no. 7, pp. 637-640, 2014.
10. L. Yin et al., "Performance evaluation of non-orthogonal multiple access in visible light communication," *IEEE Transactions on Communications*, vol. 64, no. 12, pp. 5162-5175, 2016.
