#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Clinical Benchmark Pipeline
完整的临床评测流程 - 从原始数据到最终评分

This script orchestrates the complete pipeline:
1. Data Validation (Stage 0)
2. ETL - UniClinicalDataEngine (Stage 1)
3. Task Validation (Stage 1.5)
4. Quality Filtering - DataQualityFiltering (Stage 2)
5. Agent Simulation (Stage 3)
6. Evaluation (Stage 4)

Usage:
    python scripts/master_pipeline.py \
        --input data/raw/medical_dialogue.json \
        --output results/ \
        --run-agents \
        --evaluate \
        --domain clinical_cardiology
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Data processing modules
from DataValidator import MedicalDialogueValidator
from UniClinicalDataEngine import run_etl, ETLConfig
from DataQualityFiltering import run_filter, FilterConfig

# Tau2 modules for agent simulation and evaluation
try:
    from tau2.cli import run
    from tau2.evaluator import ClinicalEvaluator
    from tau2.data_model.tasks import Task
    from tau2.data_model.simulation import SimulationRun
    from tau2.evaluator.evaluator import EvaluationType, evaluate_simulation
    TAU2_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Tau2 modules not available: {e}")
    TAU2_AVAILABLE = False


def setup_logging(log_file: Optional[str] = None, level: str = "INFO") -> None:
    """Setup logging configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers
    )


def load_json(file_path: str) -> Any:
    """Load JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Any, file_path: str) -> None:
    """Save data to JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class MasterPipeline:
    """
    Master pipeline for clinical benchmark processing.

    Orchestrates the complete flow from raw data to final evaluation scores.
    """

    def __init__(
        self,
        input_path: str,
        output_dir: str = "./outputs/master",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the master pipeline.

        Args:
            input_path: Path to raw input data
            output_dir: Base output directory
            config: Pipeline configuration
        """
        self.logger = logging.getLogger(__name__)
        self.input_path = input_path
        self.output_dir = output_dir
        self.config = config or {}

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Results tracking
        self.results = {
            "start_time": datetime.now().isoformat(),
            "input_path": input_path,
            "stages": {},
            "success": False,
        }

    def run(
        self,
        run_agents: bool = False,
        evaluate_results: bool = False,
        agent_config: Optional[Dict[str, Any]] = None,
        evaluation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline.

        Args:
            run_agents: Whether to run agent simulations (Stage 3)
            evaluate_results: Whether to evaluate results (Stage 4)
            agent_config: Configuration for agent simulation
            evaluation_config: Configuration for evaluation

        Returns:
            Complete pipeline results
        """
        self.logger.info("=" * 80)
        self.logger.info("MASTER CLINICAL BENCHMARK PIPELINE")
        self.logger.info("=" * 80)
        self.logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Input: {self.input_path}")
        self.logger.info(f"Output: {self.output_dir}")
        self.logger.info("")

        try:
            # Stage 0: Raw Data Validation
            self.stage0_validate_raw_data()

            # Stage 1: ETL
            stage1_output = self.stage1_etl()

            # Stage 1.5: Task Validation
            self.stage1_5_validate_tasks(stage1_output)

            # Stage 2: Quality Filtering
            stage2_output = self.stage2_quality_filtering(stage1_output)

            # Stage 3: Agent Simulation (optional)
            if run_agents:
                if not TAU2_AVAILABLE:
                    self.logger.error("❌ Cannot run agents: tau2 modules not available")
                else:
                    stage3_output = self.stage3_agent_simulation(
                        stage2_output,
                        agent_config or {}
                    )
            else:
                self.logger.info("Skipping Stage 3 (Agent Simulation) as requested")
                stage3_output = None

            # Stage 4: Evaluation (optional)
            if evaluate_results and stage3_output:
                if not TAU2_AVAILABLE:
                    self.logger.error("❌ Cannot evaluate: tau2 modules not available")
                else:
                    self.stage4_evaluation(stage3_output, evaluation_config or {})
            elif evaluate_results:
                self.logger.warning("⚠️  Skipping Stage 4 (Evaluation): No simulation results to evaluate")
            else:
                self.logger.info("Skipping Stage 4 (Evaluation) as requested")

            # Mark as successful
            self.results["success"] = True
            self.logger.info("")
            self.logger.info("=" * 80)
            self.logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 80)

        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
            self.results["success"] = False
            self.results["error"] = str(e)

        finally:
            # Save results
            self.results["end_time"] = datetime.now().isoformat()

            # Calculate duration
            start = datetime.fromisoformat(self.results["start_time"])
            end = datetime.fromisoformat(self.results["end_time"])
            self.results["duration_seconds"] = (end - start).total_seconds()

            # Save to file
            results_file = os.path.join(self.output_dir, "master_pipeline_results.json")
            save_json(self.results, results_file)
            self.logger.info(f"Results saved to: {results_file}")

        return self.results

    def stage0_validate_raw_data(self) -> None:
        """Stage 0: Validate raw input data."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 0: Raw Data Validation")
        self.logger.info("=" * 80)

        stage_dir = os.path.join(self.output_dir, "stage0_validation")
        os.makedirs(stage_dir, exist_ok=True)

        # Basic file format validation
        file_ext = Path(self.input_path).suffix.lower()

        result = {
            "stage": "stage0",
            "validated": False,
            "is_valid": False,
            "errors": [],
            "warnings": [],
        }

        try:
            if file_ext in ['.json', '.jsonl']:
                with open(self.input_path, 'r', encoding='utf-8') as f:
                    if file_ext == '.jsonl':
                        lines = f.readlines()[:100]  # Check first 100 lines
                        data = [json.loads(line.strip()) for line in lines if line.strip()]
                        self.logger.info(f"JSONL: validated {len(data)} sample records")
                    else:
                        data = json.load(f)
                        count = len(data) if isinstance(data, list) else 1
                        self.logger.info(f"JSON: loaded {count} records")

                result["validated"] = True
                result["is_valid"] = True
                result["stats"] = {"format": file_ext, "sample_count": len(data) if isinstance(data, list) else 1}

            else:
                result["warnings"].append(f"Format {file_ext} not validated")

            self.logger.info("✅ Stage 0 completed")
            self.results["stages"]["stage0"] = result

        except Exception as e:
            result["errors"].append(str(e))
            self.logger.error(f"Stage 0 failed: {e}")
            self.results["stages"]["stage0"] = result

        self.logger.info("")

    def stage1_etl(self) -> str:
        """Stage 1: ETL - Convert raw data to tau2 format."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 1: UniClinicalDataEngine - ETL Pipeline")
        self.logger.info("=" * 80)

        stage_dir = os.path.join(self.output_dir, "stage1_etl")
        os.makedirs(stage_dir, exist_ok=True)

        try:
            etl_result = run_etl(
                input_path=self.input_path,
                input_format=self.config.get("etl_format", "auto"),
                output_dir=stage_dir,
                validate_input=True,
                anonymize_phi=self.config.get("anonymize_phi", False),
                log_level="INFO",
            )

            self.results["stages"]["stage1"] = {
                "stage": "stage1",
                "success": etl_result.success,
                "records_processed": etl_result.records_processed,
                "tasks_generated": etl_result.tasks_generated,
                "output_files": etl_result.output_files,
                "errors": etl_result.errors,
            }

            if not etl_result.success:
                raise RuntimeError(f"ETL failed: {etl_result.errors}")

            self.logger.info(f"✅ Stage 1 completed")
            self.logger.info(f"   - Records processed: {etl_result.records_processed}")
            self.logger.info(f"   - Tasks generated: {etl_result.tasks_generated}")

        except Exception as e:
            self.logger.error(f"Stage 1 failed: {e}")
            self.results["stages"]["stage1"] = {"stage": "stage1", "success": False, "error": str(e)}
            raise

        self.logger.info("")
        return stage_dir

    def stage1_5_validate_tasks(self, stage1_output: str) -> None:
        """Stage 1.5: Validate generated tasks using DataValidator."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 1.5: DataValidator - Task Validation")
        self.logger.info("=" * 80)

        tasks_json = os.path.join(stage1_output, "tasks.json")

        if not os.path.exists(tasks_json):
            self.logger.warning(f"⚠️  tasks.json not found, skipping validation")
            self.results["stages"]["stage1_5"] = {"stage": "stage1_5", "skipped": True}
            self.logger.info("")
            return

        try:
            validator = MedicalDialogueValidator(strict_mode=False)
            validation_result = validator.validate_dataset(Path(tasks_json))

            self.results["stages"]["stage1_5"] = {
                "stage": "stage1_5",
                "is_valid": validation_result.is_valid,
                "total_tasks": validation_result.total_tasks,
                "error_count": len([i for i in validation_result.issues if i.level.value == "error"]),
                "warning_count": len([i for i in validation_result.issues if i.level.value == "warning"]),
                "stats": validation_result.stats,
            }

            if validation_result.is_valid:
                self.logger.info(f"✅ Stage 1.5 completed")
                self.logger.info(f"   - Tasks validated: {validation_result.total_tasks}")
            else:
                self.logger.warning(f"⚠️  Stage 1.5 found validation issues")

        except Exception as e:
            self.logger.error(f"Stage 1.5 failed: {e}")
            self.results["stages"]["stage1_5"] = {"stage": "stage1_5", "error": str(e)}

        self.logger.info("")

    def stage2_quality_filtering(self, stage1_output: str) -> str:
        """Stage 2: Quality filtering."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 2: DataQualityFiltering - Quality Filtering")
        self.logger.info("=" * 80)

        stage_dir = os.path.join(self.output_dir, "stage2_filtered")
        os.makedirs(stage_dir, exist_ok=True)

        tasks_json = os.path.join(stage1_output, "tasks.json")

        try:
            filter_result = run_filter(
                input_path=tasks_json,
                output_dir=stage_dir,
                min_quality_score=self.config.get("min_quality_score", 3.0),
                preserve_rejected_tasks=True,
                log_level="INFO",
            )

            self.results["stages"]["stage2"] = {
                "stage": "stage2",
                "success": filter_result.success,
                "total_tasks": filter_result.total_tasks,
                "high_quality_tasks": filter_result.high_quality_tasks,
                "pass_rate": filter_result.pass_rate,
                "output_files": filter_result.output_files,
                "statistics": filter_result.statistics,
            }

            if not filter_result.success:
                raise RuntimeError(f"Quality filtering failed: {filter_result.errors}")

            self.logger.info(f"✅ Stage 2 completed")
            self.logger.info(f"   - Total tasks: {filter_result.total_tasks}")
            self.logger.info(f"   - High quality: {filter_result.high_quality_tasks}")
            self.logger.info(f"   - Pass rate: {filter_result.pass_rate:.2f}%")

        except Exception as e:
            self.logger.error(f"Stage 2 failed: {e}")
            self.results["stages"]["stage2"] = {"stage": "stage2", "success": False, "error": str(e)}
            raise

        self.logger.info("")
        return stage_dir

    def stage3_agent_simulation(
        self,
        stage2_output: str,
        agent_config: Dict[str, Any]
    ) -> str:
        """Stage 3: Run agent simulations."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 3: Agent Simulation")
        self.logger.info("=" * 80)

        stage_dir = os.path.join(self.output_dir, "stage3_simulation")
        os.makedirs(stage_dir, exist_ok=True)

        try:
            # Get configuration
            domain = agent_config.get("domain", "clinical_cardiology")
            agent_type = agent_config.get("agent", "llm_agent")
            model = agent_config.get("model", "gpt-4")
            num_tasks = agent_config.get("num_tasks", 10)  # Default: run on 10 tasks

            self.logger.info(f"Domain: {domain}")
            self.logger.info(f"Agent: {agent_type}")
            self.logger.info(f"Model: {model}")
            self.logger.info(f"Num tasks: {num_tasks}")
            self.logger.info("")

            # Note: Actual agent simulation would require calling tau2.run
            # This is a placeholder for the implementation
            self.logger.info("⚠️  Agent simulation requires tau2.run integration")
            self.logger.info("   This stage is prepared but not fully implemented")
            self.logger.info("   Please use: python -m tau2.cli run --domain {domain} --model {model}")

            self.results["stages"]["stage3"] = {
                "stage": "stage3",
                "success": True,
                "configured": True,
                "domain": domain,
                "agent": agent_type,
                "model": model,
                "num_tasks": num_tasks,
            }

            self.logger.info("✅ Stage 3 configured (requires manual tau2.cli run)")

        except Exception as e:
            self.logger.error(f"Stage 3 failed: {e}")
            self.results["stages"]["stage3"] = {"stage": "stage3", "success": False, "error": str(e)}
            raise

        self.logger.info("")
        return stage_dir

    def stage4_evaluation(
        self,
        stage3_output: str,
        evaluation_config: Dict[str, Any]
    ) -> None:
        """Stage 4: Evaluate agent performance."""
        self.logger.info("=" * 80)
        self.logger.info("STAGE 4: Evaluation - Clinical Assessment")
        self.logger.info("=" * 80)

        try:
            # Get configuration
            eval_type = evaluation_config.get("type", "ALL_WITH_CLINICAL")
            model = evaluation_config.get("model", "gpt-4")

            self.logger.info(f"Evaluation type: {eval_type}")
            self.logger.info(f"Model: {model}")
            self.logger.info("")

            # Note: Actual evaluation would require simulation results from stage 3
            self.logger.info("⚠️  Evaluation requires simulation results from Stage 3")
            self.logger.info("   This stage is prepared but requires simulation data")

            self.results["stages"]["stage4"] = {
                "stage": "stage4",
                "configured": True,
                "eval_type": eval_type,
                "model": model,
            }

            self.logger.info("✅ Stage 4 configured (requires simulation results)")

        except Exception as e:
            self.logger.error(f"Stage 4 failed: {e}")
            self.results["stages"]["stage4"] = {"stage": "stage4", "error": str(e)}

        self.logger.info("")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Master Clinical Benchmark Pipeline - Complete End-to-End Flow"
    )
    parser.add_argument(
        "input",
        help="Path to raw input data file"
    )
    parser.add_argument(
        "-o", "--output",
        default="./outputs/master",
        help="Output directory (default: ./outputs/master)"
    )
    parser.add_argument(
        "--run-agents",
        action="store_true",
        help="Run agent simulations (Stage 3)"
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate results (Stage 4)"
    )
    parser.add_argument(
        "--domain",
        default="clinical_cardiology",
        help="Clinical domain for agent simulation (default: clinical_cardiology)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="LLM model for agents (default: gpt-4)"
    )
    parser.add_argument(
        "--num-tasks",
        type=int,
        default=10,
        help="Number of tasks to simulate (default: 10)"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=3.0,
        help="Minimum quality score (default: 3.0)"
    )
    parser.add_argument(
        "--log-file",
        help="Log file path"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file, args.log_level)

    # Create pipeline
    pipeline = MasterPipeline(
        input_path=args.input,
        output_dir=args.output,
        config={"min_quality_score": args.min_quality}
    )

    # Run pipeline
    results = pipeline.run(
        run_agents=args.run_agents,
        evaluate_results=args.evaluate,
        agent_config={
            "domain": args.domain,
            "model": args.model,
            "num_tasks": args.num_tasks,
        },
        evaluation_config={
            "type": "ALL_WITH_CLINICAL",
            "model": args.model,
        }
    )

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    main()
