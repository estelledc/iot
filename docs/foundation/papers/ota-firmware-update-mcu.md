---
schema_version: '1.0'
id: ota-firmware-update-mcu
title: MCU OTA固件更新机制与双Bank设计
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
# MCU OTA固件更新机制与双Bank设计
> **难度**：🟡 中级 | **领域**：固件更新架构 | **阅读时间**：约 20 分钟

## 引言

想象你的手机系统出了个Bug，如果不支持在线更新，你就得去售后排队刷机。IoT设备也是一样——部署在客户现场的上万台设备，如果没有OTA(Over-The-Air)更新能力，每次修Bug都需要派人上门或者召回设备，成本远超BOM本身。

OTA不是"锦上添花"的功能，而是IoT产品的"基础设施"。本文从Flash布局、双Bank设计、安全验签到差分更新，系统讲解MCU上的OTA实现。

## 1. OTA的重要性

### 1.1 为什么IoT设备必须支持OTA

| 场景 | 无OTA | 有OTA |
|------|-------|-------|
| 修复Bug | 派人或召回，成本高 | 远程推送，零边际成本 |
| 添加功能 | 无法升级 | 持续演进 |
| 安全补丁 | 漏洞长期暴露 | 快速响应 |
| 合规变更 | 重新认证后停产换新 | 软件更新即可 |

### 1.2 OTA的成本收益

假设1万台设备，每次现场更新的成本：

- 派工费用：200元/台 x 10000 = 200万元
- OTA推送：服务器带宽费用约2000元

一次OTA更新节省近200万元。对百万级出货量，这个差距更加悬殊。

## 2. OTA架构概览

### 2.1 端到端流程

```
[云端服务器] --(发布新固件)--> [传输通道] --(下载)--> [设备Bootloader]
                                                        |
                                            [写入Flash暂存区]
                                                        |
                                            [校验+验签]
                                                        |
                                            [切换启动分区]
                                                        |
                                            [运行新固件]
```

### 2.2 各层职责

| 层级 | 职责 | 关键技术 |
|------|------|----------|
| 云端 | 固件管理、版本分发、灰度发布 | CDN、版本策略 |
| 传输 | 可靠传输、断点续传 | HTTPS/CoAP/MQTT |
| 设备端 | 下载、校验、切换、回滚 | Bootloader、双Bank |

## 3. Flash存储布局

### 3.1 典型分区设计

```
0x0800_0000 +-------------------+
            |    Bootloader     |  16KB - 32KB
0x0800_8000 +-------------------+
            |    Partition Table |  4KB
0x0800_9000 +-------------------+
            |    Bank A (Active) |  200KB - 500KB
0x0803_B000 +-------------------+
            |    Bank B (Staging)|  200KB - 500KB
0x0806_D000 +-------------------+
            |    NVS / Config    |  16KB - 32KB
0x0807_5000 +-------------------+
            |    Reserved        |
0x0808_0000 +-------------------+  (Flash末尾)
```

### 3.2 各分区说明

| 分区 | 用途 | 修改频率 |
|------|------|----------|
| Bootloader | 启动逻辑、OTA切换 | 极少(仅出厂烧录) |
| Partition Table | 分区偏移和大小定义 | 极少 |
| Bank A / Bank B | 固件本体 | 每次OTA更新 |
| NVS | 设备配置、WiFi凭据、校准值 | 偶尔 |

## 4. 单Bank vs 双Bank

### 4.1 单Bank方案

```
[Bootloader] [Firmware] [Staging] [NVS]

流程:
1. 下载新固件到Staging区
2. 重启进入Bootloader
3. Bootloader将Staging复制到Firmware区
4. 校验成功则启动新固件
```

**风险**：复制过程中如果断电，Firmware区数据不完整，设备变砖。

### 4.2 双Bank方案

```
[Bootloader] [Bank A] [Bank B] [NVS]

流程:
1. 下载新固件到非活动Bank(如Bank B)
2. 校验+验签通过
3. 修改启动标志指向Bank B
4. 重启后Bootloader从Bank B启动
5. 如果新固件运行正常，确认更新
6. 如果异常，回滚到Bank A
```

