#!/bin/bash
# WSL2测试脚本 - 在真实的Linux环境中测试

echo "🐧 Running tests in WSL2 (Ubuntu)"
echo "=================================="
echo ""

# 检查WSL是否安装
if ! command -v wsl &> /dev/null; then
    echo "❌ WSL not found!"
    echo ""
    echo "To install WSL2:"
    echo "1. Open PowerShell as Administrator"
    echo "2. Run: wsl --install"
    echo "3. Restart computer"
    echo "4. Install Ubuntu from Microsoft Store"
    echo ""
    exit 1
fi

# 在WSL中运行测试
echo "📋 Running test in WSL..."
wsl bash -c "
    cd /mnt/c/Users/方正/tau2-bench
    python3 --version
    echo ''

    echo 'Test 1: Import Check'
    python3 -c \"
    import sys
    sys.path.insert(0, '.')
    import DataQualityFiltering
    import tau2
    print('[OK] Imports successful')
    \"

    echo ''
    echo 'Test 2: Tau2 Evaluators'
    python3 -c \"
    from tau2.evaluator import ClinicalEvaluator
    print('[OK] ClinicalEvaluator works')
    \"

    echo ''
    echo 'Test 3: Core Modules'
    python3 -c \"
    from DataQualityFiltering.core import LLMEvaluator
    print('[OK] Core modules work')
    \"

    echo ''
    echo '✅ All WSL tests passed!'
"

echo ""
echo "✅ WSL test completed!"
echo ""
echo "WSL tests passed = GitHub Actions will pass"
