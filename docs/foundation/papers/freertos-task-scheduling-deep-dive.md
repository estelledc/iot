# FreeRTOS任务调度器源码深度分析
> **难度**：🔴 高级 | **领域**：RTOS内核 | **阅读时间**：约 25 分钟

## 引言

想象一个繁忙的餐厅厨房：多个厨师同时做不同的菜，但灶台有限。厨师长就是调度器 -- 他决定谁先上灶、谁等着、谁可以先休息。高优先级的菜(客人催的)必须优先做，同优先级的轮流上灶，没菜做的厨师去整理厨具(idle task)。FreeRTOS的调度器就是这位"厨师长"，用精巧的数据结构让有限CPU在数十个任务间高效切换，核心代码不到500行。

本文从源码层面逐层拆解：TCB数据结构、就绪列表、调度算法、上下文切换、状态机、同步原语内幕。目标读者是已熟悉基本API、希望理解底层机制的嵌入式开发者。

## 1. 内核架构与关键全局变量

### 1.1 分层结构

```
+-----------------------------------+
|        应用层 (User Tasks)        |
+-----------------------------------+
|  API层 (task.c / queue.c / ...)   |
+-----------------------------------+
|  核心层 (调度器 + 中断管理 + 内存) |
+-----------------------------------+
|  移植层 (port.c / portmacro.h)    |
+-----------------------------------+
|         硬件层 (Cortex-M / ...)    |
+-----------------------------------+
```

`tasks.c`实现调度器主体(约2500行)，是本文重点；`port.c`提供上下文切换和Tick中断，与芯片架构强相关。

### 1.2 核心全局变量

```c
PRIVILEGED_DATA static volatile UBaseType_t uxTopReadyPriority = 0;
PRIVILEGED_DATA static List_t pxReadyTasksLists[configMAX_PRIORITIES];
PRIVILEGED_DATA static List_t xDelayedTaskList1;
PRIVILEGED_DATA static List_t xDelayedTaskList2;
PRIVILEGED_DATA static List_t *pxDelayedTaskList;
PRIVILEGED_DATA static List_t *pxOverflowDelayedTaskList;
PRIVILEGED_DATA static List_t xSuspendedTaskList;
PRIVILEGED_DATA static TCB_t *pxCurrentTCB = NULL;
```

- `pxCurrentTCB`：指向当前运行任务的TCB
- `pxReadyTasksLists[]`：就绪列表数组，下标即优先级
- `uxTopReadyPriority`：当前最高就绪优先级(优化查找用)

## 2. TCB -- 任务控制块

### 2.1 数据结构

TCB是FreeRTOS对任务的唯一抽象，每个任务在内核中就是一个TCB实例：

```c
typedef struct tskTaskControlBlock {
    volatile StackType_t *pxTopOfStack;    /* 栈顶指针 -- 上下文恢复的起点 */
    ListItem_t xStateListItem;    /* 状态链表节点(挂入就绪/阻塞/挂起链表) */
    ListItem_t xEventListItem;    /* 事件链表节点(挂入等待队列/信号量) */
    UBaseType_t uxPriority;       /* 当前优先级 */
    StackType_t *pxStartOfStack;  /* 栈起始地址(栈溢出检测) */
    #if (configUSE_MUTEXES == 1)
        UBaseType_t uxBasePriority;  /* 基优先级(优先级继承还原用) */
        UBaseType_t uxMutexesHeld;   /* 持有的互斥量计数 */
    #endif
    #if (configUSE_TASK_NOTIFICATIONS == 1)
        volatile uint32_t ulNotifiedValue;
        volatile uint8_t ucNotifyState;
    #endif
    char pcTaskName[configMAX_TASK_NAME_LEN]; /* 调试用任务名 */
} tskTCB;
```

### 2.2 内嵌链表节点的设计

TCB内嵌两个 `ListItem_t`，任务不必"被放入"链表，TCB本身就携带链表节点。`xStateListItem.pvOwner` 反指回所属TCB，调度器从链表摘下节点后通过 `pvOwner` 可立即获取TCB，零额外分配。

## 3. 就绪列表 -- 调度器的核心索引

### 3.1 结构与含义

```c
static List_t pxReadyTasksLists[configMAX_PRIORITIES];
```

以优先级为下标的链表数组：

```
pxReadyTasksLists[5] (最高) --> [TaskH] --> NULL
pxReadyTasksLists[4]        --> [TaskE] --> [TaskF] --> NULL
pxReadyTasksLists[3]        --> NULL
pxReadyTasksLists[2]        --> [TaskB] --> [TaskC] --> [TaskD] --> NULL
pxReadyTasksLists[0] (最低) --> [Idle]  --> NULL
```

