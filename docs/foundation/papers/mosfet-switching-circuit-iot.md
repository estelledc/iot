# MOSFET开关电路在IoT负载控制中的设计

> **难度**：🟢 初级 | **领域**：功率开关设计 | **阅读时间**：约 18 分钟

## 引言

想象你家里的灯开关——你轻轻一拨，电流就通了。MOSFET在电路中就是这样一个电子开关，只不过它由电压控制而不是机械动作。在IoT设备中，MCU的GPIO只能输出3.3V、几毫安的微弱信号，但需要控制的负载可能是12V、几安培的LED灯带、电机或加热器。MOSFET就是MCU和功率负载之间的"大力士"——MCU给一个信号，MOSFET完成重活。

## 1. 为什么用MOSFET做开关

### 1.1 MOSFET vs BJT vs 继电器

| 特性 | MOSFET | BJT | 继电器 |
|------|--------|-----|--------|
| 驱动方式 | 电压驱动 | 电流驱动 | 电流驱动 |
| 驱动功耗 | 几乎为零(稳态) | 需持续基极电流 | 需持续线圈电流 |
| 开关速度 | ns-us级 | us级 | ms级 |
| 导通压降 | I*Rds_on(可很低) | Vce_sat约0.2-0.7V | 接触电阻约50mO |
| 寿命 | 半永久 | 半永久 | 机械磨损 |
| 体积 | 小(SOT-23) | 小 | 大 |

### 1.2 MOSFET优势

- **低导通损耗**：Rds_on可低至1mO，远优于BJT的Vce饱和压降
- **电压控制**：栅极几乎不取电流，MCU GPIO可直接驱动(逻辑电平MOSFET)
- **快速开关**：适合PWM调光、电机调速
- **无机械磨损**：适合频繁开关的IoT场景

## 2. N沟道与P沟道

### 2.1 N沟道MOSFET(低边开关)

```
        Vcc
         |
       [负载]
         |
    D --|   |-- G (MCU GPIO)
        |   |
    S --|___|-- S --> GND
```

- 负载接在Vcc和漏极之间，源极接地
- 栅极高电平导通，低电平关断
- 驱动简单，Rds_on低

### 2.2 P沟道MOSFET(高边开关)

```
        Vcc
         |
    S --|   |-- G
        |   |
    D --|___|-- D --> [负载] --> GND
```

- 源极接Vcc，负载接在漏极和地之间
- 栅极拉低导通，拉高到Vcc关断
- Rds_on通常是N-MOSFET的2-3倍

### 2.3 选择原则

| 场景 | 推荐 | 原因 |
|------|------|------|
| 简单开关 | N-MOSFET低边 | 驱动简单，Rds_on低 |
| 需要负载完全断电 | P-MOSFET高边 | 切断Vcc通路 |
| 电池防反接 | P-MOSFET | 源极接电池正极 |
| H桥电机驱动 | N+P组合 | 双向电流 |

## 3. 关键MOSFET参数

### 3.1 栅极阈值电压(Vgs_th)

MOSFET刚开始导通的栅源电压，通常1-4V。注意：Vgs_th只是"开始导通"的阈值，此时Rds_on仍然很大。要获得标称Rds_on，Vgs需要远高于Vgs_th。

```
例: IRLML6344 (逻辑电平N-MOSFET)
Vgs_th = 1.0V(典型)
Rds_on @ Vgs=2.5V: 60mO
Rds_on @ Vgs=4.5V: 45mO
Rds_on @ Vgs=1.8V: 120mO (Rds_on增大2-3倍!)
```

### 3.2 导通电阻(Rds_on)

MOSFET完全导通时漏源之间的电阻，直接决定导通损耗：

```
导通功耗 P = I^2 * Rds_on
例: 负载电流2A, Rds_on = 50mO
P = 2^2 * 0.05 = 0.2W
如果是BJT: P = I * Vce_sat = 2 * 0.5 = 1W (损耗大5倍)
```

### 3.3 漏源耐压(Vds_max)与漏极电流(Id_max)

```
选型裕量: Vds_max >= 1.5 * Vcc_max
例: 12V系统 -> 选30V或40V规格

Id_max需降额: 实际电流不超过Id_max的50-70%
(标称值在25C壳温下测得，高温需降额)
```

### 3.4 栅极电荷(Qg)

开关一次栅极需要充入的电荷量，影响开关速度和驱动功耗：

```
开关功耗 Psw = Qg * Vgs * f_switch
例: Qg=10nC, Vgs=3.3V, f=1kHz -> Psw=33uW (可忽略)
例: Qg=50nC, Vgs=12V, f=100kHz(PWM) -> Psw=60mW (需关注)
```

## 4. 低边N-MOSFET开关设计

### 4.1 基本电路

