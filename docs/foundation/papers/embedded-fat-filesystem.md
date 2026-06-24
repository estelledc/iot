# 嵌入式FAT文件系统FatFs移植与SD卡操作
> **难度**：中级 | **领域**：文件系统移植 | **阅读时间**：约 20 分钟

## 引言

电脑上的文件系统就像一个图书馆：每本书(文件)有自己的编号(路径)，目录卡片(FAT表)记录了书在哪个书架(哪些簇)上。FatFs就是把这个微型图书馆搬到MCU里的方案 -- 只要实现几个读写接口，就能让嵌入式设备也用上和电脑兼容的文件操作。插上SD卡，MCU写的数据电脑直接能读，这在数据记录场景中特别方便。

## 1 FatFs概述

### 1.1 FatFs是什么

FatFs是日本开发者ChaN编写的通用FAT/exFAT文件系统模块：

- 纯C语言编写，可移植性强
- 支持FAT12/FAT16/FAT32/exFAT
- 与Windows完全兼容，PC可直读
- 开源免费，授权宽松
- 代码量小(核心约8KB)，适合嵌入式

### 1.2 为什么选FatFs

| 优势 | 说明 |
|------|------|
| PC兼容 | SD卡拔出直接在电脑读取 |
| 成熟稳定 | 十年以上迭代，bug极少 |
| 占用小 | RAM需求约1-4KB(取决于配置) |
| 接口简洁 | 标准POSIX风格文件API |

## 2 FAT文件系统基础

### 2.1 FAT版本

| 版本 | 最大簇数 | 卷大小上限 | 典型用途 |
|------|----------|-----------|----------|
| FAT12 | 4084 | 16MB | 软盘 |
| FAT16 | 65524 | 2GB | 小容量SD卡 |
| FAT32 | 268435456 | 2TB | 大容量SD卡 |
| exFAT | 约4B | 128PB | SDXC卡 |

### 2.2 FAT文件系统结构

SD卡上FAT32的布局：

```
+------------------+
| MBR/引导扇区     |  扇区0: 分区表
+------------------+
| 保留扇区         |  包含BPB(BIOS Parameter Block)
+------------------+
| FAT表(两份)      |  簇链分配信息
+------------------+
| 根目录           |  FAT32根目录也是簇链
+------------------+
| 数据区           |  文件和子目录存储区
+------------------+
```

### 2.3 关键概念

- **簇(Cluster)**：最小分配单位，1簇 = n个扇区(n为2的幂)
- **FAT表**：记录每个簇的状态(空闲/下一簇号/文件末尾/坏簇)
- **目录项**：32字节结构，存储文件名、大小、首簇号、时间戳

## 3 FatFs架构

### 3.1 分层结构

```
+---------------------------+
|     应用程序               |  f_open, f_read, f_write...
+---------------------------+
|     FatFs模块              |  文件系统逻辑
+---------------------------+
|     磁盘I/O层(需用户实现)   |  disk_read, disk_write...
+---------------------------+
|     物理存储介质            |  SD卡 / SDIO / SPI Flash
+---------------------------+
```

### 3.2 用户需要做什么

用户只需实现磁盘I/O层的几个函数，FatFs模块本身不需要修改。

## 4 移植FatFs

### 4.1 需要实现的接口

```c
// diskio.h - 用户必须实现的5个函数

DSTATUS disk_initialize(BYTE pdrv);      // 初始化磁盘
DSTATUS disk_status(BYTE pdrv);          // 获取磁盘状态
DRESULT disk_read(BYTE pdrv, BYTE* buff,
                  LBA_t sector, UINT count);    // 读扇区
DRESULT disk_write(BYTE pdrv, const BYTE* buff,
                   LBA_t sector, UINT count);   // 写扇区
DRESULT disk_ioctl(BYTE pdrv, BYTE cmd,
                   void* buff);           // 控制命令
DWORD   get_fattime(void);               // 获取当前时间
```

### 4.2 关键实现要点

- `disk_initialize`：初始化SPI/SDIO接口，调用sd_card_init()
- `disk_read/disk_write`：转发到SD卡扇区读写函数
- `disk_status`：检测卡是否在位
- `disk_ioctl`：处理CTRL_SYNC/GET_SECTOR_COUNT等控制命令

### 4.3 get_fattime实现

```c
DWORD get_fattime(void) {
    // 返回FAT时间戳格式: bit[31:25]=年-1980
    //   bit[24:21]=月, bit[20:16]=日
    //   bit[15:11]=时, bit[10:5]=分, bit[4:0]=秒/2
    // 如果没有RTC，返回固定时间
    return ((DWORD)(2024 - 1980) << 25)
         | ((DWORD)1 << 21)
         | ((DWORD)1 << 16);
}
```

## 5 SD卡SPI接口

### 5.1 SPI模式初始化流程

