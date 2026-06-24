# LoRaWAN组播固件更新FUOTA机制
> **难度**：🔴 高级 | **领域**：LoRaWAN高级功能 | **阅读时间**：约 22 分钟

## 引言

想象你是广播电台的DJ,需要把一首新歌发给1000个听众。你有两个选择: 给每个听众单独打电话播放一遍(单播,打1000个电话);或通过广播一次性发送,所有调对频率的听众同时收听(组播,只发一次)。LoRaWAN的FUOTA(Firmware Update Over The Air)选择了"广播"方式来给大量设备同时更新固件。

问题是LoRaWAN数据速率极低且有严格占空比限制。100KB固件用单播逐个更新1000个设备可能需要数年。FUOTA通过组播传输结合前向纠错编码,将时间压缩到小时级别。

## 1. FUOTA面临的挑战

### 1.1 LoRaWAN的约束

```
数据速率: SF9/125kHz约1760bps
占空比: 欧洲频段限制1%(每小时只能发36秒)
载荷大小: 单帧约50-222字节(取决于DR)
链路可靠性: 典型丢包率5-15%
下行限制: Class A仅上行后有短暂接收窗口
```

### 1.2 单播 vs 组播时间估算

```python
def estimate_time(firmware_kb=100, fragment_size=50,
                  device_count=1000, duty_cycle=0.01):
    fragments = (firmware_kb * 1024) // fragment_size  # 2000片

    # 单播: 每设备单独发
    unicast_airtime = fragments * device_count * 1.0  # 200万秒
    unicast_days = unicast_airtime / duty_cycle / 86400  # 约2315天

    # 组播: 所有设备同时接收
    multicast_airtime = fragments * 1.0  # 2000秒
    multicast_hours = multicast_airtime / duty_cycle / 3600  # 约56小时
    # 加30%FEC冗余: 约72小时

    return unicast_days, multicast_hours
```

单播1000设备约需6年;组播约需3天。组播是唯一可行方案。

## 2. FUOTA三大构建模块

### 2.1 架构

```
+-----------------------------------------------+
|           固件更新管理层                        |
+-----------------------------------------------+
         |                |                |
+-------------+  +------------------+  +------------------+
| 时钟同步     |  | 组播设置          |  | 碎片化数据传输    |
| Clock Sync  |  | Multicast Setup  |  | Fragmented Data  |
+-------------+  +------------------+  +------------------+
```

- **时钟同步**: 确保所有设备同时打开接收窗口
- **组播设置**: 配置组播地址和密钥
- **碎片化传输**: 固件分片并添加FEC冗余

## 3. 时钟同步

### 3.1 为什么需要精确时钟

Class C组播要求所有设备同一时刻监听同一频率。设备使用低精度晶振(几十ppm漂移),运行数天后时钟可能偏差数秒。

### 3.2 同步协议

```python
class ClockSyncProtocol:
    def send_time_request(self):
        """AppTimeReq: 发送设备当前时间"""
        device_time = self.get_local_time()
        self.send_mac_command(CID_APP_TIME_REQ,
                             struct.pack('<I', device_time))

    def handle_time_answer(self, payload):
        """AppTimeAns: 应用时间校正"""
        correction = struct.unpack('<i', payload[:4])[0]
        self.time_offset += correction
        self.last_sync = self.get_local_time()

    def is_sync_valid(self, max_drift_s=2):
        elapsed = self.get_local_time() - self.last_sync
        expected_drift = elapsed * 30e-6  # 30ppm
        return expected_drift < max_drift_s
```

### 3.3 精度要求

```
guard_time=100ms, 晶振30ppm:
max_interval = 0.1 / 30e-6 = 3333s = 约55分钟
结论: 同步后55分钟内必须开始组播
实际部署通常在组播前几分钟执行同步
```

## 4. 组播设置

### 4.1 组播组配置

通过单播为每个设备配置参数:

```python
class MulticastSetup:
    def __init__(self):
        self.mc_addr = None        # 组播地址
        self.mc_nwk_s_key = None   # 组播网络密钥
        self.mc_app_s_key = None   # 组播应用密钥
        self.frequency = None      # 接收频率
        self.data_rate = None      # 接收速率
        self.session_time = None   # 会话开始时间
```

