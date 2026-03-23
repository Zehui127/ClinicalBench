# KGGenerator - 医学知识图谱任务生成器
# Medical Knowledge Graph Task Generator

## 📖 简介

KGGenerator是一个基于医学知识图谱的对话任务生成系统，能够从PrimeKG（哈佛医学院医学知识图谱）自动生成真实、多样、高质量的医学对话任务。

## ✨ 核心特性

- **知识驱动**: 基于哈佛医学院PrimeKG真实医学知识
- **自动生成**: Random Walk算法自动生成任务路径
- **多样性**: 支持short/medium/long三种路径长度
- **真实性**: 生成的任务基于真实的医学关系
- **可扩展**: 理论上可生成无限数量的任务
- **Tau2兼容**: 直接生成tau2-bench兼容格式

## 🎯 与datagenerator的配合

```
数据生成流程:
┌─────────────────┐
│  PrimeKG知识图谱  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  kg_generator   │ ← 生成新任务
│  (新任务生成)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  datagenerator  │ ← 优化任务质量
│  (质量优化)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  最终数据集       │
│  (高质量+大规模)  │
└─────────────────┘
```

## 📦 模块结构

```
kg_generator/
├── README.md                          # 本文档
├── __init__.py                        # 包初始化
├── core/                              # 核心模块
│   ├── __init__.py
│   ├── kg_loader.py                   # 知识图谱加载器
│   ├── random_walk.py                 # Random Walk算法
│   └── task_generator.py              # 任务生成器
├── utils/                             # 工具模块
│   ├── __init__.py
│   └── tau2_converter.py             # Tau2格式转换器
└── tests/                             # 测试模块
    ├── __init__.py
    ├── test_loader.py                 # 加载器测试
    ├── test_random_walk.py            # Random Walk测试
    └── test_task_generator.py         # 生成器测试
```

## 🚀 快速开始

### 基本使用

#### 1. 生成单个任务
```python
from kg_generator.core.task_generator import KGTaskGenerator

# 初始化生成器
generator = KGTaskGenerator(use_cache=True)

# 生成任务
task = generator.generate(
    symptom_keyword="头痛",
    walk_type="medium"  # short, medium, long
)

# 保存为tau2格式
generator.export_to_tau2(task, "output/task.json")
```

#### 2. 批量生成任务
```python
# 生成多个任务
symptoms = ["头痛", "胸痛", "发热", "咳嗽"]

for i, symptom in enumerate(symptoms):
    task = generator.generate(
        symptom_keyword=symptom,
        walk_type="short"
    )
    generator.export_to_tau2(
        task,
        f"output/primekg_task_{i}.json"
    )
```

#### 3. 命令行使用
```bash
# 生成任务
python -m kg_generator.core.task_generator \
  --symptom "头痛" \
  --walk-type "medium" \
  --output "output/task.json"

# 批量生成
python -m kg_generator.core.task_generator \
  --batch \
  --symptoms "头痛,胸痛,发热" \
  --output-dir "output/"
```

## 📊 PrimeKG数据源

### 数据规模
- **节点**: 20,000+ 医学实体
  - 疾病 (diseases)
  - 药物 (drugs)
  - 症状 (symptoms/phenotypes)
  - 基因 (genes)
  - 通路 (pathways)

- **边**: 300,000+ 医学关系
  - 药物治疗疾病
  - 疾病引起症状
  - 药物副作用
  - 基因关联疾病

### 数据来源
- **PrimeKG**: Harvard Medical School
- **更新**: 定期更新
- **许可**: 开放使用

## 🎨 核心算法

### Random Walk算法

```python
# 从症状节点开始随机游走
def random_walk(kg, start_node, length):
    path = [start_node]

    for step in range(length):
        current = path[-1]
        neighbors = kg.get_neighbors(current)

        # 智能选择下一个节点
        next_node = select_next_node(neighbors, strategy="medical_relevance")
        path.append(next_node)

    return path
```

### 路径长度策略
- **short** (3-5节点): 简单咨询 → 轻微症状
- **medium** (6-10节点): 常规问诊 → 中等复杂度
- **long** (11-15节点): 复杂病例 → 多重并发症

## 🔧 配置选项

### 缓存配置
```python
generator = KGTaskGenerator(
    use_cache=True,              # 使用本地缓存
    cache_dir="data/primekg_cache",
    force_reload=False            # 强制重新加载
)
```

