# 物理不可克隆函数PUF设备指纹技术
> **难度**：🔴 高级 | **领域**：硬件安全原语 | **阅读时间**：约 22 分钟

## 引言

想象一下,世界上没有两片完全相同的树叶。即使同一棵树上的叶子,在微观层面也各不相同。硅芯片也一样——即使是同一批次的芯片,由于制造过程中的微小随机波动,每颗芯片的物理特性都有细微差异。物理不可克隆函数(Physical Unclonable Function, PUF)就是利用这些天生的"指纹"来唯一标识每颗芯片,就像用指纹来区分每个人一样。

传统IoT设备的安全依赖于在非易失性存储器中保存密钥。但存储的密钥可以被读取、复制或篡改。PUF从根本上改变了这一范式——密钥不再"存储",而是在需要时由芯片的物理特性"生成",用完即消失。攻击者即使物理拆解芯片,也找不到任何密钥的痕迹。

## 1. PUF的基本概念

### 1.1 什么是PUF

PUF是一种将物理系统的内在随机性映射为可重复输出响应的函数。给定一个输入(挑战,Challenge),PUF产生一个确定但不可预测的输出(响应,Response)。这种映射关系由制造过程中的随机物理变化决定,无法被复制或克隆。

```
PUF的基本工作模式:
Challenge (输入) ---> [PUF硬件] ---> Response (输出)
                         |
                    制造随机性(不可复制)
```

PUF的核心思想可以类比为:把一颗弹珠扔进一个复杂的弹珠台,弹珠的路径由台面上无数微小的凸起决定(制造随机性),但同一个弹珠台每次扔同一种弹珠,弹珠最终落到的位置是相同的(可重复性)。

```c
// 唯一性计算: 两个不同芯片的响应之间的海明距离
float uniqueness = (float)hamming_distance(resp_chip_A, resp_chip_B) / total_bits;
// 理想值: 0.50 (50%的比特不同)

// 可靠性计算: 同一芯片多次响应的稳定性
float reliability = 1.0 - (float)hamming_distance(resp_1, resp_2) / total_bits;
// 理想值: 1.00 (完全一致,实际约0.95-0.99)
```

### 1.2 PUF的三大核心属性

| 属性 | 含义 | 量化指标 |
|------|------|---------|
| 唯一性(Uniqueness) | 不同设备对同一挑战产生不同响应 | 海明距离(HD)接近50%为最佳 |
| 可靠性(Reliability) | 同一设备多次对同一挑战产生相同响应 | 误码率(BER)越低越好 |
| 不可预测性(Unpredictability) | 已知部分CRP无法推断未知CRP | 无法用机器学习建模 |

## 2. PUF的主要类型

### 2.1 SRAM PUF

SRAM PUF利用SRAM上电瞬间的初始状态作为设备指纹。未初始化的SRAM单元中,每个比特倾向于0还是1,由交叉耦合反相器的阈值电压失配决定。

```
SRAM PUF关键优势:
- 无需额外硬件: 每颗MCU都有SRAM,直接复用
- 实现简单: 上电后立即读取,然后初始化SRAM正常使用
- 零成本: 不增加芯片面积和成本

上电瞬间: 哪边反相器导通更快 -> 该比特的初始值
阈值失配 -> 偏好固定 -> 构成指纹
```

```c
// SRAM PUF 读取示例(伪代码)
#define PUF_SRAM_START  0x20000000
#define PUF_SRAM_SIZE   256  // 读取256字节作为PUF响应

void read_sram_puf(uint8_t *puf_data) {
    // 关键: 必须在SRAM初始化之前读取
    volatile uint8_t *sram = (volatile uint8_t *)PUF_SRAM_START;
    for (int i = 0; i < PUF_SRAM_SIZE; i++) {
        puf_data[i] = sram[i];
    }
    // 读取完毕后,SRAM可被正常初始化使用
    memset((void *)PUF_SRAM_START, 0, PUF_SRAM_SIZE);
}
// 注意: 编译器可能自动插入SRAM初始化代码
// 需要修改启动文件,延迟.bss段初始化
```

