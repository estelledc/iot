---
schema_version: '1.0'
id: device-tree-embedded-linux
title: 设备树Device Tree在嵌入式Linux中的硬件描述
layer: 1
content_type: UNKNOWN
difficulty: advanced
reading_time: 22
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 设备树Device Tree在嵌入式Linux中的硬件描述
> **难度**：🔴 高级 | **领域**：Linux硬件抽象 | **阅读时间**：约 22 分钟

## 引言

想象你搬进一间新公寓。房东不会把每面墙、每个插座都焊死在房屋结构里，而是给你一张平面图——哪里有插座、哪里有开关、管道怎么走，都标注清楚。你按图使用即可，不需要拆墙重新装修。设备树就是Linux内核的那张"平面图"：它把硬件信息从内核代码中分离出来，让同一份内核代码适配不同硬件，只需要换一张"图"。

## 1. 设备树的诞生背景

### 1.1 设备树之前：板文件时代

在设备树出现之前，Linux通过板文件（Board File）描述硬件。每个开发板在内核源码中有一个对应的C文件，硬编码了所有外设的地址、中断号和配置参数。

```c
/* 旧式板文件示例：arch/arm/mach-xxx/board-myboard.c */
static struct i2c_board_info myboard_i2c_devices[] __initdata = {
    {
        I2C_BOARD_INFO("tmp102", 0x48),  /* 硬编码I2C地址 */
        .irq = gpio_to_irq(23),           /* 硬编码中断 */
    },
};

static void __init myboard_init(void)
{
    i2c_register_board_info(0, myboard_i2c_devices,
                            ARRAY_SIZE(myboard_i2c_devices));
}
```

### 1.2 板文件的痛点与设备树的解决思路

板文件的三大问题：每个板变体都需要修改内核源码并重新编译；内核源码中堆积大量板文件（ARM架构一度有数千个）；违反内核原则——内核代码不应包含平台特定的硬编码信息。

设备树将硬件描述从内核源码中完全剥离，以独立的数据结构传递给内核。内核只需编写驱动代码，硬件配置由设备树提供。这实现了"一份内核，多张设备树"的灵活架构。PowerPC架构最先采用设备树，随后ARM架构在2011年左右全面迁移，最终成为Linux的标准硬件描述机制。

## 2. DTS语法基础

### 2.1 节点与属性

设备树由节点（Node）和属性（Property）组成。节点表示一个设备或总线，属性描述该设备的配置信息。

```dts
/ {                          /* 根节点，代表整个硬件 */
    model = "My IoT Board";  /* 属性：板子名称 */
    compatible = "myvendor,myboard";  /* 兼容性字符串 */

    i2c0: i2c@40002000 {     /* 节点名: label: name@address */
        compatible = "myvendor,i2c-controller";
        reg = <0x40002000 0x1000>;  /* 寄存器地址和大小 */
        #address-cells = <1>;
        #size-cells = <0>;
        clock-frequency = <100000>;  /* 100kHz I2C时钟 */

        temperature-sensor@48 {  /* I2C子设备 */
            compatible = "ti,tmp102";
            reg = <0x48>;       /* I2C从地址 */
            interrupt-parent = <&gpio0>;
            interrupts = <23 0>; /* GPIO23, 下降沿 */
        };
    };
};
```

### 2.2 常用属性详解

| 属性 | 说明 | 示例 |
|------|------|------|
| compatible | 驱动匹配字符串 | "vendor,device" |
| reg | 寄存器地址和大小 | <0x40002000 0x1000> |
| interrupts | 中断号和触发类型 | <23 0> |
| clocks | 时钟引用 | <&clk_periph> |
| status | 启用或禁用设备 | "okay"或"disabled" |
| #address-cells | 子节点reg中地址占用的cell数 | <1> |
| #size-cells | 子节点reg中大小占用的cell数 | <0> |

### 2.3 compatible字符串的匹配规则

compatible是连接设备树和驱动的关键纽带。内核驱动通过of_device_id表声明自己支持的compatible值：

```c
/* 内核驱动侧 */
static const struct of_device_id tmp102_of_match[] = {
    { .compatible = "ti,tmp102" },
    { .compatible = "ti,tmp75" },
    { }
};
MODULE_DEVICE_TABLE(of, tmp102_of_match);

static struct i2c_driver tmp102_driver = {
    .driver = {
        .name = "tmp102",
        .of_match_table = tmp102_of_match,
    },
    .probe = tmp102_probe,
};
```

## 3. 设备树结构详解

### 3.1 标准顶层节点

