#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Pipeline Script - Runs Complete Clinical Data Processing Pipeline
主管道脚本 - 运行完整的临床数据处理管道

Stage 0: DataValidator (Raw Data Validation)
Stage 1: UniClinicalDataEngine (ETL)
Stage 2: DataQualityFiltering (Quality Filter)
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from DataValidator import MedicalDialogueValidator


# ============================================================================
# Wrapper functions for UniClinicalDataEngine
# ============================================================================

@dataclass
class ETLResult:
    """Result from ETL process."""
    success: bool
    records_processed: int
    tasks_generated: int
    output_files: Dict[str, str]
    errors: List[str] = field(default_factory=list)


def run_etl(
    input_path: str,
    input_format: str = "auto",
    output_dir: str = "./outputs/etl",
    validate_input: bool = True,
    anonymize_phi: bool = False,
    log_level: str = "INFO"
) -> ETLResult:
    """
    Run ETL process using UniClinicalDataEngine.

    Wrapper function to simplify the interface.
    """
    logger = logging.getLogger(__name__)

    try:
        from UniClinicalDataEngine.engine import UniClinicalDataEngine
        from UniClinicalDataEngine.models import EngineConfig as _EngineConfig

        # Determine source type from format
        format_to_type = {
            "nhands_json": "nhands",
            "nhands_jsonl": "nhands",
            "json": "json",
            "jsonl": "json",
            "csv": "csv",
        }

        source_type = "json"  # Default
        if input_format != "auto":
            source_type = format_to_type.get(input_format, "json")

        # Create config
        config = _EngineConfig(
            source_type=source_type,
            source_path=input_path,
            output_dir=output_dir,
            domain_name="clinical",
        )

        # Run engine
        engine = UniClinicalDataEngine(config)
        output_dir_result = engine.run_and_save()

        # Count generated tasks
        tasks_file = os.path.join(output_dir_result, "tasks.json")
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
                tasks_generated = len(tasks)
        else:
            tasks_generated = 0

        return ETLResult(
            success=True,
            records_processed=1,  # Placeholder
            tasks_generated=tasks_generated,
            output_files={
                "tasks.json": os.path.join(output_dir_result, "tasks.json"),
                "db.json": os.path.join(output_dir_result, "db.json"),
                "tools.json": os.path.join(output_dir_result, "tools.json"),
                "policy.md": os.path.join(output_dir_result, "policy.md"),
            },
            errors=[]
        )

    except Exception as e:
        logger.error(f"ETL failed: {e}")
        return ETLResult(
            success=False,
            records_processed=0,
            tasks_generated=0,
            output_files={},
            errors=[str(e)]
        )


# ============================================================================
# Wrapper functions for DataQualityFiltering
# ============================================================================

@dataclass
class FilterResult:
    """Result from filtering process."""
    success: bool
    total_tasks: int
    high_quality_tasks: int
    pass_rate: float
    output_files: Dict[str, str]
    statistics: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


def run_filter(
    input_path: str,
    output_dir: str = "./outputs/filtered",
    min_quality_score: float = 3.5,
    preserve_rejected_tasks: bool = True,
    log_level: str = "INFO"
) -> FilterResult:
    """
    Run quality filtering using DataQualityFiltering.

    Wrapper function to simplify the interface.
    """
    logger = logging.getLogger(__name__)

    try:
        from DataQualityFiltering.data_quality.filter_engine import QualityFilter, FilterConfig

        # Create config
        config = FilterConfig(
            input_path=input_path,
            output_dir=output_dir,
            min_quality_score=min_quality_score,
            preserve_rejected_tasks=preserve_rejected_tasks,
            log_level=log_level,
        )

        # Run filter
        filter_engine = QualityFilter(config)
        filter_engine.run()

        # Get results
        stats = filter_engine.stats

        return FilterResult(
            success=True,
            total_tasks=stats.get("total_tasks", 0),
            high_quality_tasks=stats.get("high_quality_tasks", 0),
            pass_rate=stats.get("pass_rate", 0.0),
            output_files={
                "tasks_filtered.json": os.path.join(output_dir, "tasks_filtered.json"),
            },
            statistics=stats,
            errors=[]
        )

    except Exception as e:
        logger.error(f"Filtering failed: {e}")
        return FilterResult(
            success=False,
            total_tasks=0,
            high_quality_tasks=0,
            pass_rate=0.0,
            output_files={},
            statistics={},
            errors=[str(e)]
        )


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


