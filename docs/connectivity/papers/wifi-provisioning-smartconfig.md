---
schema_version: '1.0'
id: wifi-provisioning-smartconfig
title: WiFi配网技术SmartConfig/SoftAP/BLE辅助对比
layer: 2
content_type: UNKNOWN
difficulty: beginner
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# WiFi配网技术SmartConfig/SoftAP/BLE辅助对比
> **难度**：🟢 初级 | **领域**：WiFi配网方案 | **阅读时间**：约 18 分钟

## 引言

想象你买了一个新的智能插座,拆开包装准备联网。问题来了:这个小东西既没有屏幕也没有键盘,你怎么告诉它家里WiFi的名字和密码?这就好比你要给一个聋哑人传递一个地址,你们之间需要约定一种特殊的沟通方式。WiFi配网技术要解决的就是这个"无界面设备如何获取网络凭证"的核心难题。

本文将对比三种主流配网方案:SmartConfig、SoftAP和BLE辅助配网,分析各自的工作原理、优劣势和适用场景,帮助开发者在实际项目中做出合理选择。

## 1 配网问题的本质

### 1.1 为什么配网是个难题

IoT设备通常是"无头"(headless)设备,缺少人机交互界面。要让设备连上WiFi,必须将两个关键信息传递给它:

- SSID: WiFi网络的名称
- Password: WiFi的接入密码

传递过程必须满足几个约束条件:操作简单(用户可能是技术小白)、速度够快(用户不愿等太久)、安全可靠(密码不能泄露)。不同配网方案在这三个维度上做了不同的权衡取舍。

### 1.2 配网流程的通用模型

无论采用哪种方案,配网流程都遵循一个基本模型:

```
用户操作 -> 手机App获取WiFi凭证 -> 通过某种通道传给设备 -> 设备尝试连接WiFi -> 反馈结果
```

三种方案的核心区别在于"通过某种通道传给设备"这一步采用了不同的物理层和协议。

## 2 SmartConfig(ESP-Touch)方案

### 2.1 工作原理

SmartConfig的思路非常巧妙:手机已经连在WiFi上了,那就通过WiFi本身来传递信息。具体流程如下:

1. IoT设备进入混杂模式(promiscuous mode),监听空气中所有WiFi数据帧
2. 手机App将SSID和密码编码到UDP广播或组播包的特定字段中(通常是包长度)
3. 设备通过分析捕获的数据帧长度模式,解码出WiFi凭证
4. 设备退出混杂模式,使用凭证连接WiFi

```c
// ESP32 SmartConfig 启动示例
#include "esp_smartconfig.h"
#include "esp_wifi.h"

void start_smartconfig(void) {
    // 初始化WiFi为Station模式
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();

    // 配置SmartConfig类型为ESP-Touch
    smartconfig_start_config_t cfg = SMARTCONFIG_START_CONFIG_DEFAULT();
    esp_smartconfig_set_type(SC_TYPE_ESPTOUCH);
    esp_smartconfig_start(&cfg);
    // 等待回调中接收SSID和密码
}
```

### 2.2 编码机制详解

SmartConfig的核心技巧在于利用数据帧长度编码信息。WiFi协议中,即使数据内容被加密,帧的长度信息是明文可见的。发送方通过精确控制每个UDP包的长度来编码字节数据,接收方通过统计帧长度序列来还原原始数据。

编码过程大致如下:

```
原始数据: "MyWiFi" + "password123"
     |
编码为UDP包长度序列: [67, 121, 87, 105, 70, 105, ...]
     |
接收端捕获帧长度 -> 还原数据
```

这种编码方式利用了WiFi协议的一个有趣特性:即使你看不到加密包的内容,你仍然可以看到每个包有多大。就像你听不懂外语,但可以数对方说了几个音节。

### 2.3 信道扫描策略

设备进入混杂模式后,需要在2.4GHz频段的13个信道上逐个监听,寻找SmartConfig编码信号。典型的扫描策略是在每个信道上停留100-200ms,整个扫描周期约1.3-2.6秒。如果在某个信道上检测到编码模式,就锁定该信道持续接收。

```c
// 信道扫描伪代码
for (int ch = 1; ch <= 13; ch++) {
    esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE);
    // 在当前信道监听200ms
    vTaskDelay(pdMS_TO_TICKS(200));
    if (detect_smartconfig_pattern()) {
        // 锁定信道,开始解码
        start_decoding();
        break;
    }
}
```

### 2.4 优势与局限

SmartConfig的优势在于快速便捷。用户只需在App中点击一个按钮,设备端不需要切换网络,整个过程通常在10-30秒内完成。设备端不需要额外创建AP热点,硬件成本低。

