---
schema_version: '1.0'
id: eeprom-vs-flash-data-storage
title: EEPROM与Flash在IoT配置存储中的对比
layer: 1
content_type: comparison
difficulty: beginner
reading_time: 16
prerequisites:
  - nor-flash-spi-qspi-xip
  - mcu-memory-map-flash-ram
tags:
  - EEPROM
  - NOR-Flash
  - 配置存储
  - 磨损均衡
  - I2C
  - 非易失存储
  - Flash模拟EEPROM
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# EEPROM与Flash在IoT配置存储中的对比

> **难度**：🟢 初级 | **领域**：嵌入式存储 | **关键词**：EEPROM, NOR Flash, 扇区擦除, 写放大 | **阅读时间**：约 16 分钟

## 日常类比

保险箱很小，格子可单独换东西——这是电可擦除可编程只读存储器（Electrically Erasable Programmable Read-Only Memory, EEPROM）。仓库很大，但要清空一整面墙才能重摆——这是闪存（Flash）：按扇区/块擦除再按页编程。物联网（IoT）里配置像身份证（碎、常改），固件与日志像货物（大、顺序写），选错会提前磨死芯片[1][2][3]。

## 摘要

对比字节级 EEPROM 与扇区级 NOR/NAND Flash 的粒度、寿命、接口与 IoT 用法，并说明无内置 EEPROM 时的 Flash 模拟（如 STM32 AN2594 思路）。擦写次数与时序为典型量级，**以具体型号数据手册为准**[2][3]。

## 1. 机制差异

两者多基于浮栅电荷存储；差别在阵列组织与擦除粒度。EEPROM 可按字节（或小页）更新；Flash 必须先擦除较大扇区/块，再编程，导致改 1 字节也要读-改-擦-写整扇区，产生写放大与磨损集中[3][4]。

| 参数 | EEPROM（典型） | NOR Flash（典型） |
|------|----------------|-------------------|
| 擦除粒度 | 字节级 | 扇区（常数 KB 起） |
| 写入 | 字节/页 | 页编程 |
| 容量倾向 | KB～约 1 MB | MB～百 MB 级 |
| 擦写寿命倾向 | 约 10⁵～10⁶ 次/字节 | 约 10⁴～10⁵ 次/扇区 |
| 接口 | I2C / SPI | SPI / 并行；可 XIP |
| 原地小更新 | 友好 | 不友好 |

NAND 容量更大、随机读弱、需 ECC，IoT 配置场景更常用外挂 EEPROM 或片内 Flash 模拟，而非直接拿 NAND 存几十字节参数[3]。

## 2. IoT 用法分工

| 数据 | 更合适 | 原因 |
|------|--------|------|
| Wi-Fi/密钥、校准、序列号 | EEPROM 或模拟 EEPROM | 小、偶发更新 |
| 固件、XIP 代码 | NOR Flash | 容量与执行 |
| 传感器日志 | Flash + 文件系统/环形缓冲 | 顺序追加 |

I2C EEPROM（如 AT24C 系列）注意页写回卷：跨页连续写可能覆盖页首。写周期结束后才可读，需轮询 ACK 或等待 tWR[2][5]。

## 3. Flash 模拟 EEPROM

无内置 EEPROM 的微控制器（Microcontroller Unit, MCU）常用双页轮转：活跃页追加“虚拟地址 + 数据”，读时取同地址最新记录；页满则迁移有效记录到空页并擦旧页[1]。可叠加多页磨损均衡、合并写与延迟刷盘。

| 方案 | 优点 | 代价 |
|------|------|------|
| 片内 Flash 模拟 | 省器件 | 占 Flash、打断执行、寿命按扇区算 |
| 外挂 EEPROM | 真正字节更新 | BOM、总线、掉电时序 |
| 外挂 NOR + LittleFS 等 | 文件语义 | 对“几字节配置”偏重 |

## 4. 选型决策（简）

1. 数据 ≪ 数 KB 且常改 → EEPROM / 模拟。
2. 大容量固件或日志 → Flash。
3. 每秒多次计数 → RAM 聚合再低频落盘，避免磨死。
4. 安全凭据 → 考虑只写一次区、备份区与校验，而非裸写单副本。

## 5. 局限、挑战与可改进方向

### 1. 写放大与寿命误判

**局限**：把 Flash 当 EEPROM 逐字节改，扇区很快耗尽。
**改进**：追加日志结构或外挂 EEPROM；估算日写入扇区次数。

### 2. 掉电一致性

**局限**：擦写中掉电导致半新半旧配置。
**改进**：双副本 + CRC/魔数；先写新后无效旧；上电选合法副本。

### 3. 页写回卷与总线错误

**局限**：I2C 页写越界静默损坏；时钟拉伸/上拉不当导致偶发失败。
**改进**：封装按页边界切分；写后回读校验；硬件按手册上拉与长度。

### 4. 模拟 EEPROM 占用与停子

**局限**：擦除期间 MCU 可能不可取指（视架构）。
**改进**：把模拟区放到独立 bank；关键实时任务避开擦除窗或用外挂芯片。

## 6. 实践要点

1. 配置与固件分存储技术，不要混在同一热扇区。
2. 计数器类热点键必须磨损均衡或缓存。
3. 量产锁定 EEPROM/Flash 型号与页/扇区大小，避免“兼容料”时序差异。

## 参考文献

[1] STMicroelectronics, AN2594 EEPROM emulation for STM32.
[2] Microchip, AT24C256 I2C EEPROM datasheet.
[3] Infineon/Cypress, S25FL-K NOR Flash family datasheets.
[4] J. Hennessy, D. Patterson, Computer Architecture: A Quantitative Approach（存储层次）.
[5] NXP, UM10204 I2C-bus specification.
[6] JEDEC, Flash memory standard overviews（NOR/NAND 术语）.
[7] ARM mbed, LittleFS design（对照掉电安全文件存储）.
[8] Micron / Spansion NOR Flash application notes（扇区擦除与写放大）.
[9] STM32 HAL Flash programming reference manuals.
[10] Atmel/Microchip SPI EEPROM 25LC series datasheets.
[11] IEC / 工业设备数据保持与寿命评估相关应用笔记（配置存储语境）.
