# 边缘消息队列：NATS 与 Mosquitto 深度对比

> **难度**：🟡 中级 | **领域**：消息中间件、IoT 通信、分布式系统 | **阅读时间**：约 20 分钟

## 日常类比

消息队列就像一个智能邮局系统。Mosquitto（MQTT broker）像是一个专门的报刊亭——擅长把订阅的杂志准时送到每户人家门口，轻量、省纸（带宽），即使信箱满了也能把杂志先存着（QoS 1/2）。它专注于一件事：发布/订阅消息投递。

NATS 则更像一个现代物流中心——不仅能送杂志（pub/sub），还能帮你寄快递等回复（request/reply），提供包裹存储和历史查询（JetStream），甚至能在多个城市间自动同步库存（集群/超级集群）。它更通用，但相应地也需要更多仓库空间。

在边缘 IoT 场景中，选择 Mosquitto 还是 NATS 取决于你的通信模式：纯遥测上报选 Mosquitto，需要命令下发和确认回复选 NATS，或者两者结合使用。

## 1. 消息模式基础

### 1.1 Pub/Sub vs Request/Reply

```
Pub/Sub (发布/订阅):
Publisher --> [Topic: sensors/temp] --> Subscriber A
                                   --> Subscriber B
                                   --> Subscriber C
发布者不知道谁在订阅，解耦度高

Request/Reply (请求/响应):
Requester --[请求]--> Service --[响应]--> Requester
类似 HTTP 但基于消息，支持超时/重试

Queue Group (负载均衡):
Publisher --> [Subject] --> |Worker A|  (轮流消费)
                       --> |Worker B|
                       --> |Worker C|
```

### 1.2 IoT 通信模式映射

| IoT 场景 | 通信模式 | 更适合 |
|----------|---------|--------|
| 传感器上报遥测 | Pub/Sub (单向) | MQTT/Mosquitto |
| 云端下发配置 | Pub/Sub (带确认) | MQTT QoS 1-2 |
| 设备命令控制 | Request/Reply | NATS |
| 固件升级通知 | Pub/Sub + 持久化 | NATS JetStream |
| 边缘服务发现 | Request (广播) | NATS |
| 数据流处理 | Stream (有序、重放) | NATS JetStream |

## 2. Mosquitto（MQTT Broker）深入

### 2.1 MQTT 协议特点

MQTT 是为受限设备设计的轻量协议：

- 最小包头仅 2 字节（HTTP 至少几百字节）
- 三级 QoS（0: 最多一次, 1: 至少一次, 2: 精确一次）
- 遗嘱消息（设备离线自动通知）
- 保留消息（新订阅者立刻获取最新值）
- Topic 通配符（sensors/+/temperature, sensors/#）

### 2.2 Mosquitto 配置与部署

```conf
# mosquitto.conf (边缘优化)
listener 1883 0.0.0.0
protocol mqtt

# TLS 加密（生产必须）
listener 8883
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
cafile /etc/mosquitto/certs/ca.crt

# 持久化（确保 QoS 1/2 消息不丢）
persistence true
persistence_location /var/lib/mosquitto/
autosave_interval 60

# 性能调优
max_inflight_messages 100
max_queued_messages 10000
message_size_limit 1048576

# 桥接到云端 MQTT（断网时本地缓存）
connection bridge-to-cloud
address cloud-mqtt.example.com:8883
topic sensors/# out 1
topic commands/# in 1
bridge_cafile /etc/mosquitto/certs/cloud-ca.crt
notifications true
restart_timeout 30
```

### 2.3 Python 客户端示例

