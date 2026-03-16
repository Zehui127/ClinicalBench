# Clinical Science Benchmark Design

## Overview

This repository extends the tau2-bench framework with clinical consultation domains, enabling evaluation of AI agents in medical consultation scenarios across 5 clinical specialties.

## Supported Domains

### Standard tau2-bench Domains
- **airline** - Airline customer service
- **retail** - Retail customer support
- **telecom** - Telecommunications technical support
- **mock** - Testing/mock domain

### Clinical Domains (NEW)
- **clinical_cardiology** - Cardiovascular medicine (758 tasks)
- **clinical_endocrinology** - Hormonal/metabolic disorders (176 tasks)
- **clinical_gastroenterology** - Digestive system (475 tasks)
- **clinical_nephrology** - Kidney diseases (300 tasks)
- **clinical_neurology** - Nervous system (741 tasks)

**Total: 2,450 clinical consultation tasks**

## 1. Role Mapping

| Tau2 Role | Clinical Benchmark Role |
|-----------|------------------------|
| User      | Patient                |
| Agent     | Clinician              |

---

## 2. Task Definition Schema

Each task is defined as a JSON object with the following components:

- **Task Definition** (JSON): Describes the clinical scenario, patient context, and expected clinician actions.
- **Tool Definitions** (Markdown): Documents the tools available to the clinician agent.
- **Evaluation Criteria**: What the evaluator checks after the conversation, e.g.:
  - *Action check*: Drug B123 (Cocaine) is prescribed.
  - *Communication check*: Patient is informed they need rest.

### Example Tool

```python
def find_patient_info(name: str) -> Patient:
    """Look up patient record by name."""
    return Patient(year, sex, past_record, weight)
```

### Example Conversation

```
Patient:   My name is Zehui, I feel bad.
Clinician: Hello, sorry to hear that. Do you feel pain in your head?
Patient:   Yes.
Clinician: [calls find_patient_info("Zehui")]
```

### Evaluation

```
evaluator(conversation, criteria) -> reward: 0 / 1 / 2
```

- **0** = Failure (wrong or missing actions/communication)
- **1** = Partial success
- **2** = Full success

---

## 3. Complete End-to-End Pipeline

### Overview

The complete clinical benchmark pipeline consists of 5 stages that process raw medical dialogue data into final evaluation scores for AI agents.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE CLINICAL BENCHMARK PIPELINE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. Raw Medical Dialogue Data                                                 │
│     ↓                                                                       │
│  2. DataValidator (Stage 0) ✓ NEW                                           │
│     ├─ Raw data validation                                                 │
│     └─ Format checking                                                    │
│     ↓                                                                       │
│  3. UniClinicalDataEngine (Stage 1)                                       │
│     ├─ ETL: Extract → Transform → Load                                    │
│     └─ Generate: tasks.json, db.json, tools.json, policy.md               │
│     ↓                                                                       │
│  4. DataValidator (Stage 1.5) ✓ NEW                                       │
│     └─ Generated tasks validation                                         │
│     ↓                                                                       │
│  5. DataQualityFiltering (Stage 2)                                         │
│     ├─ Quality scoring (tool_count + content_length)                     │
│     └─ Filtering (threshold-based)                                        │
│     ↓                                                                       │
│  6. High-Quality Tasks                                                     │
│     ↓                                                                       │
│  7. Agent Simulation (Stage 3)                                             │
│     └─ AI doctors answer patient questions                                │
│     ↓                                                                       │
│  8. Clinical Evaluation (Stage 4) ✓ NEW                                    │
│     ├─ ClinicalAccuracyEvaluator (40%)                                    │
│     ├─ DialogueFluencyEvaluator (30%)                                     │
│     └─ SafetyEmpathyEvaluator (30%)                                       │
│     ↓                                                                       │
│  9. Final Scores & Analysis                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Stage 0: Raw Data Validation (NEW)

Validates raw input data before processing to ensure format correctness.

```bash
# Automatic validation (included in pipeline)
python scripts/run_pipeline.py data.json --output outputs/
```