```
        12V
         |
       [LED灯带]
         |
    D --|IRLML6344|-- G --[100O]-- MCU GPIO (3.3V)
        |          |                |
    S --|__________|--             100kO
         |                          |
        GND                        GND
```

### 4.2 元件作用

- **100O栅极电阻**：限制栅极充放电电流，减缓开关边沿，减少EMI
- **100kO下拉电阻**：MCU复位期间GPIO为高阻态，下拉确保MOSFET关断
- **逻辑电平MOSFET**：3.3V GPIO即可充分导通

### 4.3 GPIO配置

```c
// STM32 HAL: 配置GPIO推挽输出
void mosfet_gpio_init(void) {
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = GPIO_PIN_5;
    GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;  // 推挽输出
    GPIO_InitStruct.Pull = GPIO_PULLDOWN;         // 内部下拉
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;  // 低速(减小EMI)
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);
    HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
}
```

## 5. 高边P-MOSFET开关设计

### 5.1 基本电路(含电平转换)

当Vcc > MCU Vcc时，需要N-MOSFET做电平转换：

```
        12V
         |
    S --|SI2301(P-MOS)|-- G --[10kO]-- 12V
        |              |         |
    D --|______________|      [N-MOS]
         |                        |
       [负载]                    GND
         |                        |
        GND                  MCU GPIO
```

工作过程：
- MCU GPIO高 -> N-MOS导通 -> P-MOS栅极拉到GND -> P-MOS导通
- MCU GPIO低 -> N-MOS关断 -> P-MOS栅极被10kO拉到12V -> P-MOS关断

### 5.2 电池断路开关

P-MOSFET常用作电池供电系统的总开关：

```
电池+ ---[P-MOS(SI2301)]--- Vcc系统
              |
            G --- [1MO] --- 电池+
              |
           [按键/EN信号] --- GND

按键按下: Vgs = -Vbat, P-MOS导通
松开按键: Vgs = 0, P-MOS关断, 零待机功耗
```

## 6. 栅极驱动要点

### 6.1 逻辑电平MOSFET

3.3V MCU必须选逻辑电平规格的MOSFET：

```
常见逻辑电平N-MOSFET:
- IRLML6344: 30V/3.4A, Rds_on=45mO@4.5V, SOT-23
- SI2302: 20V/2.2A, Rds_on=65mO@4.5V, SOT-23
- AO3400: 30V/5.8A, Rds_on=26mO@4.5V, SOT-23

常见逻辑电平P-MOSFET:
- SI2301: -20V/-2.2A, Rds_on=120mO@-4.5V, SOT-23
- AO3401: -30V/-4.2A, Rds_on=58mO@-4.5V, SOT-23
```

### 6.2 栅极电阻与米勒平台

栅极电阻选择：22-220O(大多数IoT场景100O即可)。太小则EMI严重，太大则开关损耗增大。

MOSFET开关过程中存在米勒平台：漏极电压变化通过Cgd耦合到栅极，使Vgs暂时不变。米勒平台期间功耗最大(P=Id*Vds)，Qg越大的MOSFET平台越长。

## 7. 功耗计算与散热

### 7.1 导通损耗与开关损耗

```
导通损耗: P_cond = I^2 * Rds_on
例: 1A, Rds_on=50mO -> P_cond = 0.05W

开关损耗: P_sw = 0.5 * Vds * Id * (t_rise+t_fall) * f_sw
例: 12V, 1A, 100ns, 1kHz -> P_sw = 0.6mW (可忽略)
    12V, 1A, 100ns, 20kHz -> P_sw = 12mW (仍可接受)
```

### 7.2 封装热阻

| 封装 | 热阻(Rth_ja) | 适用功耗 |
|------|-------------|---------|
| SOT-23 | 200-300C/W | <0.3W |
| SOT-223 | 60-80C/W | <1W |
| DPAK | 40-60C/W | <2W |
| D2PAK | 30-50C/W | <3W |

```
温升 = P_total * Rth_ja
要求: T_junction < 125C (留裕量)
```

## 8. 保护电路

### 8.1 栅极ESD保护

MOSFET栅极氧化层极薄(几十nm)，容易被ESD击穿。用齐纳二极管(如5.1V)将Vgs钳位在安全范围：

```
GPIO --[Rg]--+-- Gate
              |
          Zener(5.1V)
              |
             GND
```

### 8.2 感性负载续流二极管

电机、继电器线圈、电磁阀等感性负载关断瞬间产生反向电动势，必须加续流二极管：

```
        Vcc
         |
       [电机]
         |-----|<|----- Vcc
         |   续流二极管
    D --|MOS|
         |
        GND
```

二极管选择：额定电流>=负载电流，反向耐压>=Vcc。常用1N4148(小电流)或1N5819(大电流肖特基)。

### 8.3 过流保护

