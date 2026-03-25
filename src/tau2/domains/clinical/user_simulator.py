"""Global User Simulator for Clinical Domains

This module provides a unified user simulator for all clinical domains.
It replaces the individual user_tools.py and user_data_model.py files
that were previously in each clinical specialty directory.

Enhanced with medical persona support and disease-symptom mapping.
"""

import logging
from typing import Dict, List, Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.environment.toolkit import ToolKitBase

# Import new medical data models
try:
    from tau2.data_model.medical_tasks import MedicalPersona
    from tau2.domains.clinical.data_sources.disease_symptom_mapper import DiseaseSymptomMapper
    MEDICAL_MODELS_AVAILABLE = True
except ImportError:
    MEDICAL_MODELS_AVAILABLE = False
    MedicalPersona = None
    DiseaseSymptomMapper = None

logger = logging.getLogger(__name__)


# === USER DATA MODEL ===

class ClinicalUserDB(DB):
    """Database for clinical user information.

    This stores user/patient information that is used during the consultation
    across all clinical domains (cardiology, endocrinology, gastroenterology,
    nephrology, neurology).
    """

    name: Optional[str] = Field(
        None,
        description="The patient's name",
    )
    mrn: Optional[str] = Field(
        None,
        description="Medical Record Number",
    )
    age: Optional[int] = Field(
        None,
        description="The patient's age",
    )
    gender: Optional[str] = Field(
        None,
        description="The patient's gender",
    )
    specialty: Optional[str] = Field(
        None,
        description="The clinical specialty for this consultation",
    )
    chief_complaint: Optional[str] = Field(
        None,
        description="The patient's chief complaint or reason for visit",
    )
    # Extended medical fields (optional, for medical persona support)
    symptoms: Optional[List[str]] = Field(
        None,
        description="List of symptoms the patient is experiencing",
    )
    duration: Optional[str] = Field(
        None,
        description="Duration of symptoms",
    )
    severity: Optional[str] = Field(
        None,
        description="Severity of symptoms",
    )
    past_medical_history: Optional[List[str]] = Field(
        None,
        description="Past medical history",
    )
    current_medications: Optional[List[str]] = Field(
        None,
        description="Current medications",
    )
    allergies: Optional[List[str]] = Field(
        None,
        description="Known allergies",
    )


# === USER TOOLS ===

class ClinicalUserTools(ToolKitBase):
    """
    Provides methods to simulate user/patient actions and state
    across all clinical domains.
    """

    db: ClinicalUserDB

    def __init__(self, db: ClinicalUserDB):
        """
        Initializes the clinical user tools.

        Args:
            db: The clinical user database containing patient information.
        """
        super().__init__(db)

    def set_user_info(
        self,
        name: str,
        mrn: str,
        age: int = None,
        gender: str = None,
        specialty: str = None,
    ) -> str:
        """
        Sets the patient's information for the consultation.

        Args:
            name: The patient's name.
            mrn: Medical Record Number.
            age: The patient's age (optional).
            gender: The patient's gender (optional).
            specialty: The clinical specialty (optional).

        Returns:
            A confirmation message with the patient information.
        """
        self.db.name = name
        self.db.mrn = mrn
        self.db.age = age
        self.db.gender = gender
        self.db.specialty = specialty

        parts = [f"Name: {name}", f"MRN: {mrn}"]
        if age is not None:
            parts.append(f"Age: {age}")
        if gender is not None:
            parts.append(f"Gender: {gender}")
        if specialty is not None:
            parts.append(f"Specialty: {specialty}")

        return "Patient information set:\n" + "\n".join(parts)

    def set_chief_complaint(self, complaint: str) -> str:
        """
        Sets the patient's chief complaint or reason for visit.

        Args:
            complaint: The patient's chief complaint.

        Returns:
            A confirmation message.
        """
        self.db.chief_complaint = complaint
        return f"Chief complaint set: {complaint}"

    def get_user_info(self) -> str:
        """
        Returns the current patient information.

        Returns:
            A formatted string with the patient's information.
        """
        parts = []
        if self.db.name:
            parts.append(f"Name: {self.db.name}")
        if self.db.mrn:
            parts.append(f"MRN: {self.db.mrn}")
        if self.db.age is not None:
            parts.append(f"Age: {self.db.age}")
        if self.db.gender:
            parts.append(f"Gender: {self.db.gender}")
        if self.db.specialty:
            parts.append(f"Specialty: {self.db.specialty}")
        if self.db.chief_complaint:
            parts.append(f"Chief Complaint: {self.db.chief_complaint}")

        if not parts:
            return "No patient information set."

        return "Current Patient Information:\n" + "\n".join(parts)

    def set_medical_persona(self, persona: Dict) -> str:
        """
        Sets patient information from a MedicalPersona or dictionary.

        Args:
            persona: Dictionary containing medical persona information

        Returns:
            A confirmation message
        """
        # Set basic info
        self.db.name = persona.get("name", self.db.name)
        self.db.age = persona.get("age", self.db.age)
        self.db.gender = persona.get("gender", self.db.gender)

        # Set medical info
        self.db.symptoms = persona.get("symptoms", [])
        self.db.duration = persona.get("duration")
        self.db.severity = persona.get("severity")
        self.db.past_medical_history = persona.get("past_medical_history", [])
        self.db.current_medications = persona.get("current_medications", [])
        self.db.allergies = persona.get("allergies", [])

        return "Medical persona set successfully"

    def get_medical_info(self) -> Dict:
        """
        Returns the medical information for this patient.

        Returns:
            Dictionary with all medical information
        """
        return {
            "name": self.db.name,
            "age": self.db.age,
            "gender": self.db.gender,
            "symptoms": self.db.symptoms or [],
            "duration": self.db.duration,
            "severity": self.db.severity,
            "past_medical_history": self.db.past_medical_history or [],
            "current_medications": self.db.current_medications or [],
            "allergies": self.db.allergies or [],
            "chief_complaint": self.db.chief_complaint,
        }

    def generate_patient_description(self) -> str:
        """
        Generate a natural language description of the patient for use in prompts.

        Returns:
            A description string
        """
        parts = []

        # Basic info
        if self.db.age:
            parts.append(f"{self.db.age}-year-old")
        if self.db.gender:
            parts.append(self.db.gender)
        parts.append("patient")

        # Chief complaint
        if self.db.chief_complaint:
            parts.append(f"presenting with {self.db.chief_complaint}")

        # Symptoms
        if self.db.symptoms:
            symptoms_str = ", ".join(self.db.symptoms[:-1]) + (
                f" and {self.db.symptoms[-1]}" if len(self.db.symptoms) > 1 else self.db.symptoms[0]
            )
            parts.append(f"reporting {symptoms_str}")

            if self.db.duration:
                parts.append(f"for {self.db.duration}")
            if self.db.severity:
                parts.append(f"(severity: {self.db.severity})")

        # Medical history
        history_parts = []
        if self.db.past_medical_history:
            history_parts.append(f"past history of {', '.join(self.db.past_medical_history)}")
        if self.db.current_medications:
            history_parts.append(f"current medications: {', '.join(self.db.current_medications)}")
        if self.db.allergies:
            history_parts.append(f"allergies: {', '.join(self.db.allergies)}")

        if history_parts:
            parts.append(f"with {'; '.join(history_parts)}")

        return " ".join(parts)


