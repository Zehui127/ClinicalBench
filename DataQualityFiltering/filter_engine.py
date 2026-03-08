#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quality Filter Engine for Clinical Tasks
临床任务质量过滤引擎

Filters clinical tasks based on quality scores and criteria.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable


@dataclass
class FilterConfig:
    """Configuration for quality filtering."""

    # Input/Output paths
    input_path: str = ""
    output_dir: str = "./outputs/stage2_output"

    # Quality thresholds
    min_quality_score: float = 3.5
    min_tool_count: int = 1
    max_tool_count: int = 8
    min_content_length: int = 50

    # Filtering options
    auto_calculate_scores: bool = True
    preserve_rejected_tasks: bool = True
    categorize_by_department: bool = True

    # Scoring weights
    tool_count_weight: float = 0.6
    content_length_weight: float = 0.02
    clinical_accuracy_weight: float = 1.0
    scenario_realism_weight: float = 1.0

    # Logging
    log_level: str = "INFO"


@dataclass
class FilterResult:
    """Result of quality filtering operation."""

    success: bool
    total_tasks: int = 0
    high_quality_tasks: int = 0
    failed_tasks: int = 0
    pass_rate: float = 0.0

    filtered_tasks: List[Dict] = field(default_factory=list)
    rejected_tasks: List[Dict] = field(default_factory=list)
    review_scores: List[Dict] = field(default_factory=list)

    statistics: Dict[str, Any] = field(default_factory=dict)

    output_files: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class QualityFilter:
    """
    Quality Filter for Clinical Tasks
    临床任务质量过滤器

    Filters clinical tasks based on configurable quality criteria.
    """

    def __init__(self, config: Optional[FilterConfig] = None):
        """
        Initialize the quality filter.

        Args:
            config: Filter configuration
        """
        self.config = config or FilterConfig()
        self._setup_logging()
        self._setup_output_directory()

        # Statistics tracking
        self.stats = {
            "by_department": {},
            "by_difficulty": {},
            "by_quality_range": {},
            "rejection_reasons": {},
        }

    def _setup_logging(self):
        """Configure logging."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))

        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _setup_output_directory(self):
        """Create output directory if it doesn't exist."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        self.logger.info(f"Output directory: {self.config.output_dir}")

    def load_tasks(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Load clinical tasks from file.

        Args:
            path: Path to input file (uses config.input_path if not provided)

        Returns:
            List of task dictionaries
        """
        input_path = path or self.config.input_path

        if not input_path or not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        self.logger.info(f"Loading tasks from: {input_path}")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different formats
        if isinstance(data, dict):
            tasks = data.get("tasks", data.get("data", [data]))
        elif isinstance(data, list):
            tasks = data
        else:
            raise ValueError(f"Unexpected data format: {type(data)}")

        self.logger.info(f"Loaded {len(tasks)} tasks")

        return tasks

    def calculate_quality_score(self, task: Dict[str, Any]) -> float:
        """
        Calculate quality score for a task.

        Args:
            task: Task dictionary

        Returns:
            Quality score (0-5)
        """
        score = 0.0

        # Tool count contribution
        tool_count = len(task.get("tool_call_requirements", {}).get("required_tools", []))
        tool_score = min(5.0, tool_count * self.config.tool_count_weight)

        # Content length contribution
        content = str(task.get("clinical_scenario", "")) + str(task.get("description", ""))
        content_score = min(5.0, len(content) * self.config.content_length_weight / 100)

        # Base score
        base_score = (tool_score + content_score) / 2

        # Apply weights
        score = (
            base_score * self.config.tool_count_weight +
            base_score * self.config.clinical_accuracy_weight +
            base_score * self.config.scenario_realism_weight
        ) / 3

        return min(5.0, score)

    def validate_task(self, task: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a task against quality criteria.

        Args:
            task: Task dictionary

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        if not task.get("id") and not task.get("task_id"):
            errors.append("Missing task identifier")

        if not task.get("description"):
            errors.append("Missing description")

        # Check tool count
        tool_count = len(task.get("tool_call_requirements", {}).get("required_tools", []))
        if tool_count < self.config.min_tool_count:
            errors.append(f"Insufficient tools: {tool_count} < {self.config.min_tool_count}")

        if tool_count > self.config.max_tool_count:
            errors.append(f"Too many tools: {tool_count} > {self.config.max_tool_count}")

        # Check content length
        content_length = len(str(task.get("clinical_scenario", "")))
        if content_length < self.config.min_content_length:
            errors.append(f"Insufficient content: {content_length} < {self.config.min_content_length}")

        return len(errors) == 0, errors

    def filter_tasks(self, tasks: List[Dict[str, Any]]) -> FilterResult:
        """
        Filter tasks based on quality criteria.

        Args:
            tasks: List of task dictionaries

        Returns:
            Filter result
        """
        result = FilterResult(success=True)
        result.start_time = datetime.now()
        result.total_tasks = len(tasks)

        self.logger.info("=" * 60)
        self.logger.info("QUALITY FILTERING")
        self.logger.info("=" * 60)
        self.logger.info(f"Total tasks to filter: {len(tasks)}")
        self.logger.info(f"Minimum quality score: {self.config.min_quality_score}")

        for idx, task in enumerate(tasks, 1):
            try:
                # Normalize task
                if not isinstance(task, dict):
                    self.logger.warning(f"Task {idx} is not a dictionary, skipping")
                    continue

                # Get task ID
                task_id = task.get("id") or task.get("task_id", f"task_{idx}")

                # Validate task structure
                is_valid, validation_errors = self.validate_task(task)

                # Calculate quality score
                quality_score = self.calculate_quality_score(task)
                pass_filter = quality_score >= self.config.min_quality_score

                # Create review score entry
                review_score = {
                    "task_id": task_id,
                    "quality_score": round(quality_score, 2),
                    "tool_count": len(task.get("tool_call_requirements", {}).get("required_tools", [])),
                    "content_length": len(str(task.get("clinical_scenario", ""))),
                    "pass_filter": pass_filter,
                    "validation_errors": validation_errors,
                    "difficulty_level": self._classify_difficulty(quality_score),
                }

                result.review_scores.append(review_score)

                # Update statistics
                self._update_statistics(task, quality_score, pass_filter)

                # Filter task
                if pass_filter and is_valid:
                    result.filtered_tasks.append(task)
                    result.high_quality_tasks += 1
                else:
                    result.rejected_tasks.append(task)
                    result.failed_tasks += 1

                    # Track rejection reasons
                    if not pass_filter:
                        reason = f"Low quality score ({quality_score:.2f})"
                    else:
                        reason = "; ".join(validation_errors)

                    self.stats["rejection_reasons"][reason] = (
                        self.stats["rejection_reasons"].get(reason, 0) + 1
                    )

                # Progress update
                if idx % 100 == 0 or idx == len(tasks):
                    progress = (idx / len(tasks)) * 100
                    self.logger.info(
                        f"Progress: {idx}/{len(tasks)} ({progress:.1f}%) | "
                        f"High quality: {result.high_quality_tasks} | "
                        f"Rejected: {result.failed_tasks}"
                    )

            except Exception as e:
                self.logger.error(f"Error processing task {idx}: {e}")
                result.errors.append(f"Task {idx}: {e}")
                continue

        # Calculate final statistics
        result.pass_rate = (
            (result.high_quality_tasks / result.total_tasks * 100)
            if result.total_tasks > 0 else 0
        )

        result.statistics = self.stats.copy()
        result.end_time = datetime.now()

        self.logger.info("=" * 60)
        self.logger.info("FILTERING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"High quality tasks: {result.high_quality_tasks}")
        self.logger.info(f"Failed tasks: {result.failed_tasks}")
        self.logger.info(f"Pass rate: {result.pass_rate:.2f}%")

        return result

    def _classify_difficulty(self, quality_score: float) -> str:
        """Classify task difficulty based on quality score."""
        if quality_score < 2:
            return "easy"
        elif quality_score < 4:
            return "moderate"
        else:
            return "hard"

    def _update_statistics(
        self,
        task: Dict[str, Any],
        quality_score: float,
        pass_filter: bool
    ):
        """Update filtering statistics."""
        # Extract department
        department = self._extract_department(task)
        self.stats["by_department"][department] = (
            self.stats["by_department"].get(department, 0) + 1
        )

        # Extract difficulty
        difficulty = self._classify_difficulty(quality_score)
        self.stats["by_difficulty"][difficulty] = (
            self.stats["by_difficulty"].get(difficulty, 0) + 1
        )

        # Quality range
        if quality_score < 2:
            range_key = "0-2"
        elif quality_score < 3:
            range_key = "2-3"
        elif quality_score < 4:
            range_key = "3-4"
        else:
            range_key = "4-5"

        self.stats["by_quality_range"][range_key] = (
            self.stats["by_quality_range"].get(range_key, 0) + 1
        )

    def _extract_department(self, task: Dict[str, Any]) -> str:
        """Extract department from task."""
        # Direct department field
        dept = task.get("department", "")

        if dept:
            return dept

        # Try to extract from other fields
        task_id = str(task.get("id") or task.get("task_id", "")).lower()
        diagnosis = str(task.get("diagnosis", "")).lower()
        description = str(task.get("description", "")).lower()

        # Department keywords
        if any(kw in task_id or kw in diagnosis or kw in description
               for kw in ["cardio", "heart", "chest_pain"]):
            return "cardiology"
        elif any(kw in task_id or kw in diagnosis or kw in description
                 for kw in ["nephro", "renal", "kidney", "ckd"]):
            return "nephrology"
        elif any(kw in task_id or kw in diagnosis or kw in description
                 for kw in ["gastro", "stomach", "ulcer", "digestive"]):
            return "gastroenterology"

        return "general_practice"

    def save_results(self, result: FilterResult) -> FilterResult:
        """
        Save filtering results to output files.

        Args:
            result: Filter result

        Returns:
            Updated filter result with output file paths
        """
        self.logger.info("Saving filtering results...")

        # Save filtered tasks
        filtered_path = os.path.join(self.config.output_dir, "tasks_filtered.json")
        with open(filtered_path, "w", encoding="utf-8") as f:
            json.dump(result.filtered_tasks, f, indent=2, ensure_ascii=False)
        result.output_files["filtered_tasks"] = filtered_path
        self.logger.info(f"Saved filtered tasks: {filtered_path}")

        # Save review scores
        scores_path = os.path.join(self.config.output_dir, "review_scores.json")
        with open(scores_path, "w", encoding="utf-8") as f:
            json.dump(result.review_scores, f, indent=2, ensure_ascii=False)
        result.output_files["review_scores"] = scores_path
        self.logger.info(f"Saved review scores: {scores_path}")

        # Save rejected tasks (if any)
        if result.rejected_tasks and self.config.preserve_rejected_tasks:
            rejected_path = os.path.join(self.config.output_dir, "tasks_rejected.json")
            with open(rejected_path, "w", encoding="utf-8") as f:
                json.dump(result.rejected_tasks, f, indent=2, ensure_ascii=False)
            result.output_files["rejected_tasks"] = rejected_path
            self.logger.info(f"Saved rejected tasks: {rejected_path}")

        # Save statistics
        stats_path = os.path.join(self.config.output_dir, "filter_statistics.json")
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(result.statistics, f, indent=2, ensure_ascii=False)
        result.output_files["statistics"] = stats_path
        self.logger.info(f"Saved statistics: {stats_path}")

        return result

    def run(self, input_path: Optional[str] = None) -> FilterResult:
        """
        Run the complete quality filtering pipeline.

        Args:
            input_path: Path to input file (uses config.input_path if not provided)

        Returns:
            Filter result
        """
        try:
            # Load tasks
            tasks = self.load_tasks(input_path)

            # Filter tasks
            result = self.filter_tasks(tasks)

            # Save results
            result = self.save_results(result)

            result.success = not result.errors

            return result

        except Exception as e:
            self.logger.error(f"Filtering failed: {e}")
            import traceback
            traceback.print_exc()

            return FilterResult(
                success=False,
                errors=[str(e)]
            )


def run_filter(
    input_path: str,
    output_dir: str = "./outputs/stage2_output",
    min_quality_score: float = 3.5,
    **kwargs
) -> FilterResult:
    """
    Convenience function to run quality filtering.

    Args:
        input_path: Path to input file
        output_dir: Output directory path
        min_quality_score: Minimum quality score threshold
        **kwargs: Additional configuration

    Returns:
        Filter result
    """
    config = FilterConfig(
        input_path=input_path,
        output_dir=output_dir,
        min_quality_score=min_quality_score,
        **kwargs
    )

    filter_engine = QualityFilter(config)
    return filter_engine.run()
