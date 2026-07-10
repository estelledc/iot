---
schema_version: '1.0'
id: active-filter-butterworth-chebyshev
title: 有源滤波器Butterworth与Chebyshev拓扑对比
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 有源滤波器Butterworth与Chebyshev拓扑对比

> **难度**: 🟡 中级 | **领域**: 模拟滤波器设计 | **阅读时间**: 约 20 分钟

## 引言

想象你在听收音机,旁边有人大声说话。你想要一种"耳机"能把噪音挡住,只让音乐进来--这就是滤波器做的事。但耳机有很多种:有的隔音均匀(Butterworth),有的在某段频率特别安静但偶尔漏一点声(Chebyshev),有的让你听到的声音不变形但隔音一般(Bessel)。

在IoT传感器信号调理中,我们经常需要用有源滤波器把传感器输出中的噪声和干扰滤掉,保留有用的信号。选择哪种滤波器近似,就像选择哪种耳机--没有完美的方案,只有最适合场景的权衡。

## 1 滤波器逼近理论基础

### 1.1 理想滤波器与物理约束

理想低通滤波器的幅度响应是一个矩形:通带内增益恒为1,阻带内增益恒为0。但"砖墙"特性物理上不可能实现,因为理想矩形的冲激响应是sinc函数,时域延伸到无穷(非因果系统),且佩利-维纳定理要求幅度响应满足可积性约束。所以我们只能用有理函数去"逼近"理想响应,不同逼近策略产生不同滤波器类型。

### 1.2 传递函数与极点零点

n阶有源滤波器的传递函数:

```
H(s) = N(s) / D(s) = K * (s - z1)(s - z2)...(s - zm) / (s - p1)(s - p2)...(s - pn)
```

- `z1, z2, ...` 是零点,使H(s) = 0
- `p1, p2, ...` 是极点,使H(s)趋于无穷
- 稳定性要求:所有极点在s平面左半部分(实部 < 0)

不同逼近方法的本质区别就是极点在s平面上的分布策略不同。

### 1.3 归一化与去归一化

设计时先对截止频率做归一化:Omega = omega / omega_c,得到截止频率1 rad/s的原型低通。之后通过频率变换得到实际滤波器:低通到低通s -> s/omega_c;低通到高通s -> omega_c/s;低通到带通s -> (s^2 + omega_0^2)/(BW*s)。

## 2 Butterworth滤波器: 最大平坦幅度

### 2.1 定义与幅度响应

Butterworth滤波器在omega = 0处幅度响应尽可能"平坦":

```
|H(j*Omega)|^2 = 1 / (1 + Omega^(2n))
```

关键性质:
- Omega = 0时前2n-1阶导数均为零(最大平坦)
- Omega = 1时|H| = 1/sqrt(2) = -3.01 dB(所有阶数都过-3dB点)
- Omega >> 1时以-20n dB/decade速率衰减

### 2.2 极点分布

极点均匀分布在s平面左半的单位圆上:

```
p_k = exp(j * pi * (2k + n - 1) / (2n)),  k = 1, 2, ..., n
```

各阶极点举例:

| 阶数n | 极点(实部, 虚部) |
|-------|-----------------|
| 2 | (-0.7071, +0.7071), (-0.7071, -0.7071) |
| 3 | (-1.0000, 0), (-0.5000, +0.8660), (-0.5000, -0.8660) |
| 4 | (-0.3827, +0.9239), (-0.9239, +0.3827) 及共轭 |

### 2.3 优缺点

优点:通带最平坦无纹波;相位较线性;设计公式简洁。缺点:过渡带衰减同阶最慢;阶跃响应有过冲(但比Chebyshev温和)。

## 3 Chebyshev Type I滤波器: 等纹波通带

### 3.1 定义与幅度响应

允许通带内有等幅纹波,换取更陡的过渡带:

```
|H(j*Omega)|^2 = 1 / (1 + epsilon^2 * C_n^2(Omega))
```

epsilon是纹波参数,C_n(Omega)是n阶Chebyshev多项式。

### 3.2 Chebyshev多项式

递推定义:C_0 = 1, C_1 = Omega, C_n = 2*Omega*C_(n-1) - C_(n-2)。

| 阶数n | C_n(Omega) |
|-------|-----------|
| 0 | 1 |
| 1 | Omega |
| 2 | 2*Omega^2 - 1 |
| 3 | 4*Omega^3 - 3*Omega |
| 4 | 8*Omega^4 - 8*Omega^2 + 1 |

