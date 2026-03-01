"""Converts ClinicalScenarios into tau2-bench Task objects."""

import sys
from pathlib import Path
from typing import List, Optional

# Ensure tau2 is importable
_tau2_src = Path(__file__).resolve().parent.parent / "tau2-bench" / "src"
if str(_tau2_src) not in sys.path:
    sys.path.insert(0, str(_tau2_src))

from tau2.data_model.tasks import (
    Action,
    Description,
    EvaluationCriteria,
    RewardType,
    StructuredUserInstructions,
    Task,
    UserScenario,
    make_task_id,
)

from UniClinicalDataEngine.models import ClinicalScenario


class ClinicalTaskBuilder:
    """Converts ClinicalScenario objects into tau2-bench Task objects."""

    def __init__(self, domain_name: str = "clinical"):
        self.domain_name = domain_name

    def build_task(self, scenario: ClinicalScenario) -> Task:
        """Convert a single ClinicalScenario into a tau2 Task.

        Args:
            scenario: The clinical scenario to convert.

        Returns:
            A tau2 Task object.
        """
        # Build structured user instructions
        known_info_parts = []
        patient = scenario.patient
        if patient.name:
            known_info_parts.append(f"Name: {patient.name}")
        if patient.age is not None:
            known_info_parts.append(f"Age: {patient.age}")
        if patient.sex:
            known_info_parts.append(f"Sex: {patient.sex}")
        if patient.medical_history:
            known_info_parts.append(
                f"Medical history: {', '.join(patient.medical_history)}"
            )
        if patient.current_medications:
            known_info_parts.append(
                f"Current medications: {', '.join(patient.current_medications)}"
            )
        if patient.allergies:
            known_info_parts.append(f"Allergies: {', '.join(patient.allergies)}")

        known_info = "\n".join(known_info_parts) if known_info_parts else None

        unknown_info_parts = []
        if not patient.diagnoses:
            unknown_info_parts.append("Diagnosis has not been determined yet")
        if not patient.lab_results:
            unknown_info_parts.append("Lab results are pending")
        unknown_info = (
            "\n".join(unknown_info_parts) if unknown_info_parts else None
        )

        instructions = StructuredUserInstructions(
            domain=self.domain_name,
            reason_for_call=scenario.reason_for_call,
            known_info=known_info,
            unknown_info=unknown_info,
            task_instructions=scenario.task_instructions,
        )

        # Build user scenario
        persona = self._build_persona(patient)
        user_scenario = UserScenario(persona=persona, instructions=instructions)

        # Build description
        description = Description(
            purpose=f"Clinical scenario: {scenario.reason_for_call}",
            notes=f"Difficulty: {scenario.difficulty or 'medium'}. "
            + (f"Domain: {scenario.clinical_domain}." if scenario.clinical_domain else ""),
        )

        # Build evaluation criteria
        evaluation_criteria = self._build_evaluation_criteria(scenario)

        return Task(
            id=scenario.scenario_id,
            description=description,
            user_scenario=user_scenario,
            evaluation_criteria=evaluation_criteria,
        )

    def build_tasks(self, scenarios: List[ClinicalScenario]) -> List[Task]:
        """Convert a list of ClinicalScenarios into tau2 Tasks.

        Args:
            scenarios: List of clinical scenarios.

        Returns:
            List of tau2 Task objects.
        """
        return [self.build_task(s) for s in scenarios]

    def _build_persona(self, patient) -> str:
        """Build a patient persona string."""
        parts = ["You are a patient visiting a healthcare provider."]
        if patient.age:
            parts.append(f"You are {patient.age} years old.")
        if patient.sex:
            parts.append(f"Your sex is {patient.sex}.")
        parts.append(
            "You communicate clearly about your symptoms and medical history when asked."
        )
        return " ".join(parts)

    def _build_evaluation_criteria(
        self, scenario: ClinicalScenario
    ) -> EvaluationCriteria:
        """Build EvaluationCriteria from a scenario."""
        actions = None
        if scenario.expected_actions:
            actions = []
            for act_dict in scenario.expected_actions:
                actions.append(
                    Action(
                        action_id=act_dict.get("action_id", make_task_id()),
                        name=act_dict["name"],
                        arguments=act_dict.get("arguments", {}),
                        compare_args=act_dict.get("compare_args"),
                        info=act_dict.get("info"),
                    )
                )

        nl_assertions = scenario.nl_assertions

        reward_basis = []
        if actions:
            reward_basis.append(RewardType.ACTION)
        if nl_assertions:
            reward_basis.append(RewardType.NL_ASSERTION)
        if not reward_basis:
            reward_basis = [RewardType.NL_ASSERTION]

        return EvaluationCriteria(
            actions=actions,
            nl_assertions=nl_assertions,
            reward_basis=reward_basis,
        )
