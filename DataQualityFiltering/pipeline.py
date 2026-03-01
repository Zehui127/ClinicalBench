"""DataQualityPipeline: orchestrates review mode selection and filtering."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from DataQualityFiltering.calibration import Calibrator
from DataQualityFiltering.filter import TaskFilter
from DataQualityFiltering.human_review import HumanReviewer
from DataQualityFiltering.llm_review import LLMReviewer
from DataQualityFiltering.models import (
    CalibrationResult,
    FilterConfig,
    ReviewResult,
)


class DataQualityPipeline:
    """Orchestrates quality review, calibration, and filtering.

    Supports three modes:
    - "human": Interactive human review only
    - "semi_auto": LLM review only
    - "both": Human review on a subset, LLM review on all, plus calibration
    """

    def __init__(self, config: FilterConfig):
        self.config = config

    def run(
        self,
        tasks: List[Dict[str, Any]],
        human_scores_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the full pipeline.

        Args:
            tasks: List of task dicts (loaded from tasks.json).
            human_scores_path: Optional path to pre-existing human scores file.

        Returns:
            Dict with keys:
                - accepted: list of accepted task dicts
                - rejected: list of rejected task dicts
                - review_scores: ReviewResult used for filtering
                - calibration: CalibrationResult (only in "both" mode)
        """
        mode = self.config.review_mode

        if mode == "human":
            return self._run_human(tasks, human_scores_path)
        elif mode == "semi_auto":
            return self._run_semi_auto(tasks)
        elif mode == "both":
            return self._run_both(tasks, human_scores_path)
        else:
            raise ValueError(
                f"Unknown review mode: {mode}. Use 'human', 'semi_auto', or 'both'."
            )

    def _run_human(
        self,
        tasks: List[Dict[str, Any]],
        human_scores_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run human-only review mode."""
        reviewer = HumanReviewer()

        if human_scores_path:
            review = reviewer.load_scores_from_file(human_scores_path)
        else:
            review = reviewer.review_interactive(tasks)

        task_filter = TaskFilter(threshold=self.config.threshold)
        accepted, rejected = task_filter.filter(tasks, review)

        return {
            "accepted": accepted,
            "rejected": rejected,
            "review_scores": review,
            "calibration": None,
        }

    def _run_semi_auto(
        self, tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run LLM-only review mode."""
        guidance = None
        if self.config.guidance_path:
            with open(self.config.guidance_path, "r") as f:
                guidance = f.read()

        reviewer = LLMReviewer(model=self.config.llm_model, guidance=guidance)
        review = reviewer.review(tasks)

        task_filter = TaskFilter(threshold=self.config.threshold)
        accepted, rejected = task_filter.filter(tasks, review)

        return {
            "accepted": accepted,
            "rejected": rejected,
            "review_scores": review,
            "calibration": None,
        }

    def _run_both(
        self,
        tasks: List[Dict[str, Any]],
        human_scores_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run both human and LLM review with calibration."""
        # Human review
        human_reviewer = HumanReviewer()
        if human_scores_path:
            human_review = human_reviewer.load_scores_from_file(human_scores_path)
        else:
            human_review = human_reviewer.review_interactive(tasks)

        # LLM review
        guidance = None
        if self.config.guidance_path:
            with open(self.config.guidance_path, "r") as f:
                guidance = f.read()

        llm_reviewer = LLMReviewer(
            model=self.config.llm_model, guidance=guidance
        )
        llm_review = llm_reviewer.review(tasks)

        # Calibration
        calibrator = Calibrator(
            min_common_tasks=self.config.min_calibration_tasks
        )
        calibration = calibrator.calibrate(human_review, llm_review)

        # Use LLM scores for filtering (calibrated by human review)
        task_filter = TaskFilter(threshold=self.config.threshold)
        accepted, rejected = task_filter.filter(tasks, llm_review)

        return {
            "accepted": accepted,
            "rejected": rejected,
            "review_scores": llm_review,
            "human_review": human_review,
            "calibration": calibration,
        }

    def run_and_save(
        self,
        tasks_path: str,
        output_path: str,
        human_scores_path: Optional[str] = None,
    ) -> Path:
        """Run the pipeline and save results.

        Args:
            tasks_path: Path to input tasks.json.
            output_path: Directory for output files.
            human_scores_path: Optional path to human scores file.

        Returns:
            Path to the output directory.
        """
        with open(tasks_path, "r") as f:
            tasks = json.load(f)

        results = self.run(tasks, human_scores_path)

        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save filtered tasks
        filtered_path = output_dir / "tasks_filtered.json"
        with open(filtered_path, "w") as f:
            json.dump(results["accepted"], f, indent=2, default=str)

        # Save review scores
        scores_path = output_dir / "review_scores.json"
        review_data = results["review_scores"].model_dump()
        with open(scores_path, "w") as f:
            json.dump(review_data, f, indent=2)

        # Save calibration report if available
        calibration = results.get("calibration")
        if calibration is not None:
            cal_path = output_dir / "calibration_report.json"
            with open(cal_path, "w") as f:
                json.dump(calibration.model_dump(), f, indent=2)

        return output_dir
