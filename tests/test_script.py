import json
from pathlib import Path

print("Starting...")

base_dir = Path(r'C:/Users/方正/tau2-bench/data/processed')

# Load one file to test
tasks = json.load(open(r'C:/Users/方正/tau2-bench/data/clinical/tasks.json', encoding='utf-8'))
print(f"Loaded {len(tasks)} tasks")

# Create one output file
(base_dir / 'medagentbench').mkdir(parents=True, exist_ok=True)
output_file = base_dir / 'medagentbench' / 'consultation_paradigm.json'

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(tasks[:1], f, indent=2, ensure_ascii=False)

print(f"Wrote test file to {output_file}")
print("Test complete!")
