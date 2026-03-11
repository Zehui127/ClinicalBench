"""Clinical Tools for Endocrinology Domain"""

from typing import Optional, TYPE_CHECKING
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool

if TYPE_CHECKING:
    from tau2.domains.clinical.endocrinology.environment import EndocrinologyDB



class EndocrinologyTools(ToolKitBase):
    """Clinical tools for endocrinology domain"""
    db: 'EndocrinologyDB'

    def __init__(self, db: 'EndocrinologyDB') -> None:
        super().__init__(db)

    @is_tool(ToolType.READ)
    def interpret_blood_glucose(self, glucose: float, fasting: bool = True) -> dict:
        """
        Interpret blood glucose levels.

        Args:
            glucose: Blood glucose in mg/dL
            fasting: Whether this is a fasting measurement

        Returns:
            Glucose interpretation
        """
        if fasting:
            if glucose < 70:
                category = "Hypoglycemia"
                recommendation = "Immediate glucose intake required"
            elif glucose < 100:
                category = "Normal fasting"
                recommendation = "Normal fasting glucose"
            elif glucose < 126:
                category = "Impaired fasting glucose"
                recommendation = "Prediabetes - consider lifestyle modifications"
            else:
                category = "Diabetes"
                recommendation = "Diagnostic of diabetes - confirm with HbA1c"
        else:
            if glucose < 70:
                category = "Hypoglycemia"
                recommendation = "Immediate glucose intake required"
            elif glucose < 140:
                category = "Normal random"
                recommendation = "Normal random glucose"
            else:
                category = "Hyperglycemia"
                recommendation = "Further evaluation needed"

        return {
            "glucose": glucose,
            "fasting": fasting,
            "category": category,
            "recommendation": recommendation
        }

    @is_tool(ToolType.READ)
    def interpret_hba1c(self, hba1c: float) -> dict:
        """
        Interpret hemoglobin A1c levels.

        Args:
            hba1c: HbA1c value in %

        Returns:
            HbA1c interpretation and diabetes assessment
        """
        if hba1c < 5.7:
            category = "Normal"
            recommendation = "Normal glucose levels"
            avg_glucose = "117 mg/dL"
        elif hba1c < 6.5:
            category = "Prediabetes"
            recommendation = "Increased risk of developing diabetes - lifestyle changes recommended"
            avg_glucose = "140 mg/dL"
        else:
            category = "Diabetes"
            recommendation = "Diagnostic of diabetes - confirm with blood glucose testing"
            avg_glucose = f"~{int(hba1c * 28.7)} mg/dL"

        return {
            "hba1c": hba1c,
            "category": category,
            "recommendation": recommendation,
            "estimated_average_glucose": avg_glucose
        }

    @is_tool(ToolType.READ)
    def interpret_thyroid(self, tsh: float, t4: Optional[float] = None) -> dict:
        """
        Interpret thyroid function tests.

        Args:
            tsh: TSH level in mIU/L
            t4: Optional T4 level in mcg/dL

        Returns:
            Thyroid function interpretation
        """
        if tsh < 0.4:
            if t4 and t4 > 2.0:
                condition = "Hyperthyroidism (overactive)"
                recommendation = "Consider antithyroid medication or radioiodine"
            else:
                condition = "Subclinical hyperthyroidism"
                recommendation = "Monitor and repeat TSH in 2-3 months"
        elif tsh > 4.0:
            if t4 and t4 < 0.8:
                condition = "Hypothyroidism (underactive)"
                recommendation = "Consider levothyroxine replacement"
            else:
                condition = "Subclinical hypothyroidism"
                recommendation = "Monitor and repeat TSH in 2-3 months"
        else:
            condition = "Normal thyroid function"
            recommendation = "No intervention needed"

        return {
            "tsh": tsh,
            "t4": t4,
            "condition": condition,
            "recommendation": recommendation
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