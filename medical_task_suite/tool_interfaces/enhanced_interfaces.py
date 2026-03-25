"""
Enhanced Tool Interfaces for Medical Task Suite

This module provides enhanced implementations of tool interfaces
with actual logic for testing and integration.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re


class EnhancedHISInterface:
    """Enhanced HIS interface with mock data and logic."""

    def __init__(self):
        """Initialize enhanced HIS interface."""
        self.mock_patients = self._create_mock_patients()
        self.mock_appointments = self._create_mock_appointments()

    def _create_mock_patients(self) -> Dict[str, Dict]:
        """Create mock patient database."""
        return {
            "P001": {
                "patient_id": "P001",
                "name": "张三",
                "age": 45,
                "gender": "男",
                "phone": "13800138000",
                "insurance": "城镇职工基本医疗保险",
                "allergies": ["青霉素"],
                "chronic_conditions": ["高血压", "糖尿病"],
                "last_visit": "2024-03-15"
            },
            "P002": {
                "patient_id": "P002",
                "name": "李四",
                "age": 32,
                "gender": "女",
                "phone": "13900139000",
                "insurance": "城镇居民基本医疗保险",
                "allergies": [],
                "chronic_conditions": [],
                "last_visit": "2024-02-20"
            }
        }

    def _create_mock_appointments(self) -> List[Dict]:
        """Create mock appointments."""
        return [
            {
                "appointment_id": "APT001",
                "patient_id": "P001",
                "department": "心内科",
                "doctor": "王医生",
                "appointment_time": "2024-03-25 09:00",
                "status": "scheduled",
                "purpose": "高血压复诊"
            }
        ]

    def get_patient_records(
        self,
        patient_id: str,
        record_type: Optional[str] = None,
        date_range: Optional[tuple] = None
    ) -> List[Dict]:
        """Get patient records with mock data."""
        if patient_id not in self.mock_patients:
            return []

        # Return mock records
        return [
            {
                "record_id": "R001",
                "patient_id": patient_id,
                "visit_date": "2024-03-15",
                "department": "心内科",
                "doctor": "李医生",
                "diagnosis": "高血压",
                "treatment": "降压药物治疗",
                "notes": "血压控制尚可，继续用药"
            }
        ]

    def verify_patient_exists(self, patient_id: str) -> bool:
        """Check if patient exists."""
        return patient_id in self.mock_patients


class EnhancedDrugDatabase:
    """Enhanced drug database with actual interaction data."""

    def __init__(self):
        """Initialize enhanced drug database."""
        self.drug_database = self._create_drug_database()
        self.interactions = self._create_interactions()
        self.allergies = self._create_allergy_data()

    def _create_drug_database(self) -> Dict[str, Dict]:
        """Create mock drug database."""
        return {
            "阿司匹林": {
                "generic_name": "阿司匹林",
                "category": "抗血小板药",
                "contraindications": ["活动性溃疡", "出血倾向"],
                "side_effects": ["胃肠道反应", "出血"],
                "pregnancy_category": "C"
            },
            "阿莫西林": {
                "generic_name": "阿莫西林",
                "category": "抗生素",
                "contraindications": ["青霉素过敏"],
                "side_effects": ["过敏反应", "胃肠道反应"],
                "pregnancy_category": "B"
            },
            "硝苯地平": {
                "generic_name": "硝苯地平",
                "category": "钙通道阻滞剂",
                "contraindications": ["严重低血压", "心源性休克"],
                "side_effects": ["头痛", "面部潮红", "踝部水肿"],
                "pregnancy_category": "C"
            }
        }

    def _create_interactions(self) -> Dict[str, List[Dict]]:
        """Create drug interaction data."""
        return {
            "阿司匹林": [
                {
                    "drug": "华法林",
                    "severity": "major",
                    "description": "增加出血风险",
                    "management": "监测INR，调整剂量"
                },
                {
                    "drug": "布洛芬",
                    "severity": "moderate",
                    "description": "增加胃肠道出血风险",
                    "management": "建议避免合用"
                }
            ]
        }

    def _create_allergy_data(self) -> Dict[str, List[str]]:
        """Create allergy cross-reactivity data."""
        return {
            "青霉素": ["阿莫西林", "氨苄西林", "苯唑西林"],
            "磺胺类": ["磺胺甲噁唑", "磺胺嘧啶"]
        }

    def check_interactions(
        self,
        medications: List[str]
    ) -> List[Dict]:
        """Check for drug interactions."""
        found_interactions = []

        for i, med1 in enumerate(medications):
            for med2 in medications[i+1:]:
                # Check if med1 has interactions with med2
                if med1 in self.interactions:
                    for interaction in self.interactions[med1]:
                        if interaction['drug'] == med2:
                            found_interactions.append(interaction)

        return found_interactions

    def check_allergy_cross_reactivity(
        self,
        allergen: str,
        medication: str
    ) -> bool:
        """Check for allergy cross-reactivity."""
        if allergen in self.allergies:
            return medication in self.allergies[allergen]
        return False


class EnhancedInsuranceSystem:
    """Enhanced insurance system with actual logic."""

    def __init__(self):
        """Initialize enhanced insurance system."""
        self.coverage_rules = self._create_coverage_rules()
        self.reimbursement_rates = {
            "城镇职工基本医疗保险": {
                "outpatient": 0.70,
                "inpatient": 0.80,
                "chronic_disease": 0.85
            },
            "城镇居民基本医疗保险": {
                "outpatient": 0.50,
                "inpatient": 0.60,
                "chronic_disease": 0.70
            }
        }

    def _create_coverage_rules(self) -> Dict[str, Dict]:
        """Create coverage rules."""
        return {
            "血常规": {"covered": True, "category": "化验检查", "reimbursement": 0.8},
            "CT检查": {"covered": True, "category": "影像检查", "reimbursement": 0.7},
            "MRI检查": {"covered": True, "category": "影像检查", "reimbursement": 0.6},
            "降压药": {"covered": True, "category": "药品", "reimbursement": 0.7}
        }

    def calculate_reimbursement(
        self,
        insurance_type: str,
        services: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate actual reimbursement amounts."""
        total_cost = sum(s.get('cost', 0) for s in services)

        if insurance_type not in self.reimbursement_rates:
            return {
                "total_cost": total_cost,
                "covered_amount": 0,
                "patient_responsibility": total_cost
            }

        # Simplified calculation
        coverage_rate = self.reimbursement_rates[insurance_type]["outpatient"]
        covered_amount = total_cost * coverage_rate

        return {
            "total_cost": total_cost,
            "covered_amount": covered_amount,
            "patient_responsibility": total_cost - covered_amount,
            "coverage_rate": coverage_rate
        }

    def check_service_coverage(
        self,
        insurance_type: str,
        service_name: str
    ) -> Dict[str, Any]:
        """Check if a service is covered."""
        if service_name in self.coverage_rules:
            rule = self.coverage_rules[service_name]
            return {
                "is_covered": rule["covered"],
                "category": rule["category"],
                "reimbursement_rate": rule["reimbursement"]
            }
        return {
            "is_covered": False,
            "reason": "Service not found in coverage list"
        }


