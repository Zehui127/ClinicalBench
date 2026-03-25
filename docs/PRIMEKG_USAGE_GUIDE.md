# PrimeKG Random Walk 使用指南

## 📖 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [数据准备](#数据准备)
4. [生成任务](#生成任务)
5. [集成到 tau2-bench](#集成到-tau2-bench)
6. [升级改造方案](#升级改造方案)
7. [常见问题](#常见问题)

---

## 快速开始

### 方案 1: 直接使用（推荐 - 5分钟）

如果你的本地已经有 PrimeKG 缓存数据，可以直接使用：

```python
from primekg_random_walk import PrimeKGRandomWalkPipeline

# 1. 初始化（使用缓存，约20秒加载）
pipeline = PrimeKGRandomWalkPipeline(
    use_cache=True,
    focus_types=["disease", "drug", "effect/phenotype"]
)

# 2. 搜索可用症状
symptoms = pipeline.real_kg.search_nodes("pain", limit=5)
print("可用症状:")
for s in symptoms:
    print(f"  - {s['name']}")

# 3. 生成任务
task = pipeline.generate_consultation_task(
    symptom_keyword=symptoms[0]['name'],
    walk_type="medium"
)

# 4. 查看对话
print(f"\n患者主诉: {task.patient_profile['chief_complaint']}")
print(f"诊断: {task.patient_profile.get('underlying_condition', 'Unknown')}")
print(f"\n对话内容:")
for turn in task.dialogue_turns:
    print(f"[{turn['role'].capitalize()}] {turn['content']}")

# 5. 导出（可选）
pipeline.export_to_tau2(task, "output/my_task.json")
```

### 方案 2: 从头开始（首次使用 - 30-40分钟）

如果是第一次使用或没有缓存数据：

```python
from primekg_random_walk import PrimeKGRandomWalkPipeline

# 1. 初始化（会自动下载 PrimeKG 数据）
pipeline = PrimeKGRandomWalkPipeline(
    use_cache=True,  # 首次后会缓存
    focus_types=["disease", "drug", "effect/phenotype"]
)

# 下载进度：
# - 下载 PrimeKG CSV: ~10-20 分钟（936 MB）
# - 解析 CSV: ~5-10 分钟
# - 过滤子图: ~2-5 分钟
# - 构建图: ~1-2 分钟
# 总计: ~20-40 分钟

# 2. 后续使用都会使用缓存（~20秒）
```

---

## 系统架构

```
用户输入症状
    ↓
[PrimeKGRandomWalkPipeline]
    ↓
[1. 加载 PrimeKG] → RealMedicalKnowledgeGraph (23,087 节点, 617,118 边)
    ↓
[2. 搜索症状节点] → 通过关键词搜索 effect/phenotype 节点
    ↓
[3. Random Walk] → 生成路径: symptom → disease → drug
    ↓
[4. Task Generator] → 转换为对话（5-6 轮）
    ↓
[5. 导出] → JSON 格式（tau2 或自定义）
```

---

## 数据准备

### 检查本地数据

```bash
# 检查 PrimeKG 数据是否存在
ls -lh data/primekg_cache/

# 应该看到以下文件：
# - primekg_kg.csv (936 MB) - 原始数据
# - primekg_filtered_nodes.json (2.5 MB)
# - primekg_filtered_edges.json (70 MB)
# - primekg_filtered_graph.gml (55 MB)
```

### 数据状态

| 文件 | 大小 | 说明 | 必需 |
|------|------|------|------|
| primekg_kg.csv | 936 MB | PrimeKG 原始数据 | ⚠️ 首次需要 |
| primekg_filtered_nodes.json | 2.5 MB | 过滤后的节点 | ✅ 是 |
| primekg_filtered_edges.json | 70 MB | 过滤后的边 | ✅ 是 |
| primekg_filtered_graph.gml | 55 MB | NetworkX 图 | ✅ 是 |

**如果缺少文件**：
- 系统会自动下载 primekg_kg.csv
- 其他文件会自动生成

---

## 生成任务

### 单个任务生成

```python
from primekg_random_walk import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

# 方式1: 使用症状关键词
task = pipeline.generate_consultation_task(
    symptom_keyword="hypertension",
    walk_type="medium"  # short/medium/long
)

# 方式2: 使用症状ID（高级用法）
symptoms = pipeline.real_kg.search_nodes("fever", limit=1)
task = pipeline.generate_consultation_task(
    symptom_keyword=symptoms[0]['name'],
    walk_type="long"
)
```

### 批量生成任务

```python
# 生成多个任务
symptom_keywords = ["pain", "fever", "nausea", "hypertension"]

tasks = []
for keyword in symptom_keywords:
    try:
        for walk_type in ["short", "medium"]:
            task = pipeline.generate_consultation_task(
                symptom_keyword=keyword,
                walk_type=walk_type
            )
            tasks.append(task)
            print(f"✓ Generated: {keyword} ({walk_type})")
    except Exception as e:
        print(f"✗ Failed: {keyword} - {e}")

print(f"\nTotal tasks: {len(tasks)}")
```

### 自定义生成

```python
from primekg_random_walk import (
    PrimeKGRandomWalkGenerator,
    PrimeKGTaskGenerator
)
from primekg_loader import PrimeKGLoader, RealMedicalKnowledgeGraph

# 1. 加载 PrimeKG
loader = PrimeKGLoader()
real_kg = RealMedicalKnowledgeGraph(loader)
real_kg.load_from_primekg(use_cache=True)

# 2. 搜索起始症状
results = real_kg.search_nodes("diabetes", limit=1)
if results:
    symptom_id = results[0]['id']

    # 3. 生成多条路径
    walk_gen = PrimeKGRandomWalkGenerator(real_kg)
    paths = walk_gen.generate_multiple_walks(
        symptom_id,
        num_walks=10,
        walk_type="medium"
    )

    # 4. 为每条路径生成任务
    task_gen = PrimeKGTaskGenerator(real_kg)
    tasks = []

    for i, path in enumerate(paths):
        task = task_gen.generate_task(
            path,
            task_id=f"diabetes_task_{i}"
        )
        tasks.append(task)

    print(f"Generated {len(tasks)} tasks from diabetes symptom")
```

---

## 集成到 tau2-bench

### 方式 1: 转换为 tau2 格式

创建一个转换脚本 `primekg_to_tau2.py`：

```python
#!/usr/bin/env python3
"""
将 PrimeKG 生成的任务转换为 tau2 格式
"""

import json
from pathlib import Path
from primekg_random_walk import PrimeKGRandomWalkPipeline

def convert_to_tau2_format(primekg_task, domain="primekg"):
    """将 PrimeKG 任务转换为 tau2 格式"""

    # 提取对话
    dialogue_turns = []
    for turn in primekg_task.dialogue_turns:
        if turn['role'] == 'patient':
            dialogue_turns.append({
                "role": "user",
                "content": turn['content']
            })
        else:  # doctor
            dialogue_turns.append({
                "role": "assistant",
                "content": turn['content']
            })

    # 构建 tau2 格式任务
    tau2_task = {
        "id": primekg_task.task_id,
        "description": {
            "purpose": f"Medical consultation - {primekg_task.patient_profile['chief_complaint']}",
            "relevant_policies": None,
            "notes": f"Generated from PrimeKG knowledge graph. Path: {' → '.join(primekg_task.metadata.get('node_types', []))}"
        },
        "user_scenario": {
            "persona": f"{primekg_task.patient_profile['age']}-year-old {primekg_task.patient_profile['gender']} patient with {primekg_task.patient_profile['chief_complaint']}",
            "instructions": {
                "domain": domain,
                "reason_for_call": primekg_task.patient_profile['chief_complaint'],
                "known_info": primekg_task.patient_profile.get('underlying_condition', 'Unknown condition'),
                "unknown_info": None,
                "task_instructions": f"You are a patient seeking medical advice.\n\nYour concern: {primekg_task.patient_profile['chief_complaint']}\n\nDuration: {primekg_task.patient_profile['duration_days']} days\nSeverity: {primekg_task.patient_profile['severity']}\n\nPlease engage in a natural conversation with the doctor."
            }
        },
        "ticket": primekg_task.patient_profile['chief_complaint'],
        "initial_state": {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": "PrimeKG Patient",
                        "mrn": primekg_task.task_id,
                        "age": primekg_task.patient_profile['age'],
                        "gender": primekg_task.patient_profile['gender']
                    }
                }
            ]
        },
        "evaluation_criteria": {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {
                        "should_address": primekg_task.patient_profile['chief_complaint']
                    }
                }
            ],
            "communication_checks": [
                {
                    "check_id": "helpful_response",
                    "criteria": "Response should address patient's concern"
                }
            ]
        },
        "reference_dialogue": dialogue_turns,
        "metadata": {
            "source": "PrimeKG Random Walk",
            "path_length": primekg_task.metadata.get('path_length', 0),
            "node_types": primekg_task.metadata.get('node_types', []),
            "edge_types": primekg_task.metadata.get('edge_types', [])
        }
    }

    return tau2_task


def batch_convert(primekg_tasks_dir, output_dir, domain="primekg"):
    """批量转换 PrimeKG 任务为 tau2 格式"""

    input_path = Path(primekg_tasks_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 读取所有 PrimeKG 任务
    primekg_files = list(input_path.glob("primekg_*.json"))

    tau2_tasks = []

    for primekg_file in primekg_files:
        with open(primekg_file, 'r', encoding='utf-8') as f:
            primekg_data = json.load(f)

        # 提取任务信息
        from primekg_random_walk import ConsultationTask, WalkPath
        from dataclasses import dataclass, field

        # 重建 ConsultationTask 对象
        path = WalkPath(
            nodes=primekg_data['path']['nodes'],
            edges=primekg_data['path']['edges']
        )

        task = ConsultationTask(
            task_id=primekg_data['task_id'],
            path=path,
            patient_profile=primekg_data['patient_profile'],
            dialogue_turns=primekg_data['dialogue'],
            metadata=primekg_data['metadata']
        )

        # 转换
        tau2_task = convert_to_tau2_format(task, domain)
        tau2_tasks.append(tau2_task)

    # 保存为 tau2 格式
    output_file = output_path / "tasks.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tau2_tasks, f, ensure_ascii=False, indent=2)

    print(f"✓ Converted {len(tau2_tasks)} tasks")
    print(f"✓ Saved to: {output_file}")

    # 生成 split_tasks.json
    import random
    random.shuffle(tau2_tasks)

    split_point = int(len(tau2_tasks) * 0.8)
    train_tasks = tau2_tasks[:split_point]
    test_tasks = tau2_tasks[split_point:]

    split_data = {
        "train": [t['id'] for t in train_tasks],
        "test": [t['id'] for t in test_tasks]
    }

    split_file = output_path / "split_tasks.json"
    with open(split_file, 'w', encoding='utf-8') as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Split: {len(train_tasks)} train, {len(test_tasks)} test")

    # 生成 db.json
    db_data = {
        "domain": domain,
        "description": f"Medical consultation tasks generated from PrimeKG knowledge graph",
        "source": "Harvard Medical School PrimeKG",
        "total_tasks": len(tau2_tasks),
        "metadata": {
            "primekg_nodes": 23087,
            "primekg_edges": 617118,
            "generated_date": "2025-03-22"
        }
    }

    db_file = output_path / "db.json"
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Database info saved")

    return tau2_tasks


if __name__ == "__main__":
    # 转换示例任务
    batch_convert(
        primekg_tasks_dir="data/primekg_tasks",
        output_dir="data/tau2/domains/clinical/primekg",
        domain="primekg_internal_medicine"
    )
```

运行转换：

```bash
python primekg_to_tau2.py
```

### 方式 2: 直接生成 tau2 格式

修改 `primekg_random_walk.py` 中的 `export_to_tau2` 方法：

```python
def export_to_tau2_format(self, task, output_file):
    """直接导出为 tau2 格式"""

    tau2_task = convert_to_tau2_format(task)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tau2_task, f, ensure_ascii=False, indent=2)

    print(f"[Export] Task saved to: {output_file}")
```

---

## 升级改造方案

### 方案 A: 快速集成（1-2小时）

**目标**: 将 PrimeKG 任务添加到现有的 clinical domain

```bash
# 1. 生成 PrimeKG 任务
python test_primekg_random_walk.py

# 2. 转换为 tau2 格式
python primekg_to_tau2.py

# 3. 将生成的任务添加到现有系统
# 任务会保存在 data/tau2/domains/clinical/primekg/
```

**优点**:
- 不需要修改现有代码
- 可以直接使用现有的评估框架
- 快速见效

**缺点**:
- PrimeKG 任务是英文的
- 与现有中文任务风格不一致

### 方案 B: 中文适配（4-6小时）

**目标**: 将 PrimeKG 知识图谱用于生成中文医疗任务

#### 步骤 1: 创建中文翻译层

```python
# primekg_chinese_adapter.py

class PrimeKGChineseAdapter:
    """PrimeKG 中文适配器"""

    def __init__(self, primekg_pipeline):
        self.pipeline = primekg_pipeline

        # 医学术语翻译
        self.translations = {
            "pain": "疼痛",
            "fever": "发热",
            "nausea": "恶心",
            "hypertension": "高血压",
            "diabetes": "糖尿病",
            # ... 更多翻译
        }

        # 对话模板
        self.dialogue_templates = {
            "patient_complaint": "医生，我{duration}了{days}天。",
            "doctor_inquiry": "请问您的{symptom}是怎么样的？",
            # ... 更多模板
        }

    def translate_symptom(self, english_name):
        """翻译症状名称"""
        return self.translations.get(english_name.lower(), english_name)

    def generate_chinese_dialogue(self, primekg_task):
        """生成中文对话"""
        chinese_turns = []

        for turn in primekg_task.dialogue_turns:
            if turn['role'] == 'patient':
                # 翻译患者对话
                chinese_content = self._translate_patient_turn(turn)
                chinese_turns.append({
                    "role": "user",
                    "content": chinese_content
                })
            else:
                # 翻译医生对话
                chinese_content = self._translate_doctor_turn(turn)
                chinese_turns.append({
                    "role": "assistant",
                    "content": chinese_content
                })

        return chinese_turns
```

#### 步骤 2: 生成中文任务

```python
from primekg_chinese_adapter import PrimeKGChineseAdapter

# 初始化
pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
chinese_adapter = PrimeKGChineseAdapter(pipeline)

# 生成任务
task = pipeline.generate_consultation_task("pain")

# 转换为中文
chinese_dialogue = chinese_adapter.generate_chinese_dialogue(task)

# 保存
# ...
```

### 方案 C: 混合方案（推荐）

**目标**: 结合 PrimeKG 知识和现有中文任务

```python
# hybrid_task_generator.py

class HybridTaskGenerator:
    """混合任务生成器"""

    def __init__(self):
        # 加载 PrimeKG
        self.primekg_pipeline = PrimeKGRandomWalkPipeline(use_cache=True)

        # 加载现有的中文任务模板
        self.chinese_templates = self._load_chinese_templates()

    def generate_enhanced_task(self, chinese_task_id):
        """为现有中文任务添加 PrimeKG 知识"""

        # 1. 读取现有中文任务
        chinese_task = self._load_chinese_task(chinese_task_id)

        # 2. 提取关键词
        keywords = self._extract_medical_keywords(chinese_task)

        # 3. 在 PrimeKG 中搜索相关知识
        primekg_knowledge = []
        for keyword in keywords:
            results = self.primekg_pipeline.real_kg.search_nodes(
                keyword,
                limit=3
            )
            primekg_knowledge.extend(results)

        # 4. 用 PrimeKG 知识增强任务
        enhanced_task = self._enhance_task_with_knowledge(
            chinese_task,
            primekg_knowledge
        )

        return enhanced_task
```

---

## 常见问题

### Q1: PrimeKG 数据太大，能否使用更小的版本？

**A**: 可以调整过滤参数：

```python
# 使用更严格的过滤
pipeline = PrimeKGRandomWalkPipeline(
    focus_types=["disease", "drug"],  # 只保留疾病和药物
    use_cache=True
)

# 这会减少到约 15,000 节点和 400,000 边
```

### Q2: 如何自定义 Random Walk 路径？

**A**: 修改 `PrimeKGRandomWalkGenerator.generate_walk()` 方法：

```python
def generate_walk(self, start_symptom_id, walk_type="medium"):
    # 添加自定义路径模式
    if state == "disease":
        # 添加实验室检查
        lab_neighbors = self.adapter.get_neighbors_by_type(
            current_node,
            target_types=["biological_process"],
            edge_types=["target"]
        )
        # ...
```

### Q3: 生成的对话太简单，如何改进？

**A**: 使用 LLM 增强对话：

```python
from openai import OpenAI

client = OpenAI()

def enhance_dialogue_with_llm(primekg_task):
    """使用 LLM 增强对话"""

    for turn in primekg_task.dialogue_turns:
        if turn['role'] == 'doctor':
            # 使用 LLM 重新生成更自然的医生回复
            prompt = f"""
根据以下信息生成医生的回复：

患者信息: {primekg_task.patient_profile}
诊断: {primekg_task.metadata.get('diagnosis')}
治疗: {primekg_task.metadata.get('treatment')}

原始回复: {turn['content']}

请生成更详细、更自然的医生回复：
"""

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )

            turn['content'] = response.choices[0].message.content

    return primekg_task
```

### Q4: 如何评估生成任务的质量？

**A**: 使用现有评估框架：

```python
from evaluation import evaluate_task

# 评估 PrimeKG 任务
task = pipeline.generate_consultation_task("hypertension")

# 使用 tau2 评估框架
results = evaluate_task(
    task=task,
    metrics=["medical_accuracy", "dialogue_quality", "completeness"]
)

print(f"Medical Accuracy: {results['medical_accuracy']}")
print(f"Dialogue Quality: {results['dialogue_quality']}")
```

---

## 📚 相关文档

- `PRIMEKG_LOADER_README.md` - PrimeKG 加载器详细说明
- `PRIMEKG_RANDOM_WALK_INTEGRATION.md` - 完整集成报告
- `primekg_random_walk.py` - 核心代码（带注释）
- `test_primekg_random_walk.py` - 测试示例

---

**最后更新**: 2025-03-22
**作者**: Claude Sonnet 4.5
