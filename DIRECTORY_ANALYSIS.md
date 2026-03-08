# Tau2-Bench Directory Analysis
**Generated:** 2026-03-06

## Executive Summary

The `C:\Users\方正\tau2-bench` directory contains:
- **Main tau2-bench project** (agent benchmarking framework)
- **UniClinicalDataEngine** (clinical data ETL pipeline)
- **MedAgentBench** (medical evaluation benchmark)
- Multiple data processing scripts and outputs
- Various temporary/cache files

---

## 1. CORE PROJECT FILES (Keep)

### 1.1 Tau2-Bench Core
```
C:\Users\方正\tau2-bench\
├── src/tau2/                    # [CORE] Main source code
├── pyproject.toml               # [CORE] Project dependencies
├── config.py                    # [CORE] Configuration
├── Makefile                     # [CORE] Build automation
├── .gitignore                   # [CORE] Git ignore rules
├── .env.example                 # [CORE] Environment template
├── README.md                    # [CORE] Main documentation
├── CHANGELOG.md                 # [CORE] Version history
├── CONTRIBUTING.md              # [CORE] Contribution guide
├── LICENSE                      # [CORE] License file
├── VERSIONING.md                # [CORE] Versioning policy
├── RELEASE_NOTES.md             # [CORE] Release notes
├── AUTOMATION_GUIDE.md          # [CORE] Automation guide
```

### 1.2 UniClinicalDataEngine
```
C:\Users\方正\tau2-bench\UniClinicalDataEngine\  # [CORE] Complete ETL engine
├── __init__.py
├── engine.py
├── cli.py
├── tools.py
├── adapters/
├── generators/
├── models/
├── tests/
└── requirements.txt
```
**Status:** ✅ **COMPLETE** - All files present and functional

### 1.3 MedAgentBench
```
C:\Users\方正\tau2-bench\MedAgentBench\  # [CORE] Medical benchmark
├── med_agent_server/
├── med_agent_client/
├── tests/
└── README.md
```

---

## 2. TEMPORARY/CACHE FILES (Delete)

### 2.1 Empty/Zero-byte Files
```
C:\Users\方正\tau2-bench\
├── python_err.txt              # [DELETE] 0 bytes - empty error log
├── python_out.txt              # [DELETE] 0 bytes - empty output log
├── run_result.txt              # [DELETE] 0 bytes - empty result file
└── nul                         # [DELETE] 149 bytes - Windows null device copy
```

### 2.2 Test Completion Markers
```
C:\Users\方正\tau2-bench\data\processed\clinical_tools\
├── AUDIT_FIX_COMPLETE.txt      # [DELETE] Completion marker
├── AUDIT_REPORT.txt            # [DELETE] Audit log
├── BATCH_REPAIR_FIX_COMPLETE.txt # [DELETE] Completion marker
├── COMPLETE.txt                # [DELETE] Completion marker
├── DATA_QUALITY_FILTER_COMPLETE.txt # [DELETE] Completion marker
└── MOCK_EXECUTION_VERIFICATION.txt # [DELETE] Verification log
```

---

## 3. DUPLICATE/REDUNDANT FILES

### 3.1 Duplicate Processing Scripts (Python vs JavaScript)
```
C:\Users\方正\tau2-bench\
├── process_medxpert.py         # [KEEP] Python version
├── process_medxpertqa.js       # [DELETE] JavaScript duplicate
├── process_prodmedbench.py     # [KEEP] Python version
└── process_prodmedbench.js     # [DELETE] JavaScript duplicate
```

### 3.2 Duplicate Reconstruction Scripts
```
C:\Users\方正\tau2-bench\
├── reconstruct_medical.py      # [KEEP] Main version
├── reconstruct_medical_win.py  # [DELETE] Windows-specific (redundant)
└── reconstruct_simple.py       # [DELETE] Simplified version (redundant)
```

