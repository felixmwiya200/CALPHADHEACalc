@echo off
setlocal
title CALPHADHEACalc 2026 - High-Entropy Alloy Workstation
cd /d "%~dp0"

:: -----------------------------------------------------------------------------
:: CALPHADHEACalc Standalone Native Desktop Launcher (Zero MATLAB Required)
:: Launches the high-density CALPHAD materials suite in native desktop app window
:: -----------------------------------------------------------------------------

set "APP_FILE=%~dp0index.html"
set "APP_URL=file:///%APP_FILE:\=/%"

:: Check for Microsoft Edge (installed on 100% of modern Windows 10/11 systems)
if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%" --window-size=1440,900
    exit /b 0
)

if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
    start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app="%APP_URL%" --window-size=1440,900
    exit /b 0
)

:: Check for Google Chrome
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app="%APP_URL%" --window-size=1440,900
    exit /b 0
)

if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --app="%APP_URL%" --window-size=1440,900
    exit /b 0
)

:: Fallback: Open in default system browser
start "" "%APP_FILE%"
exit /b 0
