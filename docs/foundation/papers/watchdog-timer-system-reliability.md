---
schema_version: '1.0'
id: watchdog-timer-system-reliability
title: 看门狗定时器在嵌入式系统可靠性中的作用
layer: 1
content_type: UNKNOWN
difficulty: beginner
reading_time: 15
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 看门狗定时器在嵌入式系统可靠性中的作用

> **难度**：🟢 初级 | **领域**：嵌入式可靠性 | **阅读时间**：约 15 分钟

## 引言

想象你养了一只牧羊犬看羊。羊群正常时它趴着休息，但只要羊跑偏了就冲过去赶回来。如果牧羊犬自己打盹了怎么办？你给它定了个规矩：每 5 分钟必须回羊圈门口按按钮，连续 15 分钟没按就说明它也出问题了，你要亲自上山查看。

看门狗定时器 (Watchdog Timer, WDT) 就是这只牧羊犬。它是一个独立倒计时器：程序正常运行时定期"喂狗"(重置计数器)，倒计时归零前喂了就没事；一旦程序跑飞或死锁，没人喂狗，倒计时归零就触发系统复位，让设备从异常中恢复。

在无人值守的 IoT 场景中，设备挂在电线杆上、埋在农田里，你不可能每次死机都跑过去按复位键。看门狗就是最后一道防线——让设备"自救"。

## 1. 为什么嵌入式系统会"挂"

### 1.1 常见的系统异常来源

嵌入式系统没有桌面操作系统的进程隔离和内存保护，一段野指针就能让整个系统崩溃：

| 异常类型 | 典型原因 | 表现 |
|----------|---------|------|
| 死循环 | while 条件永远为真、状态机卡死 | CPU 占用 100%，其他任务饿死 |
| 死锁 | 多个互斥锁循环等待 | 两个任务都卡住 |
| 野指针/栈溢出 | 数组越界、递归过深 | HardFault，跳到非法地址 |
| 外设无响应 | I2C 从机拉低 SCL 不放 | 驱动层阻塞在等待应答 |
| 中断风暴 | 故障传感器持续触发中断 | 主循环跑不到 |
| EMI 干扰 | 强电磁脉冲翻转 RAM 位 | 变量值突变、逻辑异常 |

### 1.2 没有"看门狗"的后果

- 消费电子：用户手动重启，最多骂一句
- 工业控制：产线停工，损失以小时计
- 远程 IoT：设备在荒郊野外，人工复位成本极高，可能永远失联

看门狗核心价值：**用一次自动复位，替代一次人工干预**。

## 2. 两种看门狗：IWDG vs WWDG

STM32 提供两种硬件看门狗，时钟源、机制和场景完全不同。

### 2.1 独立看门狗 (IWDG)

独立看门狗由专用低速时钟 (LSI, 约 32-40 kHz) 驱动，即使主时钟崩溃，IWDG 仍在倒计时。

```
LSI (32kHz) --> 预分频器 --> 倒计数器 --> 归零 --> 系统复位
                    ^                          |
                    +------ 喂狗 (KR=0xAAAA) ---+
```

- 超时范围：约 0.1 ms ~ 26 秒
- 一旦启用无法关闭
- 低功耗模式下可选继续运行或停止

### 2.2 窗口看门狗 (WWDG)

窗口看门狗引入"时间窗口"：不仅不能喂太晚，也不能喂太早。喂狗必须落在 [T_window, T_timeout] 内。

```
    喂太早!            可以喂狗           喂太晚!
   |<--禁止-->|<------窗口内------>|<--禁止-->|
   0       T_window            T_timeout  复位!
```

WWDG 由 APB1 总线时钟驱动，7 位计数器 (0x40 ~ 0x7F)，递减到 0x3F 时触发复位。

### 2.3 IWDG vs WWDG 对比

| 特性 | IWDG | WWDG |
|------|------|------|
| 时钟源 | LSI (独立低速) | APB1 (系统总线) |
| 计数器宽度 | 12 位 | 7 位 |
| 超时范围 | 0.1 ms ~ 26 s | 几十 us ~ 几十 ms |
| 窗口约束 | 无 | 必须在窗口内喂 |
| 低功耗行为 | 可选继续/停止 | 随系统时钟停止 |
| 可否关闭 | 启动后不可关闭 | 可通过 EWI 延迟 |
| 早期中断 | 无 | 有 (EWI) |
| 典型用途 | 通用监控 | 精确时序、安全关键 |

**选择建议**：大多数 IoT 项目用 IWDG 就够了；需要严格时序约束时用 WWDG，或两者同时使用。

## 3. 超时时间计算

### 3.1 IWDG 超时计算

```
T_timeout = (Prescaler x Reload_Value) / LSI_Freq
```

以 LSI = 40 kHz 为例：

