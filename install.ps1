# =========================
# INSTALL IT GUARDIAN AGENT
# =========================

$installPath = "C:\ProgramData\ITGuardian"

# create folder
if (!(Test-Path $installPath)) {
    New-Item -ItemType Directory -Path $installPath
}

# copy agent
Copy-Item "$PSScriptRoot\agent.ps1" "$installPath\agent.ps1" -Force

# create hidden runner
$vb = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -File ""$installPath\agent.ps1""", 0, False
"@

$vb | Out-File "$installPath\run_hidden.vbs"

# create task
schtasks /Delete /TN "IT-Guardian-Agent" /F 2>$null

schtasks /Create `
 /SC MINUTE `
 /MO 5 `
 /TN "IT-Guardian-Agent" `
 /TR "wscript.exe `"$installPath\run_hidden.vbs`"" `
 /RL HIGHEST `
 /F

Write-Output "Installation completed!"