**Validation checks:**
- File format validation (JSON, JSONL, CSV)
- Structure verification
- Sample data loading test

### Stage 1: UniClinicalDataEngine (ETL)

Converts raw clinical data into tau2-bench compatible format.

```bash
python -m UniClinicalDataEngine.cli \
    --source-type nhands \
    --source-path ./raw_data/patients.json \
    --output-dir ./stage1_output
```

**Generated files:**
- `tasks.json` - Clinical tasks
- `db.json` - Clinical knowledge base
- `tools.json` - Tool definitions
- `policy.md` - Clinical policy

### Stage 1.5: Task Validation (NEW)

Validates generated tasks using DataValidator.

```python
from DataValidator import MedicalDialogueValidator

validator = MedicalDialogueValidator(strict_mode=False)
result = validator.validate_dataset(Path("stage1_output/tasks.json"))

if result.is_valid:
    print("Tasks are valid!")
else:
    print(f"Found {len(result.issues)} issues")
```

### Stage 2: DataQualityFiltering

Filters tasks based on quality scores.

```bash
python -m DataQualityFiltering data-quality filter \
    --input stage1_output/tasks.json \
    --output stage2_output/ \
    --threshold 3.5
```

**Quality criteria:**
- Tool count (60% weight)
- Content length (40% weight)

### Stage 3: Agent Simulation (tau2)

AI agents (doctors) interact with patient simulators.

```bash
python -m tau2.cli run \
    --domain clinical_cardiology \
    --agent llm_agent \
    --model gpt-4 \
    --tasks stage2_output/tasks_filtered.json
```

**Outputs:**
- Simulation runs with message history
- Agent actions and tool calls
- Patient responses

### Stage 4: Clinical Evaluation (NEW)

Evaluates agent performance using clinical evaluators.

```python
from tau2.evaluator import ClinicalEvaluator

reward_info = ClinicalEvaluator.calculate_reward(
    task=task,
    full_trajectory=simulation.messages,
    model="gpt-4"
)

print(f"Clinical Score: {reward_info.clinical_checks[0].overall_score}/5.0")
```

**Evaluation dimensions:**
- Clinical Accuracy (40%): Medical knowledge, diagnostic reasoning, treatment appropriateness
- Dialogue Fluency (30%): Question understanding, coherence, clarity, interaction
- Safety & Empathy (30%): Safety awareness, empathy, communication

### Quick Start: End-to-End

#### Option 1: Using Master Pipeline (Recommended)

```bash
# Complete pipeline with agent simulation and evaluation
python scripts/master_pipeline.py \
    --input data/raw/medical_dialogue.json \
    --output results/ \
    --run-agents \
    --evaluate \
    --domain clinical_cardiology \
    --model gpt-4 \
    --num-tasks 10
```

#### Option 2: Step-by-Step

```bash
# Step 1: Generate tasks from raw data
python -m UniClinicalDataEngine.cli \
    --source-type nhands \
    --source-path data/raw/patients.json \
    --output-dir stage1_output

# Step 2: Validate generated tasks
python -m DataValidator stage1_output/tasks.json

# Step 3: Filter by quality
python -m DataQualityFiltering data-quality filter \
    --input stage1_output/tasks.json \
    --output stage2_output \
    --threshold 3.5

# Step 4: Run agent simulation
python -m tau2.cli run \
    --domain clinical_cardiology \
    --agent llm_agent \
    --model gpt-4 \
    --num-tasks 10

# Step 5: Evaluate results (automatic with tau2)
# Evaluation is built into tau2 run, or use ClinicalEvaluator directly
```

### Pipeline Scripts

| Script | Purpose | Stages |
|--------|---------|--------|
| `scripts/run_pipeline.py` | Data processing only | 0, 1, 1.5, 2 |
| `scripts/master_pipeline.py` | Complete end-to-end | 0, 1, 1.5, 2, 3, 4 |

### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **DataValidator** | `DataValidator/` | Validates medical dialogue data structure and content |
| **ClinicalEvaluator** | `src/tau2/evaluator/evaluator_clinical.py` | Multi-dimensional clinical evaluation |
| **RewardType.CLINICAL** | `src/tau2/data_model/tasks.py` | Clinical reward type |
| **ClinicalCheck** | `src/tau2/data_model/simulation.py` | Clinical evaluation result model |
| **EvaluationType.CLINICAL** | `src/tau2/evaluator/evaluator.py` | Clinical evaluation type |

---

## 4. Data Pipeline (Legacy)

### Stage 1: UniClinicalDataEngine

Converts raw clinical data from various sources into tau2-bench compatible task sets. The engine normalizes heterogeneous clinical data into a standardized format and generates all artifacts needed for benchmarking: tasks, database, tools, and policy documents.

```
raw clinical data --> UniClinicalDataEngine --> tasks.json, db.json, tools.json, policy.md
```

#### Supported Data Sources

| Source Type | Format | Description |
|------------|--------|-------------|
| `nhands`   | JSON / JSONL | NHands clinical dataset format |
| `csv`      | CSV | Tabular clinical data with configurable column mapping |
| `json`     | JSON / JSONL | Generic JSON with dot-path field mapping for nested structures |

#### Generated Outputs

| File | Description |
|------|-------------|
| `tasks.json` | Array of tau2 Task objects with patient scenarios and evaluation criteria |
| `db.json` | Clinical database with `patients` and `encounters` tables |
| `tools.json` | OpenAI-compatible tool definitions (6 default clinical tools) |
| `policy.md` | Clinical policy document covering prescribing, lab orders, diagnosis, transfers, and communication guidelines |

#### Default Clinical Tools

The engine generates specifications for six clinical tools:

| Tool | Type | Description |
|------|------|-------------|
| `find_patient_info` | read | Look up patient demographics, history, allergies, medications |
| `get_medical_history` | read | Retrieve full medical history |
| `prescribe_medication` | write | Prescribe medication with dosage, frequency, and duration |
| `order_lab_test` | write | Order lab tests (CBC, BMP, etc.) with priority level |
| `record_diagnosis` | write | Record diagnosis with ICD-10 code |
| `transfer_to_specialist` | generic | Transfer patient to specialist with clinical summary |

#### CLI Usage

```bash
python -m UniClinicalDataEngine.cli \
    --source-type nhands \
    --source-path ./raw_data/patients.json \
    --output-dir ./output \
    --domain-name clinical
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source-type` | Yes | — | `nhands`, `csv`, or `json` |
| `--source-path` | Yes | — | Path to source data file |
| `--output-dir` | No | `output` | Directory for generated files |
| `--domain-name` | No | `clinical` | Domain name for tau2 tasks |
| `--adapter-kwargs` | No | — | JSON string with adapter-specific config |

**Adapter-specific configuration** is passed via `--adapter-kwargs`:

```bash
# CSV with custom column mapping
python -m UniClinicalDataEngine.cli \
    --source-type csv \
    --source-path data.csv \
    --adapter-kwargs '{"column_mapping": {"patient_id": "pid", "name": "patient_name"}}'

# JSON with nested records path and field mapping
python -m UniClinicalDataEngine.cli \
    --source-type json \
    --source-path data.json \
    --adapter-kwargs '{"records_path": "data.patients", "field_path_mapping": {"name": "demographics.full_name"}}'
```

#### Custom Adapters

New data source adapters can be registered programmatically:

```python
from UniClinicalDataEngine.engine import UniClinicalDataEngine
from UniClinicalDataEngine.adapters.base import BaseAdapter

class MyAdapter(BaseAdapter):
    def load_raw_data(self): ...
    def normalize_record(self, raw): ...
    def build_scenario(self, patient, index): ...

UniClinicalDataEngine.register_adapter("my_source", MyAdapter)
```

---

### Stage 2: DataQualityFiltering

Scores and filters candidate tasks across four quality dimensions using human review, LLM-based review, or both. Tasks below a configurable threshold are rejected.

```
tasks.json --> DataQualityFiltering --> tasks_filtered.json + review_scores.json
```

