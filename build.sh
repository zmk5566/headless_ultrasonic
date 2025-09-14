#!/bin/bash
#
# headless_ultrasonic 编译脚本
# 使用PyInstaller将FastAPI应用编译为独立可执行文件
#

set -e  # 出错时停止执行

echo "🚀 开始编译 headless_ultrasonic..."

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

# 执行编译
echo "🔨 开始PyInstaller编译..."
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

# 检查编译结果
if [ -f "dist/headless_ultrasonic/headless_ultrasonic" ]; then
    echo "✅ 编译成功！"
    echo ""
    echo "📁 编译输出位置: dist/headless_ultrasonic/"
    echo "📄 可执行文件: dist/headless_ultrasonic/headless_ultrasonic"
    echo ""
    
    # 显示文件大小
    EXEC_SIZE=$(du -h dist/headless_ultrasonic/headless_ultrasonic | cut -f1)
    TOTAL_SIZE=$(du -sh dist/headless_ultrasonic | cut -f1)
    echo "📊 文件大小:"
    echo "   可执行文件: $EXEC_SIZE"
    echo "   总目录大小: $TOTAL_SIZE"
    echo ""
    
    echo "🧪 测试编译结果..."
    echo "正在启动编译版本进行测试..."
    
    # 后台启动测试
    cd dist/headless_ultrasonic
    timeout 10s ./headless_ultrasonic > /tmp/build_test.log 2>&1 &
    TEST_PID=$!
    
    # 等待启动
    sleep 3
    
    # 测试API
    if curl -s http://localhost:8380/api/status > /dev/null 2>&1; then
        echo "✅ 编译版本测试成功！API响应正常"
        kill $TEST_PID 2>/dev/null || true
    else
        echo "⚠️ 编译版本测试失败，请检查日志:"
        cat /tmp/build_test.log
        kill $TEST_PID 2>/dev/null || true
        cd ../..
        exit 1
    fi
    
    cd ../..
    
    echo ""
    echo "🎉 编译完成！"
    echo ""
    echo "🚀 使用方法:"
    echo "   cd dist/headless_ultrasonic"
    echo "   ./headless_ultrasonic"
    echo ""
    echo "🌐 API访问:"
    echo "   http://localhost:8380/api/status"
    echo "   http://localhost:8380/docs"
    echo ""
    
else
    echo "❌ 编译失败！请检查错误信息"
    exit 1
fi

echo "✨ 编译流程完成！"