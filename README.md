# Headless超声波可视化器

基于FastAPI + SSE的实时FFT数据流服务，支持前后端分离和远程监控。

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建conda环境
conda create -n headless-ultrasonic python=3.11 -y
conda activate headless-ultrasonic

# 安装依赖
pip install fastapi uvicorn pydantic numpy scipy sounddevice
```

### 2. 启动服务器

**方法一：直接运行**
```bash
cd headless_ultrasonic
python -c "
import uvicorn
from main import app
print('🎵 启动Headless超声波可视化器...')
print('服务器地址: http://localhost:8380')
uvicorn.run(app, host='0.0.0.0', port=8380, log_level='info')
"
```

**方法二：使用运行脚本（如果导入问题已修复）**
```bash
cd headless_ultrasonic  
python run.py
```

### 3. 访问服务

- **Web界面**: http://localhost:8380 - 🆕 **集成实时频谱可视化！**
- **API文档**: http://localhost:8380/docs  
- **SSE数据流**: http://localhost:8380/api/stream

### 🎨 Web界面功能

新的Web界面包含完整的可视化系统：

- **实时频谱图表** - 使用Chart.js显示0-100kHz频谱
- **实时数据指标** - FPS、峰值频率、声压级、数据速率等
- **系统控制面板** - 启停、FPS调节、连接状态
- **事件日志** - 实时显示数据接收和系统状态
- **数据导出** - 一键导出分析数据

## 📡 API端点

### 🆕 新架构API（每设备独立控制）

#### 系统级控制API
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/system/status` | GET | 获取系统整体状态 |
| `/api/system/devices` | GET | 列出所有设备（增强版） |
| `/api/system/devices/refresh` | POST | 刷新设备列表 |
| `/api/system/cleanup` | POST | 系统清理 |
| `/api/system/stop-all` | POST | 停止所有设备 |
| `/api/system/health` | GET | 系统健康检查 |
| `/api/system/performance` | GET | 系统性能统计 |

#### 每设备控制API
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/devices/{device_id}/start` | POST | 启动指定设备 |
| `/api/devices/{device_id}/stop` | POST | 停止指定设备 |
| `/api/devices/{device_id}/restart` | POST | 重启指定设备 |
| `/api/devices/{device_id}/status` | GET | 获取设备详细状态 |
| `/api/devices/{device_id}/stream` | GET | 设备专属SSE数据流 |
| `/api/devices/{device_id}/config/stream` | GET/POST | 获取/设置设备流配置 |
| `/api/devices/{device_id}/config/audio` | GET/POST | 获取/设置设备音频配置 |
| `/api/devices/{device_id}` | DELETE | 移除设备实例 |

#### 批量操作API
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/devices/batch/start` | POST | 批量启动设备 |
| `/api/devices/batch/stop` | POST | 批量停止设备 |

### 🔄 兼容性API（向后兼容）

#### 传统控制API
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/status` | GET | 获取系统状态 |
| `/api/start` | POST | 启动音频采集 |
| `/api/stop` | POST | 停止音频采集 |
| `/api/config/stream` | GET/POST | 获取/设置流配置 |
| `/api/config/fps` | POST | 快速设置FPS |
| `/api/devices` | GET | 列出音频设备及状态（使用稳定ID） |
| `/api/devices/{device_id}/status` | GET | 获取指定设备详细状态（支持稳定ID） |
| `/api/devices/mapping/info` | GET | 获取设备ID映射信息 |
| `/api/devices/mapping/cleanup` | POST | 清理无效的设备映射 |

#### 数据流API
| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/stream` | GET | SSE实时FFT数据流 |
| `/api/stream/test` | GET | SSE连接测试 |
| `/api/stream/stats` | GET | 流传输统计 |

## 🎯 稳定设备ID系统

为了解决设备索引变化的问题，系统采用了稳定的设备ID机制：

### 特性
- **持久化映射**: 设备ID映射保存到本地文件 `device_mapping.json`
- **智能生成**: 基于设备名称+硬件特征生成友好的稳定ID
- **自动清理**: 自动清理不存在的设备映射
- **向后兼容**: 保留系统索引作为参考

