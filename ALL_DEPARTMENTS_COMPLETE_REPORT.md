# 6个科室完整数据流程报告

## 执行日期
2025-03-19

---

## 总体成果

✅ **完成流程**：原始数据验证 → 数据转换 → 数据增强
✅ **总数据量**：3,000个医学咨询任务（6个科室 × 500任务）
✅ **质量保证**：严格验证模式 + 追问阈值规则

---

## 阶段1: 原始数据验证 ✅

### 验证标准（严格模式）
- 患者主诉 ≥ 20字符
- 医生回答 ≥ 30字符
- 对话轮数 ≥ 2轮
- 医学关键词 ≥ 2个

### 各科室验证结果

| 科室 | 总对话数 | 通过数 | 通过率 | 质量排名 |
|------|---------|--------|--------|----------|
| 肿瘤科 | 75,553 | 62,340 | **82.5%** | 🥇 1 |
| 男科 | 94,596 | 73,087 | **77.3%** | 🥈 2 |
| 外科 | 115,991 | 84,785 | **73.1%** | 🥉 3 |
| 内科 | 220,606 | 152,026 | 68.9% | 4 |
| 儿科 | 101,602 | 67,757 | 66.7% | 5 |
| 妇产科 | 183,751 | 120,775 | 65.7% | 6 |
| **总计** | **792,099** | **560,770** | **70.8%** | - |

**验证通过数据**: 56.1万条高质量对话

---

## 阶段2: 数据转换 ✅

### 转换结果
- **转换方法**: 从验证通过的对话中随机取样
- **取样策略**: 每个科室500个任务
- **输出格式**: Tau2-bench标准格式

### 各科室转换结果

| 科室 | 任务数 | 文件大小 | 输出文件 |
|------|--------|----------|----------|
| 内科 | 500 | 1.3M | `tasks_内科.json` |
| 外科 | 500 | 1.2M | `tasks_外科.json` |
| 妇产科 | 500 | 1.2M | `tasks_妇产科.json` |
| 儿科 | 500 | 1.3M | `tasks_儿科.json` |
| 肿瘤科 | 500 | 1.2M | `tasks_肿瘤科.json` |
| 男科 | 500 | 1.2M | `tasks_男科.json` |
| **总计** | **3,000** | **7.4M** | - |

**任务结构**:
```json
{
  "id": "clinical_<dept>_0",
  "ticket": "患者问题...",
  "user_scenario": {...},
  "initial_state": {...},
  "evaluation_criteria": {...}
}
```

---

## 阶段3: 数据增强 ✅

### 增强内容
每个任务都添加了以下增强：

1. **场景分类**: 6种场景类型自动识别
2. **追问阈值规则**: 基于风险等级的差异化阈值
3. **安全验证规则**: 强制安全检查
4. **质量元数据**: V2.0版本标记

### 各科室增强结果

| 科室 | 任务数 | 场景分类 | 追问阈值规则 | 示例场景 |
|------|--------|----------|--------------|----------|
| 内科 | 500 | ✅ 100% | ✅ 100% | INFORMATION_QUERY |
| 外科 | 500 | ✅ 100% | ✅ 100% | SYMPTOM_ANALYSIS |
| 妇产科 | 500 | ✅ 100% | ✅ 100% | INFORMATION_QUERY |
| 儿科 | 500 | ✅ 100% | ✅ 100% | INFORMATION_QUERY |
| 肿瘤科 | 500 | ✅ 100% | ✅ 100% | INFORMATION_QUERY |
| 男科 | 500 | ✅ 100% | ✅ 100% | INFORMATION_QUERY |

**文件大小**: 每个科室约3.4M（增强后）

---

## 追问阈值规则详情

### 规则结构
每个任务包含完整的追问阈值配置：

```json
{
  "inquiry_threshold_validation": {
    "scenario_type": "INFORMATION_QUERY",
    "risk_level": "LOW",
    "threshold_config": {
      "min_questions_before_advice": 0,
      "allowed_response_type": "FULL_ADVICE",
      "threshold_penalty": "NONE"
    },
    "evaluation_rules": [
      "🟢 低风险场景：无强制追问要求",
      "未达阈值时的处理：可直接回答+免责声明"
    ]
  }
}
```

### 场景类型分布（示例）

| 场景类型 | 风险等级 | 最小问题数 | 响应类型 |
|---------|---------|-----------|----------|
| INFORMATION_QUERY | 🟢 LOW | 0 | FULL_ADVICE |
| SYMPTOM_ANALYSIS | 🟡 MEDIUM | 3 | POSSIBILITY_RANGE |
| MEDICATION_CONSULTATION | 🔴 HIGH | 4 | SAFETY_WARNING_ONLY |
| EMERGENCY_CONCERN | 🔴 HIGH | 1 | EMERGENCY_GUIDANCE |
| CHRONIC_MANAGEMENT | 🟡 MEDIUM | 3 | MANAGEMENT_ADVICE |
| LIFESTYLE_ADVICE | 🟢 LOW | 1 | PRACTICAL_ADVICE |

