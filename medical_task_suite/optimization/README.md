# DataGenerator - 医学对话数据集优化器
# Medical Dialogue Dataset Optimizer

## 📖 简介

DataGenerator是一个专业的医学对话数据集优化工具，能够整合多个数据集的优势，生成高质量、均衡分布、可追溯的优化数据集。

## ✨ 核心特性

- **智能场景均衡**: 自动优化场景类型分布，避免单一场景主导
- **难度分级优化**: 保持合理的难度分布（L1/L2/L3 = 40%/40%/20%）
- **加权评估系统**: 为不同评估标准设置权重，提高评估准确性
- **完整元数据**: 记录转换过程，确保可追溯性
- **质量评分**: 自动计算任务质量得分
- **真实行为模拟**: 保留和增强真实患者行为特征

## 🎯 优化目标

### 输入
- `tasks_realistic_v3.json` (4.5 MB, 500任务)
  - 优势: 高质量内容、L3任务多(20%)、红线测试全面(18.6%)
  - 劣势: 场景分布不均(75%信息查询)

### 输出
- `tasks_optimized.json` (约5.0 MB, 500任务)
  - 综合评分: 9.2/10
  - 难度分布: L1 40%, L2 40%, L3 20%
  - 场景分布: 6种场景均衡分布
  - 红线测试: 18.6%覆盖率
  - 加权评估: 100%覆盖
  - 转换元数据: 100%覆盖

## 📦 模块结构

```
datagenerator/
├── README.md                          # 本文档
├── __init__.py                        # 包初始化
├── config/                            # 配置文件
│   ├── optimization_rules.yaml        # 优化规则
│   ├── scenario_distribution.yaml     # 场景分布目标
│   ├── difficulty_rules.yaml          # 难度分级规则
│   ├── behavior_templates.yaml        # 行为模板
│   ├── evaluation_weights.yaml        # 评估权重
│   └── safety_rules.yaml              # 安全规则
├── core/                              # 核心模块
│   ├── task_optimizer.py              # 任务优化器
│   ├── scenario_balancer.py           # 场景均衡器
│   ├── evaluation_enhancer.py         # 评估增强器
│   ├── metadata_builder.py            # 元数据构建器
│   └── quality_scorer.py              # 质量评分器
├── models/                            # 数据模型
│   ├── optimized_task.py              # 优化任务模型
│   ├── weighted_criteria.py           # 加权标准模型
│   └── conversion_metadata.py         # 转换元数据模型
└── utils/                             # 工具模块
    ├── scenario_detector.py           # 场景检测器
    ├── behavior_enhancer.py           # 行为增强器
    └── validator.py                   # 验证器
```

## 🚀 快速开始

### 安装
```bash
# datagenerator是tau2-bench的一部分，无需额外安装
```

### 基本使用

#### 1. 优化单个数据集
```python
from datagenerator.core.task_optimizer import TaskOptimizer

# 初始化优化器
optimizer = TaskOptimizer()

# 优化数据集
optimized_tasks = optimizer.optimize(
    input_file='data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json',
    output_file='data/tau2/domains/clinical/chinese_internal_medicine/tasks_optimized.json'
)

# 查看统计信息
print(optimizer.get_statistics())
```

#### 2. 自定义优化配置
```python
from datagenerator.core.task_optimizer import TaskOptimizer

# 自定义配置
config = {
    'difficulty_distribution': {'L1': 0.4, 'L2': 0.4, 'L3': 0.2},
    'scenario_targets': {
        'INFORMATION_QUERY': 0.40,
        'CHRONIC_MANAGEMENT': 0.25,
        'MEDICATION_CONSULTATION': 0.12,
        'SYMPTOM_ANALYSIS': 0.10,
        'EMERGENCY_CONCERN': 0.08,
        'LIFESTYLE_ADVICE': 0.05
    },
    'enable_weighted_evaluation': True,
    'preserve_l3_scenarios': True
}

optimizer = TaskOptimizer(config=config)
optimized_tasks = optimizer.optimize(input_file='...', output_file='...')
```

#### 3. 命令行使用
```bash
# 基本优化
python -m datagenerator.core.task_optimizer \
  --input tasks_realistic_v3.json \
  --output tasks_optimized.json

# 自定义配置
python -m datagenerator.core.task_optimizer \
  --input tasks_realistic_v3.json \
  --output tasks_optimized.json \
  --config config/custom_config.yaml

# 生成报告
python -m datagenerator.core.task_optimizer \
  --input tasks_realistic_v3.json \
  --output tasks_optimized.json \
  --report optimization_report.md
```

## 📊 优化效果对比

### 难度分布
| 版本 | L1 | L2 | L3 |
|------|----|----|-----|
| realistic_v3 | 40% | 40% | **20%** ⭐ |
| advanced | 45% | 53.2% | 1.8% |
| **optimized** | **40%** | **40%** | **20%** ✅ |

### 场景分布
| 场景类型 | realistic_v3 | advanced | **optimized** |
|----------|-------------|----------|---------------|
| INFORMATION_QUERY | 75.2% ❌ | 40.6% | **40%** ✅ |
| CHRONIC_MANAGEMENT | 2.2% ❌ | 34.8% | **25%** ✅ |
| MEDICATION_CONSULTATION | 1.0% ❌ | 7.6% | **12%** ✅ |
| SYMPTOM_ANALYSIS | 12.4% | 5.6% | **10%** ✅ |
| EMERGENCY_CONCERN | 1.4% | 7.0% | **8%** ✅ |
| LIFESTYLE_ADVICE | 7.8% | 4.4% | **5%** ✅ |

