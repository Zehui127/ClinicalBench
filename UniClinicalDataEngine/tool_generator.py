"""Default clinical tool specifications and code generation."""

from typing import Dict, List

from UniClinicalDataEngine.models import ClinicalToolSpec


def get_default_clinical_tools() -> List[ClinicalToolSpec]:
    """Return default clinical tool specifications for a clinical domain.

    These tools follow the tau2-bench ToolKitBase pattern:
    - READ tools query data without modifying state
    - WRITE tools modify patient state or place orders
    - GENERIC tools handle transfers and utilities
    """
    return [
        ClinicalToolSpec(
            name="find_patient_info",
            description=(
                "Look up patient information by patient ID. "
                "Returns demographics, medical history, allergies, and current medications."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
            },
            return_type="dict",
            tool_type="read",
        ),
        ClinicalToolSpec(
            name="get_medical_history",
            description=(
                "Retrieve the full medical history for a patient, "
                "including past diagnoses, surgeries, and hospitalizations."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
            },
            return_type="dict",
            tool_type="read",
        ),
        ClinicalToolSpec(
            name="prescribe_medication",
            description=(
                "Prescribe a medication for a patient. "
                "Records the medication name, dosage, frequency, and duration."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
                "medication_name": {
                    "type": "str",
                    "description": "Name of the medication to prescribe",
                },
                "dosage": {
                    "type": "str",
                    "description": "Dosage amount and unit (e.g., '500mg')",
                },
                "frequency": {
                    "type": "str",
                    "description": "How often to take (e.g., 'twice daily')",
                },
                "duration": {
                    "type": "str",
                    "description": "Duration of prescription (e.g., '7 days')",
                },
            },
            return_type="str",
            tool_type="write",
        ),
        ClinicalToolSpec(
            name="order_lab_test",
            description=(
                "Order a laboratory test for a patient. "
                "Specifies the test type and any special instructions."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
                "test_name": {
                    "type": "str",
                    "description": "Name of the lab test to order (e.g., 'CBC', 'BMP')",
                },
                "priority": {
                    "type": "str",
                    "description": "Priority level: routine, urgent, stat",
                },
                "notes": {
                    "type": "str",
                    "description": "Additional instructions or clinical notes",
                },
            },
            return_type="str",
            tool_type="write",
        ),
        ClinicalToolSpec(
            name="record_diagnosis",
            description=(
                "Record a diagnosis for a patient. "
                "Can record primary or differential diagnoses with ICD codes."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
                "diagnosis": {
                    "type": "str",
                    "description": "The diagnosis description",
                },
                "icd_code": {
                    "type": "str",
                    "description": "ICD-10 code for the diagnosis (optional)",
                },
                "diagnosis_type": {
                    "type": "str",
                    "description": "Type: primary, differential, or rule_out",
                },
            },
            return_type="str",
            tool_type="write",
        ),
        ClinicalToolSpec(
            name="transfer_to_specialist",
            description=(
                "Transfer the patient to a specialist or another department. "
                "Only transfer if the case requires specialized care beyond current scope, "
                "or if the patient explicitly requests a specialist."
            ),
            parameters={
                "patient_id": {
                    "type": "str",
                    "description": "The unique patient identifier",
                },
                "specialty": {
                    "type": "str",
                    "description": "The specialty to transfer to (e.g., 'cardiology')",
                },
                "summary": {
                    "type": "str",
                    "description": "Clinical summary and reason for transfer",
                },
            },
            return_type="str",
            tool_type="generic",
        ),
    ]


def generate_tool_definitions(
    tools: List[ClinicalToolSpec],
) -> List[Dict]:
    """Convert ClinicalToolSpecs into JSON-serializable tool definitions.

    These definitions can be included in the domain output for reference
    and are compatible with OpenAI function-calling schema.

    Args:
        tools: List of ClinicalToolSpec objects.

    Returns:
        List of tool definition dicts.
    """
    definitions = []
    for tool in tools:
        params_properties = {}
        required = []
        for param_name, param_info in tool.parameters.items():
            params_properties[param_name] = {
                "type": "string",
                "description": param_info["description"],
            }
            required.append(param_name)

        definitions.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": params_properties,
                        "required": required,
                    },
                },
                "tool_type": tool.tool_type,
            }
        )
    return definitions
