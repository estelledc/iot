# LittleFS文件系统在MCU Flash上的应用
> **难度**：🟡 中级 | **领域**：嵌入式文件系统 | **阅读时间**：约 20 分钟

## 引言

想象一下你的文件柜: 如果没有文件夹和标签, 所有文件堆在一起, 找一份合同要翻遍整摞纸。MCU 上的 Flash 也是如此 -- 没有文件系统, 数据就是一团裸字节, 你得自己记住"配置信息在第 0x0800 FC00 偏移处"。文件系统就是给 Flash 装上"文件夹 + 标签", 让数据有条理地存储和查找。LittleFS 正是专为 MCU Flash 这种资源受限场景设计的文件系统。

## 1 为什么 MCU 需要文件系统

### 1.1 结构化数据存储

裸 Flash 操作需要手动管理偏移地址, 多个数据块容易互相覆盖。文件系统提供目录、文件名和层级结构, 让每类数据各归其位。

### 1.2 OTA 固件管理

OTA (Over-The-Air) 升级需要存储新固件镜像、校验信息、回滚标志。文件系统保证这些元数据在断电时不会丢失或损坏。

### 1.3 配置文件持久化

设备参数 (Wi-Fi 凭据、传感器校准值、用户偏好) 需要掉电不丢失, 且能随时修改。文件系统让配置读写像操作文件一样简单。

## 2 LittleFS 设计目标

LittleFS 由 ARM mbed 团队开发, 专门针对嵌入式 Flash 存储的三个核心痛点:

| 设计目标 | 说明 |
|----------|------|
| 掉电安全 (Power-loss resilient) | 任意时刻断电, 文件系统不会损坏, 重启后可恢复到最近一致状态 |
| 磨损均衡 (Wear leveling) | 均匀分布写入, 避免 Flash 某些块过早耗尽寿命 |
| 有界资源 (Bounded RAM/ROM) | RAM 和 ROM 占用量与 Flash 容量无关, 不随存储增大而增长 |

## 3 LittleFS 架构

### 3.1 元数据: Copy-on-Write 机制

LittleFS 的元数据 (目录项、文件属性) 采用 Copy-on-Write (COW) 策略: 修改时不覆盖旧数据, 而是写入新位置, 然后原子地更新指针。这保证了断电时要么看到旧状态, 要么看到新状态, 不会出现半写半旧的中间态。

```
修改前:            修改后 (COW):
[Block A] meta     [Block A] meta (旧, 仍完整)
                   [Block B] meta' (新, 写完后原子切换)
```

### 3.2 小文件: Inline Files

小于块大小的文件数据直接存储在目录项中 (inline), 不额外分配数据块。这对配置文件等小文件场景节省空间和写入次数。

### 3.3 大文件: CTZ Skip-List

大文件使用 CTZ (Constant-Time Z) 跳表索引数据块。跳表结构保证:
- 追加写入 O(1)
- 随机读取 O(n^(1/2)) -- 远优于链表的 O(n)
- 内存占用 O(1) -- 不需要缓存整个索引

CTZ 跳表的第 i 个块指向前面第 2^0, 2^1, 2^2, ... 个块, 形成多级索引。

## 4 磨损均衡机制

### 4.1 动态块分配

LittleFS 不固定数据块位置。每次写入时, 文件系统从空闲块池中选取写入次数最少的块, 自然地将写入分散到整个 Flash。

### 4.2 Block Cycles 参数

`block_cycles` 参数控制磨损均衡的积极程度。当一个块被擦写次数达到 `block_cycles` 时, LittleFS 会将该块的数据迁移到其他块, 让高磨损块"休息"。设为 0 则禁用主动磨损均衡 (仅依赖 COW 的自然分散)。

### 4.3 旧块驱逐 (Eviction)

元数据 COW 会持续产生旧版本块。LittleFS 在元数据对 (metadata pair) 写满后, 将有效数据搬到新位置, 驱逐整个旧块, 使其可被擦除重用。

## 5 掉电安全

### 5.1 原子元数据提交

元数据以块对 (metadata pair) 的形式存储。更新时先写 partner 块, 完成后修改指向 partner 块的指针。指针更新是单次写入操作, 具有原子性。

