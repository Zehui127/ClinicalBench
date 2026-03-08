# Clinical Consultation Agent Benchmark - Usage Guide

## Overview

The `benchmark_evaluation.py` script provides a comprehensive evaluation framework for assessing Clinical Consultation Agent performance in tool invocation accuracy, timing, and clinical context awareness.

## Quick Start

### Installation

No external dependencies required - uses only Python standard libraries (json, datetime).

**Requirement:** Python 3.8+

```bash
cd C:\Users\方正\tau2-bench\data\processed\clinical_tools\
python benchmark_evaluation.py
```

### Running Test Cases

```bash
# Run with default tools.json path
python benchmark_evaluation.py

# Run with custom tools.json path
python benchmark_evaluation.py /path/to/your/tools.json
```

---

## Core Functions

### 1. load_tools(tools_path=None)

Load and parse tools.json file.

```python
from benchmark_evaluation import load_tools

# Load from default path
tools = load_tools()

# Load from custom path
tools = load_tools("/path/to/tools.json")

print(f"Loaded {len(tools)} tools")
for tool in tools:
    print(f"  - {tool['function']['name']}")
```

**Returns:** List of tool dictionaries containing schema and metadata

**Raises:**
- `FileNotFoundError` if tools.json not found
- `json.JSONDecodeError` if tools.json contains invalid JSON

---

### 2. evaluate_agent(agent_tool_calls, tools_path=None)

Main evaluation function - calculates total score and generates structured report.

#### Input Format

```python
agent_tool_calls = [
    {
        "tool_name": "find_patient_basic_info",
        "parameters": {
            "patient_id": "P20260303001"
        },
        "call_time": "2026-03-03T08:00:00"  # Optional ISO timestamp
    },
    {
        "tool_name": "get_medical_history_key",
        "parameters": {
            "patient_id": "P20260303001",
            "history_type": "allergies"
        },
        "call_time": "2026-03-03T08:05:00"
    },
    # ... more tool calls
]
```

#### Usage Example

```python
from benchmark_evaluation import evaluate_agent, print_evaluation_report

# Define Agent tool calls
agent_calls = [
    {
        "tool_name": "find_patient_basic_info",
        "parameters": {"patient_id": "P20260303001"},
        "call_time": "2026-03-03T08:00:00"
    },
    {
        "tool_name": "assess_risk_level",
        "parameters": {
            "patient_id": "P20260303001",
            "symptoms": "chest pain",
            "vital_signs": "BP 160/100"
        },
        "call_time": "2026-03-03T08:05:00"
    },
    {
        "tool_name": "get_medical_history_key",
        "parameters": {
            "patient_id": "P20260303001",
            "history_type": "allergies"
        },
        "call_time": "2026-03-03T08:07:00"
    },
    {
        "tool_name": "prescribe_medication_safe",
        "parameters": {
            "patient_id": "P20260303001",
            "medication_name": "Amlodipine",
            "dosage": "5mg qd",
            "duration": "30 days",
            "route": "oral"
        },
        "call_time": "2026-03-03T08:10:00"
    },
    {
        "tool_name": "generate_follow_up_plan",
        "parameters": {
            "patient_id": "P20260303001",
            "diagnosis": "hypertension",
            "follow_up_type": "in_person",
            "timeframe_days": 14
        },
        "call_time": "2026-03-03T08:15:00"
    }
]

# Evaluate Agent
report = evaluate_agent(agent_calls)

# Print report
print_evaluation_report(report)

# Access specific scores
print(f"Total Score: {report['total_score']}/100")
print(f"Pass Status: {report['pass_status']}")
print(f"Timing Score: {report['timing_score']}/50")
print(f"Parameter Score: {report['parameter_score']}/30")
print(f"Context Score: {report['context_score']}/20")
```

#### Output Format

```python
{
    "total_score": 95,              # 0-100 overall score
    "timing_score": 50,             # 0-50 invocation timing
    "parameter_score": 28.5,        # 0-30 parameter accuracy
    "context_score": 16.5,          # 0-20 context awareness
    "feedback": [
        "EXCELLENT: Outstanding performance",
        "✓ find_patient_basic_info called first",
        "✓ All required parameters present",
        "✓ Risk assessment before treatment"
    ],
    "pass_status": true,            # True if score >= 70
    "evaluation_timestamp": "2026-03-03T08:20:00",
    "tool_calls_evaluated": 5
}
```

