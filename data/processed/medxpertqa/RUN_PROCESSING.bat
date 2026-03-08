@echo off
REM ========================================
REM MedXpertQA One-Click Processing Script
REM ========================================

echo.
echo ========================================
echo   MedXpertQA Processing Launcher
REM   Tau2-Bench Data Processor
echo ========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell not found!
    echo Please ensure PowerShell is installed and in PATH.
    pause
    exit /b 1
)

REM Run the PowerShell processing script
echo Starting MedXpertQA processing...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0medxpertqa_full_process.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   Processing completed successfully!
    echo ========================================
    echo.
    echo Check the output directory for results:
    echo   %~dp0
    echo.
) else (
    echo.
    echo ========================================
    echo   Processing failed with error code %ERRORLEVEL%
    echo ========================================
    echo.
    echo Please check the log file for details:
    echo   %~dp0process_log_medxpertqa.txt
    echo.
)

pause
