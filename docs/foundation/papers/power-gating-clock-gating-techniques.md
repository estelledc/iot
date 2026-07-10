---
schema_version: '1.0'
id: power-gating-clock-gating-techniques
title: 电源门控与时钟门控低功耗技术详解
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
# 电源门控与时钟门控低功耗技术详解
> **难度**：🔴 高级 | **领域**：低功耗IC设计 | **阅读时间**：约 22 分钟

## 引言

想象一座办公楼：时钟门控就像下班后关掉空调和照明 -- 人不在，但办公桌上的文件还在；电源门控则像拉闸断电 -- 整层楼完全断电，桌面清空，再来上班时需要从大堂重新领文件、重新开设备。两种策略都能省电，但省的幅度不同，付出的"恢复代价"也不同。低功耗IC设计的核心权衡就在于此：**省多少电 vs 醒来要多快**。

本文从CMOS功耗来源出发，系统梳理时钟门控和电源门控的原理、实现方式、辅助结构(retention register, isolation cell)、系统级集成(UPF, power domain, power state machine)，并延伸到MCU级别的电源域架构与软件控制，最后对三大低功耗手段做横向比较。

## 1. 功耗来源：静态与动态

### 1.1 动态功耗 (Dynamic Power)

动态功耗来自信号翻转(switching)：

```
P_dynamic = a * C_L * V_DD^2 * f
```

- `a` -- 活动因子(0~1)；`C_L` -- 负载电容；`V_DD` -- 供电电压；`f` -- 时钟频率

关键洞察：动态功耗与电压平方成正比，降电压比降频率更有效。

### 1.2 静态功耗 (Static Power)

静态功耗来自漏电流(leakage)，即使不翻转也在耗电：

```
P_static = I_leakage * V_DD
```

| 漏电流类型 | 机制 | 随工艺缩放趋势 |
|-----------|------|---------------|
| 亚阈值漏电 (subthreshold) | 栅压低于阈值时仍有微弱电流 | 每代增大约10x |
| 栅极漏电 (gate oxide) | 薄氧化层隧穿电流 | 高k介质可缓解 |
| 结漏电 (junction) | PN结反偏漏电 | 相对较小 |

28nm以下节点，静态功耗可达总功耗的30-50%。

### 1.3 两种功耗的对策差异

| 特性 | 动态功耗 | 静态功耗 |
|------|---------|---------|
| 根本原因 | 信号翻转 | 漏电流 |
| 降压效果 | 非常有效 (V^2) | 有限 (线性) |
| 时钟门控能否消除 | 可以 | 不能 |
| 电源门控能否消除 | 可以 | 可以 |

结论：时钟门控只管动态功耗；要消灭静态功耗，必须电源门控或彻底断电。

## 2. 时钟门控 (Clock Gating)

### 2.1 基本原理与AND门插入

核心思想：**如果寄存器不需要更新，就不要给它们送时钟**。时钟树有巨大电容负载，即使数据不翻转，时钟缓冲器也在持续充放电。最直觉的实现是在时钟路径上插入AND门：

```
         CLK
          |
         AND <-- enable
          |
        GCLK (gated clock)
```

**问题**：enable在CLK为高时变化会产生毛刺(glitch)，导致误捕获。

### 2.2 集成时钟门控单元 (ICG Cell)

工业标准做法使用ICG cell，内部包含一个负电平透明锁存器：

```
           CLK
            |
    +-------+-------+
    |     Latch     | <-- enable
    |  (负电平透明)  |
    +-------+-------+
            |
           AND --> GCLK
```

CLK为低时latch透明，enable通过；CLK为高时latch保持，enable被锁住。GCLK不会出现毛刺。标准库命名如`TLATNTSCAx`、`CKLNQ`等。

### 2.3 RTL级与综合级门控

```verilog
// 综合工具自动推断时钟门控 (推荐)
always @(posedge clk or negedge rst_n) begin
  if (!rst_n) data_reg <= 0;
  else        data_reg <= enable ? data_in : data_reg;
end
```

位宽较大(如32位)时，综合工具提取共用enable，插入一个ICG cell代替32个MUX，面积和功耗都更优。

```tcl
# Synopsys DC: 开启自动时钟门控推断
set_clock_gating_style -sequential_cell latch -max_fanout 32 -num_stages 2
```

