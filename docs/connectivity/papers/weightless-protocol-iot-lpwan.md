# Weightless协议族在IoT LPWAN中的定位
> **难度**: 中级 | **领域**: LPWAN协议 | **阅读时间**: 约 20 分钟

## 引言

想象有人在2012年设计了一辆性能优秀的电动汽车--加速更快、续航更长、价格更低。但推出时特斯拉已经建好充电网络,竞品已占据经销商渠道,消费者已形成品牌认知。最终这辆"更好的车"只卖出几百辆就退出了市场。

Weightless协议在LPWAN领域的故事与此类似。它是一套技术上颇具亮点的开放标准协议族,由ARM前高管创办的Neul公司主导开发,目标是成为"IoT的WiFi"。然而尽管技术设计优势明显,Weightless最终未能获得商业牵引力。这个案例提供了宝贵教训: 技术标准竞争中,技术优势并非决定性因素。

## 1. Weightless的诞生背景

### 1.1 创始团队与愿景

Weightless由Neul公司发起,2011年成立于英国剑桥,创始人James Collier曾是ARM工程副总裁。核心愿景: 创建开放、免版税的LPWAN标准,类似WiFi在局域网中的角色--通过开放标准推动多厂商竞争降低成本。Weightless SIG(Special Interest Group)于2012年成立,参照蓝牙SIG模式运营,吸引了约60家成员公司,涵盖芯片、模块和系统集成商。

### 1.2 时间线

```
2011: Neul公司成立(英国剑桥)
2012: Weightless SIG成立, 发布Weightless-W规范(TV白频谱)
2013: 发布Weightless-N规范(窄带Sub-GHz)
2014: 发布Weightless-P规范(Sub-GHz双向)
2015: Neul被华为收购 | LoRa Alliance成立并快速发展
2016: Weightless SIG活动减少, 市场被LoRaWAN/NB-IoT主导
2017+: Weightless事实上停止发展
```

### 1.3 市场背景

Weightless比LoRa Alliance更早提出开放标准LPWAN概念,但未能抓住窗口期:

| 时间 | LoRaWAN | Sigfox | NB-IoT | Weightless |
|------|---------|--------|--------|------------|
| 2012 | LoRa芯片刚出 | 法国试运营 | 概念阶段 | W规范发布 |
| 2014 | Alliance即将成立 | 覆盖数国 | 3GPP立项 | P规范发布 |
| 2015 | Alliance成立爆发 | 快速扩张 | 标准冻结 | Neul被收购 |

## 2. Weightless协议族: 三个变体

### 2.1 概述

```
Weightless-W (White Space): TV白频谱(470-790MHz), 最具创新性
Weightless-N (Narrowband):  Sub-GHz ISM, 类Sigfox窄带方案
Weightless-P (Performance): Sub-GHz ISM, 双向完整方案, 最终主推版本
```

### 2.2 Weightless-W: TV白频谱方案

基于TV白频谱(TVWS)--模拟电视迁移后空闲的VHF/UHF频段。技术参数: 470-790MHz,可用6-8MHz信道,数据速率1kbps-10Mbps,完全双向。

但TVWS面临现实困难:

```
TVWS的"先有鸡还是先有蛋"问题:

  IoT设备需要联网 -> 需要知道可用信道
  知道可用信道 -> 需要查询在线数据库
  查询在线数据库 -> 需要先联网
  死循环!

其他TVWS困难:
  - 可用性因地区差异极大
    美国: FCC已开放, 数据库可用
    欧洲: 各国不一, Ofcom领先
    亚洲: 大多未开放
  - 无法做全球统一方案
  - 次级用户功率受限(避免干扰主用户)
```

### 2.3 Weightless-N: 窄带方案

鉴于W的频谱问题推出替代: Sub-GHz ISM频段,DBPSK调制约200Hz信道,约100bps,主要上行。本质上是Sigfox的开放标准版本。

