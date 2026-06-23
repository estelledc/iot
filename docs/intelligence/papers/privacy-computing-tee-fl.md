# 隐私计算：TEE 加联邦学习联合方案

> **难度**：🟡 中级 | **领域**：隐私计算、可信执行环境、联邦学习 | **阅读时间**：约 22 分钟

## 日常类比

想象几家医院想联合研究一种罕见病（联合训练模型），但患者数据不能出院（隐私法规）。传统做法是把数据集中到一个地方分析，但这违反隐私规定。

联邦学习的方案是：每家医院在本地训练模型，只把"学到的经验"（模型参数）发给中央服务器汇总。但这还不够安全——有人可能从参数中反推出原始数据（梯度攻击）。

TEE（可信执行环境）就像一个"密封的保险箱"：数据进去后，即使服务器管理员也看不到里面在算什么。把联邦学习的聚合过程放在 TEE 里，就像在银行金库里开会——参与者的秘密在金库里合并，出来的只有最终结果。

## 1. 隐私威胁与保护需求

### 1.1 边缘 AI 的隐私风险

| 威胁类型 | 描述 | 影响 | 典型场景 |
|----------|------|------|----------|
| 数据泄露 | 原始数据被窃取 | 直接暴露隐私 | 设备被盗/入侵 |
| 模型逆向 | 从模型推断训练数据 | 间接泄露 | 模型被下载分析 |
| 梯度攻击 | 从梯度重建原始样本 | FL 场景 | 恶意聚合服务器 |
| 成员推断 | 判断某样本是否在训练集中 | 隐私确认 | 模型 API 暴露 |
| 模型窃取 | 复制模型知识产权 | 商业损失 | 边缘设备逆向 |

### 1.2 保护目标

- **数据隐私**：原始数据不离开设备
- **模型隐私**：模型参数不被窃取
- **计算隐私**：推理过程不被观察
- **结果隐私**：输出不泄露输入信息

## 2. TEE 技术详解

### 2.1 主流 TEE 方案对比

| 特性 | ARM TrustZone | Intel SGX | ARM CCA | RISC-V Keystone |
|------|--------------|-----------|---------|-----------------|
| 架构 | 双世界隔离 | Enclave | Realm | Enclave |
| 内存保护 | 硬件分区 | 加密+完整性 | GPT 隔离 | PMP + 加密 |
| 可用内存 | 灵活配置 | 128-512 MB | 灵活 | 灵活 |
| 性能开销 | <5% | 5-30% | <10% | 5-15% |
| 远程证明 | 有限 | 完整 | 完整 | 可选 |
| IoT 适用性 | 最佳 | 服务器/PC | 未来边缘 | 新兴 |
| 成熟度 | 高 | 高 | 中（2024+） | 低 |

### 2.2 ARM TrustZone 架构

```
+--------------------------------------------------+
|                  应用处理器                        |
|  +-------------------+  +---------------------+  |
|  |   Normal World    |  |   Secure World      |  |
|  |   (REE)           |  |   (TEE)             |  |
|  |                   |  |                     |  |
|  | +------+ +------+ |  | +-------+ +------+ |  |
|  | | App1 | | App2 | |  | | TA1   | | TA2  | |  |
|  | +------+ +------+ |  | +-------+ +------+ |  |
|  |                   |  |                     |  |
|  | +------+          |  | +-------+           |  |
|  | | OS   |          |  | | TEE OS|           |  |
|  | +------+          |  | +-------+           |  |
|  +-------------------+  +---------------------+  |
|              |  Monitor (EL3)  |                  |
+--------------+----------------+------------------+

TA = Trusted Application (可信应用)
REE = Rich Execution Environment (普通执行环境)
```

### 2.3 TEE 中的模型保护

```c
// OP-TEE 可信应用示例：在 TEE 中执行模型推理
// 文件: ta/ml_inference_ta.c

#include <tee_internal_api.h>

// 模型权重存储在安全内存中
static float model_weights[MODEL_SIZE] __attribute__((section(".secure_data")));

TEE_Result TA_InvokeCommandEntryPoint(uint32_t cmd_id, 
                                       TEE_Param params[4]) {
    switch (cmd_id) {
        case CMD_LOAD_MODEL:
            // 从安全存储加载加密模型
            return load_encrypted_model(params[0].memref.buffer,
                                       params[0].memref.size);
        
        case CMD_INFERENCE:
            // 在安全世界中执行推理
            float *input = (float *)params[0].memref.buffer;
            float *output = (float *)params[1].memref.buffer;
            
            // 推理计算完全在 TEE 内完成
            // 即使 Normal World 被攻破，也无法窃取模型
            run_inference(model_weights, input, output);
            
            return TEE_SUCCESS;
        
        case CMD_SECURE_AGGREGATE:
            // 安全聚合：多方梯度在 TEE 内合并
            return secure_federated_aggregate(params);
    }
    return TEE_ERROR_NOT_SUPPORTED;
}

// Normal World 调用接口
// 文件: host/main.c
void run_secure_inference(float *input, float *output) {
    TEEC_Session session;
    TEEC_Operation op;
    
    // 打开与 TA 的会话
    TEEC_OpenSession(&ctx, &session, &ta_uuid, ...);
    
    // 准备参数
    op.params[0].memref.buffer = input;
    op.params[0].memref.size = INPUT_SIZE * sizeof(float);
    op.params[1].memref.buffer = output;
    op.params[1].memref.size = OUTPUT_SIZE * sizeof(float);
    
    // 调用安全推理
    TEEC_InvokeCommand(&session, CMD_INFERENCE, &op, NULL);
    
    // output 中是推理结果，但模型权重从未离开 TEE
    TEEC_CloseSession(&session);
}
```