```
步骤1: 发送80个以上时钟脉冲(CS拉高), SD卡进入SPI模式
步骤2: CMD0 (复位) -> 应答0x01 (进入IDLE状态)
步骤3: CMD8 (电压检查, SD V2必须) -> 应答0x01 + 电压范围
步骤4: ACMD41 (初始化, 反复发送直到退出IDLE) -> 应答0x00
步骤5: CMD58 (读OCR寄存器) -> 确认SDHC/SDSC类型
```

### 5.2 基本读写命令

| 命令 | 功能 | 参数 |
|------|------|------|
| CMD17 | 读单个扇区 | 扇区地址 |
| CMD24 | 写单个扇区 | 扇区地址 |
| CMD18 | 读多扇区(连续) | 起始扇区 |
| CMD25 | 写多扇区(连续) | 起始扇区 |
| CMD12 | 停止传输 | 无 |

### 5.3 SPI读写扇区代码

```c
DRESULT sd_read_sectors(uint32_t sector, uint8_t *buf,
                        uint32_t count) {
    if (count == 1) {
        // 单扇区读取
        sd_send_cmd(CMD17, sector);
        sd_wait_token(0xFE);  // 等待数据起始令牌
        spi_read(buf, 512);   // 读取512字节数据
        spi_read(crc, 2);     // 读取2字节CRC(可忽略)
    } else {
        // 多扇区读取
        sd_send_cmd(CMD18, sector);
        for (uint32_t i = 0; i < count; i++) {
            sd_wait_token(0xFE);
            spi_read(buf + i * 512, 512);
            spi_read(crc, 2);
        }
        sd_send_cmd(CMD12, 0);  // 停止传输
    }
    return RES_OK;
}
```

## 6 SD卡SDIO接口

SDIO模式比SPI更快，但实现更复杂：

| 特性 | SPI模式 | SDIO模式 |
|------|---------|----------|
| 总线宽度 | 1位 | 1位/4位 |
| 时钟频率 | 最高25MHz | 最高50MHz |
| 理论速度 | 约3MB/s | 约25MB/s |
| 引脚数 | 4(SPI) | 6(CMD+CLK+4xDAT) |
| 实现复杂度 | 简单 | 复杂(需DMA) |

STM32使用SDIO外设配合DMA，初始化时用1位宽总线，成功后切换到4位以获得最高速度。

## 7 FatFs配置

### 7.1 ffconf.h关键配置项

```c
#define FF_FS_READONLY   0    // 0:可读写  1:只读
#define FF_FS_MINIMIZE   0    // 0:全功能  3:最小化
#define FF_USE_STRFUNC   1    // 1:启用字符串函数
#define FF_USE_FIND      1    // 1:启用目录搜索
#define FF_USE_MKFS      1    // 1:启用格式化
#define FF_USE_FASTSEEK  1    // 1:启用快速定位
#define FF_USE_LFN       2    // 2:长文件名(堆分配)
#define FF_CODE_PAGE     936  // 936:中文GBK
#define FF_VOLUMES       1    // 逻辑驱动器数量
#define FF_MIN_SS        512  // 最小扇区大小
#define FF_MAX_SS        512  // 最大扇区大小
#define FF_FS_EXFAT      0    // 0:不启用exFAT
```

### 7.2 长文件名配置

`FF_USE_LFN`控制长文件名支持：0=仅8.3格式, 1=静态缓冲, 2=堆动态分配(推荐), 3=栈分配。注意长文件名功能需要额外的代码页表，会增加Flash占用。

## 8 基本操作代码示例

### 8.1 文件读写

```c
FATFS fs;       // 文件系统对象
FIL file;       // 文件对象
FRESULT res;    // 返回值

// 1. 挂载文件系统
res = f_mount(&fs, "0:", 1);
if (res != FR_OK) {
    // 挂载失败处理
}

// 2. 创建/打开文件并写入
res = f_open(&file, "0:test.csv", FA_WRITE | FA_CREATE_ALWAYS);
if (res == FR_OK) {
    const char *data = "time,temperature,humidity\r\n";
    UINT written;
    f_write(&file, data, strlen(data), &written);
    f_close(&file);
}

// 3. 读取文件
res = f_open(&file, "0:test.csv", FA_READ);
if (res == FR_OK) {
    char buf[256];
    UINT read;
    f_read(&file, buf, sizeof(buf), &read);
    buf[read] = '\0';
    f_close(&file);
}

// 4. 卸载
f_mount(NULL, "0:", 0);
```

### 8.2 目录操作

```c
// 创建目录
f_mkdir("0:data");

// 遍历目录
DIR dir;
FILINFO info;
res = f_opendir(&dir, "0:data");
if (res == FR_OK) {
    while (1) {
        res = f_readdir(&dir, &info);
        if (res != FR_OK || info.fname[0] == '\0') break;
        // info.fname: 文件名
        // info.fsize: 文件大小
    }
    f_closedir(&dir);
}
```

