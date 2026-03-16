#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无需 LLM 的测试脚本

用于测试数据质量验证和过滤功能，不需要调用大模型 API。
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from DataQualityFiltering.data_quality import (
    QualityFilter,
    FilterConfig,
    MedicalDialogueValidator,
)


def test_data_validation():
    """测试数据验证（无需 LLM）"""
    print("=" * 70)
    print("测试 1: 医学对话数据验证")
    print("=" * 70)

    # 创建测试数据
    test_task = {
        "task_id": "test_001",
        "instruction": "模拟医生问诊，收集患者信息",
        "environment": {
            "medical_dialogue": {
                "patient_question": "医生，我最近总是感觉疲劳，而且体重下降明显",
                "doctor_response": "您好！请问您的疲劳感持续多久了？体重下降了多少斤？有没有其他症状如发热、盗汗等？",
                "dialogue_type": "consultation"
            }
        },
        "tool_calls": [
            {"tool": "ask_symptom", "parameters": {"symptom": "fatigue"}},
            {"tool": "ask_duration", "parameters": {"duration": "2_weeks"}},
            {"tool": "ask_history", "parameters": {"history": "weight_loss"}}
        ],
        "content": "患者主诉疲劳和体重下降，进行了症状询问和病史采集。"
    }

    # 验证数据
    validator = MedicalDialogueValidator()
    is_valid, errors = validator.validate(test_task)

    print(f"\n✅ 验证结果: {'通过' if is_valid else '失败'}")

    if errors:
        print(f"\n❌ 错误信息:")
        for error in errors:
            print(f"  - {error}")
    else:
        print(f"\n✅ 数据格式正确，所有字段完整")

    return is_valid


def test_quality_scoring():
    """测试质量评分（无需 LLM）"""
    print("\n" + "=" * 70)
    print("测试 2: 数据质量评分")
    print("=" * 70)

    # 创建测试数据
    test_task = {
        "task_id": "test_002",
        "tool_calls": [
            {"tool": "ask_symptom"},
            {"tool": "check_vital_signs"},
            {"tool": "diagnose"},
            {"tool": "prescribe_medication"},
            {"tool": "follow_up"}
        ],
        "content": """
        患者主诉头痛，伴随恶心。医生进行了详细的症状询问，
        检查了生命体征，初步诊断为紧张性头痛，开具了止痛药物，
        并嘱咐患者注意休息，如有加重及时复诊。整个诊疗过程规范，
        建议合理。
        """ * 5  # 重复以增加长度
    }

    # 配置过滤器
    config = FilterConfig(
        min_quality_score=3.5,
        min_tool_count=1,
        max_tool_count=8,
        min_content_length=50,
    )

    # 计算质量分数
    filter_engine = QualityFilter(config)
    score = filter_engine.calculate_quality_score(test_task)

    # 分析各项指标
    tool_count = len(test_task["tool_calls"])
    content_length = len(test_task["content"])

    print(f"\n📊 质量分析:")
    print(f"  - 工具数量: {tool_count} (要求: {config.min_tool_count}-{config.max_tool_count})")
    print(f"  - 内容长度: {content_length} 字符 (要求: >{config.min_content_length})")
    print(f"  - 质量分数: {score:.2f}/5.0 (阈值: {config.min_quality_score})")

    if score >= config.min_quality_score:
        print(f"\n✅ 质量达标 (分数: {score:.2f} >= {config.min_quality_score})")
    else:
        print(f"\n❌ 质量不达标 (分数: {score:.2f} < {config.min_quality_score})")

    return score >= config.min_quality_score


def test_batch_filtering():
    """测试批量过滤（无需 LLM）"""
    print("\n" + "=" * 70)
    print("测试 3: 批量数据过滤")
    print("=" * 70)

    # 创建测试数据集
    tasks = [
        {
            "task_id": f"task_{i:03d}",
            "tool_calls": [{"tool": f"tool_{j}"} for j in range(i % 8)],
            "content": f"这是第 {i} 个任务的内容。" * (i * 10)
        }
        for i in range(1, 11)
    ]

    # 配置过滤器
    config = FilterConfig(min_quality_score=3.5)
    filter_engine = QualityFilter(config)

    # 过滤数据
    print(f"\n📋 原始数据: {len(tasks)} 个任务")

    accepted = []
    rejected = []

    for task in tasks:
        score = filter_engine.calculate_quality_score(task)
        task["quality_score"] = score

        if score >= config.min_quality_score:
            accepted.append(task)
        else:
            rejected.append(task)

    print(f"\n✅ 通过: {len(accepted)} 个任务")
    print(f"❌ 拒绝: {len(rejected)} 个任务")
    print(f"📊 通过率: {len(accepted)/len(tasks)*100:.1f}%")

    # 显示通过的任务
    if accepted:
        print(f"\n✅ 通过的任务:")
        for task in accepted[:5]:  # 只显示前5个
            print(f"  - {task['task_id']}: {task['quality_score']:.2f}")

    # 显示拒绝的任务
    if rejected:
        print(f"\n❌ 拒绝的任务:")
        for task in rejected[:5]:
            print(f"  - {task['task_id']}: {task['quality_score']:.2f}")

    return len(accepted), len(rejected)


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("DataQualityFiltering - 无需 LLM 的功能测试")
    print("=" * 70)

    results = []

    # 运行测试
    try:
        results.append(("数据验证", test_data_validation()))
        results.append(("质量评分", test_quality_scoring()))
        results.append(("批量过滤", test_batch_filtering()))
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！系统可以正常使用。")
        print("\n💡 提示:")
        print("  - 这些功能无需调用 LLM，可以立即使用")
        print("  - 如需使用 LLM 自动审查或 Agent 评估功能，请配置 API 密钥")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
