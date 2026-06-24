# FRAM/MRAM/NVRAM新型非易失存储对比
> **难度**：🟡 中级 | **领域**：新型存储技术 | **阅读时间**：约 20 分钟

## 引言

传统非易失存储就像两种笔记本：一种(EEPROM)每页只能写一个字但能反复擦写，另一种(Flash)每页能写很多字但必须整本擦除重写，而且都有"写废"的一天。如果有一种笔记本，写得跟铅笔一样快、擦得跟橡皮一样方便、永远写不坏，那该多好？FRAM和MRAM就是向这个方向迈出的关键一步——它们写入速度接近SRAM，寿命几乎无限，同时断电不丢数据。本文对比FRAM、MRAM、ReRAM等新型非易失存储，看它们如何突破传统NVM的瓶颈，以及在IoT中的实际应用。

## 1. 传统NVM的局限性

### 1.1 Flash的瓶颈

Flash存储器虽然容量大、成本低，但在IoT场景中面临三个根本性限制：

- **写入慢**：必须先擦除整个扇区(4KB-256KB)再写入，擦除时间可达数百毫秒
- **寿命有限**：每个扇区擦写1万-10万次后可能失效，频繁写入场景(如每秒记录一次传感器数据)几个月就可能耗尽寿命
- **写放大**：逻辑上修改1字节，物理上需要擦除+重写整个扇区，浪费大量寿命

### 1.2 EEPROM的局限

EEPROM虽支持字节级擦写且寿命达100万次，但：

- **容量小**：通常1KB-1MB，无法存储大数据量
- **写入慢**：每字节写入约需5ms，不适合高频数据采集
- **成本高**：每比特成本远高于Flash

这些局限催生了对新型非易失存储的需求：写入快、寿命长、容量适中、功耗低。

## 2. FRAM：铁电存储器

### 2.1 工作原理

FRAM(Ferroelectric RAM)利用铁电材料的**极化方向**存储数据。核心存储单元是一个铁电电容，其内部晶格中的原子有两个稳定的极化状态(向上/向下)，分别表示0和1。

```
铁电电容结构:
       电极
    |-------|
    | 铁电  |  <- PZT或BLT薄膜
    | 薄膜  |     原子极化方向 = 数据(0/1)
    |-------|
       电极

读取: 施加电场, 检测极化翻转产生的电流脉冲
写入: 施加足够电场, 切换极化方向
```

关键点：极化切换所需的能量极低(约1-2V电压即可)，切换速度在纳秒级，且不像Flash那样需要高电压隧穿，因此不会损伤介质。

### 2.2 核心特性

| 参数 | FRAM |
|------|------|
| 擦写粒度 | 字节级 |
| 擦写寿命 | 10的14次方次(几乎无限) |
| 写入速度 | 与SRAM相当(约50-100ns) |
| 读取速度 | 约100ns |
| 容量 | 4Kb-8Mb(独立芯片), 16KB-256KB(MCU内置) |
| 写入电压 | 1.5V-3.6V(无需电荷泵) |
| 功耗 | 极低(写入电流约1mA) |
| 保持时间 | 10年(85度C)至150年(25度C) |
| 破坏性读出 | 是(读后需回写) |

### 2.3 破坏性读出与对策

FRAM的读取是**破坏性**的——检测极化方向会改变状态。因此每次读取后必须自动回写(DRA: Destructive Read with Auto-Restore)。现代FRAM芯片已将此过程集成在硬件中，对用户透明。但这也意味着读取操作也会消耗寿命，不过10的14次方的数量级使此影响可忽略。

### 2.4 无需磨损均衡

FRAM的10的14次方次寿命意味着：即使每秒写入1000次，可连续使用约317万年。因此FRAM完全不需要磨损均衡(Wear Leveling)算法，开发复杂度大幅降低。

## 3. MRAM：磁阻存储器

### 3.1 工作原理

MRAM(Magnetoresistive RAM)利用**磁隧道结(MTJ: Magnetic Tunnel Junction)**存储数据。MTJ由两层铁磁层夹一层绝缘层构成：

```
磁隧道结结构:
  | 自由层(Free Layer)   | <- 磁化方向可切换 = 数据(0/1)
  | 绝缘势垒(MgO)        | <- 约1nm厚
  | 固定层(Pinned Layer) | <- 磁化方向固定

平行状态 -> 低电阻 -> 0
反平行状态 -> 高电阻 -> 1
```

