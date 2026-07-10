---
schema_version: '1.0'
id: bare-metal-state-machine-pattern
title: 裸机编程状态机模式与事件驱动架构
layer: 1
content_type: UNKNOWN
difficulty: intermediate
reading_time: 20
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 裸机编程状态机模式与事件驱动架构
> **难度**：🟡 中级 | **领域**：嵌入式软件架构 | **阅读时间**：约 20 分钟

## 引言

想象你是一个地铁站的值班员。站台上同时有人问路、列车进站、广播响铃、监控报警——如果每一件事你都要当场处理完再做下一件，那列车早开走了。聪明的做法是：把每件事写成一张纸条丢进信箱，按优先级一张一张取出来处理。每张纸条就是一个**事件**，你的工作方式就是**事件驱动**。

而你自己也在"等列车""开门检票""处理突发"之间切换，每次切换遵循明确规则。这种"在有限几个状态之间按规则跳转"的思维方式，就是**有限状态机 (FSM)**。

裸机项目里最常见的写法是一个超级大 `while(1)` 顺序调用各模块——模块一多就变成"面条代码"。状态机 + 事件驱动是升级到可维护架构的第一步。

## 1. 超级循环的局限

### 1.1 典型 super-loop

```c
int main(void) {
    hardware_init();
    while (1) {
        sensor_read();    // 可能阻塞 50ms
        ble_process();
        uart_handle();
        display_update();
        delay_ms(10);
    }
}
```

### 1.2 问题清单

| 问题 | 根因 |
|------|------|
| 优先级倒置 | 所有模块平等轮询 |
| 隐式状态 | 状态散落在全局变量 |
| 不可测试 | 业务逻辑与硬件耦合 |
| 扩展困难 | 无统一调度入口 |

**核心矛盾**：super-loop 把"做什么"和"什么时候做"混在一起。状态机管"做什么",事件驱动管"什么时候做"。

## 2. 有限状态机 (FSM) 概念

### 2.1 形式化定义

FSM 是五元组 `(S, E, T, s0, F)`：`S` 为有限状态集合, `E` 为事件集合, `T: S x E -> S` 为转移函数, `s0` 为初始状态, `F` 为终止状态集合 (可选)。

### 2.2 状态转移图

```
          START           TICK            STOP
  IDLE --------> RUNNING --------> RUNNING -------> IDLE
                    | ERROR            | ERROR
                    v                  v
                 ERROR <------------ ERROR
                    | RESET
                    v
                  IDLE
```

### 2.3 两个关键动作

- **迁移动作 (transition action)**：状态切换时执行,如"开电机"
- **内部动作 (internal action)**：留在当前状态时执行,如"累加计数"

内部动作不触发退出/进入动作,这是 HSM 里容易踩坑的地方。

## 3. switch-case 状态机实现

### 3.1 基本框架

```c
typedef enum { IDLE, RUNNING, ERROR } State;
typedef enum { EVT_START, EVT_STOP, EVT_TICK, EVT_ERROR, EVT_RESET } Event;
static State current_state = IDLE;

void fsm_handle(Event evt) {
    switch (current_state) {
    case IDLE:
        if (evt == EVT_START) { motor_on(); current_state = RUNNING; }
        break;
    case RUNNING:
        if (evt == EVT_TICK) { counter++; }
        else if (evt == EVT_STOP) { motor_off(); current_state = IDLE; }
        else if (evt == EVT_ERROR) { log_error(); current_state = ERROR; }
        break;
    case ERROR:
        if (evt == EVT_RESET) { motor_off(); counter = 0; current_state = IDLE; }
        break;
    }
}
```

### 3.2 进入/退出动作的模拟

```c
void fsm_handle(Event evt) {
    State next = current_state;
    switch (current_state) {
    case IDLE: if (evt == EVT_START) next = RUNNING; break;
    // ... 其他状态 ...
    }
    if (next != current_state) {
        exit_action(current_state);
        entry_action(next);
        current_state = next;
    }
}
```

"先算下一状态,再统一做进入/退出"是向表驱动和 HSM 过渡的关键思想。**优点**：零依赖直观;**缺点**：switch 膨胀,无法共享公共逻辑。

## 4. 表驱动状态机

### 4.1 核心思想

把转移规则从代码逻辑搬到数据表——查表代替分支,逻辑与数据分离。

### 4.2 实现要点

