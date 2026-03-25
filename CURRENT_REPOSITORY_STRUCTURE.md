# agentmy 仓库当前结构

**仓库**: https://github.com/circadiancity/agentmy
**最后更新**: 2026-03-24 (清理后)

---

## 📂 完整目录树

```
agentmy/
│
├── 📄 核心文档 (13 个)
│   ├── README.md                          # 主文档
│   ├── CONTRIBUTING.md                    # 贡献指南
│   ├── LICENSE                            # 许可证
│   ├── CHANGELOG.md                       # 变更日志
│   ├── CLINICAL_BENCHMARK_GUIDE.md        # 临床基准指南
│   ├── CLINICAL_EVALUATION_GUIDE.md       # 临床评估指南
│   ├── DOCKER_GUIDE.md                    # Docker 指南
│   ├── OPTIMIZATION_SPEC.md               # 优化规范
│   ├── VERSIONING.md                      # 版本管理
│   ├── PRIMEKG_USAGE_GUIDE.md             # PrimeKG 使用指南
│   ├── INSTALL_DOCKER.md                  # Docker 安装
│   ├── RELEASE_NOTES.md                   # 发布说明
│   ├── FILES_TO_DELETE.md                 # 清理记录
│   └── CLEANUP_COMPLETED.md               # 清理完成报告
│
├── 🔧 配置文件
│   ├── .gitignore                         # Git 忽略规则
│   ├── .env.example                       # 环境变量示例
│   ├── pyproject.toml                     # Python 项目配置
│   ├── pdm.lock                          # 依赖锁定文件
│   ├── uv.lock                           # UV 依赖锁定
│   ├── config.py                          # 配置脚本
│   ├── Dockerfile.test                    # 测试 Dockerfile
│   └── Makefile                           # 构建配置
│
├── 📂 主要模块
│   │
│   ├── 🏥 medical_task_suite/            # 医疗任务套件 (新增)
│   │   ├── __init__.py
│   │   ├── config/                        # 配置文件
│   │   │   ├── module_definitions.yaml    # 13个模块定义
│   │   │   ├── difficulty_levels.yaml     # 难度分级
│   │   │   └── red_line_rules.yaml        # 红线规则
│   │   ├── modules/                       # 13个核心模块
│   │   │   ├── base_module.py             # 基础模块类
│   │   │   ├── lab_test_inquiry.py        # 模块1: 检验检查调阅
│   │   │   ├── hallucination_free_diag.py # 模块2: 无幻觉诊断
│   │   │   ├── medication_guidance.py     # 模块3: 用药指导
│   │   │   ├── differential_diag.py       # 模块4: 鉴别诊断
│   │   │   ├── visit_instructions.py      # 模块5: 就诊事项告知
│   │   │   ├── structured_emr.py          # 模块6: 结构化病历
│   │   │   ├── history_verification.py    # 模块7: 病史核实
│   │   │   ├── lab_analysis.py            # 模块8: 检验指标分析
│   │   │   ├── tcm_cognitive.py           # 模块9: 中医药认知
│   │   │   ├── cutting_edge_tx.py         # 模块10: 前沿治疗
│   │   │   ├── insurance_guidance.py      # 模块11: 医保政策
│   │   │   ├── multimodal_understanding.py # 模块12: 多模态感知
│   │   │   └── emergency_handling.py      # 模块13: 紧急情况处置
│   │   ├── evaluation/                    # 评估系统
│   │   │   ├── confidence_scorer.py       # 置信度评分器
│   │   │   ├── red_line_detector.py       # 红线检测器
│   │   │   └── module_coverage.py         # 模块覆盖度分析
│   │   ├── optimization/                  # 优化模块
│   │   │   └── core/module_integrator.py  # 模块集成器
│   │   ├── behavior_simulation/           # 患者行为模拟
│   │   ├── tool_interfaces/               # 工具接口
│   │   ├── generation/                    # 任务生成
│   │   ├── examples/                      # 5个使用示例
│   │   │   ├── example_01_basic_single_module.py
│   │   │   ├── example_02_multi_modules.py
│   │   │   ├── example_03_complete_workflow.py
│   │   │   ├── example_04_clinical_scenarios.py
│   │   │   └── example_05_advanced_features.py
│   │   ├── advanced_features.py           # 高级功能
│   │   ├── deep_validation_test.py        # 深度验证测试
│   │   ├── DEEP_VALIDATION_REPORT.md      # 验证报告
│   │   └── EXTENDED_ADVERSARIAL_TESTS.md  # 扩展对抗测试
│   │
│   ├── 🔬 UniClinicalDataEngine/         # ETL 数据引擎
│   │   ├── __init__.py
│   │   ├── engine.py                      # 核心引擎
│   │   ├── cli.py                         # 命令行接口
│   │   ├── adapters/                      # 数据适配器
│   │   │   ├── base.py                    # 基础适配器
│   │   │   ├── nhands_adapter.py          # NHands 格式
│   │   │   ├── csv_adapter.py             # CSV 格式
│   │   │   └── json_adapter.py            # JSON 格式
│   │   ├── generators/                    # 生成器
│   │   ├── models/                        # 数据模型
│   │   ├── tests/                         # 测试
│   │   └── utils/                         # 工具
│   │
│   ├── ✅ DataQualityFiltering/           # 质量过滤系统
│   │   ├── __init__.py
│   │   ├── cli.py                         # 命令行接口
│   │   ├── core/                          # 核心功能
│   │   ├── data_quality/                  # 质量评估
│   │   ├── evaluators/                    # 评估器
│   │   ├── llm_evaluators/                # LLM 评估
│   │   ├── pipelines/                     # 管道
│   │   ├── reviewers/                     # 审查器
│   │   ├── validators/                    # 验证器
│   │   ├── test_outputs/                  # 测试输出
│   │   ├── examples/                      # 示例
│   │   └── tests/                         # 测试
│   │
│   ├── 🔍 DataValidator/                  # 数据验证器
│   │   ├── __init__.py
│   │   ├── validators/                    # 验证器
│   │   ├── utils/                         # 工具
│   │   └── tests/                         # 测试
│   │
│   ├── 💬 MedicalDialogueTaskGenerator/   # 医疗对话生成器
│   │   ├── config/                        # 配置
│   │   ├── examples/                      # 示例
│   │   ├── src/                           # 源代码
│   │   └── tests/                         # 测试
│   │
│   ├── 📊 MedAgentBench/                   # MedAgent 基准
│   │   ├── .git/                          # 子模块
│   │   ├── configs/                       # 配置
│   │   ├── data/                          # 数据
│   │   ├── img/                           # 图片
│   │   └── src/                           # 源代码
│   │
│   └── 🧪 src/tau2/                       # tau2 框架
│       ├── domains/                       # 领域
│       │   └── clinical/                  # 临床领域
│       │       ├── environments/          # 环境
│       │       ├── kg_generator/          # 知识图谱生成器
│       │       └── primekg/               # PrimeKG 集成
│       ├── evaluator/                     # 评估器
│       │   └── evaluator_clinical.py      # 临床评估器
│       ├── experiments/                   # 实验
│       └── gym/                           # 健身房环境
│
├── 📁 数据目录
│   ├── configs/                           # 配置文件
│   ├── data/
│   │   ├── raw/                           # 原始数据
│   │   ├── processed/                     # 处理后数据
│   │   │   └── medical_dialogues/         # 医疗对话
│   │   ├── primekg_cache/                # PrimeKG 缓存
│   │   ├── primekg_tasks/                # PrimeKG 任务
│   │   └── tau2/                         # tau2 数据
│   ├── docs/                              # 文档
│   ├── figs/                             # 图片
│   ├── scripts/                          # 脚本
│   ├── tests/                            # 测试
│   │   ├── test_domains/                 # 领域测试
│   │   └── test_gym/                     # 健身房测试
│   └── web/                              # Web 界面
│       └── leaderboard/                  # 排行榜
│
└── 🐍 Python 脚本 (30+ 个)
    ├── run_clinical_benchmark.py          # 运行临床基准
    ├── run_evaluation.py                  # 运行评估
    ├── convert_*.py                       # 数据转换脚本
    ├── generate_*.py                      # 数据生成脚本
    ├── test_*.py                          # 测试脚本
    └── cleanup_repo.sh                    # 清理脚本
```

