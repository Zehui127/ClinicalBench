# Agentmy 代码流程验证报告

## 验证目标

检查代码库是否符合以下数据流程：

```
原始医疗对话数据
    ↓
【DataValidator】 ← 第1层：原生数据质量验证
    ↓
经过验证的原始数据
    ↓
【Task生成】 ← 转换成统一的 task 格式
    ↓
生成的评测任务（tasks.json）
    ↓
【DataQualityFiltering】 ← 第2层：生成任务的质量过滤
    ↓
高质量评测任务
    ↓
【Agent运行】 ← AI医生回答问题
    ↓
Agent的对话记录（simulation）
    ↓
【tau2/evaluator/】 ← 第3层：Agent表现评估
    ↓
最终评分
```

## 验证结果：✅ 基本符合，但有断层

---

## 第1层：DataValidator（原生数据质量验证）

### ✅ 组件存在

**位置**: `DataValidator/`

**功能**:
- 医疗对话数据集验证器
- 模块化架构，支持多轮对话验证

**验证模块**:
```python
DataValidator/
├── validators/
│   ├── structure_validator.py      # 结构验证
│   ├── medical_content_validator.py # 医疗内容验证
│   └── multi_turn_validator.py      # 多轮对话验证
├── keywords.py                      # 987个医疗术语
└── core.py                          # 主验证器
```

**使用示例**:
```bash
python -m DataValidator data/tau2/domains/clinical/tasks.json --strict
```

### ⚠️ 问题

1. **未被集成到主管道**
   - `scripts/run_pipeline.py` 中没有调用 DataValidator
   - `configs/pipeline_config.json` 中没有配置 DataValidator

2. **与原始数据脱节**
   - 没有看到从原始数据（如 MedDialog、MedQA）到验证器的自动化流程
   - 转换脚本（`convert_*.py`）没有调用 DataValidator

---

## 第2层：Task生成（转换成统一格式）

### ✅ 组件存在

**位置**: `UniClinicalDataEngine/`

**功能**:
- 完整的 ETL（Extract → Transform → Load）管道
- 将异构临床数据转换为 tau2-bench 格式

**流程**:
```python
UniClinicalDataEngine/
├── adapters/          # 数据格式适配器
│   ├── nhands_adapter.py
│   ├── csv_adapter.py
│   └── json_adapter.py
├── task_builder.py    # 任务构建器
├── db_builder.py      # 知识库构建器
├── tool_generator.py  # 工具生成器
└── policy_generator.py # 策略文档生成器
```

**输出文件**:
- `tasks.json` - tau2 任务定义
- `db.json` - 临床知识库
- `tools.json` - 工具定义
- `policy.md` - 使用策略

**使用方式**:
```bash
# 从 ETL 运行
python -m UniClinicalDataEngine --input medxpertqa.json --output outputs/

# 或通过主管道
python scripts/run_pipeline.py --input data/raw/medxpertqa.json
```

### ✅ 状态：正常

---

## 第3层：DataQualityFiltering（质量过滤）

### ✅ 组件存在

**位置**: `DataQualityFiltering/`

**功能**:
- 质量过滤和评分
- 基于 tool_count 和 content_length 的质量计算

**核心组件**:
```python
DataQualityFiltering/
├── data_quality/
│   ├── validators/
│   │   └── medical_dialogue_validator.py
│   ├── filter_engine.py    # 质量过滤器
│   ├── pipelines/          # 过滤管道
│   └── reviewers/          # 人工审查支持
```

**配置** (`configs/pipeline_config.json`):
```json
"stage2": {
  "name": "DataQualityFiltering",
  "config": {
    "min_quality_score": 3.5,
    "min_tool_count": 1,
    "max_tool_count": 8,
    "min_content_length": 50
  }
}
```

**使用方式**:
```bash
python -m DataQualityFiltering data-quality filter \
  --input outputs/stage1_output/tasks.json \
  --output outputs/stage2_output/
```

### ⚠️ 问题

1. **功能分离不清**
   - DataQualityFiltering 原本包含 agent_evaluation
   - agent_evaluation 已迁移到 tau2.evaluator
   - 但 data_quality 部分仍独立存在

2. **集成不完整**
   - `scripts/run_pipeline.py` 调用了 DataQualityFiltering
   - 但没有明确的文档说明何时/如何使用

