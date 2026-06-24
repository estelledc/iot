# Zigbee OTA固件升级机制与实现
> **难度**：🟡 中级 | **领域**：Zigbee设备管理 | **阅读时间**：约 20 分钟

## 引言

想象你有一台手机，系统提示有新版本可以更新，点击下载几分钟就完成了。但如果这台"手机"是一个只有256KB闪存、通过250kbps无线链路连接的温度传感器呢? 下载100KB固件可能需要35分钟，而且中途不能断电，否则设备可能变砖。

这就是 Zigbee OTA(Over-The-Air)固件升级面临的挑战。设备部署后可能运行数年，期间需要修复安全漏洞、添加新功能、修正bug，但无线升级必须在极低带宽、有限存储和不可靠链路的约束下可靠完成。

## 1. OTA升级的必要性与挑战

### 1.1 为什么需要无线升级

物联网设备一旦部署，物理接触变得困难或不可能:

- 安全补丁: 发现漏洞后需快速修复，不能等设备回收
- 功能迭代: 新标准特性需固件支持(如Matter桥接)
- Bug修复: 现场发现的问题需远程修复
- 合规更新: 无线电法规变化可能要求调整发射参数
- 互操作性: 与新设备的兼容性问题需固件适配

### 1.2 核心挑战

| 挑战 | 具体问题 |
|------|----------|
| 带宽限制 | 250kbps共享带宽，实际可用远低于此 |
| 存储限制 | MCU闪存128-512KB，需存储新旧固件 |
| 可靠性 | 升级失败不能变砖，必须可回滚 |
| 网络影响 | 大量数据传输不能阻塞正常业务流量 |
| 电池设备 | 休眠设备的升级需特殊处理 |
| 安全性 | 防止恶意固件被注入设备 |

## 2. ZCL OTA升级集群

### 2.1 角色定义

ZCL OTA Upgrade Cluster(集群ID: 0x0019)标准化了固件升级流程:

- OTA Server: 持有固件镜像，提供下载服务(通常是网关/协调器)
- OTA Client: 需要升级的设备，主动查询和下载固件

### 2.2 关键属性

OTA Client 维护的关键属性:

| 属性ID | 名称 | 说明 |
|--------|------|------|
| 0x0000 | UpgradeServerID | OTA Server的IEEE地址 |
| 0x0001 | FileOffset | 当前下载偏移量 |
| 0x0002 | CurrentFileVersion | 当前固件版本号 |
| 0x0006 | ImageUpgradeStatus | 升级状态 |
| 0x0007 | ManufacturerID | 制造商ID |

### 2.3 集群命令

```
Client -> Server:
  - Query Next Image Request: 查询是否有可用更新
  - Image Block Request: 请求固件数据块
  - Upgrade End Request: 通知下载完成/失败

Server -> Client:
  - Query Next Image Response: 回复镜像信息或无更新
  - Image Block Response: 返回请求的数据块
  - Upgrade End Response: 指示何时应用更新
```

## 3. OTA Server实现

### 3.1 镜像管理

```python
# OTA Server镜像管理伪代码
class OTAImageStore:
    def __init__(self):
        self.images = {}  # key: (manufacturer_id, image_type, version)

    def add_image(self, image_file):
        header = parse_ota_header(image_file)
        key = (header.manufacturer_id, header.image_type, header.file_version)
        self.images[key] = image_file

    def query_next_image(self, manufacturer_id, image_type, current_version):
        candidates = [
            (ver, img) for (mfr, typ, ver), img in self.images.items()
            if mfr == manufacturer_id and typ == image_type
            and ver > current_version
        ]
        if candidates:
            return max(candidates, key=lambda x: x[0])[1]
        return None  # 无可用更新
```

### 3.2 流量控制

Server 需控制 OTA 流量避免网络拥塞: 限制同时升级设备数(如最多3个并行)、设置块请求最小间隔(如每秒1个块)、业务高峰期暂停传输、正常业务流量优先于OTA流量。

## 4. 镜像发现流程

### 4.1 查询机制

OTA Client 周期性查询 Server 是否有新版本(通常24小时间隔):

```
Client                              Server
  |--- Query Next Image Request ------>|
  |    (ManufacturerID, ImageType,     |
  |     CurrentVersion, HW Version)    |
  |                                    |
  |<-- Query Next Image Response ------|
  |    (Status, ImageSize, Version)    |
  |    或 (NO_IMAGE_AVAILABLE)         |
```

