#!/usr/bin/env python3
"""
PyInstaller 构建配置
用于将 headless_ultrasonic 编译成独立可执行文件
"""

import os
import sys
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 添加当前目录到路径
sys.path.insert(0, str(current_dir))

# 主要的 Python 文件
main_script = current_dir / "main.py"

# 需要包含的数据文件
data_files = [
    # 设备配置文件
    ('core/device_mapping.json', 'core'),
    ('core/device_configs.json', 'core'),
    # 配置示例文件
    ('config_example.env', '.'),
]

# 需要包含的隐式导入
hidden_imports = [
    'uvicorn',
    'fastapi',
    'sounddevice',
    'numpy',
    'scipy',
    'pako',
    'asyncio',
    'threading',
    'multiprocessing',
    'queue',
    'json',
    'gzip',
    'base64',
    'time',
    'logging',
    # FastAPI 相关
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.staticfiles',
    'fastapi.responses',
    'starlette',
    'starlette.middleware',
    'starlette.middleware.cors',
    # 其他可能需要的模块
    'pydantic',
    'email_validator',
    'python_multipart',
]

# PyInstaller Analysis 配置
a = Analysis(
    [str(main_script)],
    pathex=[str(current_dir)],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的模块以减小文件大小
        'tkinter',
        'matplotlib',
        'PIL',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='headless_ultrasonic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保持控制台输出以便调试
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)