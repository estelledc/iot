# PWM电机控制在嵌入式IoT执行器中的应用
> **难度**：🟢 初级 | **领域**：电机控制基础 | **阅读时间**：约 18 分钟

## 引言

想象你在用花洒洗澡。水龙头只有开和关两个状态,但你可以通过快速切换来控制出水量:开的时间长一些,水量就大;开的时间短一些,水量就小。PWM(脉宽调制)控制电机就是这个道理:开关管只有导通和关断两种状态,但通过调节"导通时间占总周期的比例"(占空比),就能控制电机的平均电压,进而控制转速。

在IoT设备中,从风扇调速、阀门控制到小型机器人驱动,PWM电机控制是最常见的执行器驱动方式。本文从基础概念出发,覆盖硬件驱动、MCU配置、控制算法和保护机制,帮助你在嵌入式项目中正确使用PWM驱动电机。

## 1 PWM基础概念

### 1.1 什么是PWM

PWM(Pulse Width Modulation,脉宽调制)是一种用数字信号控制模拟量的技术:

- 信号只有高电平和低电平两种状态
- **占空比(Duty Cycle)** = 高电平时间 / 周期时间 * 100%
- 平均输出电压 = 供电电压 * 占空比

```
占空比 25%:        占空比 50%:        占空比 75%:
 ___                   ___               ___
|   |                 |   |             |   |
|   |___              |   |___          |   |___

5V*0.25=1.25V        5V*0.5=2.5V       5V*0.75=3.75V
```

### 1.2 为什么用PWM而不用线性调节

| 对比项 | 线性调节 | PWM |
|--------|----------|-----|
| 开关管工作状态 | 放大区(部分导通) | 饱和/截止区(完全导通或关断) |
| 功耗 | 管压降*电流 = 大量发热 | 导通电阻极小,发热少 |
| 效率 | 低(50-70%) | 高(90-98%) |
| 散热需求 | 需要散热片 | 通常无需散热片 |
| 控制精度 | 高(连续调节) | 取决于分辨率(8-16bit) |

对于电池供电的IoT设备,效率至关重要,PWM是唯一合理的选择。

## 2 直流电机基础

### 2.1 直流电机工作原理

永磁直流电机的两个核心关系:

- **转速**正比于电枢两端电压(忽略内阻压降时)
- **转矩**正比于电枢电流

```
V = Ke * omega + I * R
T = Kt * I

V: 施加电压
Ke: 反电动势常数
omega: 角速度
I: 电枢电流
R: 电枢电阻
Kt: 转矩常数
```

### 2.2 从电压到转速

PWM控制电机转速的本质是控制平均电压:

```
V_avg = V_supply * duty_cycle
转速 n = (V_avg - I*R) / Ke
```

空载时电流I很小,转速近似正比于占空比。带载后,同样的占空比转速会降低,这就是开环控制的局限。

## 3 H桥驱动电路

### 3.1 H桥结构

H桥由4个开关管组成,可以控制电机的正转、反转和制动:

```
      Q1              Q3
V+ ---||----+----||--- V+
             |
          [MOTOR]
             |
V- ---||----+----||--- V-
      Q2              Q4
```

| 运行模式 | Q1 | Q2 | Q3 | Q4 | 电流方向 |
|----------|----|----|----|----|----------|
| 正转     | ON | OFF| OFF| ON | V+ -> Q1 -> 电机 -> Q4 -> V- |
| 反转     | OFF| ON | ON | OFF| V+ -> Q3 -> 电机 -> Q2 -> V- |
| 刹车     | ON | OFF| ON | OFF| 电机短路制动 |
| 滑行     | OFF| OFF| OFF| OFF| 电机自由旋转 |

### 3.2 直通保护

直通(Shoot-through)是H桥最致命的故障:同侧上下管同时导通,造成电源短路,瞬间烧毁开关管。

防护措施:

- 硬件死区:驱动IC内置死区时间(典型50-200ns)
- 软件死区:软件设置互补PWM的死区时间
- 互锁逻辑:上下管控制信号用硬件逻辑互锁

