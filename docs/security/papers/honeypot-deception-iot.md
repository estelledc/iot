# IoT 蜜罐与诱骗技术

> **难度**：🟡 中级 | **领域**：威胁情报、入侵检测 | **阅读时间**：约 18 分钟

## 日常类比

警察抓小偷有一种经典手法：在商场里放一个看起来很值钱但实际装了 GPS 追踪器的"诱饵包"。小偷偷走后，警察能追踪到他的窝点，还能了解他的作案手法。

蜜罐（Honeypot）就是网络安全领域的"诱饵包"。它伪装成一个真实的 IoT 设备（比如一个看起来有默认密码的摄像头），吸引攻击者来"偷"。攻击者的每一步操作都被详细记录：他用什么工具扫描、尝试什么密码、上传什么恶意软件。这些情报帮助防御者了解最新的攻击趋势，提前加固真实设备。

## 1. 蜜罐分类

### 1.1 按交互程度分类

| 类型 | 交互深度 | 复杂度 | 情报价值 | 风险 |
|------|---------|--------|---------|------|
| 低交互 | 模拟服务响应 | 低 | 扫描/探测数据 | 极低 |
| 中交互 | 模拟部分功能 | 中 | 攻击手法 | 低 |
| 高交互 | 真实或近真实系统 | 高 | 完整攻击链 | 中高 |

### 1.2 按部署目的分类

**研究型蜜罐**：
- 目标：收集攻击情报、研究新型威胁
- 部署位置：互联网直接暴露
- 典型用户：安全研究机构、CERT

**生产型蜜罐**：
- 目标：检测内网入侵、延缓攻击者
- 部署位置：企业内网、IoT 网段
- 典型用户：企业安全团队

### 1.3 IoT 蜜罐的特殊需求

- 模拟特定协议（Telnet、MQTT、CoAP、Modbus）
- 伪装设备指纹（banner、MAC 地址前缀）
- 模拟固件行为（BusyBox 命令集）
- 支持大规模部署（一台服务器模拟数百设备）

## 2. IoT 专用蜜罐系统

### 2.1 主流 IoT 蜜罐对比

| 蜜罐 | 交互级别 | 模拟协议 | 语言 | 维护状态 |
|------|---------|---------|------|---------|
| Cowrie | 中-高 | SSH/Telnet | Python | 活跃 |
| HoneyThing | 低-中 | TR-069/HTTP | Python | 停滞 |
| IoTPOT | 中 | Telnet(多架构) | C/Python | 研究项目 |
| Conpot | 中 | Modbus/S7/IPMI | Python | 活跃 |
| Dionaea | 中 | SMB/HTTP/FTP | Python/C | 活跃 |
| ThingPot | 低 | MQTT/CoAP/HTTP | Go | 研究项目 |

### 2.2 Cowrie 部署配置

```yaml
# docker-compose.yml - Cowrie IoT 蜜罐部署
version: '3.8'
services:
  cowrie:
    image: cowrie/cowrie:latest
    ports:
      - "2222:2222"   # SSH 蜜罐
      - "2223:2223"   # Telnet 蜜罐
    volumes:
      - ./cowrie-data:/cowrie/cowrie-git/var
      - ./cowrie.cfg:/cowrie/cowrie-git/etc/cowrie.cfg
    environment:
      - COWRIE_TELNET_ENABLED=yes
    restart: unless-stopped
  
  # ELK 日志分析
  elasticsearch:
    image: elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
  
  kibana:
    image: kibana:8.12.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

```ini
# cowrie.cfg - 模拟 IoT 设备配置
[honeypot]
hostname = DLink-Router
# 模拟 BusyBox 环境
shell = busybox

[telnet]
enabled = true
listen_port = 2223

# 设置弱密码吸引攻击者
[userdb]
# 格式: username:uid:password
root:0:admin
root:0:123456
admin:0:admin
support:0:support