### 2.2 仲裁器PUF(Arbiter PUF)

仲裁器PUF利用信号在两条对称路径上的竞争关系产生响应。路径延迟差异具有随机性,两条路径哪个信号先到达不可预测。

```
仲裁器PUF结构:
Input --+---[SW0]---[SW1]---...---[SWn-1]---+---> D
        +---[SW0]---[SW1]---...---[SWn-1]---+---> CLK
                                                  [Arbiter] -> Response(0/1)

每个SWi根据Challenge[i]决定信号走上面还是下面
挑战空间随级数指数增长,n级有2^n种挑战(强PUF)
弱点: 容易受机器学习攻击(可建模性)
```

### 2.3 环形振荡器PUF(RO PUF)

RO PUF利用奇数个反相器组成的环形电路的振荡频率差异。两个RO的频率比较结果构成1比特响应。

```c
// RO PUF读取示例(伪代码)
uint8_t ro_puf_compare(uint32_t ro_a_base, uint32_t ro_b_base,
                       uint32_t count_window) {
    uint32_t count_a = 0, count_b = 0;
    start_counters(ro_a_base, ro_b_base);
    wait_us(count_window);
    count_a = read_counter(ro_a_base);
    count_b = read_counter(ro_b_base);
    return (count_a > count_b) ? 1 : 0;  // f_A > f_B -> 1
}
```

### 2.4 PUF类型对比

| 特性 | SRAM PUF | 仲裁器PUF | RO PUF |
|------|----------|----------|--------|
| CRP数量 | 少(弱PUF) | 多(强PUF) | 中等 |
| 额外硬件 | 无 | 需要路径选择器 | 需要RO阵列 |
| 抗机器学习 | 强 | 弱 | 中等 |
| 典型应用 | 密钥生成 | 设备认证 | 密钥生成/认证 |
| IoT适用性 | 高 | 中 | 中高 |

## 3. 挑战-响应对(CRP)与弱/强PUF

```
CRP工作流程:

注册阶段(Enrollment):
Challenge C ---> [PUF Device] ---> Response R
                     |--> R + 辅助数据存入数据库

认证阶段(Authentication):
Challenge C ---> [PUF Device] ---> Response R'
                     |--> R'与数据库中的R比对(容错匹配)

| 分类 | CRP数量 | 典型代表 | 主要用途 |
|------|---------|---------|---------|
| 弱PUF | 少(等于比特数) | SRAM PUF | 密钥生成 |
| 强PUF | 指数级多 | 仲裁器PUF | 设备认证 |
```

弱PUF像只有一把钥匙的锁——钥匙有限但安全(藏在设备内部)。强PUF像有无数种开门方式的保险库——每次验证用不同挑战,已用CRP可公开,攻击者无法推断新CRP。

## 4. 模糊提取器(Fuzzy Extractor)

### 4.1 为什么需要模糊提取器

PUF响应并非100%稳定。温度变化、电压波动、老化等因素会导致3-15%的比特翻转。但密码学密钥要求每一位都精确——差一个比特密钥就完全不同。模糊提取器是解决"不完美物理响应"与"精确密钥要求"之间矛盾的桥梁。

### 4.2 工作原理

```
注册阶段:
原始PUF响应 W ---> [纠错编码] ---> 码字 C
  C XOR W = 辅助数据 H (公开存储)
  W ---> [哈希函数] ---> 密钥 K (隐私放大)

重构阶段:
含噪PUF响应 W' ---> H XOR W' ---> 纠错解码 ---> W ---> [哈希] ---> 密钥 K
```

