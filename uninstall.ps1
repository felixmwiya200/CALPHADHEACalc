# =============================================================================
# CALPHADHEACalc: Software Uninstaller Script (PowerShell)
# Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)
# =============================================================================

[CmdletBinding()]
param (
    [switch]$KeepMatlabPath
)

Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host "  CALPHADHEACalc: Software Uninstaller (PowerShell)                          " -ForegroundColor White
Write-Host "=============================================================================" -ForegroundColor Cyan
Write-Host ""

$DesktopFolder = [System.Environment]::GetFolderPath('Desktop')
$ProgramsFolder = [System.Environment]::GetFolderPath('Programs')

# 1. Remove Desktop Shortcuts
$l1 = Join-Path $DesktopFolder "CALPHADHEACalc.lnk"
$l2 = Join-Path $DesktopFolder "CALPHADHEACalc (MATLAB Desktop).lnk"
if (Test-Path $l1) {
    Remove-Item $l1 -Force
    Write-Host "  [REMOVED] Desktop Shortcut: $l1" -ForegroundColor Yellow
}
if (Test-Path $l2) {
    Remove-Item $l2 -Force
    Write-Host "  [REMOVED] Desktop Shortcut: $l2" -ForegroundColor Yellow
}

# 2. Remove Start Menu
$MenuDir = Join-Path $ProgramsFolder "CALPHADHEACalc"
if (Test-Path $MenuDir) {
    Remove-Item $MenuDir -Recurse -Force
    Write-Host "  [REMOVED] Start Menu Folder: $MenuDir" -ForegroundColor Yellow
}

# 3. Clean MATLAB Path
if (-not $KeepMatlabPath) {
    $MatlabCmd = Get-Command "matlab" -ErrorAction SilentlyContinue
    if ($MatlabCmd) {
        Write-Host "  Cleaning MATLAB search path..." -ForegroundColor Gray
        try {
            & "matlab" -batch "try, rmpath(genpath(pwd)); savepath; disp('[SUCCESS] MATLAB search path cleaned.'); catch ME, disp(ME.message); end" | Out-Null
            Write-Host "  [CLEANED] MATLAB search path restored." -ForegroundColor Green
        } catch {}
    }
}

Write-Host ""
Write-Host "Uninstallation completed successfully. Repository files were preserved." -ForegroundColor Green
Write-Host ""
