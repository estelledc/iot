---
schema_version: '1.0'
id: eeprom-vs-flash-data-storage
title: EEPROM与Flash在IoT配置存储中的对比
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# EEPROM与Flash在IoT配置存储中的对比
> **难度**：🟢 初级 | **领域**：数据存储基础 | **阅读时间**：约 18 分钟

## 引言

想象你有一个保险箱和一个仓库。保险箱很小但每个格子都能单独换东西，仓库很大但每次必须清空一整面墙才能重新摆放。保险箱就是EEPROM——容量小但可以逐字节擦写；仓库就是Flash——容量大但必须按扇区擦除再写入。在IoT设备里，配置参数像身份证一样零碎又重要，而固件和数据日志像货物一样大批量存储，选对存储类型直接影响设备寿命和可靠性。

本文系统对比EEPROM与Flash两种非易失存储技术在IoT场景中的特性、用法和选型策略。

## 1. EEPROM特性详解

### 1.1 基本工作原理

EEPROM(Electrically Erasable Programmable Read-Only Memory)的存储单元由浮栅晶体管构成，利用隧道效应(Fowler-Nordheim隧穿)实现电擦除和编程。关键特性：每个存储单元可以**独立擦除和写入**，无需影响其他字节。

核心参数：

| 参数 | 典型值 |
|------|--------|
| 擦除粒度 | 单字节 |
| 写入粒度 | 单字节 |
| 容量范围 | 1KB - 1MB |
| 擦写寿命 | 100万次(1M cycles) |
| 写入速度 | 约5ms/字节 |
| 读取速度 | 约1us/字节 |
| 保持时间 | 100年(典型) |
| 工作电压 | 1.8V - 5.5V |

### 1.2 按字节操作的意义

EEPROM最独特的优势是**字节级擦写粒度**。修改一个配置参数只需写入1-2字节，不需要擦除整块区域。这意味着：

- 写入开销极小——改一个字只改一个字
- 无需缓冲区——不需要先把整页数据读出来再写回去
- 磨损分散——每次写入只影响目标字节的寿命计数

### 1.3 写入时序与页写入

虽然EEPROM支持字节写入，但实际芯片通常提供**页写入(Page Write)**功能来提高效率。以AT24C系列为例：

```
单字节写入流程:
START -> 设备地址+W -> ACK -> 字节地址 -> ACK -> 数据 -> ACK -> STOP
                                                    等待tWR(约5ms)

页写入流程(以AT24C256, 64字节页为例):
START -> 设备地址+W -> ACK -> 起始地址 -> ACK -> 数据0 -> ACK
-> 数据1 -> ACK -> ... -> 数据63 -> ACK -> STOP
                                     等待tWR(约5ms)
```

注意页写入的地址回卷：写入数据超过页边界时，地址会在页内回卷，覆盖已写数据，导致数据损坏。

## 2. Flash特性详解

### 2.1 基本工作原理

Flash存储器同样基于浮栅晶体管，但结构更紧凑——一个浮栅晶体管存储1位(NOR Flash)或多位(NAND Flash)。关键区别：Flash必须以**扇区(Sector)**或**块(Block)**为单位擦除，然后以**页(Page)**为单位写入。

```
Flash存储层次:
+-------------------+
| Block (64KB-256KB)|
|  +--------------+ |
|  | Sector (4KB) | |
|  |  +---------+ | |
|  |  | Page    | | |
|  |  | (256B)  | | |
|  |  +---------+ | |
|  +--------------+ |
+-------------------+
```

### 2.2 核心参数

| 参数 | NOR Flash | NAND Flash |
|------|-----------|------------|
| 擦除粒度 | 扇区(4KB-64KB) | 块(128KB-512KB) |
| 写入粒度 | 页/字节 | 页(2KB-8KB) |
| 容量范围 | 1MB-128MB | 128MB-数TB |
| 擦写寿命 | 1万-10万次 | 1万-10万次 |
| 读取速度 | 约100ns | 约25us(随机) |
| 写入速度 | 约1ms/页 | 约200us/页 |
| 随机访问 | 支持(XIP) | 不支持 |
| 位翻转 | 极少 | 需ECC纠正 |

### 2.3 擦除-再写入的代价

Flash的扇区擦除带来重大影响：

