# 嵌入式数据日志环形缓冲区与Flash写入
> **难度**：🟢 初级 | **领域**：数据存储策略 | **阅读时间**：约 18 分钟

## 引言

想象一条环形跑道: 运动员跑完一圈回到起点, 继续跑就覆盖之前的脚印。环形缓冲区 (Ring Buffer) 就是这样的"数据跑道" -- 数据写满一圈后回到开头, 覆盖最旧的数据。在 IoT 设备中, 传感器源源不断地产出数据, 存储空间却有限, 环形缓冲区让"新数据覆盖旧数据"变成一种有序可控的策略, 而不是混乱的覆盖。

## 1 IoT 数据日志需求

### 1.1 数据类型

IoT 设备通常需要记录三类数据:

| 数据类型 | 示例 | 特点 |
|----------|------|------|
| 传感器数据 | 温度、湿度、加速度 | 周期性产生, 数据量稳定 |
| 事件日志 | 报警触发、状态切换 | 非周期, 需要时间戳 |
| 诊断记录 | 异常堆栈、看门狗复位 | 偶发, 数据量不定 |

### 1.2 核心需求

- **顺序写入为主**: 数据追加写入, 极少随机修改
- **断电不丢失**: 设备可能随时掉电, 已写入的数据必须可恢复
- **容量有限**: Flash 空间通常在几百 KB 到几 MB
- **写入耐久性**: Flash 有擦写次数限制 (1万-10万次), 需要均衡磨损

## 2 环形缓冲区原理

### 2.1 基本概念

环形缓冲区使用一块固定大小的连续存储区, 维护两个指针:

- **head (写指针)**: 指向下一个写入位置, 数据写入后前移
- **tail (读指针)**: 指向下一个读取位置, 数据读出后前移

当指针到达缓冲区末尾时, 回绕到开头 (取模运算), 形成"环形"效果。

### 2.2 满与空的判断

关键问题: head == tail 时是满还是空? 两种常见方案:

1. **计数器法**: 维护一个元素计数, 0 为空, 等于容量为满
2. **留空法**: 缓冲区总留一个空位, (head+1) % size == tail 为满, head == tail 为空

```
空:  [ | | | | ]       满:  [A|B|C|D| ]  (留空法)
     ^head^tail              tail^    ^head
```

### 2.3 覆盖策略

当缓冲区满时, 选择:
- **丢弃新数据**: 保留旧数据, 适用于历史分析场景
- **覆盖最旧数据**: head 推进时同步推进 tail, 适用于实时监控场景 (IoT 更常用)

## 3 RAM 环形缓冲区实现

### 3.1 定长条目

RAM 环形缓冲区适合定长条目, 简化指针管理:

```c
#define BUF_SIZE 256
#define ENTRY_SIZE 8  // 每条记录 8 字节

typedef struct {
    uint8_t data[BUF_SIZE][ENTRY_SIZE];
    volatile uint16_t head;
    volatile uint16_t tail;
    volatile uint16_t count;
} RingBuffer;

void rb_init(RingBuffer *rb) {
    rb->head  = 0;
    rb->tail  = 0;
    rb->count = 0;
}

// 写入一条记录 (覆盖最旧)
void rb_push(RingBuffer *rb, const uint8_t *entry) {
    memcpy(rb->data[rb->head], entry, ENTRY_SIZE);
    rb->head = (rb->head + 1) % BUF_SIZE;
    if (rb->count == BUF_SIZE) {
        // 满: 覆盖最旧, tail 跟进
        rb->tail = (rb->tail + 1) % BUF_SIZE;
    } else {
        rb->count++;
    }
}

// 读取一条记录
int rb_pop(RingBuffer *rb, uint8_t *entry) {
    if (rb->count == 0) return -1; // 空
    memcpy(entry, rb->data[rb->tail], ENTRY_SIZE);
    rb->tail = (rb->tail + 1) % BUF_SIZE;
    rb->count--;
    return 0;
}
```

### 2.2 回绕逻辑要点

- 所有指针运算都取模: `(ptr + 1) % SIZE`
- 中断中写入 + 主循环读取时, `head` 和 `count` 需声明为 `volatile`
- 多线程访问需要关中断或加锁保护