## 9 实践案例：IoT数据记录器

每秒记录温湿度数据到CSV，每天创建新文件：

```c
void data_logger_task(void) {
    FATFS fs;
    FIL file;
    char filename[32];

    f_mount(&fs, "0:", 1);
    while (1) {
        // 按日期生成文件名
        RTC_DateTypeDef date;
        HAL_RTC_GetDate(&hrtc, &date, FORMAT_BIN);
        snprintf(filename, sizeof(filename),
                 "0:%04d%02d%02d.csv",
                 2000 + date.Year, date.Month, date.Date);

        // 追加打开或新建文件
        FRESULT res = f_open(&file, filename,
                             FA_WRITE | FA_OPEN_APPEND);
        if (res == FR_NO_FILE) {
            f_open(&file, filename, FA_WRITE | FA_CREATE_NEW);
            f_printf(&file, "timestamp,temp,humi\r\n");
        }
        if (res == FR_OK) {
            float temp = read_temperature();
            float humi = read_humidity();
            RTC_TimeTypeDef time;
            HAL_RTC_GetTime(&hrtc, &time, FORMAT_BIN);
            f_printf(&file, "%02d:%02d:%02d,%.1f,%.1f\r\n",
                     time.Hours, time.Minutes, time.Seconds, temp, humi);
            f_sync(&file);
            f_close(&file);
        }
        osDelay(1000);
    }
}
```

## 10 性能优化

### 10.1 写入优化

- **批量写入**：积累多个数据点后一次性写入，而非逐字节
- **簇对齐**：写入起始地址对齐到簇边界，减少跨簇操作
- **预分配**：用f_lseek预分配文件大小，避免反复更新FAT表

```c
// 预分配文件大小
f_open(&file, "0:log.bin", FA_WRITE | FA_CREATE_ALWAYS);
f_lseek(&file, PREALLOC_SIZE);  // 预分配空间
f_lseek(&file, 0);              // 回到开头开始写入
```

### 10.2 掉电安全

```c
// 关键操作后调用f_sync
f_write(&file, data, len, &written);
f_sync(&file);  // 立即刷新FAT表和目录项到SD卡

// 对于关键数据，写两份文件交叉更新
// 读时检查哪个文件完整
```

## 11 常见问题

### 11.1 SD卡初始化失败

常见原因及对策：

- SPI时钟过快：初始化阶段必须用低速(400kHz以下)
- 供电不足：SD卡写入时电流可达100mA，确保供电稳定
- 接触不良：检查SD卡座焊接

### 11.2 写入性能衰减

SD卡内部磨损均衡导致长期使用后变慢：

- 使用高品质SD卡(工业级)
- 避免频繁创建删除小文件
- 定期格式化

### 11.3 掉电文件损坏

FAT表和目录项可能处于不一致状态：

- 每次写入后调用f_sync
- 使用双文件交替写入策略
- 考虑使用LittleFS等掉电安全文件系统

### 11.4 FAT32文件大小限制

FAT32单文件最大4GB，对于持续写入的数据记录器可能不够：

- 定期创建新文件(按天/按大小)
- 考虑exFAT(需开启FF_FS_EXFAT)

## 12 FatFs与LittleFS对比

| 特性 | FatFs | LittleFS |
|------|-------|----------|
| PC兼容 | 直接可读 | 需要专门工具 |
| 磨损均衡 | 无(依赖SD卡内部) | 有(内置) |
| 掉电安全 | 不保证 | 保证(写时拷贝) |
| 适用介质 | SD卡为主 | SPI Flash为主 |
| RAM占用 | 1-4KB | 约4KB |
| 文件系统开销 | 取决于分区大小 | 固定2个块 |

## 总结

FatFs是嵌入式领域最成熟的FAT文件系统实现，移植只需实现5个磁盘I/O函数。SD卡接口可选SPI(简单低速)或SDIO(复杂高速)，根据项目需求选择。配置ffconf.h可精细控制功能与代码体积的平衡。实际项目中，关键注意事项是掉电安全(使用f_sync)、写入优化(批量写入)和容量管理(定期创建新文件)。如果目标介质是SPI Flash且需要掉电安全保证，LittleFS可能是更好的选择。

## 参考文献

1. ChaN. FatFs - Generic FAT File System Module Documentation, 2024.
2. SD Specifications Part 1: Physical Layer Simplified Specification, SD Association, 2023.
3. STM32Cube FATFS Middleware Documentation, STMicroelectronics.
4. LittleFS: A fail-safe file system for microcontrollers, ARM mbed, 2024.
5. Anderson D. Interfacing SD Cards with Microcontrollers, Embedded Systems Conference, 2022.
