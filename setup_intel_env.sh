#!/bin/bash
#
# 设置 Intel x86_64 编译环境脚本
# 在 Apple Silicon Mac 上创建 x86_64 conda 环境用于编译 Intel 版本
#

set -e

echo "🚀 开始设置 Intel x86_64 编译环境..."

# 检查是否在 Apple Silicon Mac 上
if [[ $(uname -m) != "arm64" ]]; then
    echo "⚠️  此脚本设计用于 Apple Silicon Mac，当前系统架构: $(uname -m)"
    echo "💡 如果您已在 Intel Mac 上，可以直接使用普通的 conda 环境"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查是否已安装 Rosetta 2
if ! pgrep oahd >/dev/null 2>&1; then
    echo "❌ 需要安装 Rosetta 2 才能运行 x86_64 版本"
    echo "请运行以下命令安装 Rosetta 2："
    echo "   softwareupdate --install-rosetta"
    exit 1
fi

echo "✅ Rosetta 2 已安装"

# 设置环境变量
export CONDA_SUBDIR=osx-64

# 检查是否已存在 Intel 编译环境
INTEL_ENV_NAME="audio-sync-intel"
if conda info --envs | grep -q "$INTEL_ENV_NAME"; then
    echo "⚠️  环境 '$INTEL_ENV_NAME' 已存在"
    read -p "是否删除现有环境并重新创建？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️ 删除现有环境..."
        conda env remove -n "$INTEL_ENV_NAME" -y
    else
        echo "使用现有环境"
        exit 0
    fi
fi

echo "🔨 创建 Intel x86_64 conda 环境..."

# 设置环境变量强制使用 x86_64 包
export CONDA_SUBDIR=osx-64

# 创建环境
conda create -n "$INTEL_ENV_NAME" python=3.11 -y

echo "📦 激活环境并安装依赖..."
# 激活环境
conda activate "$INTEL_ENV_NAME"

# 配置环境使用 x86_64 包
conda config --env --set subdir osx-64

# 安装 x86_64 版本的包
echo "📦 安装 x86_64 依赖包..."
conda install numpy scipy -y
pip install fastapi uvicorn pydantic sounddevice watchfiles pyinstaller

# 重置环境变量
unset CONDA_SUBDIR

echo "✅ Intel x86_64 编译环境设置完成！"
echo ""
echo "🚀 使用方法："
echo "1. 激活环境："
echo "   conda activate $INTEL_ENV_NAME"
echo ""
echo "2. 验证架构："
echo "   python -c \"import platform; print('架构:', platform.machine())\""
echo ""
echo "3. 运行编译脚本："
echo "   ./build_universal.sh"
echo ""
echo "💡 注意：在此环境中，Python 将以 x86_64 模式运行"