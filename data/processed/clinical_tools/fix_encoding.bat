@echo off
REM ========================================================================
REM UTF-8 BOM Encoding Fix for PowerShell Scripts
REM PowerShell 脚本的 UTF-8 BOM 编码修复
REM ========================================================================

echo ========================================================================
echo UTF-8 BOM Encoding Fix
echo UTF-8 BOM 编码修复
echo ========================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "TARGET_FILE=%SCRIPT_DIR%run_batch_repair.ps1"

echo Target file: %TARGET_FILE%
echo 目标文件： %TARGET_FILE%
echo.

if not exist "%TARGET_FILE%" (
    echo [ERROR] File not found: run_batch_repair.ps1
    echo [错误] 文件未找到：run_batch_repair.ps1
    pause
    exit /b 1
)

echo [INFO] Reading file content...
echo [信息] 正在读取文件内容...
echo.

powershell -NoProfile -Command "& {$content = Get-Content '%TARGET_FILE%' -Raw -Encoding UTF8; $utf8WithBom = New-Object System.Text.UTF8Encoding $true; [System.IO.File]::WriteAllText('%TARGET_FILE%', $content, $utf8WithBom); Write-Host '[SUCCESS] File saved with UTF-8 BOM encoding' -ForegroundColor Green; Write-Host '[成功] 文件已使用 UTF-8 BOM 编码保存' -ForegroundColor Green}"

echo.
echo ========================================================================
echo Encoding fix complete!
echo 编码修复完成！
echo ========================================================================
echo.
echo You can now run: .\run_batch_repair.ps1
echo 现在可以运行：.\run_batch_repair.ps1
echo.
pause
