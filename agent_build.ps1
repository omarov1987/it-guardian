$apiUrl = "https://omar-it-guardian.onrender.com/device"

$hostname = $env:COMPUTERNAME
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$disk = (Get-PSDrive C).Free

$body = @{
    hostname   = $hostname
    os_version = $os
    disk_free  = $disk
} | ConvertTo-Json

Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json"

# =========================
# CREATE TASK (AUTO START)
# =========================

$taskName = "IT-Guardian-Agent"

$action = New-ScheduledTaskAction -Execute "$PSScriptRoot\agent.exe"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1)
$trigger.Repetition.Interval = (New-TimeSpan -Minutes 5)
$trigger.Repetition.Duration = ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -Hidden

try {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force
} catch {
    # already exists
}