### 生成配置
```python
task = generator.generate(
    symptom_keyword="头痛",
    walk_type="medium",
    max_attempts=10,             # 最大尝试次数
    require_path_diversity=True,  # 路径多样性
    include_reference_dialogue=True  # 包含参考对话
)
```

## 📈 输出格式

### Tau2兼容格式
```json
{
  "id": "primekg_task_123",
  "description": {
    "purpose": "Medical consultation - 头痛",
    "notes": "Generated from PrimeKG knowledge graph"
  },
  "user_scenario": {
    "persona": "45-year-old female with 头痛",
    "instructions": {
      "domain": "primekg",
      "reason_for_call": "头痛",
      "known_info": "患者头痛3天，严重程度中等"
    }
  },
  "ticket": "头痛",
  "metadata": {
    "source": "PrimeKG Knowledge Graph",
    "primekg_path_length": 7,
    "primekg_node_types": ["phenotype", "disease", "drug"],
    "primekg_edge_types": ["associated_with", "treats"]
  }
}
```

## 🧪 测试

```bash
# 运行所有测试
python -m pytest kg_generator/tests/

# 测试知识图谱加载
python -m pytest kg_generator/tests/test_loader.py

# 测试Random Walk
python -m pytest kg_generator/tests/test_random_walk.py

# 测试任务生成
python -m pytest kg_generator/tests/test_task_generator.py
```

## 📚 示例代码

查看 `examples/` 目录获取完整示例：
- `basic_generation.py` - 基础生成示例
- `batch_generation.py` - 批量生成示例
- `custom_walk.py` - 自定义路径示例
- `integrate_with_datagenerator.py` - 与datagenerator集成示例

## 🤝 与datagenerator集成

### 完整工作流
```python
# Step 1: 使用kg_generator生成新任务
from kg_generator.core.task_generator import KGTaskGenerator

kg_gen = KGTaskGenerator()
new_tasks = []

for symptom in ["头痛", "胸痛", "发热"]:
    task = kg_gen.generate(symptom, walk_type="medium")
    new_tasks.append(task)

# Step 2: 使用datagenerator优化
from datagenerator.core.task_optimizer import TaskOptimizer

optimizer = TaskOptimizer()
optimized_tasks = optimizer.optimize(
    tasks=new_tasks,
    enable_scenario_balancing=True,
    enable_evaluation_enhancement=True,
    enable_metadata_enrichment=True
)

# Step 3: 保存最终结果
import json
with open('final_dataset.json', 'w') as f:
    json.dump(optimized_tasks, f, ensure_ascii=False, indent=2)
```

## 📋 文件清单

### 核心文件
- `core/kg_loader.py` - 知识图谱加载器 (29KB)
- `core/random_walk.py` - Random Walk算法 (26KB)
- `core/task_generator.py` - 任务生成器 (整合模块)

### 工具文件
- `utils/tau2_converter.py` - Tau2格式转换器

### 测试文件
- `tests/test_loader.py` - 加载器测试
- `tests/test_random_walk.py` - Random Walk测试
- `tests/test_task_generator.py` - 生成器测试

## ⚠️ 注意事项

### 性能考虑
- 首次加载需要下载和缓存数据（~1GB）
- 建议使用缓存加速后续生成
- Random Walk计算较复杂，生成速度较慢

### 质量控制
- 生成的任务质量可能不稳定
- 建议与datagenerator配合使用
- 需要人工审核部分任务

### 数据依赖
- 需要稳定的网络连接（首次使用）
- PrimeKG数据可能更新
- 缓存需要定期清理

## 🚀 性能优化

### 使用缓存
```python
# 首次生成会创建缓存
generator = KGTaskGenerator(use_cache=True)

# 后续生成使用缓存，速度快10倍+
```

### 批量生成
```python
# 批量生成比单个生成效率高
tasks = generator.batch_generate(
    symptom_keywords=["头痛", "胸痛", "发热"],
    walk_type="medium"
)
```

## 📄 许可证

MIT License

## 👥 作者

tau2-bench 项目团队

## 🙏 致谢

- Harvard Medical School - PrimeKG数据
- tau2-bench社区 - 框架支持
- datagenerator模块 - 优化工具

## 🔗 相关链接

- PrimeKG: https://primekg.harvard.edu
- tau2-bench: https://github.com/anthropics/tau2-bench
- datagenerator: ./datagenerator/

---

*版本: 1.0.0*
*最后更新: 2025-03-23*
*PrimeKG版本: 2024-09*
