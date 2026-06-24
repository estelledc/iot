# I2C总线协议深度解析：地址/时序/仲裁

> **难度**：🟢 初级 | **领域**：嵌入式通信协议 | **阅读时间**：约 18 分钟

## 引言

想象一个教室：老师(SCL)掌握节奏，学生(SDA)轮流回答问题。只有老师拍一下桌子，学生才能开口；如果两个学生同时抢答，先开口的继续，后开口的自觉闭嘴。这就是I2C总线的日常类比——两根线、一个时钟主控、多个设备共享同一条"说话线"，靠仲裁规则避免冲突。

I2C(Inter-Integrated Circuit)由Philips半导体于1982年发明，初衷是让电视里的芯片之间低成本通信。如今从温湿度传感器到EEPROM，从OLED到PMU，几乎无处不在。本文从物理层到应用层，逐步拆解I2C的核心机制。

## 1. I2C总线概述

### 1.1 两线制架构与开漏输出

I2C只需两根信号线：

| 信号线 | 方向 | 功能 |
|--------|------|------|
| SDA | 双向 | 数据线，地址/数据/应答均在此传输 |
| SCL | 双向 | 时钟线，主机驱动，从机可拉低(stretch) |

所有设备SDA/SCL分别连在一起，形成"线与"逻辑。I2C输出级是开漏(Open-Drain)结构——设备只能拉低(输出0)，高电平由外部上拉电阻提供：

```
VCC
 |
 Rp (上拉电阻)
 |---- SDA/SCL
 |
[设备1 MOSFET]  [设备2 MOSFET]  ...  [设备N MOSFET]
 |                 |                    |
GND               GND                  GND
```

为什么用开漏而非推挽？(1) 线与安全：多设备共享时推挽可能短路，开漏天然避免；(2) 多主兼容：仲裁依赖"0覆盖1"的线与特性；(3) 电平转换：不同VCC设备通过各自开漏+共同上拉自然匹配。

### 1.2 上拉电阻取值计算

阻值太小功耗大，阻值太大上升沿过慢。由两个约束决定：

- **下限**(低电平约束)：`Rp(min) = (VCC - VOL(max)) / IOL`，IOL为总线灌电流之和
- **上限**(上升时间约束)：`Rp(max) = tr / (0.8473 * Cb)`，Cb为总线总电容

| VCC | Cb | Rp推荐 | 典型值 |
|-----|------|--------|--------|
| 3.3V | < 100pF | 1k-4.7k | 4.7k |
| 3.3V | 100-200pF | 1k-2.2k | 2.2k |
| 5.0V | < 100pF | 1k-4.7k | 4.7k |

经验法则：标准模式100kHz用4.7k，快速模式400kHz用2.2k或1k。长总线(>30cm)必须降低阻值。

## 2. 地址机制

### 2.1 7位地址

地址在START后发送，占1字节高7位，最低位是R/W方向位：

```
[ A6 | A5 | A4 | A3 | A2 | A1 | A0 | R/W ]
  |<--------- 7位地址 ---------->|  |0:写 1:读|
```

7位地址空间=128个，但保留了一部分：

| 地址范围 | 用途 |
|----------|------|
| 0x00 | 通用呼叫(General Call) |
| 0x01 - 0x07 | 保留给未来标准 |
| 0x08 - 0x77 | 可用地址(112个) |
| 0x78 - 0x7F | 10位地址及保留 |

实际可用112个，同型号传感器多了容易冲突。

### 2.2 10位地址

10位地址分两字节发送，第1字节高5位固定11110为标识前缀：

```
第1字节: [ 1 | 1 | 1 | 1 | 0 | A9 | A8 | R/W ]
第2字节: [ A7 | A6 | A5 | A4 | A3 | A2 | A1 | A0 ]
```

10位和7位地址设备可混挂在同一总线，主机通过前缀区分。

### 2.3 地址冲突与解决

同型号器件常有固定地址(如BMP280固定0x76/0x77)，两个相同器件冲突的解决方案：

| 方案 | 原理 | 优缺点 |
|------|------|--------|
| 器件ADDR引脚 | 拉高/拉低改变低1-2位 | 最简单，受限于引脚数 |
| I2C多路复用器 | TCA9548A分出8条子总线 | 灵活，增加硬件成本 |
| 软件切换 | 部分器件支持软件改地址 | 器件特定，非通用 |

## 3. 时序详解