### 3.3 自举电路

高侧NMOS管的栅极电压需要高于源极(即电源电压),需要自举(Bootstrap)电路:

```
VCC ---[Diode]---+--- VB (自举电容正极)
                 |         |
                [C_boot]  [High-side Driver]
                 |         |
V+ -------------+--- VS (高侧源极)
```

自举电容在低侧导通时充电,在高侧导通时提供驱动电压。这意味着:

- 首个PWM周期高侧可能驱动不足(电容未充满)
- 占空比接近100%时自举电容会放电过多,高侧可能退出饱和区
- 典型最大占空比限制在95-99%

## 4 PWM频率选择

### 4.1 频率范围

| 频率范围 | 特点 | 适用场景 |
|----------|------|----------|
| 100Hz-1kHz | 可听噪音明显,电流纹波大 | 不推荐 |
| 1kHz-20kHz | 可听噪音区(啸叫) | 低成本风扇 |
| 20kHz-50kHz | 超声波,人耳不可闻 | 大多数IoT应用 |
| 50kHz-200kHz | 开关损耗增大 | 小电感电机 |
| >200kHz | 损耗过大,EMI问题 | 极少使用 |

### 4.2 频率选择的权衡

- **频率太低**:电流纹波大,电机振动明显,运行粗糙
- **频率太高**:开关损耗增大(每次开关都有过渡损耗),驱动器发热,EMI加重
- **经验法则**:选择使电流纹波在平均电流10-20%以内的最低频率

电流纹波近似:

```
delta_I = (V_supply * duty * (1-duty)) / (f_pwm * L_motor)
```

L_motor为电机电感,电感越大,纹波越小,频率可以越低。

## 5 常用驱动IC

### 5.1 L298N

- 双H桥,可驱动两路电机
- 双极性晶体管输出,饱和压降约2V(发热严重)
- 最高46V,每桥2A
- 价格便宜,教学常用
- 缺点:效率低,散热需求大,不推荐产品级使用

### 5.2 DRV8833

- 双H桥,现代MOSFET工艺
- 低导通电阻(约360mOhm每桥)
- 2.7-10.8V供电,每桥1.5A连续
- 内置过温保护和过流保护
- 适合3.3V/5V低压IoT设备

### 5.3 TB6612FNG

- 双H桥,MOSFET输出
- 导通电阻约500mOhm
- 2.5-13.5V供电,每桥1.2A连续(峰值3.2A)
- standby模式功耗极低(<1uA)
- 体积小(SSOP-24),适合空间受限的IoT设计

### 5.4 选型对比

| 参数 | L298N | DRV8833 | TB6612 |
|------|-------|---------|--------|
| 电压范围 | 4.5-46V | 2.7-10.8V | 2.5-13.5V |
| 持续电流 | 2A | 1.5A | 1.2A |
| 导通电阻 | 约3Ohm | 约0.36Ohm | 约0.5Ohm |
| 效率 | 低 | 高 | 高 |
| 保护功能 | 无 | 过温/过流 | 过温/过流 |
| 价格 | 低 | 中 | 中 |

## 6 MCU定时器配置

### 6.1 定时器外设结构

以STM32为例,PWM输出需要配置定时器:

```
时钟源 -> 预分频器(PSC) -> 计数器(CNT) -> 自动重载寄存器(ARR)
                                          |
                                    比较寄存器(CCR) -> PWM输出
```

- **PSC(预分频器)**:降低计数器时钟频率
- **ARR(自动重载值)**:决定PWM周期 = (ARR+1) / (定时器时钟 / (PSC+1))
- **CCR(比较值)**:决定占空比 = CCR / (ARR+1)

### 6.2 配置示例

