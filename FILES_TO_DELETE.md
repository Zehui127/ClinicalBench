# GitHub 仓库清理建议

**仓库**: https://github.com/circadiancity/agentmy
**分析日期**: 2026-03-24

---

## 📊 问题概述

当前仓库存在大量重复、临时和不必要的文件，建议清理以保持仓库整洁。

### 文件统计
- **根目录 Markdown 文档**: 88 个 (其中 70+ 个是临时报告)
- **重复的输出目录**: 3 个 (output/, outputs/, results/)
- **中文目录名**: 1 个 (医学数据标注/)
- **备份/临时文件**: 多个

---

## 🗑️ 建议删除的文件清单

### 1. 临时总结报告 (70+ 个)

这些文件是开发过程中的临时总结，内容重复，应该删除：

#### **COMPLETE/IMPLEMENTATION 类**
```
ALL_DEPARTMENTS_COMPLETE_REPORT.md
ALL_DEPARTMENTS_VALIDATION_REPORT.md
ARCHITECTURE_AND_EVALUATION_COMPLETE.md
COMPLETE_IMPLEMENTATION_SUMMARY.md
COMPLETE_PROJECT_SUMMARY.md
COMPLETION_SUMMARY.md
FINAL_SUMMARY.md
MERGE_COMPLETE_REPORT.md
OPTIMIZATION_COMPLETE_REPORT.md
STEP_3_4_COMPLETE.md
```

#### **INTEGRATION 类**
```
CLINICAL_INTEGRATION_SUMMARY.md
FROM_SCRIPT_TO_ENVIRONMENT_COMPLETE.md
INTEGRATED_GENERATION_TEST_REPORT.md
PRIMEKG_INTEGRATION_COMPLETE.md
REORGANIZATION_SUMMARY.md
```

#### **TASKS_UPGRADE 类**
```
TASKS_V2_IMPROVEMENTS.md
TASKS_V2_FUNDAMENTAL_LIMITATIONS.md
TASKS_V2_UPGRADE_COMPLETE.md
TASKS_V3_IMPROVEMENTS.md
```

#### **GUIDE/USAGE 类 (大部分重复)**
```
11DIMENSIONS_USAGE_GUIDE.md
AUTOMATION_GUIDE.md
CLINICAL_BENCHMARK_GUIDE.md  ← 可能需要保留
CLINICAL_EVALUATION_GUIDE.md  ← 可能需要保留
DOCKER_GUIDE.md
ENHANCED_EVALUATION_GUIDE.md
LINUX_TEST_GUIDE.md
PRIMEKG_LOADER_README.md
PRIMEKG_USAGE_GUIDE.md
QUICK_DOCKER_START.md
QUICKSTART_PRIMEKG.md
```

#### **SUMMARY/REPORT 类**
```
CHINESE_MEDDIALOG_CONVERSION_SUMMARY.md
CLINICAL_CAPABILITY_11DIMENSIONS_FRAMEWORK.md
CLINICAL_DATA_IMPROVEMENT_PLAN.md
CLINICAL_DOMAINS_SUMMARY.md
CLINICAL_TRIAGE_REPORT.md
CONSULTATION_GENERATOR_SUMMARY.md
CONVERSION_REPORT.md
Data_Enhancement_Comparison.md
DATA_INPUT_ANALYSIS.md
DATA_QUALITY_MODULES_USAGE.md
DATA_STRUCTURE_SUMMARY.md
DATA_VALIDATOR_README.md
DATAGENERATOR_VS_PRIMEKG_COMPARISON.md
DATASET_COMPARISON_REPORT.md
DIRECTORY_ANALYSIS.md
ENRICHER_DEMO_RESULTS.md
ENRICHER_TEST_RESULTS.md
EVALUATION_SETUP_SUMMARY.md
FILES_ON_GITHUB.md
GITHUB_UNICLINICAL_STATUS.md
GITHUB_UPLOAD_STATUS.md
INTEGRATED_GENERATION_TEST_REPORT.md
KG_DIALOGUE_GENERATOR_README.md
KG_SYSTEM_COMPLETE_SUMMARY.md
MERGED_TASKS_REPORT.md
MODULES_LOCATION.md
MODULES_OVERVIEW.md
PIPELINE_VERIFICATION_REPORT.md
PRIMEKG_CLARIFICATION.md
PRIMEKG_DATA_SOURCE.md
PRIMEKG_LOADER_README.md
PRIMEKG_RANDOM_WALK_INTEGRATION.md
PRIMEKG_TASKS_SUMMARY.md
QUICK_SYNC.md
REALISTIC_PATIENT_SCENARIOS_DESIGN.md
REALISTIC_SCENARIOS_SUMMARY.md
RESTRUCTURING_PLAN.md
SCRIPT_TO_ENVIRONMENT_TRANSITION.md
STATIC_VS_DYNAMIC_CLARIFICATION.md
SYNC_COMPLETE.md
SYNC_GUIDE.md
TASK_REALISTIC_CRITIQUE_AND_IMPROVEMENT.md
THREADMED_QA_CONVERSION_SUMMARY.md
THREADMED_QA_DOWNLOAD_GUIDE.md
UPLOAD_PLAN.md
V2_IMPLEMENTATION_SUMMARY.md
WHAT_DATAGENERATOR_OPTIMIZES.md
WORKFLOW_EXAMPLE.md
```

#### **其他重复文档**
```
MEDICAL_AGENT_ARCHITECTURE.md
MEDICAL_AGENT_EVALUATION_FRAMEWORK.md
MedicalDialogue_EVALUATION_REQUIREMENTS.md
```