```c
// 模糊提取器简化示例(基于BCH码)
#include "bch_codec.h"
#include "sha256.h"

// 注册阶段: 生成辅助数据和密钥
void fuzzy_extractor_enroll(const uint8_t *puf_resp, int resp_len,
                            uint8_t *helper_data, uint8_t *key) {
    uint8_t codeword[MAX_LEN];
    bch_encode(puf_resp, resp_len, codeword);
    for (int i = 0; i < resp_len; i++)
        helper_data[i] = codeword[i] ^ puf_resp[i];
    sha256(puf_resp, resp_len, key);  // 隐私放大
}

// 重构阶段: 从含噪响应恢复密钥
int fuzzy_extractor_reconstruct(const uint8_t *puf_noisy, int resp_len,
                                const uint8_t *helper_data, uint8_t *key) {
    uint8_t codeword_noisy[MAX_LEN], puf_clean[MAX_LEN];
    for (int i = 0; i < resp_len; i++)
        codeword_noisy[i] = helper_data[i] ^ puf_noisy[i];
    if (bch_decode(codeword_noisy, resp_len, puf_clean) != 0)
        return -1;  // 纠错失败
    sha256(puf_clean, resp_len, key);
    return 0;
}
```

隐私放大通过密码学哈希函数将PUF响应压缩为均匀分布的密钥:
- 哈希函数的雪崩效应消除统计偏差
- 压缩比例(如256比特PUF响应压缩为128比特密钥)增强安全性
- 即使辅助数据泄露,攻击者也无法从哈希输出反推PUF响应

## 5. PUF在IoT中的应用

### 5.1 设备认证

```
基于强PUF的认证协议:
Server                              Device
  |--- Challenge C ------------------>|  计算PUF响应R'
  |<-- Response R' -------------------|
  | 验证: |R XOR R'| < 阈值 -> 通过   |
```

### 5.2 安全密钥生成

```c
// IoT设备启动时的PUF密钥生成流程
void boot_secure_key_generation(void) {
    uint8_t puf_raw[PUF_RAW_LEN], helper_data[PUF_RAW_LEN];
    uint8_t root_key[32], session_key[16];

    // Step 1: 读取SRAM PUF(必须在SRAM初始化前)
    read_sram_puf(puf_raw);

    // Step 2: 从Flash读取辅助数据(公开的,不怕泄露)
    flash_read(HELPER_DATA_ADDR, helper_data, PUF_RAW_LEN);

    // Step 3: 模糊提取器重构根密钥
    if (fuzzy_extractor_reconstruct(puf_raw, PUF_RAW_LEN,
                                     helper_data, root_key) != 0) {
        halt_system();  // 纠错失败,可能硬件被篡改
    }

    // Step 4: 从根密钥派生会话密钥
    derive_key(root_key, "session-key-v1", session_key, 16);

    // Step 5: 安全清除中间数据
    secure_memset(puf_raw, 0, PUF_RAW_LEN);
    secure_memset(root_key, 0, 32);
    // session_key可用,且不存在于任何NVM中
}
```

### 5.3 防伪与IP保护

- **防伪**: 每颗芯片PUF指纹唯一,无法复制,可验证真伪
- **IP保护**: 固件加密密钥由PUF生成,只有原始芯片能解密
- **供应链追踪**: 记录每颗芯片PUF指纹,追踪产品流向

## 6. 商业PUF产品

| 产品 | 厂商 | 技术路线 | 特点 |
|------|------|---------|------|
| QuiddiKey | Intrinsic ID | SRAM PUF(纯软件IP) | 零硬件,已集成多款MCU/FPGA |
| Synopsys PUF | Synopsys | SRAM PUF(IP核) | FIPS 140-3认证,含模糊提取器 |
| LPC55S6x PUF | NXP | 内置SRAM PUF | 可生成4个独立密钥,硬件自动擦除 |

