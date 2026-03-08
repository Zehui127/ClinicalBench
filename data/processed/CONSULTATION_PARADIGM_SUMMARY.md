# Medical Consultation Paradigm - Unified Reconstruction Summary

**Date:** 2026-03-03
**Version:** 1.0

## Overview

Successfully reconstructed all 4 medical datasets into a **unified medical consultation task paradigm** following the doctor-patient dialogue format ("患者问：... 医生答：...").

---

## Generated Files

### 1. MedAgentBench Consultation Paradigm
- **Path:** `C:\Users\方正\tau2-bench\data\processed\medagentbench\consultation_paradigm.json`
- **Task Count:** 8 tasks
- **Task Type:** `core_consultation`
- **Consultation Scenario:** `primary_care`
- **File Size:** 14,728 bytes

### 2. MedXpertQA Consultation Paradigm
- **Path:** `C:\Users\方正\tau2-bench\data\processed\medxpertqa\consultation_paradigm.json`
- **Task Count:** 2,450 tasks
- **Task Type:** `specialist_consultation`
- **Consultation Scenario:** `specialist_consultation`
- **File Size:** 10,378,648 bytes (~9.9 MB)

### 3. PhysioNet Consultation Paradigm
- **Path:** `C:\Users\方正\tau2-bench\data\processed\physionet\consultation_paradigm.json`
- **Task Count:** 10 tasks
- **Task Type:** `structured_query`
- **Consultation Scenario:** `pre_consultation_data`
- **File Size:** 18,357 bytes

### 4. ProdMedBench Consultation Paradigm
- **Path:** `C:\Users\方正\tau2-bench\data\processed\prodmedbench\consultation_paradigm.json`
- **Task Count:** 1,000 tasks
- **Task Type:** `mcq_screening`
- **Consultation Scenario:** `differential_diagnosis`
- **File Size:** 1,058,591 bytes (~1 MB)

### 5. Universal Consultation Template
- **Path:** `C:\Users\方正\tau2-bench\data\processed\universal_template\universal_consultation_template.json`
- **Purpose:** Unified field standards and workflow definition
- **File Size:** 3,243 bytes

---

## Task Hierarchy

### Core Consultation Tasks (2,458 tasks)
- **MedAgentBench (8 tasks):** Primary care consultation - patient information lookup
- **MedXpertQA (2,450 tasks):** Specialist consultation - medical knowledge Q&A

### Supplementary Tasks (1,010 tasks)
- **PhysioNet (10 tasks):** Pre-consultation data retrieval - structured lab queries
- **ProdMedBench (1,000 tasks):** MCQ screening - differential diagnosis with CoT

**Total: 3,468 consultation tasks**

---

## Unified Consultation Workflow

```
Step 1: Pre-consultation Data Retrieval
    ↓ (structured_query - PhysioNet)
    Retrieve patient lab results, vital signs, diagnoses

Step 2: Primary Care Assessment
    ↓ (core_consultation - MedAgentBench)
    Initial consultation, patient information lookup

Step 3: Specialist Consultation
    ↓ (specialist_consultation - MedXpertQA)
    Complex medical knowledge Q&A, specialist advice

Step 4: Differential Diagnosis Screening
    ↓ (mcq_screening - ProdMedBench)
    MCQ with chain-of-thought reasoning

Step 5: Resolution
    ↓
    Final diagnosis/advice in natural language
```

---

## Mandatory Field Standards

All consultation paradigm tasks include:

| Field | Format | Description |
|-------|--------|-------------|
| `id` | string | Unique task identifier |
| `task_type` | enum | `core_consultation` \| `structured_query` \| `mcq_screening` \| `specialist_consultation` |
| `consultation_scenario` | enum | `primary_care` \| `pre_consultation_data` \| `specialist_consultation` \| `differential_diagnosis` |
| `question` | string | Consultation question (prefixed with role) |
| `answer` | string | Consultation answer (prefixed with role) |
| `domain` | string | Always `clinical/consultation` |
| `ticket` | string | Original question text |
| `original_format` | string | Source dataset name |

### Question Format Examples

**MedAgentBench (Primary Care):**
```json
"question": "Patient asks: What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29?"
"answer": "Doctor answers: Please provide the patient information."
```

**PhysioNet (Pre-consultation):**
```json
"question": "Nurse asks: What is the creatinine level of patient 10032?"
"answer": "Doctor answers: 1.2 mg/dL"
```

**MedXpertQA (Specialist):**
```json
"question": "Patient asks: [Medical question from MedXpertQA]"
"answer": "Doctor answers: [Medical answer]"
```

**ProdMedBench (MCQ Screening):**
```json
"question": "Patient asks: [Chinese medical MCQ]"
"answer": "Doctor answers: [Correct option]"
"options": "A. xxx B. xxx C. xxx D. xxx E. xxx"
"cot": "[Chain of thought reasoning]"
```

---

## Dataset Mapping Table

| Dataset | Tasks | Type | Scenario | Description |
|---------|-------|------|----------|-------------|
| MedAgentBench | 8 | Core | primary_care | Patient MRN lookup, free-form consultation |
| MedXpertQA | 2,450 | Core | specialist_consultation | Medical knowledge Q&A across body systems |
| PhysioNet | 10 | Supplementary | pre_consultation_data | Lab results, vital signs, diagnoses lookup |
| ProdMedBench | 1,000 | Supplementary | differential_diagnosis | Chinese MCQs with CoT reasoning |

---

## Scripts Created

1. **create_consultation_paradigm.ps1** - Processes MedAgentBench and PhysioNet
2. **process_large_datasets.ps1** - Processes MedXpertQA (2,450 tasks) and ProdMedBench (1,000 tasks)

---

## Execution Summary

```
[✓] MedAgentBench: 8 tasks processed
[✓] MedXpertQA: 2,450 tasks processed (with progress indicators)
[✓] PhysioNet: 10 tasks processed
[✓] ProdMedBench: 1,000 tasks processed (with progress indicators)
[✓] Universal Template: Created
```

---

## Technical Notes

- All files use UTF-8 encoding
- PowerShell scripts use .NET StreamReader for proper UTF-8 handling
- Large datasets (MedXpertQA, ProdMedBench) use -Compress to reduce file size
- Progress indicators show processing status every 250-500 tasks

---

## Next Steps

The consultation paradigm files are ready for use in tau2-bench evaluations. Each file can be loaded independently or referenced through the universal template.

To use the consultation paradigm:
1. Load the appropriate consultation_paradigm.json file
2. Filter by task_type or consultation_scenario as needed
3. Use the question/answer pairs for doctor-patient dialogue evaluation
