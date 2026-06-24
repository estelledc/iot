# 传感器数据融合卡尔曼滤波实现详解
> **难度**：🔴 高级 | **领域**：数据融合算法 | **阅读时间**：约 25 分钟

## 引言

想象你在盲人摸象——只摸象腿会以为是柱子, 只摸象鼻会以为是蛇。单一传感器就像只摸一个部位, 得到的信息永远不完整。数据融合就是让你同时摸到象腿和象鼻, 再把信息综合起来, 最终还原出完整的大象。卡尔曼滤波则是最经典的"信息综合器"——它不是简单取平均, 而是根据每个信息源的可靠程度, 做加权最优估计。

## 1. 数据融合的动机

### 1.1 单一传感器的局限

任何传感器都有先天缺陷:

- 精度有限: 测量值与真值之间始终存在偏差
- 噪声干扰: 环境电磁干扰、量化噪声等引入随机误差
- 量程与带宽限制: 一种传感器无法覆盖所有工作范围
- 故障脆弱性: 单点故障导致整个系统失效

以IoT资产追踪为例, GPS能提供全局位置但更新率低(1-10Hz)且室内不可用, IMU能提供高频率(100-1000Hz)的姿态信息但存在累积漂移。两者单独使用都无法满足实时追踪的需求。

### 1.2 互补信息融合

不同传感器的弱点往往是互补的:

| 传感器 | 优势 | 劣势 |
|--------|------|------|
| GPS | 全局定位, 无漂移 | 低更新率, 室内失效 |
| IMU | 高频, 短期精确 | 角度漂移累积 |
| 气压计 | 垂直高度参考 | 受天气影响 |
| 磁力计 | 航向参考 | 受铁磁干扰 |

数据融合的核心思想: 用A的优势弥补B的劣势, 反之亦然, 最终得到比任何单一传感器都更可靠的估计。

## 2. 卡尔曼滤波的直觉

### 2.1 加权平均的本质

卡尔曼滤波的本质是一种递归加权平均。假设你有两个独立估计:

- 预测值 x_pred, 方差 P_pred
- 测量值 z, 方差 R

卡尔曼增益K决定了你更信任谁:

```
K = P_pred / (P_pred + R)
x_est = x_pred + K * (z - x_pred)
```

当R很小(测量很准)时, K趋近1, 你更信任测量; 当P_pred很小(预测很准)时, K趋近0, 你更信任预测。这就是卡尔曼滤波的核心直觉——谁更可靠就听谁的。

### 2.2 递归计算的优势

卡尔曼滤波不需要存储历史数据。每一时刻只需:

1. 基于上一时刻的状态做预测
2. 用当前测量修正预测

这种递归特性使它非常适合资源受限的嵌入式系统。

## 3. 状态空间模型

### 3.1 状态向量

状态向量x包含你想估计的所有变量。对于资产追踪的6自由度模型:

```
x = [px, py, pz, vx, vy, vz]^T
```

其中px/py/pz是三维位置, vx/vy/vz是三维速度。

### 3.2 状态转移方程

```
x_k = F * x_{k-1} + B * u_{k-1} + w_{k-1}
```

- F: 状态转移矩阵, 描述系统动力学
- B: 控制输入矩阵, 描述外部输入的影响
- u: 控制输入(如加速度计读数)
- w: 过程噪声, 协方差为Q

对于匀速运动模型:

```
F = [1  0  0  dt  0   0 ]
    [0  1  0  0   dt  0 ]
    [0  0  1  0   0   dt]
    [0  0  0  1   0   0 ]
    [0  0  0  0   1   0 ]
    [0  0  0  0   0   1 ]
```

### 3.3 观测方程

```
z_k = H * x_k + v_k
```

- H: 观测矩阵, 将状态映射到测量空间
- v: 测量噪声, 协方差为R

GPS只测位置不测速度时:

```
H = [1 0 0 0 0 0]
    [0 1 0 0 0 0]
    [0 0 1 0 0 0]
```

## 4. 卡尔曼滤波算法步骤

### 4.1 预测步(Predict)

状态外推:

```
x_pred = F * x_est_{k-1} + B * u_{k-1}
```

协方差传播:

```
P_pred = F * P_{k-1} * F^T + Q
```

Q是过程噪声协方差, 代表模型的不确定性。Q越大, 滤波器对预测的信心越低, 会更依赖测量。

