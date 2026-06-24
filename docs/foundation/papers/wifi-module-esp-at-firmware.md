# WiFi模组ESP AT固件指令集与主控接口
> **难度**：🟢 初级 | **领域**：WiFi模组应用 | **阅读时间**：约 18 分钟

## 引言

想象你入住一家外国酒店，你不会说当地语言，但前台有一位翻译--你只需要用标准句式说出需求，翻译就会帮你完成入住、点餐、叫车。ESP-AT固件就是IoT设备与WiFi世界之间的那位翻译:主控MCU不需要懂TCP/IP协议栈、不需要跑WiFi驱动，只需要通过串口发送AT指令，ESP模组就会帮你连接WiFi、建立TCP连接、收发数据。

## 1. AT指令概念

### 1.1 Hayes指令集的遗产

AT指令的历史可追溯到1980年代:

- **AT**: Attention的缩写，意为"请注意"
- 最早由Hayes公司为调制解调器(Modem)设计
- 所有指令以"AT"开头，以回车换行(\r\n)结尾

```
基本格式:
  发送: AT+<命令>=<参数>\r\n
  回复: +<命令>:<数据>\r\n
        OK\r\n   或   ERROR\r\n
```

### 1.2 为什么IoT还在用AT指令

| 优势 | 说明 |
|------|------|
| 简单 | 任何有UART的MCU都能用 |
| 低资源 | 主控不需要WiFi协议栈 |
| 标准化 | 统一接口，换模组只换指令表 |
| 可调试 | 串口助手直接输入指令测试 |
| 可靠 | 请求-响应模式，结果明确 |

指令的四种变体: AT+CMD?(查询当前值)、AT+CMD=?(查询可选值)、AT+CMD=x(设置值)、AT+CMD(执行命令)。

## 2. ESP-AT固件概述

### 2.1 什么是ESP-AT

ESP-AT是乐鑫官方提供的WiFi/BLE模组固件，预编译烧录即可使用，支持WiFi Station+SoftAP，内置LwIP协议栈，支持TLS/SSL、MQTT、HTTP。

### 2.2 固件版本与芯片对应

| 固件版本 | 芯片 | WiFi | BLE | 备注 |
|----------|------|------|-----|------|
| ESP32-AT | ESP32 | 2.4G | 4.2 | 经典方案 |
| ESP32-C3-AT | ESP32-C3 | 2.4G | 5.0 | RISC-V，低功耗 |
| ESP32-S2-AT | ESP32-S2 | 2.4G | 无 | USB-OTG支持 |
| ESP32-C6-AT | ESP32-C6 | 2.4G+6 | 5.0 | WiFi6 |

### 2.3 烧录固件

```bash
# 擦除flash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# 烧录固件
esptool.py --chip esp32 --port /dev/ttyUSB0 \
  --baud 460800 write_flash \
  0x10000 bootloader.bin \
  0x8000 partitions.bin \
  0x24000 esp-at.bin

# 首次启动应看到: ready / AT version:2.x.x
```

## 3. UART接口连接

### 3.1 硬件接线

```
主控MCU (STM32)            ESP32模组
  TX (PA9)  ------------>  RX (GPIO16)
  RX (PA10) <------------  TX (GPIO17)
  GND       ------------- GND
  3.3V      ------------- 3.3V

注意: TX/RX交叉连接, 必须共地
      ESP32峰值电流500mA, MCU的3.3V可能不够
```

### 3.2 波特率配置

默认115200，支持1200-5760000。修改方式:

```
AT+UART_CUR=921600,8,1,0,0  --> 本次生效(重启恢复)
AT+UART_DEF=921600,8,1,0,0  --> 永久保存(重启不恢复)
```

```c
// STM32 UART初始化
void MX_USART1_UART_Init(void)
{
    huart1.Instance = USART1;
    huart1.Init.BaudRate = 115200;
    huart1.Init.WordLength = UART_WORDLENGTH_8B;
    huart1.Init.StopBits = UART_STOPBITS_1;
    huart1.Init.Parity = UART_PARITY_NONE;
    huart1.Init.Mode = UART_MODE_TX_RX;
    huart1.Init.HWFlowCtl = UART_HWCONTROL_NONE;
    HAL_UART_Init(&huart1);
}
```

