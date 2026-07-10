---
schema_version: '1.0'
id: sd-emmc-storage-embedded
title: SD/eMMC嵌入式存储接口与文件系统选择
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
# SD/eMMC嵌入式存储接口与文件系统选择
> **难度**：🟡 中级 | **领域**：嵌入式存储系统 | **阅读时间**：约 20 分钟

## 引言

想象你需要一个大仓库来存放货物流水记录。你可以租一个移动板房(SD卡)——插上就用，随时搬走，但地基不稳、容易晃；也可以建一个固定仓库(eMMC)——焊死在厂房里，地基牢固，但一旦建成就不容易换。在IoT设备中，SD卡和eMMC就是这两种"大容量仓库"，它们都能提供GB级存储空间，但接口、可靠性、使用方式截然不同。本文从硬件接口到文件系统，系统梳理嵌入式存储的选型与实现。

## 1. SD卡接口

### 1.1 SD卡物理接口

SD卡支持两种通信模式：

**SPI模式**：4线制，MCU普遍支持

```
信号线:
  CS   (片选, 低有效)
  CLK  (时钟, MCU输出)
  MOSI (主机出从机入)
  MISO (主机入从机出)

优点: 几乎所有MCU都有SPI外设, 驱动简单
缺点: 速度慢(默认25MHz), 仅1位传输
```

**SD模式**：由SD主机控制器驱动，支持更高速率

```
SD 1-bit模式: CMD, CLK, DAT0          (3线)
SD 4-bit模式: CMD, CLK, DAT0-DAT3     (6线)
SD UHS-I模式: CMD, CLK, DAT0-DAT3     (6线, 1.8V信令)

优点: 4位并行传输, 速度快
缺点: 需要SDIO外设, 驱动复杂
```

### 1.2 SD模式速率等级

| 模式 | 时钟 | 总线宽度 | 理论带宽 |
|------|------|----------|----------|
| Default Speed | 25MHz | 1-bit | 12.5MB/s |
| High Speed | 50MHz | 1-bit | 25MB/s |
| High Speed | 50MHz | 4-bit | 50MB/s |
| UHS-I SDR50 | 50MHz(1.8V) | 4-bit | 50MB/s |
| UHS-I SDR104 | 104MHz(1.8V) | 4-bit | 104MB/s |
| UHS-I DDR50 | 50MHz(1.8V, DDR) | 4-bit | 50MB/s |

大多数MCU(如STM32)的SDIO外设最高支持4-bit 50MHz模式(约25MB/s实际吞吐)。

### 1.3 SD卡速度等级

| 等级 | 最低顺序写入 | 适用场景 |
|------|-------------|----------|
| Class 10 | 10MB/s | 基本视频录制 |
| UHS Speed Class 1(U1) | 10MB/s | Full HD视频 |
| UHS Speed Class 3(U3) | 30MB/s | 4K视频 |
| Video Speed Class V10 | 10MB/s | 视频分级 |
| Application Class A1 | 1500 IOPS随机读, 500 IOPS随机写 | IoT应用/应用启动 |
| Application Class A2 | 4000 IOPS随机读, 2000 IOPS随机写, 支持命令队列 | 高性能IoT |

**IoT选型要点**：顺序写入速率对视频记录重要，但传感器数据日志通常是小块随机写入，A1/A2等级的随机IOPS更关键。

## 2. eMMC接口

### 2.1 eMMC架构

eMMC(Embedded Multi Media Card)将NAND Flash芯片和控制器封装在一个BGA芯片中，焊接在PCB上：

```
eMMC内部结构:
+----------------------------------+
| eMMC BGA封装                     |
|  +----------+    +-----------+   |
|  | NAND     |    | 控制器    |   |
|  | Flash    |<-->| - 磨损均衡|   |
|  | 芯片     |    | - 坏块管理|   |
|  |          |    | - ECC     |   |
|  +----------+    | - 缓存    |   |
|                  +-----------+   |
+--|---|---|---|---|---|---|---|--+
   D0  D1  D2  D3  D4  D5  D6  D7  CMD  CLK  RST
```

