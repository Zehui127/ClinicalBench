#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量阈值筛选系统测试脚本
验证所有模块的正常工作
"""

import sys
import os

# 添加当前目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_scoring_system():
    """测试评分系统"""
    logger.info("=" * 60)
    logger.info("测试 1: 评分系统")
    logger.info("=" * 60)

    from scoring import ExtendedScoringSystem, ScoringConfig

    # 创建评分系统
    config = ScoringConfig()
    scoring_system = ExtendedScoringSystem(config)

    # 测试 5 分制转换
    scores_5_point = {
        "clinical_accuracy": 4.5,
        "scenario_realism": 4.2,
        "evaluation_completeness": 4.8,
        "difficulty_appropriateness": 4.0
    }

    extended_scores = scoring_system.convert_from_5_point_scale(scores_5_point)
    total_score = scoring_system.calculate_total_score(extended_scores)
    quality_level = scoring_system.classify_quality(total_score, extended_scores)

    logger.info(f"原始分数 (5分制): {scores_5_point}")
    logger.info(f"扩展分数: {extended_scores}")
    logger.info(f"总分: {total_score}/30")
    logger.info(f"质量等级: {quality_level}")

    assert total_score > 0, "总分应该大于 0"
    assert quality_level in ["HIGH", "MEDIUM", "LOW"], "质量等级应该有效"

    logger.info("✅ 评分系统测试通过\n")
    return True


def test_quality_classifier():
    """测试质量分级器"""
    logger.info("=" * 60)
    logger.info("测试 2: 质量分级器")
    logger.info("=" * 60)

    from scoring import ExtendedScoringSystem
    from quality_classifier import QualityClassifier

    # 创建分级器
    scoring_system = ExtendedScoringSystem()
    classifier = QualityClassifier(scoring_system)

    # 测试任务
    test_task = {
        "id": "test_task_001",
        "description": "测试任务"
    }

    # 测试分数
    scores = {
        "clinical_accuracy": 9.0,
        "scenario_realism": 7.0,
        "evaluation_completeness": 6.0,
        "difficulty_appropriateness": 5.0
    }

    # 分级
    result = classifier.classify(test_task, scores)

    logger.info(f"任务 ID: {result.task_id}")
    logger.info(f"总分: {result.total_score}/30")
    logger.info(f"质量等级: {result.quality_level}")
    logger.info(f"处理动作: {result.action}")

    assert result.task_id == "test_task_001", "任务 ID 应该匹配"
    assert result.action in ["KEEP", "IMPROVE", "REJECT"], "处理动作应该有效"

    logger.info("✅ 质量分级器测试通过\n")
    return True


def test_task_improver():
    """测试任务改进器"""
    logger.info("=" * 60)
    logger.info("测试 3: 任务改进器")
    logger.info("=" * 60)

    from scoring import ExtendedScoringSystem
    from quality_classifier import QualityClassifier, QualityClassificationResult
    from improver import TaskImprover

    # 创建改进器
    scoring_system = ExtendedScoringSystem()
    improver = TaskImprover(scoring_system)

    # 测试任务
    test_task = {
        "id": "test_task_002",
        "description": "测试任务",
        "user_scenario": {"instructions": {}},
        "evaluation_criteria": {"nl_assertions": []}
    }

    # 创建中等质量的分级结果
    scores = {
        "clinical_accuracy": 7.5,
        "scenario_realism": 6.0,
        "evaluation_completeness": 5.0,
        "difficulty_appropriateness": 4.0
    }

    classification = QualityClassificationResult(
        task_id="test_task_002",
        total_score=22.5,
        quality_level="MEDIUM",
        dimension_scores=scores,
        action="IMPROVE",
        reasons=["总分在中等等级"]
    )

    # 改进任务
    result = improver.improve_medium_quality_task(test_task, classification)

    logger.info(f"原始分数: {result.original_score}/30")
    logger.info(f"改进分数: {result.improved_score}/30")
    logger.info(f"分数提升: {result.score_delta:+.2f}")
    logger.info(f"应用的改进建议数: {len(result.suggestions_applied)}")

    assert result.improved_score >= result.original_score, "改进后分数应该不低于原始分数"

    logger.info("✅ 任务改进器测试通过\n")
    return True


def test_quality_threshold_pipeline():
    """测试质量阈值管道"""
    logger.info("=" * 60)
    logger.info("测试 4: 质量阈值管道")
    logger.info("=" * 60)

    from quality_threshold_pipeline import QualityThresholdPipeline

    # 测试任务
    test_tasks = [
        {"id": "task_001", "description": "高质量任务"},
        {"id": "task_002", "description": "中等质量任务"},
        {"id": "task_003", "description": "低质量任务"}
    ]

    # 测试分数
    scores_list = [
        {"clinical_accuracy": 9.0, "scenario_realism": 7.5, "evaluation_completeness": 6.5, "difficulty_appropriateness": 5.0},
        {"clinical_accuracy": 7.5, "scenario_realism": 6.0, "evaluation_completeness": 5.0, "difficulty_appropriateness": 4.0},
        {"clinical_accuracy": 5.0, "scenario_realism": 4.0, "evaluation_completeness": 4.0, "difficulty_appropriateness": 3.0}
    ]

    # 创建管道
    pipeline = QualityThresholdPipeline(
        enable_improvement=True,
        output_dir="./test_outputs/pipeline_test"
    )

    # 运行管道
    results = pipeline.run(test_tasks, scores_list)

    logger.info(f"高质量任务: {len(results['high_quality'])}")
    logger.info(f"中等质量改进成功: {len(results['medium_quality_improved'])}")
    logger.info(f"中等质量改进失败: {len(results['medium_quality_failed'])}")
    logger.info(f"低质量任务: {len(results['low_quality'])}")

    # 验证结果
    total_processed = (
        len(results['high_quality']) +
        len(results['medium_quality_improved']) +
        len(results['medium_quality_failed']) +
        len(results['low_quality'])
    )

    assert total_processed == len(test_tasks), "所有任务都应该被处理"

    logger.info("✅ 质量阈值管道测试通过\n")
    return True


def test_report_generator():
    """测试报告生成器"""
    logger.info("=" * 60)
    logger.info("测试 5: 报告生成器")
    logger.info("=" * 60)

    from reporting import QualityReportGenerator

    # 测试数据
    test_results = {
        "high_quality": [{"id": "task_001"}],
        "medium_quality_improved": [],
        "medium_quality_failed": [],
        "low_quality": [{"id": "task_002"}]
    }

    test_statistics = {
        "total_tasks": 2,
        "high_quality": 1,
        "medium_quality": 0,
        "low_quality": 1,
        "keep": 1,
        "improve": 0,
        "reject": 1,
        "average_score": 24.5,
        "score_distribution": {
            "0-10": 0,
            "10-15": 0,
            "15-20": 0,
            "20-24": 1,
            "24-27": 0,
            "27-30": 1
        },
        "pass_rate": 50.0
    }

    test_classifications = [
        {
            "task_id": "task_001",
            "total_score": 27.5,
            "quality_level": "HIGH",
            "action": "KEEP",
            "reasons": ["所有维度都达到高标准"]
        },
        {
            "task_id": "task_002",
            "total_score": 21.5,
            "quality_level": "LOW",
            "action": "REJECT",
            "reasons": ["总分低于阈值"]
        }
    ]

    # 生成报告
    generator = QualityReportGenerator(output_dir="./test_outputs/reports_test")
    report_files = generator.generate_comprehensive_report(
        test_results, test_statistics, test_classifications
    )

    logger.info("生成的报告文件:")
    for report_type, path in report_files.items():
        logger.info(f"  {report_type}: {path}")

    # 验证文件存在
    assert "json" in report_files, "应该生成 JSON 报告"
    assert Path(report_files["json"]).exists(), "JSON 报告文件应该存在"

    logger.info("✅ 报告生成器测试通过\n")
    return True


def main():
    """运行所有测试"""
    logger.info("\n" + "=" * 60)
    logger.info("质量阈值筛选系统 - 完整测试")
    logger.info("=" * 60 + "\n")

    tests = [
        ("评分系统", test_scoring_system),
        ("质量分级器", test_quality_classifier),
        ("任务改进器", test_task_improver),
        ("质量阈值管道", test_quality_threshold_pipeline),
        ("报告生成器", test_report_generator),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            logger.error(f"❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # 打印总结
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"通过: {passed}/{len(tests)}")
    logger.info(f"失败: {failed}/{len(tests)}")

    if failed == 0:
        logger.info("\n🎉 所有测试通过！")
        return 0
    else:
        logger.info(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
