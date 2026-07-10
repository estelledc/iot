---
schema_version: '1.0'
id: zephyr-rtos-device-driver-model
title: Zephyr RTOS设备驱动模型与DeviceTree
layer: 1
content_type: UNKNOWN
difficulty: advanced
reading_time: 25
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# Zephyr RTOS设备驱动模型与DeviceTree

> **难度**：🔴 高级 | **领域**：RTOS驱动框架 | **阅读时间**：约 25 分钟

## 引言

想象你开了一家大型连锁酒店。每家分店有不同的房间布局(开发板)、不同的家具供应商(外设芯片)、不同的前台系统(MCU型号)。如果每开一家分店就要重写一套管理系统，那你永远也扩张不了。

聪明的做法是：制定一套"家具接口规范"(DeviceTree描述)——不管什么品牌的灯，只要符合规范就能接入；再制定一套"安装流程标准"(驱动模型)——先装基础设施(PRE_KERNEL_1)，再装家具(PRE_KERNEL_2)，最后安排人员(POST_KERNEL)。新店开业时，只需要改一份"分店配置单"(overlay文件)，不需要重写任何管理代码。

Zephyr RTOS就是这样管理IoT设备的。它从Linux借来了DeviceTree硬件描述机制，搭配统一的驱动模型和Kconfig构建系统，让同一份驱动代码能跑在不同MCU上——换芯片只改配置，不改代码。

## 1. Zephyr项目概览与治理

Zephyr项目由Linux Foundation于2016年发起，初始代码基于Wind River的Rocket内核。与FreeRTOS由单一公司(Amazon)主导不同，Zephyr采用中立基金会治理，成员包括Intel、Nordic、NXP、STM等芯片厂商。LTS版本每2年发布一次，维护周期3年。

核心设计哲学：

1. **可扩展性**：从4KB RAM的MCU到MB级RAM的MPU，同一套内核
2. **安全性**：编译时资源分配、栈溢出检测、权限隔离
3. **统一抽象**：DeviceTree描述硬件、Kconfig裁剪功能、驱动模型统一API

```
+---------------------------------------------------+
|                  Application                      |
+---------------------------------------------------+
|  Subsystem APIs (GPIO/I2C/SPI/UART/Sensor/BLE...) |
+---------------------------------------------------+
|              Device Driver Model                   |
|          (struct device / init levels)            |
+---------------------------------------------------+
|    DeviceTree          Kconfig        West        |
|    (硬件描述)          (功能裁剪)    (构建工具)    |
+---------------------------------------------------+
|                  Zephyr Kernel                     |
+---------------------------------------------------+
```

Zephyr从Linux继承了多个关键概念，但做了"缩小"适配：

| 概念 | Linux | Zephyr |
|------|-------|--------|
| DeviceTree | 运行时解析DTB | 编译时生成C宏定义 |
| 驱动模型 | 可加载模块(.ko) | 编译时静态链接 |
| 构建系统 | Kbuild | CMake + Kconfig |
| 内存分配 | 动态(slab/buddy) | 静态为主(编译时分配) |

关键区别：Linux的DeviceTree是运行时解析的DTB，Zephyr在编译时把DTS转成C宏，零运行时开销——这对资源受限的MCU至关重要。

## 2. DeviceTree机制

### 2.1 DTS语法与硬件描述

DeviceTree用树形节点描述硬件，核心思想是**硬件描述与驱动代码分离**——驱动只写逻辑，不硬编码地址和引脚号：

```dts
/ {
    chosen {
        zephyr,console = &uart0;
        zephyr,sram = &sram0;
    };

    soc {
        i2c0: i2c@40003000 {
            compatible = "nordic,nrf-twi";
            reg = <0x40003000 0x1000>;
            status = "okay";

            bme280@76 {
                compatible = "bosch,bme280";
                reg = <0x76>;
                label = "BME280";
            };
        };
    };
};
```

关键属性：`compatible`(驱动匹配标识)、`reg`(寄存器地址和长度)、`status`("okay"启用/"disabled"禁用)、`label`(设备查找键)、`&`(节点引用)。

### 2.2 Bindings: YAML模式定义

每个`compatible`对应一个YAML binding文件，约束节点允许的属性和类型。它同时充当文档(开发者知道支持哪些属性)、验证器(构建时检查)和代码生成器(决定哪些属性转成C宏)。

### 2.3 从DTS到C代码

构建时dtc将DTS转成C头文件，通过`DT_NODELABEL`、`DT_LABEL`、`DT_REG_ADDR`等宏访问节点信息，编译后替换为具体值，零运行时开销。

