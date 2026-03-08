# ========================================================================
# Batch Repair Script - Quick Execution
# 批量修复脚本 - 快速执行
# ========================================================================
#
# FIX NOTES:
# 1. File saved as UTF-8 with BOM for Chinese character support
# 2. Replaced Unicode checkmark (✓) with [OK] for ASCII compatibility
# 3. Escaped parentheses in strings or used different quote styles
# 4. Fixed variable interpolation syntax
# ========================================================================

# Set UTF-8 encoding for Chinese characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Navigate to clinical_tools directory
$scriptDir = "C:\Users\方正\tau2-bench\data\processed\clinical_tools"
Set-Location $scriptDir

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Batch Repair Script - Quick Execution" -ForegroundColor Cyan
Write-Host "批量修复脚本 - 快速执行" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Working directory: $scriptDir" -ForegroundColor Yellow
Write-Host ""

# Check if batch repair script exists
if (-not (Test-Path "batch_repair_all.py")) {
    Write-Host "[ERROR] batch_repair_all.py not found!" -ForegroundColor Red
    Write-Host "Please ensure the file exists in the current directory." -ForegroundColor Yellow
    exit 1
}

Write-Host "[Starting batch repair process...]" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will:" -ForegroundColor Yellow
Write-Host "  1. Generate 3,000 synthetic clinical tasks" -ForegroundColor White
Write-Host "  2. Fix review_scores.json schema" -ForegroundColor White
Write-Host "  3. Fix tasks_filtered.json format" -ForegroundColor White
# FIX: Escaped parentheses or used single quotes for special characters
Write-Host '  4. Generate category files (100 tasks each)' -ForegroundColor White
Write-Host ""

# Confirm execution
$confirmation = Read-Host "Continue? (Y/N)"
if ($confirmation -ne "Y" -and $confirmation -ne "y") {
    Write-Host ""
    Write-Host "[CANCELLED] Operation cancelled by user." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[Executing batch_repair_all.py...]" -ForegroundColor Cyan
Write-Host ""

# Execute the Python script
$startTime = Get-Date
python batch_repair_all.py
$exitCode = $LASTEXITCODE
$endTime = Get-Date
$duration = $endTime - $startTime

# Check exit code
if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] Batch repair completed successfully!" -ForegroundColor Green
    Write-Host "[成功] 批量修复成功完成！" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Execution time: $($duration.TotalSeconds.ToString('F2')) seconds" -ForegroundColor Cyan
    Write-Host "执行时间：$($duration.TotalSeconds.ToString('F2')) 秒" -ForegroundColor Cyan
    Write-Host ""

    # Show generated files
    Write-Host "Generated root files:" -ForegroundColor Cyan
    $rootFiles = @("tasks_raw.json", "review_scores.json", "tasks_filtered.json")
    foreach ($file in $rootFiles) {
        if (Test-Path $file) {
            $size = [math]::Round((Get-Item $file).Length / 1KB, 2)
            # FIX: Replaced Unicode ✓ with [OK] for ASCII compatibility
            Write-Host "  [OK] $file ($size KB)" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "Generated category files:" -ForegroundColor Cyan

    if (Test-Path "standardized_test_set") {
        $categoryFiles = Get-ChildItem "standardized_test_set" -Filter "*.json"
        foreach ($file in $categoryFiles) {
            $size = [math]::Round($file.Length / 1KB, 2)
            $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
            # FIX: Escaped variables in string properly
            Write-Host "  [OK] $($file.Name) ($($content.Count) tasks, $size KB)" -ForegroundColor Green
        }

        Write-Host ""
        Write-Host "Total category files: $($categoryFiles.Count)" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Review the generated files" -ForegroundColor White
    Write-Host '  2. Run: python split_standardized_tasks_fixed.py' -ForegroundColor White
    Write-Host "  3. Verify output in standardized_test_set/" -ForegroundColor White

} else {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host "[ERROR] Batch repair failed with exit code: $exitCode" -ForegroundColor Red
    Write-Host "[错误] 批量修复失败，退出代码：$exitCode" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above for details." -ForegroundColor Yellow
    Write-Host "请检查上方的错误消息以获取详细信息。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Python version must be 3.9+" -ForegroundColor White
    Write-Host "  - Insufficient disk space" -ForegroundColor White
    Write-Host "  - Write permissions on directory" -ForegroundColor White
}

Write-Host ""
