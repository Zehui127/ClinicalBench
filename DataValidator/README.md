# DataValidator Module

Medical Consultation Dialogue Dataset Validator with modular architecture.

## 📁 Directory Structure

```
DataValidator/
├── __init__.py                  # Module entry point
├── __main__.py                  # CLI entry point (python -m DataValidator)
├── cli.py                       # Command-line interface
├── core.py                      # Main validator class
├── models.py                    # Data models (ValidationIssue, ValidationResult)
├── keywords.py                  # Medical keywords (987 terms)
│
├── validators/                  # Validation modules
│   ├── __init__.py
│   ├── structure_validator.py      # Structure validation
│   ├── medical_content_validator.py # Medical content validation
│   └── multi_turn_validator.py      # Multi-turn dialogue validation
│
├── utils/                       # Utility functions
│   ├── __init__.py
│   └── statistics.py              # Statistics calculation
│
└── tests/                       # Tests
    ├── __init__.py
    └── (test files)
```

## 🚀 Usage

### Command-line

```bash
# Validate a dataset
python -m DataValidator data/tau2/domains/clinical/tasks.json

# Strict mode
python -m DataValidator data/tau2/domains/clinical/tasks.json --strict

# Quiet mode (only errors/warnings)
python -m DataValidator data/tau2/domains/clinical/tasks.json --quiet

# Save JSON output
python -m DataValidator data/tau2/domains/clinical/tasks.json --json-output result.json

# Show keyword information
python -m DataValidator --show-keywords
```

### Python API

```python
from DataValidator import MedicalDialogueValidator
from pathlib import Path

# Initialize validator
validator = MedicalDialogueValidator(strict_mode=False)

# Validate dataset
result = validator.validate_dataset(Path("tasks.json"))

# Check result
if result.is_valid:
    print("✅ Dataset is valid!")
else:
    print("❌ Dataset has issues:")
    for error in result.errors:
        print(f"  - {error}")

# Print detailed report
result.print_report()

# Access statistics
stats = result.stats
print(f"Total tasks: {result.total_tasks}")
print(f"Multi-turn tasks: {stats.get('multi_turn_tasks', 0)}")
print(f"Domain distribution: {stats.get('domain_distribution', {})}")
```

### Validating Task Lists

```python
from DataValidator import MedicalDialogueValidator
import json

# Load tasks
with open('tasks.json', 'r') as f:
    tasks = json.load(f)

# Validate directly
validator = MedicalDialogueValidator()
result = validator.validate_tasks(tasks)

print(f"Valid: {result.is_valid}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")
```

## 📦 Components

### Core Classes

- **MedicalDialogueValidator** (`core.py`)
  - Main validator class
  - Orchestrates all validation checks

- **ValidationResult** (`models.py`)
  - Contains validation results
  - Provides reporting and statistics

- **ValidationIssue** (`models.py`)
  - Represents a single validation issue
  - Has severity levels: ERROR, WARNING, INFO

### Validators

- **StructureValidator** (`validators/structure_validator.py`)
  - Validates required fields
  - Checks data structure
  - Validates evaluation criteria

- **MedicalContentValidator** (`validators/medical_content_validator.py`)
  - Validates medical terminology
  - Checks consultation patterns
  - Identifies safety concerns

- **MultiTurnValidator** (`validators/multi_turn_validator.py`)
  - Counts dialogue turns
  - Validates multi-turn structure
  - Provides turn statistics

### Utilities

- **calculate_dataset_statistics** (`utils/statistics.py`)
  - Calculates comprehensive statistics
  - Domain distribution
  - Ticket length statistics

## 🔧 Extending the Validator

### Adding a New Validator

```python
# In validators/custom_validator.py
from ..models import ValidationIssue, ValidationLevel

class CustomValidator:
    def validate(self, task, task_idx):
        issues = []
        task_id = task.get("id", f"task_{task_idx}")

        # Add your validation logic here
        if some_condition:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                category="custom",
                message="Custom validation message",
                task_id=task_id,
                suggestion="Fix suggestion"
            ))

        return issues
```

Then integrate it into `core.py`:

```python
from .validators.custom_validator import CustomValidator

class MedicalDialogueValidator:
    def __init__(self, strict_mode: bool = False):
        # ... existing code ...
        self.custom_validator = CustomValidator()

    def validate_task(self, task, idx):
        issues = []
        # ... existing validations ...
        custom_issues = self.custom_validator.validate(task, idx)
        issues.extend(custom_issues)
        return issues
```

### Adding New Keywords

Edit `keywords.py` and add to the appropriate category:

```python
class MedicalKeywords:
    MY_CATEGORY_ZH = [
        "keyword1", "keyword2", "keyword3"
    ]

    @classmethod
    def get_all_keywords(cls):
        keywords = super().get_all_keywords()
        keywords.extend(cls.MY_CATEGORY_ZH)
        return keywords
```

## 📊 Statistics Provided

- **Total tasks**: Number of tasks in dataset
- **Errors/Warnings/Info**: Count of issues by level
- **Tasks with errors/warnings**: Number of affected tasks
- **Multi-turn tasks**: Number of tasks with multi-turn dialogue
- **Safety-related tasks**: Number of tasks mentioning urgent conditions
- **Total evaluation actions**: Number of evaluation criteria actions
- **Average/Min/Max ticket length**: Ticket length statistics
- **Domain distribution**: Tasks per medical domain

## 🎯 Validation Levels

| Level | Meaning | Impact |
|-------|---------|--------|
| **ERROR** | Critical issues preventing dataset use | Blocks validation |
| **WARNING** | Should be addressed but doesn't block use | Advisory |
| **INFO** | Informational messages and suggestions | No action required |

## 📚 Related Documentation

- [Main README](../../DATA_VALIDATOR_README.md) - Complete usage guide
- [Test Suite](../../test_validator.py) - Example usage and test cases

## 📝 Version

Current version: 1.0.0
- Supports bilingual (English/Chinese) validation
- 987 medical keywords across 30+ categories
- Modular architecture for easy extension
