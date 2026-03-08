@echo off
cd /d C:\Users\方正\tau2-bench\data\processed\medxpertqa
call python process_medxpertqa.py
echo.
echo SCRIPT_EXIT_CODE: %ERRORLEVEL%