1. **修改1字节的代价**：必须先读出整个扇区数据到RAM缓冲区，擦除扇区，再写回修改后的全部数据。一个4KB扇区只为改1字节就要搬运4KB数据。
2. **磨损集中**：频繁更新的数据所在的扇区磨损远快于其他扇区。
3. **写放大**：逻辑上写1字节，物理上擦除+写入4KB甚至更多。

## 3. EEPROM与Flash全面对比

| 对比维度 | EEPROM | Flash(NOR) |
|----------|--------|------------|
| 擦写粒度 | 字节级 | 扇区擦除 + 页写入 |
| 擦写寿命 | 100万次 | 1万-10万次 |
| 容量 | 1KB-1MB | 1MB-128MB |
| 读取速度 | 慢(约1us/B) | 快(约100ns) |
| 写入速度 | 慢(约5ms/B) | 快(批量写入时) |
| 每位成本 | 高 | 低 |
| 功耗 | 低(小容量) | 中等 |
| 接口 | I2C/SPI | SPI/并行 |
| 随机访问 | 字节寻址 | 字节寻址(NOR) |
| 原地更新 | 支持 | 不支持(需擦除) |
| 适用场景 | 配置/校准数据 | 固件/数据日志 |

一句话总结：EEPROM是"改一个字换一个字"的精细存储，Flash是"清空一面墙再刷一面"的批量存储。

## 4. IoT中的EEPROM应用场景

### 4.1 设备配置参数

IoT设备需要保存网络配置(APN、代理地址)、采样间隔、报警阈值等参数。这些数据量小(通常<1KB)但需要频繁修改。

```c
// 设备配置结构体示例
typedef struct {
    uint16_t magic;         // 魔数, 用于校验有效性
    uint8_t  sampling_rate;  // 采样间隔(秒)
    uint8_t  report_mode;    // 上报模式
    uint32_t apn_offset;     // APN字符串在EEPROM中的偏移
    uint8_t  checksum;       // 校验和
} device_config_t;          // 总计8字节

// 读取配置
int config_read(device_config_t *cfg) {
    return eeprom_read(CONFIG_BASE_ADDR, (uint8_t*)cfg, sizeof(*cfg));
}

// 写入配置(只改这几个字节)
int config_write(const device_config_t *cfg) {
    return eeprom_write(CONFIG_BASE_ADDR, (uint8_t*)cfg, sizeof(*cfg));
}
```

### 4.2 传感器校准数据

出厂校准系数(偏移、增益)一旦写入很少修改，但修改时不能丢失旧值。EEPROM的字节级写入支持"先写新值再擦旧值"的原子更新策略。

### 4.3 设备序列号与唯一ID

出厂时写入一次，之后只读。用EEPROM存储可确保断电不丢失，且无需占用Flash的扇区空间。

### 4.4 小型计数器

累计运行时间、重启次数等计数器每次加1，若用Flash则每次需擦除整个扇区，严重浪费寿命。EEPROM的100万次擦写寿命在每秒1次的频率下可用约11天，需要更频繁时考虑RAM缓存+定期刷入策略。

### 4.5 网络凭据

WiFi SSID/密码、LoRa DevEUI/AppKey等。修改频率低但修改时不能出错，EEPROM的字节级写入可配合"双区备份"确保安全。

## 5. IoT中的Flash应用场景

### 5.1 固件存储

固件通常几十KB到几MB，远超EEPROM容量。NOR Flash支持XIP(eXecute In Place)，MCU可直接从Flash取指令执行，无需搬运到RAM。

### 5.2 数据日志

传感器采集数据持续追加写入，利用Flash的页写入顺序追加，写满一个扇区后再擦除下一个扇区循环使用(环形缓冲)。

### 5.3 文件系统

在较大容量Flash上运行LittleFS、SPIFFS等嵌入式文件系统，为应用提供文件级接口。

## 6. 内部EEPROM与外部EEPROM

### 6.1 MCU内置EEPROM

部分MCU(如AVR ATmega系列、PIC系列)内置EEPROM，容量通常为256B-4KB。优势是无需外部器件，劣势是容量有限且MCU选择受限。

### 6.2 外部EEPROM芯片

通过I2C或SPI连接的独立EEPROM芯片，常见型号：

| 型号 | 接口 | 容量 | 页大小 | 特点 |
|------|------|------|--------|------|
| AT24C02 | I2C | 2Kb(256B) | 8B | 最小容量, 便宜 |
| AT24C256 | I2C | 256Kb(32KB) | 64B | 常用中等容量 |
| AT25LC512 | SPI | 512Kb(64KB) | 128B | SPI速度快 |
| 93LC86 | Microwire | 16Kb(2KB) | 16B | 引脚少(3线) |

