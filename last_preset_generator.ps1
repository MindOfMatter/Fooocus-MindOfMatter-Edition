clear


# Navigate to outputs directory
$scriptPath = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$outputsPath = Join-Path -Path $scriptPath -ChildPath "outputs"

# Find all log.html files within the nested directories and sort them by LastWriteTime
$logFiles = Get-ChildItem -Path $outputsPath -Filter "log.html" -Recurse | Sort-Object LastWriteTime -Descending

# Check if any log.html files were found
if ($logFiles.Count -gt 0) {
    # Get the path of the most recent log.html file
    $latestLogFile = $logFiles[0].FullName
    Write-Host "Latest log file: $latestLogFile"
} else {
    Write-Host "No log.html files found in the outputs directory."
}

# Extract data from the latest log file
# Note: Actual extraction -Path logic depends on HTML structure and might require additional tools or a custom function
# Load the content of the log file
$logContent = Get-Content $latestLogFile -Raw

# Define the regex pattern to find the content passed to to_clipboard function
$pattern = 'to_clipboard\(''([^'']+)''\)' # Adjust the pattern to match your HTML structure

# Perform the regex match to find the first occurrence
if ($logContent -match $pattern) {
    # Extract the first match group, which is the content of to_clipboard
    $matchedContent = $matches[1]

    # Decode and parse the JSON content
    try {
        $decodedContent = [System.Net.WebUtility]::UrlDecode($matchedContent)
        $jsonObject = $decodedContent | ConvertFrom-Json
    } catch {
        Write-Host "Error in parsing or converting JSON"
    }
} else {
    Write-Host "No match found"
}

# Other parts of the script remain the same

# Assuming $jsonObject is your decoded JSON input
$template = @{
    default_model = if ($jsonObject.'Base Model') { $jsonObject.'Base Model' } else { "None" }
    default_refiner = if ($jsonObject.'Refiner Model') { $jsonObject.'Refiner Model' } else { "None" }
    default_refiner_switch = if ($jsonObject.'Refiner Switch') { $jsonObject.'Refiner Switch' } else { 0.5 }
    default_image_number = 1
    default_max_image_number = 80
    default_loras_min_weight = -5
    default_loras_max_weight = 5
    default_loras_max_number = 80
    default_cfg_scale = if ($jsonObject.'CFG Scale') { $jsonObject.'CFG Scale' } else { 5.0 }
    default_loras = @()
    default_sample_sharpness = 2.0
    default_sampler = if ($jsonObject.'Sampler') { $jsonObject.'Sampler' } else { "dpmpp_2m_sde_gpu" }
    default_scheduler = if ($jsonObject.'Scheduler') { $jsonObject.'Scheduler' } else { "karras" }
    default_performance = if ($jsonObject.'Performance') { $jsonObject.'Performance' } else { "Speed" }
    default_prompt = if ($jsonObject.Prompt) { $jsonObject.Prompt } else { "None" }
    default_prompt_negative = if ($jsonObject.'Negative Prompt') { $jsonObject.'Negative Prompt' } else { "None" }
    default_styles = @()
    default_aspect_ratio = if ($jsonObject.'Aspect Ratio') { $jsonObject.'Aspect Ratio' } else { "1200*900" }
}

# Handle Styles Array
if ($jsonObject.Styles -and $jsonObject.Styles -ne '[]') {
    $stylesArray = $jsonObject.Styles.Trim('[',']') -split ','
    foreach ($style in $stylesArray) {
        $trimmedStyle = $style.Trim().Trim("'")
        $template.default_styles += $trimmedStyle
    }
} else {
    $template.default_styles = @("Default Style")
}

# Process LoRA entries
foreach ($prop in $jsonObject.PSObject.Properties) {
    if ($prop.Name -match '^LoRA \d+$') {
        $split = $prop.Value -split ' : '
        $numberString = $split[1].Replace(',', '.')
        try {
            $number = [double]::Parse($numberString, [Globalization.CultureInfo]::InvariantCulture)
            $template.default_loras += ,@($split[0], $number)
        } catch {
            Write-Host "Failed to parse number: $numberString"
        }
    }
}

function Format-Json {
    param(
        [Parameter(Mandatory = $true)]
        [string]$json
    )

    $decodedJson = $json | ConvertFrom-Json
    $formattedJson = $decodedJson | ConvertTo-Json -Depth 10

    # Simplify the replacements to match the specified format
    $formattedJson = $formattedJson -replace '": "', '": ' -replace ' {2,}', ' ' -replace '\r?\n', "`n" -replace '`n{2,}', "`n" -replace '`n(\s*)("|\})', "`n$1$2" -replace '`n(\s*)\[', "`n$1["

    return $formattedJson
}

# Convert and format JSON
$structuredJson = $template | ConvertTo-Json -Depth 10 -Compress
$formattedJson = Format-Json -json $structuredJson

# Save the JSON
$savePath = Join-Path -Path $scriptPath -ChildPath "presets\last.json"
$formattedJson | Out-File -FilePath $savePath -Encoding utf8
