# USB OTG在嵌入式IoT设备中的实现
> **难度**：🟡 中级 | **领域**：USB嵌入式应用 | **阅读时间**：约 20 分钟

## 引言

想象你走进一家酒店:房间里的插座是"主人"，插头是"客人"，客人只能服从主人提供的电力规则。USB的世界也是一样--Host(主机)决定谁发言、何时发言，Device(设备)只能乖乖应答。但有时候，你的手机既是客人(连电脑传文件)，又是主人(接U盘读数据)，这就需要USB OTG--一种"角色互换"的能力。对IoT设备来说，掌握USB OTG意味着设备可以在现场充当主机读取传感器数据，回办公室后又变成从机被PC调试，一根线搞定两种身份。

## 1. USB协议概述

### 1.1 USB角色与速度等级

USB通信始终是一主一从的模型:

- **Host(主机)**: 总线控制器，发起所有传输，提供VBUS电力
- **Device(设备)**: 响应Host请求，不能主动发数据

| 速度等级 | 缩写 | 速率 | 典型应用 |
|----------|------|------|----------|
| Low-Speed | LS | 1.5 Mbps | 鼠标、键盘 |
| Full-Speed | FS | 12 Mbps | CDC虚拟串口、HID |
| High-Speed | HS | 480 Mbps | U盘、视频流 |

IoT设备最常用FS(12Mbps)，足以覆盖串口、HID和批量传输场景。

四种传输类型:

| 传输类型 | 特点 | 典型用途 |
|----------|------|----------|
| 控制传输 | 可靠、用于配置 | 枚举、标准请求 |
| 中断传输 | 周期性、低延迟 | HID、键盘 |
| 批量传输 | 可靠、无带宽保证 | U盘、打印机 |
| 等时传输 | 实时、无重传 | 音频、视频 |

### 1.2 USB描述符体系

USB设备通过描述符向Host报告自身能力:

```
设备描述符 (Device Descriptor)
  |-- 配置描述符 (Configuration Descriptor)
  |     |-- 接口描述符 (Interface Descriptor)
  |     |     |-- 端点描述符 (Endpoint Descriptor)
  |     |     |-- 类描述符 (Class Descriptor)
  |     |-- 接口关联描述符 (IAD)
  |-- 字符串描述符 (String Descriptor)
```

设备描述符关键字段:

```c
typedef struct {
    uint8_t  bLength;
    uint8_t  bDescriptorType;   // 类型 = 0x01
    uint16_t bcdUSB;            // USB版本 (0x0200 = USB2.0)
    uint8_t  bDeviceClass;      // 设备类
    uint8_t  bMaxPacketSize0;   // 端点0最大包长 (FS=64)
    uint16_t idVendor;          // VID
    uint16_t idProduct;         // PID
    uint8_t  bNumConfigurations;// 配置数量
} USB_DeviceDescriptor;
```

## 2. IoT相关USB设备类

| 类代码 | 名称 | 用途 | IoT典型场景 |
|--------|------|------|-------------|
| 0x02 | CDC-ACM | 虚拟串口 | 调试口、日志输出 |
| 0x03 | HID | 人机接口 | 自定义控制协议 |
| 0x08 | MSC | 大容量存储 | 固件升级、数据导出 |
| 0xFF | Vendor | 厂商自定义 | 私有协议通信 |

**CDC虚拟串口**: 免驱(Win10+/Linux/macOS内置驱动)，FS下实际约800KB/s，需要2个接口共用3个端点。

**HID类**: 无需驱动、支持中断传输(低延迟)，但每帧最大64字节(FS)，不适合大数据量。

**MSC类**: 设备端实现SCSI命令子集+FAT文件系统，典型方案是"拖拽升级"--将固件文件拖入虚拟U盘，设备自动烧录。

## 3. USB OTG双角色机制

### 3.1 OTG核心概念

USB OTG(On-The-Go)允许设备在Host和Device之间切换:

- **SRP**: Device请求Host开启VBUS
- **HNP**: 两个OTG设备间的角色切换
- **ADP**: 检测对端是否接入

OTG使用AB型接口，ID引脚接地为Host模式，悬空为Device模式。

### 3.2 OTG角色切换流程

```
设备A (初始Host)           设备B (初始Device)
    |                            |
    |  <--- HNP Request ---      |
    |  ---> HNP Accept --->      |
    |  (A断开VBUS, B开启VBUS)    |
设备A (新Device)           设备B (新Host)
```