```dts
/ {
    cpus { ... };      /* CPU核心描述 */
    memory { ... };    /* 物理内存布局 */
    chosen { ... };    /* 内核启动参数 */
    soc { ... };       /* SoC内部外设 */
    leds { ... };      /* 板级设备 */
};
```

### 3.2 cpus、memory与chosen节点

```dts
cpus {
    #address-cells = <1>;
    #size-cells = <0>;
    cpu0: cpu@0 {
        compatible = "arm,cortex-a53";
        reg = <0x0>;
        clock-frequency = <800000000>;  /* 800MHz */
    };
};

memory@80000000 {
    device_type = "memory";
    reg = <0x80000000 0x20000000>;  /* 起始地址 512MB */
};

chosen {
    stdout-path = &uart0;
    bootargs = "console=ttyS0,115200 root=/dev/mmcblk0p2 rootwait";
};
```

## 4. 编译与加载流程

### 4.1 编译链路

```
DTS源码  -->  DTC编译器  -->  DTB二进制  -->  Bootloader加载  -->  内核解析
(.dts)       (dtc工具)      (.dtb)        (u-boot传递)        (early_init_dt)
```

### 4.2 编译命令

```bash
# 手动编译单个设备树
dtc -I dts -O dtb -o myboard.dtb myboard.dts

# 反编译DTB为DTS（调试用）
dtc -I dtb -O dts -o myboard_decompiled.dts myboard.dtb

# 内核构建系统自动编译
make dtbs
```

### 4.3 Bootloader传递设备树

U-Boot在启动内核时，将DTB加载到内存并传递其地址：

```bash
# U-Boot命令
fatload mmc 0:1 ${fdt_addr} myboard.dtb
fatload mmc 0:1 ${kernel_addr} Image
booti ${kernel_addr} - ${fdt_addr}
```

## 5. 设备树覆盖层(Overlay)

### 5.1 什么是Overlay

设备树覆盖层（DTBO）允许在运行时修改基础设备树，而不需要重新编译整个DTB。这对于扩展板、功能模块等即插即用的硬件非常有用。

### 5.2 Overlay的应用场景

- 扩展板/盾板：如Raspberry Pi的HAT、BeagleBone的Cape
- 运行时硬件配置：根据检测结果启用/禁用设备
- 多硬件版本：基础DTB加不同Overlay支持不同版本

### 5.3 Overlay示例

```dts
/* enable-sensor-overlay.dts */
/dts-v1/;
/plugin/;

/ {
    compatible = "myvendor,myboard";

    fragment@0 {
        target = <&i2c0>;

        __overlay__ {
            pressure-sensor@76 {
                compatible = "bosch,bmp280";
                reg = <0x76>;
                status = "okay";
            };
        };
    };
};
```

```bash
# 编译Overlay
dtc -I dts -O dtb -o enable-sensor.dtbo enable-sensor-overlay.dts

# 在U-Boot中应用Overlay
fdt addr ${fdt_addr}
fdt overlay apply ${fdt_addr} ${overlay_addr}
```

## 6. pinctrl与引脚复用

### 6.1 为什么需要pinctrl

大多数SoC的引脚具有复用功能——同一个物理引脚可以配置为GPIO、I2C、SPI或UART。pinctrl子系统通过设备树描述引脚的复用配置，确保不同外设不会争抢同一引脚。

### 6.2 设备树中的pinctrl配置

```dts
&i2c0 {
    pinctrl-names = "default";
    pinctrl-0 = <&i2c0_pins>;
    status = "okay";
};

&pinctrl {
    i2c0_pins: i2c0-pins {
        pins = "GPIO4", "GPIO5";
        function = "i2c0";
        bias-pull-up;
        drive-strength = <2>;
    };
};
```

## 7. 实战示例

### 7.1 启用I2C传感器

```dts
&i2c0 {
    status = "okay";

    temperature-sensor@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;
        interrupt-parent = <&gpio0>;
        interrupts = <23 IRQ_TYPE_EDGE_FALLING>;
        vcc-supply = <&reg_3v3>;
    };
};
```

### 7.2 配置SPI Flash与GPIO LED

```dts
&spi0 {
    status = "okay";

    flash@0 {
        compatible = "jedec,spi-nor";
        reg = <0>;           /* SPI片选0 */
        spi-max-frequency = <50000000>;  /* 50MHz */
    };
};

/ {
    leds {
        compatible = "gpio-leds";

        led-status {
            label = "status";
            gpios = <&gpio0 13 0>;
            linux,default-trigger = "heartbeat";
        };
    };
};
```

## 8. 调试设备树