## 4. 基础AT指令

```
AT          --> 测试AT启动，回复OK
AT+RST      --> 重启模组
AT+GMR      --> 查询固件版本信息
AT+RESTORE  --> 恢复出厂设置
```

指令变体示例:

```
> AT+CWMODE?       // 查询当前WiFi模式
+CWMODE:1
OK

> AT+CWMODE=?      // 查询可选值
+CWMODE:(1-3)
OK
// 1=Station, 2=SoftAP, 3=Station+SoftAP
```

## 5. WiFi指令

### 5.1 模式设置与扫描连接

```
AT+CWMODE=1    --> Station模式(连路由器)
AT+CWMODE=2    --> SoftAP模式(做热点)
AT+CWMODE=3    --> Station+SoftAP(混合)

> AT+CWLAP                         // 扫描附近WiFi
+CWLAP:(0,"MyWiFi",-45,"aa:bb:cc:dd:ee:ff",1,0,0)

> AT+CWJAP="MyWiFi","mypassword"   // 连接WiFi
WIFI CONNECTED
WIFI GOT IP
OK

> AT+CIFSR                         // 查询IP
+CIFSR:STAIP,"192.168.1.100"
OK
```

### 5.2 自动重连

```
AT+CWAUTOCONN=1   // 开启自动重连
// AT+CWJAP默认保存WiFi信息，最多5个AP
```

## 6. TCP/IP指令

### 6.1 建立连接与收发数据

```
> AT+CIPSTART="TCP","192.168.1.200",8080
CONNECT
OK

> AT+CIPSEND=12                  // 指定发送长度
OK
> Hello World!
SEND OK

// 接收数据(模组主动上报):
+IPD,0,5:hello
// 格式: +IPD,<link_id>,<len>:<data>

> AT+CIPCLOSE=0
CLOSED
OK
```

### 6.2 多连接模式

```
> AT+CIPMUX=1                    // 开启多连接(最多5个)
OK
> AT+CIPSTART=0,"TCP","192.168.1.200",8080   // 指定link_id
0,CONNECT
OK
> AT+CIPSEND=0,5                // 指定link_id发送
OK
```

## 7. MQTT AT指令

```
// 1. 配置MQTT用户属性
AT+MQTTUSERCFG=0,1,"client_id","user","pass",0,0,""

// 2. 连接MQTT Broker
AT+MQTTCONN=0,"broker.emqx.io",1883,0
+MQTTCONNECTED:0,1

// 3. 订阅主题
AT+MQTTSUB=0,"sensor/temp",1,0

// 4. 发布消息
AT+MQTTPUB=0,"sensor/temp","25.6",1,0

// 5. 接收消息(自动上报)
+MQTTSUBRECV:0,"sensor/temp",4:25.6

// 6. 断开
AT+MQTTDISCONN=0
```

## 8. HTTP AT指令

```
// HTTP GET
AT+HTTPCLIENT=1,0,"http://api.example.com/data",,,0
+HTTPCLIENT:0,200
+HTTPCLIENT:1,{"temp":25.6,"humidity":60}

// HTTP POST
AT+HTTPCLIENT=3,0,"http://api.example.com/update",,"Content-Type: application/json",0,"{\"temp\":25.6}"
```

## 9. AT指令响应解析

### 9.1 主控代码解析框架