### 4.2 Class C切换

```python
class DeviceFUOTAState:
    def start_multicast_session(self):
        """session_time到达时切换到Class C"""
        self.radio.set_class_c(
            frequency=self.mc_config.frequency,
            data_rate=self.mc_config.data_rate,
        )
        self.fragment_decoder.start()

    def on_session_complete(self):
        """组播结束恢复Class A"""
        self.radio.set_class_a()
```

正常模式(Class A)设备大部分时间休眠;FUOTA模式(Class C)持续监听,电池消耗显著增加。

## 5. 碎片化数据传输与FEC

### 5.1 固件分片

```python
class FragmentEncoder:
    def __init__(self, firmware_data, fragment_size=50):
        self.nb_frag = (len(firmware_data) + fragment_size - 1) // fragment_size
        padded_len = self.nb_frag * fragment_size
        self.padded_data = firmware_data + bytes(padded_len - len(firmware_data))
        self.frag_size = fragment_size

    def get_fragment(self, index):
        start = index * self.frag_size
        return self.padded_data[start:start + self.frag_size]
```

### 5.2 前向纠错编码(FEC)

FEC允许设备丢失部分片段仍能重建完整固件:

```
原理:
- M个数据片段 + N个冗余片段 = M+N总片段
- 设备只需收到任意M个即可重建
- 允许丢失最多N个片段

示例: 2000数据片 + 600冗余片(30%)
  发送2600片,设备需任意2000片即可重建
  容忍23%丢包率
```

### 5.3 FEC编解码

```python
class FECDecoder:
    def __init__(self, nb_data_fragments, fragment_size):
        self.nb_data = nb_data_fragments
        self.received_data = [None] * nb_data_fragments
        self.coded_fragments = []
        self.received_count = 0

    def add_data_fragment(self, index, data):
        if self.received_data[index] is None:
            self.received_data[index] = data
            self.received_count += 1

    def add_coded_fragment(self, data, participating_indices):
        self.coded_fragments.append((data, participating_indices))
        self.try_decode()

    def try_decode(self):
        """用编码片段恢复丢失的数据片段"""
        progress = True
        while progress:
            progress = False
            for coded_data, indices in self.coded_fragments:
                unknown = [i for i in indices
                           if self.received_data[i] is None]
                if len(unknown) == 1:
                    recovered = bytearray(coded_data)
                    for i in indices:
                        if i != unknown[0]:
                            for j in range(len(recovered)):
                                recovered[j] ^= self.received_data[i][j]
                    self.received_data[unknown[0]] = bytes(recovered)
                    self.received_count += 1
                    progress = True

    def is_complete(self):
        return self.received_count >= self.nb_data
```

## 6. FUOTA完整流程

### 6.1 端到端步骤

```
阶段1-准备(单播): McGroupSetupReq + McClassCSessionReq + FragSessionSetupReq
阶段2-同步(单播): AppTimeReq/Ans时钟同步
阶段3-传输(组播): 发送数据片段 + 编码片段
阶段4-补漏(单播): 设备报告缺失,服务器针对性重传
阶段5-应用(本地): 验证签名 -> 写Flash -> 重启
```

### 6.2 时间估算

```python
def estimate_fuota_duration(firmware_kb=100, fragment_size=50,
                            duty_cycle=0.01, redundancy=0.3):
    nb_frags = (firmware_kb * 1024) // fragment_size
    total_frags = int(nb_frags * (1 + redundancy))
    airtime_per_frag_ms = 330  # SF9/125kHz, 50字节

    total_airtime_s = total_frags * airtime_per_frag_ms / 1000
    transmission_hours = total_airtime_s / duty_cycle / 3600
    return transmission_hours  # 约24小时
```

## 7. 可靠性机制

### 7.1 FEC冗余率选择

```
10%冗余: 容忍约9%丢包
20%冗余: 容忍约17%丢包
30%冗余: 容忍约23%丢包(典型选择)
策略: 冗余率 = 实际丢包率 * 1.5
```

### 7.2 状态报告与修复

