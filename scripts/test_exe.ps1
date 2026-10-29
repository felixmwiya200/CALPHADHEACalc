$p = Start-Process -FilePath "dist\PyCALPHAD_Suite\PyCALPHAD_Suite.exe" -PassThru
Start-Sleep -Seconds 2
$proc = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Success: Process $($proc.ProcessName) (PID: $($proc.Id)) is running normally."
    Stop-Process -Id $p.Id -Force
} else {
    Write-Host "Process terminated."
}
