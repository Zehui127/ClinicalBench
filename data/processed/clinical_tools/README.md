# Clinical Consultation Agent Benchmark - Tools Overview

## Quick Reference

| Tool | Purpose | Required Parameters | Call Timing |
|------|---------|---------------------|-------------|
| find_patient_basic_info | Get demographics | patient_id | FIRST - at consultation start |
| get_medical_history_key | Get allergies/medications | patient_id, history_type | Before any treatment |
| ask_symptom_details | Systematic symptom assessment | patient_id, symptom_category, question_focus | After demographics |
| retrieve_medication_details | Get drug safety info | medication_name, info_type | Before prescribing |
| assess_risk_level | Triage and urgency | patient_id, symptoms | After initial presentation |
| prescribe_medication_safe | Safe prescription | patient_id, medication_name, dosage, duration, route | ONLY after safety checks |
| retrieve_clinical_guideline | Evidence-based guidance | condition, specialty, guideline_aspect | When uncertain |
| record_diagnosis_icd10 | Document diagnosis | patient_id, diagnosis_name, icd10_code, diagnosis_type | After assessment |
| transfer_to_specialist | Specialist referral | patient_id, specialty, urgency, referral_reason | When case complexity exceeds scope |
| generate_follow_up_plan | Post-visit planning | patient_id, diagnosis, follow_up_type, timeframe_days | LAST - at consultation end |

## Workflow Sequence

```
1. find_patient_basic_info (MUST BE FIRST)
   ↓
2. assess_risk_level (triage)
   ↓
3. get_medical_history_key (safety check)
   ↓
4. ask_symptom_details (assessment)
   ↓
5. retrieve_clinical_guideline (if needed)
   ↓
6. retrieve_medication_details (before prescribing)
   ↓
7. prescribe_medication_safe (only after safety checks)
   ↓
8. record_diagnosis_icd10 (document)
   ↓
9. transfer_to_specialist (if needed)
   ↓
10. generate_follow_up_plan (MUST BE LAST)
```

## Critical Safety Rules

1. **ALWAYS** check allergies via `get_medical_history_key(history_type="allergies")` before prescribing
2. **NEVER** prescribe without calling `retrieve_medication_details` for contraindications
3. **ALWAYS** call `assess_risk_level` early to identify emergencies
4. **MUST** complete `find_patient_basic_info` before any clinical decisions
5. **ONLY** call `prescribe_medication_safe` after prior safety checks pass

## Evaluation Scoring

- **Invocation Timing (0-3 pts):** When tool is called in workflow
- **Parameter Accuracy (0-3 pts):** Correctness of input parameters
- **Contextual Integration (0-4 pts):** How output is used in decisions

**Maximum: 10 points per tool × 10 tools = 100 points total**

## File Structure

```
clinical_tools/
├── tools.json                    # OpenAI Function Call schema (deployable)
├── TOOL_EVALUATION_FRAMEWORK.md  # Detailed assessment criteria
└── README.md                     # This quick reference
```

## Usage Example

```json
{
  "patient_query": "45-year-old female with headache and elevated BP 160/100",
  "expected_tool_sequence": [
    "find_patient_basic_info",
    "assess_risk_level",
    "get_medical_history_key",
    "ask_symptom_details",
    "retrieve_clinical_guideline",
    "prescribe_medication_safe",
    "record_diagnosis_icd10",
    "generate_follow_up_plan"
  ]
}
```

## Department Specializations

### Nephrology
- Focus on: medication nephrotoxicity, renal dosing, CKD staging
- Key tools: get_medical_history_key, retrieve_medication_details

### Cardiology
- Focus on: symptom characterization, risk assessment, guideline adherence
- Key tools: ask_symptom_details, assess_risk_level, retrieve_clinical_guideline

### Gastroenterology
- Focus on: medication history (NSAIDs), detailed GI symptoms, specialist referral
- Key tools: get_medical_history_key, ask_symptom_details, transfer_to_specialist
