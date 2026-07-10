---
schema_version: '1.0'
id: edge-database-sqlite-duckdb
title: 边缘数据库：SQLite 与 DuckDB 实战
layer: 4
content_type: UNKNOWN
difficulty: intermediate
reading_time: 18
prerequisites: UNKNOWN
tags: []
source_status: UNVERIFIED
review_status: UNREVIEWED
last_reviewed: UNKNOWN
---
# 边缘数据库：SQLite 与 DuckDB 实战

> **难度**：🟡 中级 | **领域**：嵌入式数据库、时序数据、边缘分析 | **阅读时间**：约 18 分钟

## 日常类比

如果把数据库比作图书馆，传统的云端数据库（PostgreSQL、MySQL）就像一座大型市立图书馆——藏书丰富、服务齐全，但你每次借书都要坐公交去一趟。SQLite 像是你书桌上的小书架——就在手边，拿取极快，能放几百本常用书。DuckDB 则像一个专门的杂志架——不是一本本翻找，而是能同时扫描一整排杂志的某一栏目（列式存储），特别适合统计分析。

在边缘计算场景中，设备常常处于弱网或离线状态，不能每笔数据都上传云端。嵌入式数据库让数据就地存储、就地查询，只在网络恢复时才批量同步。SQLite 适合稳定的行级读写（传感器日志），DuckDB 适合就地做分析聚合（边缘 BI）。

## 1. 为什么边缘需要嵌入式数据库

### 1.1 边缘数据挑战

| 挑战 | 说明 | 数据库需求 |
|------|------|-----------|
| 网络不稳定 | 4G/WiFi 可能断连数小时 | 本地持久化 |
| 资源受限 | 64MB-4GB RAM | 低内存占用 |
| 高写入频率 | 每秒数百到数千条传感器记录 | 高效写入 |
| 本地查询 | 异常检测、边缘分析 | 查询能力 |
| 数据同步 | 恢复联网后上传 | 增量同步支持 |
| 无 DBA | 部署即运行，零运维 | 零配置 |

### 1.2 嵌入式 vs 客户端-服务器

```
客户端-服务器模型 (PostgreSQL/MySQL):
App --> TCP连接 --> 数据库进程 --> 磁盘
         (需要网络、进程管理、认证...)

嵌入式模型 (SQLite/DuckDB):
App --> 函数调用 --> 数据库库 --> 文件
         (同一进程、零延迟、零配置)
```

## 2. SQLite：行存引擎的边缘王者

### 2.1 架构特点

SQLite 的设计哲学是"做好一件事"——可靠的本地数据存储：

- 单文件数据库（整个数据库就是一个 .db 文件）
- 零配置（无需安装、启动、管理）
- 事务安全（ACID，即使断电也不丢数据）
- 库大小仅约 600KB（静态链接后）
- 每秒可写入 5-10 万条记录（WAL 模式）

### 2.2 WAL 模式配置

对于 IoT 高频写入场景，Write-Ahead Logging 模式是必须的：

```python
import sqlite3
import time

# 连接并优化配置
conn = sqlite3.connect('/data/sensors.db')
conn.execute("PRAGMA journal_mode=WAL")        # WAL 模式：读写不互斥
conn.execute("PRAGMA synchronous=NORMAL")       # 平衡安全与速度
conn.execute("PRAGMA cache_size=-64000")        # 64MB 缓存
conn.execute("PRAGMA mmap_size=268435456")      # 256MB mmap
conn.execute("PRAGMA temp_store=MEMORY")        # 临时表在内存

# 创建传感器数据表
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

# 批量写入（比逐条快 100 倍）
def batch_insert(readings):
    conn.executemany(
        "INSERT INTO readings VALUES (?, ?, ?, ?, ?)",
        readings
    )
    conn.commit()

# 性能测试：批量写入 10 万条
readings = [
    (int(time.time()) + i, f"dev-{i % 100:03d}", 25.0 + i*0.01, 60.0, 95)
    for i in range(100000)
]
start = time.time()
batch_insert(readings)
elapsed = time.time() - start
print(f"100K inserts: {elapsed:.2f}s ({100000/elapsed:.0f} rows/sec)")
# 典型输出: 100K inserts: 0.85s (117647 rows/sec)
```

### 2.3 时序数据模式

