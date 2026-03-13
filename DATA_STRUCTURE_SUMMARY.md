# Tau2-Bench Clinical Data Structure Summary

## 🎯 Unified Directory Structure

All clinical consultation datasets are now stored in **one location**:
```
data/tau2/domains/clinical/
```

## 📊 Current Inventory

### MedXpertQA Datasets (5 departments)
| Domain | Tasks | Type |
|---|---|---|
| cardiology | 758 | Simulated multi-turn |
| neurology | 741 | Simulated multi-turn |
| gastroenterology | 475 | Simulated multi-turn |
| endocrinology | 176 | Simulated multi-turn |
| nephrology | 300 | Simulated multi-turn |
| **Total** | **2,450** | |

### Chinese MedDialog Datasets (6 departments)
| Domain | Tasks | Type |
|---|---|---|
| chinese_internal_medicine | 500 | Real Q&A |
| chinese_surgery | 500 | Real Q&A |
| chinese_obstetrics_gynecology | 500 | Real Q&A |
| chinese_pediatrics | 500 | Real Q&A |
| chinese_oncology | 500 | Real Q&A |
| chinese_andrology | 500 | Real Q&A |
| **Total** | **3,000** | |

### ThReadMed-QA Dataset (待下载)
| Domain | Tasks | Type |
|---|---|---|
| threadmed_qa | 2,437 | Real multi-turn |

## 🔑 Key Insights

### Dataset Comparison
| Aspect | MedXpertQA | Chinese MedDialog | ThReadMed-QA |
|---|---|---|---|
| **Source** | Exam questions | haodf.com | Reddit r/AskDocs |
| **Authenticity** | Simulated | Real | Real |
| **Dialogue** | Multi-turn | Single-turn | Multi-turn |
| **Language** | Chinese | Chinese | English |
| **Quality** | High (exam) | High (real) | High (verified) |

### Strengths by Use Case

**MedXpertQA** - Best for:
- Multi-turn dialogue evaluation
- Clinical reasoning testing
- Structured clinical scenarios

**Chinese MedDialog** - Best for:
- Real patient question analysis
- Chinese medical knowledge assessment
- Large-scale training data (792K+ available)

**ThReadMed-QA** - Best for:
- Authentic multi-turn consultation
- Real-world patient behavior
- Error propagation analysis
- Cross-turn consistency measurement

## 📈 Total Tasks

- **MedXpertQA**: 2,450 tasks
- **Chinese MedDialog**: 3,000 tasks
- **ThReadMed-QA**: 2,437 conversations (pending download)
- **Grand Total**: 7,887 tasks

## 🚀 Quick Start

### List all domains
```bash
ls data/tau2/domains/clinical/
```

### Run evaluation
```bash
# MedXpertQA (simulated multi-turn)
python run_clinical_benchmark.py --domain cardiology

# Chinese MedDialog (real Q&A)
python run_clinical_benchmark.py --domain chinese_internal_medicine

# All clinical domains
python run_clinical_benchmark.py --all
```

## 📝 File Structure Standard

Each domain follows this structure:
```
<domain>/
├── tasks.json           # Tau2-bench format tasks
├── split_tasks.json     # Train/val/test split
├── db.json              # Patient database (optional)
└── policy.md            # Clinical policy (optional)
```

## 🔗 Documentation Links

- [Clinical Domains README](data/tau2/domains/clinical/README.md)
- [CLINICAL_BENCHMARK_GUIDE.md](CLINICAL_BENCHMARK_GUIDE.md)
- [Chinese MedDialog Summary](CHINESE_MEDDIALOG_CONVERSION_SUMMARY.md)
- [ThReadMed-QA Summary](THREADMED_QA_CONVERSION_SUMMARY.md)

---

**Last Updated**: 2025-03-13  
**Status**: Directory structure unified, 7,887 tasks across 12 domains
