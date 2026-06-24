# 太阳能采集MPPT算法与IoT节点集成

> **难度**：🔴 高级 | **领域**：能量采集系统 | **阅读时间**：约 22 分钟

## 引言

想象你在自助餐厅取餐,站在不同位置拿菜效率不同。如果你恰好站在出菜口旁边,取餐最快。太阳能电池也是如此 -- 光照和温度变化时,"最佳取菜位置"(最大功率点)也在移动。MPPT(最大功率点跟踪)就是帮你始终站在出菜口旁的导航系统。对于IoT节点,光照微弱时输出仅微瓦级,一个低效MPPT可能让节点无法存活。

## 1 太阳能电池电气特性

### 1.1 光伏效应与等效电路

太阳能电池基于光伏效应:光子能量大于禁带宽度时激发电子-空穴对,在PN结内建电场下形成光生电流。简化等效电路由光生电流源Iph、二极管D、串联电阻Rs和并联电阻Rsh组成。

```
      Iph
       |---->|---- Rs ----+---- I
       |  D              |
       +----<|---- Rsh ---+
```

### 1.2 I-V与P-V特性曲线

输出电流与电压关系: `I = Iph - I0*(exp((V+I*Rs)/(n*Vt))-1) - (V+I*Rs)/Rsh`

| 参数 | 符号 | 典型值(单晶硅) |
|------|------|---------------|
| 短路电流 | Isc | 8-10 A |
| 开路电压 | Voc | 0.5-0.7 V |
| MPP电流 | Imp | 约0.9*Isc |
| MPP电压 | Vmp | 约0.8*Voc |
| 填充因子 | FF | 0.7-0.85 |

### 1.3 环境因素影响

**光照强度**: 主要影响Isc,近似线性关系;Voc仅对数下降。弱光下功率损失主要来自电流减少。

**温度**: 主要影响Voc,每升高1C下降约2.2mV(硅电池),综合功率系数约-0.4%--0.5%/C。

## 2 最大功率点概念

### 2.1 为什么需要MPPT

太阳能电池输出功率P=V*I仅在某一电压点最大。直接接负载时工作点由负载阻抗决定,很少恰好在MPP。例如:某板Voc=5.5V、Isc=120mA,直接供3.3V系统得363mW,而MPP处约470mW,损失23%。

### 2.2 MPP数学条件

MPP满足dP/dV=0,即 `dI/dV = -I/V`。I-V曲线斜率绝对值等于电流电压之比,这是增量电导法的理论基础。

### 2.3 MPP动态特性

MPP非固定点,随光照角度和遮挡不断移动。IoT节点部署在树荫/窗边时,光照变化更剧烈,MPPT响应速度至关重要。

## 3 MPPT算法详解

### 3.1 扰动观察法(P&O)

周期性扰动电压(delta V),功率增加则同方向继续,减少则反向。

```
void pno_mppt(float v, float i, float *v_ref, int *dir) {
    float p = v * i;
    if (p > p_prev) {
        *v_ref += (*dir) * DELTA_V;  // 保持方向
    } else {
        *dir = -(*dir);              // 反转方向
        *v_ref += (*dir) * DELTA_V;
    }
    p_prev = p;
}
```

优点:实现简单,无需电池参数。缺点:稳态振荡损失能量;光照快变时误判方向;delta V选择困难。

### 3.2 增量电导法(IncCond)

利用dI/dV = -I/V条件,比较瞬时电导与增量电导判断工作点位置。

```
void inccond_mppt(float v, float i, float dv, float di) {
    float cond = i / v;
    float dcond = di / dv;
    if (fabs(dcond + cond) < EPS) {
        // 在MPP,无需动作
    } else if (dcond > -cond) {
        // MPP左侧,增大电压
    } else {
        // MPP右侧,减小电压
    }
}
```

优点:MPP处可不振荡;能区分扰动与环境变化。缺点:对ADC精度和噪声敏感;量化误差下完全消除振荡较难。

### 3.3 分数开路电压法(Fractional Voc)

Vmp约等于k_voc*Voc,k_voc通常0.75-0.85。周期性断开负载测Voc,再设定工作电压。

```
float fractional_voc_mppt(float k_voc) {
    float voc = measure_open_circuit_voltage();
    return k_voc * voc;  // 典型 k_voc = 0.76
}
```