```c
// STM32 HAL: 配置TIM3 CH1 输出20kHz PWM
void PWM_Init(void) {
    TIM_HandleTypeDef htim3;
    htim3.Instance = TIM3;
    htim3.Init.Prescaler = 0;        // 不分频, 72MHz
    htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    htim3.Init.Period = 3599;        // ARR: 72M/3600 = 20kHz
    htim3.Init.ClockDivision = 0;
    HAL_TIM_PWM_Init(&htim3);

    TIM_OC_InitTypeDef sConfig;
    sConfig.OCMode = TIM_OCMODE_PWM1;
    sConfig.Pulse = 0;               // 初始占空比0%
    sConfig.OCPolarity = TIM_OCMODE_PWM1;
    HAL_TIM_PWM_ConfigChannel(&htim3, &sConfig, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
}

// 设置占空比 (0-100%)
void PWM_SetDuty(uint8_t duty_percent) {
    uint32_t pulse = (3599 + 1) * duty_percent / 100;
    __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, pulse);
}
```

### 6.3 互补输出与死区

对于H桥驱动,需要互补PWM输出(一对高低侧信号):

```
TIMx_CH1  ----+    +----+    +----
              |    |    |    |
TIMx_CH1N ---+    +----+    +----
              |<->|    |<->|
              死区     死区
```

STM32高级定时器(TIM1/TIM8)支持:

- 互补通道自动输出
- 可编程死区时间(典型50-200ns)
- Break输入(故障时自动关闭所有输出)

## 7 速度控制

### 7.1 开环控制

直接设置占空比,不测量实际转速:

- 优点:简单,无需编码器
- 缺点:负载变化时转速不稳定,电池电压下降时转速也下降
- 适用:风扇、水泵等对转速精度要求不高的场景

### 7.2 闭环控制

测量实际转速,反馈到控制器,形成闭环:

```
设定转速 --->[PID]---> 占空比 ---> 电机 ---> 实际转速
                ^                               |
                |---------- 编码器反馈 ---------|
```

### 7.3 PID控制器

```c
// 简单PID控制器
typedef struct {
    float Kp, Ki, Kd;     // PID系数
    float integral;        // 积分累积
    float prev_error;      // 上一次误差
    float output_limit;    // 输出限幅
} PID_t;

float PID_Update(PID_t *pid, float setpoint, float measured) {
    float error = setpoint - measured;
    pid->integral += error;
    // 积分限幅,防止积分饱和
    if (pid->integral > pid->output_limit) pid->integral = pid->output_limit;
    if (pid->integral < -pid->output_limit) pid->integral = -pid->output_limit;

    float derivative = error - pid->prev_error;
    pid->prev_error = error;

    float output = pid->Kp * error + pid->Ki * pid->integral + pid->Kd * derivative;
    // 输出限幅
    if (output > pid->output_limit) output = pid->output_limit;
    if (output < -pid->output_limit) output = -pid->output_limit;
    return output;
}
```

PID调参建议:

- 先只用P:逐渐增大Kp直到系统振荡,取振荡时Kp的60%
- 再加I:从小Ki开始,消除稳态误差
- 最后加D:小Kd抑制超调,但过大会引入噪声敏感

## 8 电流检测

### 8.1 低侧采样电阻

在H桥低侧与地之间串联一个采样电阻(典型0.05-0.5Ohm):

```
Q2/Q4 源极 ---[R_sense]--- GND
                  |
              放大器 --> ADC
```

- 电阻上的电压 = I_motor * R_sense
- 需要电流检测放大器(如INA181)放大毫伏级信号
- 只能在低侧开关导通时采样(同步采样)

### 8.2 采样时机

在PWM周期中心点采样,避开开关瞬间的尖峰:

```
PWM:  ___           ___
     |   |         |   |
     |   |    +    |   |
_____|   |________|   |_____
          ^
       采样点(中心对齐)
```

## 9 保护功能

### 9.1 过流保护

- 硬件比较器:电流超过阈值立即切断PWM(微秒级响应)
- 软件:ADC采样电流,超阈值后软件关闭(毫秒级响应,适合限流而非保护)
- 推荐:硬件保护做最后一道防线,软件做限流和监测

### 9.2 过温保护

驱动IC内置热关断(典型150-170C):

- 达到关断温度时自动关闭输出
- 温度回落后自动恢复(带迟滞)
- 不要依赖过温保护做正常工作范围,应保证散热使工作温度低于保护阈值