当|Omega| <= 1时,C_n在[-1, +1]之间等幅振荡,这正是"等纹波"的来源。

### 3.3 极点分布与纹波关系

极点分布在s平面左半的椭圆上(非Butterworth的圆):

```
短轴 a = sinh(v),  长轴 b = cosh(v),  v = (1/n) * arcsinh(1/epsilon)
```

epsilon越小椭圆越接近圆,Chebyshev越接近Butterworth。

纹波delta_p(dB)与epsilon的关系:epsilon = sqrt(10^(delta_p/10) - 1)。

| 纹波(dB) | epsilon | 通带幅度波动 |
|----------|---------|------------|
| 0.1 | 0.1526 | 1.006 ~ 0.995 |
| 0.5 | 0.3493 | 1.059 ~ 0.944 |
| 1.0 | 0.5088 | 1.122 ~ 0.891 |

阻带衰减比同阶Butterworth快约20*log10(2^(n-1)*epsilon) dB。

## 4 Chebyshev Type II滤波器: 等纹波阻带

Chebyshev Type II(逆Chebyshev)在阻带内等纹波,通带内单调下降:

```
|H(j*Omega)|^2 = epsilon^2 * C_n^2(1/Omega) / (1 + epsilon^2 * C_n^2(1/Omega))
```

| 特性 | Type I | Type II |
|------|--------|---------|
| 通带 | 等纹波 | 单调下降 |
| 阻带 | 单调衰减 | 等纹波 |
| 零点 | 无(全极点) | 有限个(在j*omega轴) |
| 实现难度 | 较易 | 较难(零点需额外电路) |

IoT传感器中Type II较少使用:通带虽单调但不如Butterworth平坦,且有限零点增加电路复杂度。

## 5 Bessel滤波器: 最大平坦群延迟

Bessel不以幅度响应为优化目标,而是追求群延迟在通带内尽可能恒定:

```
群延迟 tau(omega) = -d(phi)/d(omega)
```

恒定群延迟意味着所有频率成分延迟相同,信号波形不失真。传递函数由Bessel多项式定义:B_0 = 1, B_1 = s+1, B_n = (2n-1)*B_(n-1) + s^2*B_(n-2)。Bessel过渡带衰减最慢,但阶跃响应几乎无振铃,在ECG心电、脉冲传感器等需要保真波形的场景中是首选。

## 6 频率响应对比

### 6.1 幅度响应关键指标

4阶低通、截止频率1kHz:

| 指标 | Butterworth | Chebyshev I(0.5dB) | Chebyshev I(1dB) | Bessel |
|------|-------------|---------------------|-------------------|--------|
| 通带纹波 | 0 dB | 0.5 dB | 1.0 dB | 0 dB |
| 2kHz处衰减 | -24 dB | -34 dB | -37 dB | -17 dB |

### 6.2 抗混叠需求实例

传感器信号带宽5kHz,采样率20kHz,需要-60dB衰减在10kHz处:

- Butterworth 4阶: 10kHz处仅-48dB,不够
- Butterworth 6阶: 约-72dB,满足(需3个运放)
- Chebyshev I 4阶(0.5dB): 约-68dB,满足(仅需2个运放)

同阶Chebyshev的过渡带明显更陡,可用更低阶数达到同样阻带衰减,节省运放和元件。

### 6.3 通带纹波vs过渡带陡度权衡

这是滤波器设计最核心的权衡:纹波越大 -> 过渡带越陡 -> 所需阶数越低 -> 电路越简单。在IoT传感器中,0.1~0.5dB纹波通常可接受,因为后续ADC的量化误差本身就大于此纹波量。

## 7 电路拓扑实现

### 7.1 Sallen-Key拓扑

最常用的二阶有源滤波器拓扑,需1个运放、2个电容、2~4个电阻。二阶低通传递函数:

```
H(s) = K / (s^2*R1*R2*C1*C2 + s*[R2*C2 + R1*C2 + R1*C1*(1-K)] + 1)
```

K = 1 + R4/R3为直流增益。特点:同相放大(K >= 1),电路简单,但高Q时元件灵敏度大,适合Q < 10的低阶节。

### 7.2 多重反馈(MFB)拓扑

用1个运放实现反相二阶节,二阶低通传递函数:

