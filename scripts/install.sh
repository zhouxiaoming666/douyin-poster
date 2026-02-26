#!/bin/bash

set -e

echo "🚀 安装抖音发布技能..."

# 创建虚拟环境
echo "📦 创建 Python 虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
echo "📥 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
playwright install chromium

# 安装系统依赖（Linux）
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔧 安装系统依赖..."
    playwright install-deps chromium 2>/dev/null || {
        echo "⚠️  自动安装失败，请手动安装："
        echo "   sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2"
    }
fi

# 创建配置目录
echo "⚙️  创建配置目录..."
mkdir -p assets

# 复制配置模板
if [ ! -f assets/config.json ]; then
    cp assets/config.example.json assets/config.json
    echo "✅ 配置已创建：assets/config.json"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "下一步："
echo "  1. 运行 'python scripts/login.py' 扫码登录"
echo "  2. 运行 'python scripts/douyin_post.py --help' 查看使用帮助"
echo ""
