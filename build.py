#!/usr/bin/env python3
"""
简单的 PyInstaller 构建脚本
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    # 确保在正确的目录中
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("正在构建 headless_ultrasonic 可执行文件...")
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--onedir',  # 创建目录而不是单个文件（更快）
        '--console',
        '--name', 'headless_ultrasonic',
        '--add-data', 'core/device_mapping.json:core',
        '--add-data', 'core/device_configs.json:core',
        '--hidden-import', 'uvicorn.main',
        '--hidden-import', 'sounddevice',
        '--hidden-import', 'numpy',
        '--hidden-import', 'scipy.signal',
        '--hidden-import', 'scipy.fft',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'pandas', 
        '--exclude-module', 'tensorflow',
        '--exclude-module', 'torch',
        '--exclude-module', 'cv2',
        '--exclude-module', 'tkinter',
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt6',
        'main.py'
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功!")
        print(f"可执行文件位置: {script_dir / 'dist' / 'headless_ultrasonic'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"构建失败: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)