"""Base generator for consultation dialogue data.

This module provides the abstract base class for all dialogue generators.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class DialogueTurn(Enum):
    """Types of dialogue turns."""
    OPENING = "opening"           # Patient presents problem
    HISTORY_GATHERING = "history"  # Clinician asks about history
    EXAMINATION = "examination"    # Physical exam discussion
    DIAGNOSIS = "diagnosis"        # Diagnosis discussion
    TREATMENT = "treatment"        # Treatment plan discussion
    CLOSING = "closing"           # Closing the consultation


@dataclass
class PatientProfile:
    """Patient demographic and clinical profile."""
    age: Optional[int] = None
    gender: Optional[str] = None  # male/female
    chief_complaint: Optional[str] = None
    symptoms: List[str] = None
    medical_history: List[str] = None
    medications: List[str] = None
    known_conditions: List[str] = None
    vital_signs: Dict[str, Any] = None

    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []
        if self.medical_history is None:
            self.medical_history = []
        if self.medications is None:
            self.medications = []
        if self.known_conditions is None:
            self.known_conditions = []
        if self.vital_signs is None:
            self.vital_signs = {}


@dataclass
class DialogueMessage:
    """A single message in the dialogue."""
    role: str  # 'user' (patient) or 'assistant' (clinician)
    content: str
    turn_type: DialogueTurn


@dataclass
class ConsultationDialogue:
    """A complete consultation dialogue."""
    task_id: str
    patient_profile: PatientProfile
    department: str
    dialogue: List[DialogueMessage]
    expected_tools: List[str] = None
    expected_outcome: str = None

    def __post_init__(self):
        if self.expected_tools is None:
            self.expected_tools = []


class BaseGenerator(ABC):
    """Abstract base class for dialogue generators.

    Subclasses must implement the generate method to convert
    source data into consultation dialogues.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the generator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}

    @abstractmethod
    def generate(self, source_data: Dict[str, Any]) -> ConsultationDialogue:
        """Generate a consultation dialogue from source data.

        Args:
            source_data: Raw source data (e.g., MCQ, EMR record)

        Returns:
            A ConsultationDialogue object
        """
        pass

    @abstractmethod
    def to_tau2_format(self, dialogue: ConsultationDialogue) -> Dict[str, Any]:
        """Convert a ConsultationDialogue to tau2 format.

        Args:
            dialogue: The consultation dialogue to convert

        Returns:
            A dictionary in tau2 task format
        """
        pass

    def generate_batch(
        self,
        source_data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate multiple dialogues in tau2 format.

        Args:
            source_data_list: List of source data items

        Returns:
            List of tau2 format dictionaries
        """
        results = []
        for source_data in source_data_list:
            dialogue = self.generate(source_data)
            tau2_task = self.to_tau2_format(dialogue)
            results.append(tau2_task)
        return results
