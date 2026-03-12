# 临床数据质量改进方案

## 📊 问题诊断结果

### 当前数据状态分析

| 指标 | 结果 | 占比 | 评价 |
|------|------|------|------|
| **总任务数** | 758 | 100% | - |
| **数据来源** | MCQ 转换 | 100% | 单一来源 |
| **使用占位符** | 107 | 14% | ❌ 需改进 |
| **临床信息丰富** (>50字符) | 188 | 25% | ⚠️ 偏低 |
| **临床信息贫乏** (<50字符) | 570 | 75% | ❌ 严重问题 |

### 问题根源分析

```
┌─────────────────────────────────────────────────────────────┐
│                    问题根源诊断                              │
└─────────────────────────────────────────────────────────────┘

数据源: MedXpertQA (MCQ 格式)
    ↓
Adapter: MCQToDialogueConverter
    ↓
问题:
  1. MCQ 本身信息有限（只有题目 + 选项 + 答案）
  2. 缺乏患者背景、病史、体征等临床细节
  3. 转换器只是简单模板填充，没有信息丰富化
  4. 评估标准千篇一律，没有区分场景
```

### 具体问题示例

**❌ 当前任务（信息贫乏）:**
```json
{
  "ticket": "I have chest discomfort and I'm worried it might be a heart problem.",
  "known_info": "Symptoms: fever, rash",
  "task_instructions": "Patient: I have chest discomfort... Since {timeframe}."
}
```

**✅ 理想任务（信息丰富）:**
```json
{
  "ticket": "I've been having chest pain for the past 3 days and it's getting worse.",
  "known_info": "52-year-old male, history of hypertension, smoker (30 pack-years), presents with substernal chest pain radiating to left arm, associated with diaphoresis and nausea. Pain started 3 days ago, initially exertional, now occurring at rest. BP 165/95, HR 102, RR 18. No prior cardiac workup.",
  "task_instructions": "Detailed clinical scenario with realistic dialogue flow..."
}
```

---

## 🎯 改进方案

### 方案 A: 优化 Adapter（推荐用于短期改进）

**目标**: 在现有数据基础上，通过增强 MCQToDialogueConverter 来提升质量

**实现步骤**:

#### 1. 创建 ClinicalDataEnricher 模块

```python
# UniClinicalDataEngine/generators/clinical_enricher.py

class ClinicalDataEnricher:
    """使用 LLM 丰富临床数据的详细信息"""

    def enrich_scenario(self, mcq_data: dict) -> dict:
        """
        从简短的 MCQ 生成丰富的临床场景

        输入: MCQ 题目
        输出: 包含详细临床信息的场景
        """
        # 1. 提取核心信息（诊断/症状）
        # 2. 使用 LLM 生成：
        #    - 详细病史
        #    - 体格检查发现
        #    - 生命体征
        #    - 鉴别诊断考虑
        #    - 危险分层
        pass
```

#### 2. 增强 TemplateManager

添加更复杂的对话模板：

```python
# 不同场景类型的模板
DIALOGUE_TEMPLATES = {
    "acute_coronary_syndrome": {
        "symptom_progression": "...",
        "risk_factors": "...",
        "red_flags": "..."
    },
    "heart_failure": {
        "symptom_progression": "...",
        "functional_status": "...",
        "exacerbation_triggers": "..."
    },
    # ... 更多场景
}
```

#### 3. 改进评估标准生成器

```python
class SmartCriteriaGenerator:
    """根据场景类型生成定制化的评估标准"""

    def generate_criteria(self, scenario_type: str) -> dict:
        # 急性胸痛：重点评估危险分层、心电图解读、肌钙蛋白时机的选择
        # 慢性心衰：重点评估 NYHA 分级、药物优化、患者教育
        # 心律失常：重点评估 ECG 解读、抗凝指征、急诊处理
        pass
```

**优点**:
- ✅ 可以快速应用到现有 758 个任务
- ✅ 不需要寻找新的数据源
- ✅ 可控的质量提升

**缺点**:
- ⚠️ 仍受限于 MCQ 的原始信息
- ⚠️ LLM 生成可能产生幻觉

---

### 方案 B: 引入新数据源（推荐用于长期改进）

**目标**: 引入更高质量的原始数据

**候选数据源**:

| 数据源 | 格式 | 质量 | 覆盖范围 | 获取难度 |
|--------|------|------|----------|----------|
| **MedQA** | 病例问答 | ⭐⭐⭐⭐ | 全科 | ⭐ |
| **PubMedQA** | 文献问答 | ⭐⭐⭐⭐⭐ | 专科 | ⭐⭐ |
| **NHands** | 结构化病例 | ⭐⭐⭐⭐⭐ | 全科 | ⭐⭐⭐ |
| **ClinicalCases** | 病例库 | ⭐⭐⭐ | 心脏科 | ⭐⭐ |

**实现步骤**:

#### 1. 创建 RichCaseAdapter