写入时通过电流产生的磁场或自旋转移力矩(STT: Spin Transfer Torque)切换自由层的磁化方向。读取时测量MTJ的电阻值判断状态。

### 3.2 Toggle MRAM vs STT-MRAM

| 对比项 | Toggle MRAM | STT-MRAM |
|--------|-------------|----------|
| 写入方式 | 电流产生磁场切换 | 自旋极化电流直接切换 |
| 单元面积 | 较大(约20F2) | 较小(约6-10F2) |
| 密度 | 低 | 高,接近DRAM |
| 写入电流 | 较大(约5-10mA) | 较小(约50-100uA) |
| 工艺节点 | 130nm-180nm | 28nm-40nm |
| 代表产品 | Everspin MR4A16B | Everspin EMxxLX, STT-MRAM IP |

STT-MRAM是当前主流方向，密度更高、功耗更低，已开始嵌入先进工艺节点的MCU/SoC中。

### 3.3 核心特性

| 参数 | MRAM(STT-MRAM) |
|------|----------------|
| 擦写粒度 | 字节级 |
| 擦写寿命 | 几乎无限(10的15次方次以上) |
| 写入速度 | 约10-35ns |
| 读取速度 | 约10-30ns |
| 容量 | 1Mb-256Mb |
| 写入电压 | 1.2V-3.3V |
| 功耗 | 极低(待机约10uA) |
| 辐射耐受 | 强(抗单粒子翻转) |
| 保持时间 | 20年以上 |

### 3.4 辐射耐受特性

MRAM的磁化状态不受电离辐射影响，这使其在航天、汽车电子等恶劣环境下具有独特优势。相比之下，Flash和SRAM在强辐射环境下容易发生位翻转。

## 4. ReRAM/RRAM：阻变存储器

### 4.1 工作原理

ReRAM(Resistive RAM)利用金属氧化物薄膜在电压作用下形成/断开导电细丝(filament)来实现高低阻态切换：

```
ReRAM单元结构:
  | 上电极(Pt/TiN) |
  | 金属氧化物(HfO2/TaOx) | <- 导电细丝 = 低阻(1)
  | 下电极(Pt/TiN) |         无细丝 = 高阻(0)

Set: 施加正电压 -> 形成细丝 -> 低阻态
Reset: 施加反电压 -> 断开细丝 -> 高阻态
```

### 4.2 核心特性

| 参数 | ReRAM |
|------|-------|
| 擦写寿命 | 10的6次方-10的10次方次(差异大) |
| 写入速度 | 约10-100ns |
| 读取速度 | 约10-50ns |
| 容量 | 实验室可达Gb级 |
| 单元面积 | 约4F2(极小) |
| 写入电压 | 约1-3V |
| 成熟度 | 研发/早期量产阶段 |

ReRAM目前成熟度较低，寿命一致性是主要挑战，但高密度潜力使其在嵌入式存储领域有前景。

## 5. 新型NVM全面对比

| 对比维度 | FRAM | MRAM | ReRAM | Flash(NOR) | EEPROM |
|----------|------|------|-------|------------|--------|
| 写入速度 | 50-100ns | 10-35ns | 10-100ns | 1ms/页 | 5ms/B |
| 读取速度 | 100ns | 10-30ns | 10-50ns | 100ns | 1us/B |
| 擦写寿命 | 10的14次方 | 10的15次方 | 10的6-10次方 | 10的4-5次方 | 10的6次方 |
| 容量 | 4Kb-8Mb | 1Mb-256Mb | 实验室Gb级 | 1Mb-128Mb | 1Kb-1Mb |
| 功耗(写入) | 极低 | 极低 | 低 | 中 | 中 |
| 破坏性读出 | 是 | 否 | 否 | 否 | 否 |
| 磨损均衡 | 不需要 | 不需要 | 可能需要 | 需要 | 不需要 |
| 成熟度 | 高(量产20年+) | 中高(量产中) | 低(研发) | 高 | 高 |
| 每比特成本 | 高 | 中高 | 潜在低 | 低 | 高 |
| 辐射耐受 | 中 | 强 | 中 | 弱 | 弱 |

## 6. 商用产品与集成方案

### 6.1 FRAM产品

**TI MSP430FRxx系列(内置FRAM)**：

