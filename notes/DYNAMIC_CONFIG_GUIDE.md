# 🎛️ 动态参数控制指南

## 概述

新增的动态参数控制系统允许你在不重启服务器的情况下实时调整关键参数，极大提高了调试和优化效率。

## 🔥 热更新功能 (无需重启)

### 1. 实时FPS控制
- **API**: `POST /api/config/fps`
- **Web UI**: 拖动FPS滑块 (5-60)
- **效果**: 立即调整数据流帧率

```javascript
// 前端调用示例
fetch('/api/config/fps', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({target_fps: 45})
});
```

### 2. dB阈值动态调整
- **API**: `POST /api/config/threshold`
- **Web UI**: 拖动dB阈值滑块 (-120dB 到 -60dB)
- **效果**: 实时过滤噪声，改善显示效果

```javascript
// 调整多个阈值
fetch('/api/config/threshold', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        threshold_db: -90.0,           // FFT数据过滤阈值
        magnitude_threshold_db: -70.0, // 帧发送阈值
        similarity_threshold: 0.92     // 相似度跳帧阈值
    })
});
```

### 3. 压缩级别优化
- **API**: `POST /api/config/compression`
- **Web UI**: 拖动压缩级别滑块 (1-9)
- **效果**: 平衡传输速度与CPU占用

```javascript
// 调整压缩级别
fetch('/api/config/compression', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({compression_level: 9})
});
```

### 4. 过滤功能开关
- **API**: `POST /api/config/filter`
- **效果**: 启用/禁用智能跳帧和自适应FPS

```javascript
// 切换过滤功能
fetch('/api/config/filter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        enable_smart_skip: false,    // 禁用智能跳帧
        enable_adaptive_fps: true    // 启用自适应FPS
    })
});
```

## 🎯 预设配置系统

### 快速预设
Web界面提供四个一键预设按钮：

1. **平衡模式** (默认推荐)
   - dB阈值: -100dB
   - 目标FPS: 30
   - 压缩级别: 6
   - 适合大多数场景

2. **低噪声模式** (高灵敏度)
   - dB阈值: -120dB
   - 目标FPS: 30
   - 压缩级别: 9
   - 适合安静环境

3. **强信号模式** (抗干扰)
   - dB阈值: -80dB
   - 目标FPS: 60
   - 压缩级别: 3
   - 适合嘈杂环境

4. **性能优先** (低CPU占用)
   - dB阈值: -90dB
   - 目标FPS: 15
   - 压缩级别: 9
   - 适合长时间监控

### 预设API调用
```javascript
// 应用预设
fetch('/api/config/apply_preset/balanced', {
    method: 'POST'
});
```

## 📊 配置监控

### 获取当前配置
```bash
curl http://localhost:8380/api/config/current
```

### 查看所有预设
```bash
curl http://localhost:8380/api/config/presets
```

## 🔧 高级用法

### 场景1: 调试新设备
```javascript
// 1. 先降低阈值，查看所有信号
await updateThreshold(-120);

// 2. 提高FPS，获得更高时间分辨率  
await updateFPS(60);

// 3. 降低压缩级别，减少延迟
await updateCompression(3);
```

### 场景2: 长期监控优化
```javascript
// 1. 应用性能预设
await applyPreset('performance');

// 2. 根据环境微调
await updateThreshold(-85);  // 稍微提高阈值
await updateFPS(10);         // 进一步降低FPS
```

### 场景3: 实时演示优化
```javascript
// 1. 应用强信号模式
await applyPreset('high_signal');

// 2. 提高帧率获得流畅显示
await updateFPS(60);

// 3. 降低压缩获得最低延迟
await updateCompression(1);
```

## 🔍 API端点总览

| 端点 | 方法 | 功能 | 重启需求 |
|------|------|------|----------|
| `/api/config/fps` | POST | 调整目标FPS | ❌ 热更新 |
| `/api/config/threshold` | POST | 调整各种阈值 | ❌ 热更新 |
| `/api/config/compression` | POST | 调整压缩级别 | ❌ 热更新 |
| `/api/config/filter` | POST | 切换过滤功能 | ❌ 热更新 |
| `/api/config/current` | GET | 获取当前配置 | - |
| `/api/config/presets` | GET | 获取所有预设 | - |
| `/api/config/apply_preset/{name}` | POST | 应用预设 | ❌ 热更新 |

## ⚠️ 注意事项

1. **参数范围限制**:
   - FPS: 1-120 (推荐5-60)
   - dB阈值: -200dB 到 0dB
   - 压缩级别: 1-9

2. **性能影响**:
   - 高FPS + 低压缩 = 高CPU占用
   - 低阈值 = 更多数据传输
   - 关闭智能跳帧 = 更多网络流量

3. **Web UI同步**:
   - API调用会自动更新Web界面滑块
   - 页面刷新会重置为服务器当前值

4. **配置持久性**:
   - 动态配置在服务器重启后会重置
   - 如需永久配置，请修改.env文件

## 🚀 未来扩展

目前支持的是热更新参数，未来版本将支持：

### 温重启参数 (计划中)
- 采样率调整
- FFT大小变更
- 窗函数类型切换
- 音频块大小调整

### 冷重启参数 (计划中)
- 音频设备切换
- 服务器端口更改
- 日志级别调整

## 💡 使用技巧

1. **渐进式调优**: 从默认预设开始，逐步微调
2. **实时反馈**: 观察Web界面的系统日志了解效果
3. **性能监控**: 通过`/api/status`监控帧率和客户端数
4. **备份配置**: 记录好用的参数组合用于后续复用

---

**现在就可以在Web界面 (http://localhost:8380) 体验这些动态控制功能！** 🎉