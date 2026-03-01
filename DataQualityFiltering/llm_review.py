"""LLM-based semi-automatic task scoring using litellm."""

import json
from typing import Any, Dict, List, Optional

from DataQualityFiltering.models import ReviewResult, TaskScore


DEFAULT_GUIDANCE = """\
You are a clinical domain expert reviewing generated benchmark tasks for a clinical AI evaluation system.

For each task, evaluate it on 4 dimensions, scoring each from 0 to 5:

1. **Clinical Accuracy** (0-5): Is the clinical information medically accurate? Are symptoms, diagnoses, medications, and procedures consistent and realistic?

2. **Scenario Realism** (0-5): Is this a realistic patient encounter? Would this scenario occur in a real clinical setting?

3. **Evaluation Completeness** (0-5): Are the evaluation criteria (expected actions, assertions) comprehensive enough to properly evaluate an AI clinician's performance?

4. **Difficulty Appropriateness** (0-5): Is the difficulty level appropriate for benchmarking? Too easy tasks don't differentiate AI performance; too hard tasks may be unsolvable.

Respond ONLY with a JSON object in this exact format:
{
    "clinical_accuracy": <score>,
    "scenario_realism": <score>,
    "evaluation_completeness": <score>,
    "difficulty_appropriateness": <score>,
    "comments": "<brief explanation>"
}
"""


class LLMReviewer:
    """LLM-based task reviewer using litellm for scoring."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        guidance: Optional[str] = None,
    ):
        self.model = model
        self.guidance = guidance or DEFAULT_GUIDANCE

    def review(self, tasks: List[Dict[str, Any]]) -> ReviewResult:
        """Score all tasks using the LLM.

        Args:
            tasks: List of task dicts (parsed from tasks.json).

        Returns:
            ReviewResult with LLM scores.
        """
        import litellm

        scores = []
        for i, task in enumerate(tasks):
            task_id = task.get("id", f"task_{i}")
            task_json = json.dumps(task, indent=2, default=str)

            messages = [
                {"role": "system", "content": self.guidance},
                {
                    "role": "user",
                    "content": f"Please evaluate the following clinical benchmark task:\n\n{task_json}",
                },
            ]

            try:
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,
                )
                content = response.choices[0].message.content.strip()
                score_data = self._parse_response(content)
                score_data["task_id"] = task_id
                scores.append(TaskScore.model_validate(score_data))
            except Exception as e:
                print(f"Warning: LLM review failed for task {task_id}: {e}")
                # Assign neutral scores on failure
                scores.append(
                    TaskScore(
                        task_id=task_id,
                        clinical_accuracy=2.5,
                        scenario_realism=2.5,
                        evaluation_completeness=2.5,
                        difficulty_appropriateness=2.5,
                        comments=f"LLM review failed: {e}",
                    )
                )

        return ReviewResult(
            reviewer_type="llm", scores=scores, model_name=self.model
        )

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response into a score dict.

        Handles responses that may contain markdown code fences.
        """
        # Strip markdown code fences if present
        if "```" in content:
            lines = content.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            content = "\n".join(json_lines)

        data = json.loads(content)

        # Clamp scores to [0, 5]
        for key in [
            "clinical_accuracy",
            "scenario_realism",
            "evaluation_completeness",
            "difficulty_appropriateness",
        ]:
            if key in data:
                data[key] = max(0.0, min(5.0, float(data[key])))

        return data