三种方案：
1. **保险丝**：一次性，最简单
2. **自恢复保险丝(PTC)**：过流后自动恢复
3. **电流采样+MCU保护**：采样电阻+ADC监测，超阈值关断MOSFET

## 9. 实战案例

### 9.1 3.3V MCU控制12V LED灯带

```
设计: LED灯带12V/2A, STM32L4 GPIO 3.3V
选型: AO3400 (N-MOS, 30V/5.8A, Rds_on=26mO@4.5V)
3.3V Vgs下Rds_on约50mO, 功耗=2^2*0.05=0.2W
SOT-23温升=0.2*250=50C, 结温约90C (可接受)
```

```c
// LED PWM调光
void led_breath(void) {
    for (int i = 0; i < 256; i++) {
        __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, i);
        HAL_Delay(10);
    }
}
```

### 9.2 电池总开关

```
设计: 锂电池3.0-4.2V, 最大500mA, 关断时零功耗
选型: SI2301 (P-MOS, -20V/-2.2A)
电路: 电池+--SI2301(S/D)--Vcc系统, G--[1MO]--电池+, G--[按键]--GND
按键按下导通, 松开关断, 零待机功耗
```

### 9.3 直流电机H桥

```
         6V
          |
    Q1(N)   Q3(N)
      |        |
      +--[电机]--+
      |        |
    Q2(N)   Q4(N)
          |
         GND

正转: Q1+Q4导通  反转: Q2+Q3导通
刹车: Q2+Q4导通  滑行: 全部关断
注意: 死区时间! 上下管不能同时导通(直通短路)
```

## 10. IoT常见负载选型速查

| 负载类型 | 电压/电流 | 推荐MOSFET | 封装 | 备注 |
|---------|----------|-----------|------|------|
| LED指示灯 | 3.3V/20mA | IRLML6344 | SOT-23 | 过杀但便宜 |
| LED灯带 | 12V/2A | AO3400 | SOT-23 | 注意散热 |
| 小直流电机 | 6V/500mA | SI2302 | SOT-23 | 加续流二极管 |
| 电磁阀 | 12V/1A | AO3400 | SOT-23 | 加续流二极管 |
| 加热片 | 5V/3A | AO4407(P) | DPAK | 逻辑电平 |
| 电池开关 | 4.2V/2A | SI2301(P) | SOT-23 | 高边开关 |

## 11. 常见错误与避坑

### 11.1 Vgs不足导致未充分导通

错误认知：Vgs超过Vgs_th(如1V)就能当开关用。

正确理解：Vgs_th只是"开始导通"的阈值，此时Rds_on极大。3.3V系统必须选逻辑电平MOSFET，确认Rds_on在Vgs=2.5V或4.5V下达标。

### 11.2 MCU复位时MOSFET意外导通

错误认知：GPIO默认低电平，MOSFET不会导通。

正确理解：MCU复位期间GPIO为高阻态，MOSFET栅极悬空可能因噪声导通。必须加下拉电阻(N-MOS)或上拉电阻(P-MOS)确保复位期间关断。

### 11.3 忽视散热问题

错误认知：SOT-23小封装也能开关几安培。

正确理解：SOT-23热阻约250C/W，0.5W功耗就升温125C。大电流选DPAK/D2PAK封装，PCB铺铜皮散热。

### 11.4 感性负载不加续流二极管

错误认知：断电后电流自然消失。

正确理解：感性负载电流不能突变，关断瞬间产生反向高压尖峰可击穿MOSFET。必须加续流二极管提供泄放路径。

## 总结

MOSFET开关电路是IoT负载控制的基础，核心要点：

- **低边开关用N-MOSFET**：驱动简单，Rds_on低，首选方案
- **高边开关用P-MOSFET**：负载可完全断电，但需注意电平转换
- **3.3V系统必须选逻辑电平MOSFET**：确认Rds_on在低Vgs下达标
- **栅极必须加下拉/上拉电阻**：防止MCU复位期间意外导通
- **感性负载必须加续流二极管**：保护MOSFET不被反电势击穿
- **关注散热**：SOT-23适合1A以下，大电流选DPAK以上

每次设计都检查Vgs裕量、功耗温升、保护电路这三项，就能避开90%的坑。

## 参考文献

1. Infineon. AN201608: MOSFET Gate Driver Design. Application Note. 2016.
2. ON Semiconductor. AND9093/D: MOSFET Selection Guide for DC-DC Converters. 2018.
3. A. Bindra. "MOSFET Gate Drive Considerations." IEEE Power Electronics Magazine, vol. 5, no. 4, 2018.
4. Alpha & Omega Semiconductor. AO3400 datasheet: N-Channel Enhancement Mode MOSFET. 2020.
5. Vishay. AN608: Power MOSFET Basics: Understanding Gate Charge. 2016.
