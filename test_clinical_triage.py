#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试临床分诊模块"""
import sys
import json
from pathlib import Path

# 设置UTF-8编码输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from DataQualityFiltering.modules.clinical_triage import (
    analyze_patient_questions,
    QuestionPrioritizer,
    CrossDepartmentDetector
)


def test_cross_department_detection():
    """测试跨科室识别"""
    print("="*60)
    print("测试1: 跨科室识别")
    print("="*60)

    detector = CrossDepartmentDetector()

    test_questions = [
        "我眼睛看不清楚",
        "最近失眠睡不着",
        "皮肤很痒",
        "血压高",
        "牙齿痛"
    ]

    for question in test_questions:
        dept, confidence, urgent = detector.detect_department(question)
        print(f"\n问题: {question}")
        print(f"  识别科室: {dept}")
        print(f"  置信度: {confidence:.2f}")
        print(f"  是否紧急: {urgent}")


def test_question_prioritization():
    """测试问题优先级判断"""
    print("\n" + "="*60)
    print("测试2: 问题优先级判断")
    print("="*60)

    # 真实场景：内科患者问多个问题
    ticket = "我有高血压这两天女婿来的时候给我拿了些党参泡水喝，您好高血压可以吃党参吗？我眼睛也有点花，是不是老花眼？还需要做什么检查吗？我最近睡眠也不好，经常失眠，会不会抑郁？"

    print(f"\n患者问题: {ticket}")
    print(f"当前科室: 内科")

    result = analyze_patient_questions(ticket, "内科")

    print("\n" + "="*60)
    print("分诊结果")
    print("="*60)

    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_emergency_detection():
    """测试紧急情况识别"""
    print("\n" + "="*60)
    print("测试3: 紧急情况识别")
    print("="*60)

    emergency_questions = [
        "胸痛呼吸困难，能吃心脏病药吗？",
        "宝宝高烧不退还抽搐了",
        "突然看不见了"
    ]

    for question in emergency_questions:
        dept, confidence, urgent = CrossDepartmentDetector().detect_department(question)
        print(f"\n问题: {question}")
        print(f"  识别科室: {dept}")
        print(f"  置信度: {confidence:.2f}")
        print(f"  是否紧急: {urgent}")
        if urgent:
            print("  【警告】这是紧急情况，需要立即处理！")


def test_real_scenario():
    """测试真实临床场景"""
    print("\n" + "="*60)
    print("测试4: 真实临床场景（完整流程）")
    print("="*60)

    # 场景：焦虑的内科患者
    scenario = {
        "patient_complaint": "我今天血压测出来160/100，有点担心。我有高血压能不能吃党参？我眼睛最近总是花，看不清东西，是不是老花眼？我最近睡眠也不好，经常失眠，会不会抑郁？我邻居说我心脏不好，要不要做检查？",
        "current_dept": "内科",
        "patient_state": "焦虑，多问"
    }

    print(f"\n场景描述: {scenario['patient_complaint']}")
    print(f"患者状态: {scenario['patient_state']}")
    print(f"当前科室: {scenario['current_dept']}")

    # 分析问题
    result = analyze_patient_questions(scenario['patient_complaint'], scenario['current_dept'])

    print("\n" + "="*60)
    print("分诊结果")
    print("="*60)

    # 提取关键信息
    priority_analysis = result.get('priority_analysis', {})
    referral_recommendations = result.get('referral_recommendations', [])

    print(f"\n📊 问题分析:")
    print(f"  - 核心问题: {len(priority_analysis.get('core_questions', []))}个")
    print(f"  - 当前科室问题: {priority_analysis.get('current_dept_questions', 0)}个")
    print(f"  - 其他科室问题: {priority_analysis.get('other_dept_questions', 0)}个")

    print(f"\n❓ 追问策略:")
    inquiry_strategy = result.get('inquiry_strategy', {})
    must_ask = inquiry_strategy.get('must_ask', [])
    print(f"  必须问的问题 ({len(must_ask)}个):")
    for i, q in enumerate(must_ask[:3], 1):
        print(f"    {i}. {q}")

    print(f"\n🏥 转诊建议:")
    for i, ref in enumerate(referral_recommendations, 1):
        print(f"  {i}. 问题: {ref['question']}")
        print(f"     目标科室: {ref['target_dept']}")
        print(f"     建议: {ref['advice']}")

    print(f"\n⚠️ 评估规则:")
    for rule in result.get('evaluation_rules', []):
        print(f"  - {rule}")


if __name__ == "__main__":
    test_cross_department_detection()
    test_question_prioritization()
    test_emergency_detection()
    test_real_scenario()

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
