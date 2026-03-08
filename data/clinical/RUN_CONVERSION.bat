@echo off
REM ========================================
REM MedAgentBench to Tau2-Bench Conversion Script
REM ========================================

echo ======================================
echo MedAgentBench to Tau2-Bench Conversion
echo ======================================
echo.

cd /d "C:\Users\方正\tau2-bench"

echo Step 1: Checking clinical directory...
if not exist "data\clinical" (
    mkdir "data\clinical"
    echo Created directory: data\clinical
) else (
    echo Directory exists: data\clinical
)
echo.

echo Step 2: Running full conversion...
python "data\clinical\full_convert.py"
if errorlevel 1 (
    echo Conversion failed with error code %errorlevel%
    pause
    exit /b %errorlevel%
)
echo.

echo Step 3: Verifying output...
powershell -Command "try { Get-Content 'data\clinical\tasks.json' -Raw -Encoding UTF8 | ConvertFrom-Json | Out-Null; Write-Host 'SUCCESS: JSON is valid' -ForegroundColor Green } catch { Write-Host 'ERROR: Invalid JSON' -ForegroundColor Red }"
echo.

echo ======================================
echo Conversion Complete!
echo ======================================
echo.
echo Output file: C:\Users\方正\tau2-bench\data\clinical\tasks.json
echo.

pause