```c
typedef struct { State cur; Event evt; void (*act)(void); State nxt; } Trans;

static const Trans table[] = {
    { IDLE,    EVT_START, motor_on,  RUNNING },
    { RUNNING, EVT_TICK,  count_inc, RUNNING },
    { RUNNING, EVT_STOP,  motor_off, IDLE    },
    { RUNNING, EVT_ERROR, log_error, ERROR   },
    { ERROR,   EVT_RESET, full_reset,IDLE    },
};

void fsm_dispatch(Event evt) {
    for (int i = 0; i < ARR_LEN(table); i++) {
        if (table[i].cur == current_state && table[i].evt == evt) {
            table[i].act();
            current_state = table[i].nxt;
            return;
        }
    }
}
```

### 4.3 与 switch-case 对比

| 维度 | switch-case | 表驱动 |
|------|------------|--------|
| 代码量 | 状态少时紧凑 | 需表结构开销 |
| 可维护性 | 逻辑分散在 case | 集中在一张表 |
| 可测试性 | 需 mock 硬件 | 表可离线验证 |
| 运行时修改 | 不可能 | 可替换表指针 |
| 共享逻辑 | 难 | 仍难 (需 HSM) |

## 5. 层次状态机 (HSM / Statecharts)

### 5.1 为什么需要层次

BLE 协议栈中"连接态"下有"发现服务""写特征值"等子状态,它们共享断连清理逻辑。HSM 把"连接态"作为父状态,断连处理写在父状态退出动作里,子状态自动继承。

```
  TOP
   +-- DISCONNECTED
   +-- CONNECTED
         +-- DISCOVERING
         +-- WRITING
         +-- SUBSCRIBING
```

**关键语义**：子状态不处理的事件向父状态冒泡;进入子状态前先执行父 entry;离开子状态后才执行父 exit。

### 5.2 简化 HSM 实现 (QP 风格)

```c
// 每个状态是一个函数,返回 NULL 表示已处理,
// 返回父状态函数表示事件向上冒泡
State state_connected(Event evt) {
    switch (evt) {
    case EVT_DISCONNECT: ble_cleanup(); return (State)state_disconnected;
    case EVT_DISCOVER:  return (State)state_discovering;
    default: return NULL;
    }
}
State state_discovering(Event evt) {
    switch (evt) {
    case EVT_DISCOVER_DONE: return (State)state_writing;
    case EVT_DISCONNECT:    return (State)state_connected;  // 冒泡
    default:                return (State)state_connected;  // 冒泡
    }
}
```

| 维度 | 平面 FSM | HSM |
|------|----------|-----|
| 公共逻辑 | 每个状态重复 | 父状态统一处理 |
| 状态数 | 扁平展开 20+ | 层次组织每层 3-5 |
| 事件传播 | 未匹配即丢弃 | 自动冒泡到父状态 |

## 6. 事件驱动架构

### 6.1 核心组件

```
  中断/定时器/外部输入 --> 事件队列 --> 调度器 --> 状态机处理
```

1. **事件生产者**：ISR、定时器回调——只构造事件并入队
2. **事件队列**：环形缓冲区,8-64 个槽位
3. **调度器**：主循环从队列取事件,派发给状态机

### 6.2 最小实现

```c
#define QUEUE_SIZE 32
typedef struct { Event evt; void *data; } QItem;
static QItem queue[QUEUE_SIZE];
static volatile uint8_t head = 0, tail = 0;

void event_post(Event evt, void *data) {          // ISR 中调用
    uint8_t next = (tail + 1) % QUEUE_SIZE;
    if (next != head) { queue[tail].evt = evt; queue[tail].data = data; tail = next; }
}
bool event_get(QItem *item) {                      // 主循环调用
    if (head == tail) return false;
    *item = queue[head]; head = (head + 1) % QUEUE_SIZE; return true;
}
void dispatcher_run(void) {
    QItem item;
    while (1) {
        if (event_get(&item)) fsm_handle(item.evt);
        else __WFI();    // 等待中断,省电
    }
}
```

### 6.3 优先级扩展

FIFO 队列所有事件平等。BLE 心跳比传感器采样更紧急,解决方案：

- **双队列**：高优先级 + 普通,调度器优先取高优
- **优先级位图**：每个优先级一个队列,位图标记非空,O(1) 找最高优先级

## 7. QP 框架核心概念