---

### 2. 备份和临时文件

```
tau2-backup-20260309-204305.tar.gz  ← 备份文件
nul                                 ← Windows空设备文件
test_output.txt                     ← 测试输出
```

---

### 3. 输出目录 (应该被 .gitignore)

```
output/
outputs/
results/

# 以及所有子目录：
outputs/final/
outputs/medagentbench/
outputs/medagentbench_auto/
outputs/medagentbench_v2/
outputs/medagentbench_v2_filtered/
outputs/medmcqa/
outputs/medqa/
outputs/medxpertqa_text/
outputs/medxpertqa_text_filtered/
outputs/mmlu_medical/
outputs/stage1_output/
outputs/stage2_output/
outputs/test_run/
outputs/test_run_filtered/
results/primekg/
```

**建议**: 只保留 `.gitignore` 文件，删除所有输出目录

---

### 4. 中文目录名 (跨平台兼容性问题)

```
医学数据标注/  ← 包含子目录 manual_review_all_46/ 等
```

**建议**: 重命名为英文或删除

---

### 5. 临时测试数据文件

```
chinese_internal_medicine_tasks_improved.json
chinese_internal_medicine_tasks_original.json
chinese_internal_medicine_tasks_v2.json
improvement_statistics_v2.json
```

**建议**: 移动到 `data/` 目录或删除

---

## ✅ 应该保留的核心文档 (10-15个)

```
README.md                        ← 主文档
CONTRIBUTING.md                  ← 贡献指南
LICENSE                          ← 许可证
CHANGELOG.md                     ← 变更日志
RELEASE_NOTES.md                 ← 发布说明
VERSIONING.md                    ← 版本管理规范
CLINICAL_BENCHMARK_GUIDE.md      ← 临床基准指南 (可能需要)
CLINICAL_EVALUATION_GUIDE.md     ← 临床评估指南 (可能需要)
DOCKER_GUIDE.md                  ← Docker指南
OPTIMIZATION_SPEC.md             ← 优化规范
```

---

## 📋 .gitignore 建议

确保 `.gitignore` 包含以下内容：

```gitignore
# 输出目录
output/
outputs/
results/

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/

# 备份文件
*.tar.gz
*.backup
*.bak

# 临时文件
test_output.txt
nul

# IDE
.idea/
.vscode/
*.swp
*.swo

# 数据文件
*.json
!data/*.json

# 医学数据标注
医学数据标注/

# 测试缓存
.cache/
.pytest_cache/
```

---

## 🔧 清理步骤

### 方案 A: 保守清理 (推荐)

```bash
# 1. 创建清理脚本
cat > cleanup_repo.sh << 'EOF'
#!/bin/bash

# 删除临时报告文档
rm -f *_SUMMARY.md
rm -f *_REPORT.md
rm -f *_COMPLETE.md
rm -f *_GUIDE.md
rm -f DATAGENERATOR_*.md
rm -f PRIMEKG_*.md
rm -f CLINICAL_*.md  # 保留 CLINICAL_BENCHMARK_GUIDE.md 和 CLINICAL_EVALUATION_GUIDE.md

# 删除备份和临时文件
rm -f *.tar.gz
rm -f nul
rm -f test_output.txt

# 删除输出目录
rm -rf output/
rm -rf outputs/
rm -rf results/

# 删除中文目录
rm -rf 医学数据标注/

# 删除临时JSON文件
rm -f chinese_internal_medicine_tasks_*.json
rm -f improvement_statistics_v2.json

echo "清理完成！"
EOF

chmod +x cleanup_repo.sh
./cleanup_repo.sh
```

### 方案 B: 激进清理

```bash
# 删除所有列出的文件和目录
# (详见上面的完整清单)
```

---

## 📊 清理后的预期效果

| 项目 | 清理前 | 清理后 | 减少 |
|-----|--------|--------|------|
| 根目录文件数 | ~150 | ~20 | -87% |
| Markdown文档 | 88 | 10-15 | -83% |
| 输出目录 | 3 | 0 | -100% |
| 总文件大小 | ~500MB | ~50MB | -90% |

---

## ⚠️ 注意事项

1. **备份重要数据**: 清理前请确保重要数据已备份
2. **团队确认**: 清理大量文档前请与团队成员确认
3. **分支保护**: 建议在新分支上进行清理，确认无误后再合并

---

## 📝 清理后的仓库结构

```
agentmy/
├── README.md                      # 主文档
├── CONTRIBUTING.md                # 贡献指南
├── LICENSE                        # 许可证
├── CHANGELOG.md                   # 变更日志
├── CLINICAL_BENCHMARK_GUIDE.md    # 临床基准指南
├── CLINICAL_EVALUATION_GUIDE.md   # 临床评估指南
├── DOCKER_GUIDE.md                # Docker指南
├── configs/                       # 配置文件
├── data/                          # 数据目录
│   ├── raw/                       # 原始数据
│   ├── processed/                 # 处理后的数据
│   └── primekg_tasks/            # PrimeKG任务
├── src/                           # 源代码
│   └── tau2/                      # tau2框架
├── medical_task_suite/            # 医疗任务套件 (新增)
├── UniClinicalDataEngine/         # ETL引擎
├── DataQualityFiltering/          # 质量过滤
├── DataValidator/                 # 数据验证
├── scripts/                       # 脚本
├── tests/                         # 测试
├── docs/                          # 文档
└── .gitignore                     # Git忽略配置
```

---

**建议优先级**: 🔴 **高优先级** - 建议尽快清理以保持仓库整洁

---

**创建时间**: 2026-03-24
**状态**: 待执行