### 4.2 版本判断逻辑

Server 检查: 版本号必须更高、硬件版本兼容、可选的灰度发布策略(按设备百分比逐步推送)。只有满足所有条件才返回可用镜像信息。

## 5. 镜像下载过程

### 5.1 分块下载

固件镜像被分成小块逐一传输:

```
Client                              Server
  |--- Image Block Request ---------->|
  |    (Offset=0, BlockSize=64)        |
  |<-- Image Block Response -----------|
  |    (Data[0:63])                    |
  |                                    |
  |--- Image Block Request ---------->|
  |    (Offset=64, BlockSize=64)       |
  |<-- Image Block Response -----------|
  |    (Data[64:127])                  |
  |                                    |
  |    ... 重复直到整个镜像下载完成 ... |
```

### 5.2 下载速率计算

块大小受ZCL帧最大载荷限制(约82字节)，常用48-64字节:

| 镜像大小 | 理论时间(480B/s) | 实际时间(含开销) |
|----------|------------------|------------------|
| 64KB | 约2.2分钟 | 约3-4分钟 |
| 128KB | 约4.4分钟 | 约7-10分钟 |
| 256KB | 约8.9分钟 | 约15-20分钟 |
| 512KB | 约17.8分钟 | 约30-40分钟 |

### 5.3 断点续传

下载可能因网络故障或设备重启中断，OTA协议支持断点续传:

```python
class OTAClient:
    def resume_download(self):
        offset = load_from_nvm("ota_offset")  # 从非易失存储读取
        if offset > 0 and offset < self.image_size:
            self.current_offset = offset  # 从中断位置继续
        self.request_next_block()

    def on_block_received(self, offset, data):
        write_to_storage(offset, data)
        self.current_offset = offset + len(data)
        save_to_nvm("ota_offset", self.current_offset)
        if self.current_offset >= self.image_size:
            self.verify_image()
        else:
            self.request_next_block()
```

## 6. 镜像验证

### 6.1 验证步骤

下载完成后 Client 必须验证镜像完整性:

1. CRC校验: 计算整个镜像的CRC32，与头部记录比对
2. 大小校验: 实际接收字节数与头部声明一致
3. 签名验证: 使用预置公钥验证镜像签名(安全关键)

### 6.2 签名机制

```
制造商侧(构建时):
  编译固件 -> 计算SHA-256哈希 -> 私钥签名(ECDSA-P256) -> 附加到镜像

设备侧(下载后):
  提取签名 -> 计算接收固件哈希 -> 公钥验证
  有效 -> 允许应用
  无效 -> 丢弃镜像，报告错误，设备继续运行当前固件
```

## 7. Bootloader与固件应用

### 7.1 存储架构

```
方案A - 双Bank内部Flash:
  +------------------+------------------+
  | Bank 0 (Active)  | Bank 1 (Download)|
  +------------------+------------------+
  优点: 切换快速，无需外部存储
  缺点: 可用Flash减半，成本较高

方案B - 外部SPI Flash:
  内部Flash:          外部SPI Flash:
  +----------------+  +------------------+
  | 当前运行固件   |  | 下载的新固件     |
  +----------------+  +------------------+
  优点: 内部Flash全部可用
  缺点: 需额外硬件，复制时间长
```

### 7.2 固件应用流程

1. 镜像验证通过
2. Client发送Upgrade End Request(status=SUCCESS)
3. Server回复Upgrade End Response(含应用时间)
4. 到达指定时间: 设备进入Bootloader
5. Bootloader二次验证新镜像
6. 双Bank: 切换活动Bank标志; 外部Flash: 复制到内部
7. 重启进入新固件，执行自检
8. 自检通过确认成功; 失败则回滚

### 7.3 回滚机制

```python
# Bootloader回滚逻辑
def bootloader_main():
    if new_image_pending():
        set_boot_flag(TRYING_NEW)
        boot_new_image()
    elif get_boot_flag() == TRYING_NEW:
        # 上次尝试新固件后异常重启 = 新固件有问题
        set_boot_flag(ROLLBACK)
        boot_old_image()
    else:
        boot_current_image()

# 新固件启动后确认
def application_startup():
    if get_boot_flag() == TRYING_NEW:
        if self_test_passed():
            set_boot_flag(CONFIRMED)  # 确认OK
        else:
            trigger_reboot()  # 触发回滚
```