eMMC对外接口只有CMD、CLK、DAT0-DAT7(8位数据线)和RST，控制器对主机屏蔽了NAND Flash的物理细节。

### 2.2 eMMC速率模式

| 模式 | 总线宽度 | 时钟 | 理论带宽 |
|------|----------|------|----------|
| HS200 | 8-bit | 200MHz | 200MB/s |
| HS400 | 8-bit | 200MHz(DDR) | 400MB/s |
| HS400 Enhanced Strobe | 8-bit | 200MHz(DDR) | 400MB/s |

### 2.3 eMMC版本对比

| 版本 | 年份 | 关键特性 | 顺序读取 | 顺序写入 |
|------|------|----------|----------|----------|
| 4.5 | 2011 | HPI(高优先级中断), 缓存 | 200MB/s | 50MB/s |
| 5.0 | 2013 | HS200模式 | 200MB/s | 90MB/s |
| 5.1 | 2015 | HS400模式, 命令队列(CQ), 缓存 | 400MB/s | 150MB/s |

eMMC 5.1引入的命令队列(CQ: Command Queuing)允许控制器一次接收多个读写命令并优化执行顺序，显著提升随机I/O性能。

## 3. SD卡与eMMC对比

| 对比维度 | SD卡 | eMMC |
|----------|------|------|
| 安装方式 | 插槽(可拆卸) | BGA焊接(固定) |
| 容量 | 2GB-1TB | 4GB-256GB |
| 振动可靠性 | 差(接触不良风险) | 优(焊接固定) |
| 顺序读取 | 最高约100MB/s(UHS-I) | 最高约400MB/s(HS400) |
| 顺序写入 | 最高约90MB/s | 最高约150MB/s |
| 批量成本 | 高(连接器+卡) | 低(芯片级) |
| 可更换性 | 现场可换 | 不可换 |
| 磨损均衡 | 卡内控制器(质量参差) | 内置控制器(较可靠) |
| 功耗 | 较高(3.3V信令) | 较低(1.8V/1.2V信令可选) |
| 防尘防水 | 需密封卡槽 | 无此问题 |

**核心差异**：SD卡可更换但可靠性差，eMMC焊接固定但可靠性高。工业场景优先eMMC，消费类产品或需用户更换存储的场景选SD卡。

## 4. SD卡初始化流程

### 4.1 SPI模式初始化

SD卡上电后必须按标准流程初始化，才能从idle状态进入数据传输状态：

```
上电延迟(>1ms, 74+个CLK)
  |
CMD0 (GO_IDLE_STATE) -> 进入Idle状态
  |
CMD8 (SEND_IF_COND) -> 检测是否SD v2.0+
  |   参数: 0x000001AA (电压2.7-3.6V, 校验模式)
  |   响应: R7 (含回显校验值)
  |   无响应 -> SD v1.x 或 MMC
  |
ACMD41 (SD_SEND_OP_COND) -> 启动初始化
  |   参数: HCS位(支持SDHC)
  |   循环发送直到busy位清零
  |   (SPI模式: 发CMD55+ACMD41)
  |
CMD2 (ALL_SEND_CID) -> 获取CID(卡身份信息)
  |
CMD3 (SEND_RELATIVE_ADDR) -> 分配RCA(相对地址)
  |
CMD7 (SELECT/DESELECT_CARD) -> 选中卡, 进入传输状态
  |
CMD9 (SEND_CSD) -> 获取CSD(卡特性数据: 容量/速度等)
  |
ACMD6 (SET_BUS_WIDTH) -> 设置总线宽度(SD模式4-bit)
  |
-> 初始化完成, 可进行读写
```

### 4.2 初始化代码示例(SPI模式)

