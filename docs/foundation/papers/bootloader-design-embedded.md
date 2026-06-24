# 嵌入式Bootloader设计与固件升级流程
> **难度**：🟡 中级 | **领域**：系统启动设计 | **阅读时间**：约 20 分钟

## 引言

想象一台电脑的开机过程：按下电源键后，屏幕先显示主板Logo(BIOS/UEFI在自检)，然后才进入操作系统。Bootloader就是嵌入式设备的"BIOS"——它是复位后第一段执行的代码，负责初始化最基础的硬件，然后决定是运行应用程序还是进入升级模式。

Bootloader虽小，但责任重大：它直接决定了设备能否启动、能否安全更新、能否从故障中恢复。一个可靠的Bootloader是整个系统稳定性的基石。

## 1. Bootloader的角色

### 1.1 什么是Bootloader

Bootloader是MCU上电复位后执行的第一段代码，核心职责：

| 职责 | 说明 |
|------|------|
| 硬件初始化 | 配置时钟、GPIO、UART等最基础外设 |
| 启动决策 | 决定进入应用程序还是升级模式 |
| 固件更新 | 接收新固件并写入Flash |
| 完整性校验 | 验证应用程序是否完整有效 |
| 跳转启动 | 将控制权交给应用程序 |

### 1.2 Bootloader vs 应用程序

| 特性 | Bootloader | 应用程序 |
|------|------------|----------|
| 代码量 | 小(4-32KB) | 大(64KB-数MB) |
| 更新频率 | 极少 | 频繁 |
| 复杂度 | 低(最小功能集) | 高(丰富功能) |
| 可靠性要求 | 极高(坏了设备变砖) | 高(可通过OTA修复) |
| 外设依赖 | 仅UART/Flash | 全部外设 |

核心原则：Bootloader只做必须做的事，越简单越可靠。

## 2. 启动流程

### 2.1 完整启动序列

```
MCU复位
    |
    v
[复位向量] -> 跳转到Bootloader入口
    |
    v
[Bootloader初始化]
  - 配置系统时钟
  - 初始化GPIO(LED指示)
  - 初始化UART(调试输出)
  - 初始化Flash控制器
    |
    v
[检查更新触发条件]
  - GPIO按键是否按下?
  - NVS中是否有更新标志?
  - 上次应用程序是否正常退出?
  - 是否超时未检测到有效应用?
    |
    +-- 有触发 --> [进入更新模式]
    |                  |
    |                  v
    |              [接收新固件]
    |                  |
    |                  v
    |              [写入Flash]
    |                  |
    |                  v
    |              [校验固件]
    |                  |
    |                  v
    |              [标记更新完成]
    |                  |
    +-- 无触发 -----+--+
                     |
                     v
              [校验应用程序]
              - 检查镜像头魔数
              - 验证CRC/SHA256
              - (可选)验证签名
                     |
                     +-- 校验失败 --> [进入更新模式或等待]
                     |
                     +-- 校验通过 --> [跳转到应用程序]
```

### 2.2 关键时序

| 阶段 | 典型耗时 | 说明 |
|------|----------|------|
| Bootloader初始化 | 10-50ms | 时钟配置、外设初始化 |
| 更新触发检测 | 1-100ms | 按键去抖或NVS读取 |
| 应用校验 | 50-500ms | SHA256计算依赖固件大小 |
| 跳转 | <1ms | 设置SP和PC |

## 3. 更新触发方式

### 3.1 GPIO按键

最简单直接的方式——用户按住特定按键上电：

```c
#define UPDATE_PIN  GPIO_PIN_0

bool check_gpio_trigger(void) {
    // 等待去抖
    HAL_Delay(50);
    return HAL_GPIO_ReadPin(GPIOA, UPDATE_PIN) == GPIO_PIN_RESET;
}
```

优点：不需要应用程序配合，任何时候都能触发。
缺点：需要物理接触，不适合远程更新。

### 3.2 应用程序设置标志

应用程序运行时检测到新固件可用，在NVS中写入标志然后重启：

```c
// 应用程序端
void request_ota_update(void) {
    nvs_write_u32("ota_request", OTA_FLAG_VALUE);
    NVIC_SystemReset();  // 软件复位
}

// Bootloader端
bool check_nvs_trigger(void) {
    uint32_t flag = nvs_read_u32("ota_request");
    if (flag == OTA_FLAG_VALUE) {
        nvs_write_u32("ota_request", 0);  // 清除标志
        return true;
    }
    return false;
}
```

### 3.3 超时检测

Bootloader启动后等待一段时间(如500ms)，如果应用程序未"报到"则进入更新模式：

