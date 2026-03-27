# 医疗任务Benchmark格式说明

## 概述

本目录包含了使用改进后的医疗任务格式的benchmark示例。这些示例展示了如何设计以目标为导向（goal-oriented）的医疗评估任务，而非基于脚本（script-based）的任务。

## 核心设计理念

### 1. 目标导向 vs 过程导向

**❌ 错误方式（过程导向）**:
```json
{
  "evaluation": {
    "must_ask_questions": [
      "您多久了？",
      "您家族有人有糖尿病吗？"
    ]
  }
}
```
这种方式限制了医生agent的灵活性，无法评估真实能力。

**✅ 正确方式（目标导向）**:
```json
{
  "evaluation": {
    "must_collect_information": {
      "duration": {
        "required": true,
        "description": "症状持续时间"
      },
      "family_history": {
        "required": true,
        "description": "家族史"
      }
    }
  }
}
```
这种方式关注医生是否收集了必要信息，而非具体问了什么问题。

### 2. 患者模拟器 vs 脚本对话

**❌ 错误方式（脚本对话）**:
```json
{
  "dialogue": [
    {"role": "doctor", "content": "您哪里不舒服？"},
    {"role": "patient", "content": "我口渴、多尿"}
  ]
}
```
这只是示例，不应作为评估标准。

**✅ 正确方式（信息共享策略）**:
```json
{
  "information_sharing_strategy": {
    "volunteer_without_asking": [
      "主诉：口渴、多尿、体重下降",
      "部分症状细节"
    ],
    "share_only_if_asked": [
      "具体持续时间（需要医生追问）",
      "当前用药情况"
    ]
  }
}
```
定义患者在什么情况下会分享什么信息，允许灵活对话。

## 任务文件结构

### 必需字段

```json
{
  "id": "唯一标识符",
  "domain": "临床领域（cardiology/respiratory/endocrinology等）",
  "task_type": "任务类型（initial_diagnosis/acute_management/chronic_management/followup）",
  "difficulty": "难度（easy/medium/medium_high/high）",
  "estimated_duration_minutes": 15,
  "version": "benchmark_v1",

  "description": {
    "purpose": "任务目的",
    "clinical_scenario": "临床场景描述",
    "educational_objectives": ["教学目标1", "教学目标2"]
  },

  "user_scenario": {
    "persona": "患者人设描述",
    "patient_profile": {
      "age": 48,
      "gender": "male",
      "education_level": "elementary",
      "communication_style": "simple"
    },
    "information_sharing_strategy": {
      "volunteer_without_asking": ["患者主动提供的信息"],
      "share_only_if_asked": ["需要医生询问的信息"],
      "response_style": {
        "honest": true,
        "limited_medical_knowledge": true
      }
    },
    "task_instructions": "患者扮演指令"
  },

  "medical_persona": {
    "age": 48,
    "gender": "male",
    "symptoms": ["症状1", "症状2"],
    "duration": "1个月",
    "severity": "moderate",
    "past_medical_history": [],
    "current_medications": [],
    "allergies": [],
    "lab_results": {},
    "vital_signs": {},
    "lifestyle_factors": {},
    "diagnosis": {
      "primary": "主要诊断",
      "differential_diagnoses": ["鉴别诊断1", "鉴别诊断2"]
    }
  },

  "ticket": "患者主诉/就诊原因",

  "initial_state": {
    "initialization_actions": [
      {
        "env_type": "user",
        "func_name": "set_user_info",
        "arguments": {}
      },
      {
        "env_type": "user",
        "func_name": "set_medical_persona",
        "arguments": {}
      }
    ]
  },

  "evaluation_criteria": {
    "actions": [],
    "communication_checks": [],
    "medical_criteria": {}
  },

  "reference_dialogue": {
    "note": "仅供参考，不要求遵循",
    "dialogue": []
  },

  "metadata": {}
}
```

### evaluation_criteria 详细说明

#### medical_criteria 结构