```c
// SD卡SPI模式初始化(简化版)
int sd_spi_init(spi_dev_t *spi) {
    // 1. 上电延迟: 发送80个CLK
    spi_cs_high(spi);
    for (int i = 0; i < 80; i++) {
        spi_transfer_byte(spi, 0xFF);
    }

    // 2. CMD0: 进入Idle
    spi_cs_low(spi);
    uint8_t r1 = sd_send_cmd(spi, CMD0, 0, 0x95);
    if (r1 != 0x01) return SD_ERR_NO_CARD;

    // 3. CMD8: 检查SD v2.0+
    r1 = sd_send_cmd(spi, CMD8, 0x000001AA, 0x87);
    int is_v2 = (r1 == 0x01);  // v2.0+会响应

    // 4. ACMD41: 初始化(循环等待)
    int timeout = 1000;
    do {
        sd_send_cmd(spi, CMD55, 0, 0xFF);  // ACMD前缀
        r1 = sd_send_cmd(spi, ACMD41, is_v2 ? 0x40000000 : 0, 0xFF);
        if (r1 == 0x00) break;  // 初始化完成
        HAL_Delay(1);
    } while (--timeout > 0);

    if (timeout == 0) return SD_ERR_TIMEOUT;
    return SD_OK;
}
```

## 5. eMMC内置磨损均衡

### 5.1 为什么eMMC的磨损均衡更可靠

SD卡的控制器质量参差不齐——廉价卡可能只有最基本的磨损均衡，甚至完全没有。eMMC的控制器由芯片厂商提供，磨损均衡算法经过严格验证：

- **动态磨损均衡**：将冷数据(很少修改)从高擦写次数的块搬到低擦写次数的块，释放高擦写块给热数据
- **静态磨损均衡**：主动搬移长期不更新的静态数据，均衡所有物理块的擦写次数
- **预留空间(OP)**：eMMC通常有7%-15%的额外物理容量用于磨损均衡和坏块替换

### 5.2 TRIM/DISCARD支持

eMMC支持DISCARD命令(类似SATA TRIM)，通知控制器某些逻辑块不再需要，控制器可在后台回收物理块。文件系统删除文件后应发送DISCARD，避免写放大。

## 6. 文件系统选择

### 6.1 嵌入式常用文件系统对比

| 文件系统 | 最大分区 | 日志 | 掉电安全 | 适用平台 | 特点 |
|----------|----------|------|----------|----------|------|
| FAT32 | 2TB(32KB簇) | 无 | 差 | 所有 | 通用兼容, PC可读 |
| exFAT | 128PB | 无 | 差 | 所有 | 支持大文件(>4GB) |
| ext4 | 1EB | 有 | 好 | Linux | 成熟稳定 |
| LittleFS | 无硬限制 | 有(COW) | 好 | MCU | 专为MCU设计 |
| SPIFFS | 无硬限制 | 无 | 中 | MCU | 针对小Flash优化 |

### 6.2 FAT32：通用兼容之选

FAT32是嵌入式最广泛使用的文件系统，优势在于几乎所有操作系统都能直接读取：

- **优点**：PC/Mac/Linux通用可读，驱动成熟(FatFs库)，内存占用小
- **缺点**：无日志，异常断电易损坏FAT表和目录项，不支持>4GB单文件
- **适用**：需要PC导出数据的IoT设备(如传感器数据记录器)

### 6.3 LittleFS：MCU掉电安全之选

LittleFS专为资源受限的MCU设计，核心特性：

- **Copy-on-Write(COW)**：元数据更新时写新副本，确认成功后原子切换，异常断电不损坏文件系统
- **动态磨损均衡**：存储块在逻辑上循环使用，配合Flash的块擦除特性
- **内存占用小**：RAM需求与目录深度成正比，典型<5KB

```c
// LittleFS使用示例
#include "lfs.h"

lfs_t lfs;
lfs_file_t file;

// 格式化(首次使用)
lfs_format(&lfs, &cfg);

// 挂载
lfs_mount(&lfs, &cfg);

// 写入日志
lfs_file_open(&lfs, &file, "sensor.log",
               LFS_O_WRONLY | LFS_O_CREAT | LFS_O_APPEND);
char buf[64];
int len = snprintf(buf, sizeof(buf), "%d,%d\n",
                   (int)timestamp, (int)sensor_val);
lfs_file_write(&lfs, &file, buf, len);
lfs_file_close(&lfs, &file);

// 卸载
lfs_unmount(&lfs);
```

### 6.4 ext4：Linux网关之选

