# Linux内核GPIO驱动开发基础
> **难度**：🟡 中级 | **领域**：Linux驱动开发 | **阅读时间**：约 20 分钟

## 引言

如果说内核是IoT设备的"大脑"，那么GPIO就是它的"手脚"——大脑发出指令，手脚去控制灯光、读取按钮、驱动电机。在Linux中控制GPIO，就像指挥一个有严格纪律的组织：你不能直接伸手去操作，必须走正规流程——申请资源、配置方向、读写数据、释放资源。本文从用户空间到内核空间，系统梳理Linux GPIO的开发方法。

## 1. Linux GPIO子系统概述

### 1.1 架构分层

Linux GPIO子系统分为两层：

- GPIO控制器驱动：操作硬件寄存器，提供标准的GPIO操作回调。每个GPIO控制器在系统中注册为一个gpiochip。
- GPIO消费者驱动：通过标准API请求和操作GPIO，无需关心底层寄存器细节。

```
用户空间应用
    |
    V
libgpiod / sysfs接口
    |
    V
GPIO消费者驱动 (gpiod API)
    |
    V
gpiolib核心层
    |
    V
GPIO控制器驱动 (硬件寄存器操作)
    |
    V
物理GPIO引脚
```

### 1.2 gpiolib核心层

gpiolib是内核中GPIO的统一管理层。它提供标准化的API，屏蔽不同SoC的GPIO控制器差异。所有GPIO操作都通过gpiolib进行，确保了API的一致性和代码的可移植性。gpiolib还负责GPIO资源的分配和管理，防止多个驱动同时操作同一引脚。

## 2. 用户空间GPIO操作

### 2.1 旧式sysfs接口（已废弃）

早期Linux通过sysfs文件系统暴露GPIO控制接口。虽然简单直观，但已被内核标记为废弃：

```bash
# 导出GPIO 17
echo 17 > /sys/class/gpio/export

# 设置为输出方向
echo out > /sys/class/gpio/gpio17/direction

# 设置输出高电平
echo 1 > /sys/class/gpio/gpio17/value

# 释放GPIO
echo 17 > /sys/class/gpio/gpio17/unexport
```

sysfs接口的问题：不支持并发访问、无法原子读写、无法高效检测中断、已被标记为废弃将在未来内核移除。

### 2.2 新式字符设备接口（libgpiod）

新内核使用字符设备/dev/gpiochipN替代sysfs。libgpiod库和配套命令行工具提供了更安全、更高效的GPIO操作方式：

```bash
# 读取GPIO值
gpioget gpiochip0 17

# 设置GPIO输出
gpioset gpiochip0 17=1

# 监控GPIO事件（边沿中断）
gpiomon gpiochip0 23

# 查看GPIO芯片信息
gpioinfo gpiochip0
```

### 2.3 libgpiod C语言编程

```c
#include <gpiod.h>

int main(void)
{
    struct gpiod_chip *chip = gpiod_chip_open_by_name("gpiochip0");
    struct gpiod_line *line = gpiod_chip_get_line(chip, 17);

    gpiod_line_request_input(line, "my-sensor");
    int value = gpiod_line_get_value(line);
    printf("GPIO 17 value: %d\n", value);

    gpiod_line_release(line);
    gpiod_chip_close(chip);
    return 0;
}
```

## 3. 内核空间GPIO操作

### 3.1 gpiod API

现代Linux内核推荐使用基于描述符的gpiod API，替代旧版基于整数的gpio API。gpiod API通过设备树自动获取GPIO配置，代码更清晰、更安全。

| API函数 | 说明 |
|---------|------|
| gpiod_get(dev, con_id, flags) | 获取GPIO描述符 |
| gpiod_get_index(dev, con_id, idx, flags) | 获取索引GPIO |
| gpiod_direction_input(desc) | 配置为输入 |
| gpiod_direction_output(desc, val) | 配置为输出并设初始值 |
| gpiod_set_value(desc, val) | 设置输出值 |
| gpiod_get_value(desc) | 读取输入值 |
| gpiod_set_value_cansleep(desc, val) | 可休眠的设置 |
| gpiod_put(desc) | 释放GPIO |

### 3.2 从设备树获取GPIO

设备树中的GPIO属性自动映射到gpiod_get的con_id参数：

```dts
/* 设备树 */
my-led {
    compatible = "myvendor,my-led";
    led-gpios = <&gpio0 13 0>;  /* GPIO_ACTIVE_HIGH */
};
```

```c
/* 驱动代码 */
struct gpio_desc *led;

/* "led"对应设备树中的led-gpios */
led = gpiod_get(dev, "led", GPIOD_OUT_LOW);
if (IS_ERR(led)) {
    dev_err(dev, "failed to get LED GPIO\n");
    return PTR_ERR(led);
}
```

