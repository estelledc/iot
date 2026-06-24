# MEMS加速度计ADXL345原理与运动检测

> **类型**：技术分析 | **难度**：🟢 初级 | **领域**：惯性传感、运动检测、可穿戴设备

---

## 加速度测量基础

### 静态加速度与动态加速度

加速度计能感知两类信号，理解两者的区别是用好传感器的关键。

**静态加速度**——由重力引起。传感器静止不动时，也能读到约 1g 的值。就像把弹簧秤挂在挂钩上，即使不晃动，弹簧也被重力拉长。倾斜检测正是利用了静态加速度在不同轴上的投影分量。

**动态加速度**——由运动引起。走路时的上下颠簸、手机震动马达的振动、汽车碰撞的冲击，都属于动态加速度。

日常类比：想象你站在电梯里。电梯不动时，脚下感受的是"静态"——地球重力；电梯启动上升时，额外感到一股向上的推力，这就是"动态"加速度。加速度计同时感受到两者，后文会讲到如何用滤波把它们分离开。

| 特征 | 静态加速度 | 动态加速度 |
|------|-----------|-----------|
| 来源 | 重力 | 运动惯性力 |
| 频率 | 0 Hz（直流） | 0.5 Hz ~ 数 kHz |
| 典型幅值 | 恒定 1g | 0.01g ~ 数十 g |
| 典型应用 | 倾斜角检测、屏幕旋转 | 计步、跌倒检测、振动监测 |

加速度是矢量——有大小也有方向。三轴（X、Y、Z）加速度计组合就能还原完整的三维运动。传感器水平静止时，X/Y 轴读数接近 0，Z 轴读数约 1g；倾斜时重力在各轴上的投影比例随之改变，这正是倾斜角计算的数学基础。

---

## MEMS电容式传感结构

### MEMS是什么

MEMS（Micro-Electro-Mechanical Systems，微机电系统）是在硅片上用半导体工艺制造的微型机械结构。日常类比：MEMS 加速度计就像在一块指甲盖大小的硅片上，造了一座微型"游乐园"——里面有弹簧、滑块、梳齿，全都是微米级的机械零件，但功能跟宏观弹簧秤完全一样。

### 核心结构：质量块 + 弹簧 + 梳齿电容

1. **质量块（Proof Mass）**：可沿敏感轴自由移动的硅质微结构。质量越大，同样加速度下惯性力越大，灵敏度越高。

2. **弹性梁（Spring/Beam）**：连接质量块和固定锚点，充当"弹簧"。偏移量与加速度成正比。

3. **梳齿电容（Comb Fingers）**：质量块两侧伸出密排梳齿，与固定梳齿交错排列。质量块移动时梳齿交错深度改变，电容值变化，由此反推位移和加速度。

```
固定锚点 ─── 弹性梁 ─── 质量块 ─── 弹性梁 ─── 固定锚点
                        │
              ▏固定梳齿 ▏▏可动梳齿▏
              ▏▏▏▏▏▏▏▏▏▏│▏▏▏▏▏▏▏▏▏▏
                   差分电容 C1/C2
```

### 差分检测原理

梳齿电容组成差分对 C1/C2。加速度为零时 C1 = C2；有加速度时一侧间隙变小、另一侧变大。测量 (C1 - C2)/(C1 + C2) 可消除温度漂移等共模干扰。这就是 MEMS 加速度计需要"对称结构"的原因。

ADXL345 在同一芯片上集成两个传感单元：X/Y 轴共用面内单元（梳齿沿两正交方向排列），Z 轴使用面外单元（极板上下排列），统一输出为 16 位二进制补码数据。

---

## ADXL345核心特性

### 概览

| 参数 | 规格 |
|------|------|
| 供电电压 | 2.0 V ~ 3.6 V |
| 测量范围 | ±2g / ±4g / ±8g / ±16g（可编程） |
| 分辨率 | 13 位（全分辨率模式 3.9 mg/LSB） |
| 输出数据速率 | 0.1 Hz ~ 3200 Hz（可编程） |
| 通信接口 | SPI（3线/4线，最高 5 MHz）/ I2C（最高 400 kHz） |
| 工作电流 | 测量模式约 40 μA（@100 Hz），待机 0.1 μA |
| 内置功能 | 活动/非活动检测、单击/双击、自由落体检测 |
| 封装 | 5 mm × 5 mm × 2 mm LGA |

