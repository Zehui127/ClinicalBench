#!/bin/bash
# Docker安装检查和引导脚本

echo "========================================"
echo "  Docker Desktop 安装检查"
echo "========================================"
echo ""

# 检查Docker是否已安装
echo "🔍 检查Docker安装状态..."
echo ""

if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装！"
    docker --version
    echo ""

    # 检查Docker是否运行
    if docker ps &> /dev/null; then
        echo "✅ Docker 正在运行！"
        echo ""
        echo "🧪 运行测试..."
        bash test_with_docker.sh
        exit 0
    else
        echo "❌ Docker 未运行"
        echo ""
        echo "请启动Docker Desktop："
        echo "1. 双击桌面图标"
        echo "2. 等待图标变绿"
        echo "3. 重新运行此脚本"
        exit 1
    fi
else
    echo "❌ Docker 未安装"
    echo ""
    echo "请按以下步骤安装："
    echo ""
    echo "方式1：官网下载（推荐）"
    echo "  访问：https://www.docker.com/products/docker-desktop/"
    echo "  下载 Windows 版本"
    echo ""
    echo "方式2：我帮你打开下载页面"
    read -p "是否打开下载页面？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 尝试打开浏览器
        if command -v start &> /dev/null; then
            start https://www.docker.com/products/docker-desktop/
            echo "✅ 已打开下载页面"
        elif command -v xdg-open &> /dev/null; then
            xdg-open https://www.docker.com/products/docker-desktop/
            echo "✅ 已打开下载页面"
        else
            echo "请手动访问："
            echo "https://www.docker.com/products/docker-desktop/"
        fi
    fi
    echo ""
    echo "安装完成后："
    echo "1. 运行安装程序"
    echo "2. 重启计算机"
    echo "3. 启动Docker Desktop"
    echo "4. 重新运行此脚本"
    echo ""
fi

echo "========================================"
echo "  需要帮助？"
echo "========================================"
echo ""
echo "查看完整安装指南："
echo "  cat INSTALL_DOCKER.md"
echo ""
echo "或告诉我遇到了什么问题，我会帮你解决！"