---

## 第4层：Agent运行（AI医生回答）

### ✅ 组件存在

**位置**: `src/tau2/`

**核心文件**:
```python
src/tau2/
├── run.py                    # 主运行脚本
├── agent/
│   └── llm_agent.py         # LLM Agent 实现
├── orchestrator/
│   └── orchestrator.py      # 编排器
├── user/
│   └── user_simulator.py    # 用户模拟器（患者）
└── environment/
    └── environment.py       # 环境（医疗工具、数据库）
```

**运行方式**:
```bash
# 使用 CLI
python -m tau2.cli run \
  --agent llm_agent \
  --domain clinical_cardiology \
  --model gpt-4

# 或使用脚本
python run_clinical_benchmark.py \
  --domains clinical_cardiology \
  --agent llm_agent \
  --model gpt-4
```

**流程**:
1. 加载任务（tasks.json）
2. 初始化 Agent（医生）
3. 初始化 User Simulator（患者）
4. 运行对话循环
5. 保存 SimulationRun（对话记录）

### ✅ 状态：正常

---

## 第5层：tau2/evaluator/（Agent表现评估）

### ✅ 组件存在且刚完成集成

**位置**: `src/tau2/evaluator/`

**评估器**:
```python
src/tau2/evaluator/
├── evaluator_base.py              # 基类
├── evaluator.py                   # 评估调度器
│
├── [原有评估器]
│   ├── evaluator_action.py        # 动作检查
│   ├── evaluator_communicate.py   # 通信检查
│   ├── evaluator_env.py           # 环境断言
│   └── evaluator_nl_assertions.py # 自然语言断言
│
└── [新增医疗评估器] ✨ 最新集成
    ├── evaluator_clinical.py           # 综合医疗评估
    ├── evaluator_clinical_accuracy.py  # 临床准确性 (40%)
    ├── evaluator_dialogue_fluency.py   # 对话流畅性 (30%)
    └── evaluator_safety_empathy.py     # 安全性与同理心 (30%)
```

**数据模型**:
```python
# 新增
from tau2.data_model.tasks import RewardType
RewardType.CLINICAL  # ✅ 已添加

from tau2.data_model.simulation import ClinicalCheck
# ✅ 已添加，包含 overall_score, dimension_scores, strengths, weaknesses
```

**评估类型**:
```python
from tau2.evaluator.evaluator import EvaluationType

# 纯医疗评估
EvaluationType.CLINICAL

# 综合评估（包含医疗）
EvaluationType.ALL_WITH_CLINICAL
```

**使用方式**:
```python
from tau2.evaluator import ClinicalEvaluator

reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=simulation.messages,
    model="gpt-4"
)

# 返回 RewardInfo，包含：
# - reward: float (0-1)
# - clinical_checks: List[ClinicalCheck]
# - dimension_scores: dict (三个维度的详细分数)
```

### ✅ 状态：刚完成集成（2026-03-16）

---

## 主管道集成

### ✅ scripts/run_pipeline.py

**功能**: 运行完整的2阶段管道

```python
#!/usr/bin/env python3
# Master Pipeline Script

Stage 1: UniClinicalDataEngine (ETL)
Stage 2: DataQualityFiltering (Quality Filter)
```

**使用方式**:
```bash
python scripts/run_pipeline.py \
  --input data/raw/medxpertqa.json \
  --output outputs/ \
  --min-quality-score 3.5
```

### ⚠️ 缺失环节

1. **没有调用 DataValidator**
   - 管道直接从原始数据开始
   - 跳过了"原生数据质量验证"层

2. **没有集成 Agent 运行**
   - 管道只生成高质量任务
   - 没有自动运行 Agent 评估

---

## 流程对比

### 你的流程图 vs 实际代码

| 你的流程图 | 实际代码 | 状态 |
|-----------|---------|------|
| 原始数据 → DataValidator | ❌ 未集成 | ⚠️ 缺失 |
| DataValidator → 验证数据 | ❌ 不存在 | ⚠️ 缺失 |
| 验证数据 → Task生成 | ✅ UniClinicalDataEngine | ✅ 正常 |
| tasks.json → DataQualityFiltering | ✅ DataQualityFiltering | ✅ 正常 |
| 高质量任务 → Agent运行 | ✅ tau2 run.py | ✅ 正常 |
| simulation → tau2/evaluator/ | ✅ tau2/evaluator/ | ✅ 刚完成 |