I2C EEPROM地址引脚配置(A0/A1/A2)允许同一总线上挂载最多8片同型号芯片：

```
地址字节: 1 0 1 0 A2 A1 A0 R/W
         |---固定---| |---可配---|
```

### 6.3 选型考虑

- 容量需求 < 4KB：AT24C32/64即可
- 需要快速写入：选SPI接口(25LC系列)
- 多片并联：I2C地址引脚版本更灵活
- 低功耗场景：关注待机电流(通常1-5uA)

## 7. Flash模拟EEPROM

### 7.1 为什么需要Flash模拟EEPROM

很多现代MCU(如STM32)没有内置EEPROM，只有Flash。但IoT应用需要EEPROM的字节级更新能力。解决方案是用Flash的某些扇区模拟EEPROM的行为。

### 7.2 STM32 EEPROM Emulation原理

ST官方应用笔记AN2594描述的方案使用两个Flash页交替使用：

```
页面状态:
+-------------------+     +-------------------+
| Page 0 (1KB)     |     | Page 1 (1KB)      |
| 状态: ACTIVE      |     | 状态: ERASED       |
+-------------------+     +-------------------+

数据存储格式(键值对):
| 虚拟地址(16bit) | 数据值(16bit) |
| 0x0001          | 0x1234         |
| 0x0002          | 0x5678         |
| 0x0001          | 0xABCD  <- 新值覆盖旧值 |
```

关键机制：

1. **追加写入**：新值直接追加到活跃页末尾，旧值不擦除
2. **有效判定**：同一虚拟地址的最后一次写入为有效值
3. **页交换**：活跃页写满时，将有效数据搬移到空页，然后擦除旧页

### 7.3 磨损均衡

简单的Flash模拟方案中，频繁更新的变量会导致活跃页很快写满，触发页交换。优化策略：

- **合并写入**：多个变量修改后一次性追加
- **页大小选择**：使用较大的Flash页降低交换频率
- **多页轮转**：使用3个以上页循环，进一步分散磨损

### 7.4 代码示例

```c
// 简化版Flash EEPROM模拟核心逻辑
#define PAGE_SIZE    1024
#define PAGE0_BASE   0x08080000
#define PAGE1_BASE   0x08080400
#define VAR_MAX     32

typedef struct {
    uint16_t virt_addr;
    uint16_t data;
} eeprom_entry_t;

// 读取变量: 从活跃页末尾向前扫描, 找最新值
uint16_t ee_read(uint16_t virt_addr) {
    uint32_t page_base = get_active_page();
    int entries = PAGE_SIZE / sizeof(eeprom_entry_t);
    for (int i = entries - 1; i >= 0; i--) {
        eeprom_entry_t entry;
        memcpy(&entry, (void*)(page_base + i * sizeof(entry)), sizeof(entry));
        if (entry.virt_addr == virt_addr) {
            return entry.data;
        }
    }
    return 0xFFFF; // 未找到
}

// 写入变量: 追加到活跃页
int ee_write(uint16_t virt_addr, uint16_t data) {
    uint32_t write_pos = find_next_free_slot();
    if (write_pos == 0) {
        // 页满, 触发页交换
        return page_swap_and_rewrite(virt_addr, data);
    }
    eeprom_entry_t entry = {virt_addr, data};
    return flash_write(write_pos, &entry, sizeof(entry));
}
```

## 8. I2C EEPROM读写实战

### 8.1 基本读写流程

```c
// I2C EEPROM(AT24C256)单字节写入
int at24c_write_byte(I2C_HandleTypeDef *hi2c, uint16_t addr, uint8_t data) {
    uint8_t buf[3];
    buf[0] = (addr >> 8) & 0xFF;   // 地址高字节
    buf[1] = addr & 0xFF;           // 地址低字节
    buf[2] = data;                  // 数据
    HAL_StatusTypeDef status = HAL_I2C_Master_Transmit(
        hi2c, AT24C_ADDR << 1, buf, 3, 100);
    HAL_Delay(5);  // 等待写入完成(tWR)
    return (status == HAL_OK) ? 0 : -1;
}

// I2C EEPROM(AT24C256)单字节读取
int at24c_read_byte(I2C_HandleTypeDef *hi2c, uint16_t addr, uint8_t *data) {
    uint8_t addr_buf[2];
    addr_buf[0] = (addr >> 8) & 0xFF;
    addr_buf[1] = addr & 0xFF;
    // 先写地址
    HAL_I2C_Master_Transmit(hi2c, AT24C_ADDR << 1, addr_buf, 2, 100);
    // 再读数据
    HAL_StatusTypeDef status = HAL_I2C_Master_Receive(
        hi2c, AT24C_ADDR << 1, data, 1, 100);
    return (status == HAL_OK) ? 0 : -1;
}
```