问题在于缺乏差异化优势: 已经在用Sigfox的客户没有迁移动力(功能几乎相同); 新客户面对"有芯片的Sigfox"和"没芯片的Weightless-N",选择显而易见。

### 2.4 Weightless-P: 性能均衡方案

最完整的方案,在LoRa和Sigfox之间找平衡:

| 参数 | 数值 |
|------|------|
| 频段 | Sub-GHz ISM(138/433/470/868/915MHz) |
| 信道带宽 | 12.5kHz |
| 多址接入 | FDMA + TDMA |
| 调制 | GMSK/offset-QPSK(可变) |
| 数据速率 | 0.625kbps - 100kbps |
| 安全 | AES-128加密 |
| ACK | 完全支持 |
| 自适应速率 | 支持(根据信号质量调整) |

## 3. Weightless-P技术深入分析

### 3.1 FDMA/TDMA混合接入

比LoRaWAN更结构化的信道接入:

```
频率
  ^
  | [设备A] [设备C]     信道1 (12.5kHz)
  | [设备B]      [设备D] 信道2 (12.5kHz)
  |      [设备E] [设备F] 信道3 (12.5kHz)
  +------------------------------> 时间
FDMA: 不同设备使用不同频率(并行传输)
TDMA: 同频率上不同设备占不同时隙(避免冲突)
```

优势: 比LoRaWAN的纯ALOHA冲突概率低,时隙化接入更可预测,频谱效率更高。

### 3.2 自适应数据速率

根据链路质量动态调整: 信号强时用高阶调制达100kbps,信号弱时降到0.625kbps换取更远距离。与LoRaWAN的ADR概念类似但实现不同: LoRaWAN改变扩频因子(SF7-SF12),Weightless-P改变调制阶数和编码率。

### 3.3 ACK与可靠传输

Weightless-P原生支持确认式传输:

```
设备                               基站
  |--- 上行数据(帧序号=1) --------->|
  |<-- ACK(确认帧序号=1) -----------|
  |--- 上行数据(帧序号=2) --------->|
  |          (丢失)                  |
  |--- 超时重传(帧序号=2) --------->|
  |<-- ACK(确认帧序号=2) -----------|
```

对关键指令(如阀门控制),ACK机制确保被接收执行。这是Sigfox(几乎无下行)做不到的。

### 3.4 安全机制

```
Weightless-P安全栈:
  加密:      AES-128 (与LoRaWAN相同级别)
  认证:      预共享密钥 (设备入网时注入)
  完整性:    MIC消息完整性码 (防篡改)
  防重放:    帧计数器 (每帧递增, 拒绝旧帧)
  密钥管理:  支持密钥更新 (运营中可轮换)
```

安全设计与LoRaWAN安全级别相当。

## 4. 与LoRaWAN和Sigfox的全面对比

### 4.1 技术参数对比

| 参数 | Weightless-P | LoRaWAN | Sigfox |
|------|-------------|---------|--------|
| 信道带宽 | 12.5kHz | 125-500kHz | ~100Hz |
| 调制 | GMSK/QPSK | CSS | DBPSK |
| 数据速率 | 0.625-100kbps | 0.3-50kbps | 0.1-0.6kbps |
| 距离 | 2-10km | 2-15km | 10-50km |
| 双向通信 | 完全支持 | Class A/B/C | 极有限 |
| ACK | 原生支持 | Class C最佳 | 不支持 |
| 多址接入 | FDMA/TDMA | ALOHA | 随机ALOHA |
| 标准类型 | 开放免版税 | 开放(PHY层Semtech专利) | 私有 |
| 自适应速率 | 支持 | ADR支持 | 不支持 |

### 4.2 Weightless-P的技术优势