```python
import paho.mqtt.client as mqtt
import json
import time

class IoTSensorPublisher:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client(
            client_id="sensor-001",
            clean_session=False  # 持久会话，断线重连不丢消息
        )
        # 遗嘱消息：设备异常离线时自动发布
        self.client.will_set(
            "devices/sensor-001/status",
            payload="offline",
            qos=1,
            retain=True
        )
        self.client.connect(broker, port, keepalive=60)
        self.client.loop_start()

    def publish_reading(self, temperature, humidity):
        payload = json.dumps({
            "ts": int(time.time() * 1000),
            "temp": temperature,
            "humid": humidity,
            "device": "sensor-001"
        })
        # QoS 1: 至少送达一次
        self.client.publish(
            "sensors/sensor-001/readings",
            payload=payload,
            qos=1
        )

class IoTCommandSubscriber:
    def __init__(self, broker="localhost"):
        self.client = mqtt.Client(client_id="gateway-001")
        self.client.on_message = self._on_message
        self.client.connect(broker)
        # 订阅该网关下所有设备的命令
        self.client.subscribe("commands/gateway-001/#", qos=1)
        self.client.loop_start()

    def _on_message(self, client, userdata, msg):
        command = json.loads(msg.payload)
        print(f"Received command on {msg.topic}: {command}")
        # 执行命令并回复状态
        self.client.publish(
            f"responses/{msg.topic}",
            payload=json.dumps({"status": "ok"}),
            qos=1
        )
```

## 3. NATS 核心与 JetStream

### 3.1 NATS 架构

NATS 的设计哲学是"简单至上"：

```
NATS Core (内存中，无持久化):
  - Pub/Sub: 发布即忘，超快（10M+ msg/s 单节点）
  - Request/Reply: 同步请求模式
  - Queue Groups: 负载均衡消费

NATS JetStream (持久化层):
  - Stream: 持久化消息序列
  - Consumer: 可重放、可确认的消费者
  - Key-Value: 分布式 KV 存储
  - Object Store: 大对象存储
```

### 3.2 NATS 服务器部署

```conf
# nats-server.conf (边缘配置)
listen: 0.0.0.0:4222

# 适配边缘资源
max_payload: 1MB
max_connections: 1000

# JetStream 持久化
jetstream {
    store_dir: "/data/nats/jetstream"
    max_memory_store: 256MB
    max_file_store: 2GB
}

# 叶子节点连接到中心集群
leafnodes {
    remotes [
        {
            url: "nats-leaf://cloud-nats.example.com:7422"
            credentials: "/etc/nats/edge-node.creds"
        }
    ]
}

# 认证
authorization {
    users = [
        {user: "sensor", password: "xxx", permissions: {
            publish: ["sensors.>"]
            subscribe: ["commands.gateway-001.>"]
        }}
        {user: "admin", password: "xxx", permissions: {
            publish: [">"]
            subscribe: [">"]
        }}
    ]
}
```

### 3.3 NATS 客户端示例

```python
import nats
import asyncio
import json

async def main():
    # 连接 NATS
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()

    # 创建 Stream（持久化）
    await js.add_stream(
        name="SENSORS",
        subjects=["sensors.>"],
        retention="limits",
        max_bytes=1024*1024*512,  # 512MB 上限
        max_age=86400 * 7,       # 保留 7 天
        storage="file"
    )

    # 发布传感器数据（持久化到 JetStream）
    async def publish_reading(device_id, temp, humid):
        await js.publish(
            f"sensors.{device_id}.readings",
            json.dumps({
                "ts": asyncio.get_event_loop().time(),
                "temp": temp,
                "humid": humid
            }).encode()
        )

    # Request/Reply: 发送命令并等待回复
    async def send_command(device_id, command):
        try:
            response = await nc.request(
                f"commands.{device_id}",
                json.dumps(command).encode(),
                timeout=5.0  # 5 秒超时
            )
            return json.loads(response.data)
        except nats.errors.TimeoutError:
            return {"error": "device not responding"}

    # 创建持久化消费者（支持重放）
    consumer = await js.pull_subscribe(
        "sensors.>",
        durable="edge-processor"
    )

    # 批量拉取处理
    while True:
        try:
            msgs = await consumer.fetch(batch=100, timeout=1)
            for msg in msgs:
                data = json.loads(msg.data)
                process(data)
                await msg.ack()  # 确认处理完成
        except nats.errors.TimeoutError:
            await asyncio.sleep(0.1)

asyncio.run(main())
```

