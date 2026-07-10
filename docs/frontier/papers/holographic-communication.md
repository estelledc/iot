---
schema_version: '1.0'
id: holographic-communication
title: 全息通信：从平面视频到三维临场
layer: 8
content_type: technical_analysis
difficulty: intermediate
reading_time: 28
prerequisites: UNKNOWN
tags:
- 全息通信
- 6G
- 点云
- CGH
- 体积视频
- NeRF
- 光场显示
- 边缘渲染
source_status: UNVERIFIED
review_status: IN_REVIEW
last_reviewed: '2026-07-10'
---
# 全息通信：从平面视频到三维临场

> **难度**：🟡 中级 | **领域**：全息显示、6G 通信、点云处理 | **阅读时间**：约 28 分钟

## 日常类比

想象视频通话的演进。最初是电话（只有声音），后来是视频通话（2D 画面），再后来是 VR（Virtual Reality，虚拟现实）会议（3D 沉浸但需戴头显）。全息通信是下一步——对方的立体影像直接出现在你面前，不需要任何穿戴设备，你可以从任何角度看到她，就像她真的站在那里一样。

再想想电影《星球大战》里莱娅公主的全息投影，或者《钢铁侠》里托尼操作的空中立体显示屏。这些科幻场景的实现需要解决两个核心问题：怎么"采集"一个人的 3D 信息（常需多相机阵列），以及怎么在远端"重建"这个 3D 影像（需要全息或光场显示技术）。

而连接这两端的"管道"——网络——需要传输的数据量远高于当前视频通话。这也是全息型通信常被讨论为第六代移动通信（6G）愿景应用，而非仅靠第五代（5G）即可全面落地的原因之一。

## 1. 全息通信基础

### 1.1 与现有视频通信对比

下表带宽/延迟为数量级示意，随分辨率、压缩与场景复杂度变化很大。

| 维度 | 2D 视频 | 立体视频 (3D) | 体积视频 | 全息通信 |
|------|---------|-------------|---------|---------|
| 视角 | 固定 | 双目 | 自由视角 | 完全自由 |
| 数据格式 | 像素矩阵 | 左右双流 | 点云/Mesh | 全息图 |
| 带宽需求（示意） | 约 5–50 Mbps | 约 20–100 Mbps | 约 0.1–10 Gbps | 原始可达 Tbps 量级；压缩后仍常需很高速率 |
| 延迟要求（示意） | <150 ms | <100 ms | <50 ms | 交互场景常希望数毫秒级 |
| 显示设备 | 屏幕 | 3D 屏/VR | VR/光场 | 全息显示器 |
| 交互性 | 无 | 有限 | 六自由度 | 完全自然 |
| 临场感 | 低 | 中 | 高 | 极高 |

### 1.2 全息信息量估算

下列估算用于建立数量级直觉；压缩比与点属性字节数因标准与实现而异。

```python
def holographic_data_requirements():
    """全息通信数据量估算"""
    
    # 基本参数
    hologram_resolution = 8192 * 8192  # 全息面板分辨率
    pixel_depth_bits = 32  # 相位+振幅信息
    framerate = 60  # fps
    
    # 原始全息数据率
    raw_bitrate_bps = hologram_resolution * pixel_depth_bits * framerate
    raw_tbps = raw_bitrate_bps / 1e12
    
    # 压缩后（压缩比高度依赖内容与算法，此处仅示意）
    compressed_gbps = raw_tbps * 1000 / 100  # 示意约 100 Gbps 量级
    
    # 点云替代方案（近期更可行）
    point_cloud_points = 1_000_000  # 100 万个点
    bits_per_point = 12 * 8  # xyz + 属性示意
    point_cloud_mbps = (point_cloud_points * bits_per_point * framerate) / 1e6
    
    return {
        'raw_hologram_tbps': f"{raw_tbps:.1f} Tbps",
        'compressed_hologram_gbps': f"{compressed_gbps:.0f} Gbps",
        'point_cloud_gbps': f"{point_cloud_mbps/1000:.1f} Gbps",
        'current_4k_video_mbps': '约 25 Mbps',
        'gap_factor': f"相对 4K 仍可能高数个数量级"
    }

# 示意：原始可达约百 Tbps 量级；压缩后仍可能需数十–百 Gbps；点云路径更低但仍远高于普通视频
```

