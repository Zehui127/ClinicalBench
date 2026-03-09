"""Process medxpertqa tasks with deduplication and merging features."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from collections import defaultdict

# Add the project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import functions directly from task_processor to avoid package __init__.py issues
from difflib import SequenceMatcher
import re

def normalize_text(text: str) -> str:
    """Normalize text for comparison by lowercasing and removing extra whitespace."""
    if text is None:
        return ""
    return " ".join(text.lower().split())

def text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts using SequenceMatcher."""
    return SequenceMatcher(None, text1, text2).ratio()


class MedXpertQATask:
    """Wrapper for medxpertqa task to provide ClinicalScenario-like interface."""

    def __init__(self, task_data: Dict[str, Any]):
        self.raw_data = task_data
        self.task_id = task_data.get("id", "")
        self.purpose = task_data.get("description", {}).get("purpose", "")
        self.notes = task_data.get("description", {}).get("notes", "")
        self.task_instructions = task_data.get("user_scenario", {}).get(
            "instructions", {}
        ).get("task_instructions", "")
        self.ticket = task_data.get("ticket", "")
        self.evaluation_criteria = task_data.get("evaluation_criteria")

    @property
    def patient_id(self) -> str:
        """Extract patient-like ID from task."""
        # For medxpertqa, use the task_id prefix or medical system
        if self.notes and "System:" in self.notes:
            system = self.notes.split("System:")[-1].strip().split(",")[0].strip()
            return system.lower()
        return self.task_id.split("_")[0] if "_" in self.task_id else "unknown"

    @property
    def clinical_domain(self) -> str:
        """Extract clinical domain from notes."""
        if self.notes and "System:" in self.notes:
            system = self.notes.split("System:")[-1].strip().split(",")[0].strip()
            return system.lower()
        return "general"

    @property
    def reason_for_call(self) -> str:
        """Return purpose as reason for call."""
        return self.purpose

    @property
    def difficulty(self) -> str:
        """Infer difficulty from task content."""
        # Simple tasks are straightforward QA
        instruction_lower = self.task_instructions.lower()
        if "which" in instruction_lower and "answer choices" in instruction_lower:
            return "easy"
        return "medium"

    def to_dict(self) -> Dict[str, Any]:
        """Convert back to dict format."""
        return self.raw_data


class MedXpertQADeduplicator:
    """Deduplicator adapted for medxpertqa format."""

    def __init__(self, similarity_threshold: float = 0.75):
        """Initialize the deduplicator.

        Args:
            similarity_threshold: Threshold for considering two tasks as duplicates (0-1)
        """
        self.similarity_threshold = similarity_threshold

    def is_duplicate(
        self,
        task1: MedXpertQATask,
        task2: MedXpertQATask,
    ) -> bool:
        """Check if two medxpertqa tasks are duplicates.

        Args:
            task1: First task to compare
            task2: Second task to compare

        Returns:
            True if tasks are considered duplicates
        """
        # Exact match on task_instructions is strong indicator
        if normalize_text(task1.task_instructions) == normalize_text(
            task2.task_instructions
        ):
            return True

        # Calculate text similarity on task instructions
        instructions_similarity = text_similarity(
            normalize_text(task1.task_instructions),
            normalize_text(task2.task_instructions),
        )

        # Also check ticket similarity
        ticket_similarity = 0.0
        if task1.ticket and task2.ticket:
            ticket_similarity = text_similarity(
                normalize_text(task1.ticket),
                normalize_text(task2.ticket),
            )

        # Use the higher similarity
        combined_similarity = max(instructions_similarity, ticket_similarity)

        return combined_similarity >= self.similarity_threshold

    def deduplicate(self, tasks: List[MedXpertQATask]) -> List[MedXpertQATask]:
        """Remove duplicate tasks from a list.

        Args:
            tasks: List of tasks to deduplicate

        Returns:
            Deduplicated list of tasks
        """
        if not tasks:
            return []

        unique_tasks: List[MedXpertQATask] = []

        for task in tasks:
            # Check against existing unique tasks
            is_dup = False
            for existing in unique_tasks:
                if self.is_duplicate(task, existing):
                    is_dup = True
                    break

            if not is_dup:
                unique_tasks.append(task)

        return unique_tasks


