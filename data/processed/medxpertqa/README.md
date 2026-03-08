# MedXpertQA Dataset Processor

One-click processing scripts to convert MedXpertQA dataset from GitHub into tau2-bench standard format.

## Quick Start

### Option 1: One-Click (Recommended)
Simply double-click the batch file:
```
RUN_PROCESSING.bat
```

### Option 2: PowerShell Command
```powershell
cd "C:\Users\方正\tau2-bench\data\processed\medxpertqa"
.\medxpertqa_full_process.ps1
```

### Option 3: Manual Git Clone (if script fails)
```powershell
# Clone repository manually
git clone https://github.com/TsinghuaC3I/MedXpertQA.git "C:\Users\方正\tau2-bench\data\raw\MedXpertQA"

# Then run the processing script
.\medxpertqa_full_process.ps1
```

---

## Files Overview

| File | Description |
|------|-------------|
| `RUN_PROCESSING.bat` | One-click launcher (Windows batch file) |
| `medxpertqa_full_process.ps1` | Main processing script (PowerShell) |
| `medxpertqa_validate.py` | Validation script (Python) |

---

## Output Structure

After successful processing, the following files will be created:

```
C:\Users\方正\tau2-bench\data\processed\medxpertqa\
├── tasks.json                           # Pure questions (no answers)
├── db.json                              # QA pair database
├── policy.md                            # Clinical policy/guidelines
├── process_log_medxpertqa.txt           # Processing log
├── MedXpertQA_raw_backup.zip            # Backup of raw data
├── medxpertqa_full_process.ps1          # Processing script
├── medxpertqa_validate.py               # Validation script
├── RUN_PROCESSING.bat                   # One-click launcher
└── README.md                            # This file
```

---

## Configuration

To modify paths or processing options, edit the configuration section in `medxpertqa_full_process.ps1`:

```powershell
# Configuration Section
$Config = @{
    RepoUrl = "https://github.com/TsinghuaC3I/MedXpertQA.git"
    RepoPath = "C:\Users\方正\tau2-bench\data\raw\MedXpertQA"
    ProcessedOutput = "C:\Users\方正\tau2-bench\data\processed\medxpertqa"
    MaxRetries = 3
    CreateBackup = $true
    Verbose = $true
}
```

---

## Processing Steps

The script performs the following steps automatically:

### Step 1: Check Git Installation
- Verifies Git is installed and accessible
- Provides download link if not found

### Step 2: Clone Repository
- Clones MedXpertQA from GitHub
- Implements retry logic (3 attempts)
- Provides troubleshooting tips if failed

### Step 3: Analyze Dataset
- Scans repository for data files (JSON, CSV, TXT)
- Identifies file types and structure

### Step 4: Identify Core Data Files
- Searches for QA pair files
- Analyzes field names and structure
- Detects question/answer columns

### Step 5: Process Data
- Converts to tau2-bench standard format
- Generates unique task IDs (medxpertqa_001, 002, ...)
- Extracts domains and difficulty levels
- Preserves original question/answer wording

### Step 6: Save Processed Files
- `tasks.json`: Pure questions without answers
- `db.json`: Complete QA pair database
- `policy.md`: Clinical policy template

### Step 7: Create Backup
- Compresses raw repository data
- Saves as `MedXpertQA_raw_backup.zip`

### Step 8: Verify Files
- Validates JSON format
- Checks field completeness
- Verifies data consistency

---

## Validation

### Run Validation Script
```bash
python medxpertqa_validate.py --data-dir "C:\Users\方正\tau2-bench\data\processed\medxpertqa"
```

### With Verbose Output
```bash
python medxpertqa_validate.py --data-dir "C:\Users\方正\tau2-bench\data\processed\medxpertqa" -v
```

### Validation Checks
- ✓ JSON format validity
- ✓ Required fields presence
- ✓ No answers in tasks.json
- ✓ Data consistency between files
- ✓ Comparison with other tau2-bench datasets

---

## File Format Reference

