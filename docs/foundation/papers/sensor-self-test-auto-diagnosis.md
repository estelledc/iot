# 传感器自测试与自动诊断功能实现
> **难度**：🟡 中级 | **领域**：传感器可靠性 | **阅读时间**：约 20 分钟

## 引言

去医院体检，医生会做一系列检查——量血压、查心率、验血——每项检查都在确认身体某个系统的功能是否正常。传感器也需要"体检"：在无人值守的 IoT 节点中，如果传感器悄悄失效了，系统可能还在"正常"输出数据，但实际上全是垃圾值。自测试（Self-Test）和自动诊断就是让设备定期给自己做体检，发现异常及时上报，而不是等到有人发现数据不对才追悔莫及。

## 1 为什么自测试至关重要

### 1.1 无人值守场景的挑战

IoT 传感器节点通常部署在偏远或危险区域：

- 人员无法定期巡检
- 失效可能长期不被发现
- 基于错误数据的决策可能导致严重后果

典型场景：水库水位传感器失效后持续上报"水位正常"，洪水来了毫无预警。

### 1.2 安全关键应用的要求

在功能安全标准（IEC 61508、ISO 26262）中，诊断覆盖率（Diagnostic Coverage, DC）是衡量安全完整性的关键指标：

| SIL 等级 | 要求的诊断覆盖率 |
|----------|-----------------|
| SIL 1 | 60-90% |
| SIL 2 | 90-99% |
| SIL 3 | >=99% |
| SIL 4 | >=99.9% |

## 2 内建自测试（BIST）

### 2.1 MEMS 加速度计的静电驱动自测试

MEMS 加速度计内部有可动的微机械结构。自测试时，在检测电极上施加已知电压，产生静电引力使质量块位移，等效于施加了一个已知加速度：

- 施加自测试电压 -> 质量块位移 -> 输出变化量与标称值比较
- 偏差在允许范围内 -> 传感结构正常
- 偏差超限 -> 传感器可能损坏或参数漂移

```
// ADXL345 自测试流程
// 1. 读取当前输出(自测试关闭)
// 2. 使能自测试位
// 3. 等待稳定(约4ms)
// 4. 读取输出(自测试开启)
// 5. 计算差值并与规格比较
```

### 2.2 气体传感器的加热器自测试

电化学气体传感器通常内置加热器：

- 加热器电阻变化 -> 反映加热器是否正常
- 加热器升温后基线变化 -> 反映敏感电极是否响应
- 加热器断路 -> 传感器彻底失效

### 2.3 BIST 的局限性

- 只能检测到自测试激励能触及的故障
- 无法发现信号调理电路的某些故障
- 诊断覆盖率通常 60-80%，需配合其他方法提升

## 3 通信链路测试

### 3.1 WHO_AM_I 寄存器检查

大多数数字传感器都有 WHO_AM_I 寄存器，存放固定值：

```c
// I2C通信链路自测试
#define BME280_WHO_AM_I_VAL  0x60
#define BME280_WHO_AM_I_ADDR 0xD0

bool bme280_comm_test(i2c_inst_t *i2c, uint8_t addr) {
    uint8_t reg = BME280_WHO_AM_I_ADDR;
    uint8_t val = 0;
    int ret = i2c_write_timeout_us(i2c, addr, &reg, 1, true, 1000);
    if (ret < 0) return false;
    ret = i2c_read_timeout_us(i2c, addr, &val, 1, false, 1000);
    if (ret < 0) return false;
    return (val == BME280_WHO_AM_I_VAL);
}
```

### 3.2 通信错误统计

持续监测通信质量：

```c
typedef struct {
    uint32_t total_transactions;
    uint32_t i2c_nack_count;
    uint32_t i2c_crc_error_count;
    uint32_t i2c_timeout_count;
} comm_stats_t;

bool comm_health_ok(comm_stats_t *stats) {
    float error_rate = (float)(stats->i2c_nack_count +
                               stats->i2c_crc_error_count +
                               stats->i2c_timeout_count) /
                               stats->total_transactions;
    return error_rate < 0.01f;
}
```

## 4 量程合理性检查

### 4.1 物理边界检测

传感器输出应在物理上可能的范围内：

- 室内温度传感器：-40 度C 到 +85 度C
- 气压传感器：300hPa 到 1100hPa
- 加速度计（静态设备）：-0.5g 到 +1.5g

```c
typedef struct {
    int16_t min_valid;
    int16_t max_valid;
} range_check_t;

bool range_plausibility_check(int16_t value, const range_check_t *range) {
    return (value >= range->min_valid) && (value <= range->max_valid);
}

// 温度: -40度C ~ 85度C -> -400 ~ 850
const range_check_t temp_range = {-400, 850};
```

