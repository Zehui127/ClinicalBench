#!/usr/bin/env python3
"""
Simple tau2 evaluation script for clinical consultation tasks.

This script runs a tau2 evaluation on clinical tasks with configurable parameters.
"""

import sys
from pathlib import Path

# Add tau2 to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Run tau2 evaluation."""
    import argparse
    import json
    import os
    from pathlib import Path
    from tau2.run import run_tasks
    from tau2.data_model.tasks import Task

    parser = argparse.ArgumentParser(description="Run tau2 clinical evaluation")
    parser.add_argument("--domain", default="clinical_neurology",
                       help="Clinical domain to evaluate")
    parser.add_argument("--max-tasks", type=int, default=1,
                       help="Maximum number of tasks to evaluate")
    parser.add_argument("--max-rounds", type=int, default=3,
                       help="Maximum rounds per task")
    parser.add_argument("--data-dir", default="./data",
                       help="Data directory path")
    parser.add_argument("--agent", default="llm_agent",
                       help="Agent type to use")
    parser.add_argument("--user", default="user_simulator",
                       help="User simulator type")
    parser.add_argument("--agent-model", default="gpt-4",
                       help="Model for agent")
    parser.add_argument("--user-model", default="gpt-4",
                       help="Model for user simulator")
    parser.add_argument("--api-key", default=None,
                       help="OpenAI API key (defaults to OPENAI_API_KEY env variable)")

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OpenAI API key not found. Please set OPENAI_API_KEY environment variable or use --api-key argument.")
        return 1

    print("="*70)
    print("TAU2 CLINICAL EVALUATION")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Domain: {args.domain}")
    print(f"  Max tasks: {args.max_tasks}")
    print(f"  Max rounds: {args.max_rounds}")
    print(f"  Agent: {args.agent} (model: {args.agent_model})")
    print(f"  User: {args.user} (model: {args.user_model})")
    print(f"  Data directory: {args.data_dir}")

    # Load tasks
    tasks_file = Path(args.data_dir) / "tau2" / "domains" / args.domain / "tasks.json"

    print(f"\nLoading tasks from: {tasks_file}")

    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks_data = json.load(f)

    print(f"Loaded {len(tasks_data)} tasks")

    # Convert to Task objects
    tasks = [Task(**task_data) for task_data in tasks_data[:args.max_tasks]]

    print(f"Evaluating {len(tasks)} task(s)")

    print("\n" + "-"*70)
    print("Starting evaluation...")
    print("-"*70 + "\n")

    # Run the simulation
    try:
        result = run_tasks(
            domain=args.domain,
            tasks=tasks,
            agent=args.agent,
            user=args.user,
            llm_agent=args.agent_model,
            llm_user=args.user_model,
            llm_args_agent={"api_key": api_key},
            llm_args_user={"api_key": api_key},
            max_steps=args.max_rounds,
            num_trials=1,
            console_display=True,
        )

        print("\n" + "="*70)
        print("EVALUATION COMPLETE")
        print("="*70)
        print(f"\nResult type: {type(result)}")
        print(f"Result keys: {result.model_fields if hasattr(result, 'model_fields') else 'N/A'}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
