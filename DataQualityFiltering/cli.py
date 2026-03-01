"""CLI entry point for DataQualityFiltering."""

import argparse
import sys

from DataQualityFiltering.models import FilterConfig
from DataQualityFiltering.pipeline import DataQualityPipeline


def main():
    parser = argparse.ArgumentParser(
        description="DataQualityFiltering: Review and filter clinical benchmark tasks."
    )
    parser.add_argument(
        "--tasks-path",
        required=True,
        help="Path to input tasks.json file.",
    )
    parser.add_argument(
        "--output-path",
        default="filtered_output",
        help="Directory for output files (default: filtered_output).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=3.0,
        help="Minimum overall score to accept a task, 0-5 (default: 3.0).",
    )
    parser.add_argument(
        "--review-mode",
        choices=["human", "semi_auto", "both"],
        default="semi_auto",
        help="Review mode (default: semi_auto).",
    )
    parser.add_argument(
        "--llm-model",
        default="gpt-4o-mini",
        help="LLM model for automated review (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--guidance-path",
        default=None,
        help="Path to custom guidance prompt file for LLM review.",
    )
    parser.add_argument(
        "--human-scores-path",
        default=None,
        help="Path to pre-existing human scores JSON file.",
    )

    args = parser.parse_args()

    config = FilterConfig(
        threshold=args.threshold,
        review_mode=args.review_mode,
        llm_model=args.llm_model,
        guidance_path=args.guidance_path,
    )

    pipeline = DataQualityPipeline(config)
    output_dir = pipeline.run_and_save(
        tasks_path=args.tasks_path,
        output_path=args.output_path,
        human_scores_path=args.human_scores_path,
    )

    print(f"Output written to: {output_dir}")
    print(f"  - tasks_filtered.json")
    print(f"  - review_scores.json")
    if args.review_mode == "both":
        print(f"  - calibration_report.json")


if __name__ == "__main__":
    main()