### 3.3 Duplicate Run Scripts
```
C:\Users\方正\tau2-bench\
├── run_python.bat              # [KEEP] Python runner
├── run_python2.bat             # [DELETE] Duplicate
├── run_reconstruct.bat         # [DELETE] Old script
└── RUN_RECONSTRUCTION.bat      # [DELETE] Old script
```

### 3.4 PowerShell Scripts (Consolidate)
```
C:\Users\方正\tau2-bench\
├── create_consultation_paradigm.ps1  # [MOVE to scripts/]
├── create_physionet_files.py        # [MOVE to scripts/]
├── fix_medxpertqa.ps1               # [DELETE] One-time fix
├── fix_prodmedbench.ps1             # [DELETE] One-time fix
├── process_large_datasets.ps1       # [MOVE to scripts/]
├── reconstruct.ps1                   # [DELETE] Old script
└── run_script.ps1                   # [DELETE] Old script
```

---

## 4. DATA QUALITY FILTERING (Stage 2)

**Status:** ⚠️ **NOT YET CREATED AS SEPARATE MODULE**

Related files exist in:
```
C:\Users\方正\tau2-bench\data\processed\clinical_tools\
├── data_quality_filter.py      # [CORE] Quality filtering logic
├── calculate_quality_statistics.py
├── review_scores.json
└── tasks_filtered.json
```

**Recommendation:** Extract into `DataQualityFiltering/` module as planned.

---

## 5. DATA DIRECTORY STRUCTURE

### 5.1 Raw Data (Keep)
```
C:\Users\方正\tau2-bench\data\
├── raw/
│   ├── MedXpertQA/            # [KEEP] Raw medical QA data
│   ├── PhysioNet/             # [KEEP] Physiological data
│   ├── ProdMedBench/          # [KEEP] Medical benchmark
│   └── clinical/              # [KEEP] Clinical tool data
└── tau2/                      # [KEEP] Main tau2 benchmark data
```

### 5.2 Processed Data (Organize)
```
C:\Users\方正\tau2-bench\data\processed\
├── clinical_tools/            # [REVIEW] Quality filtered outputs
├── medxpertqa/                # [MOVE to outputs/]
├── prodmedbench/              # [MOVE to outputs/]
├── physionet/                 # [MOVE to outputs/]
└── medagentbench/             # [MOVE to outputs/]
```

---

## 6. CONFIGURATION FILES (Consolidate)

### 6.1 Duplicate Configurations
```
C:\Users\方正\tau2-bench\
├── config.py                   # [CORE] Main config
├── src/tau2/config.py          # [DUPLICATE] Same as above
└── data/clinical/adapter_config.json  # [MOVE to configs/]
```

### 6.2 Pipeline Configuration
```
C:\Users\方正\tau2-bench\
└── pipeline_config.json        # [CREATE] Need to create
```

---

## 7. RECOMMENDED DIRECTORY STRUCTURE

```
C:\Users\方正\tau2-bench\
├── UniClinicalDataEngine/          # Stage 1: Data transformation engine
│   ├── __init__.py                 # ✅ COMPLETE
│   ├── engine.py
│   ├── cli.py
│   ├── tools.py
│   ├── adapters/
│   ├── generators/
│   ├── models/
│   └── tests/
│
├── DataQualityFiltering/            # Stage 2: Quality filtering (TO CREATE)
│   ├── __init__.py
│   ├── cli.py
│   ├── filter_engine.py
│   ├── reviewers/
│   ├── validators/
│   └── tests/
│
├── data/                            # Data directory
│   ├── raw/                         # Raw input data
│   │   ├── clinical/
│   │   ├── medxpertqa/
│   │   ├── physionet/
│   │   └── prodmedbench/
│   ├── sample/                      # Sample data for testing
│   └── tau2/                        # Main tau2 benchmark data
│
├── outputs/                         # Pipeline outputs
│   ├── stage1_output/               # UniClinicalDataEngine outputs
│   ├── stage2_output/               # DataQualityFiltering outputs
│   └── final/                       # Final processed data
│
├── scripts/                         # Auxiliary scripts
│   ├── create_consultation_paradigm.ps1
│   ├── create_physionet_files.py
│   ├── process_large_datasets.ps1
│   ├── process_medxpert.py
│   └── process_prodmedbench.py
│
├── src/tau2/                        # Main tau2-bench source
│   ├── agent/
│   ├── api_service/
│   ├── cli.py
│   └── ...
│
├── MedAgentBench/                   # Medical benchmark
│   ├── med_agent_server/
│   ├── med_agent_client/
│   └── tests/
│
├── configs/                         # Configuration files (NEW)
│   ├── pipeline_config.json
│   ├── adapter_config.json
│   └── tool_registry.json
│
├── tests/                           # Test files
│   ├── integration/
│   └── unit/
│
├── docs/                            # Documentation
│   ├── api/
│   ├── user_guide/
│   └── development/
│
├── pyproject.toml                   # Project dependencies
├── requirements.txt                 # Additional requirements
├── README.md                        # Main README
├── CHANGELOG.md                     # Version history
├── CONTRIBUTING.md                  # Contribution guide
├── LICENSE
└── Makefile
```