# 模拟文件系统
[filesystem]
# 使用预制的 IoT 设备文件系统镜像
contents = share/cowrie/fs.pickle
```

### 2.3 MQTT 蜜罐实现

```python
# 简易 MQTT 蜜罐 - 记录所有连接和消息
import asyncio
import json
import logging
from datetime import datetime

class MQTTHoneypot:
    def __init__(self, host='0.0.0.0', port=1883):
        self.host = host
        self.port = port
        self.logger = logging.getLogger('mqtt_honeypot')
        self.connections = []
    
    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.logger.info(f"新连接: {addr}")
        
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'src_ip': addr[0],
            'src_port': addr[1],
            'protocol': 'mqtt',
            'events': []
        }
        
        try:
            while True:
                data = await asyncio.wait_for(
                    reader.read(4096), timeout=30.0
                )
                if not data:
                    break
                
                # 解析 MQTT 包类型
                pkt_type = (data[0] & 0xF0) >> 4
                event['events'].append({
                    'type': self._pkt_type_name(pkt_type),
                    'raw_hex': data.hex()[:200],
                    'time': datetime.utcnow().isoformat()
                })
                
                # 对 CONNECT 包回复 CONNACK（接受连接）
                if pkt_type == 1:  # CONNECT
                    connack = bytes([0x20, 0x02, 0x00, 0x00])
                    writer.write(connack)
                    await writer.drain()
                
                # 对 SUBSCRIBE 回复 SUBACK
                elif pkt_type == 8:  # SUBSCRIBE
                    msg_id = data[2:4]
                    suback = bytes([0x90, 0x03]) + msg_id + bytes([0x00])
                    writer.write(suback)
                    await writer.drain()
                    
        except asyncio.TimeoutError:
            pass
        finally:
            # 记录完整会话
            self._save_event(event)
            writer.close()
    
    def _pkt_type_name(self, pkt_type):
        names = {1: 'CONNECT', 3: 'PUBLISH', 8: 'SUBSCRIBE',
                 12: 'PINGREQ', 14: 'DISCONNECT'}
        return names.get(pkt_type, f'UNKNOWN({pkt_type})')
    
    def _save_event(self, event):
        with open('mqtt_honeypot.jsonl', 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    async def start(self):
        server = await asyncio.start_server(
            self.handle_client, self.host, self.port
        )
        self.logger.info(f"MQTT 蜜罐启动: {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
```

## 3. 诱骗技术（Deception Technology）

### 3.1 超越传统蜜罐

现代诱骗技术不只是单个蜜罐，而是构建完整的"虚假网络"：

```
真实网络                    诱骗层
┌──────────┐              ┌──────────────────┐
│ 真实设备  │              │ 虚假设备 (蜜罐)   │
│ 10.0.1.x │              │ 10.0.2.x         │
├──────────┤              ├──────────────────┤
│ 真实服务  │              │ 虚假服务          │
│ MQTT真实  │              │ MQTT蜜罐          │
├──────────┤              ├──────────────────┤
│ 真实数据  │              │ 诱饵数据          │
│ 传感器值  │              │ 假传感器值        │
└──────────┘              └──────────────────┘
         ↑                         ↑
         │    攻击者无法区分         │
         └─────────────────────────┘
```

### 3.2 诱饵类型

| 诱饵 | 描述 | 检测信号 |
|------|------|---------|
| 蜜罐设备 | 模拟 IoT 设备 | 任何连接即告警 |
| 蜜令牌 | 假的 API Key/密码 | 使用即告警 |
| 蜜文件 | 假的配置文件 | 访问即告警 |
| 蜜网段 | 未使用的 IP 段 | 任何流量即告警 |
| 蜜 DNS | 假的内部域名 | 解析即告警 |

### 3.3 IoT 网络中的诱骗部署

```python
# 自动化诱骗部署脚本
import ipaddress
import subprocess

class IoTDeceptionDeployer:
    def __init__(self, network='10.0.1.0/24'):
        self.network = ipaddress.ip_network(network)
        self.decoys = []
    
    def deploy_fake_devices(self, count=20):
        """在网络中部署虚假 IoT 设备"""
        # 找出未使用的 IP
        used_ips = self._scan_active_ips()
        available = [ip for ip in self.network.hosts() 
                     if str(ip) not in used_ips]
        
        for ip in available[:count]:
            decoy = {
                'ip': str(ip),
                'type': self._random_device_type(),
                'services': []
            }
            
            # 配置虚假 ARP 响应
            self._setup_arp_response(ip, decoy['type'])
            
            # 启动对应服务
            if decoy['type'] == 'camera':
                decoy['services'] = ['rtsp:554', 'http:80']
            elif decoy['type'] == 'plc':
                decoy['services'] = ['modbus:502', 'http:80']
            elif decoy['type'] == 'sensor':
                decoy['services'] = ['mqtt:1883', 'coap:5683']
            
            self.decoys.append(decoy)
        
        return self.decoys
    
    def _random_device_type(self):
        import random
        return random.choice(['camera', 'plc', 'sensor', 
                            'gateway', 'thermostat'])
```

## 4. 威胁情报收集

### 4.1 数据收集维度

| 维度 | 收集内容 | 分析价值 |
|------|---------|---------|
| 网络层 | 源 IP、扫描模式、端口序列 | 攻击基础设施识别 |
| 认证层 | 用户名/密码组合 | 凭证字典更新 |
| 载荷层 | 恶意软件样本、脚本 | 恶意软件分析 |
| 行为层 | 命令序列、横向移动 | TTPs 提取 |
| 时间层 | 攻击时间分布 | 攻击者画像 |

### 4.2 攻击者行为分析

基于 2024 年 IoT 蜜罐数据的典型攻击模式：

```
阶段 1: 扫描 (0-5 秒)
  → Shodan/Censys 风格的 banner 抓取
  → 目标: Telnet(23), SSH(22), HTTP(80/8080)

阶段 2: 暴力破解 (5-60 秒)
  → Top 10 密码: admin/admin, root/root, 
    admin/123456, root/vizxv, default/default
  → 平均尝试 15-30 组凭证

阶段 3: 初始访问 (1-5 分钟)
  → 执行 uname -a, cat /proc/cpuinfo
  → 确认架构 (MIPS/ARM/x86)

阶段 4: 载荷投递 (5-10 分钟)
  → wget/curl 下载恶意二进制
  → 或通过 echo + base64 写入
  → 主要: Mirai 变种, 挖矿程序

阶段 5: 持久化 (10+ 分钟)
  → 修改 crontab
  → 替换系统二进制
  → 清除日志
```

### 4.3 情报输出格式（STIX）

```json
{
  "type": "indicator",
  "spec_version": "2.1",
  "id": "indicator--a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created": "2025-01-15T08:00:00Z",
  "name": "Mirai Variant C2 Server",
  "pattern": "[ipv4-addr:value = '185.220.101.xxx']",
  "pattern_type": "stix",
  "valid_from": "2025-01-15T08:00:00Z",
  "labels": ["malicious-activity"],
  "description": "IoT 蜜罐捕获的 Mirai 变种 C2 通信地址"
}
```

## 5. 部署架构

### 5.1 分布式蜜罐网络

```
                    ┌─────────────────┐
                    │  中央分析平台    │
                    │  (SIEM/ELK)     │
                    └────────┬────────┘
                             │ VPN/加密通道
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────┴──┐  ┌───────┴────┐  ┌─────┴───────┐
    │ 节点 A     │  │ 节点 B     │  │ 节点 C      │
    │ 云服务器   │  │ 家庭网络   │  │ 工业网络    │
    │ 公网 IP    │  │ NAT 后     │  │ 隔离网段    │
    ├────────────┤  ├────────────┤  ├─────────────┤
    │ Cowrie     │  │ MQTT蜜罐   │  │ Conpot      │
    │ HTTP蜜罐  │  │ CoAP蜜罐   │  │ Modbus蜜罐  │
    │ Telnet蜜罐│  │ UPnP蜜罐   │  │ S7comm蜜罐  │
    └────────────┘  └────────────┘  └─────────────┘
```

### 5.2 安全隔离

```bash
# 使用 Docker 网络隔离蜜罐
# 蜜罐只能向外发送日志，不能访问内网

# 创建隔离网络
docker network create --internal honeypot-internal
docker network create honeypot-external

# 蜜罐容器：只连接外部网络（接收攻击）
docker run --network honeypot-external \
  --cap-drop ALL \
  --read-only \
  --memory 256m \
  --cpus 0.5 \
  cowrie/cowrie

# 日志收集器：桥接两个网络
docker run --network honeypot-internal \
  --network honeypot-external \
  filebeat
```

## 6. 法律与伦理考量

### 6.1 法律风险

| 问题 | 说明 | 建议 |
|------|------|------|
| 引诱犯罪 | 蜜罐是否构成"钓鱼执法" | 被动等待，不主动引诱 |
| 数据隐私 | 记录攻击者 IP 是否侵犯隐私 | 遵循当地数据保护法 |
| 跨境问题 | 攻击者来自其他国家 | 与 CERT 合作 |
| 恶意软件存储 | 收集的样本是否合法持有 | 安全存储，限制访问 |

### 6.2 最佳实践

- 在公司法务审核后部署
- 不主动向攻击者发送数据
- 日志保留期限符合法规要求
- 与行业 ISAC 共享情报时脱敏处理

## 7. 实践建议

### 7.1 初学者入门路径

1. 在虚拟机中部署 Cowrie，观察 24 小时内的攻击
2. 分析日志：统计 Top 10 密码、攻击来源国
3. 部署 T-Pot（集成多种蜜罐的一体化平台）
4. 编写自定义 MQTT/CoAP 蜜罐
5. 将蜜罐数据接入 ELK 做可视化分析

### 7.2 具体调优建议

**提高真实度**：
- 使用真实设备的 banner 和指纹（从 Shodan 收集）
- 模拟真实的响应延迟（不要太快）
- 添加"正常"的背景流量
- 定期更新模拟的固件版本号

**降低误报**：
- 白名单内部扫描器 IP
- 区分自动化扫描和人工攻击
- 设置告警阈值（单次连接不告警，持续攻击才告警）

**规模化部署**：
- 使用 T-Pot 或 MHN（Modern Honey Network）统一管理
- 每个网段至少部署 2-3 个蜜罐
- 混合不同类型（SSH + MQTT + HTTP）
- 定期轮换 IP 和设备类型

## 参考文献

1. Pa, Y.M.P. et al. "IoTPOT: A Novel Honeypot for Revealing Current IoT Threats." Journal of Information Processing, 2016.
2. Oosterhof, M. "Cowrie SSH/Telnet Honeypot." GitHub, 2024.
3. Vetterl, A. & Clayton, R. "Bitter Harvest: Systematically Fingerprinting Low- and Medium-interaction Honeypots." USENIX WOOT, 2018.
4. Luo, T. et al. "IoTCandyJar: Towards an Intelligent-Interaction IoT Honeypot." Black Hat USA, 2017.
5. T-Pot Project. "T-Pot: The All In One Multi Honeypot Platform." GitHub/Telekom Security, 2024.
6. MITRE ATT&CK. "ICS Techniques." 2024.
7. Conpot Team. "Conpot: ICS/SCADA Honeypot." Documentation, 2024.
8. Dowling, S. et al. "A ZigBee Honeypot to Assess IoT Cyberattack Behaviour." IEEE PIMRC, 2017.
9. Hakim, M.S. et al. "A Survey on IoT Honeypots: Techniques, Threats, and Opportunities." IEEE Access, 2023.
10. Spitzner, L. "Honeypots: Tracking Hackers." Addison-Wesley, 2003.