```
Weightless-P的四大技术优势:

1. 更结构化的FDMA/TDMA接入
   - 减少冲突, 适合需要可预测延迟的工业控制
   - LoRaWAN的纯ALOHA在高密度场景冲突率高

2. 完全开放免版税
   - 任何芯片厂商可实现(LoRa PHY层是Semtech专利)
   - 理论上可形成多供应商竞争降低成本

3. 从设计之初考虑上下行对称
   - ACK/远程配置/OTA都有原生支持
   - 不像Sigfox是事后加入下行能力

4. 数据速率动态范围更宽
   - 0.625kbps到100kbps(160倍范围)
   - LoRaWAN: 0.3-50kbps(167倍,类似)
   - Sigfox: 0.1-0.6kbps(6倍,非常窄)
```

## 5. 商业失败分析

### 5.1 Neul被华为收购

2015年华为收购Neul,直接导致Weightless转折。华为动机是获取LPWAN技术团队和专利,整合到3GPP NB-IoT标准化工作(华为是NB-IoT主要推动者)。后果: Neul团队重新分配到NB-IoT项目,Weightless失去核心技术推动力,SIG失去领导组织,其他成员逐渐退出。

### 5.2 生态系统缺失

```
成功LPWAN需要的生态要素:
                LoRaWAN(成功)     Weightless(失败)
芯片供应商:     Semtech + 多家     无商用芯片
模块厂商:       数十家              无商用模块
网关厂商:       数十家              无商用网关
开发者社区:     数万人              几百人
参考设计:       丰富                极少

没有芯片 -> 无法做产品 -> 没有网络部署动力 -> "死亡螺旋"
```

### 5.3 时间窗口错失

2012-2014年窗口打开期,市场没有明确赢家,但Weightless协议还在迭代(W到N到P),没有稳定版本,更没有芯片。2015年窗口关闭: LoRa Alliance成立快速聚集产业伙伴,Sigfox大规模融资加速部署,3GPP启动NB-IoT,Neul被收购。此后格局已定。

### 5.4 开放标准的悖论

```
WiFi成功的前提条件(Weightless都不具备):

  WiFi(成功)                    Weightless(失败)
  -------------------------------------------------------
  IEEE 802.11成熟标准            标准还在W->N->P迭代
  多家大型芯片厂商同时投入       没有芯片厂商愿意投入
  PC/手机巨大需求拉动            IoT市场2012年还很小
  标准先于产品存在               产品与标准同步开发
  成本持续下降有利可图           客户对成本极敏感
```

LoRa虽然PHY层私有,但Semtech积极授权价格合理--"足够开放"胜过了"完全开放但没有芯片"。这是Weightless最痛苦的教训。

## 6. 从Weightless学到的教训

### 6.1 技术标准竞争的关键因素

```
因素权重(从Weightless案例总结):
  生态系统(40%): 芯片/模块/网关/运营商/开发者 -- 最重要
  时间窗口(25%): 先发优势,切换成本高
  商业模式(20%): 与产业链利益对齐
  技术优势(15%): 重要但不是决定性的
```

### 6.2 对当前新LPWAN技术的启示

当前仍有新技术出现(MIOTY、DECT-2020 NR+、Amazon Sidewalk)。从Weightless案例提炼的成功条件:

```
新LPWAN技术存活检查清单:
  [ ] 至少一家大型芯片厂商支持(无芯片=死亡)
  [ ] 有明确差异化场景(不只是"更好")
  [ ] 在该场景中比LoRaWAN/NB-IoT有显著优势
  [ ] 有大型企业背书(降低采用风险)
  [ ] 与现有生态共存而非替代(降低迁移成本)
```

MIOTY的策略相对成功: 不试图取代LoRa而是补充恶劣环境场景,有Fraunhofer学术声誉背书,ETSI标准化提供可信度,专注工业细分市场。

## 7. Weightless技术遗产

### 7.1 对NB-IoT的影响

华为收购Neul后,团队经验和专利用于NB-IoT标准化:

```
Weightless概念          NB-IoT实现
窄带信道设计     ->     180kHz窄带载波
自适应速率       ->     多TBS传输块大小
双向通信         ->     全双工DL/UL
TDMA时隙化       ->     SC-FDMA调度
```

Weightless的部分理念在NB-IoT中延续,只是在3GPP授权频谱框架下而非ISM频段。

