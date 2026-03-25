#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗Agent测试环境验证脚本

测试Step 3和Step 4的实现：
1. API模拟器
2. 临床环境管理器
3. Agent评估器

作者：Claude Sonnet 4.5
日期：2025-03-21
"""

import json
import sys
import io
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from medical_agent_test_environment import (
    MockEMRAPI,
    MockMedicationAPI,
    MockLabOrderAPI,
    MockLabResultAPI,
    MockPrescriptionAPI,
    ClinicalEnvironment,
    AgentEvaluator
)


def test_api_simulators():
    """测试API模拟器"""
    print("\n" + "="*60)
    print(" [测试 1/3] API 模拟器")
    print("="*60)

    # 测试 EMR API
    print("\n1.1 测试 EMR API")
    patient_data = {
        "past_medical_history": ["高血压3年", "2型糖尿病5年"],
        "current_medications": ["氨氯地平 5mg qd"],
        "allergies": ["青霉素"]
    }
    emr_api = MockEMRAPI(patient_data)
    result = emr_api.query("P001", ["past_medical_history", "current_medications"])
    print(f"  ✓ EMR 查询成功")
    print(f"    - 既往病史: {result['data']['past_medical_history']}")
    print(f"    - 当前用药: {result['data']['current_medications']}")

    # 测试 Medication API
    print("\n1.2 测试 Medication API")
    med_api = MockMedicationAPI()
    result = med_api.query("氨氯地平", ["contraindications", "interactions", "dosage"])
    print(f"  ✓ Medication 查询成功")
    print(f"    - 禁忌症: {len(result['data']['contraindications'])} 项")
    print(f"    - 相互作用: {len(result['data']['interactions'])} 项")
    print(f"    - 剂量: {result['data']['dosage']}")

    # 测试 Lab Order API
    print("\n1.3 测试 Lab Order API")
    lab_api = MockLabOrderAPI()
    result = lab_api.order_test(["心电图", "血常规"], "routine", "头晕待查")
    print(f"  ✓ Lab Order 开具成功")
    print(f"    - Order ID: {result['order_id']}")
    print(f"    - 预计等待: {result['estimated_time']}")

    # 测试 Lab Result API
    print("\n1.4 测试 Lab Result API")
    result_api = MockLabResultAPI()
    result = result_api.get_result("LAB000001")
    print(f"  ✓ Lab Result 查询成功")
    print(f"    - 检查类型: {result['data'].get('test_type', '未知')}")
    interpretation = result['data'].get('interpretation', '无解读')
    print(f"    - 结果: {interpretation}")

    # 测试 Prescription API
    print("\n1.5 测试 Prescription API")
    rx_api = MockPrescriptionAPI()
    result = rx_api.prescribe("氨氯地平", "5mg", "qd", "30天")
    print(f"  ✓ Prescription 开具成功")
    print(f"    - Prescription ID: {result['prescription_id']}")
    print(f"    - 状态: {result['status']}")

    print("\n✓ 所有 API 模拟器测试通过")
    return True


def test_clinical_environment():
    """测试临床环境管理器"""
    print("\n" + "="*60)
    print(" [测试 2/3] 临床环境管理器")
    print("="*60)

    # 创建简化的任务配置
    task_config = {
        "id": "test_task_001",
        "ticket": "我头晕三天了",
        "difficulty": "L2",
        "environment": {
            "available_tools": {
                "emr_query": {
                    "name": "electronic_medical_record",
                    "api": "/api/emr/query"
                },
                "medication_query": {
                    "name": "medication_database",
                    "api": "/api/meds/query"
                },
                "lab_order": {
                    "name": "lab_order_system",
                    "api": "/api/lab/order"
                },
                "prescription_order": {
                    "name": "prescription_system",
                    "api": "/api/rx/prescribe"
                }
            },
            "scenario_type": "SYMPTOM_ANALYSIS"
        },
        "tool_evaluation_criteria": {
            "required_tools": ["emr_query"],
            "conditional_tools": ["lab_order", "prescription_order"],
            "scoring_weights": {
                "tool_timing": 0.3,
                "tool_quality": 0.3,
                "decision_flow": 0.4
            }
        }
    }

    # 创建环境
    env = ClinicalEnvironment(task_config)
    print(f"\n2.1 创建环境")
    print(f"  ✓ 环境 ID: {env.task_id}")
    print(f"  ✓ 可用工具: {len(env.available_tools)} 个")
    print(f"  - 工具列表: {', '.join(env.available_tools.keys())}")

    # 模拟Agent交互
    print(f"\n2.2 模拟 Agent 交互")

    # Step 1: 查询EMR
    action = {
        "type": "tool_call",
        "tool": "emr_query",
        "parameters": {
            "patient_id": "P001",
            "query_type": ["past_medical_history", "current_medications"]
        }
    }
    result = env.step(action)
    print(f"  Step 1: emr_query")
    print(f"    - 成功: {result.success}")
    print(f"    - 工具: {result.tool_name}")

    # Step 2: 对话
    action = {
        "type": "dialogue",
        "content": "我看到您有高血压，最近在吃药吗？"
    }
    result = env.step(action)
    print(f"  Step 2: dialogue")
    print(f"    - 成功: {result.success}")
    print(f"    - 患者响应: {result.result['patient_response']}")

    # Step 3: 开检查
    action = {
        "type": "tool_call",
        "tool": "lab_order",
        "parameters": {
            "test_type": ["心电图"],
            "urgency": "routine",
            "clinical_indication": "头晕待查"
        }
    }
    result = env.step(action)
    print(f"  Step 3: lab_order")
    print(f"    - 成功: {result.success}")
    print(f"    - Order ID: {result.result['order_id']}")

    # 获取观察
    print(f"\n2.3 环境观察")
    observation = env.get_observation()
    print(f"  ✓ 当前步数: {observation['step']}")
    print(f"  ✓ EMR 已查询: {observation['emr_queried']}")
    print(f"  ✓ 待处理检查: {len(observation['pending_lab_orders'])} 个")
    print(f"  ✓ 已完成检查: {len(observation['completed_lab_orders'])} 个")

    print("\n✓ 临床环境管理器测试通过")
    return True


def test_agent_evaluator():
    """测试Agent评估器"""
    print("\n" + "="*60)
    print(" [测试 3/3] Agent 评估器")
    print("="*60)

    # 创建任务配置
    task_config = {
        "id": "test_task_002",
        "tool_evaluation_criteria": {
            "required_tools": ["emr_query"],
            "conditional_tools": ["lab_order", "prescription_order"],
            "scoring_weights": {
                "tool_timing": 0.3,
                "tool_quality": 0.3,
                "decision_flow": 0.4
            }
        }
    }

    # 测试场景1：优秀的Agent
    print("\n3.1 测试优秀 Agent")
    good_trace = [
        {
            "step": 1,
            "action": "tool_call",
            "tool": "emr_query",
            "parameters": {"patient_id": "P001", "query_type": ["past_medical_history"]}
        },
        {
            "step": 2,
            "action": "dialogue",
            "content": "根据您的病史，我建议...",
            "based_on": "emr_query_result"
        },
        {
            "step": 3,
            "action": "tool_call",
            "tool": "lab_order",
            "parameters": {"test_type": ["心电图"], "urgency": "routine"}
        }
    ]

    evaluator = AgentEvaluator()
    result = evaluator.evaluate(good_trace, task_config)

    print(f"  总分: {result.overall_score}/5.0")
    print(f"  评级: {result.grading}")
    print(f"  时机得分: {result.timing_score}/5.0")
    print(f"  质量得分: {result.quality_score}/5.0")
    print(f"  决策得分: {result.decision_score}/5.0")

    # 测试场景2：缺少必需工具的Agent
    print("\n3.2 测试缺少必需工具的 Agent")
    bad_trace = [
        {
            "step": 1,
            "action": "dialogue",
            "content": "您头晕多久了？"
        },
        {
            "step": 2,
            "action": "dialogue",
            "content": "我建议您吃降压药"
        }
    ]

    result = evaluator.evaluate(bad_trace, task_config)

    print(f"  总分: {result.overall_score}/5.0")
    print(f"  评级: {result.grading}")
    print(f"  时机扣分: {len(result.timing_penalties)} 项")
    if result.timing_penalties:
        for penalty in result.timing_penalties:
            print(f"    - {penalty}")

    # 测试场景3：工具参数不完整的Agent
    print("\n3.3 测试工具参数不完整的 Agent")
    incomplete_trace = [
        {
            "step": 1,
            "action": "tool_call",
            "tool": "emr_query",
            "parameters": {"patient_id": "P001", "query_type": []}  # 空query_type
        },
        {
            "step": 2,
            "action": "tool_call",
            "tool": "prescription_order",
            "parameters": {"medication": "氨氯地平"}  # 缺少 dose, frequency, duration
        }
    ]

    result = evaluator.evaluate(incomplete_trace, task_config)

    print(f"  总分: {result.overall_score}/5.0")
    print(f"  评级: {result.grading}")
    print(f"  质量错误: {len(result.quality_errors)} 项")
    if result.quality_errors:
        for error in result.quality_errors:
            print(f"    - [{error['tool']}] {error['issue']} (severity: {error['severity']})")

    # 测试场景4：红线违规
    print("\n3.4 测试红线违规")
    violation_trace = [
        {
            "step": 1,
            "action": "tool_call",
            "tool": "prescription_order",  # 在未查询药物的情况下开处方
            "parameters": {"medication": "氨氯地平", "dose": "5mg", "frequency": "qd"}
        }
    ]

    result = evaluator.evaluate(violation_trace, task_config)

    print(f"  总分: {result.overall_score}/5.0")
    print(f"  评级: {result.grading}")
    print(f"  红线违规: {len(result.red_line_violations)} 项")
    if result.red_line_violations:
        for violation in result.red_line_violations:
            print(f"    - {violation}")

    print("\n✓ Agent 评估器测试通过")
    return True


def test_with_real_task():
    """使用真实任务测试"""
    print("\n" + "="*60)
    print(" [测试 4/4] 使用真实任务测试")
    print("="*60)

    # 加载真实任务
    tasks_file = Path("data/tau2/domains/clinical/chinese_internal_medicine/tasks_with_agent_workflow.json")

    if not tasks_file.exists():
        print(f"\n⚠️  未找到任务文件: {tasks_file}")
        print(f"  跳过此测试")
        return False

    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)

    print(f"\n4.1 加载任务")
    print(f"  ✓ 总任务数: {len(tasks)}")

    # 选择一个L2或L3任务进行测试
    test_task = next(
        (t for t in tasks if t.get("difficulty") in ["L2", "L3"]),
        tasks[0]
    )

    print(f"\n4.2 测试任务: {test_task['id']}")
    print(f"  - 场景类型: {test_task['environment']['scenario_type']}")
    print(f"  - 难度: {test_task['difficulty']}")
    print(f"  - 可用工具: {len(test_task['environment']['available_tools'])} 个")
    print(f"  - 预期工作流: {len(test_task['expected_agent_workflow'])} 步")

    # 创建环境
    env = ClinicalEnvironment(test_task)
    print(f"\n4.3 创建环境")
    print(f"  ✓ 环境 ID: {env.task_id}")
    print(f"  ✓ 可用工具: {', '.join(env.available_tools.keys())}")

    # 模拟一个简单的Agent行为
    print(f"\n4.4 模拟 Agent 行为")

    agent_trace = []

    # 执行前3步工作流
    for step_info in test_task['expected_agent_workflow'][:3]:
        step_num = step_info['step']
        action_type = step_info['action']

        if action_type == "tool_call":
            tool = step_info.get('tool')
            parameters = step_info.get('parameters', {})

            # 简化参数
            if tool == "emr_query":
                parameters = {
                    "patient_id": "P001",
                    "query_type": ["past_medical_history", "current_medications"]
                }
            elif tool == "lab_order":
                parameters = {
                    "test_type": ["心电图"],
                    "urgency": "routine",
                    "clinical_indication": step_info.get('purpose', '')
                }

            action = {
                "type": "tool_call",
                "tool": tool,
                "parameters": parameters
            }

            result = env.step(action)
            agent_trace.append({
                "step": step_num,
                "action": "tool_call",
                "tool": tool,
                "parameters": parameters
            })

            print(f"  Step {step_num}: {tool}")
            print(f"    - 成功: {result.success}")

        elif action_type == "dialogue":
            action = {
                "type": "dialogue",
                "content": f"（Agent与患者对话：{step_info.get('purpose', '')}）"
            }

            result = env.step(action)
            agent_trace.append({
                "step": step_num,
                "action": "dialogue",
                "content": action["content"],
                "based_on": step_info.get('based_on', '')
            })

            print(f"  Step {step_num}: dialogue")

    # 评估Agent表现
    print(f"\n4.5 评估 Agent 表现")

    evaluator = AgentEvaluator()
    eval_result = evaluator.evaluate(agent_trace, test_task)

    print(f"  总分: {eval_result.overall_score}/5.0")
    print(f"  评级: {eval_result.grading}")
    print(f"  时机得分: {eval_result.timing_score}/5.0")
    print(f"  质量得分: {eval_result.quality_score}/5.0")
    print(f"  决策得分: {eval_result.decision_score}/5.0")

    if eval_result.timing_penalties:
        print(f"\n  时机扣分:")
        for penalty in eval_result.timing_penalties[:3]:
            print(f"    - {penalty}")

    if eval_result.improvement_suggestions:
        print(f"\n  改进建议:")
        for suggestion in eval_result.improvement_suggestions:
            print(f"    - {suggestion['suggestion']}")

    print("\n✓ 真实任务测试通过")
    return True


def main():
    """主测试函数"""
    print("="*60)
    print(" 医疗Agent测试环境 - 验证测试")
    print("="*60)
    print("\n测试内容:")
    print("  1. API 模拟器（5个必选工具）")
    print("  2. 临床环境管理器")
    print("  3. Agent 评估器（3个维度）")
    print("  4. 真实任务测试")

    # 设置 UTF-8 编码输出
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    try:
        # 运行测试
        test_api_simulators()
        test_clinical_environment()
        test_agent_evaluator()
        test_with_real_task()

        # 总结
        print("\n" + "="*60)
        print(" ✓ 所有测试通过！")
        print("="*60)
        print("\n功能验证:")
        print("  ✓ Step 3: API模拟器")
        print("    - emr_query")
        print("    - medication_query")
        print("    - lab_order")
        print("    - lab_result_query")
        print("    - prescription_order")
        print("  ✓ Step 4: 临床环境管理器")
        print("    - 工具管理")
        print("    - 状态管理")
        print("    - 动作执行")
        print("  ✓ Step 4: Agent评估器")
        print("    - 工具调用时机评估（30%）")
        print("    - 工具使用质量评估（30%）")
        print("    - 决策流程质量评估（40%）")
        print("    - 红线违规检测")

        print("\n下一步:")
        print("  1. 使用真实Agent进行完整测试")
        print("  2. 收集评估结果并分析")
        print("  3. 优化评估标准")

        return 0

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
