---
schema_version: '1.0'
id: edge-database-sqlite-duckdb
title: 边缘数据库：SQLite 与 DuckDB 实战
layer: 4
content_type: comparison
difficulty: intermediate
reading_time: 18
prerequisites:
  - edge-computing-survey
  - edge-storage-minio-ceph
tags:
- SQLite
- DuckDB
- 嵌入式数据库
- 列存
- WAL
- 边缘分析
- 时序数据
source_status: VERIFIED
review_status: HUMAN_APPROVED
last_reviewed: '2026-07-10'
---
# 边缘数据库：SQLite 与 DuckDB 实战

> **难度**：🟡 中级 | **领域**：嵌入式数据库、时序数据、边缘分析 | **阅读时间**：约 18 分钟

## 日常类比

云端库（PostgreSQL、MySQL）像市立图书馆：功能全，但每次借书都要出门。SQLite（Structured Query Language Lite）像书桌上的小书架——同进程、零配置、行级读写快。DuckDB 像杂志架：列式（columnar）排布，适合一次扫一整栏做统计。弱网/离线时，数据先落本地，再批量上云；事务写走 SQLite，聚合分析走 DuckDB。

## 摘要

对比嵌入式行存（SQLite）与列存分析引擎（DuckDB）在边缘的分工：WAL（Write-Ahead Logging）写入、时序分区、`sqlite_scan` 联邦、边云增量同步。吞吐与延迟数字多为公开文档或单机示意量级，须在目标板复测[1][2][3]。

## 1 为何边缘需要嵌入式库

| 挑战 | 说明 | 库侧需求 |
|------|------|----------|
| 网络不稳 | 断连可达数小时 | 本地持久化 |
| 资源受限 | 约数十 MB–数 GB RAM | 低内存占用 |
| 高频写入 | 传感器可达数百–数千条/s 量级 | 批量/WAL |
| 本地查询 | 异常检测、边缘 BI | SQL 能力 |
| 无 DBA | 部署即跑 | 零配置 |

```
客户端-服务器 (PostgreSQL/MySQL):
App → TCP → 独立进程 → 磁盘

嵌入式 (SQLite/DuckDB):
App → 函数调用 → 同进程库 → 文件
```

## 2 SQLite：行存与 WAL

### 2.1 设计要点

- 单文件 `.db`；零配置；ACID（Atomicity, Consistency, Isolation, Durability）事务[1][4]
- 静态链接库体积约数百 KB 量级[1]
- WAL 下读写可并发；批量 `executemany` 远快于逐条 `commit`[8]

未引用板级数字时，勿把「每秒数万行」当承诺——介质（eMMC/SD/NVMe）与 `synchronous` 档位主导结果。

### 2.2 边缘常用 PRAGMA

```python
import sqlite3

conn = sqlite3.connect('/data/sensors.db')
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")  # FULL 更安全、更慢
conn.execute("PRAGMA cache_size=-64000")    # 负值：KB 为单位
conn.execute("PRAGMA mmap_size=268435456")
conn.execute("PRAGMA temp_store=MEMORY")

conn.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        timestamp INTEGER NOT NULL,
        device_id TEXT NOT NULL,
        temperature REAL,
        humidity REAL,
        battery_pct INTEGER,
        PRIMARY KEY (timestamp, device_id)
    ) WITHOUT ROWID
""")

def batch_insert(readings):
    conn.executemany(
        "INSERT INTO readings VALUES (?, ?, ?, ?, ?)",
        readings
    )
    conn.commit()
```

### 2.3 时序实践

按天拆文件便于归档；`ATTACH` 跨库查询；降采样用整数桶：

```sql
ATTACH DATABASE '/data/archive/2024-12-01.db' AS day1;
SELECT avg(temperature) FROM day1.readings WHERE device_id = 'dev-001';

SELECT
    (timestamp / 60) * 60 AS minute,
    device_id,
    avg(temperature) AS avg_temp,
    count(*) AS sample_count
FROM readings
WHERE timestamp > unixepoch() - 3600
GROUP BY minute, device_id;
```

## 3 DuckDB：列存分析

### 3.1 行存 vs 列存

| 形态 | 适合 | 机制 |
|------|------|------|
| 行存（SQLite） | OLTP（Online Transaction Processing）点查/写入 | 整行连续 |
| 列存（DuckDB） | OLAP（Online Analytical Processing）聚合 | 同列连续、易压缩与 SIMD（Single Instruction Multiple Data）[2][5][10] |

「只读温度与时间戳」类查询，列存可显著少读无关列；具体 I/O 降幅视列宽与选择性而定，不宜写死百分比。

### 3.2 从 SQLite 导入并分析

