# OLED显示屏SSD1306驱动接口与图形库
> **难度**：🟢 初级 | **领域**：显示接口设计 | **阅读时间**：约 18 分钟

## 引言

想象一块自发光的告示牌：每个像素点都像一盏独立的小灯，不需要背后打光就能自己亮起来。OLED就是这样工作的——每个像素由有机发光材料构成，通电即发光。SSD1306是驱动这种"自发光告示牌"最常用的控制器芯片，本文讲解如何与它通信、如何画图、以及在IoT中如何用好它。

## 1 OLED显示基础

### 1.1 有机LED原理

OLED使用有机化合物作为发光层：电流通过有机薄膜时，电子和空穴在发光层复合释放光子。每个像素独立发光，无需背光。

### 1.2 与LCD对比

| 特性     | OLED             | LCD              |
|---------|------------------|------------------|
| 背光     | 不需要            | 需要              |
| 对比度   | 极高              | 1000:1左右        |
| 可视角度  | 接近180度         | 依赖面板类型       |
| 响应速度  | 微秒级            | 毫秒级            |
| 黑色表现  | 纯黑(不发光)       | 背光漏光偏灰       |

### 1.3 IoT中的定位

0.49"-2.42"常见尺寸，单色最普遍，分辨率64x32到256x64，功耗低，模块价格低廉。

## 2 SSD1306控制器概述

### 2.1 基本规格

- 分辨率：128x64 或 128x32 像素，单色(1bit/pixel)
- 内置电荷泵：无需外部高电压
- 显示RAM：1024字节(128x64)

### 2.2 内置电荷泵

OLED驱动需7-9V，但模块只需3.3V/5V供电。SSD1306内置电荷泵升压，软件使能：

```
0x8D (电荷泵设置) -> 0x14 (使能)
```

初始化序列中必须包含此命令。

## 3 接口选择：I2C vs SPI

### 3.1 I2C接口

只需2根信号线(SCL + SDA)：

- 优点：只占2个GPIO，标准协议兼容性好，可挂多设备
- 缺点：速度慢(全屏刷新约30ms@400kHz)，需命令字节前缀区分命令/数据

### 3.2 SPI接口

需要4根信号线(CS + DC + SCLK + MOSI)：

- 优点：速度快(最高10MHz，全屏刷新约1-2ms)，适合动画
- 缺点：占4个GPIO，廉价模块通常只提供I2C版本

| 场景             | 推荐 | 理由               |
|-----------------|------|-------------------|
| 静态显示/低刷新   | I2C  | 省GPIO，够用        |
| 动画/高刷新率     | SPI  | 速度优势明显        |
| GPIO紧张         | I2C  | 只需2线            |

## 4 I2C通信协议

### 4.1 从机地址

- **0x3C**：SA0引脚接地(最常见)
- **0x3D**：SA0引脚接高

### 4.2 命令与数据区分

I2C通过控制字节前缀区分：

| 控制字节 | 含义           | 用途            |
|---------|---------------|----------------|
| 0x00    | 后续是命令字节  | 发送配置命令      |
| 0x40    | 后续是显示数据  | 写入帧缓冲区      |
| 0x80    | 单字节命令      | 紧跟1字节命令     |

### 4.3 I2C代码示例

```c
void ssd1306_write_cmd(uint8_t cmd) {
    i2c_cmd_handle_t h = i2c_cmd_link_create();
    i2c_master_start(h);
    i2c_master_write_byte(h, 0x78, true);  // 地址 + 写
    i2c_master_write_byte(h, 0x00, true);  // 控制字节: 命令
    i2c_master_write_byte(h, cmd, true);   // 命令字节
    i2c_master_stop(h);
    i2c_master_cmd_begin(I2C_NUM_0, h, 100 / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(h);
}

void ssd1306_write_data(const uint8_t *buf, int len) {
    i2c_cmd_handle_t h = i2c_cmd_link_create();
    i2c_master_start(h);
    i2c_master_write_byte(h, 0x78, true);
    i2c_master_write_byte(h, 0x40, true);  // 控制字节: 数据
    i2c_master_write(h, buf, len, true);
    i2c_master_stop(h);
    i2c_master_cmd_begin(I2C_NUM_0, h, 100 / portTICK_PERIOD_MS);
    i2c_cmd_link_delete(h);
}
```

