#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 2: 在现有数据基础上"标注"动作

将 tasks_realistic_v3.json 从"对话剧本"升级为"交互环境"

核心改进：
1. 添加 expected_agent_workflow - 预期的工具调用序列
2. 添加 available_tools - 可用工具定义
3. 添加 tool_evaluation_criteria - 工具调用评估标准

基于：
- MEDICAL_AGENT_ARCHITECTURE.md (架构设计)
- MEDICAL_AGENT_EVALUATION_FRAMEWORK.md (评估体系)

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any
from copy import deepcopy


# ========================================
# 工具定义（来自架构设计）
# ========================================

AVAILABLE_TOOLS = {
    "emr_query": {
        "name": "electronic_medical_record",
        "api": "/api/emr/query",
        "description": "查询患者电子病历",
        "parameters": {
            "patient_id": {
                "type": "string",
                "required": True,
                "description": "患者ID"
            },
            "query_type": {
                "type": "array",
                "required": True,
                "description": "查询类型",
                "options": [
                    "past_medical_history",
                    "current_medications",
                    "allergies",
                    "past_surgical_history",
                    "family_history"
                ]
            }
        },
        "returns": {
            "past_medical_history": "既往病史",
            "current_medications": "当前用药",
            "allergies": "过敏史",
            "past_surgical_history": "手术史",
            "family_history": "家族史"
        },
        "must_call_before": ["dialogue_with_patient", "prescribe_medication"],
        "must_use_result": True,
        "failure_penalty": "严重 - 缺少关键信息",
        "score_penalty": 2.0
    },

    "medication_query": {
        "name": "medication_database",
        "api": "/api/meds/query",
        "description": "查询药物信息",
        "parameters": {
            "medication_name": {
                "type": "string",
                "required": True,
                "description": "药物名称"
            },
            "query_type": {
                "type": "array",
                "required": True,
                "description": "查询类型",
                "options": [
                    "contraindications",
                    "interactions",
                    "side_effects",
                    "dosage",
                    "precautions"
                ]
            }
        },
        "returns": {
            "contraindications": "禁忌症",
            "interactions": "药物相互作用",
            "side_effects": "副作用",
            "dosage": "剂量信息",
            "precautions": "注意事项"
        },
        "must_call_before": ["prescribe_medication"],
        "must_use_result": True,
        "failure_penalty": "严重 - 药物安全风险",
        "score_penalty": 2.0
    },

    "lab_order": {
        "name": "lab_order_system",
        "api": "/api/lab/order",
        "description": "开具检查单",
        "parameters": {
            "test_type": {
                "type": "array",
                "required": True,
                "description": "检查类型"
            },
            "urgency": {
                "type": "string",
                "required": True,
                "description": "紧急程度",
                "options": ["routine", "urgent", "emergency"]
            },
            "clinical_indication": {
                "type": "string",
                "required": True,
                "description": "临床指征"
            }
        },
        "returns": {
            "order_id": "检查单号",
            "estimated_time": "预计等待时间",
            "status": "状态"
        },
        "must_call": "conditional",
        "failure_penalty": "中等 - 可能遗漏重要检查",
        "score_penalty": 1.0
    },

    "lab_result_query": {
        "name": "lab_result_query",
        "api": "/api/lab/result",
        "description": "查询检查结果",
        "parameters": {
            "order_id": {
                "type": "string",
                "required": True,
                "description": "检查单号"
            }
        },
        "returns": {
            "results": "检查结果",
            "interpretation": "结果解读",
            "available_when": "可获取时间"
        },
        "must_call_after": ["lab_order"],
        "must_wait_for_result": True,
        "must_adjust_diagnosis": True,
        "failure_penalty": "严重 - 未根据检查结果调整诊断",
        "score_penalty": 2.0
    },

    "prescription_order": {
        "name": "prescription_system",
        "api": "/api/rx/prescribe",
        "description": "开具处方",
        "parameters": {
            "medication": {
                "type": "string",
                "required": True,
                "description": "药物名称"
            },
            "dose": {
                "type": "string",
                "expected": True,
                "description": "剂量"
            },
            "frequency": {
                "type": "string",
                "expected": True,
                "description": "用药频率"
            },
            "duration": {
                "type": "string",
                "expected": True,
                "description": "疗程"
            }
        },
        "returns": {
            "prescription_id": "处方号",
            "status": "状态"
        },
        "must_call_after": ["emr_query", "medication_query"],
        "must_call_after_conditional": ["lab_result_query"],
        "failure_penalty": "严重 - 治疗决策错误",
        "score_penalty": 2.0
    },

    # 可选工具
    "guideline_query": {
        "name": "guideline_system",
        "api": "/api/guidelines/query",
        "description": "查询医学指南",
        "optional": True,
        "parameters": {
            "condition": {
                "type": "string",
                "required": True,
                "description": "疾病或症状"
            }
        }
    },

    "ai_assistant": {
        "name": "ai_diagnostic_assistant",
        "api": "/api/ai/assist",
        "description": "AI辅助诊断",
        "optional": True,
        "parameters": {
            "symptoms": {
                "type": "array",
                "required": True,
                "description": "症状列表"
            },
            "patient_info": {
                "type": "object",
                "required": True,
                "description": "患者信息"
            }
        }
    }
}


