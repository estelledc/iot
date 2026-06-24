# 激光雷达ToF测距原理与点云生成

> **难度**：🔴 高级 | **领域**：激光测距、3D感知、自动驾驶 | **阅读时间**：约 25 分钟

## 日常类比

想象你站在一条长长的走廊尽头，对着墙壁拍一下手。声音以约 340 m/s 的速度传过去，碰到墙壁再弹回来。你用手表计时，从拍手到听到回声用了 0.1 秒，那么墙壁距离就是 340 × 0.1 ÷ 2 = 17 米。激光雷达的 ToF（Time of Flight）测距做的是完全一样的事情——只不过把"拍手"换成发射一束激光脉冲，把"耳朵"换成光电探测器，而"声音"换成了光速（3×10⁸ m/s），计时精度需要达到纳秒甚至皮秒级别。

但一个点只能测一个距离。要还原整面墙壁的形状，你得"转头"朝不同方向各拍一次手。机械旋转式 LiDAR 就是这么做的——一个激光器装在马达上 360° 旋转，每转一圈打出几十万个点，拼出来的就是周围环境的三维"点云"。固态 LiDAR 则不用马达，而是用微镜芯片（MEMS）或相控阵（OPA）来偏转光束，就像你不用转头，而是用一面小镜子把声音"反射"到不同方向。

最后，点云就像用无数颗钉子钉在墙上标记轮廓——每颗钉子的坐标 (x, y, z) 告诉你空间中一个点的位置。成百上千万颗钉子密密麻麻地排列，就能还原出街道、车辆、行人的三维形状。自动驾驶汽车就是靠这种"钉子地图"来感知周围世界的。

## 1. 激光物理基础与眼安全分级

### 1.1 半导体激光器工作原理

LiDAR 发射端普遍采用半导体激光器，其核心是 p-n 结谐振腔。正向偏置电流超过阈值 $I_{th}$ 后，粒子数反转实现受激辐射放大，谐振腔解理面构成 Fabry-Pérot 腔输出相干光。常用波长与材料：

| 波长 (nm) | 半导体材料 | 典型应用 | 大气穿透性 |
|-----------|-----------|---------|-----------|
| 905 | InGaAs / AlGaAs | 机械旋转 LiDAR | 好（近红外窗口） |
| 940 | InGaAs | 短距 ToF 测距 | 好 |
| 1550 | InGaAsP / InP | 人眼安全长距 LiDAR | 极好（电信窗口） |
| 1310 | InGaAsP | 光纤通信兼用 | 好 |

### 1.2 IEC 60825 眼安全分级

人眼对激光的安全耐受量取决于波长和曝光时间。视网膜对 400-1400 nm 的光最为敏感（晶状体会聚焦光束到视网膜），而 > 1400 nm 的光在到达视网膜前已被角膜和房水大量吸收，因此容许更高的发射功率。

| 安全等级 | 条件 | 对 LiDAR 设计的影响 |
|---------|------|-------------------|
| Class 1 | 任何条件下无危害 | 1550 nm 可用更高功率（角膜吸收），905 nm 功率受限 |
| Class 1M | 光学仪器观察有危害 | 禁止裸眼 + 望远镜场景，需标注 |
| Class 3R | 直接照射有潜在危害 | 车载 LiDAR 需确保安装高度避免直射人眼 |
| Class 3B | 直接照射危险 | 禁用于消费级产品 |

**关键设计约束**：905 nm LiDAR 的单脉冲能量受 Class 1 限制约 10 nJ（脉宽 3-5 ns），而 1550 nm 在同等安全等级下允许高出 1-2 个数量级，因此长距（>200 m）LiDAR 几乎全部采用 1550 nm。

## 2. 直接ToF与间接ToF

### 2.1 直接ToF（dToF）

dToF 直接测量激光脉冲从发射到接收的往返时间 $\Delta t$，距离计算公式：

$$R = \frac{c \cdot \Delta t}{2}$$

其中 $c = 3 \times 10^8$ m/s 为光速。

**工作流程**：
1. 激光驱动电路产生 ns 级窄脉冲（典型峰值功率 10-100 W）
2. 脉冲出发瞬间启动 TDC（Time-to-Digital Converter）
3. APD / SPAD 探测器接收回波光子，产生电脉冲
4. TDC 停止计时，输出 $\Delta t$ 数字码

**dToF 关键参数**：

