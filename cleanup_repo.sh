#!/bin/bash
# GitHub仓库清理脚本
# 仓库: circadiancity/agentmy

echo "============================================"
echo "  GitHub 仓库清理脚本"
echo "  仓库: circadiancity/agentmy"
echo "============================================"
echo ""

# 询问用户
echo "此脚本将删除以下内容："
echo "  1. 70+ 个临时总结报告 (.md文件)"
echo "  2. 备份和临时文件"
echo "  3. 输出目录 (output/, outputs/, results/)"
echo "  4. 中文目录名 (医学数据标注/)"
echo "  5. 临时JSON数据文件"
echo ""
echo "预计清理: ~450MB 文件"
echo ""
read -p "是否继续？(y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "已取消清理。"
    exit 0
fi

echo ""
echo "开始清理..."
echo ""

# ============================================================================
# 1. 删除临时总结报告 (保守清理，保留重要文档)
# ============================================================================
echo "[1/6] 删除临时总结报告..."

# 删除各类SUMMARY和REPORT
rm -f *_SUMMARY.md
rm -f *_REPORT.md
rm -f *_COMPLETE.md
rm -f *_ANALYSIS.md
rm -f *_COMPARISON.md

# 删除特定的重复文档
rm -f 11DIMENSIONS_USAGE_GUIDE.md
rm -f AUTOMATION_GUIDE.md
rm -f ENHANCED_EVALUATION_GUIDE.md
rm -f LINUX_TEST_GUIDE.md
rm -f QUICK_DOCKER_START.md
rm -f QUICKSTART_PRIMEKG.md
rm -f QUICK_SYNC.md
rm -f SYNC_GUIDE.md
rm -f SYNC_COMPLETE.md
rm -f GITHUB_UNICLINICAL_STATUS.md
rm -f GITHUB_UPLOAD_STATUS.md
rm -f FILES_ON_GITHUB.md
rm -f UPLOAD_PLAN.md

# 删除 DATAGENERATOR 和 PRIMEKG 相关的重复文档
rm -f DATAGENERATOR_*.md
rm -f PRIMEKG_CLARIFICATION.md
rm -f PRIMEKG_DATA_SOURCE.md
rm -f PRIMEKG_LOADER_README.md
rm -f PRIMEKG_RANDOM_WALK_INTEGRATION.md
rm -f PRIMEKG_TASKS_SUMMARY.md
rm -f KG_DIALOGUE_GENERATOR_README.md
rm -f KG_SYSTEM_COMPLETE_SUMMARY.md

# 删除 TASKS 相关文档
rm -f TASKS_V2_*.md
rm -f TASKS_V3_*.md
rm -f TASK_REALISTIC_CRITIQUE_AND_IMPROVEMENT.md

# 删除其他重复文档
rm -f MEDICAL_AGENT_ARCHITECTURE.md
rm -f MEDICAL_AGENT_EVALUATION_FRAMEWORK.md
rm -f MedicalDialogue_EVALUATION_REQUIREMENTS.md
rm -f FROM_SCRIPT_TO_ENVIRONMENT_COMPLETE.md
rm -f SCRIPT_TO_ENVIRONMENT_TRANSITION.md
rm -f REORGANIZATION_SUMMARY.md
rm -f RESTRUCTURING_PLAN.md
rm -f STATIC_VS_DYNAMIC_CLARIFICATION.md

echo "  ✓ 已删除临时报告"

# ============================================================================
# 2. 删除备份和临时文件
# ============================================================================
echo "[2/6] 删除备份和临时文件..."

rm -f *.tar.gz
rm -f *.backup
rm -f *.bak
rm -f nul
rm -f test_output.txt

echo "  ✓ 已删除备份和临时文件"

# ============================================================================
# 3. 删除输出目录
# ============================================================================
echo "[3/6] 删除输出目录..."

rm -rf output/
rm -rf outputs/
rm -rf results/

echo "  ✓ 已删除输出目录"

# ============================================================================
# 4. 删除中文目录名
# ============================================================================
echo "[4/6] 删除中文目录..."

rm -rf 医学数据标注/

echo "  ✓ 已删除中文目录"

# ============================================================================
# 5. 删除临时JSON数据文件
# ============================================================================
echo "[5/6] 删除临时JSON文件..."

rm -f chinese_internal_medicine_tasks_improved.json
rm -f chinese_internal_medicine_tasks_original.json
rm -f chinese_internal_medicine_tasks_v2.json
rm -f improvement_statistics_v2.json

echo "  ✓ 已删除临时JSON文件"

# ============================================================================
# 6. 更新 .gitignore
# ============================================================================
echo "[6/6] 更新 .gitignore..."

if [ -f .gitignore ]; then
    # 备份原 .gitignore
    cp .gitignore .gitignore.backup

    # 添加新的忽略规则（如果不存在）
    grep -q "^output/$" .gitignore || echo "output/" >> .gitignore
    grep -q "^outputs/$" .gitignore || echo "outputs/" >> .gitignore
    grep -q "^results/$" .gitignore || echo "results/" >> .gitignore
    grep -q "^医学数据标注/$" .gitignore || echo "医学数据标注/" >> .gitignore
    grep -q "*.tar.gz" .gitignore || echo "*.tar.gz" >> .gitignore
    grep -q "^nul$" .gitignore || echo "nul" >> .gitignore

    echo "  ✓ .gitignore 已更新"
else
    echo "  ⚠ .gitignore 文件不存在，跳过"
fi

# ============================================================================
# 清理完成
# ============================================================================
echo ""
echo "============================================"
echo "  清理完成！"
echo "============================================"
echo ""
echo "建议的后续步骤："
echo "  1. 检查删除的文件: git status"
echo "  2. 提交更改: git add . && git commit -m 'chore: clean up repository'"
echo "  3. 推送到GitHub: git push my_github main"
echo ""
echo "如需恢复，请使用: git checkout -- <filename>"
echo ""
