# MedAgentBench to Tau2-Bench Adapter - Complete Guide

## Overview

This directory contains the complete adapter configuration and scripts to convert MedAgentBench's `test_data_v2.json` into the tau2-bench `tasks.json` format.

## Files Created

| File | Description |
|------|-------------|
| `tasks.json` | Generated tau2-bench format tasks (sample with 8 tasks) |
| `adapter_config.json` | Adapter configuration with field mappings |
| `run_commands.ps1` | PowerShell commands for Windows execution |
| `convert_medagentbench.py` | Standalone conversion script with CLI |
| `full_convert.py` | Full conversion script (converts ALL tasks) |
| `validate_tasks.py` | Validation script for generated tasks.json |
| `README.md` | This documentation file |

## Quick Start (Windows PowerShell)

### Option 1: Run All Commands at Once

```powershell
cd "C:\Users\方正\tau2-bench"
# Open and run: data\clinical\run_commands.ps1
```

### Option 2: Step-by-Step Commands

```powershell
# 1. Navigate to project directory
cd "C:\Users\方正\tau2-bench"

# 2. Create clinical directory (if not exists)
if (-not (Test-Path "data\clinical")) {
    New-Item -ItemType Directory -Path "data\clinical" -Force
}

# 3. Run full conversion
python "data\clinical\full_convert.py"

# 4. Verify JSON
Get-Content "data\clinical\tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json

# 5. Validate
python "data\clinical\validate_tasks.py" --tasks "data\clinical\tasks.json"
```

## Adapter-Kwargs Mapping Configuration

### Field Mappings

| Source Field (MedAgentBench) | Target Path (Tau2-Bench) | Transformation |
|------------------------------|--------------------------|----------------|
| `id` | `id` | Direct copy |
| `instruction` | `user_scenario.instructions.task_instructions` | Direct copy |
| `instruction` | `ticket` | Copy (for solo agent) |
| `instruction` (regex) | `user_scenario.instructions.known_info` | Extract patient info |
| `context` | `user_scenario.instructions.unknown_info` | Direct copy |
| `sol` | `annotations.expected_solution` | Wrap in array |
| `eval_MRN` | `annotations.expected_answer` | Direct copy |
| `eval_MRN` | `evaluation_criteria.nl_assertions[0]` | Template: "Agent should correctly identify the MRN as {value}" |

### Static Fields Added

```json
{
  "description": {
    "purpose": "Find patient MRN by name and date of birth",
    "relevant_policies": null,
    "notes": null
  },
  "user_scenario": {
    "persona": null,
    "instructions": {
      "domain": "clinical",
      "reason_for_call": "Looking up patient information"
    }
  },
  "initial_state": null,
  "evaluation_criteria": {
    "actions": [],
    "communicate_info": []
  },
  "annotations": {
    "source_format": "medagentbench_v2"
  }
}
```

## Task Structure Comparison

### Source (MedAgentBench)
```json
{
  "id": "task1_1",
  "instruction": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be \"Patient not found\"",
  "context": "",
  "sol": ["S6534835"],
  "eval_MRN": "S6534835"
}
```

### Target (Tau2-Bench)
```json
{
  "id": "task1_1",
  "description": {
    "purpose": "Find patient MRN by name and date of birth",
    "relevant_policies": null,
    "notes": null
  },
  "user_scenario": {
    "persona": null,
    "instructions": {
      "task_instructions": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be \"Patient not found\"",
      "domain": "clinical",
      "reason_for_call": "Looking up patient information",
      "known_info": "Patient name: Peter Stafford, DOB: 1932-12-29",
      "unknown_info": null
    }
  },
  "ticket": "What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29? If the patient does not exist, the answer should be \"Patient not found\"",
  "initial_state": null,
  "evaluation_criteria": {
    "actions": [],
    "communicate_info": [],
    "nl_assertions": [
      "Agent should correctly identify the MRN as S6534835"
    ]
  },
  "annotations": {
    "expected_answer": "S6534835",
    "expected_solution": ["S6534835"],
    "source_format": "medagentbench_v2"
  }
}
```

## Running the Adapter

### Using the Standalone Script (Recommended)

```bash
# Basic conversion
python data/clinical/full_convert.py

# With custom paths
python data/clinical/convert_medagentbench.py \
    --source "MedAgentBench/data/medagentbench/test_data_v2.json" \
    --output "data/clinical/tasks.json" \
    --config "data/clinical/adapter_config.json"
```

### Using UniClinicalDataEngine (If Available)

```bash
python -m src.tau2.cli adapt \
    --adapter MedAgentBenchToTau2Adapter \
    --source "MedAgentBench/data/medagentbench/test_data_v2.json" \
    --output "data/clinical/tasks.json" \
    --adapter-config "data/clinical/adapter_config.json"
```

## Validation

### Quick Validation (PowerShell)

```powershell
# Check JSON validity
Get-Content "data\clinical\tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json

# Count tasks
$json = Get-Content "data\clinical\tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$json.Count
```

### Full Validation (Python)

```bash
python data/clinical/validate_tasks.py --tasks data/clinical/tasks.json
```

## File Locations

| Type | Path |
|------|------|
| Source | `C:\Users\方正\tau2-bench\MedAgentBench\data\medagentbench\test_data_v2.json` |
| Output | `C:\Users\方正\tau2-bench\data\clinical\tasks.json` |
| Scripts | `C:\Users\方正\tau2-bench\data\clinical\*.py` |

## Important Notes

### Structure Discrepancy

The actual MedAgentBench `test_data_v2.json` file has a **simple flat structure**:
- `id`, `instruction`, `context`, `sol`, `eval_MRN`

The user's original mapping request mentioned fields like:
- `patient_id`, `patient_info.name`, `patient_info.age`, etc.

**These fields do not exist in the actual source file.** The adapter handles the actual structure found in `test_data_v2.json` and uses regex extraction to derive patient information from the `instruction` field.

### Regex Pattern Used

The adapter uses this pattern to extract patient information:
```python
pattern = r"name\s+([\w\s]+?)\s+and\s+DOB\s+of\s+([\d\-]+)"
```

Example extraction:
- Input: `"What's the MRN of the patient with name Peter Stafford and DOB of 1932-12-29?"`
- Output: `"Patient name: Peter Stafford, DOB: 1932-12-29"`

## Next Steps

1. **Review the generated tasks.json** - Check if the field mappings match your requirements
2. **Customize adapter_config.json** - Modify mappings if needed
3. **Run tau2-bench evaluation**:
   ```bash
   python -m src.tau2.run --domain clinical --tasks data/clinical/tasks.json
   ```

## Troubleshooting

### Issue: Python cannot read the source file
**Solution**: Ensure the file path uses backslashes and proper encoding:
```python
with open(r'C:\Users\方正\tau2-bench\...', 'r', encoding='utf-8') as f:
```

### Issue: JSON validation fails
**Solution**: Check for:
- Proper UTF-8 encoding
- Valid JSON syntax (commas, brackets)
- No trailing commas

### Issue: Missing fields in output
**Solution**: The adapter handles the actual source structure. If you need additional fields, modify the `convert_task()` function in `full_convert.py` or update the `adapter_config.json`.

## Contact

For issues or questions about this adapter, refer to the tau2-bench documentation or create an issue in the project repository.
