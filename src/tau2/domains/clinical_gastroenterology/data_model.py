"""
Data Models for Clinical Gastroenterology Domain
Defines patient records, GI lab results, and digestive system data
"""

import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class GILabResults(BaseModel):
    """Gastrointestinal lab results"""
    liver_enzymes_alt: Optional[float] = None  # U/L
    liver_enzymes_ast: Optional[float] = None  # U/L
    bilirubin: Optional[float] = None  # mg/dL
    albumin: Optional[float] = None  # g/dL
    inr: Optional[float] = None  # International Normalized Ratio
    hemoglobin: Optional[float] = None  # g/dL
    platelets: Optional[float] = None  # K/uL


class EndoscopyRecord(BaseModel):
    """Endoscopy procedure record"""
    procedure_type: str  # colonoscopy, egd, sigmoidoscopy
    date: str
    findings: List[str] = []
    biopsy_taken: bool = False
    pathology_results: Optional[str] = None


class PatientRecord(BaseModel):
    """Patient medical record for gastroenterology"""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnoses: List[str] = []
    gi_lab_results: Optional[GILabResults] = None
    endoscopies: List[EndoscopyRecord] = []
    medications: List[str] = []
    comorbidities: List[str] = []
    chief_complaint: Optional[str] = None


class GastroenterologyDB(BaseModel):
    """Gastroenterology domain database"""
    patients: Dict[str, PatientRecord] = {}
    lab_results: Dict[str, GILabResults] = {}
    procedures: Dict[str, EndoscopyRecord] = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def load(cls, db_path: str) -> "GastroenterologyDB":
        """Load database from JSON file"""
        import json
        from pathlib import Path

        path = Path(db_path)
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get patient by ID"""
        return self.patients.get(patient_id)