### 8.2 Flash扇区管理

```c
// Flash扇区擦除与写入(以STM32内部Flash为例)
int flash_sector_write(uint32_t sector_addr, const uint8_t *data, uint16_t len) {
    HAL_FLASH_Unlock();

    // 擦除扇区
    FLASH_EraseInitTypeDef erase_init;
    uint32_t sector_error;
    erase_init.TypeErase = FLASH_TYPEERASE_SECTORS;
    erase_init.Sector = get_sector_number(sector_addr);
    erase_init.NbSectors = 1;
    erase_init.VoltageRange = FLASH_VOLTAGE_RANGE_3;
    HAL_FLASHEx_Erase(&erase_init, &sector_error);

    // 逐字写入
    for (uint16_t i = 0; i < len; i += 4) {
        uint32_t word = 0xFFFFFFFF;
        memcpy(&word, data + i, (len - i >= 4) ? 4 : (len - i));
        HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,
                          sector_addr + i, word);
    }

    HAL_FLASH_Lock();
    return 0;
}
```

## 9. IoT项目选型决策指南

### 9.1 决策流程

根据以下问题选择存储方案：

1. 数据量多大？
   - < 4KB 且需字节级更新 -> EEPROM
   - > 4KB -> Flash

2. 更新频率多高？
   - 每秒多次 -> RAM缓存 + 定期刷EEPROM/Flash
   - 每分钟几次 -> EEPROM直接写入
   - 极少更新 -> Flash即可

3. 是否需要掉电保持？
   - 是 -> 必须非易失存储
   - 否 -> RAM即可

4. MCU有无内置EEPROM？
   - 有 -> 直接用
   - 无 -> Flash模拟EEPROM或外挂EEPROM

### 9.2 典型方案搭配

| 项目类型 | 存储方案 | 说明 |
|----------|----------|------|
| 传感器节点 | MCU内置Flash模拟EEPROM | 省成本, 配置参数少 |
| 智能家居 | 外挂I2C EEPROM + MCU内置Flash | 配置用EEPROM, 固件用Flash |
| 数据记录器 | SPI NOR Flash + LittleFS | 大量数据日志需文件系统 |
| 网关设备 | eMMC/SD + NOR Flash | Linux系统用eMMC, 引导用NOR Flash |

## 总结

EEPROM和Flash在IoT存储中各有定位，选择的核心在于理解"擦写粒度"和"寿命"两个关键差异：

1. **EEPROM**以字节为粒度、100万次寿命，适合配置、校准、序列号等小数据频繁修改场景
2. **Flash**以扇区为粒度、1万-10万次寿命，适合固件、数据日志等大批量顺序写入场景
3. 无内置EEPROM的MCU可用**Flash模拟EEPROM**方案，追加写入+页交换实现字节级更新
4. 外挂EEPROM通过I2C/SPI连接，提供独立于MCU的存储空间，选型时关注容量、接口和页大小
5. 实际项目中常**混合使用**：EEPROM存配置，Flash存固件和数据，各取所长

选型时的经验法则：先确认数据量和更新频率，再在成本和寿命之间取平衡点。

## 参考文献

1. STMicroelectronics. *EEPROM emulation techniques for STM32 microcontrollers* (AN2594), Application Note, 2020.
2. Microchip Technology. *AT24C256 Datasheet: 256Kb I2C Serial EEPROM*, Rev. 6, 2019.
3. Spansion/Cypress. *S25FL-K NOR Flash Data Sheet*, Infineon Technologies, 2022.
4. J. Hennessy and D. Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed., Morgan Kaufmann, 2019, ch. 1 (Memory Hierarchy).
5. NXP Semiconductors. *I2C-bus specification and user manual* (UM10204), Rev. 7.0, 2021.
