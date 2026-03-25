# Tau2 医疗评估系统使用指南

## 概述

Tau2 框架现已集成医疗评估能力，从"通用 Agent 评测框架"升级为"医疗 Agent 评测框架"。

本文档说明如何使用新的医疗评估功能来评估 AI 医学助手在医疗场景中的表现。

## 核心组件

### 1. 数据模型增强

#### 新增 RewardType

```python
class RewardType(str, Enum):
    DB = "DB"
    ENV_ASSERTION = "ENV_ASSERTION"
    NL_ASSERTION = "NL_ASSERTION"
    ACTION = "ACTION"
    COMMUNICATE = "COMMUNICATE"
    CLINICAL = "CLINICAL"  # 新增：医疗/临床评估
```

#### 新增 ClinicalCheck 数据模型

```python
class ClinicalCheck(BaseModel):
    overall_score: float  # 总体评分 (0-5)
    dimension_scores: dict  # 各维度详细分数
    met: bool  # 是否达到阈值
    reward: float  # 归一化奖励 (0-1)
    strengths: Optional[list[str]]  # 优点
    weaknesses: Optional[list[str]]  # 不足
    suggestions: Optional[list[str]]  # 改进建议
    comments: Optional[str]  # 评语
```

### 2. 评估器架构

#### 三个维度评估器

**ClinicalAccuracyEvaluator** (临床准确性 - 40% 权重)
- 医学知识准确性 (30%)
- 诊断推理合理性 (30%)
- 治疗建议适当性 (25%)
- 安全警告 (15%)

**DialogueFluencyEvaluator** (对话流畅性 - 30% 权重)
- 问题理解能力 (25%)
- 回答连贯性 (25%)
- 语言表达清晰度 (25%)
- 交互能力 (25%)

**SafetyEmpathyEvaluator** (安全性与同理心 - 30% 权重)
- 安全意识 (40%)
- 同理心表达 (35%)
- 沟通技巧 (25%)

#### 综合评估器

**ClinicalEvaluator** (继承自 EvaluatorBase)
- 整合三个维度评估器
- 实现标准的 `calculate_reward` 接口
- 返回符合 tau2 规范的 RewardInfo

### 3. 评估类型

```python
class EvaluationType(str, Enum):
    # ... 原有类型 ...
    CLINICAL = "clinical"  # 纯医疗评估
    ALL_WITH_CLINICAL = "all_with_clinical"  # 综合+医疗评估
```

## 使用方法

### 方法 1: 纯医疗评估

仅使用医疗评估器评估 Agent 表现：

```python
from tau2.evaluator import ClinicalEvaluator
from tau2.data_model.tasks import Task
from tau2.data_model.message import Message

# 假设你有任务和对话轨迹
task: Task = ...  # 医疗任务对象
full_trajectory: list[Message] = ...  # 对话历史

# 执行医疗评估
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=full_trajectory,
    model="gpt-4",  # 可选：指定 LLM
)

# 查看结果
print(f"总奖励: {reward_info.reward}")
print(f"临床检查: {reward_info.clinical_checks}")

for check in reward_info.clinical_checks:
    print(f"\n总分: {check.overall_score}/5.0")
    print(f"通过: {check.met}")
    print(f"\n维度分数:")
    for dim, scores in check.dimension_scores.items():
        print(f"  {dim}: {scores}")
    print(f"\n优点: {check.strengths}")
    print(f"不足: {check.weaknesses}")
    print(f"建议: {check.suggestions}")
```

### 方法 2: 综合评估（包含医疗评估）

结合环境断言、动作检查、通信检查和医疗评估：

```python
from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType
from tau2.data_model.simulation import SimulationRun

# 假设你有模拟运行结果
simulation_run: SimulationRun = ...
task: Task = ...

# 执行综合评估（包含医疗）
reward_info = evaluate_simulation(
    simulation=simulation_run,
    task=task,
    evaluation_type=EvaluationType.ALL_WITH_CLINICAL,  # 关键参数
    solo_mode=False,
    domain="healthcare",  # 医疗领域
    clinical_model="gpt-4",  # 可选：指定医疗评估的模型
)

# 查看综合结果
print(f"总奖励: {reward_info.reward}")
print(f"奖励构成: {reward_info.reward_breakdown}")
print(f"临床检查: {reward_info.clinical_checks}")
print(f"动作检查: {reward_info.action_checks}")
print(f"通信检查: {reward_info.communicate_checks}")
```