| 层级 | 粒度 | 实现方式 | 省电效果 |
|------|------|---------|---------|
| 模块级 | 整个IP核 | 软件控制ICG | 大 |
| 寄存器级 | 单个/组寄存器 | 综合自动推断 | 中 |
| 门级 | 单个触发器 | 极少使用 | 小 |

## 3. 电源门控 (Power Gating)

### 3.1 Header Switch与Footer Switch

**Header Switch (PMOS)** -- 在VDD侧切断：

```
    VDD --> [PMOS] <-- SLEEP (低有效)
              |
            VVDD (虚拟电源)
              |
           [逻辑] --> GND
```

**Footer Switch (NMOS)** -- 在GND侧切断：

```
    VDD --> [逻辑]
              |
            VGND (虚拟地)
              |
           [NMOS] <-- SLEEP (高有效) --> GND
```

| 特性 | Header Switch | Footer Switch |
|------|-------------|---------------|
| 导通电阻 | 较高 | 较低 (NMOS迁移率高) |
| 面积 | 较大 | 较小 |
| 噪声影响 | 虚拟电源波动 | 虚拟地波动，影响更大 |
| 实际使用 | **更常见** | 较少单独使用 |

### 3.2 MTCMOS (Multi-Threshold CMOS)

- 逻辑部分使用低阈值(LVT)晶体管 -- 速度快但漏电大
- 开关部分使用高阈值(HVT)晶体管 -- 漏电小，作为电源开关
- 活跃：SLEEP=0，header导通；休眠：SLEEP=1，漏电降3-4个数量级

### 3.3 开关阵列与dI/dt问题

电源开关是大量并联的PMOS阵列。开关越大导通电阻越小但面积和漏电越大。所有开关同时打开会产生浪涌电流(inrush current)导致电压骤降。解决方案是**分级开启**：

```verilog
always @(posedge wake_req) begin
  switch_en[0] <= 1'b1;  // 第1级立即开
  #DELAY_STG1;
  switch_en[1] <= 1'b1;  // 第2级延迟开
  #DELAY_STG2;
  switch_en[2] <= 1'b1;  // 第3级
  switch_en[3] <= 1'b1;  // 第4级
end
```

## 4. 电源门控的辅助结构

断电前要保存状态，断电处要隔离信号，恢复后要还原状态。

### 4.1 Retention Register (状态保持寄存器)

双轨供电：主寄存器用可断电VVDD，影子寄存器用常开VDD。

```
  VDD (always-on)         VVDD (switchable)
   |                        |
[影子寄存器] <-- SAVE --- [主寄存器]
   |                        |
   └--- RESTORE ----------→┘
```

操作：SAVE(断电前写入影子) -> 断电(主丢失，影子保持) -> RESTORE(供电后写回)。面积代价约1.5-2x。

### 4.2 Isolation Cell (隔离单元)

断电后输出浮空等效X态，可能导致下游PMOS/NMOS同时导通产生短路电流。

| 策略 | 断电后输出 | 适用场景 |
|------|----------|---------|
| Clamp-to-0 | 钳位到0 | 默认低有效 |
| Clamp-to-1 | 钳位到1 | 默认高有效 |
| Clamp-to-last | 保持最后值 | 需维持状态 |

```
断电域信号 ──┐
             OR (isolation cell) ──→ 活跃域
ISO_EN ──────┘   (ISO_EN=1时钳位到1)
```

### 4.3 Power Controller时序

```
[ACTIVE] ──SAVE──→ [SAVING] ──done──→ [ISOLATE] ──iso_ack──→ [SWITCH_OFF]
                                                                    │
[ACTIVE] ←─RESTORE── [RESTORING] ←─pwr_ok── [SWITCH_ON] ←─wake────┘
```

断电顺序：SAVE -> ISO -> SWITCH_OFF；上电顺序：SWITCH_ON -> pwr_ok -> ISO_OFF -> RESTORE

## 5. 系统级电源管理

### 5.1 电源域划分与Always-On域

```
┌─────────────────────────────────┐
│ VDD_ALWAYS (常开域)              │
│  PMU / RTC / GPIO / 中断控制器   │
├─────────────────────────────────┤
│ VDD_CORE (可门控)                │
│  CPU / SRAM                     │
├─────────────────────────────────┤
│ VDD_PERIPH (可门控)              │
│  UART / SPI / I2C / ADC        │
└─────────────────────────────────┘
```

