# 实时 Linux PREEMPT_RT 在边缘计算中的应用

> **难度**：🟡 中级 | **领域**：实时系统、Linux 内核、工业控制 | **阅读时间**：约 20 分钟

## 日常类比

想象你是一家医院的急诊调度员。普通 Linux 像是一个尽力而为的调度系统——来了病人就排队，偶尔有人插队（中断），但没有严格的时间保证。如果正在给一个感冒病人看病时来了心梗患者，系统大概率会让心梗优先，但不能打包票——因为感冒病人可能正好占着唯一的 CT 机不放手。

PREEMPT_RT 补丁则把调度变成军事化管理：任何时刻，最高优先级的任务必须在确定的时间内获得 CPU，不管当前在做什么（哪怕在关着门处理中断），都可以被更高优先级的任务打断。这就是实时的含义——不是快，而是确定性。

在边缘计算场景中，工业控制、机器人运动、电力系统保护等应用需要微秒级的响应确定性。PREEMPT_RT 让标准 Linux 具备了这种能力。

## 1. 实时性基础概念

### 1.1 硬实时 vs 软实时

| 类型 | 定义 | 后果 | 例子 |
|------|------|------|------|
| 硬实时 | 必须在截止时间前完成 | 超时等于系统失败 | 汽车 ABS、心脏起搏器 |
| 紧实时 | 偶尔超时可接受 | 超时等于质量下降 | 视频编码、音频处理 |
| 软实时 | 统计意义上满足 | 超时等于体验差 | Web 服务响应 |

PREEMPT_RT 的目标是让 Linux 达到紧实时级别（最坏情况延迟小于 100us），接近硬实时（但不能替代专用 RTOS 如 VxWorks 在安全认证场景的地位）。

### 1.2 延迟的来源

从中断触发到任务响应，延迟由以下部分组成：

```
中断触发
  |
  v
[中断延迟 Interrupt Latency]
  - 中断被屏蔽的时间
  - 中断控制器路由时间
  |
  v
[调度延迟 Scheduling Latency]
  - 中断处理时间
  - 调度器决策时间
  - 上下文切换时间
  |
  v
任务开始执行
```

## 2. Linux 调度类与 PREEMPT_RT

### 2.1 Linux 调度器层次

```c
// Linux 调度类优先级（从高到低）
// 1. SCHED_DEADLINE - 最高优先级，EDF 调度
// 2. SCHED_FIFO     - 实时先来先服务
// 3. SCHED_RR       - 实时轮转
// 4. SCHED_NORMAL   - 普通 CFS 调度
// 5. SCHED_BATCH    - 批处理
// 6. SCHED_IDLE     - 空闲时才运行

#include <sched.h>
#include <pthread.h>

void setup_realtime_thread(pthread_t *thread, int priority) {
    struct sched_param param;
    param.sched_priority = priority;  // 1-99, 99 最高

    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
    pthread_attr_setschedparam(&attr, &param);
    pthread_attr_setinheritsched(&attr, PTHREAD_EXPLICIT_SCHED);

    pthread_create(thread, &attr, realtime_task, NULL);
}
```

### 2.2 PREEMPT_RT 核心机制

标准 Linux 内核有多个不可抢占区域，PREEMPT_RT 逐一解决：

| 问题 | 标准 Linux | PREEMPT_RT 方案 |
|------|-----------|----------------|
| 中断处理不可抢占 | hardirq 中执行 | 中断线程化 |
| 自旋锁关闭抢占 | spin_lock 禁止调度 | 转为 rt_mutex |
| 软中断在中断上下文 | softirq 延迟处理 | softirq 线程化 |
| RCU 回调延迟 | 回调在 softirq 中 | RCU 线程化处理 |
| printk 持锁时间长 | 同步输出到控制台 | 异步 printk |

### 2.3 中断线程化

这是 PREEMPT_RT 最核心的改变——把硬中断处理器变成普通内核线程：

```c
// 标准 Linux：中断处理在硬件中断上下文，不可被抢占
irqreturn_t sensor_irq_handler(int irq, void *dev_id) {
    // 这段代码执行时，同优先级和低优先级中断被阻塞
    read_sensor_data();
    wake_up(&sensor_waitqueue);
    return IRQ_HANDLED;
}

// PREEMPT_RT：中断处理在专用内核线程中
// 可以被更高优先级的实时线程抢占
request_threaded_irq(irq,
    sensor_irq_quick,   // 极短的顶半部
    sensor_irq_thread,  // 主处理在线程中
    IRQF_ONESHOT, "sensor", dev);
```

## 3. 内核配置与构建

### 3.1 获取 PREEMPT_RT 补丁