### 7.2 对LPWAN标准化的启示

Weightless首先提出LPWAN需要开放标准,促使LoRa Alliance更加开放,也促使3GPP加速NB-IoT标准化。Weightless-W是最早将TVWS用于LPWAN的尝试,为后续研究提供参考。多级速率自适应设计影响了后续LPWAN技术的优化方向。

## 8. 案例分析: 技术优势为何败给生态

### 8.1 假设场景

2014年一家智慧农业公司选择LPWAN技术,覆盖5000亩农田2000个土壤传感器:

```
需求: 3km覆盖, 2000传感器, 每小时上报20字节, 需要下行, 6个月内部署
```

### 8.2 技术评分 vs 可行性评分

```
纯技术评分(每项满分10分):
                    Weightless-P  LoRaWAN  Sigfox
双向通信:              9           7        3
接入效率:              8           6        7
标准开放性:            10          7        3
自适应速率:            8           7        2
安全机制:              8           8        5
多址接入:              8           7        6
技术总分:              51          42       26
Weightless-P技术上领先!

实际可行性评分(每项满分10分):
                    Weightless-P  LoRaWAN  Sigfox
芯片可买到:            1           8        7
模块可买到:            1           7        6
有SDK/文档:            3           8        7
能6月部署:             1           8        7
有参考案例:            1           8        7
社区支持:              1           9        6
可行性总分:            8           48       40
LoRaWAN碾压!
```

### 8.3 决策结论

最终选择LoRaWAN。"Weightless-P技术规格很棒,但买不到芯片,找不到模块,没有开发板做原型,6个月内不可能部署。LoRaWAN虽然技术上没那么'完美',但明天就能买到开发板开始原型。"这就是"可用性胜过优越性"的经典案例。

## 9. 当前LPWAN格局的反思

2024年LPWAN市场: LoRaWAN是私有网络之王(生态最丰富,全球数亿设备); NB-IoT是运营商网络之王(3GPP标准,原生QoS保障); Sigfox衰落中(2022年破产被UnaBiz收购,教训是单一供应商运营商模式风险高); Weightless已消亡(技术文档仍可查阅,无商业部署)。

Weightless失败不意味着开放标准在LPWAN没有价值。近年新尝试包括: DECT-2020 NR+(ETSI标准,有Nordic等芯片厂商支持,吸取教训先有芯片再推标准); Wi-SUN(IEEE 802.15.4g,智能电网开放Mesh标准,已有实际部署); Amazon Sidewalk(Amazon生态加持,利用Echo/Ring设备做网关避免冷启动问题)。

## 总结

Weightless协议族是LPWAN发展史上值得深入研究的案例。从纯技术角度,Weightless-P在多个维度上优于同期竞品: 开放标准免版税、完善双向通信、结构化FDMA/TDMA接入、宽范围自适应速率。然而技术优势未能转化为商业成功。核心原因不是技术不够好,而是生态系统没有建立起来: 没有芯片厂商将规范变成硅片,开发者无法构建产品。Neul被华为收购加速了消亡,其团队和专利被整合到NB-IoT标准化中。对今天的技术选型者,Weightless留下的教训是: 生态系统的建设速度比技术指标的优越性更重要,"足够好"的技术加上强大生态,几乎总是胜过"最优"技术但缺乏生态支持。

## 参考文献

1. Weightless SIG. "Weightless-P System Specification." Version 1.0, 2014.
2. W. Webb. "Weightless: The Technology to Finally Realize the M2M Vision." Cambridge Wireless, 2013.
3. Huawei. "Acquisition of Neul Ltd - Press Release." 2015.
4. K. Mekki et al. "A Comparative Study of LPWAN Technologies for Large-scale IoT Deployment." ICT Express, Vol. 5, 2019.
5. U. Raza et al. "Low Power Wide Area Networks: An Overview." IEEE Communications Surveys and Tutorials, Vol. 19, No. 2, 2017.