运行Linux的IoT网关(如树莓派、工业网关)使用ext4作为根文件系统：

- **日志(journal)**：记录元数据变更，崩溃后快速恢复
- **延期分配(delayed allocation)**：减少碎片
- **配额(quota)和ACL**：多用户/多应用场景

### 6.5 选型决策

| 场景 | 文件系统 | 存储介质 | 原因 |
|------|----------|----------|------|
| MCU数据记录, 需掉电安全 | LittleFS | SPI NOR Flash | COW保证一致性 |
| MCU数据记录, 需PC读取 | FAT32(FatFs) | SD卡(SPI) | PC可直接读卡 |
| Linux网关根文件系统 | ext4 | eMMC | 日志保证可靠性 |
| Linux网关数据分区 | FAT32/exFAT | eMMC | 大文件, 通用兼容 |
| 大文件视频存储(>4GB) | exFAT | SD卡/USB | 突破4GB限制 |

## 7. SD卡在IoT中的可靠性问题

### 7.1 掉电损坏

SD卡(FAT32)最常见的问题是异常断电导致文件系统损坏。FAT表和目录项更新不是原子操作，断电可能留下不一致状态。

缓解措施：

1. **使用掉电安全文件系统**：LittleFS替代FAT32
2. **硬件掉电检测**：监测VCC，提前卸载文件系统
3. **双FAT备份**：FAT32本身有两份FAT表，可互相修复
4. **定期fsck**：Linux环境定时运行文件系统检查

### 7.2 工业级SD卡

消费级SD卡使用TLC/QLC NAND，寿命和可靠性有限。工业级SD卡特点：

| 对比项 | 消费级 | 工业级 |
|--------|--------|--------|
| NAND类型 | TLC/QLC | SLC/MLC(pSLC模式) |
| 擦写寿命 | 300-3000次 | 3000-30000次 |
| 工作温度 | 0-70度C | -40-85度C |
| 磨损均衡 | 基础 | 高级动态+静态 |
| 预留空间 | 约3% | 约7%-15% |
| 价格 | 低 | 5-20倍 |
| 代表产品 | SanDisk Ultra | SanDisk Industrial, Swissbit |

### 7.3 SD卡寿命估算

```c
// SD卡寿命估算
// 假设: 8GB工业级SD卡(pSLC模式, 30000次PE), 7%OP
// 有效物理容量 = 8GB * 1.07 = 8.56GB
// 总写入量(TBW) = 8.56GB * 30000 = 256.8TB

// 每日写入量:
// 传感器数据: 10字节/条 * 1条/秒 * 86400秒/天 = 864KB/天
// 加上FAT表和日志开销(约3x): 864KB * 3 = 2.6MB/天
// TBW寿命 = 256.8TB / 2.6MB/天 = 约2700万天 = 约74000年

// 看似寿命很长, 但FAT32的写放大会使实际寿命远低于理论值
// 频繁创建/删除小文件时, FAT表反复更新, 写放大可达10-100倍
```

## 8. 实战案例

### 8.1 SPI模式SD卡数据记录器

```c
// 基于FatFs的SD卡数据记录器(MCU + SPI SD卡)
#include "ff.h"

FATFS fs;
FIL logfile;
char logbuf[256];
int buf_pos = 0;

int logger_init(void) {
    FRESULT res;

    // 挂载文件系统
    res = f_mount(&fs, "", 1);
    if (res != FR_OK) return -1;

    // 打开日志文件(追加模式)
    res = f_open(&logfile, "data.csv",
                 FA_WRITE | FA_OPEN_APPEND | FA_CREATE_NEW);
    if (res != FR_OK) return -1;

    // 写CSV头
    f_puts("timestamp,temperature,humidity\n", &logfile);
    f_sync(&logfile);  // 强制刷入SD卡
    return 0;
}

void logger_log(uint32_t ts, float temp, float hum) {
    int len = snprintf(logbuf + buf_pos, sizeof(logbuf) - buf_pos,
                       "%lu,%.1f,%.1f\n", ts, temp, hum);
    buf_pos += len;

    // 缓冲区满时写入SD卡
    if (buf_pos > sizeof(logbuf) - 32) {
        f_write(&logfile, logbuf, buf_pos, NULL);
        f_sync(&logfile);
        buf_pos = 0;
    }
}

void logger_deinit(void) {
    if (buf_pos > 0) {
        f_write(&logfile, logbuf, buf_pos, NULL);
    }
    f_sync(&logfile);
    f_close(&logfile);
    f_mount(NULL, "", 0);
}
```