**优势**：

- 断电安全：写入过程中断电不影响活动Bank
- 即时回滚：只需切换Bank指针
- 原子性：更新要么完全成功，要么完全不变

### 4.3 两种方案对比

| 项目 | 单Bank | 双Bank |
|------|--------|--------|
| Flash需求 | 较少(无需双倍固件空间) | 较多(2倍固件空间) |
| 断电安全性 | 不安全 | 安全 |
| 回滚速度 | 慢(需重新复制) | 快(切换指针) |
| 适用场景 | Flash紧张的低成本产品 | 大多数IoT产品 |

## 5. 双Bank实现细节

### 5.1 A/B分区

两个Bank大小相同，结构相同：

```c
typedef struct {
    uint32_t bank_addr;      // Bank起始地址
    uint32_t bank_size;      // Bank大小
    uint8_t  active;         // 0: Bank A, 1: Bank B
} ota_bank_t;

ota_bank_t banks[2] = {
    { 0x0800_9000, 0x0003_2000, 1 },  // Bank A, 当前活跃
    { 0x0803_B000, 0x0003_2000, 0 },  // Bank B, 待更新
};
```

### 5.2 版本元数据

每个Bank头部存储固件元信息：

```c
typedef struct __attribute__((packed)) {
    uint32_t magic;          // 魔数: 0x4F544131 ("OTA1")
    uint32_t version;        // 固件版本: 0xMMmmPP (主.次.补丁)
    uint32_t image_size;     // 固件有效长度
    uint8_t  sha256[32];     // SHA256校验和
    uint8_t  signature[64]; // ECDSA签名
    uint32_t boot_count;     // 启动计数(用于自动回滚)
    uint32_t boot_confirm;   // 确认标志(0x54455354 = "TEST")
} ota_image_header_t;
```

### 5.3 启动标志与计数器

```
启动流程:
1. Bootloader读取Bank A的boot_count
2. 如果boot_count > MAX_BOOT_COUNT且未confirm -> 回滚到Bank B
3. 否则boot_count++, 启动Bank A
4. 应用程序正常运行后调用ota_confirm()确认
5. 确认后boot_count清零, 更新成功
```

## 6. 固件镜像格式

### 6.1 镜像头

```
+-------------------+
| Magic (4B)        |  镜像标识
+-------------------+
| Version (4B)      |  版本号
+-------------------+
| Size (4B)         |  有效负载长度
+-------------------+
| SHA256 (32B)      |  完整性校验
+-------------------+
| Signature (64B)   |  ECDSA签名
+-------------------+
| Payload (N KB)    |  固件二进制
+-------------------+
```

### 6.2 压缩 vs 原始

| 方式 | 下载大小 | Flash占用 | 解压时间 |
|------|----------|-----------|----------|
| 原始二进制 | 100% | 1:1 | 无 |
| LZMA压缩 | 40-50% | 1:1(解压到Bank) | 1-3秒 |
| 差分更新 | 10-20% | 仅差异部分 | 需原镜像 |

## 7. 下载协议

### 7.1 HTTPS分块下载

最常用的OTA下载方式：

```c
// HTTPS分块下载示例
int ota_download_https(const char *url, uint8_t *bank_addr) {
    http_client_t client;
    http_client_init(&client);
    http_client_set_header(&client, "X-Device-ID", device_id);
    http_client_set_header(&client, "X-FW-Version", current_version);

    int ret = http_client_get(&client, url);
    if (ret != 200) return -1;

    uint32_t offset = 0;
    uint8_t buf[4096];
    int bytes;
    while ((bytes = http_client_read(&client, buf, sizeof(buf))) > 0) {
        flash_write(bank_addr + offset, buf, bytes);
        offset += bytes;
    }
    http_client_cleanup(&client);
    return offset;
}
```

### 7.2 其他传输方式

| 协议 | 场景 | 特点 |
|------|------|------|
| HTTPS | Wi-Fi/Ethernet设备 | 最通用，支持断点续传 |
| CoAP Block | NB-IoT/LoRa设备 | 轻量，适合低带宽 |
| BLE DFU | BLE设备 | 蓝牙专用更新协议 |
| MQTT Binary | MQTT设备 | 复用现有MQTT连接 |

