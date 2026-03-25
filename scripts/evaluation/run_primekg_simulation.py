#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run agent simulation on PrimeKG tasks
"""

import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, 'src')

from tau2.run import run_tasks, get_tasks
from tau2.evaluator.evaluator import EvaluationType


def run_primekg_simulation(
    num_tasks: int = 3,
    agent: str = "llm_agent_solo",
    model: str = "gpt-4o-mini",
    save_results: bool = True,
):
    """
    Run agent simulation on PrimeKG tasks

    Args:
        num_tasks: Number of tasks to run (default: 3)
        agent: Agent type (default: llm_agent_solo)
        model: LLM model to use (default: gpt-4o-mini)
        save_results: Whether to save results to file
    """
    print("="*70)
    print(" PrimeKG Agent Simulation")
    print("="*70)

    # Configuration
    print(f"\nConfiguration:")
    print(f"  Domain: primekg")
    print(f"  Agent: {agent}")
    print(f"  Model: {model}")
    print(f"  Number of tasks: {num_tasks}")

    # Load tasks
    print(f"\nLoading PrimeKG tasks...")
    try:
        tasks = get_tasks('primekg')
        print(f"  [OK] Loaded {len(tasks)} tasks")

        # Select first N tasks
        selected_tasks = tasks[:num_tasks]
        print(f"  Selected {len(selected_tasks)} tasks for simulation")
        for i, task in enumerate(selected_tasks, 1):
            print(f"    {i}. {task.id} - {task.ticket}")

    except Exception as e:
        print(f"  [FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

    # Create output directory
    if save_results:
        output_dir = Path("results/primekg")
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"simulation_{timestamp}.json"

        print(f"\nOutput will be saved to:")
        print(f"  {output_file}")

    # Run simulation
    print(f"\n{'='*70}")
    print(f" Running Simulation")
    print(f"{'='*70}")

    try:
        # LLM arguments for agent (model should not be in llm_args)
        llm_args_agent = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "timeout": 60,
        }

        # LLM arguments for user (empty for dummy_user)
        llm_args_user = {}

        # Run tasks
        results = run_tasks(
            domain="primekg",
            tasks=selected_tasks,
            agent=agent,
            user="dummy_user",  # Use dummy user for solo mode
            llm_agent=model,  # Model name goes here, not in llm_args_agent
            llm_args_agent=llm_args_agent,
            llm_user=None,
            llm_args_user=llm_args_user,
            num_trials=1,
            max_steps=20,
            max_errors=5,
            save_to=str(output_file) if save_results else None,
            console_display=True,
            evaluation_type=EvaluationType.ALL,
            max_concurrency=1,
            seed=42,
            log_level="INFO",
        )

        # Display results
        print(f"\n{'='*70}")
        print(f" Simulation Complete!")
        print(f"{'='*70}")

        print(f"\nResults:")
        print(f"  Total simulations: {len(results.simulations)}")
        print(f"  Tasks completed: {len([s for s in results.simulations if s.error is None])}")
        print(f"  Tasks failed: {len([s for s in results.simulations if s.error is not None])}")

        # Display rewards
        print(f"\nRewards:")
        for sim in results.simulations:
            if sim.error is None:
                reward = sim.reward_info.total_reward if sim.reward_info else "N/A"
                print(f"  {sim.task_id}: {reward}")

        # Save summary
        if save_results:
            summary_file = output_dir / f"summary_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"PrimeKG Simulation Summary\n")
                f.write(f"="*70 + "\n\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Model: {model}\n")
                f.write(f"Agent: {agent}\n")
                f.write(f"Tasks: {len(selected_tasks)}\n\n")
                f.write(f"Results:\n")
                f.write(f"  Total simulations: {len(results.simulations)}\n")
                f.write(f"  Completed: {len([s for s in results.simulations if s.error is None])}\n")
                f.write(f"  Failed: {len([s for s in results.simulations if s.error is not None])}\n\n")

                for sim in results.simulations:
                    f.write(f"\nTask: {sim.task_id}\n")
                    f.write(f"  Status: {'Success' if sim.error is None else 'Failed'}\n")
                    if sim.error:
                        f.write(f"  Error: {sim.error}\n")
                    if sim.reward_info:
                        f.write(f"  Total Reward: {sim.reward_info.total_reward}\n")

            print(f"\nSummary saved to:")
            print(f"  {summary_file}")

        print(f"\n{'='*70}")
        print(f" [SUCCESS] Simulation completed successfully!")
        print(f"{'='*70}")

        if save_results:
            print(f"\nResults saved to:")
            print(f"  {output_file}")
            print(f"  {summary_file}")

        return True

    except Exception as e:
        print(f"\n[FAIL] Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Run agent simulation on PrimeKG tasks")
    parser.add_argument("--num-tasks", type=int, default=3, help="Number of tasks to run")
    parser.add_argument("--agent", type=str, default="llm_agent_solo", help="Agent type")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="LLM model")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")

    args = parser.parse_args()

    return run_primekg_simulation(
        num_tasks=args.num_tasks,
        agent=args.agent,
        model=args.model,
        save_results=not args.no_save,
    )


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