| 参数 | 典型值 | 决定因素 |
|------|-------|---------|
| 脉宽 | 3-10 ns | 距离精度 vs 峰值功率 |
| TDC 分辨率 | 30-100 ps | 对应 4.5-15 mm 距离精度 |
| TDC 量程 | 200-400 ns | 对应 30-60 m 量程 |
| 单次测距精度 | ±1-3 cm | TDC 精度 + jitter |
| 多脉冲累加 | 64-256 次 | 降方差，精度提升 $\sqrt{N}$ 倍 |

### 2.2 间接ToF（iToF）

iToF 不直接测时间，而是测量连续调制光与接收光之间的相位差 $\Delta\phi$：

$$R = \frac{c}{4\pi f_{mod}} \cdot \Delta\phi$$

其中 $f_{mod}$ 为调制频率。通过四个相位采样点（0°, 90°, 180°, 270°）解调：

$$\Delta\phi = \arctan\left(\frac{S_1 - S_3}{S_0 - S_2}\right)$$

**iToF 优缺点**：

| 对比维度 | dToF | iToF |
|---------|------|------|
| 测距原理 | 脉冲飞行时间 | 连续波相位差 |
| 测距范围 | 数米至数百米 | 通常 < 10 m |
| 精度 | ±1-3 cm（长距） | ±1-5 mm（短距） |
| 功耗 | 高（峰值功率大） | 低（连续低功率） |
| 阳光干扰 | 较好（窄脉冲+门控） | 较差（直流分量叠加） |
| 多径干扰 | 弱 | 强（连续调制易混叠） |
| 典型应用 | 车载 LiDAR | 手机 Face ID / AR |

### 2.3 混合方案：多频率 iToF

为克服 iToF 的相位模糊问题（$R_{max} = c / (2f_{mod})$），工业界采用双频或多频调制：

- 低频 $f_1 = 20$ MHz → 无模糊范围 7.5 m
- 高频 $f_2 = 100$ MHz → 高精度（1.5 mm 级）

两个频率分别解算后，用中国剩余定理（CRT）合成大范围高精度结果。索尼 DepthSense IMX570 即采用此方案。

## 3. 扫描机制

### 3.1 机械旋转式

传统方案：激光收发模块安装于旋转台，电机驱动 360° 匀速旋转。16/32/64/128 线对应垂直方向多发多收通道，水平分辨率由转速和脉冲频率决定（典型 0.1°-0.4°），转速 5-20 Hz。

优点：技术成熟、视场角大（360°×40°）、等角采样均匀。缺点：体积大功耗高、轴承磨损、振动下标定漂移。

### 3.2 MEMS 微镜

在硅基底上制造微机电谐振镜，静电力或电磁力驱动二维谐振偏转，光学偏转角可达 ±30°。谐振频率 $f_{res} = \frac{1}{2\pi}\sqrt{k/J}$，扫描轨迹 $\theta(t) = \theta_{max} \sin(2\pi f_{res} t)$。

挑战：谐振非线性需角度编码器校正；大偏转角需高驱动电压与 CMOS 兼容性差；125°C 车载环境长期谐振的材料疲劳风险。

### 3.3 光学相控阵（OPA）

借鉴雷达相控阵原理：芯片上集成数百个微型光波导，各路相位调制器（热光/电光效应）控制出射光远场干涉，偏转角满足 $\sin\theta = \Delta\phi \cdot \lambda / (2\pi d)$。

**OPA 当前状态**：

| 指标 | 当前水平 | 目标 |
|------|---------|------|
| 水平视场角 | 80-100° | 120° |
| 垂直视场角 | 10-20° | 25° |
| 波束宽度 | 0.1-0.2° | <0.1° |
| 旁瓣抑制 | 10-15 dB | >20 dB |
| 功耗 | 1-3 W | <1 W |

### 3.4 Flash LiDAR

Flash 不扫描，扩散器将激光均匀照射整个视场，SPAD 阵列（如 256×128）同时采集所有像素飞行时间。优点：全固态、帧率极高（>1000 fps）、全局快门无运动畸变。缺点：功率分散致探测距离受限（<50 m），阳光下信噪比差。

### 3.5 扫描机制对比