### 方法 3: 在任务配置中启用医疗评估

在任务的 `evaluation_criteria` 中添加 `CLINICAL` 到 `reward_basis`：

```python
from tau2.data_model.tasks import Task, EvaluationCriteria, RewardType
from tau2.data_model.user_scenario import UserScenario
from tau2.data_model.tasks import StructuredUserInstructions

# 创建用户指令
user_instructions = StructuredUserInstructions(
    domain="healthcare",  # 医疗领域
    reason_for_call="患者咨询头痛症状",
    task_instructions="作为医疗助手，评估患者的头痛症状并给出建议"
)

# 创建评估标准
evaluation_criteria = EvaluationCriteria(
    reward_basis=[
        RewardType.CLINICAL,  # 启用医疗评估
        RewardType.COMMUNICATE,  # 可选：同时启用通信评估
    ],
    nl_assertions=[
        "助手应该询问头痛的具体位置和性质",
        "助手应该识别危险信号并建议就医",
    ]
)

# 创建任务
task = Task(
    id="medical_task_001",
    user_scenario=UserScenario(instructions=user_instructions),
    evaluation_criteria=evaluation_criteria,
)
```

## 权重自定义

### 默认权重

```python
DEFAULT_WEIGHTS = {
    "clinical_accuracy": 0.40,    # 临床准确性 40%
    "dialogue_fluency": 0.30,     # 对话流畅性 30%
    "safety_empathy": 0.30,       # 安全性与同理心 30%
}
```

### 自定义权重

```python
# 创建评估器时传入自定义权重
from tau2.evaluator import ClinicalEvaluator

evaluator = ClinicalEvaluator(
    model="gpt-4",
    weights={
        "clinical_accuracy": 0.50,    # 提高临床准确性权重
        "dialogue_fluency": 0.25,
        "safety_empathy": 0.25,
    },
    pass_threshold=3.5,  # 提高通过阈值
)

# 使用类方法时传入权重
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    weights={
        "clinical_accuracy": 0.50,
        "dialogue_fluency": 0.25,
        "safety_empathy": 0.25,
    }
)
```

## 评估流程

### 1. 数据准备

确保任务对象包含：
- `domain`: 设置为 "healthcare" 或其他医疗相关领域
- `user_scenario`: 包含患者的咨询内容
- `evaluation_criteria`: 包含 `reward_basis` 和 `CLINICAL` 类型

### 2. 对话轨迹

`full_trajectory` 应包含完整的消息历史：
```python
[
    Message(role="user", content="患者问题..."),
    Message(role="assistant", content="AI 回答..."),
    # ... 可选的后续对话
]
```

### 3. 评估执行

```python
# 自动提取患者问题和 AI 回答
patient_question, ai_response = evaluator._extract_dialogue(full_trajectory)

# 自动提取上下文信息
context_info = evaluator._extract_context(task)

# 并行执行三个维度评估
accuracy_result = clinical_accuracy_eval.evaluate(...)
fluency_result = dialogue_fluency_eval.evaluate(...)
safety_result = safety_empathy_eval.evaluate(...)

# 整合结果
clinical_check = evaluator._combine_results(...)
```

### 4. 结果整合

最终返回的 `RewardInfo` 包含：
- `reward`: 总体奖励分数 (0-1)
- `clinical_checks`: 临床检查列表
- `reward_basis`: 标记包含 `CLINICAL` 类型
- `reward_breakdown`: 各类型奖励分解

## 完整示例

### 示例 1: 评估医学问答

