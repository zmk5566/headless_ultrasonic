# Headless Ultrasonic Visualizer

Real-time FFT data streaming service based on FastAPI + SSE, supporting frontend-backend separation and remote monitoring.

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create conda environment
conda create -n headless-ultrasonic python=3.11 -y
conda activate headless-ultrasonic

# Install dependencies
pip install fastapi uvicorn pydantic numpy scipy sounddevice
```

### 2. Start Server

**Method 1: Direct run**
```bash
cd headless_ultrasonic
python -c "
import uvicorn
from main import app
print('🎵 Starting Headless Ultrasonic Visualizer...')
print('Server address: http://localhost:8380')
uvicorn.run(app, host='0.0.0.0', port=8380, log_level='info')
"
```

**Method 2: Using run script (if import issues are fixed)**
```bash
cd headless_ultrasonic  
python run.py
```

### 3. Access Services

- **Web Interface**: http://localhost:8380 - 🆕 **Integrated real-time spectrum visualization!**
- **API Documentation**: http://localhost:8380/docs  
- **SSE Data Stream**: http://localhost:8380/api/stream

### 🎨 Web Interface Features

The new web interface includes a complete visualization system:

- **Real-time spectrum chart** - Using Chart.js to display 0-100kHz spectrum
- **Real-time data metrics** - FPS, peak frequency, SPL, data rate, etc.
- **System control panel** - Start/stop, FPS adjustment, connection status
- **Event log** - Real-time display of data reception and system status
- **Data export** - One-click analysis data export

## 📡 API Endpoints

### 🆕 New Architecture API (Per-device independent control)

#### System-level Control API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/status` | GET | Get overall system status |
| `/api/system/devices` | GET | List all devices (enhanced) |
| `/api/system/devices/refresh` | POST | Refresh device list |
| `/api/system/cleanup` | POST | System cleanup |
| `/api/system/stop-all` | POST | Stop all devices |
| `/api/system/health` | GET | System health check |
| `/api/system/performance` | GET | System performance stats |

#### Per-device Control API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices/{device_id}/start` | POST | Start specified device |
| `/api/devices/{device_id}/stop` | POST | Stop specified device |
| `/api/devices/{device_id}/restart` | POST | Restart specified device |
| `/api/devices/{device_id}/status` | GET | Get detailed device status |
| `/api/devices/{device_id}/stream` | GET | Device-specific SSE data stream |
| `/api/devices/{device_id}/config/stream` | GET/POST | Get/set device stream config |
| `/api/devices/{device_id}/config/audio` | GET/POST | Get/set device audio config |
| `/api/devices/{device_id}` | DELETE | Remove device instance |

#### Batch Operations API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices/batch/start` | POST | Batch start devices |
| `/api/devices/batch/stop` | POST | Batch stop devices |

### 🔄 Compatibility API (Backward compatible)

#### Legacy Control API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Get system status |
| `/api/start` | POST | Start audio capture |
| `/api/stop` | POST | Stop audio capture |
| `/api/config/stream` | GET/POST | Get/set stream config |
| `/api/config/fps` | POST | Quick set FPS |
| `/api/devices` | GET | List audio devices with status |
| `/api/devices/{device_id}/status` | GET | Get device detailed status |

#### Data Stream API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stream` | GET | SSE real-time FFT data stream |
| `/api/stream/test` | GET | SSE connection test |
| `/api/stream/stats` | GET | Stream transmission stats |

## 🎯 Stable Device ID System

To solve the issue of changing device indices, the system uses a stable device ID mechanism:

### Features
- **Persistent mapping**: Device ID mappings saved to local file `device_mapping.json`
- **Smart generation**: Friendly stable IDs generated based on device name + hardware features
- **Auto cleanup**: Automatically cleans invalid device mappings
- **Backward compatible**: Keeps system index as reference

### ID Format Examples
```
ultramicfefe12_a1b2c3  # UltraMic device based on hardware features
builtinmic_d4e5f6      # Built-in microphone
usbheadset_g7h8i9      # USB headset
```

## 🔧 Usage Examples

### 1. New Architecture API Usage

#### System Management
```bash
# Get overall system status
curl http://localhost:8380/api/system/status

# List all devices (enhanced)
curl http://localhost:8380/api/system/devices

# System health check
curl http://localhost:8380/api/system/health

# Stop all devices
curl -X POST http://localhost:8380/api/system/stop-all
```

#### Single Device Control
```bash
# Start specified device (using stable ID)
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/start

# Get device detailed status
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/status

# Stop specified device
curl -X POST http://localhost:8380/api/devices/ultramicfefe12_abc123/stop

# Connect to device-specific data stream
curl http://localhost:8380/api/devices/ultramicfefe12_abc123/stream
```

### 2. Frontend SSE Connection

#### New Architecture: Connect to Specific Device
```javascript
// Connect to specified device's data stream
const deviceId = 'ultramicfefe12_abc123';
const eventSource = new EventSource(`http://localhost:8380/api/devices/${deviceId}/stream`);