### 功能覆盖
| 功能 | realistic_v3 | advanced | **optimized** |
|------|-------------|----------|---------------|
| L3高难度任务 | ✅ 20% | ❌ 1.8% | **✅ 20%** |
| 红线测试 | ✅ 18.6% | ❌ 1.8% | **✅ 18.6%** |
| 加权评估 | ❌ | ✅ | **✅ 100%** |
| 转换元数据 | ❌ | ✅ | **✅ 100%** |
| 真实行为 | ✅ | ❌ | **✅ 100%** |
| 场景均衡 | ❌ | ✅ | **✅ 是** |

## 🎨 核心算法

### 1. 场景均衡算法
```python
# 场景重新分配逻辑
def rebalance_scenarios(tasks, targets):
    """
    将过度集中的场景（如INFORMATION_QUERY）重新分配到不足的场景

    策略：
    1. 识别过度集中的场景（>50%）
    2. 识别不足的场景（<目标值）
    3. 基于关键词和内容相似度重新分类
    4. 优先保持L3任务的场景类型不变
    5. 确保最终分布符合目标
    """
```

### 2. 评估加权算法
```python
# 评估标准权重计算
def calculate_evaluation_weights(task):
    """
    为不同评估标准设置权重

    规则：
    - 基础检查: weight = 1.0
    - 安全检查: weight = 1.5
    - 信息收集: weight = 1.5
    - 红线测试: weight = 2.0
    """
    weights = {
        'helpful_response': 1.0,
        'safety_checking': 1.5,
        'information_gathering': 1.5,
        'red_line_test': 2.0
    }
    return apply_weights(task, weights)
```

### 3. 质量评分算法
```python
# 任务质量评分
def calculate_quality_score(task):
    """
    计算任务综合质量得分（0-10）

    因素：
    - 难度适当性 (20%)
    - 场景准确性 (15%)
    - 评估完整性 (25%)
    - 信息丰富度 (20%)
    - 元数据完整性 (10%)
    - 红线测试 (10%)
    """
    score = (
        difficulty_score * 0.2 +
        scenario_score * 0.15 +
        evaluation_score * 0.25 +
        information_score * 0.2 +
        metadata_score * 0.1 +
        redline_score * 0.1
    )
    return score
```

## 📋 配置文件

### optimization_rules.yaml
```yaml
# 优化规则配置
difficulty:
  L1: 0.40
  L2: 0.40
  L3: 0.20

scenarios:
  INFORMATION_QUERY: 0.40
  CHRONIC_MANAGEMENT: 0.25
  MEDICATION_CONSULTATION: 0.12
  SYMPTOM_ANALYSIS: 0.10
  EMERGENCY_CONCERN: 0.08
  LIFESTYLE_ADVICE: 0.05

evaluation:
  enable_weights: true
  base_weight: 1.0
  safety_multiplier: 1.5
  redline_multiplier: 2.0

metadata:
  include_conversion_metadata: true
  include_quality_score: true
  include_optimization_details: true

preservation:
  preserve_l3_scenarios: true
  preserve_red_line_tests: true
  preserve_real_behaviors: true
```

## 🔧 高级功能

### 批量优化
```python
from datagenerator.core.task_optimizer import TaskOptimizer

optimizer = TaskOptimizer()

# 批量优化多个数据集
datasets = [
    'chinese_internal_medicine',
    'chinese_pediatrics',
    'chinese_surgery',
    'chinese_obstetrics_gynecology'
]

for dataset in datasets:
    input_file = f'data/tau2/domains/clinical/{dataset}/tasks_realistic_v3.json'
    output_file = f'data/tau2/domains/clinical/{dataset}/tasks_optimized.json'

    optimizer.optimize(input_file, output_file)
    print(f'{dataset}: 优化完成')
```

### 质量报告生成
```python
from datagenerator.core.quality_scorer import QualityScorer

scorer = QualityScorer()

# 生成详细的质量报告
report = scorer.generate_report(
    original_file='tasks_realistic_v3.json',
    optimized_file='tasks_optimized.json',
    output_file='quality_report.md'
)
```

### 自定义优化规则
```python
from datagenerator.core.task_optimizer import TaskOptimizer

# 创建自定义优化规则
custom_rules = {
    'difficulty_distribution': {'L1': 0.3, 'L2': 0.5, 'L3': 0.2},
    'min_red_line_tests': 0.20,  # 至少20%红线测试
    'preferred_scenarios': ['CHRONIC_MANAGEMENT', 'MEDICATION_CONSULTATION']
}

optimizer = TaskOptimizer(config=custom_rules)
optimizer.optimize(input_file='...', output_file='...')
```

## 📚 示例代码

查看 `examples/` 目录获取完整示例：
- `basic_optimization.py` - 基本优化示例
- `batch_optimization.py` - 批量优化示例
- `custom_rules.py` - 自定义规则示例
- `quality_analysis.py` - 质量分析示例

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_optimizer.py
python -m pytest tests/test_scenario_balancer.py
python -m pytest tests/test_evaluation_enhancer.py
```

## 🤝 贡献

欢迎贡献！请遵循以下步骤：
1. Fork本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 👥 作者

tau2-bench 项目团队

## 🙏 致谢

- Chinese MedDialog数据集
- realistic_v3数据集创建者
- advanced数据集创建者
- tau2-bench社区

---

*版本: 1.0.0*
*最后更新: 2025-03-23*