```python
import duckdb

conn = duckdb.connect('/data/analytics.duckdb')
conn.execute("""
    INSERT INTO sensor_data
    SELECT
        to_timestamp(timestamp) AS timestamp,
        device_id, temperature, humidity, NULL AS pressure
    FROM sqlite_scan('/data/sensors.db', 'readings')
    WHERE timestamp > epoch(now()) - 86400
""")
```

DuckDB 原生可读 SQLite/Parquet，适合边缘联邦查询[3][9]。

### 3.3 互补关系（示意）

| 负载 | SQLite 倾向 | DuckDB 倾向 |
|------|-------------|-------------|
| 逐条/小批量 INSERT | 优 | 写放大更明显 |
| 按主键点查 | B-tree 友好 | 常需扫列块 |
| `GROUP BY` 聚合 | 全表行扫偏慢 | 向量化执行更强 |

公开基准与自测（如树莓派级）仅作量级参考，跨版本/介质不可直接外推[2][5]。

## 4 与专用时序库选型

| 维度 | SQLite | DuckDB | InfluxDB | TimescaleDB |
|------|--------|--------|----------|-------------|
| 部署 | 嵌入式 | 嵌入式 | 独立服务 | 独立服务（PostgreSQL） |
| 内存门槛量级 | 很低（MB 级） | 数十 MB 起更舒适 | 数百 MB 量级 | 更高 |
| 写入 | 批量+WAL 强 | 偏批量加载 | 时序写入优化 | 时序扩展 |
| 分析 SQL | 一般 | 强 | 中（方言） | 强 |
| 运维 | 零 | 零 | 中 | 较高 |

```
RAM 极紧 → SQLite
要复杂分析且内存尚可 → SQLite 写 + DuckDB 读
有运维与独立进程预算 → Influx / Timescale
仅阈值告警 → SQLite + 应用逻辑
```

## 5 边云同步与空间治理

增量水位表 + 批量 POST；失败保留水位、下次重试。清理仅删「已同步且超保留期」行，再 `VACUUM`/`auto_vacuum`。SD 卡场景优先考虑磨损与文件系统（如 F2FS），避免无节制小写[1][8]。

混合架构：SQLite 作写入缓冲，定时 `sqlite_scan` 迁入 DuckDB；分析查询不打写入路径。

## 6 局限、挑战与可改进方向

### 1. 单写者与并发上限

**局限**：SQLite 写锁语义下，多进程高频写仍易排队；WAL 改善读并发，不变成多主库[8]。
**改进**：单写进程 + 队列；或按设备/天分库；写压过大再评估轻量服务端库。

### 2. DuckDB 不适合高频单条写

**局限**：列存追加与压缩对「每条一事务」不友好。
**改进**：应用侧攒批；或 SQLite 缓冲再迁移；设置 `memory_limit` 防 OOM（Out Of Memory）。

### 3. 断电与 `synchronous` 权衡

**局限**：`NORMAL` 相对 `FULL` 有更小窗口的尾事务风险[1]。
**改进**：关键水位/账本表用更严同步；UPS（Uninterruptible Power Supply）或电容掉电保护；定期完整性检查。

### 4. 介质寿命与 VACUUM

**局限**：高频写 + 全量 `VACUUM` 放大 SD/eMMC 磨损。
**改进**：增量 vacuum、按天文件丢弃代替大删除、热数据放更高耐久介质。

## 7 实践要点

1. 先测 WAL vs delete journal 的写入曲线。
2. 批量 10²–10³ 行再提交，避免逐条 commit。
3. 索引只保留高频点查路径。
4. DuckDB 分析前设内存上限。
5. 同步水位与业务表同一事务语义边界要清晰（至少崩溃后可重传）。

## 参考文献

[1] SQLite Project, "SQLite Documentation," https://sqlite.org/docs.html
[2] M. Raasveldt, H. Mühleisen, "DuckDB: An Embeddable Analytical Database," SIGMOD, 2019.
[3] DuckDB Labs, "DuckDB Documentation," https://duckdb.org/docs/
[4] R. Hipp, "SQLite: Past, Present, and Future," VLDB, 2022.
[5] T. Kersten et al., "Everything You Always Wanted to Know About Compiled and Vectorized Queries," VLDB, 2018.
[6] InfluxData, "InfluxDB for IoT / Edge," technical materials, 2024.
[7] T. Pelkonen et al., "Gorilla: A Fast, Scalable, In-Memory Time Series Database," VLDB, 2015.
[8] SQLite, "Write-Ahead Logging," https://sqlite.org/wal.html
[9] DuckDB, "SQLite Scanner Extension," https://duckdb.org/docs/extensions/sqlite
[10] P. Boncz et al., "MonetDB/X100: Hyper-Pipelining Query Execution," CIDR, 2005.
[11] Timescale, "TimescaleDB Documentation," 2024.
[12] DuckDB, "Persistence and Insert Performance," documentation, 2024.
