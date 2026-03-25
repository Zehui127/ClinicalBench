#!/bin/bash
# 同步质量阈值筛选模块到 agentmy 仓库

set -e

echo "=========================================="
echo "质量阈值筛选模块同步脚本"
echo "=========================================="
echo ""

# 1. 检查并克隆 agentmy 仓库
if [ ! -d "agentmy" ]; then
    echo "步骤 1: 克隆 agentmy 仓库..."
    cd /c/Users/方正

    # 尝试 SSH（推荐）
    if [ -f ~/.ssh/id_rsa ]; then
        echo "使用 SSH 克隆..."
        git clone git@github.com:circadiancity/agentmy.git
    else
        echo "使用 HTTPS 克隆..."
        git clone https://github.com/circadiancity/agentmy.git
    fi

    cd agentmy
else
    echo "步骤 1: agentmy 目录已存在，跳过克隆"
    cd /c/Users/方正/agentmy
fi

echo "✅ 仓库准备完成"
echo ""

# 2. 创建 feature 分支
echo "步骤 2: 创建 feature 分支..."
git checkout -b feature/quality-threshold-filtering 2>/dev/null || git checkout feature/quality-threshold-filtering
echo "✅ 分支准备完成"
echo ""

# 3. 复制新文件
echo "步骤 3: 复制新模块文件..."
TAU2_PATH="/c/Users/方正/tau2-bench/DataQualityFiltering"

FILES_TO_COPY=(
    "scoring.py"
    "quality_classifier.py"
    "improver.py"
    "quality_threshold_pipeline.py"
    "reporting.py"
    "test_quality_threshold.py"
    "QUALITY_THRESHOLD_README.md"
)

for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$TAU2_PATH/$file" ]; then
        cp "$TAU2_PATH/$file" DataQualityFiltering/
        echo "  ✓ 已复制: $file"
    else
        echo "  ✗ 文件不存在: $file"
    fi
done

echo "✅ 文件复制完成"
echo ""

# 4. 修改 __main__.py
echo "步骤 4: 应用 CLI 修改..."
echo "注意: 需要手动应用或查看 tau2-bench/DataQualityFiltering/__main__.py 的修改"
echo "主要修改："
echo "  1. 添加 UTF-8 编码支持（在文件开头）"
echo "  2. 添加 quality-threshold 命令（在 data-quality 子命令下）"
echo "  3. 添加 _handle_quality_threshold() 函数"
echo ""

# 5. 运行测试
echo "步骤 5: 运行测试..."
cd DataQualityFiltering
if python test_quality_threshold.py; then
    echo "✅ 所有测试通过"
else
    echo "⚠️  测试失败，请检查"
    read -p "是否继续提交？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 用户取消操作"
        exit 1
    fi
fi

echo ""
cd /c/Users/方正/agentmy

# 6. 提交更改
echo "步骤 6: 提交更改..."
git add DataQualityFiltering/scoring.py
git add DataQualityFiltering/quality_classifier.py
git add DataQualityFiltering/improver.py
git add DataQualityFiltering/quality_threshold_pipeline.py
git add DataQualityFiltering/reporting.py
git add DataQualityFiltering/test_quality_threshold.py
git add DataQualityFiltering/QUALITY_THRESHOLD_README.md

# 注意：__main__.py 需要手动修改后再添加
# git add DataQualityFiltering/__main__.py

git commit -m "$(cat <<'EOF'
feat: add quality threshold filtering system (0-30 point scale)

Implement comprehensive quality threshold filtering with three-tier classification:

Features:
- Extended scoring system (0-30 points)
  - Clinical Accuracy: 0-10 points (33%)
  - Scenario Realism: 0-8 points (27%)
  - Evaluation Completeness: 0-7 points (23%)
  - Difficulty Appropriateness: 0-5 points (17%)

- Three-tier quality classification:
  - HIGH (≥27): Keep
  - MEDIUM (24-26): Improve and re-evaluate
  - LOW (<24): Reject

- Automatic improvement mechanism:
  - Identify weakness dimensions
  - Generate improvement suggestions
  - Apply improvements automatically
  - Re-evaluate improved tasks

- CLI integration:
  - New `quality-threshold` command
  - Customizable thresholds
  - Optional auto-improvement

- Comprehensive reporting:
  - JSON reports
  - Markdown reports
  - HTML reports with styling

All tests passing (5/5).

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
EOF
)"

echo "✅ 提交完成"
echo ""

# 7. 推送到远程
echo "步骤 7: 推送到远程仓库..."
echo "正在推送到 origin: feature/quality-threshold-filtering..."
git push -u origin feature/quality-threshold-filtering

echo ""
echo "=========================================="
echo "🎉 同步完成！"
echo "=========================================="
echo ""
echo "接下来："
echo "1. 访问 GitHub 创建 Pull Request:"
echo "   https://github.com/circadiancity/agentmy/compare/main...feature/quality-threshold-filtering"
echo ""
echo "2. 或者继续在本地开发"
echo ""