## 2. 全息显示技术

### 2.1 显示原理分类

| 技术 | 原理 | 分辨率 | 视角 | 成熟度 | 代表 |
|------|------|--------|------|--------|------|
| CGH (Computer-Generated Holography，计算全息) | 光波干涉重建 | 极高 | 全 | 早期研究/原型 | 研究机构与实验室系统 |
| 光场显示 | 多方向光线控制 | 中 | 宽 | 原型/小规模商用 | Looking Glass 等 |
| 体积显示 | 3D 空间发光点 | 中 | 360° | 原型 | Voxon 等 |
| 扫描显示 | 高速旋转/振动 | 中 | 360° | 小尺寸商用 | Hypervsn 等 |
| 多层 LCD | 层叠显示深度 | 高 | 窄 | 研究 | 多层显示研究 |
| 全息胶片 | 记录干涉图样 | 极高 | 固定 | 成熟(静态) | 传统全息成像 |

### 2.2 计算全息图（CGH）

CGH 的核心机制：对场景中每个点（或面元）计算其在空间光调制器（Spatial Light Modulator, SLM）平面上的复振幅贡献并相干叠加，再驱动 SLM 调制照明光以重建波前。复杂度大致随点数 × 面板像素数增长，是实时全息的主要算力瓶颈。

```python
import numpy as np

class ComputerGeneratedHologram:
    """计算全息图生成（简化）"""
    
    def __init__(self, resolution=1024, wavelength_nm=532, pixel_pitch_um=1.0):
        self.N = resolution
        self.wavelength = wavelength_nm * 1e-9  # 转为米
        self.pitch = pixel_pitch_um * 1e-6
    
    def point_source_hologram(self, point_3d):
        """单点源全息图计算"""
        x0, y0, z0 = point_3d
        
        # 全息面坐标网格
        x = np.arange(self.N) * self.pitch - self.N * self.pitch / 2
        y = np.arange(self.N) * self.pitch - self.N * self.pitch / 2
        X, Y = np.meshgrid(x, y)
        
        # 计算从点源到全息面每个像素的距离
        r = np.sqrt((X - x0)**2 + (Y - y0)**2 + z0**2)
        
        # 球面波相位
        k = 2 * np.pi / self.wavelength
        phase = k * r
        
        # 全息图 = 参考波 + 物体波 的干涉
        hologram = np.cos(phase)  # 简化为实数全息
        return hologram
    
    def scene_hologram(self, point_cloud):
        """从点云生成全息图（叠加所有点的贡献）"""
        hologram = np.zeros((self.N, self.N))
        
        for point in point_cloud:
            # 每个点贡献一个球面波
            hologram += self.point_source_hologram(point[:3])
        
        # 归一化到 [0, 1] 用于 SLM 显示
        hologram = (hologram - hologram.min()) / (hologram.max() - hologram.min())
        return hologram
    
    def compute_complexity(self, n_points):
        """计算复杂度估算"""
        ops_per_point = self.N * self.N  # 每个点需要 NxN 次计算
        total_ops = n_points * ops_per_point
        
        return {
            'total_operations': total_ops,
            'at_60fps_tflops': total_ops * 60 / 1e12,
            'feasibility': 'GPU 可实时' if total_ops * 60 < 100e12 else '需专用硬件/近似算法'
        }
```

## 3. 3D 数据采集与表示

### 3.1 采集技术