## 5 SPI通信

SPI通过DC引脚区分命令(DC=0)和数据(DC=1)：

```
写命令: CS=0, DC=0, 发送cmd, CS=1
写数据: CS=0, DC=1, 发送data, CS=1
```

10MHz时钟下全屏传输约0.82ms，远快于I2C。

## 6 初始化序列

### 6.1 完整初始化命令

```c
const uint8_t init_cmds[] = {
    0xAE,         // 显示关闭
    0xD5, 0x80,   // 时钟分频
    0xA8, 0x3F,   // 多路复用比: 64(128x64)
    0xD3, 0x00,   // 显示偏移: 0
    0x40,         // 起始行: 0
    0x8D, 0x14,   // 电荷泵: 使能(关键!)
    0x20, 0x00,   // 寻址模式: 水平寻址
    0xA1,         // 段重映射(根据接线)
    0xC8,         // COM扫描方向(根据接线)
    0xDA, 0x12,   // COM引脚配置
    0x81, 0xCF,   // 对比度: 207
    0xD9, 0xF1,   // 预充电周期
    0xDB, 0x40,   // VCOMH电压
    0xA4,         // 正常显示(非全亮)
    0xA6,         // 正常显示(非反色)
    0xAF,         // 显示开启
};
```

### 6.2 关键命令

| 命令     | 功能         | 说明                     |
|---------|-------------|-------------------------|
| 0x8D    | 电荷泵控制   | 必须使能(0x14)，否则无显示 |
| 0xA1/A0 | 段重映射     | 根据模块方向选择          |
| 0xC8/C0 | COM扫描方向  | 根据模块方向选择          |
| 0x81    | 对比度设置   | 0-255，值越大越亮         |
| 0x20    | 寻址模式     | 0=水平，1=垂直，2=页寻址  |

## 7 显示内存组织

### 7.1 页(Page)结构

128x64显示RAM分为8个页，每页8像素高，每页128列，每列1字节(8bit对应8行像素)。

### 7.2 像素到位的映射

字节中最低位对应最上面的像素：D7...D0对应行7...行0(页内)。注意竖向排列，对字体渲染有影响。

### 7.3 寻址模式

- **水平寻址(最常用)**：写完一列自动移到下一列，写完一页跳到下一页，适合连续写入整屏
- **垂直寻址**：写完一页移到下一页同列，适合纵向绘制
- **页寻址**：写完一列移到下一列，不跨页，适合只更新某一页

## 8 图形库

### 8.1 Adafruit SSD1306 + GFX

Arduino生态最流行方案，API成熟，文档丰富：

```c
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

Adafruit_SSD1306 display(128, 64, &Wire, -1);

void setup() {
    display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 0);
    display.println("Hello OLED!");
    display.display();
}
```

### 8.2 u8g2通用库

支持数百种OLED/LCD控制器，字体丰富，内存模式可选(F=全缓冲，1/2=页缓冲)。

### 8.3 自定义帧缓冲方案

资源受限MCU可自写轻量驱动：

```c
static uint8_t fb[1024];  // 128x64 / 8

void fb_set_pixel(int x, int y) {
    if (x < 0 || x >= 128 || y < 0 || y >= 64) return;
    fb[x + (y / 8) * 128] |= (1 << (y & 7));
}

void fb_clear(void) { memset(fb, 0, sizeof(fb)); }
void fb_flush(void) { ssd1306_write_data(fb, 1024); }
```

完全可控，最小内存占用，但需自己实现绘图函数。

