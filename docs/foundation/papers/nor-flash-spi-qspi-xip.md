---
schema_version: '1.0'
id: nor-flash-spi-qspi-xip
title: NOR Flash SPI/QSPI接口与XIP执行
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
# NOR Flash SPI/QSPI接口与XIP执行
> **难度**：🟡 中级 | **领域**：存储接口技术 | **阅读时间**：约 20 分钟

## 引言

想象你的书架(NOR Flash)和书桌(RAM)的关系。书架上每本书都有明确的编号(地址)，你可以直接走到那个位置取下任何一本书(随机访问)。相比之下，NAND Flash更像一摞摞的文件夹 -- 必须从头翻到尾才能找到需要的内容。NOR Flash的这种"随机访问"特性，使得CPU可以直接从Flash中取指令执行，就像你站在书架前直接阅读，而不必先把书搬到书桌上 -- 这就是XIP(Execute-In-Place)的核心思想。

本文将系统介绍NOR Flash的接口演进、QSPI协议细节、XIP执行机制，以及在IoT系统中的实际应用。

## 1. NOR Flash基础特性

### 1.1 为什么叫NOR Flash

NOR Flash的存储单元采用NOR逻辑门结构连接：

```
NOR结构: 每个位线(Bitline)上的单元是并联的
  选中某字线(Wordline) -> 对应单元导通 -> 位线拉低
  
对比NAND结构: 单元串联
  必须整串导通才能读取 -> 只能按页顺序访问
```

NOR的并联结构带来关键优势：可以独立寻址任意单元，实现真正的随机读取。

### 1.2 NOR Flash vs NAND Flash

| 特性 | NOR Flash | NAND Flash |
|------|-----------|------------|
| 读取方式 | 随机访问，字节寻址 | 按页访问(典型2KB+) |
| 读取速度 | 快(随机访问) | 快(顺序访问) |
| 写入方式 | 按字节/字写入 | 按页写入 |
| 擦除方式 | 扇区/块擦除 | 块擦除 |
| 密度 | 低(典型1-256Mb) | 高(典型8Gb+) |
| 每位成本 | 高 | 低 |
| 可靠性 | 高(无坏块) | 低(有坏块) |
| 典型用途 | 代码存储 | 数据存储 |

### 1.3 NOR Flash在IoT中的角色

IoT设备中NOR Flash的核心角色是存储代码：

- **启动代码**：MCU从NOR Flash启动(Boot)
- **应用程序**：XIP直接执行或复制到RAM后执行
- **配置数据**：设备参数、校准数据
- **OTA固件**：存储升级固件镜像

## 2. SPI接口模式演进

### 2.1 标准SPI (1-bit)

标准SPI使用4根信号线：

| 信号 | 方向 | 功能 |
|------|------|------|
| CS# | MCU -> Flash | 片选，低有效 |
| SCLK | MCU -> Flash | 串行时钟 |
| MOSI(DI) | MCU -> Flash | 主出从入(数据输入) |
| MISO(DO) | Flash -> MCU | 主入从出(数据输出) |

标准SPI读取时序：

```
CS#   |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|
SCLK  | |‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|
MOSI  |<-- 指令(8bit) -->|<-- 地址(24bit) -->|<dummy>|<-- 数据 -->|
       03h              A23-A0               数据输出
```

标准SPI每个时钟周期传输1位数据，读取吞吐量 = SCLK频率 / 8。

### 2.2 Dual SPI (2-bit)

Dual SPI复用MOSI和MISO为双向数据线：

- **指令阶段**：1-bit(仅MOSI)
- **地址阶段**：1-bit或2-bit
- **数据阶段**：2-bit(MOSI+MISO同时传输)

吞吐量翻倍：读取速度 = SCLK频率 / 4。

### 2.3 Quad SPI (4-bit)

Quad SPI增加两根数据线，使用4根数据线并行传输：

| 信号 | 方向 | 功能 |
|------|------|------|
| CS# | MCU -> Flash | 片选 |
| SCLK | MCU -> Flash | 时钟 |
| DI(IO0) | 双向 | 数据线0 |
| DO(IO1) | 双向 | 数据线1 |
| WP#(IO2) | 双向 | 数据线2(复用写保护) |
| HOLD#(IO3) | 双向 | 数据线3(复用保持) |

