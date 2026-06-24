# 裸机编程与RTOS：IoT项目决策框架

> **难度**：🟢 初级 | **领域**：嵌入式架构决策 | **阅读时间**：约 18 分钟

## 引言

想象你一个人在家做晚饭：先切菜，再开火炒菜，顺便盯着锅别糊了，手机响了还得接电话。你只能在几件事之间来回跑——没有帮手，全靠自己的脑子安排顺序。这就是"裸机编程"：一个 CPU，一个大循环，所有事情排队做。

现在想象你请了三个帮手：一个专管炒菜，一个专管洗碗，一个专管接电话。每个人各干各的，偶尔互相喊一声"菜好了，端走"。这就是 RTOS 编程：多个任务并行运行，由调度器统一管理。

两种方式没有绝对的好坏——如果只是煮碗面，请三个帮手反而浪费。IoT 项目该选哪种？这篇文章给你一个决策框架。

## 1. 裸机编程模型

### 1.1 超级循环 (Super Loop)

所有逻辑放在 `while(1)` 里依次执行，是最经典的裸机模型：

```c
int main(void) {
    hardware_init();
    while (1) {
        read_sensor();     // 读传感器
        process_data();    // 处理数据
        send_uart();       // 串口发送
        check_button();    // 检查按键
        delay_ms(100);
    }
}
```

特点：结构直观，但任何一个函数卡住，后面所有逻辑都被阻塞。

### 1.2 中断驱动模型

在超级循环基础上引入中断，让紧急事务能立刻响应：

```c
// ISR —— 仅做数据搬运，越短越好
void USART1_IRQHandler(void) {
    if (USART1->ISR & USART_ISR_RXNE) {
        rx_buffer[rx_head++] = USART1->RDR;
        rx_flag = 1;                  // 设标志位
    }
}

// 主循环处理非紧急逻辑
while (1) {
    if (rx_flag) { process_command(); rx_flag = 0; }
    read_sensor();
    update_display();
}
```

核心原则：ISR 尽量短，只搬运数据；主循环轮询标志位处理业务逻辑。

### 1.3 裸机模型变体

| 变体 | 结构 | 适用场景 |
|------|------|----------|
| 纯轮询 | while(1) 顺序执行 | 无实时性要求的简单系统 |
| 中断 + 轮询 | ISR 设标志，主循环处理 | 大多数简单 IoT 节点 |
| 前后台 | ISR 做关键处理，主循环做后台 | 对实时性有部分要求 |
| 状态机驱动 | while(1) 内按状态切换 | 协议解析、UI 逻辑 |

## 2. RTOS 编程模型

### 2.1 任务与调度

RTOS 把程序拆成多个独立任务，每个任务是独立的执行流：

```c
void sensor_task(void *pvParameters) {
    while (1) {
        float temp = read_temperature();
        xQueueSend(temp_queue, &temp, portMAX_DELAY);
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

void display_task(void *pvParameters) {
    float temp;
    while (1) {
        if (xQueueReceive(temp_queue, &temp, portMAX_DELAY))
            update_lcd(temp);
    }
}

int main(void) {
    hardware_init();
    temp_queue = xQueueCreate(10, sizeof(float));
    xTaskCreate(sensor_task,  "Sensor",  256, NULL, 2, NULL);
    xTaskCreate(display_task, "Display", 256, NULL, 1, NULL);
    vTaskStartScheduler();
}
```

关键区别：每个任务有自己的栈和执行上下文；高优先级任务就绪时立即抢占低优先级；任务间通过 IPC 通信。

### 2.2 调度策略

| 策略 | 原理 | 特点 |
|------|------|------|
| 优先级抢占 | 高优先级就绪立即抢占 | 实时性好，需防优先级反转 |
| 时间片轮转 | 同优先级任务轮流执行 | 公平，适合无严格实时要求 |
| 协作调度 | 任务主动让出 CPU | 确定性高，但依赖任务配合 |

FreeRTOS 默认使用优先级抢占 + 可选时间片，是 IoT 项目最常用的配置。