从 Linux 6.12 开始，PREEMPT_RT 已合并入主线内核（2024 年 11 月）。之前需要单独打补丁：

```bash
# Linux 6.12+ 直接配置即可
# 旧版本需要下载补丁
wget https://cdn.kernel.org/pub/linux/kernel/projects/rt/6.6/patch-6.6.52-rt43.patch.xz
xz -d patch-6.6.52-rt43.patch.xz
cd linux-6.6.52
patch -p1 < ../patch-6.6.52-rt43.patch
```

### 3.2 关键内核配置

```bash
# make menuconfig 关键选项

# 抢占模型选择（最重要的一项）
# General Setup -> Preemption Model
#   -> Fully Preemptible Kernel (Real-Time)
# CONFIG_PREEMPT_RT=y

# 高精度定时器
# CONFIG_HIGH_RES_TIMERS=y

# 禁用不确定性因素
# Timer frequency -> 1000 Hz
# CPU Frequency Scaling -> 关闭
# CPU Idle -> 关闭或限制 C-state
```

### 3.3 构建与验证

```bash
make -j$(nproc)
make modules_install
make install

# 验证内核版本
uname -a
# Linux edge-gw 6.6.52-rt43 #1 SMP PREEMPT_RT ...
```

## 4. 延迟测试与调优

### 4.1 cyclictest 基准测试

cyclictest 是测量 Linux 实时性能的标准工具：

```bash
# 安装 rt-tests
apt install rt-tests

# 基本测试：10 个线程，运行 5 分钟，FIFO 优先级 80
cyclictest -t 10 -p 80 -n -i 1000 -l 300000

# 输出示例（PREEMPT_RT 内核, 树莓派 4）
# T: 0 Min:   3 Act:   5 Avg:   7 Max:  42
# T: 1 Min:   3 Act:   6 Avg:   7 Max:  38

# 对比（标准内核, 同硬件）
# T: 0 Min:   4 Act:  12 Avg:  15 Max: 2847  (毫秒级尾部延迟!)
```

### 4.2 关键调优参数

```bash
# /etc/default/grub GRUB_CMDLINE_LINUX 追加:

# 隔离 CPU 核心给实时任务
# isolcpus=2,3
# 不在隔离核心上运行定时器
# nohz_full=2,3
# RCU 回调不在隔离核心
# rcu_nocbs=2,3
# 禁用频率调节
# intel_pstate=disable
# 关闭节能状态
# processor.max_cstate=0 idle=poll
```

### 4.3 IRQ 亲和性设置

```bash
#!/bin/bash
# 将所有非关键中断迁移到 CPU 0-1
# 保留 CPU 2-3 给实时任务

for irq in $(ls /proc/irq/ | grep -E '^[0-9]+$'); do
    if [ -f "/proc/irq/$irq/smp_affinity_list" ]; then
        echo "0-1" > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    fi
done

# 将传感器中断绑定到实时核心
SENSOR_IRQ=$(grep "sensor-gpio" /proc/interrupts | awk '{print $1}' | tr -d ':')
echo "2" > /proc/irq/$SENSOR_IRQ/smp_affinity_list
```

## 5. PREEMPT_RT vs 专用 RTOS

### 5.1 对比矩阵

| 维度 | PREEMPT_RT Linux | FreeRTOS | VxWorks | Zephyr |
|------|-----------------|----------|---------|--------|
| 最坏延迟 | 20-100 us | 1-10 us | 1-5 us | 5-20 us |
| 确定性保证 | 统计级 | 数学证明 | 数学证明+认证 | 统计级 |
| 安全认证 | 无 | 部分 | DO-178C/IEC 61508 | 无 |
| 驱动生态 | 极丰富 | 有限 | 丰富（商业） | 增长中 |
| 网络栈 | 完整 TCP/IP | lwIP | 完整 | 完整 |
| 开发难度 | 低 | 中等 | 高 | 中等 |
| 适用场景 | 工控/机器人 | MCU 控制 | 航空/医疗 | IoT+实时 |

### 5.2 混合架构方案

当既需要 Linux 生态又需要硬实时保证时：

```
方案 A: 双核异构 (如 STM32MP1, i.MX8)
+-----------------+    +-----------------+
| Linux (Cortex-A)|    | RTOS (Cortex-M) |
| - UI/网络/存储  |<-->| - 电机控制      |
| - 数据处理      | IPC| - 安全逻辑      |
+-----------------+    +-----------------+

方案 B: Hypervisor 分区 (Jailhouse/Xen)
+-----------------+    +-----------------+
| Linux VM        |    | RTOS VM         |
| (PREEMPT_RT)    |    | (Zephyr)        |
+-----------------+    +-----------------+
|         Jailhouse Hypervisor           |
+----------------------------------------+
|              硬件                       |
+----------------------------------------+
```