#### Quality Dimensions

Each task is scored 0–5 on four dimensions:

| Dimension | Description |
|-----------|-------------|
| Clinical Accuracy | Correctness of the clinical scenario |
| Scenario Realism | How realistic the patient scenario is |
| Evaluation Completeness | Completeness of evaluation criteria |
| Difficulty Appropriateness | Whether the difficulty level is suitable |

The **overall score** is the mean of the four dimension scores. Tasks with an overall score >= the threshold are accepted.

#### Review Modes

| Mode | Description |
|------|-------------|
| `human` | Interactive terminal-based scoring by a human reviewer |
| `semi_auto` | Automated scoring via LLM (default) |
| `both` | Human review on a subset + LLM review on all, with calibration analysis |

#### CLI Usage

```bash
python -m DataQualityFiltering.cli \
    --tasks-path ./output/tasks.json \
    --output-path ./filtered_output \
    --threshold 3.5 \
    --review-mode semi_auto \
    --llm-model gpt-4o-mini
```

**Arguments:**

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--tasks-path` | Yes | — | Path to input `tasks.json` |
| `--output-path` | No | `filtered_output` | Directory for output files |
| `--threshold` | No | `3.0` | Minimum overall score to accept (0–5) |
| `--review-mode` | No | `semi_auto` | `human`, `semi_auto`, or `both` |
| `--llm-model` | No | `gpt-4o-mini` | LLM model for automated review |
| `--guidance-path` | No | — | Path to custom guidance prompt file |
| `--human-scores-path` | No | — | Path to pre-existing human scores JSON |

#### Output Files

| File | Description |
|------|-------------|
| `tasks_filtered.json` | Tasks that passed the quality threshold |
| `review_scores.json` | Full scores for all tasks with per-dimension breakdowns |
| `calibration_report.json` | Correlation analysis between human and LLM reviewers (only in `both` mode) |

#### Calibration (`both` mode)

When using `--review-mode both`, the pipeline computes Pearson correlation between human and LLM scores — both overall and per-dimension. This validates whether the LLM reviewer can serve as a reliable proxy for human review.

- **Minimum calibration tasks**: 3 (configurable)
- **Target correlation**: r > 0.5

---

### End-to-End Example

```bash
# Stage 1: Generate tasks from raw NHands data
python -m UniClinicalDataEngine.cli \
    --source-type nhands \
    --source-path ./raw_data/patients.json \
    --output-dir ./generated

# Stage 2: Filter tasks using LLM review
python -m DataQualityFiltering.cli \
    --tasks-path ./generated/tasks.json \
    --output-path ./final \
    --threshold 3.5 \
    --review-mode semi_auto

# Result: ./final/tasks_filtered.json contains quality-checked tasks
```

---

## 4. Benchmark Scale

| Dimension | Target |
|-----------|--------|
| Domains   | 4      |
| Tasks     | 100    |
| Models    | 5      |

---

## 5. Authentication

Access to patient data tools is gated by a token (password-based auth), consistent with the tau2 orchestrator's token injection mechanism.

---

## 6. Running Evaluations

To run tau2-bench evaluations on the clinical domains, see [CLINICAL_BENCHMARK_GUIDE.md](CLINICAL_BENCHMARK_GUIDE.md).

**Quick Start:**

```bash
# 1. Configure API key in .env file
# 2. List available clinical domains
python run_clinical_benchmark.py --list

# 3. Run a test evaluation (1 task)
python run_clinical_benchmark.py --domain clinical_neurology --max-tasks 1

# 4. Run full evaluation (all domains)
python run_clinical_benchmark.py --all --max-tasks 5
```

For detailed instructions, model options, and troubleshooting, refer to the [Clinical Benchmark Guide](CLINICAL_BENCHMARK_GUIDE.md).

---

## 7. Dependencies

- **pydantic** — Data validation and models
- **litellm** — LLM API abstraction (used by DataQualityFiltering)
- **scipy** (optional) — Pearson correlation for calibration (falls back to pure-Python implementation)
