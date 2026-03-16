#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agentmy 系统完整运作流程示例

展示新数据从进入到产生结果的完整流程
"""

print("=" * 80)
print("agentmy 系统运作流程详解")
print("=" * 80)

# =============================================================================
# 阶段 1: 数据准备
# =============================================================================

print("\n【阶段 1】数据准备")
print("-" * 80)

print("""
原始数据格式示例 (medical_dialogues.json):

{
  "dialogues": [
    {
      "id": "case_001",
      "department": "neurology",
      "patient_complaint": "我最近经常头痛，伴有恶心",
      "dialogue": [
        {
          "role": "patient",
          "content": "医生，我头痛已经一周了"
        },
        {
          "role": "doctor",
          "content": "请问头痛的部位在哪里？"
        }
      ]
    }
  ]
}
""")

# =============================================================================
# 阶段 2: 数据转换 (UniClinicalDataEngine)
# =============================================================================

print("\n【阶段 2】数据转换")
print("-" * 80)

print("""
文件位置: UniClinicalDataEngine/ 或 src/tau2/data_model/

步骤 2.1: 读取原始数据
-----------------------------------
from UniClinicalDataEngine import run_etl

# 运行 ETL 转换
results = run_etl(
    input_path="medical_dialogues.json",
    input_format="json",
    output_dir="./output/stage1",
    validate_input=True,
    anonymize_phi=False,
    auto_detect_tools=True
)

输出文件:
- output/stage1/tasks.json      # 标准任务格式
- output/stage1/db.json         # 工具数据库
- output/stage1/tools.json      # 工具定义
- output/stage1/policy.md       # 任务策略
""")

print("""
步骤 2.2: 转换为标准 Task 格式
-----------------------------------
from tau2.data_model.tasks import Task

# 转换后的 Task 对象结构:
task = Task(
    id="neurology_case_001",
    user_scenario={
        "persona": "患者",
        "instructions": "我最近经常头痛，伴有恶心...",
        "context": {...}
    },
    description={
        "overview": "神经科头痛诊断",
        "steps": ["问诊", "检查", "诊断"]
    },
    evaluation_criteria={
        "actions": [...],
        "nl_assertions": [...]
    }
)
""")

# =============================================================================
# 阶段 3: 数据质量验证
# =============================================================================

print("\n【阶段 3】数据质量验证")
print("-" * 80)

print("""
文件位置: DataQualityFiltering/data_quality/

步骤 3.1: 医学对话验证
-----------------------------------
from DataQualityFiltering.data_quality import MedicalDialogueValidator

validator = MedicalDialogueValidator()

# 验证数据
is_valid, errors = validator.validate(task)

print(f"验证结果: {'通过' if is_valid else '失败'}")
if errors:
    for error in errors:
        print(f"  - {error}")

# 计算医学分数
medical_score = validator.calculate_medical_score(task)
print(f"医学相关性分数: {medical_score:.2f}/5.0")
""")

print("""
步骤 3.2: 质量过滤
-----------------------------------
from DataQualityFiltering.data_quality import QualityFilter, FilterConfig

config = FilterConfig(
    min_quality_score=3.5,
    min_tool_count=1,
    max_tool_count=8,
    min_content_length=50
)

filter_engine = QualityFilter(config)

# 计算质量分数
score = filter_engine.calculate_quality_score(task)
print(f"质量分数: {score:.2f}/5.0")

if score >= 3.5:
    print("✅ 数据质量达标，进入下一阶段")
else:
    print("❌ 数据质量不达标，被过滤")
""")

# =============================================================================
# 阶段 4: 任务注册
# =============================================================================

print("\n【阶段 4】任务注册")
print("-" * 80)

print("""
文件位置: src/tau2/registry.py

步骤 4.1: 注册任务到系统
-----------------------------------
from tau2.registry import registry

# 定义任务加载函数
def clinical_neurology_get_tasks():
    """加载神经科任务"""
    with open("output/stage1/tasks.json", "r") as f:
        tasks = json.load(f)
    return tasks

# 注册到系统
registry.register_tasks(
    clinical_neurology_get_tasks,
    "clinical_neurology"
)

# 步骤 4.2: 加载任务
tasks = registry.get_tasks_loader("clinical_neurology")()
print(f"已加载 {len(tasks)} 个神经科任务")
""")

# =============================================================================
# 阶段 5: Agent 运行
# =============================================================================

print("\n【阶段 5】Agent 运行")
print("-" * 80)

print("""
文件位置: src/tau2/run.py, src/tau2/orchestrator/

步骤 5.1: 初始化组件
-----------------------------------
from tau2.run import run_task
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.environment.interface_agent import InterfaceAgent