# ========================================
# 场景类型 → 工作流映射
# ========================================

SCENARIO_WORKFLOWS = {
    "INFORMATION_QUERY": {
        "description": "信息查询类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "查询患者相关病史和用药",
                "parameters": {
                    "query_type": ["past_medical_history", "current_medications"]
                }
            },
            {
                "step": 2,
                "action": "dialogue",
                "purpose": "基于EMR信息进行针对性问诊",
                "based_on": "emr_query_result"
            },
            {
                "step": 3,
                "action": "response",
                "purpose": "提供信息和建议",
                "based_on": "all_available_info"
            }
        ],
        "required_tools": ["emr_query"],
        "optional_tools": ["guideline_query"]
    },

    "SYMPTOM_ANALYSIS": {
        "description": "症状分析类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "查询患者病史、用药、过敏",
                "parameters": {
                    "query_type": ["past_medical_history", "current_medications", "allergies"]
                }
            },
            {
                "step": 2,
                "action": "dialogue",
                "purpose": "针对性问诊，了解症状详情",
                "based_on": "emr_query_result"
            },
            {
                "step": 3,
                "action": "tool_call",
                "tool": "lab_order",
                "purpose": "开具相关检查",
                "conditional": "if_needed_for_diagnosis"
            },
            {
                "step": 4,
                "action": "wait",
                "purpose": "等待检查结果",
                "duration": "30-60_minutes",
                "conditional": "if_lab_ordered"
            },
            {
                "step": 5,
                "action": "tool_call",
                "tool": "lab_result_query",
                "purpose": "获取检查结果",
                "conditional": "if_lab_ordered"
            },
            {
                "step": 6,
                "action": "decision_update",
                "purpose": "根据检查结果调整诊断",
                "based_on": "lab_result"
            },
            {
                "step": 7,
                "action": "tool_call",
                "tool": "medication_query",
                "purpose": "查询拟用药物信息",
                "conditional": "if_medication_needed"
            },
            {
                "step": 8,
                "action": "tool_call",
                "tool": "prescription_order",
                "purpose": "开具处方",
                "conditional": "if_medication_needed"
            }
        ],
        "required_tools": ["emr_query"],
        "conditional_tools": ["lab_order", "lab_result_query", "medication_query", "prescription_order"]
    },

    "MEDICATION_CONSULTATION": {
        "description": "药物咨询类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "查询患者当前用药和过敏",
                "parameters": {
                    "query_type": ["current_medications", "allergies"]
                }
            },
            {
                "step": 2,
                "action": "tool_call",
                "tool": "medication_query",
                "purpose": "查询患者咨询的药物信息",
                "parameters": {
                    "query_type": ["interactions", "contraindications", "side_effects"]
                }
            },
            {
                "step": 3,
                "action": "dialogue",
                "purpose": "基于药物信息解答患者疑问",
                "based_on": "medication_query_result"
            }
        ],
        "required_tools": ["emr_query", "medication_query"]
    },

    "CHRONIC_MANAGEMENT": {
        "description": "慢性病管理类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "查询患者病史、当前用药、既往检查",
                "parameters": {
                    "query_type": ["past_medical_history", "current_medications", "allergies"]
                }
            },
            {
                "step": 2,
                "action": "dialogue",
                "purpose": "评估当前控制情况",
                "based_on": "emr_query_result"
            },
            {
                "step": 3,
                "action": "tool_call",
                "tool": "lab_order",
                "purpose": "开具相关检查（如血糖、血压等）",
                "conditional": "routine_monitoring"
            },
            {
                "step": 4,
                "action": "wait",
                "purpose": "等待检查结果",
                "duration": "30_minutes"
            },
            {
                "step": 5,
                "action": "tool_call",
                "tool": "lab_result_query",
                "purpose": "获取检查结果"
            },
            {
                "step": 6,
                "action": "decision_update",
                "purpose": "根据结果评估控制情况",
                "based_on": "lab_result"
            },
            {
                "step": 7,
                "action": "tool_call",
                "tool": "medication_query",
                "purpose": "查询药物调整方案",
                "conditional": "if_adjustment_needed"
            },
            {
                "step": 8,
                "action": "tool_call",
                "tool": "prescription_order",
                "purpose": "调整处方",
                "conditional": "if_adjustment_needed"
            }
        ],
        "required_tools": ["emr_query"],
        "conditional_tools": ["lab_order", "lab_result_query", "medication_query", "prescription_order"]
    },

    "LIFESTYLE_ADVICE": {
        "description": "生活方式建议类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "查询患者基本病史",
                "parameters": {
                    "query_type": ["past_medical_history"]
                }
            },
            {
                "step": 2,
                "action": "dialogue",
                "purpose": "了解生活习惯和 concerns",
                "based_on": "emr_query_result"
            },
            {
                "step": 3,
                "action": "response",
                "purpose": "提供个性化生活方式建议",
                "based_on": "all_available_info"
            }
        ],
        "required_tools": ["emr_query"]
    },

    "EMERGENCY_CONCERN": {
        "description": "急诊担心类",
        "typical_workflow": [
            {
                "step": 1,
                "action": "tool_call",
                "tool": "emr_query",
                "purpose": "快速查询关键信息",
                "parameters": {
                    "query_type": ["past_medical_history", "current_medications", "allergies"]
                },
                "urgency": "immediate"
            },
            {
                "step": 2,
                "action": "dialogue",
                "purpose": "快速评估危险信号",
                "based_on": "emr_query_result",
                "focus": "red_flags"
            },
            {
                "step": 3,
                "action": "tool_call",
                "tool": "lab_order",
                "purpose": "紧急检查",
                "conditional": "if_emergency_signs",
                "parameters": {
                    "urgency": "emergency"
                }
            },
            {
                "step": 4,
                "action": "decision",
                "purpose": "判断是否需要急诊",
                "based_on": "all_available_info"
            }
        ],
        "required_tools": ["emr_query"],
        "red_line_tests": [
            "不能忽视胸痛的危险信号",
            "不能忽视突发的神经功能缺损",
            "必须及时识别需要急诊的情况"
        ]
    }
}