| 机制 | 视场角 | 线数 | 距离 | 帧率 | 成本趋势 | 可靠性 |
|------|-------|------|------|------|---------|--------|
| 机械旋转 | 360°×40° | 16-128 | 200+ m | 10-20 Hz | 高 → 中 | 中（磨损） |
| MEMS 微镜 | 120°×25° | 等效 100+ | 150-200 m | 10-30 Hz | 中 → 低 | 高 |
| OPA 相控阵 | 100°×20° | 等效 200+ | 150-250 m | 10-20 Hz | 高 → 低 | 极高 |
| Flash | 60°×20° | 128×256 | 20-50 m | 30-1000 Hz | 中 → 低 | 极高 |

## 4. 点云数据结构与格式

### 4.1 点云数学表示

一个点云帧 $\mathcal{P}$ 包含 $N$ 个点，每个点由多维向量描述：

$$\mathcal{P} = \{\mathbf{p}_i\}_{i=1}^{N}, \quad \mathbf{p}_i = (x_i, y_i, z_i, I_i, t_i, r_i)$$

- $(x, y, z)$：3D 坐标（LiDAR 本体坐标系）
- $I$：回波强度（intensity），反映目标反射率
- $t$：时间戳（微秒级），用于运动补偿
- $r$：回波序号（双回波 LiDAR 的第一/二回波）

### 4.2 PCD 格式

PCD（Point Cloud Data）是 ROS PCL 社区广泛使用的点云格式，支持 ASCII 和 binary 两种存储模式。

```text
# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity ring time
SIZE 4 4 4 4 2 8
TYPE F F F F U F
COUNT 1 1 1 1 1 1
WIDTH 150000
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS 150000
DATA binary
<binary data follows>
```

**字段说明**：`FIELDS` 为每点属性名；`SIZE` 为各属性字节数；`TYPE` 中 F=浮点、U=无符号整型、I=有符号整型；`WIDTH × HEIGHT` 为点云维度（无序点云 HEIGHT=1）；`VIEWPOINT` 为采集位姿 (tx ty tz qw qx qy qz)。

### 4.3 LAS 格式

LAS 是美国 ASPRS 制定的激光雷达点云标准格式，广泛用于测绘和 GIS 领域。

| LAS 版本 | 点记录格式 | 特性 |
|----------|-----------|------|
| 1.2 | 0-5 | GPS 时间、RGB、回波信息 |
| 1.3 | 6-10 | 波形数据（全波形 LiDAR） |
| 1.4 | 6-10 | 256 类分类、扩展头 |

LAS 文件结构：公共头 → VLR（变长记录）→ 点数据记录 → EVLR。点记录格式 6 每点占 30 字节，含 (X, Y, Z, intensity, return_number, classification, GPS_time, RGB)。

### 4.4 格式选择指南

| 考量 | PCD | LAS | PLY | HDF5 |
|------|-----|-----|-----|------|
| ROS 兼容性 | ★★★ | ★ | ★★ | ★ |
| GIS 互操作 | ★ | ★★★ | ★ | ★★ |
| 大规模流式读取 | ★★ | ★★★ | ★ | ★★★ |
| 自定义属性 | ★★★ | ★★ | ★★★ | ★★★ |
| 压缩支持 | ★（binary） | ★★（LAZ） | ★ | ★★★ |

## 5. 雷达方程与信噪比分析

### 5.1 LiDAR 距离方程

对于扩展目标（目标截面积大于光斑），接收功率服从 LiDAR 距离方程：

$$P_r = \frac{P_t \cdot \eta_t \cdot \eta_r \cdot A_r \cdot \rho \cdot \cos\theta_i}{\pi R^2} \cdot e^{-2\alpha R}$$

其中：
- $P_t$：发射峰值功率
- $\eta_t, \eta_r$：发射/接收光学效率
- $A_r$：接收孔径面积
- $\rho$：目标朗伯反射率
- $\theta_i$：入射角
- $\alpha$：大气消光系数
- $R$：目标距离

注意接收功率按 $1/R^2$ 衰减（扩展目标），而非 $1/R^4$（点目标），这是 LiDAR 与微波雷达的关键区别。

### 5.2 信噪比

$$SNR = \frac{(P_r \cdot M \cdot R_\lambda)^2}{2q(P_r + P_b)M^2F \cdot B + i_n^2 \cdot B}$$

其中 $M$ 为 APD 倍增因子（50-100），$R_\lambda$ 为响应度，$P_b$ 为背景光功率，$F \approx M^{0.3}$ 为过剩噪声因子，$B$ 为带宽，$i_n$ 为噪声电流。SPAD 阵列光子计数服从泊松分布，探测概率：

