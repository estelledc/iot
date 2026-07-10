---
schema_version: '1.0'
id: ota-firmware-update-mcu
title: MCU OTA固件更新机制与双Bank设计
layer: 1
content_type: technical_analysis
difficulty: intermediate
reading_time: 20
prerequisites:
  - bootloader-design-embedded
  - eeprom-vs-flash-data-storage
  - arm-trustzone-iot-security
tags:
  - OTA
  - 双Bank
  - 引导加载程序
  - 固件签名
  - 差分更新
  - MCUboot
  - 回滚
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# MCU OTA固件更新机制与双Bank设计

> **难度**：🟡 中级 | **领域**：固件更新架构 | **关键词**：OTA, A/B, MCUboot, 验签 | **阅读时间**：约 20 分钟

## 日常类比

手机系统出 Bug 若不能在线更新，就得去售后刷机。现场上万台物联网（Internet of Things, IoT）设备若无空中下载（Over-The-Air, OTA），修 Bug 只能上门或召回，成本远超物料清单（Bill of Materials, BOM）。OTA 不是锦上添花，而是“更新失败也不能变砖”的基础设施[1][4]。

## 摘要

说明微控制器（Microcontroller Unit, MCU）Flash 分区、单/双 Bank、校验与回滚、差分更新与安全验签。具体 API 以 ESP-IDF、MCUboot 等现行文档为准[1][2]。

## 1. 为何与端到端流程

| 场景 | 无 OTA | 有 OTA |
|------|--------|--------|
| 修 Bug | 上门/召回 | 远程推送 |
| 安全补丁 | 长期暴露 | 可快速响应 |
| 功能演进 | 难 | 可持续 |

云端发布 → 设备下载到非活动槽 → 完整性/签名校验 → 切换启动槽 → 健康确认；失败则回滚[1][4]。

## 2. 单 Bank vs 双 Bank

| 方案 | Flash | 断电安全 | 回滚 | 适用 |
|------|-------|----------|------|------|
| 单 Bank | 省 | 差（写活动区易砖） | 难 | 仅极成本敏感且可接受风险 |
| 双 Bank（A/B） | 约 2× 应用区 | 写非活动槽 | 自然支持 | 量产默认 |

双 Bank：版本元数据 + 启动尝试计数；应用“确认成功”前失败即回滚。镜像头含版本、尺寸、哈希；传输常用 HTTPS 分块与断点续传[1][2]。

## 3. 校验、安全与差分

三层常见：传输/存储 CRC 或哈希防损坏；SHA-256 等完整性；ECDSA/RSA 验签防篡改。另需防回滚版本计数器，避免重放旧漏洞固件[2][4]。

| 差分方案 | 特点 | 限制 |
|----------|------|------|
| bsdiff 等 | 补丁小 | 设备端 RAM/CPU 与基线版本绑定 |
| 全量 | 简单 | 带宽大 |

差分适合带宽贵的蜂窝节点，但要验证合成后大小与签名仍覆盖最终镜像[3]。

## 4. 失败模式

| 失败 | 预防 |
|------|------|
| 写入中断电 | 只写非活动 Bank |
| 空间不足 | 链接脚本/CI 检查镜像≤槽 |
| 配置不兼容 | NVS 结构版本 + 回滚 |
| 下载中断 | 断点续传 + 最终哈希 |

## 5. 局限、挑战与可改进方向

### 1. Flash 成本与分区碎片

**局限**：双 Bank 挤占数据区或迫使更大 Flash。
**改进**：外部 Flash；压缩镜像；评估单 Bank+恢复分区的风险接受度[1]。

### 2. 验签与安全启动未贯通

**局限**：只 HTTPS 无安全启动，仍可被刷恶意包。
**改进**：安全启动 + 签名镜像 + 防回滚熔丝/计数器[2][4]。

### 3. 差分基线漂移

**局限**：现场版本碎片导致补丁失败。
**改进**：限制支持的基线集合；失败回落全量；云端跟踪版本矩阵[3]。

### 4. 确认逻辑不完善导致误回滚/变砖

**局限**：应用未及时“mark OK”或健康检查过严/过松。
**改进**：明确确认点（连云成功等）；尝试次数与退避策略可配置[1][2]。

## 总结

量产 MCU OTA 默认双 Bank + 哈希验签 + 启动确认回滚；差分与压缩是带宽优化而非安全替代。目标是失败可恢复，而不是“能升上去”。

## 参考文献

[1] Espressif, ESP-IDF OTA 指南.
[2] MCUboot Project, Secure Bootloader Documentation.
[3] C. Percival, bsdiff/bspatch.
[4] NIST SP 800-193, Platform Firmware Resiliency.
[5] IETF SUIT / 相关固件更新架构草案与 RFC 背景.
[6] ARM Trusted Firmware / 安全启动实践文档.
[7] ESP32 分区表与 OTA API 文档.
[8] AES/ECDSA 固件签名实现应用笔记.
[9] 蜂窝 IoT 差分更新带宽案例研究.
[10] Flash 磨损与 OTA 写入策略文献.
[11] 断点续传与 A/B 状态机设计实践.
[12] OWASP IoT 固件更新安全建议.