### 4.2 更新步(Update)

卡尔曼增益:

```
K = P_pred * H^T * (H * P_pred * H^T + R)^(-1)
```

状态修正:

```
x_est = x_pred + K * (z_k - H * x_pred)
```

其中(z_k - H * x_pred)称为新息(Innovation), 即测量与预测的差值。

协方差更新:

```
P = (I - K * H) * P_pred
```

或使用Joseph形式(数值更稳定):

```
P = (I - K * H) * P_pred * (I - K * H)^T + K * R * K^T
```

### 4.3 完整循环示意

```
初始化: x_0, P_0
循环:
  1. x_pred = F * x + B * u
  2. P_pred = F * P * F^T + Q
  3. K = P_pred * H^T * inv(H * P_pred * H^T + R)
  4. x = x_pred + K * (z - H * x_pred)
  5. P = (I - K * H) * P_pred
```

## 5. Q和R矩阵的调参

### 5.1 Q矩阵: 过程噪声

Q反映你对模型的确信程度:

- Q过大: 滤波器过于信任测量, 响应快但噪声抑制差
- Q过小: 滤波器过于信任模型, 延迟大但平滑

经验法则: Q的对角元素可以设为"模型在两个采样周期内可能偏离的方差"。对于匀速模型, 位置的过程噪声大约是0.5*a_max*dt^2对应的方差。

### 5.2 R矩阵: 测量噪声

R反映传感器的实际精度:

- 从传感器数据手册获取标称值
- 在静态条件下采集数据, 计算实际方差
- R通常比标称值设大一些, 更鲁棒

### 5.3 Q/R比值的关键作用

真正影响滤波器行为的不是Q和R的绝对值, 而是它们的比值:

- Q/R大: 滤波器带宽高, 跟踪快但噪声大
- Q/R小: 滤波器带宽低, 平滑但跟踪慢

实际调试时, 先固定R为传感器实测方差, 再调Q直到获得满意的响应速度。

## 6. 扩展卡尔曼滤波(EKF)

### 6.1 非线性系统的挑战

标准卡尔曼滤波要求状态转移和观测都是线性的。但现实中:

- 雷达测距: r = sqrt(x^2 + y^2), 非线性观测
- 姿态运动学: 四元数更新, 非线性状态转移
- 电池模型: 非线性电压-电流特性

### 6.2 Jacobian线性化

EKF的核心思想: 在当前估计点对非线性函数做一阶Taylor展开, 用Jacobian矩阵替代F和H。

非线性函数f(x)和h(x), 对应的Jacobian:

```
F_jacobian = df/dx | x=x_est     (状态转移Jacobian)
H_jacobian = dh/dx | x=x_pred    (观测Jacobian)
```

EKF的预测和更新步骤与标准KF完全相同, 只需用F_jacobian和H_jacobian替换F和H。

### 6.3 EKF的局限

- 线性化误差: 强非线性时, 一阶近似不够准确
- 不保证最优: 与标准KF不同, EKF只是次优估计
- Jacobian计算: 需要解析求导或数值差分, 增加实现复杂度
- 发散风险: 初始估计偏差大时, 线性化误差可能导致滤波器发散

## 7. 实践案例: IMU+GPS融合资产追踪

### 7.1 系统架构

6自由度状态向量:

```
x = [px, py, pz, vx, vy, vz, roll, pitch, yaw]^T
```

传感器配置:

- IMU(MPU6050): 100Hz, 提供加速度和角速度作为控制输入
- GPS: 5Hz, 提供位置测量
- 磁力计: 50Hz, 提供航向参考

### 7.2 融合策略

```
预测步(100Hz, IMU驱动):
  - 用加速度计积分更新位置和速度
  - 用陀螺仪积分更新姿态

更新步(5Hz, GPS驱动):
  - 当GPS数据到达时, 用位置测量修正位置和速度
  - 新息过大时标记GPS可能的异常

更新步(50Hz, 磁力计驱动):
  - 用磁力计修正航向角
```

### 7.3 典型性能指标

| 指标 | 仅GPS | IMU+GPS融合 |
|------|-------|-------------|
| 位置精度 | 2-5m | 0.5-1.5m |
| 更新率 | 5Hz | 100Hz |
| 室内可用 | 否 | 短期可用(IMU推算) |
| 漂移 | 无 | 长期有(需GPS修正) |

