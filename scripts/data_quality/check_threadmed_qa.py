#!/usr/bin/env python3
"""
ThReadMed-QA Availability Checker

This script checks if the ThReadMed-QA dataset is available
and provides download instructions.
"""

import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_dataset_status():
    """Check if ThReadMed-QA dataset is downloaded."""
    project_root = Path(__file__).parent
    raw_dir = project_root / "data" / "raw" / "medical_dialogues" / "threadmed_qa"

    print("\n" + "=" * 60)
    print("  ThReadMed-QA Dataset Status Check")
    print("=" * 60)

    print(f"\nTarget directory: {raw_dir}")

    if not raw_dir.exists():
        print("\n❌ Directory does not exist")
        print("\n📋 Action Required:")
        print("   1. Open: https://github.com/monicamunnangi/ThReadMed-QA")
        print("   2. Download ZIP or clone repository")
        print(f"   3. Extract to: {raw_dir}")
        return False

    # Check if directory has content
    files = list(raw_dir.glob("*"))
    files = [f for f in files if f.name != ".git"]

    if not files:
        print("\n⚠️  Directory exists but is empty")
        print("\n📋 Action Required:")
        print("   1. Open: https://github.com/monicamunnangi/ThReadMed-QA")
        print("   2. Download ZIP or clone repository")
        print(f"   3. Extract to: {raw_dir}")
        return False

    # Check for expected files
    print(f"\n✓ Directory exists with {len(files)} items")

    # Look for data files
    json_files = list(raw_dir.rglob("*.json"))
    data_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name != ".git"]

    if json_files:
        print(f"\n✓ Found {len(json_files)} JSON file(s)")
        for f in json_files[:5]:
            size = f.stat().st_size
            print(f"  - {f.relative_to(raw_dir)} ({size:,} bytes)")
    else:
        print("\n⚠️  No JSON files found")

    if data_dirs:
        print(f"\n✓ Found {len(data_dirs)} subdirector{ies}:" if len(data_dirs) != 1 else "\n✓ Found 1 subdirectory:")
        for d in data_dirs[:5]:
            print(f"  - {d.name}/")

    # Check if conversion ready
    print("\n📊 Dataset Status:")

    has_data = len(json_files) > 0 or len(data_dirs) > 0

    if has_data:
        print("  ✓ Dataset downloaded")
        print("\n🚀 Next Step:")
        print("   python convert_threadmed_qa.py")
        return True
    else:
        print("  ✗ Dataset not downloaded")
        print("\n📋 Download Instructions:")
        print("\n   Option 1 - Git Clone:")
        print(f"     cd {raw_dir}")
        print("     git clone https://github.com/monicamunnangi/ThReadMed-QA.git .")
        print("\n   Option 2 - Manual Download:")
        print("     1. Visit: https://github.com/monicamunnangi/ThReadMed-QA")
        print("     2. Click 'Code' → 'Download ZIP'")
        print(f"     3. Extract to: {raw_dir}")
        return False

def main():
    """Main function."""
    try:
        ready = check_dataset_status()

        print("\n" + "=" * 60)

        if ready:
            print("\n✅ Dataset is ready for conversion!")
        else:
            print("\n⚠️  Please download the dataset first")
            print("\n📖 See THREADMED_QA_DOWNLOAD_GUIDE.md for details")

        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error checking status: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