QP (Quantum Platform) 是 Miro Samek 开源的事件驱动框架,把 HSM + 事件队列 + 定时器 + 内存池打包,典型占用 2-4KB ROM。

| 概念 | 说明 | 类比 |
|------|------|------|
| QActive | 活动对象 = 状态机 + 事件队列 + 优先级 | 独立的"值班员" |
| QHsm | 层次状态机基类 | 值班员的"行为规则" |
| QEvt | 事件基类,可携带参数 | 纸条 |
| QTimeEvt | 定时器事件,可单次/周期 | 闹钟 |
| QF | 框架核心:发布/订阅 | 邮局 |

**为什么值得学**：裸机可用不需 RTOS;HSM 语义严格符合 UML Statecharts;活动对象天然线程安全;QP/nano 不到 1KB ROM。

## 8. 状态机 + 定时器: IoT 协议实战

### 8.1 BLE 连接状态机

BLE 连接涉及广播、发现服务等阶段,每个阶段有超时。"状态机 + 定时器"表达最自然。

```c
typedef enum { BLE_OFF, BLE_ADV, BLE_DISCOVERING, BLE_READY } BleState;
static BleState ble_state = BLE_OFF;
static TimerHandle_t ble_timer;

void ble_fsm(Event evt) {
    switch (ble_state) {
    case BLE_OFF:
        if (evt == EVT_BLE_START) {
            ble_start_adv(); timer_start(ble_timer, ADV_TIMEOUT_MS); ble_state = BLE_ADV;
        }
        break;
    case BLE_ADV:
        if (evt == EVT_BLE_CONNECTED) {
            timer_stop(ble_timer); ble_start_discover();
            timer_start(ble_timer, DISCOVER_TIMEOUT_MS); ble_state = BLE_DISCOVERING;
        } else if (evt == EVT_TIMEOUT) {
            ble_restart_adv(); timer_start(ble_timer, ADV_TIMEOUT_MS);
        }
        break;
    case BLE_DISCOVERING:
        if (evt == EVT_BLE_DISCOVER_DONE) { timer_stop(ble_timer); ble_state = BLE_READY; }
        else if (evt == EVT_TIMEOUT) { ble_disconnect(); ble_state = BLE_OFF; }
        break;
    case BLE_READY:
        if (evt == EVT_BLE_DISCONNECTED) { ble_start_adv(); ble_state = BLE_ADV; }
        break;
    }
}
```

**要点**：每个状态配超时定时器,进入时启动,离开时停止。TIMEOUT 和正常事件走同一个状态机。

### 8.2 传感器采样状态机

```c
typedef enum { SENS_IDLE, SENS_INIT, SENS_SETTLING, SENS_SAMPLING } SensState;

void sensor_fsm(Event evt) {
    switch (sens_state) {
    case SENS_IDLE:
        if (evt == EVT_SAMPLE_REQ) { sensor_hw_init(); timer_start(...); sens_state = SENS_INIT; }
        break;
    case SENS_INIT:
        if (evt == EVT_TIMEOUT) { sensor_hw_start_convert(); timer_start(...); sens_state = SENS_SETTLING; }
        break;
    case SENS_SETTLING:
        if (evt == EVT_TIMEOUT) { sensor_hw_read(&raw); event_post(EVT_DATA_READY, &raw); sens_state = SENS_SAMPLING; }
        break;
    case SENS_SAMPLING:
        if (evt == EVT_DATA_READY) { process_sample(...); sens_state = SENS_IDLE; }
        break;
    }
}
```

**设计模式**：传感器状态机是"自驱"的——请求到来后自动走完流程,回到 IDLE 等下次请求。

## 9. 状态机测试策略

### 9.1 为什么好测

状态机把"在什么状态下做什么"显式化。测试只需验证：给定状态 + 给定事件 = 期望下一状态 + 期望动作。

### 9.2 Unity 风格示例

```c
void test_idle_start_enters_running(void) {
    current_state = IDLE; fsm_handle(EVT_START);
    TEST_ASSERT_EQUAL(RUNNING, current_state);
}
void test_running_tick_stays_running(void) {
    current_state = RUNNING; uint32_t before = counter; fsm_handle(EVT_TICK);
    TEST_ASSERT_EQUAL(RUNNING, current_state);
    TEST_ASSERT_EQUAL(before + 1, counter);
}
```

### 9.3 覆盖率要求

