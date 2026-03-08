"""Data Models for Clinical Cardiology Domain"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class VitalSigns(BaseModel):
    """Patient vital signs"""
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[float] = None


class CardiacTest(BaseModel):
    """Cardiac diagnostic test results"""
    ecg_interpretation: Optional[str] = None
    echocardiogram: Optional[str] = None
    stress_test: Optional[str] = None
    cardiac_biomarkers: Optional[dict] = None


class PatientRecord(BaseModel):
    """Patient record for cardiology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    vital_signs: Optional[VitalSigns] = None
    cardiac_tests: Optional[CardiacTest] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class CardiologyDB(BaseModel):
    """Cardiology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "CardiologyDB":
        import json
        from pathlib import Path
        path = Path(db_path)
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        return self.patients.get(patient_id)