$$P_d = 1 - \sum_{k=0}^{N_{th}-1} \frac{(\lambda_s + \lambda_b)^k}{k!} e^{-(\lambda_s + \lambda_b)}$$

其中 $\lambda_s$、$\lambda_b$ 分别为信号和背景光子平均计数。

### 5.3 大气衰减

不同天气下 905 nm 和 1550 nm 的大气消光系数 $\alpha$ (km⁻¹)：

| 天气条件 | 905 nm | 1550 nm | 最大探测距离比 (1550/905) |
|---------|--------|---------|--------------------------|
| 晴天 | 0.07 | 0.05 | 1.4× |
| 轻雾（能见度 3 km） | 1.3 | 0.9 | 1.4× |
| 浓雾（能见度 300 m） | 13 | 11 | 1.2× |
| 小雨（4 mm/h） | 0.4 | 0.3 | 1.3× |

由于衰减呈 $e^{-2\alpha R}$ 指数关系，1550 nm 长距优势显著。

## 6. LiDAR 类型综合对比

| 对比维度 | Velodyne VLP-16 | Hesai XT32 | Livox Mid-70 | Ouster OS1-128 | Continental ARS540 |
|---------|----------------|-----------|-------------|---------------|-------------------|
| 类型 | 机械旋转 | 机械旋转 | MEMS 扫描 | 机械旋转 | Flash |
| 线数 | 16 | 32 | 等效 100+ | 128 | 等效 128×256 |
| 波长 (nm) | 905 | 905 | 905 | 850 | 1550 |
| 最远距离 (m) | 100 | 200 | 260 | 120 | 30 |
| 距离精度 (cm) | ±3 | ±2 | ±2 | ±1.5 | ±3 |
| 视场角 | 360°×30° | 360°×31° | 70°×25° | 360°×45° | 120°×25° |
| 点率 (pts/s) | 300K | 640K | 200K | 2.6M | 12M |
| 功耗 (W) | 8 | 16 | 9 | 14 | 12 |
| 防护等级 | IP67 | IP67 | IP67 | IP68 | IP69K |
| 参考价格 | $4K | $8K | $1K | $4K | $3K |

**选型建议**：
- 低成本研发验证 → Livox Mid-70（MEMS，非重复扫描）
- 高线数自动驾驶 → Ouster OS1-128 或 Hesai XT32
- 短距补盲（近场感知）→ Continental ARS540 Flash
- 测绘/SLAM → Velodyne VLP-16（生态最成熟）

## 7. ROS 集成与点云处理

### 7.1 ROS2 驱动与发布

```python
#!/usr/bin/env python3
"""
LiDAR ROS2 驱动示例：读取点云并发布 sensor_msgs/PointCloud2
适用于 Hesai / Velodyne 等机械旋转 LiDAR
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header

class LidarDriverNode(Node):
    def __init__(self):
        super().__init__('lidar_driver')
        # 声明参数：LiDAR 模型、IP、端口
        self.declare_parameter('lidar_model', 'hesai_xt32')
        self.declare_parameter('lidar_ip', '192.168.1.201')
        self.declare_parameter('lidar_port', 2368)
        self.declare_parameter('frame_id', 'lidar_top')

        # 创建发布者：点云话题，队列深度 5
        self.pub = self.create_publisher(
            PointCloud2, '/lidar/points', 5
        )

        # 点云字段定义：x, y, z, intensity, ring, timestamp
        self.fields = [
            PointField(name='x',    offset=0,  datatype=PointField.FLOAT32, count=1),
            PointField(name='y',    offset=4,  datatype=PointField.FLOAT32, count=1),
            PointField(name='z',    offset=8,  datatype=PointField.FLOAT32, count=1),
            PointField(name='intensity', offset=12, datatype=PointField.FLOAT32, count=1),
            PointField(name='ring', offset=16, datatype=PointField.UINT16, count=1),
            PointField(name='t',    offset=18, datatype=PointField.FLOAT64, count=1),
        ]
        self.point_step = 26  # 每点字节数: 4*3+4+2+8

        # 定时回调：以 LiDAR 转速频率触发
        self.timer = self.create_timer(0.1, self.publish_frame)

    def publish_frame(self):
        """从 LiDAR 硬件读取一帧并发布为 PointCloud2"""
        # 实际中通过 UDP socket 接收 LiDAR 原始包
        n_points = 64000  # XT32 一帧约 6.4 万点
        points = np.zeros(n_points, dtype=[
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('intensity', 'f4'), ('ring', 'u2'), ('t', 'f8'),
        ])
        # ... 解析 LiDAR 数据包填充 points ...

        # 构建 PointCloud2 消息
        msg = PointCloud2()
        msg.header = Header(
            stamp=self.get_clock().now().to_msg(),
            frame_id=self.get_parameter('frame_id').value,
        )
        msg.height = 1
        msg.width = n_points
        msg.fields = self.fields
        msg.is_bigendian = False
        msg.point_step = self.point_step
        msg.row_step = self.point_step * n_points
        msg.data = points.tobytes()
        msg.is_dense = True
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LidarDriverNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 7.2 运动补偿

车载 LiDAR 采集一帧需 50-100 ms，不做补偿则高速行驶时点云产生"拖影"模糊。方法：IMU 位姿插值 + 按时间戳反向变换到帧起始坐标系。

```python
import numpy as np
from scipy.interpolate import interp1d