```c
#define AT_BUF_SIZE 512

typedef enum { AT_IDLE, AT_WAIT_OK, AT_TIMEOUT } AT_State_t;

static char at_rx_buf[AT_BUF_SIZE];
static uint16_t at_rx_len = 0;

// 发送AT指令并等待响应
AT_State_t at_send_cmd(const char *cmd, uint32_t timeout_ms)
{
    at_rx_len = 0;
    HAL_UART_Transmit(&huart1, (uint8_t *)cmd, strlen(cmd), 100);
    HAL_UART_Transmit(&huart1, (uint8_t *)"\r\n", 2, 100);

    uint32_t start = HAL_GetTick();
    while (HAL_GetTick() - start < timeout_ms) {
        if (strstr(at_rx_buf, "OK")) return AT_WAIT_OK;
        if (strstr(at_rx_buf, "ERROR")) return AT_TIMEOUT;
        HAL_Delay(10);
    }
    return AT_TIMEOUT;
}
```

### 9.2 解析+IPD数据

```c
// 格式: +IPD,<link_id>,<len>:<data>
int at_parse_ipd(const char *buf, uint8_t *link_id,
                 uint16_t *data_len, uint8_t *data_out)
{
    const char *p = strstr(buf, "+IPD,");
    if (!p) return -1;
    p += 5;
    *link_id = atoi(p);
    p = strchr(p, ',');  if (!p) return -1;  p++;
    *data_len = atoi(p);
    p = strchr(p, ':');  if (!p) return -1;  p++;
    memcpy(data_out, p, *data_len);
    return 0;
}
```

## 10. 透传模式与命令模式

| 特性 | 命令模式(Normal) | 透传模式(Passthrough) |
|------|------------------|----------------------|
| 数据格式 | AT指令 | 原始数据流 |
| 延迟 | 较高(需封装) | 最低(直通) |
| 适合场景 | 控制命令 | 大量数据传输 |
| 退出透传 | -- | 发送"+++"(1秒内) |

```
// 进入透传模式
AT+CIPMODE=1
OK
AT+CIPSEND
>   (此后串口数据直接发送到服务器)

// 退出透传模式
+++   (前后1秒内不能有其他数据)
```

透传注意事项: 透传模式下无法发AT指令; 必须先建连接再进透传; 断线后透传自动退出。

## 11. 固件更新

```
// OTA升级
AT+CIUPDATE
+CIUPDATE:1   // 找到服务器
+CIUPDATE:4   // 开始下载
+CIUPDATE:5   // 下载完成
OK

// 主控控制OTA:
void esp_ota_update(void)
{
    if (at_send_cmd("AT+CWJAP?", 2000) != AT_WAIT_OK) return;
    if (at_send_cmd("AT+CIUPDATE", 120000) == AT_WAIT_OK) {
        HAL_Delay(3000); // 等待重启
    }
}
```

## 12. ESP-AT vs ESP-IDF开发

| 特性 | ESP-AT固件 | ESP-IDF原生开发 |
|------|-----------|----------------|
| 开发难度 | 低 | 中高 |
| 主控MCU | 需要(STM32等) | 不需要 |
| 灵活性 | 受限于AT指令集 | 完全自由 |
| 实时性 | 串口延迟(ms级) | 直接调用(us级) |
| 功耗控制 | 受限 | 精细控制 |
| 适合场景 | 快速原型、简单应用 | 复杂应用、量产优化 |

使用AT固件的场景: MCU已有成熟代码只加WiFi、项目时间紧、WiFi功能简单、团队无ESP-IDF经验。

迁移到自定义固件的场景: 延迟无法满足需求、ESP32需运行复杂逻辑、需精细功耗控制、量产降本去掉主控MCU。

```
决策: WiFi简单? --是--> 有ESP-IDF经验? --否--> AT固件
                              --是--> 时间紧? --是--> AT固件
                                               --否--> ESP-IDF
        --否--> 需极低延迟? --是--> ESP-IDF
                              --否--> AT可尝试
```

## 13. 与STM32主控集成实例

### 13.1 完整初始化流程

