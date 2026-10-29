# build_suite.ps1
$ErrorActionPreference = 'SilentlyContinue'

# Stop any running process
Get-Process | Where-Object { $_.ProcessName -like "*PyCALPHAD*" } | Stop-Process -Force

Start-Sleep -Seconds 1

# Force delete old dist
if (Test-Path "dist\PyCALPHAD_Suite") {
    # Remove readonly flags if any
    Get-ChildItem -Path "dist\PyCALPHAD_Suite" -Recurse -Force | ForEach-Object {
        $_.Attributes = 'Normal'
    }
    Remove-Item -Path "dist\PyCALPHAD_Suite" -Recurse -Force
}

Write-Output "Dist cleaned. Building with PyInstaller..."
& pyinstaller --noconfirm PyCALPHAD_Suite.spec

if ($LASTEXITCODE -eq 0) {
    Write-Output "BUILD_SUCCESS"
} else {
    Write-Output "BUILD_FAILED with code $LASTEXITCODE"
}
