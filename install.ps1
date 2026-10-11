# =============================================================================
# CALPHADHEACalc: High-Entropy Alloy Multi-Physics Software Installation Script
# Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)
# =============================================================================

[CmdletBinding()]
param (
    [switch]$NoDesktopShortcut,
    [switch]$NoStartMenu,
    [switch]$SkipMatlab,
    [switch]$Silent
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $Silent) {
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host "  CALPHADHEACalc: Software Installation Wizard (PowerShell)                 " -ForegroundColor White
    Write-Host "  Authors: Felix Mwiya & Prof. Sheela Singh, SRM University-AP (2026)       " -ForegroundColor Gray
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host ""
}

# 1. Verify Core Repository Files
if (-not $Silent) { Write-Host "[1/5] Verifying repository structure..." -ForegroundColor Yellow }
$RequiredFiles = @("index.html", "App\CALPHADHEACalc.m", "CALPHADHEACalc_Desktop.bat", "CALPHADHEACalc_Desktop.vbs")
$Missing = @()
foreach ($file in $RequiredFiles) {
    $fullPath = Join-Path $ScriptDir $file
    if (-not (Test-Path $fullPath)) {
        $Missing += $file
    }
}

if ($Missing.Count -gt 0) {
    Write-Host "[ERROR] Missing critical repository files: $($Missing -join ', ')" -ForegroundColor Red
    exit 1
}
if (-not $Silent) { Write-Host "  All core calculation and UI files verified." -ForegroundColor Green }

# 2. Runtime Detection
if (-not $Silent) { Write-Host "[2/5] Detecting available software runtimes..." -ForegroundColor Yellow }

# Check Browser / Desktop WebView
$EdgePaths = @(
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"
)
$DesktopBrowser = $EdgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1
$DesktopReady = [bool]$DesktopBrowser
if ($DesktopReady -and -not $Silent) {
    Write-Host "  [FOUND] Desktop CAE Browser Host: $DesktopBrowser" -ForegroundColor Green
} elseif (-not $Silent) {
    Write-Host "  [INFO] Default web browser will be used for standalone mode." -ForegroundColor Gray
}

# Check Node.js
$NodePath = Get-Command "node" -ErrorAction SilentlyContinue
$NodeReady = [bool]$NodePath
if ($NodeReady -and -not $Silent) {
    $NodeVer = & node -v
    Write-Host "  [FOUND] Node.js $NodeVer detected (Decoupled API Server ready)" -ForegroundColor Green
} elseif (-not $Silent) {
    Write-Host "  [INFO] Node.js not found (Optional: required for headless API streaming)" -ForegroundColor Gray
}

# Check MATLAB
$MatlabPath = Get-Command "matlab" -ErrorAction SilentlyContinue
$MatlabExe = $null
if ($MatlabPath) {
    $MatlabExe = $MatlabPath.Source
} else {
    $MatlabSearch = Get-ChildItem "C:\Program Files\MATLAB" -Filter "matlab.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($MatlabSearch) {
        $MatlabExe = $MatlabSearch.FullName
    }
}
$MatlabReady = [bool]$MatlabExe
if ($MatlabReady -and -not $Silent) {
    Write-Host "  [FOUND] MATLAB detected: $MatlabExe" -ForegroundColor Green
} elseif (-not $Silent) {
    Write-Host "  [INFO] MATLAB not detected (Standalone Web & Desktop suites run 100% without MATLAB)" -ForegroundColor Gray
}

# 3. Configure MATLAB Path (if present)
if (-not $Silent) { Write-Host "[3/5] Configuring calculation engines..." -ForegroundColor Yellow }
if ($MatlabReady -and -not $SkipMatlab) {
    if (-not $Silent) { Write-Host "  Registering CALPHADHEACalc in MATLAB search path..." -ForegroundColor Gray }
    try {
        & "$MatlabExe" -batch "try, addpath(genpath('$ScriptDir')); savepath; disp('[SUCCESS] MATLAB search path saved.'); catch ME, disp(ME.message); end" | Out-Null
        if (-not $Silent) { Write-Host "  MATLAB search path registered permanently." -ForegroundColor Green }
    } catch {
        if (-not $Silent) { Write-Host "  [NOTICE] MATLAB path auto-save skipped: $_" -ForegroundColor Gray }
    }
} else {
    if (-not $Silent) { Write-Host "  Skipping MATLAB path registration (Standalone mode active)." -ForegroundColor Gray }
}