### 2.4 Overlay文件: 板级定制

不修改上游board文件的前提下调整硬件配置：

```dts
/* nrf52840dk_nrf52840.overlay */
&i2c1 {
    sht30@44 {
        compatible = "sensirion,sht3xd";
        reg = <0x44>;
        label = "SHT30";
        status = "okay";
    };
};
```

查找顺序：命令行`-DDTC_OVERLAY_FILE=` > 板级目录`boards/<board>.overlay` > 应用目录。

## 3. 设备驱动API模型

### 3.1 struct device与设备查找

所有设备用`struct device`表示，编译时静态分配：

```c
struct device {
    const char *name;        /* 设备名称 */
    const void *config;      /* 编译时常量配置(来自DTS) */
    const void *api;         /* API函数指针表(类似虚函数表) */
    void *data;              /* 运行时可变状态 */
};
```

查找设备——传统方式vs推荐方式：

```c
/* 传统：字符串查找，运行时可能返回NULL */
const struct device *dev = device_get_binding("BME280");

/* 推荐：DT宏，编译时解析，设备不存在则构建失败 */
const struct device *dev = DEVICE_DT_GET(BME280_NODE);
```

### 3.2 驱动API: 函数指针表实现多态

每个子系统定义API结构体，驱动实现函数指针：

```c
/* 传感器子系统定义的API结构体 */
__subsystem struct sensor_driver_api {
    sensor_trigger_set_t trigger_set;
    sensor_sample_fetch_t sample_fetch;
    sensor_channel_get_t channel_get;
};

/* 驱动实现并填充 */
static int bme280_sample_fetch(const struct device *dev,
                                enum sensor_channel chan) { /* ... */ }
static int bme280_channel_get(const struct device *dev,
                               enum sensor_channel chan,
                               struct sensor_value *val) { /* ... */ }

static const struct sensor_driver_api bme280_api = {
    .sample_fetch = bme280_sample_fetch,
    .channel_get  = bme280_channel_get,
};
```

调用者不需要知道具体驱动，只通过子系统API操作：`sensor_sample_fetch(dev)` 底层调用 `bme280_sample_fetch`。

## 4. 驱动初始化级别

### 4.1 四级初始化

```
+------------------+
| PRE_KERNEL_1     | <-- CPU架构、中断控制器
+------------------+
| PRE_KERNEL_2     | <-- 基本外设、定时器
+------------------+
| POST_KERNEL      | <-- 大多数驱动在这里初始化
+------------------+
| APPLICATION      | <-- 应用级初始化
+------------------+
```

每个级别内按优先级(0-99)排序，数值越小越先执行。

### 4.2 定义与注册初始化函数

```c
static int bme280_init(const struct device *dev)
{
    const struct bme280_config *cfg = dev->config;
    if (!device_is_ready(cfg->i2c.bus)) {
        return -ENODEV;
    }
    /* 复位传感器、读取校准数据... */
    return 0;
}

DEVICE_DT_DEFINE(BME280_NODE,
                 bme280_init,            /* init函数 */
                 NULL,                    /* PM控制 */
                 &bme280_data,            /* 运行时数据 */
                 &bme280_config,          /* 编译时配置 */
                 POST_KERNEL,             /* 初始化级别 */
                 80,                      /* 优先级 */
                 &bme280_api);            /* API函数表 */
```

关键约束：被依赖者必须在更早的级别或同级别更低优先级初始化。I2C控制器在PRE_KERNEL_2(优先级60)完成，BME280在POST_KERNEL(优先级80)初始化——顺序正确。

## 5. Kconfig构建系统

Kconfig解决**哪些代码被编译进去**的问题。每个驱动/子系统有对应符号：

```kconfig
config BME280
    bool "BME280 sensor"
    depends on I2C

config BME280_OVERSAMPLE
    int "Oversampling factor"
    default 1
    range 1 16
    depends on BME280
```

配置文件层次(上层覆盖下层)：

```
Zephyr默认值 -> Board defconfig -> Application prj.conf -> Overlay config
```

典型prj.conf：

```ini
CONFIG_SERIAL=y
CONFIG_I2C=y
CONFIG_SENSOR=y
CONFIG_BME280=y
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
```

未启用的驱动不会被编译——固件只包含实际使用的代码，这对MCU的Flash空间至关重要。

## 6. West构建工具

West是Zephyr的元工具，负责多仓库管理(20+外部模块)、构建封装(CMake + Ninja)、烧录封装(openocd/pyocd/nrfjprog)。

