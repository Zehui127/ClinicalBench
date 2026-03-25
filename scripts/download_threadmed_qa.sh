#!/bin/bash
# ThReadMed-QA Dataset Download Script
# This script attempts multiple methods to download the dataset

set -e

TARGET_DIR="data/raw/medical_dialogues/threadmed_qa"
REPO_URL="https://github.com/monicamunnangi/ThReadMed-QA.git"
REPO_ZIP="https://github.com/monicamunnangi/ThReadMed-QA/archive/refs/heads/main.zip"

echo "=========================================="
echo "  ThReadMed-QA Dataset Download Script"
echo "=========================================="
echo ""
echo "Target directory: $TARGET_DIR"
echo ""

# Create target directory
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Method 1: Git clone
echo "Method 1: Trying git clone..."
if git clone "$REPO_URL" . 2>/dev/null; then
    echo "✓ Successfully downloaded via git clone"
    echo ""
    ls -la
    echo ""
    echo "Download complete! Run conversion script:"
    echo "  cd ../../.."
    echo "  python convert_threadmed_qa.py"
    exit 0
fi

echo "✗ Git clone failed"
echo ""

# Method 2: Download ZIP
echo "Method 2: Trying to download ZIP file..."
if curl -L -o threadmed-qa.zip "$REPO_ZIP" 2>/dev/null; then
    if unzip -q threadmed-qa.zip 2>/dev/null; then
        echo "✓ Successfully downloaded and extracted ZIP"
        rm -f threadmed-qa.zip
        echo ""
        ls -la
        echo ""
        echo "Download complete! Run conversion script:"
        echo "  cd ../../.."
        echo "  python convert_threadmed_qa.py"
        exit 0
    else
        echo "✗ ZIP extraction failed"
        rm -f threadmed-qa.zip
    fi
else
    echo "✗ ZIP download failed"
fi

echo ""
echo "=========================================="
echo "  ❌ All automatic download methods failed"
echo "=========================================="
echo ""
echo "Please download manually:"
echo ""
echo "1. Visit: https://github.com/monicamunnangi/ThReadMed-QA"
echo "2. Click 'Code' → 'Download ZIP'"
echo "3. Extract to: $TARGET_DIR"
echo "4. Run: python convert_threadmed_qa.py"
echo ""
echo "Or clone using git:"
echo "  cd $TARGET_DIR"
echo "  git clone https://github.com/monicamunnangi/ThReadMed-QA.git ."
echo ""
echo "Repository status:"
echo "  - URL: https://github.com/monicamunnangi/ThReadMed-QA"
echo "  - Exists: Yes"
echo "  - Private: No (public repository)"
echo ""

# Check if directory is not empty
if [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    echo "Current directory contents:"
    ls -la "$TARGET_DIR"
else
    echo "Directory is empty (dataset not downloaded yet)"
fi