优点:极简,无需电流传感器。缺点:测量Voc时断开负载损失能量;k_voc为经验值,偏差5-15%;本质是估算非跟踪。

### 3.4 分数短路电流法(Fractional Isc)

Imp约等于k_isc*Isc,k_isc通常0.85-0.95。需短路测量Isc,实现复杂且中断供电,实践中极少单独使用,可作为其他算法的初始化辅助。

### 3.5 算法对比与选择

| 特性 | P&O | IncCond | Frac Voc | Frac Isc |
|------|-----|---------|----------|----------|
| 复杂度 | 低 | 中 | 极低 | 高 |
| 稳态效率 | 95-97% | 97-99% | 85-92% | 85-90% |
| 动态响应 | 差 | 好 | 中 | 中 |
| IoT适用性 | 常用 | 推荐 | 超低功耗 | 极少用 |

IoT推荐: >10mW用IncCond(12-bit ADC);1-10mW用P&O;<1mW用Fractional Voc(传感器功耗可能超过MPPT收益)。

## 4 室内与室外太阳能采集差异

### 4.1 光照量级对比

| 环境 | 照度(lux) | 辐照度(W/m2) | 相对室外 |
|------|----------|-------------|---------|
| 室外直射 | 100,000 | 1000 | 1.0 |
| 室外阴天 | 10,000-30,000 | 100-300 | 0.1-0.3 |
| 室内窗边 | 1,000-3,000 | 1-3 | 0.001-0.003 |
| 室内办公 | 300-500 | 0.3-0.5 | 0.0003-0.0005 |

室内光照仅为室外1/1000到1/10000,原百毫瓦输出可能仅剩零点几毫瓦。

### 4.2 光谱与MPPT影响

室内LED/荧光灯光谱集中于可见光,红外极少。非晶硅(a-Si)在可见光响应优于晶硅,更适合室内。室内MPPT影响:功率极低时电路静态功耗占比大;光照为阶跃变化(开关灯)而非渐变;Voc可能低于储能最低电压,冷启动更困难。

## 5 IoT小型太阳能板选型

### 5.1 电池技术对比

| 参数 | 单晶硅 | 多晶硅 | 非晶硅 | DSSC |
|------|--------|--------|--------|------|
| 室外效率 | 18-22% | 15-18% | 6-10% | 8-12% |
| 室内效率 | 3-5% | 2-4% | 8-15% | 10-18% |
| 弱光响应 | 差 | 差 | 好 | 优 |
| 寿命 | 25年+ | 20年+ | 10-15年 | 5-10年 |

选型要点:面积<50cm2;确保Vmp高于储能最低充电电压;室内部署必选a-Si或DSSC;PET封装轻便但耐候性差。

### 5.2 常见商用小型板

| 型号 | 技术 | 尺寸(mm) | Vmp | Imp |
|------|------|----------|-----|-----|
| PowerFilm MP3-37 | a-Si | 64x37 | 3.0V | 22mA |
| IXYS KXOB22-12X1L | 单晶 | 22x7 | 0.5V | 50mA |
| Panasonic AM-1815CA | a-Si | 53x30 | 2.4V | 50uA@200lux |

## 6 能量采集IC详解

### 6.1 BQ25570 (TI)

冷启动电压330mV,内置boost+buck,MPPT用Fractional Voc法(可编程25%-80%),静态电流488nA(buck关)/7.5uA(buck开),支持电池和超级电容。适用室外/窗边,功率>10mW。

```
// BQ25570 MPPT比值配置
// R1=3.9M, R2=1.5M -> 比值 = 1.5/(3.9+1.5) = 0.278
// 对于Voc=5V的板, VMPPT = 0.278 * 5 = 1.39V
```

### 6.2 SPV1050 (ST)

冷启动电压120mV(太阳能),buck-boost拓扑,静态800nA,6档MPPT比值(50%-90%),最大输入约50mW。适用室内弱光,输入可能低于输出电压的场景。

### 6.3 AEM10941 (e-peas)

冷启动电压50mV/3uW,双路输出(LDO+buck-boost),静态150nA(MPPT关)/450nA(开),独立管理超级电容和电池。适用室内极弱光,冷启动要求高的场景。

```
// AEM10941冷启动序列
// VBAT<1.8V: 冷启动boost工作,无MPPT,效率约30%
// VBAT>1.8V: LDO使能
// VBAT>2.0V: buck-boost使能,MPPT开启
```

### 6.4 IC选型对比