```python
class FUOTAServer:
    def handle_status_report(self, device, status):
        if status.nb_missing == 0:
            device.fuota_state = "complete"
        elif status.nb_missing < 10:
            # 少量缺失用单播补发
            for idx in status.missing_indices:
                self.unicast_send_fragment(device, idx)
        else:
            device.fuota_state = "needs_retry"
```

## 8. 安全考虑

### 8.1 固件签名验证

```c
typedef struct {
    uint8_t signature[64];   // ECDSA-P256签名
    uint8_t fw_hash[32];     // SHA-256哈希
    uint32_t fw_version;     // 版本号(防降级)
    uint32_t fw_size;
} firmware_header_t;

int verify_firmware(uint8_t *fw, size_t size,
                    firmware_header_t *hdr,
                    uint8_t *mfr_pubkey) {
    uint8_t hash[32];
    sha256(fw, size, hash);
    if (memcmp(hash, hdr->fw_hash, 32) != 0)
        return -1;  // 完整性失败
    if (!ecdsa_verify(mfr_pubkey, hdr->fw_hash, hdr->signature))
        return -2;  // 签名失败
    if (hdr->fw_version <= get_current_fw_version())
        return -3;  // 拒绝降级
    return 0;
}
```

### 8.2 组播密钥安全

组播密钥通过各设备的单播加密通道分发,每次FUOTA使用新密钥,一个设备被攻破只影响该次会话。

## 9. 实际部署考虑

### 9.1 电池影响

```
Class C接收: 约10mA * 8小时 = 80mAh
AA电池2400mAh: 一次FUOTA消耗约3.3%
每月更新: 年消耗约40%用于FUOTA

缓解: 低活动时段执行/delta更新/优化SF
```

### 9.2 Delta更新

```python
def create_delta(old_fw, new_fw):
    delta = binary_diff(old_fw, new_fw)
    # 小改动delta通常为完整固件的10-30%
    # 100KB完整->15KB delta: 传输时间减少85%
    return delta
```

### 9.3 A/B分区安全回滚

```
+------------------+
| Bootloader       |  验证签名
+------------------+
| Partition A      |  当前固件
+------------------+
| Partition B      |  新固件写入
+------------------+
| 碎片缓冲区       |  临时存储片段
+------------------+

流程: 片段->缓冲区->FEC重建->验签->写B->重启->Bootloader验B->启动B
回滚: B连续3次启动失败->自动回滚A
```

## 10. 实现参考

### 10.1 开源方案

- **ChirpStack FUOTA Server**: Go语言,完整流程管理
- **AWS IoT Core for LoRaWAN**: 托管服务,自动处理碎片和组播
- **Semtech参考实现**: C语言设备端,STM32L平台

### 10.2 监控指标

```yaml
fuota_metrics:
  progress:
    fragments_sent: 2600
    elapsed_hours: 7.5
  devices:
    complete: 920
    partial: 60
    failed: 20
  reliability:
    avg_loss_rate: "12%"
    fec_recovery_rate: "99.2%"
```

## 总结

FUOTA解决了一个看似不可能的问题: 在极低速率的LPWAN上为数千设备同时更新固件。通过组播、FEC和时钟同步三大技术的组合,将数年的更新压缩到数小时。

核心要点:
- 单播固件更新在大规模部署中不可行,组播是唯一选择
- 三个协议层: 时钟同步、组播设置、碎片化传输
- FEC允许丢失部分片段仍能重建完整固件
- 典型场景(1000设备/100KB)约需18-24小时
- 安全: 固件签名验证 + 组播密钥通过加密单播分发
- 电池影响显著,用delta更新和A/B分区减少影响

## 参考文献

1. LoRa Alliance, "LoRaWAN Fragmented Data Block Transport v1.0.0", 2018
2. LoRa Alliance, "LoRaWAN Remote Multicast Setup v1.0.0", 2018
3. LoRa Alliance, "LoRaWAN Application Layer Clock Sync v1.0.0", 2018
4. Semtech, "FUOTA Process for LoRaWAN Devices", Technical Paper, 2019
5. ChirpStack, "Firmware Update Over The Air", https://www.chirpstack.io/docs/