传感器数据本质是时序数据，SQLite 中的最佳实践：

```sql
-- 按天分区（每天一个数据库文件，便于归档和清理）
-- main.db 只存最近 7 天
-- archive/ 目录存历史按天文件

-- 使用 ATTACH 跨文件查询
ATTACH DATABASE '/data/archive/2024-12-01.db' AS day1;
SELECT avg(temperature) FROM day1.readings WHERE device_id = 'dev-001';

-- 降采样查询（1 分钟粒度）
SELECT
    (timestamp / 60) * 60 AS minute,
    device_id,
    avg(temperature) AS avg_temp,
    max(temperature) AS max_temp,
    min(temperature) AS min_temp,
    count(*) AS sample_count
FROM readings
WHERE timestamp > unixepoch() - 3600  -- 最近一小时
GROUP BY minute, device_id;
```

## 3. DuckDB：列存分析引擎

### 3.1 为什么需要列式存储

行存（SQLite）vs 列存（DuckDB）的区别：

```
行存 (适合 OLTP - 逐条读写):
| ts | device | temp | humid | battery |
| 1  | dev-01 | 25.1 | 60.2  | 95      |  <- 整行连续存储
| 2  | dev-01 | 25.3 | 59.8  | 94      |
| 3  | dev-02 | 24.7 | 61.1  | 88      |

列存 (适合 OLAP - 聚合分析):
ts:      [1, 2, 3, ...]        <- 同列连续存储
device:  [dev-01, dev-01, dev-02, ...]
temp:    [25.1, 25.3, 24.7, ...]  <- 压缩率高、SIMD 加速
humid:   [60.2, 59.8, 61.1, ...]
battery: [95, 94, 88, ...]
```

对于 "过去24小时所有设备的平均温度" 这类查询，列存只需要读 temp 列和 ts 列，不碰其他列，磁盘 I/O 减少 60-80%。

### 3.2 DuckDB 边缘分析实战

```python
import duckdb

# DuckDB 同样是嵌入式、零配置
conn = duckdb.connect('/data/analytics.duckdb')

# 创建分析表
conn.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        timestamp TIMESTAMP NOT NULL,
        device_id VARCHAR NOT NULL,
        temperature DOUBLE,
        humidity DOUBLE,
        pressure DOUBLE
    )
""")

# 从 SQLite 导入数据（DuckDB 原生支持读 SQLite）
conn.execute("""
    INSERT INTO sensor_data
    SELECT
        to_timestamp(timestamp) as timestamp,
        device_id, temperature, humidity, NULL as pressure
    FROM sqlite_scan('/data/sensors.db', 'readings')
    WHERE timestamp > epoch(now()) - 86400
""")

# 复杂分析查询（DuckDB 的强项）
result = conn.execute("""
    WITH hourly AS (
        SELECT
            date_trunc('hour', timestamp) AS hour,
            device_id,
            avg(temperature) AS avg_temp,
            stddev(temperature) AS std_temp,
            count(*) AS samples
        FROM sensor_data
        WHERE timestamp > now() - INTERVAL '24 hours'
        GROUP BY hour, device_id
    )
    SELECT
        device_id,
        hour,
        avg_temp,
        CASE WHEN avg_temp > (
            SELECT avg(avg_temp) + 2 * stddev(avg_temp) FROM hourly h2
            WHERE h2.device_id = hourly.device_id
        ) THEN 'ANOMALY' ELSE 'NORMAL' END AS status
    FROM hourly
    ORDER BY hour DESC, device_id
""").fetchdf()  # 返回 Pandas DataFrame

print(result)
```

### 3.3 性能对比

在 Raspberry Pi 4（4GB）上的基准测试，数据量 1000 万行传感器记录：

```
查询: SELECT device_id, avg(temp), max(temp), min(temp)
      FROM readings WHERE ts > X GROUP BY device_id

SQLite:    12.3 秒  (全表扫描，行存)
DuckDB:     0.8 秒  (向量化执行，列存)

查询: SELECT * FROM readings WHERE device_id = 'dev-001'
      ORDER BY ts DESC LIMIT 10

SQLite:     0.002 秒  (B-tree 索引命中)
DuckDB:     0.15 秒   (需要扫描列块)

写入: 逐条 INSERT 1000 条
SQLite:     0.05 秒   (行存优势)
DuckDB:     0.3 秒    (列存写放大)
```