### 2.3 进程间通信 (IPC)

裸机靠全局变量和标志位协调，RTOS 提供更安全的原语：

```c
// 互斥锁 —— 保护共享资源
SemaphoreHandle_t uart_mutex;
void task_a(void *p) {
    while (1) {
        xSemaphoreTake(uart_mutex, portMAX_DELAY);
        printf("Task A sending...\n");
        xSemaphoreGive(uart_mutex);
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}

// 消息队列 —— ISR 向任务传递数据
void button_isr(void) {
    uint8_t evt = BTN_PRESSED;
    xQueueSendFromISR(evt_queue, &evt, NULL);  // ISR 用 FromISR 版本
}
```

| IPC 类型 | 用途 | ISR 可用 |
|----------|------|----------|
| 队列 (Queue) | 传递数据 | FromISR 变体可以 |
| 信号量 (Semaphore) | 同步/计数 | FromISR 变体可以 |
| 互斥锁 (Mutex) | 互斥访问 | 不可以 (会阻塞) |
| 事件组 (Event Group) | 多条件同步 | FromISR 变体可以 |

## 3. 资源开销对比

### 3.1 内存占用

| 资源 | 裸机 | FreeRTOS 最小配置 | FreeRTOS 常用配置 |
|------|------|-------------------|-------------------|
| Flash | 0 KB 额外 | ~6 KB | ~12 KB |
| RAM (内核) | 0 KB 额外 | ~0.5 KB | ~1.5 KB |
| RAM (每任务栈) | 共享主栈 | 0.2-1 KB | 0.5-2 KB |
| RAM (3 任务总) | ~0.5 KB | ~2-3 KB | ~4-6 KB |

任务栈是最大的 RAM 开销来源。一个 3 任务系统的 RAM 开销约是裸机的 4-8 倍。

### 3.2 CPU 开销

- 上下文切换：~50-200 个时钟周期 (Cortex-M4 @ 100MHz 约 0.5-2 us)
- Tick 中断：通常 1ms 一次，每次约 10-30 个时钟周期
- 总开销：典型场景下 < 2% CPU 时间，可忽略；真正需关注的是 RAM

## 4. 时序确定性

| 指标 | 裸机 | RTOS |
|------|------|------|
| 最小中断延迟 | 几个时钟周期 | 几个时钟周期 |
| 最大中断延迟 | 取决于主循环长度，不可预测 | 由内核配置决定，有上界 |
| 任务响应时间 | 轮询间隔决定，不可预测 | 优先级调度，可预测 |

裸机的核心问题：如果主循环某函数执行了 50ms，按键响应可能等 50ms。RTOS 中高优先级任务可在几 us 内被调度。

实时性分类：硬实时 (错过 = 灾难，如安全气囊) > 固实时 (错过 = 无效，如视频帧) > 软实时 (错过 = 降质，如 UI 卡顿)。大多数 IoT 属软/固实时，两者都能满足；硬实时则 RTOS 优势明显。

## 5. 开发复杂度与可维护性

| 维度 | 裸机 | RTOS |
|------|------|------|
| 入门门槛 | 低 (顺序思维) | 中 (需理解调度/同步) |
| 并发处理 | 靠标志位和状态机 | 靠任务和 IPC |
| 调试难度 | 低 (路径明确) | 中 (竞态条件难复现) |
| 代码耦合度 | 高 (逻辑混在一起) | 低 (任务间解耦) |

裸机项目功能越多，`while(1)` 越臃肿，改一处怕影响他处。RTOS 中每个功能独立为任务，增删互不影响。

团队规模上：1 人裸机高效，2-3 人开始冲突 (都改 main.c)，4+ 人裸机合并困难而 RTOS 可按任务分工并行。类比：裸机是一口锅，RTOS 是多口灶。

## 6. 裸机更优的场景

### 6.1 简单传感器节点

```c
// 温湿度节点 —— 裸机完全够用
int main(void) {
    sensor_init(); lora_init();
    while (1) {
        float temp = read_temp();
        float humi = read_humidity();
        lora_send(&temp, &humi);
        deep_sleep(60);    // 深度睡眠 60 秒，功耗 < 5uA
    }
}
```

