"""Template manager for dialogue generation.

This module provides templates for different types of consultation dialogues
across clinical departments and difficulty levels.
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Import local modules
try:
    from .base_generator import PatientProfile, DialogueTurn
except ImportError:
    # Direct imports for standalone usage
    generators_dir = Path(__file__).parent
    sys.path.insert(0, str(generators_dir))
    from base_generator import PatientProfile, DialogueTurn


class TemplateManager:
    """Manages dialogue templates for consultation generation."""

    # Department-specific opening templates
    OPENING_TEMPLATES = {
        "clinical_neurology": [
            "I've been having {symptom} and I'm worried it might be something serious with my nervous system.",
            "Doctor, I've been experiencing {symptom} for {duration} and it's getting worse.",
            "I have this {symptom} that comes and goes, and I'm not sure what to do about it.",
            "I've been noticing {symptom} lately and my family is concerned.",
            "For the past few days, I've had {symptom} and it's really affecting my daily life.",
        ],
        "clinical_cardiology": [
            "I've been having {symptom} and I'm concerned about my heart.",
            "Doctor, I've been experiencing {symptom} and I have a history of {condition}.",
            "I have chest discomfort and I'm worried it might be a heart problem.",
            "I've been feeling {symptom} and I'm not sure if it's related to my heart.",
            "My {symptom} has been bothering me, especially when I exert myself.",
        ],
        "clinical_gastroenterology": [
            "I've been having {symptom} for {duration} and it's really bothering me.",
            "Doctor, I've been experiencing digestive issues including {symptom}.",
            "I have abdominal {symptom} and I'm not sure what's causing it.",
            "I've had {symptom} for a while now and it's not getting better.",
            "My stomach has been bothering me with {symptom}, and I'm worried.",
        ],
        "clinical_endocrinology": [
            "I've been feeling {symptom} and I think it might be hormonal.",
            "Doctor, I've been experiencing {symptom} and I'm concerned about my {condition}.",
            "I've noticed {symptom} lately and I wonder if my hormones are imbalanced.",
            "I have a history of {condition} and I'm having {symptom} now.",
            "My energy levels have been {symptom} and I'm concerned.",
        ],
        "clinical_nephrology": [
            "I've been having {symptom} and I'm concerned about my kidney function.",
            "Doctor, I've noticed {symptom} and I'm worried it could be kidney-related.",
            "I've been experiencing {symptom} and I have a history of kidney issues.",
            "My urine has been {symptom} and I'm not sure what's causing it.",
            "I've been feeling {symptom} and I'm concerned about my kidneys.",
        ],
        "default": [
            "I've been having {symptom} and I'd like to get it checked out.",
            "Doctor, I've been experiencing {symptom} for {duration}.",
            "I'm concerned about {symptom} and would like your opinion.",
            "I've been dealing with {symptom} and need some advice.",
            "Doctor, I have {symptom} that's concerning me.",
        ],
    }

    # Clinician question templates by turn type
    CLINICIAN_QUESTIONS = {
        DialogueTurn.HISTORY_GATHERING: [
            "How long have you been experiencing these symptoms?",
            "Can you tell me more about when the symptoms started?",
            "Have you noticed anything that makes the symptoms better or worse?",
            "Do you have any medical history I should know about?",
            "Are you taking any medications?",
            "Have you had these symptoms before?",
        ],
        DialogueTurn.EXAMINATION: [
            "I'm going to examine you now. Let me know if you feel any discomfort.",
            "Can you point to where it hurts?",
            "I'm going to check your vital signs.",
            "Does this hurt when I press here?",
        ],
        DialogueTurn.DIAGNOSIS: [
            "Based on your symptoms and examination, I believe you have {condition}.",
            "Your symptoms suggest {condition}. We should run some tests to confirm.",
            "I'd like to order some tests to better understand what's going on.",
        ],
        DialogueTurn.TREATMENT: [
            "For your condition, I recommend {treatment}.",
            "We have several treatment options available. Let me explain them.",
            "I'm going to prescribe {medication} and monitor your progress.",
        ],
    }

    # Patient response templates
    PATIENT_RESPONSES = {
        "duration": [
            "It's been about {duration}.",
            "For approximately {duration} now.",
            "Since {timeframe}.",
        ],
        "severity": [
            "It's quite severe, especially at night.",
            "It varies throughout the day.",
            "It's moderate but getting worse.",
        ],
        "triggers": [
            "It gets worse when I {activity}.",
            "{activity} seems to trigger it.",
            "I haven't noticed any specific triggers.",
        ],
        "medical_history": [
            "Yes, I have a history of {condition}.",
            "I've had {condition} for {duration}.",
            "No significant medical history aside from {condition}.",
        ],
        "medications": [
            "I'm taking {medications}.",
            "Yes, I'm on {medications} for {condition}.",
            "I'm not currently taking any medications.",
        ],
    }

    # Symptoms by department
    DEPARTMENT_SYMPTOMS = {
        "clinical_neurology": [
            "headaches", "dizziness", "numbness", "tingling", "memory problems",
            "difficulty speaking", "vision changes", "loss of coordination", "seizures",
            "weakness in my limbs", "funny feelings in my head"
        ],
        "clinical_cardiology": [
            "chest pain", "palpitations", "shortness of breath", "leg swelling",
            "high blood pressure", "irregular heartbeat", "fatigue with exertion",
            "nosebleeds that won't stop"
        ],
        "clinical_gastroenterology": [
            "abdominal pain", "nausea", "vomiting", "diarrhea", "jaundice",
            "difficulty swallowing", "loss of appetite", "digestive issues",
            "yellowing of my skin"
        ],
        "clinical_endocrinology": [
            "fatigue", "weight changes", "temperature sensitivity", "excessive thirst",
            "frequent urination", "hair loss", "menstrual irregularities", "low energy"
        ],
        "clinical_nephrology": [
            "swelling in my legs", "foamy urine", "difficulty urinating", " flank pain",
            "changes in urine output", "high blood pressure", "fluid retention"
        ],
    }

    @classmethod
    def get_opening_template(
        cls,
        department: str,
        symptom: str,
        duration: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> str:
        """Get an opening statement template for a patient.

        Args:
            department: The clinical department
            symptom: Patient's chief complaint
            duration: Duration of symptoms (optional)
            condition: Known condition (optional)

        Returns:
            A formatted opening statement
        """
        templates = cls.OPENING_TEMPLATES.get(department, cls.OPENING_TEMPLATES["default"])
        import random
        template = random.choice(templates)

        # Fill in placeholders
        result = template.replace("{symptom}", symptom)
        if duration and "{duration}" in result:
            result = result.replace("{duration}", duration)
        if condition and "{condition}" in result:
            result = result.replace("{condition}", condition)

        return result

    @classmethod
    def get_clinician_question(cls, turn_type: DialogueTurn, context: Optional[Dict] = None) -> str:
        """Get a clinician question for a specific turn type.

        Args:
            turn_type: The type of dialogue turn
            context: Optional context dict for filling placeholders

        Returns:
            A clinician question
        """
        questions = cls.CLINICIAN_QUESTIONS.get(turn_type, [])
        if not questions:
            return "Can you tell me more?"

        import random
        question = random.choice(questions)

        # Fill in placeholders if context provided
        if context:
            for key, value in context.items():
                placeholder = f"{{{key}}}"
                if placeholder in question:
                    question = question.replace(placeholder, str(value))

        return question

    @classmethod
    def get_patient_response(
        cls,
        response_type: str,
        context: Dict[str, str],
    ) -> str:
        """Get a patient response for a specific response type.

        Args:
            response_type: Type of response (duration, severity, triggers, etc.)
            context: Context dict with values for placeholders

        Returns:
            A patient response
        """
        responses = cls.PATIENT_RESPONSES.get(response_type, ["I'm not sure."])
        import random
        response = random.choice(responses)

        # Fill in placeholders
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in response:
                response = response.replace(placeholder, str(value))

        return response

    @classmethod
    def get_department_symptoms(cls, department: str) -> List[str]:
        """Get common symptoms for a department.

        Args:
            department: The clinical department

        Returns:
            List of common symptoms
        """
        return cls.DEPARTMENT_SYMPTOMS.get(department, ["pain", "discomfort"])

    @classmethod
    def generate_duration_expression(cls, duration_text: Optional[str] = None) -> str:
        """Generate a natural duration expression.

        Args:
            duration_text: Optional duration text extracted from question

        Returns:
            A natural duration expression
        """
        if duration_text:
            return duration_text

        import random
        durations = [
            "a few days",
            "about a week",
            "a couple of weeks",
            "several weeks",
            "about a month",
            "a few months",
        ]
        return random.choice(durations)


class DialogueBuilder:
    """Builds multi-turn dialogues from templates."""

    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """Initialize the dialogue builder.

        Args:
            template_manager: Optional custom template manager
        """
        self.template_manager = template_manager or TemplateManager()

    def build_diagnostic_dialogue(
        self,
        patient_profile: PatientProfile,
        department: str,
    ) -> List[tuple]:
        """Build a diagnostic consultation dialogue.

        Args:
            patient_profile: The patient's profile
            department: Clinical department

        Returns:
            List of (role, content, turn_type) tuples
        """
        dialogue = []
        symptom = patient_profile.symptoms[0] if patient_profile.symptoms else "symptoms"
        duration = self.template_manager.generate_duration_expression()

        # Opening - patient presents problem
        opening = self.template_manager.get_opening_template(
            department=department,
            symptom=symptom,
            duration=duration,
        )
        dialogue.append(("user", opening, DialogueTurn.OPENING))

        # History gathering
        question1 = self.template_manager.get_clinician_question(DialogueTurn.HISTORY_GATHERING)
        dialogue.append(("assistant", question1, DialogueTurn.HISTORY_GATHERING))

        response1 = self.template_manager.get_patient_response("duration", {"duration": duration})
        dialogue.append(("user", response1, DialogueTurn.HISTORY_GATHERING))

        # More history
        if patient_profile.medical_history:
            question2 = self.template_manager.get_clinician_question(
                DialogueTurn.HISTORY_GATHERING,
                {"condition": patient_profile.medical_history[0] if patient_profile.medical_history else "issues"}
            )
            dialogue.append(("assistant", question2, DialogueTurn.HISTORY_GATHERING))

            response2 = self.template_manager.get_patient_response(
                "medical_history",
                {"condition": patient_profile.medical_history[0] if patient_profile.medical_history else "no major issues"}
            )
            dialogue.append(("user", response2, DialogueTurn.HISTORY_GATHERING))

        # Examination
        exam_question = self.template_manager.get_clinician_question(DialogueTurn.EXAMINATION)
        dialogue.append(("assistant", exam_question, DialogueTurn.EXAMINATION))

        # Diagnosis discussion
        if patient_profile.known_conditions:
            diagnosis = self.template_manager.get_clinician_question(
                DialogueTurn.DIAGNOSIS,
                {"condition": patient_profile.known_conditions[0]}
            )
            dialogue.append(("assistant", diagnosis, DialogueTurn.DIAGNOSIS))

        return dialogue

    def build_treatment_dialogue(
        self,
        patient_profile: PatientProfile,
        department: str,
    ) -> List[tuple]:
        """Build a treatment consultation dialogue.

        Args:
            patient_profile: The patient's profile
            department: Clinical department

        Returns:
            List of (role, content, turn_type) tuples
        """
        dialogue = []
        symptom = patient_profile.symptoms[0] if patient_profile.symptoms else "symptoms"
        condition = patient_profile.known_conditions[0] if patient_profile.known_conditions else "my condition"

        # Opening - patient presents problem
        opening = self.template_manager.get_opening_template(
            department=department,
            symptom=symptom,
            condition=condition,
        )
        dialogue.append(("user", opening, DialogueTurn.OPENING))

        # Acknowledge and assess
        question1 = self.template_manager.get_clinician_question(
            DialogueTurn.HISTORY_GATHERING,
            {"condition": condition}
        )
        dialogue.append(("assistant", question1, DialogueTurn.HISTORY_GATHERING))

        # Patient responds about condition
        response1 = f"Yes, I've been diagnosed with {condition}."
        dialogue.append(("user", response1, DialogueTurn.HISTORY_GATHERING))

        # Treatment discussion
        treatment = self.template_manager.get_clinician_question(
            DialogueTurn.TREATMENT,
            {"treatment": "medication to help manage your symptoms"}
        )
        dialogue.append(("assistant", treatment, DialogueTurn.TREATMENT))

        # Patient acknowledges
        dialogue.append(("user", "That sounds good. Thank you, doctor.", DialogueTurn.TREATMENT))

        return dialogue
