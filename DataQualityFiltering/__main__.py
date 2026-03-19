#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataQualityFiltering - 统一的医学评估框架
主 CLI 入口点

使用示例:
    # 数据质量评估
    python -m DataQualityFiltering data-quality check --input data.json
    python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

    # Agent 性能评估
    python -m DataQualityFiltering agent-eval evaluate --input agent_results.json
    python -m DataQualityFiltering agent-eval batch --input results.json --max-workers 8

    # 查看帮助
    python -m DataQualityFiltering --help
    python -m DataQualityFiltering data-quality --help
    python -m DataQualityFiltering agent-eval --help
"""

import argparse
import json
import sys
import os
from pathlib import Path

# 设置控制台输出编码为 UTF-8（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="DataQualityFiltering - 统一的医学评估框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 数据质量评估
  python -m DataQualityFiltering data-quality check --input data.json
  python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

  # Agent 性能评估
  python -m DataQualityFiltering agent-eval evaluate --input agent_results.json
  python -m DataQualityFiltering agent-eval batch --input results.json --max-workers 8

  # 查看版本
  python -m DataQualityFiltering --version
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 2.0.0"
    )

    # 子命令
    subparsers = parser.add_subparsers(
        dest="subsystem",
        help="选择子系统",
        metavar="SUBSYSTEM"
    )

    # ============================================================================
    # 原始数据验证子系统
    # ============================================================================
    raw_data_parser = subparsers.add_parser(
        "raw-data",
        help="原始数据验证",
        description="验证原始医患对话数据是否适合转换"
    )

    raw_data_subparsers = raw_data_parser.add_subparsers(
        dest="command",
        help="原始数据验证命令",
        metavar="COMMAND"
    )

    # validate 命令
    rd_validate_parser = raw_data_subparsers.add_parser(
        "validate",
        help="验证原始对话数据",
        description="验证原始医患对话数据的质量和完整性"
    )
    rd_validate_parser.add_argument(
        "--input",
        required=True,
        help="输入文件路径（CSV或JSON格式）"
    )
    rd_validate_parser.add_argument(
        "--output",
        help="输出报告文件路径（JSON格式）"
    )
    rd_validate_parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="输入文件格式（默认自动检测）"
    )
    rd_validate_parser.add_argument(
        "--encoding",
        default="utf-8",
        help="文件编码（默认: utf-8）"
    )
    rd_validate_parser.add_argument(
        "--strict",
        action="store_true",
        help="严格模式（warnings也会导致验证失败）"
    )
    rd_validate_parser.add_argument(
        "--min-patient-length",
        type=int,
        default=5,
        help="患者主诉最小长度（默认: 5）"
    )
    rd_validate_parser.add_argument(
        "--min-doctor-length",
        type=int,
        default=10,
        help="医生回答最小长度（默认: 10）"
    )
    rd_validate_parser.add_argument(
        "--min-turns",
        type=int,
        default=2,
        help="最少对话轮数（默认: 2）"
    )

    # ============================================================================
    # 数据质量评估子系统
    # ============================================================================
    data_quality_parser = subparsers.add_parser(
        "data-quality",
        help="数据质量评估子系统",
        description="验证和过滤医学对话数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检查医学对话
  python -m DataQualityFiltering data-quality check --input data.json

  # 过滤低质量数据
  python -m DataQualityFiltering data-quality filter --input data.json --threshold 3.5

  # 运行完整管道
  python -m DataQualityFiltering data-quality pipeline --input data.json --mode semi_auto
        """
    )

    data_quality_subparsers = data_quality_parser.add_subparsers(
        dest="command",
        help="数据质量命令",
        metavar="COMMAND"
    )

    # check 命令
    check_parser = data_quality_subparsers.add_parser(
        "check",
        help="检查医学对话数据",
        description="检查数据是否符合医学对话格式要求"
    )
    check_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    check_parser.add_argument(
        "--output",
        help="输出报告文件路径（可选）"
    )

    # filter 命令
    filter_parser = data_quality_subparsers.add_parser(
        "filter",
        help="过滤低质量数据",
        description="根据质量分数过滤数据"
    )
    filter_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    filter_parser.add_argument(
        "--threshold",
        type=float,
        default=3.5,
        help="质量阈值（默认: 3.5）"
    )
    filter_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )

    # pipeline 命令
    pipeline_parser = data_quality_subparsers.add_parser(
        "pipeline",
        help="运行完整的数据质量管道",
        description="运行完整的质量评估和过滤管道"
    )
    pipeline_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    pipeline_parser.add_argument(
        "--mode",
        choices=["human", "semi_auto", "both"],
        default="semi_auto",
        help="审查模式（默认: semi_auto）"
    )
    pipeline_parser.add_argument(
        "--threshold",
        type=float,
        default=3.5,
        help="质量阈值（默认: 3.5）"
    )
    pipeline_parser.add_argument(
        "--output-dir",
        help="输出目录（可选）"
    )

    # quality-threshold 命令
    qt_parser = data_quality_subparsers.add_parser(
        "quality-threshold",
        help="质量阈值筛选（0-30分制）",
        description="使用扩展的质量阈值筛选系统进行三级分类和自动改进",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用质量阈值筛选
  python -m DataQualityFiltering data-quality quality-threshold --input tasks.json

  # 自定义阈值
  python -m DataQualityFiltering data-quality quality-threshold --input tasks.json --high 27 --medium 24

  # 禁用自动改进
  python -m DataQualityFiltering data-quality quality-threshold --input tasks.json --no-improvement

  # 指定输出目录
  python -m DataQualityFiltering data-quality quality-threshold --input tasks.json --output-dir ./results
        """
    )
    qt_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    qt_parser.add_argument(
        "--output-dir",
        default="./outputs/quality_threshold",
        help="输出目录（默认: ./outputs/quality_threshold）"
    )
    qt_parser.add_argument(
        "--high",
        type=float,
        default=27.0,
        dest="high_threshold",
        help="高质量阈值（默认: 27.0）"
    )
    qt_parser.add_argument(
        "--medium",
        type=float,
        default=24.0,
        dest="medium_threshold",
        help="中等质量阈值（默认: 24.0）"
    )
    qt_parser.add_argument(
        "--no-improvement",
        action="store_false",
        dest="enable_improvement",
        help="禁用自动改进功能"
    )
    qt_parser.add_argument(
        "--scores-file",
        help="预计算的分数文件（JSON 格式，可选）"
    )

    # ============================================================================
    # Agent 性能评估子系统
    # ============================================================================
    agent_eval_parser = subparsers.add_parser(
        "agent-eval",
        help="Agent 性能评估子系统",
        description="评估 Agent 在医学任务上的表现",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 评估单个任务
  python -m DataQualityFiltering agent-eval evaluate --input task.json

  # 批量评估
  python -m DataQualityFiltering agent-eval batch --input tasks.json --max-workers 8

  # 生成报告
  python -m DataQualityFiltering agent-eval report --input results.json --output report.md
        """
    )

    agent_eval_subparsers = agent_eval_parser.add_subparsers(
        dest="command",
        help="Agent 评估命令",
        metavar="COMMAND"
    )

    # evaluate 命令
    ae_eval_parser = agent_eval_subparsers.add_parser(
        "evaluate",
        help="评估 Agent 回答",
        description="评估 Agent 在医学任务上的回答质量"
    )
    ae_eval_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    ae_eval_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    ae_eval_parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM 模型（默认: gpt-4-turbo）"
    )

    # batch 命令
    ae_batch_parser = agent_eval_subparsers.add_parser(
        "batch",
        help="批量评估",
        description="批量评估多个 Agent 回答"
    )
    ae_batch_parser.add_argument(
        "--input",
        required=True,
        help="输入 JSON 文件路径"
    )
    ae_batch_parser.add_argument(
        "--output",
        help="输出文件路径（可选）"
    )
    ae_batch_parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="最大并发数（默认: 4）"
    )
    ae_batch_parser.add_argument(
        "--model",
        default="gpt-4-turbo",
        help="LLM 模型（默认: gpt-4-turbo）"
    )

    # report 命令
    ae_report_parser = agent_eval_subparsers.add_parser(
        "report",
        help="生成评估报告",
        description="从评估结果生成 Markdown 报告"
    )
    ae_report_parser.add_argument(
        "--input",
        required=True,
        help="评估结果 JSON 文件路径"
    )
    ae_report_parser.add_argument(
        "--output",
        help="报告输出路径（可选）"
    )

    # 解析参数
    args = parser.parse_args()

    # 如果没有提供子命令，显示帮助
    if not args.subsystem:
        parser.print_help()
        return 0

    # 路由到对应的处理器
    if args.subsystem == "raw-data":
        return _handle_raw_data(args)
    elif args.subsystem == "data-quality":
        return _handle_data_quality(args)
    elif args.subsystem == "agent-eval":
        return _handle_agent_eval(args)
    else:
        parser.print_help()
        return 1


