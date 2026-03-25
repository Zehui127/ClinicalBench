#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗评估系统测试脚本

测试 tau2 框架中的医疗评估功能是否正常工作。
此脚本不需要实际的 LLM API 调用，仅测试导入和基本结构。
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """测试所有必要的导入是否正常"""
    print("=" * 70)
    print("测试 1: 导入检查")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # 测试 1.1: 导入 RewardType.CLINICAL
    try:
        from tau2.data_model.tasks import RewardType
        assert hasattr(RewardType, 'CLINICAL'), "RewardType.CLINICAL 不存在"
        assert RewardType.CLINICAL == "CLINICAL"
        print("[OK] RewardType.CLINICAL 导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] RewardType.CLINICAL 导入失败: {e}")
        tests_failed += 1

    # 测试 1.2: 导入 ClinicalCheck
    try:
        from tau2.data_model.simulation import ClinicalCheck
        print("[OK] ClinicalCheck 导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalCheck 导入失败: {e}")
        tests_failed += 1

    # 测试 1.3: 导入三个医疗评估器
    try:
        from tau2.evaluator import (
            ClinicalAccuracyEvaluator,
            DialogueFluencyEvaluator,
            SafetyEmpathyEvaluator,
        )
        print("[OK] 三个维度评估器导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] 维度评估器导入失败: {e}")
        tests_failed += 1

    # 测试 1.4: 导入 ClinicalEvaluator
    try:
        from tau2.evaluator import ClinicalEvaluator
        print("[OK] ClinicalEvaluator 导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalEvaluator 导入失败: {e}")
        tests_failed += 1

    # 测试 1.5: 导入 EvaluationType
    try:
        from tau2.evaluator.evaluator import EvaluationType
        assert hasattr(EvaluationType, 'CLINICAL'), "EvaluationType.CLINICAL 不存在"
        assert hasattr(EvaluationType, 'ALL_WITH_CLINICAL'), "EvaluationType.ALL_WITH_CLINICAL 不存在"
        print("[OK] EvaluationType.CLINICAL 和 ALL_WITH_CLINICAL 导入成功")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] EvaluationType 导入失败: {e}")
        tests_failed += 1

    print(f"\n导入测试完成: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0


def test_data_models():
    """测试数据模型结构"""
    print("\n" + "=" * 70)
    print("测试 2: 数据模型结构")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # 测试 2.1: 创建 ClinicalCheck 实例
    try:
        from tau2.data_model.simulation import ClinicalCheck

        check = ClinicalCheck(
            overall_score=4.2,
            dimension_scores={
                "clinical_accuracy": {
                    "medical_knowledge": {"score": 4.0, "reasoning": "知识准确"},
                    "diagnostic_reasoning": {"score": 4.5, "reasoning": "推理合理"},
                },
                "dialogue_fluency": {
                    "question_understanding": {"score": 4.0, "reasoning": "理解准确"},
                },
                "safety_empathy": {
                    "safety_awareness": {"score": 5.0, "reasoning": "安全意识强"},
                },
            },
            met=True,
            reward=0.84,
            strengths=["医学知识准确", "安全意识强"],
            weaknesses=["可以更详细"],
            suggestions=["增加更多细节"],
            comments="测试评语",
        )
        print("[OK] ClinicalCheck 实例创建成功")
        print(f"  - 总分: {check.overall_score}")
        print(f"  - 通过: {check.met}")
        print(f"  - 奖励: {check.reward}")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalCheck 实例创建失败: {e}")
        tests_failed += 1

    # 测试 2.2: RewardInfo 包含 clinical_checks 字段
    try:
        from tau2.data_model.simulation import RewardInfo, ClinicalCheck

        check = ClinicalCheck(
            overall_score=4.2,
            dimension_scores={},
            met=True,
            reward=0.84,
        )

        reward_info = RewardInfo(
            reward=0.84,
            clinical_checks=[check],
            reward_basis=["CLINICAL"],
        )
        assert reward_info.clinical_checks is not None
        assert len(reward_info.clinical_checks) == 1
        print("[OK] RewardInfo.clinical_checks 字段正常")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] RewardInfo.clinical_checks 字段测试失败: {e}")
        tests_failed += 1

    print(f"\n数据模型测试完成: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0


def test_evaluator_structure():
    """测试评估器结构"""
    print("\n" + "=" * 70)
    print("测试 3: 评估器结构")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # 测试 3.1: ClinicalEvaluator 继承自 EvaluatorBase
    try:
        from tau2.evaluator import ClinicalEvaluator
        from tau2.evaluator.evaluator_base import EvaluatorBase

        assert issubclass(ClinicalEvaluator, EvaluatorBase)
        print("[OK] ClinicalEvaluator 继承自 EvaluatorBase")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalEvaluator 继承测试失败: {e}")
        tests_failed += 1

    # 测试 3.2: ClinicalEvaluator 有 calculate_reward 方法
    try:
        from tau2.evaluator import ClinicalEvaluator

        assert hasattr(ClinicalEvaluator, 'calculate_reward')
        print("[OK] ClinicalEvaluator.calculate_reward 方法存在")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalEvaluator.calculate_reward 方法检查失败: {e}")
        tests_failed += 1

    # 测试 3.3: 检查评估器初始化
    try:
        from tau2.evaluator import ClinicalEvaluator

        # 注意：这不实际调用 LLM，只测试初始化
        evaluator = ClinicalEvaluator(
            model="gpt-4",
            weights={"clinical_accuracy": 0.5, "dialogue_fluency": 0.25, "safety_empathy": 0.25},
            pass_threshold=3.5,
        )
        assert evaluator.model == "gpt-4"
        assert evaluator.weights["clinical_accuracy"] == 0.5
        assert evaluator.pass_threshold == 3.5
        print("[OK] ClinicalEvaluator 初始化成功")
        print(f"  - 模型: {evaluator.model}")
        print(f"  - 权重: {evaluator.weights}")
        print(f"  - 阈值: {evaluator.pass_threshold}")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] ClinicalEvaluator 初始化失败: {e}")
        tests_failed += 1

    print(f"\n评估器结构测试完成: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0


def test_evaluation_type():
    """测试评估类型枚举"""
    print("\n" + "=" * 70)
    print("测试 4: 评估类型")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    try:
        from tau2.evaluator.evaluator import EvaluationType

        # 检查 CLINICAL 类型
        assert EvaluationType.CLINICAL == "clinical"
        print("[OK] EvaluationType.CLINICAL = 'clinical'")

        # 检查 ALL_WITH_CLINICAL 类型
        assert EvaluationType.ALL_WITH_CLINICAL == "all_with_clinical"
        print("[OK] EvaluationType.ALL_WITH_CLINICAL = 'all_with_clinical'")

        # 检查枚举值
        expected_types = {
            "ENV", "COMMUNICATE", "ACTION", "ALL",
            "NL_ASSERTIONS", "ALL_WITH_NL_ASSERTIONS",
            "CLINICAL", "ALL_WITH_CLINICAL"
        }
        actual_types = {e.value for e in EvaluationType}

        missing = expected_types - actual_types
        if missing:
            print(f"[WARN] 缺少评估类型: {missing}")

        extra = actual_types - expected_types
        if extra:
            print(f"[INFO] 额外的评估类型: {extra}")

        print(f"[OK] 评估类型枚举检查通过")
        tests_passed += 1

    except Exception as e:
        print(f"[FAIL] 评估类型测试失败: {e}")
        tests_failed += 1

    print(f"\n评估类型测试完成: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0


def test_integration():
    """测试与 tau2 框架的集成"""
    print("\n" + "=" * 70)
    print("测试 5: 框架集成")
    print("=" * 70)

    tests_passed = 0
    tests_failed = 0

    # 测试 5.1: 检查 evaluate_simulation 函数支持 CLINICAL
    try:
        from tau2.evaluator.evaluator import evaluate_simulation, EvaluationType
        from tau2.data_model.tasks import RewardType

        # 验证 CLINICAL 在 RewardType 中
        assert RewardType.CLINICAL in RewardType._value2member_map_
        print("[OK] RewardType.CLINICAL 已注册")

        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] 框架集成测试失败: {e}")
        tests_failed += 1

    # 测试 5.2: 检查导入路径
    try:
        from tau2.evaluator import (
            EvaluatorBase,
            ClinicalEvaluator,
            ClinicalAccuracyEvaluator,
            DialogueFluencyEvaluator,
            SafetyEmpathyEvaluator,
        )
        print("[OK] 所有评估器可从 tau2.evaluator 导入")
        tests_passed += 1
    except Exception as e:
        print(f"[FAIL] 导入路径测试失败: {e}")
        tests_failed += 1

    print(f"\n框架集成测试完成: {tests_passed} 通过, {tests_failed} 失败")
    return tests_failed == 0


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("Tau2 医疗评估系统测试")
    print("=" * 70)
    print()

    all_passed = True

    # 运行所有测试
    all_passed &= test_imports()
    all_passed &= test_data_models()
    all_passed &= test_evaluator_structure()
    all_passed &= test_evaluation_type()
    all_passed &= test_integration()

    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)

    if all_passed:
        print("[SUCCESS] 所有测试通过!")
        print("\nTau2 医疗评估系统已成功集成。")
        print("您现在可以使用:")
        print("  - from tau2.evaluator import ClinicalEvaluator")
        print("  - from tau2.data_model.tasks import RewardType")
        print("  - RewardType.CLINICAL")
        print("  - EvaluationType.CLINICAL")
        print("  - EvaluationType.ALL_WITH_CLINICAL")
        return 0
    else:
        print("[FAIL] 部分测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