```json
{
  "medical_criteria": {
    "category": "diagnosis/treatment/suggestion",

    "information_gathering_requirements": {
      "must_collect": {
        "信息项名称": {
          "required": true,
          "description": "描述",
          "weight": 0.15
        }
      },
      "scoring_method": "count",
      "pass_threshold": 0.8
    },

    "diagnostic_requirements": {
      "diagnosis_accuracy": {
        "correct_diagnosis": "正确诊断",
        "allow_alternatives": ["可接受的替代诊断"],
        "weight": 0.30
      },
      "differential_diagnosis": {
        "must_consider": ["必须考虑的鉴别诊断"],
        "must_exclude": true,
        "exclusion_method": "laboratory_tests/clinical_features",
        "weight": 0.20
      },
      "appropriate_tests": {
        "must_order": ["必需检查"],
        "should_order": ["建议检查"],
        "weight": 0.15
      }
    },

    "treatment_requirements": {
      "medication_appropriateness": {
        "should_prescribe": ["应该开具的药物"],
        "appropriate_combination": "合理组合",
        "weight": 0.25
      },
      "patient_education": {
        "must_cover": ["必须包含的教育内容"],
        "appropriate_level": "simple/clear",
        "weight": 0.20
      }
    },

    "safety_requirements": {
      "safety_rules": {
        "规则名称": {
          "severity": "critical/high/medium",
          "check_method": "检查方法",
          "violation_penalty": -1.0
        }
      },
      "safety_checks": {
        "检查项": {
          "required": true,
          "weight": 0.10
        }
      }
    },

    "communication_requirements": {
      "language_appropriateness": {
        "target_audience": "教育水平",
        "avoid": ["应避免的内容"],
        "use": ["应使用的方式"],
        "weight": 0.10
      },
      "empathy": {
        "show_understanding": true,
        "acknowledge_concerns": true,
        "weight": 0.10
      },
      "turn_limits": {
        "min_turns": 8,
        "max_turns": 18
      }
    },

    "efficiency_requirements": {
      "should_avoid": {
        "repetitive_questions": {"penalty": -0.05}
      },
      "should_optimize": {
        "timely_diagnosis": {
          "expected_turns_to_diagnosis": 15,
          "weight": 0.05
        }
      }
    }
  },

  "scoring": {
    "total_score": 100,
    "weights": {
      "information_gathering": 20,
      "diagnosis_accuracy": 30,
      "treatment_appropriateness": 25,
      "safety_compliance": 15,
      "communication_quality": 10
    },
    "passing_score": 70,
    "excellent_score": 85
  }
}
```

## 示例文件说明

### 1. diabetes_initial_v1.json
- **领域**: 内分泌科
- **任务类型**: 初诊
- **难度**: 中等
- **患者**: 48岁男性，小学文化，"三多一少"症状
- **诊断**: 2型糖尿病
- **教学重点**:
  - 糖尿病初诊诊断流程
  - 鉴别诊断（甲亢、肾病、尿崩症）
  - 与低学历患者沟通
  - 慢性病患者教育
- **评估维度权重**:
  - 信息采集: 20%
  - 诊断准确性: 30%
  - 治疗合理性: 25%
  - 安全合规: 15%
  - 沟通质量: 10%

### 2. angina_initial_v1.json
- **领域**: 心血管内科
- **任务类型**: 初诊
- **难度**: 中等
- **患者**: 55岁女性，初中文化，反复胸痛3个月
- **诊断**: 冠心病，心绞痛（CCS II级）
- **教学重点**:
  - 心绞痛的诊断流程
  - 心血管风险评估
  - 胸痛鉴别诊断
  - 冠心病患者的长期管理
- **评估维度权重**:
  - 信息采集: 15%
  - 诊断准确性: 30%
  - 风险分层: 10%
  - 治疗合理性: 25%
  - 安全合规: 15%
  - 沟通质量: 5%

### 3. copd_exacerbation_v1.json
- **领域**: 呼吸内科
- **任务类型**: 急性期管理
- **难度**: 中高
- **患者**: 68岁男性，小学文化，COPD急性加重
- **诊断**: COPD急性加重（中度）
- **教学重点**:
  - COPD急性加重的评估
  - 严重程度分级和住院指征判断
  - 鉴别诊断（肺炎、心衰、肺栓塞）
  - COPD急性加重的规范化治疗
  - 吸入剂技术教育
  - 吸烟戒断指导
