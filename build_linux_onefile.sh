#!/bin/bash
#
# headless_ultrasonic Linux单文件编译脚本
# 使用PyInstaller --onefile将FastAPI应用编译为单个可执行文件
#

set -e  # 出错时停止执行

echo "🚀 开始编译 headless_ultrasonic (Linux单文件版本)..."

# 检测当前架构
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    TARGET_ARCH="amd64"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
    TARGET_ARCH="arm64"
else
    echo "❌ 不支持的架构: $ARCH"
    echo "   支持的架构: x86_64 (amd64), aarch64/arm64 (arm64)"
    exit 1
fi

echo "✅ 检测到架构: $ARCH -> $TARGET_ARCH"

# 检查Python虚拟环境
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "❌ 请先激活Python虚拟环境:"
    echo "   创建虚拟环境: python3 -m venv venv"
    echo "   激活虚拟环境: source venv/bin/activate"
    echo "   或者使用conda: conda activate your-env"
    exit 1
fi

if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ 当前虚拟环境: $VIRTUAL_ENV"
elif [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "✅ 当前conda环境: $CONDA_DEFAULT_ENV"
fi

# 检查必要依赖
echo "🔍 检查依赖包..."
python3 -c "import fastapi, uvicorn, pydantic, numpy, scipy, sounddevice, watchfiles" 2>/dev/null || {
    echo "❌ 缺少必要依赖，正在安装..."
    pip install -r requirements.txt
    pip install pyinstaller watchfiles
}

echo "✅ 依赖检查完成"

# 设置输出目录和文件名
OUTPUT_FILE="dist/headless_ultrasonic_linux_${TARGET_ARCH}_onefile"

# 清理之前的编译结果
if [ -f "$OUTPUT_FILE" ]; then
    echo "🗑️ 清理之前的编译结果..."
    rm -f "$OUTPUT_FILE"
fi

if [ -f "headless_ultrasonic_onefile.spec" ]; then
    rm -f headless_ultrasonic_onefile.spec
fi

# 检查必要文件是否存在
for file in "main.py" "config.json" "config_loader.py"; do
    if [ ! -f "$file" ]; then
        echo "❌ 找不到必要文件: $file"
        exit 1
    fi
done

for dir in "core" "models" "api"; do
    if [ ! -d "$dir" ]; then
        echo "❌ 找不到必要目录: $dir"
        exit 1
    fi
done

# 执行单文件编译
echo "🔨 开始PyInstaller单文件编译 (${TARGET_ARCH})..."
# 清除可能影响的环境变量
unset HOST HOSTNAME
pyinstaller --onefile \
  --collect-all scipy \
  --collect-all numpy \
  --hidden-import sounddevice \
  --hidden-import watchfiles \
  --add-data "config.json:." \
  --add-data "config_loader.py:." \
  --add-data "core:core" \
  --add-data "models:models" \
  --add-data "api:api" \
  --distpath "dist" \
  --workpath "build_onefile_${TARGET_ARCH}" \
  --name "headless_ultrasonic_linux_${TARGET_ARCH}_onefile" \
  main.py

# 检查编译结果
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ 单文件编译成功！"
    echo ""
    echo "📁 编译输出文件: $OUTPUT_FILE"
    echo "🏗️ 目标架构: $TARGET_ARCH"
    echo ""

    # 显示文件大小
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "📊 文件大小: $FILE_SIZE"
    echo ""

    # 显示可执行文件信息
    echo "🔍 可执行文件信息:"
    file "$OUTPUT_FILE"
    echo ""

    # 设置可执行权限
    chmod +x "$OUTPUT_FILE"

    echo "🧪 测试单文件版本..."
    echo "正在启动单文件版本进行测试..."

    # 后台启动测试
    timeout 10s "$OUTPUT_FILE" > /tmp/build_onefile_test.log 2>&1 &
    TEST_PID=$!

    # 等待启动
    sleep 3

    # 测试API
    if curl -s http://localhost:8380/api/status > /dev/null 2>&1; then
        echo "✅ 单文件版本测试成功！API响应正常"
        kill $TEST_PID 2>/dev/null || true
    else
        echo "⚠️ 单文件版本测试失败，请检查日志:"
        cat /tmp/build_onefile_test.log
        kill $TEST_PID 2>/dev/null || true
        exit 1
    fi

    echo ""
    echo "🎉 单文件编译完成！"
    echo ""
    echo "🚀 使用方法:"
    echo "   ./$OUTPUT_FILE"
    echo ""
    echo "🌐 API访问:"
    echo "   http://localhost:8380/api/status"
    echo "   http://localhost:8380/docs"
    echo ""
    echo "📦 分发说明:"
    echo "   单个文件即可运行，无需依赖"
    echo "   复制到其他相同架构的Linux系统即可使用"
    echo ""
    echo "⚠️ 注意事项:"
    echo "   - 单文件版本启动稍慢（需要解压依赖）"
    echo "   - 但分发更简单，只有一个文件"
    echo ""

else
    echo "❌ 单文件编译失败！请检查错误信息"
    exit 1
fi

echo "✨ Linux单文件编译流程完成！"