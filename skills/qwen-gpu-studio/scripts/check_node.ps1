# Quick Health Check for Remote GPU Node (192.168.1.152)
Write-Host "=== Checking Remote Node: AMD RX 6600 XT ===" -ForegroundColor Cyan

$remoteScript = @'
Write-Host "`n[GPU Status]" -ForegroundColor Green
Get-CimInstance Win32_VideoController | Format-Table Name, DriverVersion, Status
Write-Host "[Storage Space]" -ForegroundColor Green
Get-PSDrive C, D -ErrorAction SilentlyContinue | Format-Table Root, @{N="FreeGB";E={[math]::Round($_.Free/1GB,1)}}, @{N="UsedGB";E={[math]::Round($_.Used/1GB,1)}}
Write-Host "[RAM Usage]" -ForegroundColor Green
Get-CimInstance Win32_OperatingSystem | Format-Table @{N="TotalRAM_GB";E={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}, @{N="FreeRAM_GB";E={[math]::Round($_.FreePhysicalMemory/1MB,1)}}
'@

$bytes = [System.Text.Encoding]::Unicode.GetBytes($remoteScript)
$encoded = [Convert]::ToBase64String($bytes)

ssh itx "powershell -NoProfile -EncodedCommand $encoded"