### 5.2 无孤儿文件

掉电后, LittleFS 通过扫描元数据对判断哪些块属于哪个文件。未完成的写操作产生的块会被识别为孤儿并回收。文件系统始终处于可恢复的一致状态。

### 5.3 数据块的写时拷贝

文件数据修改同样遵循 COW: 新数据写入新块, 然后更新文件索引指向新块。旧数据块在确认新数据写入成功后才被标记为可回收。

## 6 配置参数详解

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `block_size` | Flash 擦除块大小 (字节) | 4096 (内部 Flash), 4096/65536 (SPI Flash) |
| `block_count` | Flash 总块数 | 依 Flash 容量计算 |
| `cache_size` | 读写缓存大小 (字节) | 16-64, 需 >= read/prog 缓冲区 |
| `lookahead_size` | 前瞻缓冲区大小 (bit) | 8-32, 影响 mount 速度 |
| `block_cycles` | 磨损均衡周期 | 100-1000, 设 0 禁用 |

`cache_size` 影响 RAM 占用: 每个 mounted 分区占用 2 * `cache_size` 字节 RAM。`lookahead_size` 影响空闲块扫描速度, 越大 mount 越快但 RAM 越多。

## 7 移植到硬件

### 7.1 四个回调函数

LittleFS 通过回调函数抽象 Flash 硬件, 需要实现以下接口:

```c
// 读取: 从 block 的 off 偏移处读 size 字节到 buffer
int flash_read(const struct lfs_config *cfg,
               lfs_block_t block, lfs_off_t off,
               void *buffer, lfs_size_t size);

// 写入: 将 buffer 的 size 字节写到 block 的 off 偏移处
int flash_prog(const struct lfs_config *cfg,
               lfs_block_t block, lfs_off_t off,
               const void *buffer, lfs_size_t size);

// 擦除: 擦除整个 block
int flash_erase(const struct lfs_config *cfg,
                lfs_block_t block);

// 同步: 确保数据已写入 Flash (某些硬件需要)
int flash_sync(const struct lfs_config *cfg);
```

### 7.2 STM32 内部 Flash 示例

STM32 内部 Flash 的擦除粒度通常为 2KB 或 4KB (因系列而异)。注意:
- 写入前必须解锁 Flash
- 擦除后才能写入 (不能覆盖写)
- 中断向量表通常在 Flash 前部, LittleFS 应放在尾部

### 7.3 外部 SPI Flash (W25Q) 示例

W25Q 系列 SPI Flash 的 4KB 扇区是自然对齐的, 非常适合 LittleFS。要点:
- 使用 SPI/Dual SPI/Quad SPI 通信
- 写入前检查 Write Enable (WEL) 位
- 擦除和写入操作需要等待 Busy 位清零
- 建议启用 Quad SPI 以提升吞吐量

## 8 与其他嵌入式文件系统对比

| 特性 | LittleFS | SPIFFS | FatFS | YAFFS |
|------|----------|--------|-------|-------|
| 目录支持 | 有 | 无 (扁平结构) | 有 | 有 |
| 磨损均衡 | 有 (动态) | 有 (基本) | 无 | 有 (NAND 优化) |
| 掉电安全 | 有 | 部分 | 无 | 有 |
| RAM 占用 | O(1) 固定 | O(1) | O(n) 随容量增长 | O(n) |
| ROM 占用 | 约 8-12KB | 约 6KB | 约 8-20KB | 约 30KB |
| 适用介质 | NOR Flash | NOR Flash | 任意块设备 | NAND Flash |
| 维护状态 | 活跃 | 已弃用 | 活跃 | 活跃 |

**SPIFFS** 不支持目录, 已标记为弃用, 新项目不建议使用。
**FatFS** 成熟稳定但无磨损均衡, 且 RAM 随容量线性增长, 不适合大容量 NOR Flash。
**YAFFS** 针对 NAND Flash 优化, 在 NOR Flash 上有额外开销。

## 9 性能特征

### 9.1 挂载时间

LittleFS mount 时间与 Flash 中有效数据量相关, 通常在几十毫秒级别。`lookahead_size` 越大, 空闲块扫描越快, mount 越快。