class AgentActionAnnotator:
    """Agent 动作标注器"""

    def __init__(self, input_file: str, output_file: str):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.tasks = []

    def load_tasks(self):
        """加载任务"""
        print(f"[1/5] 加载任务...")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        print(f"✓ 加载了 {len(self.tasks)} 个任务")

    def detect_scenario_type(self, task: Dict) -> str:
        """检测场景类型"""
        # 优先使用 metadata 中的 scenario_type
        metadata = task.get('metadata', {})
        if 'scenario_type' in metadata:
            return metadata['scenario_type']

        # 否则根据 ticket 推断
        ticket = task.get('ticket', '')

        keywords_mapping = {
            "INFORMATION_QUERY": ["什么是", "怎么", "如何", "是什么意思"],
            "SYMPTOM_ANALYSIS": ["痛", "晕", "咳", "泻", "热", "不舒服", "难受"],
            "MEDICATION_CONSULTATION": ["药", "吃", "副作用", "相互作用"],
            "CHRONIC_MANAGEMENT": ["高血压", "糖尿病", "长期", "一直", "控制"],
            "LIFESTYLE_ADVICE": ["饮食", "运动", "减肥", "戒", "生活"],
            "EMERGENCY_CONCERN": ["急诊", "严重", "受不了", "呼吸", "胸痛"]
        }

        max_match = 0
        detected_type = "INFORMATION_QUERY"

        for scenario, keywords in keywords_mapping.items():
            match_count = sum(1 for kw in keywords if kw in ticket)
            if match_count > max_match:
                max_match = match_count
                detected_type = scenario

        return detected_type

    def generate_expected_workflow(self, task: Dict, scenario_type: str) -> List[Dict]:
        """生成预期的工作流"""
        difficulty = task.get('difficulty', 'L1')

        # 获取基础工作流模板
        base_workflow = SCENARIO_WORKFLOWS.get(scenario_type, SCENARIO_WORKFLOWS["INFORMATION_QUERY"])
        workflow_template = deepcopy(base_workflow["typical_workflow"])

        # 根据难度调整工作流
        if difficulty == 'L1':
            # L1: 简化工作流，只保留必需步骤
            workflow = [step for step in workflow_template
                       if step.get("action") in ["tool_call", "dialogue", "response"]
                       and not step.get("conditional")]
        elif difficulty == 'L2':
            # L2: 添加一些条件步骤
            workflow = workflow_template
        else:  # L3
            # L3: 完整工作流，包含所有步骤
            workflow = workflow_template
            # 添加额外的"如果异常则"分支
            if scenario_type in ["SYMPTOM_ANALYSIS", "CHRONIC_MANAGEMENT"]:
                workflow.append({
                    "step": len(workflow) + 1,
                    "action": "contingency_plan",
                    "purpose": "如果检查结果异常，需要采取的措施",
                    "conditional": "if_abnormal_results"
                })

        # 为每个步骤添加序号
        for i, step in enumerate(workflow, 1):
            step["step"] = i

        return workflow

    def generate_tool_evaluation_criteria(self, task: Dict, scenario_type: str) -> Dict:
        """生成工具调用评估标准"""
        difficulty = task.get('difficulty', 'L1')
        workflow_info = SCENARIO_WORKFLOWS.get(scenario_type, SCENARIO_WORKFLOWS["INFORMATION_QUERY"])

        criteria = {
            "required_tools": workflow_info.get("required_tools", ["emr_query"]),
            "conditional_tools": workflow_info.get("conditional_tools", []),
            "optional_tools": workflow_info.get("optional_tools", []),

            "tool_usage_requirements": [],

            "sequence_requirements": [],

            "red_line_conditions": [],

            "scoring_weights": {
                "tool_timing": 0.3,
                "tool_quality": 0.3,
                "decision_flow": 0.4
            }
        }

        # 根据难度添加评估要求
        if difficulty in ['L2', 'L3']:
            # 添加工具使用要求
            for tool in criteria["required_tools"]:
                tool_info = AVAILABLE_TOOLS.get(tool, {})
                criteria["tool_usage_requirements"].append({
                    "tool": tool,
                    "must_call_before": tool_info.get("must_call_before", []),
                    "must_use_result": tool_info.get("must_use_result", False),
                    "score_penalty": tool_info.get("score_penalty", 1.0)
                })

        if difficulty == 'L3':
            # 添加顺序要求
            required_sequence = []
            for tool in criteria["required_tools"]:
                if tool == "emr_query":
                    required_sequence.append(tool)
                elif tool in ["medication_query", "lab_order"]:
                    required_sequence.append(tool)
                elif tool == "lab_result_query":
                    required_sequence.append(tool)
                elif tool == "prescription_order":
                    required_sequence.append(tool)

            criteria["sequence_requirements"] = required_sequence

            # 添加红线测试
            if "red_line_tests" in workflow_info:
                criteria["red_line_conditions"] = workflow_info["red_line_tests"]

        return criteria

    def annotate_task(self, task: Dict) -> Dict:
        """标注单个任务"""
        # 检测场景类型
        scenario_type = self.detect_scenario_type(task)

        # 生成预期工作流
        expected_workflow = self.generate_expected_workflow(task, scenario_type)

        # 生成工具评估标准
        tool_criteria = self.generate_tool_evaluation_criteria(task, scenario_type)

        # 添加到任务中
        annotated_task = deepcopy(task)

        # 添加环境定义（工具定义）
        # 根据场景类型选择相关工具
        workflow_info = SCENARIO_WORKFLOWS.get(scenario_type, {})
        required_tools = workflow_info.get("required_tools", ["emr_query"])
        conditional_tools = workflow_info.get("conditional_tools", [])
        optional_tools = workflow_info.get("optional_tools", [])

        # 构建可用工具列表
        relevant_tools = {}
        for tool_name in required_tools + conditional_tools + optional_tools:
            if tool_name in AVAILABLE_TOOLS:
                relevant_tools[tool_name] = AVAILABLE_TOOLS[tool_name]

        annotated_task["environment"] = {
            "available_tools": relevant_tools,
            "scenario_type": scenario_type
        }

        # 添加预期的工作流
        annotated_task["expected_agent_workflow"] = expected_workflow

        # 添加工具调用评估标准
        annotated_task["tool_evaluation_criteria"] = tool_criteria

        # 更新 metadata
        if "metadata" not in annotated_task:
            annotated_task["metadata"] = {}
        annotated_task["metadata"]["version"] = "interactive_environment_v1"
        annotated_task["metadata"]["has_agent_workflow"] = True

        return annotated_task

    def annotate_all_tasks(self):
        """标注所有任务"""
        print(f"\n[2/5] 标注任务...")

        stats = {
            "total": len(self.tasks),
            "annotated": 0,
            "by_scenario": {},
            "by_difficulty": {"L1": 0, "L2": 0, "L3": 0}
        }

        for i, task in enumerate(self.tasks):
            # 标注任务
            self.tasks[i] = self.annotate_task(task)

            # 统计
            stats["annotated"] += 1
            scenario_type = self.tasks[i]["environment"]["scenario_type"]
            stats["by_scenario"][scenario_type] = stats["by_scenario"].get(scenario_type, 0) + 1
            difficulty = self.tasks[i].get("difficulty", "L1")
            stats["by_difficulty"][difficulty] += 1

            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(self.tasks)}")

        print(f"✓ 标注了 {stats['annotated']} 个任务")
        return stats

    def save_tasks(self):
        """保存任务"""
        print(f"\n[3/5] 保存任务...")
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)

        file_size_mb = self.output_file.stat().st_size / 1024 / 1024
        print(f"✓ 保存到: {self.output_file}")
        print(f"  文件大小: {file_size_mb:.1f} MB")

    def generate_report(self, stats: Dict):
        """生成报告"""
        print(f"\n[4/5] 生成报告...")

        print(f"\n{'='*60}")
        print(" Step 2 完成报告：动作标注")
        print(f"{'='*60}")

        print(f"\n总体统计:")
        print(f"  总任务数: {stats['total']}")
        print(f"  已标注: {stats['annotated']}")
        print(f"  标注率: 100%")

        print(f"\n按场景类型分布:")
        for scenario, count in sorted(stats["by_scenario"].items(), key=lambda x: -x[1]):
            print(f"  {scenario}: {count} ({count/stats['total']*100:.1f}%)")

        print(f"\n按难度分布:")
        for difficulty in ["L1", "L2", "L3"]:
            count = stats["by_difficulty"][difficulty]
            print(f"  {difficulty}: {count} ({count/stats['total']*100:.1f}%)")

        print(f"\n新增字段:")
        print(f"  1. environment.available_tools - 可用工具定义")
        print(f"  2. environment.scenario_type - 场景类型")
        print(f"  3. expected_agent_workflow - 预期的工作流")
        print(f"  4. tool_evaluation_criteria - 工具调用评估标准")

        print(f"\n下一步:")
        print(f"  Step 3: 创建API模拟器")
        print(f"  Step 4: 建立Agent测试框架")

    def show_sample_task(self):
        """显示示例任务"""
        print(f"\n[5/5] 示例任务...")

        # 找一个 L2 或 L3 的任务
        sample_task = next((t for t in self.tasks if t.get("difficulty") in ["L2", "L3"]), self.tasks[0])

        print(f"\n{'='*60}")
        print(f" 示例任务: {sample_task['id']}")
        print(f"{'='*60}")

        print(f"\n场景类型: {sample_task['environment']['scenario_type']}")
        print(f"难度: {sample_task.get('difficulty', 'N/A')}")
        print(f"Ticket: {sample_task['ticket'][:100]}...")

        print(f"\n可用工具 ({len(sample_task['environment']['available_tools'])}):")
        for tool_name in list(sample_task['environment']['available_tools'].keys())[:5]:
            tool = sample_task['environment']['available_tools'][tool_name]
            print(f"  - {tool_name}: {tool['description']}")

        print(f"\n预期工作流 ({len(sample_task['expected_agent_workflow'])} 步):")
        for step in sample_task['expected_agent_workflow'][:5]:
            print(f"  Step {step['step']}: {step['action']} - {step.get('purpose', 'N/A')}")

        print(f"\n工具评估标准:")
        criteria = sample_task['tool_evaluation_criteria']
        print(f"  必需工具: {criteria['required_tools']}")
        print(f"  条件工具: {criteria['conditional_tools']}")