### 3.3 GPIO标志位

设备树GPIO属性的第三个cell指定电气标志：

| 标志 | 值 | 说明 |
|------|----|------|
| GPIO_ACTIVE_HIGH | 0 | 高电平有效（默认） |
| GPIO_ACTIVE_LOW | 1 | 低电平有效 |
| GPIO_OPEN_DRAIN | 2 | 开漏输出 |
| GPIO_OPEN_SOURCE | 4 | 开源输出 |

使用GPIO_ACTIVE_LOW时，gpiod_set_value(desc, 1)会物理输出低电平，gpiod API内部处理极性翻转，开发者无需手动取反。

## 4. GPIO中断处理

### 4.1 获取中断号与注册处理函数

GPIO可以通过gpiod_to_irq获取对应的中断号，然后使用标准内核中断API注册处理函数：

```c
int irq;

irq = gpiod_to_irq(button_gpio);
if (irq < 0) {
    dev_err(dev, "failed to get IRQ for GPIO\n");
    return irq;
}

/* 注册中断处理函数 */
ret = request_irq(irq, button_isr,
                  IRQF_TRIGGER_FALLING,  /* 下降沿触发 */
                  "my-button", dev);
```

### 4.2 中断处理函数

```c
#include <linux/interrupt.h>

static irqreturn_t button_isr(int irq, void *data)
{
    struct my_device *dev = data;

    /* 中断上下文：不能睡眠，快速处理 */
    dev->event_count++;
    /* 唤醒下半部处理 */
    schedule_work(&dev->button_work);

    return IRQ_HANDLED;
}
```

### 4.3 线程化中断

对于需要睡眠操作的中断处理（如I2C通信），使用request_threaded_irq：

```c
static irqreturn_t sensor_thread_fn(int irq, void *data)
{
    struct my_device *dev = data;

    /* 线程上下文：可以睡眠 */
    int value = i2c_smbus_read_byte(dev->client);
    if (value >= 0)
        dev->last_reading = value;

    return IRQ_HANDLED;
}

/* 注册线程化中断 */
ret = request_threaded_irq(irq, NULL, sensor_thread_fn,
                           IRQF_TRIGGER_FALLING | IRQF_ONESHOT,
                           "my-sensor", dev);
```

### 4.4 中断触发类型

| 标志 | 说明 |
|------|------|
| IRQF_TRIGGER_RISING | 上升沿触发 |
| IRQF_TRIGGER_FALLING | 下降沿触发 |
| IRQF_TRIGGER_BOTH | 双边沿触发 |
| IRQF_SHARED | 共享中断线 |
| IRQF_ONESHOT | 线程化中断专用，处理期间禁用中断 |

## 5. 实战驱动：LED控制驱动

### 5.1 设备树节点

```dts
my-leds {
    compatible = "myvendor,simple-led";
    led0-gpios = <&gpio0 13 GPIO_ACTIVE_LOW>;
    led1-gpios = <&gpio0 14 GPIO_ACTIVE_LOW>;
};
```

### 5.2 驱动核心代码

```c
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/gpio/consumer.h>
#include <linux/of.h>

struct led_priv {
    struct gpio_desc *led0;
    struct gpio_desc *led1;
};

/* sysfs写入回调 */
static ssize_t led0_store(struct device *dev,
                          struct device_attribute *attr,
                          const char *buf, size_t count)
{
    struct led_priv *priv = dev_get_drvdata(dev);
    int val;
    if (kstrtoint(buf, 0, &val))
        return -EINVAL;
    gpiod_set_value(priv->led0, val);
    return count;
}
static DEVICE_ATTR_WO(led0);

static int led_probe(struct platform_device *pdev)
{
    struct device *dev = &pdev->dev;
    struct led_priv *priv;

    priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
    if (!priv)
        return -ENOMEM;

    priv->led0 = devm_gpiod_get(dev, "led0", GPIOD_OUT_LOW);
    if (IS_ERR(priv->led0))
        return PTR_ERR(priv->led0);

    priv->led1 = devm_gpiod_get(dev, "led1", GPIOD_OUT_LOW);
    if (IS_ERR(priv->led1))
        return PTR_ERR(priv->led1);

    device_create_file(dev, &dev_attr_led0);
    platform_set_drvdata(pdev, priv);
    return 0;
}

static int led_remove(struct platform_device *pdev)
{
    struct led_priv *priv = platform_get_drvdata(pdev);
    device_remove_file(&pdev->dev, &dev_attr_led0);
    gpiod_set_value(priv->led0, 0);
    gpiod_set_value(priv->led1, 0);
    return 0;
}

static const struct of_device_id led_of_match[] = {
    { .compatible = "myvendor,simple-led" }, { }
};
MODULE_DEVICE_TABLE(of, led_of_match);

static struct platform_driver led_driver = {
    .probe  = led_probe,
    .remove = led_remove,
    .driver = { .name = "simple-led", .of_match_table = led_of_match },
};
module_platform_driver(led_driver);
MODULE_LICENSE("GPL");
```

