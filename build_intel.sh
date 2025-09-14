#!/bin/bash
#
# headless_ultrasonic Intel 专用编译脚本
# 使用专门的 Intel conda 环境编译 x86_64 版本
#

set -e

echo "🚀 开始编译 headless_ultrasonic (Intel x86_64 专用版本)..."

# 初始化 conda
source /opt/anaconda3/etc/profile.d/conda.sh

# 检查 Intel 环境是否存在
if ! conda info --envs | grep -q "audio-sync-intel"; then
    echo "❌ Intel 编译环境 'audio-sync-intel' 不存在"
    echo "请先运行: ./setup_intel_env.sh"
    exit 1
fi

# 激活 Intel 环境
echo "🔄 激活 Intel 编译环境..."
conda activate audio-sync-intel

# 验证架构
PYTHON_ARCH=$(python -c "import platform; print(platform.machine())")
if [ "$PYTHON_ARCH" != "x86_64" ]; then
    echo "❌ 环境架构错误: $PYTHON_ARCH，期望: x86_64"
    exit 1
fi

echo "✅ 使用 Intel x86_64 Python 环境"
echo "📱 Python 架构: $PYTHON_ARCH"

# 检查依赖
echo "🔍 检查依赖包..."
python -c "import fastapi, uvicorn, pydantic, numpy, scipy, sounddevice, watchfiles" || {
    echo "❌ 缺少必要依赖"
    exit 1
}

echo "✅ 依赖检查完成"

# 清理之前的编译结果
if [ -d "dist" ]; then
    echo "🗑️ 清理之前的编译结果..."
    rm -rf dist build *.spec
fi

# 设置输出文件名
OUTPUT_NAME="headless_ultrasonic_intel"

# 执行编译
echo "🔨 开始PyInstaller编译 (Intel x86_64 目录模式)..."
pyinstaller --onedir \
  --collect-all scipy \
  --collect-all numpy \
  --hidden-import sounddevice \
  --exclude-module PyQt5 \
  --exclude-module PyQt6 \
  --exclude-module tkinter \
  --exclude-module matplotlib \
  --exclude-module jupyter \
  --exclude-module notebook \
  --add-data "config.json:." \
  --add-data "config_loader.py:." \
  --add-data "core:core" \
  --add-data "models:models" \
  --add-data "api:api" \
  --name "$OUTPUT_NAME" \
  main.py

# 检查编译结果
if [ -f "dist/$OUTPUT_NAME/$OUTPUT_NAME" ]; then
    echo "✅ 编译成功！"
    echo ""
    echo "📁 编译输出位置: dist/$OUTPUT_NAME/"
    echo "📄 可执行文件: dist/$OUTPUT_NAME/$OUTPUT_NAME"
    echo ""
    
    # 显示文件大小
    EXEC_SIZE=$(du -h "dist/$OUTPUT_NAME/$OUTPUT_NAME" | cut -f1)
    TOTAL_SIZE=$(du -sh "dist/$OUTPUT_NAME" | cut -f1)
    echo "📊 文件大小:"
    echo "   可执行文件: $EXEC_SIZE"
    echo "   总目录大小: $TOTAL_SIZE"
    echo ""
    
    # 设置可执行权限
    chmod +x "dist/$OUTPUT_NAME/$OUTPUT_NAME"
    
    # 验证架构
    echo "🔍 验证架构信息..."
    ARCH_INFO=$(file "dist/$OUTPUT_NAME/$OUTPUT_NAME")
    echo "   $ARCH_INFO"
    
    if echo "$ARCH_INFO" | grep -q "x86_64"; then
        echo "✅ 确认为 Intel x86_64 架构"
    else
        echo "⚠️ 警告: 架构可能不正确"
    fi
    
    # 使用 lipo 检查架构详情
    if command -v lipo >/dev/null 2>&1; then
        echo "🔍 详细架构信息:"
        lipo -info "dist/$OUTPUT_NAME/$OUTPUT_NAME" 2>/dev/null || echo "   无法获取详细架构信息"
    fi
    echo ""
    
    echo "🧪 测试编译结果..."
    echo "正在启动编译版本进行测试..."
    
    # 后台启动测试
    cd "dist/$OUTPUT_NAME"
    "./$OUTPUT_NAME" > /tmp/build_test.log 2>&1 &
    TEST_PID=$!
    
    # 等待启动
    sleep 5
    
    # 测试API
    if curl -s http://localhost:8380/api/status > /dev/null 2>&1; then
        echo "✅ 编译版本测试成功！API响应正常"
        kill $TEST_PID 2>/dev/null || true
        # 等待进程完全停止
        sleep 1
    else
        echo "⚠️ 编译版本测试失败，请检查日志:"
        cat /tmp/build_test.log
        kill $TEST_PID 2>/dev/null || true
        # 等待进程完全停止
        sleep 1
        cd ../..
        exit 1
    fi
    
    cd ../..
    
    echo ""
    echo "🎉 Intel 版本编译完成！"
    echo ""
    echo "🚀 使用方法:"
    echo "   cd dist/$OUTPUT_NAME"
    echo "   ./$OUTPUT_NAME"
    echo ""
    echo "📋 或者直接运行:"
    echo "   ./dist/$OUTPUT_NAME/$OUTPUT_NAME"
    echo ""
    echo "🌐 API访问:"
    echo "   http://localhost:8380/api/status"
    echo "   http://localhost:8380/docs"
    echo ""
    echo "💡 提示: 该版本为 Intel x86_64 架构，可在 Intel Mac 上原生运行"
    echo "         在 ARM Mac 上通过 Rosetta 2 运行"
    
else
    echo "❌ 编译失败！请检查错误信息"
    exit 1
fi

echo "✨ Intel x86_64 专用编译流程完成！"