## 4 Flash 写入的挑战

### 4.1 擦除后才能写入

Flash 的物理特性: 必须先擦除整个扇区 (sector), 才能写入新数据。不能像 RAM 那样直接覆盖已有数据。擦除粒度通常为 4KB。

### 4.2 扇区粒度操作

擦除以扇区为单位, 但写入可以按页 (256 字节) 或更小单位。这意味着修改一个扇区中的任何数据, 都需要擦除整个扇区并重写所有内容。

### 4.3 有限的擦写寿命

NOR Flash 典型寿命为 10 万次擦写, NAND Flash 为 1-3 万次。频繁擦除同一扇区会导致该扇区提前失效。

## 5 基于 Flash 的环形日志设计

### 5.1 扇区轮转

将 Flash 日志区域划分为 N 个扇区, 顺序使用:

```
[Sector 0] [Sector 1] [Sector 2] [Sector 3] ...
  当前写入 ->                      最早数据
```

写满当前扇区后, 擦除并使用下一个扇区。到达末尾后回绕到开头, 形成环形。

### 5.2 写指针追踪

维护一个持久化的写指针, 记录当前写入位置:

```c
typedef struct {
    uint32_t sector;       // 当前写入扇区号
    uint32_t offset;       // 扇区内偏移
    uint32_t seq;          // 全局序列号 (单调递增)
} WritePointer;
```

写指针本身也需要掉电安全存储 -- 通常放在每个扇区的头部。

### 5.3 序列号与恢复

每个扇区头部记录一个序列号 (sequence number)。设备上电时, 扫描所有扇区的序列号, 序列号最大的就是最新写入位置。这保证了即使写指针丢失, 也能恢复。

```
Sector 0: seq=100 (旧)
Sector 1: seq=101 (较新)
Sector 2: seq=102 (最新) <-- 写指针恢复到这里
Sector 3: seq=99  (更旧)
```

## 6 头部与元数据设计

### 6.1 扇区头部结构

每个扇区开头存储头部信息, 用于数据校验和恢复:

```c
#define SECTOR_MAGIC 0x4C4F4731  // "LOG1"

typedef struct {
    uint32_t magic;        // 魔数, 用于识别有效扇区
    uint32_t seq;          // 序列号, 单调递增
    uint32_t timestamp;    // 首条记录的时间戳
    uint16_t entry_count;  // 扇区内已写入条目数
    uint16_t flags;        // 状态标志 (可擦除/已上传等)
    uint32_t crc;          // 头部 CRC 校验
} SectorHeader;            // 固定大小, 对齐到 Flash 页
```

### 6.2 条目格式

每条日志记录包含:

| 字段 | 大小 | 说明 |
|------|------|------|
| timestamp | 4 字节 | Unix 时间戳或相对时间 |
| type | 1 字节 | 数据类型 (传感器/事件/诊断) |
| length | 2 字节 | 负载数据长度 |
| payload | 变长 | 实际数据 |
| crc | 2 字节 | 条目 CRC |

### 6.3 CRC 校验

CRC 保证数据完整性。上电扫描时跳过 CRC 不通过的条目, 防止读取到断电时写入了一半的脏数据。

## 7 断电恢复

### 7.1 启动时扫描

设备上电后的恢复流程:

1. 读取所有日志扇区的头部
2. 校验每个头部的 CRC, 跳过损坏的
3. 找到序列号最大的扇区 -- 即最新扇区
4. 在最新扇区内, 逐条扫描条目, 校验 CRC, 找到最后一条有效条目
5. 恢复写指针到该位置

### 7.2 处理部分写入

断电可能发生在:
- 写条目数据的过程中: CRC 校验失败, 丢弃该条目
- 擦除扇区的过程中: 整个扇区数据丢失, 序列号缺失, 依赖相邻扇区推断
- 写扇区头部的过程中: 头部 CRC 失败, 视为空扇区

关键原则: **数据宁可丢弃, 不可使用损坏数据**。

## 8 磨损分布

### 8.1 自然磨损均衡

环形日志的顺序写入特性天然实现磨损均衡: 每个扇区轮流使用, 擦写次数接近均匀。

### 8.2 避免热点