但局限性同样明显。首先是可靠性问题:在复杂的WiFi环境中(多个AP、信道拥挤),帧长度编码容易受到干扰,导致配网失败。其次是安全隐患:编码后的凭证本质上是在空气中广播的,理论上可以被同样处于混杂模式的设备截获。最后,SmartConfig只支持2.4GHz频段,因为IoT设备通常只有2.4GHz射频前端。

## 3 SoftAP方案

### 3.1 工作原理

SoftAP方案的思路更直接:既然设备没法直接加入WiFi,那就让设备自己创建一个临时WiFi热点,手机先连上这个热点,通过HTTP或WebSocket把凭证发过去。

具体流程如下:

1. IoT设备启动AP模式,创建一个开放或有预设密码的WiFi热点(如"SmartDevice_XXXX")
2. 用户手动将手机WiFi切换到这个热点
3. 手机App通过HTTP请求将家庭WiFi的SSID和密码发送给设备
4. 设备收到凭证后切换到STA模式,连接家庭WiFi
5. 手机切回家庭WiFi,确认设备上线

```c
// ESP32 SoftAP模式配置示例
#include "esp_wifi.h"
#include "esp_http_server.h"

void start_softap(void) {
    wifi_config_t ap_config = {
        .ap = {
            .ssid = "SmartDevice_001",
            .ssid_len = 0,
            .password = "setup1234",
            .max_connection = 4,
            .authmode = WIFI_AUTH_WPA2_PSK
        },
    };
    esp_wifi_set_mode(WIFI_MODE_AP);
    esp_wifi_set_config(WIFI_IF_AP, &ap_config);
    esp_wifi_start();

    // 启动HTTP服务器接收配网请求
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    httpd_handle_t server = NULL;
    httpd_start(&server, &config);
    // 注册URI处理函数接收SSID和密码
}
```

### 3.2 Web配置界面

SoftAP方案的一个独特优势是可以提供完整的Web配置界面。设备内嵌一个简单的HTTP服务器,用户通过浏览器访问设备IP(通常是192.168.4.1),看到一个配置页面,可以扫描周围WiFi列表、选择网络、输入密码,甚至配置其他设备参数。

这种方式对用户非常友好,尤其适合需要配置多个参数的场景(WiFi凭证、设备名称、服务器地址等)。

### 3.3 HTTP API设计

SoftAP模式下的配网HTTP API通常设计如下:

```
GET  /api/wifi/scan     -> 触发WiFi扫描,返回附近AP列表
GET  /api/wifi/status   -> 返回当前连接状态
POST /api/wifi/connect  -> 提交SSID和密码,设备尝试连接
GET  /api/device/info   -> 返回设备型号、固件版本等信息
```

请求和响应使用JSON格式:

```json
// POST /api/wifi/connect 请求体
{
  "ssid": "HomeWiFi",
  "password": "mypassword123",
  "bssid": "AA:BB:CC:DD:EE:FF"
}

// 响应
{
  "status": "connecting",
  "timeout": 15
}
```

### 3.4 优势与局限

SoftAP方案最大的优势是可靠性。因为通过直接的HTTP连接传输凭证,不受环境干扰,几乎不会失败。同时支持5GHz网络的凭证传输(虽然SoftAP热点本身通常是2.4GHz)。可以呈现丰富的配置界面,用户体验灵活可控。

主要问题是用户体验中的"WiFi切换"步骤。用户需要手动离开当前WiFi、连接设备热点、完成配网、再切回原WiFi。在iOS上这个过程尤其繁琐,因为系统会提示"此WiFi无互联网连接"。对于非技术用户来说,这几步操作容易引起困惑。

## 4 BLE辅助配网方案

### 4.1 工作原理

BLE辅助配网利用蓝牙低功耗(BLE)作为侧信道来传递WiFi凭证。这个方案结合了两种无线技术的优势:用BLE的便捷性完成凭证传递,用WiFi的高带宽完成实际数据通信。

具体流程如下:

1. IoT设备开启BLE广播,通告自己是一个待配网的设备
2. 手机App通过BLE扫描发现设备
3. 手机与设备建立BLE连接(可选配对加密)
4. 手机通过BLE GATT服务将WiFi凭证写入设备
5. 设备使用凭证连接WiFi
6. 设备通过BLE通知手机配网结果
7. BLE连接断开,配网完成

