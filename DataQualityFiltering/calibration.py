"""Calibration: Pearson correlation between human and LLM scores."""

from typing import Dict, List, Optional, Tuple

from DataQualityFiltering.models import CalibrationResult, ReviewResult


def _pearsonr_fallback(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Pure-Python Pearson correlation coefficient with two-tailed p-value.

    Used as fallback when scipy is not available.
    """
    import math

    n = len(x)
    if n < 3:
        return 0.0, 1.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if std_x == 0 or std_y == 0:
        return 0.0, 1.0

    r = cov / (std_x * std_y)
    r = max(-1.0, min(1.0, r))

    # Approximate p-value using t-distribution
    if abs(r) == 1.0:
        p = 0.0
    else:
        t_stat = r * math.sqrt((n - 2) / (1 - r * r))
        # Approximate two-tailed p-value using normal approximation for large n
        # For small n, this is a rough estimate
        df = n - 2
        # Use a simple approximation
        p = 2.0 * (1.0 - _normal_cdf(abs(t_stat)))

    return r, p


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF using error function approximation."""
    import math

    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _compute_pearsonr(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson r, preferring scipy if available."""
    try:
        from scipy.stats import pearsonr
        r, p = pearsonr(x, y)
        return float(r), float(p)
    except ImportError:
        return _pearsonr_fallback(x, y)


class Calibrator:
    """Computes calibration metrics between human and LLM review scores."""

    def __init__(self, min_common_tasks: int = 3):
        self.min_common_tasks = min_common_tasks

    def calibrate(
        self,
        human_review: ReviewResult,
        llm_review: ReviewResult,
    ) -> CalibrationResult:
        """Compute Pearson correlation between human and LLM overall scores.

        Args:
            human_review: ReviewResult from human review.
            llm_review: ReviewResult from LLM review.

        Returns:
            CalibrationResult with correlation metrics.
        """
        human_map = human_review.get_score_map()
        llm_map = llm_review.get_score_map()

        common_ids = sorted(set(human_map.keys()) & set(llm_map.keys()))

        if len(common_ids) < self.min_common_tasks:
            return CalibrationResult(
                pearson_r=0.0,
                p_value=1.0,
                num_common_tasks=len(common_ids),
                calibrated=False,
            )

        # Overall scores
        human_scores = [human_map[tid].overall_score for tid in common_ids]
        llm_scores = [llm_map[tid].overall_score for tid in common_ids]

        r, p = _compute_pearsonr(human_scores, llm_scores)

        # Per-dimension correlations
        dimensions = [
            "clinical_accuracy",
            "scenario_realism",
            "evaluation_completeness",
            "difficulty_appropriateness",
        ]
        dim_corrs = {}
        for dim in dimensions:
            h_vals = [getattr(human_map[tid], dim) for tid in common_ids]
            l_vals = [getattr(llm_map[tid], dim) for tid in common_ids]
            dim_r, _ = _compute_pearsonr(h_vals, l_vals)
            dim_corrs[dim] = round(dim_r, 4)

        return CalibrationResult(
            pearson_r=round(r, 4),
            p_value=round(p, 6),
            num_common_tasks=len(common_ids),
            dimension_correlations=dim_corrs,
            calibrated=True,
        )
