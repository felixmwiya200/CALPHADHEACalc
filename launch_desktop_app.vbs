Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\Dell\Documents\Material design"
WshShell.Run "pythonw.exe pycalphad_app\main.py", 0, False