---

### 3. validate_invocation_timing(agent_tool_calls, tool_list)

Validate if tools are called in correct workflow order.

**Scoring:** 50 points max
- **Critical Failures (0 points):**
  - `find_patient_basic_info` not called first
  - `generate_follow_up_plan` not called last
- **Deductions:**
  - -5 points per major order violation
  - -10 points for prescribing without allergy check

```python
from benchmark_evaluation import load_tools, validate_invocation_timing

tools = load_tools()
agent_calls = [...]  # Your tool calls

score, feedback = validate_invocation_timing(agent_calls, tools)

print(f"Timing Score: {score}/50")
for fb in feedback:
    print(f"  {fb}")
```

---

### 4. validate_parameter_accuracy(agent_tool_call, tool_schema)

Validate if parameters are complete and valid.

**Scoring:** 3 points per tool (max 30 total)

```python
from benchmark_evaluation import load_tools, validate_parameter_accuracy

tools = load_tools()
tool_schemas = {t['function']['name']: t['function'] for t in tools}

# Validate a single tool call
tool_call = {
    "tool_name": "prescribe_medication_safe",
    "parameters": {
        "patient_id": "P123",
        "medication_name": "Amlodipine",
        "dosage": "5mg qd",
        "duration": "30 days",
        "route": "oral"
    }
}

score, feedback = validate_parameter_accuracy(
    tool_call,
    tool_schemas["prescribe_medication_safe"]
)

print(f"Parameter Score: {score}/3")
for fb in feedback:
    print(f"  {fb}")
```

---

### 5. validate_context_awareness(agent_tool_calls)

Validate clinical workflow dependencies.

**Scoring:** 20 points max
- 5 points: Risk assessment before treatment
- 5 points: Symptom exploration before diagnosis
- 5 points: Safety checks before prescribing
- 5 points: Clinical guideline consultation

```python
from benchmark_evaluation import validate_context_awareness

agent_calls = [...]  # Your tool calls

score, feedback = validate_context_awareness(agent_calls)

print(f"Context Score: {score}/20")
for fb in feedback:
    print(f"  {fb}")
```

---

## Scoring Rubric

### Total Score: 100 points

| Dimension | Points | Pass Threshold |
|-----------|--------|----------------|
| **Invocation Timing** | 50 | ≥35 points |
| **Parameter Accuracy** | 30 | ≥20 points |
| **Context Awareness** | 20 | ≥12 points |
| **TOTAL** | **100** | **≥70 points** |

### Grade Boundaries

| Score | Grade | Status |
|-------|-------|--------|
| 90-100 | Excellent | ✓ Pass |
| 70-89 | Competent | ✓ Pass |
| 50-69 | Needs Improvement | ✗ Fail |
| 0-49 | Critical Failures | ✗ Fail |

---

## Critical Workflow Rules

### Auto-Fail Conditions (Score = 0)

1. **find_patient_basic_info not called first**
   ```python
   # WRONG - This will FAIL
   [
       {"tool_name": "get_medical_history_key", ...},  # Not first!
       {"tool_name": "find_patient_basic_info", ...}
   ]
   ```

2. **generate_follow_up_plan not called last**
   ```python
   # WRONG - This will FAIL
   [
       {"tool_name": "find_patient_basic_info", ...},
       {"tool_name": "generate_follow_up_plan", ...},  # Not last!
       {"tool_name": "record_diagnosis_icd10", ...}
   ]
   ```

3. **Prescribing without allergy check**
   ```python
   # WRONG - This will FAIL
   [
       {"tool_name": "find_patient_basic_info", ...},
       {"tool_name": "prescribe_medication_safe", ...}  # No allergy check!
   ]
   ```

### Correct Workflow Example

```python
# CORRECT - This will PASS
[
    {"tool_name": "find_patient_basic_info", ...},      # 1st (REQUIRED)
    {"tool_name": "assess_risk_level", ...},
    {"tool_name": "get_medical_history_key", ...},      # Before prescribing
    {"tool_name": "ask_symptom_details", ...},
    {"tool_name": "retrieve_clinical_guideline", ...},
    {"tool_name": "retrieve_medication_details", ...},  # Before prescribing
    {"tool_name": "prescribe_medication_safe", ...},
    {"tool_name": "record_diagnosis_icd10", ...},
    {"tool_name": "generate_follow_up_plan", ...}       # Last (REQUIRED)
]
```