| 方案 | 传感器 | 适用场景 | 质量 | 实时性 |
|------|--------|---------|------|--------|
| 多目相机阵列 | 数十至数百摄像头 | 演播室 | 极高 | 准实时 |
| 深度相机 (ToF) | 结构光/ToF（Time of Flight，飞行时间） | 室内 | 中 | 实时 |
| LiDAR | 激光雷达 | 大场景 | 高（几何） | 实时 |
| NeRF（Neural Radiance Fields，神经辐射场） | 少量照片 + AI | 静态/准静态 | 高 | 多为离线/加速推理 |
| 4D 雷达 | 毫米波 | 人体动作 | 低 | 实时 |

### 3.2 点云 vs 全息图

```
两种 3D 表示的对比：

点云（Point Cloud）：
  [x1,y1,z1,r1,g1,b1], [x2,y2,z2,r2,g2,b2], ...
  - 优点：直观、可编辑、易压缩（MPEG V-PCC/G-PCC）
  - 缺点：离散采样、有空洞、光照信息有限
  - 带宽：随点数、属性与帧率线性增长（常为 Gbps 量级挑战）
  - 标准：MPEG Point Cloud Compression (V-PCC, G-PCC)

全息图（Hologram）：
  2D 相位+振幅矩阵（复数场）
  - 优点：更完整的波前信息、可自然聚焦
  - 缺点：数据量巨大、计算复杂
  - 带宽：高分辨率面板 × 位深 × 帧率 → 原始可达 Tbps 量级
  - 压缩：全息特异性编码，压缩比高度依赖内容

实际路径（示意时间线，非承诺）：
近期: 体积视频（点云/Mesh）-> 数–数十 Gbps 挑战
中期: 光场视频 -> 更高带宽与边缘渲染
远期: 真全息 -> 需更高空口能力与专用显示
```

| 表示 | 存储对象 | 主要瓶颈 | 近期可部署性 |
|------|---------|---------|-------------|
| Mesh/点云 | 几何+属性 | 捕获标定、压缩、空洞 | 较高 |
| 光场 | 多视角光线 | 采集密度、显示角分辨率 | 中 |
| CGH 全息 | 复振幅面板 | 算力、SLM、带宽 | 较低 |

## 4. 压缩与传输

### 4.1 全息数据压缩

```python
class HolographicCompression:
    """全息数据压缩方案"""
    
    def point_cloud_compression(self, point_cloud):
        """点云压缩（MPEG V-PCC 思路）"""
        # 方法1: 3D -> 2D 投影后用视频编码（V-PCC）
        # 将点云投影到多个面，用 HEVC 编码 2D 图
        projections = self.project_to_patches(point_cloud)
        compressed_geometry = hevc_encode(projections['geometry'])
        compressed_color = hevc_encode(projections['color'])
        
        # 方法2: 八叉树（G-PCC）
        # 递归细分空间为八个子空间
        octree = self.build_octree(point_cloud, max_depth=12)
        compressed_octree = arithmetic_encode(octree)
        
        return {
            'v_pcc_ratio': '约 30–100x（示意）',
            'g_pcc_ratio': '约 10–30x（示意）',
            'ai_ratio': '视表示与失真约束（示意）'
        }
    
    def hologram_compression(self, hologram):
        """全息图压缩"""
        # 1. 相位解包 + 量化
        phase = np.angle(hologram)
        amplitude = np.abs(hologram)
        
        # 2. 频域压缩（全息图在频域常较稀疏）
        freq_domain = np.fft.fft2(hologram)
        # 保留显著系数（稀疏）
        threshold = np.percentile(np.abs(freq_domain), 95)
        sparse_freq = freq_domain * (np.abs(freq_domain) > threshold)
        
        # 3. 利用时间冗余（帧间预测）
        # 全息图相邻帧高度相关
        
        return {
            'spatial_compression': '数倍–十余倍（示意）',
            'frequency_sparsity': '视场景稀疏度',
            'temporal_prediction': '额外数倍（示意）',
            'total_achievable': '需按失真约束实测'
        }
```

### 4.2 6G 网络支持全息的要求

