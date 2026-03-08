import json
from pathlib import Path

# Paths
base_dir = Path(r'C:\Users\方正\tau2-bench\data\processed')

# Ensure directories exist
for name in ['medagentbench', 'medxpertqa', 'physionet', 'prodmedbench']:
    (base_dir / name).mkdir(parents=True, exist_ok=True)

# Load sources
print("Loading source files...")
sources = {}
sources['tasks_medagentbench'] = json.load(open(r'C:\Users\方正\tau2-bench\data\clinical\tasks.json', encoding='utf-8'))
sources['db_medagentbench'] = json.load(open(r'C:\Users\方正\tau2-bench\data\clinical\db.json', encoding='utf-8'))
sources['tasks_medxpertqa'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\medxpertqa\tasks.json', encoding='utf-8'))
sources['db_medxpertqa'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\medxpertqa\db.json', encoding='utf-8'))
sources['tasks_physionet'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\physionet\tasks.json', encoding='utf-8'))
sources['db_physionet'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\physionet\db.json', encoding='utf-8'))
sources['tasks_prodmedbench'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\prodmedbench\tasks.json', encoding='utf-8'))
sources['db_prodmedbench'] = json.load(open(r'C:\Users\方正\tau2-bench\data\processed\prodmedbench\db.json', encoding='utf-8'))

print("Files loaded successfully")

reconstructed = {}

# Process MedAgentBench
print("Processing MedAgentBench...")
medagentbench_tasks = []
for task in sources['tasks_medagentbench']:
    task_id = task['id']
    ticket = task.get('ticket', '')
    known_info = task.get('user_scenario', {}).get('instructions', {}).get('known_info', '')
    
    consultation_task = {
        'id': task_id,
        'task_type': 'core_consultation',
        'consultation_scenario': 'primary_care',
        'question': 'Patient asks: ' + ticket,
        'answer': 'Doctor answers: Please provide the information.',
        'domain': 'clinical/consultation',
        'ticket': ticket,
        'original_format': 'MedAgentBench',
        'description': {
            'purpose': 'Free-form clinical consultation',
            'relevant_policies': None,
            'notes': task.get('description', {}).get('notes', 'Patient information lookup')
        },
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': ticket,
                'domain': 'clinical',
                'reason_for_call': 'Patient consultation',
                'known_info': known_info,
                'unknown_info': None
            }
        },
        'initial_state': None,
        'evaluation_criteria': None,
        'annotations': None
    }
    medagentbench_tasks.append(consultation_task)

reconstructed['medagentbench'] = medagentbench_tasks

# Process MedXpertQA
print("Processing MedXpertQA...")
medxpertqa_tasks = []
medxpertqa_db = sources['db_medxpertqa']['qa_pairs']

for task in sources['tasks_medxpertqa']:
    task_id = task['id']
    ticket = task.get('ticket', '')
    qa_data = medxpertqa_db.get(task_id, {})
    answer = qa_data.get('answer', '')
    medical_task = qa_data.get('medical_task', '')
    
    consultation_task = {
        'id': task_id,
        'task_type': 'core_consultation',
        'consultation_scenario': 'specialist_consultation',
        'question': 'Patient asks: ' + ticket,
        'answer': 'Doctor answers: ' + answer,
        'domain': 'clinical/consultation',
        'ticket': ticket,
        'original_format': 'MedXpertQA',
        'medical_task': medical_task,
        'description': {
            'purpose': 'Medical knowledge QA consultation',
            'relevant_policies': None,
            'notes': 'Medical Task: ' + medical_task
        },
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': ticket,
                'domain': 'clinical',
                'reason_for_call': 'Medical consultation',
                'known_info': task.get('user_scenario', {}).get('instructions', {}).get('known_info', ''),
                'unknown_info': None
            }
        },
        'initial_state': None,
        'evaluation_criteria': None,
        'annotations': None
    }
    medxpertqa_tasks.append(consultation_task)

reconstructed['medxpertqa'] = medxpertqa_tasks

# Process PhysioNet
print("Processing PhysioNet...")
physionet_tasks = []
physionet_db = sources['db_physionet']['qa_pairs']

for i, (qa_id, qa) in enumerate(physionet_db.items(), 1):
    question_text = qa.get('question', '')
    answer_text = qa.get('answer', '')
    patient_id = qa.get('patient_id', '')
    lab_type = qa.get('lab_type', '')
    
    consultation_task = {
        'id': f'physionet_{i:03d}',
        'task_type': 'structured_query',
        'consultation_scenario': 'pre_consultation_data',
        'question': 'Nurse asks: ' + question_text,
        'answer': 'Doctor answers: ' + answer_text,
        'domain': 'clinical/consultation',
        'ticket': question_text,
        'original_format': 'PhysioNet',
        'structured_query': {
            'patient_id': patient_id,
            'indicators': [lab_type],
            'query_type': 'lab_result_lookup'
        },
        'description': {
            'purpose': 'Pre-consultation data retrieval',
            'relevant_policies': None,
            'notes': f'Patient: {patient_id}, Type: {lab_type}'
        },
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': question_text,
                'domain': 'clinical',
                'reason_for_call': 'Patient data lookup',
                'known_info': f'Patient: {patient_id}, Type: {lab_type}',
                'unknown_info': None
            }
        },
        'initial_state': None,
        'evaluation_criteria': None,
        'annotations': None
    }
    physionet_tasks.append(consultation_task)

