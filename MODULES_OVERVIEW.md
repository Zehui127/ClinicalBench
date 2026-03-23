# 医学对话数据集生成与优化系统
# Medical Dialogue Dataset Generation and Optimization System

## 📖 系统概述

本系统提供了一套完整的医学对话数据集解决方案，包含两个核心模块和一个集成脚本，能够实现从知识图谱生成到质量优化的完整流程。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    医学对话数据集系统                         │
│              Medical Dialogue Dataset System                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌─────────────────┐                   ┌─────────────────┐
│  kg_generator   │                   │ datagenerator   │
│  知识图谱生成     │                   │  数据集优化      │
└────────┬────────┘                   └────────┬────────┘
         │                                     │
         │    新任务                           │
         ├────────────────────────────────────►│
         │                                     │ 优化后任务
         │                                     │
         │                               ┌─────┴─────┐
         │                               │           │
         ▼                               ▼           ▼
   ┌─────────┐                      ┌──────────┐ ┌──────────┐
   │PrimeKG  │                      │tasks_real│ │tasks_    │
   │知识图谱  │                      │istic_v3  │ │optimized │
   └─────────┘                      └──────────┘ └──────────┘
```

## 📦 核心模块

### 1. kg_generator/ - 知识图谱任务生成器

**定位**: 新任务生成工具

**功能**:
- 基于PrimeKG医学知识图谱生成新任务
- Random Walk算法保证任务多样性
- 支持short/medium/long三种路径长度
- 自动生成tau2-bench兼容格式

**输入**:
- PrimeKG知识图谱（哈佛医学院）
- 症状关键词列表

**输出**:
- 新生成的医学对话任务
- 包含完整的患者档案和对话示例

**使用场景**:
- ✅ 扩充数据集规模
- ✅ 生成全新任务
- ✅ 覆盖更多疾病和症状
- ✅ 知识图谱研究

**快速开始**:
```python
from kg_generator import KGTaskGenerator

gen = KGTaskGenerator(use_cache=True)
task = gen.generate("头痛", walk_type="medium")
gen.export_to_tau2(task, "output/task.json")
```

---

### 2. datagenerator/ - 数据集优化器

**定位**: 数据集质量优化工具

**功能**:
- 场景分布均衡
- 评估标准增强（添加权重）
- 元数据构建（转换追溯）
- 质量评分（6个维度）

**输入**:
- 现有任务数据集

**输出**:
- 优化后的任务数据集
- 加权评估100%覆盖
- 完整元数据100%覆盖

**使用场景**:
- ✅ 提升现有数据集质量
- ✅ 数据集标准化
- ✅ 添加加权评估
- ✅ 质量评分和分析

**快速开始**:
```python
from datagenerator import TaskOptimizer

optimizer = TaskOptimizer()
optimized = optimizer.optimize(
    input_file='tasks_realistic_v3.json',
    output_file='tasks_optimized.json'
)
```

---

### 3. integrated_generation.py - 集成生成脚本

**定位**: 组合使用两个模块

**功能**:
- 自动化端到端流程
- 生成 → 优化 → 输出
- 一键获得高质量数据集

**优势**:
- 结合两者优点
- 最大化数据质量
- 最小化人工干预

**快速开始**:
```bash
python integrated_generation.py
```

---

## 🎯 使用指南

### 场景1: 从零生成高质量数据集

```bash
# Step 1: 使用知识图谱生成新任务
python -c "
from kg_generator import KGTaskGenerator
gen = KGTaskGenerator()
tasks = [gen.generate(s) for s in ['头痛', '胸痛', '发热']]
"

# Step 2: 使用datagenerator优化
python -c "
from datagenerator import TaskOptimizer
optimizer = TaskOptimizer()
optimizer.optimize(
    input_file='generated_tasks.json',
    output_file='final_tasks.json'
)
"
```

### 场景2: 优化现有数据集

```bash
# 直接使用datagenerator
python optimize_dataset.py
```

### 场景3: 扩充数据集规模

```bash
# 使用集成脚本
python integrated_generation.py
```

---

## 📊 效果对比

### kg_generator单独使用
```
输出: 新任务（未优化）
- 数量: 理论上无限
- 质量: 6-8分（不稳定）
- 加权评估: ❌
- 元数据: ❌
```

### datagenerator单独使用
```
输出: 优化后的现有任务
- 数量: 受限于输入
- 质量: 8.64分（显著提升）
- 加权评估: ✅ 100%
- 元数据: ✅ 100%
```

### 集成使用（kg_generator + datagenerator）
```
输出: 新生成且优化的任务
- 数量: 可扩展
- 质量: 8.5+分（稳定高质量）
- 加权评估: ✅ 100%
- 元数据: ✅ 100%
- 知识驱动: ✅
```

---

## 📈 推荐工作流

### 最佳实践流程

```
1. 需求分析
   ├─ 需要新任务? → 是 → 使用kg_generator
   └─ 有现有数据? → 是 → 使用datagenerator