| 预分频 | 重载值 | 超时时间 |
|--------|--------|---------|
| 4 | 4095 | 0.41 ms |
| 64 | 1000 | 1.6 s |
| 256 | 4095 | 26.2 s |

### 3.2 WWDG 超时计算

```
T_timeout = (T[6:0] - 0x3F) x T_pclk1 / (4096 x 2^WDGTB)
T_window = (T[6:0] - W[6:0]) x T_pclk1 / (4096 x 2^WDGTB)
```

示例 (PCLK1=36MHz, WDGTB=8, 初值=0x7F, 窗口=0x5F)：T_timeout = 54.6 ms，T_window = 27.3 ms。喂狗必须在 27.3 ms ~ 54.6 ms 的时间窗口内完成。

## 4. 喂狗策略

### 4.1 任务级喂狗 vs 中断喂狗

```c
// --- 错误：在定时器中断里喂狗 ---
void TIM2_IRQHandler(void) {
    IWDG_ReloadCounter();  // BUG: 中断还在跑，主循环早死了
    TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
}
```

中断喂狗只能证明中断还活着，主循环死锁时看门狗永远不超时——形同虚设。

```c
// --- 正确：主循环喂狗 + 任务心跳检测 ---
volatile uint32_t g_task_heartbeat[TASK_NUM];
void main_loop(void) {
    while (1) {
        bool all_alive = true;
        for (int i = 0; i < TASK_NUM; i++) {
            if (get_tick() - g_task_heartbeat[i] > TASK_TIMEOUT_MS)
                { all_alive = false; break; }
        }
        if (all_alive) IWDG_ReloadCounter();  // 所有任务正常才喂
    }
}
```

### 4.2 多任务看门狗模式

RTOS 环境中，每个任务维护心跳计数器，看门狗任务统一检查：

```c
#define MAX_TASKS 8
typedef struct { TaskHandle_t handle; uint32_t last_checkin, timeout_ms; } watched_task_t;
static watched_task_t s_watched[MAX_TASKS];
static uint8_t s_watched_count = 0;

void task_checkin(TaskHandle_t self) {  // 各任务在主循环中签到
    for (int i = 0; i < s_watched_count; i++)
        if (s_watched[i].handle == self)
            { s_watched[i].last_checkin = xTaskGetTickCount(); return; }
}

void watchdog_task(void *pv) {  // 看门狗守护任务
    IWDG_Init(IWDG_Prescaler_64, 1000);  // 约 1.6s 超时
    while (1) {
        bool all_ok = true;
        for (int i = 0; i < s_watched_count; i++) {
            uint32_t elapsed = xTaskGetTickCount() - s_watched[i].last_checkin;
            if (elapsed > s_watched[i].timeout_ms)
                { all_ok = false; log_error("Task %d timeout", i); break; }
        }
        if (all_ok) IWDG_ReloadCounter();
        vTaskDelay(pdMS_TO_TICKS(500));
    }
}
```

## 5. 窗口看门狗的优势

### 5.1 为什么"不能太早喂"很重要

程序跑飞后恰好跳到一段包含喂狗指令的代码，反复执行时独立看门狗永远不会超时——这是"误喂"问题。窗口看门狗通过时间窗口约束解决：

- 喂太早 = 程序可能在错误路径快速循环 = 复位
- 喂太晚 = 程序卡住了 = 复位
- 精确窗口内喂狗 = 程序按预期执行 = 安全

### 5.2 早期唤醒中断 (EWI)

当计数器递减到 0x40 时，WWDG 可触发早期唤醒中断，给最后一次自救机会：

```c
void HAL_WWDG_EarlyWakeupCallback(WWDG_HandleTypeDef *hwwdg) {
    emergency_save_state();   // 保存关键数据
    motor_emergency_stop();   // 关闭危险外设
    // 不要在此回调中喂狗，否则窗口看门狗失去意义
}
```

## 6. 外部看门狗 IC

### 6.1 为什么需要外部看门狗

内部看门狗的根本局限：MCU 供电异常或内部 LSI 时钟出问题时，可能无法可靠触发复位。外部看门狗 IC 提供更强独立性。

### 6.2 TPS3823

TI 的 TPS3823 是常用外部看门狗 IC：

- 供电范围：1.1 V ~ 5.5 V
- 看门狗超时：典型 1.6 s
- 手动复位输入 (MR)：可接按钮
- 低静态电流：15 uA
- 内置电源监控：VDD 低于阈值也触发复位

```
              VDD
               |
              [R] 10k
               |
MCU_GPIO ----+---- TPS3823 WDI

TPS3823 WDO -----> MCU nRST (低有效复位)
TPS3823 MR  <----- 复位按钮 (低有效)
```

### 6.3 内部 vs 外部看门狗对比