### ID格式示例
```
ultramicfefe12_a1b2c3  # UltraMic设备，基于硬件特征生成
builtinmic_d4e5f6      # 内置麦克风
usbheadset_g7h8i9      # USB耳机
```

### 映射文件位置
```
headless_ultrasonic/core/device_mapping.json
```

## 🔧 使用示例

### 1. 新架构API使用

#### 系统管理
```bash
# 获取系统整体状态
curl http://localhost:8380/api/system/status

# 列出所有设备（增强版）
curl http://localhost:8380/api/system/devices

# 刷新设备列表
curl -X POST http://localhost:8380/api/system/devices/refresh

# 系统健康检查
curl http://localhost:8380/api/system/health

# 停止所有设备
curl -X POST http://localhost:8380/api/system/stop-all
```

#### 单设备控制
```bash
# 启动指定设备（使用稳定ID）
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/start

# 获取设备详细状态
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/status

# 停止指定设备
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/stop

# 重启设备
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/restart

# 连接到设备专属数据流
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/stream
```

#### 设备配置管理
```bash
# 更新设备流配置
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/config/stream \
  -H "Content-Type: application/json" \
  -d '{"target_fps": 60, "compression_level": 9}'

# 获取设备流配置
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/config/stream

# 更新设备音频配置
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/config/audio \
  -H "Content-Type: application/json" \
  -d '{"sample_rate": 384000, "fft_size": 8192}'
```

#### 批量操作
```bash
# 批量启动多个设备
curl -X POST http://localhost:8380/api/devices/batch/start \
  -H "Content-Type: application/json" \
  -d '["ultramicfefe12_abc123", "builtinmic_d4e5f6"]'

# 批量停止多个设备
curl -X POST http://localhost:8380/api/devices/batch/stop \
  -H "Content-Type: application/json" \
  -d '["ultramicfefe12_abc123", "builtinmic_d4e5f6"]'
```

### 2. 兼容API使用（向后兼容）

```bash
# 启动音频采集
curl -X POST http://localhost:8380/api/start

# 查看状态
curl http://localhost:8380/api/status

# 设置FPS
curl -X POST http://localhost:8380/api/config/fps \
  -H "Content-Type: application/json" \
  -d '60'

# 停止采集
curl -X POST http://localhost:8380/api/stop

# 列出所有音频设备及状态（返回稳定ID）
curl http://localhost:8380/api/devices

# 获取指定设备的详细状态（使用稳定ID）
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/status

# 查看设备ID映射信息
curl http://localhost:8380/api/devices/mapping/info

# 清理无效的设备映射
curl -X POST http://localhost:8380/api/devices/mapping/cleanup
```

### 3. 前端SSE连接

#### 新架构：连接到特定设备
```javascript
// 连接到指定设备的数据流
const deviceId = 'ultramicfefe12_abc123';
const eventSource = new EventSource(`http://localhost:8380/api/devices/${deviceId}/stream`);

eventSource.onmessage = function(event) {
    const fftFrame = JSON.parse(event.data);
    
    console.log(`设备 ${deviceId} 数据:`);
    console.log('时间戳:', fftFrame.timestamp);
    console.log('序列号:', fftFrame.sequence_id);
    console.log('采样率:', fftFrame.sample_rate);
    console.log('峰值频率:', fftFrame.peak_frequency_hz);
    console.log('声压级:', fftFrame.spl_db);
    
    // 解压缩FFT数据
    const compressedData = fftFrame.data_compressed;
    // 需要使用pako或其他库解压缩gzip数据
};

eventSource.onerror = function(event) {
    console.error(`设备 ${deviceId} SSE连接错误:`, event);
};
```

#### 多设备同时连接
```javascript
// 同时连接多个设备的数据流
const devices = ['ultramicfefe12_abc123', 'builtinmic_d4e5f6'];
const eventSources = {};

devices.forEach(deviceId => {
    const eventSource = new EventSource(`http://localhost:8380/api/devices/${deviceId}/stream`);
    eventSources[deviceId] = eventSource;
    
    eventSource.onmessage = function(event) {
        const fftFrame = JSON.parse(event.data);
        console.log(`设备 ${deviceId}:`, fftFrame.peak_frequency_hz, 'Hz');
        
        // 处理设备专属数据
        processDeviceData(deviceId, fftFrame);
    };
    
    eventSource.onerror = function(event) {
        console.error(`设备 ${deviceId} 连接错误:`, event);
    };
});