同优先级多任务以FIFO顺序挂入同一链表，链表头即"当前应运行"任务。

### 3.2 位图优化 -- O(1)查找最高优先级

当 `configUSE_PORT_OPTIMISED_TASK_SELECTION` 为1时：

```c
/* 每个优先级占一bit，置1表示该优先级有就绪任务 */
#define portRECORD_READY_PRIORITY( uxPriority, uxTopReadyPriority ) \
    ( uxTopReadyPriority ) |= ( 1UL << ( uxPriority ) )
#define portGET_HIGHEST_PRIORITY( uxTopReadyPriority, uxTopReadyPriority ) \
    ( uxTopReadyPriority ) = ( 31UL - ( uint32_t ) __clz( ( uxTopReadyPriority ) ) )
```

CLZ(Count Leading Zeros)硬件指令一次定位最高位，O(1)找到最高优先级。Cortex-M3/M4/M7均支持。

## 4. 调度算法

### 4.1 优先级抢占式调度

FreeRTOS默认策略：任何时刻运行任务必定是最高就绪优先级的链表头；更高优先级任务就绪时立刻抢占。抢占触发点：中断退出、API调用内、Yield主动让出。

### 4.2 同优先级时间片轮转

`configUSE_TIME_SLICING` 为1(默认)时，同优先级任务按Tick轮流执行。每个SysTick中断到来时，若当前优先级链表有后继，当前任务被移到链表尾部，下一个任务成为链表头。

### 4.3 vTaskSwitchContext -- 调度核心

```c
void vTaskSwitchContext( void )
{
    taskCHECK_FOR_STACK_OVERFLOW();
    listGET_OWNER_OF_NEXT_ENTRY( pxCurrentTCB,
        &( pxReadyTasksLists[ uxTopReadyPriority ] ) );
    /* 取出最高优先级链表首任务的TCB作为新的pxCurrentTCB */
}
```

## 5. 上下文切换机制 (Cortex-M)

### 5.1 两种触发路径

```
路径A: 任务级Yield               路径B: 中断级Yield
  taskYIELD()                     xHigherPriorityTaskWoken == pdTRUE
    |                               |
    v                               v
  portYIELD()                     portYIELD_FROM_ISR()
    |                               |
    +-------------------------------+
    |
    v
  PendSV_Handler() --> 保存当前上下文 --> vTaskSwitchContext() --> 恢复新上下文
```

### 5.2 PendSV为何设最低优先级

PendSV设为最低中断优先级，意味着任何其他中断都能抢占它。上下文切换不会打断中断服务，保证中断响应实时性。

```c
void xPortStartScheduler( void )
{
    portNVIC_SYSPRI2_REG |= portPENDSV_PRIORITY << 16UL;  /* PendSV = 最低 */
    portNVIC_SYSPRI2_REG |= portSYSCALL_PRIORITY  << 24UL; /* SysTick = 较低 */
    vPortStartFirstTask();
}
```

### 5.3 PendSV汇编核心

```asm
PendSV_Handler:
    mrs     r0, psp             /* 获取进程栈指针 */
    ldr     r3, =pxCurrentTCB
    ldr     r2, [r3]            /* r2 = pxCurrentTCB */
    stmdb   r0!, {r4-r11}      /* 保存R4-R11到任务栈 */
    str     r0, [r2]            /* TCB.pxTopOfStack = 新栈顶 */
    bl      vTaskSwitchContext  /* C函数，更新pxCurrentTCB */
    ldr     r3, =pxCurrentTCB
    ldr     r2, [r3]
    ldr     r0, [r2]            /* r0 = 新任务的pxTopOfStack */
    ldmia   r0!, {r4-r11}      /* 恢复R4-R11 */
    msr     psp, r0
    bx      r14                 /* 异常返回，硬件自动恢复R0-R3,R12,LR,PC,xPSR */
```

硬件在异常入口自动保存R0-R3,R12,LR,PC,xPSR(8个寄存器)，PendSV只需保存R4-R11，将切换开销压到最低。

## 6. Tick中断与时间管理

### 6.1 SysTick中断服务

```c
void xPortSysTickHandler( void )
{
    vPortRaiseBASEPRI();
    if( xTaskIncrementTick() != pdFALSE )
        portNVIC_ICSR_REG = portNVIC_PENDSVSET_BIT;  /* 触发PendSV */
    vPortClearBASEPRIFromISR();
}
```

### 6.2 xTaskIncrementTick 核心逻辑

