"""CLI entry point for UniClinicalDataEngine."""

import argparse
import json
import sys

from UniClinicalDataEngine.engine import UniClinicalDataEngine
from UniClinicalDataEngine.models import EngineConfig


def main():
    parser = argparse.ArgumentParser(
        description="UniClinicalDataEngine: Convert raw clinical data to tau2-bench task sets."
    )
    parser.add_argument(
        "--source-type",
        required=True,
        choices=["nhands", "csv", "json"],
        help="Type of data source adapter to use.",
    )
    parser.add_argument(
        "--source-path",
        required=True,
        help="Path to the source data file.",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for output files (default: output).",
    )
    parser.add_argument(
        "--domain-name",
        default="clinical",
        help="Domain name for tau2 tasks (default: clinical).",
    )
    parser.add_argument(
        "--adapter-kwargs",
        default=None,
        help='Additional adapter kwargs as JSON string (e.g., \'{"column_mapping": {...}}\').',
    )

    args = parser.parse_args()

    adapter_kwargs = None
    if args.adapter_kwargs:
        try:
            adapter_kwargs = json.loads(args.adapter_kwargs)
        except json.JSONDecodeError as e:
            print(f"Error parsing --adapter-kwargs: {e}", file=sys.stderr)
            sys.exit(1)

    config = EngineConfig(
        source_type=args.source_type,
        source_path=args.source_path,
        output_dir=args.output_dir,
        domain_name=args.domain_name,
        adapter_kwargs=adapter_kwargs,
    )

    engine = UniClinicalDataEngine(config)
    output_dir = engine.run_and_save()

    print(f"Output written to: {output_dir}")
    print(f"  - tasks.json")
    print(f"  - db.json")
    print(f"  - policy.md")
    print(f"  - tools.json")


if __name__ == "__main__":
    main()