## 8. 完整性校验

### 8.1 三层校验体系

| 层级 | 算法 | 检测能力 | 计算成本 |
|------|------|----------|----------|
| 损坏检测 | CRC32 | 传输/写入中的比特翻转 | 极低(硬件加速) |
| 完整性验证 | SHA256 | 任何数据篡改 | 中(需软件实现) |
| 真实性验证 | ECDSA-P256 | 伪造固件 | 高(非对称运算) |

### 8.2 校验流程

```
1. 下载完成 -> 计算CRC32 -> 比对镜像头中的CRC
   不匹配: 丢弃, 重新下载

2. CRC通过 -> 计算SHA256 -> 比对镜像头中的SHA256
   不匹配: 丢弃, 报告错误

3. SHA256通过 -> 用公钥验证ECDSA签名
   不通过: 丢弃, 报告安全事件
```

### 8.3 SHA256实现

```c
// SHA256校验示例
int verify_sha256(const uint8_t *data, size_t len,
                  const uint8_t expected[32]) {
    uint8_t computed[32];
    mbedtls_sha256_context ctx;
    mbedtls_sha256_init(&ctx);
    mbedtls_sha256_starts(&ctx, 0);  // SHA-256
    mbedtls_sha256_update(&ctx, data, len);
    mbedtls_sha256_finish(&ctx, computed);
    mbedtls_sha256_free(&ctx);
    return memcmp(computed, expected, 32) == 0 ? 0 : -1;
}
```

## 9. 回滚机制

### 9.1 启动计数器

核心思路：新固件必须在N次启动内"报到确认"，否则视为异常，自动回滚。

```c
#define MAX_BOOT_COUNT  3

void bootloader_check_rollback(void) {
    ota_image_header_t *active = get_active_bank_header();

    if (active->boot_confirm == CONFIRM_VALUE) {
        return;  // 已确认, 正常启动
    }

    active->boot_count++;
    flash_write_header(active);

    if (active->boot_count > MAX_BOOT_COUNT) {
        // 新固件多次启动未确认, 回滚
        switch_to_previous_bank();
        system_reset();
    }
}
```

### 9.2 应用程序确认

```c
// 新固件正常运行后必须调用
void ota_confirm_update(void) {
    ota_image_header_t *active = get_active_bank_header();
    active->boot_confirm = CONFIRM_VALUE;
    active->boot_count = 0;
    flash_write_header(active);
}
```

### 9.3 回滚触发条件

| 条件 | 说明 |
|------|------|
| 启动计数超限 | 新固件启动N次未确认 |
| 看门狗复位 | 新固件导致连续看门狗复位 |
| 应用程序主动回滚 | 检测到不兼容，主动请求回滚 |
| 手动回滚 | 用户/运维人员触发 |

## 10. 差分/增量更新

### 10.1 原理

只传输新旧固件之间的差异部分：

```
旧固件: v1.0.0 (200KB)
新固件: v1.1.0 (202KB)
差异包: bsdiff(v1, v2) = 18KB  (仅9%!)

设备端:
1. 读取当前Bank的旧固件
2. 接收差异包
3. 本地合成新固件: bspatch(old + diff = new)
4. 校验新固件
5. 写入非活动Bank
```

### 10.2 差分算法对比

| 算法 | 差异包大小 | 合成内存 | 合成速度 |
|------|-----------|----------|----------|
| bsdiff | 最小 | 需2倍固件大小 | 中 |
| hdiffpatch | 较小 | 需1倍固件大小 | 快 |
| VCDIFF(RFC 3284) | 中 | 需1倍固件大小 | 快 |

### 10.3 差分更新的限制

- 必须知道设备当前运行的精确版本
- 需要足够的RAM来合成新固件
- 跨大版本差异时差异包可能接近全量
- 需要在设备端实现patch算法

## 11. 实战案例：ESP32 OTA

### 11.1 分区表

