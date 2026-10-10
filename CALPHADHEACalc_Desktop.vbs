' CALPHADHEACalc 2026 - Silent Desktop Launcher (Zero MATLAB Required)
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strBat = strDir & "\CALPHADHEACalc_Desktop.bat"
objShell.Run """" & strBat & """", 0, False
