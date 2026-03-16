# Agent 性能评估子系统

评估 Agent 在医学任务上的表现，提供多维度、全方位的性能分析。

## 功能概述

- ✅ **三维度评估** - 临床准确性、对话流畅性、安全性与同理心
- ✅ **综合审查** - 整合多个评估器的结果
- ✅ **批量处理** - 支持多线程批量评估
- ✅ **详细报告** - 生成 Markdown 评估报告
- ✅ **灵活配置** - 自定义评估维度和权重
- ✅ **缓存机制** - 减少 LLM 调用成本

## 使用方法

### Python API

```python
from DataQualityFiltering.agent_evaluation import (
    AgentEvaluationPipeline,
    MedicalAgentReviewer,
)
import json

# 方式1: 使用评估管道
pipeline = AgentEvaluationPipeline(
    model="gpt-4-turbo",
    max_workers=4,
    pass_threshold=3.5,
)

results = pipeline.evaluate_from_file(
    input_file="agent_results.json",
    output_file="evaluation_results.json",
)

print(f"通过率: {results['statistics']['pass_rate']}%")

# 方式2: 使用审查器
reviewer = MedicalAgentReviewer(model="gpt-4-turbo")

result = reviewer.review(
    patient_question="患者头痛，应该怎么办？",
    ai_response="您好！头痛可能由多种原因引起...",
    context_info="患者，男性，45岁",
)

print(f"总分: {result['overall_score']}")
print(f"通过: {result['pass_status']}")
```

### CLI 工具

#### 评估单个任务

```bash
python -m DataQualityFiltering agent-eval evaluate \
    --input task.json \
    --output result.json \
    --model gpt-4-turbo
```

#### 批量评估

```bash
python -m DataQualityFiltering agent-eval batch \
    --input tasks.json \
    --output results.json \
    --max-workers 8 \
    --model gpt-4-turbo
```

#### 生成报告

```bash
python -m DataQualityFiltering agent-eval report \
    --input results.json \
    --output report.md
```

## 评估维度

### 1. 临床准确性 (40% 权重)

评估医学知识的正确性和诊断推理能力：

- **医学知识** - 医学术语、疾病诊断、治疗方案的准确性
- **诊断推理** - 症状分析、鉴别诊断的逻辑性
- **治疗方案** - 治疗建议的合理性和安全性
- **用药指导** - 药物选择、剂量、注意事项的正确性

**评分标准**:
- 5.0: 完全准确，符合临床规范
- 4.0: 基本准确，有小的瑕疵
- 3.0: 部分准确，有明显不足
- 2.0: 存在错误，需要改进
- 1.0: 严重错误，不建议使用

### 2. 对话流畅性 (35% 权重)

评估对话的连贯性和理解能力：

- **问题理解** - 准确理解患者问题和需求
- **回答连贯** - 回答逻辑清晰，前后一致
- **表达清晰** - 语言表达准确，易于理解
- **交互能力** - 恰当的追问和澄清

**评分标准**:
- 5.0: 对话自然流畅，理解准确
- 4.0: 对话较流畅，理解基本准确
- 3.0: 对话一般，理解有偏差
- 2.0: 对话不连贯，理解有误
- 1.0: 对话混乱，完全误解

### 3. 安全性与同理心 (25% 权重)

评估安全意识和人文关怀：

- **安全警告** - 及时提醒危险症状和就医建议
- **同理心** - 表现出对患者的理解和关心
- **沟通技巧** - 使用恰当的语言和语气
- **隐私保护** - 保护患者隐私信息

**评分标准**:
- 5.0: 安全意识强，同理心表达好
- 4.0: 安全意识较好，有同理心
- 3.0: 安全意识一般，同理心不足
- 2.0: 安全意识弱，缺乏同理心
- 1.0: 无安全意识，冷漠

## 评估器

### ClinicalAccuracyEvaluator

临床准确性评估器：