```
# Name,    Type, SubType, Offset,   Size
nvs,       data, nvs,    0x9000,   0x4000
otadata,   data, ota,    0xd000,   0x2000
phy_init,  data, phy,    0xf000,   0x1000
ota_0,     app,  ota_0,  0x10000,  0x1E0000
ota_1,     app,  ota_1,  0x1F0000, 0x1E0000
```

### 11.2 OTA API使用

```c
#include "esp_ota_ops.h"

void ota_task(void *pvParameter) {
    esp_ota_handle_t update_handle = 0;
    const esp_partition_t *update_part =
        esp_ota_get_next_update_partition(NULL);

    // 开始OTA
    esp_ota_begin(update_part, OTA_SIZE_UNKNOWN, &update_handle);

    // 分块写入(通常从HTTPS下载)
    while (1) {
        int data_len = http_download_chunk(buf, sizeof(buf));
        if (data_len <= 0) break;
        esp_ota_write(update_handle, buf, data_len);
    }

    // 结束并校验
    esp_err_t err = esp_ota_end(update_handle);
    if (err != ESP_OK) {
        printf("OTA end failed: %s\n", esp_err_to_name(err));
        return;
    }

    // 设置启动分区
    esp_ota_set_boot_partition(update_part);
    printf("OTA success, restarting...\n");
    esp_restart();
}
```

## 12. 安全考量

### 12.1 签名镜像

- 固件必须用私钥签名，设备用公钥验证
- 私钥绝不离开构建服务器
- 公钥烧录在设备出厂时(Bootloader中)

### 12.2 加密传输

- 下载通道必须加密(HTTPS/TLS)
- 固件本身也可以加密，设备端解密后写入Flash
- 防止中间人篡改和窃取固件

### 12.3 反回滚计数器

使用eFuse中的硬件计数器防止降级攻击：

```c
// 简化的反回滚检查
bool anti_rollback_check(uint32_t new_version) {
    uint32_t efuse_min_version = read_efuse_rollback_counter();
    if (new_version < efuse_min_version) {
        printf("Anti-rollback: rejected v%d < min v%d\n",
               new_version, efuse_min_version);
        return false;
    }
    return true;
}
```

每次安全更新后，烧录eFuse计数器到新版本号。eFuse不可逆，因此攻击者无法将固件降级到有已知漏洞的版本。

## 13. 常见失败模式

### 13.1 写入过程中断电

**症状**：设备变砖，不响应任何指令。

**预防**：使用双Bank设计，写入非活动Bank，确认后才切换。

### 13.2 Flash空间不足

**症状**：写入到一半报错，新固件无法完整写入。

**预防**：编译时检查固件大小是否超过Bank容量；差分更新时验证合成后的镜像大小。

### 13.3 版本不兼容

**症状**：新固件启动后外设不工作，配置格式不匹配。

**预防**：版本号中包含NVS结构版本；不兼容时自动回滚。

### 13.4 网络中断导致下载不完整

**症状**：校验失败，OTA中止。

**预防**：支持断点续传；记录已下载的偏移量，重连后从断点继续。

## 总结

OTA固件更新是IoT产品的核心基础设施，设计时需关注：

1. Flash布局：双Bank是安全更新的基础，多花一倍Flash空间换来断电安全和即时回滚
2. 校验体系：CRC检测损坏，SHA256验证完整性，ECDSA确认来源可信
3. 回滚机制：启动计数器+确认标志，确保新固件异常时自动恢复
4. 安全链路：签名镜像+加密传输+反回滚计数器，三层防护
5. 差分更新：大幅降低带宽需求和下载时间，但需权衡设备端RAM和CPU开销

一句话：OTA不是"能更新就行"，而是"更新失败也不能变砖"。

## 参考文献

1. Espressif. "ESP-IDF OTA Guide", 2023.
2. MCUboot Project. "MCUboot Secure Bootloader Documentation", 2022.
3. C. Percival. "bsdiff / bspatch: Binary Diff/Patch", 2003.
4. NIST SP 800-193. "Platform Firmware Resiliency", 2022.
5. RFC 9031. "Constrained Join Protocol (CoJP) for 6TiSCH", 2021.