不用 RTOS 的原因：功能单一无并发需求；睡眠期间 RTOS 定时器仍耗电；RAM 只有 2-4 KB 给内核分不出多少。

### 6.2 成本敏感产品

百万级出货时，RTOS 需更大 RAM 的 MCU 可能每个多 0.5-1 元，百万出货就是 100 万额外成本。裸机能跑在 STM32G0 (8KB RAM)，RTOS 可能需要 STM32G4 (32KB RAM)。

### 6.3 超低功耗场景

纽扣电池设备 (如智能水表)：活跃周期 < 100ms，深度睡眠 > 99.9% 时间。RTOS 的 Tick 中断会阻止进入最深层睡眠。

## 7. RTOS 更优的场景

### 7.1 多并发活动

典型场景——智能门锁：BLE 保持连接、指纹模块异步响应、键盘输入实时检测、电机控制精确定时、OTA 后台升级。裸机需要大量状态机协调，RTOS 中每个活动一个任务，逻辑清晰。

### 7.2 网络协议栈

```c
void network_task(void *p) {
    while (1) { mqtt_process(); vTaskDelay(pdMS_TO_TICKS(10)); }
}
void sensor_task(void *p) {
    while (1) {
        float val = read_sensor();
        mqtt_publish("sensor/topic", &val, sizeof(val));
        vTaskDelay(pdMS_TO_TICKS(5000));
    }
}
```

裸机处理网络栈极痛苦：TCP/IP 天然需要并发，网络延迟不可预测，MQTT/HTTP 有超时重传逻辑。

### 7.3 复杂状态管理

裸机中状态变量散落各处、互相依赖；RTOS 中每个状态封装在对应任务内部，接口清晰。

## 8. 混合方案

### 8.1 裸机 + 协作式调度器

介于裸机和 RTOS 之间的折中方案：

```c
#define MAX_TASKS 8
typedef struct {
    void (*task_func)(void);
    uint32_t period_ms;
    uint32_t last_run;
} CoopTask;

CoopTask tasks[MAX_TASKS];
uint8_t task_count = 0;

void scheduler_add(void (*func)(void), uint32_t period_ms) {
    tasks[task_count].task_func = func;
    tasks[task_count].period_ms = period_ms;
    tasks[task_count].last_run = 0;
    task_count++;
}

void scheduler_run(void) {
    while (1) {
        uint32_t now = get_tick();
        for (uint8_t i = 0; i < task_count; i++) {
            if (now - tasks[i].last_run >= tasks[i].period_ms) {
                tasks[i].task_func();
                tasks[i].last_run = now;
            }
        }
        __WFI();
    }
}

int main(void) {
    hardware_init();
    scheduler_add(sensor_read,    1000);
    scheduler_add(display_update,  500);
    scheduler_add(battery_check,   5000);
    scheduler_run();
}
```

特点：无优先级抢占，任务须主动返回；RAM 开销极小；Flash 开销 < 1 KB；适合中等复杂度、无硬实时要求的场景。

### 8.2 RTOS + 裸机风格 ISR

电机控制等需 us 级响应的场景，ISR 直接触发不走 RTOS 调度：

```c
void timer_isr(void) {           // 高频定时 —— 裸机风格
    stepper_update();             // ISR 直接执行，保证时序
}
void sensor_task(void *p) {      // 低频处理 —— RTOS 任务
    while (1) { process_data(); vTaskDelay(pdMS_TO_TICKS(100)); }
}
```

## 9. 实际项目决策示例

### 9.1 智能温控器 -> RTOS

需求：BLE 配网 + PID 控制 + LCD 触摸 + OTA，MCU: STM32L4 (64KB RAM)，多人开发。

```
多并发活动? ── YES -> 有网络栈? ── YES -> RAM > 16KB? ── YES -> 多人开发? ── YES
  -> 选择 FreeRTOS
```

