#!/bin/bash
#
# headless_ultrasonic Universal编译脚本
# 使用PyInstaller将FastAPI应用编译为通用二进制文件
# 支持ARM64和x86_64架构
#

set -e  # 出错时停止执行

echo "🚀 开始编译 headless_ultrasonic (Universal 通用版本)..."

# 检测当前 Python 架构
PYTHON_ARCH=$(python3 -c "import platform; print(platform.machine())")
ARCH_NAME="universal"
echo "🖥️ 编译目标: Universal 通用二进制 (ARM64 + x86_64)"
echo "📱 当前 Python 运行架构: $PYTHON_ARCH"

# 检查conda环境
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "❌ 请先激活conda环境:"
    echo "   conda create -n audio-sync python=3.11 -y"
    echo "   conda activate audio-sync"
    exit 1
fi

echo "✅ 当前conda环境: $CONDA_DEFAULT_ENV"

# 检查必要依赖
echo "🔍 检查依赖包..."
python -c "import fastapi, uvicorn, pydantic, numpy, scipy, sounddevice, watchfiles" 2>/dev/null || {
    echo "❌ 缺少必要依赖，正在安装..."
    pip install fastapi uvicorn pydantic numpy scipy sounddevice watchfiles pyinstaller
}

echo "✅ 依赖检查完成"

# 清理之前的编译结果
if [ -d "dist" ]; then
    echo "🗑️ 清理之前的编译结果..."
    rm -rf dist build *.spec
fi

# 设置输出文件名
OUTPUT_NAME="headless_ultrasonic_${ARCH_NAME}"

# 执行编译 - 目录模式，Universal 二进制
echo "🔨 开始PyInstaller编译 (目录模式，Universal二进制)..."
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
  --target-arch universal2 \
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
    
    if echo "$ARCH_INFO" | grep -q "universal"; then
        echo "✅ 确认为 Universal 通用二进制文件"
    elif echo "$ARCH_INFO" | grep -q "x86_64"; then
        echo "📱 Intel x86_64 架构 (单架构)"
    elif echo "$ARCH_INFO" | grep -q "arm64"; then
        echo "📱 ARM64 架构 (单架构)"
    else
        echo "❓ 未知架构信息"
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
    echo "🎉 编译完成！"
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
    echo "💡 提示: Universal版本可在ARM和Intel Mac上都原生运行，无需Python环境"
    
else
    echo "❌ 编译失败！请检查错误信息"
    exit 1
fi

echo "✨ Universal通用二进制编译流程完成！"