def _handle_raw_data(args):
    """处理原始数据验证命令"""
    if not args.command:
        print("错误: 请指定原始数据验证命令（validate）")
        print("使用 --help 查看帮助")
        return 1

    if args.command == "validate":
        # 导入原始数据验证器
        try:
            from raw_data_validator import RawDataValidator
        except ImportError:
            # 添加当前目录到路径
            import sys
            current_dir = Path(__file__).parent
            if str(current_dir) not in sys.path:
                sys.path.insert(0, str(current_dir))
            from raw_data_validator import RawDataValidator

        # 创建验证器配置
        config = {
            "min_patient_length": args.min_patient_length,
            "min_doctor_length": args.min_doctor_length,
            "min_total_turns": args.min_turns,
            "strict_mode": args.strict
        }

        # 创建验证器
        validator = RawDataValidator(config)

        # 检测文件格式
        file_path = Path(args.input)
        if args.format == "auto":
            file_format = file_path.suffix.lstrip(".")
        else:
            file_format = args.format

        # 验证文件
        try:
            if file_format == "csv":
                report = validator.validate_csv_file(args.input, args.encoding)
            elif file_format == "json":
                report = validator.validate_json_file(args.input, args.encoding)
            else:
                print(f"❌ 不支持的文件格式: {file_format}")
                return 1

            # 打印摘要
            print(validator.generate_summary(report))

            # 保存详细报告
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
                print(f"✅ 详细报告已保存到: {args.output}")

            # 返回状态码
            return 0 if report.failed_dialogues == 0 else 1

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return 1
    else:
        print(f"错误: 未知命令 '{args.command}'")
        return 1


