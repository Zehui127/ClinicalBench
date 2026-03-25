# 医学对话任务生成器 (Medical Dialogue Task Generator)

一个可复用的医学对话任务生成器，能够从原始医患对话数据自动生成符合tau2-bench格式的评估任务。

## 功能特性

- **难度分级**：自动识别任务复杂度，分为L1（基础）、L2（中等）、L3（高难）三个级别
- **患者行为模拟**：生成真实患者行为，包括信息隐瞒、说谎、矛盾陈述、情绪状态等
- **对话流程控制**：配置对话展开模式和信息逐渐揭露机制
- **评估标准构建**：自动生成完整的评估标准，包括通信检查和安全规则
- **安全红线测试**：内置红线测试机制，确保AI助手不犯关键错误
- **场景类型识别**：自动识别8种常见医疗场景类型
- **医学专业性保证**：内置医学知识库，确保生成任务的医学专业性

## 安装

### 从源码安装

```bash
cd MedicalDialogueTaskGenerator
pip install -e .
```

### 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 基础使用

```python
from src.core.task_generator import TaskGenerator
from src.models.data_models import RawDialogueData

# 初始化生成器
generator = TaskGenerator()

# 准备输入数据
raw_data = RawDialogueData(
    id="dialogue_001",
    ticket="高血压患者能吃党参吗？",
    known_info="我有高血压这两天女婿来的时候给我拿了些党参泡水喝",
    department_cn="内科",
    source="Chinese MedDialog",
    original_title="高血压患者能吃党参吗？"
)

# 生成任务
task = generator.generate(raw_data)

# 保存结果
import json
with open("output.json", "w", encoding="utf-8") as f:
    json.dump(task.to_dict(), f, ensure_ascii=False, indent=2)
```

### 命令行使用

```bash
# 生成单个任务
python -m src.cli --input sample_input.json --output output.json

# 批量生成
python -m src.cli --input-dir raw_data/ --output-dir tasks/

# 指定难度分布
python -m src.cli --input data.json --output tasks.json \
    --difficulty-distribution L1:0.5,L2:0.3,L3:0.2

# 验证任务
python -m src.cli --validate --input tasks.json

# 统计分析
python -m src.cli --stats --input tasks.json
```

## 输入数据格式

```json
{
  "id": "dialogue_001",
  "ticket": "患者的主诉问题",
  "known_info": "患者提供的信息",
  "department_cn": "科室名称",
  "source": "数据来源",
  "original_title": "原始标题"
}
```

## 输出任务格式

生成的任务包含以下核心字段：

```json
{
  "id": "任务ID",
  "description": {
    "purpose": "任务目的",
    "notes": "备注信息"
  },
  "user_scenario": {
    "persona": "患者人设",
    "instructions": "患者指令"
  },
  "ticket": "患者主诉",
  "evaluation_criteria": {
    "actions": [...],
    "communication_checks": [...]
  },
  "metadata": {
    "scenario_type": "场景类型",
    "inquiry_requirements": {...},
    "safety_rules": [...]
  },
  "difficulty": "L1/L2/L3",
  "patient_behavior": {
    "cooperation": "配合度",
    "behaviors": ["行为列表"],
    "information_quality": "信息质量"
  }
}
```

## 难度级别说明

### L1（基础难度）
- 患者完全配合，信息完整
- 无信息隐瞒、无矛盾、无情绪问题
- 适用于简单信息查询和基础健康咨询

### L2（中等难度）
- 患者部分配合，存在信息隐瞒
- 需要3-5轮对话获取完整信息
- 包含系统记录和问诊策略
- 适用于药物咨询和症状分析

### L3（高难度）
- 患者不配合，多重行为问题
- 包含矛盾信息、情绪干扰
- 需要4-6轮对话
- 包含安全红线测试
- 适用于复杂病例和多重并发症

## 场景类型

| 类型 | 中文名称 | 说明 |
|------|---------|-----|
| INFORMATION_QUERY | 信息查询 | 患者询问能否做某事、如何做某事 |
| SYMPTOM_ANALYSIS | 症状分析 | 患者询问症状原因、怎么回事 |
| CHRONIC_MANAGEMENT | 慢性病管理 | 慢性病长期管理和控制 |
| MEDICATION_CONSULTATION | 药物咨询 | 关于药物使用、副作用、相互作用 |
| LIFESTYLE_ADVICE | 生活方式建议 | 饮食、运动、生活习惯建议 |
| EMERGENCY_CONCERN | 紧急关注 | 可能涉及危险信号的情况 |

## 配置文件

### difficulty_rules.yaml
难度分级规则配置，包括：
- 难度分布比例
- 复杂度分数阈值
- 场景类型基础分数

### behavior_templates.yaml
患者行为模板配置，包括：
- 信息隐瞒行为
- 说谎场景
- 情绪状态
- 矛盾类型

### evaluation_templates.yaml
评估标准模板配置，包括：
- 不同难度级别的评估标准
- 场景类型与问诊要求映射
- 评分标准

### safety_rules.yaml
安全规则库配置，包括：
- 安全规则定义
- 红线测试配置
- 评分权重

## 项目结构

```
MedicalDialogueTaskGenerator/
├── README.md
├── setup.py
├── requirements.txt
├── config/
│   ├── difficulty_rules.yaml
│   ├── behavior_templates.yaml
│   ├── evaluation_templates.yaml
│   └── safety_rules.yaml
├── src/
│   ├── core/
│   │   ├── task_generator.py
│   │   ├── difficulty_classifier.py
│   │   ├── behavior_assigner.py
│   │   ├── evaluation_builder.py
│   │   └── scenario_detector.py
│   ├── models/
│   │   ├── data_models.py
│   │   └── tau2_schema.py
│   └── utils/
│       ├── text_analyzer.py
│       ├── medical_knowledge.py
│       └── validator.py
├── tests/
└── examples/
    └── usage_example.py
```

## 示例代码

查看 `examples/usage_example.py` 获取更多使用示例：

```bash
python examples/usage_example.py
```

示例包括：
1. 基础使用 - 生成单个任务
2. 批量生成 - 处理多个原始对话
3. 自定义配置 - 调整难度分布
4. 任务验证 - 验证生成的任务
5. 统计分析 - 分析任务分布
6. 从真实数据生成 - 从MedDialog数据生成

## 测试

运行测试：

```bash
pytest tests/
```

运行特定测试：

```bash
pytest tests/test_generator.py
pytest tests/test_difficulty.py
pytest tests/test_behavior.py
pytest tests/test_validation.py
```

## 开发路线图

- [ ] 完整实现所有核心模块
- [ ] 添加更多场景类型支持
- [ ] 集成真实的医学知识库
- [ ] 支持多语言
- [ ] 添加Web界面
- [ ] 性能优化和缓存

## 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详见 LICENSE 文件。

## 联系方式

如有问题或建议，请创建Issue或联系维护者。

## 致谢

- tau2-bench项目
- Chinese MedDialog数据集
- 医学对话评估最佳实践

## 更新日志

### v0.1.0 (2025-03-23)
- 初始版本
- 基础任务生成功能
- L1/L2/L3难度分级
- 核心患者行为支持
- 配置文件系统