Quad SPI读取时序：

```
CS#   |‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|
SCLK  | |‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|‾|_|
IO0-3 |<-- 指令(2clk) -->|<-- 地址(6clk) -->|<dum>|<-- 数据(每clk 4bit) -->|
       6Bh                A23-A0                  D7-D0每周期
```

Quad SPI每个时钟周期传输4位数据，吞吐量 = SCLK频率 / 2。

### 2.4 QPI模式 (4-bit全四线)

QPI(Quad Peripheral Interface)将指令阶段也改为4线传输：

| 阶段 | SPI | Dual SPI | Quad SPI | QPI |
|------|-----|----------|----------|-----|
| 指令 | 1-bit | 1-bit | 1-bit | 4-bit |
| 地址 | 1-bit | 2-bit | 4-bit | 4-bit |
| Dummy | 有 | 有 | 有 | 有 |
| 数据 | 1-bit | 2-bit | 4-bit | 4-bit |

QPI模式切换：先发送38h指令进入QPI，发送FFh退出。

### 2.5 读取性能对比

| 模式 | 时钟 | 数据位宽 | 理论吞吐量 | 典型芯片 |
|------|------|----------|-----------|----------|
| SPI | 50MHz | 1-bit | 6.25MB/s | 所有NOR Flash |
| Dual SPI | 80MHz | 2-bit | 20MB/s | W25Q20EW |
| Quad SPI | 80MHz | 4-bit | 40MB/s | W25Q32 |
| Quad SPI | 133MHz | 4-bit | 66.5MB/s | IS25LP064 |
| QPI | 133MHz | 4-bit | 66.5MB/s | GD25Q128 |

注意：Quad SPI和QPI的理论峰值相同，但QPI的指令阶段更快(2个时钟 vs 8个时钟)，对短读取更友好。

## 3. QSPI命令协议详解

### 3.1 常用读取命令

| 命令码 | 名称 | 地址位宽 | Dummy周期 | 数据位宽 | 最高频率 |
|--------|------|----------|-----------|----------|----------|
| 03h | Read | 24-bit | 0 | 1-bit | 50MHz |
| 0Bh | Fast Read | 24-bit | 1(8clk) | 1-bit | 104MHz |
| 3Bh | Dual Read | 24-bit | 1(8clk) | 2-bit | 104MHz |
| 6Bh | Quad Read | 24-bit | 2(8clk) | 4-bit | 104MHz |
| BBh | Dual IO Read | 24-bit | 0 | 2-bit | 104MHz |
| EBh | Quad IO Read | 24-bit | 2(6clk) | 4-bit | 133MHz |
| 0Ch | Fast Read 4Byte | 32-bit | 1(8clk) | 1-bit | 104MHz |
| 6Ch | Quad Read 4Byte | 32-bit | 2(8clk) | 4-bit | 104MHz |

### 3.2 Dummy周期的作用

Dummy周期(Dummy Cycles)是地址发送完成和数据输出开始之间的空闲时钟周期：

```
为什么需要Dummy周期?

1. Flash内部解码时间: 地址解码和存储阵列访问需要时间
2. 高速读取更长的Dummy: 频率越高，Flash需要越多的准备时间
3. 可配置Dummy: 部分芯片允许通过寄存器调整Dummy长度

Dummy周期与频率关系(示例):
- 54MHz:  2个Dummy时钟(Quad)
- 84MHz:  4个Dummy时钟(Quad)  
- 104MHz: 4-6个Dummy时钟(Quad)
- 133MHz: 6-8个Dummy时钟(Quad)
```

### 3.3 写使能与命令

写入操作前必须发送写使能命令：

| 命令码 | 名称 | 功能 |
|--------|------|------|
| 06h | Write Enable | 设置WEL位，允许写入 |
| 04h | Write Disable | 清除WEL位，禁止写入 |
| 02h | Page Program | 页编程(最多256字节) |
| 32h | Quad Page Program | 四线页编程 |
| 20h | Sector Erase | 扇区擦除(4KB) |
| D8h | Block Erase | 块擦除(64KB) |
| C7h | Chip Erase | 全片擦除 |

## 4. XIP (Execute-In-Place) 机制

### 4.1 XIP概念

XIP允许CPU直接从外部Flash取指令执行，无需先复制到RAM：

