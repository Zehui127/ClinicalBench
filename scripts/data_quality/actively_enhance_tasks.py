#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主动数据增强器

不仅仅检查任务质量，而是主动增强任务数据：
1. 主动添加不确定性（即使原任务没有）
2. 主动生成追问点
3. 主动添加安全规则
4. 主动创建患者特征标签

作者：Claude Sonnet 4.5
日期：2025-03-20
"""

import json
import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / "DataQualityFiltering"))

from modules.scenario_classifier import ScenarioClassifier
from modules.uncertainty_handler import UncertaintyHandler
from modules.safety_validator import SafetyValidator
from modules.inquiry_threshold_validator import InquiryThresholdValidator


def actively_enhance_tasks(input_file: str, output_file: str):
    """
    主动增强任务数据

    不仅检查，而是主动添加改进内容：
    - 为信息查询任务添加追问要求
    - 为所有任务添加安全规则
    - 为简单任务添加不确定性变体
    - 添加患者特征标签
    """
    print("="*60)
    print(" 主动数据增强器")
    print("="*60)

    # 1. 加载数据
    print(f"\n[1/6] 加载数据: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    print(f"✓ 加载了 {len(tasks)} 个任务")

    # 2. 初始化模块
    print("\n[2/6] 初始化增强模块")
    scenario_classifier = ScenarioClassifier()
    uncertainty_handler = UncertaintyHandler()
    safety_validator = SafetyValidator()
    threshold_validator = InquiryThresholdValidator({})
    print("✓ 场景分类器")
    print("✓ 不确定性处理器（主动增强模式）")
    print("✓ 安全验证器（主动生成模式）")
    print("✓ 追问阈值验证器（主动生成模式）")

    # 3. 主动增强
    print("\n[3/6] 主动增强数据...")
    enhanced_count = 0
    stats = {
        "uncertainty_added": 0,
        "inquiry_points_added": 0,
        "safety_rules_generated": 0,
        "patient_tags_added": 0
    }

    for i, task in enumerate(tasks):
        # 确保 metadata 存在
        if 'metadata' not in task:
            task['metadata'] = {}

        # 3.1 场景分类
        scenario_result = scenario_classifier.classify(task)
        scenario_type = scenario_result.get('type')
        task['metadata']['scenario_type'] = scenario_type
        task['metadata']['scenario_name'] = scenario_result.get('name')
        task['metadata']['scenario_confidence'] = scenario_result.get('confidence_score', 0)

        # 3.2 主动生成追问要求（关键！）
        inquiry_requirements = _generate_inquiry_requirements(task, scenario_type)
        if inquiry_requirements:
            task['metadata']['inquiry_requirements'] = inquiry_requirements
            stats["inquiry_points_added"] += len(inquiry_requirements)
            # 主动添加 uncertainty 来要求追问
            task = uncertainty_handler.add_uncertainty(task)
            if task.get('uncertainties_added'):
                stats["uncertainty_added"] += 1
                task['metadata']['uncertainties_added'] = task.get('uncertainties_added', [])

        # 3.3 主动生成安全规则
        safety_rules = _generate_safety_rules_by_scenario(task, scenario_type)
        if safety_rules:
            task['metadata']['safety_rules'] = safety_rules
            stats["safety_rules_generated"] += len(safety_rules)

        # 3.4 主动添加患者特征标签
        patient_tags = _generate_patient_tags(task)
        if patient_tags:
            task['metadata']['patient_tags'] = patient_tags
            stats["patient_tags_added"] += 1

        enhanced_count += 1
        if (i + 1) % 50 == 0:
            print(f"  进度: {i+1}/{len(tasks)}")

    print(f"✓ 增强了 {enhanced_count} 个任务")

    # 4. 统计增强效果
    print("\n[4/6] 增强效果统计")
    print(f"✓ 追问要求添加: {stats['inquiry_points_added']} 条")
    print(f"✓ 不确定性标记: {stats['uncertainty_added']} 个任务")
    print(f"✓ 安全规则生成: {stats['safety_rules_generated']} 条")
    print(f"✓ 患者标签: {stats['patient_tags_added']} 个任务")

    # 5. 保存增强数据
    print(f"\n[5/6] 保存增强数据: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print(f"✓ 保存完成")

    # 6. 展示增强示例
    print("\n[6/6] 增强示例展示")
    _show_enhancement_example(tasks[0])

    return tasks


def _generate_inquiry_requirements(task, scenario_type: str) -> dict:
    """
    主动生成追问要求

    根据场景类型，主动生成需要追问的信息点
    """
    ticket = task.get('ticket', '')
    requirements = {}

    # 根据场景类型生成不同的追问要求
    if scenario_type == "INFORMATION_QUERY":
        # 信息查询场景需要追问的基本信息
        requirements = {
            "basic_info": {
                "症状_duration": {
                    "question": "这个问题持续多久了？",
                    "priority": "high",
                    "reason": "判断病情发展阶段"
                },
                "severity": {
                    "question": "严重程度如何？有没有加重或缓解？",
                    "priority": "medium",
                    "reason": "评估病情严重性"
                }
            },
            "medical_context": {
                "current_medications": {
                    "question": "目前吃什么药？",
                    "priority": "high",
                    "reason": "避免药物相互作用"
                },
                "allergies": {
                    "question": "有没有药物过敏史？",
                    "priority": "high",
                    "reason": "避免过敏反应"
                }
            }
        }

    elif scenario_type == "SYMPTOM_ANALYSIS":
        # 症状分析场景需要详细追问
        requirements = {
            "symptom_details": {
                "onset": {
                    "question": "症状是什么时候开始的？",
                    "priority": "high",
                    "reason": "判断起病急缓"
                },
                "location": {
                    "question": "具体在哪个部位？",
                    "priority": "high",
                    "reason": "定位病变部位"
                },
                "character": {
                    "question": "是什么样的感觉？（疼痛、麻木、肿胀等）",
                    "priority": "high",
                    "reason": "症状性质判断"
                },
                "triggers": {
                    "question": "有什么诱因吗？（饮食、活动、情绪等）",
                    "priority": "medium",
                    "reason": "寻找诱因"
                }
            },
            "associated_symptoms": {
                "other_symptoms": {
                    "question": "还有其他不舒服吗？",
                    "priority": "high",
                    "reason": "鉴别诊断"
                }
            }
        }

    elif scenario_type == "MEDICATION_CONSULTATION":
        # 用药咨询需要详细的用药信息
        requirements = {
            "medication_details": {
                "current_medication": {
                    "question": "目前吃什么药？剂量多少？",
                    "priority": "high",
                    "reason": "评估当前用药情况"
                },
                "duration": {
                    "question": "这个药吃了多久了？",
                    "priority": "high",
                    "reason": "评估治疗时长"
                }
            },
            "safety_checks": {
                "allergies": {
                    "question": "有药物过敏史吗？",
                    "priority": "critical",
                    "reason": "避免过敏"
                },
                "interactions": {
                    "question": "还在吃其他药吗？",
                    "priority": "critical",
                    "reason": "避免药物相互作用"
                },
                "conditions": {
                    "question": "有什么其他疾病吗？肝肾功能如何？",
                    "priority": "high",
                    "reason": "考虑药物代谢"
                }
            }
        }

    elif scenario_type == "EMERGENCY_CONCERN":
        # 紧急场景需要快速识别危险信号
        requirements = {
            "emergency_assessment": {
                "severity": {
                    "question": "症状有多严重？能正常活动吗？",
                    "priority": "critical",
                    "reason": "评估危重程度"
                },
                "time_course": {
                    "question": "症状是持续的还是阵发的？",
                    "priority": "critical",
                    "reason": "判断病情趋势"
                },
                "warning_signs": {
                    "question": "有以下情况吗？（出冷汗、放射痛、呼吸困难加重）",
                    "priority": "critical",
                    "reason": "识别危险信号"
                }
            }
        }

    elif scenario_type == "CHRONIC_MANAGEMENT":
        # 慢性病管理需要追踪和控制情况
        requirements = {
            "control_status": {
                "current_status": {
                    "question": "最近指标控制得如何？",
                    "priority": "high",
                    "reason": "评估控制效果"
                },
                "medication_adherence": {
                    "question": "药按时吃了吗？有没有漏服？",
                    "priority": "high",
                    "reason": "评估依从性"
                }
            },
            "lifestyle": {
                "diet": {
                    "question": "饮食控制得怎么样？",
                    "priority": "medium",
                    "reason": "生活方式评估"
                },
                "exercise": {
                    "question": "运动情况如何？",
                    "priority": "medium",
                    "reason": "运动量评估"
                }
            }
        }

    elif scenario_type == "LIFESTYLE_ADVICE":
        # 生活方式咨询需要了解现状
        requirements = {
            "current_status": {
                "current_habits": {
                    "question": "现在这方面的习惯怎么样？",
                    "priority": "medium",
                    "reason": "了解基线情况"
                },
                "constraints": {
                    "question": "有什么限制或困难吗？",
                    "priority": "medium",
                    "reason": "考虑可行性"
                }
            }
        }

    return requirements


def _generate_safety_rules_by_scenario(task, scenario_type: str) -> list:
    """
    主动生成安全规则

    根据场景类型，主动生成必须遵守的安全规则
    """
    rules = []

    # 通用安全规则（所有场景）
    rules.append({
        "rule_type": "no_definitive_diagnosis",
        "description": "在没有充分检查依据时，不能给出确定性诊断",
        "severity": "high",
        "action": "使用'可能'、'疑似'、'需要排除'等词汇"
    })

    rules.append({
        "rule_type": "emergency_referral",
        "description": "如果出现胸痛、呼吸困难、严重头痛等症状，立即建议就医",
        "severity": "critical",
        "action": "识别危险信号并给出紧急建议"
    })

    # 场景特定规则
    if scenario_type == "INFORMATION_QUERY":
        rules.append({
            "rule_type": "medication_consultation_referral",
            "description": "涉及药物使用的问题，建议咨询医生或药师",
            "severity": "medium",
            "action": "添加'建议咨询医生'的提示"
        })

    elif scenario_type == "MEDICATION_CONSULTATION":
        rules.append({
            "rule_type": "allergy_check_required",
            "description": "必须询问过敏史",
            "severity": "critical",
            "action": "强制检查过敏史"
        })
        rules.append({
            "rule_type": "interaction_check_required",
            "description": "必须检查药物相互作用",
            "severity": "critical",
            "action": "强制检查当前用药"
        })

    elif scenario_type == "SYMPTOM_ANALYSIS":
        rules.append({
            "rule_type": "no_diagnosis_without_exam",
            "description": "不能仅凭症状就确诊，需要检查",
            "severity": "high",
            "action": "建议相关检查"
        })

    elif scenario_type == "EMERGENCY_CONCERN":
        rules.append({
            "rule_type": "immediate_action",
            "description": "紧急情况需要立即建议",
            "severity": "critical",
            "action": "不能等待，立即给出建议"
        })

    return rules


def _generate_patient_tags(task) -> dict:
    """
    主动生成患者特征标签

    根据任务内容，提取或推断患者特征
    """
    tags = {}
    ticket = task.get('ticket', '')

    # 提取患者特征
    # 1. 年龄推断
    if any(kw in ticket for kw in ["老人", "爷爷", "奶奶", "高龄"]):
        tags["age_group"] = "elderly"
    elif any(kw in ticket for kw in ["小孩", "孩子", "婴儿", "宝宝"]):
        tags["age_group"] = "pediatric"

    # 2. 情绪状态
    if any(kw in ticket for kw in ["担心", "害怕", "焦虑", "恐慌"]):
        tags["emotional_state"] = "anxious"
    elif any(kw in ticket for kw in ["平静", "还好", "一般"]):
        tags["emotional_state"] = "calm"

    # 3. 信息质量
    if any(kw in ticket for kw in ["不确定", "不知道", "不清楚"]):
        tags["information_quality"] = "poor"
    elif any(kw in ticket for kw in ["详细", "具体", "明确"]):
        tags["information_quality"] = "good"

    # 4. 咨询目的
    if any(kw in ticket for kw in ["能吃", "能不能", "可以吃"]):
        tags["consultation_purpose"] = "medication_safety"
    elif any(kw in ticket for kw in ["怎么", "如何", "是什么"]):
        tags["consultation_purpose"] = "information_seeking"
    elif any(kw in ticket for kw in ["是不是", "是啥"]):
        tags["consultation_purpose"] = "diagnosis_seeking"

    return tags


def _show_enhancement_example(task):
    """展示增强前后的对比"""
    print("\n任务示例:", task['id'])
    print("\n原始字段:", list(task.keys()))
    print("\n新增metadata字段:")

    metadata = task.get('metadata', {})
    for key, value in metadata.items():
        if isinstance(value, (str, int, float, bool)):
            print(f"  {key}: {value}")
        elif isinstance(value, list):
            print(f"  {key}: {len(value)} items")
        elif isinstance(value, dict):
            print(f"  {key}: {list(value.keys())[:5]}...")

    # 特别展示追问要求
    if 'inquiry_requirements' in metadata:
        print("\n  [新增] 追问要求示例:")
        reqs = metadata['inquiry_requirements']

        for category, items in list(reqs.items())[:2]:
            print(f"    {category}:")
            if isinstance(items, dict):
                for key, info in list(items.items())[:2]:
                    print(f"      - {key}: {info.get('question', 'N/A')}")
                    print(f"        优先级: {info.get('priority', 'N/A')}")

    # 特别展示安全规则
    if 'safety_rules' in metadata and metadata['safety_rules']:
        print(f"\n  [新增] 安全规则: {len(metadata['safety_rules'])} 条")
        for rule in metadata['safety_rules'][:3]:
            print(f"      - {rule.get('rule_type')}: {rule.get('description')}")


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 输入输出文件路径
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_enhanced.json"

    # 运行主动增强
    try:
        enhanced_tasks = actively_enhance_tasks(input_file, output_file)

        print("\n" + "="*60)
        print(" ✓ 主动增强完成！")
        print("="*60)
        print(f"\n对比:")
        print(f"  被动检查: tasks_improved.json (检查现有特征)")
        print(f"  主动增强: tasks_enhanced.json (主动添加特征)")
        print(f"\n下一步:")
        print(f"1. 查看 tasks_enhanced.json")
        print(f"2. 使用增强后的数据进行Agent评估")
        print(f"3. 分析Agent在不同场景下的表现")

    except Exception as e:
        print(f"\n[错误] 增强失败: {e}")
        import traceback
        traceback.print_exc()
