# ========================================
# PowerShell Commands for MedAgentBench to Tau2-Bench Adapter
# ========================================
# Copy and paste each command block into your PowerShell terminal
# ========================================

# ------------------------------------------------
# Step 1: Navigate to the tau2-bench project directory
# ------------------------------------------------
cd "C:\Users\方正\tau2-bench"

# ------------------------------------------------
# Step 2: Create the clinical directory if it doesn't exist
# ------------------------------------------------
if (-not (Test-Path "data\clinical")) {
    New-Item -ItemType Directory -Path "data\clinical" -Force
    Write-Host "Created directory: data\clinical" -ForegroundColor Green
} else {
    Write-Host "Directory already exists: data\clinical" -ForegroundColor Cyan
}

# ------------------------------------------------
# Step 3: Run the full conversion script
# (Converts ALL tasks from test_data_v2.json to tasks.json)
# ------------------------------------------------
Write-Host "`n=== Running Full Conversion ===" -ForegroundColor Cyan
python "data\clinical\full_convert.py"

# ------------------------------------------------
# Step 4: Verify the generated tasks.json is valid JSON
# ------------------------------------------------
Write-Host "`n=== Verifying JSON format ===" -ForegroundColor Cyan
try {
    $jsonContent = Get-Content "data\clinical\tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host "✓ JSON format is valid!" -ForegroundColor Green
    Write-Host "✓ Number of tasks: $($jsonContent.Count)" -ForegroundColor Green
} catch {
    Write-Host "✗ JSON validation failed: $_" -ForegroundColor Red
}

# ------------------------------------------------
# Step 5: Verify required fields exist in the tasks.json
# ------------------------------------------------
Write-Host "`n=== Verifying required fields ===" -ForegroundColor Cyan
$requiredFields = @("id", "user_scenario", "evaluation_criteria")
$jsonContent = Get-Content "data\clinical\tasks.json" -Raw -Encoding UTF8 | ConvertFrom-Json

$allValid = $true
$taskCount = 0
foreach ($task in $jsonContent) {
    $taskCount++
    foreach ($field in $requiredFields) {
        if (-not $task.PSObject.Properties.Name -contains $field) {
            Write-Host "✗ Task $($task.id) missing field: $field" -ForegroundColor Red
            $allValid = $false
        }
    }
}

if ($allValid) {
    Write-Host "✓ All $taskCount tasks have required fields!" -ForegroundColor Green
}

# ------------------------------------------------
# Step 6: Display sample task structure
# ------------------------------------------------
Write-Host "`n=== Sample Task Structure ===" -ForegroundColor Cyan
$firstTask = $jsonContent[0]
$firstTask | ConvertTo-Json -Depth 3 | Out-String | Write-Host

# ------------------------------------------------
# Step 7: Confirm file location and size
# ------------------------------------------------
Write-Host "`n=== File Information ===" -ForegroundColor Cyan
$fileInfo = Get-Item "data\clinical\tasks.json"
Write-Host "✓ File path: $($fileInfo.FullName)" -ForegroundColor Green
Write-Host "✓ File size: $([math]::Round($fileInfo.Length / 1KB, 2)) KB" -ForegroundColor Green
Write-Host "✓ Last modified: $($fileInfo.LastWriteTime)" -ForegroundColor Green

# ------------------------------------------------
# Step 8: Display statistics
# ------------------------------------------------
Write-Host "`n=== Statistics ===" -ForegroundColor Cyan
Write-Host "Total tasks: $taskCount" -ForegroundColor Green
Write-Host "Sample task IDs: $($jsonContent[0].id), $($jsonContent[1].id), $($jsonContent[2].id)" -ForegroundColor Cyan

# ------------------------------------------------
# Step 9: Run the validation script (optional)
# ------------------------------------------------
Write-Host "`n=== Running Validation Script ===" -ForegroundColor Cyan
python "data\clinical\validate_tasks.py" --tasks "data\clinical\tasks.json"

# ------------------------------------------------
# Step 10: Summary
# ------------------------------------------------
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "✓ Clinical directory created/verified" -ForegroundColor Green
Write-Host "✓ Tasks JSON generated from MedAgentBench source" -ForegroundColor Green
Write-Host "✓ JSON validation completed" -ForegroundColor Green
Write-Host "✓ Field validation completed" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Review the generated tasks.json file" -ForegroundColor White
Write-Host "  2. Run tau2-bench evaluation with: python -m src.tau2.run --domain clinical --tasks data\clinical\tasks.json" -ForegroundColor White
Write-Host "  3. Or integrate with your existing workflow" -ForegroundColor White

# ------------------------------------------------
# ADAPTER-KWARGS REFERENCE
# ------------------------------------------------
Write-Host "`n=== Adapter-Kwargs Reference ===" -ForegroundColor Cyan
Write-Host @"
The adapter uses the following field mappings:
  Source Field                ->  Target Path (tau2-bench)
  ----------------------------->-----------------------------
  id                          ->  id
  instruction                 ->  user_scenario.instructions.task_instructions
  instruction                 ->  ticket (copied)
  instruction (regex extract) ->  user_scenario.instructions.known_info
  context                     ->  user_scenario.instructions.unknown_info
  sol                         ->  annotations.expected_solution
  eval_MRN                    ->  annotations.expected_answer
  eval_MRN                    ->  evaluation_criteria.nl_assertions[0] (template)

Static fields added:
  - description.purpose: "Find patient MRN by name and date of birth"
  - user_scenario.instructions.domain: "clinical"
  - user_scenario.instructions.reason_for_call: "Looking up patient information"
  - evaluation_criteria.actions: []
  - evaluation_criteria.communicate_info: []
  - annotations.source_format: "medagentbench_v2"

To run with UniClinicalDataEngine (if available):
  python -m src.tau2.cli adapt `
      --adapter MedAgentBenchToTau2Adapter `
      --source "MedAgentBench\data\medagentbench\test_data_v2.json" `
      --output "data\clinical\tasks.json" `
      --adapter-config "data\clinical\adapter_config.json"
"@
