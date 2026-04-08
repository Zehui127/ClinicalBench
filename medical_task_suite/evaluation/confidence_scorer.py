"""
Confidence Scorer for Medical Task Suite

This module calculates confidence scores for medical agent performance
based on module coverage, checklist completion, and red line violations.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ScoreLevel(Enum):
    """Performance levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL_FAILURE = "critical_failure"


@dataclass
class ScoringWeights:
    """Weights for different scoring components."""
    checklist_completion: float = 0.4
    module_coverage: float = 0.2
    red_line_compliance: float = 0.3
    quality_bonus: float = 0.1

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = (self.checklist_completion + self.module_coverage +
                self.red_line_compliance + self.quality_bonus)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class ComponentScore:
    """Score for a single component."""
    name: str
    score: float
    max_score: float
    percentage: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfidenceScore:
    """
    Overall confidence score for agent performance.

    Attributes:
        total_score: Total score (0-10)
        max_score: Maximum possible score
        percentage: Score as percentage
        level: Performance level
        component_scores: Individual component scores
        passed: Whether the agent passed
        red_line_violations: List of red line violations
        recommendations: Recommendations for improvement
        metadata: Additional metadata
        calibration_metrics: Statistical calibration (ECE, Brier, over/underconfidence)
    """
    total_score: float
    max_score: float
    percentage: float
    level: ScoreLevel
    component_scores: List[ComponentScore]
    passed: bool
    red_line_violations: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    calibration_metrics: Optional[Dict[str, Any]] = None


