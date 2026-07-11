---
schema_version: '1.0'
id: flink-on-edge-streaming
title: 流处理 Flink-on-Edge 实践
layer: 4
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - edge-message-queue-nats
  - edge-computing-survey
tags:
- Apache Flink
- 流处理
- Watermark
- Checkpoint
- 边缘分析
- Exactly-Once
- PyFlink
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 流处理 Flink-on-Edge 实践

> **难度**：🟡 中级 | **领域**：流处理、边缘分析 | **阅读时间**：约 20 分钟

## 日常类比

批处理像收网后再分鱼；流处理（Apache Flink）像河上筛网——事件经过即分拣、聚合、告警。传感器是无界流：先攒批上云再分析，异常可能晚分钟～小时。Flink-on-Edge 把窗口与状态放到数据源头附近；断网补传造成的乱序靠事件时间与 Watermark（水位线）消化。

## 摘要

梳理流批差异、事件时间、窗口、边缘资源裁剪、mini-batch、与 Kafka Streams 等替代，以及 Checkpoint 与 Exactly-Once 在闪存边缘上的代价。延迟/内存数字为量级示意[1][2][3]。

## 1 流处理基础

| 维度 | 批处理 | 流处理 |
|------|--------|--------|
| 数据 | 有界 | 无界事件流 |
| 触发 | 定时/手动 | 持续/事件驱动 |
| 延迟 | 分钟～小时量级 | 毫秒～秒量级（视配置） |
| 状态 | 常每次重算 | 增量状态 |
| 容错 | 重跑作业 | Checkpoint / 重放 |

事件时间（设备采样时刻）≠ 处理时间（引擎见到时刻）。IoT 乱序用有界乱序 Watermark 策略[9]：

```java
.assignTimestampsAndWatermarks(
    WatermarkStrategy
        .<SensorEvent>forBoundedOutOfOrderness(Duration.ofSeconds(5))
        .withTimestampAssigner((e, ts) -> e.getTimestamp()))
```

窗口：滚动（Tumbling）、滑动（Sliding）、会话（Session）把无界流切成可聚合片段[1][6]。

## 2 Flink 架构与作业形态

JobManager 调度与 Checkpoint 协调；TaskManager 跑算子与 Slot（槽）资源隔离[1][10]。边缘常单节点 Standalone：1 JM + 1 TM，并行度压到核数减一。

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.time import Time

env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(2)
(env.add_source(mqtt_source)
   .filter(lambda x: x.value is not None)
   .key_by(lambda x: x.device_id)
   .window(TumblingEventTimeWindows.of(Time.minutes(1)))
   .aggregate(TemperatureAggregator())
   .filter(lambda x: x.avg_temp > x.threshold)
   .add_sink(alert_sink()))
env.execute("Edge Temperature Monitor")
```

## 3 边缘资源裁剪

云端多 TM 大内存假设不成立。边缘方向：JM/TM 进程内存压到数百 MB–约 1GB 量级；减小 network buffer；RocksDB 状态后端限制 block cache；Checkpoint 间隔拉长、增量 + 本地恢复[2][10]。绝对能否在某树莓派镜像跑通，取决于作业状态大小与 JVM，需实测。

```yaml
jobmanager.memory.process.size: 512m
taskmanager.memory.process.size: 1024m
taskmanager.numberOfTaskSlots: 2
state.backend: rocksdb
execution.checkpointing.interval: 60000
state.backend.incremental: true
state.backend.local-recovery: true
```

## 4 Mini-batch 与框架对比

| 方面 | True Streaming | Mini-Batch |
|------|----------------|------------|
| 延迟 | 更低 | 秒级可配 |
| 吞吐/CPU | 逐条开销大 | 批量摊销更好 |
| 边缘 | 要低延迟告警时用 | 资源紧、延迟松时优 |

Table API 可开 `table.exec.mini-batch.*` 攒批[2]。

| 框架 | 资源门槛量级 | 状态 | 适合 |
|------|--------------|------|------|
| Flink | 较高（GB 级更舒适） | 强（RocksDB） | 复杂有状态分析 |
| Kafka Streams | 较低（库嵌入） | 强 | 已有 Kafka |
| Spark Structured Streaming | 更高 | 微批为主 | 批流一体已有 Spark |
| Benthos 等 | 很低 | 弱/无 | 简单 ETL |

资源不够完整 Flink 时，Kafka Streams 库模式或更轻 ETL 常更现实[5][3]。

## 5 Exactly-Once 与 Checkpoint

At-most-once / at-least-once / exactly-once：工业告警既怕漏也怕刷屏。Flink 用 barrier 对齐 Checkpoint，故障从快照恢复并重放；端到端 exactly-once 还要求 Source/Sink 事务或幂等配合[1][10]。

边缘优化：拉长间隔、增量快照、本地恢复；接受「恢复时重放更多」换「平时少写盘」。

## 6 局限、挑战与可改进方向

### 1. JVM 与镜像过重

**局限**：标准 Flink 发行版对 RAM/启动时间不友好，ARM 上 GC 停顿更明显[2][7]。
**改进**：压内存参数、G1、考虑 GraalVM Native 试验；状态与并行度先做容量规划。

### 2. Checkpoint 磨损闪存

**局限**：SD/eMMC 上频繁 checkpoint 缩短寿命。
**改进**：目录放 SSD/tmpfs（权衡掉电）；增量 + 长间隔；上游 MQTT/NATS 持久化作缓冲[2]。

### 3. 乱序与晚到数据

**局限**：断网补传可击穿过小 Watermark，窗口结果偏差。
**改进**：按业务设乱序界与允许 lateness；关键指标用可修正会话或侧输出晚到事件。

### 4. 「上了 Flink」不等于可观测闭环

**局限**：缺背压、checkpoint 失败、消费滞后监控时难运维。
**改进**：暴露 metrics；告警 checkpoint 时长/失败；演练 kill TM 恢复。

## 7 实践要点

并行度 ≤ 核数留余量；大状态用 RocksDB 但盯磁盘；序列化用 Avro/Protobuf 而非默认可串行化；Source 侧保留本地队列以抗断网；先本地 WordCount → 事件时间窗口 → Compose 最小集群 → 再上 ARM 板。

## 参考文献

[1] P. Carbone et al., "Apache Flink: Stream and Batch Processing in a Single Engine," IEEE Data Eng. Bull., 2015.
[2] Apache Flink, "Documentation," https://flink.apache.org/
[3] J. Karimov et al., "Benchmarking Distributed Stream Data Processing Systems," ICDE, 2018.
[4] M. Zaharia et al., "Structured Streaming," SIGMOD, 2018.
[5] Apache Kafka, "Kafka Streams," documentation.
[6] F. Hueske, V. Kalavri, *Stream Processing with Apache Flink*, O'Reilly, 2019.
[7] S. Zeuch et al., "Analyzing Efficient Stream Processing on Modern Hardware," VLDB, 2019.
[8] Eclipse, "Streamsheets" / edge stream materials.
[9] T. Akidau et al., "The Dataflow Model," VLDB, 2015.
[10] P. Carbone et al., "State Management in Apache Flink," VLDB, 2017.
[11] Apache Flink, "Checkpointing," documentation.
[12] Apache Flink, "Table mini-batch aggregation," documentation.