```python
from DataQualityFiltering.agent_evaluation import ClinicalAccuracyEvaluator

evaluator = ClinicalAccuracyEvaluator(model="gpt-4-turbo")

result = evaluator.evaluate(
    patient_question="...",
    ai_response="...",
    reference_answer="...",  # 可选
)

print(f"分数: {result['overall_score']}")
print(f"优点: {result['strengths']}")
print(f"不足: {result['weaknesses']}")
```

### DialogueFluencyEvaluator

对话流畅性评估器：

```python
from DataQualityFiltering.agent_evaluation import DialogueFluencyEvaluator

evaluator = DialogueFluencyEvaluator(model="gpt-4-turbo")

result = evaluator.evaluate(
    patient_question="...",
    ai_response="...",
)
```

### SafetyEmpathyEvaluator

安全性与同理心评估器：

```python
from DataQualityFiltering.agent_evaluation import SafetyEmpathyEvaluator

evaluator = SafetyEmpathyEvaluator(model="gpt-4-turbo")

result = evaluator.evaluate(
    patient_question="...",
    ai_response="...",
)
```

## 审查器

### MedicalAgentReviewer

综合审查器，整合三个评估维度：

```python
from DataQualityFiltering.agent_evaluation import MedicalAgentReviewer

reviewer = MedicalAgentReviewer(
    model="gpt-4-turbo",
    pass_threshold=3.5,
)

result = reviewer.review(
    patient_question="患者头痛，应该怎么办？",
    ai_response="您好！头痛可能由多种原因引起...",
    context_info="患者，男性，45岁",
    reference_answer="...",  # 可选
    task_id="task_001",
)

# 查看结果
print(f"总分: {result['overall_score']}")
print(f"通过: {result['pass_status']}")

# 各维度分数
print(f"临床准确性: {result['dimension_scores']['clinical_accuracy']}")
print(f"对话流畅性: {result['dimension_scores']['dialogue_fluency']}")
print(f"安全性与同理心: {result['dimension_scores']['safety_empathy']}")

# 详细反馈
print(f"优点: {result['strengths']}")
print(f"不足: {result['weaknesses']}")
print(f"建议: {result['suggestions']}")
```

## 配置选项

### AgentEvaluationPipeline

```python
from DataQualityFiltering.agent_evaluation import AgentEvaluationPipeline

pipeline = AgentEvaluationPipeline(
    # LLM 配置
    model="gpt-4-turbo",  # 或 claude-3-sonnet-20240229, local

    # 并发配置
    max_workers=4,

    # 缓存配置
    cache_dir="./cache/llm",
    use_cache=True,

    # 评估配置
    pass_threshold=3.5,
    save_intermediate=True,
)
```

### MedicalAgentReviewer

```python
from DataQualityFiltering.agent_evaluation import MedicalAgentReviewer

reviewer = MedicalAgentReviewer(
    model="gpt-4-turbo",
    pass_threshold=3.5,
    cache_dir="./cache/llm",
    use_cache=True,
)
```

## 输入数据格式

```json
{
  "items": [
    {
      "task_id": "task_001",
      "patient_question": "患者头痛，应该怎么办？",
      "ai_response": "您好！头痛可能由多种原因引起...",
      "context_info": "患者，男性，45岁",
      "reference_answer": "根据患者描述，建议..."
    },
    ...
  ]
}
```

## 输出格式

### 评估结果

```json
{
  "task_id": "task_001",
  "overall_score": 4.2,
  "pass_status": true,
  "pass_threshold": 3.5,
  "dimension_scores": {
    "clinical_accuracy": 4.5,
    "dialogue_fluency": 4.0,
    "safety_empathy": 4.2
  },
  "strengths": [
    "医学知识准确",
    "诊断逻辑清晰"
  ],
  "weaknesses": [
    "可以更详细地询问症状"
  ],
  "suggestions": [
    "建议追问头痛的具体位置和性质",
    "建议询问伴随症状"
  ],
  "comments": "✅ 良好的医学助手回答，达到高质量标准。",
  "timestamp": "2025-03-15T12:00:00",
  "evaluation_time_seconds": 3.2
}
```

