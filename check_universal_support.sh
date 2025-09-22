#!/bin/bash
#
# 检查 Universal2 支持脚本
# 验证当前环境是否支持 PyInstaller Universal2 编译
#

echo "🔍 检查 Universal2 编译支持..."
echo ""

# 检查 Python 架构
echo "1️⃣ 检查 Python 架构:"
PYTHON_ARCH=$(python3 -c "import platform; print(platform.machine())")
echo "   当前 Python 架构: $PYTHON_ARCH"

# 检查 Python 是否为 Universal2
python3 -c "
import sys
import subprocess
try:
    result = subprocess.run(['file', sys.executable], capture_output=True, text=True)
    if 'universal' in result.stdout.lower():
        print('   ✅ Python 支持 Universal2')
    else:
        print('   ❌ Python 不支持 Universal2 (单架构)')
        print(f'   📄 详情: {result.stdout.strip()}')
except:
    print('   ❓ 无法检测 Python 架构支持')
"

echo ""

# 检查关键依赖包的架构
echo "2️⃣ 检查关键依赖包架构:"
for pkg in numpy scipy sounddevice; do
    echo "   检查 $pkg..."
    python3 -c "
import $pkg
import os
import subprocess
try:
    # 尝试找到包的二进制文件
    pkg_path = $pkg.__file__
    pkg_dir = os.path.dirname(pkg_path)
    
    # 查找 .so 文件
    import glob
    so_files = glob.glob(os.path.join(pkg_dir, '**/*.so'), recursive=True)
    if so_files:
        result = subprocess.run(['file', so_files[0]], capture_output=True, text=True)
        if 'universal' in result.stdout.lower():
            print('     ✅ $pkg 支持 Universal2')
        else:
            print('     ❌ $pkg 不支持 Universal2')
    else:
        print('     📦 $pkg 是纯 Python 包')
except Exception as e:
    print(f'     ❓ 无法检测 $pkg: {e}')
" 2>/dev/null || echo "     ❌ $pkg 未安装或检测失败"
done

echo ""

# 检查 conda 环境类型
echo "3️⃣ 检查 conda 环境:"
if [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "   当前环境: $CONDA_DEFAULT_ENV"
    
    # 检查 conda 安装类型
    CONDA_INFO=$(conda info | grep "platform" || echo "unknown")
    echo "   $CONDA_INFO"
    
    if conda info | grep -q "osx-arm64"; then
        echo "   📱 这是 ARM64 专用的 conda 环境"
    elif conda info | grep -q "osx-64"; then
        echo "   💻 这是 x86_64 专用的 conda 环境"
    else
        echo "   ❓ 未知的 conda 环境类型"
    fi
else
    echo "   ❌ 未激活 conda 环境"
fi

echo ""

# 提供建议
echo "💡 建议方案:"
echo ""

if python3 -c "import subprocess; result = subprocess.run(['file', __import__('sys').executable], capture_output=True, text=True); exit(0 if 'universal' in result.stdout.lower() else 1)" 2>/dev/null; then
    echo "✅ 您的 Python 支持 Universal2，可以尝试编译 Universal 版本"
    echo "   运行: ./build_universal.sh"
else
    echo "❌ 当前环境不支持 Universal2 编译"
    echo ""
    echo "🔧 解决方案选择："
    echo ""
    echo "方案1: 安装官方 Universal2 Python"
    echo "   1. 从 python.org 下载 Universal2 版本"
    echo "   2. 使用 pip 安装依赖"
    echo "   3. 运行 PyInstaller"
    echo ""
    echo "方案2: 使用 Miniforge3 (推荐)"
    echo "   1. 下载 Miniforge3-MacOSX-arm64.sh"
    echo "   2. 创建新的 Universal2 环境"
    echo "   3. 安装支持 Universal2 的依赖包"
    echo ""
    echo "方案3: 创建单架构版本"
    echo "   - 当前版本: ARM64 (在 ARM Mac 上原生运行)"
    echo "   - 创建 x86_64 环境编译 Intel 版本"
    echo ""
    echo "🚀 推荐运行: ./setup_intel_env.sh (创建 Intel 专用环境)"
fi