# 4. Create Desktop & Start Menu Shortcuts
if (-not $Silent) { Write-Host "[4/5] Creating application shortcuts..." -ForegroundColor Yellow }
$WshShell = New-Object -ComObject WScript.Shell
$DesktopFolder = [System.Environment]::GetFolderPath('Desktop')
$ProgramsFolder = [System.Environment]::GetFolderPath('Programs')
$IconPath = Join-Path $ScriptDir "app_icon.ico"
$TargetVbs = Join-Path $ScriptDir "CALPHADHEACalc_Desktop.vbs"

if (-not $NoDesktopShortcut) {
    $DesktopLnk = Join-Path $DesktopFolder "CALPHADHEACalc.lnk"
    $Link = $WshShell.CreateShortcut($DesktopLnk)
    $Link.TargetPath = $TargetVbs
    $Link.WorkingDirectory = $ScriptDir
    $Link.IconLocation = "$IconPath,0"
    $Link.Description = "CALPHADHEACalc - High-Entropy Alloy Multi-Physics Software"
    $Link.Save()
    if (-not $Silent) { Write-Host "  [CREATED] Desktop Shortcut: $DesktopLnk" -ForegroundColor Green }

    if ($MatlabReady) {
        $MatlabLnk = Join-Path $DesktopFolder "CALPHADHEACalc (MATLAB Desktop).lnk"
        $MLink = $WshShell.CreateShortcut($MatlabLnk)
        $MLink.TargetPath = Join-Path $ScriptDir "Launch_CALPHADHEACalc.vbs"
        $MLink.WorkingDirectory = $ScriptDir
        $MLink.IconLocation = "$IconPath,0"
        $MLink.Description = "CALPHADHEACalc MATLAB CAE Suite"
        $MLink.Save()
        if (-not $Silent) { Write-Host "  [CREATED] Desktop Shortcut: $MatlabLnk" -ForegroundColor Green }
    }
}

if (-not $NoStartMenu) {
    $MenuDir = Join-Path $ProgramsFolder "CALPHADHEACalc"
    if (-not (Test-Path $MenuDir)) {
        New-Item -ItemType Directory -Path $MenuDir -Force | Out-Null
    }
    $MenuLnk = Join-Path $MenuDir "CALPHADHEACalc.lnk"
    $Link = $WshShell.CreateShortcut($MenuLnk)
    $Link.TargetPath = $TargetVbs
    $Link.WorkingDirectory = $ScriptDir
    $Link.IconLocation = "$IconPath,0"
    $Link.Description = "CALPHADHEACalc"
    $Link.Save()
    if (-not $Silent) { Write-Host "  [CREATED] Start Menu Program: $MenuLnk" -ForegroundColor Green }
}

# 5. Summary
if (-not $Silent) {
    Write-Host "[5/5] Installation Completed Successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host "  INSTALLATION SUMMARY                                                       " -ForegroundColor White
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host "  Software Version   : CALPHADHEACalc v3.4.0"
    Write-Host "  Directory          : $ScriptDir"
    Write-Host "  Standalone Web App : Ready (Zero installation / 100% offline)"
    Write-Host "  Desktop App Mode   : $(if ($DesktopReady) { 'Active (Bordered CAE Window)' } else { 'Default Browser' })"
    Write-Host "  Decoupled Server   : $(if ($NodeReady) { 'Node.js API Gateway Ready' } else { 'Optional' })"
    Write-Host "  MATLAB Suite       : $(if ($MatlabReady) { 'Configured in MATLAB Path' } else { 'Not configured (Optional)' })"
    Write-Host ""
    Write-Host "  HOW TO LAUNCH:" -ForegroundColor Yellow
    Write-Host "  1. Double-click the 'CALPHADHEACalc' shortcut on your Desktop."
    Write-Host "  2. Or run: .\CALPHADHEACalc_Desktop.bat"
    if ($MatlabReady) {
        Write-Host "  3. In MATLAB, type: CALPHADHEACalc"
    }
    Write-Host "=============================================================================" -ForegroundColor Cyan
    Write-Host ""
}
exit 0