```c
#define APP_CONFIRM_TIMEOUT_MS  500

bool check_timeout_trigger(void) {
    uint32_t start = get_tick();
    while ((get_tick() - start) < APP_CONFIRM_TIMEOUT_MS) {
        if (nvs_read_u32("app_confirmed") == CONFIRM_VALUE) {
            return false;  // 应用已确认, 不进入更新模式
        }
    }
    return true;  // 超时, 进入更新模式
}
```

## 4. 通信接口

### 4.1 UART/串口

最通用的更新接口：

| 优点 | 缺点 |
|------|------|
| 几乎所有MCU都有 | 速度有限(115200bps常见) |
| 协议简单 | 需要线缆连接 |
| 调试方便 | 不适合产品级OTA |

### 4.2 USB DFU

USB Device Firmware Upgrade是USB-IF标准协议：

- 标准设备类(DFU Class 0xFE, Subclass 01)
- 主机端有标准驱动(Windows/Linux/macOS)
- 速度比UART快得多(12Mbps Full Speed)

### 4.3 CAN总线

汽车和工业设备常用：

- 在CAN网络中远程更新节点
- UDS(ISO 14229)协议栈提供标准化的更新流程
- 支持多节点批量更新

### 4.4 接口选型建议

| 场景 | 推荐接口 |
|------|----------|
| 开发调试 | UART/SWD |
| 消费产品出厂烧录 | USB DFU |
| 汽车/工业现场 | CAN + UDS |
| 从主机处理器更新 | SPI/I2C |

## 5. 存储映射设计

### 5.1 典型内存布局

```
0x0800_0000 +-------------------+
            |   Bootloader      |  16KB (0x4000)
0x0800_4000 +-------------------+
            |   Application     |  200KB+
0x0803_6000 +-------------------+
            |   Shared Data     |  4KB
0x0803_7000 +-------------------+
            |   NVS / Config    |  4KB
0x0803_8000 +-------------------+  (Flash末尾, 以256KB为例)
```

### 5.2 共享数据区

Bootloader和应用程序之间的通信区域：

```c
// 共享数据结构(放在固定的Flash区域)
typedef struct __attribute__((packed)) {
    uint32_t magic;          // 魔数, 验证区域有效性
    uint32_t ota_flag;      // 0=正常启动, 1=请求OTA
    uint32_t ota_status;    // OTA状态: 进行中/成功/失败
    uint32_t app_version;   // 应用程序版本
    uint32_t boot_count;    // 启动计数(用于回滚判断)
} shared_data_t;

#define SHARED_DATA_ADDR  0x0803_6000
#define SHARED_MAGIC      0x5348_4152  // "SHAR"
```

### 5.3 地址规划原则

- Bootloader放在Flash起始地址(复位向量位置)
- 应用程序偏移必须对齐Flash页大小(STM32通常2KB)
- 共享数据区放在两者之间或固定位置
- 预留空间给将来扩展

## 6. 向量表重定位

### 6.1 为什么需要重定位

Cortex-M系列MCU复位后从0x0000_0000(或0x0800_0000)读取初始栈指针和复位向量。应用程序的中断向量表不在Flash起始位置，必须告诉MCU新的向量表地址。

### 6.2 SCB->VTOR设置

```c
// 应用程序启动时必须重定位向量表
#define APP_VECTOR_TABLE_ADDR  0x0800_4000

void app_init_vector_table(void) {
    // 设置VTOR指向应用程序向量表
    SCB->VTOR = APP_VECTOR_TABLE_ADDR;
    __DSB();  // 数据同步屏障
    __ISB();  // 指令同步屏障
}
```

### 6.3 重定位时机

应用程序的SystemInit()或main()最开头就要设置VTOR——在任何中断发生之前。否则第一个中断就会跳转到错误地址。

## 7. Bootloader安全性

### 7.1 验证应用程序签名

Bootloader在跳转前必须验证应用程序的完整性：

```c
bool verify_app_signature(const uint8_t *app_addr, size_t app_size) {
    // 1. 读取镜像头中的SHA256和签名
    const ota_image_header_t *hdr = (ota_image_header_t *)app_addr;

    // 2. 计算SHA256
    uint8_t computed_sha[32];
    sha256_compute(app_addr + sizeof(ota_image_header_t),
                   app_size, computed_sha);

    // 3. 比对SHA256
    if (memcmp(computed_sha, hdr->sha256, 32) != 0) return false;

    // 4. 验证ECDSA签名
    return ecdsa_verify(hdr->sha256, hdr->signature, public_key);
}
```

### 7.2 写保护Bootloader区域

防止应用程序意外或恶意修改Bootloader：