```python
from tau2.evaluator import ClinicalEvaluator
from tau2.data_model.tasks import Task, make_task
from tau2.data_model.tasks import EvaluationCriteria, StructuredUserInstructions
from tau2.data_model.message import Message
from tau2.data_model.tasks import RewardType

# 准备对话数据
messages = [
    Message(role="user", content="医生，我最近经常头痛，特别是早上，有时候还会恶心，这是什么问题？"),
    Message(role="assistant", content="""您好，头痛和恶心这些症状需要引起重视。根据您的描述，可能的原因包括：

1. 偏头痛：典型表现为单侧搏动性头痛，可伴有恶心
2. 高血压：晨起头痛是高血压的常见症状
3. 颅内压增高：需要警惕

我强烈建议您尽快到医院就诊，特别是神经内科。医生可能会建议做头颅CT或MRI检查。在此之前，请记录头痛的时间、频率、疼痛程度等信息，这对诊断很有帮助。

请问：您的血压正常吗？家族有高血压病史吗？"""),
]

# 创建任务
user_instructions = StructuredUserInstructions(
    domain="healthcare",
    reason_for_call="患者咨询头痛症状",
    task_instructions="评估患者的头痛症状，识别危险信号，并给出适当的就医建议"
)

evaluation_criteria = EvaluationCriteria(
    reward_basis=[RewardType.CLINICAL],
    nl_assertions=[
        "助手应该识别头痛伴恶心的危险信号",
        "助手应该建议患者及时就医",
        "助手应该避免给出具体诊断"
    ]
)

task = make_task(
    user_instructions=user_instructions,
    eval_criteria=evaluation_criteria,
    message_history=messages
)

# 执行评估
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=messages,
    model="gpt-4"
)

# 输出结果
print("=" * 60)
print("医疗评估结果")
print("=" * 60)
print(f"总体奖励: {reward_info.reward:.3f}")
print()

for check in reward_info.clinical_checks:
    print(f"临床总分: {check.overall_score}/5.0")
    print(f"评估结果: {'✅ 通过' if check.met else '❌ 未通过'}")
    print()

    print("维度分数:")
    for dim_name, scores in check.dimension_scores.items():
        print(f"\n{dim_name}:")
        for score_name, score_data in scores.items():
            if isinstance(score_data, dict):
                print(f"  {score_name}: {score_data['score']:.2f}")
                print(f"    理由: {score_data['reasoning'][:100]}...")

    print("\n优点:")
    for strength in (check.strengths or []):
        print(f"  + {strength}")

    print("\n不足:")
    for weakness in (check.weaknesses or []):
        print(f"  - {weakness}")

    print("\n建议:")
    for suggestion in (check.suggestions or []):
        print(f"  * {suggestion}")

    print(f"\n评语: {check.comments}")
```

### 示例 2: 批量评估医疗任务

```python
from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType
from tau2.data_model.simulation import SimulationRun
from tau2.data_model.tasks import Task
import pandas as pd

# 假设你有多个医疗任务
results = []

for task in medical_tasks:
    # 运行模拟（假设已有）
    simulation_run = run_simulation(task, agent)

    # 执行综合评估
    reward_info = evaluate_simulation(
        simulation=simulation_run,
        task=task,
        evaluation_type=EvaluationType.ALL_WITH_CLINICAL,
        solo_mode=False,
        domain="healthcare",
    )

    # 记录结果
    results.append({
        "task_id": task.id,
        "total_reward": reward_info.reward,
        "clinical_score": reward_info.clinical_checks[0].overall_score,
        "clinical_met": reward_info.clinical_checks[0].met,
        "action_score": reward_info.action_checks[0].action_reward if reward_info.action_checks else None,
        "communicate_score": len([c for c in reward_info.communicate_checks if c.met]) if reward_info.communicate_checks else None,
    })

# 转换为 DataFrame
df = pd.DataFrame(results)

# 分析结果
print("医疗任务评估统计:")
print(f"平均总分: {df['total_reward'].mean():.3f}")
print(f"平均临床分数: {df['clinical_score'].mean():.2f}")
print(f"临床评估通过率: {df['clinical_met'].mean():.1%}")
```

## 最佳实践

### 1. 领域检测

自动检测是否为医疗领域：

```python
def is_medical_domain(task: Task) -> bool:
    """检测任务是否属于医疗领域"""
    medical_keywords = [
        "医疗", "医学", "健康", "诊断", "治疗",
        "症状", "疾病", "患者", "医生", "医院"
    ]

    domain = task.user_scenario.instructions.domain.lower()
    return any(keyword in domain for keyword in medical_keywords)
```

### 2. 条件评估

根据任务类型自动选择评估方式：