---

## Integration Examples

### Example 1: Evaluate OpenAI Agent

```python
import json
from benchmark_evaluation import evaluate_agent

# Simulate Agent tool calls from OpenAI Function Calling
agent_response = {
    "tool_calls": [
        {
            "id": "call_1",
            "function": {
                "name": "find_patient_basic_info",
                "arguments": '{"patient_id": "P001"}'
            }
        },
        # ... more tool calls
    ]
}

# Convert to evaluation format
tool_calls = []
for tc in agent_response["tool_calls"]:
    tool_calls.append({
        "tool_name": tc["function"]["name"],
        "parameters": json.loads(tc["function"]["arguments"]),
        "call_time": datetime.now().isoformat()
    })

# Evaluate
report = evaluate_agent(tool_calls)
print(f"Score: {report['total_score']}/100")
```

### Example 2: Batch Evaluation

```python
from benchmark_evaluation import evaluate_agent
import csv

# Load Agent results from CSV
def evaluate_batch(csv_file):
    results = []

    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse tool calls from CSV
            agent_calls = json.loads(row['tool_calls'])

            # Evaluate
            report = evaluate_agent(agent_calls)

            results.append({
                'agent_id': row['agent_id'],
                'total_score': report['total_score'],
                'pass_status': report['pass_status']
            })

    return results

# Example: Save results
results = evaluate_batch('agent_results.csv')
for r in results:
    print(f"{r['agent_id']}: {r['total_score']}/100 - {'PASS' if r['pass_status'] else 'FAIL'}")
```

### Example 3: Real-Time Monitoring

```python
from benchmark_evaluation import evaluate_agent

class AgentMonitor:
    def __init__(self):
        self.session_calls = []

    def log_tool_call(self, tool_name, parameters):
        self.session_calls.append({
            "tool_name": tool_name,
            "parameters": parameters,
            "call_time": datetime.now().isoformat()
        })

    def evaluate_session(self):
        report = evaluate_agent(self.session_calls)
        return report

# Usage
monitor = AgentMonitor()
monitor.log_tool_call("find_patient_basic_info", {"patient_id": "P001"})
monitor.log_tool_call("assess_risk_level", {"patient_id": "P001", "symptoms": "chest pain"})

# Get live evaluation
report = monitor.evaluate_session()
print(f"Current Score: {report['total_score']}/100")
```

---

## Error Handling

### Missing Tools

```python
from benchmark_evaluation import evaluate_agent

# Invalid tool name
agent_calls = [
    {
        "tool_name": "invalid_tool_name",  # Not in tools.json
        "parameters": {}
    }
]

report = evaluate_agent(agent_calls)
# Result: Score deduction, feedback includes "Unknown tool" warning
```

### Missing Required Parameters

```python
# Missing 'route' parameter (required for prescribe_medication_safe)
agent_calls = [
    {
        "tool_name": "prescribe_medication_safe",
        "parameters": {
            "patient_id": "P001",
            "medication_name": "Amlodipine",
            "dosage": "5mg qd",
            "duration": "30 days"
            # 'route' is missing!
        }
    }
]

report = evaluate_agent(agent_calls)
# Result: Parameter score deduction, feedback warns of missing parameter
```

### Invalid Enum Values

```python
# Invalid route value
agent_calls = [
    {
        "tool_name": "prescribe_medication_safe",
        "parameters": {
            "patient_id": "P001",
            "medication_name": "Amlodipine",
            "dosage": "5mg qd",
            "duration": "30 days",
            "route": "invalid_route"  # Not in enum!
        }
    }
]

report = evaluate_agent(agent_calls)
# Result: Parameter score deduction, feedback warns of invalid enum value
```

---

## Advanced Usage

### Custom Scoring Thresholds

```python
from benchmark_evaluation import evaluate_agent

# Evaluate and apply custom thresholds
report = evaluate_agent(agent_calls)

# Custom thresholds
EXCELLENCE_THRESHOLD = 85  # Default is 90
PASS_THRESHOLD = 65        # Default is 70

if report['total_score'] >= EXCELLENCE_THRESHOLD:
    grade = "Excellent"
elif report['total_score'] >= PASS_THRESHOLD:
    grade = "Pass"
else:
    grade = "Fail"

print(f"Grade: {grade} ({report['total_score']}/100)")
```

### Export Report to JSON

