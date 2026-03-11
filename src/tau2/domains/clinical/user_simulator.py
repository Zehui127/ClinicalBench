"""Global User Simulator for Clinical Domains

This module provides a unified user simulator for all clinical domains.
It replaces the individual user_tools.py and user_data_model.py files
that were previously in each clinical specialty directory.
"""

from typing import Optional

from pydantic import Field

from tau2.environment.db import DB
from tau2.environment.toolkit import ToolKitBase


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