```python
# UniClinicalDataEngine/adapters/rich_case_adapter.py

class RichCaseAdapter(BaseAdapter):
    """处理富含临床信息的病例数据"""

    def load_raw_data(self):
        # 加载病例库数据
        pass

    def normalize_record(self, raw_case):
        # 转换为标准格式，保留所有临床细节
        return {
            "patient_profile": {
                "age": ...,
                "gender": ...,
                "demographics": ...,
                "social_history": ...,
            },
            "chief_complaint": ...,
            "history_of_present_illness": ...,  # 详细现病史
            "past_medical_history": ...,
            "medications": ...,
            "allergies": ...,
            "physical_exam": ...,  # 详细体格检查
            "vital_signs": ...,
            "lab_results": ...,
            "imaging": ...,
        }
```

#### 2. 使用 TaskMerger 合并相关任务

**已有的模块** (task_processor.py):

```python
from UniClinicalDataEngine.task_processor import TaskMerger, ScenarioProcessor

# 配置合并策略
processor = ScenarioProcessor(
    enable_deduplication=True,
    enable_merging=True,  # ← 这个功能已存在！
    merge_min_tasks=2,
    merge_max_tasks=5
)

# 使用示例
# 将同一患者的多个简单问题合并为一个复杂病例
merged_tasks = processor.process(tasks)
```

**合并效果示例**:

```
输入 3 个简单任务:
  1. "我有高血压，该怎么用药？"
  2. "我最近心跳很快，是什么原因？"
  3. "我脚有点肿，要紧吗？"

输出 1 个复杂任务:
  "68岁女性，高血压10年，近期出现心悸和下肢水肿。
   需要评估：药物依从性、心率快的原因（心律失常？心衰？）、
   水肿程度（心衰表现？）。需要完整的病史、体格检查、心电图、
   超声心动图评估。"
```

---

### 方案 C: 混合方案（推荐）

**结合方案 A 和 B 的优点**:

1. **短期（1-2周）**: 使用方案 A 改进现有 758 个任务
2. **中期（1个月）**: 引入新数据源，添加高质量病例
3. **长期（持续）**: 建立质量监控系统

---

## 🚀 实施计划

### 阶段 1: 快速改进（现有数据）

**目标**: 将 75% 的"信息贫乏"任务降低到 30%

**任务**:
1. ✅ 创建 ClinicalDataEnricher
2. ✅ 增强对话模板
3. ✅ 改进评估标准
4. ✅ 重新处理现有数据

**预期结果**:
- 临床信息丰富度: 25% → 60%
- 占位符使用: 14% → 0%
- 评估标准多样性: 1 种 → 5+ 种场景类型

### 阶段 2: 引入高质量数据

**目标**: 添加 200+ 个高质量复杂病例

**任务**:
1. 寻找并整合新数据源
2. 创建 RichCaseAdapter
3. 使用 TaskMerger 合并任务
4. 人工审核关键病例

**预期结果**:
- 总任务数: 758 → 958+
- 高质量病例: 0 → 200+
- 复杂病例比例: 5% → 30%

### 阶段 3: 质量监控

**目标**: 建立持续质量改进机制

**任务**:
1. 实现自动化质量评分
2. 定期审计任务质量
3. 收集评测反馈
4. 迭代改进数据

---

## 📋 关于 TaskMerger 的说明

**是的，TaskMerger 模块已经存在！**

位置: `UniClinicalDataEngine/task_processor.py`

**功能**:
- ✅ 去重 (TaskDeduplicator)
- ✅ 合并 (TaskMerger) - 将简单任务合并成复杂任务
- ✅ 分组（按患者、按科室）

**使用方法**:
```python
from UniClinicalDataEngine.task_processor import ScenarioProcessor

processor = ScenarioProcessor(
    enable_merging=True,
    merge_min_tasks=2,  # 最少2个任务才合并
    merge_max_tasks=5   # 最多5个任务合并成1个
)

processed_tasks = processor.process(original_tasks)
```

---

## 🎯 立即行动建议

### 第一步：评估数据源 vs Adapter

| 问题 | 数据源问题 | Adapter 问题 |
|------|-----------|-------------|
| MCQ 信息有限 | ✅ 主要问题 | - |
| 转换简单模板化 | - | ✅ 次要问题 |
| 缺乏临床细节 | ✅ 主要问题 | ⚠️ 可以改进 |
| 评估标准单一 | - | ✅ 主要问题 |

**结论**: 两者都有问题，但数据源是主要限制因素

### 第二步：改进优先级

1. **立即执行** (本周):
   - 改进评估标准生成（Adapter 层面）
   - 移除所有占位符
   - 增加对话模板多样性

2. **短期执行** (2周内):
   - 实现 ClinicalDataEnricher
   - 重新处理现有数据
   - 启用 TaskMerger

3. **中期执行** (1个月内):
   - 引入新的高质量数据源
   - 人工审核和标注
   - 建立质量基准

---

## 📊 改进效果预估

| 指标 | 当前 | 阶段1后 | 阶段2后 | 阶段3后 |
|------|------|---------|---------|---------|
| 临床信息丰富度 | 25% | 60% | 80% | 90% |
| 占位符使用 | 14% | 0% | 0% | 0% |
| 评估标准类型 | 1 | 5+ | 10+ | 15+ |
| 复杂病例比例 | 5% | 15% | 30% | 40% |
| 总任务数 | 758 | 758 | 958+ | 1000+ |

---

**创建日期**: 2026-03-11
**下一步**: 创建 ClinicalDataEnricher 模块