### 3.3 IoT中的OTG应用场景

1. **现场数据采集**: 设备作为Host读取USB传感器/存储
2. **离线配置**: 设备作为Host读取U盘中的配置文件
3. **PC调试**: 设备作为Device连接PC，暴露调试串口
4. **固件升级**: 设备作为Device通过DFU接收新固件

## 4. STM32 USB外设

### 4.1 外设类型

| 外设 | 速度 | 典型型号 | 备注 |
|------|------|----------|------|
| USB(仅Device) | FS | STM32F103 | 只能做设备 |
| OTG_FS | FS | STM32F405 | 支持Host/Device/OTG |
| OTG_HS | HS(可降FS) | STM32F405 | 支持HS PHY接口 |

### 4.2 时钟与引脚配置

```c
// STM32H743 OTG_FS 时钟配置
// USB时钟必须为48MHz
RCC_PeriphCLKInitTypeDef periph_clk = {};
periph_clk.PeriphClockSelection = RCC_PERIPHCLK_USB;
periph_clk.UsbClockSelection = RCC_USBCLKSOURCE_HSI48;
HAL_RCCEx_PeriphCLKConfig(&periph_clk);

// 引脚: PA11(USB_DM), PA12(USB_DP)
GPIO_InitTypeDef gpio = {};
gpio.Pin = GPIO_PIN_11 | GPIO_PIN_12;
gpio.Mode = GPIO_MODE_AF_PP;
gpio.Speed = GPIO_SPEED_FREQ_VERY_HIGH;
gpio.Alternate = GPIO_AF10_OTG_FS;
HAL_GPIO_Init(GPIOA, &gpio);
```

## 5. USB中间件栈

### 5.1 STM32 USB库层次

```
+-----------------------------+
|     Application Layer       |  用户代码
+-----------------------------+
|     Class Layer             |  CDC/HID/MSC等类实现
+-----------------------------+
|     Core Layer              |  USBD核心状态机
+-----------------------------+
|     Driver Layer            |  HAL/LL底层驱动
+-----------------------------+
```

### 5.2 TinyUSB库

TinyUSB是开源跨平台USB设备栈，逐渐成为IoT领域首选:

```c
#include "tusb.h"

tusb_desc_device_t const desc_device = {
    .bLength         = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB          = 0x0200,
    .bDeviceClass    = TUSB_CLASS_MISC,
    .idVendor        = 0xCafe,
    .idProduct       = 0x4004,
    .bMaxPacketSize0 = 64,
    .bNumConfigurations = 0x01
};

while (1) {
    tud_task();    // 处理USB事件
    cdc_task();    // 处理CDC数据
}
```

优势: MIT协议、支持多MCU平台、RTOS友好、内存占用约8KB Flash。

### 5.3 中间件选型对比

| 特性 | STM32 HAL USB | TinyUSB | LUFA |
|------|---------------|---------|------|
| 协议 | BSD | MIT | MIT |
| 平台 | 仅STM32 | 多平台 | 仅AVR |
| RTOS | 部分支持 | 原生支持 | 不支持 |
| 学习曲线 | 中等 | 低 | 中等 |

## 6. CDC虚拟串口实现

### 6.1 硬件连接

```
STM32                    USB Type-B
  PA12 (USB_DP) --------> D+
  PA11 (USB_DM) --------> D-
  5V              --------> VBUS (仅检测)
  GND             --------> GND
```

### 6.2 实现代码

```c
// 初始化USB外设
void MX_USB_DEVICE_Init(void)
{
    USBD_Init(&hUsbDeviceFS, &FS_Desc, DEVICE_FS);
    USBD_RegisterClass(&hUsbDeviceFS, &USBD_CDC);
    USBD_CDC_RegisterInterface(&hUsbDeviceFS, &USBD_Interface_fops_FS);
    USBD_Start(&hUsbDeviceFS);
}

// 接收回调
static int8_t CDC_Receive_FS(uint8_t *Buf, uint32_t *Len)
{
    uint32_t rx_len = *Len;
    for (uint32_t i = 0; i < rx_len; i++) {
        uart_rx_buffer_push(Buf[i]);
    }
    USBD_CDC_SetRxBuffer(&hUsbDeviceFS, &Buf[0]);
    USBD_CDC_ReceivePacket(&hUsbDeviceFS);
    return USBD_OK;
}

// 发送数据
void CDC_SendData(uint8_t *data, uint16_t len)
{
    USBD_CDC_SetTxBuffer(&hUsbDeviceFS, data, len);
    USBD_CDC_TransmitPacket(&hUsbDeviceFS);
}
```

