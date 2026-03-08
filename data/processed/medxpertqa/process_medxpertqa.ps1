# MedXpertQA Processor - PowerShell Version
# Converts medxpertqa_text_input.jsonl to tasks.json and db.json

# Use script directory as base
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Paths relative to project root (avoid encoding issues)
$projectRoot = "C:\Users\方正\tau2-bench"
$inputFile = "$projectRoot\data\raw\MedXpertQA\eval\data\medxpertqa\input\medxpertqa_text_input.jsonl"
$outputDir = "$projectRoot\data\processed\medxpertqa"
$tasksOutput = Join-Path $outputDir "tasks.json"
$dbOutput = Join-Path $outputDir "db.json"

Write-Host "=" * 60
Write-Host "MedXpertQA Processor (PowerShell)"
Write-Host "=" * 60
Write-Host ""

# Create output directory first
Write-Host "Creating output directory..."
if (-not (Test-Path $outputDir)) {
    try {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
        Write-Host "  Created: $outputDir"
    } catch {
        Write-Host "  ERROR: $_"
    }
} else {
    Write-Host "  Directory exists: $outputDir"
}
Write-Host ""

# Step 1: Read JSONL file using .NET to avoid encoding issues
Write-Host "Step 1: Reading JSONL file..."
Write-Host "  Input: $inputFile"

$entries = @()

try {
    $reader = [System.IO.StreamReader]::new($inputFile)
    $lineNum = 0

    while ($null -ne ($line = $reader.ReadLine())) {
        $lineNum++
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        try {
            $entry = $line | ConvertFrom-Json
            $entries += $entry
            if ($lineNum % 100 -eq 0) {
                Write-Host "  Processed $lineNum lines..."
            }
        } catch {
            # Skip invalid lines
        }
    }

    $reader.Close()
    Write-Host "  Total entries loaded: $($entries.Count)"
} catch {
    Write-Host "  ERROR reading file: $_"
    Write-Host "  Trying alternative method..."
}

Write-Host ""

if ($entries.Count -eq 0) {
    Write-Host "ERROR: No entries loaded. Cannot continue."
    exit 1
}

# Step 2: Generate tasks.json
Write-Host "Step 2: Generating tasks.json..."
$tasks = @()

for ($i = 0; $i -lt $entries.Count; $i++) {
    $entry = $entries[$i]
    $idx = $i + 1
    $taskId = "medxpertqa_{0:D3}" -f $idx

    # Extract fields
    $question = $entry.question
    $medicalTask = if ($entry.medical_task) { $entry.medical_task } else { "Diagnosis" }
    $bodySystem = if ($entry.body_system) { $entry.body_system } else { "General" }
    $questionType = if ($entry.question_type) { $entry.question_type } else { "Reasoning" }

    # Build ticket with fallback
    $ticket = $question
    if (-not $ticket.EndsWith("Not found")) {
        $ticket = "$ticket If the answer does not exist, the answer should be 'Not found'"
    }

    # Build known_info
    $knownInfoParts = @()
    if ($medicalTask) { $knownInfoParts += "Task Type: $medicalTask" }
    if ($bodySystem) { $knownInfoParts += "Body System: $bodySystem" }
    if ($questionType) { $knownInfoParts += "Question Type: $questionType" }
    $knownInfo = if ($knownInfoParts.Count -gt 0) { $knownInfoParts -join ", " } else { $null }

    # Build notes
    $notesParts = @()
    if ($medicalTask) { $notesParts += "Task: $medicalTask" }
    if ($bodySystem) { $notesParts += "System: $bodySystem" }
    $notes = if ($notesParts.Count -gt 0) { $notesParts -join ", " } else { $null }

    # Create task object (EXACT MedAgentBench format)
    $task = [PSCustomObject]@{
        id = $taskId
        description = [PSCustomObject]@{
            purpose = "Medical knowledge QA"
            relevant_policies = $null
            notes = $notes
        }
        user_scenario = [PSCustomObject]@{
            persona = $null
            instructions = [PSCustomObject]@{
                task_instructions = $ticket
                domain = "clinical"
                reason_for_call = "Medical consultation"
                known_info = $knownInfo
                unknown_info = $null
            }
        }
        ticket = $ticket
        initial_state = $null
        evaluation_criteria = $null
        annotations = $null
    }
    $tasks += $task
}

