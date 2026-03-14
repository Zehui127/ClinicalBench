# 医学问诊多轮对话检测模块

## 概述

这个模块用于检测生成的 task 是否符合医学问诊多轮对话的格式和要求。

## 功能特性

### 1. 医学对话验证器 (`MedicalDialogueValidator`)

验证任务是否符合医学问诊多轮对话的要求：

- **医学术语检测**：检查是否包含足够的医学关键词（支持英文和中文，929+术语）
- **多轮对话结构**：验证是否包含多轮医患对话
- **咨询模式**：检查是否符合患者咨询的问题格式
- **对话标记**：检测对话标记（Patient:, Doctor:, 患者:, 医生:）
- **医学相关性评分**：计算任务的医学相关性分数（0-1）

### 2. 医学对话审查器 (`MedicalDialogueReviewer`)

对医学对话任务进行质量评估：

- **医学相关性** (0-5分)：评估医学内容的丰富程度
- **对话结构** (0-5分)：评估对话结构的合理性
- **咨询质量** (0-5分)：评估患者咨询问题的质量
- **临床真实性** (0-5分)：评估临床场景的真实性

### 3. CLI 检测工具

命令行工具，用于批量检测任务文件。

## 使用方法

### 基本用法

```bash
# 检测单个任务文件
python check_medical_dialogue.py tasks.json

# 自定义阈值
python check_medical_dialogue.py tasks.json --min-keywords 3 --min-turns 3

# 启用严格模式
python check_medical_dialogue.py tasks.json --strict

# 生成 Markdown 报告
python check_medical_dialogue.py tasks.json --format markdown -o report.md

# 详细日志输出
python check_medical_dialogue.py tasks.json --verbose
```

### Python API 使用

#### 验证单个任务

```python
from DataQualityFiltering.validators.medical_dialogue_validator import MedicalDialogueValidator

# 创建验证器
validator = MedicalDialogueValidator(
    min_medical_keywords=2,
    min_dialogue_turns=2,
    strict_mode=False
)

# 验证任务
is_valid, issues = validator.validate(task)

# 计算医学相关性分数
medical_score = validator.calculate_medical_score(task)

# 快速检查是否为医学对话
is_medical = validator.is_medical_dialogue(task)
```

#### 批量验证

```python
from DataQualityFiltering.validators.medical_dialogue_validator import MedicalDialoguePipeline

# 创建管道
pipeline = MedicalDialoguePipeline(
    min_medical_keywords=2,
    min_dialogue_turns=2
)

# 验证多个任务
summary = pipeline.validate_tasks(tasks)

print(f"总任务数: {summary['total_tasks']}")
print(f"医学对话数: {summary['valid_tasks']}")
print(f"通过率: {summary['validity_rate']:.2%}")
print(f"平均医学分数: {summary['avg_medical_score']:.3f}")
```

#### 过滤任务

```python
# 分离有效和无效任务
valid_tasks, invalid_tasks = pipeline.filter_valid_dialogues(tasks)

print(f"有效任务: {len(valid_tasks)}")
print(f"无效任务: {len(invalid_tasks)}")
```

## 任务格式要求

### 必需字段

```json
{
  "id": "任务ID",
  "description": {
    "purpose": "任务目的"
  },
  "ticket": "患者咨询内容",
  "user_scenario": {
    "role": "医生",
    "instructions": {
      "task_instructions": "多轮对话内容"
    }
  },
  "evaluation_criteria": ["评估标准1", "评估标准2"]
}
```

### 医学问诊对话示例

```json
{
  "id": "hypertension_consultation_001",
  "description": {
    "purpose": "患者咨询高血压相关问题"
  },
  "ticket": "医生，我最近血压有点高，想咨询一下应该怎么控制？",
  "user_scenario": {
    "role": "医生",
    "instructions": {
      "task_instructions": "Patient: 医生，我最近血压有点高，想咨询一下应该怎么控制？\nDoctor: 您好，血压高是需要重视的问题。请问您目前的血压是多少？有没有头晕、头痛的症状？\nPatient: 收缩压大概150左右，舒张压95左右。有时候会有点头晕。\nDoctor: 了解。您这个血压确实偏高。请问您平时作息怎么样？有没有家族高血压病史？"
    }
  },
  "evaluation_criteria": [
    "询问血压具体数值",
    "了解症状",
    "询问家族史"
  ]
}
```

## 医学关键词库

验证器包含丰富的医学关键词库：

- **英文医学术语**：症状、疾病、药物、检查、科室等
- **中文医学术语**：症状、疾病、药物、检查、科室、中医术语等
- **总计 929+ 医学关键词**

## 输出格式

### JSON 输出

```json
{
  "timestamp": "2024-03-14T21:33:04",
  "total_tasks": 3,
  "medical_dialogues": 2,
  "non_medical_tasks": 1,
  "passed_tasks": 2,
  "failed_tasks": 0,
  "pass_rate": 100.0,
  "results": [
    {
      "task_id": "test_medical_001",
      "is_medical_dialogue": true,
      "validation_passed": true,
      "review_passed": true,
      "overall_passed": true,
      "medical_relevance_score": 0.29
    }
  ]
}
```

### Markdown 报告

生成包含详细分析和建议的 Markdown 格式报告。

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `min_medical_keywords` | 2 | 最少医学关键词数量 |
| `min_dialogue_turns` | 2 | 最少对话轮数 |
| `strict_mode` | False | 严格模式（警告视为错误） |
| `min_quality_score` | 0.2 | 最低医学相关性分数 |

## 项目结构

```
DataQualityFiltering/
├── validators/
│   ├── __init__.py
│   └── medical_dialogue_validator.py    # 医学对话验证器
├── reviewers/
│   ├── __init__.py
│   └── medical_dialogue_reviewer.py     # 医学对话审查器
├── check_medical_dialogue.py            # CLI 检测工具
├── sample_medical_dialogue.json         # 示例任务文件
└── MEDICAL_DIALOGUE_CHECKER_README.md   # 本文档
```

## 常见问题

### Q: 为什么我的医学任务被判定为非医学对话？

A: 可能的原因：
1. 缺少足够的医学关键词
2. 没有明确的对话结构
3. 缺少对话标记（Patient:, Doctor:, 患者:, 医生:）
4. 不符合咨询问题的格式

### Q: 如何提高医学相关性分数？

A: 可以通过以下方式：
1. 添加更多医学专业术语
2. 增加医患对话轮数
3. 使用明确的对话标记
4. 包含具体的临床细节（症状、检查、治疗等）

### Q: 验证器和审查器有什么区别？

A:
- **验证器**：检查任务是否符合基本格式和要求
- **审查器**：评估任务的质量和给出改进建议

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可

遵循项目主许可。