```c
// STM32 Flash写保护示例
void lock_bootloader_region(void) {
    // 设置WRP(Write Protection)位
    // 保护0x0800_0000 - 0x0800_3FFF (Bootloader区域)
    FLASH_OBProgramInitTypeDef ob;
    HAL_FLASHEx_OBGetConfig(&ob);
    ob.WRPState = OB_WRPSTATE_ENABLE;
    ob.WRPSector = OB_WRP_SECTOR_0;  // 保护Sector 0
    HAL_FLASHEx_OBProgram(&ob);
    HAL_FLASH_OBLaunch();  // 应用选项字节
}
```

### 7.3 安全启动链

```
[硬件Root of Trust]
    |
    v
[Bootloader验证] -- 验证应用程序签名
    |
    v
[应用程序验证] -- 验证OTA固件签名
    |
    v
[固件运行] -- 运行受信任的代码
```

每一层都验证下一层的完整性，形成信任链。

## 8. Bootloader体积优化

### 8.1 最小功能集

一个仅支持UART更新+Flash写入+CRC校验的Bootloader可以做到8KB以内：

| 功能 | 代码量 | 是否必需 |
|------|--------|----------|
| 时钟初始化 | 200B | 是 |
| GPIO初始化 | 100B | 是 |
| UART驱动 | 500B | 是 |
| Flash读写 | 800B | 是 |
| CRC32校验 | 300B | 是(可硬件加速) |
| XMODEM协议 | 1KB | 是 |
| 跳转逻辑 | 200B | 是 |
| 总计 | ~3KB | - |

### 8.2 优化技巧

- 使用硬件CRC外设代替软件CRC实现
- 不使用标准库(不用printf、malloc)
- 内联关键函数减少调用开销
- 使用查表法替代浮点运算

## 9. 实战案例：STM32自定义Bootloader

### 9.1 UART协议

使用XMODEM-1K协议传输固件：

```c
// 简化的XMODEM接收流程
int xmodem_receive(uint8_t *flash_addr) {
    uint8_t pkt_buf[1024 + 5];  // 数据 + 头 + 校验
    uint8_t pkt_num = 1;
    uint32_t offset = 0;

    // 发送'C'启动CRC模式
    uart_send_byte('C');

    while (1) {
        uint8_t sof = uart_recv_byte_timeout(1000);
        if (sof == EOT) {
            uart_send_byte(ACK);
            break;  // 传输完成
        }
        if (sof != STX) continue;  // 等待1K包

        // 读取包号、数据、CRC
        uart_recv(pkt_buf, 1024 + 5);

        // 校验CRC
        uint16_t crc = calc_crc16(pkt_buf + 2, 1024);
        if (crc != (pkt_buf[1026] << 8 | pkt_buf[1027])) {
            uart_send_byte(NAK);  // 校验失败, 重传
            continue;
        }

        // 写入Flash
        flash_write(flash_addr + offset, pkt_buf + 2, 1024);
        offset += 1024;
        uart_send_byte(ACK);
        pkt_num++;
    }
    return offset;
}
```

### 9.2 完整Bootloader主流程

```c
int main(void) {
    // 1. 硬件初始化
    SystemInit();
    GPIO_Init();
    UART_Init();
    Flash_Init();

    // 2. 检查更新触发
    if (check_gpio_trigger() || check_nvs_trigger()) {
        led_on();  // 指示更新模式
        printf("Entering update mode...\r\n");

        // 3. 接收新固件
        int size = xmodem_receive(APP_FLASH_ADDR);
        if (size <= 0) {
            printf("Update failed!\r\n");
            while(1);  // 等待人工处理
        }

        // 4. 校验固件
        if (verify_crc32(APP_FLASH_ADDR, size) != 0) {
            printf("CRC check failed!\r\n");
            while(1);
        }

        printf("Update success! Size: %d\r\n", size);
        // 更新标志清除
        clear_ota_flag();
    }

    // 5. 校验应用程序
    if (verify_app_magic(APP_FLASH_ADDR) != 0) {
        printf("No valid application!\r\n");
        while(1);  // 等待更新
    }

    // 6. 跳转到应用程序
    jump_to_app(APP_FLASH_ADDR);

    while(1);  // 不应到达
}
```

### 9.3 跳转函数