```
传统方式(非XIP):
Flash -> (DMA/软件拷贝) -> RAM -> CPU取指令

XIP方式:
Flash -> (QSPI控制器) -> CPU取指令
```

XIP的优势：
- **节省RAM**：不需要将全部代码复制到RAM
- **快速启动**：无需等待代码搬运，上电即可执行
- **简化软件**：无需管理代码加载过程

### 4.2 XIP的硬件实现

XIP需要MCU内部QSPI控制器的特殊支持：

```
MCU XIP架构:

+-------+     +-----------+     +-----------+     +----------+
| CPU   |---->| AHB总线    |---->| QSPI控制器 |---->| QSPI     |----> NOR Flash
|       |<----| (内存映射) |<----| (XIP模式)  |<----| 接口     |
+-------+     +-----------+     +-----------+     +----------+
                                    |
                                +-------+
                                | Cache |  <-- 可选缓存
                                +-------+
                                    |
                                +-------+
                                | Prefetch| <-- 预取缓冲
                                +-------+
```

XIP工作流程：

1. CPU发起内存映射地址访问(如0x90000000)
2. QSPI控制器检测到XIP区域访问
3. 自动生成QSPI读取命令(6Bh/EBh)
4. 从Flash获取数据返回给CPU
5. 同时预取后续地址的数据到Prefetch Buffer

### 4.3 Cache在XIP中的作用

XIP性能严重依赖缓存命中率：

| 缓存大小 | 缓存命中率(典型) | 有效带宽 | 适合场景 |
|----------|-----------------|----------|----------|
| 无缓存 | 约0% | 原始QSPI带宽 | 简单控制逻辑 |
| 4KB | 约60-70% | 约2-3x | 小型固件 |
| 16KB | 约80-90% | 约5-10x | 中型固件 |
| 64KB | 约90-95% | 约10-20x | 大型固件 |

缓存带来的挑战：

- **数据一致性**：Flash写入后需手动失效缓存
- **实时性**：缓存未命中时延迟不确定
- **中断安全**：中断向量表在XIP区域时需保证缓存命中

### 4.4 预取缓冲(Prefetch Buffer)

预取缓冲利用Flash的顺序读取特性：

```
CPU取指令地址: 0x90001000 -> 命中缓存
CPU取指令地址: 0x90001004 -> 命中缓存(预取)
CPU取指令地址: 0x90001008 -> 命中缓存(预取)
...
缓存未命中 -> 触发新的QSPI读取(突发读取多个字)
```

## 5. IoT常用NOR Flash芯片

### 5.1 主流芯片对比

| 芯片 | 容量 | 最高频率 | 接口 | 封装 | 特点 |
|------|------|----------|------|------|------|
| W25Q16JV | 16Mb | 133MHz | SPI/Dual/Quad | SOIC8/WSON8 | 通用首选 |
| W25Q32JV | 32Mb | 133MHz | SPI/Dual/Quad | SOIC8 | 高性价比 |
| W25Q64JV | 64Mb | 133MHz | SPI/Dual/Quad | SOIC8 | 大容量 |
| W25Q128JV | 128Mb | 133MHz | SPI/Dual/Quad | SOIC16 | 超大容量 |
| GD25Q16C | 16Mb | 120MHz | SPI/Dual/Quad | SOIC8 | 国产替代 |
| GD25Q32C | 32Mb | 120MHz | SPI/Dual/Quad | SOIC8 | 国产替代 |
| IS25LP016D | 16Mb | 133MHz | SPI/Dual/Quad | SOIC8 | 低功耗 |
| IS25LP064A | 64Mb | 133MHz | SPI/Dual/Quad | SOIC8 | 低功耗 |
| MX25L1606E | 16Mb | 104MHz | SPI/Dual/Quad | SOIC8 | 成熟稳定 |
| XT25F16B | 16Mb | 120MHz | SPI/Dual/Quad | SOP8 | 国产低成本 |

### 5.2 容量与速度选择建议

| IoT场景 | 推荐容量 | 推荐速度 | 理由 |
|---------|----------|----------|------|
| 简单传感器节点 | 8-16Mb | 80MHz Quad | 代码量小，成本优先 |
| WiFi/BLE设备 | 16-32Mb | 104MHz Quad | 网络栈代码量大 |
| Linux最小系统 | 64-128Mb | 133MHz Quad | 需要XIP执行Linux内核 |
| OTA双区设计 | 64Mb+ | 133MHz Quad | 双分区固件更新 |

