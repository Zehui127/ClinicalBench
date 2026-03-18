# 质量阈值筛选系统 (Quality Threshold Filtering)

## 概述

质量阈值筛选系统是对现有 DataQualityFiltering 模块的扩展，实现了基于 0-30 分制的三级质量分类和自动改进功能。

## 主要功能

### 1. 扩展评分系统 (0-30 分制)

| 维度 | 分数范围 | 权重 |
|------|----------|------|
| Clinical Accuracy | 0-10 | 33% |
| Scenario Realism | 0-8 | 27% |
| Evaluation Completeness | 0-7 | 23% |
| Difficulty Appropriateness | 0-5 | 17% |

### 2. 三级质量分类

- **高质量 (≥27分)**：保留
  - 所有维度都达到高标准
  - 临床场景准确、真实
  - 评估标准完整

- **中等质量 (24-26分)**：改进后重新评估
  - 部分维度有改进空间
  - 可通过自动改进提升质量

- **低质量 (<24分)**：剔除
  - 多个维度不达标
  - 存在严重缺陷

### 3. 自动改进机制

- 识别具体不足的维度
- 生成针对性的改进建议
- 自动应用改进
- 重新评估改进效果

## 使用方法

### 基本用法

```bash
# 使用质量阈值筛选
python -m DataQualityFiltering data-quality quality-threshold \
    --input tasks.json

# 自定义阈值
python -m DataQualityFiltering data-quality quality-threshold \
    --input tasks.json \
    --high 27 \
    --medium 24

# 禁用自动改进
python -m DataQualityFiltering data-quality quality-threshold \
    --input tasks.json \
    --no-improvement

# 指定输出目录
python -m DataQualityFiltering data-quality quality-threshold \
    --input tasks.json \
    --output-dir ./results
```

### Python API 使用

```python
from DataQualityFiltering.scoring import ExtendedScoringSystem, ScoringConfig
from DataQualityFiltering.quality_classifier import QualityClassifier
from DataQualityFiltering.quality_threshold_pipeline import QualityThresholdPipeline

# 创建配置
config = ScoringConfig(
    HIGH_THRESHOLD=27.0,
    MEDIUM_THRESHOLD=24.0
)

# 创建管道
pipeline = QualityThresholdPipeline(
    config=config,
    enable_improvement=True,
    output_dir="./outputs/quality_threshold"
)

# 运行管道
results = pipeline.run(tasks, scores_list, original_scores_list)

# 查看结果
print(f"高质量任务: {len(results['high_quality'])}")
print(f"中等质量改进成功: {len(results['medium_quality_improved'])}")
print(f"低质量任务: {len(results['low_quality'])}")
```

## 输出文件

运行质量阈值筛选后，会生成以下文件：

| 文件 | 描述 |
|------|------|
| `tasks_high_quality.json` | 高质量任务（保留） |
| `tasks_improved.json` | 中等质量任务成功改进后 |
| `tasks_failed_improvement.json` | 中等质量任务改进失败 |
| `tasks_low_quality.json` | 低质量任务（拒绝） |
| `quality_statistics.json` | 详细统计信息 |
| `quality_classifications.json` | 每个任务的分级结果 |

## 模块说明

### scoring.py

扩展的评分系统，实现 0-30 分制的评分逻辑。

**主要类**：
- `ScoringConfig`: 评分配置
- `ExtendedScoringSystem`: 评分系统

**主要方法**：
- `normalize_dimension_score()`: 将 5 分制转换为扩展分数
- `calculate_total_score()`: 计算总分（0-30）
- `classify_quality()`: 质量分级

### quality_classifier.py

质量分级器，对任务进行三级分类。

**主要类**：
- `QualityClassificationResult`: 分级结果
- `QualityClassifier`: 分级器

**主要方法**：
- `classify()`: 对单个任务分级
- `batch_classify()`: 批量分级
- `generate_statistics()`: 生成统计信息

### improver.py

任务改进器，自动改进中等质量任务。

**主要类**：
- `ImprovementSuggestion`: 改进建议
- `ImprovementResult`: 改进结果
- `TaskImprover`: 改进器

**主要方法**：
- `improve_medium_quality_task()`: 改进单个任务
- `batch_improve()`: 批量改进

### quality_threshold_pipeline.py

质量阈值筛选管道，整合所有功能。

