"""
Data Models for Clinical Nephrology Domain
Defines patient records, lab results, and kidney function data
"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class KidneyFunction(BaseModel):
    """Kidney function lab results"""
    creatinine: float  # mg/dL
    egfr: float  # mL/min/1.73m²
    bun: Optional[float] = None  # mg/dL
    potassium: Optional[float] = None  # mEq/L
    sodium: Optional[float] = None  # mEq/L
    albumin: Optional[float] = None  # g/dL


class PatientRecord(BaseModel):
    """Patient medical record for nephrology"""
    patient_id: str
    name: str
    age: int
    gender: str  # "male" or "female"
    race: Optional[str] = None  # For eGFR calculation
    diagnoses: List[str] = []
    kidney_function: Optional[KidneyFunction] = None
    medications: List[str] = []
    comorbidities: List[str] = []  # diabetes, hypertension, etc.
    ckd_stage: Optional[int] = None  # CKD stage 1-5


class MedicationRecord(BaseModel):
    """Medication record for renal dosing"""
    medication_name: str
    standard_dose: float
    adjusted_dose: Optional[float] = None
    adjustment_reason: Optional[str] = None
    requires_renal_dosing: bool = False


class NephrologyDB(BaseModel):
    """Nephrology domain database"""
    patients: Dict[str, PatientRecord] = {}
    lab_results: Dict[str, KidneyFunction] = {}
    medications: Dict[str, MedicationRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "NephrologyDB":
        """Load database from JSON file"""
        import json
        from pathlib import Path

        path = Path(db_path)
        if not path.exists():
            # Return empty database if file doesn't exist
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get patient by ID"""
        return self.patients.get(patient_id)

    def add_patient(self, patient: PatientRecord) -> None:
        """Add patient to database"""
        self.patients[patient.patient_id] = patient
