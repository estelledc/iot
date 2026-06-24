# 学习路线图

> 从零基础到前沿研究的推荐学习路径。最后更新: 2026-06-24

---

## 项目目标

将 IoT 阅读站从 200 篇扩展到 2000 篇，覆盖物联网 8 层架构的完整知识体系。每篇文章 300-400 行，中文，先日常类比再技术深入，适合零基础读者逐步进阶。

---

## 扩展路线 (Timeline)

```
Phase 1: 种子内容 [DONE]
  - 8 层各 25 篇 = 200 篇
  - 建立站点框架、主题、导航

Phase 2: Layer 1 Foundation 扩展 [DONE]
  - +250 篇 (plan: 59 topics -> 实际 275 篇)
  - 传感器、硬件、嵌入式全覆盖

Phase 3: Layer 2 Connectivity 扩展 [DONE - 2026-06-24]
  - +192 篇 (plan: 192 topics -> 实际 217 篇)
  - 无线协议、频谱、调制、接入全覆盖

Phase 4: Layer 3 Network 扩展 [NEXT]
  - 计划 +180 篇
  - 协议栈、路由、SDN、TSN、消息队列

Phase 5: Layer 4 Computing 扩展
  - 计划 +191 篇
  - 边缘计算、容器、Serverless、数字孪生

Phase 6: Layer 5 Intelligence 扩展
  - 计划 +302 篇 (最大层)
  - 边缘AI、联邦学习、模型压缩、推理优化

Phase 7: Layer 6 Security 扩展
  - 计划 +198 篇
  - 加密、认证、隐私、合规、供应链安全

Phase 8: Layer 7 Applications 扩展
  - 计划 +206 篇
  - 垂直行业应用: 工业、医疗、农业、交通、能源

Phase 9: Layer 8 Frontier 扩展
  - 计划 +249 篇
  - 6G、量子、全息、具身智能、元宇宙
```

**预计总量**: ~1968 篇 (已超 2000 目标的可行边界)

---

## 难度分级

- **零基础**: 无需任何前置知识
- **入门**: 需要基本编程能力或计算机网络基础
- **进阶**: 需要该层级的入门知识
- **前沿**: 需要扎实的理论基础，面向研究者

---

## 推荐路径

### 路径 A: 嵌入式 IoT 开发者

```
RTOS 对比 → ESP32 原型开发 → BLE/WiFi 接入
→ MQTT 协议 → 边缘计算概念 → TinyML 部署
```

### 路径 B: 网络与通信研究者

```
LPWAN 对比 → 5G RedCap → TSN/DetNet
→ 网络切片 → SDN for IoT → 6G ISAC
```

### 路径 C: 边缘 AI 研究者

```
边缘计算综述 → 模型压缩 → 协作推理
→ Jupiter → 联邦学习 → LLM on Edge
```

### 路径 D: IoT 安全研究者

```
IoT 安全全景 → 固件安全 → PUF 认证
→ TEE 边缘计算 → FL+DP 隐私 → 零信任 IoT
```

### 路径 E: 全栈纵览 (推荐)

```
Layer 1 概览 → Layer 2 概览 → Layer 3 概览 → Layer 4 概览
→ Layer 5 概览 → Layer 6 概览 → Layer 7 概览 → Layer 8 概览
```

每层先读概览页(index.md)，再按兴趣深入具体论文。

---

## 各层核心阅读

| 层级 | 必读(入门) | 推荐(进阶) | 选读(前沿) |
|------|-------------|-------------|-------------|
| L1 | RTOS 对比、ESP32 原型 | MEMS 传感器、能量收集 | 神经形态感知、RISC-V |
| L2 | LPWAN 对比、星闪 vs BLE | UWB 定位、WiFi 7 | 反向散射、卫星 IoT |
| L3 | IoT 协议对比、MQTT 深入 | TSN/DetNet、6LoWPAN | NDN-IoT、网络切片 |
| L4 | 边缘计算综述、平台对比 | 任务卸载、Serverless | 微服务边缘、异构资源 |
| L5 | Jupiter、模型压缩 | 联邦学习、分割计算 | 持续学习、设备端训练 |
| L6 | 安全全景、隐私 FL | TEE、区块链 IoT | 对抗攻击、量子安全 |
| L7 | V2X、室内定位 | IIoT、智慧医疗 | 智能电网、供应链 |
| L8 | 数字孪生、6G ISAC | Wasm 边缘、绿色计算 | AIGC 边缘、天地一体 |

---

## 生成规范

每篇文章遵循统一格式:

- 行数: 300-400 行 (不超过 420)
- 语言: 中文
- 结构: 标题 → 元信息(难度/领域/阅读时间) → 引言(日常类比) → 编号章节 → 代码/表格 → 总结 → 参考文献
- 文件命名: kebab-case, 放在 `docs/<layer>/papers/` 下
- 计划文件: `plans/layer<N>-<name>.json` (JSON 数组, 每项含 slug + title + description)
