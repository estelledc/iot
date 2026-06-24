# LoRaWAN Class A/B/C工作模式对比分析
> **难度**：🟢 初级 | **领域**：LoRaWAN协议 | **阅读时间**：约 18 分钟

## 引言

想象一个快递驿站的三种取件方式: A方式是你每次寄出包裹后,驿站有两次机会给你回复,其余时间你不在驿站; B方式是驿站每天固定几个时间段开门,你按时去取; C方式是你一直站在驿站门口等着,随时能收到快递。这三种方式分别对应LoRaWAN的Class A、B、C三种工作模式——它们在功耗和下行通信延迟之间做出了不同的权衡。

本文将详细对比三种Class的工作机制、功耗特征和适用场景。

## 1. LoRaWAN网络架构概览

### 1.1 星型拓扑

```
[终端设备] ---LoRa无线--- [网关] ---IP网络--- [网络服务器] --- [应用服务器]
[终端设备] ---LoRa无线--- [网关] ---|
[终端设备] ---LoRa无线--- [网关] ---|
```

终端设备是传感器/执行器(电池供电), 网关透明转发LoRa与IP数据, 网络服务器管理网络和MAC调度, 应用服务器处理业务数据。

### 1.2 上行与下行

上行(终端到服务器)很简单——设备想发就发。下行(服务器到终端)才是Class区别的核心: 设备什么时候"听"决定了什么时候能收到下行数据。

### 1.3 为什么需要不同Class

IoT设备需求差异巨大: 温度传感器只需上报,电池要用10年; 路灯控制器需要接收命令但可容忍秒级延迟; 紧急报警器需要立即收到确认。三种Class为不同需求而设计。

## 2. Class A: 最低功耗

### 2.1 工作原理

Class A是基础模式,所有设备必须支持。核心规则: 设备只在主动发送上行后才打开接收窗口。

```
  睡眠    TX(上行)  等1s  RX1  等1s  RX2    睡眠(直到下次上行)
|--------|========|-----|====|-----|====|------------------------>
```

### 2.2 接收窗口时序

**RX1**: 上行结束后1秒开启, 使用与上行相同信道(或配置的对应信道), 持续约500ms。

**RX2**: 上行结束后2秒开启, 使用固定预配置信道和数据速率(通常SF12/125kHz), 作为RX1的备份。

```
接收逻辑:
if RX1收到有效下行帧:
    跳过RX2, 处理数据
elif RX1超时:
    打开RX2
    if RX2收到:
        处理数据
    else:
        本次无下行, 回到睡眠
```

### 2.3 功耗分析

```
典型电流消耗:
- TX: 120mA * 100-2000ms (取决于SF)
- RX窗口: 15mA * 500ms (每个)
- 深度睡眠: 1-2uA

示例(每小时发1条, SF9, 50字节):
- TX: 120mA * 247ms = 0.008 mAh
- RX1+RX2: 15mA * 1000ms = 0.004 mAh
- Sleep: 0.001mA * 3597s = 1.0 mAh
- 合计约 1.01 mAh/h

优化后的设备(待机0.5uA)可达5-10年电池寿命
```

### 2.4 Class A的局限

最大问题是下行延迟不可控。服务器想发命令必须等设备下次上行。如果设备每小时上行一次,最坏等待1小时。

## 3. Class B: 有界延迟

### 3.1 工作原理

Class B在Class A基础上增加定期接收窗口(Ping Slot),通过与网关时间同步实现可预测的下行延迟。

```
  Beacon    Ping  Ping  Ping    Beacon    Ping  Ping
  接收      Slot  Slot  Slot    接收      Slot  Slot
|==|--------|==|--|==|--|==|----|==|--------|==|--|==|---->
 ^           (每128秒一个Beacon周期)         ^
```

### 3.2 信标机制

网关每128秒广播信标帧用于时间同步。所有Class B设备接收信标校准时钟。如果连续多个信标丢失,设备退回Class A。

### 3.3 Ping Slot配置

信标间128秒被划分为多个Ping Slot:

| Ping周期 | Slot数/128s | 最大延迟 | 功耗级别 |
|----------|------------|---------|---------|
| 128s | 1 | 128s | 最低 |
| 32s | 4 | 32s | 中低 |
| 16s | 8 | 16s | 中 |
| 4s | 32 | 4s | 高 |
| 1s | 128 | 1s | 最高 |

每个设备的Ping Slot时间基于设备地址伪随机偏移,避免所有设备同时唤醒。

### 3.4 功耗

```
相比Class A额外增加:
- 信标接收: 15mA * 30ms, 每128秒一次
- Ping Slot: 15mA * 30ms, 每PingPeriod一次

示例(Ping周期32s):
额外平均电流约 17uA
对比Class A待机1-2uA, 电池寿命从10年降至2-5年
```

### 3.5 实际困难

Class B部署较少: 需要网关精确信标广播和GPS/PTP时间同步; 设备侧复杂时间管理; 大多场景用Class A轮询或Class C替代。

## 4. Class C: 最低延迟

### 4.1 工作原理

Class C设备不发送时始终保持接收器开启:

```
  RX(持续接收)   TX   RX1  RX2    RX(持续接收)
|================|===|====|====|========================>
```

服务器可以随时发送下行消息,延迟接近实时。

### 4.2 功耗

```
接收器常开: 10-15mA持续消耗
2400mAh电池: 2400/12 = 200小时 = 约8天
结论: Class C不适合电池供电,必须外部供电
```

### 4.3 适用设备

市电供电设备(智能插座/电表), 太阳能+储能设备, 需要立即响应的执行器, LoRaWAN网关本身, 紧急警报系统。

## 5. 三种Class综合对比

### 5.1 核心指标

| 指标 | Class A | Class B | Class C |
|------|---------|---------|---------|
| 下行延迟 | 不确定 | 有界(PingPeriod) | 接近实时 |
| 平均功耗 | 1-5uA | 10-20uA | 10-15mA |
| 电池寿命 | 5-10年 | 2-5年 | 不适合电池 |
| 实现复杂度 | 低 | 高 | 低 |
| 必须支持 | 是 | 可选 | 可选 |

### 5.2 下行延迟对比

```
Class A (每15分钟上行):
  最好: 1-2秒(刚发完上行)
  最坏: 15分钟(刚错过上行)
  平均: ~7.5分钟

Class B (Ping周期32秒):
  最好: 几百毫秒
  最坏: 32秒
  平均: ~16秒

Class C:
  最好/最坏: <1-2秒
```

## 6. 应用场景映射

### 6.1 Class A典型应用

**环境传感器**: 温湿度每30分钟上报, 不需要接收命令, 电池5年以上。

**资产追踪器**: GPS定位器周期上报位置, 小锂电池长续航, 偶尔接收配置更新。

**水表/电表**: 每小时或每天上报读数, 10年电池硬性要求。

### 6.2 Class B典型应用

**智能路灯**: 接收开关/调光命令, 可容忍秒级延迟, 太阳能供电但冬季电量有限。

**工业阀门**: 远程开/关阀门, 30秒内响应, 布线困难的位置。

**农业灌溉**: 按传感器触发灌溉, 太阳能供电, 分钟级延迟可接受。

### 6.3 Class C典型应用

**LoRaWAN中继/网关**: 必须随时转发下行, 有市电供电。

**紧急报警确认**: 报警后必须立即收到确认, 市电供电消防系统。

**电子显示屏**: 需要随时更新显示内容, 市电供电。

## 7. Class切换

### 7.1 动态切换

LoRaWAN允许运行时切换Class:

```
设备启动 -> Class A(发送Join) -> 入网成功 -> 按需切换B/C
Class B丢失信标 -> 自动退回Class A
应用层可根据电量/需求动态切换
```

### 7.2 混合策略

常见模式:
- 平时Class A, OTA升级时临时切Class C, 完成后切回
- 太阳能设备白天Class B/C, 夜晚切回Class A
- 检测到异常后切Class C等待指令

