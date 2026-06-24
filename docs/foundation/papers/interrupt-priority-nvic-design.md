# NVIC中断优先级配置与嵌套中断设计
> **难度**：🟡 中级 | **领域**：嵌入式中断系统 | **阅读时间**：约 20 分钟

## 引言

想象你在餐厅当服务员: 同时有客人叫点菜、厨房出菜铃响了、还有电话要接. 你必须决定先处理哪个 -- 厨房出菜最紧急 (菜凉了就毁了), 电话其次, 点菜可以稍等. 如果正在接电话时厨房铃响, 你需要暂停通话去端菜, 端完再回来继续接电话. 这就是嵌套中断的日常版.

Cortex-M 中的 NVIC (Nested Vectored Interrupt Controller) 就是那个帮你排优先级、允许打断、保证不乱的 "餐厅经理". 本文从寄存器到底层机制, 系统拆解 NVIC 的优先级配置与嵌套中断设计.

## 1. NVIC 架构总览

### 1.1 NVIC 在 Cortex-M 中的位置

NVIC 是 Cortex-M 处理器内核的紧耦合组件, 直接挂载在处理器内部总线上:

- 中断响应延迟可预测 (固定 12 个时钟周期)
- 中断向量表位于内存, 软件可重定位
- 优先级判断逻辑在硬件层完成, 零软件开销

```
+--------------------------------------------------+
|                  Cortex-M Core                    |
|  +----------+    +----------+    +------------+  |
|  |   CPU    |<-->|   NVIC   |<-->|   SCB      |  |
|  +----------+    | Priority |    | VectorTab  |  |
|                  | Masking  |    | SysTick    |  |
|                  +----+-----+    +------------+  |
+-----------------------+---------------------------+
                        |
              +---------+---------+
              | External IRQs     |
              | GPIO, UART, ...   |
              +-------------------+
```

### 1.2 NVIC 核心能力

| 特性 | 说明 |
|------|------|
| 可屏蔽中断数 | M0: 32, M3/M4/M7: 240 |
| 优先级位宽 | 3-8 bit (实现定义), 常见 4 bit = 16 级 |
| 自动上下文保存 | 硬件自动压栈 xPSR/PC/LR/R12/R3-R0 |
| 尾链 Tail-chaining | 连续中断免出栈/压栈开销 |
| 晚到 Late-arriving | 更高优先级中断可在入栈阶段抢占 |

## 2. 优先级分组: 抢占优先级与子优先级

### 2.1 优先级位拆分原理

NVIC 优先级寄存器为 8 位, Cortex-M 只使用高位. STM32 使用 4 位 (bit[7:4]), 分成两组:

- **抢占优先级 (Preemption Priority)**: 数值越小优先级越高; 高抢占优先级可以打断低抢占优先级的中断
- **子优先级 (Sub-priority)**: 同一抢占优先级内的排队顺序; 数值越小越先执行, 不能嵌套抢占

SCB_AIRCR 的 PRIGROUP 字段决定分组方式:

| PRIGROUP | 抢占位 | 子优先级位 | 抢占级数 | 子优先级级数 |
|----------|--------|-----------|---------|-------------|
| 0 | - | [7:4] | 1 | 16 |
| 1 | [7] | [6:4] | 2 | 8 |
| 2 | [7:6] | [5:4] | 4 | 4 |
| 3 | [7:5] | [4] | 8 | 2 |
| 4 | [7:4] | - | 16 | 1 |

> 注意: PRIGROUP 5-7 在 4 位实现中与 4 效果相同.

### 2.2 分组选择策略

- 无嵌套需求 (简单裸机): PRIGROUP = 0, 所有中断平级按自然顺序处理
- 少量嵌套 (典型 IoT): PRIGROUP = 2, 4 级抢占 + 4 级子优先级
- 深度嵌套 (RTOS): PRIGROUP = 4, 16 级抢占优先级 (FreeRTOS 推荐分组)

### 2.3 STM32 HAL 分组配置

```c
// 方案 A: 2 位抢占 + 2 位子优先级 (推荐通用场景)
HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_2);

// 方案 B: 4 位全部抢占 (FreeRTOS 推荐分组)
HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_4);
```

## 3. NVIC 寄存器详解

### 3.1 寄存器总览