### 9.2 烟雾报警器 -> 裸机

需求：单传感器 + 蜂鸣器 + 纽扣电池 3 年，MCU: STM32G0 (8KB RAM)，单人开发。

```
多并发活动? ── NO -> RAM < 8KB? ── YES -> 超低功耗? ── YES -> 单人开发? ── YES
  -> 选择裸机 (中断驱动)
```

### 9.3 工业网关 -> RTOS + 裸机 ISR

需求：Modbus + CAN + 4G/MQTT + OTA，MCU: STM32H7 (512KB RAM)，Modbus 有硬实时要求。

```
多并发活动? ── YES -> 有网络栈? ── YES -> RAM > 16KB? ── YES -> 硬实时? ── YES
  -> 选择 FreeRTOS + 裸机风格 ISR
```

## 10. 从裸机迁移到 RTOS

### 10.1 渐进式迁移

**第一阶段：拆分模块** —— 把 while(1) 中的功能拆成独立函数，减少全局变量，不需 RTOS。

**第二阶段：引入协作式调度器** —— 用简易调度器替代超级循环，验证各模块独立正确性，RAM 开销几乎不变。

**第三阶段：替换为 RTOS** —— 将调度器任务逐个替换为 FreeRTOS 任务，用队列替代全局变量，用互斥锁保护共享资源，每替换一个任务就测试。

### 10.2 迁移常见坑

| 坑 | 现象 | 解决方案 |
|----|------|----------|
| 栈溢出 | 任务跑飞/HardFault | 任务栈留 30% 余量，开启溢出检测 |
| 忘加互斥锁 | 数据偶尔错乱 | 共享资源必须加 Mutex |
| ISR 调阻塞 API | 系统死锁 | ISR 只用 FromISR 后缀 API |
| 优先级反转 | 高优先级卡住 | 开启优先级继承 (Mutex 自带) |
| 忘喂狗 | 系统重启 | 单独看门狗任务监控存活 |

### 10.3 迁移检查清单

- [ ] 裸机模块已封装为独立函数
- [ ] 全局变量已列出，标注哪些需保护
- [ ] ISR 已改为"设标志 + 主循环处理"
- [ ] RAM 预算已评估 (内核 + 任务栈 + 队列)
- [ ] 调试手段已准备 (FreeRTOS Viewer / SystemView)
- [ ] 回退方案已确定 (保留裸机版本，Git 分支管理)

## 总结

裸机与 RTOS 不是非此即彼，而是根据项目需求匹配的工具：

- **选裸机**：功能简单、资源极度受限、超低功耗、单人开发、出货量极大
- **选 RTOS**：多并发活动、网络协议栈、多人协作、功能持续迭代
- **选混合**：中等复杂度、部分实时要求、暂时不想引入 RTOS 全套

核心判断只有两个问题：(1) 项目是否有多个需要"同时"进行的活动？(2) 团队是否 > 1 人且功能在持续增加？两个"否"选裸机，任一"是"认真考虑 RTOS。

最后提醒：不要因为"学技术"而选 RTOS。简单传感器节点裸机 100 行搞定，没必要上 RTOS 写 500 行。选最简方案解决问题，才是工程思维。

## 参考文献

1. Richard Barry. *Mastering the FreeRTOS Real Time Kernel*. 2016. FreeRTOS 官方教程，涵盖任务调度、IPC 和内存管理。
2. Jean J. Labrosse. *MicroC/OS-II: The Real-Time Kernel*. CRC Press, 1998. 嵌入式 RTOS 经典教材，调度理论讲解清晰。
3. ARM. *Cortex-M Programming Guide to Interrupts*. ARM DEN0034A, 2020. 中断配置与优先级管理权威参考。
4. Jack Ganssle. *The Art of Programming Embedded Systems*. Academic Press, 1992. 裸机架构设计与状态机方法的经典著作。
5. STM32. *STM32CubeMX FreeRTOS Implementation Guide*. STMicroelectronics AN4989, 2020. 从裸机迁移到 FreeRTOS 的实践指南。