指标为目标/愿景量级对比，标准与实现会演进。

| 指标 | 5G（量级） | 6G（愿景量级） | 全息/沉浸媒体需求 | 差距判断 |
|------|----------|----------|---------|------|
| 峰值速率 | 约 20 Gbps | 可达 Tbps 愿景 | 视压缩后码率 | 真全息仍紧 |
| 用户体验速率 | 约百 Mbps | 更高 Gbps 愿景 | 常需 Gbps 级 | 仍有缺口 |
| 端到端延迟 | 约 ms 级 | 亚 ms 愿景 | 交互希望很低 | 6G 更友好 |
| 连接密度 | 高 | 更高 | 视场景 | 非主瓶颈 |
| 频谱效率 | 高 | 更高愿景 | 高 | 持续挑战 |

## 5. 边缘处理

### 5.1 全息渲染卸载

```
全息通信的边缘计算架构：

发送端：
[多相机阵列] -> [边缘服务器: 3D重建 + 压缩] -> [网络传输]
                      |
               点云生成 / NeRF 或 3DGS 推理
               数据压缩 (V-PCC/AI)
               算力需求：视分辨率与算法，常需高性能 GPU

接收端：
[网络接收] -> [边缘服务器: 解压 + CGH 计算] -> [全息显示器]
                      |
               数据解压缩
               全息图计算 (CGH)
               CGH 通常是算力大头

为什么需要边缘：
- 云端太远（往返延迟难满足强交互）
- 终端太弱（全息计算太密集）
- 边缘折中：算力靠近用户 + 延迟可控
```

### 5.2 AI 加速全息处理

加速比为文献/演示中常见量级示意，依赖基线实现。

| 处理环节 | 传统方法 | AI 加速方法 | 加速/收益（示意） |
|----------|---------|-----------|--------|
| 3D 重建 | 多视角立体匹配 | NeRF / 3D Gaussian Splatting（3DGS） | 质量或速度显著改善 |
| 点云压缩 | G-PCC 标准编码 | 学习型编码器 | 率失真可更优 |
| CGH 计算 | 角谱法逐点叠加 | 神经网络直接预测全息图 | 可达数量级加速 |
| 超分辨率 | 插值 | GAN/扩散模型 | 分辨率提升 |
| 动作预测 | 线性外推 | 序列模型预测 | 有助于掩盖网络抖动 |

## 6. 触觉集成

### 6.1 全息 + 触觉 = 更强临场

```
全息通信 + 触觉反馈 = 远程临场：

视觉通道：全息/光场显示（看到 3D 人物）
听觉通道：空间音频（声音来自正确方向）
触觉通道：力反馈手套/衣服（感受接触）

触觉通道需求（示意）：
- 更新率: 常需数百–上千 Hz（人体触觉灵敏）
- 延迟:  ideally 很低（过高会感到不同步）
- 空间分辨率: 指尖可达毫米级目标
- 力反馈: 覆盖精细到较大力的动态范围

应用场景：
- 远程手术：医生感受组织弹性（强监管）
- 远程维修：技师感受扭矩
- 社交：握手等接触感
- 教育：触摸虚拟标本
```

机制要点：视听可在数十毫秒内仍可接受，但触觉对延迟更敏感；多模态系统需统一时间戳与预测补偿，否则会出现"看到已握住、手感滞后"的违和。

## 7. 局限、挑战与可改进方向

### 1. 带宽与压缩仍远未闭环

**局限**：真全息原始码率过高；激进压缩易引入伪影，破坏临场感。
**改进**：近期主攻点云/Mesh + V-PCC/G-PCC；按注视点/感兴趣区分层传输；端到端率失真以主观临场感为指标。

### 2. CGH 实时算力墙

**局限**：高分辨率 SLM 上逐点叠加难以在通用 GPU 上稳定 60 fps。
**改进**：神经网络 CGH、稀疏/分层计算、FPGA/ASIC；先光场/体积显示降低对真全息的依赖。