### 3.1 启动与停止条件

START和STOP是唯一允许SDA在SCL高电平期间变化的时刻：

```
START: SCL高时, SDA高->低      STOP: SCL高时, SDA低->高
SCL: ‾‾‾‾‾‾‾‾‾‾              SCL: ‾‾‾‾‾‾‾‾‾‾
SDA: ‾‾\________               SDA: ____/‾‾‾‾‾
         ^ START                       ^ STOP
```

正常数据传输时，SDA只在SCL低时变化，SCL高时必须稳定。

### 3.2 数据帧格式

写操作：`[S] [A6-A0+W] [ACK] [D7-D0] [ACK] ... [P]`

读操作：`[S] [A6-A0+R] [ACK] [D7-D0] [NACK] [P]`

关键细节：(1) 每字节后必须跟ACK(0)或NACK(1)；(2) 读操作最后字节主机必须发NACK再发STOP；(3) MSB first，与UART相反。

### 3.3 重复启动(Repeated Start)

Sr允许主机不释放总线就切换方向或目标器件：

```
[S] [addr+W] [ACK] [reg] [ACK] [Sr] [addr+R] [ACK] [data] [NACK] [P]
```

这是经典的"先写寄存器地址，再读数据"模式。Sr保证操作原子性——用STOP+START则中间其他主机可能抢占总线。Sr和S电气条件完全相同，协议上Sr只是不产生STOP的连续操作。

三种需要Sr的典型场景：(1) 读寄存器；(2) 访问10位地址器件；(3) 确保多字节读不被打断。

### 3.4 时钟拉伸(Clock Stretching)

从机可拉低SCL"拖住"主机，争取处理时间：

```
主机SCL: ‾‾‾‾\_____________________________/‾‾‾‾
                    ^ 从机拉低            ^ 从机释放
```

典型场景：EEPROM页写(tWR约5ms)、ADC转换未完成、软件I2C跟不上硬件主机。注意：部分USB-I2C适配器不支持stretching，会导致通信失败。

### 3.5 总线速度模式

| 模式 | 速率 | 上升时间上限 | 总电容上限 | 典型应用 |
|------|------|-------------|-----------|---------|
| 标准(Standard) | 100 kHz | 1000 ns | 400 pF | 传感器/EEPROM |
| 快速(Fast) | 400 kHz | 300 ns | 400 pF | 现代传感器 |
| 快速+(Fm+) | 1 MHz | 120 ns | 550 pF | 高吞吐场景 |
| 高速(HS) | 3.4 MHz | 12 ns | 100 pF | 存储器批量读写 |

400kHz是最常用的平衡点。速度越高，上拉电阻越小、走线越短、电容控制越严。

## 4. 多主机仲裁

### 4.1 仲裁原理

两主机同时发起通信时，仲裁自动裁决。每发一位，主机回读SDA实际电平。若自己发1但读回0，说明另一主机发了0(线与)，自己退出：

```
主机A: 1 0 0 1 1 0 ... (地址0x4C)
主机B: 1 0 0 1 0 1 ... (地址0x4A)
               ^
               第5位: A发1, B发0, 总线=0
               A读到0!=1 → A退出, B继续
```

关键特性：(1) **不破坏数据**——退出方只在发出位与总线不一致时才退出；(2) **地址越低越优先**——0x00永远赢；(3) **零额外成本**——仲裁完全利用SDA线与特性。

### 4.2 仲裁失败后的处理

1. 切换为从机模式，监听总线(可能正被寻址)
2. 等待总线空闲(STOP后)
3. 重新发起通信

STM32 HAL中仲裁失败产生`HAL_I2C_ERROR_ARLO`错误码，软件需处理。

## 5. 电气特性与信号完整性

标准模式与快速模式关键时序参数对比：

| 参数 | 标准模式 | 快速模式 | 说明 |
|------|---------|---------|------|
| fSCL | 0-100 kHz | 0-400 kHz | SCL频率 |
| tHD;STA | 4.0 us | 0.6 us | START后SCL低保持时间 |
| tSU;STA | 4.7 us | 0.6 us | START前SCL高建立时间 |
| tSU;DAT | 250 ns | 100 ns | 数据建立时间 |
| tBUF | 4.7 us | 1.3 us | STOP到下次START空闲时间 |

常见信号问题：上升沿过缓(Rp过大)、振铃(长走线+快边沿)、串扰(SDA/SCL平行过长)。解决：缩短走线、降低Rp、必要时加100pF滤波电容、SDA与SCL间加地线隔离。