结论：分析用 DuckDB，事务用 SQLite，二者可以互补。

## 4. 与专用时序数据库的对比

### 4.1 选型矩阵

| 维度 | SQLite | DuckDB | InfluxDB | TimescaleDB |
|------|--------|--------|----------|-------------|
| 部署模型 | 嵌入式 | 嵌入式 | 独立服务 | 独立服务 |
| 最低内存 | 1 MB | 50 MB | 256 MB | 512 MB |
| 磁盘大小 | 600 KB | 20 MB | 100 MB+ | 200 MB+ |
| 写入性能 | 10 万/s | 3 万/s | 50 万/s | 20 万/s |
| 分析查询 | 慢 | 快 | 中等 | 快 |
| 点查询 | 快 | 中等 | 快 | 快 |
| 压缩率 | 1x | 3-5x | 5-10x | 3-5x |
| ARM 支持 | 完美 | 良好 | 良好 | 需要 PostgreSQL |
| 运维复杂度 | 零 | 零 | 中等 | 高 |

### 4.2 何时选择什么

```
设备内存 < 128MB?
  --> 只能 SQLite

需要复杂分析但内存 > 256MB?
  --> SQLite(写入) + DuckDB(分析) 组合

有网络且团队有运维能力?
  --> InfluxDB 或 TimescaleDB

只需要简单告警（阈值检测）?
  --> SQLite + 应用层逻辑即可
```

## 5. 数据同步到云端

### 5.1 增量同步策略

```python
import sqlite3
import json
import requests
from datetime import datetime

class EdgeSyncer:
    def __init__(self, db_path, cloud_endpoint):
        self.conn = sqlite3.connect(db_path)
        self.endpoint = cloud_endpoint

        # 同步状态表
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                table_name TEXT PRIMARY KEY,
                last_synced_ts INTEGER DEFAULT 0
            )
        """)

    def get_unsynced_data(self, table, batch_size=1000):
        """获取未同步的数据"""
        row = self.conn.execute(
            "SELECT last_synced_ts FROM sync_state WHERE table_name=?",
            (table,)
        ).fetchone()
        last_ts = row[0] if row else 0

        rows = self.conn.execute(f"""
            SELECT * FROM {table}
            WHERE timestamp > ?
            ORDER BY timestamp
            LIMIT ?
        """, (last_ts, batch_size)).fetchall()

        return rows

    def sync_batch(self, table):
        """同步一批数据到云端"""
        rows = self.get_unsynced_data(table)
        if not rows:
            return 0

        # 压缩后上传
        payload = json.dumps(rows)
        try:
            resp = requests.post(
                f"{self.endpoint}/ingest/{table}",
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if resp.status_code == 200:
                last_ts = rows[-1][0]  # timestamp 是第一列
                self.conn.execute(
                    "INSERT OR REPLACE INTO sync_state VALUES (?, ?)",
                    (table, last_ts)
                )
                self.conn.commit()
                return len(rows)
        except requests.exceptions.RequestException:
            pass  # 网络不通，下次再试
        return 0
```

### 5.2 存储空间管理

```python
import os

class StorageManager:
    def __init__(self, db_path, max_size_mb=500):
        self.db_path = db_path
        self.max_size = max_size_mb * 1024 * 1024

    def check_and_cleanup(self):
        """检查空间，必要时清理已同步数据"""
        current_size = os.path.getsize(self.db_path)

        if current_size > self.max_size * 0.8:  # 80% 告警
            conn = sqlite3.connect(self.db_path)

            # 删除已同步且超过 7 天的数据
            conn.execute("""
                DELETE FROM readings
                WHERE timestamp < (
                    SELECT last_synced_ts FROM sync_state
                    WHERE table_name = 'readings'
                ) AND timestamp < unixepoch() - 7*86400
            """)
            conn.execute("VACUUM")  # 回收空间
            conn.commit()
```

## 6. 高级模式

### 6.1 SQLite + DuckDB 混合架构