划分原则：功能耦合模块同域；关键路径模块放常开域；经常独立空闲的模块单独成域。Always-on域用HVT器件减漏电，面积尽量小，可降电压但不断电。

### 5.2 Power State Machine

```
              ┌──────────┐
 中断/唤醒 ──→│  ACTIVE  │ 所有域上电
              └────┬─────┘
                   │ 空闲超时
              ┌────v─────┐
              │  SLEEP   │ CPU域断电, 外设可选
              └────┬─────┘
                   │ 深度空闲
              ┌────v─────┐
  唤醒 ──────→│DEEP SLEEP│ 仅Always-on域
              └────┬─────┘
                   │ 长时间无活动
              ┌────v─────┐
  唤醒 ──────→│ STANDBY  │ RTC only
              └──────────┘
```

### 5.3 UPF (Unified Power Format)

IEEE 1801标准，Tcl语法描述电源意图，与RTL分离：

```tcl
create_power_domain PD_CPU -includes {.cpu_inst}
create_power_switch SW_CPU -domain PD_CPU \
  -input_supply_port {in VDD_TOP} \
  -output_supply_port {out VDD_CPU} \
  -control_port {sleep_ctrl} \
  -on_state {ON in {!sleep_ctrl}} \
  -off_state {OFF {!sleep_ctrl}}
create_isolation_strategy ISO_CPU -domain PD_CPU \
  -isolation_signal iso_ctrl -isolation_value 0
create_retention_policy RET_CPU -domain PD_CPU -retention_net VDD_TOP
add_power_state PD_CPU -state ON  {-supply_expr {power == FULL_ON}}
add_power_state PD_CPU -state OFF {-supply_expr {power == OFF}}
create_pst pst1 -supplies {VDD_TOP VDD_CPU VDD_PERIPH}
add_pst_state pst1_active -pst pst1 -state {ON ON ON}
add_pst_state pst1_sleep  -pst pst1 -state {ON OFF ON}
add_pst_state pst1_deep   -pst pst1 -state {ON OFF OFF}
```

UPF价值：电源管理与功能逻辑解耦；综合、验证、物理设计共用同一份；形式化工具可检查一致性。

## 6. MCU级别的电源门控

### 6.1 STM32电源域架构 (以STM32L4为例)

| 模式 | CPU | Flash | Regulator | 唤醒时间 | 典型电流 |
|------|-----|-------|-----------|---------|---------|
| Run | ON | ON | MR | - | ~100 uA/MHz |
| Sleep | OFF | ON | MR | ~2 us | ~4 mA |
| Stop 0 | OFF | OFF | MR | ~5 us | ~8 uA |
| Stop 1 | OFF | OFF | LPR | ~5 us | ~600 nA |
| Stop 2 | OFF | OFF | LPR+SRAM2 | ~5 us | ~300 nA |
| Standby | OFF | OFF | OFF | ~50 ms | ~20 nA |
| Shutdown | OFF | OFF | OFF | ~500 ms | ~3 nA |

### 6.2 软件控制电源域

```c
void enter_stop2(void) {
    EXTI->IMR1 |= EXTI_IMR1_IM0;     // 配置唤醒源
    PWR->CR1 |= PWR_CR1_LPR;         // 低功耗调节器
    PWR->CR1 &= ~PWR_CR1_MRUDS;      // Stop 2 子模式
    PWR->CR1 |= PWR_CR1_LPUDS;
    SCB->SCR |= SCB_SCR_SLEEPDEEP_Msk;
    __WFI();                          // 进入深度睡眠
    // --- 唤醒后继续 ---
    SystemClock_Config();             // 重配时钟 (HSI->PLL->80MHz)
}
```

注意：唤醒后用HSI(16MHz)需重配PLL；SRAM1在Stop2中丢失，SRAM2可选保持；外设需重新初始化。

### 6.3 唤醒延迟分析

```
总延迟 = 信号传播(~10ns) + 电源开关开启(~1-10us) + 电压稳定(~1-5us)
       + PLL锁定(~50-200us) + Retention恢复(~100ns) + 软件初始化(~10-500us)
```