```c
// ESP32 BLE配网服务端示例(简化)
#include "esp_wifi.h"
#include "wifi_provisioning/manager.h"
#include "wifi_provisioning/scheme_ble.h"

void start_ble_provisioning(void) {
    wifi_prov_mgr_config_t config = {
        .scheme = wifi_prov_scheme_ble,
        .scheme_event_handler =
            WIFI_PROV_SCHEME_BLE_EVENT_HANDLER_FREE_BTDM
    };
    wifi_prov_mgr_init(config);

    // 设置BLE设备名称和服务UUID
    wifi_prov_mgr_start_provisioning(
        WIFI_PROV_SECURITY_1,  // 使用安全模式1(加密)
        "abcd1234",            // proof of possession
        "PROV_DEVICE",         // BLE设备名
        NULL                   // 服务UUID使用默认
    );
}
```

### 4.2 GATT服务设计

BLE配网使用自定义GATT服务来传递数据。典型的服务结构包含以下Characteristic:

| Characteristic | UUID | 属性 | 用途 |
|---------------|------|------|------|
| WiFi SSID | 自定义 | Write | 接收SSID |
| WiFi Password | 自定义 | Write | 接收密码 |
| WiFi Status | 自定义 | Read/Notify | 返回连接状态 |
| Device Info | 自定义 | Read | 设备信息 |

ESP-IDF的provisioning库封装了这些细节,开发者不需要手动定义GATT服务。

### 4.3 安全性优势

BLE辅助配网在安全性上有天然优势。BLE连接可以使用配对加密,凭证在加密通道中传输。同时BLE的通信距离较短(通常10米以内),物理层面就限制了窃听的可能性。ESP-IDF的provisioning库支持两种安全模式:

- Security 0: 无加密,仅用于开发调试
- Security 1: 使用Curve25519密钥交换和AES-CTR加密,配合proof of possession(PoP)防止未授权配网

### 4.4 优势与局限

BLE方案提供了最好的用户体验。用户不需要切换WiFi网络,App可以自动发现附近待配网的设备,整个过程流畅自然。同时支持向5GHz WiFi传递凭证,因为凭证传输走的是BLE通道而非WiFi。安全性也优于SmartConfig,因为有加密通道保护。

缺点是需要设备具备BLE硬件,增加了BOM成本(虽然ESP32等芯片已集成WiFi和BLE,实际增加的成本微乎其微)。BLE传输速度有限,但对于传递SSID和密码这样的小数据完全足够。

## 5 三种方案综合对比

### 5.1 核心指标对比

| 对比维度 | SmartConfig | SoftAP | BLE辅助 |
|---------|------------|--------|---------|
| 配网速度 | 10-30秒 | 30-60秒 | 15-30秒 |
| 可靠性 | 中(受环境影响) | 高 | 高 |
| 安全性 | 低(空中广播) | 中(临时AP) | 高(加密通道) |
| 用户体验 | 好(一键配网) | 差(需切换WiFi) | 最好(自动发现) |
| 5GHz支持 | 不支持 | 可传递5GHz凭证 | 可传递5GHz凭证 |
| 硬件要求 | 仅WiFi | 仅WiFi | WiFi加BLE |
| 多设备批量 | 支持(广播) | 逐个配置 | 逐个配置 |

### 5.2 选型建议

选择SmartConfig的场景:成本极度敏感、设备只有WiFi模块、需要同时配网多个设备。

选择SoftAP的场景:可靠性是第一优先级、需要丰富的配置界面、目标用户有一定技术基础。

选择BLE辅助的场景:用户体验是第一优先级、设备已经具备BLE(如ESP32)、安全性要求较高的消费级产品。

实际工程中,很多产品会实现多种方案并设置回退机制:优先尝试BLE配网,失败后回退到SoftAP。

## 6 安全性深入分析

### 6.1 SmartConfig的安全风险

SmartConfig最大的安全隐患在于凭证以编码形式在空中广播。虽然不是明文,但编码方案是公开的,攻击者如果在信号范围内同时运行混杂模式监听,理论上可以解码出WiFi密码。在公寓楼等密集环境中,这个风险不可忽视。

部分改进方案使用AES加密原始凭证后再进行长度编码,但这需要设备和App预共享密钥,增加了实现复杂度。

### 6.2 SoftAP的安全考量

SoftAP方案中,如果临时热点是开放网络(无密码),凭证传输过程相当于明文HTTP。改进方案包括:为临时热点设置预印在设备标签上的密码,或在HTTP通信层面使用TLS加密。

### 6.3 BLE配网的安全机制

BLE配网可以利用BLE协议栈的安全特性:LE Secure Connections配对提供ECDH密钥交换,proof of possession(通常是设备上印刷的PIN码或二维码)防止中间人攻击。这是三种方案中安全性最高的。

## 7 新兴配网技术

### 7.1 WiFi Easy Connect(DPP)

WiFi联盟推出的Device Provisioning Protocol(DPP)是WPA3标准的一部分。用户扫描设备上的QR码,App通过公钥加密交换WiFi凭证。整个过程基于非对称加密,安全性远高于传统方案。