```c
void jump_to_app(uint32_t app_addr) {
    // 1. 禁用所有中断
    __disable_irq();

    // 2. 停止外设并复位
    HAL_DeInit();

    // 3. 清除挂起中断
    for (int i = 0; i < 8; i++) {
        NVIC->ICER[i] = 0xFFFFFFFF;  // 清除使能
        NVIC->ICPR[i] = 0xFFFFFFFF;  // 清除挂起
    }

    // 4. 读取应用程序栈指针和复位向量
    uint32_t app_sp  = *(volatile uint32_t *)app_addr;
    uint32_t app_entry = *(volatile uint32_t *)(app_addr + 4);

    // 5. 校验栈指针有效性(应在RAM范围内)
    if ((app_sp & 0x2FFE0000) != 0x20000000) {
        __enable_irq();
        return;  // 无效的应用程序
    }

    // 6. 设置栈指针
    __set_MSP(app_sp);

    // 7. 跳转
    void (*app_reset)(void) = (void (*)(void))app_entry;
    app_reset();
}
```

## 10. 现有Bootloader方案

### 10.1 MCUboot

开源Bootloader，广泛用于Zephyr和Mbed OS：

| 特性 | 说明 |
|------|------|
| 签名验证 | ECDSA-RSA多种算法 |
| 双Bank | 原生支持A/B分区 |
| 差分更新 | 支持压缩和差分 |
| 回滚 | 启动计数器自动回滚 |
| 可移植 | 支持多款MCU |

### 10.2 STM32内置系统Bootloader

ST在出厂时烧录的系统Bootloader：

- 支持UART、I2C、SPI、USB、CAN等接口
- 通过BOOT0/BOOT1引脚选择启动模式
- 不可修改，始终可用作最后的恢复手段
- 但功能有限，不支持签名验证

### 10.3 ESP32二级Bootloader

ESP32使用两级启动：

1. 一级Bootloader(ROM固化)：加载二级Bootloader
2. 二级Bootloader(可配置)：读取分区表，选择启动分区，加载应用程序

## 11. 常见问题

### 11.1 栈指针初始化

错误：跳转到应用程序后立即HardFault。

原因：应用程序的向量表第一个字是初始栈指针值。如果Flash中该位置不是有效的RAM地址，MSP设置后立即异常。

```c
// 必须校验栈指针
uint32_t app_sp = *(volatile uint32_t *)APP_ADDR;
if ((app_sp & 0xFFF00000) != 0x20000000) {
    // 栈指针不在SRAM范围, 应用无效
    error_handler();
}
```

### 11.2 跳转前禁用中断

错误：跳转后应用程序的中断处理异常。

原因：Bootloader中使能的中断在应用程序中仍然挂起，但向量表已经改变，导致跳转到错误地址。

```c
// 跳转前必须：
__disable_irq();                    // 全局禁用中断
for (int i = 0; i < 8; i++) {
    NVIC->ICER[i] = 0xFFFFFFFF;     // 清除中断使能
    NVIC->ICPR[i] = 0xFFFFFFFF;     // 清除挂起标志
}
SysTick->CTRL = 0;                  // 停止SysTick
```

### 11.3 看门狗处理

错误：更新过程中看门狗复位导致更新中断。

解决方案：

- Bootloader中喂狗：在长时间操作(如Flash擦除)前后喂狗
- 更新过程中暂时禁用独立看门狗(IWDG)
- 使用窗口看门狗(WWDG)时确保更新操作在窗口内

```c
// 更新过程中定期喂狗
void flash_write_with_wdg(uint32_t addr, uint8_t *data, size_t len) {
    for (size_t i = 0; i < len; i += FLASH_PAGE_SIZE) {
        size_t chunk = MIN(FLASH_PAGE_SIZE, len - i);
        flash_write_page(addr + i, data + i, chunk);
        HAL_IWDG_Refresh(&hiwdg);  // 喂狗
    }
}
```

## 总结

Bootloader是嵌入式系统启动和更新的基石，设计要点：

1. 职责明确：只做硬件初始化、启动决策、固件更新和跳转，越简单越可靠
2. 触发灵活：GPIO/NVS标志/超时多种方式组合，确保总能进入更新模式
3. 安全验证：签名校验防止恶意固件，写保护防止Bootloader被篡改
4. 跳转安全：禁用中断、清除挂起、校验栈指针——每一步都不能省
5. 最后手段：保留芯片内置Bootloader或SWD接口，作为最终恢复手段

一句话：Bootloader可能一辈子只执行几百毫秒，但它决定了设备一生的可靠性。

## 参考文献

1. Joseph Yiu. "The Definitive Guide to ARM Cortex-M0/M0+/M3/M4/M7", 2nd Edition, 2023.
2. MCUboot Project. "MCUboot Design Documentation", 2022.
3. STM32. "AN2606: STM32 System Memory Boot Mode", 2023.
4. USB-IF. "Device Firmware Upgrade Specification", Revision 1.1, 2004.
5. ARM. "Cortex-M4 Technical Reference Manual (DDI0439)", 2022.
