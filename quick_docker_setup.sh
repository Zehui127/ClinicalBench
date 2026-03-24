#!/bin/bash
# Docker快速设置脚本
# 适用于Windows系统

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Docker 测试环境设置"
echo "=========================================="
echo ""

# 检查Docker是否安装
echo "🔍 步骤 1/3: 检查Docker安装..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装"
    docker --version
else
    echo "❌ Docker 未安装"
    echo ""
    echo "请先安装Docker Desktop："
    echo "1. 访问 https://www.docker.com/products/docker-desktop/"
    echo "2. 下载 Windows 版本"
    echo "3. 运行安装程序"
    echo "4. 重启计算机"
    echo "5. 启动Docker Desktop"
    echo ""
    echo "安装完成后，重新运行此脚本"
    exit 1
fi

echo ""
echo "🔍 步骤 2/3: 构建Docker镜像..."
echo "这可能需要5-10分钟（第一次）..."
echo ""

# 构建镜像
docker build -f Dockerfile.test -t tau2-test . 2>&1 | tee build.log

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Docker镜像构建成功！"
else
    echo ""
    echo "❌ Docker镜像构建失败"
    echo ""
    echo "请检查 build.log 文件查看详细错误"
    exit 1
fi

echo ""
echo "🧪 步骤 3/3: 运行测试..."
echo ""

# 运行测试
docker run --rm tau2-test

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "  ✅ 所有测试通过！"
    echo "=========================================="
    echo ""
    echo "现在你可以："
    echo "1. 推送代码到GitHub"
    echo "2. GitHub Actions也将通过"
    echo ""
    echo "推送命令："
    echo "   git push"
    echo ""
else
    echo ""
    echo "❌ 测试失败"
    echo ""
    echo "请检查错误信息并修复问题"
    exit 1
fi