# 创建 Agent
agent = LLMAgent(
    model="gpt-4",
    api_key="your_api_key"
)

# 创建用户模拟器
user = UserSimulator(
    model="gpt-4",
    task=task
)

# 创建环境
environment = InterfaceAgent(task)
""")

print("""
步骤 5.2: 运行模拟对话
-----------------------------------
from tau2.orchestrator.orchestrator import Orchestrator

orchestrator = Orchestrator(
    agent=agent,
    user=user,
    environment=environment,
    max_steps=100
)

# 执行模拟
simulation = orchestrator.run()

# 模拟过程:
# Round 1:
#   Agent: "您好，请问有什么可以帮您的？"
#   User:  "我最近经常头痛..."
#   Environment: 记录对话，更新状态
#
# Round 2:
#   Agent: "请问头痛的部位在哪里？"
#   User:  "主要在右侧太阳穴..."
#   Environment: 检查工具调用
#
# ... 继续对话直到完成或达到最大步数
""")

# =============================================================================
# 阶段 6: 评估
# =============================================================================

print("\n【阶段 6】评估")
print("-" * 80)

print("""
文件位置: src/tau2/evaluator/

步骤 6.1: 评估模拟结果
-----------------------------------
from tau2.evaluator.evaluator import evaluate_simulation

# 评估结果
evaluation = evaluate_simulation(
    simulation=simulation,
    task=task
)

# 评估维度:
# 1. 行为正确性 (actions)
#    - 是否调用了正确的工具
#    - 工具参数是否正确
#
# 2. 自然语言断言 (nl_assertions)
#    - 是否提供了正确的建议
#    - 是否询问了关键信息
#
# 3. 对话质量
#    - 是否有同理心
#    - 是否保持了专业性

# 评估结果示例:
{
    "success": True,
    "score": 0.85,
    "action_score": 0.9,
    "nl_assertion_score": 0.8,
    "details": {
        "correct_actions": 8,
        "total_actions": 10,
        "passed_assertions": 4,
        "total_assertions": 5
    }
}
""")

# =============================================================================
# 阶段 7: 结果保存
# =============================================================================

print("\n【阶段 7】结果保存")
print("-" * 80)

print("""
文件位置: simulations/ 目录

步骤 7.1: 保存模拟结果
-----------------------------------
import json

# 保存完整模拟记录
output_path = f"simulations/{task.id}_{agent.model}.json"

with open(output_path, "w") as f:
    json.dump({
        "task_id": task.id,
        "domain": "clinical_neurology",
        "agent": agent.model,
        "user": user.model,
        "timestamp": datetime.now().isoformat(),
        "simulation": simulation.dict(),
        "evaluation": evaluation
    }, f, indent=2)

print(f"结果已保存到: {output_path}")
""")

# =============================================================================
# 完整流程总结
# =============================================================================

print("\n" + "=" * 80)
print("完整流程总结")
print("=" * 80)

print("""
命令行一键运行:
-----------------------------------
# 运行单个任务
python run_clinical_benchmark.py \\
    --domain clinical_neurology \\
    --max-tasks 1 \\
    --agent-model gpt-4 \\
    --user-model gpt-4

# 运行所有任务
python run_clinical_benchmark.py \\
    --all \\
    --max-tasks 10 \\
    --agent-model gpt-4

数据流转图:
-----------------------------------
原始数据 (JSON/CSV)
    ↓
[UniClinicalDataEngine] 数据转换
    ↓
[DataQualityFiltering] 质量过滤
    ↓
[Registry] 任务注册
    ↓
[Agent + User + Environment] 模拟运行
    ↓
[Evaluator] 结果评估
    ↓
[JSON] 结果保存

关键文件映射:
-----------------------------------
1. 数据入口:
   - run_clinical_benchmark.py (主入口)
   - run_evaluation.py (简化入口)

2. 数据处理:
   - UniClinicalDataEngine/ (数据转换)
   - DataQualityFiltering/ (质量过滤)
   - configs/pipeline_config.json (配置)

3. 运行系统:
   - src/tau2/run.py (运行引擎)
   - src/tau2/orchestrator/ (协调器)
   - src/tau2/registry.py (注册表)

4. 核心组件:
   - src/tau2/agent/ (Agent实现)
   - src/tau2/user/ (用户模拟)
   - src/tau2/environment/ (环境)
   - src/tau2/evaluator/ (评估器)

5. 数据模型:
   - src/tau2/data_model/tasks.py (任务模型)
   - src/tau2/data_model/simulation.py (模拟结果)
   - src/tau2/data_model/message.py (消息模型)
""")

print("=" * 80)
