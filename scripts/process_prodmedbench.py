import json
from pathlib import Path

# Paths
input_file = r'C:\Users\方正\tau2-bench\data\raw\ProdMedBench\prodmedbench.jsonl'
output_dir = Path(r'C:\Users\方正\tau2-bench\data\processed\prodmedbench')
output_dir.mkdir(parents=True, exist_ok=True)

# Read JSONL
entries = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            entries.append(json.loads(line))

print(f'Loaded {len(entries)} entries')

# Generate tasks.json (NO ANSWERS)
tasks = []
for i, entry in enumerate(entries):
    task_id = f'prodmedbench_{i+1:03d}'
    question = entry.get('question', '')
    
    ticket = f'{question} If the answer does not exist, the answer should be "Not found"'
    
    # Create notes from question if available
    notes = f'ProdMedBench clinical QA'
    known_info = 'Clinical domain query'
    
    task = {
        'id': task_id,
        'description': {
            'purpose': 'Clinical knowledge QA',
            'relevant_policies': None,
            'notes': notes
        },
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': ticket,
                'domain': 'clinical',
                'reason_for_call': 'Medical consultation',
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
for i, entry in enumerate(entries):
    task_id = f'prodmedbench_{i+1:03d}'
    question = entry.get('question', '')
    answer = entry.get('answer', '')
    options = entry.get('options', '')
    
    # Find full answer text from options
    answer_text = answer
    if options and answer:
        # Parse options to find the full text
        option_lines = options.split('\n')
        for line in option_lines:
            line = line.strip()
            if line.startswith(f'{answer}.') or line.startswith(f'{answer} '):
                answer_text = line.split('.', 1)[1].strip() if '.' in line else line
                break
    
    qa_pair = {
        'id': f'qa_{task_id}',
        'question': question,
        'answer': answer_text,
        'task_id': task_id
    }
    
    # Add optional fields if they exist
    if 'options' in entry:
        qa_pair['options'] = entry['options']
    if 'cot' in entry:
        qa_pair['cot'] = entry['cot']
    
    qa_pairs[task_id] = qa_pair

db_data = {'qa_pairs': qa_pairs}

# Write files
with open(output_dir / 'tasks.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

with open(output_dir / 'db.json', 'w', encoding='utf-8') as f:
    json.dump(db_data, f, indent=2, ensure_ascii=False)

print(f'Created {len(tasks)} tasks and {len(qa_pairs)} QA pairs')
print(f'Tasks: {output_dir / "tasks.json"}')
print(f'DB: {output_dir / "db.json"}')