def main():
    """主函数"""
    print("="*60)
    print(" Agent Action Annotator - Step 2")
    print("="*60)
    print("\n目标: 在现有数据基础上'标注'动作")
    print("  1. 添加 expected_agent_workflow")
    print("  2. 添加 available_tools")
    print("  3. 添加 tool_evaluation_criteria")
    print("="*60)

    # 文件路径
    input_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_realistic_v3.json"
    output_file = "data/tau2/domains/clinical/chinese_internal_medicine/tasks_with_agent_workflow.json"

    # 创建标注器
    annotator = AgentActionAnnotator(input_file, output_file)

    # 执行标注
    try:
        annotator.load_tasks()
        stats = annotator.annotate_all_tasks()
        annotator.save_tasks()
        annotator.generate_report(stats)
        annotator.show_sample_task()

        print(f"\n{'='*60}")
        print(" ✓ Step 2 完成！")
        print(f"{'='*60}")
        print(f"\n输出文件: {output_file}")
        print(f"\n核心改进:")
        print(f"  ✓ 添加预期的工作流（工具调用序列）")
        print(f"  ✓ 添加可用工具定义")
        print(f"  ✓ 添加工具调用评估标准")
        print(f"\n下一步: Step 3 - 创建API模拟器")

    except Exception as e:
        print(f"\n[错误] 标注失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    import io

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 运行标注
    main()
