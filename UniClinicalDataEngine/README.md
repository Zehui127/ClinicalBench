# UniClinicalDataEngine

Universal Clinical Data ETL Engine - A complete Extract → Transform → Load pipeline for clinical data processing.

统一的临床数据 ETL 引擎 - 用于临床数据处理的完整提取 → 转换 → 加载管道。

## Features / 特性

### Complete ETL Pipeline / 完整 ETL 管道

- **Extract**: Load data from JSON/JSONL (NHands format) and CSV
- **Transform**: Normalize, validate, filter, and anonymize clinical data
- **Load**: Generate standardized output files

### Supported Formats / 支持的格式

- **Input**:
  - NHands JSON (`.json`)
  - NHands JSON Lines (`.jsonl`)
  - CSV (`.csv`)

- **Output**:
  - `tasks.json` - Clinical task definitions
  - `db.json` - Clinical knowledge database
  - `tools.json` - Tool definitions
  - `policy.md` - Usage policy document

### 6 Default Clinical Tools / 6个默认临床工具

1. **eGFR Calculator** - Kidney function assessment
2. **Drug Dosing Calculator** - Medication dose adjustments
3. **Drug Interaction Checker** - Drug-drug interaction analysis
4. **Vital Signs Analyzer** - Critical value identification
5. **Lab Values Interpreter** - Lab result interpretation
6. **Clinical Calculator Suite** - Risk scores & decision rules

### Data Processing / 数据处理

- Field normalization and mapping
- Schema validation
- Department and difficulty filtering
- PHI anonymization (optional)
- Auto-detection of required tools
- Statistics and reporting

## Installation / 安装

```bash
cd UniClinicalDataEngine
```

**No external dependencies required!** The core ETL pipeline uses only Python standard library.

Optional (for Excel support):
```bash
pip install -r requirements.txt
```

## Quick Start / 快速开始

### 1. Command Line / 命令行

```bash
# Run complete ETL pipeline
python -m UniClinicalDataEngine.cli etl input.jsonl -o ./output

# With filters
python -m UniClinicalDataEngine.cli etl input.jsonl -o ./output --department cardiology

# With anonymization
python -m UniClinicalDataEngine.cli etl input.jsonl -o ./output --anonymize

# Validate input
python -m UniClinicalDataEngine.cli validate input.jsonl

# Show available tools
python -m UniClinicalDataEngine.cli tools --detail

# Show summary
python -m UniClinicalDataEngine.cli summary ./output/etl_summary.json
```

### 2. Python API / Python 接口

```python
from UniClinicalDataEngine import run_etl

# Run complete ETL pipeline
result = run_etl(
    input_path="data.jsonl",
    input_format="auto",  # Auto-detect
    output_dir="./output",
    validate_input=True,
    anonymize_phi=False,
)

if result.success:
    print(f"Processed {result.records_processed} records")
    print(f"Generated {result.tasks_generated} tasks")
```

## Input Data Format / 输入数据格式

### NHands JSONL Format (Recommended)

```json
{"id": "TASK001", "description": "65-year-old male with hypertension", "department": "cardiology", "difficulty": "moderate", "clinical_scenario": {"patient_info": {"age": 65, "gender": "male"}, "diagnosis": "hypertension", "vital_signs": {"blood_pressure_systolic": 165, "blood_pressure_diastolic": 95}, "lab_results": {"creatinine": 1.8, "egfr": 42}}, "tool_call_requirements": {"required_tools": ["drug_dosing_calculator"]}}
```

### CSV Format

```csv
id,description,department,difficulty,age,gender,diagnosis
TASK001,Hypertension,cardiology,moderate,65,male,hypertension
TASK002,CKD,nephrology,easy,62,female,CKD
```

## Output Files / 输出文件

### 1. tasks.json

Clinical task definitions with standardized schema.

```json
[
  {
    "id": "TASK001",
    "department": "cardiology",
    "difficulty": "moderate",
    "description": "65-year-old male with hypertension",
    "clinical_scenario": {...},
    "tool_call_requirements": {...}
  }
]
```

### 2. db.json

Clinical knowledge database with indexes.

