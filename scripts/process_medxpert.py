import json
import sys
from pathlib import Path

# Input/Output paths
input_file = r"C:\Users\方正\tau2-bench\data\raw\MedXpertQA\eval\data\medxpertqa\input\medxpertqa_text_input.jsonl"
output_dir = Path(r"C:\Users\方正\tau2-bench\data\processed\medxpertqa")
tasks_output = output_dir / "tasks.json"
db_output = output_dir / "db.json"

# Create output directory
output_dir.mkdir(parents=True, exist_ok=True)

# Read JSONL
entries = []
with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            entries.append(json.loads(line))

print(f"Loaded {len(entries)} entries")

# Generate tasks.json
tasks = []
for i, entry in enumerate(entries):
    task_id = f"medxpertqa_{i+1:03d}"
    question = entry.get("question", "")
    medical_task = entry.get("medical_task", "")
    body_system = entry.get("body_system", "")
    question_type = entry.get("question_type", "")
    
    # Build ticket with fallback
    ticket = question
    if not ticket.endswith("Not found"):
        ticket = f"{ticket} If the answer does not exist, the answer should be 'Not found'"
    
    # Build known_info and notes
    known_info_parts = []
    notes_parts = []
    if medical_task:
        known_info_parts.append(f"Task Type: {medical_task}")
        notes_parts.append(f"Task: {medical_task}")
    if body_system:
        known_info_parts.append(f"Body System: {body_system}")
        notes_parts.append(f"System: {body_system}")
    if question_type:
        known_info_parts.append(f"Question Type: {question_type}")
    
    known_info = ", ".join(known_info_parts) if known_info_parts else None
    notes = ", ".join(notes_parts) if notes_parts else None
    
    task = {
        "id": task_id,
        "description": {
            "purpose": "Medical knowledge QA",
            "relevant_policies": None,
            "notes": notes
        },
        "user_scenario": {
            "persona": None,
            "instructions": {
                "task_instructions": ticket,
                "domain": "clinical",
                "reason_for_call": "Medical consultation",
                "known_info": known_info,
                "unknown_info": None
            }
        },
        "ticket": ticket,
        "initial_state": None,
        "evaluation_criteria": None,
        "annotations": None
    }
    tasks.append(task)

# Generate db.json
qa_pairs = {}
for i, entry in enumerate(entries):
    task_id = f"medxpertqa_{i+1:03d}"
    question = entry.get("question", "")
    
    # Find answer
    label = entry.get("label", [])
    options = entry.get("options", [])
    answer = "Not found"
    if label and options:
        for opt in options:
            if opt.get("letter") == label[0]:
                answer = opt.get("content", "Not found")
                break
    
    qa_pair = {
        "id": f"qa_{task_id}",
        "question": question,
        "answer": answer,
        "task_id": task_id
    }
    
    # Add optional fields
    if entry.get("medical_task"):
        qa_pair["medical_task"] = entry["medical_task"]
    if entry.get("body_system"):
        qa_pair["body_system"] = entry["body_system"]
    if entry.get("question_type"):
        qa_pair["question_type"] = entry["question_type"]
    
    qa_pairs[task_id] = qa_pair

db_data = {"qa_pairs": qa_pairs}

# Write files
with open(tasks_output, 'w', encoding='utf-8') as f:
    json.dump(tasks, f, indent=2, ensure_ascii=False)

with open(db_output, 'w', encoding='utf-8') as f:
    json.dump(db_data, f, indent=2, ensure_ascii=False)

print(f"Created {tasks_output}")
print(f"Created {db_output}")
print(f"Tasks: {len(tasks)}, QA pairs: {len(qa_pairs)}")
print("Processing complete!")
