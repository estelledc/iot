---
schema_version: '1.0'
id: current-sense-resistor-shunt
title: 电流采样电阻与分流器精密电流测量
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 14
prerequisites:
  - signal-conditioning-amplifier-filter
  - adc-reference-voltage-design
tags:
  - 电流采样
  - 分流器
  - 开尔文连接
  - 高侧采样
  - INA
  - 功耗监测
  - PCB布局
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 电流采样电阻与分流器精密电流测量

> **难度**：🟡 中级 | **领域**：电流测量技术 | **阅读时间**：约 14 分钟

## 日常类比

要估河流量，可在河中放一块石头，看前后水位差：石头越大差越明显但越挡水。电流采样电阻（shunt）就是电路里的那块石头——串联测压降推电流；阻值越大信号越好测，插入损耗与自热也越大[1][2]。

## 摘要

IoT 功耗分析、电池管理与过流保护常用分流电阻法。核心权衡是 **R_sense、精度/TCR（Temperature Coefficient of Resistance）、高侧/低侧与开尔文布线**。文中阻值与误差量为级示意，**以数据手册与系统校准为准**[1][3]。

## 1. 方法定位

| 方法 | 原理 | 优点 | 局限 | 常见场景 |
|------|------|------|------|----------|
| 采样电阻 | V=IR | 线性好、成本低 | 有压降与自热 | 毫安～数十安 |
| 霍尔 | 磁场 | 隔离、无插入损耗 | 温漂与偏移 | 大电流/隔离 |
| 电流互感器 | 感应 | 隔离、工频大电流 | 交流为主 | 市电计量 |
| 罗氏线圈 | 微分磁场 | 柔性、脉冲 | 需积分 | 瞬态大电流 |

中小电流 IoT 节点优先分流电阻；需电气隔离再看霍尔等[1][4]。

## 2. 阻值与误差机制

```
I = V_sense / R_sense
P = I² × R_sense
```

| 量程量级 | R_sense 量级（示意） | 主要矛盾 |
|----------|----------------------|----------|
| 毫安级 | 欧姆级 | 信号 vs 压降 |
| 安培级 | 0.01～0.1 Ω | 功耗与温升 |
| 十安以上 | 毫欧分流器 | 铜皮/焊盘电阻 |

误差源：电阻容差、TCR、放大器偏移/增益、ADC 量化、走线电阻。校准可消固定增益与偏移，**残差常由 TCR 与长期漂移主导**[2][5]。

| TCR（ppm/°C） | ΔT≈50°C 时阻值偏移量级 |
|---------------|------------------------|
| 50 | ~0.25% |
| 25 | ~0.125% |
| 10 | ~0.05% |

精密场合倾向低 TCR 合金分流器，并按峰值电流做功率降额（常见工程做法是实际功耗远低于额定）[4][6]。

## 3. 高侧 vs 低侧

| 条件 | 更常见选择 |
|------|------------|
| 成本敏感、负载可浮地 | 低侧 |
| 负载必须接地 / 需检对地短路 | 高侧 |
| 电池漏电监测 | 高侧更常见 |
| 多路共地采集 | 高侧 |

高侧共模电压高，需差分或专用电流检测放大器（如 INA 系列）；低侧可用地参考 ADC，但无法直接看对地短路[1][3]。

## 4. 放大器与动态范围

| 类型 | 输出 | 倾向场景 |
|------|------|----------|
| 数字电流监视器（如 INA219 类） | I²C | 功耗分析、少引脚 |
| 模拟 CSA（Current Sense Amplifier） | 电压 | 过流比较、快响应 |
| 纳安级偏置 CSA | 电压 | 长期电池监测 |

休眠 μA 与发射数十～百 mA 同板时，单量程 12 位 ADC 常不够；多阻值切换或可编程增益更现实。对数放大少见，精度与成本通常不划算[3][7]。

## 5. PCB：开尔文连接

Sense 线必须从分流器焊盘内侧引出，不与大电流铜皮共段；否则毫欧级分流器会被走线电阻“吃掉”。电流路径按载流加宽，Sense 可细。电阻下方铺铜散热，远离基准与晶振[4][8]。

## 6. 局限、挑战与可改进方向

### 1. 用标称容差当系统精度

**局限**：忽略 TCR、自热与放大器偏移叠加。
**改进**：做温度与满量程校准；RSS（Root Sum Square）或蒙特卡洛估误差预算[2][5]。

### 2. 低侧省事却漏掉短路故障

**局限**：对地短路时低侧分流器无电流。
**改进**：安全相关路径改高侧或加独立保护[1]。

### 3. 宽动态范围硬套单量程

**局限**：休眠电流淹没在 LSB 里。
**改进**：量程切换、可编程增益，或分路径测休眠/工作电流[7]。

### 4. 毫欧级不做开尔文

**局限**：焊盘与铜皮电阻成主导误差。
**改进**：四端子封装 + 开尔文布线；必要时测铜皮压降[4][8]。

## 7. 实践要点

1. 先定 I_min/I_max、允许压降与功耗，再选 R_sense。
2. 电池与安全路径优先高侧 + 专用 CSA。
3. 布局评审必查 Sense 是否从焊盘引出。

## 参考文献

[1] Texas Instruments, Current Sensing in Power Delivery Systems, SBOA298.
[2] Analog Devices, High-Side Current Sensing Techniques, AN-1054.
[3] Maxim/ADI, Current-Sense Amplifier Basics, AN-6604.
[4] Vishay, Current Sensing with Surface Mount Shunt Resistors.
[5] J. Witt, Low-Side vs High-Side Current Sensing, EDN.
[6] Vendor shunt resistor datasheets (TCR, power rating, Kelvin packages).
[7] TI INA219 / INA180 family datasheets and application notes.
[8] IPC / PCB current-carrying capacity design guidance.
[9] JEDEC / resistor reliability notes on self-heating.
[10] Battery fuel-gauge current-sense layout application notes.
[11] IEC / industrial overcurrent protection sensing practices (context).
