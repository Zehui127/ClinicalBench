"""Clinical Tools for Cardiology Domain"""

from typing import Optional
from tau2.domains.clinical_cardiology.data_model import CardiologyDB
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class CardiologyTools(ToolKitBase):
    """Clinical tools for cardiology domain"""
    db: CardiologyDB

    def __init__(self, db: CardiologyDB) -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def assess_blood_pressure(self, systolic: int, diastolic: int, age: int) -> dict:
        """
        Assess blood pressure and provide classification.

        Args:
            systolic: Systolic BP in mmHg
            diastolic: Diastolic BP in mmHg
            age: Patient age

        Returns:
            BP classification with recommendations
        """
        # BP categories
        if systolic < 120 and diastolic < 80:
            category = "Normal"
            recommendation = "Continue healthy lifestyle"
        elif systolic < 130 and diastolic < 80:
            category = "Elevated"
            recommendation = "Lifestyle modifications recommended"
        elif systolic < 140 or diastolic < 90:
            category = "Hypertension Stage 1"
            recommendation = "Lifestyle changes, consider medication"
        elif systolic < 180 or diastolic < 120:
            category = "Hypertension Stage 2"
            recommendation = "Medication likely required"
        else:
            category = "Hypertensive Crisis"
            recommendation = "Immediate medical attention required"

        return {
            "systolic": systolic,
            "diastolic": diastolic,
            "category": category,
            "recommendation": recommendation
        }

    @is_tool(ToolType.READ)
    def calculate_qtc(self, qt_interval: int, heart_rate: int) -> dict:
        """
        Calculate corrected QT interval (QTc) using Bazett's formula.

        Args:
            qt_interval: QT interval in milliseconds
            heart_rate: Heart rate in beats per minute

        Returns:
            QTc value with interpretation
        """
        qtc = int(qt_interval / (heart_rate / 60) ** 0.5)

        if qtc < 440:
            interpretation = "Normal"
        elif qtc < 470:
            interpretation = "Borderline"
        else:
            interpretation = "Prolonged - risk of arrhythmia"

        return {
            "qt_interval": qt_interval,
            "heart_rate": heart_rate,
            "qtc": qtc,
            "interpretation": interpretation
        }

    @is_tool(ToolType.READ)
    def get_patient_by_mrn(self, mrn: str) -> dict:
        """Find patient by MRN"""
        for patient_id, patient in self.db.patients.items():
            if patient.patient_id == mrn:
                return {
                    "patient_id": patient.patient_id,
                    "name": patient.name,
                    "age": patient.age,
                    "gender": patient.gender,
                    "diagnoses": patient.diagnoses,
                    "chief_complaint": patient.chief_complaint,
                    "medications": patient.medications
                }
        raise ValueError(f"Patient with MRN {mrn} not found")

    @is_tool(ToolType.READ)
    def interpret_heart_rate(self, heart_rate: int, age: int) -> dict:
        """
        Interpret heart rate based on age and activity level.

        Args:
            heart_rate: Heart rate in bpm
            age: Patient age

        Returns:
            Heart rate interpretation
        """
        # Normal resting HR ranges
        if age < 1:
            normal_range = (100, 160)
        elif age < 6:
            normal_range = (80, 120)
        elif age < 12:
            normal_range = (70, 110)
        else:
            normal_range = (60, 100)

        min_normal, max_normal = normal_range

        if heart_rate < min_normal:
            status = "Bradycardia"
        elif heart_rate > max_normal:
            status = "Tachycardia"
        else:
            status = "Normal"

        return {
            "heart_rate": heart_rate,
            "age": age,
            "normal_range": f"{min_normal}-{max_normal}",
            "status": status
        }
