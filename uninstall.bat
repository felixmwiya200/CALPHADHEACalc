@echo off
setlocal enabledelayedexpansion
title CALPHADHEACalc - Software Uninstallation Wizard
cd /d "%~dp0"

echo =============================================================================
echo   CALPHADHEACalc: Software Uninstaller
echo   Authors: Felix Mwiya ^& Prof. Sheela Singh, SRM University-AP (2026)
echo =============================================================================
echo.

echo Removing desktop and start menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
    "$programs = [System.Environment]::GetFolderPath('Programs'); " ^
    "$l1 = Join-Path $desktop 'CALPHADHEACalc.lnk'; " ^
    "$l2 = Join-Path $desktop 'CALPHADHEACalc (MATLAB Desktop).lnk'; " ^
    "$menuDir = Join-Path $programs 'CALPHADHEACalc'; " ^
    "if (Test-Path $l1) { Remove-Item $l1 -Force }; " ^
    "if (Test-Path $l2) { Remove-Item $l2 -Force }; " ^
    "if (Test-Path $menuDir) { Remove-Item $menuDir -Recurse -Force };"

echo Shortcuts removed.
echo.

where matlab >nul 2>nul
if %errorlevel% equ 0 (
    echo Unregistering CALPHADHEACalc from MATLAB search path...
    matlab -batch "try, rmpath(genpath(pwd)); savepath; disp('[SUCCESS] MATLAB search path cleaned.'); catch ME, disp(ME.message); end" >nul 2>nul
    echo MATLAB path cleaned.
)

echo.
echo Uninstallation completed successfully. Repository files were kept intact.
echo.
pause
