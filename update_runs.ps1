clear

# Change to the script's directory
$currentPath = Split-Path -Parent -Path $MyInvocation.MyCommand.Definition
$scriptPath = Split-Path -Parent -Path $currentPath
Set-Location -Path $scriptPath

# Listing .json files in the specified directory
$presetsPath = "$scriptPath\Fooocus\presets"
$jsonFiles = Get-ChildItem -Path $presetsPath -Filter "*.json"

# Iterate over each .json file
foreach ($file in $jsonFiles) {
    # Extract the preset name (without extension)
    $preset = [System.IO.Path]::GetFileNameWithoutExtension($file.FullName)

    # Check and create run_$preset.bat if not exists
    $batFilePath = "$scriptPath\run_$preset.bat"
    if (-not (Test-Path -Path $batFilePath)) {
        $batContent = "@echo off`r`ncd /d %~dp0`r`n`r`n.\python_embeded\python.exe -s Fooocus\entry_with_update.py --preset $preset`r`npause"
        Set-Content -Path $batFilePath -Value $batContent
    }
}

# Print all .json files with an index
for ($i = 0; $i -lt $jsonFiles.Count; $i++) {
    Write-Host "$($i+1): $($jsonFiles[$i].Name)"
}

# User input to choose a file
[int]$userChoice = 0
if ($userChoice -eq 0) {
    while ($userChoice -lt 1 -or $userChoice -gt $jsonFiles.Count) {
        $userChoice = Read-Host "Enter the number of the preset you want to choose"
    }
}

# Extract the chosen file name (without extension)
$chosen_preset = [System.IO.Path]::GetFileNameWithoutExtension($jsonFiles[$userChoice - 1].FullName)

# Display the chosen preset
Write-Host "Running Fooocus with chosen preset: $chosen_preset"

# Build the batch file name
$batchFileName = "run_$chosen_preset.bat"

# Check if the batch file exists
if (Test-Path $batchFileName) {
    # Run the batch file in a new Command Prompt window
    Start-Process "cmd.exe" -ArgumentList "/c $batchFileName" -WindowStyle Normal
} else {
    Write-Host "Batch file not found: $batchFileName"
}