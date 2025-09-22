#!/usr/bin/env python3
"""
测试导入问题
"""
import sys
import os

print("Python:", sys.version)
print("Executable:", sys.executable)
print("Frozen:", getattr(sys, 'frozen', False))
print("Path:", sys.path[:3])

# 修复PyInstaller编译后的导入路径
if getattr(sys, 'frozen', False):
    # 如果是PyInstaller打包后的环境
    app_path = os.path.dirname(sys.executable)
    internal_path = os.path.join(app_path, '_internal')
    if os.path.exists(internal_path):
        sys.path.insert(0, internal_path)
        print(f"Added to path: {internal_path}")
else:
    # 如果是正常Python环境
    app_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, app_path)

print("\nTrying to import config...")
try:
    from config import Config
    print("Success! Config imported")
    print("Config.PORT:", Config.PORT)
except Exception as e:
    print(f"Failed: {e}")
    
print("\nChecking if config.py exists...")
for path in sys.path:
    config_file = os.path.join(path, 'config.py')
    if os.path.exists(config_file):
        print(f"Found: {config_file}")