eventSource.onmessage = function(event) {
    const fftFrame = JSON.parse(event.data);
    
    console.log(`Device ${deviceId} data:`);
    console.log('Timestamp:', fftFrame.timestamp);
    console.log('Sequence:', fftFrame.sequence_id);
    console.log('Sample rate:', fftFrame.sample_rate);
    console.log('Peak frequency:', fftFrame.peak_frequency_hz);
    console.log('SPL:', fftFrame.spl_db);
    
    // Decompress FFT data
    const compressedData = fftFrame.data_compressed;
    // Use pako or other library to decompress gzip data
};
```

#### Compatibility Mode: Connect to Global Stream
```javascript
// Connect SSE data stream (compatibility mode)
const eventSource = new EventSource('http://localhost:8380/api/stream');

eventSource.onmessage = function(event) {
    const fftFrame = JSON.parse(event.data);
    
    console.log('Timestamp:', fftFrame.timestamp);
    console.log('Sequence:', fftFrame.sequence_id);
    console.log('Peak frequency:', fftFrame.peak_frequency_hz);
    console.log('SPL:', fftFrame.spl_db);
};
```

### 3. Simple Web Monitoring Page

```html
<!DOCTYPE html>
<html>
<head>
    <title>Ultrasonic Monitor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pako/2.0.4/pako.min.js"></script>
</head>
<body>
    <h1>Real-time Ultrasonic Data</h1>
    <div id="status">Not connected</div>
    <div id="data"></div>
    
    <script>
        const eventSource = new EventSource('http://localhost:8380/api/stream');
        
        eventSource.onopen = function() {
            document.getElementById('status').textContent = 'Connected';
        };
        
        eventSource.onmessage = function(event) {
            const frame = JSON.parse(event.data);
            
            // Display basic info
            document.getElementById('data').innerHTML = `
                <p>Timestamp: ${new Date(frame.timestamp).toLocaleTimeString()}</p>
                <p>Sequence: ${frame.sequence_id}</p>
                <p>FPS: ${frame.fps.toFixed(1)}</p>
                <p>Peak frequency: ${(frame.peak_frequency_hz/1000).toFixed(1)} kHz</p>
                <p>Peak magnitude: ${frame.peak_magnitude_db.toFixed(1)} dB</p>
                <p>SPL: ${frame.spl_db.toFixed(1)} dB SPL</p>
                <p>Data size: ${frame.data_size_bytes} bytes</p>
                <p>Compression ratio: ${(frame.data_size_bytes/frame.original_size_bytes*100).toFixed(1)}%</p>
            `;
        };
        
        eventSource.onerror = function() {
            document.getElementById('status').textContent = 'Connection error';
        };
    </script>
</body>
</html>
```

## 🐛 Troubleshooting

### Common Issues

1. **ImportError: attempted relative import with no known parent package**
   - Issue: Python module import path error
   - Solution: Use absolute import or run main.py directly

2. **Audio device not found**
   - Check available devices: `curl http://localhost:8380/api/devices`
   - Configure environment: `export DEVICE_NAMES="YourDevice"`

3. **SSE connection timeout**
   - Check firewall settings
   - Confirm server started normally: `curl http://localhost:8380/api/status`

4. **🆕 FFT data stream not updating (most common issue)**
   - **Symptoms**: Device starts successfully, SSE connects normally, but frontend sees no spectrum data updates
   - **Cause**: Smart skip feature skips all frames in quiet environments
   - **Solutions**:
     ```bash
     # Method 1: Disable smart skip (recommended)
     export SMART_SKIP=false
     
     # Method 2: Adjust magnitude threshold
     export MAGNITUDE_THRESHOLD=-120.0
     
     # Method 3: Dynamic configuration via API
     curl -X POST http://localhost:8380/api/config/stream \
       -H "Content-Type: application/json" \
       -d '{"enable_smart_skip": false}'
     ```

### Debug Methods

```bash
# 1. Check server status
curl -v http://localhost:8380/api/status

# 2. Test SSE connection (timeout exit)
timeout 10 curl -N http://localhost:8380/api/stream/test

# 3. Check port usage
lsof -i :8380

# 4. View detailed logs
export LOG_LEVEL=DEBUG
python main.py
```

## 📊 Performance Metrics

### Data Volume Estimation

| Config | Raw Data/Frame | Compressed/Frame | 30FPS Total | 60FPS Total |
|---------|----------------|------------------|-------------|-------------|
| Default | ~16KB | ~5KB | 1.2MB/s | 2.4MB/s |
| High Compression | ~16KB | ~3KB | 0.7MB/s | 1.4MB/s |

### Network Requirements

- **LAN**: ✅ Gigabit network fully supported
- **WiFi**: ✅ WiFi 5 and above recommended  
- **4G/LTE**: ⚠️ Need to reduce FPS to 10-15
- **Remote VPN**: ⚠️ Recommend low FPS + high compression

## 🚀 Deployment

### Production Environment
```bash
# Using gunicorn deployment
pip install gunicorn
gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8380 --timeout 300
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8380

CMD ["python", "-c", "import uvicorn; from main import app; uvicorn.run(app, host='0.0.0.0', port=8380)"]
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details