| 特性 | 内部 WDT | 外部 WDT IC |
|------|---------|-------------|
| 独立性 | 与 MCU 共用供电 | 独立供电监控 |
| 电压监控 | 需额外配置 BOR | 内置 |
| 成本 | 零 | 几毛到几元 |
| PCB 面积 | 零 | SOT-23/SC-70 |
| 配置灵活性 | 可编程 | 通常固定超时 |
| 安全认证 | 需软件配合 | 硬件级别保障 |

一般 IoT 项目用内部 IWDG 即可；安全关键应用建议内+外双看门狗。

## 7. 低功耗模式下的看门狗

看门狗和低功耗天然矛盾——看门狗需要定时喂，低功耗需要长时间睡。

| 低功耗模式 | IWDG | WWDG | 处理方式 |
|-----------|------|------|---------|
| Sleep | 继续运行 | 继续运行 | 正常喂狗 |
| Stop | 可配置 | 停止 | 配置停止或 RTC 定时唤醒喂狗 |
| Standby | 停止 | 停止 | 唤醒后重新初始化 |
| Shutdown | 停止 | 停止 | 唤醒后重新初始化 |

Stop 模式下 IWDG 仍在运行时，需用 RTC 定时唤醒喂狗：

```c
void enter_stop_with_iwdg(void) {
    while (1) {
        RTC_SetWakeUpCounter(1000);  // 1s 唤醒 (IWDG 超时 1.6s)
        RTC_WakeUpCmd(ENABLE);
        PWR_EnterSTOPMode(PWR_Regulator_LowPower, PWR_STOPEntry_WFI);
        SystemInit();           // 重配时钟 (Stop 后 HSI 8MHz)
        IWDG_ReloadCounter();   // 喂狗
        process_pending_work();
        if (should_wake_fully()) break;
    }
}
```

如果选择在 Stop 下关闭 IWDG，代价是此期间程序异常无法自动恢复。电池供电场景可选关闭，但需确保有外部唤醒源。

## 8. STM32 看门狗配置代码

### 8.1 IWDG 初始化

```c
#include "stm32l4xx_hal.h"
// LSI=32kHz, Prescaler=32, Reload=1000 => T=1.0s
void IWDG_Init(void) {
    IWDG_HandleTypeDef hiwdg;
    hiwdg.Instance = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_32;
    hiwdg.Init.Reload = 1000;
    hiwdg.Init.Window  = IWDG_WINDOW_DISABLE;
    HAL_IWDG_Init(&hiwdg);  // 一旦启动无法停止
}
void IWDG_Feed(void) {
    IWDG_HandleTypeDef hiwdg = {.Instance = IWDG};
    HAL_IWDG_Refresh(&hiwdg);
}
```

### 8.2 WWDG 初始化

```c
void WWDG_Init(void) {
    WWDG_HandleTypeDef hwwdg;
    hwwdg.Instance = WWDG;
    hwwdg.Init.Prescaler = WWDG_PRESCALER_8;
    hwwdg.Init.Window    = 0x5F;
    hwwdg.Init.Counter   = 0x7F;
    hwwdg.Init.EWIMode   = WWDG_EWI_ENABLE;
    HAL_WWDG_Init(&hwwdg);
}
```

CubeMX 配置：Pinout & Configuration -> IWDG/WWDG -> Activated -> 设置预分频和重载值 -> 生成代码后在主循环加喂狗。

## 9. 常见错误与陷阱

### 9.1 喂狗太早

```c
void SystemInit(void) {
    IWDG_Init();
    IWDG_Feed();  // BUG: 后面的初始化如果死循环，这行白喂了
}
```

正确做法：系统完全就绪后才开始喂狗，初始化阶段超时要设足够大。

### 9.2 在错误上下文中喂狗

```c
// 错误：中断喂狗，主循环卡死也看不出来
void EXTI0_IRQHandler(void) {
    IWDG_ReloadCounter();  // BUG!
}
```

必须通过心跳检测，在主循环中根据所有任务状态决定是否喂狗。

### 9.3 喂狗间隔与超时太接近

```c
// 危险：余量仅 100ms，中断延迟就可能导致超时
#define FEED_INTERVAL_MS  900
#define WDG_TIMEOUT_MS    1000

// 安全：至少留 50% 余量
#define FEED_INTERVAL_MS  500
#define WDG_TIMEOUT_MS    1500
```

### 9.4 关键初始化前启动看门狗

```c
void main(void) {
    IWDG_Init();  // 超时 100ms
    LCD_Init();   // 80ms
    WiFi_Init();  // 100ms
    // 还没初始化完就被复位 => 无限重启循环!
}
```

### 9.5 喂狗代码散落各处

```c
// 反模式：到处喂狗，关键任务卡死但其他路径还在喂
void task_a(void) { IWDG_Feed(); /* ... */ }
void task_b(void) { IWDG_Feed(); /* ... */ }
void isr_handler(void) { IWDG_Feed(); /* ... */ }
```

