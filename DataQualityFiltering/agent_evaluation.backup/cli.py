#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI Tool for Medical Agent Evaluation
医学 Agent 评估 CLI 工具

使用示例：
    python evaluate_agent.py input.json --output results.json
    python evaluate_agent.py input.json --max-workers 8
    python evaluate_agent.py input.json --model claude-3-sonnet-20240229
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 导入本模块的组件
from .pipeline import AgentEvaluationPipeline


def setup_logging(verbose: bool = False) -> logging.Logger:
    """设置日志"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    return logging.getLogger(__name__)


def load_input_file(input_path: str) -> list:
    """加载输入文件"""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 处理不同的数据格式
    if isinstance(data, dict):
        items = data.get("items", data.get("evaluations", []))
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError(f"不支持的数据格式: {type(data)}")

    return items


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="医学 Agent 评估 CLI 工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 基本用法
    python evaluate_agent.py input.json

    # 指定输出文件
    python evaluate_agent.py input.json --output results.json

    # 自定义并发数
    python evaluate_agent.py input.json --max-workers 8

    # 使用不同的模型
    python evaluate_agent.py input.json --model claude-3-sonnet-20240229

    # 生成 Markdown 报告
    python evaluate_agent.py input.json --report report.md

    # 详细日志
    python evaluate_agent.py input.json --verbose
        """
    )

    parser.add_argument(
        "input",
        help="输入 JSON 文件路径"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出 JSON 文件路径（默认：auto-generated）"
    )

    parser.add_argument(
        "--report",
        default=None,
        help="报告文件路径（Markdown 格式）"
    )

    parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM 模型名称（默认：gpt-4-turbo）"
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="最大并发数（默认：4）"
    )

    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=3.5,
        help="通过阈值（默认：3.5）"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="禁用缓存"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="详细日志输出"
    )

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    try:
        # 加载数据
        logger.info(f"加载输入文件: {args.input}")
        items = load_input_file(args.input)
        logger.info(f"加载了 {len(items)} 个评估项目")

        # 创建管道
        pipeline = AgentEvaluationPipeline(
            model=args.model,
            max_workers=args.max_workers,
            use_cache=not args.no_cache,
            pass_threshold=args.pass_threshold,
        )

        # 确定输出路径
        output_file = args.output
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"./outputs/agent_evaluation_{timestamp}.json"

        # 评估
        result = pipeline.evaluate_from_file(
            input_file=args.input,
            output_file=output_file,
            show_progress=True,
        )

        # 生成报告
        if args.report:
            logger.info(f"生成 Markdown 报告: {args.report}")
            report = pipeline.generate_report(
                result["results"],
                output_file=args.report,
                format="markdown",
            )

        # 打印统计
        stats = result["statistics"]
        logger.info("\n" + "="*70)
        logger.info("评估完成")
        logger.info("="*70)
        logger.info(f"总数: {stats['total_reviews']}")
        logger.info(f"通过: {stats['passed']}")
        logger.info(f"失败: {stats['failed']}")
        logger.info(f"通过率: {stats['pass_rate']}%")
        logger.info(f"\n平均分数:")
        logger.info(f"  临床准确性: {stats['average_scores']['clinical_accuracy']}")
        logger.info(f"  对话流畅性: {stats['average_scores']['dialogue_fluency']}")
        logger.info(f"  安全性与同理心: {stats['average_scores']['safety_empathy']}")
        logger.info(f"  总体: {stats['average_scores']['overall']}")
        logger.info("="*70)

        return 0 if stats['pass_rate'] >= 50 else 1

    except Exception as e:
        logger.error(f"评估失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