| 型号 | FRAM容量 | RAM | 特点 |
|------|----------|-----|------|
| MSP430FR2111 | 4KB | 1KB | 最小FRAM MCU |
| MSP430FR5994 | 256KB | 8KB | 信号处理(DSP) |
| MSP430FR6047 | 128KB | 8KB | 超声波流量计专用 |

MSP430FR系列的优势：FRAM既是程序存储器又是数据存储器，统一编址，无需区分Flash和EEPROM区域。低功耗模式下FRAM保持数据不丢失，可实现"瞬间唤醒"。

**独立SPI FRAM芯片**：

| 型号 | 厂商 | 容量 | 接口 | 频率 |
|------|------|------|------|------|
| MB85RS256A | Fujitsu/Infineon | 256Kb | SPI | 25MHz |
| MB85RS1MT | Fujitsu/Infineon | 1Mb | SPI | 25MHz |
| FM25W256 | Cypress/Infineon | 256Kb | SPI | 20MHz |
| MB85RC256V | Fujitsu/Infineon | 256Kb | I2C | 1MHz |

SPI FRAM引脚兼容对应容量的SPI Flash，可做直接替换以获得更高写入寿命。

### 6.2 MRAM产品

| 型号 | 厂商 | 容量 | 接口 | 特点 |
|------|------|------|------|------|
| MR4A16B | Everspin | 16Mb | 并行 | Toggle MRAM |
| MR5A16A | Everspin | 16Mb | 并行 | 工业级 |
| EMxxLX | Everspin | 8Mb-256Mb | DDR3 | STT-MRAM, 兼容DDR3接口 |

嵌入式MRAM：台积电(TSMC)在40nm和22nm工艺节点提供嵌入式MRAM IP，部分MCU厂商已开始集成。

### 6.3 选型建议

- 需要极低功耗 + 频繁写入：MSP430FR系列
- 已有设计需升级存储寿命：SPI FRAM直接替换SPI EEPROM/Flash
- 高可靠性/辐射环境：Everspin MRAM
- 大批量低成本：传统Flash + 磨损均衡

## 7. IoT应用场景分析

### 7.1 FRAM在IoT中的应用

**频繁写入的计数器与日志**：

传统方案中，传感器数据每秒记录一次到Flash，扇区寿命(1万次)很快耗尽。用FRAM则无需担心寿命问题：

```c
// FRAM数据记录示例(MSP430FR5994)
#pragma LOCATION = 0x4400  // FRAM区域
const uint16_t log_buffer[512];  // FRAM中分配日志缓冲区

void log_sensor_data(uint16_t value) {
    static uint16_t index = 0;
    // 直接写入FRAM, 无需擦除, 无需磨损均衡
    // 注意: 实际代码需禁用看门狗等防止写入中断
    __disable_interrupt();
    log_buffer[index] = value;
    index = (index + 1) % 512;
    __enable_interrupt();
}
```

**瞬时断电状态保存**：

FRAM写入速度快(50-100ns)，在检测到掉电信号后可在微秒内将关键状态保存到FRAM，设备重新上电后从断点恢复：

```c
// 掉电中断服务程序
#pragma vector = PORT1_VECTOR
__interrupt void power_loss_isr(void) {
    // VCC监测引脚触发, 还剩约100us的电容能量
    saved_state.pc = current_pc;
    saved_state.mode = operation_mode;
    saved_state.sensor_val = last_reading;
    // FRAM写入完成, 约200ns, 安全
    saved_state.magic = STATE_VALID;
}
```

### 7.2 MRAM在IoT中的应用

**汽车电子与工业控制**：

MRAM的辐射耐受和几乎无限的寿命使其适合汽车ECU、工业PLC等高可靠性场景。Everspin MRAM已用于汽车ADAS系统的事件记录器。

**航天与空间应用**：

MRAM抗单粒子翻转(SEU)的特性使其成为卫星和航天器存储器的理想选择，替代SRAM + 电池备份方案。

**边缘AI推理**：

STT-MRAM的读取速度接近SRAM，可作为神经网络权重存储器，掉电不丢失模型参数，实现"即时开机即推理"。

### 7.3 各技术适用场景总结

