# Build a portable Jtutor zip for Windows (no Irodori assets, no Node required for end users).
param(
  [string]$OutDir = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $OutDir) {
  $OutDir = Join-Path $Root "dist-release"
}

$Stage = Join-Path $OutDir "Jtutor"
$ZipPath = Join-Path $OutDir "Jtutor-portable-win.zip"

Write-Host "==> Building UI..."
npm run build --prefix apps\desktop
if ($LASTEXITCODE -ne 0) { throw "UI build failed" }

if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage | Out-Null

function Copy-Tree($From, $To, $ExcludeDirs = @()) {
  New-Item -ItemType Directory -Path $To -Force | Out-Null
  Get-ChildItem $From -Force | ForEach-Object {
    if ($_.PSIsContainer -and ($ExcludeDirs -contains $_.Name)) { return }
    $dest = Join-Path $To $_.Name
    if ($_.PSIsContainer) {
      Copy-Tree $_.FullName $dest $ExcludeDirs
    } else {
      Copy-Item $_.FullName $dest -Force
    }
  }
}

Write-Host "==> Staging files..."
Copy-Tree (Join-Path $Root "backend") (Join-Path $Stage "backend") @("__pycache__", ".pytest_cache", "*.pyc")
# prune pycache after copy
Get-ChildItem (Join-Path $Stage "backend") -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Copy-Tree (Join-Path $Root "content") (Join-Path $Stage "content") @()
# Drop huge optional whisper cache if present (not needed for runtime)
$tx = Join-Path $Stage "content\starter\audio_transcripts.json"
if (Test-Path $tx) { Remove-Item $tx -Force }
$tx2 = Join-Path $Stage "content\elementary1\audio_transcripts.json"
if (Test-Path $tx2) { Remove-Item $tx2 -Force }

New-Item -ItemType Directory -Path (Join-Path $Stage "ui") | Out-Null
Copy-Item (Join-Path $Root "apps\desktop\dist\*") (Join-Path $Stage "ui") -Recurse -Force

Copy-Item (Join-Path $Root "release\INSTALL.bat") $Stage -Force
Copy-Item (Join-Path $Root "release\START.bat") $Stage -Force
Copy-Item (Join-Path $Root "release\STOP.bat") $Stage -Force
Copy-Item (Join-Path $Root "release\README.md") (Join-Path $Stage "README.md") -Force
# Plain-text copy for people who open it in Notepad without Markdown preview
Copy-Item (Join-Path $Root "release\README.md") (Join-Path $Stage "README.txt") -Force

New-Item -ItemType Directory -Path (Join-Path $Stage "assets\audio") -Force | Out-Null
Copy-Item (Join-Path $Root "release\assets\README.txt") (Join-Path $Stage "assets\README.txt") -Force
New-Item -ItemType Directory -Path (Join-Path $Stage "data") -Force | Out-Null

# Tiny placeholder so empty audio folder is kept in zip
Set-Content -Path (Join-Path $Stage "assets\audio\.gitkeep") -Value ""

# Version stamp
$ver = @{
  version = "0.1.0"
  built = (Get-Date).ToString("s")
  books = @("starter", "elementary1")
  note = "Irodori PDFs/MP3s not included"
} | ConvertTo-Json
Set-Content -Path (Join-Path $Stage "VERSION.json") -Value $ver -Encoding UTF8

Write-Host "==> Zipping $ZipPath ..."
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $Stage -DestinationPath $ZipPath -Force

$size = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "Release ready:"
Write-Host "  Folder: $Stage"
Write-Host "  Zip:    $ZipPath  ($size MB)"
Write-Host ""
Write-Host "Send the zip. Recipient: unzip -> INSTALL.bat -> add assets -> START.bat"
Write-Host "Do NOT include assets/irodori PDFs or MP3s in what you send."
