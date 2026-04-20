$apiUrl = "https://omar-it-guardian.onrender.com/device"

# =========================
# DEVICE ID
# =========================
$configFile = "$PSScriptRoot\config.json"

if (Test-Path $configFile) {
    $config = Get-Content $configFile | ConvertFrom-Json
    $device_id = $config.device_id
} else {
    $device_id = [guid]::NewGuid().ToString()
    @{ device_id = $device_id } | ConvertTo-Json | Set-Content $configFile
}

# =========================
# SYSTEM INFO
# =========================
$hostname = $env:COMPUTERNAME
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$disk = (Get-PSDrive C).Free

# =========================
# SEND DATA
# =========================
$body = @{
    device_id  = $device_id
    hostname   = $hostname
    os_version = $os
    disk_free  = $disk
} | ConvertTo-Json

try {
    Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json"
    Write-Output "Data sent"
} catch {
    Write-Output "API error"
}


# =========================
# TASK SCHEDULER (ROBUST)
# =========================
$taskName = "IT-Guardian-Agent"

$existingTask = schtasks /Query /TN $taskName 2>$null

if ($LASTEXITCODE -ne 0) {

    $scriptPath = "$PSScriptRoot\agent.ps1"

    schtasks /Create `
        /SC MINUTE `
        /MO 5 `
        /TN $taskName `
        /TR "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`"" `
        /RL HIGHEST `
        /F

    # 🔥 IMPORTANT: Enable task explicitly
    schtasks /Change /TN $taskName /ENABLE

    Write-Output "Task created & enabled"
}