### 4.2 ADC 饱和检测

```c
#define ADC_NEAR_FULL  4090
#define ADC_NEAR_ZERO    5

bool adc_saturation_check(uint16_t adc_val) {
    if (adc_val >= ADC_NEAR_FULL || adc_val <= ADC_NEAR_ZERO) {
        return true;  // 可能饱和
    }
    return false;
}
```

## 5 变化率检查

### 5.1 检测卡死故障

传感器信号长时间不变可能意味着卡死（stuck-at）故障：

```c
#define STUCK_AT_COUNT_THRESHOLD  10

typedef struct {
    int16_t last_value;
    int16_t same_count;
} rate_check_t;

bool stuck_at_fault_detect(int16_t current, rate_check_t *ctx) {
    if (current == ctx->last_value) {
        ctx->same_count++;
    } else {
        ctx->same_count = 0;
    }
    ctx->last_value = current;
    return ctx->same_count >= STUCK_AT_COUNT_THRESHOLD;
}
```

### 5.2 变化率合理性

物理量的变化速率有上限——温度变化通常 < 1 度C/s，气压变化通常 < 1 hPa/min。

```c
#define TEMP_MAX_RATE_PER_SEC  20  // 2.0度C/s (0.1度C单位)

bool rate_of_change_ok(int16_t current, int16_t previous,
                       uint32_t dt_ms) {
    if (dt_ms == 0) return true;
    int16_t delta = abs(current - previous);
    int16_t max_delta = (int16_t)((int32_t)TEMP_MAX_RATE_PER_SEC * dt_ms / 1000);
    return delta <= max_delta;
}
```

## 6 冗余传感器诊断

### 6.1 双传感器比较

同一位置安装两个相同传感器，比较输出：

```c
typedef struct {
    int16_t sensor_a;
    int16_t sensor_b;
    int16_t max_divergence;
} dual_sensor_t;

typedef enum {
    DUAL_AGREE,
    DUAL_DIVERGE,
} dual_check_result_t;

dual_check_result_t dual_sensor_check(dual_sensor_t *ds) {
    int16_t diff = abs(ds->sensor_a - ds->sensor_b);
    if (diff <= ds->max_divergence) return DUAL_AGREE;
    return DUAL_DIVERGE;
}
```

### 6.2 异构冗余

使用不同原理的传感器测量同一物理量（NTC + PN 结温度传感器），共因故障概率更低。

## 7 诊断覆盖率

### 7.1 故障模式与诊断方法映射

| 故障模式 | 诊断方法 | 覆盖率估算 |
|----------|----------|-----------|
| 传感元件失效 | BIST | 70% |
| 通信链路断开 | WHO_AM_I | 95% |
| 输出卡死 | 变化率检查 | 90% |
| 输出超量程 | 量程检查 | 80% |
| 精度漂移 | 冗余比较 | 60% |
| 组合诊断 | 以上全部 | ~95% |

单一方法难以达到高覆盖率，需要组合使用。

## 8 RTOS 中的自测试任务架构

### 8.1 周期性自测试任务

在 RTOS 中创建低优先级周期任务，定期执行自测试：

```c
void self_test_task(void *pvParameters) {
    const TickType_t period = pdMS_TO_TICKS(60000);
    TickType_t last_wake = xTaskGetTickCount();

    for (;;) {
        vTaskDelayUntil(&last_wake, period);
        health_status_t status = {0};

        status.comm_ok = bme280_comm_test(i2c0, BME280_ADDR);
        status.range_ok = range_plausibility_check(current_temp, &temp_range);
        status.rate_ok = rate_of_change_ok(current_temp, prev_temp, 60000);

        xSemaphoreTake(health_mutex, portMAX_DELAY);
        g_health_status = status;
        xSemaphoreGive(health_mutex);

        if (!status.comm_ok || !status.range_ok || !status.rate_ok) {
            send_alert(&status);
        }
    }
}
```

### 8.2 测试时序安排

| 测试项 | 频率 | 理由 |
|--------|------|------|
| 通信链路 | 每次采样 | 开销极小 |
| 量程检查 | 每次采样 | 开销极小 |
| 变化率检查 | 每次采样 | 需连续数据 |
| BIST | 上电 + 周期(1h) | 影响正常测量 |
| 冗余比较 | 周期(10min) | 需等待数据积累 |

## 9 诊断报告与告警

### 9.1 诊断码定义

```c
typedef enum {
    DIAG_OK              = 0x00,
    DIAG_COMM_FAIL       = 0x01,
    DIAG_WHO_AM_I_FAIL   = 0x02,
    DIAG_RANGE_FAIL      = 0x10,
    DIAG_STUCK_AT        = 0x20,
    DIAG_RATE_FAIL       = 0x30,
    DIAG_BIST_FAIL       = 0x40,
    DIAG_REDUNDANCY_FAIL = 0x50,
} diag_code_t;
```