13 位分辨率意味着在 ±16g 量程下最小可分辨 3.9 mg，能检测不到 1° 的倾斜变化。需注意仅在 `DATA_FORMAT` 寄存器设置 `FULL_RES` 位后才在所有量程下保持此精度。

### SPI与I2C接口选择

| 接口 | 优势 | 劣势 | 适用场景 |
|------|------|------|---------|
| SPI（4线） | 速率高（5 MHz），延迟低 | 占 4 个 GPIO | 高采样率、实时性要求高 |
| I2C | 只占 2 个 GPIO，支持多设备 | 最高 400 kHz | 普通物联网项目、原型验证 |

I2C 地址：SDO 接地时为 0x53，接 VDDIO 时为 0x1D。

### 电源管理

- **正常模式**：约 40 μA（@100 Hz ODR）
- **低功耗模式**：`BW_RATE` 寄存器 Bit4 使能，电流降低约 50%
- **待机模式**：`POWER_CTL` 寄存器 Bit2 设置，电流降至 0.1 μA
- **自动休眠**：非活动检测后自动进入低功耗模式

---

## 寄存器配置与工作模式

### 关键寄存器一览

| 地址 | 名称 | 功能 |
|------|------|------|
| 0x00 | DEVID | 设备 ID，固定读回 0xE5 |
| 0x24 | THRESH_ACT | 活动阈值（62.5 mg/LSB） |
| 0x25 | THRESH_INACT | 非活动阈值（62.5 mg/LSB） |
| 0x26 | TIME_INACT | 非活动时间（1 s/LSB） |
| 0x27 | ACT_INACT_CTL | 活动/非活动轴使能与耦合方式 |
| 0x28 | THRESH_FF | 自由落体阈值（62.5 mg/LSB） |
| 0x29 | TIME_FF | 自由落体时间（5 ms/LSB） |
| 0x2C | BW_RATE | 输出数据速率与低功耗模式 |
| 0x2D | POWER_CTL | 电源模式控制 |
| 0x2E | INT_ENABLE | 中断使能 |
| 0x2F | INT_MAP | 中断引脚映射 |
| 0x31 | DATA_FORMAT | 数据格式、量程、全分辨率 |
| 0x32~0x37 | DATAX0~DATAZ1 | 三轴加速度数据（6 字节） |

### 初始化配置

```c
// ADXL345 初始化示例（基于 I2C）
#define ADXL345_ADDR    0x53  // SDO 接地
#define REG_DEVID       0x00
#define REG_DATA_FORMAT 0x31
#define REG_BW_RATE     0x2C
#define REG_POWER_CTL   0x2D

void adxl345_init(void) {
    uint8_t dev_id;
    // 1. 验证设备 ID
    dev_id = i2c_read_reg(ADXL345_ADDR, REG_DEVID);
    if (dev_id != 0xE5) { return; }
    // 2. 设置 ±16g 全分辨率
    i2c_write_reg(ADXL345_ADDR, REG_DATA_FORMAT, 0x0B);
    //    0x0B = FULL_RES(0x08) | ±16g(0x03)
    // 3. 设置 100 Hz 输出速率
    i2c_write_reg(ADXL345_ADDR, REG_BW_RATE, 0x0A);
    // 4. 启动测量
    i2c_write_reg(ADXL345_ADDR, REG_POWER_CTL, 0x08);
    //    0x08 = Measure 位使能
}
```

### 数据读取与换算

三轴数据各占 2 字节（低字节在前），共 6 字节。全分辨率模式下 scale_factor 固定为 3.9 mg/LSB（0.0039 g/LSB），与量程无关。

```c
// 读取三轴加速度并换算为 g
void adxl345_read_accel(float *x_g, float *y_g, float *z_g) {
    uint8_t buf[6];
    i2c_read_regs(ADXL345_ADDR, 0x32, buf, 6);
    int16_t raw_x = (int16_t)(buf[1] << 8 | buf[0]);
    int16_t raw_y = (int16_t)(buf[3] << 8 | buf[2]);
    int16_t raw_z = (int16_t)(buf[5] << 8 | buf[4]);
    const float scale = 0.0039f;
    *x_g = raw_x * scale;
    *y_g = raw_y * scale;
    *z_g = raw_z * scale;
}
```

---

## 内置运动检测功能

ADXL345 最具特色的能力是片上硬件级运动检测——MCU 无需持续采样，只需响应中断即可，大幅降低系统功耗。

