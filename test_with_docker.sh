#!/bin/bash
# Docker测试脚本 - 模拟GitHub Actions环境

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=========================================="
echo "  Docker 测试 - 模拟GitHub Actions"
echo "=========================================="
echo -e "${NC}"

# 检查Docker
echo -e "${YELLOW}🔍 检查Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    echo ""
    echo "请先安装Docker Desktop："
    echo "https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo -e "${GREEN}✅ Docker已安装${NC}"
docker --version
echo ""

# 构建镜像
echo -e "${YELLOW}📦 构建Docker镜像...${NC}"
echo "这可能需要5-10分钟（第一次构建较慢）"
echo ""

start_time=$(date +%s)

docker build -f Dockerfile.test -t tau2-test . 2>&1 | tee /tmp/docker_build.log || {
    echo -e "${RED}❌ Docker镜像构建失败${NC}"
    echo ""
    echo "查看完整日志："
    echo "  cat /tmp/docker_build.log"
    exit 1
}

end_time=$(date +%s)
duration=$((end_time - start_time))

echo -e "${GREEN}✅ 构建完成！耗时：${duration}秒${NC}"
echo ""

# 运行测试
echo -e "${YELLOW}🧪 运行测试...${NC}"
echo ""

docker run --rm tau2-test || {
    echo -e "${RED}❌ 测试失败${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}=========================================="
echo "  🎉 所有测试通过！"
echo "==========================================${NC}"
echo ""

# 显示下一步
echo "📤 下一步："
echo ""
echo "   1. 查看更改："
echo "      git status"
echo ""
echo "   2. 提交代码："
echo "      git add ."
echo "      git commit -m 'your message'"
echo ""
echo "   3. 推送到GitHub："
echo "      git push"
echo ""
echo -e "${GREEN}   ✅ GitHub Actions也会通过！${NC}"
echo ""
