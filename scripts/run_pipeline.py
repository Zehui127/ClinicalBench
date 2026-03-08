#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Pipeline Script - Runs Complete Clinical Data Processing Pipeline
主管道脚本 - 运行完整的临床数据处理管道

Stage 1: UniClinicalDataEngine (ETL)
Stage 2: DataQualityFiltering (Quality Filter)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from UniClinicalDataEngine import run_etl, ETLConfig
from DataQualityFiltering import run_filter, FilterConfig


def setup_logging(log_file: str = None):
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logging.getLogger().addHandler(file_handler)


def run_complete_pipeline(
    input_path: str,
    output_dir: str = "./outputs",
    stage1_format: str = "auto",
    min_quality_score: float = 3.5,
    **kwargs
) -> dict:
    """
    Run the complete two-stage pipeline.

    Args:
        input_path: Path to input data file
        output_dir: Base output directory
        stage1_format: Input format for stage 1
        min_quality_score: Minimum quality score for stage 2
        **kwargs: Additional configuration

    Returns:
        Dictionary with pipeline results
    """
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    logger.info("=" * 70)
    logger.info("CLINICAL DATA PROCESSING PIPELINE")
    logger.info("Starting complete 2-stage pipeline")
    logger.info("=" * 70)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input file: {input_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("")

    results = {
        "start_time": start_time.isoformat(),
        "input_path": input_path,
        "stage1": None,
        "stage2": None,
        "success": False,
    }

    try:
        # ========================================================================
        # STAGE 1: UniClinicalDataEngine (ETL)
        # ========================================================================
        logger.info("=" * 70)
        logger.info("STAGE 1: UniClinicalDataEngine - ETL Pipeline")
        logger.info("=" * 70)
        logger.info("")

        stage1_output = os.path.join(output_dir, "stage1_output")

        stage1_result = run_etl(
            input_path=input_path,
            input_format=stage1_format,
            output_dir=stage1_output,
            validate_input=True,
            anonymize_phi=False,
            log_level="INFO",
        )

        results["stage1"] = {
            "success": stage1_result.success,
            "records_processed": stage1_result.records_processed,
            "tasks_generated": stage1_result.tasks_generated,
            "output_files": stage1_result.output_files,
            "errors": stage1_result.errors,
        }

        if not stage1_result.success:
            logger.error("Stage 1 failed! Aborting pipeline.")
            return results

        logger.info("")
        logger.info(f"Stage 1 completed successfully!")
        logger.info(f"  - Records processed: {stage1_result.records_processed}")
        logger.info(f"  - Tasks generated: {stage1_result.tasks_generated}")
        logger.info("")

        # ========================================================================
        # STAGE 2: DataQualityFiltering (Quality Filter)
        # ========================================================================
        logger.info("=" * 70)
        logger.info("STAGE 2: DataQualityFiltering - Quality Filtering")
        logger.info("=" * 70)
        logger.info("")

        stage2_input = os.path.join(stage1_output, "tasks.json")
        stage2_output = os.path.join(output_dir, "stage2_output")

        stage2_result = run_filter(
            input_path=stage2_input,
            output_dir=stage2_output,
            min_quality_score=min_quality_score,
            preserve_rejected_tasks=True,
            log_level="INFO",
        )

        results["stage2"] = {
            "success": stage2_result.success,
            "total_tasks": stage2_result.total_tasks,
            "high_quality_tasks": stage2_result.high_quality_tasks,
            "pass_rate": stage2_result.pass_rate,
            "output_files": stage2_result.output_files,
            "statistics": stage2_result.statistics,
            "errors": stage2_result.errors,
        }

        if not stage2_result.success:
            logger.error("Stage 2 failed! However, Stage 1 output is preserved.")
            results["partial_success"] = True
        else:
            results["success"] = True

        logger.info("")
        logger.info(f"Stage 2 completed!")
        logger.info(f"  - Total tasks: {stage2_result.total_tasks}")
        logger.info(f"  - High quality: {stage2_result.high_quality_tasks}")
        logger.info(f"  - Pass rate: {stage2_result.pass_rate:.2f}%")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        results["errors"] = [str(e)]

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    results["end_time"] = end_time.isoformat()
    results["duration_seconds"] = duration

    logger.info("")
    logger.info("=" * 70)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 70)
    logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Status: {'SUCCESS' if results['success'] else 'FAILED' if not results.get('partial_success', False) else 'PARTIAL'}")
    logger.info("")

    # Save pipeline results
    results_file = os.path.join(output_dir, "pipeline_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Pipeline results saved to: {results_file}")

    return results


def main():
    """Main entry point for the pipeline script."""
    parser = argparse.ArgumentParser(
        description="Run complete clinical data processing pipeline"
    )
    parser.add_argument(
        "input",
        help="Path to input data file"
    )
    parser.add_argument(
        "-o", "--output",
        default="./outputs",
        help="Output directory (default: ./outputs)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["auto", "nhands_json", "nhands_jsonl", "json", "jsonl", "csv"],
        default="auto",
        help="Input format (default: auto-detect)"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=3.5,
        help="Minimum quality score (default: 3.5)"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file)

    # Run pipeline
    results = run_complete_pipeline(
        input_path=args.input,
        output_dir=args.output,
        stage1_format=args.format,
        min_quality_score=args.min_quality,
    )

    # Exit with appropriate code
    sys.exit(0 if results["success"] or results.get("partial_success", False) else 1)


if __name__ == "__main__":
    main()
