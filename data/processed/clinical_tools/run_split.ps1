# ========================================================================
# Standardized Task Splitter - Quick Execution Script
# 标准化任务分割器 - 快速执行脚本
# ========================================================================

# Set UTF-8 encoding for Chinese characters
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Navigate to clinical_tools directory
$scriptDir = "C:\Users\方正\tau2-bench\data\processed\clinical_tools"
Set-Location $scriptDir

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Standardized Task Splitter - Quick Execution" -ForegroundColor Cyan
Write-Host "标准化任务分割器 - 快速执行" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Working directory: $scriptDir" -ForegroundColor Yellow
Write-Host ""

# Check if input files exist
Write-Host "[Checking input files...]" -ForegroundColor Cyan
$tasksFilteredExists = Test-Path "tasks_filtered.json"
$reviewScoresExists = Test-Path "review_scores.json"

if ($tasksFilteredExists) {
    Write-Host "[OK] tasks_filtered.json found" -ForegroundColor Green
} else {
    Write-Host "[ERROR] tasks_filtered.json NOT found" -ForegroundColor Red
    Write-Host "Please run data_quality_filter.py first" -ForegroundColor Yellow
    exit 1
}

if ($reviewScoresExists) {
    Write-Host "[OK] review_scores.json found" -ForegroundColor Green
} else {
    Write-Host "[ERROR] review_scores.json NOT found" -ForegroundColor Red
    Write-Host "Please run data_quality_filter.py first" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[Executing split_standardized_tasks_fixed.py...]" -ForegroundColor Cyan
Write-Host ""

# Execute the Python script
python split_standardized_tasks_fixed.py

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] Script completed successfully!" -ForegroundColor Green
    Write-Host "[成功] 脚本执行成功！" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green

    # Show output directory
    $outputDir = Join-Path $scriptDir "standardized_test_set"
    if (Test-Path $outputDir) {
        Write-Host ""
        Write-Host "Output directory: $outputDir" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Generated files:" -ForegroundColor Cyan
        Get-ChildItem $outputDir | ForEach-Object {
            $size = [math]::Round($_.Length / 1KB, 2)
            Write-Host "  - $($_.Name) ($size KB)" -ForegroundColor White
        }
    }
} else {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host "[ERROR] Script failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    Write-Host "[错误] 脚本执行失败，退出代码：$LASTEXITCODE" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check the error messages above for details." -ForegroundColor Yellow
    Write-Host "请检查上方的错误消息以获取详细信息。" -ForegroundColor Yellow
}

Write-Host ""
