#!/usr/bin/env python3
"""
Command-line interface for the medical dialogue validator.

Example:
    python -m DataValidator data/tau2/domains/clinical/tasks.json
    python -m DataValidator data/tau2/domains/clinical/tasks.json --strict
    python -m DataValidator data/tau2/domains/clinical/tasks.json --json-output result.json
"""

import argparse
import json
import sys
from pathlib import Path

from .core import MedicalDialogueValidator


def main():
    """Command-line interface for the validator."""
    parser = argparse.ArgumentParser(
        description="Validate medical consultation dialogue datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data/tau2/domains/clinical/tasks.json
  %(prog)s data/tau2/domains/clinical/tasks.json --strict
  %(prog)s data/tau2/domains/clinical/tasks.json --quiet
  %(prog)s data/tau2/domains/clinical/tasks.json --json-output result.json
  %(prog)s --show-keywords

For more information, see:
  https://github.com/circadiancity/agentmy/blob/main/DATA_VALIDATOR_README.md
        """
    )

    parser.add_argument(
        "dataset_path",
        type=str,
        nargs='?',  # Optional for --show-keywords
        help="Path to the dataset JSON file to validate"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (warnings become errors)"
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors and warnings, not info"
    )

    parser.add_argument(
        "--json-output",
        type=str,
        metavar="FILE",
        help="Save validation result to JSON file"
    )

    parser.add_argument(
        "--show-keywords",
        action="store_true",
        help="Show information about loaded medical keywords"
    )

    args = parser.parse_args()

    # Show keyword info if requested
    if args.show_keywords:
        keyword_info = MedicalDialogueValidator.get_keyword_info()
        print("\n" + "=" * 60)
        print("  MEDICAL KEYWORDS INFORMATION")
        print("=" * 60)
        print(f"\nTotal Keywords: {keyword_info['total_keywords']:,}")
        print(f"Categories: {keyword_info['categories']}")
        print("\nKeyword Categories Include:")
        print("  - Symptoms (general, respiratory, skin, digestive, etc.)")
        print("  - Medical terms (roles, concepts, medications)")
        print("  - Departments (cardiology, neurology, etc.)")
        print("  - Diseases (cardiovascular, respiratory, etc.)")
        print("  - TCM terms (Traditional Chinese Medicine)")
        print("  - Body parts and organs")
        print("  - Medical settings and scenarios")
        print()
        return 0

    # Check if dataset path is provided
    if not args.dataset_path:
        parser.print_help()
        print("\n❌ Error: Please provide a dataset path or use --show-keywords")
        return 1

    # Initialize validator
    validator = MedicalDialogueValidator(strict_mode=args.strict)

    # Validate dataset
    data_path = Path(args.dataset_path)
    result = validator.validate_dataset(data_path)

    # Print report
    result.print_report(verbose=not args.quiet)

    # Save JSON output if requested
    if args.json_output:
        output_path = Path(args.json_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_dict = result.to_dict()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_dict, f, indent=2, ensure_ascii=False)

        print(f"Validation result saved to: {output_path}")

    # Exit code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
