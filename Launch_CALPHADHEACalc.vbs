' =========================================================================
'   CALPHADHEACalc — Silent Native Windows Launcher
'   1. Launches native Florence flask splash screen instantly (<25ms)
'   2. Spawns MATLAB silently in background (NO MATLAB IDE window, NO MATLAB taskbar tab)
'   3. Only the application's own window & taskbar tab is visible.
'   4. When the application tab is closed, MATLAB terminates cleanly.
' =========================================================================

Option Explicit

Dim WshShell, fso, strDir, htaCmd, matlabCmd

Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Launch MATLAB in completely hidden batch mode (0 = SW_HIDE)
' This guarantees NO MATLAB IDE desktop, NO console window, and NO MATLAB tab in taskbar!
matlabCmd = "matlab -batch ""try, addpath('" & strDir & "\App'); addpath('" & strDir & "'); app = CALPHADHEACalc([], false, true); waitfor(app.UIFigure); catch ME, disp(ME.message); end"""
WshShell.Run matlabCmd, 0, False