---

## 问题总结

### 1. 架构不完整 ⭐⭐⭐

**问题**: DataValidator 被跳过

**影响**:
- 原始数据质量无法保证
- 转换前的数据验证缺失
- 可能生成低质量的任务

**建议**:
```python
# 在 scripts/run_pipeline.py 中添加
from DataValidator import DataValidator

# Stage 0: 原生数据验证
validator = DataValidator(input_data)
is_valid, errors = validator.validate()
if not is_valid:
    logger.error(f"Data validation failed: {errors}")
    return

# Stage 1: ETL
# ...
```

### 2. 流程不连贯 ⭐⭐⭐

**问题**: 三个独立系统，缺少统一编排

**影响**:
- 用户需要手动运行多个脚本
- 容易出错
- 难以复现

**建议**: 创建统一的 Master Pipeline

```python
# scripts/master_pipeline.py
class MasterPipeline:
    def run(self):
        # Stage 0: DataValidator
        validated_data = self.validate_raw_data()

        # Stage 1: UniClinicalDataEngine
        tasks = self.generate_tasks(validated_data)

        # Stage 2: DataQualityFiltering
        filtered_tasks = self.filter_tasks(tasks)

        # Stage 3: Agent Evaluation
        results = self.run_agents(filtered_tasks)

        # Stage 4: tau2/evaluator/
        scores = self.evaluate_results(results)

        return scores
```

### 3. 文档不清晰 ⭐⭐

**问题**:
- DataValidator 的用途不清楚
- 各系统之间的关系模糊
- 没有端到端的使用指南

**建议**: 创建 `END_TO_END_GUIDE.md`

### 4. 功能重叠 ⭐

**问题**:
- `DataQualityFiltering` 和 `DataValidator` 功能重叠
- 都在做数据验证

**建议**: 明确分工
- **DataValidator**: 原始数据验证（转换前）
- **DataQualityFiltering**: 生成任务的质量过滤（转换后）

---

## 优先修复建议

### 短期（1-2天）

1. **集成 DataValidator 到主管道**
   ```bash
   # 修改 scripts/run_pipeline.py
   # 添加 Stage 0: 数据验证
   ```

2. **创建端到端测试**
   ```python
   # test_e2e_pipeline.py
   # 从原始数据到最终评分的完整测试
   ```

3. **更新 README**
   ```markdown
   ## 完整流程
   1. 原始数据 → DataValidator → 验证
   2. 验证数据 → UniClinicalDataEngine → tasks.json
   3. tasks.json → DataQualityFiltering → 高质量任务
   4. 高质量任务 → tau2 run.py → Agent 对话
   5. 对话记录 → tau2/evaluator/ → 最终评分
   ```

### 中期（1周）

1. **创建 Master Pipeline 脚本**
   - 一键运行从原始数据到最终评分
   - 自动化中间步骤

2. **添加数据流监控**
   - 每个阶段的统计信息
   - 质量指标追踪

### 长期（持续）

1. **优化组件接口**
   - 统一数据格式
   - 标准化配置

2. **性能优化**
   - 并行处理
   - 缓存机制

---

## 结论

### ✅ 符合程度：70%

**符合的部分**:
- ✅ Task 生成（UniClinicalDataEngine）
- ✅ 质量过滤（DataQualityFiltering）
- ✅ Agent 运行（tau2 run.py）
- ✅ Agent 评估（tau2/evaluator/，刚完成集成）

**不符合的部分**:
- ❌ DataValidator 未集成到主管道
- ❌ 缺少统一的 Master Pipeline
- ❌ 文档不够清晰

### 核心建议

**最需要做的事**：

1. **集成 DataValidator** ⭐⭐⭐
   - 在 `scripts/run_pipeline.py` 中添加验证步骤
   - 确保原始数据质量

2. **创建 Master Pipeline** ⭐⭐⭐
   - 一键运行完整流程
   - 提高可用性

3. **端到端测试** ⭐⭐
   - 验证整个流程
   - 确保各组件协作正常

4. **更新文档** ⭐
   - 清晰说明流程
   - 提供使用示例

---

**生成时间**: 2026-03-16
**验证者**: Claude Sonnet 4.5