| 特性 | BQ25570 | SPV1050 | AEM10941 |
|------|---------|---------|----------|
| 冷启动电压 | 330mV | 120mV | 50mV |
| 静态电流 | 488nA | 800nA | 450nA |
| 拓扑 | Boost+Buck | Buck-Boost | Boost+BB |
| 室内适用性 | 中 | 好 | 优 |
| 价格(1k) | $3.5 | $2.8 | $4.2 |

## 7 系统架构设计

### 7.1 完整能量链路

```
太阳能板 -> MPPT电路 -> 储能元件 -> 稳压器 -> 负载
   |            |             |           |
 光伏电池    DC-DC+MPPT   电容/电池   LDO/Buck: 3.3V/1.8V
```

系统总效率: `eta_sys = eta_MPPT * eta_storage * eta_regulator`,典型值0.61-0.86。

### 7.2 储能选择

| 特性 | 超级电容 | LiFePO4 | 固态锂电 |
|------|----------|---------|---------|
| 能量密度 | 5-10 Wh/kg | 90-160 Wh/kg | 200-260 Wh/kg |
| 循环寿命 | >500K次 | 2K-5K次 | 500-1K次 |
| 充放效率 | 95-98% | 90-95% | 85-90% |
| 自放电率 | 20-40%/月 | 2-5%/月 | 1-3%/月 |

建议:短期缓冲用超级电容(0.1-1F);跨夜用LiFePO4(50-200mAh);周级用固态锂电(注意循环寿命)。

## 8 能量预算计算

### 8.1 负载功耗建模

LoRaWAN环境监测节点示例:

| 模式 | 电流 | 时间 | 频率 | 日均功耗 |
|------|------|------|------|---------|
| 深睡眠 | 2uA | 连续 | - | 0.19mJ/s |
| 采样 | 5mA | 100ms | 1次/min | 0.03mJ/s |
| LoRa TX | 45mA | 100ms | 1次/10min | 0.025mJ/s |

日均总功耗约0.25mW。

### 8.2 采集能量估算与平衡

```
// 室外: 50cm2单晶硅 @1000W/m2, 效率18%
P_peak = 1000 * 0.005 * 0.18 = 0.9W (正午)
P_avg = 0.9 * 4h/24h = 150mW (日平均)

// 室内: 50cm2 a-Si @200lux
P_harvest = 0.5W/m2 * 0.005m2 * 0.10 = 0.25mW

// 室内节点能量缺口: 0.25*0.65=0.16mW < 0.25mW
// 调整采样间隔1min->5min后: P_load=0.06mW < 0.16mW -- 可行
```

## 9 间歇计算

### 9.1 概念与挑战

采集能量不足以连续运行时,系统在"计算-断电-重启"间循环。关键挑战:任务在任意点断电致中间状态丢失;重启后状态不一致;同一任务可能反复从头开始。

### 9.2 检查点策略

```
void intermittent_task() {
    restore_checkpoint(&state);
    while (!task_complete(state)) {
        step_result = compute_one_step(state);
        if (vbat_read() < V_THRESHOLD) {
            save_checkpoint(&state);
            power_down();  // 主动断电,恢复后继续
        }
        update_state(&state, step_result);
    }
    commit_result(state);
}
```

### 9.3 非易失处理器

MSP430FR系列(FRAM MCU)是当前最接近商用化的方案:FRAM写入速度与SRAM相当(~100ns),无次数限制,掉电数据保持10年以上,但读取功耗高于SRAM需缓存策略。

## 10 冷启动问题

### 10.1 问题描述

储能电压为零时,MPPT电路自身需供电才能工作,DC-DC无法启动,负载消耗阻碍电压上升 -- 这是能量采集最困难的阶段。

### 10.2 解决方案

**负载隔离**: 冷启动期间断开所有负载,采集能量仅充储能:

```
void power_management() {
    float vbat = read_battery_voltage();
    if (vbat < V_LOW) {
        load_switch_off();    // 断开负载
    } else if (vbat > V_HIGH) {
        load_switch_on();     // 接通负载
    }
    // 迟滞区间保持状态,避免频繁切换
}
```