DPP的流程:设备出厂预置公钥对,公钥编码在QR码中。用户扫码后App获取设备公钥,通过DH密钥交换建立安全通道,然后传递WiFi凭证。

### 7.2 Matter标准配网流程

Matter协议定义了统一的配网流程:设备通过BLE广播、用户扫描设备二维码、App通过BLE建立加密通道(使用SPAKE2+协议)、传递WiFi或Thread网络凭证。这是目前智能家居行业推动的标准化方向。

```
Matter配网流程:
设备开机 -> BLE广播(发现标识)
     |
用户扫描QR码 -> App获取设备信息
     |
BLE连接 -> SPAKE2+认证(使用QR码中的配对码)
     |
加密通道建立 -> 传递WiFi/Thread凭证
     |
设备加入网络 -> 配网完成
```

## 8 工程实践要点

### 8.1 失败处理与回退策略

配网失败是常见场景,需要合理的重试和回退机制:

1. 设置合理超时(SmartConfig建议60秒,SoftAP建议120秒)
2. 超时后自动切换备选方案(SmartConfig失败自动启动SoftAP)
3. 凭证验证:收到凭证后先尝试连接,确认成功再保存到NVS(非易失性存储)
4. 提供手动重置配网的物理按钮(长按5秒恢复出厂)

### 8.2 凭证持久化

配网成功后,WiFi凭证需要安全地存储在设备的非易失性存储(NVS)中:

```c
// ESP32 NVS存储WiFi凭证
#include "nvs_flash.h"

esp_err_t save_wifi_credentials(
    const char *ssid, const char *password) {
    nvs_handle_t handle;
    esp_err_t err;
    err = nvs_open("wifi_config", NVS_READWRITE, &handle);
    if (err != ESP_OK) return err;

    nvs_set_str(handle, "ssid", ssid);
    nvs_set_str(handle, "password", password);
    nvs_commit(handle);
    nvs_close(handle);
    return ESP_OK;
}
```

### 8.3 批量配网场景

工厂环境或大规模部署时,配网方式有所不同:

- 工厂预烧录:生产线上直接将WiFi凭证烧录到设备固件中,适合目标网络确定的场景
- 网关批量配网:通过一个已联网的网关设备,批量发现和配置周围的IoT设备
- 云端零接触配网(Zero-Touch):设备出厂预置设备证书和云平台地址,开机后自动连接预置的配网WiFi,从云端拉取实际WiFi凭证

## 9 用户体验优化

### 9.1 完整配网流程设计

一个好的配网体验应该遵循以下流程:

1. 拆箱通电:设备自动进入配网模式(LED闪烁指示)
2. App引导:打开App,自动检测到附近待配网设备
3. 确认设备:通过扫码或设备名称确认目标设备
4. 传递凭证:App自动获取当前WiFi信息,用户只需确认或输入密码
5. 等待连接:显示进度条,设备尝试连接WiFi
6. 完成确认:设备上线成功,App显示设备可用

### 9.2 常见失败场景处理

配网过程中常见的失败原因及处理方式:

- 密码错误:提示用户重新输入,高亮密码输入框
- WiFi信号弱:建议用户将设备靠近路由器完成配网后再移动到目标位置
- 路由器限制:某些路由器开启了AP隔离或MAC过滤,需引导用户检查路由器设置
- 超时未完成:自动回退到备选方案,给出明确提示

## 总结

WiFi配网是IoT设备用户体验的第一道门槛。SmartConfig胜在快速和简单,但可靠性和安全性是短板;SoftAP最为可靠,但用户体验受限于WiFi切换流程;BLE辅助配网在用户体验和安全性上表现最优,是目前消费级产品的主流选择。

随着Matter标准的推广和WiFi Easy Connect(DPP)的普及,配网体验正在向"扫码即连"的标准化方向演进。对于新项目,建议优先考虑BLE辅助配网方案,同时实现SoftAP作为回退选项,以覆盖各种使用场景。

## 参考文献

1. Espressif Systems. "ESP-IDF Programming Guide: SmartConfig". https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_smartconfig.html
2. Espressif Systems. "ESP-IDF WiFi Provisioning". https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/provisioning/wifi_provisioning.html
3. WiFi Alliance. "Wi-Fi Easy Connect Specification (Device Provisioning Protocol)". https://www.wi-fi.org/discover-wi-fi/wi-fi-easy-connect
4. Connectivity Standards Alliance. "Matter Specification - Commissioning Flow". https://csa-iot.org/developer-resource/specifications/
5. IEEE 802.11-2020. "Part 11: Wireless LAN Medium Access Control (MAC) and Physical Layer (PHY) Specifications". IEEE Standards Association.