| 寄存器 | 全称 | 功能 | 访问 |
|--------|------|------|------|
| ISER | Interrupt Set-Enable Register | 使能中断 | RW |
| ICER | Interrupt Clear-Enable Register | 禁用中断 | RW |
| ISPR | Interrupt Set-Pending Register | 挂起中断 | RW |
| ICPR | Interrupt Clear-Pending Register | 解除挂起 | RW |
| IPR | Interrupt Priority Register | 设置优先级 | RW |
| IABR | Interrupt Active Bit Register | 读取活跃状态 | RO |

### 3.2 使能与挂起寄存器

```c
// 使能中断
NVIC_EnableIRQ(USART1_IRQn);          // CMSIS 封装
NVIC->ISER[37 / 32] = (1UL << (37 % 32)); // 直接寄存器

// 禁用中断 (注意: 不清除已挂起状态, 中断仍会触发一次)
NVIC_DisableIRQ(USART1_IRQn);

// 软件触发中断 (常用于软中断/测试)
NVIC_SetPendingIRQ(IRQn);

// 清除挂起标志 (防止使能后立即触发)
NVIC_ClearPendingIRQ(IRQn);
```

### 3.3 优先级寄存器 (IPR)

每个中断对应一个字节, 只有高位有效. STM32 使用 bit[7:4]:

```c
// 4 位实现下, 优先级值必须左移 4 位
NVIC->IP[37] = 0x40;  // 直接写寄存器 (抢占=1, 子=0, GROUP2)

// CMSIS 标准函数 (内部自动左移, 范围 0-15)
NVIC_SetPriority(USART1_IRQn, 4);

// STM32 HAL 封装 (最常用, 自动按分组解码)
HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);
```

## 4. 中断延迟优化机制

### 4.1 标准中断响应

从 IRQ 信号到 ISR 第一条指令执行, Cortex-M 需要固定 12 个时钟周期:

```
时钟:  T0  T1  ... T8  T9  T10 T11 T12
        |-- 入栈 (8 regs) --|-- 取向量 --|- 处理 -|
IRQ:    ^                                        v
                                              ISR 执行
```

### 4.2 尾链 (Tail-chaining)

ISR 执行完毕时, 如果有其他中断正在挂起, 处理器跳过出栈/压栈, 直接跳转下一个 ISR:

```
无尾链: ISR_A | POP 8 regs | PUSH 8 regs | ISR_B | POP 8 regs |
              <--- 20+ cycles overhead --->

有尾链: ISR_A | tail-chain | ISR_B | POP 8 regs |
              <- 6 cycles ->
```

尾链节省约 14 个时钟周期, 多中断连续触发时效果显著.

### 4.3 晚到 (Late-arriving)

低优先级中断入栈阶段, 更高优先级中断请求到达时, 入栈完成后直接跳转高优先级 ISR:

```
正常抢占: [Stacking Low] -> [ISR_Low] -> [Stacking High] -> [ISR_High]
晚到机制: [Stacking Low] -> [检测到更高] -> [ISR_High] (Low 保持挂起)
```

## 5. 嵌套中断行为分析

### 5.1 嵌套规则

1. 高抢占优先级可以打断低抢占优先级 (嵌套)
2. 相同抢占优先级之间不能嵌套, 按子优先级排队
3. 子优先级仅决定排队顺序, 不产生嵌套

### 5.2 嵌套时序示例

场景: PRIGROUP = 2, 中断配置如下:

```
Timer2:  抢占=0, 子=0 (最高)   UART1: 抢占=1, 子=0 (中)
GPIO:   抢占=2, 子=1 (低)     ADC:   抢占=2, 子=0 (低)

时序:
  T0: GPIO 触发, 进入 GPIO ISR
  T1: ADC 触发, 同抢占级(=2), ADC 子优先级更低(0<1), 排队等待
  T2: Timer2 触发, 抢占级更高(0<2), 嵌套抢占 GPIO ISR
  T3: Timer2 ISR 完成, 返回 GPIO ISR
  T4: GPIO ISR 完成, ADC 子优先级更低, 进入 ADC ISR
  T5: ADC ISR 完成, 返回线程模式
```

### 5.3 自动上下文保存

Cortex-M 硬件自动保存/恢复 xPSR, PC, LR, R12, R3-R0 (无需软件干预). ISR 中使用的 R4-R11 由编译器自动保存.

## 6. 临界区保护策略

### 6.1 三种方式对比

