---
schema_version: '1.0'
id: edge-message-queue-nats
title: 边缘消息队列：NATS 与 Mosquitto 深度对比
layer: 4
content_type: comparison
difficulty: intermediate
reading_time: 20
prerequisites:
  - mqtt5-deep-dive
  - edge-computing-survey
tags:
- NATS
- MQTT
- Mosquitto
- JetStream
- Pub/Sub
- 边缘消息
- QoS
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 边缘消息队列：NATS 与 Mosquitto 深度对比

> **难度**：🟡 中级 | **领域**：消息中间件、IoT 通信 | **阅读时间**：约 20 分钟

## 日常类比

Mosquitto（MQTT broker）像报刊亭：专做订阅投递，包头小、省带宽，QoS（Quality of Service）管「丢了重送」。NATS 像物流中心：Pub/Sub、Request/Reply、JetStream 持久化与重放、叶子节点联邦都在一套里。纯遥测上报偏 MQTT；要命令确认、流重放、多边缘联邦偏 NATS——也可桥接共存。

## 摘要

对比 Eclipse Mosquitto（MQTT）与 NATS Core/JetStream 在边缘的协议开销、持久化、集群/叶子节点与安全模型。吞吐与延迟为公开材料或单机示意量级，跨硬件须复测[1][2][3][8]。

## 1 通信模式

| IoT 场景 | 模式 | 更贴合 |
|----------|------|--------|
| 遥测上报 | Pub/Sub | MQTT / Mosquitto |
| 配置下发 | Pub/Sub + 确认 | MQTT QoS 1–2 |
| 命令控制 | Request/Reply | NATS |
| 固件/审计流 | 持久化 + 重放 | NATS JetStream |
| 边缘服务发现 | Request / 广播 | NATS |
| 多工人消费 | 共享订阅 / Queue Group | MQTT 5 / NATS |

```
Pub/Sub: 发布者 ↔ Topic/Subject ↔ 多订阅者（解耦）
Request/Reply: 请求方等待响应（类 RPC over messaging）
Queue Group: 同组内负载均衡消费
```

## 2 Mosquitto 与 MQTT

MQTT（Message Queuing Telemetry Transport）面向受限设备：固定头可小至约 2 字节量级；QoS 0/1/2；Will（遗嘱）、Retain；通配 `+`/`#`[1][5]。

边缘配置要点：TLS 监听、`persistence`、合理 `max_queued_messages`、桥接云端 broker（断网本地积压、恢复后刷出）[3]。

```python
import paho.mqtt.client as mqtt
import json, time

client = mqtt.Client(client_id="sensor-001", clean_session=False)
client.will_set("devices/sensor-001/status", "offline", qos=1, retain=True)
client.connect("localhost", 1883, keepalive=60)
client.loop_start()
client.publish(
    "sensors/sensor-001/readings",
    json.dumps({"ts": int(time.time() * 1000), "temp": 25.1}),
    qos=1,
)
```

## 3 NATS Core 与 JetStream

| 层 | 能力 |
|----|------|
| NATS Core | 内存 Pub/Sub、Request/Reply、Queue Group；默认不持久化[2] |
| JetStream | Stream 持久化、Consumer 确认/重放、KV、Object Store[2][6] |

边缘常见：限制 `max_payload`/`max_connections`；JetStream `max_memory_store`/`max_file_store` 封顶；`leafnodes` 连云端集群，断网本地域继续工作[2]。

```python
import nats, asyncio, json

async def main():
    nc = await nats.connect("nats://localhost:4222")
    js = nc.jetstream()
    await js.add_stream(
        name="SENSORS",
        subjects=["sensors.>"],
        max_bytes=512 * 1024 * 1024,
        max_age=86400 * 7,
        storage="file",
    )
    await js.publish("sensors.dev1.readings", json.dumps({"temp": 25.1}).encode())
    resp = await nc.request("commands.dev1", b'{"op":"ping"}', timeout=5.0)
asyncio.run(main())
```

## 4 对比表

### 4.1 资源与功能

