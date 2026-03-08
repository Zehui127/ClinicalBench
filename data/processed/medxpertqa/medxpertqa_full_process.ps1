# ========================================
# MedXpertQA Full Processing Script
# Clones repo, processes data into tau2-bench format
# ========================================

# Configuration Section - Modify these paths as needed
# ========================================
$Config = @{
    # GitHub repository URL
    RepoUrl = "https://github.com/TsinghuaC3I/MedXpertQA.git"

    # Local paths
    ProjectRoot = "C:\Users\方正\tau2-bench"
    RawDataRoot = "C:\Users\方正\tau2-bench\data\raw"
    ProcessedOutput = "C:\Users\方正\tau2-bench\data\processed\medxpertqa"

    # Repository specific paths
    RepoName = "MedXpertQA"
    RepoPath = "C:\Users\方正\tau2-bench\data\raw\MedXpertQA"

    # Processing options
    MaxRetries = 3
    CreateBackup = $true
    Verbose = $true
}

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to write log
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    $logMessage | Out-File -FilePath (Join-Path $Config.ProcessedOutput "process_log_medxpertqa.txt") -Append -Encoding UTF8
    if ($Config.Verbose) {
        $color = switch ($Level) {
            "ERROR" { "Red" }
            "WARNING" { "Yellow" }
            "SUCCESS" { "Green" }
            "INFO" { "Cyan" }
            default { "White" }
        }
        Write-ColorOutput $logMessage $color
    }
}

# Function to check if Git is installed
function Test-GitInstalled {
    try {
        $gitVersion = git --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Git is installed: $gitVersion" "SUCCESS"
            return $true
        }
    } catch {
        # Ignore error
    }
    Write-Log "Git is not installed or not in PATH" "ERROR"
    return $false
}

