#!/usr/bin/env python3
"""
Convert ThReadMed-QA Dataset to Tau2-Bench Format

This script converts real multi-turn medical dialogues from Reddit r/AskDocs
into tau2-bench format.

Dataset: ThReadMed-QA
Source: https://github.com/monicamunnangi/ThReadMed-QA
Paper: https://arxiv.org/html/2603.11281v1

Author: Claude Sonnet 4.5
Date: 2025-03-13
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class ThReadMedQAConverter:
    """Convert ThReadMed-QA multi-turn dialogues to tau2-bench format."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the converter.

        Args:
            config: Optional configuration with keys:
                - max_conversations: Maximum number of conversations to convert
                - max_turns: Maximum turns per conversation
                - split_ratio: Train/val/test split ratio (default: 0.8/0.1/0.1)
        """
        self.config = config or {}
        self.max_conversations = self.config.get("max_conversations", None)
        self.max_turns = self.config.get("max_turns", None)
        self.split_ratio = self.config.get("split_ratio", [0.8, 0.1, 0.1])

        # Statistics
        self.stats = defaultdict(int)

    def load_data(self, data_dir: Path) -> List[Dict[str, Any]]:
        """Load ThReadMed-QA dataset from directory.

        Args:
            data_dir: Path to the ThReadMed-QA directory

        Returns:
            List of conversation records
        """
        conversations = []

        # Look for JSON files
        json_files = list(data_dir.glob("**/*.json"))

        if not json_files:
            print(f"\nERROR: No JSON files found in {data_dir}")
            print("\nExpected file structure:")
            print("  ThReadMed-QA/")
            print("  ├── data/")
            print("  │   ├── train.json")
            print("  │   ├── val.json")
            print("  │   └── test.json")
            print("  └── README.md")
            return []

        print(f"\nFound {len(json_files)} JSON files")

        for json_file in json_files:
            print(f"  Loading {json_file.name}...")

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle different file formats
                if isinstance(data, list):
                    conversations.extend(data)
                elif isinstance(data, dict):
                    if "conversations" in data:
                        conversations.extend(data["conversations"])
                    elif "data" in data:
                        conversations.extend(data["data"])

                self.stats[f"loaded_{json_file.stem}"] = len(conversations)

            except Exception as e:
                print(f"    Error reading {json_file.name}: {e}")
                continue

        # Limit conversations if specified
        if self.max_conversations and len(conversations) > self.max_conversations:
            conversations = conversations[:self.max_conversations]

        print(f"\nTotal conversations loaded: {len(conversations)}")
        return conversations

    def convert_to_tau2(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert conversations to tau2-bench format.

        Args:
            conversations: List of conversation records

        Returns:
            List of tau2 task dictionaries
        """
        tau2_tasks = []

        print("\nConverting to tau2-bench format...")

        for i, conv in enumerate(conversations):
            try:
                tau2_task = self._conversation_to_tau2(conv, i)
                tau2_tasks.append(tau2_task)

                if (i + 1) % 100 == 0:
                    print(f"  Converted {i + 1}/{len(conversations)} tasks")

            except Exception as e:
                print(f"  Error converting conversation {i}: {e}")
                continue

        print(f"\nSuccessfully converted {len(tau2_tasks)} tasks")
        return tau2_tasks

    def _conversation_to_tau2(self, conversation: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """Convert a single conversation to tau2 format.

        Args:
            conversation: Conversation record
            idx: Index

        Returns:
            Tau2 task dictionary
        """
        # Extract conversation data
        # Adapt this based on actual data format from GitHub
        conv_id = conversation.get("id", f"threadmed_{idx}")

        # Extract turns (question-answer pairs)
        turns = conversation.get("turns", conversation.get("qa_pairs", []))

        # Limit turns if specified
        if self.max_turns and len(turns) > self.max_turns:
            turns = turns[:self.max_turns]

        # Build dialogue from turns
        dialogue_messages = []
        for turn_idx, turn in enumerate(turns):
            question = turn.get("question", turn.get("patient_question", ""))
            answer = turn.get("answer", turn.get("physician_response", ""))

            if question:
                dialogue_messages.append({
                    "role": "user",
                    "content": question,
                    "turn": turn_idx * 2
                })

            if answer:
                dialogue_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "turn": turn_idx * 2 + 1
                })

        # Get first question as the ticket/chief complaint
        first_question = turns[0].get("question", turns[0].get("patient_question", "")) if turns else ""

        # Build user scenario
        user_scenario = {
            "persona": "Patient seeking medical advice from an online physician community",
            "instructions": {
                "domain": "medical_consultation",
                "reason_for_call": first_question[:100] if first_question else "Medical consultation",
                "known_info": turns[0].get("question", "")[:200] if turns else "",
                "unknown_info": None,
                "task_instructions": self._build_task_instructions(dialogue_messages),
            }
        }

        # Build description
        description = {
            "purpose": f"Multi-turn medical consultation from Reddit r/AskDocs",
            "relevant_policies": None,
            "notes": f"Real patient-physician dialogue from ThReadMed-QA dataset. Thread ID: {conv_id}. Turns: {len(turns)}",
        }

        # Build ticket
        ticket = first_question[:200] if first_question else "Medical consultation request"

        # Build initial state
        initial_state = {
            "initialization_actions": [
                {
                    "env_type": "user",
                    "func_name": "set_user_info",
                    "arguments": {
                        "name": "Reddit User",
                        "patient_id": conv_id,
                        "platform": "AskDocs",
                        "anonymized": True,
                    }
                }
            ]
        }

        # Build evaluation criteria
        evaluation_criteria = {
            "actions": [
                {
                    "action_id": "provide_medical_advice",
                    "requestor": "assistant",
                    "name": "provide_medical_advice",
                    "arguments": {
                        "should_be_clinically_accurate": True,
                        "should_address_patient_concerns": True,
                        "should_include_safety_warnings": True,
                    }
                }
            ],
            "communication_checks": [
                {
                    "check_id": "empathetic_response",
                    "criteria": "Response should be empathetic and professional"
                },
                {
                    "check_id": "appropriate_urgency",
                    "criteria": "Should correctly assess urgency of the situation"
                }
            ]
        }

        return {
            "id": conv_id,
            "description": description,
            "user_scenario": user_scenario,
            "ticket": ticket,
            "initial_state": initial_state,
            "evaluation_criteria": evaluation_criteria,
            "metadata": {
                "source": "ThReadMed-QA",
                "platform": "Reddit r/AskDocs",
                "num_turns": len(turns),
                "original_conversation": conversation,
            }
        }

    def _build_task_instructions(self, dialogue_messages: List[Dict]) -> str:
        """Build task instructions from dialogue messages.

        Args:
            dialogue_messages: List of dialogue messages

        Returns:
            Task instructions string
        """
        if not dialogue_messages:
            return "Engage in a medical consultation with the patient."

        instructions = ["You are a physician responding to a patient's medical question on an online forum."]
        instructions.append("\nThe conversation will unfold as follows:\n")

        for msg in dialogue_messages:
            role_name = "Patient" if msg["role"] == "user" else "Physician"
            instructions.append(f"{role_name}: {msg['content']}")
            instructions.append("")

        return "\n".join(instructions)

    def save_tasks(self, tasks: List[Dict[str, Any]], output_dir: Path) -> None:
        """Save converted tasks to output directory.

        Args:
            tasks: List of tau2 tasks
            output_dir: Output directory path
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into train/val/test
        n_tasks = len(tasks)
        train_end = int(n_tasks * self.split_ratio[0])
        val_end = train_end + int(n_tasks * self.split_ratio[1])

        train_tasks = tasks[:train_end]
        val_tasks = tasks[train_end:val_end]
        test_tasks = tasks[val_end:]

        # Save all tasks
        tasks_file = output_dir / "tasks.json"
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(tasks)} tasks to {tasks_file}")

        # Save train/val/test splits
        for split_name, split_tasks in [("train", train_tasks), ("val", val_tasks), ("test", test_tasks)]:
            split_file = output_dir / f"tasks_{split_name}.json"
            with open(split_file, "w", encoding="utf-8") as f:
                json.dump(split_tasks, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(split_tasks)} {split_name} tasks to {split_file}")

        # Create split_tasks.json
        split_data = {
            "train": [task["id"] for task in train_tasks],
            "validation": [task["id"] for task in val_tasks],
            "test": [task["id"] for task in test_tasks]
        }

        split_file = output_dir / "split_tasks.json"
        with open(split_file, "w", encoding="utf-8") as f:
            json.dump(split_data, f, indent=2)
        print(f"Saved train/val/test split to {split_file}")

    def generate_db(self, tasks: List[Dict[str, Any]], output_dir: Path) -> None:
        """Generate database from tasks.

        Args:
            tasks: List of tau2 tasks
            output_dir: Output directory path
        """
        patients = {}

        for task in tasks:
            task_id = task["id"]
            init_actions = task.get("initial_state", {}).get("initialization_actions", [])
            if init_actions:
                patient_info = init_actions[0].get("arguments", {})
                patient_id = patient_info.get("patient_id", task_id)

                if patient_id not in patients:
                    patients[patient_id] = {
                        "patient_id": patient_id,
                        "platform": patient_info.get("platform", "AskDocs"),
                        "anonymized": patient_info.get("anonymized", True),
                        "chief_complaint": task.get("ticket", ""),
                        "num_turns": task["metadata"].get("num_turns", 0),
                    }

        db_file = output_dir / "db.json"
        db_data = {"patients": patients}

        with open(db_file, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=2, ensure_ascii=False)

        print(f"Saved database with {len(patients)} patients to {db_file}")

    def print_statistics(self) -> None:
        """Print conversion statistics."""
        print("\n" + "=" * 70)
        print("  CONVERSION STATISTICS")
        print("=" * 70)

        for key, value in sorted(self.stats.items()):
            print(f"  {key}: {value}")

        print("=" * 70 + "\n")


def main():
    """Main conversion function."""
    print("\n" + "=" * 70)
    print("  THREADMED-QA TO TAU2-BENCH CONVERSION")
    print("=" * 70)

    # Configuration
    config = {
        "max_conversations": None,  # Convert all conversations
        "max_turns": None,  # Keep all turns
        "split_ratio": [0.8, 0.1, 0.1],  # 80/10/10 split
    }

    # Paths
    data_dir = project_root / "data" / "raw" / "medical_dialogues" / "threadmed_qa" / "data"
    output_dir = project_root / "data" / "tau2" / "domains" / "clinical" / "threadmed_qa"

    print(f"\nInput directory: {data_dir}")
    print(f"Output directory: {output_dir}")

    # Check input directory
    if not data_dir.exists():
        print(f"\nERROR: Input directory not found: {data_dir}")
        print("\nPlease download ThReadMed-QA dataset first:")
        print("1. Visit: https://github.com/monicamunnangi/ThReadMed-QA")
        print("2. Download the repository")
        print(f"3. Extract to: {project_root / 'data/raw/medical_dialogues/threadmed_qa/'}")
        return

    # Initialize converter
    converter = ThReadMedQAConverter(config)

    # Load data
    print("\nStep 1: Loading ThReadMed-QA conversations...")
    conversations = converter.load_data(data_dir)

    if not conversations:
        print("\nERROR: No conversations loaded!")
        return

    # Convert to tau2 format
    print("\nStep 2: Converting to tau2-bench format...")
    tau2_tasks = converter.convert_to_tau2(conversations)

    # Save results
    print("\nStep 3: Saving results...")
    converter.save_tasks(tau2_tasks, output_dir)
    converter.generate_db(tau2_tasks, output_dir)

    # Print statistics
    converter.print_statistics()

    print("=" * 70)
    print("  CONVERSION COMPLETE")
    print("=" * 70)
    print(f"\nOutput files saved to: {output_dir}")
    print(f"  - tasks.json (all tasks)")
    print(f"  - tasks_train.json, tasks_val.json, tasks_test.json (splits)")
    print(f"  - db.json (patient database)")
    print(f"  - split_tasks.json (train/val/test IDs)")
    print()


if __name__ == "__main__":
    main()