## 3. 联邦学习基础

### 3.1 FedAvg 算法

```python
import torch
import copy

class FederatedServer:
    """联邦学习服务器"""
    
    def __init__(self, global_model, n_clients):
        self.global_model = global_model
        self.n_clients = n_clients
    
    def fedavg_round(self, client_updates, client_sizes):
        """
        FedAvg 聚合
        client_updates: 各客户端的模型参数
        client_sizes: 各客户端的数据量（用于加权）
        """
        total_size = sum(client_sizes)
        global_dict = self.global_model.state_dict()
        
        # 加权平均
        for key in global_dict:
            global_dict[key] = sum(
                client_updates[i][key] * (client_sizes[i] / total_size)
                for i in range(len(client_updates))
            )
        
        self.global_model.load_state_dict(global_dict)
        return self.global_model.state_dict()


class FederatedClient:
    """联邦学习客户端（边缘设备）"""
    
    def __init__(self, model, local_data, device_id):
        self.model = model
        self.data = local_data
        self.device_id = device_id
    
    def local_train(self, global_weights, n_epochs=5, lr=0.01):
        """本地训练"""
        self.model.load_state_dict(global_weights)
        optimizer = torch.optim.SGD(self.model.parameters(), lr=lr)
        
        for epoch in range(n_epochs):
            for batch_x, batch_y in self.data:
                pred = self.model(batch_x)
                loss = torch.nn.functional.cross_entropy(pred, batch_y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
        
        return self.model.state_dict(), len(self.data)
```

### 3.2 联邦学习的隐私漏洞

即使不共享原始数据，梯度也可能泄露信息：

```python
def gradient_inversion_attack(gradient, model, dummy_data_shape):
    """
    梯度反演攻击：从梯度重建原始数据
    证明单纯的 FL 不足以保护隐私
    """
    # 随机初始化假数据
    dummy_data = torch.randn(dummy_data_shape, requires_grad=True)
    dummy_label = torch.randn(1, requires_grad=True)
    
    optimizer = torch.optim.LBFGS([dummy_data, dummy_label])
    
    for i in range(300):
        def closure():
            optimizer.zero_grad()
            pred = model(dummy_data)
            loss = F.cross_entropy(pred, dummy_label.argmax().unsqueeze(0))
            
            # 计算假数据的梯度
            dummy_grad = torch.autograd.grad(loss, model.parameters(), create_graph=True)
            
            # 最小化假梯度与真实梯度的差异
            grad_diff = sum(
                ((dg - rg) ** 2).sum() 
                for dg, rg in zip(dummy_grad, gradient)
            )
            grad_diff.backward()
            return grad_diff
        
        optimizer.step(closure)
    
    # dummy_data 可能非常接近原始训练数据！
    return dummy_data.detach()

# 实验结果：
# - 单张图片：PSNR > 30 dB（几乎完美重建）
# - batch=1 时最危险
# - batch=32 时攻击难度显著增加
```

## 4. TEE + FL 联合方案

### 4.1 安全聚合架构

```
客户端 1 (边缘设备)          TEE 聚合服务器           客户端 2 (边缘设备)
+------------------+      +------------------+      +------------------+
| 本地数据         |      | Secure Enclave   |      | 本地数据         |
| 本地训练         |      |                  |      | 本地训练         |
| 加密梯度 --------|----->| 解密             |<-----|----- 加密梯度    |
|                  |      | 聚合             |      |                  |
|                  |      | 加密结果         |      |                  |
| <-- 聚合结果 ----|<-----| 发送给各客户端   |----->|---- 聚合结果 --> |
+------------------+      +------------------+      +------------------+

关键：聚合过程在 TEE 内完成，服务器管理员也无法看到各客户端的梯度
```

### 4.2 TEE 辅助安全聚合实现