```
H(s) = -R3/R1 / (s^2*R2*R3*C1*C2 + s*R3*C2*(1+R3/R1+R3/R2) + 1)
```

特点:反相放大;元件灵敏度低于Sallen-Key;高Q时更稳定;适合Q到20+的高Q节。

### 7.3 拓扑选择策略

| 考虑因素 | Sallen-Key | MFB |
|---------|------------|-----|
| 增益极性 | 同相(K >= 1) | 反相 |
| Q值范围 | Q < 10 | Q可到20+ |
| 元件灵敏度 | 较高 | 较低 |
| 元件数 | 少(4无源+1运放) | 多(5无源+1运放) |

一般策略:低Q节用Sallen-Key(简单),高Q节用MFB(稳定),级联时两种可混用。

## 8 阶跃响应对比

### 8.1 过冲与振铃

4阶各类型的典型阶跃响应:

| 滤波器类型 | 过冲(%) | 建立时间(到1%内) | 振铃情况 |
|-----------|---------|-----------------|---------|
| Bessel | ~0.8% | 最短 | 几乎无 |
| Butterworth | ~10.9% | 中等 | 轻微 |
| Chebyshev I(0.5dB) | ~16% | 较长 | 明显 |
| Chebyshev I(1dB) | ~21% | 长 | 显著 |

### 8.2 振铃对IoT传感器的影响

振铃在以下场景是严重问题:脉冲型传感器(PIR红外/光电)会误触发;多路复用采样切换后首个采样受影响;阈值检测会多次穿越;ECG/EMG波形失真影响诊断。而在缓变传感器(温度/湿度)、只做粗滤的模拟前端、只关心稳态频域精度的场景中,振铃可容忍。

建立时间决定了通道切换后需等多久才能采样:多路复用时每通道采样间隔 > t_settle。Chebyshev较长的建立时间可能成为多路复用系统的瓶颈。

## 9 品质因数Q与稳定性

### 9.1 各类型各阶的Q值

二阶标准形式:H(s) = H0*omega_0^2 / (s^2 + (omega_0/Q)*s + omega_0^2)。Q越高极点越靠近j*omega轴,响应越尖锐。4阶滤波器分解为两个二阶节:

| 滤波器类型 | 第1节Q | 第2节Q | 最大Q |
|-----------|--------|--------|-------|
| Butterworth 4阶 | 0.541 | 1.307 | 1.307 |
| Chebyshev I(0.5dB) 4阶 | 0.619 | 2.089 | 2.089 |
| Chebyshev I(1dB) 4阶 | 0.677 | 2.660 | 2.660 |

Chebyshev的Q值明显高于Butterworth,元件容差要求更严格,运放GBW需求更高。

### 9.2 元件灵敏度分析

灵敏度S_x^Q = (dQ/Q) / (dx/x)衡量参数x变化对Q的影响。Sallen-Key的Q灵敏度与Q成正比(Q=5时1%元件变化可导致Q变化10%以上),MFB的Q灵敏度与Q基本无关。故高Q节应选用MFB。

### 9.3 运放增益带宽积(GBW)的影响

有限GBW导致实际Q升高(Q增强效应):

```
Q_actual = Q_ideal / (1 - 2*pi*f_0*Q_ideal / GBW)
```

分母接近零时电路振荡。设计准则:GBW > 100*Q*f_0。例如Chebyshev 4阶1dB纹波f_0=1kHz时需GBW > 266kHz(LM358可满足),但f_0=10kHz时需GBW > 2.66MHz(需TLV272等)。

## 10 实用设计工具与流程

### 10.1 TI FilterPro与ADI Filter Wizard

TI FilterPro:免费软件,选择滤波器类型/截止频率/逼近方法后自动计算极点、Q值、元件值,可选Sallen-Key或MFB拓扑,输出原理图。

ADI Analog Filter Wizard(在线工具):实时拖拽调整参数看响应变化;自动推荐运放型号(基于GBW和Q需求);元件值自动匹配E24/E96标准系列;支持全差分设计。

### 10.2 手工设计示例

2阶Sallen-Key低通Butterworth,截止频率f_c = 1kHz,增益K = 1:

1. omega_c = 2*pi*1000 = 6283 rad/s,Q = 0.707
2. 选C1 = C2 = 10nF
3. R1 = R2 = 1/(omega_c*sqrt(C1*C2)) = 15.9k,取E96标准值15.8k
4. K = 1时R3开路R4短路

Python验证:

```python
import numpy as np
from scipy import signal

fc = 1000
wc = 2 * np.pi * fc
Q = 1 / np.sqrt(2)
num = [wc**2]
den = [1, wc/Q, wc**2]
sys = signal.TransferFunction(num, den)
w, h = signal.freqresp(sys, w=np.logspace(2, 5, 1000))
mag_db = 20 * np.log10(np.abs(h))
idx_3db = np.argmin(np.abs(mag_db + 3.01))
print(f"-3dB frequency: {w[idx_3db]/(2*np.pi):.1f} Hz")
```

## 11 IoT传感器场景选型指南

### 11.1 按传感器信号特性选择

| 传感器类型 | 信号特征 | 推荐滤波器 | 理由 |
|-----------|---------|-----------|------|
| 温度/湿度NTC | 缓变,近直流 | Butterworth低阶 | 平坦通带,振铃无关紧要 |
| 加速度计IMU | 宽频,含冲击 | Chebyshev(0.5dB) | 陡过渡带抗混叠,纹波可接受 |
| 麦克风/声学 | 需保真波形 | Bessel | 最小相位失真 |
| ECG/PPG | 脉冲型,需诊断 | Bessel或Butterworth | 振铃干扰R波检测 |
| 压力/称重 | 阶跃型 | Bessel | 快速建立,无振铃 |
| 电流互感器 | 含50Hz工频干扰 | Chebyshev(1dB) | 陡过渡带隔离工频 |

### 11.2 按系统约束选择

**功耗优先**(电池IoT节点):Chebyshev低阶(运放更少),选低静态电流运放(如TLV9062, I_q = 10uA)。**精度优先**(计量/校准):Butterworth或Bessel,0.1%容差电阻+1% C0G电容,预留2~3dB余量。**成本优先**(消费级):Chebyshev低阶+通用运放(LM358/TLV272),接受1dB纹波。

### 11.3 混合策略: 模拟+数字两级滤波

最佳实践:模拟Chebyshev低阶做抗混叠(允许通带纹波) -> ADC -> 数字FIR精确滤除(线性相位,补偿模拟纹波)。既减少模拟电路复杂度,又通过数字手段保证最终精度。

### 11.4 设计检查清单

- [ ] 截止频率是否留有余量(信号带宽1.5~2倍)?
- [ ] 阻带衰减是否满足SNR要求?
- [ ] 通带纹波是否在ADC LSB范围内可接受?
- [ ] 阶跃响应建立时间是否满足采样时序?
- [ ] 运放GBW是否 > 100*Q*f_0?
- [ ] 元件容差是否满足灵敏度要求(高Q节用1%)?
- [ ] 是否验证PCB布局对寄生参数的影响?
- [ ] 是否做了温度漂移分析(C1/C2温度系数匹配)?

## 总结

Butterworth与Chebyshev滤波器代表了模拟滤波器设计中最基本的权衡:通带平坦度与过渡带陡度。

- **Butterworth**: 通带最平坦,相位较线性,过渡带最缓,适合对幅度精度和波形保真要求高的场景
- **Chebyshev I**: 通带等纹波,过渡带最陡,同衰减下阶数最低,适合抗混叠和强干扰抑制
- **Chebyshev II**: 阻带等纹波,IoT中较少使用
- **Bessel**: 群延迟最平坦,阶跃响应最优,过渡带最缓,适合脉冲/瞬态信号

电路实现上,Sallen-Key拓扑简单但高Q灵敏度大,MFB拓扑更稳定适合高Q节。实际IoT设计中,模拟Chebyshev抗混叠+数字FIR精确滤波的混合策略,兼顾了电路简洁和最终精度。选择滤波器不是追求"最好",而是在平坦度、陡度、时域行为、功耗和成本之间找到最适合当前传感器的平衡点。

## 参考文献

1. Van Valkenburg M E. Analog Filter Design. Holt, Rinehart and Winston, 1982. -- 经典教材,极点表完整
2. Texas Instruments. Active Filter Design Techniques, SLOA088, 2001. -- TI官方设计指南
3. Williams A B, Taylor F J. Electronic Filter Design Handbook, 4th ed. McGraw-Hill, 2006. -- 工程设计手册
4. Analog Devices. Analog Filter Wizard Design Guide, MT-227, 2019. -- ADI在线工具原理
5. Kugelstadt T. Active Filter Design Using FilterPro, SLOA051, 2010. -- FilterPro设计实例
