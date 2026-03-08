@echo off
cd /d C:\Users\方正\tau2-bench
python process_medxpert.py > script_output.txt 2>&1
type script_output.txt