### 8.1 运行时检查设备树

内核将解析后的设备树暴露在proc文件系统中：

```bash
# 查看完整设备树
ls /proc/device-tree/
cat /proc/device-tree/model
# 输出: My IoT Board

# 查看特定设备节点
ls /proc/device-tree/i2c@40002000/
cat /proc/device-tree/i2c@40002000/compatible
```

### 8.2 从运行系统反编译设备树

```bash
# 从/proc/device-tree重建DTS源码
dtc -I fs -O dts /proc/device-tree -o live-devicetree.dts

# 检查驱动绑定
ls -l /sys/bus/i2c/devices/0-0048/driver
# 输出应指向绑定的驱动目录
```

### 8.3 内核日志排查绑定问题

```bash
dmesg | grep -i "of\|device tree\|probe"
# 常见错误信息：
# "no compatible node found"  -> compatible字符串不匹配
# "probe failed"              -> 资源获取失败
# "deferred probe pending"    -> 依赖未就绪
```

## 9. 常见错误与排查

### 9.1 错误排查清单

| 错误现象 | 可能原因 | 排查方法 |
|----------|----------|----------|
| 驱动未绑定 | compatible不匹配 | 对比DTS和驱动of_device_id |
| 设备不可用 | status未设为"okay" | 检查节点status属性 |
| probe失败 | reg地址错误 | 对照SoC手册确认地址 |
| 中断无效 | 中断号或类型错误 | 检查interrupts属性 |
| 引脚冲突 | pinctrl配置重叠 | 检查pinctrl节点 |

### 9.2 典型错误示例

**错误：compatible字符串拼写不一致**

```dts
/* 设备树写的是 */
compatible = "ti,tmp-102";  /* 多了一个连字符 */
/* 驱动匹配的是 */
/* .compatible = "ti,tmp102" */
/* 结果：驱动找不到设备 */
```

**错误：忘记启用设备**

当SoC的设备树默认将外设status设为"disabled"时，必须在板级设备树中显式启用：

```dts
&i2c0 {
    status = "okay";  /* 必须显式启用 */
    temperature-sensor@48 {
        compatible = "ti,tmp102";
        reg = <0x48>;
    };
};
```

## 10. IoT场景下的设备树应用

### 10.1 自定义传感器板描述

```dts
/ {
    model = "MyEnv Sensor Board v1.2";
    compatible = "myvendor,envsensor-v1.2", "myvendor,envsensor";

    fixed-regulators {
        reg_3v3: regulator-3v3 {
            compatible = "regulator-fixed";
            regulator-name = "3V3";
            regulator-min-microvolt = <3300000>;
            regulator-max-microvolt = <3300000>;
            gpio = <&gpio0 7 0>;
            enable-active-high;
        };
    };
};
```

### 10.2 功耗优化：禁用未使用外设

```dts
/* 禁用不需要的外设以降低功耗 */
&usb0 { status = "disabled"; };
&hdmi { status = "disabled"; };
&gpu  { status = "disabled"; };

/* 只保留IoT必需外设 */
&uart0 { status = "okay"; };   /* 调试串口 */
&i2c0  { status = "okay"; };   /* 传感器总线 */
&spi0  { status = "okay"; };   /* Flash存储 */
```

### 10.3 支持多硬件版本

利用Overlay支持同一产品多个硬件版本：

```bash
# 在init脚本中根据硬件版本加载不同Overlay
hw_rev=$(gpio_read 12)  # 读取版本识别GPIO

if [ "$hw_rev" = "1" ]; then
    fdt overlay apply /boot/overlays/hw-v1.dtbo
elif [ "$hw_rev" = "2" ]; then
    fdt overlay apply /boot/overlays/hw-v2.dtbo
fi
```

## 总结

设备树是嵌入式Linux中连接硬件和软件的关键桥梁。它将硬件描述从内核代码中解耦出来，让一份内核代码可以适配多种硬件平台，极大地提高了代码复用性和可维护性。掌握设备树的核心在于理解三个映射关系：compatible映射驱动，reg映射地址，interrupts映射中断。在实际IoT项目中，善用设备树的覆盖层和状态控制机制，可以优雅地解决多硬件版本和功耗优化的问题。

## 参考文献

1. devicetree.org, "Devicetree Specification v0.4", 2023
2. Kernel.org, "Device Tree Usage Guide", 2024
3. Bootlin, "Embedded Linux System Development - Device Tree", 2024
4. Free Electrons, "Device Tree for Dummies", ELCE 2013
5. Linaro, "Device Tree Overlay Documentation", 2024
