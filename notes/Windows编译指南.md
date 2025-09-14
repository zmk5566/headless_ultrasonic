# headless_ultrasonic Windows 编译指南

## 概述

本文档介绍如何在Windows环境下将headless_ultrasonic编译为单文件可执行程序(.exe)，无需依赖Python环境即可在其他Windows系统上运行。

## 环境要求

- Windows 10/11
- Python 3.11 或 3.12
- PowerShell 5.0+
- 网络连接（用于下载依赖包）

## 编译步骤

### 1. 准备编译环境

确保你在headless_ultrasonic目录下：
```powershell
cd headless_ultrasonic
```

### 2. 运行编译脚本

使用提供的PowerShell脚本：
```powershell
powershell -ExecutionPolicy Bypass -File build_simple.ps1
```

### 3. 编译过程说明

编译脚本将自动执行以下步骤：

1. **检测系统架构**
   - 自动识别AMD64、ARM64或x86架构
   - 根据架构设置对应的输出文件名

2. **检查Python环境**
   - 验证Python是否正确安装
   - 显示Python版本信息

3. **安装依赖包**（使用清华镜像源加速）
   ```
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
     "numpy<2.0" "scipy>=1.11.0" sounddevice fastapi \
     uvicorn pydantic watchfiles pyinstaller
   ```

4. **清理旧的编译结果**
   - 删除之前的.exe文件
   - 清理.spec文件

5. **执行PyInstaller编译**
   ```powershell
   python -m PyInstaller --onefile \
     --collect-all scipy \
     --collect-all numpy \
     --hidden-import sounddevice \
     --hidden-import watchfiles \
     --hidden-import uvicorn.main \
     --add-data "config.json;." \
     --add-data "config_loader.py;." \
     --add-data "core;core" \
     --add-data "models;models" \
     --add-data "api;api" \
     --distpath "dist" \
     --workpath "build_onefile_amd64" \
     --name "headless_ultrasonic_windows_amd64_onefile" \
     --console \
     main.py
   ```

## 编译结果

### 输出文件
- **位置**: `dist/headless_ultrasonic_windows_amd64_onefile.exe`
- **大小**: 约180-190MB
- **类型**: 单文件可执行程序

### 文件特性
- ✅ 无需Python环境
- ✅ 无需额外依赖
- ✅ 包含所有必要库
- ✅ 支持FastAPI服务
- ✅ 包含音频处理功能

## 使用方法

### 运行程序
```cmd
# 方法1: 双击exe文件直接运行
# 方法2: 命令行运行
headless_ultrasonic_windows_amd64_onefile.exe
```

### 访问API
- **状态检查**: http://localhost:8380/api/status
- **API文档**: http://localhost:8380/docs
- **默认端口**: 8380

## 故障排除

### 常见问题

1. **PowerShell执行策略错误**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **PyInstaller未找到**
   ```powershell
   python -m pip install pyinstaller
   ```

3. **依赖下载慢**
   - 脚本已配置清华镜像源
   - 如需更换其他源，修改pip install命令中的-i参数

4. **编译内存不足**
   - 确保至少有8GB可用内存
   - 关闭不必要的应用程序

### 日志和调试

编译过程中的详细日志会显示在PowerShell窗口中，包括：
- 依赖分析过程
- 模块收集情况
- 可能的警告信息

## 高级配置

### 自定义编译参数

可以修改`build_simple.ps1`中的PyInstaller参数：

```powershell
$pyinstallerArgs = @(
    "--onefile"                    # 单文件模式
    "--windowed"                   # 无控制台窗口（可选）
    "--icon", "app.ico"           # 自定义图标（可选）
    "--name", "custom_name"        # 自定义文件名
    # 其他参数...
)
```

### 排除不必要的模块

如果想减小文件大小，可以添加排除参数：
```powershell
"--exclude-module", "tkinter"
"--exclude-module", "matplotlib"
```

## 分发说明

### 系统兼容性
- Windows 7 SP1 及以上
- 相同架构（x64程序仅在x64系统运行）
- 无需Visual C++ Redistributable

### 安全提醒
- Windows Defender可能报告为未知发布者
- 首次运行可能需要管理员权限
- 企业环境可能需要IT部门白名单

### 性能特点
- 首次启动较慢（需要解压依赖到临时目录）
- 后续启动速度正常
- 内存占用比Python脚本略高

## 版本历史

- **v1.0**: 初始版本，支持AMD64架构
- **v1.1**: 添加清华镜像源支持
- **v1.2**: 修复PowerShell编码问题

## 相关文件

- `build_simple.ps1`: 简化版编译脚本
- `build_windows_onefile.ps1`: 完整版编译脚本（有编码问题）
- `build_windows_onefile.bat`: 批处理版本（有编码问题）
- `headless_ultrasonic_windows_amd64_onefile.spec`: PyInstaller配置文件

---

*编译完成后，单个exe文件即可在任何Windows系统上独立运行headless_ultrasonic服务。*