// 关闭所有连接
function closeAllConnections() {
    Object.values(eventSources).forEach(es => es.close());
}
```

#### 兼容模式：连接到全局数据流
```javascript
// 连接SSE数据流（兼容模式）
const eventSource = new EventSource('http://localhost:8380/api/stream');

eventSource.onmessage = function(event) {
    const fftFrame = JSON.parse(event.data);
    
    console.log('时间戳:', fftFrame.timestamp);
    console.log('序列号:', fftFrame.sequence_id);
    console.log('采样率:', fftFrame.sample_rate);
    console.log('峰值频率:', fftFrame.peak_frequency_hz);
    console.log('声压级:', fftFrame.spl_db);
    
    // 解压缩FFT数据
    const compressedData = fftFrame.data_compressed;
    // 需要使用pako或其他库解压缩gzip数据
};

eventSource.onerror = function(event) {
    console.error('SSE连接错误:', event);
};
```

### 3. 简单的Web监控页面

```html
<!DOCTYPE html>
<html>
<head>
    <title>超声波监控</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.0.4/pako.min.js"></script>
</head>
<body>
    <h1>实时超声波数据</h1>
    <div id="status">未连接</div>
    <div id="data"></div>
    
    <script>
        const eventSource = new EventSource('http://localhost:8380/api/stream');
        
        eventSource.onopen = function() {
            document.getElementById('status').textContent = '已连接';
        };
        
        eventSource.onmessage = function(event) {
            const frame = JSON.parse(event.data);
            
            // 显示基本信息
            document.getElementById('data').innerHTML = `
                <p>时间戳: ${new Date(frame.timestamp).toLocaleTimeString()}</p>
                <p>序列号: ${frame.sequence_id}</p>
                <p>FPS: ${frame.fps.toFixed(1)}</p>
                <p>峰值频率: ${(frame.peak_frequency_hz/1000).toFixed(1)} kHz</p>
                <p>峰值幅度: ${frame.peak_magnitude_db.toFixed(1)} dB</p>
                <p>声压级: ${frame.spl_db.toFixed(1)} dB SPL</p>
                <p>数据大小: ${frame.data_size_bytes} bytes</p>
                <p>压缩比: ${(frame.data_size_bytes/frame.original_size_bytes*100).toFixed(1)}%</p>
            `;
        };
        
        eventSource.onerror = function() {
            document.getElementById('status').textContent = '连接错误';
        };
    </script>
</body>
</html>
```

## 🐛 问题排查

### 常见问题

1. **ImportError: attempted relative import with no known parent package**
   - 问题：Python模块导入路径错误
   - 解决：使用绝对导入或直接运行main.py

2. **音频设备未找到**
   - 检查可用设备：`curl http://localhost:8380/api/devices`
   - 配置环境变量：`export DEVICE_NAMES="YourDevice"`

3. **SSE连接超时**
   - 检查防火墙设置
   - 确认服务器正常启动：`curl http://localhost:8380/api/status`

4. **数据压缩/解压错误**
   - 前端需要pako.js或类似库解压gzip数据
   - 检查Base64解码是否正确

5. **🆕 FFT数据流不更新（最常见问题）**
   - **症状**：设备启动成功，SSE连接正常，但前端看不到频谱数据更新
   - **原因**：智能跳帧功能在安静环境中会跳过所有帧
   - **解决方案**：
     ```bash
     # 方法1: 禁用智能跳帧（推荐）
     export SMART_SKIP=false
     
     # 方法2: 调整幅度阈值
     export MAGNITUDE_THRESHOLD=-120.0
     
     # 方法3: 通过API动态配置
     curl -X POST http://localhost:8380/api/config/stream \
       -H "Content-Type: application/json" \
       -d '{"enable_smart_skip": false}'
     ```
   - **验证修复**：
     ```bash
     # 测试数据流是否正常
     curl -N http://localhost:8380/api/devices/{device_id}/stream | head -n 5
     # 应该看到sequence_id递增的JSON数据
     ```