### 9.2 健康状态寄存器

```c
typedef struct __attribute__((packed)) {
    uint8_t  diag_code;
    uint8_t  sensor_id;
    uint16_t raw_value;
    uint32_t timestamp;
    uint16_t error_count;
} health_register_t;
```

### 9.3 告警策略

```
单次异常    -> 记录日志，不告警
连续2次异常 -> 低优先级告警(状态位)
连续5次异常 -> 高优先级告警(推送通知)
持续1小时   -> 降级运行或停机
```

## 10 实战示例

### 10.1 ADXL345 自测试

```c
#define ADXL345_ADDR        0x53
#define ADXL345_DATA_FORMAT 0x31

bool adxl345_self_test(i2c_inst_t *i2c) {
    // Step 1: 正常模式读取X轴(取64次平均)
    int16_t normal_x = adxl345_read_avg(i2c, AXIS_X, 64);

    // Step 2: 使能自测试位(DATA_FORMAT bit7)
    uint8_t fmt = 0;
    i2c_reg_read(i2c, ADXL345_ADDR, ADXL345_DATA_FORMAT, &fmt, 1);
    fmt |= 0x80;
    i2c_reg_write(i2c, ADXL345_ADDR, ADXL345_DATA_FORMAT, &fmt, 1);

    // Step 3: 等待稳定
    sleep_ms(4);

    // Step 4: 自测试模式读取X轴
    int16_t test_x = adxl345_read_avg(i2c, AXIS_X, 64);

    // Step 5: 恢复正常模式
    fmt &= ~0x80;
    i2c_reg_write(i2c, ADXL345_ADDR, ADXL345_DATA_FORMAT, &fmt, 1);

    // Step 6: 计算偏差并与规格比较
    int16_t delta = test_x - normal_x;
    return (delta > -105 && delta < 105);
}
```

### 10.2 BME280 状态寄存器监测

BME280 的 status 寄存器（0xF3）包含两个关键位：bit0 为 nm_rdy，bit1 为 measuring。

```c
typedef struct {
    bool measuring;
    bool new_data_ready;
} bme280_status_t;

bme280_status_t bme280_read_status(i2c_inst_t *i2c, uint8_t addr) {
    uint8_t status = 0;
    i2c_reg_read(i2c, addr, 0xF3, &status, 1);
    bme280_status_t s;
    s.measuring      = (status & 0x02) != 0;
    s.new_data_ready = (status & 0x01) == 0;
    return s;
}
```

## 11 故障检测后的优雅降级

| 故障等级 | 策略 | 示例 |
|----------|------|------|
| 轻微(偶发) | 标记可疑，继续运行 | 单次通信超时 |
| 中等(持续) | 降级运行，降低采样率 | 冗余校验持续偏差 |
| 严重(功能失效) | 停止使用该传感器 | BIST 失败 |
| 致命(安全隐患) | 系统安全停机 | 安全关键传感器失效 |

每个测量值附带质量标记：

```c
typedef enum {
    QUALITY_GOOD     = 0,
    QUALITY_ESTIMATED = 1,
    QUALITY_DEGRADED  = 2,
    QUALITY_INVALID   = 3
} data_quality_t;

typedef struct {
    int16_t        value;
    data_quality_t quality;
    uint32_t       timestamp;
} measurement_t;
```

## 总结

传感器自测试和自动诊断是 IoT 可靠性的核心保障：

- BIST 是传感器的"内置体检"，覆盖传感元件故障
- 通信链路测试用 WHO_AM_I 确认链路完整性
- 量程和变化率检查几乎零开销就能捕获多数异常
- 冗余比较是唯一能有效检测精度漂移的方法
- 组合使用多种方法可将诊断覆盖率提升至 95% 以上
- 故障后的优雅降级比直接崩溃好得多

诊断不是可选项——在无人值守场景下，没有自诊断能力的传感器等于"闭着眼睛猜数据"。

## 参考文献

1. IEC 61508, "Functional safety of electrical/electronic/programmable electronic safety-related systems", 2010.
2. Analog Devices, "ADXL345 Datasheet: Self-Test Operation", Rev.C, 2017.
3. Bosch Sensortec, "BME280 Datasheet: Status Register Description", BST-BME280-DS001, 2022.
4. NASA, "Sensor Health Monitoring and Fault Detection for Autonomous Systems", NASA/TM-2019-220298, 2019.
5. ISO 26262-5, "Road vehicles - Functional safety - Product development at hardware level", 2018.