```
NXP LPC55S6x PUF使用流程:
1. 首次: PUF_Enroll() -> 生成辅助数据 -> 存Flash(公开)
2. 后续: PUF_GetKey() -> 辅助数据+PUF响应 -> 恢复密钥
3. 密钥仅在RAM中,使用后硬件自动擦除
```

## 7. PUF与传统存储密钥对比

| 对比维度 | PUF密钥 | 存储密钥(NVM) |
|----------|---------|--------------|
| 密钥存在形式 | 动态生成,用完即消失 | 静态存储,持续存在 |
| 物理攻击抗性 | 拆解芯片破坏PUF特性 | 可通过探针读取Flash |
| 克隆抗性 | 物理特性不可复制 | Flash内容可复制 |
| 成本 | 低(复用SRAM) | 需要安全存储硬件 |
| 环境稳定性 | 受温度/电压影响 | 稳定 |

## 8. PUF面临的挑战

### 8.1 老化与环境敏感性

芯片长期使用后晶体管特性偏移(NBTI、HCI),导致PUF误码率上升。不同条件下的典型SRAM PUF误码率:

```
条件                   误码率(BER)
25 C, 标称电压         2-5%
-40 C, 标称电压        8-12%
85 C, 标称电压         6-10%
-40 C, 电压降10%       12-18%

应对: 模糊提取器需覆盖最坏情况;定期重新注册
```

### 8.2 注册阶段安全

PUF的注册阶段(Enrollment)是安全链中最薄弱的环节:
- 注册时PUF响应以明文形式存在
- 如果注册环境被攻击者控制,PUF响应可能被窃取
- 应对: 在可信制造环境(Trust Factory)中完成注册

### 8.3 机器学习攻击

特别是对仲裁器PUF等强PUF:
- 攻击者收集大量CRP,用机器学习建立PUF模型
- 模型建立后可预测未知挑战的响应
- 应对: 使用前馈结构、XOR仲裁器PUF等抗建模变体

## 9. 实际集成方案

```
典型IoT设备安全架构:

上电 --> SRAM PUF读取(启动最早期)
           |
     模糊提取器重构
           |
       根密钥(仅存于RAM)
       /    |    \
    派生  派生   派生
     |     |     |
  AES密钥  HMAC密钥  通信密钥
     |     |     |
  数据加密 消息认证  TLS/DTLS

断电 --> 所有密钥消失 --> 下次启动重新生成
```

设计注意事项:

1. **读取时机**: SRAM PUF必须在任何初始化代码之前读取
2. **辅助数据保护**: 公开存储但应防篡改(加完整性校验)
3. **误码率预算**: 模糊提取器纠错能力应覆盖最坏工作条件
4. **密钥生命周期**: 密钥仅在RAM中,断电消失,使用后及时清零
5. **降级方案**: PUF失败时应有安全回退机制(如锁定设备)

## 总结

PUF将芯片的制造随机性转化为设备唯一指纹,从根本上解决了IoT设备中密钥存储的安全难题。SRAM PUF因其零额外硬件成本成为IoT首选方案。模糊提取器通过纠错编码和隐私放大,将不完美的物理响应转化为精确的密码学密钥。虽然PUF面临老化、环境敏感等挑战,但在设备认证、密钥生成、防伪等场景中已展现出不可替代的价值。对于资源受限的IoT设备,PUF提供了一条从"存储密钥"到"生成密钥"的安全范式转换路径。

## 参考文献

1. G. E. Suh, S. Devadas, "Physical Unclonable Functions for Device Authentication and Secret Key Generation", DAC 2007
2. R. Maes, "Physically Unclonable Functions: Constructions, Properties and Applications", Springer 2013
3. Intrinsic ID, "QuiddiKey Product Brief", https://www.intrinsic-id.com
4. NXP, "LPC55S6x User Manual - PUF Chapter", NXP Semiconductor 2020
5. C. Bohm, M. Hofer, "Physical Unclonable Functions in Theory and Practice", Springer 2012
