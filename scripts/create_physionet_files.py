import json
from pathlib import Path

# Paths
output_dir = Path(r'C:\Users\方正\tau2-bench\data\processed\physionet')
output_dir.mkdir(parents=True, exist_ok=True)

# Sample clinical QA data (typical MIMIC-style questions)
sample_data = [
    {'patient_id': '10032', 'question': 'What is the creatinine level of patient 10032?', 'answer': '1.2 mg/dL', 'lab_type': 'Chemistry', 'unit': 'mg/dL'},
    {'patient_id': '10058', 'question': 'What is the heart rate of patient 10058?', 'answer': '86 bpm', 'lab_type': 'Vital Signs', 'unit': 'bpm'},
    {'patient_id': '10147', 'question': 'What is the diagnosis for patient 10147?', 'answer': 'Sepsis', 'lab_type': 'Diagnosis', 'unit': None},
    {'patient_id': '10256', 'question': 'What is the SpO2 level of patient 10256?', 'answer': '94%', 'lab_type': 'Vital Signs', 'unit': '%'},
    {'patient_id': '10389', 'question': 'What is the glucose level of patient 10389?', 'answer': '142 mg/dL', 'lab_type': 'Chemistry', 'unit': 'mg/dL'},
    {'patient_id': '10421', 'question': 'What is the blood pressure of patient 10421?', 'answer': '120/80 mmHg', 'lab_type': 'Vital Signs', 'unit': 'mmHg'},
    {'patient_id': '10567', 'question': 'What is the WBC count of patient 10567?', 'answer': '11.2 K/uL', 'lab_type': 'Hematology', 'unit': 'K/uL'},
    {'patient_id': '10689', 'question': 'What is the platelet count of patient 10689?', 'answer': '180 x10^3/uL', 'lab_type': 'Hematology', 'unit': 'x10^3/uL'},
    {'patient_id': '10723', 'question': 'What is the potassium level of patient 10723?', 'answer': '4.2 mEq/L', 'lab_type': 'Chemistry', 'unit': 'mEq/L'},
    {'patient_id': '10845', 'question': 'What is the respiratory rate of patient 10845?', 'answer': '18 breaths/min', 'lab_type': 'Vital Signs', 'unit': 'breaths/min'},
]

# Generate tasks.json (NO ANSWERS)
tasks = []
for i, item in enumerate(sample_data):
    task_id = f'physionet_{i+1:03d}'
    question = item['question']
    
    ticket = f'{question} If the answer does not exist, the answer should be "Not found"'
    
    notes = f"Patient ID: {item['patient_id']}, Lab Type: {item['lab_type']}"
    known_info = f"Patient: {item['patient_id']}, Type: {item['lab_type']}"
    
    task = {
        'id': task_id,
        'description': {'purpose': 'Clinical data query', 'relevant_policies': None, 'notes': notes},
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': ticket,
                'domain': 'clinical',
                'reason_for_call': 'Patient data lookup',
                'known_info': known_info,
                'unknown_info': None
            }
        },
        'ticket': ticket,
        'initial_state': None,
        'evaluation_criteria': None,
        'annotations': None
    }
    tasks.append(task)

# Generate db.json (WITH ANSWERS)
qa_pairs = {}
for i, item in enumerate(sample_data):
    task_id = f'physionet_{i+1:03d}'
    qa_pairs[task_id] = {
        'id': f'qa_{task_id}',
        'question': item['question'],
        'answer': item['answer'],
        'task_id': task_id,
        'patient_id': item['patient_id'],
        'lab_type': item['lab_type'],
        'unit': item.get('unit')
    }

db_data = {'qa_pairs': qa_pairs}

# Write files
with open(output_dir / 'tasks.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

with open(output_dir / 'db.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, indent=2, ensure_ascii=False)

print(f'Created {len(tasks)} tasks and {len(qa_pairs)} QA pairs')
print(f'Tasks: {output_dir / "tasks.json"}')
print(f'DB: {output_dir / "db.json"}')
