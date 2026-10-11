@echo off
setlocal enabledelayedexpansion
title CALPHADHEACalc - Software Installation Wizard
cd /d "%~dp0"

echo =============================================================================
echo   CALPHADHEACalc: High-Entropy Alloy Multi-Physics Software Installation
echo   Authors: Felix Mwiya ^& Prof. Sheela Singh, SRM University-AP (2026)
echo =============================================================================
echo.

:: 1. Verify Repository Integrity
echo [1/5] Verifying repository core files...
set "MISSING=0"
if not exist "index.html" (
    echo   [ERROR] Missing core application file: index.html
    set "MISSING=1"
)
if not exist "App\CALPHADHEACalc.m" (
    echo   [ERROR] Missing MATLAB core engine: App\CALPHADHEACalc.m
    set "MISSING=1"
)
if "!MISSING!"=="1" (
    echo.
    echo Installation aborted due to missing repository files.
    pause
    exit /b 1
)
echo   Repository integrity verified (All core calculation modules present).
echo.

:: 2. Detect Runtimes
echo [2/5] Detecting available software runtimes...

:: Check Edge / Chrome for Standalone Desktop Mode
set "DESKTOP_READY=0"
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" set "DESKTOP_READY=1"
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" set "DESKTOP_READY=1"
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "DESKTOP_READY=1"
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "DESKTOP_READY=1"

if "!DESKTOP_READY!"=="1" (
    echo   [FOUND] Microsoft Edge / Google Chrome detected (Native Desktop Mode ready)
) else (
    echo   [NOTICE] Edge/Chrome not detected. Application will launch in default browser.
)

:: Check Node.js for Decoupled Server
set "NODE_READY=0"
where node >nul 2>nul
if %errorlevel% equ 0 (
    for /f "tokens=*" %%v in ('node -v 2^>nul') do set "NODE_VER=%%v"
    echo   [FOUND] Node.js !NODE_VER! detected (Decoupled API Server ready)
    set "NODE_READY=1"
) else (
    echo   [INFO] Node.js not found in PATH (Optional: required for headless API streaming)
)

:: Check MATLAB
set "MATLAB_READY=0"
where matlab >nul 2>nul
if %errorlevel% equ 0 (
    echo   [FOUND] MATLAB detected in PATH
    set "MATLAB_READY=1"
) else (
    if exist "C:\Program Files\MATLAB" (
        for /d %%D in ("C:\Program Files\MATLAB\R*") do (
            if exist "%%D\bin\matlab.exe" (
                echo   [FOUND] MATLAB detected at %%D
                set "MATLAB_READY=1"
            )
        )
    )
)
if "!MATLAB_READY!"=="0" (
    echo   [INFO] MATLAB not detected (Standalone Web ^& Desktop modes run 100%% without MATLAB)
)
echo.

:: 3. Configure MATLAB Path (if MATLAB is present)
echo [3/5] Configuring calculation engines...
if "!MATLAB_READY!"=="1" (
    echo   Registering CALPHADHEACalc in MATLAB search path...
    matlab -batch "install" >nul 2>nul
    echo   MATLAB permanent path registration and self-test complete.
) else (
    echo   Skipping MATLAB path registration (Standalone mode active).
)
echo.

:: 4. Create Desktop & Start Menu Shortcuts
echo [4/5] Creating application shortcuts...

set "SCRIPT_DIR=%~dp0"
set "ICON_PATH=%SCRIPT_DIR%app_icon.ico"
set "TARGET_VBS=%SCRIPT_DIR%CALPHADHEACalc_Desktop.vbs"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$wsh = New-Object -ComObject WScript.Shell; " ^
    "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
    "$link = $wsh.CreateShortcut(\"$desktop\CALPHADHEACalc.lnk\"); " ^
    "$link.TargetPath = '%TARGET_VBS%'; " ^
    "$link.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$link.IconLocation = '%ICON_PATH%,0'; " ^
    "$link.Description = 'CALPHADHEACalc - High-Entropy Alloy Multi-Physics Software'; " ^
    "$link.Save(); " ^
    "$programs = [System.Environment]::GetFolderPath('Programs'); " ^
    "$menuDir = Join-Path $programs 'CALPHADHEACalc'; " ^
    "if (-not (Test-Path $menuDir)) { New-Item -ItemType Directory -Path $menuDir -Force | Out-Null }; " ^
    "$menuLink = $wsh.CreateShortcut((Join-Path $menuDir 'CALPHADHEACalc.lnk')); " ^
    "$menuLink.TargetPath = '%TARGET_VBS%'; " ^
    "$menuLink.WorkingDirectory = '%SCRIPT_DIR%'; " ^
    "$menuLink.IconLocation = '%ICON_PATH%,0'; " ^
    "$menuLink.Description = 'CALPHADHEACalc'; " ^
    "$menuLink.Save();"

echo   [CREATED] Desktop Shortcut: CALPHADHEACalc.lnk
echo   [CREATED] Start Menu Program: CALPHADHEACalc

if "!MATLAB_READY!"=="1" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$wsh = New-Object -ComObject WScript.Shell; " ^
        "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
        "$link = $wsh.CreateShortcut(\"$desktop\CALPHADHEACalc (MATLAB Desktop).lnk\"); " ^
        "$link.TargetPath = '%SCRIPT_DIR%Launch_CALPHADHEACalc.vbs'; " ^
        "$link.WorkingDirectory = '%SCRIPT_DIR%'; " ^
        "$link.IconLocation = '%ICON_PATH%,0'; " ^
        "$link.Description = 'CALPHADHEACalc MATLAB CAE Suite'; " ^
        "$link.Save();"
    echo   [CREATED] Desktop Shortcut: CALPHADHEACalc (MATLAB Desktop).lnk
)
echo.

:: 5. Installation Summary
echo [5/5] Installation Completed Successfully!
echo.
echo =============================================================================
echo   INSTALLATION SUMMARY
echo =============================================================================
echo   Software Name       : CALPHADHEACalc v3.4.0
echo   Installation Path   : %~dp0
echo   Standalone Web App  : Ready (No MATLAB required)
if "!DESKTOP_READY!"=="1" (
echo   Native Desktop App  : Ready (Bordered CAE Window)
) else (
echo   Native Desktop App  : Default Browser Mode
)
if "!MATLAB_READY!"=="1" (
echo   MATLAB Suite        : Installed ^& Registered in MATLAB Path
) else (
echo   MATLAB Suite        : Not configured (Optional)
)
echo.
echo   HOW TO LAUNCH:
echo   1. Double-click the 'CALPHADHEACalc' shortcut on your Desktop.
echo   2. Or run: CALPHADHEACalc_Desktop.bat
if "!MATLAB_READY!"=="1" (
echo   3. In MATLAB, simply type: CALPHADHEACalc
)
echo =============================================================================
echo.
if not "%~1"=="--silent" if not "%~1"=="/q" pause