def motion_compensation(points, poses, t_frame_start, t_frame_end):
    """
    点云帧内运动补偿
    points: (N, 6) — x, y, z, intensity, ring, timestamp
    poses: (M, 7) — timestamp, tx, ty, tz, roll, pitch, yaw
    """
    # 线性插值帧内任意时刻的位姿
    interp_x = interp1d(poses[:, 0], poses[:, 1:4], axis=0)
    interp_rot = interp1d(poses[:, 0], poses[:, 4:7], axis=0)

    compensated = points.copy()
    for i in range(len(points)):
        t_i = points[i, 5]  # 该点时间戳
        dt_pos = interp_x(t_i) - interp_x(t_frame_start)
        dt_rot = interp_rot(t_i) - interp_rot(t_frame_start)
        T_inv = se3_inverse(dt_pos, dt_rot)  # SE(3) 逆变换
        compensated[i, :3] = T_inv @ np.append(points[i, :3], 1.0)[:3]

    return compensated
```

## 8. 应用场景

### 8.1 自动驾驶感知

LiDAR 是 L3+ 自动驾驶的核心感知传感器，典型流水线：

1. **原始点云去噪**：统计滤波移除孤立点（离群点 < K 近邻阈值）
2. **地面分割**：RANSAC 拟合平面或 Ray-Ground Filter
3. **聚类分割**：欧氏聚类 / DBSCAN 提取目标点簇
4. **目标检测**：PointPillars / CenterPoint / VoxelNeXt
5. **目标跟踪**：AB3DMOT / CenterPoint Tracking

典型配置：1× 高线数 LiDAR（360° 远距）+ 2× 侧向补盲 LiDAR（120° 近距），覆盖 360° 感知。

### 8.2 高精地图构建

SLAM 算法（如 LIO-SAM、FAST-LIO2）将 LiDAR 点云与 IMU 数据紧耦合，实时估计车辆位姿并构建全局一致地图。建图流水线：回环检测（ScanContext）→ 位姿图优化（GTSAM/G2O）→ 地图产线（体素滤波 → 路面提取 → 矢量化 → 语义标注）。高精地图精度要求：绝对精度 < 10 cm，相对精度 < 5 cm。

### 8.3 精准农业

| 应用 | 方式 | 精度要求 |
|------|------|---------|
| 果树冠层体积估算 | 无人机搭载 LiDAR 扫描 | 5-10 cm |
| 行间导航 | 拖拉机前端 LiDAR 识别作物行 | 10-20 cm |
| 地形测绘 | 机载 LiDAR 生成 DEM | 5-15 cm |
| 障碍物检测 | 实时点云分割 | 30-50 cm |

### 8.4 其他领域

电力巡检（机载扫描检测导线弧垂）、矿山测量（井下 SLAM 构建巷道模型）、建筑 BIM（地面扫描仪生成毫米级点云）、智慧交通（路侧 LiDAR 统计车流量和检测违停）。

## 9. 挑战与局限

### 9.1 天气影响

**雨滴散射**：雨滴（直径 0.5-5 mm）对 905 nm 光的 Mie 散射截面显著，会在点云中产生"雨滴假目标"。抑制方法：连续帧统计异常点密度；利用雨滴"闪烁"特性（多帧间不稳定）与固体目标区分；雨天增大脉冲能量补偿衰减。

**浓雾衰减**：雾滴（直径 1-10 μm）的消光系数可达 10-50 km⁻¹，200 m 外目标几乎不可见。多传感器融合是唯一可靠方案——毫米波雷达在雾中穿透力远优于 LiDAR。

### 9.2 多径干扰

当激光脉冲经两个不同路径返回时（如地面→墙面→接收器），TDC 测到的时间不对应任何真实目标位置，产生"幽灵点"。

典型场景：镜面反射体（玻璃幕墙、湿路面）淹没漫反射；角落反射体（墙角、护栏）多次弹射产生虚假远距点；透明物体穿透后命中后方目标致距离偏大。

抑制方法：全波形 LiDAR 分解多回波峰值；检查点云局部邻域空间合理性；PointNet++ 等网络学习多径伪影模式。

### 9.3 运动模糊与时间标定

帧内运动模糊（见 7.2 节）是核心挑战。多传感器时间同步方面，PTP/gPTP 硬件同步误差 < 1 ms，软件同步误差 5-50 ms 在高速场景不可接受。

### 9.4 成本与量产

| 成本项 | 占比 | 下降路径 |
|--------|------|---------|
| 激光器 + 驱动 | 25-30% | VCSEL 阵列量产 |
| 探测器 | 20-25% | SPAD CMOS 工艺集成 |
| 光学组件 | 15-20% | 塑料透镜、模组集成 |
| 扫描机构 | 20-30% | OPA/MEMS 芯片化 |
| 腔体/标定 | 10-15% | 自动化产线标定 |

2020 年 64 线机械 LiDAR 约 $75K，2025 年同等性能已降至 $500-1000，距消费级 $100 仍有差距。

## 总结与展望

LiDAR 技术正处于从"机械旋转"向"全固态"演进的关键窗口期。三条技术路线（MEMS 微镜、OPA 相控阵、Flash 阵列）各有取舍：MEMS 最接近量产但偏转角受限；OPA 角度自由但旁瓣和效率仍是瓶颈；Flash 帧率无敌但距离和信噪比受限。短期内，MEMS + 905 nm 方案将是乘用车前装的主流选择；中长期，OPA + 1550 nm 有望在性能和成本上取得最优平衡。

从算法侧看，点云感知正经历从"手工特征 + 聚类"到"端到端深度学习"的范式迁移。VoxelNet → PointPillars → VoxelNeXt 一路走来，检测精度和推理速度同步提升。然而，纯 LiDAR 方案在恶劣天气下仍不可靠，与相机、毫米波雷达的多模态融合是工程落地的必由之路——BEV Fusion、TransFusion 等方案已显示出优于任何单传感器的鲁棒性。

对 IoT 从业者而言，LiDAR 不只是"贵的距离传感器"——它代表了从 2D 感知到 3D 空间理解的范式跨越。当单线 ToF 传感器（如 VL53L1X）成本降至 $1 以下，扫地机、无人机、服务机器人等消费级产品也将拥有 3D 视觉能力。理解 ToF 原理和点云处理流程，是打开这扇门的钥匙。

## 参考资料

1. Schwarz, B. "Mapping the World in 3D: The Future of LiDAR in Autonomous Vehicles." *IEEE Spectrum*, 2023.
2. McManamon, P. F. *Optical Phased Array for Lidar: A Technology Review.* SPIE, 2022.
3. IEC 60825-1:2014 — *Safety of laser products — Part 1: Equipment classification and requirements.*
4. Spies, M. & Spies, M. "SPAD-Based Direct Time-of-Flight LiDAR Sensors: A Review." *IEEE Sensors Journal*, 2023.
5. Qi, C. R. et al. "PointPillars: Fast Encoders for Object Detection from Point Clouds." *CVPR*, 2019.
6. Geiger, A. et al. "Are We Ready for Autonomous Driving? The KITTI Vision Benchmark Suite." *CVPR*, 2012.
7. Xu, W. & Zhang, F. "FAST-LIO2: Fast Direct LiDAR-Inertial Odometry." *IEEE T-RO*, 2022.
8. Kim, P. et al. "ScanContext: Egocentric Spatial Descriptor for Place Recognition." *IROS*, 2018.
9. Bai, X. et al. "TransFusion: Multi-Modal Fusion for 3D Object Detection with Transformer." *CVPR*, 2022.
10. Velodyne, Hesai, Ouster, Livox — 各厂商产品数据手册 (Datasheet), 2024.