### 统计信息

```json
{
  "total_reviews": 100,
  "passed": 85,
  "failed": 15,
  "pass_rate": 85.0,
  "average_scores": {
    "overall": 4.1,
    "clinical_accuracy": 4.2,
    "dialogue_fluency": 4.0,
    "safety_empathy": 4.1
  },
  "score_distribution": {
    "excellent": 40,
    "good": 30,
    "satisfactory": 15,
    "needs_improvement": 10,
    "poor": 5
  }
}
```

## 自定义评估

### 自定义权重

```python
from DataQualityFiltering.core import EvaluatorBasedReviewer
from DataQualityFiltering.agent_evaluation import (
    ClinicalAccuracyEvaluator,
    DialogueFluencyEvaluator,
    SafetyEmpathyEvaluator,
)

reviewer = EvaluatorBasedReviewer(
    name="custom_reviewer",
    evaluators=[
        ClinicalAccuracyEvaluator(),
        DialogueFluencyEvaluator(),
        SafetyEmpathyEvaluator(),
    ],
    weights={
        "clinical_accuracy": 0.50,  # 提高临床准确性权重
        "dialogue_fluency": 0.30,
        "safety_empathy": 0.20,
    },
    pass_threshold=4.0,  # 提高通过阈值
)
```

### 添加自定义评估器

```python
from DataQualityFiltering.core import DimensionEvaluator

class CustomEvaluator(DimensionEvaluator):
    def __init__(self):
        super().__init__(
            name="custom_evaluator",
            dimension_name="custom_dimension",
            weight=0.1,
        )

    def evaluate_dimension(self, patient_question, ai_response, **kwargs):
        # 实现自定义评估逻辑
        score = self._evaluate(patient_question, ai_response)

        return {
            "score": score,
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
        }

    def _evaluate(self, question, response):
        # 实现
        return 4.0
```

## 最佳实践

1. **选择合适的模型**
   - 高准确性需求: GPT-4 或 Claude Opus
   - 性价比需求: GPT-4-turbo 或 Claude Sonnet
   - 本地部署: 使用 LocalLLMEvaluator

2. **设置合理的阈值**
   - 严格模式: 4.0-4.5（生产环境）
   - 标准模式: 3.5-4.0（一般应用）
   - 宽松模式: 3.0-3.5（开发测试）

3. **优化性能**
   - 启用缓存减少重复调用
   - 调整 `max_workers` 控制并发
   - 使用批量处理提高效率

4. **结果分析**
   - 关注各维度分数分布
   - 分析失败案例的共性
   - 收集反馈用于改进

## 故障排除

### 问题: API 密钥未配置

```bash
# 设置环境变量
export OPENAI_API_KEY="your_key"

# 或在代码中设置
import os
os.environ["OPENAI_API_KEY"] = "your_key"
```

### 问题: 评估速度慢

```python
# 增加并发数
pipeline = AgentEvaluationPipeline(
    model="gpt-4-turbo",
    max_workers=8,  # 增加到 8
)

# 启用缓存
pipeline = AgentEvaluationPipeline(
    use_cache=True,
    cache_dir="./cache/llm",
)
```

### 问题: 评估结果不理想

```python
# 调整权重
reviewer = MedicalAgentReviewer(
    model="gpt-4-turbo",
)
# 修改内部的 DIMENSION_WEIGHTS

# 或使用更强大的模型
reviewer = MedicalAgentReviewer(
    model="gpt-4",  # 使用 GPT-4 而不是 GPT-4-turbo
)
```

## 相关文档

- [主 README](../README.md)
- [数据质量评估文档](../data_quality/README.md)
- [API 参考](../docs/api.md)

---

**版本**: 2.0.0
**更新日期**: 2025-03-15