| 维度 | Mosquitto (MQTT) | NATS + JetStream |
|------|------------------|------------------|
| 二进制体积量级 | 很小（数百 KB 级常见） | 更大（单二进制十余 MB 量级）[3][2] |
| 协议开销 | 极低 | 文本协议，仍轻但通常高于 MQTT 最小帧 |
| Request/Reply | 需自建约定 | 原生 |
| 持久化 | QoS 队列 / 持久会话 | Stream + Durable Consumer |
| 消息重放 | 基本不支持 | 按序号/时间 |
| 集群 | 桥接为主 | 原生集群 + Supercluster |
| 多租户 | ACL 有限 | Account 等模型更完整 |
| MCU 客户端生态 | 成熟 | 相对少，网关侧更常见 |

### 4.2 延迟与吞吐（示意）

公开评测与博客常给出「NATS Core 极低延迟、JetStream/QoS1 更高」的相对秩序；绝对 msg/s、P99 毫秒数强烈依赖消息大小、持久化 fsync 策略、CPU 与网卡，文中不固化未复现数字[8][10]。选型以目标板上的端到端 P99 与断网积压测试为准。

## 5 联邦拓扑

**Mosquitto**：多跳 bridge（车间 ↔ 仓库 ↔ 云），运维简单但拓扑与环路要小心[3]。

**NATS**：云端集群 + 边缘 Leaf；Subject 级导入/导出控制，本地流量可不出边缘；JetStream 域可独立[2]。

## 6 安全

| 方式 | Mosquitto | NATS |
|------|-----------|------|
| 用户名密码 / TLS | 支持 | 支持 |
| 客户端证书 | 支持 | 支持 |
| JWT / NKey | 无原生 | 原生（去中心化凭证链）[2] |
| ACL 粒度 | Topic | Subject |

生产默认 TLS；设备侧最小权限 Subject/Topic；避免明文口令进镜像。

## 7 局限、挑战与可改进方向

### 1. 「更快」不等于「更适合 MCU」

**局限**：NATS 服务端与客户端栈对 RAM/Flash 极紧的 MCU 不友好；MQTT 仍是端侧主流[1][5]。
**改进**：MCU 跑 MQTT → 网关再桥 NATS；或仅在网关以上用 JetStream。

### 2. 持久化与磁盘寿命

**局限**：QoS1/JetStream file store 放大闪存写入。
**改进**：封顶 `max_bytes`/`max_age`；批量 flush；热路径放 SSD/工业级 eMMC；监控队列深度。

### 3. 语义易混用

**局限**：把 MQTT QoS2 或 JetStream ack 当成端到端业务 Exactly-Once，忽略应用去重。
**改进**：业务幂等键；明确「传输至少一次 + 应用去重」契约。

### 4. 桥接双栈复杂度

**局限**：Mosquitto↔NATS 主题映射、QoS 与保留消息语义不一致易丢语义。
**改进**：单一真源协议逐步收敛；桥接层做契约测试与死信观察。

## 8 选型与调优

```
小包高频低功耗端侧 → MQTT/Mosquitto
命令+确认、重放审计 → NATS JetStream
多边缘联邦 → NATS Leaf
已有 MQTT 资产 → 桥接渐进，而非一夜切换
```

长连接 + 合理 keepalive；大消息先压缩；JetStream 优先 file + 限额，避免 memory store 撑爆边缘节点。

## 参考文献

[1] OASIS, "MQTT Version 5.0," 2019. https://docs.oasis-open.org/mqtt/mqtt/v5.0/
[2] Synadia / NATS, "NATS Documentation," https://docs.nats.io/
[3] Eclipse Foundation, "Eclipse Mosquitto," https://mosquitto.org/
[4] D. Collison, "NATS Messaging" (blog series), nats.io.
[5] A. Stanford-Clark, H. Linh Truong, "MQTT For Sensor Networks (MQTT-SN) Protocol," IBM, 2013.
[6] Synadia, "JetStream," NATS documentation.
[7] HiveMQ, "MQTT Essentials / broker comparison materials," 2024.
[8] H. Koziolek et al., "Performance Evaluation of Message Brokers for IoT," IEEE SEAA, 2020.
[9] EMQX, "MQTT Broker Comparison," https://www.emqx.com/en/blog
[10] R. Banno et al., "Measuring MQTT Performance for IoT Applications," IEEE ICIOT, 2019.
[11] NATS, "Leaf Nodes," documentation.
[12] OASIS, "MQTT Version 3.1.1," 2014.
