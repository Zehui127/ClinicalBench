# PowerShell script to process MedXpertQA and ProdMedBench
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $scriptDir "data"
$baseDir = Join-Path $scriptDir "data\processed"

Write-Host "Loading source files for large datasets..." -ForegroundColor Cyan

# Load MedXpertQA
Write-Host "Loading MedXpertQA (2450 tasks)..." -ForegroundColor Yellow
$sr = [System.IO.StreamReader]::new((Join-Path $baseDir "medxpertqa\tasks.json"))
$medxpertJson = $sr.ReadToEnd()
$sr.Close()
$medxpertTasks = $medxpertJson | ConvertFrom-Json

$sr = [System.IO.StreamReader]::new((Join-Path $baseDir "medxpertqa\db.json"))
$medxpertDbJson = $sr.ReadToEnd()
$sr.Close()
$medxpertDb = $medxpertDbJson | ConvertFrom-Json

Write-Host "MedXpertQA: $($medxpertTasks.Count) tasks" -ForegroundColor Green

# Process MedXpertQA
Write-Host "Processing MedXpertQA..." -ForegroundColor Cyan
$medxpertConsultation = @()
$qaPairs = $medxpertDb.qa_pairs

foreach ($task in $medxpertTasks) {
    $task_id = $task.id
    $ticket = $task.ticket
    $qa_data = $qa_pairs.$task_id
    $answer = if ($qa_data.answer) { $qa_data.answer } else { "Not provided" }
    $medical_task = if ($qa_data.medical_task) { $qa_data.medical_task } else { "General" }

    $consultationTask = [PSCustomObject]@{
        id = $task_id
        task_type = "specialist_consultation"
        consultation_scenario = "specialist_consultation"
        question = "Patient asks: $ticket"
        answer = "Doctor answers: $answer"
        domain = "clinical/consultation"
        ticket = $ticket
        original_format = "MedXpertQA"
        medical_task = $medical_task
        description = [PSCustomObject]@{
            purpose = "Medical knowledge QA consultation"
            relevant_policies = $null
            notes = "Medical Task: $medical_task"
        }
        user_scenario = [PSCustomObject]@{
            persona = $null
            instructions = [PSCustomObject]@{
                task_instructions = $ticket
                domain = "clinical"
                reason_for_call = "Medical consultation"
                known_info = if ($task.user_scenario.instructions.known_info) { $task.user_scenario.instructions.known_info } else { "" }
                unknown_info = $null
            }
        }
        initial_state = $null
        evaluation_criteria = $null
        annotations = $null
    }
    $medxpertConsultation += $consultationTask

    # Progress indicator
    if ($medxpertConsultation.Count % 500 -eq 0) {
        Write-Host "  Processed $($medxpertConsultation.Count) tasks..." -ForegroundColor DarkYellow
    }
}

# Save MedXpertQA consultation paradigm
$medxpertOutput = Join-Path $baseDir "medxpertqa\consultation_paradigm.json"
$medxpertConsultation | ConvertTo-Json -Depth 10 -Compress | Out-File -FilePath $medxpertOutput -Encoding UTF8
Write-Host "Created: $medxpertOutput" -ForegroundColor Yellow

# Load ProdMedBench
Write-Host "Loading ProdMedBench (1000 tasks)..." -ForegroundColor Yellow
$sr = [System.IO.StreamReader]::new((Join-Path $baseDir "prodmedbench\tasks.json"))
$prodmedJson = $sr.ReadToEnd()
$sr.Close()
$prodmedTasks = $prodmedJson | ConvertFrom-Json

$sr = [System.IO.StreamReader]::new((Join-Path $baseDir "prodmedbench\db.json"))
$prodmedDbJson = $sr.ReadToEnd()
$sr.Close()
$prodmedDb = $prodmedDbJson | ConvertFrom-Json

Write-Host "ProdMedBench: $($prodmedTasks.Count) tasks" -ForegroundColor Green

# Process ProdMedBench
Write-Host "Processing ProdMedBench..." -ForegroundColor Cyan
$prodmedConsultation = @()
$qaPairs = $prodmedDb.qa_pairs

foreach ($task in $prodmedTasks) {
    $task_id = $task.id
    $ticket = $task.ticket
    $qa_data = $qa_pairs.$task_id
    $answer = if ($qa_data.answer) { $qa_data.answer } else { "Not provided" }
    $options = if ($qa_data.options) { $qa_data.options } else { "" }
    $cot = if ($qa_data.cot) { $qa_data.cot } else { "" }

    $consultationTask = [PSCustomObject]@{
        id = $task_id
        task_type = "mcq_screening"
        consultation_scenario = "differential_diagnosis"
        question = "Patient asks: $ticket"
        answer = "Doctor answers: $answer"
        domain = "clinical/consultation"
        ticket = $ticket
        original_format = "ProdMedBench"
        options = $options
        cot = $cot
        description = [PSCustomObject]@{
            purpose = "Differential diagnosis MCQ screening"
            relevant_policies = $null
            notes = "Multiple choice with reasoning"
        }
        user_scenario = [PSCustomObject]@{
            persona = $null
            instructions = [PSCustomObject]@{
                task_instructions = $ticket
                domain = "clinical"
                reason_for_call = "Medical consultation"
                known_info = "MCQ format"
                unknown_info = $null
            }
        }
        initial_state = $null
        evaluation_criteria = $null
        annotations = $null
    }
    $prodmedConsultation += $consultationTask

    # Progress indicator
    if ($prodmedConsultation.Count % 250 -eq 0) {
        Write-Host "  Processed $($prodmedConsultation.Count) tasks..." -ForegroundColor DarkYellow
    }
}

# Save ProdMedBench consultation paradigm
$prodmedOutput = Join-Path $baseDir "prodmedbench\consultation_paradigm.json"
$prodmedConsultation | ConvertTo-Json -Depth 10 -Compress | Out-File -FilePath $prodmedOutput -Encoding UTF8
Write-Host "Created: $prodmedOutput" -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LARGE DATASET PROCESSING COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated Files:" -ForegroundColor White
Write-Host "  MedXpertQA: $medxpertOutput" -ForegroundColor White
Write-Host "  ProdMedBench: $prodmedOutput" -ForegroundColor White
Write-Host ""
Write-Host "Task Counts:" -ForegroundColor White
Write-Host "  MedXpertQA: $($medxpertConsultation.Count) tasks" -ForegroundColor White
Write-Host "  ProdMedBench: $($prodmedConsultation.Count) tasks" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
