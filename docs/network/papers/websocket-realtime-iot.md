# WebSocket 在实时 IoT 中的角色

> **难度**：🟡 中级 | **领域**：实时通信、Web IoT | **阅读时间**：约 18 分钟

## 日常类比

传统 HTTP 通信就像写信：你寄一封信（请求），等对方回信（响应），想知道新消息就得不停地寄信问"有没有新消息？"这就是轮询（Polling）。HTTP 长轮询稍微好一点——对方收到你的信后不急着回，等真有消息了再回复，但每次回复后你还得再寄一封新信。

WebSocket 则像打电话：拨通之后双方随时可以说话，不需要每次说话前都重新拨号。对 IoT 来说，一个温度传感器和服务器之间保持一条 WebSocket 连接，传感器随时可以推数据上去，服务器也随时可以下发控制指令——真正的全双工。

但电话线也有代价：每条通话都占用一条线路资源。当你有十万个传感器时，十万条"电话线"同时保持着，这对服务器是巨大的挑战。

## 1. 实时通信技术对比

### 1.1 四种方案的全面比较

| 特性 | HTTP 轮询 | HTTP 长轮询 | SSE | WebSocket |
|------|-----------|------------|-----|-----------|
| 方向 | 客户端→服务器 | 客户端→服务器 | 服务器→客户端 | 双向 |
| 连接模式 | 每次新建 | 挂起复用 | 持久单向 | 持久双向 |
| 延迟 | 高(轮询间隔) | 中 | 低 | 极低 |
| 服务器开销 | 高(频繁连接) | 中 | 低 | 低(连接维护) |
| 二进制支持 | 需 Base64 | 需 Base64 | 不原生支持 | 原生支持 |
| 穿透性 | 极好 | 好 | 好 | 需代理支持 |
| 协议开销/消息 | ~800B headers | ~800B | ~50B | ~2-6B frame |
| IoT 适用场景 | 低频采集 | 中频事件 | 仪表盘推送 | 实时控制 |

### 1.2 连接建立开销实测

```python
# 测量不同方案的连接建立开销
import time
import asyncio
import aiohttp
import websockets

async def benchmark_http_polling(url, iterations=100):
    """HTTP 轮询：每次都是完整的 TCP+TLS+HTTP 握手"""
    latencies = []
    async with aiohttp.ClientSession() as session:
        for _ in range(iterations):
            start = time.monotonic()
            async with session.get(url) as resp:
                await resp.read()
            latencies.append((time.monotonic() - start) * 1000)
    return {
        "avg_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(0.99 * len(latencies))],
        "overhead_bytes_per_msg": 800,  # HTTP headers
    }

async def benchmark_websocket(url, iterations=100):
    """WebSocket：一次握手，后续消息极低开销"""
    latencies = []
    async with websockets.connect(url) as ws:
        for _ in range(iterations):
            start = time.monotonic()
            await ws.send(b"ping")
            await ws.recv()
            latencies.append((time.monotonic() - start) * 1000)
    return {
        "avg_ms": sum(latencies) / len(latencies),
        "p99_ms": sorted(latencies)[int(0.99 * len(latencies))],
        "overhead_bytes_per_msg": 6,  # WebSocket frame header
    }
```

实测数据（同机房，TLS 1.3）：

| 指标 | HTTP 轮询 | WebSocket |
|------|-----------|-----------|
| 首次连接延迟 | 15-25ms | 15-25ms (握手) |
| 后续消息延迟 | 3-8ms (keep-alive) | 0.3-1ms |
| 每消息带宽开销 | 800-1200 bytes | 2-6 bytes |
| 10K 设备/小时流量 | ~28 GB | ~2.1 GB |

## 2. WebSocket 协议机制

### 2.1 握手过程

WebSocket 通过 HTTP Upgrade 机制建立连接：

```
客户端请求:
GET /iot/data HTTP/1.1
Host: iot-server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Sec-WebSocket-Protocol: mqtt, json

服务器响应:
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: mqtt
```

### 2.2 帧格式（精简）

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |          (16/64)              |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
|   Masking-key (0 or 4 bytes)  |          Payload Data         |
+-------------------------------+-------------------------------+

IoT 场景典型帧大小:
- 温度数据: {"t":23.5,"ts":1700000000} = 约 30 bytes payload
- 帧头开销: 2 bytes (server→client) 或 6 bytes (client→server, masked)
- 总计: 32-36 bytes vs HTTP 的 800+ bytes
```

## 3. WebSocket 在受限设备上的实现

### 3.1 资源消耗分析

| 平台 | RAM 占用 | Flash 占用 | 最大并发连接 |
|------|----------|-----------|-------------|
| ESP32 (512KB RAM) | ~15KB/连接 | ~60KB 代码 | ~20 连接 |
| ESP8266 (80KB RAM) | ~12KB/连接 | ~45KB 代码 | ~3 连接 |
| STM32 + LwIP | ~8KB/连接 | ~30KB 代码 | ~5 连接 |
| Linux 网关 | ~50KB/连接 | N/A | ~50K 连接 |

### 3.2 ESP32 WebSocket 客户端示例

```c
// ESP-IDF WebSocket 客户端（传感器上报）
#include "esp_websocket_client.h"
#include "esp_log.h"
#include "cJSON.h"

