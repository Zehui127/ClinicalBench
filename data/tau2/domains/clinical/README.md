# Clinical Domains Dataset Structure

## 📊 Overview

All clinical consultation datasets are stored under `data/tau2/domains/clinical/` for unified access and evaluation.

## 🗂️ Current Domain Structure

```
data/tau2/domains/clinical/
├── cardiology/                      # MedXpertQA (心脏科) - 758 tasks
├── neurology/                       # MedXpertQA (神经科) - 741 tasks
├── gastroenterology/                # MedXpertQA (胃肠科) - 475 tasks
├── endocrinology/                   # MedXpertQA (内分泌科) - 176 tasks
├── nephrology/                      # MedXpertQA (肾病科) - 300 tasks
│
├── chinese_internal_medicine/       # Chinese MedDialog (内科) - 500 tasks
├── chinese_surgery/                  # Chinese MedDialog (外科) - 500 tasks
├── chinese_obstetrics_gynecology/   # Chinese MedDialog (妇产科) - 500 tasks
├── chinese_pediatrics/               # Chinese MedDialog (儿科) - 500 tasks
├── chinese_oncology/                # Chinese MedDialog (肿瘤科) - 500 tasks
├── chinese_andrology/               # Chinese MedDialog (男科) - 500 tasks
│
└── threadmed_qa/                    # ThReadMed-QA (Real Multi-turn) - 2,437 conv (待下载)
```

## 📈 Dataset Comparison

| Domain | Dataset | Type | Tasks | Source |
|---|---|---|---|---|
| **cardiology** | MedXpertQA | Simulated MCQ → Dialogue | 758 | Exam questions |
| **neurology** | MedXpertQA | Simulated MCQ → Dialogue | 741 | Exam questions |
| **gastroenterology** | MedXpertQA | Simulated MCQ → Dialogue | 475 | Exam questions |
| **endocrinology** | MedXpertQA | Simulated MCQ → Dialogue | 176 | Exam questions |
| **nephrology** | MedXpertQA | Simulated MCQ → Dialogue | 300 | Exam questions |
| **chinese_internal_medicine** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **chinese_surgery** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **chinese_obstetrics_gynecology** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **chinese_pediatrics** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **chinese_oncology** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **chinese_andrology** | Chinese MedDialog | Real Q&A | 500 | haodf.com |
| **threadmed_qa** | ThReadMed-QA | Real Multi-turn | 2,437 | Reddit r/AskDocs |

## 🎯 Total Statistics

### By Dataset Type
- **MedXpertQA**: 2,450 tasks (simulated multi-turn dialogue)
- **Chinese MedDialog**: 3,000 tasks (real single-turn Q&A)
- **ThReadMed-QA**: 2,437 conversations (real multi-turn dialogue) - 待下载

### By Data Authenticity
- **Real Data**: 5,437 tasks (Chinese MedDialog + ThReadMed-QA)
- **Simulated Data**: 2,450 tasks (MedXpertQA from MCQ)

### By Turn Structure
- **Multi-turn**: 4,887 tasks (MedXpertQA + ThReadMed-QA)
- **Single-turn**: 3,000 tasks (Chinese MedDialog)

## 📁 Standard File Structure

Each domain directory should contain:

```
<domain_name>/
├── tasks.json           # All tasks in tau2-bench format
├── split_tasks.json     # Train/val/test split IDs
├── db.json              # (Optional) Patient database
└── policy.md            # (Optional) Clinical policy document
```

## 🚀 Usage

### List all clinical domains
```bash
ls data/tau2/domains/clinical/
```

### Run evaluation on a specific domain
```bash
python run_clinical_benchmark.py --domain cardiology --max-tasks 10
python run_clinical_benchmark.py --domain chinese_internal_medicine --max-tasks 10
```

### Count tasks across all domains
```bash
find data/tau2/domains/clinical -name "tasks.json" -exec sh -c 'echo "$(dirname {}): $(python -c "import json; print(len(json.load(open(\"{}\"))))" 2>/dev/null || echo "0") tasks"' \;
```

## 🔄 Naming Conventions

### Dataset Source Prefixes
- No prefix = MedXpertQA (English exam questions)
- `chinese_` = Chinese MedDialog (haodf.com real Q&A)
- No prefix but different name = Other datasets

### Department Suffixes
- English department names (cardiology, neurology, etc.)
- Chinese department names (内科, 外科, etc.) use English prefix

## 📋 Data Quality Notes

### MedXpertQA
- ✅ Multi-turn dialogue structure
- ✅ Clinical accuracy from exam questions
- ⚠️ Simulated conversations (not real patients)
- ✅ 5 departments covered

### Chinese MedDialog
- ✅ Real patient questions and doctor responses
- ⚠️ Single-turn Q&A (not multi-turn)
- ✅ 6 departments covered
- ✅ Large scale (792,099 total Q&A pairs available)

### ThReadMed-QA (Pending Download)
- ✅ Real multi-turn patient-physician dialogue
- ✅ Verified physician responses
- ✅ 2,437 fully-answered conversation threads
- ✅ Up to 9 turns per conversation
- ✅ Ground truth for evaluation

## 🔗 Related Documentation

- [CLINICAL_BENCHMARK_GUIDE.md](../../CLINICAL_BENCHMARK_GUIDE.md) - How to run evaluations
- [CHINESE_MEDDIALOG_CONVERSION_SUMMARY.md](../../CHINESE_MEDDIALOG_CONVERSION_SUMMARY.md) - Chinese MedDialog details
- [THREADMED_QA_CONVERSION_SUMMARY.md](../../THREADMED_QA_CONVERSION_SUMMARY.md) - ThReadMed-QA details

## 📅 Last Updated

2025-03-13 - Unified directory structure, moved Chinese MedDialog to clinical domains
