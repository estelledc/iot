# 嵌入式GUI框架LVGL在IoT设备上的移植
> **难度**：🟡 中级 | **领域**：嵌入式图形界面 | **阅读时间**：约 20 分钟

## 引言

想象你在装修一个小户型公寓。空间有限,每一件家具都必须精心选择:太大了放不下,太小了不实用,风格还得统一。嵌入式 GUI 开发面临的正是这种困境:资源有限(几十 KB 的 RAM),却要做出流畅、美观、可交互的界面。LVGL(Light and Versatile Graphics Library)就像一个为小户型量身定制的家具系统:模块化、轻量、还免费。

## 1 LVGL 概述

### 1.1 什么是 LVGL

LVGL 是一个免费、开源的嵌入式图形库,用 C 语言编写,专为资源受限的 MCU 设计:

- 开源协议: MIT(可商用,无限制)
- 语言: C(核心), 支持 C++ 封装
- 设计目标: 在低端 MCU 上实现流畅 GUI
- 社区: GitHub 10K+ Star, 活跃维护

### 1.2 资源需求

| 配置 | Flash | RAM | 适用场景 |
|------|-------|-----|----------|
| 最低 | 64 KB | 16 KB | 简单文字+按钮 |
| 推荐 | 256 KB | 64 KB | 流畅交互界面 |
| 舒适 | 512 KB+ | 128 KB+ | 动画+复杂控件 |

对比: TouchGFX 需要 Cortex-M7 + 512KB RAM,GuiLite 最低只需 32KB Flash + 4KB RAM。

### 1.3 支持的硬件

- MCU: STM32, ESP32, NXP, Nordic, Raspberry Pi Pico 等
- 显示: SPI LCD, I2C OLED, RGB 接口, MIPI DSI
- 输入: 触摸屏, 按键, 编码器, 鼠标

## 2 LVGL 架构

### 2.1 整体架构

```
+---------------------------------------------+
|               Application                    |
|   (创建控件, 设置样式, 注册事件回调)           |
+---------------------------------------------+
|              LVGL Core                       |
|  +----------+  +--------+  +-----------+    |
|  | Object   |  | Style  |  | Animation |    |
|  | System   |  | System |  | Engine    |    |
|  +----------+  +--------+  +-----------+    |
+---------------------------------------------+
|          HAL (硬件抽象层)                     |
|  +-----------+  +----------+  +------+      |
|  | Display   |  | Input    |  | Tick |      |
|  | Driver    |  | Driver   |  |      |      |
|  +-----------+  +----------+  +------+      |
+---------------------------------------------+
|             Hardware                         |
|    MCU + Display + Touch/Button             |
+---------------------------------------------+
```

应用层只关心创建控件和业务逻辑,硬件细节由驱动层处理。

### 2.2 主循环模型

LVGL 采用协作式主循环,不使用 RTOS 也可以运行:

```c
while (1) {
    lv_timer_handler();  // 处理所有 LVGL 任务
    // 其他用户任务...
    delay(5);            // 建议 5ms 调用一次
}
```

如果使用 RTOS,把 `lv_timer_handler()` 放在一个低优先级任务中即可。

## 3 移植步骤

### 3.1 显示驱动: flush 回调

最核心的移植工作:实现一个函数,把 LVGL 渲染好的像素数据写入显示设备:

```c
void my_flush_cb(lv_disp_drv_t *drv, const lv_area_t *area, lv_color_t *color_p)
{
    int32_t x, y;
    for (y = area->y1; y <= area->y2; y++) {
        for (x = area->x1; x <= area->x2; x++) {
            LCD_WritePixel(x, y, color_p->full);
            color_p++;
        }
    }
    lv_disp_flush_ready(drv);  // 通知 LVGL 传输完成
}
```

### 3.2 输入驱动: read 回调

读取触摸/按键状态:

```c
void my_input_read(lv_indev_drv_t *drv, lv_indev_data_t *data)
{
    data->point.x = Touch_GetX();
    data->point.y = Touch_GetY();
    data->state = Touch_IsPressed() ? LV_INDEV_STATE_PRESSED
                                    : LV_INDEV_STATE_RELEASED;
}
```

### 3.3 时钟节拍

LVGL 需要知道时间流逝(动画、延时等):

```c
// 在 SysTick 或定时器中断中调用
void SysTick_Handler(void)
{
    lv_tick_inc(1);  // 每 1ms 调用一次, 传入 1
}
```

## 4 显示驱动选项

### 4.1 全帧缓冲

分配与屏幕分辨率相同的 RAM 缓冲区:

```
320x240x2字节 = 153,600 字节 (约 150KB)
```