| 模式 | 功耗等级 | 唤醒延迟 |
|------|---------|---------|
| Run | 高 | 零 |
| Sleep | 中低 | 微秒 |
| Stop | 微 | 数微秒 |
| Standby | 纳 | 毫秒 |
| Shutdown | 极低 | 数百毫秒 |

## 7. 三大低功耗技术横向比较

| 维度 | 时钟门控 | 电源门控 | 电压缩放 (DVFS) |
|------|---------|---------|-----------------|
| 消除动态功耗 | 是 | 是 | 降低 (V^2) |
| 消除静态功耗 | 否 | 是 | 降低 (线性) |
| 状态保持 | 自动 | 需retention | 自动 |
| 信号隔离 | 不需要 | 需ISO cell | 需level shifter |
| 唤醒延迟 | <1 cycle | us~ms | us~ms |
| 实现复杂度 | 低 | 高 | 中 |
| 面积开销 | 极小 | 大 | 中 |
| 省电幅度 | 10-50x | 100-10000x | 2-10x |
| 适用场景 | 临时空闲 | 长时间空闲 | 性能可调 |

**组合策略**：

```
短空闲 (<1us)    -> 时钟门控
中空闲 (1us~1ms) -> 时钟门控 + DVFS
长空闲 (1ms~1s)  -> 电源门控 (部分域)
超长空闲 (>1s)   -> 电源门控 (全域) + 降压
```

**常见误区**：

- 错误：电源门控总比时钟门控好 -> 正确：短空闲时电源门控的唤醒代价不划算
- 错误：两者互斥只能选一个 -> 正确：互补，时钟门控管活跃态动态功耗，电源门控管空闲态静态功耗
- 错误：DVFS可完全替代电源门控 -> 正确：DVFS不消除漏电，深亚微米工艺下漏电占比高必须用电源门控

典型功耗参考 (40nm, 1MHz)：

| 状态 | 时钟门控 | 电源门控 | DVFS (0.6V) |
|------|---------|---------|-------------|
| 漏电功耗 | ~50 uA | ~0.1 uA | ~15 uA |
| 唤醒时间 | 1 cycle | 5-50 us | 10-100 us |

## 8. 设计实践与验证

**验证流程**：UPF编写 -> RTL+UPF功能仿真(检查ISO/Retention) -> 综合 -> GLS+UPF(检查X态) -> 形式化验证 -> 物理设计

**常见陷阱**：
1. 忘记isolation cell -> 断电域输出浮空，硅片失效
2. Retention时序违规 -> SAVE信号在断电后才到达
3. 跨域信号缺level shifter -> 电平不匹配
4. 开关阵列分布不均 -> 局部IR drop过大
5. 电源状态机死锁 -> 无法退出某状态

**电源感知仿真**：

```verilog
// vcs -upf design.upf -pa_sim ...
initial $monitor("PD_CPU: %s at %0t", $get_power_state(PD_CPU), $time);

property iso_before_poweroff;
  @(posedge clk) $fell(VDD_CPU) |-> $past(iso_en, 1);
endproperty
assert property (iso_before_poweroff);
```

## 总结

- **时钟门控**：低成本、零延迟，消除动态功耗，是所有低功耗设计的第一步
- **电源门控**：高收益、高代价，同时消除动态和静态功耗，需retention register、isolation cell、power controller三类辅助结构
- **电压缩放**：介于两者之间，通过降低电压降低两种功耗

系统级集成需要UPF描述电源意图，合理划分电源域，设计电源状态机。MCU级别的实现(如STM32L4)将这些概念具体化为可配置的寄存器和低功耗模式。选择哪种技术，取决于空闲时长、唤醒延迟要求和面积预算。

核心权衡永远是一个问题：**你愿意花多少唤醒时间，换多少省电？**

## 参考文献

1. Keating M, Flymm D, et al. *Low Power Methodology Manual: For System-on-Chip Design*. Springer, 2007.
2. Narendra S, Chandrakasan A. *Leakage in Nanometer CMOS Technologies*. Springer, 2006.
3. IEEE 1801-2015. *IEEE Standard for Design and Verification of Low-Power, Energy-Aware Electronic Systems*.
4. STMicroelectronics. *STM32L4x6 Reference Manual (RM0351)*. 2023.
5. Chandra R, et al. *Power-Aware Design Methodology for SoC*. Synopsys White Paper, 2019.