## 9 绘图基础

### 9.1 基本图元

| 图元   | 核心算法            | 说明           |
|--------|--------------------|---------------|
| 像素   | 直接置位帧缓冲字节位  | 最基本操作      |
| 线段   | Bresenham算法       | 整数运算无浮点  |
| 矩形   | 水平线填充           | 速度最快       |
| 圆     | 中点圆算法           | 对称8点优化    |
| 文字   | 字模查表 + 像素置位  | 需要字体数据    |

### 9.2 Bresenham画线

```c
void fb_draw_line(int x0, int y0, int x1, int y1) {
    int dx = abs(x1 - x0), dy = -abs(y1 - y0);
    int sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    int err = dx + dy;
    while (1) {
        fb_set_pixel(x0, y0);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}
```

## 10 IoT实例：传感器数据显示

### 10.1 需求

0.96寸OLED显示SHT30温湿度数据，每秒更新，ESP32主控。

### 10.2 实现

```c
void sensor_display_task(void *arg) {
    char line1[24], line2[24];
    float temp, humi;

    ssd1306_init();
    while (1) {
        sht30_read(&temp, &humi);
        snprintf(line1, sizeof(line1), "Temp: %.1f C", temp);
        snprintf(line2, sizeof(line2), "Humi: %.1f %%", humi);

        ssd1306_clear();
        ssd1306_draw_str(0, 0, line1);
        ssd1306_draw_str(0, 16, line2);
        ssd1306_refresh();
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}
```

### 10.3 优化：局部刷新

只更新温度所在页(2页=256字节)，比全屏1024字节减少75%传输量：

```c
ssd1306_set_column_addr(0, 127);
ssd1306_set_page_addr(0, 1);
ssd1306_write_data(&fb[0], 256);
```

## 11 电源优化

### 11.1 睡眠模式

```c
// 睡眠：关闭显示和电荷泵
ssd1306_write_cmd(0xAE);     // 关闭显示
ssd1306_write_cmd(0x8D);
ssd1306_write_cmd(0x10);     // 关闭电荷泵

// 唤醒
ssd1306_write_cmd(0x8D);
ssd1306_write_cmd(0x14);     // 重新使能电荷泵
ssd1306_write_cmd(0xAF);     // 开启显示
```

### 11.2 降低对比度

对比度从0xCF降到0x40，功耗可降低约30-50%，但显示变暗。

## 12 常见问题

### 12.1 I2C地址冲突

SSD1306默认0x3C可能与其它I2C设备冲突。解决：改SA0引脚变地址为0x3D；或用I2C多路复用器TCA9548A。

### 12.2 残影与烧屏

OLED长时间显示静态内容可能导致残影(可恢复)或烧屏(永久)：

- 预防：定期全屏刷新，避免长时间显示固定画面
- 降低对比度和亮度
- 重要信息区域可定期移位显示

### 12.3 显示方向不对

调整段重映射(0xA0/0xA1)和COM扫描方向(0xC0/0xC8)组合，直到方向正确。

## 总结

SSD1306是IoT小尺寸显示的经典方案，I2C接口布线简单，SPI更快。掌握显示内存的页结构和寻址模式是高效驱动的关键。图形库方面，Adafruit适合快速原型，u8g2覆盖更广，自写驱动最精简。OLED适合需要高对比度、小尺寸显示的IoT场景，但要注意烧屏预防和功耗管理。

## 参考文献

1. Solomon Systech, "SSD1306 Datasheet", Rev 1.1, 2008
2. Adafruit Industries, "Adafruit SSD1306 Library Documentation", 2023
3. Oliver Kraus, "u8g2: Library for Monochrome Displays", GitHub, 2024
4. J. R. Sheats, "OLED Display Technology: An Overview", J. Mater. Sci., 2004
5. Espressif Systems, "ESP32 I2C Driver Documentation", ESP-IDF Guide, 2024