## 6. 平台驱动框架

### 6.1 核心数据结构

platform_driver是Linux内核中用于平台设备的驱动框架，其核心是probe/remove回调和of_match_table设备树匹配表。匹配流程：内核解析设备树后创建platform_device，驱动注册platform_driver后通过of_match_table与compatible匹配，匹配成功则调用probe()。

### 6.2 module_platform_driver宏

该宏自动生成模块的init和exit函数，简化驱动注册代码，避免手写样板代码。

## 7. 实战驱动：按钮输入驱动

### 7.1 设备树节点

```dts
my-buttons {
    compatible = "myvendor,simple-button";
    button-gpios = <&gpio0 23 GPIO_ACTIVE_LOW>;
};
```

### 7.2 驱动核心逻辑

按钮驱动相比LED驱动增加了中断处理和防抖逻辑：

```c
struct btn_priv {
    struct gpio_desc *button;
    struct device *dev;
    int irq;
    struct timer_list debounce_timer;
    struct input_dev *input;
};

/* 防抖定时器回调：在定时器上下文中读取GPIO并上报事件 */
static void btn_debounce_timer(struct timer_list *t)
{
    struct btn_priv *priv = from_timer(priv, t, debounce_timer);
    int val = gpiod_get_value(priv->button);
    input_report_key(priv->input, BTN_0, val);
    input_sync(priv->input);
}

/* 中断处理：仅启动防抖定时器，不做耗时操作 */
static irqreturn_t btn_isr(int irq, void *data)
{
    struct btn_priv *priv = data;
    mod_timer(&priv->debounce_timer,
              jiffies + msecs_to_jiffies(10));
    return IRQ_HANDLED;
}
```

probe函数中需要依次完成：获取GPIO、注册输入设备、初始化防抖定时器、请求中断。关键点是中断处理函数只启动定时器，真正的按键状态读取和事件上报在定时器回调中完成，这样既保证了中断处理的快速性，又实现了软件防抖。

## 8. 调试与常见问题

### 8.1 调试方法

```bash
cat /sys/kernel/debug/gpio                    # 查看GPIO状态
cat /sys/kernel/debug/pinctrl/pinctrl-maps    # 查看引脚复用
dmesg | grep -i "pin.*already.*requested"       # 检查引脚冲突
ls /sys/bus/platform/drivers/simple-led/      # 检查驱动绑定
```

### 8.2 常见问题排查

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| GPIO占用(-EBUSY) | 其他驱动已请求 | 禁用冲突设备树节点 |
| 引脚复用冲突 | pinctrl未配置 | 添加pinctrl-0引用 |
| 中断不触发 | 极性或级联错误 | 先用双边沿触发定位 |

## 9. 最佳实践

- **使用gpiod API**：旧版gpio_request/gpio_free已废弃，gpiod API与设备树无缝集成，自动处理极性翻转
- **使用devm管理资源**：devm_gpiod_get和devm_request_irq在驱动移除时自动释放，避免泄漏
- **处理延迟探测**：gpiod_get返回-EPROBE_DEFER时直接返回，框架会自动重试probe
- **检查所有返回值**：devm分配的资源在probe失败时自动释放，无需手动goto清理

## 总结

Linux GPIO驱动开发的关键在于理解三层结构：用户空间用libgpiod快速验证，内核空间用gpiod API加设备树开发正式驱动，平台驱动框架提供设备-驱动的自动匹配和生命周期管理。掌握gpiod API、devm资源管理和中断处理这三个核心机制，就能覆盖绝大多数IoT设备的GPIO控制需求。始终使用新版API、始终检查错误、始终用devm管理资源——这三条原则会让你的驱动代码更健壮、更简洁。

## 参考文献

1. Kernel.org, "GPIO Descriptor Driver Interface", Documentation/driver-api/gpio, 2024
2. Kernel.org, "libgpiod - C library and tools", 2024
3. Bootlin, "Embedded Linux Kernel and Driver Development Training", 2024
4. Linus Walleij, "The new GPIO character device API", 2019
5. Linux Kernel Documentation, "Driver Model - Platform Drivers", 2024