# ==============================================================================
# MEDICAL PERSONA FACTORY
# ==============================================================================

if MEDICAL_MODELS_AVAILABLE:

    class MedicalPersonaFactory:
        """
        Factory class for creating medical personas based on diseases.

        Uses the DiseaseSymptomMapper to generate medically accurate personas.
        """

        def __init__(self, knowledge_graph_adapter=None):
            """
            Initialize the medical persona factory.

            Args:
                knowledge_graph_adapter: Optional knowledge graph adapter
            """
            self.symptom_mapper = DiseaseSymptomMapper(kg_adapter=knowledge_graph_adapter)

        def create_persona_from_disease(
            self,
            disease_id: str,
            age: int = 50,
            gender: str = "male",
            information_level: str = "partial",
            severity: str = "moderate"
        ) -> Dict:
            """
            Create a medical persona based on a disease.

            Args:
                disease_id: Disease identifier
                age: Patient age
                gender: Patient gender
                information_level: Information completeness (complete/partial/minimal)
                severity: Symptom severity (mild/moderate/severe)

            Returns:
                Dictionary with medical persona information
            """
            persona = self.symptom_mapper.generate_medical_persona(
                disease_id=disease_id,
                age=age,
                gender=gender,
                information_level=information_level,
                severity=severity
            )

            return persona.dict() if hasattr(persona, 'dict') else persona

        def create_persona_from_symptoms(
            self,
            symptoms: List[str],
            age: int = 50,
            gender: str = "male",
            severity: str = "moderate"
        ) -> Dict:
            """
            Create a medical persona based on symptoms.

            Args:
                symptoms: List of symptoms
                age: Patient age
                gender: Patient gender
                severity: Symptom severity

            Returns:
                Dictionary with medical persona information
            """
            return {
                "age": age,
                "gender": gender,
                "symptoms": symptoms,
                "duration": "2 weeks",
                "severity": severity,
                "past_medical_history": [],
                "current_medications": [],
                "allergies": [],
            }

        def find_diseases_for_symptoms(
            self,
            symptoms: List[str],
            min_match: int = 2
        ) -> List[Dict]:
            """
            Find diseases that match given symptoms.

            Args:
                symptoms: List of symptoms
                min_match: Minimum symptom matches required

            Returns:
                List of candidate diseases with match information
            """
            return self.symptom_mapper.find_diseases_by_symptoms(
                symptoms=symptoms,
                min_match=min_match
            )

        def validate_symptoms_for_disease(
            self,
            disease_id: str,
            symptoms: List[str]
        ) -> Dict[str, bool]:
            """
            Validate which symptoms are associated with a disease.

            Args:
                disease_id: Disease identifier
                symptoms: List of symptoms to validate

            Returns:
                Dictionary mapping symptom to validity
            """
            return self.symptom_mapper.validate_symptom_disease_relationship(
                disease_id=disease_id,
                symptoms=symptoms
            )