```c
void esp_at_init(void)
{
    // 硬件复位ESP模组
    HAL_GPIO_WritePin(ESP_EN_GPIO_Port, ESP_EN_Pin, GPIO_PIN_RESET);
    HAL_Delay(100);
    HAL_GPIO_WritePin(ESP_EN_GPIO_Port, ESP_EN_Pin, GPIO_PIN_SET);
    HAL_Delay(2000);

    at_send_cmd("AT", 1000);          // 测试通信
    at_send_cmd("ATE0", 1000);        // 关闭回显
    at_send_cmd("AT+CWMODE=1", 1000); // Station模式
    at_send_cmd("AT+CIPMUX=0", 1000); // 单连接
    at_send_cmd("AT+CWJAP=\"MySSID\",\"MyPassword\"", 15000);
    at_send_cmd("AT+CIFSR", 2000);    // 查询IP
}
```

### 13.2 数据上报函数

```c
int esp_report_data(float temperature, float humidity)
{
    char cmd[64], data[64];

    snprintf(cmd, sizeof(cmd),
             "AT+CIPSTART=\"TCP\",\"%s\",%d", SERVER_IP, SERVER_PORT);
    if (at_send_cmd(cmd, 5000) != AT_WAIT_OK) return -1;

    int len = snprintf(data, sizeof(data),
                       "{\"temp\":%.1f,\"humi\":%.1f}",
                       temperature, humidity);

    snprintf(cmd, sizeof(cmd), "AT+CIPSEND=%d", len);
    if (at_send_cmd(cmd, 2000) != AT_WAIT_OK) return -2;

    HAL_UART_Transmit(&huart1, (uint8_t *)data, len, 1000);
    HAL_Delay(500);
    at_send_cmd("AT+CIPCLOSE", 2000);
    return 0;
}
```

## 14. 常见问题与排查

### 14.1 连接问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| AT无响应 | 接线错误/波特率不对 | 检查TX/RX交叉，确认115200 |
| WiFi连接失败 | 密码错误/信号弱 | 先用AT+CWLAP扫描 |
| TCP连接超时 | 服务器未启动/端口错误 | 确认服务器运行，查防火墙 |
| 数据发送失败 | 未先建立连接 | 先AT+CIPSTART再CIPSEND |

### 14.2 稳定性措施

```c
// 1. 开启自动重连
at_send_cmd("AT+CWAUTOCONN=1", 1000);

// 2. 心跳保活
void esp_keepalive(void)
{
    static uint32_t last_tick = 0;
    if (HAL_GetTick() - last_tick > 30000) { // 30秒
        if (at_send_cmd("AT", 1000) != AT_WAIT_OK) {
            esp_at_init(); // 重初始化
        }
        last_tick = HAL_GetTick();
    }
}

// 3. DMA接收 + 环形缓冲区防止溢出
#define RING_BUF_SIZE 2048
typedef struct {
    uint8_t buf[RING_BUF_SIZE];
    volatile uint16_t head, tail;
} RingBuf_t;
```

## 总结

1. **AT指令是通用语言**: 起源于Modem，适合资源有限的MCU控制WiFi
2. **四步上手**: 接线 --> 测试AT --> 连WiFi --> 建TCP连接
3. **WiFi指令最常用**: AT+CWMODE + AT+CWJAP覆盖90%场景
4. **TCP/IP指令是核心**: AT+CIPSTART/AT+CIPSEND完成数据通信
5. **MQTT/HTTP扩展协议**: AT指令集已覆盖常见应用层协议
6. **解析要规范**: 自己写解析器时注意超时和缓冲区溢出
7. **透传模式选对场景**: 持续大数据流用透传，控制命令用普通模式
8. **AT vs ESP-IDF**: 简单场景用AT，复杂需求迁移IDF
9. **稳定性靠设计**: 心跳、重连、看门狗、DMA缺一不可

## 参考文献

1. Espressif Systems. ESP-AT User Guide. https://docs.espressif.com/projects/esp-at/en/latest/
2. Espressif Systems. ESP32 AT Instruction Set. Version 2.4.0, 2024.
3. Hayes Microcomputer Products. Hayes Smartmodem User's Guide. 1985.
4. Espressif Systems. ESP-IDF Programming Guide. https://docs.espressif.com/projects/esp-idf/en/latest/
5. STMicroelectronics. STM32 HAL UART with DMA Application Note. AN4393.