# Function to clone repository with retry
function Invoke-GitCloneWithRetry {
    param(
        [string]$Url,
        [string]$Destination,
        [int]$MaxRetries = 3
    )

    Write-Log "Cloning repository from: $Url" "INFO"
    Write-Log "Destination: $Destination" "INFO"

    $retryCount = 0
    $success = $false

    while (-not $success -and $retryCount -lt $MaxRetries) {
        $retryCount++

        if ($retryCount -gt 1) {
            Write-Log "Retry attempt $retryCount of $MaxRetries..." "WARNING"
            Start-Sleep -Seconds 5
        }

        try {
            # Remove existing directory if it exists
            if (Test-Path $Destination) {
                Write-Log "Removing existing directory: $Destination" "INFO"
                Remove-Item -Path $Destination -Recurse -Force
            }

            # Create parent directory if it doesn't exist
            $parentDir = Split-Path -Parent $Destination
            if (-not (Test-Path $parentDir)) {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
            }

            # Clone the repository
            Write-Log "Executing: git clone $Url $Destination" "INFO"
            $result = git clone $Url $Destination 2>&1

            if ($LASTEXITCODE -eq 0) {
                Write-Log "Repository cloned successfully!" "SUCCESS"
                $success = $true
            } else {
                Write-Log "Git clone failed with exit code: $LASTEXITCODE" "ERROR"
                Write-Log "Output: $result" "ERROR"
            }
        } catch {
            Write-Log "Exception during git clone: $_" "ERROR"
        }
    }

    if (-not $success) {
        Write-Log "Failed to clone repository after $MaxRetries attempts" "ERROR"
        Write-ColorOutput ""
        Write-ColorOutput "========================================" "Yellow"
        Write-ColorOutput "TROUBLESHOOTING TIPS:" "Yellow"
        Write-ColorOutput "========================================" "Yellow"
        Write-ColorOutput "1. Check if Git is installed:" "White"
        Write-ColorOutput "   - Run: git --version" "Gray"
        Write-ColorOutput "   - If not found, install from: https://git-scm.com/download/win" "Gray"
        Write-ColorOutput ""
        Write-ColorOutput "2. Check network connection:" "White"
        Write-ColorOutput "   - Ensure you can access https://github.com" "Gray"
        Write-ColorOutput "   - Try opening the URL in a browser" "Gray"
        Write-ColorOutput ""
        Write-ColorOutput "3. Check firewall/proxy settings:" "White"
        Write-ColorOutput "   - Corporate networks may block Git" "Gray"
        Write-ColorOutput "   - Try using a different network" "Gray"
        Write-ColorOutput ""
        Write-ColorOutput "4. Try cloning manually:" "White"
        Write-ColorOutput "   git clone $($Config.RepoUrl) `"$($Config.RepoPath)`"" "Gray"
        Write-ColorOutput "========================================" "Yellow"
    }

    return $success
}

# Function to analyze dataset structure
function Get-DatasetStructure {
    param(
        [string]$RepoPath
    )

    Write-Log "Analyzing dataset structure..." "INFO"

    $structure = @{
        DataFiles = @()
        JsonFiles = @()
        CsvFiles = @()
        TxtFiles = @()
        MarkdownFiles = @()
        TotalFiles = 0
    }

    if (-not (Test-Path $RepoPath)) {
        Write-Log "Repository path does not exist: $RepoPath" "ERROR"
        return $structure
    }

    # Recursively find all data files
    Write-Log "Scanning for data files..." "INFO"

    $allFiles = Get-ChildItem -Path $RepoPath -Recurse -File |
        Where-Object { $_.Extension -match '\.(json|csv|txt|md|jsonl)$' }

    $structure.TotalFiles = $allFiles.Count

    foreach ($file in $allFiles) {
        $relativePath = $file.FullName.Substring($RepoPath.Length + 1)
        $fileInfo = @{
            Path = $file.FullName
            RelativePath = $relativePath
            Name = $file.Name
            Extension = $file.Extension
            Size = $file.Length
        }

        switch ($file.Extension) {
            ".json" { $structure.JsonFiles += $fileInfo }
            ".jsonl" { $structure.JsonFiles += $fileInfo }
            ".csv" { $structure.CsvFiles += $fileInfo }
            ".txt" { $structure.TxtFiles += $fileInfo }
            ".md" { $structure.MarkdownFiles += $fileInfo }
        }
        $structure.DataFiles += $fileInfo
    }

    Write-Log "Found $($structure.JsonFiles.Count) JSON files" "INFO"
    Write-Log "Found $($structure.CsvFiles.Count) CSV files" "INFO"
    Write-Log "Found $($structure.TxtFiles.Count) TXT files" "INFO"
    Write-Log "Found $($structure.MarkdownFiles.Count) Markdown files" "INFO"

    return $structure
}

# Function to examine a JSON file and extract sample data
function Get-JsonFileSample {
    param(
        [string]$FilePath,
        [int]$MaxSamples = 5
    )

    try {
        $content = Get-Content $FilePath -Raw -Encoding UTF8
        $data = $content | ConvertFrom-Json

        $sample = @{
            Path = $FilePath
            Type = "unknown"
            Fields = @()
            SampleData = @()
            IsArray = $false
            ArrayLength = 0
        }

        # Determine if it's an array
        if ($data -is [System.Array]) {
            $sample.IsArray = $true
            $sample.ArrayLength = $data.Count
            $sample.Type = "array"

            # Get sample entries
            $sampleCount = [Math]::Min($MaxSamples, $data.Count)
            for ($i = 0; $i -lt $sampleCount; $i++) {
                $sample.SampleData += $data[$i]
            }

            # Extract fields from first item
            if ($data.Count -gt 0) {
                $firstItem = $data[0]
                if ($firstItem.PSObject.Properties) {
                    $sample.Fields = $firstItem.PSObject.Properties.Name
                }
            }
        } elseif ($data.PSObject.Properties) {
            $sample.Type = "object"
            $sample.Fields = $data.PSObject.Properties.Name
            $sample.SampleData += $data
        }

        return $sample
    } catch {
        Write-Log "Error reading JSON file $FilePath : $_" "ERROR"
        return $null
    }
}

# Function to identify core data files
function Find-CoreDataFiles {
    param(
        [hashtable]$Structure
    )

    Write-Log "Identifying core data files..." "INFO"

    $coreFiles = @{
        PrimaryData = @()
        QAData = @()
        Metadata = @()
    }

    # Keywords to identify QA/data files
    $qaKeywords = @("qa", "question", "answer", "test", "eval", "dataset", "data")
    $metadataKeywords = @("readme", "license", "config", "setting", "info")

    # Check JSON files first
    foreach ($file in $structure.JsonFiles) {
        $fileName = $file.Name.ToLower()
        $relativePath = $file.RelativePath.ToLower()

        $isQAFile = $false
        foreach ($keyword in $qaKeywords) {
            if ($fileName -like "*$keyword*" -or $relativePath -like "*$keyword*") {
                $isQAFile = $true
                break
            }
        }

        if ($isQAFile) {
            # Get sample to verify it contains QA data
            $sample = Get-JsonFileSample -FilePath $file.Path
            if ($sample -and $sample.Fields.Count -gt 0) {
                $fieldNames = $sample.Fields -join " "
                if ($fieldNames -match "question|answer|query|response") {
                    $coreFiles.QAData += @{
                        File = $file
                        Sample = $sample
                    }
                    Write-Log "Found QA data file: $($file.RelativePath)" "SUCCESS"
                    Write-Log "  Fields: $($sample.Fields -join ', ')" "INFO"
                }
            }
        }
    }

    # Check CSV files
    foreach ($file in $structure.CsvFiles) {
        $fileName = $file.Name.ToLower()
        $isQAFile = $false
        foreach ($keyword in $qaKeywords) {
            if ($fileName -like "*$keyword*") {
                $isQAFile = $true
                break
            }
        }
        if ($isQAFile) {
            $coreFiles.QAData += @{
                File = $file
                Sample = $null
            }
            Write-Log "Found CSV data file: $($file.RelativePath)" "INFO"
        }
    }

    Write-Log "Identified $($coreFiles.QAData.Count) core QA data file(s)" "SUCCESS"

    return $coreFiles
}

# Function to process QA data into tau2-bench format
function ConvertTo-Tau2Format {
    param(
        [hashtable]$CoreFiles,
        [string]$RepoPath
    )

    Write-Log "Converting data to tau2-bench format..." "INFO"

    $tasks = @()
    $qaPairs = @{}
    $taskIdCounter = 1

    foreach ($qaData in $CoreFiles.QAData) {
        $file = $qaData.File
        $sample = $qaData.Sample

        Write-Log "Processing: $($file.RelativePath)" "INFO"

        # Determine processing based on file type
        if ($file.Extension -eq ".json" -or $file.Extension -eq ".jsonl") {
            $result = Process-JsonFile -File $file -Sample $sample -TaskIdRef ([ref]$taskIdCounter)
            $tasks += $result.Tasks
            foreach ($pair in $result.QAPairs.GetEnumerator()) {
                $qaPairs[$pair.Key] = $pair.Value
            }
        } elseif ($file.Extension -eq ".csv") {
            $result = Process-CsvFile -File $file -TaskIdRef ([ref]$taskIdCounter)
            $tasks += $result.Tasks
            foreach ($pair in $result.QAPairs.GetEnumerator()) {
                $qaPairs[$pair.Key] = $pair.Value
            }
        }
    }

    return @{
        Tasks = $tasks
        QAPairs = $qaPairs
    }
}

# Function to process JSON file
function Process-JsonFile {
    param(
        [hashtable]$File,
        [hashtable]$Sample,
        [ref]$TaskIdRef
    )

    Write-Log "Processing JSON file: $($File.Name)" "INFO"

    $tasks = @()
    $qaPairs = @{}

    try {
        $content = Get-Content $File.Path -Raw -Encoding UTF8
        $data = $content | ConvertFrom-Json

        $dataArray = if ($data -is [System.Array]) { $data } else { @($data) }

        foreach ($item in $dataArray) {
            $taskId = "medxpertqa_{0:D3}" -f $TaskIdRef.Value
            $TaskIdRef.Value++

            # Extract question and answer from item
            $question = $null
            $answer = $null
            $domain = "medical"
            $difficulty = "unknown"

            # Try to find common field names
            foreach ($prop in $item.PSObject.Properties) {
                $propName = $prop.Name.ToLower()
                if ($propName -match "question|query|prompt|input") {
                    $question = $prop.Value
                }
                if ($propName -match "answer|response|output|solution|target") {
                    $answer = $prop.Value
                }
                if ($propName -match "domain|category|subject|topic") {
                    $domain = $prop.Value
                }
                if ($propName -match "difficulty|level|complexity") {
                    $difficulty = $prop.Value
                }
            }

            # Skip if no question found
            if ([string]::IsNullOrWhiteSpace($question)) {
                Write-Log "Skipping item - no question field found" "WARNING"
                continue
            }

            # Create task (without answer)
            $task = @{
                id = $taskId
                description = @{
                    purpose = "Medical knowledge QA"
                    relevant_policies = $null
                    notes = "Domain: $domain, Difficulty: $difficulty"
                }
                user_scenario = @{
                    persona = $null
                    instructions = @{
                        task_instructions = $question
                        domain = "clinical"
                        reason_for_call = "Medical consultation"
                        known_info = $null
                        unknown_info = $null
                    }
                }
                ticket = $question
                initial_state = $null
                evaluation_criteria = $null
                annotations = $null
            }
            $tasks += $task

            # Create QA pair entry for db.json
            $qaPairs[$taskId] = @{
                question = $question
                answer = $answer
                domain = $domain
                difficulty = $difficulty
                task_id = $taskId
            }

            Write-Log "Created task: $taskId" "INFO"
        }

    } catch {
        Write-Log "Error processing JSON file: $_" "ERROR"
    }

    return @{
        Tasks = $tasks
        QAPairs = $qaPairs
    }
}

# Function to process CSV file
function Process-CsvFile {
    param(
        [hashtable]$File,
        [ref]$TaskIdRef
    )

    Write-Log "Processing CSV file: $($File.Name)" "INFO"

    $tasks = @()
    $qaPairs = @{}

    try {
        $csvData = Import-Csv -Path $File.Path -Encoding UTF8

        foreach ($row in $csvData) {
            $taskId = "medxpertqa_{0:D3}" -f $TaskIdRef.Value
            $TaskIdRef.Value++

            # Get columns
            $columns = $row.PSObject.Properties.Name

            # Find question and answer columns
            $question = $null
            $answer = $null
            $domain = "medical"
            $difficulty = "unknown"

            foreach ($col in $columns) {
                $colLower = $col.ToLower()
                if ($colLower -match "question|query|prompt") {
                    $question = $row.$col
                }
                if ($colLower -match "answer|response|solution") {
                    $answer = $row.$col
                }
                if ($colLower -match "domain|category|subject") {
                    $domain = $row.$col
                }
                if ($colLower -match "difficulty|level") {
                    $difficulty = $row.$col
                }
            }

            if ([string]::IsNullOrWhiteSpace($question)) {
                Write-Log "Skipping CSV row - no question column found" "WARNING"
                continue
            }

            # Create task
            $task = @{
                id = $taskId
                description = @{
                    purpose = "Medical knowledge QA"
                    relevant_policies = $null
                    notes = "Domain: $domain, Difficulty: $difficulty"
                }
                user_scenario = @{
                    persona = $null
                    instructions = @{
                        task_instructions = $question
                        domain = "clinical"
                        reason_for_call = "Medical consultation"
                        known_info = $null
                        unknown_info = $null
                    }
                }
                ticket = $question
                initial_state = $null
                evaluation_criteria = $null
                annotations = $null
            }
            $tasks += $task

            # Create QA pair
            $qaPairs[$taskId] = @{
                question = $question
                answer = $answer
                domain = $domain
                difficulty = $difficulty
                task_id = $taskId
            }

            Write-Log "Created task: $taskId" "INFO"
        }

    } catch {
        Write-Log "Error processing CSV file: $_" "ERROR"
    }

    return @{
        Tasks = $tasks
        QAPairs = $qaPairs
    }
}

# Function to save processed files
function Save-ProcessedFiles {
    param(
        [array]$Tasks,
        [hashtable]$QAPairs,
        [string]$OutputDir
    )

    Write-Log "Saving processed files..." "INFO"

    # Save tasks.json
    $tasksJson = $Tasks | ConvertTo-Json -Depth 10
    $tasksPath = Join-Path $OutputDir "tasks.json"
    $tasksJson | Out-File -FilePath $tasksPath -Encoding UTF8 -NoNewline
    Write-Log "Saved tasks.json with $($Tasks.Count) tasks" "SUCCESS"

    # Save db.json
    $dbStructure = @{
        qa_pairs = [PSCustomObject]$QAPairs
    }
    $dbJson = $dbStructure | ConvertTo-Json -Depth 10
    $dbPath = Join-Path $OutputDir "db.json"
    $dbJson | Out-File -FilePath $dbPath -Encoding UTF8 -NoNewline
    Write-Log "Saved db.json with $($QAPairs.Count) QA pairs" "SUCCESS"

    # Create empty policy.md
    $policyPath = Join-Path $OutputDir "policy.md"
    "# MedXpertQA Clinical Policy`n`n> Note: This dataset focuses on medical knowledge QA. No specific clinical policies are defined.`n`n## General Guidelines`n`n- Answers should be based on established medical knowledge and guidelines`n- Clinical decisions should consider current best practices`n- When uncertain, recommend consulting additional sources or specialists`n" | Out-File -FilePath $policyPath -Encoding UTF8
    Write-Log "Created policy.md" "SUCCESS"
}

# Function to verify processed files
function Test-ProcessedFiles {
    param(
        [string]$OutputDir
    )

    Write-Log "Verifying processed files..." "INFO"

    $allValid = $true

    # Check tasks.json
    $tasksPath = Join-Path $OutputDir "tasks.json"
    if (Test-Path $tasksPath) {
        try {
            $tasks = Get-Content $tasksPath -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Log "tasks.json: Valid JSON with $($tasks.Count) tasks" "SUCCESS"

            # Check for no answers
            $hasAnswers = $false
            foreach ($task in $tasks) {
                if ($task.annotations -ne $null -or $task.evaluation_criteria -ne $null) {
                    $hasAnswers = $true
                    break
                }
            }
            if ($hasAnswers) {
                Write-Log "WARNING: tasks.json may still contain answer fields" "WARNING"
            }
        } catch {
            Write-Log "tasks.json: Invalid JSON - $_" "ERROR"
            $allValid = $false
        }
    } else {
        Write-Log "tasks.json: File not found" "ERROR"
        $allValid = $false
    }

    # Check db.json
    $dbPath = Join-Path $OutputDir "db.json"
    if (Test-Path $dbPath) {
        try {
            $db = Get-Content $dbPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $qaCount = ($db.qa_pairs.PSObject.Properties.Name).Count
            Write-Log "db.json: Valid JSON with $qaCount QA pairs" "SUCCESS"
        } catch {
            Write-Log "db.json: Invalid JSON - $_" "ERROR"
            $allValid = $false
        }
    } else {
        Write-Log "db.json: File not found" "ERROR"
        $allValid = $false
    }

    # Check policy.md
    $policyPath = Join-Path $OutputDir "policy.md"
    if (Test-Path $policyPath) {
        Write-Log "policy.md: File exists" "SUCCESS"
    } else {
        Write-Log "policy.md: File not found" "WARNING"
    }

    # Check consistency
    if (Test-Path $tasksPath -and Test-Path $dbPath) {
        try {
            $tasks = Get-Content $tasksPath -Raw -Encoding UTF8 | ConvertFrom-Json
            $db = Get-Content $dbPath -Raw -Encoding UTF8 | ConvertFrom-Json

            $taskIds = @($tasks | ForEach-Object { $_.id })
            $qaIds = @($db.qa_pairs.PSObject.Properties.Name)

            $missing = $taskIds | Where-Object { $_ -notin $qaIds }
            $extra = $qaIds | Where-Object { $_ -notin $taskIds }

            if ($missing.Count -gt 0) {
                Write-Log "WARNING: $($missing.Count) tasks in tasks.json not found in db.json" "WARNING"
            }
            if ($extra.Count -gt 0) {
                Write-Log "WARNING: $($extra.Count) QA pairs in db.json not found in tasks.json" "WARNING"
            }
            if ($missing.Count -eq 0 -and $extra.Count -eq 0) {
                Write-Log "Consistency check: All tasks match QA pairs" "SUCCESS"
            }
        } catch {
            Write-Log "Consistency check failed: $_" "ERROR"
        }
    }

    return $allValid
}

# Function to create backup
function New-DataBackup {
    param(
        [string]$SourcePath,
        [string]$OutputDir
    )

    Write-Log "Creating raw data backup..." "INFO"

    try {
        $backupPath = Join-Path $OutputDir "MedXpertQA_raw_backup.zip"
        if (Test-Path $backupPath) {
            Remove-Item $backupPath -Force
        }

        Compress-Archive -Path $SourcePath -DestinationPath $backupPath -Force
        $backupSize = (Get-Item $backupPath).Length / 1MB
        Write-Log "Created backup: $backupPath ($([math]::Round($backupSize, 2)) MB)" "SUCCESS"
    } catch {
        Write-Log "Backup creation failed: $_" "WARNING"
    }
}

# ========================================
# MAIN EXECUTION
# ========================================

function Main {
    Write-ColorOutput ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "  MedXpertQA Processing Script" "Cyan"
    Write-ColorOutput "  Tau2-Bench Data Processor" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput ""

    # Initialize
    Write-Log "=== MedXpertQA Processing Started ===" "INFO"

    # Create output directory
    if (-not (Test-Path $Config.ProcessedOutput)) {
        New-Item -ItemType Directory -Path $Config.ProcessedOutput -Force | Out-Null
        Write-Log "Created output directory: $($Config.ProcessedOutput)" "SUCCESS"
    }

    # Step 1: Check Git installation
    Write-ColorOutput ""
    Write-ColorOutput "Step 1: Checking Git installation..." "Yellow"
    if (-not (Test-GitInstalled)) {
        Write-Log "Please install Git from https://git-scm.com/download/win" "ERROR"
        return 1
    }

    # Step 2: Clone repository
    Write-ColorOutput ""
    Write-ColorOutput "Step 2: Cloning MedXpertQA repository..." "Yellow"
    $cloneSuccess = Invoke-GitCloneWithRetry -Url $Config.RepoUrl -Destination $Config.RepoPath -MaxRetries $Config.MaxRetries

    if (-not $cloneSuccess) {
        Write-Log "Failed to clone repository. Please try manually or check network connection." "ERROR"
        return 1
    }

    # Step 3: Analyze dataset structure
    Write-ColorOutput ""
    Write-ColorOutput "Step 3: Analyzing dataset structure..." "Yellow"
    $structure = Get-DatasetStructure -RepoPath $Config.RepoPath

    if ($structure.TotalFiles -eq 0) {
        Write-Log "No data files found in repository!" "ERROR"
        return 1
    }

    # Step 4: Identify core data files
    Write-ColorOutput ""
    Write-ColorOutput "Step 4: Identifying core data files..." "Yellow"
    $coreFiles = Find-CoreDataFiles -Structure $structure

    if ($coreFiles.QAData.Count -eq 0) {
        Write-Log "No QA data files found! Repository structure may be different than expected." "WARNING"
        Write-Log "Listing all JSON files for manual review:" "INFO"
        foreach ($file in $structure.JsonFiles) {
            Write-Log "  - $($file.RelativePath)" "INFO"
        }
    }

    # Step 5: Process data
    Write-ColorOutput ""
    Write-ColorOutput "Step 5: Processing data to tau2-bench format..." "Yellow"
    $convertedData = ConvertTo-Tau2Format -CoreFiles $coreFiles -RepoPath $Config.RepoPath

    if ($convertedData.Tasks.Count -eq 0) {
        Write-Log "No tasks were generated! Please check the data format." "ERROR"
        return 1
    }

    # Step 6: Save processed files
    Write-ColorOutput ""
    Write-ColorOutput "Step 6: Saving processed files..." "Yellow"
    Save-ProcessedFiles -Tasks $convertedData.Tasks -QAPairs $convertedData.QAPairs -OutputDir $Config.ProcessedOutput

    # Step 7: Create backup
    if ($Config.CreateBackup) {
        Write-ColorOutput ""
        Write-ColorOutput "Step 7: Creating raw data backup..." "Yellow"
        New-DataBackup -SourcePath $Config.RepoPath -OutputDir $Config.ProcessedOutput
    }

    # Step 8: Verify processed files
    Write-ColorOutput ""
    Write-ColorOutput "Step 8: Verifying processed files..." "Yellow"
    $isValid = Test-ProcessedFiles -OutputDir $Config.ProcessedOutput

    # Final summary
    Write-ColorOutput ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "Processing Complete!" "Green"
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput ""
    Write-ColorOutput "Summary:" "Green"
    Write-ColorOutput "  - Total tasks generated: $($convertedData.Tasks.Count)" "White"
    Write-ColorOutput "  - Total QA pairs: $($convertedData.QAPairs.Count)" "White"
    Write-ColorOutput "  - Output directory: $($Config.ProcessedOutput)" "White"
    Write-ColorOutput ""
    Write-ColorOutput "Files created:" "Green"
    Write-ColorOutput "  - tasks.json       (pure questions)" "White"
    Write-ColorOutput "  - db.json          (QA pair database)" "White"
    Write-ColorOutput "  - policy.md        (clinical guidelines)" "White"
    Write-ColorOutput "  - process_log_medxpertqa.txt" "White"
    if ($Config.CreateBackup) {
        Write-ColorOutput "  - MedXpertQA_raw_backup.zip" "White"
    }
    Write-ColorOutput ""

    if ($isValid) {
        Write-ColorOutput "✓ All validation checks passed!" "Green"
    } else {
        Write-ColorOutput "⚠ Some validation checks failed. Please review the log." "Yellow"
    }

    Write-Log "=== MedXpertQA Processing Completed ===" "INFO"
    Write-ColorOutput ""

    return 0
}

# Run main function
exit (Main)