```python
class TEESecureAggregation:
    """TEE 辅助的安全聚合"""
    
    def __init__(self, n_clients, model_size):
        self.n_clients = n_clients
        # 模拟 TEE 环境（实际部署用 OP-TEE/SGX SDK）
        self.enclave_key = self._generate_enclave_key()
    
    def client_encrypt_and_send(self, client_id, model_update):
        """客户端加密模型更新"""
        # 用 TEE 的公钥加密
        encrypted = self._encrypt(model_update, self.enclave_key.public)
        # 附加远程证明（证明 TEE 是真实的）
        attestation = self._get_attestation()
        return encrypted, attestation
    
    def secure_aggregate_in_tee(self, encrypted_updates):
        """
        在 TEE 内部执行聚合
        外部无法观察中间状态
        """
        # === 以下代码在 TEE 内执行 ===
        decrypted_updates = []
        for enc_update in encrypted_updates:
            # 在 TEE 内解密
            update = self._decrypt_in_enclave(enc_update)
            decrypted_updates.append(update)
        
        # 聚合（简单平均或加权平均）
        aggregated = {}
        for key in decrypted_updates[0]:
            aggregated[key] = torch.stack(
                [u[key] for u in decrypted_updates]
            ).mean(dim=0)
        
        # 可选：添加差分隐私噪声
        if self.dp_enabled:
            for key in aggregated:
                noise = torch.normal(0, self.dp_sigma, aggregated[key].shape)
                aggregated[key] += noise
        
        # 加密聚合结果后发出
        # === TEE 执行结束 ===
        return self._encrypt_result(aggregated)
    
    def verify_attestation(self, attestation):
        """
        远程证明验证
        客户端验证服务器确实在 TEE 中运行
        """
        # 验证签名链
        # 验证 enclave 度量值（代码哈希）
        # 验证 TEE 硬件真实性
        return self._verify_signature_chain(attestation)
```

### 4.3 性能开销分析

| 操作 | 无保护 | 仅 FL | FL + DP | FL + TEE | FL + HE |
|------|--------|-------|---------|----------|---------|
| 通信量/轮 | N/A | 1x | 1x | 1.1x | 10-100x |
| 聚合延迟 | N/A | 10 ms | 12 ms | 15 ms | 5000 ms |
| 客户端计算 | 1x | 1x | 1.05x | 1.02x | 50-100x |
| 隐私保证 | 无 | 弱 | 中(epsilon) | 强 | 最强 |
| 实用性 | - | 高 | 高 | 高 | 低 |

## 5. 隐私保护方案全景对比

### 5.1 技术对比

| 方案 | 保护对象 | 计算开销 | 通信开销 | 精度影响 | 成熟度 |
|------|---------|---------|---------|---------|--------|
| 差分隐私 (DP) | 统计隐私 | 极低 | 无 | 有（噪声） | 高 |
| 同态加密 (HE) | 计算隐私 | 极高 (1000x) | 高 | 无 | 中 |
| 安全多方计算 (MPC) | 计算隐私 | 高 (10-100x) | 高 | 无 | 中 |
| TEE | 计算+数据 | 低 (5-30%) | 低 | 无 | 高 |
| 联邦学习 (FL) | 数据不出域 | 低 | 中 | 轻微 | 高 |
| FL + TEE | 数据+梯度 | 低 | 低 | 无 | 中高 |
| FL + DP | 数据+统计 | 极低 | 无 | 有 | 高 |

### 5.2 选型决策

```
需要隐私保护？
|-- 数据不能出设备？
|   |-- 是 -> 联邦学习 (基础方案)
|   |       |-- 担心梯度泄露？
|   |       |   |-- 有 TEE 硬件 -> FL + TEE (推荐)
|   |       |   |-- 无 TEE -> FL + DP (加噪声)
|   |       |   +-- 精度要求极高 -> FL + MPC (慢但精确)
|   |       +-- 不担心 -> 纯 FL 即可
|   +-- 否 -> 集中式训练 + DP/匿名化
|
|-- 模型不能被窃取？
|   |-- 有 TEE -> 模型加密存储 + TEE 内推理
|   +-- 无 TEE -> 模型混淆 + 水印
|
+-- 推理过程不能被观察？
    |-- TEE 内推理 (最佳)
    +-- 同态加密推理 (极慢，仅限简单模型)
```

## 6. 实际部署架构

### 6.1 工业 IoT 隐私计算架构