- **状态覆盖**：每个状态至少进入一次
- **转移覆盖**：每条转移至少执行一次
- **动作覆盖**：每个动作至少触发一次 (含守卫条件真假两分支)

### 9.4 硬件解耦

```c
typedef struct { void (*motor_on)(void); void (*motor_off)(void); } HwIf;
static HwIf hw = { real_motor_on, real_motor_off };
// 测试时替换为 mock
void test_start_calls_motor_on(void) {
    hw.motor_on = mock_motor_on; current_state = IDLE; fsm_handle(EVT_START);
    TEST_ASSERT_EQUAL(1, motor_on_called);
}
```

## 10. UML 状态图到代码的映射

| UML 元素 | C 代码 |
|----------|--------|
| 状态 | enum 常量 + case 分支 (或函数) |
| 事件 | enum 常量 |
| 转移 | `if (evt == X) { action(); state = Y; }` |
| 进入动作 | 状态分支顶部,或 `entry_action()` |
| 退出动作 | 切换前调用,或 `exit_action()` |
| 内部动作 | if 内执行,不改 state |
| 守卫条件 [guard] | `if (guard && evt == X)` |

UML 图画对了,代码几乎是机械翻译。自动生成工具：**QP/QM** (Samek 建模工具)、**SinelaboreRT**、**Smc** (State Machine Compiler)。

## 11. 常见反模式

### 11.1 God State (上帝状态)

**错误**：一个状态内用一堆 flag 区分子状态。RUNNING 里 `if (sub_mode == MODE_A)` 再嵌套 `if (phase == 1)` ——这其实是独立状态,不是 if 分支。

**正确**：把子状态提升为独立状态,或使用 HSM 层次结构。

### 11.2 Spaghetti Transitions (面条转移)

**错误**：状态之间随意跳转 `A --> C --> B --> D --> A`,没有规律。

**正确**：状态按阶段组织,转移沿阶段方向推进,少数"回退"转移(如错误恢复)应有明确语义。

### 11.3 在 ISR 中做状态机逻辑

**错误**：ISR 里直接调用 `fsm_handle()`——执行时间不可控且可能重入。

**正确**：ISR 只入队事件,主循环处理：`event_post_from_isr(evt, NULL)`。

### 11.4 忘记守卫条件导致非法转移

**错误**：收到事件就转移,不检查前置条件。IDLE 下收到 EVT_DATA_READY 就处理。

**正确**：状态机忽略不合法事件,或更好——源头不发不合理的事件。

## 总结

从 super-loop 到状态机 + 事件驱动的架构升级路径：

1. **super-loop** -- 能跑,但耦合、不可测试、不可扩展
2. **switch-case FSM** -- 零依赖,适合简单场景 (3-5 个状态)
3. **表驱动 FSM** -- 逻辑数据分离,易于维护和自动生成
4. **HSM** -- 解决公共逻辑复用,适合复杂协议栈 (BLE, MQTT)
5. **事件驱动架构** -- 统一中断/定时器/外部输入,解耦"做什么"和"什么时候做"
6. **QP 框架** -- 上述思想的生产级打包,裸机可用

选型建议：

- MCU RAM < 4KB,状态 < 5 个: switch-case FSM + 简单事件队列
- MCU RAM 8-32KB,多模块协作: 表驱动 + 双队列调度
- 复杂协议栈 (BLE/MQTT/USB): HSM + 事件驱动,考虑 QP
- 已上 RTOS: 每个任务一个活动对象,任务间事件通信

**一句话**：状态机让"做什么"有章可循,事件驱动让"什么时候做"有迹可查。两者结合,就是裸机架构的"从面条到面条酱"的升级。

## 参考文献

1. Samek M. *Practical Statecharts in C/C++: Quantum Programming for Embedded Systems*. CMP Books, 2002. -- HSM + QP 框架奠基之作
2. Samek M. *PSiCC2: Practical Statecharts in C/C++*, 2nd Edition. Newnes, 2008. -- 更新 QP 4.x,增加活动对象模型
3. Douglass B P. *State Machines for Embedded Systems*. ESC, 2001. -- UML Statecharts 到 C 代码映射
4. Barr M. *Programming Embedded Systems in C and C++*. O'Reilly, 2006. -- 第 6 章讲事件驱动架构基础
5. QP Framework Official Documentation. https://www.state-machine.com/qpc -- QP/C 和 QP-nano 参考手册
