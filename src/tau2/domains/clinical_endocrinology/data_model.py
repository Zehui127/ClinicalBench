"""Data Models for Clinical Endocrinology Domain"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class HormoneLevels(BaseModel):
    """Hormone lab results"""
    glucose: Optional[float] = None  # mg/dL
    hba1c: Optional[float] = None  # %
    tsh: Optional[float] = None  # mIU/L
    t4: Optional[float] = None  # mcg/dL
    t3: Optional[float] = None  # ng/dL
    cortisol: Optional[float] = None  # mcg/dL
    insulin: Optional[float] = None  # mcU/mL


class PatientRecord(BaseModel):
    """Patient record for endocrinology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    hormone_levels: Optional[HormoneLevels] = None
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class EndocrinologyDB(BaseModel):
    """Endocrinology domain database"""
    patients: Dict[str, PatientRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "EndocrinologyDB":
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