### 9.3 欠压锁定(UVLO)

电源电压低于阈值时关闭驱动:

- 防止低电压下开关管不完全导通(线性区,发热巨大)
- 阈值通常比最低工作电压低0.5-1V
- 恢复时带迟滞,防止在阈值附近振荡

## 10 实践案例:IoT环境监测仪风扇调速

### 10.1 需求

- 环境监测仪内部温度过高时启动散热风扇
- 风扇转速根据温度调节,降低噪音
- 5V直流风扇,最大电流200mA

### 10.2 硬件设计

```
STM32 PA6 (TIM3_CH1) ---[10Ohm]--- Gate
                                      |
                            [N-MOSFET SI2302]
                                      |
5V --- [Fan+]  [Fan-] -----+-------- Drain
                            |
                           GND
                            |
                       [R_sense 1Ohm] --- ADC
```

使用N-MOSFET低侧开关(风扇只需要单向,不需要H桥):

- PWM频率:25kHz(超声,无声运行)
- MOSFET导通电阻低(约50mOhm),压降可忽略
- 10Ohm栅极电阻限制开关速度,减少EMI

### 10.3 软件实现

```c
// 温度-转速映射(分段线性)
uint8_t Temp_To_Duty(float temp) {
    if (temp < 35.0f) return 0;       // 不需要散热
    if (temp < 40.0f) return 30;      // 低速
    if (temp < 50.0f) return 60;      // 中速
    if (temp < 60.0f) return 85;      // 高速
    return 100;                        // 全速
}

void Fan_ControlTask(void) {
    float temp = Read_InternalTemp();
    uint8_t duty = Temp_To_Duty(temp);
    PWM_SetDuty(duty);
}
```

## 11 软启动实现

### 11.1 为什么需要软启动

电机启动瞬间电流可达额定电流的5-10倍(堵转电流),可能导致:

- 电源电压瞬间跌落,复位MCU
- 驱动IC过流保护触发
- 机械冲击,降低寿命

### 11.2 实现方法

```c
// 软启动:逐步增加占空比
void SoftStart(uint8_t target_duty, uint16_t ramp_ms) {
    uint8_t current = PWM_GetDuty();
    int16_t step = (target_duty > current) ? 1 : -1;
    uint16_t delay = ramp_ms / abs(target_duty - current);

    while (current != target_duty) {
        current += step;
        PWM_SetDuty(current);
        HAL_Delay(delay);
    }
}
```

典型参数:从0到目标占空比,用200-500ms线性爬升。

## 12 制动方法

### 12.1 动态制动

将电机两端短路,电机变为发电机,能量消耗在电机内阻上:

- H桥低侧两管导通,电流通过二极管续流
- 制动力矩正比于转速(转速为零时制动力也为零)
- 实现简单,最常用

### 12.2 再生制动概念

将电机能量回馈到电源:

- 需要同步整流或专用充电电路
- Io电池供电设备中可延长续航
- 电路复杂度高,低功率IoT设备一般不采用

## 总结

PWM电机控制是IoT执行器驱动的基础技术,核心要点:

1. PWM用开关方式控制平均电压,效率远高于线性调节
2. H桥实现正反转和制动,必须做好直通保护和死区设置
3. PWM频率选择要平衡纹波、损耗和噪音,典型20-50kHz
4. 驱动IC选型关注电压/电流范围、导通电阻和保护功能
5. 开环适合风扇等简单场景,闭环PID适合精密调速
6. 软启动和过流保护是系统可靠性的基本保障

## 参考文献

1. Hughes A, Drury B. Electric Motors and Drives: Fundamentals, Types and Applications. 5th ed. Newnes, 2019.
2. STM32 Reference Manual RM0008, Timer chapter.
3. Texas Instruments. DRV8833 Dual H-Bridge Motor Driver Datasheet.
4. Barr M. Introduction to Pulse Width Modulation. Embedded Systems Programming, 2001.
5. AVR444: Sensorless BLDC Motor Control with ATmega32M1. Atmel Application Note.