| 方式 | 机制 | 影响范围 | RTOS 兼容性 |
|------|------|---------|-------------|
| __disable_irq() | 设置 PRIMASK | 全局屏蔽 | 差 -- 影响 RTOS 调度 |
| BASEPRI | 屏蔽低于某优先级 | 可配置范围 | 好 -- RTOS 可设阈值 |
| 组合 | PRIMASK + BASEPRI | 分层控制 | 好 |

### 6.2 __disable_irq / __enable_irq

```c
// 简单用法 -- 全局关中断
__disable_irq();
shared_var = new_value;
__enable_irq();

// 嵌套安全: 保存/恢复 PRIMASK (避免内层 enable 过早打开)
void func_a_safe(void) {
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    // 修改共享资源
    func_b();  // 即使 func_b 内部调用了 enable_irq 也没问题
    __set_PRIMASK(primask);
}
```

### 6.3 BASEPRI 方式 (推荐)

```c
// 屏蔽优先级数值 >= 阈值的中断 (数值越大优先级越低)
__set_BASEPRI(5 << 4);  // 优先级 0-4 正常, 5-15 屏蔽
__set_BASEPRI(0);        // 写 0 取消屏蔽

// FreeRTOS 临界区实现思路 (简化版)
#define configMAX_SYSCALL_INTERRUPT_PRIORITY 5
void vPortEnterCritical(void) {
    __disable_irq();
    ulCriticalNesting++;
    __set_BASEPRI(configMAX_SYSCALL_INTERRUPT_PRIORITY << 4);
    __enable_irq();
    // 高优先级中断 (0-4) 不受 RTOS 影响, 保证实时性
}
```

### 6.4 临界区选择决策

- 裸机: __disable_irq + 保存 PRIMASK
- RTOS + 涉及 RTOS API: taskENTER_CRITICAL
- RTOS + 不涉及 RTOS API: BASEPRI 屏蔽相关优先级

## 7. 中断安全的 RTOS API

### 7.1 FreeRTOS 双层 API

| API 后缀 | 使用场景 | 行为 |
|----------|---------|------|
| 无后缀 (xQueueSend) | 任务中调用 | 阻塞等待 |
| FromISR (xQueueSendFromISR) | ISR 中调用 | 非阻塞 |

### 7.2 FromISR 使用模式

```c
void USART1_IRQHandler(void) {
    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
    uint8_t rx_byte;

    if (USART1->SR & USART_SR_RXNE) {
        rx_byte = USART1->DR;
        xQueueSendFromISR(uart_rx_queue, &rx_byte,
                          &xHigherPriorityTaskWoken);
    }
    // 唤醒更高优先级任务时触发上下文切换
    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
}
```

### 7.3 ISR 中禁止事项

```c
// 错误: ISR 中调用阻塞 API
void BAD_IRQHandler(void) {
    xSemaphoreTake(uart_mutex, portMAX_DELAY);  // 会阻塞!
    vTaskDelay(pdMS_TO_TICKS(10));              // ISR 不能延迟!
    printf("ISR triggered\n");                  // 通常有阻塞操作!
}

// 正确: ISR 尽量短, 通知任务处理
void GOOD_IRQHandler(void) {
    BaseType_t xWoken = pdFALSE;
    xSemaphoreGiveFromISR(uart_sem, &xWoken);
    portYIELD_FROM_ISR(xWoken);
}
```

## 8. 常见陷阱与调试

### 8.1 优先级反转

低优先级任务持锁 -> 高优先级任务等锁 -> 中优先级任务抢 CPU -> 高优先级被间接阻塞. 解决: 优先级继承 (FreeRTOS mutex 内置) 或缩短持锁时间.

### 8.2 优先级配置常见错误

```c
// 错误 1: 忘记设置分组就配置优先级 (默认 GROUP_0, 无嵌套)
// 修正: 先设分组
HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_2);
HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);

// 错误 2: 以为数值越大优先级越高 (实际 0 最高, 15 最低)

// 错误 3: 调用 FreeRTOS API 的中断优先级数值 < configMAX_SYSCALL_INTERRUPT_PRIORITY
// 会导致断言失败或硬 fault
```

### 8.3 调试技巧

```c
// 读取中断活跃/挂起状态
if (NVIC->IABR[USART1_IRQn / 32] & (1 << (USART1_IRQn % 32))) {
    // USART1 ISR 正在执行或被嵌套
}

// Fault 诊断
void HardFault_Handler(void) {
    volatile uint32_t cfsr  = SCB->CFSR;   // Configurable Fault Status
    volatile uint32_t hfsr  = SCB->HFSR;   // HardFault Status
    volatile uint32_t mmfar = SCB->MMFAR;  // MemManage Fault Address
    volatile uint32_t bfar  = SCB->BFAR;   // BusFault Address
    (void)cfsr; (void)hfsr; (void)mmfar; (void)bfar;
    while(1);
}
```