## 8. 终端设备(休眠设备)的OTA

### 8.1 特殊挑战

休眠终端设备大部分时间无法接收数据，每次唤醒只能处理少量数据，下载时间被极大延长，电池消耗显著增加。

### 8.2 升级策略对比

```
策略A - 临时提高轮询频率:
  正常30秒 -> OTA期间1秒
  效果: 速度接近路由器设备
  代价: 电池消耗增加30倍

策略B - 利用正常轮询周期:
  每次轮询获取一个块，间隔30秒，每块48字节
  256KB镜像: 256000/48 * 30秒 = 约44小时
  优点: 不影响电池寿命
  缺点: 升级周期极长

策略C - 混合策略:
  白天(有太阳能补充)高频下载，夜间恢复正常
  适用于有能量补充的设备
```

### 8.3 实际建议

- 尽量减小固件镜像大小(差分升级)
- 在设备安装初期(电池新)完成必要升级
- 评估升级对电池寿命的影响并告知用户
- 提供"仅关键安全补丁"的最小升级选项

## 9. OTA镜像文件格式

### 9.1 文件头结构

```
| 偏移 | 大小(字节) | 字段              | 说明             |
|------|-----------|-------------------|------------------|
| 0    | 4         | File ID           | 固定0x0BEEF11E   |
| 4    | 2         | Header Version    | 头部格式版本     |
| 6    | 2         | Header Length     | 头部总长度       |
| 10   | 2         | Manufacturer Code | 制造商ID         |
| 12   | 2         | Image Type        | 镜像类型         |
| 14   | 4         | File Version      | 固件版本号       |
| 18   | 2         | Stack Version     | 协议栈版本       |
| 20   | 32        | Header String     | 描述字符串       |
| 52   | 4         | Total Image Size  | 文件总大小       |
```

### 9.2 构建OTA文件

```bash
# Silicon Labs工具构建OTA文件
commander ota create \
  --manufacturer-id 0x1234 \
  --image-type 0x0001 \
  --firmware-version 0x00010002 \
  --input application.gbl \
  --output application.ota

# 添加签名
commander ota sign \
  --input application.ota \
  --key manufacturer_private_key.pem \
  --output application_signed.ota
```

## 10. 各平台实现与最佳实践

### 10.1 主流平台

- Silicon Labs EmberZNet: GBL格式，Gecko Bootloader，支持内部双Bank和外部SPI Flash
- TI Z-Stack: 支持片上OAD和片外OAD，BIM作为Bootloader，支持增量升级
- NXP JN516x/JN518x: 外部SPI Flash存储，支持串行Bootloader后备恢复

### 10.2 通用最佳实践

- 始终启用镜像签名验证，防止恶意固件
- 实现可靠回滚机制，测试断电恢复场景
- 限制并发升级数量，避免网络拥塞
- 监控升级成功率并设置告警
- 保留物理接口恢复能力(JTAG/UART)
- 从产品设计第一天就纳入OTA: 预留存储空间、集成Bootloader、规划密钥管理

## 总结

Zigbee OTA 升级在严苛约束下实现可靠固件更新，核心思想是"慢但可靠，安全优先于速度"。ZCL OTA Cluster 提供标准化协议确保多厂商互操作; 分块下载适应低带宽链路并支持断点续传; 镜像签名防止恶意注入; Bootloader双Bank/回滚确保不变砖; 终端设备OTA需在速度和电池间权衡。实际下载速率约300-480字节/秒，大镜像需要数十分钟，但这种"慢"换来的是可靠性和安全性。

## 参考文献

1. Zigbee Alliance, "ZCL Specification - OTA Upgrade Cluster (ID 0x0019)", Revision 8, 2021
2. Silicon Labs, "UG489: Gecko Bootloader User's Guide for Zigbee", 2022
3. Texas Instruments, "SWRA896: Z-Stack OTA Upgrade User's Guide", 2021
4. NXP, "JN-AN-1003: JN516x OTA Upgrade Application Note", 2019
5. Zigbee Alliance, "Zigbee OTA Upgrade Image File Format Specification", 2020