### 活动（Activity）检测

当任意使能轴的加速度绝对值超过 `THRESH_ACT` 阈值时，触发活动中断。

- `THRESH_ACT`（0x24）：建议设为 2g~4g（0x20~0x40）
- `ACT_INACT_CTL`（0x27）Bit4：耦合方式——0=DC（含重力），1=AC（去除重力偏移）

DC 耦合检测"有运动发生"；AC 耦合检测"有振动/冲击"而忽略静止姿态。

### 非活动（Inactivity）检测

当所有使能轴的加速度绝对值均低于 `THRESH_INACT`，且持续超过 `TIME_INACT` 时触发。

- `THRESH_INACT`（0x25）：建议设为 0.5g~1.5g
- `TIME_INACT`（0x26）：1 s/LSB，最大 255 秒

### 活动与非活动联动

设置 Link 位（`ACT_INACT_CTL` Bit5），可将两者串联：等待非活动 → 检测到活动 → 重新计时非活动。Auto-sleep 位（`POWER_CTL` Bit4）还能在非活动后自动进入低功耗模式。这种联动非常适合"设备拿起唤醒、放下休眠"的场景。

### 自由落体（Free-Fall）检测

当三轴加速度均低于 `THRESH_FF`，且持续超过 `TIME_FF` 时触发。核心逻辑是"三轴同时接近零"——正常使用时至少有一个轴受重力约 1g，三轴都接近零说明设备处于失重状态。

- `THRESH_FF`（0x28）：建议 300~600 mg（0x05~0x09）
- `TIME_FF`（0x29）：5 ms/LSB，建议 100~350 ms（0x14~0x46）

```c
// 配置自由落体检测
void adxl345_config_freefall(void) {
    i2c_write_reg(ADXL345_ADDR, 0x28, 0x09);  // THRESH_FF = 600 mg
    i2c_write_reg(ADXL345_ADDR, 0x29, 0x14);  // TIME_FF = 100 ms
    i2c_write_reg(ADXL345_ADDR, 0x2F, 0x00);  // INT_MAP: Free-Fall → INT1
    i2c_write_reg(ADXL345_ADDR, 0x2E, 0x04);  // INT_ENABLE: Free-Fall
}
```

ADXL345 还支持单击/双击检测，涉及 `THRESH_TAP`、`DURATION`、`LATENT`、`WINDOW` 四个寄存器，常用于"敲击唤醒"和"双击切歌"等交互场景。

---

## 主流加速度计对比

| 特性 | ADXL345 | LIS3DH | MMA8452Q | BMA400 |
|------|---------|--------|----------|--------|
| 厂商 | Analog Devices | STMicro | NXP | Bosch |
| 分辨率 | 13 位 | 12 位 | 12 位 | 12 位 |
| 量程 | ±2/4/8/16g | ±2/4/8/16g | ±2/4/8g | ±2/4/8/16g |
| 接口 | SPI / I2C | SPI / I2C | I2C | SPI / I2C |
| 电流@100Hz | ~40 μA | ~20 μA | ~14 μA | ~3.5 μA |
| 内置检测 | 活动/非活动/自由落体/Tap | Tap/活动/自由落体 | 活动/自由落体/Tap/方向 | 活动/步数/Tap/自由落体 |
| 封装 | 5×5×2 mm | 3×3×1 mm | 3×3×1 mm | 3×3×0.85 mm |
| 参考价 | $3~5 | $1~2 | $1~2 | $2~3 |

**选型建议**：高精度倾斜角选 ADXL345；电池超低功耗选 BMA400；快速原型选 LIS3DH；需要内置计步选 BMA400。

---

## 代码实践：倾斜角计算与计步

### 倾斜角计算

倾斜检测利用静态加速度。传感器静止时三轴矢量和约 1g，各轴与重力方向的夹角通过反三角函数计算：

```
roll  = atan2(y, z)           // 绕 X 轴旋转角
pitch = atan2(-x, √(y²+z²))  // 绕 Y 轴旋转角
```

日常类比：想象一个竖着的温度计，倾斜时液柱沿管壁的投影变短——重力分量在不同方向上的"投影"就是角度关系的本质。

```c
#include <math.h>

// 从加速度计算倾斜角（单位：度）
void adxl345_get_tilt(float x_g, float y_g, float z_g,
                      float *roll_deg, float *pitch_deg) {
    *roll_deg  = atan2(y_g, z_g) * 180.0f / M_PI;
    float yz = sqrtf(y_g * y_g + z_g * z_g);
    *pitch_deg = atan2(-x_g, yz) * 180.0f / M_PI;
}
```

