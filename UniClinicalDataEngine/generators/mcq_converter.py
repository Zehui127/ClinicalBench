"""MCQ to Dialogue Converter.

This module converts medical multiple-choice questions into clinical
consultation dialogue data compatible with tau2 format.
"""

from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

# Import local modules
try:
    from .base_generator import (
        BaseGenerator,
        PatientProfile,
        ConsultationDialogue,
        DialogueMessage,
        DialogueTurn,
    )
    from .template_manager import TemplateManager, DialogueBuilder
    from .utils import (
        extract_entities_from_text,
        parse_notes,
        map_to_tau2_domain,
        determine_gender_from_context,
        generate_patient_mrn,
        generate_patient_name,
        infer_difficulty,
    )
except ImportError:
    # Direct imports for standalone usage
    generators_dir = Path(__file__).parent
    sys.path.insert(0, str(generators_dir))
    from base_generator import (
        BaseGenerator,
        PatientProfile,
        ConsultationDialogue,
        DialogueMessage,
        DialogueTurn,
    )
    from template_manager import TemplateManager, DialogueBuilder
    from utils import (
        extract_entities_from_text,
        parse_notes,
        map_to_tau2_domain,
        determine_gender_from_context,
        generate_patient_mrn,
        generate_patient_name,
        infer_difficulty,
    )


