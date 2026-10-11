@echo off
title CALPHADHEACalc Decoupled CAE Backend Server
echo =================================================================
echo        CALPHADHEACalc Decoupled CAE Backend Server v3.4.0
echo =================================================================
echo Starting Node.js API Gateway and Headless MATLAB Engine Bridge...
echo.
node "%~dp0server.js"
pause