### tasks.json Structure (Pure Questions)
```json
[
  {
    "id": "medxpertqa_001",
    "description": {
      "purpose": "Medical knowledge QA",
      "relevant_policies": null,
      "notes": "Domain: internal medicine, Difficulty: easy"
    },
    "user_scenario": {
      "persona": null,
      "instructions": {
        "task_instructions": "What is the first-line treatment for hypertension?",
        "domain": "clinical",
        "reason_for_call": "Medical consultation",
        "known_info": null,
        "unknown_info": null
      }
    },
    "ticket": "What is the first-line treatment for hypertension?",
    "initial_state": null,
    "evaluation_criteria": null,
    "annotations": null
  }
]
```

### db.json Structure (QA Database)
```json
{
  "qa_pairs": {
    "medxpertqa_001": {
      "question": "What is the first-line treatment for hypertension?",
      "answer": "The first-line treatment for hypertension typically includes...",
      "domain": "internal medicine",
      "difficulty": "easy",
      "task_id": "medxpertqa_001"
    },
    "medxpertqa_002": {
      ...
    }
  }
}
```

---

## Troubleshooting

### Git Clone Fails

**Error**: `fatal: unable to access 'https://github.com/...'`

**Solutions**:
1. Check internet connection
2. Verify Git is installed: `git --version`
3. Try cloning manually:
   ```powershell
   git clone https://github.com/TsinghuaC3I/MedXpertQA.git "C:\Users\方正\tau2-bench\data\raw\MedXpertQA"
   ```
4. Check firewall/proxy settings
5. Try using a VPN or different network

### No Data Files Found

**Error**: `No data files found in repository!`

**Solutions**:
1. The repository structure may have changed
2. Check the repository online: https://github.com/TsinghuaC3I/MedXpertQA
3. Manually locate the data files
4. Update the file detection logic in the script

### JSON Parse Errors

**Error**: `Invalid JSON format`

**Solutions**:
1. The data file format may be different than expected
2. Check the actual file structure
3. Modify the field detection logic in `Process-JsonFile` function

---

## Advanced Customization

### Changing Task ID Format

In `medxpertqa_full_process.ps1`, find and modify:
```powershell
$taskId = "medxpertqa_{0:D3}" -f $TaskIdRef.Value
```

Examples:
- `medxpertqa_{0:D4}` → medxpertqa_0001, medxpertqa_0002
- `mq_{0:D3}` → mq_001, mq_002
- `task_{0}` → task_1, task_2

### Adding Custom Field Mapping

In `Process-JsonFile` function, add more field detection:
```powershell
if ($propName -match "category|specialty|field") {
    $category = $prop.Value
}
```

### Filtering by Domain

Add filtering logic in `Process-JsonFile`:
```powershell
if ($domain -eq "internal_medicine") {
    # Only process internal medicine questions
}
```

---

## Comparison with Other Datasets

### Airline Dataset Structure
```
data/tau2/domains/airline/
├── tasks.json    (pure customer service scenarios)
├── db.json       (flights, reservations database)
└── workflows/    (automation scripts)
```

### Clinical Dataset Structure (MedAgentBench)
```
data/clinical/
├── tasks.json    (pure patient questions)
└── db.json       (patient records database)
```

### MedXpertQA Dataset Structure (This)
```
data/processed/medxpertqa/
├── tasks.json    (pure medical QA questions)
└── db.json       (medical knowledge database)
```

---

## Processing Log

All processing activities are logged to `process_log_medxpertqa.txt`:

```
[2025-03-02 17:00:00] [INFO] === MedXpertQA Processing Started ===
[2025-03-02 17:00:01] [SUCCESS] Git is installed: git version 2.x.x
[2025-03-02 17:00:05] [SUCCESS] Repository cloned successfully!
[2025-03-02 17:00:06] [INFO] Analyzing dataset structure...
...
```

---

## Support

For issues or questions:
1. Check the log file: `process_log_medxpertqa.txt`
2. Run validation: `python medxpertqa_validate.py -v`
3. Review this README's troubleshooting section
4. Check tau2-bench documentation

---

## Notes

- **Original Content Preservation**: The script preserves all original question and answer wording. Only format is adapted.
- **No Data Loss**: Raw data is backed up before processing.
- **Reproducible**: Same input always produces same output.
- **Extensible**: Easy to add support for additional datasets.

---

## Version History

- **v1.0** (2025-03-02): Initial release
  - Auto-clone from GitHub
  - JSON/CSV file support
  - Automatic field detection
  - Validation scripts
  - One-click processing
