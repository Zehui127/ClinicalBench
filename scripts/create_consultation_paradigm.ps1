# PowerShell script to create consultation paradigm files
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataDir = Join-Path $scriptDir "data"
$baseDir = Join-Path $scriptDir "data\processed"

# Create directories (skip - already exist)
Write-Host "Loading source files..." -ForegroundColor Cyan

# Load MedAgentBench using .NET StreamReader for proper UTF-8 handling
$sr = [System.IO.StreamReader]::new((Join-Path $dataDir "clinical\tasks.json"))
$medAgentJson = $sr.ReadToEnd()
$sr.Close()
$medAgentTasks = $medAgentJson | ConvertFrom-Json

$sr = [System.IO.StreamReader]::new((Join-Path $dataDir "clinical\db.json"))
$medAgentDbJson = $sr.ReadToEnd()
$sr.Close()
$medAgentDb = $medAgentDbJson | ConvertFrom-Json

Write-Host "MedAgentBench: $($medAgentTasks.Count) tasks" -ForegroundColor Green

# Process MedAgentBench
$medAgentConsultation = @()
foreach ($task in $medAgentTasks) {
    $consultationTask = @{
        id = $task.id
        task_type = "core_consultation"
        consultation_scenario = "primary_care"
        question = "Patient asks: $($task.ticket)"
        answer = "Doctor answers: Please provide the patient information."
        domain = "clinical/consultation"
        ticket = $task.ticket
        original_format = "MedAgentBench"
        description = @{
            purpose = "Free-form clinical consultation"
            relevant_policies = $null
            notes = if ($task.description.notes) { $task.description.notes } else { "Patient information lookup" }
        }
        user_scenario = @{
            persona = $null
            instructions = @{
                task_instructions = $task.ticket
                domain = "clinical"
                reason_for_call = "Patient consultation"
                known_info = $task.user_scenario.instructions.known_info
                unknown_info = $null
            }
        }
        initial_state = $null
        evaluation_criteria = $null
        annotations = $null
    }
    $medAgentConsultation += $consultationTask
}

# Save MedAgentBench consultation paradigm
$medAgentOutput = Join-Path $baseDir "medagentbench\consultation_paradigm.json"
$medAgentConsultation | ConvertTo-Json -Depth 10 | Out-File -FilePath $medAgentOutput -Encoding UTF8
Write-Host "Created: $medAgentOutput" -ForegroundColor Yellow

# Load and Process PhysioNet (small dataset, already read)
Write-Host "Processing PhysioNet..." -ForegroundColor Cyan

$physioNetTasks = @(
    @{id="physionet_001"; question="What is the creatinine level of patient 10032?"; answer="1.2 mg/dL"; patient_id="10032"; lab_type="Chemistry"},
    @{id="physionet_002"; question="What is the heart rate of patient 10058?"; answer="86 bpm"; patient_id="10058"; lab_type="Vital Signs"},
    @{id="physionet_003"; question="What is the diagnosis for patient 10147?"; answer="Sepsis"; patient_id="10147"; lab_type="Diagnosis"},
    @{id="physionet_004"; question="What is the SpO2 level of patient 10256?"; answer="94%"; patient_id="10256"; lab_type="Vital Signs"},
    @{id="physionet_005"; question="What is the glucose level of patient 10389?"; answer="142 mg/dL"; patient_id="10389"; lab_type="Chemistry"},
    @{id="physionet_006"; question="What is the blood pressure of patient 10421?"; answer="120/80 mmHg"; patient_id="10421"; lab_type="Vital Signs"},
    @{id="physionet_007"; question="What is the WBC count of patient 10567?"; answer="11.2 K/uL"; patient_id="10567"; lab_type="Hematology"},
    @{id="physionet_008"; question="What is the platelet count of patient 10689?"; answer="180 x10^3/uL"; patient_id="10689"; lab_type="Hematology"},
    @{id="physionet_009"; question="What is the potassium level of patient 10723?"; answer="4.2 mEq/L"; patient_id="10723"; lab_type="Chemistry"},
    @{id="physionet_010"; question="What is the respiratory rate of patient 10845?"; answer="18 breaths/min"; patient_id="10845"; lab_type="Vital Signs"}
)