```python
class IndustrialPrivacySystem:
    """工业 IoT 隐私计算系统架构"""
    
    def __init__(self, factories, central_server):
        """
        factories: 多个工厂的边缘节点
        central_server: 配备 TEE 的聚合服务器
        """
        self.factories = factories
        self.server = central_server
        
    def training_pipeline(self):
        """完整训练流程"""
        
        # 1. 远程证明：各工厂验证服务器 TEE 真实性
        for factory in self.factories:
            attestation = self.server.get_attestation()
            assert factory.verify_attestation(attestation), "TEE 验证失败"
        
        # 2. 密钥协商：建立安全通道
        session_keys = self.server.key_exchange(self.factories)
        
        # 3. 联邦训练循环
        for round_id in range(100):
            # 各工厂本地训练
            updates = []
            for factory in self.factories:
                local_update = factory.local_train(
                    global_model=self.server.get_global_model(),
                    epochs=5
                )
                # 加密后发送
                encrypted = factory.encrypt(local_update, session_keys[factory.id])
                updates.append(encrypted)
            
            # TEE 内安全聚合
            new_global = self.server.secure_aggregate(updates)
            
            # 4. 可选：聚合后添加 DP 噪声（双重保护）
            if self.dp_enabled:
                new_global = self.add_dp_noise(new_global, epsilon=1.0)
        
        return self.server.get_global_model()
```

### 6.2 合规性映射

| 法规要求 | 技术实现 | 验证方式 |
|----------|---------|---------|
| GDPR 数据最小化 | FL（数据不出域） | 网络流量审计 |
| GDPR 被遗忘权 | 联邦遗忘学习 | 模型更新证明 |
| 数据本地化 | 边缘计算 + FL | 部署架构审计 |
| 处理透明性 | TEE 远程证明 | 证明报告 |
| 安全保障 | TEE + 加密传输 | 渗透测试 |
| 中国个保法 | 数据不出境 + 最小必要 | 合规评估 |

## 7. 实践建议

### 7.1 初学者入门路径

1. **第一步**：用 Flower 框架搭建基础联邦学习系统（2 个客户端 + 1 个服务器）
2. **第二步**：实现梯度反演攻击，直观理解 FL 的隐私漏洞
3. **第三步**：添加差分隐私（Opacus 库），观察隐私-精度权衡
4. **第四步**：在 RPi 上部署 OP-TEE，运行简单的安全计算
5. **第五步**：将 FL 聚合逻辑移入 TEE，实现完整的 FL+TEE 方案

### 7.2 具体调优建议

- **DP 噪声预算**：epsilon=1-10 是实用范围；epsilon<1 精度损失大，>10 保护弱
- **FL 通信优化**：梯度压缩（Top-K 稀疏化）可减少 90% 通信量，对精度影响 <1%
- **TEE 内存限制**：SGX 的 EPC 只有 128-512 MB，大模型需要分块处理
- **聚合频率**：不必每个 batch 都聚合，每 5-10 个 epoch 聚合一次可大幅减少通信
- **客户端选择**：每轮随机选择 10-30% 的客户端参与，减少通信压力

### 7.3 常见陷阱

- DP 的 epsilon 是累积的——100 轮训练每轮 epsilon=0.1，总隐私预算可能远超 10
- TEE 不是万能的——侧信道攻击（如时序分析、功耗分析）仍可能泄露信息
- FL 中的 Non-IID 数据分布会严重影响收敛——用 FedProx 或 SCAFFOLD 缓解
- 不要在 TEE 外打印调试信息——这会泄露 enclave 内的中间状态
- 远程证明的验证逻辑必须在客户端实现——服务器自证清白没有意义

### 7.4 开源工具推荐

| 工具 | 用途 | 语言 | 适用场景 |
|------|------|------|----------|
| Flower | 联邦学习框架 | Python | 快速原型 |
| PySyft | 隐私计算 | Python | 研究 |
| Opacus | 差分隐私训练 | Python | PyTorch 集成 |
| OP-TEE | ARM TEE 开发 | C | 嵌入式部署 |
| Gramine | SGX 应用移植 | C | 服务器 TEE |
| TF Federated | 联邦学习 | Python | TensorFlow 生态 |

## 参考文献

1. McMahan, B. et al. "Communication-Efficient Learning of Deep Networks from Decentralized Data (FedAvg)." AISTATS 2017.
2. Bonawitz, K. et al. "Practical Secure Aggregation for Privacy-Preserving Machine Learning." CCS 2017.
3. Zhu, L. et al. "Deep Leakage from Gradients." NeurIPS 2019.
4. Sabt, M. et al. "Trusted Execution Environment: What It is, and What It is Not." IEEE TrustCom 2015.
5. Mo, F. et al. "Machine Learning with Confidential Computing: A Systematization of Knowledge." ACM Computing Surveys 2024.
6. Abadi, M. et al. "Deep Learning with Differential Privacy." CCS 2016.
7. Li, T. et al. "Federated Optimization in Heterogeneous Networks (FedProx)." MLSys 2020.
8. ARM. "Arm Confidential Compute Architecture (CCA)." Technical Documentation, 2023.
9. Kairouz, P. et al. "Advances and Open Problems in Federated Learning." Foundations and Trends in ML 2021.
10. EU GDPR. "General Data Protection Regulation." Official Journal of the European Union, 2016.