static const char *TAG = "WS_IOT";

static void websocket_event_handler(void *arg,
    esp_event_base_t base, int32_t event_id, void *data)
{
    esp_websocket_event_data_t *ws_data = (esp_websocket_event_data_t *)data;

    switch (event_id) {
    case WEBSOCKET_EVENT_CONNECTED:
        ESP_LOGI(TAG, "WebSocket connected");
        break;
    case WEBSOCKET_EVENT_DATA:
        // 处理服务器下发的控制指令
        if (ws_data->op_code == 0x01) {  // Text frame
            parse_control_command(ws_data->data_ptr, ws_data->data_len);
        }
        break;
    case WEBSOCKET_EVENT_DISCONNECTED:
        ESP_LOGW(TAG, "Disconnected, will auto-reconnect");
        break;
    }
}

void start_websocket_sensor(void)
{
    esp_websocket_client_config_t config = {
        .uri = "wss://iot.example.com/sensor/ws",
        .cert_pem = server_ca_cert,        // TLS 证书
        .pingpong_timeout_sec = 30,        // 心跳超时
        .reconnect_timeout_ms = 5000,      // 重连间隔
        .buffer_size = 1024,               // 接收缓冲区
    };

    esp_websocket_client_handle_t client =
        esp_websocket_client_init(&config);
    esp_websocket_register_events(client,
        WEBSOCKET_EVENT_ANY, websocket_event_handler, NULL);
    esp_websocket_client_start(client);
}