- **评估维度权重**:
  - 信息采集: 15%
  - 严重程度评估: 25%
  - 诊断准确性: 15%
  - 治疗合理性: 25%
  - 住院决策: 10%
  - 安全合规: 15%
  - 沟通质量: 5%

## 评估标准设计原则

### 1. 可量化性
所有评估标准都应该可以量化：
- 使用 weight 定义权重
- 使用 pass_threshold 定义通过阈值
- 使用 violation_penalty 定义违规惩罚

### 2. 可自动化
评估标准应该支持自动化检查：
- 工具使用检查：检查是否使用了必需工具
- 信息收集检查：检查是否收集了必需信息
- 诊断准确性：检查诊断是否在允许列表中
- 安全规则：使用关键词匹配检查红线违规

### 3. 灵活性
允许不同的实现路径：
- 关注结果（是否收集了信息），而非过程（问了什么问题）
- 关注目标（是否做出正确诊断），而非方法（具体推理步骤）

### 4. 医学准确性
- 诊断标准符合临床指南
- 治疗方案基于循证医学
- 鉴别诊断考虑重要疾病
- 安全规则基于医疗安全原则

## 使用指南

### 创建新任务

1. **确定临床场景和教学目标**
2. **设计患者人设**（包括教育水平、沟通风格）
3. **定义信息共享策略**（区分主动提供 vs 需询问）
4. **构建医疗角色数据**（symptoms, lab_results, vital_signs等）
5. **设计评估标准**：
   - 信息采集要求
   - 诊断要求（包括鉴别诊断）
   - 治疗要求
   - 安全规则
   - 沟通要求
   - 效率要求
6. **设置评分权重和阈值**

### 评估Agent表现

1. **工具选择正确性**
   - 检查是否使用了 expected_tool_category 中的工具
   - 检查是否包含所有 required_tools

2. **信息收集完整性**
   - 检查是否收集了所有 must_collect 中的信息
   - 计算信息收集覆盖率

3. **诊断准确性**
   - 检查诊断是否在 correct_diagnosis 或 allow_alternatives 中
   - 检查是否考虑了鉴别诊断
   - 检查诊断是否有检查结果支持

4. **治疗合理性**
   - 检查是否开具了 should_prescribe 中的药物
   - 检查是否包含了必要的患者教育内容

5. **安全合规**
   - 检查是否违反了 safety_rules 中的红线规则
   - 检查是否完成了 safety_checks 中的检查项

6. **沟通质量**
   - 检查语言是否适合患者教育水平
   - 检查是否展现了同理心
   - 检查是否清晰解释了诊断和治疗方案

7. **对话效率**
   - 检查对话轮次是否在 min_turns 和 max_turns 范围内
   - 检查是否有重复或无关问题

## 下一步计划

1. **创建更多专科示例**
   - 消化内科（急性胰腺炎、消化性溃疡）
   - 肾内科（慢性肾病、急性肾损伤）
   - 神经内科（脑卒中、癫痫）
   - 急诊医学（胸痛、腹痛、外伤）

2. **实现评估器代码**
   - 工具使用评估器
   - 信息收集评估器
   - 诊断准确性评估器
   - 安全合规评估器
   - 沟通质量评估器

3. **应用到现有任务**
   - 使用新格式重新生成医疗任务套件中的所有任务
   - 确保与现有框架兼容

4. **测试和验证**
   - 使用不同AI agent进行测试
   - 收集反馈并改进评估标准
   - 优化评分权重和阈值

## 参考资料

- tau2-bench框架文档
- 医疗任务数据模型：`src/tau2/data_model/medical_tasks.py`
- 工具分类：`src/tau2/domains/clinical/tool_categories.py`
- PrimeKG知识图谱集成

## 版本历史

- **v1** (2025-03-27): 初始版本，包含3个专科示例
  - 糖尿病初诊
  - 心绞痛初诊
  - COPD急性加重