**冷启动时间估算**:
```
// 室内: 25cm2 a-Si @200lux, 0.22F电容
// P_cold = 0.5*0.0025*0.10*0.30 = 37.5uW
// E_target = 0.5*0.22*1.8^2 = 0.356J
// t = 0.356/37.5e-6 = 9493s ≈ 2.6小时

// 室外: 50cm2 单晶 @1000W/m2, 1F电容
// P_cold = 1000*0.005*0.18*0.30 = 270mW
// E_target = 0.5*1*2.5^2 = 3.125J
// t = 3.125/0.270 = 11.6秒
```

## 11 实际设计实例

### 11.1 设计目标

室内窗边(~500lux)环境监测节点:SHT40温湿度 + nRF52833 BLE,5分钟采样,太阳能板<40cm2,连续阴天存活3天。

### 11.2 硬件选型与验证

| 组件 | 选型 | 理由 |
|------|------|------|
| 太阳能板 | AM-1815CA (a-Si) | 室内效率高,Vmp=2.4V |
| 采集IC | AEM10941 | 冷启动50mV,弱光优 |
| 储能 | 0.47F电容+CR1220 | 短期缓冲+长期备份 |
| MCU | nRF52833 | BLE5.0,睡眠1.2uA |
| 传感器 | SHT40 | 精度0.2C,待机0.4uA |

```
// 负载功耗(每5分钟周期)
// 睡眠: 1.2uA*3.3V*299.6s = 1186uJ
// 采样: 5mA*3.3V*0.1s = 1.65uJ
// BLE广播: 8mA*3.3V*0.03s*3 = 2.38uJ
// 周期总耗: 1190uJ, 平均功耗: 1190/300 = 3.97uW

// 采集: AM-1815CA@500lux ≈ 15uW, AEM10941效率50%
// P_harvest = 7.5uW, 余量: 7.5-3.97 = 3.53uW (89%)

// 3天阴天: 电容储能@3.0V=2115mJ
// 3天消耗: 343*3=1029mJ, 阴天采集(20%)=389mJ
// 净消耗: 1029-389=640mJ < 2115mJ -- 满足
```

### 11.3 软件架构

```
int main() {
    power_init();
    aem10941_init();
    if (is_cold_start()) cold_start_handler();

    while (1) {
        float vbat = read_vbat();
        if (vbat < V_LOW) { load_switch_off(); deep_sleep(); continue; }

        float temp, humi;
        sht40_read(&temp, &humi);
        ble_advertise(temp, humi);

        // 自适应采样间隔
        uint32_t sleep_sec;
        if (vbat > 3.0) sleep_sec = 300;
        else if (vbat > 2.5) sleep_sec = 600;
        else if (vbat > 2.0) sleep_sec = 1800;
        else { load_switch_off(); continue; }
        enter_low_power_sleep(sleep_sec);
    }
}
```

关键考量: AEM10941的VBAT_OK信号控制负载开关;超级电容选低漏电流型号;BLE用3次短广播代替连接;分压器用MOSFET控制仅在采样时接通。

## 总结

1. **MPPT必要性**: I-V曲线随环境动态变化,负载与电池特性不匹配导致能量损失
2. **算法选择**: 功率级决定算法 -- 毫瓦用IncCond,微瓦用Fractional Voc
3. **室内外差异**: 室内光照1/1000,需a-Si/DSSC,MPPT收益可能被自身功耗抵消
4. **储能设计**: 超级电容短期缓冲,电池长期储能,常组合使用
5. **间歇计算**: 能量不足的根本方案,需checkpoint或NV-Processor
6. **冷启动**: 最困难阶段,需专用电路和负载隔离,室内可能长达数小时
7. **系统效率**: 各级损耗相乘,需逐级优化,典型0.61-0.86
8. **能量自适应**: 优秀节点根据剩余能量动态调整行为

能量采集IoT设计的本质是在供给与需求间找平衡 -- 这正是工程学最核心的思维方式。

## 参考文献

1. Bazzi A M, Krein P T. A survey of maximum power point tracking techniques for photovoltaic systems[C]. IEEE ECCE, 2011: 2186-2192.
2. Sharma H, Haque A, Jaffery Z A. Maximum power point tracking using fractional open circuit voltage for solar powered wireless sensor nodes[J]. IET WSS, 2018, 8(5): 215-221.
3. Lucia B, Ransford B. A simpler, safer programming and execution model for intermittent systems[C]. ACM PLDI, 2015: 575-585.
4. e-peas semiconductors. AEM10941 Datasheet: Solar Energy Harvester Ultra-Low Power[J]. Rev 4.2, 2023.