reconstructed['physionet'] = physionet_tasks

# Process ProdMedBench
print("Processing ProdMedBench...")
prodmedbench_tasks = []
prodmedbench_db = sources['db_prodmedbench']['qa_pairs']

for task in sources['tasks_prodmedbench']:
    task_id = task['id']
    ticket = task.get('ticket', '')
    qa_data = prodmedbench_db.get(task_id, {})
    answer = qa_data.get('answer', '')
    options = qa_data.get('options', '')
    cot = qa_data.get('cot', '')
    
    consultation_task = {
        'id': task_id,
        'task_type': 'mcq_screening',
        'consultation_scenario': 'differential_diagnosis',
        'question': 'Patient asks: ' + ticket,
        'answer': 'Doctor answers: ' + answer,
        'domain': 'clinical/consultation',
        'ticket': ticket,
        'original_format': 'ProdMedBench',
        'options': options,
        'cot': cot,
        'description': {
            'purpose': 'Differential diagnosis MCQ screening',
            'relevant_policies': None,
            'notes': 'Multiple choice with reasoning'
        },
        'user_scenario': {
            'persona': None,
            'instructions': {
                'task_instructions': ticket,
                'domain': 'clinical',
                'reason_for_call': 'Medical consultation',
                'known_info': 'MCQ format',
                'unknown_info': None
            }
        },
        'initial_state': None,
        'evaluation_criteria': None,
        'annotations': None
    }
    prodmedbench_tasks.append(consultation_task)

reconstructed['prodmedbench'] = prodmedbench_tasks

# Write all files
print("Writing output files...")
output_files = {}
for name in ['medagentbench', 'medxpertqa', 'physionet', 'prodmedbench']:
    output_file = base_dir / name / 'consultation_paradigm.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reconstructed[name], f, indent=2, ensure_ascii=False)
    output_files[name] = str(output_file)
    print(f"Created {name}: {len(reconstructed[name])} tasks")

# Create universal template
print("Creating universal template...")
universal_dir = base_dir / 'universal_template'
universal_dir.mkdir(parents=True, exist_ok=True)

universal_template = {
    'unified_consultation_paradigm': {
        'version': '1.0',
        'description': 'Unified medical consultation task paradigm integrating multiple medical datasets',
        'task_types': {
            'core_consultation': 'Free-form doctor-patient dialogue (MedAgentBench/MedXpertQA)',
            'structured_query': 'Pre-consultation data retrieval (PhysioNet)',
            'mcq_screening': 'Differential diagnosis with MCQ (ProdMedBench)'
        },
        'mandatory_fields': {
            'id': 'unique_task_identifier',
            'task_type': 'core_consultation|structured_query|mcq_screening',
            'question': 'consultation_question',
            'answer': 'consultation_answer',
            'domain': 'clinical/consultation'
        },
        'consultation_workflow': {
            'step_1_pre_consultation': 'Structured query to retrieve patient data (PhysioNet)',
            'step_2_consultation': 'Free-form Q&A for diagnosis and treatment (MedAgentBench/MedXpertQA)',
            'step_3_screening': 'MCQ with CoT for differential diagnosis (ProdMedBench)',
            'step_4_resolution': 'Final diagnosis/advice in natural language'
        }
    }
}

template_file = universal_dir / 'universal_consultation_template.json'
with open(template_file, 'w', encoding='utf-8') as f:
    json.dump(universal_template, f, indent=2, ensure_ascii=False)

print("")
print("=" * 50)
print("   RECONSTRUCTION COMPLETE")
print("=" * 50)
print("")
print("Generated Files:")
for name, path in output_files.items():
    print(f"  {name}: {path}")
print("")
print(f"Universal Template: {template_file}")
print("")
print("=" * 50)
print("   TASK COUNTS")
print("=" * 50)
counts = {name: len(tasks) for name, tasks in reconstructed.items()}
for name, count in counts.items():
    print(f"  {name}: {count} tasks")
print("")
core_total = counts['medagentbench'] + counts['medxpertqa']
supp_total = counts['physionet'] + counts['prodmedbench']
all_total = core_total + supp_total
print(f"  Total Core Consultation: {core_total}")
print(f"  Total Supplementary: {supp_total}")
print(f"  Total All Tasks: {all_total}")
print("=" * 50)
