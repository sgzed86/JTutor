# Creates/updates a Desktop shortcut for Jtutor with the custom app icon.
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$bat = Join-Path $root "start_jtutor.bat"
$ico = Join-Path $root "build\icon.ico"
if (-not (Test-Path $bat)) { throw "Missing start_jtutor.bat" }
if (-not (Test-Path $ico)) { throw "Missing build\icon.ico" }

$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Jtutor.lnk"
$w = New-Object -ComObject WScript.Shell
$sc = $w.CreateShortcut($lnkPath)
$sc.TargetPath = $bat
$sc.WorkingDirectory = $root
$sc.WindowStyle = 7
$sc.IconLocation = "$ico,0"
$sc.Description = "Irodori local Japanese tutor"
$sc.Save()
Write-Host "Desktop shortcut updated: $lnkPath"