```python
from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType

def smart_evaluate(simulation, task):
    """根据任务类型智能选择评估方式"""

    if is_medical_domain(task):
        # 医疗任务：使用综合评估
        return evaluate_simulation(
            simulation=simulation,
            task=task,
            evaluation_type=EvaluationType.ALL_WITH_CLINICAL,
            solo_mode=False,
            domain="healthcare",
        )
    else:
        # 通用任务：使用标准评估
        return evaluate_simulation(
            simulation=simulation,
            task=task,
            evaluation_type=EvaluationType.ALL,
            solo_mode=False,
            domain=task.user_scenario.instructions.domain,
        )
```

### 3. 模型选择

为不同评估维度选择合适的模型：

```python
# 高准确性要求：使用 GPT-4
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    model="gpt-4",
)

# 快速评估：使用 GPT-3.5
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    model="gpt-3.5-turbo",
)
```

### 4. 错误处理

```python
try:
    reward_info = ClinicalEvaluator.calculate_reward(
        task=task,
        full_trajectory=trajectory,
    )

    # 检查是否有错误
    for check in reward_info.clinical_checks:
        if check.comments and "评估失败" in check.comments:
            print(f"评估失败: {check.comments}")
            # 处理失败情况
            continue

        # 正常处理
        process_result(check)

except Exception as e:
    print(f"评估异常: {e}")
    # 使用备用评估方案
    reward_info = fallback_evaluation(task, trajectory)
```

## 架构优势

### 1. 模块化设计

- 三个维度评估器独立运行
- 可单独使用或组合使用
- 易于扩展新的评估维度

### 2. 标准接口

- 继承 `EvaluatorBase` 基类
- 实现 `calculate_reward` 方法
- 返回标准的 `RewardInfo` 格式

### 3. 无缝集成

- 与现有 tau2 评估系统完全兼容
- 可与其他评估类型组合
- 不影响原有功能

### 4. 灵活配置

- 支持权重自定义
- 支持阈值调整
- 支持模型选择

## 性能考虑

### 评估时间

- 单次医疗评估约需 10-30 秒（取决于模型和响应长度）
- 三个维度评估器并行运行（如果实现异步）
- 可通过 `model` 参数切换更快的模型

### 成本优化

```python
# 开发阶段：使用快速模型
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    model="gpt-3.5-turbo",  # 成本低，速度快
)

# 生产阶段：使用准确模型
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    model="gpt-4",  # 准确性高
)
```

### 缓存机制

医疗评估器支持结果缓存（通过 `cache_dir` 参数）：

```python
evaluator = ClinicalEvaluator(
    model="gpt-4",
    cache_dir="./cache/clinical_eval",
    use_cache=True,
)
```

## 后续扩展

### 可能的新增维度

1. **伦理合规性评估**
   - 隐私保护
   - 知情同意
   - 伦理边界

2. **文化适应性评估**
   - 语言本地化
   - 文化敏感性
   - 医疗系统差异

3. **成本效益评估**
   - 医疗资源利用
   - 时间效率
   - 经济效益

### 集成其他医疗数据集

- MedQA
 - MedDialog
- PubMedQA
- DoctorQA

## 故障排查

### 问题 1: 导入错误

```python
# 错误: from tau2.evaluator import ClinicalEvaluator
# 解决: 确保使用最新版本的 tau2
pip install --upgrade tau2
```

### 问题 2: LLM API 调用失败

```python
# 检查 API 密钥
import os
assert os.getenv("OPENAI_API_KEY"), "请设置 OPENAI_API_KEY"

# 或使用 anthropic
reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=trajectory,
    model="claude-3-opus",  # 使用 Anthropic 模型
)
```

### 问题 3: 评估结果不准确

- 检查 `full_trajectory` 是否包含完整的对话
- 检查任务 `domain` 是否正确设置
- 尝试调整 `pass_threshold` 阈值
- 尝试使用更强大的模型（如 GPT-4）

## 总结

Tau2 医疗评估系统提供了：

1. **全面的多维度评估**：临床准确性、对话流畅性、安全性与同理心
2. **标准化接口**：与 tau2 框架无缝集成
3. **灵活的配置**：自定义权重、阈值、模型
4. **易于使用**：简单的 API，清晰的结果格式

通过这套系统，tau2 从通用 Agent 评测框架进化为专业的医疗 Agent 评测框架，为医疗 AI 的开发和质量保证提供了强大的工具。