class MedXpertQAMerger:
    """Merger for medxpertqa tasks - groups related simple QA tasks."""

    def __init__(
        self,
        group_by_domain: bool = True,
        min_tasks_to_merge: int = 2,
        max_tasks_per_merge: int = 5,
    ):
        """Initialize the task merger.

        Args:
            group_by_domain: Whether to group tasks by clinical domain (system)
            min_tasks_to_merge: Minimum number of tasks required to merge
            max_tasks_per_merge: Maximum number of tasks to merge at once
        """
        self.group_by_domain = group_by_domain
        self.min_tasks_to_merge = min_tasks_to_merge
        self.max_tasks_per_merge = max_tasks_per_merge

    def _get_group_key(self, task: MedXpertQATask) -> tuple:
        """Get the grouping key for a task.

        Args:
            task: Task to get key for

        Returns:
            Tuple of grouping attributes
        """
        if self.group_by_domain:
            return (task.clinical_domain,)
        return ("all",)

    def _group_tasks(
        self,
        tasks: List[MedXpertQATask],
    ) -> Dict[tuple, List[MedXpertQATask]]:
        """Group tasks by the configured criteria.

        Args:
            tasks: List of tasks to group

        Returns:
            Dictionary mapping group keys to task lists
        """
        groups = defaultdict(list)

        for task in tasks:
            key = self._get_group_key(task)
            groups[key].append(task)

        return dict(groups)

    def _merge_tasks(
        self,
        tasks: List[MedXpertQATask],
    ) -> MedXpertQATask:
        """Merge multiple tasks into a single multi-part QA task.

        Args:
            tasks: List of tasks to merge

        Returns:
            Merged task
        """
        if not tasks:
            raise ValueError("Cannot merge empty task list")

        if len(tasks) == 1:
            return tasks[0]

        # Create merged task
        task_ids = [t.task_id for t in tasks]
        merged_id = f"merged_{'_'.join(task_ids[:3])}_len{len(tasks)}"

        # Combine notes to show all systems covered
        all_notes = [t.notes for t in tasks if t.notes]
        merged_notes = f"Merged from {len(tasks)} tasks: " + "; ".join(all_notes[:3])

        # Build multi-part question
        if len(tasks) <= 3:
            # For small merges, list all questions
            combined_instructions = (
                "Please answer the following "
                + str(len(tasks))
                + " medical questions:\n\n"
            )
            for i, task in enumerate(tasks, 1):
                question = task.task_instructions
                if len(question) > 300:
                    question = question[:300] + "..."
                combined_instructions += f"Question {i}: {question}\n\n"
        else:
            # For larger merges, summarize
            combined_instructions = (
                "Please answer "
                + str(len(tasks))
                + " medical questions covering the following topics:\n"
            )
            topic_counts = defaultdict(int)
            for task in tasks:
                domain = task.clinical_domain
                topic_counts[domain] += 1

            for domain, count in sorted(topic_counts.items()):
                combined_instructions += f"- {domain.capitalize()}: {count} question(s)\n"

        # Create merged task data
        merged_data = {
            "id": merged_id,
            "description": {
                "purpose": "Medical knowledge QA (merged task)",
                "relevant_policies": None,
                "notes": merged_notes,
            },
            "user_scenario": {
                "persona": None,
                "instructions": {
                    "task_instructions": combined_instructions,
                    "domain": "clinical",
                    "reason_for_call": "Multiple medical questions",
                },
            },
            "ticket": None,
            "initial_state": None,
            "evaluation_criteria": None,
            "annotations": {"merged_from": task_ids, "merge_count": len(tasks)},
        }

        return MedXpertQATask(merged_data)

    def merge_tasks(
        self,
        tasks: List[MedXpertQATask],
    ) -> List[MedXpertQATask]:
        """Merge related simple tasks.

        Args:
            tasks: List of tasks to process

        Returns:
            List of tasks with merged tasks
        """
        if not tasks:
            return []

        # Separate simple tasks from others
        simple_tasks = [t for t in tasks if t.difficulty == "easy"]
        other_tasks = [t for t in tasks if t.difficulty != "easy"]

        if not simple_tasks:
            return tasks

        # Group simple tasks by criteria
        grouped = self._group_tasks(simple_tasks)

        # Process each group
        merged_results = list(other_tasks)

        for group_key, group_tasks in grouped.items():
            if len(group_tasks) < self.min_tasks_to_merge:
                # Not enough tasks to merge, keep original
                merged_results.extend(group_tasks)
            else:
                # Split into chunks if too many tasks
                for i in range(0, len(group_tasks), self.max_tasks_per_merge):
                    chunk = group_tasks[i : i + self.max_tasks_per_merge]
                    if len(chunk) >= self.min_tasks_to_merge:
                        merged = self._merge_tasks(chunk)
                        merged_results.append(merged)
                    else:
                        merged_results.extend(chunk)

        return merged_results


