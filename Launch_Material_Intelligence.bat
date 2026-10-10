@echo off
rem =========================================================================
rem   Material Intelligence Studio — One-Click Instant Desktop Launcher
rem   Launches native splash screen immediately (<25ms), runs MATLAB silently
rem   in the background with NO MATLAB desktop or extra taskbar tabs.
rem =========================================================================

cd /d "%~dp0"
start "" wscript.exe "%~dp0Launch_Material_Intelligence.vbs"
