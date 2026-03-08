#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete ETL Pipeline Test
完整 ETL 管道测试

Demonstrates the complete functionality of UniClinicalDataEngine.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from UniClinicalDataEngine import (
    ClinicalETLEngine,
    ETLConfig,
    run_etl,
    CLINICAL_TOOLS,
)


def create_sample_data_nhands_jsonl(output_path: str):
    """Create sample NHands JSONL data file."""
    sample_data = [
        {
            "id": "TASK001",
            "description": "65-year-old male with hypertension and CKD stage 3",
            "department": "cardiology",
            "difficulty": "moderate",
            "clinical_scenario": {
                "patient_info": {
                    "age": 65,
                    "gender": "male",
                    "symptoms": ["headache", "dizziness"],
                },
                "diagnosis": "hypertension, CKD stage 3",
                "vital_signs": {
                    "blood_pressure_systolic": 165,
                    "blood_pressure_diastolic": 95,
                    "heart_rate": 78,
                },
                "lab_results": {
                    "creatinine": 1.8,
                    "egfr": 42,
                },
                "medications": ["lisinopril", "amlodipine"],
            },
            "tool_call_requirements": {
                "required_tools": ["drug_dosing_calculator", "drug_interaction_checker"],
            },
        },
        {
            "id": "TASK002",
            "description": "45-year-old female with peptic ulcer requiring medication adjustment",
            "department": "gastroenterology",
            "difficulty": "easy",
            "clinical_scenario": {
                "patient_info": {
                    "age": 45,
                    "gender": "female",
                    "symptoms": ["abdominal pain", "nausea"],
                },
                "diagnosis": "peptic ulcer disease",
                "vital_signs": {
                    "blood_pressure_systolic": 120,
                    "blood_pressure_diastolic": 80,
                    "temperature": 37.2,
                },
                "lab_results": {
                    "hemoglobin": 12.5,
                    "h_pylori": "positive",
                },
                "medications": ["omeprazole"],
            },
            "tool_call_requirements": {
                "required_tools": ["drug_interaction_checker"],
            },
        },
        {
            "id": "TASK003",
            "description": "72-year-old male with end-stage renal disease on dialysis",
            "department": "nephrology",
            "difficulty": "hard",
            "clinical_scenario": {
                "patient_info": {
                    "age": 72,
                    "gender": "male",
                    "symptoms": ["fatigue", "shortness of breath"],
                },
                "diagnosis": "ESRD on hemodialysis",
                "vital_signs": {
                    "blood_pressure_systolic": 150,
                    "blood_pressure_diastolic": 85,
                    "heart_rate": 88,
                    "oxygen_saturation": 94,
                },
                "lab_results": {
                    "creatinine": 5.2,
                    "egfr": 12,
                    "potassium": 5.2,
                    "hemoglobin": 9.8,
                },
                "medications": ["epoetin alfa", "calcitriol", "sevelamer"],
                "comorbidities": ["diabetes", "hypertension", "heart failure"],
            },
            "tool_call_requirements": {
                "required_tools": ["egfr_calculator", "drug_dosing_calculator"],
            },
        },
        {
            "id": "TASK004",
            "description": "28-year-old female with acute chest pain",
            "department": "cardiology",
            "difficulty": "moderate",
            "clinical_scenario": {
                "patient_info": {
                    "age": 28,
                    "gender": "female",
                    "symptoms": ["chest pain", "palpitations"],
                },
                "diagnosis": "suspected acute coronary syndrome",
                "vital_signs": {
                    "blood_pressure_systolic": 140,
                    "blood_pressure_diastolic": 90,
                    "heart_rate": 105,
                    "respiratory_rate": 18,
                    "temperature": 37.0,
                },
                "lab_results": {
                    "troponin": 0.05,
                    "ck_mb": 15,
                    "bnp": 150,
                },
                "medications": ["aspirin", "nitroglycerin"],
            },
            "tool_call_requirements": {
                "required_tools": ["vital_signs_analyzer", "lab_values_interpreter"],
            },
        },
        {
            "id": "TASK005",
            "description": "55-year-old male with abnormal vital signs during routine checkup",
            "department": "general_practice",
            "difficulty": "easy",
            "clinical_scenario": {
                "patient_info": {
                    "age": 55,
                    "gender": "male",
                    "symptoms": [],
                },
                "diagnosis": "routine health assessment",
                "vital_signs": {
                    "blood_pressure_systolic": 145,
                    "blood_pressure_diastolic": 92,
                    "heart_rate": 72,
                    "temperature": 36.8,
                    "respiratory_rate": 16,
                    "oxygen_saturation": 98,
                },
                "lab_results": {
                    "fasting_glucose": 105,
                    "cholesterol": 220,
                    "ldl": 145,
                },
                "medications": [],
            },
            "tool_call_requirements": {
                "required_tools": ["vital_signs_analyzer", "clinical_calculator"],
            },
        },
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for record in sample_data:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Created sample data: {output_path}")
    print(f"  Records: {len(sample_data)}")
    return len(sample_data)


def create_sample_data_csv(output_path: str):
    """Create sample CSV data file."""
    import csv

    sample_data = [
        ["id", "description", "department", "difficulty", "age", "gender", "diagnosis", "creatinine", "egfr"],
        ["TASK101", "Hypertension management", "cardiology", "moderate", "58", "male", "hypertension", "1.2", "68"],
        ["TASK102", "CKD monitoring", "nephrology", "easy", "62", "female", "CKD stage 2", "1.1", "72"],
        ["TASK103", "GERD treatment", "gastroenterology", "easy", "35", "male", "GERD", "", ""],
        ["TASK104", "Arrhythmia evaluation", "cardiology", "hard", "71", "female", "atrial fibrillation", "1.4", "52"],
        ["TASK105", "Ulcer followup", "gastroenterology", "moderate", "48", "male", "peptic ulcer", "", ""],
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(sample_data)

    print(f"Created sample CSV data: {output_path}")
    return len(sample_data) - 1


def test_etl_pipeline():
    """Test complete ETL pipeline."""
    print("\n" + "=" * 60)
    print("UniClinicalDataEngine ETL Pipeline Test")
    print("=" * 60)

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="etl_test_")
    print(f"\nTemporary directory: {temp_dir}")

    try:
        # Test 1: NHands JSONL format
        print("\n" + "-" * 60)
        print("Test 1: NHands JSONL Format")
        print("-" * 60)

        jsonl_input = os.path.join(temp_dir, "test_input.jsonl")
        jsonl_output = os.path.join(temp_dir, "output_jsonl")

        create_sample_data_nhands_jsonl(jsonl_input)

        result = run_etl(
            input_path=jsonl_input,
            input_format="nhands_jsonl",
            output_dir=jsonl_output,
        )

        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Records processed: {result.records_processed}")
        print(f"Tasks generated: {result.tasks_generated}")

        if result.success:
            # Verify output files
            for name, path in result.output_files.items():
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"  [OK] {name}: {size} bytes")
                else:
                    print(f"  [MISSING] {name}: NOT FOUND")

        # Test 2: CSV format
        print("\n" + "-" * 60)
        print("Test 2: CSV Format")
        print("-" * 60)

        csv_input = os.path.join(temp_dir, "test_input.csv")
        csv_output = os.path.join(temp_dir, "output_csv")

        create_sample_data_csv(csv_input)

        result = run_etl(
            input_path=csv_input,
            input_format="csv",
            output_dir=csv_output,
        )

        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Records processed: {result.records_processed}")

        # Test 3: With filters
        print("\n" + "-" * 60)
        print("Test 3: With Department Filter")
        print("-" * 60)

        filtered_output = os.path.join(temp_dir, "output_filtered")

        result = run_etl(
            input_path=jsonl_input,
            input_format="nhands_jsonl",
            output_dir=filtered_output,
            department_filter="cardiology",
        )

        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Records processed: {result.records_processed}")

        # Test 4: Tools
        print("\n" + "-" * 60)
        print("Test 4: Clinical Tools")
        print("-" * 60)

        print(f"Total tools available: {len(CLINICAL_TOOLS)}")
        for tool in CLINICAL_TOOLS:
            print(f"  - {tool['name']}: {tool['display_name']}")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"[OK] All tests completed")
        print(f"[OK] Output directory: {temp_dir}")
        print(f"\nTo inspect results, check:")
        print(f"  - tasks.json: Clinical task definitions")
        print(f"  - db.json: Clinical knowledge database")
        print(f"  - tools.json: Tool definitions")
        print(f"  - policy.md: Usage policy document")
        print(f"  - etl_summary.json: ETL execution summary")

        # Show one sample output
        summary_file = os.path.join(jsonl_output, "etl_summary.json")
        if os.path.exists(summary_file):
            with open(summary_file, "r", encoding="utf-8") as f:
                summary = json.load(f)
            print(f"\nSample from summary:")
            stats = summary.get("statistics", {})
            print(f"  By department: {stats.get('by_department', {})}")
            print(f"  By difficulty: {stats.get('by_difficulty', {})}")

    finally:
        print(f"\nTest directory preserved: {temp_dir}")


if __name__ == "__main__":
    test_etl_pipeline()