2. 任务生成
   └─ kg_generator.generate(symptoms)

3. 质量优化
   └─ datagenerator.optimize(tasks)

4. 验证和评估
   └─ 查看质量报告和统计信息

5. 部署使用
   └─ 集成到tau2-bench环境
```

---

## 🗂️ 文件结构

```
tau2-bench/
├── kg_generator/                   # 知识图谱生成模块
│   ├── README.md                   # 模块文档
│   ├── core/                       # 核心组件
│   │   ├── kg_loader.py           # 知识图谱加载
│   │   ├── random_walk.py         # Random Walk算法
│   │   └── task_generator.py      # 任务生成器
│   ├── utils/                      # 工具模块
│   │   └── tau2_converter.py     # Tau2格式转换
│   └── tests/                      # 测试模块
│
├── datagenerator/                  # 数据集优化模块
│   ├── README.md                   # 模块文档
│   ├── core/                       # 核心组件
│   │   ├── task_optimizer.py      # 主优化器
│   │   ├── scenario_balancer.py   # 场景均衡器
│   │   ├── evaluation_enhancer.py # 评估增强器
│   │   ├── metadata_builder.py    # 元数据构建器
│   │   └── quality_scorer.py      # 质量评分器
│   ├── config/                     # 配置文件
│   │   └── optimization_rules.yaml
│   └── models/                     # 数据模型
│
├── integrated_generation.py        # 集成生成脚本
├── optimize_dataset.py             # 数据集优化脚本
│
└── data/                           # 数据目录
    ├── primekg_cache/             # PrimeKG缓存
    ├── primekg_tasks/             # 生成的任务
    └── tau2/domains/clinical/     # Tau2数据集
        ├── chinese_internal_medicine/
        └── primekg/
```

---

## 🎓 学习资源

### 文档
- `kg_generator/README.md` - kg_generator详细文档
- `datagenerator/README.md` - datagenerator详细文档
- `DATAGENERATOR_VS_PRIMEKG_COMPARISON.md` - 模块对比分析
- `OPTIMIZATION_COMPLETE_REPORT.md` - 优化完成报告

### 示例代码
- `integrated_generation.py` - 集成使用示例
- `optimize_dataset.py` - datagenerator使用示例
- 各模块的examples/目录

### 测试
- `kg_generator/tests/` - kg_generator测试
- datagenerator包含完整测试套件

---

## 🚀 快速开始

### 安装依赖
```bash
pip install pyyaml networkx
```

### 1. 生成新任务
```python
from kg_generator import KGTaskGenerator

gen = KGTaskGenerator()
task = gen.generate("头痛")
```

### 2. 优化数据集
```python
from datagenerator import TaskOptimizer

optimizer = TaskOptimizer()
optimized = optimizer.optimize(
    input_file='tasks.json',
    output_file='tasks_optimized.json'
)
```

### 3. 集成使用
```bash
python integrated_generation.py
```

---

## 📊 数据集对比

| 数据集 | 来源 | 大小 | 质量评分 | 说明 |
|--------|------|------|----------|------|
| tasks_realistic_v3.json | MedDialog | 4.5MB | 8.13 | 高质量内容 |
| tasks_advanced.json | 转换生成 | 2.7MB | 7.5 | 良好结构 |
| **tasks_optimized.json** | **优化生成** | **4.8MB** | **8.64** | **综合最优** ⭐ |
| primekg_tasks/ | PrimeKG | 数百个 | 6-8 | 知识驱动 |

---

## ✅ 优势总结

### kg_generator优势
- ✅ 知识驱动（哈佛医学院数据）
- ✅ 自动生成（无限扩展）
- ✅ 多样性好（Random Walk）
- ✅ 覆盖面广（各种疾病）

### datagenerator优势
- ✅ 质量提升（+6.3%）
- ✅ 功能完整（5个核心模块）
- ✅ 易于使用（一行代码）
- ✅ 生产就绪（完整测试）

### 集成使用优势
- ✅ 最佳质量（8.5+分）
- ✅ 可扩展（无限任务）
- ✅ 高效（自动化流程）
- ✅ 灵活（可定制）

---

## 🎯 选择建议

### 选择 kg_generator 如果：
- 需要生成全新任务
- 需要扩充数据规模
- 需要覆盖更多疾病

### 选择 datagenerator 如果：
- 有现有数据集需要优化
- 需要提升数据质量
- 需要统一评估标准

### 集成使用如果：
- 需要最佳质量
- 需要大规模数据
- 需要端到端流程

---

## 📞 技术支持

### 问题反馈
- GitHub Issues: https://github.com/circadiancity/agentmy/issues

### 文档
- 查看各模块的README.md
- 查看示例代码
- 查看测试用例

---

## 🙏 致谢

- Harvard Medical School - PrimeKG知识图谱
- tau2-bench社区 - 评估框架
- Chinese MedDialog - 中文医疗对话数据

---

*系统版本: 2.0*
*最后更新: 2025-03-23*
*维护团队: tau2-bench*