class EnhancedOCRInterface:
    """Enhanced OCR interface with actual processing logic."""

    def __init__(self):
        """Initialize enhanced OCR interface."""
        self.processed_documents = []

    def extract_text_from_image(
        self,
        image_description: str
    ) -> Dict[str, Any]:
        """
        Extract text from image (using description in this stub).

        In production, this would call actual OCR APIs.
        """
        # Simulate OCR extraction based on description
        if "血常规" in image_description or "化验单" in image_description:
            return self._extract_lab_report(image_description)
        elif "处方" in image_description:
            return self._extract_prescription(image_description)
        else:
            return {
                "text": "",
                "confidence": 0.0,
                "extracted_fields": {},
                "quality": "poor"
            }

    def _extract_lab_report(self, description: str) -> Dict[str, Any]:
        """Extract lab report fields."""
        return {
            "text": "血常规检查报告\nWBC: 11.5×10^9/L\nRBC: 4.5×10^12/L\nHb: 135g/L\nPLT: 220×10^9/L",
            "confidence": 0.92,
            "document_type": "lab_report",
            "extracted_fields": {
                "test_name": "血常规",
                "WBC": {"value": "11.5", "unit": "10^9/L", "flag": "H"},
                "RBC": {"value": "4.5", "unit": "10^12/L", "flag": ""},
                "Hb": {"value": "135", "unit": "g/L", "flag": ""},
                "PLT": {"value": "220", "unit": "10^9/L", "flag": ""}
            },
            "quality": "good"
        }

    def _extract_prescription(self, description: str) -> Dict[str, Any]:
        """Extract prescription fields."""
        return {
            "text": "Rx\n阿司匹林肠溶片 100mg\nsig: 100mg po qd\n",
            "confidence": 0.88,
            "document_type": "prescription",
            "extracted_fields": {
                "medication": "阿司匹林肠溶片",
                "dosage": "100mg",
                "frequency": "qd",
                "route": "po"
            },
            "quality": "good"
        }

    def verify_quality(
        self,
        ocr_result: Dict[str, Any],
        expected_fields: List[str]
    ) -> Dict[str, Any]:
        """Verify OCR extraction quality."""
        extracted = set(ocr_result.get("extracted_fields", {}).keys())
        expected = set(expected_fields)

        return {
            "completeness": len(extracted & expected) / len(expected) if expected else 0,
            "confidence": ocr_result.get("confidence", 0),
            "quality_score": ocr_result.get("quality", "unknown"),
            "missing_fields": list(expected - extracted)
        }


# Factory functions
def create_enhanced_his_interface() -> EnhancedHISInterface:
    """Create enhanced HIS interface."""
    return EnhancedHISInterface()


def create_enhanced_drug_database() -> EnhancedDrugDatabase:
    """Create enhanced drug database."""
    return EnhancedDrugDatabase()


def create_enhanced_insurance_system() -> EnhancedInsuranceSystem:
    """Create enhanced insurance system."""
    return EnhancedInsuranceSystem()


def create_enhanced_ocr_interface() -> EnhancedOCRInterface:
    """Create enhanced OCR interface."""
    return EnhancedOCRInterface()