优点: 渲染速度最快,无撕裂。缺点: RAM 占用大,低端 MCU 不适合。

### 4.2 部分缓冲

只分配几行到几十行的缓冲区:

```c
static lv_color_t buf[LV_HOR_RES_MAX * 10];  // 10 行缓冲
lv_disp_buf_init(&disp_buf, buf, NULL, LV_HOR_RES_MAX * 10);
```

优点: RAM 占用小(可低至几 KB)。缺点: flush 调用次数多,CPU 占用高。

### 4.3 直接模式

当显示控制器支持 DMA 时,让 DMA 直接从渲染缓冲区传输到屏幕,零 CPU 开销。STM32 的 DMA2D 就是典型用法。

| 方式 | RAM 需求 | CPU 占用 | 适合场景 |
|------|----------|----------|----------|
| 全帧缓冲 | 高 | 低 | 高端 MCU |
| 部分缓冲 | 低 | 高 | 低端 MCU |
| 直接/DMA | 中 | 极低 | 有 DMA 的 MCU |

## 5 控件概览

### 5.1 常用控件

LVGL 提供 30+ 内置控件,覆盖大多数 UI 需求:

| 控件 | 用途 | 典型场景 |
|------|------|----------|
| lv_label | 文字显示 | 状态、数值 |
| lv_btn | 按钮 | 操作触发 |
| lv_slider | 滑条 | 数值调节 |
| lv_chart | 图表 | 数据可视化 |
| lv_table | 表格 | 参数列表 |
| lv_image | 图片 | 图标、背景 |
| lv_textarea | 文本框 | 用户输入 |
| lv_keyboard | 键盘 | 文字输入 |
| lv_arc | 弧形 | 仪表盘 |
| lv_meter | 仪表 | 指针式显示 |

### 5.2 控件创建示例

```c
// 创建一个带标签的按钮
lv_obj_t *btn = lv_btn_create(lv_scr_act());
lv_obj_set_size(btn, 120, 50);
lv_obj_align(btn, LV_ALIGN_CENTER, 0, 0);

lv_obj_t *label = lv_label_create(btn);
lv_label_set_text(label, "Click Me");
lv_obj_center(label);
```

## 6 样式系统

### 6.1 CSS 式样式

LVGL 的样式系统类似 CSS,支持继承和级联:

```c
static lv_style_t style;
lv_style_init(&style);
lv_style_set_bg_color(&style, lv_palette_main(LV_PALETTE_BLUE));
lv_style_set_bg_opa(&style, LV_OPA_COVER);
lv_style_set_border_width(&style, 2);
lv_style_set_border_color(&style, lv_palette_darken(LV_PALETTE_BLUE, 3));
lv_style_set_radius(&style, 8);
lv_style_set_pad_all(&style, 10);

// 应用到控件
lv_obj_add_style(btn, &style, 0);
```

### 6.2 主题

主题是一套全局样式方案,统一控件外观:

- Default: 简洁蓝色主题
- Mono: 单色,适合 OLED
- Simple: 极简风格

切换主题只需一行代码,所有控件自动更新。

### 6.3 样式状态

不同状态可以有不同样式(按下、禁用、聚焦等):

```c
// 按下时背景变深
lv_style_set_bg_color(&style_pressed, lv_palette_darken(LV_PALETTE_BLUE, 2));
lv_obj_add_style(btn, &style_pressed, LV_STATE_PRESSED);
```

## 7 事件系统

### 7.1 事件类型

| 事件 | 触发时机 |
|------|----------|
| LV_EVENT_CLICKED | 按钮点击 |
| LV_EVENT_VALUE_CHANGED | 滑条/开关值变化 |
| LV_EVENT_FOCUSED | 控件获得焦点 |
| LV_EVENT_DEFOCUSED | 控件失去焦点 |
| LV_EVENT_KEY | 按键输入 |

### 7.2 事件回调

```c
void btn_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    if (code == LV_EVENT_CLICKED) {
        // 按钮被点击,执行业务逻辑
        temperature_setpoint += 1;
        update_display();
    }
}

lv_obj_add_event_cb(btn, btn_event_cb, LV_EVENT_CLICKED, NULL);
```

## 8 实战案例: IoT 温控器界面

### 8.1 硬件平台

- MCU: STM32F407 (168 MHz, 192KB RAM)
- 显示: 320x240 IPS SPI LCD
- 触摸: 电阻式触摸屏
- 连接: WiFi (ESP8266 模组)

### 8.2 界面设计