**主要类**：
- `QualityThresholdPipeline`: 管道

**主要方法**：
- `run()`: 运行完整管道

### reporting.py

报告生成器，生成统计报告和可视化图表。

**主要类**：
- `QualityReportGenerator`: 报告生成器

**主要方法**：
- `generate_comprehensive_report()`: 生成综合报告

## 配置选项

### ScoringConfig

```python
from DataQualityFiltering.scoring import ScoringConfig

config = ScoringConfig(
    # 维度分数范围
    DIMENSION_RANGES={
        "clinical_accuracy": (0, 10),
        "scenario_realism": (0, 8),
        "evaluation_completeness": (0, 7),
        "difficulty_appropriateness": (0, 5),
    },
    # 质量分级阈值
    HIGH_THRESHOLD=27.0,
    MEDIUM_THRESHOLD=24.0,
    # 维度最小及格线（一票否决）
    MIN_DIMENSION_SCORES={
        "clinical_accuracy": 7.0,
        "scenario_realism": 6.0,
        "evaluation_completeness": 5.0,
        "difficulty_appropriateness": 4.0,
    }
)
```

## 示例

### 示例 1: 高质量任务

```json
{
  "id": "task_001",
  "clinical_scenario": "一名45岁男性患者因胸痛2小时就诊...",
  "evaluation_criteria": {
    "actions": [...],
    "nl_assertions": [
      "AI 应询问疼痛的持续时间、性质、放射部位",
      "AI 应建议立即进行心电图检查",
      "AI 应包含安全警告"
    ]
  }
}
```

**评分结果**: 27.5/30 → HIGH → 保留

### 示例 2: 中等质量任务（改进前）

```json
{
  "id": "task_002",
  "clinical_scenario": "患者主诉头痛3天。",
  "evaluation_criteria": {
    "actions": [...],
    "nl_assertions": [
      "AI 应询问头痛的部位和性质"
    ]
  }
}
```

**评分结果**: 22.5/30 → MEDIUM → 自动改进

**改进后**: 添加了安全警告、详细的评估标准

**新评分**: 25.5/30 → 仍然 MEDIUM → 未能提升到 HIGH

### 示例 3: 低质量任务

```json
{
  "id": "task_003",
  "clinical_scenario": "患者不舒服。",
  "evaluation_criteria": {
    "actions": [],
    "nl_assertions": []
  }
}
```

**评分结果**: 18.0/30 → LOW → 拒绝

## 注意事项

1. **分数来源**：当前版本使用默认分数进行测试。实际使用时，需要先运行评分系统或提供预计算的分数文件。

2. **改进机制**：自动改进功能基于启发式规则，可能不完美。对于重要任务，建议人工审核。

3. **一票否决**：任何维度低于最低要求都会导致任务被拒绝（LOW）。

4. **输出编码**：所有输出文件使用 UTF-8 编码。

## 扩展和定制

### 添加新的评分维度

1. 在 `ScoringConfig` 中添加新的维度范围
2. 在 `ExtendedScoringSystem` 中实现评分逻辑
3. 更新权重配置

### 自定义改进策略

1. 继承 `TaskImprover` 类
2. 重写 `_generate_improvement_suggestions()` 方法
3. 实现自定义的改进逻辑

### 自定义报告格式

1. 继承 `QualityReportGenerator` 类
2. 重写报告生成方法
3. 添加自定义的可视化图表

## 常见问题

**Q: 如何从 5 分制转换为扩展分数？**

A: 使用 `ExtendedScoringSystem.convert_from_5_point_scale()` 方法：
```python
scoring_system = ExtendedScoringSystem()
extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
```

**Q: 改进后的任务是否保存？**

A: 是的，改进后的任务保存在 `tasks_improved.json` 中。

**Q: 如何调整阈值？**

A: 使用 CLI 参数或创建自定义的 `ScoringConfig`：
```bash
python -m DataQualityFiltering data-quality quality-threshold \
    --input tasks.json \
    --high 28 \
    --medium 25
```

## 版本历史

- **v1.0** (2025-03-17): 初始版本
  - 实现 0-30 分制评分系统
  - 实现三级质量分类
  - 实现自动改进机制
  - 实现 CLI 接口
  - 实现报告生成

## 许可证

与 agentmy 项目相同。

## 联系方式

如有问题或建议，请提交 issue 或 pull request。