挂载过程主要包括:
1. 读取根目录元数据对, 确定文件系统根结构
2. 扫描 lookahead 缓冲区, 识别空闲块
3. 如果上次非正常卸载, 可能需要额外的一致性检查

典型 mount 时间 (1MB Flash, 256 块):

| lookahead_size | mount 时间 | RAM 开销 |
|----------------|-----------|----------|
| 8 | 约 50 ms | 1 字节 |
| 16 | 约 30 ms | 2 字节 |
| 32 | 约 20 ms | 4 字节 |

### 9.2 读写吞吐量

读写性能主要受限于 Flash 硬件本身:
- 内部 Flash 写入: 约 1-5 MB/s
- SPI Flash (标准): 约 1-3 MB/s 读, 0.5-1 MB/s 写
- QSPI Flash: 读可达 10-30 MB/s, 写约 1-3 MB/s

LittleFS 的 COW 开销使写放大比约 1.2-2.0x (取决于块大小和数据量)。

### 9.3 写放大分析

写放大 (Write Amplification) 是指实际写入 Flash 的数据量与用户请求写入量的比值。LittleFS 的写放大来源:

| 来源 | 放大倍数 | 说明 |
|------|----------|------|
| 元数据 COW | 1.0-1.5x | 每次文件修改需同步更新目录元数据 |
| 块对齐 | 1.0-2.0x | 小于块大小的写入仍需整块操作 |
| 磨损均衡搬迁 | 偶发 | block_cycles 触发时整块搬迁 |

降低写放大的方法:
- 合并多次小写入为一次大写入
- 选用较大的 `prog_size` 匹配 Flash 页大小
- 减少频繁的文件创建和删除操作

### 9.4 存储空间利用率

LittleFS 的空间开销:
- 每个目录占用 1 个元数据对 (2 个块)
- 小文件 (inline) 不额外占用数据块
- 大文件的 CTZ 索引开销: 每 N 个数据块需要 1 个索引块

对于 4KB 块大小, 1MB Flash 的可用空间约 960-980 KB (元数据开销约 2-4%)。

## 10 实践代码示例

```c
#include "lfs.h"

// -- 硬件回调 (简化示例) --
int flash_read(const struct lfs_config *c, lfs_block_t block,
               lfs_off_t off, void *buf, lfs_size_t size) {
    // 从 SPI Flash 读取: 基地址 + block*block_size + off
    uint32_t addr = block * c->block_size + off;
    W25Q_Read(addr, buf, size);
    return 0;
}

int flash_prog(const struct lfs_config *c, lfs_block_t block,
               lfs_off_t off, const void *buf, lfs_size_t size) {
    uint32_t addr = block * c->block_size + off;
    W25Q_Program(addr, buf, size);
    return 0;
}

int flash_erase(const struct lfs_config *c, lfs_block_t block) {
    uint32_t addr = block * c->block_size;
    W25Q_SectorErase(addr);
    return 0;
}

int flash_sync(const struct lfs_config *c) {
    return 0; // SPI Flash 同步已由硬件保证
}

// -- 配置 --
lfs_t lfs;
struct lfs_config cfg = {
    .read      = flash_read,
    .prog      = flash_prog,
    .erase     = flash_erase,
    .sync      = flash_sync,
    .read_size      = 256,
    .prog_size      = 256,
    .block_size     = 4096,
    .block_count    = 256,     // 1MB Flash
    .cache_size     = 16,
    .lookahead_size = 16,
    .block_cycles   = 500,
};

// -- 初始化与挂载 --
int main(void) {
    SPI_Flash_Init();

    // 首次使用需要格式化
    int err = lfs_mount(&lfs, &cfg);
    if (err) {
        lfs_format(&lfs, &cfg);
        lfs_mount(&lfs, &cfg);
    }

    // 创建文件并写入
    lfs_file_t file;
    lfs_file_open(&lfs, &file, "config.json",
                  LFS_O_WRONLY | LFS_O_CREAT);
    lfs_file_write(&lfs, &file,
                   "{\"ssid\":\"MyWiFi\"}", 17);
    lfs_file_close(&lfs, &file);

    // 读取文件
    char buf[64] = {0};
    lfs_file_open(&lfs, &file, "config.json", LFS_O_RDONLY);
    lfs_size_t n = lfs_file_read(&lfs, &file, buf, sizeof(buf));
    lfs_file_close(&lfs, &file);

    // 目录列表
    lfs_dir_t dir;
    lfs_dir_open(&lfs, &dir, "/");
    struct lfs_info info;
    while (lfs_dir_read(&lfs, &dir, &info) > 0) {
        // info.type: LFS_TYPE_REG 或 LFS_TYPE_DIR
        // info.name: 文件/目录名
        // info.size: 文件大小
    }
    lfs_dir_close(&lfs, &dir);

    return 0;
}
```