6. **设备启动但无音频数据**
   - 检查设备权限（麦克风访问权限）
   - 验证设备是否被其他应用占用
   - 检查采样率是否与设备兼容

### 调试方法

```bash
# 1. 检查服务器状态
curl -v http://localhost:8380/api/status

# 2. 测试SSE连接（超时退出）
timeout 10 curl -N http://localhost:8380/api/stream/test

# 3. 检查端口占用
lsof -i :8380

# 4. 查看详细日志
export LOG_LEVEL=DEBUG
python main.py

# 5. 测试压缩性能
curl -X POST http://localhost:8380/api/test/compression
```

## 🔧 配置参数

### 环境变量

```bash
# 服务器配置
export HOST="0.0.0.0"           # 监听地址
export PORT="8380"              # 监听端口
export DEBUG="true"             # 调试模式

# 音频配置  
export SAMPLE_RATE="384000"     # 采样率
export FFT_SIZE="8192"          # FFT大小
export DEVICE_NAMES="UltraMic384K,UltraMic"  # 设备名称

# 流配置
export TARGET_FPS="30"          # 目标帧率
export COMPRESSION_LEVEL="6"    # 压缩级别 (1-9)
export MAGNITUDE_THRESHOLD="-80.0"  # 幅度阈值
```

### 配置文件

修改 `config.py` 中的默认值：

```python
class Config:
    HOST = "localhost"          # 只监听本地
    PORT = 8380                 # 自定义端口
    
    @classmethod
    def get_stream_config(cls):
        return StreamConfig(
            target_fps=60,          # 高帧率
            compression_level=9,    # 最高压缩
            enable_adaptive_fps=False  # 固定帧率
        )
```

## 📊 性能指标

### 数据量估算

| 配置 | 原始数据/帧 | 压缩后/帧 | 30FPS总量 | 60FPS总量 |
|------|------------|-----------|-----------|-----------|
| 默认 | ~16KB | ~5KB | 1.2MB/s | 2.4MB/s |
| 高压缩 | ~16KB | ~3KB | 0.7MB/s | 1.4MB/s |

### 网络要求

- **局域网**: ✅ 千兆网络完全支持
- **WiFi**: ✅ WiFi 5及以上推荐  
- **4G/LTE**: ⚠️ 需降低FPS到10-15
- **远程VPN**: ⚠️ 建议使用低FPS + 高压缩

## 🚀 部署建议

### 编译为独立可执行文件（推荐 ⭐）

为了更好的性能和便携性，推荐将应用编译为独立的可执行文件：

#### 1. 环境准备

```bash
# 创建专门的编译环境
conda create -n audio-sync python=3.11 -y
conda activate audio-sync

# 安装必要的依赖
pip install fastapi uvicorn pydantic numpy scipy sounddevice watchfiles pyinstaller
```

#### 2. 配置系统转换为JSON

确保你的项目使用了JSON配置系统（而不是Python config模块）：

- `config.json` - 配置文件
- `config_loader.py` - JSON配置加载器
- `main.py` 已修改支持编译环境

#### 3. 执行编译

```bash
cd headless_ultrasonic

# 编译为单个可执行文件（包含所有依赖）
pyinstaller --onedir \
  --collect-all scipy \
  --collect-all numpy \
  --hidden-import sounddevice \
  --add-data "config.json:." \
  --add-data "config_loader.py:." \
  --add-data "core:core" \
  --add-data "models:models" \
  --add-data "api:api" \
  --name headless_ultrasonic \
  main.py
```

#### 4. 测试编译结果

```bash
# 运行编译后的可执行文件
cd dist/headless_ultrasonic
./headless_ultrasonic

# 测试API是否正常
curl http://localhost:8380/api/status
```

#### 5. 部署编译版本

```bash
# 将整个 dist/headless_ultrasonic 目录复制到目标机器
cp -r dist/headless_ultrasonic /path/to/deployment/

# 直接运行（无需Python环境）
cd /path/to/deployment/headless_ultrasonic
./headless_ultrasonic
```

#### 编译的优势

✅ **无依赖运行**: 目标机器无需安装Python或任何依赖包  
✅ **启动更快**: 无需Python解释器启动开销  
✅ **内存稳定**: 更可预测的内存使用  
✅ **便携性强**: 单个目录包含所有内容  
✅ **集成友好**: 完美适配Electron应用架构  