## 9. STM32 HAL 完整配置示例

### 9.1 UART 中断配置 (含嵌套设计)

```c
// 优先级规划: WWDG=0,0 (最高) TIM2=1,0 UART1=2,0 DMA=2,1

int main(void) {
    HAL_Init();
    SystemClock_Config();

    // Step 1: 设置优先级分组
    HAL_NVIC_SetPriorityGrouping(NVIC_PRIORITYGROUP_2);

    // Step 2: 配置各中断优先级
    HAL_NVIC_SetPriority(WWDG_IRQn,   0, 0);
    HAL_NVIC_SetPriority(TIM2_IRQn,   1, 0);
    HAL_NVIC_SetPriority(USART1_IRQn, 2, 0);
    HAL_NVIC_SetPriority(DMA2_Stream2_IRQn, 2, 1);

    // Step 3: 使能中断
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_NVIC_EnableIRQ(TIM2_IRQn);
    HAL_NVIC_EnableIRQ(DMA2_Stream2_IRQn);

    // Step 4: 启动 UART 接收中断
    __HAL_UART_ENABLE_IT(&huart1, UART_IT_RXNE);

    while (1) { /* 主循环 */ }
}

// 接收完成回调 (ISR 上下文)
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        BaseType_t xWoken = pdFALSE;
        xQueueSendFromISR(uart_rx_queue, &rx_data, &xWoken);
        portYIELD_FROM_ISR(xWoken);
        HAL_UART_Receive_IT(&huart1, &rx_data, 1);
    }
}
```

### 9.2 临界区保护完整示例

```c
// 裸机: PRIMASK 保护
void sensor_update(void) {
    uint32_t primask = __get_PRIMASK();
    __disable_irq();
    sensor_data.temp = read_temp();
    sensor_data.humi = read_humi();
    sensor_data.timestamp = get_tick();
    __set_PRIMASK(primask);
}

// RTOS: FreeRTOS 临界区
void sensor_update_rtos(void) {
    taskENTER_CRITICAL();
    sensor_data.temp = read_temp();
    sensor_data.humi = read_humi();
    sensor_data.timestamp = xTaskGetTickCount();
    taskEXIT_CRITICAL();
}

// 混合: 高优先级中断不受 RTOS 影响
// configMAX_SYSCALL_INTERRUPT_PRIORITY = 5
HAL_NVIC_SetPriority(CAN1_RX0_IRQn, 2, 0);  // 安全, 不受 RTOS 屏蔽
HAL_NVIC_SetPriority(USART1_IRQn,  6, 0);   // 通信, 受 RTOS 临界区保护
```

## 总结

NVIC 的优先级与嵌套设计是 Cortex-M 中断系统的核心. 关键要点:

1. **分组先行**: 先确定 PRIGROUP 再配置优先级, 否则抢占/子优先级语义错乱
2. **数值越小优先级越高**: 0 是最高, 这是初学者最常犯的方向性错误
3. **BASEPRI 优于 PRIMASK**: 允许高优先级中断继续响应, 粒度更细
4. **FromISR 不可省略**: ISR 中调用 RTOS API 必须用 FromISR 版本
5. **尾链与晚到是免费优化**: 硬件自动完成, 理解机制有助于设计低延迟中断链
6. **FreeRTOS 优先级阈值**: 调用 RTOS API 的中断, 逻辑优先级必须低于 configMAX_SYSCALL_INTERRUPT_PRIORITY

遵循 "短 ISR + 优先级分层 + 正确的临界区保护" 三原则, 可以构建可靠且低延迟的嵌入式应用.

## 参考文献

1. ARM. Cortex-M4 Devices Generic User Guide (DUI 0553A). ARM Limited, 2010.
2. Joseph Yiu. The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors, 3rd Edition. Newnes, 2013.
3. Real Time Engineers Ltd. FreeRTOS Kernel Developer Docs -- Interrupt Management. https://www.freertos.org/RTOS-Cortex-M3-M4.html
4. STMicroelectronics. STM32F4 Programming Manual (PM0214).
5. Jack Ganssle. The Art of Programming Embedded Systems. Academic Press, 1992.
