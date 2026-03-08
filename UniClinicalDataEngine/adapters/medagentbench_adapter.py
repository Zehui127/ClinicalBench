#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedAgentBench Format Adapter for Clinical Data
MedAgentBench 格式的适配器

Handles MedAgentBench dataset format with FHIR tool schemas.
MedAgentBench is a benchmark for medical LLM agents with virtual EHR interactions.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base import BaseAdapter


class MedAgentBenchAdapter(BaseAdapter):
    """
    Adapter for MedAgentBench format.

    MedAgentBench structure:
    - id: Task identifier
    - instruction: Clinical task/question
    - context: Additional context (timestamp, constraints)
    - sol: Expected solution(s)
    - eval_MRN: Patient MRN for evaluation (optional)

    Additionally handles:
    - funcs_v1.json: FHIR function schemas
    """

    def __init__(self):
        """Initialize the adapter."""
        super().__init__()
        self.format_name = "medagentbench"

    def load(self, path: str) -> List[Dict[str, Any]]:
        """
        Load MedAgentBench data from file.

        Args:
            path: Path to test_data_v2.json or funcs_v1.json

        Returns:
            List of normalized records
        """
        p = self.validate_path(path, must_exist=True)

        with open(p, "r", encoding="utf-8") as f:
            content = json.load(f)

        # Handle different file types
        if "funcs" in p.name.lower():
            # Load FHIR function schemas
            return self._load_fhir_functions(content)
        else:
            # Load test data
            if isinstance(content, list):
                return [self._normalize_record(record) for record in content]
            elif isinstance(content, dict):
                if "data" in content:
                    return [self._normalize_record(r) for r in content["data"]]
                else:
                    return [self._normalize_record(content)]

        raise ValueError(f"Invalid MedAgentBench format in {path}")

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize MedAgentBench record to standard format.

        Field Mapping:
        - id -> id (task identifier)
        - instruction -> description (clinical task)
        - context -> clinical_scenario.context (additional info)
        - sol -> expected_outcome (expected answer)
        - eval_MRN -> clinical_scenario.patient_info.mrn
        """
        instruction = record.get("instruction", "")
        context = record.get("context", "")

        normalized = {
            "id": record.get("id", ""),
            "description": instruction,
            "department": self._infer_department(instruction, context),
            "difficulty": "moderate",
            "clinical_scenario": self._build_clinical_scenario(record),
            "tool_call_requirements": {
                "required_tools": [],
                "optional_tools": [],
                "tool_parameters": {}
            },
            "expected_outcome": self._format_solution(record.get("sol", [])),
            "metadata": {
                "source": "medagentbench",
                "task_type": self._classify_task_type(record),
                "context": context,
                "eval_mrn": record.get("eval_MRN"),
            }
        }

        return normalized

    def _infer_department(self, instruction: str, context: str) -> str:
        """
        Infer medical department from task content.

        Args:
            instruction: Task instruction text
            context: Additional context

        Returns:
            Department name
        """
        text = f"{instruction} {context}".lower()

        # Keyword-based department inference
        dept_keywords = {
            "cardiology": ["heart", "cardiac", "ecg", "echocardiogram", "chest pain"],
            "nephrology": ["kidney", "renal", "egfr", "creatinine", "dialysis", "glomerul"],
            "gastroenterology": ["gi", "stomach", "digestive", "endoscopy", "liver disease",
                                  "hepatology", "cirrhosis", "pancreatitis"],
            "neurology": ["brain", "neuro", "seizure", "stroke", "headache", "neural"],
            "oncology": ["cancer", "tumor", "tumour", "chemotherapy", "oncology",
                         "leukem", "lymphom"],
            "pulmonology": ["lung", "respiratory", "pulmonary", "pneumonia", "asthma"],
            "endocrinology": ["diabetes", "thyroid", "hormone", "insulin", "glucose"],
            "pediatrics": ["pediatric", "child", "infant", "neonat"],
        }

        for dept, keywords in dept_keywords.items():
            if any(keyword in text for keyword in keywords):
                return dept

        return "general_practice"

    def _build_clinical_scenario(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build clinical scenario from MedAgentBench record.

        Args:
            record: Raw MedAgentBench record

        Returns:
            Clinical scenario dictionary
        """
        instruction = record.get("instruction", "")

        return {
            "patient_info": {
                "mrn": record.get("eval_MRN", ""),
                "name": self._extract_patient_name(instruction),
                "dob": self._extract_dob(instruction),
                "age": None,
                "gender": "unknown",
                "symptoms": []
            },
            "context": record.get("context", ""),
            "diagnosis": "",
            "vital_signs": {},
            "lab_results": {},
            "medications": [],
            "comorbidities": []
        }

    def _extract_patient_name(self, instruction: str) -> str:
        """
        Extract patient name from instruction.

        Args:
            instruction: Task instruction text

        Returns:
            Patient name or empty string
        """
        # Pattern: "name <First> <Last>" or "patient with name ..."
        patterns = [
            r'name\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'patient\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, instruction)
            if match:
                return match.group(1)

        return ""

    def _extract_dob(self, instruction: str) -> str:
        """
        Extract date of birth from instruction.

        Args:
            instruction: Task instruction text

        Returns:
            DOB string or empty string
        """
        # Pattern: "DOB of YYYY-MM-DD" or "DOB: YYYY-MM-DD"
        patterns = [
            r'DOB\s+of\s+(\d{4}-\d{2}-\d{2})',
            r'DOB[:\s]+(\d{4}-\d{2}-\d{2})',
            r'date\s+of\s+birth[:\s]+(\d{4}-\d{2}-\d{2})',
        ]

        for pattern in patterns:
            match = re.search(pattern, instruction)
            if match:
                return match.group(1)

        return ""

    def _format_solution(self, sol: Any) -> str:
        """
        Format solution(s) as string.

        Args:
            sol: Solution (string, list, or other)

        Returns:
            Formatted solution string
        """
        if isinstance(sol, list):
            return ", ".join(str(s) for s in sol)
        return str(sol) if sol else ""

    def _classify_task_type(self, record: Dict[str, Any]) -> str:
        """
        Classify the type of clinical task.

        Args:
            record: MedAgentBench record

        Returns:
            Task type string
        """
        instruction = record.get("instruction", "").lower()

        # Task type classification
        if "mrn" in instruction and ("name" in instruction or "patient" in instruction):
            return "patient_lookup"
        elif "age" in instruction:
            return "patient_demographics"
        elif "medication" in instruction or "prescri" in instruction:
            return "medication_query"
        elif "lab" in instruction or "observation" in instruction or "magnesium" in instruction:
            return "lab_results"
        elif "condition" in instruction or "diagnosis" in instruction or "problem" in instruction:
            return "condition_query"
        elif "vital" in instruction or "blood pressure" in instruction:
            return "vital_signs"
        elif "referral" in instruction or "consult" in instruction:
            return "referral"
        else:
            return "general_query"

    def _load_fhir_functions(self, content: List[Dict]) -> List[Dict[str, Any]]:
        """
        Load and normalize FHIR function schemas from funcs_v1.json.

        Args:
            content: List of FHIR function definitions

        Returns:
            List of tool definitions compatible with the engine
        """
        tools = []

        for func in content:
            tool = {
                "name": self._extract_tool_name(func.get("name", "")),
                "display_name": func.get("name", ""),
                "description": func.get("description", ""),
                "category": "fhir",
                "department": "general",
                "version": "1.0.0",
                "parameters": self._convert_fhir_parameters(func.get("parameters", {})),
                "fhir_endpoint": func.get("name", ""),
                "is_fhir_tool": True,
                "original_schema": func,
            }
            tools.append(tool)

        return tools

    def _extract_tool_name(self, fhir_name: str) -> str:
        """
        Extract tool name from FHIR endpoint name.

        Args:
            fhir_name: FHIR endpoint name like "GET {api_base}/Patient"

        Returns:
            Normalized tool name like "fhir_patient_search"
        """
        # Remove template variables and convert to snake_case
        name = fhir_name.replace("{api_base}/", "")
        name = name.replace("/", "_")
        name = name.lower().replace(" ", "_").replace("-", "_")

        return f"fhir_{name}"

    def _convert_fhir_parameters(self, fhir_params: Dict) -> List[Dict[str, Any]]:
        """
        Convert FHIR parameters to tool parameter format.

        Args:
            fhir_params: FHIR parameter schema

        Returns:
            List of parameter definitions
        """
        params = []
        properties = fhir_params.get("properties", {})
        required = fhir_params.get("required", [])

        for param_name, param_info in properties.items():
            params.append({
                "name": param_name,
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", ""),
                "required": param_name in required,
            })

        return params

    def save(self, data: List[Dict[str, Any]], path: str) -> None:
        """
        Save data to MedAgentBench format.

        Args:
            data: List of records to save
            path: Output file path
        """
        self.validate_data(data)
        self.validate_path(path, must_exist=False)

        p = Path(path)

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