$physioNetConsultation = @()
foreach ($qa in $physioNetTasks) {
    $consultationTask = @{
        id = $qa.id
        task_type = "structured_query"
        consultation_scenario = "pre_consultation_data"
        question = "Nurse asks: $($qa.question)"
        answer = "Doctor answers: $($qa.answer)"
        domain = "clinical/consultation"
        ticket = $qa.question
        original_format = "PhysioNet"
        structured_query = @{
            patient_id = $qa.patient_id
            indicators = @($qa.lab_type)
            query_type = "lab_result_lookup"
        }
        description = @{
            purpose = "Pre-consultation data retrieval"
            relevant_policies = $null
            notes = "Patient: $($qa.patient_id), Type: $($qa.lab_type)"
        }
        user_scenario = @{
            persona = $null
            instructions = @{
                task_instructions = $qa.question
                domain = "clinical"
                reason_for_call = "Patient data lookup"
                known_info = "Patient: $($qa.patient_id), Type: $($qa.lab_type)"
                unknown_info = $null
            }
        }
        initial_state = $null
        evaluation_criteria = $null
        annotations = $null
    }
    $physioNetConsultation += $consultationTask
}

$physioOutput = Join-Path $baseDir "physionet\consultation_paradigm.json"
$physioNetConsultation | ConvertTo-Json -Depth 10 | Out-File -FilePath $physioOutput -Encoding UTF8
Write-Host "Created: $physioOutput" -ForegroundColor Yellow

# Create Universal Template
Write-Host "Creating universal template..." -ForegroundColor Cyan

$universalTemplate = @{
    unified_consultation_paradigm = @{
        version = "1.0"
        description = "Unified medical consultation task paradigm integrating multiple medical datasets"
        task_types = @{
            core_consultation = "Free-form doctor-patient dialogue (MedAgentBench)"
            structured_query = "Pre-consultation data retrieval (PhysioNet)"
            mcq_screening = "Differential diagnosis with MCQ (ProdMedBench)"
            specialist_consultation = "Medical knowledge QA consultation (MedXpertQA)"
        }
        mandatory_fields = @{
            id = "unique_task_identifier"
            task_type = "core_consultation|structured_query|mcq_screening|specialist_consultation"
            question = "consultation_question"
            answer = "consultation_answer"
            domain = "clinical/consultation"
        }
        consultation_workflow = @{
            step_1_pre_consultation = "Structured query to retrieve patient data (PhysioNet)"
            step_2_primary_care = "Free-form Q&A for initial assessment (MedAgentBench)"
            step_3_specialist = "Specialist consultation for complex cases (MedXpertQA)"
            step_4_screening = "MCQ with CoT for differential diagnosis (ProdMedBench)"
            step_5_resolution = "Final diagnosis/advice in natural language"
        }
        dataset_mapping = @{
            medagentbench = "8 tasks - Core consultation (primary_care)"
            medxpertqa = "2450 tasks - Specialist consultation (specialist_consultation)"
            physionet = "10 tasks - Structured query (pre_consultation_data)"
            prodmedbench = "1000 tasks - MCQ screening (differential_diagnosis)"
        }
    }
}

$templateOutput = Join-Path $baseDir "universal_template\universal_consultation_template.json"
$universalTemplate | ConvertTo-Json -Depth 10 | Out-File -FilePath $templateOutput -Encoding UTF8
Write-Host "Created: $templateOutput" -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RECONSTRUCTION COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated Files:" -ForegroundColor White
Write-Host "  MedAgentBench: $medAgentOutput" -ForegroundColor White
Write-Host "  PhysioNet: $physioOutput" -ForegroundColor White
Write-Host "  Universal Template: $templateOutput" -ForegroundColor White
Write-Host ""
Write-Host "Task Counts:" -ForegroundColor White
Write-Host "  MedAgentBench: $($medAgentConsultation.Count) tasks" -ForegroundColor White
Write-Host "  PhysioNet: $($physioNetConsultation.Count) tasks" -ForegroundColor White
Write-Host ""
Write-Host "Note: MedXpertQA and ProdMedBench require manual processing" -ForegroundColor Yellow
Write-Host "due to large file sizes (2450 and 1000 tasks respectively)." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