注意不要在固定位置频繁更新元数据 (如写指针)。如果每次写入都更新同一个 Flash 位置的写指针, 该位置会成为磨损热点。解决方案:
- 将写指针信息随当前写入位置一起存储 (每个扇区头部自带序列号)
- 使用 RAM 缓存写指针, 仅在关键时机持久化

### 8.3 扇区数量与寿命估算

假设 Flash 有 N 个日志扇区, 每秒写入 M 条记录, 每条 S 字节, 扇区大小为 B 字节:

```
扇区写满时间 = B / (M * S) 秒
单扇区擦写频率 = 1 / (N * B / (M * S))
寿命 = 100000 / 擦写频率 秒
```

例如: 8 个 4KB 扇区, 每秒写 1 条 16 字节记录:
- 扇区写满时间 = 4096 / 16 = 256 秒
- 单扇区周期 = 8 * 256 = 2048 秒
- 寿命 = 100000 * 2048 = 约 6.5 年

## 9 容量规划

### 9.1 关键参数

| 参数 | 说明 | 计算 |
|------|------|------|
| 条目大小 | 单条记录字节数 | 头部 + 负载 + CRC |
| 日志频率 | 每秒产生条目数 | 传感器采样率 |
| 保留时间 | 需要保存多少历史数据 | 业务需求 |
| Flash 大小 | 分配给日志的容量 | 硬件约束 |

### 9.2 计算示例

需求: 每秒 1 条传感器数据, 每条 20 字节, 保留 7 天:

```
日数据量 = 1 * 20 * 86400 = 1,728,000 字节/天
7 天总量 = 1,728,000 * 7 = 12,096,000 字节 (约 11.5 MB)
```

如果 Flash 只有 1 MB, 需要降低频率或缩短保留时间, 或者使用压缩。

## 10 Flash 环形缓冲区实现

```c
#define LOG_SECTOR_SIZE  4096
#define LOG_SECTOR_COUNT 8
#define LOG_BASE_ADDR    0x000000

#define HDR_MAGIC  0x4C4F4731
#define HDR_SIZE   32  // SectorHeader 对齐到 32 字节

static uint32_t current_sector = 0;
static uint32_t current_offset = HDR_SIZE;
static uint32_t global_seq    = 0;

// 初始化: 扫描扇区找最新位置
void log_init(void) {
    uint32_t max_seq = 0;
    for (int i = 0; i < LOG_SECTOR_COUNT; i++) {
        SectorHeader hdr;
        flash_read(LOG_BASE_ADDR + i * LOG_SECTOR_SIZE,
                   &hdr, sizeof(hdr));
        if (hdr.magic == HDR_MAGIC && hdr.seq >= max_seq) {
            max_seq = hdr.seq;
            current_sector = i;
        }
    }
    global_seq = max_seq;
    // 扫描当前扇区找最后有效条目
    current_offset = scan_for_last_entry(current_sector);
}

// 写入一条日志
int log_write(uint8_t type, const void *data, uint16_t len) {
    // 检查当前扇区剩余空间
    uint16_t entry_size = 4 + 1 + 2 + len + 2; // ts+type+len+payload+crc
    if (current_offset + entry_size > LOG_SECTOR_SIZE) {
        // 切换到下一扇区
        current_sector = (current_sector + 1) % LOG_SECTOR_COUNT;
        current_offset = HDR_SIZE;
        global_seq++;

        // 擦除新扇区并写头部
        flash_erase(LOG_BASE_ADDR + current_sector * LOG_SECTOR_SIZE);
        SectorHeader hdr = {
            .magic = HDR_MAGIC,
            .seq   = global_seq,
            .timestamp = get_timestamp(),
            .entry_count = 0,
            .flags = 0,
        };
        hdr.crc = crc32(&hdr, sizeof(hdr) - 4);
        flash_write(LOG_BASE_ADDR + current_sector * LOG_SECTOR_SIZE,
                    &hdr, sizeof(hdr));
    }

    // 写入条目
    uint32_t addr = LOG_BASE_ADDR
                  + current_sector * LOG_SECTOR_SIZE
                  + current_offset;
    uint8_t buf[entry_size];
    // 组装: timestamp(4) + type(1) + length(2) + payload + crc(2)
    uint32_t ts = get_timestamp();
    memcpy(buf, &ts, 4);
    buf[4] = type;
    memcpy(buf + 5, &len, 2);
    memcpy(buf + 7, data, len);
    uint16_t crc = crc16(buf, 7 + len);
    memcpy(buf + 7 + len, &crc, 2);

    flash_write(addr, buf, entry_size);
    current_offset += entry_size;
    return 0;
}
```