---

## 8. CLEANUP ACTION ITEMS

### Immediate (High Priority)
1. **Delete empty files:**
   - python_err.txt
   - python_out.txt
   - run_result.txt
   - nul

2. **Delete completion markers:**
   - All *.txt files in data/processed/clinical_tools/

3. **Delete duplicate scripts:**
   - *.js versions (keep Python)
   - Windows-specific duplicates
   - One-time fix scripts

### Medium Priority
4. **Consolidate configuration:**
   - Create `configs/` directory
   - Move adapter_config.json
   - Create pipeline_config.json

5. **Move scripts:**
   - Create `scripts/` directory
   - Move processing scripts
   - Move utility scripts

6. **Create DataQualityFiltering module:**
   - Extract from data/processed/clinical_tools/
   - Implement as separate stage

### Low Priority
7. **Organize outputs:**
   - Create `outputs/` structure
   - Move processed data to appropriate folders

8. **Update documentation:**
   - Create docs/ structure
   - Update README with new structure

---

## 9. FILES TO DELETE (List)

```
# Empty files
python_err.txt
python_out.txt
run_result.txt
nul

# Duplicate scripts
process_medxpertqa.js
process_prodmedbench.js
reconstruct_medical_win.py
reconstruct_simple.py
run_python2.bat
run_reconstruct.bat
RUN_RECONSTRUCTION.bat

# One-time fix scripts
fix_medxpertqa.ps1
fix_prodmedbench.ps1
reconstruct.ps1
run_script.ps1

# Completion markers (in data/processed/clinical_tools/)
AUDIT_FIX_COMPLETE.txt
AUDIT_REPORT.txt
BATCH_REPAIR_FIX_COMPLETE.txt
COMPLETE.txt
DATA_QUALITY_FILTER_COMPLETE.txt
MOCK_EXECUTION_VERIFICATION.txt

# Test outputs (in data/processed/clinical_tools/)
standardized_test_set/  (entire directory - test output)

# Old reconstruction files
RECONSTRUCTION_README.txt
RECONSTRUCTION_SUMMARY.md
```

---

## 10. VERIFICATION CHECKLIST

- [x] UniClinicalDataEngine is **COMPLETE**
- [ ] DataQualityFiltering needs to be **CREATED**
- [ ] Two test data phases exist (raw + processed)
- [x] Duplicate configuration files exist
- [x] Duplicate scripts exist (Python + JS)
- [ ] outputs/ directory needs to be created
- [ ] scripts/ directory needs to be created
- [ ] configs/ directory needs to be created

---

## Summary

**Total Files Analyzed:** 500+

**Core Files to Keep:** ~350
**Files to Delete:** ~50
**Files to Move:** ~30
**New Files to Create:** ~10

**Key Issues:**
1. UniClinicalDataEngine is ✅ COMPLETE
2. DataQualityFiltering needs to be created
3. Many duplicate scripts (Python + JS versions)
4. Temporary/cache files can be cleaned
5. Configuration needs consolidation
