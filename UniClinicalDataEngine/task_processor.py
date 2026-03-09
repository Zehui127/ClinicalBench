"""Task post-processing utilities for UniClinicalDataEngine.

Provides deduplication and merging capabilities for clinical scenarios.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from collections import defaultdict
from difflib import SequenceMatcher
import re

from UniClinicalDataEngine.models import ClinicalScenario, PatientRecord


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison by lowercasing and removing extra whitespace."""
    if text is None:
        return ""
    return " ".join(text.lower().split())


def text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts using SequenceMatcher.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Similarity ratio between 0 and 1
    """
    return SequenceMatcher(None, text1, text2).ratio()


def extract_significant_words(text: str) -> Set[str]:
    """Extract significant words from text, ignoring common stopwords.

    Args:
        text: Input text

    Returns:
        Set of significant words
    """
    # Common medical stopwords
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall", "can",
        "need", "your", "you", "patient", "clinician", "please", "describe",
        "based", "medical", "information", "symptoms", "questions", "seeking",
        "attention", "main", "concern", "answer", "name", "years", "old",
    }

    # Extract words, convert to lowercase, remove punctuation
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return {w for w in words if w not in stopwords}


def token_overlap_similarity(text1: str, text2: str) -> float:
    """Calculate similarity based on significant word overlap.

    Args:
        text1: First text string
        text2: Second text string

    Returns:
        Jaccard similarity coefficient between 0 and 1
    """
    words1 = extract_significant_words(text1)
    words2 = extract_significant_words(text2)

    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union) if union else 0.0


def calculate_content_hash(scenario: ClinicalScenario) -> str:
    """Calculate a content-based hash for a scenario.

    Uses patient_id, chief_complaint, and significant words from
    task_instructions to create a signature.

    Args:
        scenario: ClinicalScenario to hash

    Returns:
        String hash representing the scenario's content signature
    """
    key_parts = [
        scenario.patient.patient_id,
        normalize_text(scenario.reason_for_call),
    ]

    # Add significant words from task instructions
    sig_words = extract_significant_words(scenario.task_instructions)
    key_parts.extend(sorted(sig_words))

    return "|".join(key_parts)


class TaskDeduplicator:
    """Detects and removes duplicate clinical scenarios."""

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        use_content_hash: bool = True,
        use_text_similarity: bool = True,
    ):
        """Initialize the deduplicator.

        Args:
            similarity_threshold: Threshold for considering two scenarios as duplicates (0-1)
            use_content_hash: Whether to use content hash for exact matching
            use_text_similarity: Whether to use text similarity for fuzzy matching
        """
        self.similarity_threshold = similarity_threshold
        self.use_content_hash = use_content_hash
        self.use_text_similarity = use_text_similarity

    def is_duplicate(
        self,
        scenario1: ClinicalScenario,
        scenario2: ClinicalScenario,
    ) -> bool:
        """Check if two scenarios are duplicates.

        Args:
            scenario1: First scenario to compare
            scenario2: Second scenario to compare

        Returns:
            True if scenarios are considered duplicates
        """
        # Exact match on patient_id and chief_complaint is strong indicator
        if (scenario1.patient.patient_id == scenario2.patient.patient_id and
            normalize_text(scenario1.reason_for_call) ==
            normalize_text(scenario2.reason_for_call)):
            return True

        if not self.use_text_similarity:
            return False

        # Calculate text similarity
        reason_similarity = text_similarity(
            normalize_text(scenario1.reason_for_call),
            normalize_text(scenario2.reason_for_call),
        )

        instructions_similarity = text_similarity(
            normalize_text(scenario1.task_instructions),
            normalize_text(scenario2.task_instructions),
        )

        # Also use token overlap for more robust comparison
        token_similarity = token_overlap_similarity(
            scenario1.task_instructions,
            scenario2.task_instructions,
        )

        # Combine similarity metrics
        combined_similarity = max(
            reason_similarity,
            instructions_similarity,
            token_similarity,
        )

        return combined_similarity >= self.similarity_threshold

    def deduplicate(
        self,
        scenarios: List[ClinicalScenario],
    ) -> List[ClinicalScenario]:
        """Remove duplicate scenarios from a list.

        Args:
            scenarios: List of scenarios to deduplicate

        Returns:
            Deduplicated list of scenarios
        """
        if not scenarios:
            return []

        # Track unique scenarios
        unique_scenarios: List[ClinicalScenario] = []
        content_hashes: Set[str] = set()

        for scenario in scenarios:
            # Check content hash first for quick exact matching
            if self.use_content_hash:
                content_hash = calculate_content_hash(scenario)
                if content_hash in content_hashes:
                    continue

            # Check against existing unique scenarios
            is_dup = False
            for existing in unique_scenarios:
                if self.is_duplicate(scenario, existing):
                    is_dup = True
                    break

            if not is_dup:
                unique_scenarios.append(scenario)
                if self.use_content_hash:
                    content_hashes.add(content_hash)

        return unique_scenarios


class TaskMerger:
    """Intelligently merges related simple tasks into medium-difficulty tasks."""

    def __init__(
        self,
        group_by_patient: bool = True,
        group_by_domain: bool = True,
        min_tasks_to_merge: int = 2,
        max_tasks_per_merge: int = 5,
    ):
        """Initialize the task merger.

        Args:
            group_by_patient: Whether to group tasks by patient_id
            group_by_domain: Whether to group tasks by clinical_domain
            min_tasks_to_merge: Minimum number of tasks required to merge
            max_tasks_per_merge: Maximum number of tasks to merge at once
        """
        self.group_by_patient = group_by_patient
        self.group_by_domain = group_by_domain
        self.min_tasks_to_merge = min_tasks_to_merge
        self.max_tasks_per_merge = max_tasks_per_merge

    def _get_group_key(self, scenario: ClinicalScenario) -> Tuple[str, ...]:
        """Get the grouping key for a scenario.

        Args:
            scenario: Scenario to get key for

        Returns:
            Tuple of grouping attributes
        """
        key_parts = []

        if self.group_by_patient:
            key_parts.append(scenario.patient.patient_id)

        if self.group_by_domain:
            domain = scenario.clinical_domain or "general"
            key_parts.append(domain)

        return tuple(key_parts)

    def _group_scenarios(
        self,
        scenarios: List[ClinicalScenario],
    ) -> Dict[Tuple[str, ...], List[ClinicalScenario]]:
        """Group scenarios by the configured criteria.

        Args:
            scenarios: List of scenarios to group

        Returns:
            Dictionary mapping group keys to scenario lists
        """
        groups = defaultdict(list)

        for scenario in scenarios:
            key = self._get_group_key(scenario)
            groups[key].append(scenario)

        return dict(groups)

    def _merge_scenarios(
        self,
        scenarios: List[ClinicalScenario],
    ) -> ClinicalScenario:
        """Merge multiple scenarios into a single medium-difficulty scenario.

        Args:
            scenarios: List of scenarios to merge (must have same patient)

        Returns:
            Merged scenario with medium difficulty
        """
        if not scenarios:
            raise ValueError("Cannot merge empty scenario list")

        if len(scenarios) == 1:
            return scenarios[0]

        # All scenarios should have the same patient
        patient = scenarios[0].patient
        scenario_ids = [s.scenario_id for s in scenarios]

        # Combine reasons for call
        reasons = [s.reason_for_call for s in scenarios if s.reason_for_call]
        combined_reason = "; ".join(reasons) if reasons else "Multiple concerns"

        # Build combined task instructions
        instruction_parts = []
        instruction_parts.append(
            "You are a patient seeking medical attention with multiple concerns. "
        )

        # Add patient information
        info_parts = []
        if patient.name:
            info_parts.append(f"Your name is {patient.name}.")
        if patient.age:
            info_parts.append(f"You are {patient.age} years old.")
        if patient.sex:
            info_parts.append(f"Sex: {patient.sex}.")
        if patient.medical_history:
            info_parts.append(
                f"Your medical history includes: {', '.join(patient.medical_history)}."
            )
        if patient.current_medications:
            info_parts.append(
                f"You are currently taking: {', '.join(patient.current_medications)}."
            )
        if patient.allergies:
            info_parts.append(
                f"You have allergies to: {', '.join(patient.allergies)}."
            )

        if info_parts:
            instruction_parts.append(" ".join(info_parts))

        # Add the multiple concerns
        instruction_parts.append(f"\n\nYou have {len(reasons)} main concerns:")
        for i, reason in enumerate(reasons, 1):
            instruction_parts.append(f"{i}. {reason}")

        instruction_parts.append(
            "\n\nDescribe all your symptoms and answer the clinician's questions "
            "based on your medical information. Be prepared to discuss each of "
            "your concerns."
        )

        combined_instructions = "".join(instruction_parts)

        # Combine expected actions
        combined_actions = []
        action_ids = set()
        for scenario in scenarios:
            if scenario.expected_actions:
                for action in scenario.expected_actions:
                    action_id = action.get("action_id", "")
                    if action_id not in action_ids:
                        combined_actions.append(action)
                        action_ids.add(action_id)

        # Combine NL assertions
        combined_assertions = []
        seen_assertions = set()
        for scenario in scenarios:
            if scenario.nl_assertions:
                for assertion in scenario.nl_assertions:
                    normalized = normalize_text(assertion)
                    if normalized not in seen_assertions:
                        combined_assertions.append(assertion)
                        seen_assertions.add(normalized)

        # Determine clinical domain (use most common or first non-None)
        domains = [s.clinical_domain for s in scenarios if s.clinical_domain]
        merged_domain = domains[0] if domains else None

        # Create merged scenario ID
        merged_id = f"merged_{'_'.join(scenario_ids[:3])}_{len(scenarios)}"

        return ClinicalScenario(
            scenario_id=merged_id,
            patient=patient,
            reason_for_call=combined_reason,
            task_instructions=combined_instructions,
            expected_actions=combined_actions if combined_actions else None,
            nl_assertions=combined_assertions if combined_assertions else None,
            difficulty="medium",
            clinical_domain=merged_domain,
        )

    def merge_tasks(
        self,
        scenarios: List[ClinicalScenario],
    ) -> List[ClinicalScenario]:
        """Merge related simple tasks into medium-difficulty tasks.

        Args:
            scenarios: List of scenarios to process

        Returns:
            List of scenarios with merged tasks
        """
        if not scenarios:
            return []

        # Separate simple tasks from others
        simple_tasks = [s for s in scenarios if s.difficulty == "easy"]
        other_tasks = [s for s in scenarios if s.difficulty != "easy"]

        if not simple_tasks:
            return scenarios

        # Group simple tasks by criteria
        grouped = self._group_scenarios(simple_tasks)

        # Process each group
        merged_results = list(other_tasks)

        for group_key, group_scenarios in grouped.items():
            if len(group_scenarios) < self.min_tasks_to_merge:
                # Not enough tasks to merge, keep original
                merged_results.extend(group_scenarios)
            else:
                # Split into chunks if too many tasks
                for i in range(0, len(group_scenarios), self.max_tasks_per_merge):
                    chunk = group_scenarios[i:i + self.max_tasks_per_merge]
                    if len(chunk) >= self.min_tasks_to_merge:
                        merged = self._merge_scenarios(chunk)
                        merged_results.append(merged)
                    else:
                        merged_results.extend(chunk)

        return merged_results


class ScenarioProcessor:
    """Main processor for deduplicating and merging scenarios."""

    def __init__(
        self,
        enable_deduplication: bool = True,
        enable_merging: bool = True,
        dedup_threshold: float = 0.75,
        merge_min_tasks: int = 2,
        merge_max_tasks: int = 5,
    ):
        """Initialize the scenario processor.

        Args:
            enable_deduplication: Whether to enable deduplication
            enable_merging: Whether to enable task merging
            dedup_threshold: Similarity threshold for deduplication
            merge_min_tasks: Minimum tasks to merge
            merge_max_tasks: Maximum tasks to merge at once
        """
        self.enable_deduplication = enable_deduplication
        self.enable_merging = enable_merging

        self.deduplicator = TaskDeduplicator(
            similarity_threshold=dedup_threshold,
        )

        self.merger = TaskMerger(
            group_by_patient=True,
            group_by_domain=True,
            min_tasks_to_merge=merge_min_tasks,
            max_tasks_per_merge=merge_max_tasks,
        )

    def process(
        self,
        scenarios: List[ClinicalScenario],
    ) -> List[ClinicalScenario]:
        """Process scenarios through deduplication and merging.

        Args:
            scenarios: List of scenarios to process

        Returns:
            Processed list of scenarios
        """
        if not scenarios:
            return []

        result = scenarios

        # Step 1: Deduplicate
        if self.enable_deduplication:
            result = self.deduplicator.deduplicate(result)

        # Step 2: Merge related tasks
        if self.enable_merging:
            result = self.merger.merge_tasks(result)

        return result

    def get_stats(
        self,
        original: List[ClinicalScenario],
        processed: List[ClinicalScenario],
    ) -> Dict[str, Any]:
        """Get statistics about the processing results.

        Args:
            original: Original scenarios before processing
            processed: Scenarios after processing

        Returns:
            Dictionary with processing statistics
        """
        return {
            "original_count": len(original),
            "processed_count": len(processed),
            "duplicates_removed": len(original) - len(processed)
                if len(processed) <= len(original) else 0,
            "tasks_merged": len(original) - len(processed)
                if len(processed) < len(original) else 0,
        }