| 场景 | 推荐技术 | 原因 |
|------|----------|------|
| 传感器频繁日志 | FRAM | 无限寿命, 无需磨损均衡 |
| 断电状态保存 | FRAM | 写入极快, 纳秒级 |
| 汽车事件记录 | MRAM | 辐射耐受, 高可靠 |
| 航天存储 | MRAM | 抗SEU, 无限寿命 |
| 低成本大批量 | Flash | 成熟, 便宜 |
| 小量配置参数 | EEPROM | 字节级, 简单 |

## 8. 新型NVM的选择策略

### 8.1 评估维度

选择新型NVM时，按以下优先级评估：

1. **写入频率**：是否需要每秒多次写入？是 -> FRAM/MRAM
2. **数据量**：是否超过8Mb？是 -> MRAM或传统Flash
3. **环境要求**：有无辐射/极端温度？有 -> MRAM
4. **功耗预算**：是否uA级待机？是 -> FRAM(MSP430FR)
5. **成本敏感度**：BOM成本是否要求极低？是 -> 传统Flash

### 8.2 替换路径

已有设计中替换传统存储的路径：

- **替换外部I2C EEPROM** -> I2C FRAM(MB85RC系列)，引脚兼容，代码几乎不变
- **替换外部SPI Flash** -> SPI FRAM(MB85RS系列)，引脚兼容，去掉擦除步骤
- **替换MCU内置Flash配置区** -> 换用MSP430FR系列MCU，FRAM统一编址
- **替换电池备份SRAM** -> MRAM，无需电池，可靠性更高

## 9. 未来展望

### 9.1 通用存储器(Universal Memory)概念

理想中的通用存储器应同时具备：SRAM的速度、DRAM的密度、Flash的非易失性。FRAM和MRAM是最接近这一目标的候选者，但各有短板：

- FRAM：密度难以提升(3D堆叠进展缓慢)
- MRAM：写入电流虽已降低但仍需优化，密度尚不及DRAM

### 9.2 嵌入式MRAM的工艺进展

TSMC已在22ULP工艺提供嵌入式MRAM(eMRAM)IP，三星也在14nm/8nm工艺实现eMRAM。趋势：

- eMRAM逐步替代MCU中的嵌入式Flash作为代码存储
- 先进工艺节点(5nm及以下)中Flash难以缩微，eMRAM成为自然替代
- 预计2028年前后eMRAM将在主流MCU中普及

### 9.3 对IoT开发的影响

新型NVM的普及将改变IoT软件架构：

- **消除磨损均衡层**：应用代码直接写入存储器，无需FTL/磨损均衡
- **简化掉电处理**：无需复杂的脏数据管理，断电即安全
- **统一存储器模型**：FRAM/MRAM可同时存代码和数据，类似RAM的编程模型
- **降低功耗**：无需Flash擦写时的高电压电荷泵，待机功耗更低

## 总结

FRAM和MRAM突破了传统NVM"写入慢、寿命有限"的根本瓶颈，为IoT存储带来了新的可能性：

1. **FRAM**利用铁电极化实现纳秒级写入和10的14次方次寿命，无需磨损均衡，适合频繁写入和断电保存场景
2. **MRAM**利用磁隧道结实现近SRAM速度和几乎无限寿命，辐射耐受特性适合汽车和航天
3. **ReRAM**密度潜力大但成熟度低，是未来值得关注的候选
4. 新型NVM的**引脚兼容性**使现有设计可以低成本升级——SPI FRAM直接替换SPI EEPROM/Flash
5. 嵌入式MRAM在先进工艺节点替代嵌入式Flash的趋势已明确，将逐步改变MCU存储架构

当前阶段，FRAM已成熟可用，MRAM正在规模化，ReRAM仍在研发。选型时以"写入频率"和"寿命需求"为第一判断依据，再在成本和性能间取平衡。

## 参考文献

1. Texas Instruments. *MSP430FR4xx and MSP430FR2xx Family User's Guide* (SLAU445), 2021.
2. Everspin Technologies. *MRAM Technology and Products Overview*, 2023.
3. Fujitsu Semiconductor. *MB85RS256A SPI FRAM Data Sheet*, Rev. 3.0, 2022.
4. S. Yu and P. Y. Chen, *Emerging Memory Technologies: ReRAM, STT-MRAM, and PCM*, in Proc. IEEE International Electron Devices Meeting (IEDM), 2020.
5. T. Endoh et al., *STT-MRAM Technology and Its Application to IoT Edge Devices*, in IEEE Journal of the Electron Devices Society, vol. 10, pp. 524-531, 2022.