## 4. 深度对比

### 4.1 资源占用

测试环境：Raspberry Pi 4 (4GB), 1000 个客户端连接, 10K msg/s

| 指标 | Mosquitto 2.0 | NATS Server 2.10 |
|------|--------------|-----------------|
| 二进制大小 | 300 KB | 20 MB |
| 空闲内存 | 5 MB | 30 MB |
| 1K连接内存 | 25 MB | 80 MB |
| 10K msg/s CPU | 15% | 25% |
| 持久化写入 | 按消息 fsync | 批量 flush |
| Go/Rust 客户端 | 第三方 | 官方 |

### 4.2 延迟对比

```
端到端延迟 (本地, P99):
  NATS Core (无持久化):     0.1 ms
  NATS JetStream:          0.5 ms
  Mosquitto QoS 0:         0.2 ms
  Mosquitto QoS 1:         0.8 ms
  Mosquitto QoS 2:         2.5 ms

吞吐量 (单核, 256B 消息):
  NATS Core:               2M msg/s
  NATS JetStream:          500K msg/s
  Mosquitto QoS 0:         200K msg/s
  Mosquitto QoS 1:         80K msg/s
```

### 4.3 功能对比

| 功能 | Mosquitto (MQTT) | NATS + JetStream |
|------|-----------------|-----------------|
| 发布/订阅 | 支持 | 支持 |
| 请求/响应 | 需自行实现 | 原生支持 |
| 消息持久化 | QoS 1/2 队列 | JetStream Stream |
| 消息重放 | 不支持 | 按时间/序号重放 |
| 消费者组 | MQTT 5.0 共享订阅 | Queue Group |
| 集群 | 需桥接 | 原生集群 |
| 多租户 | 有限 | Account 隔离 |
| KV 存储 | 不支持 | JetStream KV |
| 通配符 | +/# | */.> |
| 离线消息 | 持久会话 | Durable Consumer |
| 协议开销 | 极小（2B 起） | 较小（文本协议） |

## 5. 集群与联邦

### 5.1 Mosquitto 桥接模式

Mosquitto 不支持原生集群，通过桥接实现多节点互联：

```
边缘节点 A (工厂车间)        边缘节点 B (仓库)
+-------------+             +-------------+
| Mosquitto A |--桥接------>| Mosquitto B |
| 本地设备     |<--桥接-----|  本地设备    |
+------+------+             +------+------+
       |                           |
       +----------桥接-------------+
                   |
            +------+------+
            | Cloud MQTT  |
            | (HiveMQ/EMQX)|
            +-------------+
```

### 5.2 NATS 超级集群 + 叶子节点

```
                Cloud Cluster (3 nodes)
              +---+   +---+   +---+
              | N1|---| N2|---| N3|
              +---+   +---+   +---+
               /               \
   Leaf Node /                  \ Leaf Node
     +----+                      +----+
     |Edge|                      |Edge|
     | A  |                      | B  |
     +----+                      +----+
     /    \                      /    \
  Dev1  Dev2                  Dev3  Dev4

特点:
- 叶子节点断网后独立工作
- 重连后自动同步（JetStream Replication）
- Subject 级别路由（不是所有消息都上云）
- 延迟感知（本地消息不出边缘）
```

### 5.3 NATS 叶子节点配置

```conf
# edge-leaf.conf
listen: 0.0.0.0:4222

jetstream {
    store_dir: "/data/nats"
    max_memory_store: 128MB
    max_file_store: 1GB
    domain: "edge-factory-a"  # 独立 JetStream 域
}

leafnodes {
    remotes [
        {
            url: "nats-leaf://cloud.example.com:7422"
            credentials: "/etc/nats/leaf.creds"
            # 只同步特定 subject
            deny_imports: ["internal.>"]
            deny_exports: ["local.>"]
        }
    ]
}
```