```
+----------------------------------+
|  [WiFi图标]   客厅温控   [设置]  |
|                                  |
|          23.5 C                 |
|        当前温度                  |
|                                  |
|  设定温度: [====|====] 22.0 C   |
|                                  |
|  [时间表图表]                    |
|  06:00  08:00  18:00  22:00     |
|   20     22     22     18       |
|                                  |
|  模式: [制热] [制冷] [自动]      |
+----------------------------------+
```

### 8.3 关键代码片段

```c
// 温度显示标签
lv_obj_t *temp_label = lv_label_create(lv_scr_act());
lv_label_set_text(temp_label, "23.5 C");
lv_obj_set_style_text_font(temp_label, &lv_font_montserrat_48, 0);

// 设定温度滑条
lv_obj_t *slider = lv_slider_create(lv_scr_act());
lv_slider_set_range(slider, 16, 30);
lv_slider_set_value(slider, 22, LV_ANIM_ON);

// 模式按钮组
lv_obj_t *btn_heat = lv_btn_create(lv_scr_act());
lv_obj_t *lbl = lv_label_create(btn_heat);
lv_label_set_text(lbl, "Heat");
```

## 9 性能优化

### 9.1 部分渲染

LVGL 只重绘脏区域(dirty area),不重绘整个屏幕。控制脏区域:

- 避免不必要的控件属性修改
- 对频繁更新的数值,只更新 label 文本,不重建控件
- 使用 `lv_obj_invalidate()` 手动标记

### 9.2 GPU 加速

STM32 的 DMA2D(Chrom-ART)可加速:

- 矩形填充
- 图像混合
- 颜色格式转换

```c
// LVGL 内置 DMA2D 支持, 在 lv_conf.h 中启用
#define LV_USE_GPU_STM32_DMA2D 1
```

开启 DMA2D 后,界面刷新 CPU 占用可降低 50-80%。

### 9.3 其他优化

- 避免全屏重绘: 只更新变化的部分
- 使用 canvas 绘制复杂图形: 比重建控件高效
- 适当降低刷新率: 30fps 对大多数 IoT 界面足够

## 10 内存优化

### 10.1 自定义内存分配器

```c
// 使用 RTOS 内存池替代 malloc
void *my_alloc(size_t size) { return pvPortMalloc(size); }
void my_free(void *ptr) { vPortFree(ptr); }

lv_mem_custom_init(my_alloc, my_free);
```

### 10.2 减少控件数量

- 合并相似控件
- 复用控件(切换显示内容而非创建新控件)
- 用 canvas 替代复杂布局

### 10.3 共享样式

多个控件使用相同样式对象,而非每个控件单独创建:

```c
static lv_style_t common_btn_style;  // 所有按钮共享
lv_style_init(&common_btn_style);
// ... 设置一次 ...
lv_obj_add_style(btn1, &common_btn_style, 0);
lv_obj_add_style(btn2, &common_btn_style, 0);
```

## 11 与其他框架对比

| 特性 | LVGL | TouchGFX | Embedded Wizard | GuiLite | AWTK |
|------|------|----------|-----------------|---------|------|
| 开源 | MIT | 商业 | 商业 | Apache 2.0 | LGPL |
| 最低 RAM | 16KB | 512KB | 256KB | 4KB | 32KB |
| MCU 要求 | 16MHz+ | M7 | M4+ | 任意 | M3+ |
| 控件数量 | 30+ | 25+ | 30+ | 5 | 20+ |
| 生态 | 活跃 | ST 生态 | 商业支持 | 极简 | 中文生态 |
| 设计工具 | SquareLine | Designer | Studio | 无 | Designer |

TouchGFX 只支持 ST MCU,Embedded Wizard 费用高。LVGL 在开源免费和功能丰富之间取得了最佳平衡。

## 总结

LVGL 为资源受限的 IoT 设备提供了可用的 GUI 方案:

1. 资源需求低: 64KB Flash + 16KB RAM 即可启动
2. 移植简单: 三个回调函数(flush/read/tick)即可运行
3. 控件丰富: 30+ 内置控件, CSS 式样式系统
4. 性能可调: 从部分缓冲到 DMA 加速,适配不同硬件
5. 社区活跃: 问题能快速得到帮助

选择建议: Cortex-M0/M3 用 GuiLite, Cortex-M4+ 用 LVGL, Cortex-M7+ 可考虑 TouchGFX。

## 参考文献

1. LVGL Documentation. https://docs.lvgl.io/
2. Gaitonde P. Mastering STM32. Leanpub, 2020.
3. STM32 DMA2D Application Note AN5043. STMicroelectronics, 2017.
4. SquareLine Studio. https://squareline.io/
5. TouchGFX Documentation. https://touchgfx.github.io/documentation/
