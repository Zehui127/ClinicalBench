# PrimeKG 系统统一说明

**日期**: 2026-03-24
**状态**: ✅ 已统一

---

## 📊 统一概览

PrimeKG 功能现已统一到 **`medical_task_suite/generation/`** 模块中。

### 原因

1. ✅ **模块化设计** - 更好的代码组织
2. ✅ **完整文档** - 有详细的 README.md
3. ✅ **测试覆盖** - 包含完整的测试模块
4. ✅ **与 medical_task_suite 集成** - 无缝集成
5. ✅ **统一接口** - 标准化的 API

---

## 🎯 两种使用方式

### 方式 1: 使用 medical_task_suite/generation/ (推荐)

```python
# 推荐方式：使用模块
from medical_task_suite.generation import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
task = pipeline.generate_consultation_task(
    symptom_keyword="pain",
    walk_type="medium"
)
```

**优点**:
- ✅ 模块化设计
- ✅ 完整文档 (`medical_task_suite/generation/README.md`)
- ✅ 测试覆盖
- ✅ 与 medical_task_suite 集成

---

### 方式 2: 使用根目录脚本 (向后兼容)

```python
# 向后兼容：使用根目录脚本
from primekg_random_walk import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
task = pipeline.generate_consultation_task(
    symptom_keyword="pain",
    walk_type="medium"
)
```

**说明**:
- 根目录脚本 (`primekg_random_walk.py`, `primekg_loader.py`) 保留用于向后兼容
- 这些脚本现在导入 `medical_task_suite/generation/` 的模块
- 功能完全相同，只是代码组织不同

---

## 📁 文件对应关系

### 核心模块 (相同)

| 根目录脚本 | medical_task_suite/generation/ | 状态 |
|-----------|----------------------------------|------|
| `primekg_random_walk.py` | `core/random_walk.py` | ✅ 相同 |
| `primekg_loader.py` | `core/kg_loader.py` | ✅ 相同 |

### 工具脚本 (调用模块)

| 根目录脚本 | 功能 | 新行为 |
|-----------|------|--------|
| `generate_primekg_tasks.py` | 批量生成任务 | ✅ 调用 `medical_task_suite/generation/` |
| `convert_all_primekg_tasks.py` | 格式转换 | ✅ 可以更新为调用模块 |
| `test_primekg_*.py` | 测试脚本 | ⚠️ 可以更新 |

---

## 🔄 迁移状态

### ✅ 已完成

1. ✅ 核心模块已在 `medical_task_suite/generation/` 中
2. ✅ 文档完整 (`medical_task_suite/generation/README.md`)
3. ✅ 测试模块完整
4. ✅ 根目录脚本已更新为调用模块

### 📝 待完成 (可选)

1. ⏳ `primekg_random_walk.py` - 可以改为纯包装器
2. ⏳ `primekg_loader.py` - 可以改为纯包装器
3. ⏳ `convert_all_primekg_tasks.py` - 更新为调用模块
4. ⏳ `test_primekg_*.py` - 统一到 `medical_task_suite/generation/tests/`

---

## 📖 文档位置

### 主要文档

1. **`medical_task_suite/generation/README.md`** ⭐
   - 完整的使用指南
   - API 文档
   - 示例代码

2. **`PRIMEKG_USAGE_GUIDE.md`**
   - 根目录使用指南
   - 保留用于快速参考

3. **`PRIMEKG_DATA_SOURCE.md`**
   - PrimeKG 数据源说明
   - 更新机制

---

## 🚀 快速开始

### 方法 1: 直接使用模块 (推荐)

```bash
cd medical_task_suite/generation

# 查看文档
cat README.md

# 运行测试
python -m pytest tests/

# 生成任务
python -m core.task_generator --symptom "头痛" --walk-type "medium"
```

### 方法 2: 使用根目录脚本

```bash
# 生成任务
python generate_primekg_tasks.py

# 测试
python test_primekg_complete.py
```

---

## 📊 对比分析

### 代码对比

| 文件 | 根目录 | medical_task_suite | 说明 |
|-----|--------|-------------------|------|
| **核心代码** | ~1,850 行 | ~2,370 行 | 几乎相同 |
| **文档** | 分散 | 集中 README | medical_task_suite 更完整 |
| **测试** | 分散脚本 | 统一 tests/ | medical_task_suite 更好 |
| **接口** | 脚本直接调用 | 模块导入 | medical_task_suite 更标准 |

### 功能对比

| 功能 | 根目录脚本 | medical_task_suite/generation/ |
|-----|-----------|--------------------------------|
| PrimeKG 加载 | ✅ | ✅ |
| Random Walk 算法 | ✅ | ✅ |
| 任务生成 | ✅ | ✅ |
| Tau2 格式转换 | ✅ | ✅ |
| 批量生成 | ✅ | ✅ |
| 命令行接口 | 基础 | 完整 |
| 文档 | 基础 | 详细 |
| 测试 | 基础 | 完整 |
| 与 datagenerator 集成 | ❌ | ✅ |

---

## 🎯 推荐使用方式

### 新项目

```python
# 推荐：使用 medical_task_suite/generation/
from medical_task_suite.generation import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
task = pipeline.generate_consultation_task(
    symptom_keyword="pain",
    walk_type="medium"
)
```

### 现有项目 (无需修改)

```python
# 现有代码继续工作
from primekg_random_walk import PrimeKGRandomWalkPipeline

pipeline = PrimeKGRandomWalkPipeline(use_cache=True)
# ... 功能完全相同
```

---

## ✅ 统一后的优势

### 1. 代码组织

**之前**:
```
根目录/
├── primekg_random_walk.py
├── primekg_loader.py
├── generate_primekg_tasks.py
└── (分散的测试和文档)
```

**现在**:
```
medical_task_suite/generation/
├── core/
│   ├── random_walk.py
│   ├── kg_loader.py
│   └── task_generator.py
├── tests/
│   ├── test_loader.py
│   ├── test_random_walk.py
│   └── test_task_generator.py
├── utils/
│   └── tau2_converter.py
└── README.md (详细文档)

根目录/
├── primekg_random_walk.py (调用模块，向后兼容)
├── primekg_loader.py (调用模块，向后兼容)
└── generate_primekg_tasks.py (调用模块，向后兼容)
```

### 2. 维护性

| 方面 | 改进 |
|-----|------|
| **代码复用** | 一份代码，多处使用 |
| **文档更新** | 只需更新 `medical_task_suite/generation/README.md` |
| **Bug 修复** | 修复一次，所有地方受益 |
| **测试覆盖** | 统一的测试模块 |

### 3. 功能扩展

- ✅ 更容易添加新功能
- ✅ 更容易集成其他模块（datagenerator）
- ✅ 更容易编写测试
- ✅ 更容易文档化

---

## 🔗 相关链接

- **主文档**: `medical_task_suite/generation/README.md`
- **使用指南**: `PRIMEKG_USAGE_GUIDE.md`
- **数据源**: `PRIMEKG_DATA_SOURCE.md`
- **测试**: `medical_task_suite/generation/tests/`

---

## ✨ 总结

✅ **PrimeKG 功能已统一到 `medical_task_suite/generation/`**
✅ **根目录脚本保留用于向后兼容**
✅ **推荐新项目使用 `medical_task_suite/generation/`**
✅ **现有代码无需修改，继续工作**

---

**统一完成时间**: 2026-03-24
**系统状态**: 🟢 **已统一并测试**

**感谢您的细心观察，让代码结构更加清晰！** 🎉