#### 快速编译脚本

项目提供了自动化编译脚本：

```bash
# 激活编译环境
conda activate audio-sync

# 运行编译脚本
cd headless_ultrasonic
./build.sh
```

#### Electron集成示例

编译完成后，可以在Electron主进程中集成：

```javascript
// main.js - Electron主进程
const { spawn } = require('child_process');
const path = require('path');

class BackendManager {
    constructor() {
        this.backendProcess = null;
        this.isRunning = false;
    }
    
    async startBackend() {
        return new Promise((resolve, reject) => {
            const backendPath = path.join(__dirname, 'resources', 'headless_ultrasonic', 'headless_ultrasonic');
            
            this.backendProcess = spawn(backendPath, [], {
                cwd: path.dirname(backendPath),
                stdio: ['ignore', 'pipe', 'pipe']
            });
            
            this.backendProcess.stdout.on('data', (data) => {
                console.log(`Backend: ${data}`);
                if (data.toString().includes('Uvicorn running')) {
                    this.isRunning = true;
                    resolve();
                }
            });
            
            this.backendProcess.stderr.on('data', (data) => {
                console.error(`Backend Error: ${data}`);
            });
            
            this.backendProcess.on('exit', (code) => {
                console.log(`Backend exited with code ${code}`);
                this.isRunning = false;
            });
            
            // 超时处理
            setTimeout(() => {
                if (!this.isRunning) {
                    reject(new Error('Backend startup timeout'));
                }
            }, 10000);
        });
    }
    
    stopBackend() {
        if (this.backendProcess && this.isRunning) {
            this.backendProcess.kill();
            this.isRunning = false;
        }
    }
}

// 在app ready时启动后端
const backendManager = new BackendManager();

app.whenReady().then(async () => {
    try {
        await backendManager.startBackend();
        console.log('✅ Backend started successfully');
        
        // 创建主窗口
        createWindow();
    } catch (error) {
        console.error('❌ Failed to start backend:', error);
    }
});

// 应用退出时清理
app.on('before-quit', () => {
    backendManager.stopBackend();
});
```

在渲染进程中连接API：

```javascript
// renderer.js - 渲染进程
class UltrasonicClient {
    constructor() {
        this.baseUrl = 'http://localhost:8380';
        this.eventSource = null;
    }
    
    async connectToDevice(deviceId) {
        // 启动设备
        await fetch(`${this.baseUrl}/api/devices/${deviceId}/start`, {
            method: 'POST'
        });
        
        // 连接数据流
        this.eventSource = new EventSource(`${this.baseUrl}/api/devices/${deviceId}/stream`);
        
        this.eventSource.onmessage = (event) => {
            const fftFrame = JSON.parse(event.data);
            this.updateVisualization(fftFrame);
        };
    }
    
    updateVisualization(fftFrame) {
        // 更新频谱图表
        console.log(`频率: ${fftFrame.peak_frequency_hz}Hz, 幅度: ${fftFrame.peak_magnitude_db}dB`);
    }
}

const client = new UltrasonicClient();
```

#### 常见编译问题解决

1. **scipy.signal 模块缺失**:
   ```bash
   # 使用 --collect-all 参数收集完整模块
   --collect-all scipy --collect-all numpy
   ```

2. **配置文件路径问题**:
   ```python
   # config_loader.py 中已处理编译环境路径
   if getattr(sys, 'frozen', False):
       # 编译后的路径处理
       app_path = os.path.dirname(sys.executable)
   ```

3. **隐藏导入问题**:
   ```bash
   # 添加必要的隐藏导入
   --hidden-import sounddevice
   ```

### 生产环境（Python方式）

如果不使用编译版本，可以用传统方式部署：

```bash
# 使用gunicorn部署
pip install gunicorn
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8380 --timeout 300

# 或使用systemd服务
sudo systemctl enable headless-ultrasonic
sudo systemctl start headless-ultrasonic
```

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8380

CMD ["python", "-c", "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8380)"]
```

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支：`git checkout -b feature/amazing-feature`
3. 提交修改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件