### 6.3 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 电脑识别不到设备 | 描述符错误 | 用USBTreeView检查 |
| 串口打开后无数据 | 未调用ReceivePacket | 每次接收后必须重新注册 |
| 数据丢失 | 发送过快未等完成 | 检查tx_done标志再发下一包 |

## 7. USB DFU固件升级

DFU(Device Firmware Upgrade)是USB官方定义的固件升级标准(设备类0xFE):

```c
// DFU跳转函数
void jump_to_dfu(void)
{
    __disable_irq();                    // 关闭中断
    HAL_USB_Stop(&hUsbDeviceFS);        // 关闭USB
    for (int i = 0; i < 8; i++) {
        NVIC->ICER[i] = 0xFFFFFFFF;     // 清除挂起中断
    }
    __IO uint32_t *flag = (__IO uint32_t *)0x20000000;
    *flag = 0xDFDFDFDF;                // 设置DFU标志
    HAL_NVIC_SystemReset();             // 软复位进入Bootloader
}
```

Flash分区布局:

```
0x0800 0000  System Memory (出厂Bootloader, 支持DFU)
0x0800 8000  Application (主程序区域)
0x080x xxxx  Backup/Download (临时存放新固件)
```

## 8. 电源与USB-C

### 8.1 VBUS电源考量

| 模式 | 电流 | 备注 |
|------|------|------|
| 默认 | 100mA | 枚举完成前 |
| 配置后 | 500mA (FS) | 需在配置描述符中声明 |
| USB-C | 1.5A/3A | 需CC下拉电阻配置 |

### 8.2 USB-C在IoT中的意义

- 正反插: 减少现场操作失误
- PD协商: 支持更高电压供电
- D+/D-: 与USB2.0兼容，升级成本低

## 9. 常见USB枚举问题排查

### 9.1 枚举流程

```
1. 设备接入, Host检测到D+/D-电平变化
2. Host发出BUS RESET (10ms低电平)
3. Host发送GET_DESCRIPTOR(Device) -- 获取bMaxPacketSize0
4. Host再次BUS RESET
5. Host发送SET_ADDRESS -- 分配设备地址
6. Host发送GET_DESCRIPTOR(Device) -- 读取完整设备描述符
7. Host发送GET_DESCRIPTOR(Configuration) -- 读取配置描述符
8. Host发送SET_CONFIGURATION -- 激活配置
9. 枚举完成, 加载驱动
```

### 9.2 常见失败原因

| 失败阶段 | 症状 | 可能原因 | 排查方法 |
|----------|------|----------|----------|
| 步骤1 | 设备无反应 | 硬件接线错误 | 示波器查D+/D- |
| 步骤3 | "未知USB设备" | bMaxPacketSize0错误 | 确认FS=64 |
| 步骤7 | 描述符长度不匹配 | 配置描述符总长度计算错误 | USBTreeView验证 |
| 步骤8 | 配置后立即断开 | 电流超限 | 测量功耗 |

调试工具: USBTreeView(查看描述符)、Wireshark+USBPcap(抓包)、lsusb -v(Linux详情)。

## 总结

1. **角色理解**: USB是主从模型，OTG允许设备在Host和Device间切换
2. **速度选择**: IoT设备通常使用FS(12Mbps)
3. **描述符是核心**: 枚举成功的关键是描述符链完整正确
4. **中间件选型**: TinyUSB跨平台且轻量，推荐新项目使用
5. **CDC最实用**: 虚拟串口是IoT调试和通信的首选方案
6. **DFU保底**: USB DFU是可靠的固件升级通道
7. **电源不忽视**: VBUS电流限制直接影响设备设计
8. **排查有法**: 枚举问题按流程逐步定位，善用USBTreeView和Wireshark

## 参考文献

1. USB Implementers Forum. USB 2.0 Specification. 2000.
2. STMicroelectronics. STM32F4xx Reference Manual - OTG_FS/OTG_HS Chapter. RM0090.
3. Hathaway H. TinyUSB: An open-source cross-platform USB stack. https://github.com/hathach/tinyusb
4. Axelson J. USB Complete: The Developer's Guide. 5th ed. Lakeview Research, 2015.
5. USB Implementers Forum. USB On-The-Go and Embedded Host Supplement. Rev 2.0.