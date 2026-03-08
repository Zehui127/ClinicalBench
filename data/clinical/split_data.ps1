# ========================================
# Split Clinical tasks.json into tasks.json + db.json
# Following the airline directory structure
# ========================================

# Set paths
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$clinicalDir = $scriptPath
$sourceTasksFile = Join-Path $clinicalDir "tasks.json"
$newTasksFile = Join-Path $clinicalDir "tasks_new.json"
$dbFile = Join-Path $clinicalDir "db.json"
$backupFile = Join-Path $clinicalDir "tasks_original_backup.json"

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Splitting Clinical tasks.json" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Step 1: Backup original file
Write-Host "Step 1: Backing up original tasks.json..." -ForegroundColor Yellow
if (Test-Path $sourceTasksFile) {
    Copy-Item $sourceTasksFile $backupFile -Force
    Write-Host "  Backup created: tasks_original_backup.json" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Source file not found: $sourceTasksFile" -ForegroundColor Red
    exit 1
}

# Step 2: Read source JSON
Write-Host "Step 2: Reading source tasks.json..." -ForegroundColor Yellow
try {
    $jsonContent = Get-Content $sourceTasksFile -Raw -Encoding UTF8
    $tasks = $jsonContent | ConvertFrom-Json
    Write-Host "  Loaded $($tasks.Count) tasks" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to parse JSON: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Extract patient data and create new tasks
Write-Host "Step 3: Extracting patient data and creating clean tasks..." -ForegroundColor Yellow

$patientsDict = @{}  # Use ordered dictionary
$newTasksList = @()  # Array to store clean tasks

foreach ($task in $tasks) {
    # Extract patient info from ticket field using regex
    $ticket = $task.ticket
    $taskId = $task.id
    $expectedAnswer = $task.annotations.expected_answer

    # Regex pattern: "name <Patient Name> and DOB of <YYYY-MM-DD>"
    if ($ticket -match 'name\s+([\w\s]+?)\s+and\s+DOB\s+of\s+([\d\-]+)') {
        $patientName = $matches[1].Trim()
        $patientDob = $matches[2].Trim()

        # Create patient ID and add to dictionary
        $patientId = "patient_$taskId"
        $patientsDict[$expectedAnswer] = @{
            id = $patientId
            name = $patientName
            dob = $patientDob
            mrn = $expectedAnswer
            task_id = $taskId
        }
    }

    # Create clean task (no answers) - directly as PSObject
    $cleanTask = @{
        id = $task.id
        description = $task.description
        user_scenario = $task.user_scenario
        ticket = $task.ticket
        initial_state = $task.initial_state
        evaluation_criteria = $null  # Remove evaluation criteria
        annotations = $null           # Remove annotations
    }
    $newTasksList += $cleanTask
}

Write-Host "  Extracted $($patientsDict.Count) unique patients" -ForegroundColor Green
Write-Host "  Created $($newTasksList.Count) clean tasks" -ForegroundColor Green

# Step 4: Create db.json structure (like airline's structure)
Write-Host "Step 4: Creating db.json..." -ForegroundColor Yellow

# Create patients object with MRN as key (like airline uses flight_id as key)
$patientsObject = [PSCustomObject]@{}
foreach ($mrn in $patientsDict.Keys) {
    $patientData = $patientsDict[$mrn]
    $patientObj = [PSCustomObject]@{
        id = $patientData.id
        name = $patientData.name
        dob = $patientData.dob
        mrn = $patientData.mrn
        task_id = $patientData.task_id
    }
    $patientsObject | Add-Member -NotePropertyName $mrn -NotePropertyValue $patientObj -Force
}

# Create final db structure
$dbStructure = [PSCustomObject]@{
    patients = $patientsObject
}

# Convert to JSON and save
$dbJson = $dbStructure | ConvertTo-Json -Depth 10
# Remove BOM and clean up
$dbJson = $dbJson -replace '^\xEF\xBB\xBF', ''
Set-Content -Path $dbFile -Value $dbJson -Encoding UTF8 -NoNewline
Write-Host "  Created: db.json with $($patientsDict.Count) patients" -ForegroundColor Green

# Step 5: Save new tasks.json (without answers)
Write-Host "Step 5: Saving new tasks.json..." -ForegroundColor Yellow

# Convert tasks array to JSON
$newTasksJson = $newTasksList | ConvertTo-Json -Depth 10
# Remove BOM and clean up
$newTasksJson = $newTasksJson -replace '^\xEF\xBB\xBF', ''
Set-Content -Path $newTasksFile -Value $newTasksJson -Encoding UTF8 -NoNewline
Write-Host "  Created: tasks_new.json" -ForegroundColor Green

# Step 6: Verify files
Write-Host "Step 6: Verifying created files..." -ForegroundColor Yellow

# Verify db.json
try {
    $dbVerified = Get-Content $dbFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $patientCount = ($dbVerified.patients.PSObject.Properties.Name).Count
    Write-Host "  db.json: Valid JSON with $patientCount patients" -ForegroundColor Green
} catch {
    Write-Host "  db.json: Validation failed - $_" -ForegroundColor Red
}

# Verify new tasks.json
try {
    $tasksVerified = Get-Content $newTasksFile -Raw -Encoding UTF8 | ConvertFrom-Json
    Write-Host "  tasks_new.json: Valid JSON with $($tasksVerified.Count) tasks" -ForegroundColor Green

    # Check that evaluation_criteria and annotations are removed
    $hasEvalCriteria = $false
    $hasAnnotations = $false
    foreach ($t in $tasksVerified) {
        if ($null -ne $t.evaluation_criteria) { $hasEvalCriteria = $true }
        if ($null -ne $t.annotations) { $hasAnnotations = $true }
    }

    if (-not $hasEvalCriteria -and -not $hasAnnotations) {
        Write-Host "  tasks_new.json: Clean (no evaluation_criteria or annotations)" -ForegroundColor Green
    } else {
        Write-Host "  tasks_new.json: WARNING - still contains answer fields" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  tasks_new.json: Validation failed - $_" -ForegroundColor Red
}

# Step 7: Display sample data
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Sample Data Preview" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

Write-Host "`nSample Patient (from db.json):" -ForegroundColor Yellow
$sampleMrn = ($dbStructure.patients.PSObject.Properties.Name)[0]
$dbStructure.patients.$sampleMrn | ConvertTo-Json -Depth 3 | Write-Host

Write-Host "`nSample Task (from tasks_new.json):" -ForegroundColor Yellow
$firstTask = $newTasksList[0]
$firstTask.PSObject.Properties | Format-Table -AutoSize

Write-Host "`nTask ticket field:" -ForegroundColor Yellow
Write-Host "  $($firstTask.ticket)" -ForegroundColor White

# Step 8: Summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Split Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "Files created:" -ForegroundColor Green
Write-Host "  1. $newTasksFile" -ForegroundColor White
Write-Host "  2. $dbFile" -ForegroundColor White
Write-Host "  3. $backupFile" -ForegroundColor White
Write-Host ""
Write-Host "Summary:" -ForegroundColor Green
Write-Host "  - Total tasks: $($tasks.Count)" -ForegroundColor White
Write-Host "  - Patients extracted: $($patientsDict.Count)" -ForegroundColor White
Write-Host "  - Clean tasks created: $($newTasksList.Count)" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review tasks_new.json and db.json" -ForegroundColor White
Write-Host "  2. Replace original tasks.json with the new version:" -ForegroundColor White
Write-Host "     Copy-Item tasks_new.json tasks.json -Force" -ForegroundColor Gray
Write-Host "  3. Or keep original and use tasks_new.json" -ForegroundColor White
Write-Host ""
Write-Host "Directory structure now matches airline:" -ForegroundColor Green
Write-Host "  clinical/tasks.json  (pure questions, no answers)" -ForegroundColor Gray
Write-Host "  clinical/db.json     (patient database/fact library)" -ForegroundColor Gray
Write-Host ""