## 8. MCU上的实现考量

### 8.1 矩阵运算

6自由度EKF涉及6x6矩阵运算。MCU上需考虑:

- 栈空间: 避免在栈上分配大矩阵, 使用静态或堆内存
- 运算量: 矩阵乘法O(n^3), 6x6约216次乘法, 可接受
- 库选择: ARM CMSIS-DSP提供优化的矩阵运算, 利用M4F的FPU

### 8.2 定点数考量

对于无FPU的MCU(如Cortex-M0):

- 使用Q15或Q31定点格式
- 注意矩阵求逆的精度损失, 定点数下更严重
- 考虑对状态变量做缩放, 使数值范围接近
- 协方差矩阵P的元素范围可能很大, 定点表示困难

### 8.3 内存优化

```
6自由度EKF内存需求估算:
- x: 6*4 = 24字节
- P: 6*6*4 = 144字节
- F: 6*6*4 = 144字节
- Q: 6*6*4 = 144字节
- H: 3*6*4 = 72字节
- R: 3*3*4 = 36字节
- 临时矩阵: ~500字节
总计: ~1KB, 对大多数MCU可接受
```

## 9. 互补滤波器: 轻量替代方案

### 9.1 原理

互补滤波器是卡尔曼滤波的极简版本, 只需一行代码:

```
angle = alpha * (angle + gyro * dt) + (1 - alpha) * acc_angle
```

- alpha接近1: 更信任陀螺仪(高通)
- alpha接近0: 更信任加速度计(低通)

### 9.2 与卡尔曼滤波的关系

互补滤波器本质上是频域上的融合:

- 高频段: 信任陀螺仪(加速度计高频噪声大)
- 低频段: 信任加速度计(陀螺仪低频漂移)

一阶互补滤波器等价于一维稳态卡尔曼滤波。当Q和R不随时间变化时, K收敛到常数, 就退化为互补滤波器。

### 9.3 适用场景

- 资源极度受限(8位MCU, <1KB RAM)
- 只需姿态估计(不需要速度、位置等额外状态)
- 精度要求不高(alpha取0.96-0.98即可)

## 10. 传感器融合库

### 10.1 Madgwick滤波器

专为AHRS(姿态航向参考系统)设计:

- 基于梯度下降的姿态优化
- 只需陀螺仪和加速度计(磁力计可选)
- 单参数(beta)调参, 比EKF简单得多
- 计算量远小于EKF, 适合低功耗MCU

### 10.2 Mahony滤波器

基于SO(3)上的互补滤波:

- 显式处理陀螺仪偏差补偿
- 对磁力计干扰更鲁棒
- 两个参数(Kp, Ki)调参
- 同样适合MCU实现

### 10.3 库选型建议

| 场景 | 推荐 | 理由 |
|------|------|------|
| 仅需姿态 | Madgwick | 简单高效, 单参数 |
| 需偏差补偿 | Mahony | 显式偏差估计 |
| 需位置+姿态 | EKF | 统一框架, 统一调参 |
| 极端资源受限 | 互补滤波 | 几乎零开销 |

## 11. 调试技巧

### 11.1 新息序列监控

新息(innovation) = z - H * x_pred, 它是白噪声序列时说明滤波器工作正常:

- 计算新息的自相关, 若非白噪声则模型不匹配
- 绘制新息时间序列, 应围绕零波动, 无明显趋势
- 新息方差应等于(H * P_pred * H^T + R)的理论值

### 11.2 NIS检查

归一化新息平方(Normalized Innovation Squared):

```
NIS = (z - H*x_pred)^T * S^(-1) * (z - H*x_pred)
```

其中S = H * P_pred * H^T + R是新息协方差。

NIS应服从卡方分布。对于m维测量:

- NIS的均值应约等于m
- 如果NIS持续远大于m, 说明滤波器过于自信(P太小或R太大)
- 如果NIS持续远小于m, 说明滤波器不够自信(P太大或R太小)

### 11.3 常见调试流程

1. 先在Python/MATLAB上仿真验证算法正确性
2. 检查新息是否为白噪声, NIS是否合理
3. 若滤波器发散: 检查F矩阵是否正确, Q是否过小
4. 若滤波器跟踪太慢: 增大Q或减小R
5. 若滤波器噪声太大: 减小Q或增大R
6. 部署到MCU前, 先在PC上用真实传感器数据验证