```python
# 最佳实践：SQLite 做写入缓冲，DuckDB 做分析
import sqlite3
import duckdb
import threading
import time

class HybridEdgeDB:
    def __init__(self):
        # SQLite: 高频写入 + 点查询
        self.write_db = sqlite3.connect(
            '/data/buffer.db', check_same_thread=False
        )
        self.write_db.execute("PRAGMA journal_mode=WAL")

        # DuckDB: 分析查询
        self.analytics_db = duckdb.connect('/data/analytics.duckdb')

        # 定期将 SQLite 数据迁移到 DuckDB
        self._start_migration_worker()

    def write(self, readings):
        """高频写入走 SQLite"""
        self.write_db.executemany(
            "INSERT INTO readings VALUES (?,?,?,?,?)", readings
        )
        self.write_db.commit()

    def analyze(self, query):
        """分析查询走 DuckDB"""
        return self.analytics_db.execute(query).fetchdf()

    def _migrate(self):
        """每 5 分钟将新数据从 SQLite 迁移到 DuckDB"""
        while True:
            time.sleep(300)
            self.analytics_db.execute("""
                INSERT INTO sensor_data
                SELECT * FROM sqlite_scan('/data/buffer.db', 'readings')
                WHERE timestamp > (
                    SELECT coalesce(max(epoch(timestamp)), 0)
                    FROM sensor_data
                )
            """)

    def _start_migration_worker(self):
        t = threading.Thread(target=self._migrate, daemon=True)
        t.start()
```

### 6.2 边缘 SQL 联邦查询

DuckDB 可以直接查询多种数据源：

```sql
-- 同时查询本地 SQLite、Parquet 文件、甚至远程 S3
SELECT
    s.device_id,
    s.avg_temp,
    m.device_name,
    m.location
FROM (
    SELECT device_id, avg(temperature) as avg_temp
    FROM sqlite_scan('/data/sensors.db', 'readings')
    GROUP BY device_id
) s
JOIN read_parquet('/data/device_metadata.parquet') m
    ON s.device_id = m.device_id;
```

## 7. 实践建议

### 7.1 初学者入门路径

1. 用 Python + sqlite3 标准库写一个传感器数据收集器
2. 对比 WAL 和默认 journal 模式的写入性能差异
3. 安装 DuckDB，对同样的数据做聚合分析，对比速度
4. 实现一个简单的边云同步模块
5. 在树莓派上部署完整的混合架构方案

### 7.2 具体调优建议

- **SQLite WAL 模式**：边缘场景必开，读写并发提升 10 倍
- **批量写入**：积攒 100-1000 条后一次性写入，不要逐条 commit
- **索引策略**：只建最常用的查询索引，多余索引拖慢写入
- **mmap**：对于读多写少的场景，开启 mmap_size 减少系统调用
- **DuckDB 内存限制**：设置 SET memory_limit 防止 OOM
- **VACUUM 定时**：定期执行或使用 auto_vacuum=INCREMENTAL

### 7.3 踩坑提醒

- SQLite 不支持真正的并发写（WAL 也只是减少了阻塞时间）
- DuckDB 不适合高频单条写入（设计为批量加载）
- 断电安全：SQLite PRAGMA synchronous=NORMAL 有极小概率丢最后一笔事务
- SD 卡寿命：频繁写入需考虑磨损均衡，建议用 F2FS 文件系统

## 参考文献

1. SQLite Project. "SQLite Documentation." 2024. https://sqlite.org/docs.html
2. Raasveldt, M., Muehleisen, H. "DuckDB: An Embeddable Analytical Database." SIGMOD 2019.
3. DuckDB Labs. "DuckDB Documentation." 2024. https://duckdb.org/docs/
4. Hipp, R. "SQLite: Past, Present, and Future." VLDB 2022.
5. Kersten, T., et al. "Everything You Always Wanted to Know About Compiled and Vectorized Queries." VLDB 2018.
6. InfluxData. "InfluxDB Edge vs SQLite for IoT." Technical Blog, 2024.
7. Pelkonen, T., et al. "Gorilla: A Fast, Scalable, In-Memory Time Series Database." VLDB 2015.
8. SQLite. "Write-Ahead Logging." https://sqlite.org/wal.html
9. DuckDB. "Querying SQLite databases." 2024. https://duckdb.org/docs/extensions/sqlite
10. Boncz, P., et al. "MonetDB/X100: Hyper-Pipelining Query Execution." CIDR 2005.