---

## 数据文件位置

### 验证结果文件
```
DataQualityFiltering/test_outputs/
├── validation_内科.json       (220K对话, 152K通过)
├── validation_外科.json       (116K对话, 85K通过)
├── validation_妇产科.json     (184K对话, 121K通过)
├── validation_儿科.json       (102K对话, 68K通过)
├── validation_肿瘤科.json     (76K对话, 62K通过)
└── validation_男科.json       (95K对话, 73K通过)
```

### 转换后Tasks
```
data/processed/medical_dialogues/chinese_meddialog/
├── tasks_内科.json            (500任务)
├── tasks_外科.json            (500任务)
├── tasks_妇产科.json          (500任务)
├── tasks_儿科.json            (500任务)
├── tasks_肿瘤科.json          (500任务)
└── tasks_男科.json            (500任务)
```

### 增强后Tasks
```
DataQualityFiltering/test_outputs/
├── enhanced_tasks_内科.json    (500任务, 3.4M)
├── enhanced_tasks_外科.json    (500任务, 3.3M)
├── enhanced_tasks_妇产科.json  (500任务, 3.4M)
├── enhanced_tasks_儿科.json    (500任务, 3.4M)
├── enhanced_tasks_肿瘤科.json  (500任务, 3.4M)
└── enhanced_tasks_男科.json    (500任务, 3.5M)
```

---

## 数据质量总结

### 三级质量保证体系

#### 第1级: 原始数据验证
- ✅ 过滤低质量对话（29.2%失败率）
- ✅ 确保对话完整性
- ✅ 医学内容验证

#### 第2级: 数据转换
- ✅ 标准化格式
- ✅ 元数据提取
- ✅ 患者信息生成

#### 第3级: 数据增强
- ✅ 场景自动分类
- ✅ 追问阈值规则
- ✅ 安全验证规则

### 最终数据质量

| 指标 | 数值 |
|------|------|
| **总任务数** | 3,000 |
| **场景分类覆盖率** | 100% |
| **追问阈值规则覆盖率** | 100% |
| **安全规则覆盖率** | 100% |
| **平均文件大小** | 3.4M/科室 |

---

## 使用建议

### 立即可用 ✅

当前的3,000个增强任务已经包含：

1. **完整的场景分类** - 6种场景类型自动识别
2. **追问阈值规则** - 基于风险等级的差异化配置
3. **安全验证规则** - 强制安全检查
4. **质量元数据** - V2.0版本标记

**可直接用于**:
- Agent测试和评估
- 基准测试
- Few-shot学习示例
- 数据集发布

### 选择建议

#### 方案A: 全部科室（推荐）
- **数据量**: 3,000任务
- **适用**: 全面测试、基准评估
- **优点**: 覆盖所有科室，多样性高

#### 方案B: 高质量科室
- **推荐**: 肿瘤科、男科、外科
- **数据量**: 1,500任务
- **适用**: 高质量需求
- **优点**: 通过率最高，数据质量最优

#### 方案C: 按需选择
- **快速测试**: 肿瘤科（500任务，82.5%通过率）
- **综合测试**: 内科+外科（1,000任务）

---

## 技术栈

### 验证系统
- `raw_data_validator.py` - 原始数据验证器
- 严格模式验证
- GBK编码支持

### 转换系统
- `convert_chinese_meddialog.py` - 数据转换器
- Tau2-bench标准格式
- 自动患者信息生成

### 增强系统
- `tasks_json_improver_v2.py` - V2.0增强器
- `inquiry_threshold_validator.py` - 追问阈值验证器
- 场景分类器 + 安全验证器

---

## 后续步骤

### 选项1: 直接使用（推荐）
```bash
# 使用增强后的Tasks进行Agent测试
python tau2_eval.py \
  --input DataQualityFiltering/test_outputs/enhanced_tasks_肿瘤科.json \
  --agent your_agent.py
```

### 选项2: 合并所有科室
```bash
# 合并所有科室的Tasks
python merge_all_departments.py \
  --input-dir DataQualityFiltering/test_outputs \
  --output all_departments_3000_tasks.json
```

### 选项3: 质量筛选（可选）
```bash
# 如果需要更高质量，可以使用LLM评分
python -m DataQualityFiltering data-quality llm-review \
  --input DataQualityFiltering/test_outputs/enhanced_tasks_内科.json \
  --output scores.json

# 使用评分筛选
python -m DataQualityFiltering data-quality quality-threshold \
  --input DataQualityFiltering/test_outputs/enhanced_tasks_内科.json \
  --scores-file scores.json
```

---

## 总结

✅ **完整流程已验证**:
1. 原始数据验证（56.1万条通过）
2. 数据转换（3,000个任务）
3. 数据增强（100%规则覆盖）

✅ **产出**:
- 3,000个高质量医学咨询任务
- 6个科室全覆盖
- 完整的追问阈值规则
- 6种场景类型自动分类

✅ **可立即使用**:
- Agent测试
- 基准评估
- 数据集发布
- Few-shot学习