## 12. 代码示例: 一维温度传感器融合

以下C代码实现两个温度传感器的1D卡尔曼融合:

```c
#include <stdint.h>

// 1D Kalman Filter for temperature sensor fusion
typedef struct {
    float x;      // state estimate
    float P;      // estimation error covariance
    float Q;      // process noise covariance
    float R;      // measurement noise covariance
} KalmanFilter1D;

void kf_init(KalmanFilter1D* kf, float x0, float P0, float Q, float R) {
    kf->x = x0;
    kf->P = P0;
    kf->Q = Q;
    kf->R = R;
}

// Predict step (constant model: temperature doesn't change fast)
void kf_predict(KalmanFilter1D* kf) {
    // State extrapolation: x_pred = x (constant model)
    // Covariance propagation: P_pred = P + Q
    kf->P = kf->P + kf->Q;
}

// Update step with measurement z
void kf_update(KalmanFilter1D* kf, float z) {
    // Kalman gain
    float K = kf->P / (kf->P + kf->R);

    // State correction
    kf->x = kf->x + K * (z - kf->x);

    // Covariance update
    kf->P = (1.0f - K) * kf->P;
}

// Fuse two temperature sensors
// sensor1: high accuracy, slow response (e.g., PT100 RTD)
// sensor2: low accuracy, fast response (e.g., thermistor)
float fuse_temperature(float t1, float t2,
                       KalmanFilter1D* kf1, KalmanFilter1D* kf2) {
    // Update each filter with its sensor reading
    kf_predict(kf1);
    kf_update(kf1, t1);

    kf_predict(kf2);
    kf_update(kf2, t2);

    // Weighted combination based on covariance
    // Lower covariance -> higher weight
    float w1 = 1.0f / kf1->P;
    float w2 = 1.0f / kf2->P;
    float fused = (w1 * kf1->x + w2 * kf2->x) / (w1 + w2);

    return fused;
}

// Example usage
int main(void) {
    KalmanFilter1D kf_rtd, kf_ntc;

    // RTD: accurate (R=0.01), slow dynamics
    kf_init(&kf_rtd, 25.0f, 1.0f, 0.001f, 0.01f);

    // NTC: noisy (R=0.25), fast dynamics
    kf_init(&kf_ntc, 25.0f, 1.0f, 0.01f, 0.25f);

    // Simulated readings
    float rtd_reading = 25.3f;
    float ntc_reading = 24.8f;

    float result = fuse_temperature(rtd_reading, ntc_reading,
                                    &kf_rtd, &kf_ntc);
    // result is closer to rtd_reading because RTD has lower R

    return 0;
}
```

## 总结

卡尔曼滤波是传感器数据融合的基石。理解它的关键是抓住三个核心:

1. **加权平均直觉**: 卡尔曼增益自动平衡预测与测量的可信度
2. **Q/R调参**: Q/R的比值决定滤波器的带宽和跟踪特性, 调参时先固定R再调Q
3. **递归结构**: 只需上一时刻状态和当前测量, 内存和计算量都可控

从实践路径看:

- 1D融合: 直接用1D KF, 代码量极小
- 姿态估计: Madgwick/Mahony滤波器, 不必自己写EKF
- 位置+姿态: EKF统一框架, 注意Jacobian计算和数值稳定性
- 极端受限: 互补滤波器, 几乎零成本

调试时始终监控新息序列和NIS, 它们是滤波器健康的"体检指标"。

## 参考文献

1. Welch G, Bishop G. An Introduction to the Kalman Filter. UNC Chapel Hill, 2006.
2. Madgwick SOH. An Efficient Orientation Filter for Inertial and Inertial-Magnetic Sensor Arrays. University of Bristol, 2010.
3. Mahony R, Hamel T, Pflimlin JM. Nonlinear Complementary Filters on the Special Orthogonal Group. IEEE Transactions on Automatic Control, 2008.
4. Simon D. Optimal State Estimation: Kalman, H Infinity, and Nonlinear Approaches. Wiley, 2006.
5. Bar-Shalom Y, Li XR, Kirubarajan T. Estimation with Applications to Tracking and Navigation. Wiley, 2001.