正确做法：集中一处喂狗，根据所有任务心跳状态决定。

## 10. 安全关键系统中的看门狗

### 10.1 IEC 61508 对看门狗的要求

| SIL 等级 | 看门狗要求 |
|----------|-----------|
| SIL 1 | 至少一个内部看门狗 |
| SIL 2 | 内部看门狗 + 独立时钟源，或外部 IC |
| SIL 3 | 双看门狗 (内+外)，独立供电监控，窗口看门狗 |
| SIL 4 | 通常要求冗余 MCU，各有独立看门狗 |

### 10.2 安全看门狗设计要点

SIL 2+ 系统需满足：独立性 (时钟独立于 CPU)、多样性 (内+外避免共因失效)、测试性 (上电验证复位通路)、不可绕过 (启动后不可关闭)、故障安全 (看门狗本身故障可检测)。

```c
void test_watchdog(void) {
    if (RTC->BKP0R == WDG_TEST_MAGIC) {
        RTC->BKP0R = 0; return;  // 第二次启动，测试通过
    }
    RTC->BKP0R = WDG_TEST_MAGIC;
    IWDG_Init();
    while (1);  // 故意不喂狗，等看门狗复位验证通路
}
```

## 11. IoT 远程设备的看门狗恢复策略

### 11.1 多层恢复架构

```
第 1 层：任务级自恢复 — 检测任务超时，尝试重启该任务
第 2 层：看门狗复位 — 整个系统复位重启
第 3 层：硬件看门狗断电重启 — 外部 IC 触发 nRST 或控制电源开关
第 4 层：远程 OTA 修复 — 复位后上报日志，云端推送修复固件
```

### 11.2 崩溃日志与远程诊断

```c
typedef struct __attribute__((packed)) {
    uint32_t magic, reset_reason, pc_at_fault, task_id, uptime_ms, crc;
} crash_log_t;
void HardFault_Handler(void) {
    crash_log_t *log = (crash_log_t *)RTC_BKP_BASE;
    log->magic = 0xDEADBEEF;
    log->pc_at_fault = __get_PSP();
    log->uptime_ms = get_system_tick();
    while (1);  // 等看门狗复位
}
void check_crash_log(void) {
    crash_log_t *log = (crash_log_t *)RTC_BKP_BASE;
    if (log->magic == 0xDEADBEEF) { cloud_report_crash(log); log->magic = 0; }
}
```

### 11.3 防无限重启循环

```c
uint32_t crash_count = RTC_ReadBackupRegister(RTC_BKP_CRASH_COUNT);
if (crash_count > 3) { enter_safe_mode(); }  // 只启动基本功能，等 OTA
else { RTC_WriteBackupRegister(RTC_BKP_CRASH_COUNT, crash_count + 1); normal_boot(); }
if (get_system_tick() > 5 * 60 * 1000)  // 正常运行 5 分钟后清除计数
    RTC_WriteBackupRegister(RTC_BKP_CRASH_COUNT, 0);
```

## 总结

看门狗定时器是嵌入式系统可靠性的最后防线，核心要点：

1. **本质**：独立倒计时器，超时未喂则复位，实现"自动自救"
2. **两类看门狗**：IWDG (独立时钟、通用) 和 WWDG (窗口约束、精确时序)
3. **喂狗策略**：主循环中基于任务心跳喂狗，绝不能在中断中喂
4. **多任务监控**：每个任务签到，统一检查，全部正常才喂
5. **窗口看门狗**：解决"误喂"问题，要求在精确窗口内喂狗
6. **外部看门狗**：更高独立性，安全关键系统建议内+外双看门狗
7. **低功耗矛盾**：Stop 下用 RTC 唤醒喂狗，或关闭 IWDG 接受风险
8. **常见错误**：中断喂狗、余量不足、初始化前启动、散落式喂狗
9. **安全标准**：IEC 61508 SIL 2+ 要求双看门狗 + 独立供电监控
10. **IoT 恢复**：分层恢复 + 崩溃日志 + 防无限重启，从自救到远程修复

**看门狗不是防止 bug 的，而是在 bug 发生后让设备能自己站起来。**

## 参考文献

1. STMicroelectronics. RM0351: STM32L4x6 Reference Manual, Chapter 33-34: IWDG and WWDG. 2020.
2. Texas Instruments. TPS3823 Datasheet: Supply Voltage Supervisor With Watchdog Timer. SLVS166W, 2019.
3. IEC 61508: Functional Safety of E/E/PE Safety-Related Systems, Part 2. 2010.
4. Barr M. "Watchdog Timers," Embedded Systems Programming, Nov 2001.
5. Regehr J. "Using Watchdog Timers in Embedded Systems," University of Utah, 2020.
