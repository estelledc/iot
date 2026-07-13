---
schema_version: '1.0'
id: embedded-fat-filesystem
title: 嵌入式FAT文件系统FatFs移植与SD卡操作
layer: 1
content_type: tutorial
difficulty: intermediate
reading_time: 16
prerequisites:
  - sd-emmc-storage-embedded
  - littlefs-filesystem-embedded
tags:
  - FatFs
  - FAT32
  - SD卡
  - SPI
  - SDIO
  - 数据记录
  - 嵌入式文件系统
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 嵌入式FAT文件系统FatFs移植与SD卡操作

> **难度**：🟡 中级 | **领域**：嵌入式存储软件 | **关键词**：FatFs, FAT32, diskio, SD SPI/SDIO | **阅读时间**：约 16 分钟

## 日常类比

电脑文件系统像图书馆：书是文件，目录卡片是文件分配表（File Allocation Table, FAT），书架格子是簇。FatFs 把这座“微型图书馆”搬进微控制器（MCU）：你实现底层扇区读写，上层就能 `f_open` / `f_write`；SD 卡拔到电脑上通常还能直接打开——数据记录场景很香[1][2]。

## 摘要

说明 FatFs 分层与 diskio 移植、FAT 版本差异、SD 卡 SPI/SDIO 要点、配置与掉电风险，并对照 LittleFS。吞吐与 RAM 占用随配置和卡速变化，**以实测与 ChaN 文档为准**[1][3]。

## 1. 为何 FatFs

| 点 | 说明 |
|----|------|
| PC 兼容 | Windows/macOS 常可直读 |
| 体积 | 核心可裁到数 KB～十余 KB 量级 |
| API | 接近熟悉的文件接口 |
| 许可 | 宽松，广泛用于 MCU[1] |

| 版本 | 典型容量语境 |
|------|----------------|
| FAT12/16 | 很小介质 |
| FAT32 | 常见 SDHC |
| exFAT | 更大卡；FatFs 可选启用 |

布局概要：引导/BPB → FAT（常双份）→ 目录 → 数据区。簇是分配单位；目录项含名、大小、首簇等[2]。

## 2. 移植面

应用 → FatFs → **用户实现的 diskio** → SD/SPI Flash。

必做：`disk_initialize` / `disk_status` / `disk_read` / `disk_write` / `disk_ioctl`，以及 `get_fattime`（无实时时钟可返回固定合法时间戳）[1]。

| SD 接口 | 特点 |
|---------|------|
| SPI | 实现简单，速度较低 |
| SDIO/SDMMC | 可 4 线高速，常配 DMA，驱动复杂 |

SPI 初始化需低速（约数百 kHz 量级）完成卡识别后再提速；注意供电峰值与卡座接触[2][3]。

## 3. 配置与记录器实践

`ffconf.h` 控制只读、长文件名（LFN）、exFAT、代码页等：LFN 与中文代码页显著增加 Flash。日志场景：按日切文件、批量写、`f_sync` 刷目录/FAT；预分配减少频繁扩展[1]。

| 对比 | FatFs | LittleFS |
|------|-------|----------|
| PC 直读 | 优 | 需工具 |
| 掉电安全 | 弱（依赖同步策略） | 设计目标之一 |
| 磨损均衡 | 多靠 SD 内部 | 内置（NOR 友好） |
| 介质 | SD 为主 | SPI Flash 为主 |

## 4. 局限、挑战与可改进方向

### 1. 掉电易损坏目录/FAT

**局限**：写数据后未 sync 即断电，出现文件长度为 0 或交叉链接。
**改进**：关键点 `f_sync`；双文件交替；供电监控先停写。

### 2. 小文件频繁创建删除

**局限**：碎片与 SD 内部 GC 导致越写越慢。
**改进**：追加大文件、定期格式化、工业卡；或改 LittleFS 于 Flash。

### 3. FAT32 单文件约 4 GB 上限

**局限**：长期高速记录可能触顶。
**改进**：按大小/时间切分；评估 exFAT。

### 4. 初始化与供电不稳

**局限**：SPI 过快、电流不足导致偶发挂载失败。
**改进**：分阶段时钟、去耦与限流评估、重试状态机。

## 5. 实践要点

1. 先打通单扇区读写再挂 FatFs。
2. 量产锁定卡品牌等级与文件系统配置宏。
3. 纯片上 Flash 日志优先评估 `littlefs-filesystem-embedded`。

## 参考文献

[1] ChaN, FatFs generic FAT file system module documentation.
[2] SD Association, SD specifications — physical layer simplified.
[3] STMicroelectronics, STM32Cube FATFS middleware docs.
[4] ARM mbed, LittleFS design and usage.
[5] Microsoft, FAT32 file system specification.
[6] ELM Chan application notes / samples for diskio on SPI SD.
[7] JEDEC / microSD industrial card endurance guidance.
[8] NXP/STM32 SDMMC driver application notes.
[9] POSIX-like embedded FS comparison articles（FatFs vs LittleFS）.
[10] exFAT specification overview（大容量扩展）.
[11] Power-fail safe logging patterns on SD cards（嵌入式实践）.
