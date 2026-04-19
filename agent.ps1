$apiUrl = "http://127.0.0.1:8000/device"

$hostname = $env:COMPUTERNAME
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$disk = (Get-PSDrive C).Free

$body = @{
    hostname = $hostname
    os_version = $os
    disk_free = $disk
} | ConvertTo-Json

Invoke-RestMethod -Uri $apiUrl -Method Post -Body $body -ContentType "application/json"