```python
import json
from benchmark_evaluation import evaluate_agent

report = evaluate_agent(agent_calls)

# Save report
with open('evaluation_report.json', 'w') as f:
    json.dump(report, f, indent=2)

# Load later
with open('evaluation_report.json', 'r') as f:
    loaded_report = json.load(f)
```

### Generate Comparison Report

```python
from benchmark_evaluation import evaluate_agent

def compare_agents(agent1_calls, agent2_calls):
    report1 = evaluate_agent(agent1_calls)
    report2 = evaluate_agent(agent2_calls)

    comparison = {
        "agent1_score": report1['total_score'],
        "agent2_score": report2['total_score'],
        "difference": report2['total_score'] - report1['total_score'],
        "winner": "Agent 2" if report2['total_score'] > report1['total_score'] else "Agent 1"
    }

    return comparison

# Usage
result = compare_agents(agent_a_calls, agent_b_calls)
print(f"Winner: {result['winner']}")
print(f"Score Difference: {result['difference']}")
```

---

## Troubleshooting

### Issue: ModuleNotFoundError

```bash
# Solution: Ensure you're in the correct directory
cd C:\Users\方正\tau2-bench\data\processed\clinical_tools\
python benchmark_evaluation.py
```

### Issue: FileNotFoundError - tools.json

```bash
# Solution: Ensure tools.json is in the same directory
# Or provide full path:
python benchmark_evaluation.py "C:\path\to\tools.json"
```

### Issue: JSONDecodeError in tools.json

```bash
# Solution: Validate tools.json format
python -m json.tool tools.json
```

### Issue: Low Score Despite Correct Calls

**Check:**
1. Is `find_patient_basic_info` the FIRST call?
2. Is `generate_follow_up_plan` the LAST call?
3. Is `get_medical_history_key` (allergies) BEFORE `prescribe_medication_safe`?

If any answer is NO, critical failure rules apply.

---

## Best Practices

### 1. Always Include Timestamps

```python
# GOOD
tool_call = {
    "tool_name": "find_patient_basic_info",
    "parameters": {"patient_id": "P001"},
    "call_time": "2026-03-03T08:00:00"  # Include this
}

# ACCEPTABLE (but less informative)
tool_call = {
    "tool_name": "find_patient_basic_info",
    "parameters": {"patient_id": "P001"}
    # No timestamp - still works
}
```

### 2. Use Correct Parameter Types

```python
# GOOD - string for patient_id
{"patient_id": "P001"}

# BAD - number for patient_id
{"patient_id": 123}  # Wrong type!
```

### 3. Validate Before Evaluation

```python
def validate_tool_call_format(tool_calls):
    """Validate basic structure before evaluation."""
    required_fields = ['tool_name', 'parameters']

    for tc in tool_calls:
        for field in required_fields:
            if field not in tc:
                raise ValueError(f"Missing required field: {field}")

    return True

# Use before evaluate_agent
validate_tool_call_format(agent_calls)
report = evaluate_agent(agent_calls)
```

### 4. Handle Edge Cases

```python
# Empty tool calls
report = evaluate_agent([])
# Result: Score 0, feedback "No tool calls made"

# Single tool call (incomplete workflow)
report = evaluate_agent([
    {"tool_name": "find_patient_basic_info", "parameters": {"patient_id": "P001"}}
])
# Result: Low score, feedback warns of incomplete workflow
```

---

## API Reference

### Function Signatures

```python
load_tools(tools_path: str = None) -> List[Dict]

validate_invocation_timing(
    agent_tool_calls: List[Dict],
    tool_list: List[Dict]
) -> Tuple[int, List[str]]

validate_parameter_accuracy(
    agent_tool_call: Dict,
    tool_schema: Dict
) -> Tuple[float, List[str]]

validate_context_awareness(
    agent_tool_calls: List[Dict]
) -> Tuple[float, List[str]]

evaluate_agent(
    agent_tool_calls: List[Dict],
    tools_path: str = None
) -> Dict[str, Any]

print_evaluation_report(report: Dict[str, Any]) -> None

test_evaluation() -> None
```

---

## Support

For issues or questions:
1. Check this usage guide
2. Review TOOL_EVALUATION_FRAMEWORK.md for detailed scoring criteria
3. Verify tools.json format matches OpenAI Function Call schema
4. Run `test_evaluation()` to see example pass/fail cases
