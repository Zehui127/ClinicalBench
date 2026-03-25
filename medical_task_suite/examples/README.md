# Medical Task Suite - 使用示例

本目录包含Medical Task Suite的完整使用示例，从基础到高级，帮助您快速上手。

---

## 📚 示例目录

### [示例 1: 基础使用 - 单模块任务](example_01_basic_single_module.py)

**适合**: 新手上手，了解基本流程

**内容**:
- 如何创建单个医疗模块
- 如何生成任务要求和评估标准
- 如何评估Agent的响应
- Red Line Detection和Confidence Scoring基础

**运行时间**: < 1分钟

```bash
python example_01_basic_single_module.py
```

---

### [示例 2: 进阶使用 - 多模块集成](example_02_multi_modules.py)

**适合**: 需要测试多个能力的场景

**内容**:
- 如何使用ModuleIntegrator集成多个模块
- 如何根据场景智能选择合适的模块
- 如何生成和整合多模块的评估标准
- 多模块任务的Agent响应评估

**运行时间**: 1-2分钟

```bash
python example_02_multi_modules.py
```

---

### [示例 3: 完整工作流 - 从生成到分析](example_03_complete_workflow.py)

**适合**: 生产环境使用，批量评估

**内容**:
- 批量任务生成流程
- 模拟Agent响应
- 批量评估和分数计算
- ModuleCoverageAnalyzer覆盖度分析
- 结果统计和可视化

**运行时间**: 2-3分钟

```bash
python example_03_complete_workflow.py
```

---

### [示例 4: 医疗场景实战](example_04_clinical_scenarios.py)

**适合**: 医疗场景应用，最接近实际使用

**场景**:
1. **胸痛待查** - 鉴别诊断能力
2. **高血压管理** - 用药指导和长期管理
3. **发热待查** - 检验检查分析能力
4. **Temporal Consistency** - 时序一致性验证

**运行时间**: 2-3分钟

```bash
python example_04_clinical_scenarios.py
```

---

### [示例 5: 高级功能使用](example_05_advanced_features.py)

**适合**: 深度测试和高级应用

**高级功能**:
1. **Temporal Consistency Verification** - 检测前后矛盾
2. **Execution Chain Annotation** - 标注决策过程
3. **Adversarial Test Suite** - 对抗测试
4. **Cross-Session Memory** - 跨会话记忆

**运行时间**: 3-5分钟

```bash
python example_05_advanced_features.py
```

---

## 🚀 快速开始

### 第一次使用？

建议按顺序学习：

```bash
# Step 1: 学习基础
python example_01_basic_single_module.py

# Step 2: 学习多模块
python example_02_multi_modules.py

# Step 3: 学习完整流程
python example_03_complete_workflow.py

# Step 4: 学习医疗场景
python example_04_clinical_scenarios.py

# Step 5: 学习高级功能
python example_05_advanced_features.py
```

### 有经验的用户？

直接查看相关场景：

- **需要快速集成**: 跳到 `example_02_multi_modules.py`
- **需要批量评估**: 跳到 `example_03_complete_workflow.py`
- **医疗场景应用**: 跳到 `example_04_clinical_scenarios.py`
- **高级功能**: 跳到 `example_05_advanced_features.py`

---

## 📋 学习路径

### 基础路径 (15分钟)

```
example_01 → example_02
```

**学完后您将**:
- ✅ 理解Medical Task Suite的基本架构
- ✅ 能够生成单/多模块任务
- ✅ 能够评估Agent响应

### 完整路径 (45分钟)

```
example_01 → example_02 → example_03 → example_04
```

**学完后您将**:
- ✅ 掌握完整的任务生成和评估流程
- ✅ 能够处理真实医疗场景
- ✅ 能够进行覆盖度分析
- ✅ 可以在生产环境使用

### 专家路径 (60分钟)

```
example_01 → example_02 → example_03 → example_04 → example_05
```

**学完后您将**:
- ✅ 掌握所有核心和高级功能
- ✅ 能够进行深度测试
- ✅ 能够进行对抗测试
- ✅ 能够实现跨会话记忆
- ✅ 成为Medical Task Suite专家

---

## 💡 常见使用场景

### 场景 1: 评估单个Agent

```python
# 参考 example_01 或 example_02
from modules import create_lab_test_inquiry_module
from evaluation import ConfidenceScorer

module = create_lab_test_inquiry_module()
# ... 评估逻辑
```

### 场景 2: 批量评估多个Agent

```python
# 参考 example_03
from optimization.core.module_integrator import ModuleIntegrator

integrator = ModuleIntegrator()
# ... 批量生成和评估
```

### 场景 3: 真实医疗应用

```python
# 参考 example_04
# 根据具体科室选择合适的模块组合
```

### 场景 4: 安全测试

```python
# 参考 example_05 的 Adversarial Test Suite
from advanced_features import AdversarialTestSuite

suite = AdversarialTestSuite()
# ... 对抗测试
```

### 场景 5: 质量监控

```python
# 参考 example_03 的覆盖度分析
from evaluation import ModuleCoverageAnalyzer

analyzer = ModuleCoverageAnalyzer()
# ... 覆盖度分析
```

---

## 🛠️ 依赖要求

所有示例需要以下依赖：

```python
# Medical Task Suite核心模块
from modules import *
from optimization.core.module_integrator import ModuleIntegrator
from evaluation import RedLineDetector, ConfidenceScorer, ModuleCoverageAnalyzer
from advanced_features import *
```

确保您已正确安装Medical Task Suite。

---

## 📖 相关文档

- **主文档**: `../README.md`
- **架构文档**: `../ARCHITECTURE.md`
- **验证报告**:
  - `../FINAL_VALIDATION_REPORT.md` - 基础验证 (94%通过)
  - `../DEEP_VALIDATION_REPORT.md` - 深度验证 (75%通过)

---

## 💬 反馈和帮助

如果您在使用示例时遇到问题：

1. 检查是否在正确的目录 (`medical_task_suite/`)
2. 确保所有依赖已安装
3. 查看相关文档了解详细说明
4. 运行 `quick_test.py` 验证系统状态

---

**祝您使用愉快！** 🎉