```bash
west init -m https://github.com/zephyrproject-rtos/zephyr && west update
west build -b nrf52840dk_nrf52840 -p auto   # -b: 开发板, -p auto: 自动pristine
west flash                                    # 烧录
west build -t menuconfig                      # 菜单配置
```

构建流程：CMake配置(解析Kconfig生成autoconf.h，解析DTS生成generated_dts_board.h) -> 编译(只编译启用的源文件) -> 链接(生成.elf/.hex/.bin)。

## 7. 子系统API总览

| 子系统 | 头文件 | 典型用途 |
|--------|--------|----------|
| GPIO | `drivers/gpio.h` | 引脚读写、中断、上下拉 |
| I2C | `drivers/i2c.h` | I2C总线读写传输 |
| SPI | `drivers/spi.h` | SPI全双工/半双工传输 |
| UART | `drivers/uart.h` | 串口收发(中断/DMA) |
| Sensor | `drivers/sensor.h` | 传感器采样数据解析 |
| ADC | `drivers/adc.h` | 模拟信号采集 |
| PWM | `drivers/pwm.h` | PWM输出占空比控制 |

GPIO使用示例——DT宏消除硬编码：

GPIO示例：`GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios)`从DTS获取LED引脚配置，`gpio_pin_configure_dt()`/`gpio_pin_toggle_dt()`操作引脚，全程无硬编码。

Sensor API提供统一抽象：`sensor_sample_fetch(dev)`触发采样，`sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &val)`读取数据，与具体传感器型号无关。

## 8. 编写自定义传感器驱动

### 8.1 文件结构

```
drivers/sensor/bme280/
  +-- CMakeLists.txt    # 构建配置
  +-- Kconfig           # 配置选项
  +-- bme280.h          # 驱动内部头文件
  +-- bme280.c          # 驱动实现
```

### 8.2 核心实现

```c
/* bme280.h */
#include <zephyr/drivers/i2c.h>

#define BME280_REG_ID         0xD0
#define BME280_REG_CTRL_MEAS  0xF4
#define BME280_ID_VAL         0x60

struct bme280_data {
    int32_t comp_temp, comp_press, comp_humidity;
    uint16_t dig_T1; int16_t dig_T2, dig_T3;
    /* ... 校准参数 ... */
};

struct bme280_config {
    struct i2c_dt_spec i2c;
};
```

```c
/* bme280.c */
#include <zephyr/kernel.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include "bme280.h"
LOG_MODULE_REGISTER(bme280, CONFIG_SENSOR_LOG_LEVEL);

static int bme280_sample_fetch(const struct device *dev,
                                enum sensor_channel chan)
{
    struct bme280_data *data = dev->data;
    const struct bme280_config *cfg = dev->config;
    uint8_t ctrl = 0x27; /* forced mode */
    i2c_reg_write_byte_dt(&cfg->i2c, BME280_REG_CTRL_MEAS, ctrl);
    k_msleep(10);
    /* 读取原始数据并补偿计算... */
    return 0;
}

static int bme280_channel_get(const struct device *dev,
                               enum sensor_channel chan,
                               struct sensor_value *val)
{
    struct bme280_data *data = dev->data;
    switch (chan) {
    case SENSOR_CHAN_AMBIENT_TEMP:
        sensor_value_from_micro(val, data->comp_temp * 100);
        break;
    case SENSOR_CHAN_HUMIDITY:
        sensor_value_from_micro(val, data->comp_humidity * 1000);
        break;
    default: return -ENOTSUP;
    }
    return 0;
}

static const struct sensor_driver_api bme280_api = {
    .sample_fetch = bme280_sample_fetch,
    .channel_get  = bme280_channel_get,
};

static int bme280_init(const struct device *dev)
{
    const struct bme280_config *cfg = dev->config;
    if (!device_is_ready(cfg->i2c.bus)) return -ENODEV;
    uint8_t id;
    i2c_reg_read_byte_dt(&cfg->i2c, BME280_REG_ID, &id);
    if (id != BME280_ID_VAL) return -EINVAL;
    /* 读取校准数据... */
    return 0;
}

/* 多实例自动展开宏 */
#define BME280_INIT(inst)                                          \
    static struct bme280_data data_##inst;                         \
    static const struct bme280_config config_##inst = {            \
        .i2c = I2C_DT_SPEC_INST_GET(inst),                        \
    };                                                             \
    SENSOR_DEVICE_DT_INST_DEFINE(inst, bme280_init, NULL,         \
        &data_##inst, &config_##inst, POST_KERNEL,                 \
        CONFIG_SENSOR_INIT_PRIORITY, &bme280_api);

DT_INST_FOREACH_STATUS_OKAY(BME280_INIT)
```