## 6. 写入与擦除操作

### 6.1 页编程(Page Program)

NOR Flash写入的最小单位是页(通常256字节)：

```
页编程流程:
1. 发送Write Enable(06h)
2. 发送Page Program(02h) + 24位地址 + 数据
3. 等待写入完成(轮询Status Register Bit0)
4. 检查写入结果

注意:
- 每页最多写入256字节
- 只能从1写到0(不能从0写到1，需先擦除)
- 跨页写入需分多次操作
- 写入时间: 典型0.7ms/页, 最大3ms/页
```

### 6.2 擦除操作

擦除将存储单元从0恢复为1，最小擦除单位是扇区：

| 擦除类型 | 大小 | 命令 | 典型时间 | 最大时间 |
|----------|------|------|----------|----------|
| 扇区擦除 | 4KB | 20h | 50ms | 400ms |
| 块擦除 | 32KB | 52h | 150ms | 2s |
| 块擦除 | 64KB | D8h | 200ms | 2s |
| 全片擦除 | 全片 | C7h | 10s | 60s |

### 6.3 状态寄存器

状态寄存器用于监控操作进度和配置芯片：

| 位 | 名称 | 功能 |
|----|------|------|
| Bit0 | BUSY | 1=正在写入/擦除 |
| Bit1 | WEL | 写使能锁存位 |
| Bit2 | BP0 | 块保护位0 |
| Bit3 | BP1 | 块保护位1 |
| Bit4 | BP2 | 块保护位2 |
| Bit5 | BP3 | 块保护位3 |
| Bit6 | QE | Quad使能位(关键!) |
| Bit7 | SRP0 | 状态寄存器保护 |

**QE位**是使用Quad SPI的关键 -- 必须在首次使用前设置QE=1，否则IO2/IO3不作为数据线功能。

### 6.4 保护机制

NOR Flash提供多级保护防止意外写入：