## 8. 实际部署考虑

### 8.1 选择决策流程

```
需要接收下行命令?
|-- 否 --> Class A
|-- 是 --> 可接受的最大延迟?
              |-- 分钟级 --> Class A(增加上行频率)
              |-- 秒级 --> 有稳定供电?
              |              |-- 否 --> Class B
              |              |-- 是 --> Class C
              |-- 亚秒级 --> Class C(需持续供电)
```

### 8.2 典型部署分布

约90%设备Class A, 约5%设备Class C(市电), 约5%设备Class B。Class B使用率低因为实现复杂,很多场景增加Class A上行频率也能满足需求。

### 8.3 下行容量限制

无论哪种Class,下行容量远小于上行: 网关同一时刻只能在一个信道发送; 下行占用网关接收能力(半双工); EU868下行有占空比限制。设计时应最小化下行需求。

### 8.4 固件更新(FUOTA)

远程固件更新是最大下行场景: Class A极慢(每次上行收一个分片), Class B用多播Ping Slot批量推送, Class C最快(连续接收分片)。实践中设备临时切到Class C完成FUOTA再切回。

## 9. LoRaWAN 1.1改进

### 9.1 Class B增强

信标帧加密保护, Ping Slot随机化改进, 多播Class B支持, 设备可属于多个多播组。

### 9.2 Rejoin机制

设备定期发送Rejoin保持连接活跃, 无需完整重新入网, 支持漫游网络切换, 减少会话超时问题。

## 10. 代码示例

### 10.1 LoRaMac-node配置

```c
// Class A(默认)
MibRequestConfirm_t mibReq;
mibReq.Type = MIB_DEVICE_CLASS;
mibReq.Param.Class = CLASS_A;
LoRaMacMibSetRequestConfirm(&mibReq);

// 切换到Class C
mibReq.Param.Class = CLASS_C;
LoRaMacMibSetRequestConfirm(&mibReq);
// 此后接收器常开
```

### 10.2 下行消息处理

```c
void processDownlink(uint8_t *data, uint8_t len) {
    if (len == 0) return;
    uint8_t cmd = data[0];
    switch(cmd) {
        case CMD_SET_INTERVAL:
            report_interval = (data[1] << 8) | data[2];
            saveConfig();
            break;
        case CMD_REBOOT:
            NVIC_SystemReset();
            break;
        case CMD_SWITCH_CLASS:
            switchToClass(data[1]); // 0=A, 1=B, 2=C
            break;
    }
}
```

### 10.3 Arduino LMIC示例

```c
// 启用Class C
LMIC_setClassC(1);

void onEvent(ev_t ev) {
    switch(ev) {
        case EV_TXCOMPLETE:
            if (LMIC.txrxFlags & TXRX_DNW1)
                processDownlink(LMIC.frame, LMIC.dataLen); // RX1
            if (LMIC.txrxFlags & TXRX_DNW2)
                processDownlink(LMIC.frame, LMIC.dataLen); // RX2
            break;
        case EV_RXCOMPLETE:
            // Class C非TX关联的下行
            processDownlink(LMIC.frame, LMIC.dataLen);
            break;
    }
}
```

## 总结

LoRaWAN的三种Class模式是功耗与下行延迟的权衡: Class A最省电但下行延迟不确定, Class C实时但必须外部供电, Class B折中但实现复杂。

实际部署中绝大多数传感器用Class A足够。建议从Class A开始,只在确认延迟要求无法通过增加上行频率满足时再升级到B/C。保持简单是长期运维的关键。

## 参考文献

1. LoRa Alliance, "LoRaWAN Specification v1.0.4", 2020
2. LoRa Alliance, "LoRaWAN Specification v1.1 Revision B", 2022
3. Adelantado, F. et al., "Understanding the Limits of LoRaWAN", IEEE Communications Magazine, 2017
4. LoRa Alliance, "LoRaWAN FUOTA v1.0", 2019
5. Sornin, N. et al., "LoRaWAN Specification v1.0", LoRa Alliance, 2015
