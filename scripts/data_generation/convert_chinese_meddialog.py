#!/usr/bin/env python3
"""
Convert Chinese MedDialog Dataset to Tau2-Bench Format

This script converts real Chinese medical dialogue data from the
Chinese MedDialog dataset (792,099 Q&A pairs) into tau2-bench format.

Author: Claude Sonnet 4.5
Date: 2025-03-13
"""

import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "UniClinicalDataEngine" / "generators"))

from utils import (
    extract_entities_from_text,
    map_to_tau2_domain,
    determine_gender_from_context,
    generate_patient_mrn,
    generate_patient_name,
)


class ChineseMedDialogConverter:
    """Convert Chinese medical dialogues to tau2-bench format."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the converter.

        Args:
            config: Optional configuration with keys:
                - max_samples: Maximum number of samples per department (default: 1000)
                - min_dialogue_length: Minimum dialogue length (default: 2)
                - departments: List of departments to process (default: all)
        """
        self.config = config or {}
        self.max_samples = self.config.get("max_samples", 1000)
        self.min_dialogue_length = self.config.get("min_dialogue_length", 2)
        self.target_departments = self.config.get("departments", None)

        # Department mapping from Chinese to tau2 domains
        self.department_mapping = {
            "内科": "clinical_internal_medicine",
            "外科": "clinical_surgery",
            "妇产科": "clinical_obstetrics_gynecology",
            "儿科": "clinical_pediatrics",
            "肿瘤科": "clinical_oncology",
            "男科": "clinical_andrology",
        }

        # Statistics
        self.stats = defaultdict(int)

    def load_data(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Load all CSV files from the data directory.

        Args:
            data_dir: Path to the Data_数据 directory

        Returns:
            List of dialogue records
        """
        dialogues = []

        # Find all CSV files
        csv_files = list(data_dir.glob("*/*.csv"))

        print(f"\nFound {len(csv_files)} CSV files")

        for csv_file in csv_files:
            dept_folder = csv_file.parent.name

            # Extract department name from folder name
            dept_cn = self._extract_chinese_dept_name(dept_folder)
            if not dept_cn:
                continue

            # Filter by target departments if specified
            if self.target_departments and dept_cn not in self.target_departments:
                continue

            print(f"  Processing {dept_cn}: {csv_file.name}")

            try:
                # Try multiple encodings
                encodings = ['gbk', 'gb18030', 'utf-8', 'utf-8-sig', 'latin1']
                df = None

                for encoding in encodings:
                    try:
                        df = pd.read_csv(csv_file, encoding=encoding)
                        print(f"    Successfully read with {encoding} encoding")
                        break
                    except (UnicodeDecodeError, UnicodeError):
                        continue

                if df is None:
                    print(f"    Failed to read with any encoding")
                    continue

                # Process each row
                for idx, row in df.iterrows():
                    dialogue = self._process_row(row, dept_cn, idx)
                    if dialogue:
                        dialogues.append(dialogue)
                        self.stats[f"loaded_{dept_cn}"] += 1

                        # Limit samples per department
                        if self.stats[f"loaded_{dept_cn}"] >= self.max_samples:
                            break

            except Exception as e:
                print(f"    Error reading {csv_file.name}: {e}")
                continue

        print(f"\nTotal dialogues loaded: {len(dialogues)}")
        return dialogues

    def _extract_chinese_dept_name(self, folder_name: str) -> Optional[str]:
        """Extract Chinese department name from folder name.

        Args:
            folder_name: Folder name like "IM_内科" or "Andriatria_男科"

        Returns:
            Chinese department name or None
        """
        # Pattern: XXX_中文名
        # Extract the Chinese part after underscore
        if '_' in folder_name:
            parts = folder_name.split('_')
            for part in parts:
                # Check if part contains Chinese characters
                if any('\u4e00' <= char <= '\u9fff' for char in part):
                    # Verify it's a known department
                    if part in self.department_mapping:
                        return part

        # Also check if entire folder name is a known department
        if folder_name in self.department_mapping:
            return folder_name

        return None

    def _process_row(self, row: pd.Series, dept_cn: str, idx: int) -> Optional[Dict[str, Any]]:
        """Process a single row from the CSV.

        Args:
            row: Pandas Series with columns: department, title, ask, answer
            dept_cn: Chinese department name
            idx: Row index

        Returns:
            Dialogue record or None if invalid
        """
        try:
            # Extract fields
            department = dept_cn
            title = str(row.get('title', '')).strip()
            ask = str(row.get('ask', '')).strip()
            answer = str(row.get('answer', '')).strip()

            # Validation
            if not ask or not answer:
                return None

            if len(ask) < self.min_dialogue_length or len(answer) < self.min_dialogue_length:
                return None

            # Extract entities from the dialogue
            entities = extract_entities_from_text(ask + " " + answer)

            # Build dialogue record
            return {
                "id": f"{self.department_mapping.get(dept_cn, 'clinical_other')}_{idx}",
                "department_cn": department,
                "department_en": self.department_mapping.get(dept_cn, "clinical_other"),
                "title": title,
                "patient_question": ask,
                "doctor_answer": answer,
                "entities": entities,
            }

        except Exception as e:
            print(f"    Error processing row {idx}: {e}")
            return None

    def convert_to_tau2(self, dialogues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert dialogues to tau2-bench format.

        Args:
            dialogues: List of dialogue records

        Returns:
            List of tau2 task dictionaries
        """
        tau2_tasks = []

        print("\nConverting to tau2-bench format...")

        for i, dialogue in enumerate(dialogues):
            try:
                tau2_task = self._dialogue_to_tau2(dialogue, i)
                tau2_tasks.append(tau2_task)

                if (i + 1) % 100 == 0:
                    print(f"  Converted {i + 1}/{len(dialogues)} tasks")

            except Exception as e:
                print(f"  Error converting dialogue {i}: {e}")
                continue

        print(f"\nSuccessfully converted {len(tau2_tasks)} tasks")
        return tau2_tasks

    def _dialogue_to_tau2(self, dialogue: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """Convert a single dialogue to tau2 format.

        Args:
            dialogue: Dialogue record
            idx: Index

        Returns:
            Tau2 task dictionary
        """
        dept_en = dialogue["department_en"]
        entities = dialogue.get("entities", {})

        # Generate patient profile
        age = entities.get("age", 45)
        gender = entities.get("gender") or determine_gender_from_context(
            dialogue["patient_question"], age
        )

        # Build user scenario
        user_scenario = {
            "persona": f"{age}-year-old {gender} patient with {dialogue['title']}",
            "instructions": {
                "domain": dept_en.replace("clinical_", ""),
                "reason_for_call": dialogue["title"],
                "known_info": dialogue["patient_question"][:200],
                "unknown_info": None,
                "task_instructions": self._build_task_instructions(dialogue),
            }
        }

        # Build description
        description = {
            "purpose": f"Medical consultation - {dialogue['title']}",
            "relevant_policies": None,
            "notes": f"Real Chinese medical dialogue from {dialogue['department_cn']}. Source: Chinese MedDialog Dataset.",
        }

        # Build ticket
        ticket = dialogue["patient_question"][:200]

        # Build initial state
        initial_state = {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": generate_patient_name(gender),
                        "mrn": generate_patient_mrn(),
                        "age": age,
                        "gender": gender,
                    }
                }
            ]
        }

        # Build evaluation criteria (based on expected doctor response)
        evaluation_criteria = {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {
                        "should_address": dialogue["title"],
                    }
                }
            ],
            "communication_checks": [
                {
                    "check_id": "helpful_response",
                    "criteria": "Response should address patient's concern"
                }
            ]
        }

        return {
            "id": dialogue["id"],
            "description": description,
            "user_scenario": user_scenario,
            "ticket": ticket,
            "initial_state": initial_state,
            "evaluation_criteria": evaluation_criteria,
            "metadata": {
                "source": "Chinese MedDialog",
                "department_cn": dialogue["department_cn"],
                "original_title": dialogue["title"],
            }
        }

    def _build_task_instructions(self, dialogue: Dict[str, Any]) -> str:
        """Build task instructions from dialogue.

        Args:
            dialogue: Dialogue record

        Returns:
            Task instructions string
        """
        instructions = f"""You are a patient seeking medical advice.

Your concern: {dialogue['title']}

Your question to the doctor: {dialogue['patient_question']}

Please engage in a natural conversation with the doctor about your health concern."""
        return instructions

    def save_tasks(self, tasks: List[Dict[str, Any]], output_dir: Path) -> None:
        """Save converted tasks to output directory.

        Args:
            tasks: List of tau2 tasks
            output_dir: Output directory path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save tasks.json
        tasks_file = output_dir / "tasks.json"
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(tasks)} tasks to {tasks_file}")

        # Group by department and save separate files
        dept_tasks = defaultdict(list)
        for task in tasks:
            dept = task["metadata"]["department_cn"]
            dept_tasks[dept].append(task)

        for dept, dept_task_list in dept_tasks.items():
            dept_file = output_dir / f"tasks_{dept}.json"
            with open(dept_file, "w", encoding="utf-8") as f:
                json.dump(dept_task_list, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(dept_task_list)} {dept} tasks to {dept_file}")

        # Create split_tasks.json
        task_ids = [task["id"] for task in tasks]
        split_data = {
            "train": task_ids[:int(len(task_ids) * 0.8)],
            "validation": task_ids[int(len(task_ids) * 0.8):int(len(task_ids) * 0.9)],
            "test": task_ids[int(len(task_ids) * 0.9):]
        }

        split_file = output_dir / "split_tasks.json"
        with open(split_file, "w", encoding="utf-8") as f:
            json.dump(split_data, f, indent=2)
        print(f"Saved train/val/test split to {split_file}")

    def generate_db(self, tasks: List[Dict[str, Any]], output_dir: Path) -> None:
        """Generate database from tasks.

        Args:
            tasks: List of tau2 tasks
            output_dir: Output directory path
        """
        patients = {}

        for task in tasks:
            init_actions = task.get("initial_state", {}).get("initialization_actions", [])
            if init_actions:
                patient_info = init_actions[0].get("arguments", {})
                mrn = patient_info.get("mrn")

                if mrn and mrn not in patients:
                    patients[mrn] = {
                        "name": patient_info.get("name"),
                        "age": patient_info.get("age"),
                        "gender": patient_info.get("gender"),
                        "chief_complaint": task.get("ticket", ""),
                        "department": task["metadata"]["department_cn"],
                    }

        db_file = output_dir / "db.json"
        db_data = {"patients": patients}

        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=2, ensure_ascii=False)

        print(f"Saved database with {len(patients)} patients to {db_file}")

    def print_statistics(self) -> None:
        """Print conversion statistics."""
        print("\n" + "=" * 70)
        print("  CONVERSION STATISTICS")
        print("=" * 70)

        for key, value in sorted(self.stats.items()):
            print(f"  {key}: {value}")

        print("=" * 70 + "\n")


def main():
    """Main conversion function."""
    print("\n" + "=" * 70)
    print("  CHINESE MEDDIALOG TO TAU2-BENCH CONVERSION")
    print("=" * 70)

    # Configuration
    config = {
        "max_samples": 500,  # Limit to 500 per department for testing
        "min_dialogue_length": 10,
        "departments": None,  # Process all departments
    }

    # Paths
    data_dir = project_root / "data" / "raw" / "medical_dialogues" / "chinese_meddialog" / "Data_数据"
    output_dir = project_root / "data" / "processed" / "medical_dialogues" / "chinese_meddialog"

    print(f"\nInput directory: {data_dir}")
    print(f"Output directory: {output_dir}")

    # Check input directory
    if not data_dir.exists():
        print(f"\nERROR: Input directory not found: {data_dir}")
        return

    # Initialize converter
    converter = ChineseMedDialogConverter(config)

    # Load data
    print("\nStep 1: Loading raw dialogues...")
    dialogues = converter.load_data(data_dir)

    if not dialogues:
        print("\nERROR: No dialogues loaded!")
        return

    # Convert to tau2 format
    print("\nStep 2: Converting to tau2-bench format...")
    tau2_tasks = converter.convert_to_tau2(dialogues)

    # Save results
    print("\nStep 3: Saving results...")
    converter.save_tasks(tau2_tasks, output_dir)
    converter.generate_db(tau2_tasks, output_dir)

    # Print statistics
    converter.print_statistics()

    print("=" * 70)
    print("  CONVERSION COMPLETE")
    print("=" * 70)
    print(f"\nOutput files saved to: {output_dir}")
    print(f"  - tasks.json (all tasks)")
    print(f"  - tasks_<department>.json (by department)")
    print(f"  - db.json (patient database)")
    print(f"  - split_tasks.json (train/val/test split)")
    print()


if __name__ == "__main__":
    main()
