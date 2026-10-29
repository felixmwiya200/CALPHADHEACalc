@echo off
title PyCALPHAD Materials Engineering Suite
echo Launching PyCALPHAD Materials Engineering Suite v2026.3.0...
python pycalphad_app\main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