### 8.2 Linux网关eMMC根文件系统

```bash
# eMMC分区策略(嵌入式Linux网关)
# /dev/mmcblk0 = eMMC设备

# 分区表:
# mmcblk0p1: 64MB, FAT32, boot分区(内核/设备树)
# mmcblk0p2: 512MB, ext4, rootfs(只读根文件系统)
# mmcblk0p3: 剩余空间, ext4, data分区(可读写应用数据)

# 创建分区
fdisk /dev/mmcblk0
# p1: 64MB, type 0x0C (FAT32 LBA)
# p2: 512MB, type 0x83 (Linux)
# p3: rest, type 0x83 (Linux)

# 格式化
mkfs.vfat -F 32 -n BOOT /dev/mmcblk0p1
mkfs.ext4 -L rootfs /dev/mmcblk0p2
mkfs.ext4 -L data /dev/mmcblk0p3

# 挂载选项(优化eMMC寿命)
# /etc/fstab:
/dev/mmcblk0p1  /boot   vfat    defaults,noatime        0 0
/dev/mmcblk0p2  /       ext4    ro,noatime              0 0
/dev/mmcblk0p3  /data   ext4    noatime,data=ordered    0 0

# 注意: rootfs设为只读(ro), 防止意外写入和掉电损坏
# 应用数据写入/data分区
# 使用overlayfs在rootfs上叠加可写层(如需修改配置)
```

### 8.3 分区策略要点

嵌入式Linux存储分区的一般原则：

1. **boot分区**：FAT32，存放内核(uImage/zImage)、设备树(dtb)、引导脚本。U-Boot原生支持FAT32读取
2. **rootfs分区**：ext4，设为只读或使用overlayfs，保证系统可恢复。A/B分区方案可实现系统升级回滚
3. **data分区**：ext4，可读写，存放应用数据和日志。考虑使用f2fs(Flash友好文件系统)替代ext4以获得更好的随机写入性能

## 总结

SD卡和eMMC是IoT设备中提供大容量存储的两种主流方案，选择取决于可靠性、可维护性和成本的平衡：

1. **SD卡**通过SPI或SDIO接口连接，可现场更换，但振动可靠性差，适合消费类产品和需要PC导出数据的场景
2. **eMMC**焊接固定、内置控制器提供可靠的磨损均衡和坏块管理，适合工业和汽车IoT
3. **文件系统选择**取决于平台和需求：MCU选LittleFS(掉电安全)或FAT32(PC兼容)，Linux选ext4(日志保证)
4. SD卡初始化必须严格按照CMD0-CMD8-ACMD41-CMD2-CMD3流程，跳步会导致初始化失败
5. FAT32在异常断电下易损坏是SD卡在IoT中最常见的问题，工业级卡和掉电检测是关键缓解手段
6. 嵌入式Linux的分区策略(boot + rootfs + data)将系统与数据分离，rootfs只读提升可靠性

经验法则：振动环境选eMMC，需更换选SD卡；MCU选LittleFS，Linux选ext4；关键数据必须有备份或掉电保护。

## 参考文献

1. SD Association. *SD Specifications Part 1: Physical Layer Specification*, Version 8.00, 2020.
2. JEDEC. *eMMC Specification JESD84-B51*, Version 5.1, 2015.
3. ARM Limited. *LittleFS: A fail-safe file system for embedded systems*, GitHub Repository, 2022.
4. Elm-Chan. *FatFs - Generic FAT Filesystem Module*, http://elm-chan.org/fsw/ff/00index_e.html, 2023.
5. C. Banbury et al., *Benchmarking the Performance of Embedded Flash File Systems*, in Proc. IEEE International Conference on Embedded Software (EMSOFT), 2021.