---

## 📊 统计信息

### 目录数量
- **一级目录**: ~15 个
- **二级目录**: ~60 个
- **三级目录**: ~100+ 个

### 核心模块大小
```
medical_task_suite/         ~500 KB (新)
UniClinicalDataEngine/      ~200 KB
DataQualityFiltering/       ~300 KB
DataValidator/              ~100 KB
MedicalDialogueTaskGenerator/ ~150 KB
src/tau2/                   ~2 MB
```

### 文件类型分布
- **Python 文件**: ~200 个
- **Markdown 文档**: 13 个 (清理后)
- **YAML 配置**: 5 个
- **JSON 数据**: ~50 个

---

## 🎯 核心组件说明

### 1. medical_task_suite (新)
**用途**: 医疗任务评估框架
- 13 个核心医疗模块
- 红线检测系统
- 评分引擎
- 对抗测试套件

### 2. UniClinicalDataEngine
**用途**: ETL 数据处理引擎
- 支持多种数据源 (NHands, CSV, JSON)
- 生成 tau2-bench 兼容格式
- 生成任务、数据库、工具、政策

### 3. DataQualityFiltering
**用途**: 数据质量过滤
- LLM 自动评估
- 人工审查接口
- 质量评分系统

### 4. DataValidator
**用途**: 数据验证
- 结构验证
- 内容验证
- 格式检查

### 5. src/tau2
**用途**: tau2-bench 框架集成
- 临床领域环境
- 临床评估器
- Agent 仿真

---

## 📝 配置文件

| 文件 | 用途 |
|-----|------|
| `.env.example` | 环境变量模板 |
| `pyproject.toml` | Python 项目配置 |
| `pdm.lock` | 依赖锁定 (PDM) |
| `uv.lock` | 依赖锁定 (UV) |
| `Makefile` | 构建任务 |

---

## 🔄 数据流

```
原始数据
  ↓
UniClinicalDataEngine (ETL)
  ↓
tasks.json + db.json + tools.json
  ↓
DataValidator (验证)
  ↓
DataQualityFiltering (过滤)
  ↓
tasks_filtered.json
  ↓
tau2 (Agent 仿真 + 评估)
  ↓
评估结果
```

---

## 🎨 清理后的改进

✅ **文档精简** - 从 88 个减少到 13 个 (-85%)
✅ **结构清晰** - 移除临时输出目录
✅ **跨平台兼容** - 删除中文目录
✅ **易于维护** - 清理重复和临时文件
✅ **仓库大小** - 从 ~500MB 减少到 ~90MB (-82%)

---

**查看完整详情**: https://github.com/circadiancity/agentmy