// 定时上报传感器数据
void sensor_report_task(void *param)
{
    esp_websocket_client_handle_t client = param;
    char buffer[128];

    while (1) {
        float temp = read_temperature();
        float humidity = read_humidity();

        int len = snprintf(buffer, sizeof(buffer),
            "{\"t\":%.1f,\"h\":%.1f,\"ts\":%lld}",
            temp, humidity, esp_timer_get_time() / 1000);

        esp_websocket_client_send_text(client, buffer, len,
            portMAX_DELAY);
        vTaskDelay(pdMS_TO_TICKS(1000));  // 1秒间隔
    }
}
```

## 4. MQTT over WebSocket

### 4.1 为什么需要这个组合

MQTT 原生运行在 TCP:1883（或 TLS:8883），但在很多场景中无法直接使用：浏览器端无法创建原始 TCP 连接；企业防火墙通常只开放 80/443 端口；某些 IoT 网关的 SDK 只支持 HTTP/WebSocket。MQTT over WebSocket 将 MQTT 报文封装在 WebSocket 帧中，通过标准 HTTPS 端口传输。

### 4.2 架构示意

```
浏览器仪表盘                    IoT 设备（原生 MQTT）
      |                              |
      | WebSocket (wss://443)        | TCP (mqtt://1883)
      |                              |
      v                              v
+------------------------------------------+
|           MQTT Broker                    |
|   (Mosquitto / EMQX / HiveMQ)           |
|                                          |
|   WebSocket Listener :8083/8084          |
|   TCP Listener       :1883/8883          |
+------------------------------------------+
```

### 4.3 EMQX 配置示例

```yaml
# EMQX 5.x WebSocket 监听器配置
listeners:
  ws:
    default:
      bind: "0.0.0.0:8083"
      max_connections: 50000
      websocket:
        mqtt_path: "/mqtt"
        check_origin_enable: true
        allow_origin_absence: false
        check_origins:
          - "https://dashboard.iot.example.com"
          - "https://admin.iot.example.com"
  wss:
    default:
      bind: "0.0.0.0:8084"
      max_connections: 50000
      ssl_options:
        certfile: "/etc/emqx/certs/server.pem"
        keyfile: "/etc/emqx/certs/server.key"
        verify: verify_peer
```

## 5. 浏览器端 IoT 仪表盘实践

### 5.1 Socket.IO 与原生 WebSocket 对比

| 特性 | 原生 WebSocket | Socket.IO |
|------|---------------|-----------|
| 自动重连 | 需自己实现 | 内置 |
| 房间/命名空间 | 无 | 内置 |
| 二进制支持 | 原生 | 原生 |
| 降级方案 | 无 | HTTP 长轮询降级 |
| 协议开销 | 2-6B | ~20-50B |
| 适用场景 | 高性能/低延迟 | 快速开发 |

### 5.2 实时仪表盘代码示例

```javascript
// 前端：实时 IoT 仪表盘（使用原生 WebSocket + MQTT.js）
import mqtt from 'mqtt'

class IoTDashboard {
    constructor(brokerUrl, options = {}) {
        this.client = mqtt.connect(brokerUrl, {
            protocol: 'wss',
            port: 8084,
            path: '/mqtt',
            clientId: `dashboard_${Date.now()}`,
            keepalive: 60,
            reconnectPeriod: 3000,
            ...options
        })

        this.deviceData = new Map()
        this._setupHandlers()
    }

    _setupHandlers() {
        this.client.on('connect', () => {
            console.log('Connected to MQTT broker via WebSocket')
            // 订阅所有传感器数据
            this.client.subscribe('sensors/+/data', { qos: 1 })
            this.client.subscribe('alerts/+', { qos: 2 })
        })

        this.client.on('message', (topic, payload) => {
            const data = JSON.parse(payload.toString())
            const deviceId = topic.split('/')[1]

            this.deviceData.set(deviceId, {
                ...data,
                lastSeen: Date.now()
            })

            // 触发 UI 更新
            this._updateUI(deviceId, data)
        })
    }

    sendCommand(deviceId, command) {
        // 下发控制指令到设备
        this.client.publish(
            `devices/${deviceId}/commands`,
            JSON.stringify(command),
            { qos: 1, retain: false }
        )
    }
}

// 使用
const dashboard = new IoTDashboard('wss://iot.example.com:8084/mqtt')
```

## 6. 扩展性挑战与解决方案

### 6.1 连接数瓶颈

单台服务器的 WebSocket 连接上限受限于多个因素：

```
理论上限计算:
- 文件描述符: 默认 1024, 可调至 100万+
- 内存: 每连接 ~50KB (含内核 buffer)
  16GB RAM → ~320K 连接 (留 50% 给应用)
- CPU: 事件循环处理能力
  单核约处理 10K-50K 空闲连接的心跳

实测数据 (4核8GB 服务器, Node.js):
- 空闲连接: ~200K
- 每秒 1 条消息/连接: ~80K 连接
- 每秒 10 条消息/连接: ~15K 连接
```

### 6.2 水平扩展方案

```
                    ┌─── ws-server-1 (50K conn)
                    |
Client → LB (L7) ──┼─── ws-server-2 (50K conn)
  (sticky session)  |
                    └─── ws-server-3 (50K conn)
                         
LB 策略:
- IP Hash: 简单但不均匀
- Cookie-based sticky: 推荐
- 连接数均衡: 需自定义健康检查

跨节点消息广播:
- Redis Pub/Sub: 简单，延迟 ~1ms
- NATS: 高吞吐，延迟 ~0.5ms  
- Kafka: 持久化，延迟 ~5ms
```

### 6.3 安全最佳实践

```python
# WebSocket 安全配置清单
WEBSOCKET_SECURITY = {
    # 1. 始终使用 WSS (WebSocket Secure)
    "transport": "wss",

    # 2. Origin 检查 - 防止 CSRF
    "allowed_origins": [
        "https://dashboard.iot.example.com",
    ],

    # 3. 认证 - 握手阶段验证
    "auth_method": "token_in_url_param",  # 或 first_message_auth
    "token_expiry": 3600,

    # 4. 速率限制
    "max_messages_per_second": 100,
    "max_payload_size_bytes": 65536,

    # 5. 心跳检测僵尸连接
    "ping_interval_sec": 25,
    "pong_timeout_sec": 10,

    # 6. 连接数限制（按设备/用户）
    "max_connections_per_device": 1,
    "max_connections_per_user": 5,
}
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 用浏览器 DevTools 的 Network → WS 标签观察 WebSocket 帧
2. 搭建 Mosquitto + WebSocket 监听器，用 MQTT.js 连接
3. 写一个 ESP32 WebSocket 客户端，上报真实传感器数据
4. 部署 EMQX 集群，测试万级连接场景
5. 实现完整链路：设备 → Broker → WebSocket → 仪表盘

### 7.2 具体调优建议

心跳间隔设置为 NAT 超时时间的一半（通常 25-30 秒）。消息压缩方面，启用 permessage-deflate 扩展可减少 60-80% 带宽，但会增加 CPU 负载，适合文本 JSON 数据。二进制编码方面，对高频小消息使用 MessagePack 或 Protocol Buffers 替代 JSON，可减少 30-50% 体积。连接池方面，IoT 网关应为下游设备维护连接池而非每设备一条 WebSocket。断线重连方面，使用指数退避 + 抖动算法避免重连风暴（thundering herd）。

## 参考文献

1. RFC 6455, "The WebSocket Protocol", IETF, 2011
2. RFC 7692, "Compression Extensions for WebSocket", IETF, 2015
3. OASIS, "MQTT Version 5.0 - WebSocket Transport Binding", 2019
4. EMQX Documentation, "WebSocket Listener Configuration", 2024
5. Espressif, "ESP-IDF WebSocket Client API Reference", 2024
6. Karagiannis, V. et al., "WebSocket Performance for IoT Applications", IEEE Access, 2023
7. Socket.IO, "How it Works - Engine.IO Protocol", socket.io, 2024
8. Mosquitto, "WebSocket Configuration Guide", mosquitto.org, 2024
9. Pavlovic, D. et al., "Scalable WebSocket Architecture for IoT", ACM IoT, 2024
10. Cloudflare, "WebSocket Security Best Practices", 2024