def process_medxpertqa(
    input_file: str,
    output_file: str,
    dedup_threshold: float = 0.75,
    enable_dedup: bool = True,
    enable_merge: bool = True,
    merge_min: int = 2,
    merge_max: int = 5,
):
    """Process medxpertqa tasks with deduplication and merging.

    Args:
        input_file: Path to input tasks.json
        output_file: Path to output processed tasks.json
        dedup_threshold: Similarity threshold for deduplication
        enable_dedup: Whether to enable deduplication
        enable_merge: Whether to enable merging
        merge_min: Minimum tasks to merge
        merge_max: Maximum tasks to merge at once
    """
    print("=" * 60)
    print("MedXpertQA Task Processing")
    print("=" * 60)

    # Load input data
    print(f"\n[1/4] Loading tasks from: {input_file}")
    with open(input_file, "r", encoding="utf-8-sig") as f:
        raw_data = json.load(f)

    original_count = len(raw_data)
    print(f"Loaded {original_count} tasks")

    # Convert to wrapper objects
    tasks = [MedXpertQATask(t) for t in raw_data]

    # Get statistics by difficulty
    easy_count = sum(1 for t in tasks if t.difficulty == "easy")
    medium_count = sum(1 for t in tasks if t.difficulty == "medium")
    print(f"  - Easy tasks: {easy_count}")
    print(f"  - Medium tasks: {medium_count}")

    # Get statistics by domain
    domain_counts = defaultdict(int)
    for task in tasks:
        domain_counts[task.clinical_domain] += 1
    print(f"  - Clinical domains: {len(domain_counts)}")
    top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for domain, count in top_domains:
        print(f"      * {domain}: {count} tasks")

    # Step 2: Deduplicate
    print(f"\n[2/4] Deduplication (threshold: {dedup_threshold})")
    if enable_dedup:
        deduplicator = MedXpertQADeduplicator(
            similarity_threshold=dedup_threshold,
        )
        tasks = deduplicator.deduplicate(tasks)
        dedup_count = original_count - len(tasks)
        print(f"Duplicates removed: {dedup_count}")
        print(f"Remaining tasks: {len(tasks)}")
    else:
        print("Deduplication disabled")

    # Step 3: Merge
    print(f"\n[3/4] Merging related tasks (min: {merge_min}, max: {merge_max})")
    if enable_merge:
        merger = MedXpertQAMerger(
            group_by_domain=True,
            min_tasks_to_merge=merge_min,
            max_tasks_per_merge=merge_max,
        )
        before_merge = len(tasks)
        tasks = merger.merge_tasks(tasks)
        merged_groups = before_merge - len(tasks)
        print(f"Tasks merged into {merged_groups} group(s)")
        print(f"Final task count: {len(tasks)}")
    else:
        print("Merging disabled")

    # Step 4: Save results
    print(f"\n[4/4] Saving processed tasks to: {output_file}")
    output_data = [t.to_dict() for t in tasks]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Generate report
    print("\n" + "=" * 60)
    print("Processing Report")
    print("=" * 60)
    print(f"Original tasks:     {original_count}")
    if enable_dedup:
        print(f"Duplicates removed:  {dedup_count}")
    if enable_merge:
        print(f"Tasks merged:        {merged_groups}")
    print(f"Final tasks:        {len(tasks)}")
    print(f"Reduction rate:     {(1 - len(tasks) / original_count) * 100:.1f}%")
    print("=" * 60)

    # Show example merged task
    merged_tasks = [t for t in tasks if t.task_id.startswith("merged_")]
    if merged_tasks:
        print("\n" + "=" * 60)
        print("Example Merged Task")
        print("=" * 60)
        example = merged_tasks[0]
        print(f"\nTask ID: {example.task_id}")
        print(f"Notes: {example.notes}")
        print(f"\nInstructions:\n{example.task_instructions[:600]}...")
        if example.raw_data.get("annotations"):
            print(f"\nAnnotations: {example.annotations}")

    print("\nProcessing complete!")

    return {
        "original_count": original_count,
        "final_count": len(tasks),
        "duplicates_removed": dedup_count if enable_dedup else 0,
        "merged_groups": merged_groups if enable_merge else 0,
    }


if __name__ == "__main__":
    input_path = "data/processed/medxpertqa/tasks.json"
    output_path = "data/processed/medxpertqa/tasks_processed.json"

    stats = process_medxpertqa(
        input_file=input_path,
        output_file=output_path,
        dedup_threshold=0.75,
        enable_dedup=True,
        enable_merge=True,
        merge_min=2,
        merge_max=5,
    )
