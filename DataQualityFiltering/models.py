"""Pydantic models for DataQualityFiltering."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskScore(BaseModel):
    """Scores for a single task across quality dimensions."""

    task_id: str = Field(description="The task ID being scored")
    clinical_accuracy: float = Field(
        description="Clinical accuracy score (0-5)", ge=0, le=5
    )
    scenario_realism: float = Field(
        description="Scenario realism score (0-5)", ge=0, le=5
    )
    evaluation_completeness: float = Field(
        description="Evaluation criteria completeness score (0-5)", ge=0, le=5
    )
    difficulty_appropriateness: float = Field(
        description="Difficulty appropriateness score (0-5)", ge=0, le=5
    )
    comments: Optional[str] = Field(
        default=None, description="Optional reviewer comments"
    )

    @property
    def overall_score(self) -> float:
        """Compute the mean score across all 4 dimensions."""
        return (
            self.clinical_accuracy
            + self.scenario_realism
            + self.evaluation_completeness
            + self.difficulty_appropriateness
        ) / 4.0


class ReviewResult(BaseModel):
    """Collection of scores from a review pass."""

    reviewer_type: str = Field(
        description="Type of reviewer: 'human' or 'llm'"
    )
    scores: List[TaskScore] = Field(
        description="List of task scores from this review"
    )
    model_name: Optional[str] = Field(
        default=None, description="LLM model used (if reviewer_type is 'llm')"
    )

    def get_score_map(self) -> Dict[str, TaskScore]:
        """Get a dict mapping task_id to TaskScore."""
        return {s.task_id: s for s in self.scores}


class CalibrationResult(BaseModel):
    """Result of calibrating LLM scores against human scores."""

    pearson_r: float = Field(
        description="Pearson correlation coefficient"
    )
    p_value: float = Field(description="P-value of the correlation")
    num_common_tasks: int = Field(
        description="Number of tasks with both human and LLM scores"
    )
    dimension_correlations: Optional[Dict[str, float]] = Field(
        default=None,
        description="Per-dimension Pearson correlations",
    )
    calibrated: bool = Field(
        description="Whether calibration meets minimum thresholds"
    )


class FilterConfig(BaseModel):
    """Configuration for the quality filtering pipeline."""

    threshold: float = Field(
        default=3.0,
        description="Minimum overall score to accept a task (0-5)",
        ge=0,
        le=5,
    )
    review_mode: str = Field(
        default="semi_auto",
        description="Review mode: 'human', 'semi_auto', or 'both'",
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model to use for automated review",
    )
    guidance_path: Optional[str] = Field(
        default=None,
        description="Path to custom guidance prompt file for LLM review",
    )
    min_calibration_tasks: int = Field(
        default=3,
        description="Minimum number of common tasks required for calibration",
    )
    min_calibration_r: float = Field(
        default=0.5,
        description="Minimum Pearson r to consider calibration acceptable",
    )