## 6. I2C在STM32上的实践

### 6.1 HAL库基本操作

**初始化配置**：

```c
I2C_HandleTypeDef hi2c1;

void MX_I2C1_Init(void) {
    hi2c1.Instance             = I2C1;
    hi2c1.Init.ClockSpeed      = 400000;  // 400kHz快速模式
    hi2c1.Init.DutyCycle       = I2C_DUTYCYCLE_2;
    hi2c1.Init.OwnAddress1     = 0;
    hi2c1.Init.AddressingMode  = I2C_ADDRESSINGMODE_7BIT;
    hi2c1.Init.NoStretchMode   = I2C_NOSTRETCH_DISABLE;
    HAL_I2C_Init(&hi2c1);
}
```

**写寄存器 / 读多字节**：

```c
// 写: 向0x76器件的0xF4寄存器写入0x27
HAL_I2C_Mem_Write(&hi2c1, 0x76 << 1, 0xF4,
                  I2C_MEMADD_SIZE_8BIT,
                  (uint8_t[])0x27, 1, 100);

// 读: 从0xF7寄存器连续读6字节(自动发Sr条件)
uint8_t buf[6];
HAL_I2C_Mem_Read(&hi2c1, 0x76 << 1, 0xF7,
                 I2C_MEMADD_SIZE_8BIT, buf, 6, 100);
```

### 6.2 地址左移的坑

HAL的DevAddress参数是8位格式(7位地址左移1位)，而器件手册通常标注7位地址：

```c
// 错误: 直接传7位地址, 实际访问0x0E!
HAL_I2C_Mem_Read(&hi2c1, 0x76, ...);
// 正确: 左移1位
HAL_I2C_Mem_Read(&hi2c1, 0x76 << 1, ...);
// 推荐用宏
#define I2C_ADDR_7BIT(x)  ((x) << 1)
```

### 6.3 DMA传输

大数据量传输(如图像传感器)应使用DMA避免CPU空等：

```c
HAL_I2C_Mem_Read_DMA(&hi2c1, devAddr, regAddr,
                      I2C_MEMADD_SIZE_8BIT, rxBuf, rxLen);

void HAL_I2C_MemRxCpltCallback(I2C_HandleTypeDef *hi2c) {
    dataReady = 1;  // 通知应用层
}
```

## 7. 常见问题与调试

### 7.1 总线锁死与恢复

总线锁死表现：SDA或SCL一直被拉低。根因：从机发送数据时主机异常复位，从机持续拉低SDA等待时钟。

恢复方法——手动产生9个SCL脉冲让从机完成未发完的字节，再产生STOP：

```c
void I2C_Bus_Recovery(I2C_HandleTypeDef *hi2c) {
    // 将SCL配置为GPIO输出, 产生9个时钟脉冲
    for (int i = 0; i < 9; i++) {
        HAL_GPIO_WritePin(I2C_SCL_GPIO, I2C_SCL_PIN, GPIO_PIN_RESET);
        HAL_Delay(1);
        HAL_GPIO_WritePin(I2C_SCL_GPIO, I2C_SCL_PIN, GPIO_PIN_SET);
        HAL_Delay(1);
        if (HAL_GPIO_ReadPin(I2C_SDA_GPIO, I2C_SDA_PIN) == GPIO_PIN_SET)
            break;  // SDA已高, 总线恢复
    }
    // 产生STOP: SDA低 -> SCL高 -> SDA高
    HAL_GPIO_WritePin(I2C_SDA_GPIO, I2C_SDA_PIN, GPIO_PIN_RESET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(I2C_SCL_GPIO, I2C_SCL_PIN, GPIO_PIN_SET);
    HAL_Delay(1);
    HAL_GPIO_WritePin(I2C_SDA_GPIO, I2C_SDA_PIN, GPIO_PIN_SET);
    HAL_I2C_DeInit(hi2c);
    MX_I2C1_Init();
}
```

9个时钟的原理：从机最多还有1字节(8位)+1个ACK没发完，9个脉冲足以让其释放SDA。

### 7.2 NACK常见原因

| 阶段 | NACK原因 | 排查方法 |
|------|---------|---------|
| 地址阶段 | 器件地址错误 | 用i2cdetect扫描 |
| 地址阶段 | 器件未上电/未接好 | 测VCC和接线 |
| 地址阶段 | 器件正在复位 | 查复位时间，加延时 |
| 数据阶段 | 写入只读寄存器 | 查手册寄存器属性 |
| 数据阶段 | 数据超量 | 确认不超页边界 |

