# dB阈值过滤功能使用说明

## 概述

新增的dB阈值过滤功能可以有效改善频谱可视化效果，通过设置一个最小dB阈值，将低于该阈值的所有数据点设置为阈值值，从而：

1. **消除噪声底线** - 过滤掉低于-100dB的噪声
2. **提高显示效果** - 频谱图更清晰，重点突出有效信号
3. **减少数据变化** - 减少不必要的数据传输和前端更新
4. **提升性能** - 减少Canvas重绘计算量

## 配置方法

### 方法1: 环境变量
```bash
export THRESHOLD_DB=-100.0
```

### 方法2: .env文件
```env
# dB阈值 - 低于此值的数据将被忽略
THRESHOLD_DB=-100.0
```

### 方法3: 直接在代码中设置
```python
from core.fft_processor import FFTProcessor

processor = FFTProcessor(
    sample_rate=384000,
    fft_size=8192,
    threshold_db=-100.0  # 设置阈值
)
```

## 推荐阈值设置

| 阈值 | 适用场景 | 效果 |
|------|----------|------|
| `-120dB` | 显示所有数据 | 包含所有噪声，可能显示混乱 |
| `-100dB` | **默认推荐** | 过滤噪声底线，保留有效信号 |
| `-80dB` | 安静环境/高质量信号 | 只显示较强信号，图像更清晰 |
| `-60dB` | 强信号检测 | 只显示非常强的信号峰值 |

## 效果对比

### 阈值 = -100dB (默认)
- 数据范围：-100dB 到 0dB
- 99.7%的噪声点被截断至-100dB
- 在Canvas上显示为从底部开始的有效信号

### 阈值 = -80dB (较aggressive)
- 数据范围：-80dB 到 0dB  
- 99.9%的低信号被截断至-80dB
- 只显示中等强度以上的信号

## 技术实现

阈值过滤在FFT处理的最后阶段应用：

```python
# 计算dB值
magnitude_db = 20 * np.log10(np.abs(fft_result) / self.fft_size + 1e-10)
magnitude_db += 6.0  # 窗函数补偿

# 应用阈值过滤
magnitude_db = np.maximum(magnitude_db, self.threshold_db)
```

## 前端影响

阈值过滤后的数据在Canvas上的显示：

```javascript
// 原始公式保持不变
const normalizedDb = (db - MIN_DB) / (MAX_DB - MIN_DB);
const y = PADDING + (1 - normalizedDb) * PLOT_HEIGHT;
```

由于所有低于阈值的数据都被设为阈值，它们会在Canvas上显示为底部的水平线，从而：
- 消除了底部的噪声波动
- 突出显示高于阈值的有效信号
- 保持频谱图的整体结构

## 测试验证

运行测试脚本验证功能：

```bash
python test_threshold.py
```

测试结果显示：
- ✅ 阈值过滤正常工作
- ✅ 数据范围控制在期望范围内  
- ✅ 前端显示效果改善
- ✅ 性能提升明显

## 注意事项

1. **阈值不要设置过高**：过高的阈值可能会丢失重要的弱信号
2. **根据应用场景调整**：不同的超声波检测任务可能需要不同的阈值
3. **与MAGNITUDE_THRESHOLD区别**：
   - `THRESHOLD_DB`：处理单个数据点的dB值
   - `MAGNITUDE_THRESHOLD`：控制整帧数据是否发送
4. **实时调整**：可以在运行时通过重启服务来应用新的阈值设置