- **块保护(BP位)**：保护指定地址范围不被写入/擦除
- **状态寄存器保护(SRP位)**：保护状态寄存器不被修改
- **写保护引脚(WP#)**：硬件写保护(Quad模式时复用为IO2)
- **一次性可编程(OTP)保护**：永久锁定，不可逆

## 7. OTP区域

### 7.1 OTP区域特点

OTP(One-Time Programmable)区域是一次性编程区域：

| 特性 | 说明 |
|------|------|
| 大小 | 典型256字节(含64字节锁定区) |
| 编程 | 只能从1写到0，不可擦除 |
| 锁定 | 锁定后永久不可修改 |
| 用途 | 设备序列号、MAC地址、加密密钥 |

### 7.2 IoT中的OTP使用场景

```
OTP区域布局示例(256字节):
[0x00-0x1F]  设备唯一ID(32字节) - 出厂写入
[0x20-0x3F]  MAC地址(32字节)    - 出厂写入
[0x40-0x7F]  AES密钥(64字节)    - 安全初始化时写入
[0x80-0xBF]  校准数据(64字节)   - 产线校准后写入
[0xC0-0xDF]  保留(32字节)
[0xE0-0xFF]  锁定区(32字节)     - 锁定后永久不可修改
```

## 8. 实际应用：MCU从QSPI Flash启动

### 8.1 STM32 QSPI XIP启动

STM32L4/H7系列支持从QSPI Flash启动：

```
STM32 QSPI XIP启动流程:
1. 系统复位
2. 内部Bootloader检测BOOT引脚配置
3. 配置QSPI控制器(默认SPI模式，命令03h)
4. 从0x90000000映射的Flash读取启动代码
5. 软件初始化后切换到QSPI高速模式
6. 使能QSPI Cache
7. 正常XIP执行

启动时间优化:
- 默认SPI模式启动: 约50ms(1-bit读取)
- 切换到QSPI后: XIP带宽提升4倍
```

### 8.2 ESP32 Flash映射

ESP32内部集成了SPI Flash控制器，支持XIP：

```
ESP32 Flash映射布局:
0x3F400000 - 0x3F7FFFFF: 数据映射区(只读)
0x42000000 - 0x43FFFFFF: 指令映射区(XIP)
0x3C000000 - 0x3CFFFFFF: 外部Flash映射(4MB窗口)

ESP32的Flash特点:
- 内置4MB Flash(部分型号)
- 支持Cache加速XIP
- WiFi协议栈也在Flash中XIP执行
```

### 8.3 XIP与RAM执行的混合策略

实际项目中常混合使用XIP和RAM执行：

| 代码类型 | 执行方式 | 理由 |
|----------|----------|------|
| 初始化代码 | RAM执行 | 需要配置QSPI控制器后才能XIP |
| 中断处理 | RAM执行 | 确保确定性延迟 |
| 主应用程序 | XIP执行 | 代码量大，节省RAM |
| 高频算法 | RAM执行 | 缓存命中率高时也拷贝到RAM |
| OTA写入 | Flash直接操作 | 写入时XIP必须暂停 |

```c
// 将关键函数放入RAM执行的示例(STM32)
// 在链接脚本中定义RAM执行区域

void __attribute__((section(".ram_code"))) critical_isr(void) {
    // 此函数从RAM执行，不受QSPI延迟影响
    // 适合中断服务例程
}

void __attribute__((section(".xip_code"))) main_loop(void) {
    // 此函数从Flash XIP执行，节省RAM
    // 适合非实时主循环
}
```

## 9. 可靠性考量

### 9.1 擦写寿命

NOR Flash的擦写寿命(P/E Cycles)：

| Flash类型 | P/E寿命 | 数据保持 | 典型用途 |
|-----------|---------|----------|----------|
| 标准NOR | 100K次 | 20年 | 代码存储 |
| 高耐久NOR | 100K+次 | 20年 | 频繁更新的配置区 |

对于IoT设备，100K次P/E是否足够？

```
典型OTA更新场景:
- 每周1次固件更新
- 每次更新擦写约4MB(全片)
- 100K / 52周 = 约1923年

配置数据场景:
- 每天10次参数更新
- 每次擦写1个扇区(4KB)
- 100K / 3650次/年 = 约27年
```

100K次对大多数IoT场景足够，但频繁写入的日志区域需注意。

### 9.2 数据保持

数据保持时间与温度和P/E次数相关：

```
数据保持时间影响因素:
1. 温度: 高温加速电荷流失
   - 25度: 标称20年
   - 85度: 约5年
   - 125度: 约1年

2. P/E次数: 擦写越多，保持时间越短
   - 0次P/E: 20年
   - 100K次P/E: 约5-10年

3. 读取干扰: 频繁读取同一块区域可能影响数据
```

### 9.3 环境可靠性建议

| 措施 | 效果 | 实现方式 |
|------|------|----------|
| CRC校验 | 检测数据损坏 | 启动时校验关键区域 |
| 双区OTA | 防止更新失败变砖 | A/B分区互为备份 |
| 磨损均衡 | 均匀分布写入 | 软件实现简单轮换 |
| 定期刷新 | 防止数据丢失 | 读取后回写关键数据 |
| 看门狗 | 检测XIP异常 | Cache未命中导致超时 |

## 总结

NOR Flash是IoT设备代码存储的核心，其接口技术的演进带来显著性能提升：

1. **接口演进**：从1-bit SPI到4-bit QSPI，读取带宽提升4倍，最高达66.5MB/s
2. **XIP机制**：让CPU直接从Flash取指令，节省RAM、加速启动，但依赖Cache保证性能
3. **芯片选型**：W25Q/GD25Q/IS25LP系列覆盖从8Mb到128Mb的容量需求
4. **QE位配置**：使用Quad SPI前必须设置QE位，这是初学者常忽略的关键步骤
5. **可靠性**：100K次P/E寿命对IoT代码存储足够，但需注意高温环境的数据保持

理解NOR Flash的接口和XIP机制，是设计高性能IoT启动系统的关键基础。

## 参考文献

1. Winbond, "W25Q32JV SPI Flash Datasheet", 2023
2. JEDEC, "JESD216B - Serial Flash Discoverable Parameters", 2019
3. STMicroelectronics, "AN4729 - Quad-SPI memory interface on STM32 microcontrollers", 2020
4. GigaDevice, "GD25Q32C Datasheet", 2022
5. ISSI, "IS25LP064A Datasheet", 2021