注意：角度超过 ±90° 时出现万向锁，需结合陀螺仪；运动时动态加速度会叠加导致角度跳变，需低通滤波。

### 简易计步算法

计步利用动态加速度——走路时身体上下起伏，合加速度呈周期性波动。

```c
#include <math.h>
#include <stdint.h>

#define STEP_THRESHOLD  0.25f   // 步检测阈值（g）
#define STEP_COOLDOWN   300     // 两步最小间隔（ms）

static uint32_t last_step_time = 0;
static uint32_t step_count = 0;

void step_detect(float x_g, float y_g, float z_g, uint32_t now_ms) {
    // 1. 合加速度
    float magnitude = sqrtf(x_g*x_g + y_g*y_g + z_g*z_g);
    // 2. 去除重力直流分量
    float dynamic = fabsf(magnitude - 1.0f);
    // 3. 阈值判断 + 去抖
    if (dynamic > STEP_THRESHOLD &&
        (now_ms - last_step_time) > STEP_COOLDOWN) {
        step_count++;
        last_step_time = now_ms;
    }
}

uint32_t get_step_count(void) { return step_count; }
```

这是最简化的峰值检测。实际产品还需：滑动窗口均值滤波、自适应阈值、频域分析区分走路与手部晃动、峰值→过零→谷值的状态机逻辑。

---

## IoT应用场景

### 可穿戴设备

智能手环/手表是最典型应用。活动/非活动联动 + 自动休眠使设备"戴着时工作、摘下时休眠"，整体功耗可控制在微安级。计步、睡眠监测、久坐提醒均基于加速度数据。

### 资产追踪

物流追踪器利用片上检测：活动检测判断是否在运输中，自由落体检测判断是否跌落，非活动检测触发位置上报。MCU 大部分时间深度睡眠，仅中断唤醒。

### 振动监测

ADXL345 最高 3200 Hz 采样率可覆盖电机轴承故障频段（100~1000 Hz），通过 FFT 频谱分析识别故障类型。精密场景需更低噪声的专用传感器（如 ADXL355）。

### 游戏控制器

倾斜角做方向控制，Tap 检测做按钮交互，低延迟和片上检测使其在实时交互场景下表现良好。

---

## 总结与展望

本文从加速度测量基础出发，逐步深入 MEMS 电容式传感结构、ADXL345 寄存器配置和片上运动检测，最后给出倾斜角计算与计步代码实践。

核心要点：

- **静态与动态加速度**的区别是理解所有加速度应用的基础
- **MEMS 电容式结构**（质量块 + 弹性梁 + 梳齿差分电容）是微型化和低成本的关键
- **ADXL345 核心优势**在于 13 位分辨率和片上硬件运动检测，让 MCU 不必持续采样
- **寄存器配置重点**：`DATA_FORMAT`（量程与分辨率）、`BW_RATE`（速率与功耗）、`POWER_CTL`（测量使能）
- **选型**需权衡分辨率、功耗、封装尺寸和内置功能

未来趋势：

- **更低功耗**：BMA400 已达 3.5 μA，未来向纳安级迈进
- **传感器融合**：加速度计 + 陀螺仪 + 磁力计 9 轴融合成为中高端 IoT 标配
- **AI 端侧推理**：新一代传感器集成 TinyML 加速器，片上直接输出活动类别
- **更高集成度**：传感器与 MCU、BLE 集成于同一封装，进一步缩小终端体积

---

## 参考资料

1. Analog Devices. ADXL345 Datasheet. [链接](https://www.analog.com/media/en/technical-documentation/data-sheets/ADXL345.pdf)
2. STMicroelectronics. LIS3DH Datasheet. [链接](https://www.st.com/resource/en/datasheet/lis3dh.pdf)
3. NXP. MMA8452Q Datasheet. [链接](https://www.nxp.com/docs/en/data-sheet/MMA8452Q.pdf)
4. Bosch Sensortec. BMA400 Datasheet. [链接](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bma400-ds000.pdf)
5. 王喆, 等. MEMS电容式加速度计研究综述. 传感器与微系统, 2023.
6. SparkFun. ADXL345 Hookup Guide. [链接](https://learn.sparkfun.com/tutorials/adxl345-hookup-guide)