## 11 常见问题

### 11.1 Flash 容量对齐

`block_count * block_size` 必须等于 Flash 分配给 LittleFS 的容量。如果不匹配, 可能读到错误地址或越界。建议在初始化时用 `assert` 校验。

### 11.2 线程安全

LittleFS 本身不是线程安全的。在 RTOS 环境中, 需要用互斥锁保护文件系统操作:

```c
lfs_mutex_t fs_mutex;

int mutex_lock(const struct lfs_config *c) {
    osMutexAcquire(fs_mutex, osWaitForever);
    return 0;
}

int mutex_unlock(const struct lfs_config *c) {
    osMutexRelease(fs_mutex);
    return 0;
}

// 在 cfg 中注册
cfg.lock   = mutex_lock;
cfg.unlock = mutex_unlock;
```

### 11.3 写放大

COW 机制意味着修改 1 字节可能需要擦除并重写整个块。优化方法:
- 使用 inline file 存小文件 (自动)
- 合并多次小写入为一次大写入
- 调大 `prog_size` 以匹配 Flash 页大小

### 11.4 长文件名与路径深度

LittleFS 默认文件名长度受限 (取决于 `name_max` 配置), 路径深度也受 `metadata pair` 递归限制。嵌入式场景建议文件名简短 (8.3 格式), 目录层级不超过 4 层。

### 11.5 多分区支持

LittleFS 支持在同一 Flash 上创建多个分区:
- 每个分区独立的 `lfs_t` 实例和 `lfs_config`
- 不同分区可以使用不同的块范围
- 典型用法: 一个分区存 OTA 固件, 另一个存配置和数据
- 注意: 分区间不共享磨损均衡, 各自管理各自的块池

### 11.6 调试技巧

LittleFS 提供了几个有用的调试接口:

- `lfs_fs_stat()`: 返回文件系统统计信息 (已用块数、文件数等)
- `lfs_fs_traverse()`: 遍历所有正在使用的块, 用于一致性检查
- `LFS_TRACE` 宏: 编译时启用, 打印每次 Flash 操作的日志
- `lfs_fs_size()`: 获取文件系统已使用的存储空间大小

建议在开发阶段启用 `LFS_ASSERT` 宏, 可以在参数错误时立即捕获问题, 而不是静默返回错误码。

## 总结

LittleFS 是当前 MCU Flash 上最实用的文件系统之一。它的三大核心能力 -- 掉电安全、磨损均衡、有界资源占用 -- 直接解决了嵌入式场景的痛点。移植只需实现 4 个回调函数, 就能在 STM32 内部 Flash 或外部 SPI Flash 上获得完整的文件操作能力。相比已弃用的 SPIFFS, LittleFS 支持目录且更安全; 相比 FatFS, LittleFS 自带磨损均衡且 RAM 占用恒定。新项目首选 LittleFS。

## 参考文献

1. ARM mbed. LittleFS: A fail-safe filesystem designed for microcontrollers. https://github.com/littlefs-project/littlefs
2. G. Nitz. LittleFS: A high-integrity embedded filesystem. ARM mbed Developer Conference, 2017.
3. IEEE. Standard for NOR Flash Memory Interface. IEEE Std 1003.1-2017.
4. Winbond. W25Q Serial Flash Memory Datasheet, Revision K, 2023.
5. STMicroelectronics. STM32 HAL Flash Driver Documentation, RM0433.