## 6. 工业 IoT 应用案例

### 6.1 EtherCAT 运动控制

EtherCAT 工业以太网要求 1ms 周期、抖动小于 10us：

```c
#include <time.h>
#include <pthread.h>
#include <sys/mman.h>

#define CYCLE_NS  1000000  // 1ms 周期

static void* ethercat_cycle(void* arg) {
    struct timespec next_cycle;
    clock_gettime(CLOCK_MONOTONIC, &next_cycle);

    while (running) {
        // 等待到精确的下一个周期点
        next_cycle.tv_nsec += CYCLE_NS;
        if (next_cycle.tv_nsec >= 1000000000) {
            next_cycle.tv_nsec -= 1000000000;
            next_cycle.tv_sec++;
        }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME,
                       &next_cycle, NULL);

        // EtherCAT 帧处理
        ec_receive_processdata();
        compute_control_output();
        ec_send_processdata();
    }
    return NULL;
}

int main() {
    // 锁定内存，防止页错误引起延迟
    mlockall(MCL_CURRENT | MCL_FUTURE);

    pthread_t rt_thread;
    struct sched_param param = { .sched_priority = 90 };
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
    pthread_attr_setschedparam(&attr, &param);

    // 绑定到隔离的 CPU 核心
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(2, &cpuset);
    pthread_attr_setaffinity_np(&attr, sizeof(cpuset), &cpuset);

    pthread_create(&rt_thread, &attr, ethercat_cycle, NULL);
    pthread_join(rt_thread, NULL);
    return 0;
}
```

### 6.2 典型延迟数据

在 Raspberry Pi CM4 + PREEMPT_RT 6.6 上的 cyclictest 结果：

```
配置: isolcpus=3, nohz_full=3, idle=poll
负载: stress-ng --cpu 3 --io 2 --vm 2
测试: cyclictest -t1 -p 95 -i 250 -l 1000000 -a 3

结果:
  Min:     2 us
  Avg:     4 us
  Max:    38 us   (100 万次采样)
  99.9%:  12 us
  99.99%: 28 us

对比标准 5.15 内核:
  Min:     4 us
  Avg:    18 us
  Max:  3200 us   (不可接受)
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 在树莓派上安装带 PREEMPT_RT 的内核（官方提供预编译包）
2. 运行 cyclictest 对比标准内核和 RT 内核的差异
3. 写一个简单的周期性实时线程（如 1ms 闪烁 GPIO）
4. 添加系统负载（stress-ng），观察最坏延迟变化
5. 逐步应用 isolcpus、irq affinity 等调优手段

### 7.2 具体调优建议

- **mlockall**：实时程序必须锁定内存，避免页错误带来的不确定延迟
- **预分配内存**：启动阶段分配好所有内存，运行时避免 malloc
- **优先级继承**：使用 pthread_mutexattr_setprotocol 启用优先级继承协议
- **禁用 CPU 节能**：C-state 和频率调节会引入数百微秒延迟
- **网络栈隔离**：如果实时任务不需要网络，把网络中断隔离到非实时核心

### 7.3 常见陷阱

- **printf/日志**：stdout 写操作可能阻塞数毫秒，实时循环中绝不能有
- **内存分配**：malloc/new 在实时路径中是禁止的（可能触发页错误或锁竞争）
- **文件 I/O**：任何磁盘操作都是非确定性的
- **共享库加载**：dlopen 会引入不确定延迟，应使用静态链接

## 参考文献

1. Linux Foundation. "PREEMPT_RT Merged into Linux 6.12 Mainline." 2024.
2. Reghenzani, F., et al. "The Real-Time Linux Kernel: A Survey on PREEMPT_RT." ACM Computing Surveys, 2019.
3. Gleixner, T. "The PREEMPT_RT Patchset." Linux Plumbers Conference, 2023.
4. Cerqueira, F., Brandenburg, B. "A Comparison of Scheduling Latency in Linux, PREEMPT_RT, and LITMUS." OSPERT, 2013.
5. rt-tests maintainers. "cyclictest documentation." 2024. https://wiki.linuxfoundation.org/realtime/
6. Red Hat. "Red Hat Enterprise Linux for Real Time." Product Documentation, 2024.
7. Raspberry Pi Ltd. "Real-Time Kernel for Raspberry Pi." 2024.
8. EtherCAT Technology Group. "EtherCAT on Linux Real-Time." Application Note, 2023.
9. Brown, J. "RT-Preempt Howto." Linux Wiki, 2024.
10. Oliveira, D., et al. "Demystifying the Real-Time Linux Scheduling Latency." EuroSys 2024.