### 7.3 逻辑分析仪调试

推荐步骤：(1) CH0接SCL，CH1接SDA；(2) 选择I2C协议解码，采样率>=10倍SCL频率；(3) 触发START条件单次捕获；(4) 分析地址/ACK/时序。

```
解码输出示例:
START | 0x76(W) | ACK | 0xF4 | ACK | 0x27 | ACK | STOP
           地址0x76      寄存器0xF4    数据0x27
```

分析要点：地址和R/W是否正确、ACK/NACK是否符合预期、SCL频率是否在范围、上升沿是否过缓、有无意外START/STOP。

## 8. I2C多路复用器实战

TCA9548A是8通道I2C多路复用器，自身地址0x70(可改为0x71-0x77)：

```c
#define TCA9548A_ADDR  (0x70 << 1)

void TCA9548A_SelectChannel(uint8_t ch) {
    uint8_t data = (1 << ch);  // bit0=CH0, bit1=CH1, ...
    HAL_I2C_Master_Transmit(&hi2c1, TCA9548A_ADDR, &data, 1, 100);
}

// 读取两个地址相同的传感器
void Read_Two_Sensors(void) {
    uint8_t buf[2];
    TCA9548A_SelectChannel(0);
    HAL_I2C_Mem_Read(&hi2c1, 0x76<<1, 0xF7, I2C_MEMADD_SIZE_8BIT, buf, 2, 100);
    uint16_t val_ch0 = (buf[0] << 8) | buf[1];

    TCA9548A_SelectChannel(1);
    HAL_I2C_Mem_Read(&hi2c1, 0x76<<1, 0xF7, I2C_MEMADD_SIZE_8BIT, buf, 2, 100);
    uint16_t val_ch1 = (buf[0] << 8) | buf[1];
}
```

级联可扩展到64通道(2级TCA9548A)，超过2级延迟和复杂度显著增加，通常不建议。

## 9. I2C vs SPI vs UART

| 特性 | I2C | SPI | UART |
|------|-----|-----|------|
| 信号线 | 2(SDA+SCL) | 4+(MOSI+MISO+SCK+CSx) | 2(TX+RX) |
| 拓扑 | 多点(总线) | 点对点(需CS) | 点对点 |
| 速率 | <=3.4MHz | <=80MHz | <=1.5MHz |
| 寻址 | 硬件地址 | CS选片 | 无(软件协议) |
| 双工 | 半双工 | 全双工 | 全双工 |
| 仲裁 | 硬件仲裁 | 无 | 无 |

选择建议：器件多/引脚紧张用I2C，高速/全双工用SPI，远距离点对点用UART。

## 总结

I2C的核心设计哲学是**用最少的线实现最多的功能**。两根线承载了寻址、方向控制、应答、仲裁、时钟同步等所有机制，代价是协议复杂度和速率上限。

关键要点回顾：

1. **开漏+上拉**是I2C一切机制的基础——线与特性保证多设备安全共存和多主仲裁
2. **7位地址**够用但需关注冲突；10位地址扩展到1024个器件
3. **时序**的关键约束是SDA只能在SCL低时变化(START/STOP除外)
4. **仲裁**自动、无损、零额外成本，但地址越低优先级越高
5. **Repeated Start**保证复合操作原子性，不可用STOP+START替代
6. **总线锁死**用9个SCL脉冲恢复，是生产环境必备的容错代码
7. **上拉电阻**取值需同时满足低电平电流和上升时间两个约束

实践中，建议始终用逻辑分析仪验证第一版I2C通信，把时序问题在开发早期消灭。

## 参考文献

1. NXP Semiconductors. *I2C-bus specification and user manual* (UM10204), Rev. 7.0, 2021.
2. STM32F4xx HAL Driver User Manual (UM1725), STMicroelectronics.
3. Texas Instruments. *I2C Bus Pullup Resistor Calculation* (SLVA689), Application Note, 2015.
4. TCA9548A Low-Voltage 8-Channel I2C Switch Data Sheet, Texas Instruments, 2023.
5. W. Wolf, *Computers as Components: Principles of Embedded Computing System Design*, 4th ed., Morgan Kaufmann, 2017, ch. 8.