```json
{
  "metadata": {...},
  "records": [...],
  "indexes": {
    "by_department": {...},
    "by_difficulty": {...}
  }
}
```

### 3. tools.json

Tool definitions for all 6 clinical tools.

```json
{
  "metadata": {...},
  "tools": [
    {
      "name": "egfr_calculator",
      "display_name": "eGFR Calculator",
      "parameters": [...]
    }
  ]
}
```

### 4. policy.md

Comprehensive usage policy document covering:
- Data privacy and security
- Tool usage guidelines
- Clinical decision making
- Quality assurance
- Compliance requirements

## Available Clinical Tools / 可用的临床工具

| Tool | Category | Description |
|------|----------|-------------|
| `egfr_calculator` | Nephrology | Calculate eGFR and CKD stage |
| `drug_dosing_calculator` | Pharmacology | Calculate adjusted drug doses |
| `drug_interaction_checker` | Pharmacology | Check for drug interactions |
| `vital_signs_analyzer` | Assessment | Analyze vital signs for abnormalities |
| `lab_values_interpreter` | Laboratory | Interpret lab results |
| `clinical_calculator` | Calculation | Risk scores & decision rules |

## Project Structure / 项目结构

```
UniClinicalDataEngine/
├── __init__.py              # Package exports
├── engine.py                # Core ETL engine
├── cli.py                   # Command-line interface
├── tools.py                 # 6 clinical tools definitions
├── adapters/                # Input format adapters
│   ├── base.py              # Base adapter class
│   ├── nhands_adapter.py    # NHands JSON/JSONL adapter
│   ├── json_adapter.py      # JSON adapter
│   └── csv_adapter.py       # CSV adapter
├── generators/              # Output generators
│   └── output_generator.py  # Generate tasks.json, db.json, tools.json, policy.md
├── tests/
│   └── test_etl.py          # Complete ETL test
├── requirements.txt         # Dependencies (optional)
└── README.md               # This file
```

## Running Tests / 运行测试

```bash
# Run complete ETL test
python UniClinicalDataEngine/tests/test_etl.py
```

The test will:
1. Create sample clinical data
2. Run ETL pipeline on JSONL format
3. Run ETL pipeline on CSV format
4. Test filtering capabilities
5. Display all available tools
6. Generate all output files

## Advanced Usage / 高级用法

### Custom Tool Registration

```python
from UniClinicalDataEngine import ClinicalETLEngine, ETLConfig

custom_tool = {
    "name": "my_custom_tool",
    "display_name": "My Custom Tool",
    "description": "Custom clinical tool",
    "parameters": [...]
}

config = ETLConfig(
    input_path="data.jsonl",
    output_dir="./output",
    custom_tools=[custom_tool]
)

engine = ClinicalETLEngine(config)
result = engine.run_pipeline()
```

### PHI Anonymization

```python
result = run_etl(
    input_path="patient_data.jsonl",
    output_dir="./output_anonymized",
    anonymize_phi=True  # Anonymize patient IDs and names
)
```

### Filtering

```python
result = run_etl(
    input_path="data.jsonl",
    output_dir="./output_cardio",
    department_filter="cardiology",  # Only cardiology
    difficulty_filter="moderate"     # Only moderate difficulty
)
```

## CLI Commands Reference / CLI 命令参考

```
uniclinical etl <input> -o <output> [OPTIONS]
  Run complete ETL pipeline

  Options:
    -f, --format      Input format (auto, nhands_json, nhands_jsonl, csv)
    --no-validate     Skip input validation
    --anonymize       Anonymize PHI
    --department      Filter by department
    --difficulty      Filter by difficulty (easy, moderate, hard)
    -v, --verbose     Increase verbosity

uniclinical validate <input>
  Validate input file format

uniclinical tools [--category] [--department] [--detail]
  List available clinical tools

uniclinical summary <summary_file>
  Show ETL summary report

uniclinical info <input>
  Show input file information
```

## License / 许可证

MIT License

## Contributing / 贡献

Contributions welcome! Please feel free to submit pull requests.

欢迎贡献！请随时提交拉取请求。
