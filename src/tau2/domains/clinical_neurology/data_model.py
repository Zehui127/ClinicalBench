"""Data Models for Clinical Neurology Domain"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class NeuroExam(BaseModel):
    """Neurological examination findings"""
    mental_status: Optional[str] = None
    cranial_nerves: Optional[str] = None
    motor_strength: Optional[str] = None
    sensation: Optional[str] = None
    reflexes: Optional[str] = None
    coordination: Optional[str] = None


class ImagingResult(BaseModel):
    """Neuroimaging results"""
    ct_brain: Optional[str] = None
    mri_brain: Optional[str] = None
    eeg: Optional[str] = None


class PatientRecord(BaseModel):
    """Patient record for neurology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    neuro_exam: Optional[NeuroExam] = None
    imaging: Optional[ImagingResult] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class NeurologyDB(BaseModel):
    """Neurology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "NeurologyDB":
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