- 更新 `xTickCount`，检查Tick溢出时交换 `pxDelayedTaskList` 和 `pxOverflowDelayedTaskList`(处理回绕的经典手法)
- 延迟链表按唤醒时间升序排列，while循环一次Tick可能唤醒多个到期任务
- 唤醒任务优先级 >= 当前任务时标记需要切换
- 时间片轮转：同优先级链表长度 > 1时也标记切换

## 7. 任务状态机

### 7.1 四种状态与转换

```
                  +-----------+
    xTaskCreate   |   Ready   |   vTaskDelete
       +--------> |           | --------------+
       |          +-----+-----+               |
       |                |                     |
       |  调度器选中     |  被抢占/TimeSlice   |
       |                v                     |
       |          +-----------+               |
       |          |  Running  |               |
       |          +--+-----+--+               |
       |             |     |                  |
       |  vTaskDelay |     | 等待信号量/队列   |
       |             v     v                  |
       |       +----------+  +-----------+    |
       |       |  Blocked |  | Suspended |    |
       |       +----+-----+  +-----+-----+   |
       |            |              |          |
       +<-----------+   vTaskResume+<---------+
             事件/超时
```

### 7.2 状态到链表的映射

| 状态 | 挂入链表 | 退出条件 |
|------|---------|---------|
| Running | 无(pxCurrentTCB指向) | 被抢占/阻塞/挂起 |
| Ready | `pxReadyTasksLists[pri]` | 被调度选中 |
| Blocked | `pxDelayedTaskList`或事件等待链表 | 超时/事件发生 |
| Suspended | `xSuspendedTaskList` | `vTaskResume()` |

## 8. vTaskDelay vs vTaskDelayUntil

### 8.1 vTaskDelay -- 相对延时(周期不精确)

```c
void vTaskDelay( const TickType_t xTicksToDelay )
{
    if( xTicksToDelay > ( TickType_t ) 0U )
    {
        vTaskSuspendAll();
        prvAddCurrentTaskToDelayedList( xTicksToDelay, pdFALSE );
        xTaskResumeAll();
    }
}
```

从**调用时刻**起计时，任务执行耗时导致周期漂移：

```
实际:  |--exec5--|--delay10--|--exec7--|--delay10--|  周期: 15, 17 (不稳!)
```

### 8.2 vTaskDelayUntil -- 绝对延时(周期任务首选)

```c
void vTaskDelayUntil( TickType_t * const pxPreviousWakeTime,
                      const TickType_t xTimeIncrement )
```

从**上一次唤醒时刻**计算下次唤醒，执行耗时被"吸收"：

```
实际:  |--exec5--|--delay5--|--exec7--|--delay3--|  周期: 10, 10 (稳定!)
```

`pxPreviousWakeTime` 由内核在每次唤醒时更新，首次调用初始化为 `xTaskGetTickCount()`。

## 9. 空闲任务与空闲钩子

调度器启动时自动创建空闲任务(优先级0，不可删除/挂起)：

```c
for( ;; )
{
    #if ( configUSE_IDLE_HOOK == 1 )
        vApplicationIdleHook();  /* 用户定义 */
    #endif
}
```

典型用途：低功耗模式、CPU利用率统计、后台清理。限制：**不能调用任何阻塞API**，否则所有用户任务也阻塞时系统无任务可运行。

## 10. 队列实现 -- 任务间通信基础

### 10.1 队列数据结构

```c
typedef struct QueueDefinition {
    int8_t *pcHead;                  /* 存储区起始 */
    int8_t *pcWriteTo;              /* 下一个写入位置 */
    union { int8_t *pcReadFrom; UBaseType_t uxReceiverWoken; } u;
    List_t xTasksWaitingToSend;     /* 队列满时等待发送的任务 */
    List_t xTasksWaitingToReceive;  /* 队列空时等待接收的任务 */
    volatile UBaseType_t uxMessagesWaiting;
    UBaseType_t uxLength;           /* 队列容量 */
    UBaseType_t uxItemSize;         /* 每条消息字节数 */
    #if ( configUSE_MUTEXES == 1 )
        UBaseType_t uxQueueType;    /* 0=队列, 1=互斥量 */
    #endif
} Queue_t;
```

队列本质是**环形缓冲区 + 两个等待链表**。数据拷贝用 `memcpy`，消息值传递而非引用传递，安全但占额外内存。

## 11. 互斥量与二值信号量

### 11.1 本质区别

| 特性 | 二值信号量 | 互斥量 |
|------|-----------|--------|
| 初始值 | 0 (空) | 1 (可用) |
| 优先级继承 | 无 | 有 |
| 所有者概念 | 无 | 有 |
| 用途 | 同步/中断通知 | 互斥访问共享资源 |

### 11.2 优先级继承协议

低优先级任务L持有mutex，高优先级任务H请求时：

