# ========================================================================
# Quick Verification Script for run_batch_repair.ps1
# run_batch_repair.ps1 快速验证脚本
# ========================================================================

$scriptPath = "run_batch_repair.ps1"
$fullPath = Join-Path $PSScriptRoot $scriptPath

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Verifying run_batch_repair.ps1" -ForegroundColor Cyan
Write-Host "验证 run_batch_repair.ps1" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if file exists
if (-not (Test-Path $fullPath)) {
    Write-Host "[ERROR] File not found: $scriptPath" -ForegroundColor Red
    Write-Host "[错误] 文件未找到：$scriptPath" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] File found: $scriptPath" -ForegroundColor Green
Write-Host ""

# Check file encoding (BOM)
Write-Host "Checking file encoding..." -ForegroundColor Cyan
Write-Host "检查文件编码..." -ForegroundColor Cyan
Write-Host ""

$bytes = [System.IO.File]::ReadAllBytes($fullPath)
$bom = $bytes[0..2]

if ($bytes.Length -ge 3 -and $bom[0] -eq 0xEF -and $bom[1] -eq 0xBB -and $bom[2] -eq 0xBF) {
    Write-Host "[OK] File has UTF-8 BOM encoding" -ForegroundColor Green
    Write-Host "[OK] 文件具有 UTF-8 BOM 编码" -ForegroundColor Green
} else {
    Write-Host "[WARNING] File does not have UTF-8 BOM encoding" -ForegroundColor Yellow
    Write-Host "[警告] 文件不具有 UTF-8 BOM 编码" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix this, run:" -ForegroundColor Yellow
    Write-Host "  fix_encoding.bat" -ForegroundColor White
}

Write-Host ""

# Check for syntax errors
Write-Host "Checking for syntax errors..." -ForegroundColor Cyan
Write-Host "检查语法错误..." -ForegroundColor Cyan
Write-Host ""

$content = Get-Content $fullPath -Raw -Encoding UTF8
$errors = $null

try {
    $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors)

    if ($errors.Count -eq 0) {
        Write-Host "[OK] No syntax errors found" -ForegroundColor Green
        Write-Host "[OK] 未发现语法错误" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Syntax errors found:" -ForegroundColor Red
        Write-Host "[错误] 发现语法错误：" -ForegroundColor Red
        $errors | ForEach-Object {
            Write-Host "  Line $($_.Line): $($_.Message)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "[ERROR] Failed to parse script: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Check for problematic characters
Write-Host "Checking for problematic characters..." -ForegroundColor Cyan
Write-Host "检查问题字符..." -ForegroundColor Cyan
Write-Host ""

$issues = @()
$lines = Get-Content $fullPath -Encoding UTF8
$lineNum = 0

foreach ($line in $lines) {
    $lineNum++

    # Check for Unicode checkmark (U+2713)
    if ($line -match '\u2713|\u2714|\u2611') {
        $issues += "Line $lineNum`: Contains Unicode checkmark character"
    }

    # Check for garbled checkmark pattern
    if ($line -match 'Ã‚Â|Ã‚â‚¬|âœ•|âˆš') {
        $issues += "Line $lineNum`: Contains garbled Unicode character"
    }
}

if ($issues.Count -eq 0) {
    Write-Host "[OK] No problematic characters found" -ForegroundColor Green
    Write-Host "[OK] 未发现问题字符" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Found problematic characters:" -ForegroundColor Yellow
    Write-Host "[警告] 发现问题字符：" -ForegroundColor Yellow
    $issues | ForEach-Object { Write-Host "  $_" -ForegroundColor Yellow }
}

Write-Host ""

# Summary
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "验证摘要" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

if ($errors.Count -eq 0 -and $issues.Count -eq 0) {
    Write-Host "[SUCCESS] Script is ready to execute!" -ForegroundColor Green
    Write-Host "[成功] 脚本已准备好执行！" -ForegroundColor Green
    Write-Host ""
    Write-Host "To run the script:" -ForegroundColor Yellow
    Write-Host "  .\run_batch_repair.ps1" -ForegroundColor White
} else {
    Write-Host "[WARNING] Script has issues that need to be fixed" -ForegroundColor Yellow
    Write-Host "[警告] 脚本存在需要修复的问题" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please review the errors above." -ForegroundColor Yellow
}

Write-Host ""