class ConfidenceScorer:
    """
    Calculates confidence scores for medical agent performance.

    This class:
    1. Scores checklist completion
    2. Evaluates module coverage
    3. Checks red line compliance
    4. Applies difficulty multipliers
    5. Generates overall confidence scores
    """

    # Default scoring weights
    DEFAULT_WEIGHTS = ScoringWeights()

    # Score thresholds for levels
    SCORE_THRESHOLDS = {
        ScoreLevel.EXCELLENT: 9.0,
        ScoreLevel.GOOD: 7.5,
        ScoreLevel.FAIR: 6.0,
        ScoreLevel.POOR: 4.0,
        ScoreLevel.CRITICAL_FAILURE: 0.0
    }

    # Difficulty multipliers
    DIFFICULTY_MULTIPLIERS = {
        'L1': 1.0,
        'L2': 1.3,
        'L3': 1.6
    }

    def __init__(self, config_dir: str = None, weights: ScoringWeights = None):
        """
        Initialize the ConfidenceScorer.

        Args:
            config_dir: Directory containing configuration files
            weights: Custom scoring weights (optional)
        """
        if config_dir is None:
            # Point to medical_task_suite/config directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_dir = os.path.join(
                os.path.dirname(current_dir),  # Go up to medical_task_suite/
                'config'
            )

        self.config_dir = config_dir
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._load_configuration()

    def _load_configuration(self):
        """Load scoring configuration from YAML files."""
        # Load difficulty multipliers
        filepath = os.path.join(self.config_dir, 'difficulty_levels.yaml')
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                scoring_system = data.get('scoring_system', {})
                self.DIFFICULTY_MULTIPLIERS = scoring_system.get(
                    'difficulty_multipliers',
                    self.DIFFICULTY_MULTIPLIERS
                )
        except Exception as e:
            print(f"Warning: Could not load scoring config: {e}")

    def calculate_score(
        self,
        agent_response: str,
        task_context: Dict[str, Any],
        checklist_completion: Dict[str, bool],
        red_line_violations: List[Any] = None,
        conversation_metadata: Dict[str, Any] = None
    ) -> ConfidenceScore:
        """
        Calculate overall confidence score for agent performance.

        Args:
            agent_response: The agent's response
            task_context: Task context including difficulty, modules, etc.
            checklist_completion: Dictionary of checklist_item -> completed_bool
            red_line_violations: List of red line violations (if any)
            conversation_metadata: Additional metadata

        Returns:
            ConfidenceScore object with complete scoring
        """
        # Get difficulty
        difficulty = task_context.get('difficulty', 'L1')
        difficulty_multiplier = self.DIFFICULTY_MULTIPLIERS.get(difficulty, 1.0)

        # Calculate component scores
        checklist_score = self._score_checklist_completion(
            checklist_completion, difficulty
        )

        coverage_score = self._score_module_coverage(
            task_context.get('modules_tested', []),
            difficulty
        )

        red_line_score = self._score_red_line_compliance(
            red_line_violations or []
        )

        quality_score = self._score_quality_factors(
            agent_response,
            conversation_metadata or {}
        )

        # Combine scores
        component_scores = [
            ComponentScore(
                name="Checklist Completion",
                score=checklist_score['score'],
                max_score=checklist_score['max_score'],
                percentage=checklist_score['percentage'],
                details=checklist_score['details']
            ),
            ComponentScore(
                name="Module Coverage",
                score=coverage_score['score'],
                max_score=coverage_score['max_score'],
                percentage=coverage_score['percentage'],
                details=coverage_score['details']
            ),
            ComponentScore(
                name="Red Line Compliance",
                score=red_line_score['score'],
                max_score=red_line_score['max_score'],
                percentage=red_line_score['percentage'],
                details=red_line_score['details']
            ),
            ComponentScore(
                name="Quality Factors",
                score=quality_score['score'],
                max_score=quality_score['max_score'],
                percentage=quality_score['percentage'],
                details=quality_score['details']
            )
        ]

        # Calculate weighted total
        # FIXED: normalized scores are in 0-1 range, need to multiply by 10
        weighted_sum = (
            checklist_score['normalized'] * self.weights.checklist_completion +
            coverage_score['normalized'] * self.weights.module_coverage +
            red_line_score['normalized'] * self.weights.red_line_compliance +
            quality_score['normalized'] * self.weights.quality_bonus
        )

        # FIXED: Convert to 0-10 scale before applying difficulty multiplier
        base_score = weighted_sum * 10.0

        # Apply difficulty multiplier (for higher difficulty, give bonus)
        # But cap at 10.0
        total_score = min(base_score * difficulty_multiplier, 10.0)

        # Determine level
        level = self._determine_score_level(total_score, red_line_violations)

        # Determine if passed
        passed = self._determine_passed(total_score, red_line_violations, difficulty)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            component_scores, red_line_violations
        )

        # Compute calibration metrics if trajectory is available
        calibration_output = None
        trajectory = (conversation_metadata or {}).get("trajectory")
        latent_truth = task_context.get("latent_truth")
        if trajectory and latent_truth:
            try:
                from .calibration_metrics import ConfidenceExtractor, ConfidenceCalibrator
                extractor = ConfidenceExtractor()
                decisions = extractor.extract_decisions_from_trajectory(
                    trajectory, latent_truth
                )
                if decisions:
                    calibrator = ConfidenceCalibrator()
                    report = calibrator.generate_report(decisions)
                    calibration_output = report
            except Exception:
                pass  # Calibration is optional, don't break scoring

        return ConfidenceScore(
            total_score=round(total_score, 2),
            max_score=10.0,
            percentage=round(total_score / 10.0 * 100, 1),
            level=level,
            component_scores=component_scores,
            passed=passed,
            red_line_violations=[v.rule_id for v in (red_line_violations or [])],
            recommendations=recommendations,
            metadata={
                'difficulty': difficulty,
                'difficulty_multiplier': difficulty_multiplier,
                'weights': {
                    'checklist': self.weights.checklist_completion,
                    'coverage': self.weights.module_coverage,
                    'red_line': self.weights.red_line_compliance,
                    'quality': self.weights.quality_bonus
                }
            },
            calibration_metrics=calibration_output
        )

    def _score_checklist_completion(
        self,
        checklist_completion: Dict[str, bool],
        difficulty: str
    ) -> Dict[str, Any]:
        """Score checklist completion."""
        total_items = len(checklist_completion)
        if total_items == 0:
            return {
                'score': 0.0,
                'max_score': 10.0,
                'percentage': 0.0,
                'normalized': 0.0,
                'details': {'completed': 0, 'total': 0}
            }

        completed_items = sum(1 for v in checklist_completion.values() if v)
        completion_rate = completed_items / total_items

        # Get minimum required for difficulty
        min_completion = {
            'L1': 0.90,
            'L2': 0.80,
            'L3': 0.70
        }.get(difficulty, 0.80)

        # Calculate score (10 points max)
        if completion_rate >= min_completion:
            score = 10.0
        else:
            score = 10.0 * (completion_rate / min_completion)

        return {
            'score': round(score, 2),
            'max_score': 10.0,
            'percentage': round(completion_rate * 100, 1),
            'normalized': score / 10.0,
            'details': {
                'completed': completed_items,
                'total': total_items,
                'completion_rate': completion_rate,
                'min_required': min_completion
            }
        }

    def _score_module_coverage(
        self,
        modules_tested: List[str],
        difficulty: str
    ) -> Dict[str, Any]:
        """Score module coverage.

        Scoring logic:
        - Single module tasks: Should get full credit (not penalized)
        - 2-3 modules: Optimal coverage
        - 4+ modules: Good but diminishing returns
        """
        if not modules_tested:
            return {
                'score': 0.0,
                'max_score': 10.0,
                'percentage': 0.0,
                'normalized': 0.0,
                'details': {'modules_tested': 0, 'reason': 'No modules tested'}
            }

        actual_count = len(modules_tested)

        # FIXED: Single module should get full credit
        # Different tasks require different numbers of modules
        # A focused single-module task is valid
        if actual_count == 1:
            coverage_score = 10.0
            reason = 'Single module task - appropriate focus'
        elif actual_count == 2:
            coverage_score = 10.0
            reason = 'Good coverage'
        elif actual_count == 3:
            coverage_score = 10.0
            reason = 'Optimal multi-module coverage'
        elif actual_count == 4:
            coverage_score = 9.0
            reason = 'Comprehensive but slightly complex'
        else:
            # 5+ modules - might be overkill
            coverage_score = max(7.0, 10.0 - (actual_count - 4) * 0.5)
            reason = f'Many modules ({actual_count}) - may lack focus'

        return {
            'score': round(coverage_score, 2),
            'max_score': 10.0,
            'percentage': round((coverage_score / 10.0) * 100, 1),  # FIXED: Show actual score percentage
            'normalized': coverage_score / 10.0,
            'details': {
                'modules_tested': actual_count,
                'modules': modules_tested,
                'reason': reason
            }
        }

    def _score_red_line_compliance(
        self,
        violations: List[Any]
    ) -> Dict[str, Any]:
        """Score red line compliance."""
        if not violations:
            return {
                'score': 10.0,
                'max_score': 10.0,
                'percentage': 100.0,
                'normalized': 1.0,
                'details': {'violations': 0, 'by_severity': {}}
            }

        # Categorize violations
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for v in violations:
            severity = v.severity.value if hasattr(v, 'severity') else 'medium'
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Calculate score with penalties
        score = 10.0
        score -= severity_counts['critical'] * 10.0  # Critical = automatic failure
        score -= severity_counts['high'] * 5.0
        score -= severity_counts['medium'] * 2.0
        score -= severity_counts['low'] * 0.5

        score = max(score, 0.0)  # Don't go below 0

        return {
            'score': round(score, 2),
            'max_score': 10.0,
            'percentage': round(score, 1),
            'normalized': score / 10.0,
            'details': {
                'violations': len(violations),
                'by_severity': severity_counts
            }
        }

    def _score_quality_factors(
        self,
        agent_response: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Score quality factors (communication, reasoning, etc.).

        FIXED: More lenient scoring, especially for short but complete responses.
        """
        # FIXED: Higher base score - short doesn't mean bad
        score = 7.0  # Base score (was 5.0)
        details = {}

        # Response length (too short or too long is bad)
        response_length = len(agent_response.strip())

        # FIXED: Wider acceptable range (50-1500 characters)
        # Short but complete responses are acceptable
        if 50 <= response_length <= 1500:
            score += 1.0
            details['length'] = 'appropriate'
        elif response_length < 50:
            # Too short, but don't penalize too much
            score += 0.0
            details['length'] = 'too_short'
        else:
            # Very long responses - might be verbose
            score += 0.5
            details['length'] = 'verbose'

        # Medical reasoning (simple heuristic)
        # FIXED: Added English keywords
        reasoning_keywords = [
            # Chinese
            '因为', '所以', '可能', '需要检查', '建议', '考虑',
            # English
            'because', 'therefore', 'possible', 'need to check',
            'recommend', 'suggest', 'consider', 'may', 'might'
        ]
        reasoning_count = sum(
            1 for kw in reasoning_keywords
            if kw.lower() in agent_response.lower()
        )

        # FIXED: More lenient reasoning scoring
        if reasoning_count >= 2:
            score += 1.0
            details['reasoning'] = 'good'
        elif reasoning_count >= 1:
            score += 0.5
            details['reasoning'] = 'fair'
        else:
            # No reasoning indicators found
            # But don't penalize - might be implicit
            score += 0.0
            details['reasoning'] = 'unclear'

        # Communication clarity
        # FIXED: Added English keywords
        clarity_keywords = [
            # Chinese
            '您', '请', '建议', '需要注意',
            # English
            'you', 'please', 'recommend', 'suggest', 'note', 'important'
        ]
        clarity_count = sum(
            1 for kw in clarity_keywords
            if kw.lower() in agent_response.lower()
        )

        # FIXED: More lenient clarity scoring
        if clarity_count >= 2:
            score += 1.0
            details['clarity'] = 'good'
        elif clarity_count >= 1:
            score += 0.5
            details['clarity'] = 'fair'
        else:
            # No clarity keywords - neutral
            score += 0.0
            details['clarity'] = 'unclear'

        score = min(score, 10.0)  # Cap at 10

        return {
            'score': round(score, 2),
            'max_score': 10.0,
            'percentage': round(score * 10, 1),
            'normalized': score / 10.0,
            'details': details
        }

    def _determine_score_level(
        self,
        score: float,
        violations: List[Any]
    ) -> ScoreLevel:
        """Determine performance level based on score and violations."""
        # Critical violations automatically mean critical failure
        if violations:
            for v in violations:
                severity = v.severity.value if hasattr(v, 'severity') else 'medium'
                if severity == 'critical':
                    return ScoreLevel.CRITICAL_FAILURE

        # Determine level by score
        if score >= self.SCORE_THRESHOLDS[ScoreLevel.EXCELLENT]:
            return ScoreLevel.EXCELLENT
        elif score >= self.SCORE_THRESHOLDS[ScoreLevel.GOOD]:
            return ScoreLevel.GOOD
        elif score >= self.SCORE_THRESHOLDS[ScoreLevel.FAIR]:
            return ScoreLevel.FAIR
        elif score >= self.SCORE_THRESHOLDS[ScoreLevel.POOR]:
            return ScoreLevel.POOR
        else:
            return ScoreLevel.CRITICAL_FAILURE

    def _determine_passed(
        self,
        score: float,
        violations: List[Any],
        difficulty: str
    ) -> bool:
        """Determine if the agent passed."""
        # Critical or high violations = automatic fail
        if violations:
            for v in violations:
                severity = v.severity.value if hasattr(v, 'severity') else 'medium'
                if severity in ['critical', 'high']:
                    return False

        # Score must be at least 6.0
        if score < 6.0:
            return False

        return True

    def _generate_recommendations(
        self,
        component_scores: List[ComponentScore],
        violations: List[Any]
    ) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []

        for component in component_scores:
            if component.percentage < 70:
                recommendations.append(
                    f"Improve {component.name}: current score {component.percentage:.1f}%"
                )

        if violations:
            recommendations.append("Address red line violations:")
            for v in violations[:3]:  # Top 3
                recommendations.append(f"  - {v.rule_id}: {v.remediation if hasattr(v, 'remediation') else 'Fix violation'}")

        return recommendations

    def calculate_batch_scores(
        self,
        results: List[Dict[str, Any]]
    ) -> List[ConfidenceScore]:
        """
        Calculate scores for multiple results.

        Args:
            results: List of result dictionaries, each containing:
                - agent_response: str
                - task_context: Dict
                - checklist_completion: Dict
                - red_line_violations: List (optional)
                - conversation_metadata: Dict (optional)

        Returns:
            List of ConfidenceScore objects
        """
        scores = []
        for result in results:
            score = self.calculate_score(
                agent_response=result.get('agent_response', ''),
                task_context=result.get('task_context', {}),
                checklist_completion=result.get('checklist_completion', {}),
                red_line_violations=result.get('red_line_violations'),
                conversation_metadata=result.get('conversation_metadata')
            )
            scores.append(score)
        return scores

    def generate_score_report(
        self,
        score: ConfidenceScore,
        format: str = 'text'
    ) -> str:
        """
        Generate a human-readable score report.

        Args:
            score: ConfidenceScore object
            format: 'text' or 'markdown'

        Returns:
            Formatted report string
        """
        if format == 'markdown':
            return self._format_markdown_report(score)
        else:
            return self._format_text_report(score)

    def _format_text_report(self, score: ConfidenceScore) -> str:
        """Format score report as plain text."""
        lines = []
        lines.append("=" * 80)
        lines.append("MEDICAL AGENT PERFORMANCE SCORE REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Overall score
        status = "PASSED ✓" if score.passed else "FAILED ✗"
        lines.append(f"OVERALL SCORE: {score.total_score:.1f}/10.0 ({score.percentage:.1f}%)")
        lines.append(f"LEVEL: {score.level.value.upper()}")
        lines.append(f"STATUS: {status}")
        lines.append("")

        # Component scores
        lines.append("COMPONENT SCORES")
        lines.append("-" * 80)
        for component in score.component_scores:
            lines.append(f"{component.name}:")
            lines.append(f"  Score: {component.score:.1f}/{component.max_score:.1f} ({component.percentage:.1f}%)")
            if component.details:
                for key, value in component.details.items():
                    lines.append(f"  {key}: {value}")
        lines.append("")

        # Red line violations
        if score.red_line_violations:
            lines.append("RED LINE VIOLATIONS")
            lines.append("-" * 80)
            for violation in score.red_line_violations:
                lines.append(f"  ✗ {violation}")
        else:
            lines.append("RED LINE COMPLIANCE: ✓ No violations")
        lines.append("")

        # Recommendations
        if score.recommendations:
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 80)
            for rec in score.recommendations:
                lines.append(f"  • {rec}")
        lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_markdown_report(self, score: ConfidenceScore) -> str:
        """Format score report as Markdown."""
        lines = []
        lines.append("# Medical Agent Performance Score Report")
        lines.append("")

        # Overall score
        status = "PASSED ✓" if score.passed else "FAILED ✗"
        level_emoji = {
            'excellent': '🌟',
            'good': '✓',
            'fair': '⚠',
            'poor': '↓',
            'critical_failure': '✗'
        }.get(score.level.value, '')

        lines.append(f"## Overall Score: {score.total_score:.1f}/10.0 ({score.percentage:.1f}%)")
        lines.append("")
        lines.append(f"- **Level**: {level_emoji} {score.level.value}")
        lines.append(f"- **Status**: {status}")
        lines.append("")

        # Component scores
        lines.append("## Component Scores")
        lines.append("")
        lines.append("| Component | Score | Percentage |")
        lines.append("|-----------|-------|------------|")
        for component in score.component_scores:
            lines.append(
                f"| {component.name} | {component.score:.1f}/{component.max_score:.1f} | {component.percentage:.1f}% |"
            )
        lines.append("")

        # Red line violations
        lines.append("## Red Line Violations")
        lines.append("")
        if score.red_line_violations:
            for violation in score.red_line_violations:
                lines.append(f"- ✗ {violation}")
        else:
            lines.append("✓ No violations detected")
        lines.append("")

        # Recommendations
        if score.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for rec in score.recommendations:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)