## 6. 安全模型对比

### 6.1 认证方式

| 方式 | Mosquitto | NATS |
|------|-----------|------|
| 用户名/密码 | 支持 | 支持 |
| TLS 客户端证书 | 支持 | 支持 |
| Token | 支持 | 支持 |
| JWT/NKey | 不支持 | 原生支持 |
| OAuth 2.0 | 插件 | 不支持 |
| ACL 粒度 | Topic 级 | Subject 级 |

### 6.2 NATS 去中心化安全

```bash
# NATS 使用 NKey（Ed25519 密钥对）+ JWT
# 无需中心化密码数据库

# 生成操作者密钥
nsc add operator IoT-Edge

# 创建账户（对应一个租户/项目）
nsc add account FactoryA

# 创建用户（对应一个设备/服务）
nsc add user --account FactoryA sensor-001

# 设置权限
nsc edit user sensor-001 \
  --allow-pub "sensors.factory-a.>" \
  --allow-sub "commands.sensor-001.>"

# 导出凭证文件（部署到设备）
nsc generate creds --account FactoryA --name sensor-001 > sensor-001.creds
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 安装 Mosquitto，用 mosquitto_pub/sub 命令行体验 MQTT
2. 用 Python paho-mqtt 写一个完整的传感器采集发布程序
3. 安装 NATS Server，用 nats CLI 体验 pub/sub 和 request/reply
4. 配置 JetStream，实现消息持久化和重放
5. 搭建 Mosquitto 到 NATS 的桥接（mqtt-bridge-nats）

### 7.2 具体选型建议

```
纯传感器遥测（小包、高频、低功耗设备）?
  --> Mosquitto (MQTT 协议开销最小)

需要命令下发+确认回复?
  --> NATS (原生 request/reply)

需要消息重放/审计?
  --> NATS JetStream

设备极度受限 (MCU, < 1MB RAM)?
  --> MQTT (有 MCU 级客户端实现)

需要多边缘节点联邦?
  --> NATS 超级集群 + 叶子节点

已有 MQTT 生态，逐步升级?
  --> Mosquitto + NATS 桥接混合部署
```

### 7.3 性能调优

- **Mosquitto**：开启 persistence 但设置合理的 max_queued_messages，避免内存溢出
- **NATS**：JetStream 使用 file storage 而非 memory，配合 max_bytes 限制
- **连接管理**：保持长连接，避免频繁重连（MQTT keepalive 设 60-120s）
- **批量发布**：NATS 支持批量 publish，减少网络往返
- **压缩**：大消息使用 gzip/snappy 压缩后再发送

## 参考文献

1. OASIS. "MQTT Version 5.0 Specification." 2019. https://docs.oasis-open.org/mqtt/mqtt/v5.0/
2. Synadia. "NATS Documentation." 2024. https://docs.nats.io/
3. Eclipse Foundation. "Eclipse Mosquitto." 2024. https://mosquitto.org/
4. Collison, D. "NATS Messaging - Part 1." 2024. https://nats.io/blog/
5. Jaffey, T., Stanford-Clark, A. "MQTT for IoT." IBM DeveloperWorks, 2013.
6. Synadia. "NATS JetStream Technical Preview." 2024.
7. HiveMQ. "MQTT vs NATS: A Comparison." Technical Blog, 2024.
8. Koziolek, H., et al. "Performance Evaluation of Message Brokers for IoT." IEEE SEAA 2020.
9. EMQX. "The Comparison of IoT MQTT Brokers." 2024. https://www.emqx.com/en/blog
10. Banno, R., et al. "Measuring MQTT Performance for IoT Applications." IEEE ICIOT 2019.