### 3. 捕获系统昂贵且难标定

**局限**：多相机阵列成本高、同步与几何标定复杂，出演播室即退化。
**改进**：减少相机 + 学习重建（NeRF/3DGS）；深度相机混合；移动场景用 IMU 辅助外参。

### 4. 显示硬件成熟度不足

**局限**：大视角、高亮度、真彩色动态全息显示仍稀缺。
**改进**：产品路线先光场/体积商用；全息面板与激光安全规范并行；明确"无眼镜"与"近眼"两条产品线。

### 5. 多模态同步与安全伦理

**局限**：视听触不同步破坏体验；远程临场涉及生物特征与深度隐私。
**改进**：统一时钟与预测补偿；端侧脱敏与加密传输；高风险行业（医疗）单独认证路径。

## 8. 实践建议

### 8.1 初学者入门路径

1. **第一周**：了解光学基础（干涉、衍射），理解全息图原理
2. **第二周**：学习点云数据处理（Open3D/PCL），实现简单 3D 可视化
3. **第三周**：了解 MPEG 点云压缩标准（V-PCC/G-PCC），用参考软件实验
4. **第四周**：学习 NeRF / 3D Gaussian Splatting，从照片重建 3D 场景
5. **进阶**：研究 CGH 算法加速（GPU/FPGA）、全息显示硬件原理

### 8.2 具体调优建议

- **近期可行方案**：先做点云/Mesh 传输，不急于真全息
- **压缩优先级**：几何压缩通常比属性压缩更影响观感
- **帧率 vs 分辨率**：优先保证可接受帧率，分辨率可动态降级
- **边缘部署**：CGH/重建放在靠近用户的 GPU 边缘节点
- **渐进传输**：先传粗糙几何，再逐步细化（progressive coding）
- **标准关注**：跟踪 MPEG Immersive Video (MIV)、JPEG Pleno 与相关 ITU 研究

## 参考文献

[1] A. Clemm, M. T. Vega, H. K. Ravuri, T. Wauters, and F. De Turck, "Toward Truly Immersive Holographic-Type Communication: Challenges and Solutions," IEEE Communications Magazine, 2020.
[2] D. Blinder et al., "Signal Processing Challenges for Digital Holographic Video Display Systems," Signal Processing: Image Communication, 2019.
[3] E. C. Strinati et al., "6G: The Next Frontier: From Holographic Messaging to Artificial Intelligence Using Subterahertz and Visible Light Communication," IEEE Vehicular Technology Magazine, 2019.
[4] S. Schwarz et al., "Emerging MPEG Standards for Point Cloud Compression," IEEE Journal on Emerging and Selected Topics in Circuits and Systems, 2019.
[5] L. Shi, B. Li, C. Kim, P. Kellnhofer, and W. Matusik, "Towards Real-Time Photorealistic 3D Holography with Deep Neural Networks," Nature, 2021.
[6] B. Mildenhall et al., "NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis," Communications of the ACM, 2021.
[7] B. Kerbl, G. Kopanas, T. Leimkühler, and G. Drettakis, "3D Gaussian Splatting for Real-Time Radiance Field Rendering," ACM Transactions on Graphics, 2023.
[8] E. Sahin et al., "Computer-Generated Holograms for 3D Imaging: A Survey," ACM Computing Surveys, 2020.
[9] ITU-T FG-NET2030, "Network 2030: A Blueprint of Technology, Applications and Market Drivers Towards the Year 2030 and Beyond," ITU-T Technical Report, 2020.
[10] MPEG, "V-PCC and G-PCC: Point Cloud Compression Standards," ISO/IEC MPEG, 2020.
[11] T. Shimobaba et al., "Review of Fast Algorithms and Hardware Implementations for Computer-Generated Holography," IEEE Transactions on Industrial Informatics, 2016.
[12] X. Xu, Y. Pan, C. W. Liew, and H. Ren, "Holographic Display Technology: A Review," PhotoniX, 2021.