def validate_raw_data(
    input_path: str,
    strict_mode: bool = False,
    fail_on_error: bool = True
) -> Dict[str, Any]:
    """
    Stage 0: Validate raw input data.

    Args:
        input_path: Path to input data file
        strict_mode: If True, treats warnings as errors
        fail_on_error: If True, raises exception on validation failure

    Returns:
        Validation result dict
    """
    logger = logging.getLogger(__name__)
    logger.info("Validating raw input data...")

    result = {
        "validated": False,
        "is_valid": False,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    try:
        # Check if file exists
        if not os.path.exists(input_path):
            error = f"Input file not found: {input_path}"
            logger.error(error)
            result["errors"].append(error)
            if fail_on_error:
                raise FileNotFoundError(error)
            return result

        # For non-tau2 format data (JSON/JSONL/CSV), do basic validation
        file_ext = Path(input_path).suffix.lower()

        if file_ext in ['.json', '.jsonl']:
            # Try to load and validate JSON structure
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    if file_ext == '.jsonl':
                        # JSONL: validate first few lines
                        lines = f.readlines()[:10]
                        data = [json.loads(line.strip()) for line in lines if line.strip()]
                        logger.info(f"JSONL format: validated first {len(data)} records")
                    else:
                        # JSON: load full file
                        data = json.load(f)
                        logger.info(f"JSON format: loaded {len(data) if isinstance(data, list) else 1} records")

                result["is_valid"] = True
                result["validated"] = True
                result["stats"] = {
                    "format": file_ext,
                    "record_count": len(data) if isinstance(data, list) else 1
                }
                logger.info(f"✅ Raw data validation passed: {result['stats']}")
                return result

            except json.JSONDecodeError as e:
                error = f"Invalid JSON format: {e}"
                logger.error(error)
                result["errors"].append(error)
                if fail_on_error:
                    raise ValueError(error)
                return result

        elif file_ext == '.csv':
            # CSV: check file can be read
            try:
                import pandas as pd
                df = pd.read_csv(input_path, nrows=10)
                result["is_valid"] = True
                result["validated"] = True
                result["stats"] = {
                    "format": "csv",
                    "columns": len(df.columns),
                    "sample_rows": len(df)
                }
                logger.info(f"✅ CSV validation passed: {result['stats']}")
                return result
            except Exception as e:
                error = f"CSV validation failed: {e}"
                logger.error(error)
                result["errors"].append(error)
                if fail_on_error:
                    raise ValueError(error)
                return result
        else:
            logger.warning(f"Unknown file format: {file_ext}, skipping validation")
            result["warnings"].append(f"Unknown format: {file_ext}")
            result["validated"] = False
            return result

    except Exception as e:
        error = f"Validation error: {e}"
        logger.error(error)
        result["errors"].append(error)
        if fail_on_error:
            raise
        return result


def validate_generated_tasks(
    tasks_path: str,
    strict_mode: bool = False
) -> Dict[str, Any]:
    """
    Validate generated tasks using DataValidator.

    Args:
        tasks_path: Path to tasks.json file
        strict_mode: If True, treats warnings as errors

    Returns:
        Validation result dict
    """
    logger = logging.getLogger(__name__)
    logger.info("Running DataValidator on generated tasks...")

    result = {
        "validated": False,
        "is_valid": False,
        "errors": [],
        "warnings": [],
        "stats": {},
    }

    try:
        validator = MedicalDialogueValidator(strict_mode=strict_mode)
        validation_result = validator.validate_dataset(Path(tasks_path))

        result["validated"] = True
        result["is_valid"] = validation_result.is_valid
        result["stats"] = validation_result.stats

        # Categorize issues
        for issue in validation_result.issues:
            if issue.level.value == "error":
                result["errors"].append({
                    "category": issue.category,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                })
            elif issue.level.value == "warning":
                result["warnings"].append({
                    "category": issue.category,
                    "message": issue.message,
                    "suggestion": issue.suggestion
                })

        if validation_result.is_valid:
            logger.info(f"✅ Task validation passed!")
            logger.info(f"   - Total tasks: {validation_result.total_tasks}")
            logger.info(f"   - Errors: {len(result['errors'])}")
            logger.info(f"   - Warnings: {len(result['warnings'])}")
        else:
            logger.warning(f"⚠️  Task validation failed with {len(result['errors'])} errors")

        return result

    except Exception as e:
        error = f"DataValidator error: {e}"
        logger.error(error)
        result["errors"].append(error)
        return result


def run_complete_pipeline(
    input_path: str,
    output_dir: str = "./outputs",
    stage1_format: str = "auto",
    min_quality_score: float = 3.5,
    skip_validation: bool = False,
    validate_tasks: bool = True,
    validation_strict: bool = False,
    **kwargs
) -> dict:
    """
    Run the complete three-stage pipeline.

    Args:
        input_path: Path to input data file
        output_dir: Base output directory
        stage1_format: Input format for stage 1
        min_quality_score: Minimum quality score for stage 2
        skip_validation: Skip Stage 0 (raw data validation)
        validate_tasks: Validate generated tasks with DataValidator
        validation_strict: Use strict mode for validation
        **kwargs: Additional configuration

    Returns:
        Dictionary with pipeline results
    """
    logger = logging.getLogger(__name__)
    start_time = datetime.now()

    logger.info("=" * 70)
    logger.info("CLINICAL DATA PROCESSING PIPELINE")
    logger.info("Starting complete 3-stage pipeline (with validation)")
    logger.info("=" * 70)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input file: {input_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info("")

    results = {
        "start_time": start_time.isoformat(),
        "input_path": input_path,
        "stage0": None,  # Raw data validation
        "stage1": None,  # ETL
        "stage1_validation": None,  # Task validation
        "stage2": None,  # Quality filtering
        "success": False,
    }

    try:
        # ========================================================================
        # STAGE 0: Raw Data Validation (Optional)
        # ========================================================================
        if not skip_validation:
            logger.info("=" * 70)
            logger.info("STAGE 0: DataValidator - Raw Data Validation")
            logger.info("=" * 70)
            logger.info("")

            stage0_result = validate_raw_data(
                input_path=input_path,
                strict_mode=validation_strict,
                fail_on_error=False  # Don't fail on validation errors
            )

            results["stage0"] = stage0_result

            if not stage0_result["validated"]:
                logger.warning("⚠️  Stage 0: Raw data validation was skipped (unknown format)")
            elif not stage0_result["is_valid"]:
                logger.error(f"❌ Stage 0: Raw data validation failed with {len(stage0_result['errors'])} errors")
                for error in stage0_result["errors"][:3]:  # Show first 3 errors
                    logger.error(f"   - {error}")
                if len(stage0_result["errors"]) > 3:
                    logger.error(f"   ... and {len(stage0_result['errors']) - 3} more errors")
                logger.warning("⚠️  Continuing despite validation errors...")

            logger.info("")
        else:
            logger.info("Skipping Stage 0 (raw data validation) as requested")
            logger.info("")

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
        # STAGE 1.5: Validate Generated Tasks (Optional)
        # ========================================================================
        if validate_tasks:
            logger.info("=" * 70)
            logger.info("STAGE 1.5: DataValidator - Generated Tasks Validation")
            logger.info("=" * 70)
            logger.info("")

            tasks_json = os.path.join(stage1_output, "tasks.json")
            if os.path.exists(tasks_json):
                validation_result = validate_generated_tasks(
                    tasks_path=tasks_json,
                    strict_mode=validation_strict
                )

                results["stage1_validation"] = validation_result

                if not validation_result["is_valid"] and validation_strict:
                    logger.error("❌ Task validation failed in strict mode! Aborting.")
                    return results
                elif not validation_result["is_valid"]:
                    logger.warning("⚠️  Task validation found issues, but continuing...")
            else:
                logger.warning(f"⚠️  tasks.json not found at {tasks_json}, skipping validation")

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
        description="Run complete clinical data processing pipeline with validation"
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
        "--skip-validation",
        action="store_true",
        help="Skip Stage 0 (raw data validation)"
    )
    parser.add_argument(
        "--no-task-validation",
        action="store_true",
        help="Skip Stage 1.5 (generated tasks validation)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict mode for validation (treat warnings as errors)"
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
        skip_validation=args.skip_validation,
        validate_tasks=not args.no_task_validation,
        validation_strict=args.strict,
    )

    # Exit with appropriate code
    sys.exit(0 if results["success"] or results.get("partial_success", False) else 1)


if __name__ == "__main__":
    main()
