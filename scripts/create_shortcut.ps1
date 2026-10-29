$desktop = [Environment]::GetFolderPath('Desktop')
$wsh = New-Object -ComObject WScript.Shell
$lnkPath = Join-Path $desktop "PyCALPHAD Materials Suite.lnk"
$exePath = "C:\Users\Dell\Documents\Material design\dist\PyCALPHAD_Suite\PyCALPHAD_Suite.exe"

$shortcut = $wsh.CreateShortcut($lnkPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = "C:\Users\Dell\Documents\Material design"
$shortcut.IconLocation = "$exePath,0"
$shortcut.Description = "PyCALPHAD Materials Engineering Suite v2026.3.0"
$shortcut.Save()

Write-Host "Native Desktop Application Shortcut updated at: $lnkPath"