## 11 与 LittleFS 集成 vs 裸 Flash 访问

### 11.1 使用 LittleFS

优点:
- 代码简洁, `fopen/fwrite/fclose` 即可
- 磨损均衡和掉电安全由文件系统处理
- 支持目录分类 (按日期或类型)

缺点:
- 写放大: 修改日志文件元数据产生额外 Flash 写入
- 不适合高频小数据写入场景

### 11.2 裸 Flash 访问

优点:
- 零写放大, 每字节写入都直接到 Flash
- 完全可控的扇区管理
- 最低 RAM 和 ROM 占用

缺点:
- 需要自己实现磨损均衡和断电恢复
- 代码复杂度较高

### 11.3 混合策略

实际项目常采用混合方案:
- 配置文件和 OTA 数据用 LittleFS 管理
- 高频日志数据用裸 Flash 环形缓冲区
- 两者使用不同 Flash 区域, 互不干扰

## 12 压缩延长容量

### 12.1 增量编码 (Delta Encoding)

对于缓慢变化的传感器数据, 只存储与前一值的差值:

```c
// 原始: 25.3, 25.4, 25.4, 25.5, 25.6
// 增量: 25.3, +0.1, +0.0, +0.1, +0.1
// 存储: 1 字节浮点 + 1 字节有符号增量 (vs 4 字节浮点)
```

压缩比约 2-4x, 适合温度、湿度等缓变物理量。

### 12.2 简单 RLE (Run-Length Encoding)

连续相同值压缩为 (值, 重复次数):

```c
// 原始: A A A A B B C C C C C
// RLE:  A 4 B 2 C 5
```

适合开关量、状态码等离散值场景。

### 12.3 注意事项

- 压缩增加计算开销, 需评估 MCU 算力
- 断电时压缩中间状态可能无法恢复, 建议按条目独立压缩
- 读取时需要解压, 影响回放速度

## 13 上传与清除策略

### 13.1 标记已上传

日志数据上传到云端后, 将对应扇区标记为"已上传":

```c
// 在扇区头部 flags 中设置标志
hdr.flags |= FLAG_UPLOADED;
flash_write(sector_addr + offsetof(SectorHeader, flags),
            &hdr.flags, sizeof(hdr.flags));
```

### 13.2 擦除已上传扇区

已上传的扇区在环形写指针回绕到该位置时自动被擦除重用。也可以在空闲时主动擦除, 提前释放空间。

### 13.3 上传策略选择

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| 实时上传 | 数据产生即上传 | 网络稳定, 功耗不敏感 |
| 批量上传 | 积累到一定量后上传 | 网络不稳定, 低功耗 |
| 定时上传 | 每小时/每天上传 | 数据量小, 对实时性要求低 |

## 总结

Flash 环形缓冲区是 IoT 设备数据日志的经典方案。核心设计要点: 扇区轮转实现环形写入, 序列号实现断电恢复, CRC 校验保证数据完整性, 自然轮转实现磨损均衡。容量规划需要根据条目大小、日志频率和保留时间计算。与 LittleFS 相比, 裸 Flash 方案零写放大, 适合高频写入场景, 但需要自行处理断电恢复。增量编码和 RLE 压缩可以有效延长存储容量。上传策略根据网络条件和功耗需求选择实时、批量或定时方案。

## 参考文献

1. J. Axelson. USB Mass Storage: Designing and Programming Devices and Embedded Hosts. Lakeview Research, 2006.
2. MTD Subsystem Documentation. Linux Kernel Documentation, Flash-based circular log design.
3. Zephyr Project. Flash Map API and Circular Buffer Implementation. Zephyr RTOS Documentation.
4. STMicroelectronics. AN4894: How to use the external flash memory with STM32. Application Note, 2022.
5. JEDEC Standard. JESD84-B51: Embedded Multi-Media Card (eMMC), 2021.
