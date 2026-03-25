#!/usr/bin/env python3
"""
Create sample ThReadMed-QA data for testing conversion script.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def create_sample_conversations(n: int = 10) -> List[Dict[str, Any]]:
    templates = [
        {
            "topic": "headache",
            "qa_pairs": [
                {
                    "question": "I've been having frequent headaches for the past week. They're mostly on the right side of my head and get worse when I move my eyes. Should I be worried?",
                    "answer": "Headaches that are worse with eye movement can have several causes. How old are you, and do you have any other symptoms like nausea, sensitivity to light, or vision changes?"
                },
                {
                    "question": "I'm 32 years old. I do feel some nausea when the pain is bad, and bright lights bother me. I've also been under a lot of stress at work lately.",
                    "answer": "Your description is quite consistent with migraine headaches. For now, rest in a dark room, stay hydrated, and consider over-the-counter pain relievers if you have no contraindications."
                },
                {
                    "question": "Thank you. When should I go to the ER versus waiting for a regular appointment?",
                    "answer": "Go to the ER immediately if you experience: sudden thunderclap headache, fever with stiff neck, confusion or difficulty speaking, weakness on one side of your body."
                }
            ]
        },
        {
            "topic": "rash",
            "qa_pairs": [
                {
                    "question": "My 5-year-old developed a red rash on her arms and legs yesterday. It doesn't seem to itch much but she's been running a low-grade fever. Could this be an allergy?",
                    "answer": "A rash with fever in a child has several possibilities. Viral exanthems are very common at this age."
                },
                {
                    "question": "She's a bit more tired than usual but still playing. No new foods or medicines that I can think of. The rash looks like small red spots, some slightly raised.",
                    "answer": "The description sounds like it could be a viral rash. I'd recommend urgent evaluation if: she develops a high fever, the spots become purple or don't blanch when pressed."
                }
            ]
        },
        {
            "topic": "chest_pain",
            "qa_pairs": [
                {
                    "question": "For the past three days, I've been having mild chest pain that comes and goes. It's mostly on the left side and sometimes feels like burning. Is this acid reflux?",
                    "answer": "Left-sided chest pain can have many causes. The burning quality does suggest gastrointestinal reflux disease as a possibility."
                },
                {
                    "question": "I'm 48, smoker for 20 years. No history of heart problems. The pain does get worse after spicy meals. No shortness of breath. Sometimes I feel it in my left shoulder too.",
                    "answer": "You should seek medical attention today. At minimum, you need an ECG to rule out cardiac involvement. Don't delay given your risk factors."
                }
            ]
        }
    ]

    conversations = []
    for i in range(n):
        template = templates[i % len(templates)]
        conv = {
            "id": f"threadmed_sample_{i+1}",
            "turns": template["qa_pairs"],
            "topic": template["topic"],
            "metadata": {
                "source": "sample_data",
                "num_qa_pairs": len(template["qa_pairs"]),
                "created_for": "testing_conversion_pipeline"
            }
        }
        conversations.append(conv)

    return conversations


def main():
    print("=" * 70)
    print("  CREATE SAMPLE THREADMED-QA DATA")
    print("=" * 70)

    raw_dir = Path("data/raw/medical_dialogues/threadmed_qa/data")
    raw_dir.mkdir(parents=True, exist_ok=True)

    print("Creating sample conversations...")
    train_convs = create_sample_conversations(8)
    val_convs = create_sample_conversations(1)
    test_convs = create_sample_conversations(1)

    for split_name, convs in [("train", train_convs), ("val", val_convs), ("test", test_convs)]:
        output_file = raw_dir / f"{split_name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(convs, f, indent=2, ensure_ascii=False)
        print(f"  Saved {len(convs)} conversations to {output_file}")

    all_convs = train_convs + val_convs + test_convs
    combined_file = raw_dir / "all.json"
    with open(combined_file, "w", encoding="utf-8") as f:
        json.dump(all_convs, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(all_convs)} total conversations to {combined_file}")

    print("=" * 70)
    print("  SAMPLE DATA CREATED")
    print("=" * 70)
    print(f"Data saved to: {raw_dir}")
    print("You can now run: python convert_threadmed_qa.py")


if __name__ == "__main__":
    main()