Write-Host "  Created $($tasks.Count) tasks"
Write-Host ""

# Step 3: Generate db.json
Write-Host "Step 3: Generating db.json..."
$qaPairs = [ordered]@{}

for ($i = 0; $i -lt $entries.Count; $i++) {
    $entry = $entries[$i]
    $idx = $i + 1
    $taskId = "medxpertqa_{0:D3}" -f $idx

    # Extract question
    $question = $entry.question

    # Find answer based on label
    $label = if ($entry.label) { $entry.label[0] } else { $null }
    $answer = "Not found"

    if ($label -and $entry.options) {
        foreach ($opt in $entry.options) {
            if ($opt.letter -eq $label) {
                $answer = $opt.content
                break
            }
        }
    }

    # Extract metadata
    $medicalTask = if ($entry.medical_task) { $entry.medical_task } else { $null }
    $bodySystem = if ($entry.body_system) { $entry.body_system } else { $null }
    $questionType = if ($entry.question_type) { $entry.question_type } else { $null }

    # Create QA pair (EXACT MedAgentBench format)
    $qaPair = [PSCustomObject]@{
        id = "qa_$taskId"
        question = $question
        answer = $answer
        task_id = $taskId
    }

    # Add optional fields only if they exist
    if ($medicalTask) {
        $qaPair | Add-Member -NotePropertyName "medical_task" -NotePropertyValue $medicalTask
    }
    if ($bodySystem) {
        $qaPair | Add-Member -NotePropertyName "body_system" -NotePropertyValue $bodySystem
    }
    if ($questionType) {
        $qaPair | Add-Member -NotePropertyName "question_type" -NotePropertyValue $questionType
    }

    $qaPairs[$taskId] = $qaPair
}

$dbData = [PSCustomObject]@{
    qa_pairs = [PSCustomObject]$qaPairs
}

Write-Host "  Created $($qaPairs.Count) QA pairs"
Write-Host ""

# Step 4: Write files
Write-Host "Step 4: Writing output files..."

# Write tasks.json
$tasksJson = $tasks | ConvertTo-Json -Depth 10 -AsArray
[System.IO.File]::WriteAllText($tasksOutput, $tasksJson, [System.Text.Encoding]::UTF8)
Write-Host "  Created: $tasksOutput"

# Write db.json
$dbJson = $dbData | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($dbOutput, $dbJson, [System.Text.Encoding]::UTF8)
Write-Host "  Created: $dbOutput"

Write-Host ""
Write-Host "=" * 60
Write-Host "Processing Complete!"
Write-Host "=" * 60
Write-Host ""
Write-Host "Output files:"
Write-Host "  Tasks:  $tasksOutput"
Write-Host "  DB:     $dbOutput"
Write-Host ""
Write-Host "Summary:"
Write-Host "  - Total tasks:   $($tasks.Count)"
Write-Host "  - Total QA pairs: $($qaPairs.Count)"
Write-Host ""

# Show samples
Write-Host "=" * 60
Write-Host "Sample Data (First 2 Entries)"
Write-Host "=" * 60
Write-Host ""

Write-Host "Sample Task (from tasks.json):"
Write-Host ""
$tasks[0] | ConvertTo-Json -Depth 5 | Write-Host
Write-Host ""

Write-Host "Sample QA Pair (from db.json):"
Write-Host ""
$firstQaId = $qaPairs.Keys[0]
$qaPairs[$firstQaId] | ConvertTo-Json -Depth 3 | Write-Host
Write-Host ""