class MCQToDialogueConverter(BaseGenerator):
    """Converts medical MCQs to consultation dialogues.

    This converter transforms multiple-choice medical questions into
    realistic patient-clinician consultation dialogues.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the MCQ converter.

        Args:
            config: Optional configuration with keys:
                - dialogue_style: "diagnostic", "treatment", "auto" (default)
                - num_turns: Target number of dialogue turns (default: 5-7)
                - include_rationales: Whether to include answer rationales (default: False)
        """
        super().__init__(config)
        self.template_manager = TemplateManager()
        self.dialogue_builder = DialogueBuilder(self.template_manager)

        # Configuration
        self.dialogue_style = config.get("dialogue_style", "auto") if config else "auto"
        self.target_turns = config.get("num_turns", 6) if config else 6
        self.include_rationales = config.get("include_rationales", False) if config else False

    def generate(self, source_data: Dict[str, Any]) -> ConsultationDialogue:
        """Generate a consultation dialogue from MCQ data.

        Args:
            source_data: MCQ task dictionary with fields:
                - id: Task identifier
                - description: {purpose, notes}
                - user_scenario: {instructions: {task_instructions}}

        Returns:
            A ConsultationDialogue object
        """
        # Extract task metadata
        task_id = source_data.get("id", "unknown")
        notes = source_data.get("description", {}).get("notes", "")
        task_instructions = source_data.get("user_scenario", {}).get("instructions", {}).get("task_instructions", "")

        # Parse notes to get task type and system
        parsed_notes = parse_notes(notes)
        task_type = parsed_notes["task_type"]
        system = parsed_notes["system"]

        # Extract entities from the question text
        entities = extract_entities_from_text(task_instructions)

        # Map to tau2 domain
        department = map_to_tau2_domain(system)

        # Build patient profile
        patient_profile = self._build_patient_profile(entities, task_instructions)

        # Generate dialogue based on task type
        dialogue_messages = self._generate_dialogue(
            patient_profile=patient_profile,
            department=department,
            task_type=task_type,
            task_instructions=task_instructions,
            entities=entities,
        )

        # Determine expected tools based on department
        expected_tools = self._get_expected_tools(department, entities)

        # Generate expected outcome
        expected_outcome = self._generate_expected_outcome(task_type, entities)

        return ConsultationDialogue(
            task_id=task_id,
            patient_profile=patient_profile,
            department=department,
            dialogue=dialogue_messages,
            expected_tools=expected_tools,
            expected_outcome=expected_outcome,
        )

    def to_tau2_format(self, dialogue: ConsultationDialogue) -> Dict[str, Any]:
        """Convert a ConsultationDialogue to tau2 format.

        Args:
            dialogue: The consultation dialogue to convert

        Returns:
            A dictionary in tau2 task format
        """
        # Build user scenario instructions from dialogue
        dialogue_text = self._format_dialogue_as_instructions(dialogue)

        # Build user scenario
        user_scenario = {
            "persona": self._build_persona(dialogue.patient_profile),
            "instructions": {
                "domain": dialogue.department.replace("clinical_", ""),
                "reason_for_call": dialogue.patient_profile.chief_complaint or "Medical consultation",
                "known_info": self._build_known_info(dialogue.patient_profile),
                "unknown_info": None,
                "task_instructions": dialogue_text,
            }
        }

        # Build description
        description = {
            "purpose": f"Clinical consultation - {dialogue.patient_profile.chief_complaint or 'general consultation'}",
            "relevant_policies": None,
            "notes": f"Generated from MCQ conversion. Department: {dialogue.department}",
        }

        # Build ticket (summary of patient's problem)
        ticket = self._build_ticket(dialogue)

        # Build initial state with patient info
        initial_state = {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": generate_patient_name(dialogue.patient_profile.gender),
                        "mrn": generate_patient_mrn(),
                        "age": dialogue.patient_profile.age,
                        "gender": dialogue.patient_profile.gender,
                    }
                }
            ]
        }

        # Build evaluation criteria
        evaluation_criteria = None
        if dialogue.expected_tools:
            evaluation_criteria = {
                "actions": [
                    {
                        "action_id": f"use_{tool}",
                        "requestor": "assistant",
                        "name": tool,
                        "arguments": {},
                    }
                    for tool in dialogue.expected_tools
                ]
            }

        return {
            "id": dialogue.task_id,
            "description": description,
            "user_scenario": user_scenario,
            "ticket": ticket,
            "initial_state": initial_state,
            "evaluation_criteria": evaluation_criteria,
        }

    def _build_patient_profile(self, entities: Dict[str, Any], question_text: str) -> PatientProfile:
        """Build a patient profile from extracted entities.

        Args:
            entities: Extracted medical entities
            question_text: Original question text for additional context

        Returns:
            A PatientProfile object
        """
        # Determine gender
        gender = entities.get("gender") or determine_gender_from_context(question_text, entities.get("age"))

        # Use extracted entities
        return PatientProfile(
            age=entities.get("age"),
            gender=gender,
            chief_complaint=entities["symptoms"][0] if entities["symptoms"] else None,
            symptoms=entities["symptoms"][:3],  # Limit to top 3 symptoms
            medical_history=entities.get("conditions", [])[:2],
            medications=entities.get("medications", [])[:3],
            known_conditions=entities.get("conditions", [])[:2],
            vital_signs=entities.get("vital_signs", {}),
        )

    def _generate_dialogue(
        self,
        patient_profile: PatientProfile,
        department: str,
        task_type: str,
        task_instructions: str,
        entities: Dict[str, Any],
    ) -> List[DialogueMessage]:
        """Generate dialogue messages based on task type.

        Args:
            patient_profile: The patient's profile
            department: Clinical department
            task_type: Type of task (diagnosis, treatment, basic_science)
            task_instructions: Original question text
            entities: Extracted entities

        Returns:
            List of DialogueMessage objects
        """
        # Determine dialogue style
        if self.dialogue_style == "auto":
            if task_type == "diagnosis":
                style = "diagnostic"
            elif task_type == "treatment":
                style = "treatment"
            else:
                style = "educational"
        else:
            style = self.dialogue_style

        # Build dialogue based on style
        if style == "diagnostic":
            turns_tuples = self.dialogue_builder.build_diagnostic_dialogue(patient_profile, department)
        elif style == "treatment":
            turns_tuples = self.dialogue_builder.build_treatment_dialogue(patient_profile, department)
        else:
            # Default simple dialogue
            turns_tuples = self._build_simple_dialogue(patient_profile, department)

        # Convert to DialogueMessage objects
        return [
            DialogueMessage(role=role, content=content, turn_type=turn_type)
            for role, content, turn_type in turns_tuples
        ]

    def _build_simple_dialogue(
        self,
        patient_profile: PatientProfile,
        department: str,
    ) -> List[tuple]:
        """Build a simple dialogue for basic science questions.

        Args:
            patient_profile: The patient's profile
            department: Clinical department

        Returns:
            List of (role, content, turn_type) tuples
        """
        symptom = patient_profile.symptoms[0] if patient_profile.symptoms else "symptoms"

        dialogue = []
        opening = f"Doctor, I have a question about {symptom}."
        dialogue.append(("user", opening, DialogueTurn.OPENING))

        response = f"I'd be happy to help explain what might be causing your {symptom}."
        dialogue.append(("assistant", response, DialogueTurn.HISTORY_GATHERING))

        return dialogue

    def _get_expected_tools(self, department: str, entities: Dict[str, Any]) -> List[str]:
        """Get expected tools based on department and entities.

        Args:
            department: The clinical department
            entities: Extracted entities

        Returns:
            List of expected tool names
        """
        # Department-specific tool mappings
        department_tools = {
            "clinical_neurology": [
                "assess_stroke_risk",
                "interpret_headache",
                "evaluate_seizure",
                "get_patient_by_mrn",
            ],
            "clinical_cardiology": [
                "assess_cardiovascular_risk",
                "interpret_ekg",
                "evaluate_blood_pressure",
                "get_patient_by_mrn",
            ],
            "clinical_gastroenterology": [
                "get_patient_liver_function",
                "evaluate_anemia",
                "assess_liver_fibrosis",
                "get_patient_by_mrn",
            ],
            "clinical_endocrinology": [
                "evaluate_blood_glucose",
                "assess_thyroid_function",
                "get_patient_by_mrn",
            ],
            "clinical_nephrology": [
                "evaluate_kidney_function",
                "assess_eGFR",
                "get_patient_by_mrn",
            ],
        }

        return department_tools.get(department, ["get_patient_by_mrn"])

    def _generate_expected_outcome(self, task_type: str, entities: Dict[str, Any]) -> str:
        """Generate expected outcome description.

        Args:
            task_type: Type of task
            entities: Extracted entities

        Returns:
            Expected outcome description
        """
        if task_type == "diagnosis":
            condition = entities["conditions"][0] if entities["conditions"] else "the condition"
            return f"Clinician identifies or considers {condition} as potential diagnosis"
        elif task_type == "treatment":
            return "Clinician recommends appropriate treatment plan"
        else:
            return "Clinician provides relevant medical information"

    def _format_dialogue_as_instructions(self, dialogue: ConsultationDialogue) -> str:
        """Format the dialogue as task instructions.

        Args:
            dialogue: The consultation dialogue

        Returns:
            Formatted dialogue text
        """
        lines = ["You are a patient seeking medical consultation. Here's how the conversation should flow:"]
        lines.append("")

        for msg in dialogue.dialogue:
            role_name = "Patient" if msg.role == "user" else "Clinician"
            lines.append(f"{role_name}: {msg.content}")

        return "\n".join(lines)

    def _build_persona(self, patient_profile: PatientProfile) -> Optional[str]:
        """Build a persona description for the patient.

        Args:
            patient_profile: The patient's profile

        Returns:
            Persona description string
        """
        parts = []
        if patient_profile.age:
            parts.append(f"{patient_profile.age}-year-old")
        if patient_profile.gender:
            parts.append(patient_profile.gender)
        if patient_profile.chief_complaint:
            parts.append(f"with {patient_profile.chief_complaint}")

        return " ".join(parts) if parts else None

    def _build_known_info(self, patient_profile: PatientProfile) -> str:
        """Build known_info string from patient profile.

        Args:
            patient_profile: The patient's profile

        Returns:
            Known information string
        """
        parts = []
        if patient_profile.symptoms:
            parts.append(f"Symptoms: {', '.join(patient_profile.symptoms)}")
        if patient_profile.medical_history:
            parts.append(f"History: {', '.join(patient_profile.medical_history)}")
        if patient_profile.medications:
            parts.append(f"Medications: {', '.join(patient_profile.medications)}")

        return "; ".join(parts) if parts else "No specific information provided"

    def _build_ticket(self, dialogue: ConsultationDialogue) -> str:
        """Build a ticket description from the dialogue.

        Args:
            dialogue: The consultation dialogue

        Returns:
            Ticket description string
        """
        # Use the first user message as the ticket
        for msg in dialogue.dialogue:
            if msg.role == "user":
                return msg.content

        # Fallback to chief complaint
        return dialogue.patient_profile.chief_complaint or "Medical consultation request"


def convert_mcq_to_tau2(
    mcq_tasks: List[Dict[str, Any]],
    config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Convert multiple MCQ tasks to tau2 format.

    This is a convenience function for batch conversion.

    Args:
        mcq_tasks: List of MCQ task dictionaries
        config: Optional configuration for the converter

    Returns:
        List of tau2 format task dictionaries
    """
    converter = MCQToDialogueConverter(config)
    return converter.generate_batch(mcq_tasks)