```
初始:    L(低) 持有 mutex, H(高) 请求 --> H阻塞
继承:    L优先级临时提升到H级别, 中优先级M无法抢占L
释放:    L释放mutex, 优先级恢复, H被唤醒抢占
```

源码关键(互斥量获取时)：

```c
if( pxQueue->uxQueueType == queueQUEUE_IS_MUTEX )
{
    pxQueue->pxMutexHolder = pvTaskIncrementMutexHeldCount();
    if( pxQueue->uxPriorityToInherit > pxCurrentTCB->uxPriority )
        vTaskPriorityInherit( pxQueue->pxMutexHolder, pxQueue->uxPriorityToInherit );
}
```

局限：优先级继承只解决**单层**反转，多层嵌套互斥量仍可能死锁。FreeRTOS不实现优先级天花板协议，需用户自行设计锁获取顺序。

## 12. 内核可配置选项

| 宏 | 默认值 | 说明 |
|----|--------|------|
| `configUSE_PREEMPTION` | 1 | 1=抢占式, 0=协作式 |
| `configUSE_TIME_SLICING` | 1 | 同优先级时间片轮转 |
| `configUSE_MUTEXES` | 0 | 启用互斥量及优先级继承 |
| `configMAX_PRIORITIES` | 5 | 最大优先级数 |
| `configUSE_PORT_OPTIMISED_TASK_SELECTION` | 0 | 位图优化(Cortex-M建议开) |
| `configSUPPORT_STATIC_ALLOCATION` | 0 | 静态内存分配API |

协作式调度下任务只在主动Yield或阻塞时让出CPU，可减少上下文切换开销。

## 13. 内存分配方案 -- heap_1到heap_5

| 方案 | 分配 | 释放 | 合并 | 多区域 | 适用场景 |
|------|------|------|------|--------|---------|
| heap_1 | 是 | 否 | -- | 否 | 任务全静态创建 |
| heap_2 | 是 | 是 | 否 | 否 | (已过时，用heap_4) |
| heap_3 | 是 | 是 | 依实现 | 否 | 原型验证 |
| heap_4 | 是 | 是 | 是 | 否 | **大多数项目首选** |
| heap_5 | 是 | 是 | 是 | 是 | 多RAM区域芯片 |

### 13.1 heap_4 -- 首次适应 + 碎片合并(最常用)

```c
typedef struct A_BLOCK_LINK {
    struct A_BLOCK_LINK *pxNextFreeBlock;
    size_t xBlockSize;
} BlockLink_t;
```

释放时按地址排序插入空闲链表，与前后连续空闲块合并。外部碎片消除，内部碎片仍存在。

### 13.2 heap_5 -- 多内存区域

适用于芯片有分散RAM(如STM32的CCM SRAM + 主SRAM)：

```c
HeapRegion_t xHeapRegions[] = {
    { ( uint8_t * ) 0x20000000UL, 0x10000 },  /* 主SRAM 64KB */
    { ( uint8_t * ) 0x10000000UL, 0x08000 },  /* CCM SRAM 32KB */
    { NULL, 0 }
};
vPortDefineHeapRegions( xHeapRegions );  /* 首次malloc前必须调用 */
```

## 总结

FreeRTOS调度器的精妙在于"简单数据结构 + 精确不变量"：

1. **就绪列表下标=优先级**：O(1)定位最高优先级(位图优化)
2. **TCB内嵌链表节点**：零额外分配，任务与链表无缝衔接
3. **PendSV最低优先级**：上下文切换不干扰中断响应
4. **优先级继承**：最小代价(仅临时改优先级)解决优先级反转
5. **Tick回绕双链表**：优雅处理32位Tick溢出

理解这些机制后，调试调度异常(优先级反转死锁、栈溢出、Tick丢失)有了明确路径：先看 `uxTopReadyPriority` 和就绪列表确认谁在跑，再看延迟链表确认谁在等，最后查互斥量持有者和继承链定位反转点。

## 参考文献

1. Richard Barry. *Mastering the FreeRTOS Real Time Kernel*. Real Time Engineers Ltd., 2016.
2. FreeRTOS Kernel Source Code v10.5.1. GitHub: https://github.com/FreeRTOS/FreeRTOS-Kernel
3. Joseph Yiu. *The Definitive Guide to ARM Cortex-M Processors*. 2nd Edition, Elsevier, 2017.
4. Lui Sha, Rajkumar Rajkumar, John Lehoczky. *Priority Inheritance Protocols: An Approach to Real-Time Synchronization*. Carnegie Mellon University, 1990.
5. Robert Love. *Linux Kernel Development*. 3rd Edition, Sams, 2010.