`DT_INST_FOREACH_STATUS_OKAY`对DTS中每个状态为`okay`的`bosch,bme280`节点展开一次`BME280_INIT(inst)`，自动处理多实例。

## 9. 与FreeRTOS驱动方式对比

| 维度 | FreeRTOS | Zephyr |
|------|----------|--------|
| 硬件描述 | 代码中硬编码 | DeviceTree声明式 |
| 驱动API | 厂商HAL(STM32 HAL, nRF SDK...) | 统一子系统API |
| 配置系统 | #ifdef / 手动改头文件 | Kconfig菜单式 |
| 初始化 | 手动调用init函数 | 自动按级别调用 |
| 多实例 | 手动管理结构体数组 | DT_INST_FOREACH自动展开 |
| 构建系统 | Make/CMake(手动) | West + CMake(自动化) |

同一功能的代码对比——FreeRTOS方式硬编码硬件参数，换MCU需重写I2C层：

```c
/* FreeRTOS + STM32 HAL */
#define BME280_I2C_ADDR  0x76
void bme280_init(void) {
    hi2c1.Instance = I2C1;
    hi2c1.Init.ClockSpeed = 100000;
    HAL_I2C_Init(&hi2c1);
    /* 切换到nRF52时，全部重写 */
}
```

Zephyr方式硬件参数来自DeviceTree，驱动代码与MCU无关——切换芯片只改overlay文件。

选型建议：FreeRTOS适合简单项目、团队已有厂商SDK经验；Zephyr适合多协议需求(BLE + Thread)、频繁切换MCU平台、需要安全认证(IEC 61508)的项目。

## 10. Zephyr的IoT生态

### 10.1 内置协议栈

Zephyr内置丰富的IoT协议栈，无需第三方库：

```
+---------------------------------------------------+
|              Application                           |
+---------------------------------------------------+
| BLE 5.0 | Thread 1.3 | WiFi | NFC | 802.15.4     |
+---------------------------------------------------+
|            Zephyr Networking Stack                |
| (IPv6/IPv4, 6LoWPAN, CoAP, LwM2M, MQTT, TLS)    |
+---------------------------------------------------+
|            Zephyr Kernel + Drivers                |
+---------------------------------------------------+
```

### 10.2 BLE支持

Zephyr原生支持BLE 5.0，包含完整的Controller和Host实现：Advertising Extension、2M PHY、Coded PHY、GATT、GAP、SMP安全管理、BLE Mesh 1.0.1。

BLE初始化核心流程：`bt_enable(NULL)`初始化协议栈，`bt_le_adv_start()`开始广播——只需5行代码即可启动BLE外设角色。

### 10.3 LwM2M与Thread

- **LwM2M**：OMA标准的IoT设备管理协议，Zephyr内置完整客户端——设备注册、Bootstrap、FOTA固件更新、标准化对象模型(/3/0/0=制造商, /3303/0/5700=温度)、DTLS安全传输
- **Thread**：基于IEEE 802.15.4的自组网网状网络，Zephyr是OpenThread官方参考平台——自动地址分配、Border Router、与Matter协议深度集成

## 总结

Zephyr的驱动模型设计体现三个核心权衡：

1. **编译时 vs 运行时**：DeviceTree和Kconfig在编译时完成配置，零运行时开销，代价是构建流程更复杂
2. **统一 vs 灵活**：子系统API提供统一接口，简单场景可能有额外调用开销(编译器通常内联消除)
3. **安全 vs 便捷**：静态分配、编译时检查让错误在构建阶段暴露，代价是需理解DTS和Kconfig两大配置系统

对IoT开发者而言，DeviceTree + 驱动模型 + Kconfig三位一体的最大价值是**可移植性**——从STM32切换到nRF52，或从一个传感器换成同类传感器，改配置而非改代码。长期维护的项目中省下的时间远超学习成本。

## 参考文献

1. Zephyr Project. "Zephyr RTOS Documentation: Device Tree." https://docs.zephyrproject.org/latest/build/dts/
2. Zephyr Project. "Zephyr RTOS Documentation: Device Driver Model." https://docs.zephyrproject.org/latest/kernel/drivers/
3. devicetree.org. "Devicetree Specification Release v0.4." https://www.devicetree.org/specifications/
4. Laczen, J. "Zephyr Device Driver Model - What, Why and How." Zephyr Developer Summit, 2021.
5. Nordic Semiconductor. "nRF Connect SDK Documentation." https://developer.nordicsemi.com/nRF_Connect_SDK/doc/latest/