def _handle_data_quality(args):
    """处理数据质量评估命令"""
    if not args.command:
        print("错误: 请指定数据质量命令（check, filter, pipeline, quality-threshold）")
        print("使用 --help 查看帮助")
        return 1

    # 处理 quality-threshold 命令（独立处理，避免导入问题）
    if args.command == "quality-threshold":
        return _handle_quality_threshold(args)

    # 导入数据质量模块
    try:
        from data_quality.cli import main as dq_main
        from data_quality.check_medical_dialogue import main as check_main

        if args.command == "check":
            # 调用医学对话检查
            sys.argv = [
                "check_medical_dialogue",
                "--input", args.input,
            ]
            if args.output:
                sys.argv.extend(["--output", args.output])

            return check_main()

        elif args.command == "filter":
            # 调用过滤功能
            from data_quality import QualityFilter, FilterConfig
            import json

            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = FilterConfig(min_quality_score=args.threshold)
            filter_engine = QualityFilter(config)

            # 过滤数据
            filtered = [task for task in data if filter_engine.calculate_quality_score(task) >= args.threshold]

            # 保存结果
            output_file = args.output or args.input.replace(".json", "_filtered.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(filtered, f, ensure_ascii=False, indent=2)

            print(f"过滤完成: {len(filtered)}/{len(data)} 个任务通过")
            print(f"结果保存到: {output_file}")
            return 0

        elif args.command == "pipeline":
            # 调用完整管道
            sys.argv = [
                "cli",
                "--tasks-path", args.input,
                "--review-mode", args.mode,
                "--threshold", str(args.threshold),
            ]
            if args.output_dir:
                sys.argv.extend(["--output-dir", args.output_dir])

            return dq_main()

    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _handle_quality_threshold(args):
    """处理质量阈值筛选命令"""
    import json
    import logging
    try:
        from scoring import ScoringConfig
        from quality_threshold_pipeline import QualityThresholdPipeline
    except ImportError:
        # 添加当前目录到 Python 路径
        import os
        import sys
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        from scoring import ScoringConfig
        from quality_threshold_pipeline import QualityThresholdPipeline

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("质量阈值筛选系统")
    print("=" * 60)
    print(f"输入文件: {args.input}")
    print(f"输出目录: {args.output_dir}")
    print(f"高质量阈值: {args.high_threshold}")
    print(f"中等质量阈值: {args.medium_threshold}")
    print(f"启用改进: {args.enable_improvement}")
    print("=" * 60)
    print()  # 添加空行

    # 加载任务
    print("加载任务...")
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 处理不同的数据格式
    if isinstance(data, dict):
        tasks = data.get("tasks", data.get("data", [data]))
    elif isinstance(data, list):
        tasks = data
    else:
        print(f"❌ 错误: 无法识别的数据格式")
        return 1

    print(f"加载了 {len(tasks)} 个任务")

    # 加载或生成分数
    scores_list = None
    original_scores_list = None

    if args.scores_file:
        print(f"加载预计算的分数...")
        with open(args.scores_file, "r", encoding="utf-8") as f:
            scores_data = json.load(f)
            scores_list = scores_data.get("extended_scores")
            original_scores_list = scores_data.get("original_scores")
        print(f"加载了 {len(scores_list) if scores_list else 0} 组分数")
    else:
        print(f"未提供分数文件，将使用默认分数（测试模式）")
        print(f"   实际使用时，请先运行评分系统或提供 --scores-file")
    print()  # 添加空行

    # 创建配置
    config = ScoringConfig(
        HIGH_THRESHOLD=args.high_threshold,
        MEDIUM_THRESHOLD=args.medium_threshold
    )

    # 创建并运行管道
    print("运行质量阈值筛选管道...")
    print()
    pipeline = QualityThresholdPipeline(
        config=config,
        enable_improvement=args.enable_improvement,
        output_dir=args.output_dir
    )

    results = pipeline.run(tasks, scores_list, original_scores_list)

    # 打印最终结果
    print()
    print("=" * 60)
    print("质量阈值筛选完成")
    print("=" * 60)
    print(f"高质量任务: {len(results['high_quality'])}")
    print(f"中等质量改进成功: {len(results['medium_quality_improved'])}")
    print(f"中等质量改进失败: {len(results['medium_quality_failed'])}")
    print(f"低质量任务: {len(results['low_quality'])}")
    print(f"\n结果保存到: {args.output_dir}")
    print("=" * 60)

    return 0


def _handle_agent_eval(args):
    """处理 Agent 评估命令"""
    if not args.command:
        print("错误: 请指定 Agent 评估命令（evaluate, batch, report）")
        print("使用 --help 查看帮助")
        return 1

    # 导入 Agent 评估模块
    try:
        from .agent_evaluation.cli import main as ae_main

        # 构建命令行参数
        sys.argv = [
            "evaluate_agent",
            "--input", args.input,
        ]

        if args.command == "evaluate":
            if args.output:
                sys.argv.extend(["--output", args.output])
            sys.argv.extend(["--model", args.model])

        elif args.command == "batch":
            if args.output:
                sys.argv.extend(["--output", args.output])
            sys.argv.extend(["--max-workers", str(args.max_workers)])
            sys.argv.extend(["--model", args.model])

        elif args.command == "report":
            # TODO: 实现报告生成
            print("⚠️  报告生成功能即将推出")
            return 0

        return ae_main()

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
